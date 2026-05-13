"""Load and merge CSV exports (requests, service, repairs, equipment summary)."""

import glob
import os

import pandas as pd

from dashboard import constants as C
from dashboard.taxonomy import equipment_chart_class, equipment_row_category, norm_equip_id


def _csv_paths_in_dir(directory: str) -> list[str]:
    if not os.path.isdir(directory):
        return []
    paths = sorted(glob.glob(os.path.join(directory, "*.csv")))
    return [p for p in paths if os.path.isfile(p)]


def _unique_header_names(names: list) -> list[str]:
    """Ensure column names are unique (duplicate headers / blank cells break pd.concat)."""
    out: list[str] = []
    counts: dict[str, int] = {}
    for i, raw in enumerate(names):
        s = str(raw).replace("\n", " ").strip() if not pd.isna(raw) else ""
        base = s if s else f"_unnamed_{i}"
        if base not in counts:
            counts[base] = 0
            out.append(base)
        else:
            counts[base] += 1
            out.append(f"{base}__{counts[base]}")
    return out


def _drop_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.columns.is_unique:
        return df
    return df.loc[:, ~df.columns.duplicated(keep="first")].copy()


def load_requests(path: str) -> pd.DataFrame:
    raw = pd.read_csv(path, header=None)
    raw.columns = raw.iloc[1]
    df = raw.iloc[2:].reset_index(drop=True)
    df = df[df["Work Order #"].notna() & ~df["Work Order #"].str.startswith("Total")]
    df["Request Date"] = pd.to_datetime(df["Request Date"], format="%m/%d/%Y", errors="coerce")
    df["month_key"] = df["Request Date"].dt.to_period("M").astype(str)
    return df


def load_service(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Sched. Date"] = pd.to_datetime(df["Sched. Date"], errors="coerce")
    df["Completed Date"] = pd.to_datetime(df["Completed Date"], errors="coerce")
    df["month_key"] = df["Sched. Date"].dt.to_period("M").astype(str)
    id_col = "Equipment Id" if "Equipment Id" in df.columns else None
    if id_col:
        df["equipIdNorm"] = df[id_col].map(norm_equip_id)
    else:
        df["equipIdNorm"] = ""
    name_col = "Equipment Name" if "Equipment Name" in df.columns else None
    if name_col:
        df["equipCategory"] = df[name_col].map(equipment_chart_class)
    else:
        df["equipCategory"] = "Other"
    return df


def load_repairs(path: str) -> pd.DataFrame:
    raw = pd.read_csv(path, skiprows=1, header=None)
    raw.columns = _unique_header_names([c for c in raw.iloc[0]])
    df = raw.iloc[1:].reset_index(drop=True)

    def _norm_key(name: str) -> str:
        return str(name).lower().replace(" ", "").replace("_", "")

    key_to_col = {_norm_key(c): c for c in df.columns if c != ""}

    def _col(*aliases: str):
        for a in aliases:
            k = _norm_key(a)
            if k in key_to_col:
                return key_to_col[k]
        return None

    row_col = _col("#", "no.", "no", "row", "line", "item", "#.")
    if row_col is not None:
        df = df[df[row_col].apply(lambda x: str(x).strip().isdigit())]
    else:
        # Exports without a row-index column: keep rows with a parseable completed/repair date
        date_guess = _col("Completed Date", "Date", "Repair Date", "Completed")
        if date_guess:
            dts = pd.to_datetime(df[date_guess], errors="coerce")
            df = df[dts.notna()]
        else:
            eq_guess = _col("Equipment Name", "Equipment", "Description")
            if eq_guess:
                df = df[df[eq_guess].astype(str).str.strip().ne("") & df[eq_guess].notna()]

    df.columns = _unique_header_names([str(c).replace("\n", " ").strip() if not pd.isna(c) else "" for c in df.columns])
    df = _drop_duplicate_columns(df)
    df = df.rename(
        columns={
            "Completed Date": "date",
            "Equipment Name": "equipment",
            "Equipment ID": "equipId",
            "Location": "location",
            "# of Repairs": "repairs",
            "Repair Person-Hrs": "hours",
            "Parts Cost $": "parts",
            "Total Labor $": "labor",
            "Est. Total $": "total",
        }
    )

    def _nk(c):
        return str(c).lower().replace(" ", "").replace("_", "")

    if "date" not in df.columns:
        for c in list(df.columns):
            if _nk(c) in ("completeddate", "repairdate", "completiondate", "dateclosed"):
                df = df.rename(columns={c: "date"})
                break
    if "equipment" not in df.columns:
        for c in list(df.columns):
            if _nk(c) in ("equipmentname", "equipment", "item", "description"):
                df = df.rename(columns={c: "equipment"})
                break
    if "equipId" not in df.columns:
        for c in list(df.columns):
            if _nk(c) in ("equipmentid", "equipid", "assetid"):
                df = df.rename(columns={c: "equipId"})
                break

    for need, default in [
        ("repairs", 0),
        ("hours", 0),
        ("parts", 0),
        ("labor", 0),
        ("total", 0),
        ("location", ""),
        ("equipment", ""),
        ("equipId", ""),
    ]:
        if need not in df.columns:
            df[need] = default
    if "date" not in df.columns:
        df["date"] = pd.NaT

    for col in ["repairs", "hours", "parts", "labor", "total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["month_key"] = df["date"].dt.to_period("M").astype(str)

    price_map = {
        "versamatic": 1035,
        "lindhaus": 850,
        "kaivac": 5700,
        "big vacuum": 1050,
    }

    def get_price(name):
        n = str(name).lower()
        for k, v in price_map.items():
            if k in n:
                return v
        return 1035

    df["newPrice"] = df["equipment"].apply(get_price)
    df = _drop_duplicate_columns(df)
    return df


def _load_requests_merged() -> pd.DataFrame:
    paths = _csv_paths_in_dir(C.REQUESTS_DIR)
    if not paths:
        raise FileNotFoundError(
            f"No *.csv under {C.REQUESTS_DIR!r}. Create the folder and add at least one request export."
        )
    return pd.concat([load_requests(p) for p in paths], ignore_index=True)


def _load_service_merged() -> pd.DataFrame:
    paths = _csv_paths_in_dir(C.SERVICE_DIR)
    if not paths:
        raise FileNotFoundError(
            f"No *.csv under {C.SERVICE_DIR!r}. Create the folder and add at least one service export."
        )
    return pd.concat([load_service(p) for p in paths], ignore_index=True)


def _load_repairs_merged() -> pd.DataFrame:
    paths = _csv_paths_in_dir(C.REPAIRS_DIR)
    if not paths:
        raise FileNotFoundError(
            f"No *.csv under {C.REPAIRS_DIR!r}. Create the folder and add at least one repair export."
        )
    return pd.concat([load_repairs(p) for p in paths], ignore_index=True)


def load_equipment_summary() -> pd.DataFrame:
    if not os.path.isfile(C.EQUIPMENT_SUMMARY_CSV):
        return pd.DataFrame()
    try:
        df = pd.read_csv(C.EQUIPMENT_SUMMARY_CSV)
    except Exception:
        return pd.DataFrame()
    if df.empty or "EquipmentId" not in df.columns:
        return df
    df = df.copy()
    df["equipIdNorm"] = df["EquipmentId"].map(norm_equip_id)
    df["category"] = df.apply(equipment_row_category, axis=1)
    return df


try:
    df_req = _load_requests_merged()
    df_service = _load_service_merged()
    df_repairs = _load_repairs_merged()
    df_equip = load_equipment_summary()
except FileNotFoundError as e:
    raise SystemExit(
        f"{e}\n"
        "Add one or more *.csv files under data/requests, data/service, and data/repairs "
        "(run the script from the project root so those paths resolve)."
    ) from e

all_months = sorted(
    m
    for m in (
        set(df_req["month_key"])
        | set(df_service["month_key"])
        | set(df_repairs["month_key"])
    )
    if pd.notna(m) and str(m) != "NaT"
)
MONTH_OPTIONS = [{"label": pd.Period(m).strftime("%B %Y"), "value": m} for m in all_months]

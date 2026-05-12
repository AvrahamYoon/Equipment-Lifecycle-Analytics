import os

import pandas as pd

INPUT_DIR = os.path.join("data", "equipment", "raw")
OUTPUT_DIR = os.path.join("data", "equipment", "cleaned")

_RENAME = {
    "Equipment ID": "EquipmentId",
    "Equip. Name": "Name",
    "Equip. Type": "EquipType",
    "Serial Number": "SerialNumber",
    "Depreciation Yrs": "DepreciationYears",
    "Purch. Date": "PurchaseDate",
    "Purch. Cost": "Cost",
    "Current Value": "CurrentValue",
}


def _norm_header_token(s: str) -> str:
    """Stable key for one header cell, e.g. 'Equipment ID' -> 'equipmentid'."""
    t = str(s).strip().lstrip("\ufeff").lower().replace(".", " ").replace("_", " ")
    return "".join(t.split())


def _row_looks_like_equipment_header(row) -> bool:
    """True if this row has an 'Equipment ID' (or EquipmentId) cell — strict, no substring tricks."""
    for x in row:
        if pd.isna(x) or str(x).strip() == "":
            continue
        if _norm_header_token(x) == "equipmentid":
            return True
    return False


def _detect_header_row(filepath: str, max_scan: int = 40) -> int | None:
    peek = pd.read_csv(
        filepath,
        header=None,
        nrows=max_scan,
        dtype=str,
        encoding_errors="replace",
    )
    for i in range(len(peek)):
        if _row_looks_like_equipment_header(peek.iloc[i]):
            return i
    return None


def _prepare_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={k: v for k, v in _RENAME.items() if k in df.columns})
    if "#" in df.columns:
        df = df.drop(columns=["#"], errors="ignore")
    if "CurrentValue" in df.columns:
        if "Cost" not in df.columns:
            df["Cost"] = df["CurrentValue"]
        else:
            df["Cost"] = df["Cost"].fillna(df["CurrentValue"])
        df = df.drop(columns=["CurrentValue"], errors="ignore")
    return df


def _read_with_header_skip(filepath: str, skip: int) -> pd.DataFrame:
    df = pd.read_csv(
        filepath,
        skiprows=list(range(skip)),
        header=0,
        encoding_errors="replace",
    )
    df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]
    return _prepare_columns(df)


def read_equipment_table(filepath: str) -> pd.DataFrame:
    """
    Find the header row (row containing a cell equal to Equipment ID / EquipmentId),
    then fall back to skip 1 line (title + header) or no skip (plain CSV).
    """
    found = _detect_header_row(filepath)
    tries = []
    if found is not None:
        tries.append(found)
    for s in (1, 0):
        if s not in tries:
            tries.append(s)

    last_cols = None
    for skip in tries:
        df = _read_with_header_skip(filepath, skip)
        last_cols = list(df.columns)
        if "EquipmentId" in df.columns and "Name" in df.columns:
            return df

    raise ValueError(
        "Missing EquipmentId/Name after reading. "
        f"Tried header row offsets {tries!r}. Columns: {last_cols!r}"
    )


def clean_equipment_file(filepath):
    df = read_equipment_table(filepath)

    df = df[
        (df["EquipmentId"].notna())
        & (df["Name"].notna())
        & (~df["Name"].astype(str).str.contains(r"\(Repair\)|\(PM\)", na=False))
    ]

    keep_cols = [
        "EquipmentId",
        "Name",
        "Location",
        "EquipType",
        "Manufacturer",
        "SerialNumber",
        "PurchaseDate",
        "DepreciationYears",
        "Cost",
    ]
    df = df[[c for c in keep_cols if c in df.columns]]

    df["EquipmentId"] = (
        df["EquipmentId"].astype(str).str.replace(" ", "", regex=False).str.strip()
    )

    if "Cost" in df.columns:
        df["Cost"] = (
            df["Cost"].astype(str).str.replace(r"[\$,]", "", regex=True)
        )
        df["Cost"] = pd.to_numeric(df["Cost"], errors="coerce")

    if "PurchaseDate" in df.columns:
        df["PurchaseDate"] = pd.to_datetime(df["PurchaseDate"], errors="coerce")
        df = df.sort_values(by="PurchaseDate", ascending=False)

    df = df.drop_duplicates(subset="EquipmentId", keep="first")

    if "PurchaseDate" in df.columns:
        today = pd.Timestamp.today()
        df["Age"] = (today - df["PurchaseDate"]).dt.days / 365

    return df


def main():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_data = []
    for file in sorted(os.listdir(INPUT_DIR)):
        if not file.endswith(".csv"):
            continue
        filepath = os.path.join(INPUT_DIR, file)
        print(f"Processing: {file}")
        cleaned_df = clean_equipment_file(filepath)
        out = os.path.join(OUTPUT_DIR, file.replace(".csv", "_cleaned.csv"))
        cleaned_df.to_csv(out, index=False)
        all_data.append(cleaned_df)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        if "PurchaseDate" in final_df.columns:
            final_df = final_df.sort_values(by="PurchaseDate", ascending=False)
        final_df = final_df.drop_duplicates(subset="EquipmentId", keep="first")
        final_df.to_csv(os.path.join(OUTPUT_DIR, "all_equipment_summary.csv"), index=False)
        print("✅ Done: data/equipment/cleaned/all_equipment_summary.csv")
    else:
        print(f"⚠️ No CSV in {INPUT_DIR}")


if __name__ == "__main__":
    main()

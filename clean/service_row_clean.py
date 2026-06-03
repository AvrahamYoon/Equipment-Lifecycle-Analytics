"""Clean service / equipment-detail exports from ``data/service/row/`` into ``data/service/``."""

from __future__ import annotations

import os
import re

import pandas as pd

from clean.row_clean_common import (
    infer_month_key_from_name,
    list_row_files,
    month_key_for_date,
    output_dir,
    parse_dollar,
    row_input_dir,
)

SERVICE_COLUMNS = [
    "Equipment Id",
    "Equipment Name",
    "Sched. Date",
    "Completed Date",
    "Location",
    "Description",
    "Status",
    "Estimated Price",
]


def _clean_description(desc: str) -> str:
    s = str(desc).strip()
    s = re.sub(r"\s*-\s*\(Repair\)\s*$", "", s, flags=re.I)
    s = re.sub(r"\s*-\s*\(PM\)\s*$", "", s, flags=re.I)
    return s.strip()


def _is_placeholder_description(desc: str) -> bool:
    s = str(desc).strip().lower()
    return s in ("", "- (repair)", "- (pm)", "nan")


def clean_service_raw(df: pd.DataFrame, month_key: str | None) -> pd.DataFrame:
    context: dict = {}
    rows = []

    for _, row in df.iterrows():
        eid = row.get("EquipmentId")
        if pd.notna(eid) and str(eid).strip():
            context = {
                "Equipment Id": str(eid).strip(),
                "Equipment Name": str(row.get("Name", "")).strip(),
                "Location": str(row.get("Location", "")).strip(),
                "Estimated Price": parse_dollar(row.get("Cost")),
            }

        sched_raw = row.get("ScheduledDate")
        comp_raw = row.get("CompletedDate")
        desc_raw = row.get("Description")

        if pd.isna(sched_raw) or not str(sched_raw).strip():
            continue
        if _is_placeholder_description(desc_raw):
            continue
        if not context.get("Equipment Id"):
            continue

        sched = pd.to_datetime(sched_raw, errors="coerce")
        comp = pd.to_datetime(comp_raw, errors="coerce")
        if pd.isna(sched) and pd.isna(comp):
            continue

        if month_key:
            keys = {month_key_for_date(sched), month_key_for_date(comp)}
            keys.discard(None)
            if keys and month_key not in keys:
                continue

        desc = _clean_description(desc_raw)
        if not desc or desc.lower().startswith("delete duplicate"):
            continue

        status = "Completed" if pd.notna(comp) else "Scheduled"
        price = context.get("Estimated Price") or 0.0

        rows.append(
            {
                "Equipment Id": context["Equipment Id"],
                "Equipment Name": context["Equipment Name"],
                "Sched. Date": sched.strftime("%Y-%m-%d") if pd.notna(sched) else "",
                "Completed Date": comp.strftime("%Y-%m-%d") if pd.notna(comp) else "",
                "Location": context["Location"],
                "Description": desc,
                "Status": status,
                "Estimated Price": price if price > 0 else "",
            }
        )

    return pd.DataFrame(rows, columns=SERVICE_COLUMNS)


def _default_output_name(source: str, month_key: str | None) -> str:
    if month_key:
        label = pd.Period(month_key, freq="M").strftime("%B")
        return f"{label}_Service_Orders_with_Prices.csv"
    stem = re.sub(r"[^\w]+", "_", os.path.splitext(source)[0]).strip("_")
    return f"{stem}_cleaned.csv"


def process_file(path: str, out_dir: str) -> str | None:
    df = pd.read_csv(path, encoding_errors="replace")
    month_key = infer_month_key_from_name(os.path.basename(path))
    cleaned = clean_service_raw(df, month_key)
    if cleaned.empty:
        print(f"  [skip] No service rows in {os.path.basename(path)}")
        return None

    out_name = _default_output_name(os.path.basename(path), month_key)
    out_path = os.path.join(out_dir, out_name)
    cleaned.to_csv(out_path, index=False)
    print(f"  Wrote {out_name} ({len(cleaned)} rows)")
    return out_path


def main():
    in_dir = row_input_dir("service")
    out_dir = output_dir("service")
    os.makedirs(out_dir, exist_ok=True)

    files = list_row_files("service", (".csv",))
    if not files:
        print(f"No CSV files in {in_dir}")
        return

    print(f"Cleaning service from {in_dir} → {out_dir}")
    for path in files:
        print(f"Processing {path.name}")
        process_file(str(path), str(out_dir))


if __name__ == "__main__":
    main()

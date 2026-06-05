"""Build ``Equipment Valuation Sheet.csv`` from ``purchase.csv`` purchase history.

Fills **Original Purchase Cost** with the median recorded cost per equipment
description. Other valuation columns are left for manual entry.

Run from the repo root when ``purchase.csv`` changes (dashboard reads the
output file at startup; it does not regenerate this sheet itself)::

    python -m clean.generate_valuation_sheet
"""

from __future__ import annotations

import argparse
import os
import statistics
from collections import Counter

import pandas as pd

from pricing_common import (
    norm_equipment_name,
    parse_dollar_amount,
    parse_purchase_year,
    pick_column,
)

DEFAULT_PURCHASE_CSV = os.path.join("data", "equipment", "purchase", "purchase.csv")
DEFAULT_OUTPUT_CSV = os.path.join(
    "data", "equipment", "purchase", "Equipment Valuation Sheet.csv"
)

OUTPUT_COLUMNS = [
    "Equipment",
    "Original Purchase Cost*",
    "2026 Replacement Cost",
    "Estimated Current Value",
    "Lifetime Repair Cost",
]

_MANUAL_PLACEHOLDER = "Enter Data"


def _format_dollar(amount: float) -> str:
    rounded = round(amount, 2)
    if abs(rounded - round(rounded)) < 0.005:
        return f"${int(round(rounded)):,}"
    return f"${rounded:,.2f}"


def _args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate Equipment Valuation Sheet.csv from purchase.csv."
    )
    p.add_argument("--input", default=DEFAULT_PURCHASE_CSV, help="purchase.csv path")
    p.add_argument("--output", default=DEFAULT_OUTPUT_CSV, help="output valuation CSV")
    p.add_argument(
        "--recent-years",
        type=int,
        default=0,
        metavar="N",
        help="If set, median uses only purchases within the last N calendar years "
        "(by pur. year). Default: all years.",
    )
    return p.parse_args()


def build_valuation_rows(
    purchase_path: str,
    recent_years: int = 0,
    reference_year: int | None = None,
) -> list[dict[str, str]]:
    df = pd.read_csv(purchase_path, encoding_errors="replace")
    if df.empty:
        return []

    desc_col = pick_column(df, "Description", "Equip. Name", "Equipment Name")
    cost_col = pick_column(df, "Cost", "Purch. Cost", "Purchase Cost")
    year_col = pick_column(df, "pur.", "pur", "Purchase Year", "Year", "Purch. Date")
    if not desc_col or not cost_col:
        raise SystemExit(f"Missing Description/Cost columns in {purchase_path}")

    ref_year = reference_year or pd.Timestamp.today().year
    groups: dict[str, list[tuple[str, int | None, float]]] = {}
    for _, row in df.iterrows():
        label = str(row.get(desc_col, "")).strip()
        if not label:
            continue
        cost = parse_dollar_amount(row.get(cost_col))
        if cost is None:
            continue
        key = norm_equipment_name(label)
        if not key:
            continue
        year = parse_purchase_year(row.get(year_col)) if year_col else None
        groups.setdefault(key, []).append((label, year, cost))

    rows: list[dict[str, str]] = []
    for key in sorted(groups.keys()):
        records = groups[key]
        pool = records
        if recent_years > 0:
            windowed = [
                rec
                for rec in records
                if rec[1] is not None and (ref_year - rec[1]) <= recent_years
            ]
            if windowed:
                pool = windowed

        costs = [c for _, _, c in pool]
        median_cost = float(statistics.median(costs))
        display_name = Counter(label for label, _, _ in pool).most_common(1)[0][0]

        rows.append(
            {
                "Equipment": display_name,
                "Original Purchase Cost*": _format_dollar(median_cost),
                "2026 Replacement Cost": _MANUAL_PLACEHOLDER,
                "Estimated Current Value": _MANUAL_PLACEHOLDER,
                "Lifetime Repair Cost": _MANUAL_PLACEHOLDER,
            }
        )

    rows.sort(key=lambda r: r["Equipment"].lower())
    return rows


def main() -> None:
    args = _args()
    if not os.path.isfile(args.input):
        raise SystemExit(f"Purchase file not found: {args.input}")

    rows = build_valuation_rows(args.input, recent_years=args.recent_years)
    if not rows:
        raise SystemExit(f"No purchase rows with Description + Cost in {args.input}")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    pd.DataFrame(rows, columns=OUTPUT_COLUMNS).to_csv(args.output, index=False)
    print(f"Wrote {len(rows)} equipment rows → {args.output}")


if __name__ == "__main__":
    main()

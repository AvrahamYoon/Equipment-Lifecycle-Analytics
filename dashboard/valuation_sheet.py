"""Load ``Equipment Valuation Sheet.csv`` once; lookup Original Purchase Cost only."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import pandas as pd

from pricing_common import match_equipment_key, norm_equipment_name, parse_dollar_amount, pick_column


@dataclass
class ValuationSheet:
    """Preloaded valuation rows keyed by normalized equipment label."""

    prices: dict[str, float] = field(default_factory=dict)
    keys_sorted: list[str] = field(default_factory=list)


def load_valuation_sheet(path: str) -> ValuationSheet:
    """Read valuation CSV at startup. Missing file → empty sheet (no error)."""
    if not path or not os.path.isfile(path):
        return ValuationSheet()

    try:
        df = pd.read_csv(path, encoding_errors="replace")
    except Exception:
        return ValuationSheet()
    if df.empty:
        return ValuationSheet()

    equip_col = pick_column(df, "Equipment", "Model", "Equipment Name")
    cost_col = pick_column(
        df,
        "Original Purchase Cost",
        "Original Purchase Cost*",
        "Original purchase cost",
    )
    if not equip_col or not cost_col:
        return ValuationSheet()

    prices: dict[str, float] = {}
    for _, row in df.iterrows():
        label = str(row.get(equip_col, "")).strip()
        if not label:
            continue
        cost = parse_dollar_amount(row.get(cost_col))
        if cost is None:
            continue
        key = norm_equipment_name(label)
        if key and key not in prices:
            prices[key] = cost

    keys_sorted = sorted(prices.keys(), key=len, reverse=True)
    return ValuationSheet(prices=prices, keys_sorted=keys_sorted)


def lookup_valuation_price(equipment_name, sheet: ValuationSheet | None) -> float | None:
    if not sheet or not sheet.prices:
        return None
    norm = norm_equipment_name(equipment_name)
    key = match_equipment_key(norm, sheet.keys_sorted)
    if not key:
        return None
    return sheet.prices.get(key)

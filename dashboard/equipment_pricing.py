"""New-equipment price resolution: purchase.csv by ID, valuation sheet, then service."""

from __future__ import annotations

import os

import pandas as pd

from dashboard.taxonomy import ensure_equip_id_norm_column, norm_equip_id
from dashboard.valuation_sheet import ValuationSheet, lookup_valuation_price
from pricing_common import parse_dollar_amount, pick_column


def load_purchase_price_map(path: str) -> dict[str, float]:
    """Map normalized equipment ID → purchase cost from ``purchase.csv``."""
    if not path or not os.path.isfile(path):
        return {}
    try:
        df = pd.read_csv(path, encoding_errors="replace")
    except Exception:
        return {}
    if df.empty:
        return {}

    id_col = pick_column(df, "ID #", "ID", "Equipment ID", "EquipmentId")
    cost_col = pick_column(df, "Cost", "Purch. Cost", "Purchase Cost")
    if not id_col or not cost_col:
        return {}

    out: dict[str, float] = {}
    for _, row in df.iterrows():
        eid = norm_equip_id(row.get(id_col))
        if not eid or eid in out:
            continue
        cost = parse_dollar_amount(row.get(cost_col))
        if cost is not None:
            out[eid] = cost
    return out


def build_service_price_map(df_service: pd.DataFrame) -> dict[str, float]:
    """Map normalized equipment ID → estimated price from service exports."""
    if df_service is None or df_service.empty:
        return {}

    id_col = pick_column(df_service, "Equipment Id", "Equipment ID", "equipId")
    price_col = pick_column(
        df_service,
        "Estimated Price",
        "New Price",
        "Equipment Price",
        "Est. Price",
    )
    if not id_col or not price_col:
        return {}

    out: dict[str, float] = {}
    for _, row in df_service.iterrows():
        eid = norm_equip_id(row.get(id_col))
        if not eid or eid in out:
            continue
        price = parse_dollar_amount(row.get(price_col))
        if price is not None:
            out[eid] = price
    return out


PRICE_SOURCE_PURCHASE = "purchase"
PRICE_SOURCE_VALUATION = "valuation"
PRICE_SOURCE_SERVICE = "service"
PRICE_SOURCE_NONE = ""

PRICE_SOURCE_LABEL = {
    PRICE_SOURCE_PURCHASE: "Accurate",
    PRICE_SOURCE_VALUATION: "Valuation",
    PRICE_SOURCE_SERVICE: "Estimated",
    PRICE_SOURCE_NONE: "—",
}

PRICE_BASIS_COLUMN = "Price basis"
PRICE_BASIS_TOOLTIP = (
    "Purchase.csv cost by equipment ID; else Original Purchase Cost from "
    "Equipment Valuation Sheet.csv (regenerate with "
    "python -m clean.generate_valuation_sheet when purchase.csv changes); "
    "else service estimated price."
)


def resolve_price_source(
    equip_id,
    equipment_name,
    purchase_map: dict[str, float],
    service_map: dict[str, float],
    valuation_sheet: ValuationSheet | None = None,
) -> str:
    eid = norm_equip_id(equip_id)
    if eid and eid in purchase_map:
        return PRICE_SOURCE_PURCHASE
    if lookup_valuation_price(equipment_name, valuation_sheet) is not None:
        return PRICE_SOURCE_VALUATION
    if eid and eid in service_map:
        return PRICE_SOURCE_SERVICE
    return PRICE_SOURCE_NONE


def resolve_new_price(
    equip_id,
    equipment_name,
    purchase_map: dict[str, float],
    service_map: dict[str, float],
    valuation_sheet: ValuationSheet | None = None,
) -> float:
    eid = norm_equip_id(equip_id)
    if eid and eid in purchase_map:
        return purchase_map[eid]
    val = lookup_valuation_price(equipment_name, valuation_sheet)
    if val is not None:
        return val
    if eid and eid in service_map:
        return service_map[eid]
    return 0.0


def apply_new_prices_to_repairs(
    df: pd.DataFrame,
    purchase_map: dict[str, float],
    service_map: dict[str, float],
    valuation_sheet: ValuationSheet | None = None,
) -> pd.DataFrame:
    if df.empty:
        out = df.copy()
        out["newPrice"] = pd.Series(dtype=float)
        out["priceSource"] = pd.Series(dtype=str)
        return out
    out = ensure_equip_id_norm_column(df, raw_col="equipId", norm_col="equipIdNorm")
    equip_col = "equipment" if "equipment" in out.columns else None

    def _row_prices(row):
        name = row[equip_col] if equip_col else ""
        eid = row["equipIdNorm"]
        price = resolve_new_price(
            eid, name, purchase_map, service_map, valuation_sheet
        )
        source = resolve_price_source(
            eid, name, purchase_map, service_map, valuation_sheet
        )
        return price, source

    priced = out.apply(_row_prices, axis=1, result_type="expand")
    out["newPrice"] = priced[0]
    out["priceSource"] = priced[1]
    return out

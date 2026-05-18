"""New-equipment price resolution for replacement (purchase CSV, then service estimates)."""

import os

import pandas as pd

from dashboard.taxonomy import norm_equip_id


def _norm_col_key(name: str) -> str:
    return str(name).lower().replace(" ", "").replace("_", "").replace("#", "")


def parse_dollar_amount(value) -> float | None:
    if pd.isna(value):
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.replace("$", "").replace(",", "")
    n = pd.to_numeric(s, errors="coerce")
    if pd.isna(n) or float(n) <= 0:
        return None
    return float(n)


def _pick_column(df: pd.DataFrame, *aliases: str) -> str | None:
    key_to_col = {_norm_col_key(c): c for c in df.columns}
    for a in aliases:
        k = _norm_col_key(a)
        if k in key_to_col:
            return key_to_col[k]
    return None


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

    id_col = _pick_column(df, "ID #", "ID", "Equipment ID", "EquipmentId")
    cost_col = _pick_column(df, "Cost", "Purch. Cost", "Purchase Cost")
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

    id_col = _pick_column(df_service, "Equipment Id", "Equipment ID", "equipId")
    price_col = _pick_column(
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
PRICE_SOURCE_SERVICE = "service"
PRICE_SOURCE_NONE = ""

PRICE_SOURCE_LABEL = {
    PRICE_SOURCE_PURCHASE: "Accurate",
    PRICE_SOURCE_SERVICE: "Estimated",
    PRICE_SOURCE_NONE: "—",
}

PRICE_BASIS_COLUMN = "Price basis"
PRICE_BASIS_TOOLTIP = "Recorded purchase cost when ID matches; otherwise service estimate."


def resolve_price_source(
    equip_id,
    purchase_map: dict[str, float],
    service_map: dict[str, float],
) -> str:
    """``purchase`` when cost comes from purchase.csv; ``service`` when estimated."""
    eid = norm_equip_id(equip_id)
    if eid and eid in purchase_map:
        return PRICE_SOURCE_PURCHASE
    if eid and eid in service_map:
        return PRICE_SOURCE_SERVICE
    return PRICE_SOURCE_NONE


def resolve_new_price(
    equip_id,
    purchase_map: dict[str, float],
    service_map: dict[str, float],
) -> float:
    """Purchase cost when ID matches; otherwise service estimate; else 0."""
    eid = norm_equip_id(equip_id)
    if eid and eid in purchase_map:
        return purchase_map[eid]
    if eid and eid in service_map:
        return service_map[eid]
    return 0.0


def apply_new_prices_to_repairs(
    df: pd.DataFrame,
    purchase_map: dict[str, float],
    service_map: dict[str, float],
) -> pd.DataFrame:
    if df.empty:
        out = df.copy()
        out["newPrice"] = pd.Series(dtype=float)
        out["priceSource"] = pd.Series(dtype=str)
        return out
    out = df.copy()
    out["newPrice"] = out["equipId"].map(
        lambda x: resolve_new_price(x, purchase_map, service_map)
    )
    out["priceSource"] = out["equipId"].map(
        lambda x: resolve_price_source(x, purchase_map, service_map)
    )
    return out

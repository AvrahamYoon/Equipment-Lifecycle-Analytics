"""Equipment replacement indicator table from **cumulative** repair aggregates.

Callers should pass every repair row to aggregate (typically all months loaded
from disk); the dashboard wires this independently of the header month filter.
"""

import pandas as pd

from dashboard import constants as C
from valuation import PRICE_BASIS_COLUMN, PRICE_SOURCE_LABEL
from dashboard.logic.buildings import normalize_building_value
from dashboard.logic.repair_count_bins import equip_ids_for_repair_count_bin

_MARKDOWN_COLS = frozenset({"Status", PRICE_BASIS_COLUMN})

_STATUS_PILL_HTML = {
    "Replace": '<span class="fm-pill fm-pill--replace">Replace</span>',
    "Monitor": '<span class="fm-pill fm-pill--monitor">Monitor</span>',
    "Good": '<span class="fm-pill fm-pill--good">Good</span>',
}

_BASIS_PILL_HTML = {
    "Accurate": '<span class="fm-pill fm-pill--accurate">Accurate</span>',
    "Valuation": '<span class="fm-pill fm-pill--valuation">Valuation</span>',
    "Estimated": '<span class="fm-pill fm-pill--estimated">Estimated</span>',
    "—": '<span class="fm-pill fm-pill--unknown">—</span>',
}

from dashboard.logic.overview.settings_merge import merge_app_settings
from dashboard.taxonomy import ensure_equip_id_norm_column, equipment_chart_class, filter_equip_id_substr


def _pick_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def build_replacement_table(rep: pd.DataFrame, app_settings=None, filters=None):
    """Returns (columns, records, style_data_conditional) for Dash DataTable."""
    merge_app_settings(app_settings)
    filters = filters or {}

    rep = ensure_equip_id_norm_column(rep, raw_col="equipId", norm_col="equipIdNorm")
    rep = rep[rep["equipIdNorm"].astype(str).str.len() > 0]
    building_col = _pick_col(rep, ("location", "Location", "building", "Building", "site", "Site"))
    if building_col:
        rep["_building_norm"] = rep[building_col].map(normalize_building_value)
    else:
        rep["_building_norm"] = ""

    cat_f = (filters.get("category") or "").strip()
    if cat_f:
        if "equipCategory" in rep.columns:
            rep = rep[rep["equipCategory"].astype(str) == cat_f]
        else:
            rep = rep[rep["equipment"].astype(str).map(equipment_chart_class) == cat_f]

    bld_f = (filters.get("building") or "").strip()
    if bld_f:
        rep = rep[rep["_building_norm"].astype(str) == bld_f]

    bin_f = (filters.get("repair_count_bin") or "").strip()
    if bin_f:
        allowed = equip_ids_for_repair_count_bin(rep, bin_f)
        if not allowed:
            rep = rep.iloc[0:0]
        else:
            rep = rep[rep["equipIdNorm"].astype(str).isin(allowed)]

    group_col = "equipIdNorm"

    agg_cols = {
        "equipment": ("equipment", "first"),
        "equipId": (group_col, "first"),
        "building": ("_building_norm", "first"),
        "newPrice": ("newPrice", "first"),
        "parts": ("parts", "sum"),
        "labor": ("labor", "sum"),
    }
    if "priceSource" in rep.columns:
        agg_cols["priceSource"] = ("priceSource", "first")
    agg = rep.groupby(group_col, dropna=False).agg(**agg_cols).reset_index(drop=True)
    if "priceSource" not in agg.columns:
        agg["priceSource"] = ""

    agg["Total Cost"] = agg["labor"] + agg["parts"]
    # Dollar cutoffs = that percentage of *estimated new equipment price*
    agg["80% of new price"] = agg["newPrice"] * 0.80
    agg["60% of new price"] = agg["newPrice"] * 0.60
    agg["Status"] = agg.apply(
        lambda r: C.replace_status(r["labor"], r["parts"], r["newPrice"]),
        axis=1,
    )

    st_f = (filters.get("status") or "All").strip()
    if st_f and st_f != "All":
        agg = agg[agg["Status"] == st_f]

    eq_sub = (filters.get("equipment_substr") or "").strip().lower()
    if eq_sub:
        agg = agg[agg["equipment"].astype(str).str.lower().str.contains(eq_sub, na=False)]

    id_sub = (filters.get("id_substr") or "").strip()
    if id_sub:
        agg = agg[filter_equip_id_substr(agg["equipId"], id_sub)]

    agg = agg.sort_values("Status")

    agg["priceSource"] = agg["priceSource"].map(
        lambda s: PRICE_SOURCE_LABEL.get(str(s).strip() if pd.notna(s) else "", "—")
    )

    table_data = agg.rename(
        columns={
            "equipment": "Equipment",
            "equipId": "ID",
            "building": "Building",
            "newPrice": "New Price",
            "priceSource": PRICE_BASIS_COLUMN,
            "parts": "Parts Cost",
            "labor": "Labor Cost",
        }
    )[
        [
            "Status",
            "Equipment",
            "ID",
            "Building",
            "Parts Cost",
            "Labor Cost",
            "Total Cost",
            "New Price",
            PRICE_BASIS_COLUMN,
            "80% of new price",
            "60% of new price",
        ]
    ].copy()

    for col in [
        "Parts Cost",
        "Labor Cost",
        "Total Cost",
        "New Price",
        "80% of new price",
        "60% of new price",
    ]:
        table_data[col] = table_data[col].apply(lambda x: f"${x:,.2f}")

    records = table_data.to_dict("records")
    columns = []
    for c in table_data.columns:
        col = {"name": c, "id": c}
        if c in _MARKDOWN_COLS:
            col["presentation"] = "markdown"
        columns.append(col)

    for r in records:
        s = r.get("Status", "Good")
        r["Status"] = _STATUS_PILL_HTML.get(s, _STATUS_PILL_HTML["Good"])
        pb = r.get(PRICE_BASIS_COLUMN, "—")
        r[PRICE_BASIS_COLUMN] = _BASIS_PILL_HTML.get(pb, _BASIS_PILL_HTML["—"])

    cond_style = []
    cond_style.append(
        {
            "if": {"column_id": "New Price"},
            "fontWeight": "600",
            "color": "#0f172a",
        }
    )
    cond_style.append(
        {
            "if": {"column_id": "Total Cost"},
            "fontWeight": "600",
        }
    )

    return columns, records, cond_style

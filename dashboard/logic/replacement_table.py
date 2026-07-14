"""Equipment replacement indicator table from **cumulative** repair aggregates.

Callers should pass every repair row to aggregate (typically all months loaded
from disk); the dashboard wires this independently of the header month filter.
"""

import pandas as pd

from dashboard import constants as C
from dashboard import data_loaders as loaders
from valuation import PRICE_BASIS_COLUMN, PRICE_SOURCE_LABEL
from dashboard.logic.buildings import display_building_name, normalize_building_value
from dashboard.logic.depreciation import (
    DEP_BASIS_COLUMN,
    DEP_BASIS_CONFIRMED,
    DEP_BASIS_ESTIMATED,
    DEP_BASIS_MANUAL,
    DEP_BASIS_UNKNOWN,
    extend_depreciation_result,
    format_depreciation_months,
    life_replace_status,
    resolve_depreciation,
)
from dashboard.logic.life_overrides import format_life_adj
from dashboard.logic.repair_count_bins import equip_ids_for_repair_count_bin

_MARKDOWN_COLS = frozenset({"Status", PRICE_BASIS_COLUMN, DEP_BASIS_COLUMN})

_STATUS_PILL_HTML = {
    "Replace": '<span class="fm-pill fm-pill--replace">Replace</span>',
    "Monitor": '<span class="fm-pill fm-pill--monitor">Monitor</span>',
    "Good": '<span class="fm-pill fm-pill--good">Good</span>',
}

_BASIS_PILL_HTML = {
    "Accurate": '<span class="fm-pill fm-pill--accurate">Accurate</span>',
    "Catalog": '<span class="fm-pill fm-pill--valuation">Catalog</span>',
    "Valuation": '<span class="fm-pill fm-pill--valuation">Valuation</span>',
    "Estimated": '<span class="fm-pill fm-pill--estimated">Estimated</span>',
    "—": '<span class="fm-pill fm-pill--unknown">—</span>',
}

_DEP_BASIS_PILL_HTML = {
    DEP_BASIS_CONFIRMED: '<span class="fm-pill fm-pill--accurate">Confirmed</span>',
    DEP_BASIS_ESTIMATED: '<span class="fm-pill fm-pill--estimated">Estimated</span>',
    DEP_BASIS_MANUAL: '<span class="fm-pill fm-pill--valuation">Manual</span>',
    DEP_BASIS_UNKNOWN: '<span class="fm-pill fm-pill--unknown">—</span>',
}

from dashboard.logic.overview.settings_merge import merge_app_settings
from dashboard.taxonomy import ensure_equip_id_norm_column, equipment_chart_class, filter_equip_id_substr, norm_equip_id


def _pick_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def build_replacement_table(rep: pd.DataFrame, app_settings=None, filters=None, life_overrides=None):
    """Returns (columns, records, style_data_conditional) for Dash DataTable."""
    merge_app_settings(app_settings)
    filters = filters or {}
    if life_overrides is None:
        from dashboard.data_loaders import _life_overrides

        life_overrides = _life_overrides

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
    if "equipCategory" in rep.columns:
        agg_cols["equipCategory"] = ("equipCategory", "first")
    agg = rep.groupby(group_col, dropna=False).agg(**agg_cols).reset_index(drop=True)
    if "priceSource" not in agg.columns:
        agg["priceSource"] = ""

    agg["Total Cost"] = agg["labor"] + agg["parts"]

    dep_stats = loaders._purchase_depreciation_stats
    equip_meta = loaders._equip_meta_lookup

    def _depreciation_row(r):
        equip_type = ""
        if "equipCategory" in r.index and pd.notna(r.get("equipCategory")):
            equip_type = str(r["equipCategory"])
        res = resolve_depreciation(
            r["equipId"],
            str(r.get("equipment") or ""),
            equip_type=equip_type,
            new_price=r.get("newPrice"),
            stats=dep_stats,
            equip_meta=equip_meta,
        )
        eid = norm_equip_id(r["equipId"])
        override = life_overrides.get(eid) if life_overrides else None
        extra_months = override.extra_months if override else 0.0
        if extra_months > 0:
            res = extend_depreciation_result(res, extra_months, new_price=r.get("newPrice"))
        return pd.Series(
            {
                "age_months": res.age_months,
                "useful_life_months": res.useful_life_months,
                "book_value": res.book_value,
                "basis_label": res.basis_label,
                "life_adj": extra_months,
            }
        )

    dep = agg.apply(_depreciation_row, axis=1)
    agg["Age (mo)"] = dep["age_months"]
    agg["Useful Life (mo)"] = dep["useful_life_months"]
    agg["Book Value"] = dep["book_value"]
    agg[DEP_BASIS_COLUMN] = dep["basis_label"]
    agg["life_adj_months"] = dep["life_adj"]

    agg["Status"] = agg.apply(
        lambda r: C.combine_replace_status(
            C.replace_status(r["labor"], r["parts"], r["newPrice"]),
            life_replace_status(r["Age (mo)"], r["Useful Life (mo)"]),
        ),
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

    agg["building_display"] = agg["building"].map(display_building_name)
    agg["Life adj."] = agg["life_adj_months"].map(format_life_adj)

    table_data = agg.rename(
        columns={
            "equipment": "Equipment",
            "equipId": "ID",
            "building_display": "Building",
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
            "Age (mo)",
            "Useful Life (mo)",
            "Life adj.",
            "Book Value",
            DEP_BASIS_COLUMN,
        ]
    ].copy()

    for col in ("Age (mo)", "Useful Life (mo)"):
        table_data[col] = table_data[col].map(format_depreciation_months)
    table_data["Book Value"] = table_data["Book Value"].apply(
        lambda x: f"${x:,.2f}" if pd.notna(x) else "—"
    )

    for col in [
        "Parts Cost",
        "Labor Cost",
        "Total Cost",
        "New Price",
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
        db = r.get(DEP_BASIS_COLUMN, DEP_BASIS_UNKNOWN)
        r[DEP_BASIS_COLUMN] = _DEP_BASIS_PILL_HTML.get(db, _DEP_BASIS_PILL_HTML[DEP_BASIS_UNKNOWN])

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

    cond_style.append(
        {
            "if": {"column_id": "Book Value"},
            "fontWeight": "600",
            "color": "#0f172a",
        }
    )

    return columns, records, cond_style


def replacement_life_editor_context(
    equip_id,
    equipment_name: str,
    *,
    equip_type: str = "",
    new_price=None,
    labor=0,
    parts=0,
    life_overrides=None,
):
    """Base vs extended life and status signals for the manual-life editor panel."""
    from dashboard.data_loaders import _equip_meta_lookup, _purchase_depreciation_stats

    if life_overrides is None:
        from dashboard.data_loaders import _life_overrides

        life_overrides = _life_overrides

    base = resolve_depreciation(
        equip_id,
        equipment_name or "",
        equip_type=equip_type,
        new_price=new_price,
        stats=_purchase_depreciation_stats,
        equip_meta=_equip_meta_lookup,
    )
    eid = norm_equip_id(equip_id)
    override = life_overrides.get(eid) if life_overrides else None
    extra = override.extra_months if override else 0.0
    effective = (
        extend_depreciation_result(base, extra, new_price=new_price)
        if extra > 0
        else base
    )

    repair_status = C.replace_status(labor, parts, new_price)
    base_life_status = life_replace_status(base.age_months, base.useful_life_months)
    effective_life_status = life_replace_status(
        effective.age_months, effective.useful_life_months
    )
    combined = C.combine_replace_status(repair_status, effective_life_status)

    return {
        "equip_id": eid,
        "equipment_name": equipment_name or "",
        "base_useful_life_months": base.useful_life_months,
        "effective_useful_life_months": effective.useful_life_months,
        "age_months": base.age_months,
        "extra_months": extra,
        "note": override.note if override else "",
        "review_by": override.review_by if override else "",
        "repair_status": repair_status,
        "base_life_status": base_life_status,
        "effective_life_status": effective_life_status,
        "combined_status": combined,
        "base_useful_life_label": format_depreciation_months(base.useful_life_months),
        "effective_useful_life_label": format_depreciation_months(
            effective.useful_life_months
        ),
        "age_label": format_depreciation_months(base.age_months),
    }

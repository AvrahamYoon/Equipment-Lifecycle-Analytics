"""Equipment replacement indicator table from **cumulative** repair aggregates.

Callers should pass every repair row to aggregate (typically all months loaded
from disk); the dashboard wires this independently of the header month filter.
"""

import pandas as pd

from dashboard import constants as C
from dashboard.equipment_pricing import PRICE_BASIS_COLUMN, PRICE_SOURCE_LABEL
from dashboard.logic.overview.settings_merge import merge_app_settings, replace_status_icons


def build_replacement_table(rep: pd.DataFrame, app_settings=None, filters=None):
    """Returns (columns, records, style_data_conditional) for Dash DataTable."""
    merged = merge_app_settings(app_settings)
    ico = replace_status_icons(merged)
    filters = filters or {}

    agg_cols = {
        "equipment": ("equipment", "first"),
        "equipId": ("equipId", "first"),
        "newPrice": ("newPrice", "first"),
        "parts": ("parts", "sum"),
        "labor": ("labor", "sum"),
    }
    if "priceSource" in rep.columns:
        agg_cols["priceSource"] = ("priceSource", "first")
    agg = rep.groupby("equipId").agg(**agg_cols).reset_index(drop=True)
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

    id_sub = (filters.get("id_substr") or "").strip().lower()
    if id_sub:
        agg = agg[agg["equipId"].astype(str).str.lower().str.contains(id_sub, na=False)]

    agg = agg.sort_values("Status")

    agg["priceSource"] = agg["priceSource"].map(
        lambda s: PRICE_SOURCE_LABEL.get(str(s).strip() if pd.notna(s) else "", "—")
    )

    table_data = agg.rename(
        columns={
            "equipment": "Equipment",
            "equipId": "ID",
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
    columns = [{"name": c, "id": c} for c in table_data.columns]

    status_styles = {
        "Replace": {
            "bg": "#fef2f2",
            "color": "#dc2626",
            "badge": f'{ico["Replace"]} Replace',
        },
        "Monitor": {
            "bg": "#fffbeb",
            "color": "#d97706",
            "badge": f'{ico["Monitor"]} Monitor',
        },
        "Good": {
            "bg": "#f0fdf4",
            "color": "#059669",
            "badge": f'{ico["Good"]} Good',
        },
    }

    price_basis_styles = {
        "Accurate": {
            "badge": "Accurate",
            "cell": {
                "backgroundColor": "#ecfdf5",
                "color": "#047857",
                "fontWeight": "700",
                "border": "1px solid #a7f3d0",
                "borderRadius": "999px",
            },
        },
        "Estimated": {
            "badge": "Estimated",
            "cell": {
                "backgroundColor": "#fffbeb",
                "color": "#b45309",
                "fontWeight": "700",
                "border": "1px solid #fde68a",
                "borderRadius": "999px",
            },
        },
        "—": {
            "badge": "—",
            "cell": {
                "color": C.COLOR_TEXT_MUTED,
                "fontWeight": "500",
            },
        },
    }

    for r in records:
        s = r.get("Status", "Good")
        r["Status"] = status_styles.get(s, status_styles["Good"])["badge"]
        pb = r.get(PRICE_BASIS_COLUMN, "—")
        r[PRICE_BASIS_COLUMN] = price_basis_styles.get(pb, price_basis_styles["—"])["badge"]

    cond_style = []
    for label, style in price_basis_styles.items():
        badge = style["badge"]
        cond_style.append(
            {
                "if": {
                    "filter_query": f'{{{PRICE_BASIS_COLUMN}}} = "{badge}"',
                    "column_id": PRICE_BASIS_COLUMN,
                },
                **style["cell"],
            }
        )
    for status, style in status_styles.items():
        badge = style["badge"]
        cond_style.append(
            {
                "if": {"filter_query": f'{{Status}} = "{badge}"'},
                "backgroundColor": style["bg"],
            }
        )
        cond_style.append(
            {
                "if": {"filter_query": f'{{Status}} = "{badge}"', "column_id": "Status"},
                "color": style["color"],
                "fontWeight": "700",
            }
        )
    cond_style.append(
        {
            "if": {"row_index": "odd"},
            "backgroundColor": "#fafbfc",
        }
    )

    return columns, records, cond_style

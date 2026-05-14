"""Equipment replacement indicator table from repair aggregates."""

import pandas as pd

from dashboard import constants as C
from dashboard.logic.overview.settings_merge import merge_app_settings, replace_status_icons


def build_replacement_table(rep: pd.DataFrame, app_settings=None, filters=None):
    """Returns (columns, records, style_data_conditional) for Dash DataTable."""
    merged = merge_app_settings(app_settings)
    ico = replace_status_icons(merged)
    filters = filters or {}

    agg = rep.groupby("equipId").agg(
        equipment=("equipment", "first"),
        equipId=("equipId", "first"),
        newPrice=("newPrice", "first"),
        parts=("parts", "sum"),
        labor=("labor", "sum"),
    ).reset_index(drop=True)

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

    table_data = agg.rename(
        columns={
            "equipment": "Equipment",
            "equipId": "ID",
            "newPrice": "New Price",
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

    for r in records:
        s = r.get("Status", "Good")
        r["Status"] = status_styles.get(s, status_styles["Good"])["badge"]

    cond_style = []
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

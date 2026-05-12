"""Equipment replacement indicator table from repair aggregates."""

import pandas as pd

from dashboard import constants as C


def build_replacement_table(rep: pd.DataFrame):
    """Returns (columns, records, style_data_conditional) for Dash DataTable."""
    agg = rep.groupby("equipId").agg(
        equipment=("equipment", "first"),
        equipId=("equipId", "first"),
        newPrice=("newPrice", "first"),
        parts=("parts", "sum"),
        labor=("labor", "sum"),
    ).reset_index(drop=True)

    agg["Total Cost"] = agg["labor"] + agg["parts"]
    agg["80% Threshold"] = agg["Total Cost"] * 0.80
    agg["60% Threshold"] = agg["Total Cost"] * 0.60
    agg["Status"] = agg.apply(
        lambda r: C.replace_status(r["labor"], r["parts"], r["newPrice"]),
        axis=1,
    )
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
            "80% Threshold",
            "60% Threshold",
        ]
    ].copy()

    for col in [
        "Parts Cost",
        "Labor Cost",
        "Total Cost",
        "New Price",
        "80% Threshold",
        "60% Threshold",
    ]:
        table_data[col] = table_data[col].apply(lambda x: f"${x:,.2f}")

    records = table_data.to_dict("records")
    columns = [{"name": c, "id": c} for c in table_data.columns]

    status_styles = {
        "Replace": {"bg": "#fef2f2", "color": "#dc2626", "badge": "🔴 Replace"},
        "Monitor": {"bg": "#fffbeb", "color": "#d97706", "badge": "🟡 Monitor"},
        "Good": {"bg": "#f0fdf4", "color": "#059669", "badge": "🟢 Good"},
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

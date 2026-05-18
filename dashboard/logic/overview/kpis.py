"""Overview KPI row."""

import pandas as pd
from dash import html

from dashboard import constants as C


def kpi_card(label, value, icon, accent):
    return html.Div(
        [
            html.Div(
                [
                    html.Div(icon, style={"fontSize": 22, "lineHeight": 1}),
                    html.Div(
                        style={
                            "width": 8,
                            "height": 8,
                            "borderRadius": "50%",
                            "background": accent,
                            "marginLeft": "auto",
                            "boxShadow": f"0 0 0 3px {accent}22",
                        }
                    ),
                ],
                style={"display": "flex", "alignItems": "center", "marginBottom": 14},
            ),
            html.Div(str(value), className="kpi-value"),
            html.Div(label, className="kpi-label"),
            html.Div(
                style={
                    "height": 3,
                    "borderRadius": 999,
                    "background": f"linear-gradient(90deg, {accent}, {accent}55)",
                    "marginTop": 16,
                }
            ),
        ],
        className="kpi-card lift-on-hover",
        style={
            **C.CARD_STYLE,
            "padding": "20px 20px 16px",
            "minWidth": 140,
            "flex": "1",
            "borderTop": f"3px solid {accent}",
        },
    )


def build_kpi_children(
    req: pd.DataFrame,
    svc: pd.DataFrame,
    rep: pd.DataFrame,
    kpi_icons: list[str],
):
    total_req = len(req)
    total_completed = (svc["Status"].str.strip().str.lower() == "completed").sum()
    total_scheduled = (svc["Status"].str.strip().str.lower() == "scheduled").sum()
    total_parts = rep["parts"].sum()
    total_labor = rep["labor"].sum()
    total_repair = rep["total"].sum()
    total_svc = total_completed + total_scheduled

    icons = list(kpi_icons)
    while len(icons) < 6:
        icons.append("")
    icons = icons[:6]

    return [
        kpi_card("Total Requests", total_req, icons[0], C.C_BLUE),
        kpi_card("Completed / Total", f"{total_completed}/{total_svc}", icons[1], C.C_GREEN),
        kpi_card("Scheduled", total_scheduled, icons[2], C.C_PURPLE),
        kpi_card("Total Repair Cost", f"${total_repair:,.2f}", icons[3], C.C_ORANGE),
        kpi_card("Parts Cost", f"${total_parts:,.2f}", icons[4], C.C_YELLOW),
        kpi_card("Labor Cost", f"${total_labor:,.2f}", icons[5], C.C_PINK),
    ]

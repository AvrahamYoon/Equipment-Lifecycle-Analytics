"""Overview KPI row."""

import pandas as pd
from dash import html

from dashboard import constants as C


def kpi_card(label, value, icon, accent):
    return html.Div(
        [
            html.Div(
                [
                    html.Div(icon, style={"fontSize": 20}),
                    html.Div(
                        style={
                            "width": 6,
                            "height": 6,
                            "borderRadius": "50%",
                            "background": accent,
                            "marginLeft": "auto",
                        }
                    ),
                ],
                style={"display": "flex", "alignItems": "center", "marginBottom": 12},
            ),
            html.Div(
                str(value),
                style={
                    "fontSize": 26,
                    "fontWeight": 800,
                    "color": C.COLOR_TEXT_PRIMARY,
                    "lineHeight": 1,
                },
            ),
            html.Div(
                label,
                style={
                    "fontSize": 11,
                    "color": C.COLOR_TEXT_SECONDARY,
                    "fontWeight": 600,
                    "textTransform": "uppercase",
                    "letterSpacing": "0.05em",
                    "marginTop": 6,
                },
            ),
            html.Div(
                style={
                    "height": 3,
                    "borderRadius": 2,
                    "background": accent,
                    "marginTop": 14,
                    "opacity": 0.7,
                }
            ),
        ],
        style={
            **C.CARD_STYLE,
            "padding": "18px 18px 14px",
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

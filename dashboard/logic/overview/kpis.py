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


def compute_kpi_values(
    req: pd.DataFrame,
    svc: pd.DataFrame,
    rep: pd.DataFrame,
) -> list[tuple[str, str]]:
    """Label/value pairs for KPI summary tables and PDF export."""
    total_req = len(req)
    total_completed = (svc["Status"].str.strip().str.lower() == "completed").sum()
    total_scheduled = (svc["Status"].str.strip().str.lower() == "scheduled").sum()
    total_parts = rep["parts"].sum()
    total_labor = rep["labor"].sum()
    total_repair = rep["total"].sum()
    total_svc = total_completed + total_scheduled
    return [
        ("Total Requests", f"{total_req:,}"),
        ("Completed / Total", f"{total_completed:,}/{total_svc:,}"),
        ("Scheduled", f"{total_scheduled:,}"),
        ("Total Repair Cost", f"${total_repair:,.2f}"),
        ("Parts Cost", f"${total_parts:,.2f}"),
        ("Labor Cost", f"${total_labor:,.2f}"),
    ]


def build_kpi_children(
    req: pd.DataFrame,
    svc: pd.DataFrame,
    rep: pd.DataFrame,
    kpi_icons: list[str],
):
    icons = list(kpi_icons)
    while len(icons) < 6:
        icons.append("")
    icons = icons[:6]
    accents = [C.C_BLUE, C.C_GREEN, C.C_PURPLE, C.C_ORANGE, C.C_YELLOW, C.C_PINK]
    return [
        kpi_card(label, value, icons[i], accents[i])
        for i, (label, value) in enumerate(compute_kpi_values(req, svc, rep))
    ]

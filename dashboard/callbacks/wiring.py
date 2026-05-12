"""Register Dash callbacks."""

from dash import Input, Output

from dashboard import constants as C
from dashboard.data_loaders import (
    df_equip,
    df_req,
    df_repairs,
    df_service,
)
from dashboard.logic.overview_charts import build_overview
from dashboard.logic.replacement_table import build_replacement_table


def register_callbacks(app):
    @app.callback(
        Output("page-overview", "style"),
        Output("page-replacement", "style"),
        Output("nav-wrap-overview", "style"),
        Output("nav-wrap-replacement", "style"),
        Input("url", "pathname"),
    )
    def route_pages(pathname):
        if pathname in (None, ""):
            pathname = "/"
        page = {
            "padding": "24px 28px",
            "maxWidth": 1400,
            "margin": "0 auto",
            "flex": "1",
            "minWidth": 0,
        }
        on_rep = pathname == "/replacement"
        ov_style = {**page, "display": "none" if on_rep else "block"}
        rp_style = {**page, "display": "block" if on_rep else "none"}

        def wrap(active: bool):
            return {
                "padding": "10px 14px",
                "borderRadius": 8,
                "marginBottom": 4,
                "background": "#e8f1fe" if active else "transparent",
                "color": C.COLOR_TEXT_PRIMARY if active else C.COLOR_TEXT_SECONDARY,
                "fontWeight": 700 if active else 500,
                "fontSize": 14,
            }

        return ov_style, rp_style, wrap(not on_rep), wrap(on_rep)

    @app.callback(
        Output("kpi-row", "children"),
        Output("hours-chart", "figure"),
        Output("calendar-chart", "figure"),
        Output("completion-gauge", "figure"),
        Output("avghours-gauge", "figure"),
        Output("staff-chart", "figure"),
        Output("turnaround-chart", "figure"),
        Output("availability-chart", "figure"),
        Output("footer-text", "children"),
        Input("month-select", "value"),
    )
    def update_overview(month_key):
        req = df_req[df_req["month_key"] == month_key]
        svc = df_service[df_service["month_key"] == month_key]
        rep = df_repairs[df_repairs["month_key"] == month_key]
        return build_overview(month_key, req, svc, rep, df_equip)

    @app.callback(
        Output("replace-table", "columns"),
        Output("replace-table", "data"),
        Output("replace-table", "style_data_conditional"),
        Input("month-select", "value"),
    )
    def update_replacement(month_key):
        rep = df_repairs[df_repairs["month_key"] == month_key]
        return build_replacement_table(rep)

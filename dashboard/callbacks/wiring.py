"""Register Dash callbacks."""

from dash import Input, Output, State, callback_context
from dash.exceptions import PreventUpdate

from dashboard import constants as C
from dashboard.data_loaders import (
    df_equip,
    df_req,
    df_repairs,
    df_service,
)
from dashboard.logic.overview import build_overview
from dashboard.logic.overview.settings_merge import merge_app_settings, staff_capacity_for_month, sanitise_capacity_triple
from dashboard.logic.replacement_table import build_replacement_table


def register_callbacks(app):
    @app.callback(
        Output("page-overview", "style"),
        Output("page-replacement", "style"),
        Output("page-settings", "style"),
        Output("nav-wrap-overview", "style"),
        Output("nav-wrap-replacement", "style"),
        Output("nav-wrap-settings", "style"),
        Input("url", "pathname"),
    )
    def route_pages(pathname):
        if pathname in (None, ""):
            pathname = "/"
        on_rep = pathname == "/replacement"
        on_set = pathname == "/settings"
        page = {
            "padding": "24px 28px",
            "maxWidth": 1240,
            "margin": "0 auto",
            "minWidth": 0,
        }

        def nav_left(active: bool):
            return {
                "padding": "10px 14px",
                "borderRadius": 8,
                "marginBottom": 4,
                "background": "#e8f1fe" if active else "transparent",
                "color": C.COLOR_TEXT_PRIMARY if active else C.COLOR_TEXT_SECONDARY,
                "fontWeight": 700 if active else 500,
                "fontSize": 14,
            }

        ov_style = {**page, "display": "block" if (not on_rep and not on_set) else "none"}
        rp_style = {**page, "display": "block" if on_rep else "none"}
        st_style = {**page, "display": "block" if on_set else "none"}

        return (
            ov_style,
            rp_style,
            st_style,
            nav_left(not on_rep and not on_set),
            nav_left(on_rep),
            nav_left(on_set),
        )

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
        Input("settings-store", "data"),
    )
    def update_overview(month_key, settings_data):
        req = df_req[df_req["month_key"] == month_key]
        svc = df_service[df_service["month_key"] == month_key]
        rep = df_repairs[df_repairs["month_key"] == month_key]
        return build_overview(month_key, req, svc, rep, df_equip, settings_data)

    @app.callback(
        Output("replace-table", "columns"),
        Output("replace-table", "data"),
        Output("replace-table", "style_data_conditional"),
        Input("month-select", "value"),
        Input("settings-store", "data"),
    )
    def update_replacement(month_key, settings_data):
        rep = df_repairs[df_repairs["month_key"] == month_key]
        return build_replacement_table(rep, settings_data)

    @app.callback(
        Output("nav-icon-overview", "children"),
        Output("nav-icon-replacement", "children"),
        Output("nav-icon-settings", "children"),
        Output("replace-page-title-icon", "children"),
        Output("replace-legend-ico-replace", "children"),
        Output("replace-legend-ico-monitor", "children"),
        Output("replace-legend-ico-good", "children"),
        Input("settings-store", "data"),
    )
    def sync_chrome_icons(data):
        m = merge_app_settings(data)
        return (
            m["iconNavOverview"],
            m["iconNavReplacement"],
            m["iconNavSettings"],
            m["iconReplaceTitle"],
            m["iconReplaceStatusReplace"],
            m["iconReplaceStatusMonitor"],
            m["iconReplaceStatusGood"],
        )

    @app.callback(
        Output("settings-store", "data"),
        Input("settings-apply", "n_clicks"),
        Input("settings-reset", "n_clicks"),
        State("settings-staff-count", "value"),
        State("settings-hours-day", "value"),
        State("settings-work-days", "value"),
        State("settings-base-avail", "value"),
        State("settings-week-starts", "value"),
        State("settings-iconKpiRequests", "value"),
        State("settings-iconKpiCompleted", "value"),
        State("settings-iconKpiScheduled", "value"),
        State("settings-iconKpiRepairCost", "value"),
        State("settings-iconKpiParts", "value"),
        State("settings-iconKpiLabor", "value"),
        State("settings-iconNavOverview", "value"),
        State("settings-iconNavReplacement", "value"),
        State("settings-iconNavSettings", "value"),
        State("settings-iconReplaceTitle", "value"),
        State("settings-iconReplaceStatusReplace", "value"),
        State("settings-iconReplaceStatusMonitor", "value"),
        State("settings-iconReplaceStatusGood", "value"),
        State("settings-store", "data"),
        State("month-select", "value"),
        prevent_initial_call=True,
    )
    def persist_settings(
        apply_n,
        reset_n,
        staff,
        hours,
        days,
        base_avail,
        week_val,
        ik_req,
        ik_comp,
        ik_sched,
        ik_cost,
        ik_parts,
        ik_labor,
        in_ov,
        in_rep,
        in_set,
        ir_title,
        ir_rep,
        ir_mon,
        ir_good,
        current_store,
        month_key,
    ):
        triggered = [t["prop_id"] for t in callback_context.triggered if t["prop_id"] != "."]
        if not triggered:
            raise PreventUpdate
        tid = triggered[0].split(".")[0]
        if tid == "settings-reset":
            return C.default_app_settings()
        if tid != "settings-apply":
            raise PreventUpdate
        base = merge_app_settings(current_store or {})
        by_m = dict(base.get("staffCapacityByMonth") or {})
        sc, hd, wd = sanitise_capacity_triple(staff, hours, days)
        if month_key is not None:
            mks = str(month_key).strip()
            if mks and mks not in ("None", "nan", "NaT"):
                by_m[mks] = {"staffCount": sc, "hoursPerDay": hd, "workDays": wd}
        patch = {
            "staffCount": sc,
            "hoursPerDay": hd,
            "workDays": wd,
            "baseAvailDays": base_avail,
            "weekStartsOn": week_val or "sunday",
            "iconKpiRequests": ik_req,
            "iconKpiCompleted": ik_comp,
            "iconKpiScheduled": ik_sched,
            "iconKpiRepairCost": ik_cost,
            "iconKpiParts": ik_parts,
            "iconKpiLabor": ik_labor,
            "iconNavOverview": in_ov,
            "iconNavReplacement": in_rep,
            "iconNavSettings": in_set,
            "iconReplaceTitle": ir_title,
            "iconReplaceStatusReplace": ir_rep,
            "iconReplaceStatusMonitor": ir_mon,
            "iconReplaceStatusGood": ir_good,
            "staffCapacityByMonth": by_m,
        }
        return merge_app_settings({**base, **patch})

    @app.callback(
        Output("settings-staff-count", "value"),
        Output("settings-hours-day", "value"),
        Output("settings-work-days", "value"),
        Output("settings-base-avail", "value"),
        Output("settings-week-starts", "value"),
        Output("settings-iconKpiRequests", "value"),
        Output("settings-iconKpiCompleted", "value"),
        Output("settings-iconKpiScheduled", "value"),
        Output("settings-iconKpiRepairCost", "value"),
        Output("settings-iconKpiParts", "value"),
        Output("settings-iconKpiLabor", "value"),
        Output("settings-iconNavOverview", "value"),
        Output("settings-iconNavReplacement", "value"),
        Output("settings-iconNavSettings", "value"),
        Output("settings-iconReplaceTitle", "value"),
        Output("settings-iconReplaceStatusReplace", "value"),
        Output("settings-iconReplaceStatusMonitor", "value"),
        Output("settings-iconReplaceStatusGood", "value"),
        Input("url", "pathname"),
        Input("settings-store", "data"),
        Input("month-select", "value"),
    )
    def sync_settings_form(pathname, data, month_key):
        if pathname in (None, ""):
            pathname = "/"
        if pathname != "/settings":
            raise PreventUpdate
        m = merge_app_settings(data)
        sc, hd, wd = staff_capacity_for_month(m, month_key)
        return (
            sc,
            hd,
            wd,
            m["baseAvailDays"],
            m["weekStartsOn"],
            m["iconKpiRequests"],
            m["iconKpiCompleted"],
            m["iconKpiScheduled"],
            m["iconKpiRepairCost"],
            m["iconKpiParts"],
            m["iconKpiLabor"],
            m["iconNavOverview"],
            m["iconNavReplacement"],
            m["iconNavSettings"],
            m["iconReplaceTitle"],
            m["iconReplaceStatusReplace"],
            m["iconReplaceStatusMonitor"],
            m["iconReplaceStatusGood"],
        )

"""Register Dash callbacks."""

from dash import Input, Output, State, callback_context, html
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
from dashboard.logic.repair_orders_table import build_repair_orders_table, repair_order_filter_options
from dashboard.logic.replacement_table import build_replacement_table


def _format_row_count(filtered: int, total: int, item_singular: str):
    """Build the 'Showing X of Y …' children for the row-count pill.

    Returns a list of Dash components so the numeric parts can be bold via
    ``<strong>`` without forcing the caller to render Markdown.
    """
    plural = item_singular if filtered == 1 else f"{item_singular}s"
    if filtered == total:
        return [html.Strong(f"{filtered:,}"), html.Span(f" {plural}")]
    return [
        html.Span("Showing "),
        html.Strong(f"{filtered:,}"),
        html.Span(f" of {total:,} {plural}"),
    ]


def register_callbacks(app):
    @app.callback(
        Output("page-overview", "style"),
        Output("page-replacement", "style"),
        Output("page-orders", "style"),
        Output("page-settings", "style"),
        Output("nav-wrap-overview", "style"),
        Output("nav-wrap-replacement", "style"),
        Output("nav-wrap-orders", "style"),
        Output("nav-wrap-settings", "style"),
        Input("url", "pathname"),
    )
    def route_pages(pathname):
        if pathname in (None, ""):
            pathname = "/"
        on_rep = pathname == "/replacement"
        on_ord = pathname == "/orders"
        on_set = pathname == "/settings"
        page = {
            "padding": "0",
            "maxWidth": "100%",
            "margin": "0",
            "minWidth": 0,
        }

        def nav_item(active: bool):
            return {
                "padding": "11px 16px",
                "borderRadius": 10,
                "marginBottom": 6,
                "background": "#e8f1fe" if active else "transparent",
                "color": C.COLOR_TEXT_PRIMARY if active else C.COLOR_TEXT_SECONDARY,
                "fontWeight": 700 if active else 500,
                "fontSize": 14,
                "border": f"1px solid {'#bfdbfe' if active else 'transparent'}",
            }

        ov = not on_rep and not on_ord and not on_set
        return (
            {**page, "display": "block" if ov else "none"},
            {**page, "display": "block" if on_rep else "none"},
            {**page, "display": "block" if on_ord else "none"},
            {**page, "display": "block" if on_set else "none"},
            nav_item(ov),
            nav_item(on_rep),
            nav_item(on_ord),
            nav_item(on_set),
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
        if C.is_all_months(month_key):
            req = df_req[df_req["month_key"].astype(str) != "NaT"]
            svc = df_service[df_service["month_key"].astype(str) != "NaT"]
            rep = df_repairs[df_repairs["month_key"].astype(str) != "NaT"]
        else:
            req = df_req[df_req["month_key"] == month_key]
            svc = df_service[df_service["month_key"] == month_key]
            rep = df_repairs[df_repairs["month_key"] == month_key]
        return build_overview(month_key, req, svc, rep, df_equip, settings_data)

    @app.callback(
        Output("replace-table", "columns"),
        Output("replace-table", "data"),
        Output("replace-table", "style_data_conditional"),
        Output("replace-table", "page_size"),
        Output("replace-row-count", "children"),
        Input("month-select", "value"),
        Input("settings-store", "data"),
        Input("replace-filter-status", "value"),
        Input("replace-filter-equipment", "value"),
        Input("replace-filter-id", "value"),
        Input("replace-page-size", "value"),
    )
    def update_replacement_table(
        month_key,
        settings_data,
        rep_status,
        rep_equip,
        rep_id,
        page_size_value,
    ):
        if C.is_all_months(month_key):
            rep = df_repairs[df_repairs["month_key"].astype(str) != "NaT"]
        else:
            rep = df_repairs[df_repairs["month_key"] == month_key]
        rep_filters = {
            "status": rep_status or "All",
            "equipment_substr": rep_equip or "",
            "id_substr": rep_id or "",
        }
        total = int(rep["equipId"].nunique()) if not rep.empty and "equipId" in rep.columns else 0
        cols, records, cond = build_replacement_table(rep, settings_data, rep_filters)
        return (
            cols,
            records,
            cond,
            C.resolve_page_size(page_size_value),
            _format_row_count(len(records), total, "equipment item"),
        )

    @app.callback(
        Output("order-roster-table", "columns"),
        Output("order-roster-table", "data"),
        Output("order-roster-table", "style_data_conditional"),
        Output("order-roster-table", "page_size"),
        Output("order-filter-category", "options"),
        Output("order-row-count", "children"),
        Input("month-select", "value"),
        Input("settings-store", "data"),
        Input("order-filter-category", "value"),
        Input("order-filter-status", "value"),
        Input("order-filter-equipment", "value"),
        Input("order-filter-id", "value"),
        Input("order-page-size", "value"),
    )
    def update_order_roster_table(
        month_key,
        settings_data,
        order_cat,
        order_status,
        order_equip,
        order_id,
        page_size_value,
    ):
        _ = settings_data
        if C.is_all_months(month_key):
            svc = df_service[df_service["month_key"].astype(str) != "NaT"]
        else:
            svc = df_service[df_service["month_key"] == month_key]
        order_filters = {
            "category": order_cat or "",
            "status_substr": order_status or "",
            "equipment_substr": order_equip or "",
            "id_substr": order_id or "",
        }
        total = int(len(svc))
        ocols, odata, ostyle = build_repair_orders_table(svc, order_filters)
        cat_opts = repair_order_filter_options(svc)
        return (
            ocols,
            odata,
            ostyle,
            C.resolve_page_size(page_size_value),
            cat_opts,
            _format_row_count(len(odata), total, "service line"),
        )

    @app.callback(
        Output("order-filter-category", "value"),
        Input("month-select", "value"),
        prevent_initial_call=True,
    )
    def reset_order_category_on_month(_month_key):
        return ""

    @app.callback(
        Output("nav-icon-overview", "children"),
        Output("nav-icon-replacement", "children"),
        Output("nav-icon-orders", "children"),
        Output("nav-icon-settings", "children"),
        Output("replace-page-title-icon", "children"),
        Output("order-page-title-icon", "children"),
        Output("replace-legend-ico-replace", "children"),
        Output("replace-legend-ico-monitor", "children"),
        Output("replace-legend-ico-good", "children"),
        Input("settings-store", "data"),
    )
    def sync_chrome_icons(data):
        m = merge_app_settings(data)
        io = m["iconNavOrders"]
        return (
            m["iconNavOverview"],
            m["iconNavReplacement"],
            io,
            m["iconNavSettings"],
            m["iconReplaceTitle"],
            io,
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
        State("settings-iconNavOrders", "value"),
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
        in_ord,
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
        # When "All months" is selected, Apply only updates the global defaults
        # (the triple above), not any specific month override; otherwise persist
        # the override for the currently-selected month.
        if month_key is not None and not C.is_all_months(month_key):
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
            "iconNavOrders": in_ord,
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
        Output("settings-iconNavOrders", "value"),
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
            m["iconNavOrders"],
            m["iconNavSettings"],
            m["iconReplaceTitle"],
            m["iconReplaceStatusReplace"],
            m["iconReplaceStatusMonitor"],
            m["iconReplaceStatusGood"],
        )

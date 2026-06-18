"""Register Dash callbacks."""

from urllib.parse import urlencode

from dash import Input, Output, State, callback_context, html, no_update
from dash.exceptions import PreventUpdate

from dashboard import constants as C
from dashboard.auth import (
    create_user,
    delete_user,
    get_user_scopes,
    list_users,
    resolve_auth_db_path,
    set_user_scopes,
    set_user_active,
    set_user_password,
    set_user_role,
)
from dashboard.data_loaders import (
    df_equip,
    df_req,
    df_repairs,
    df_service,
)
from dashboard.logic.overview import build_overview
from dashboard.logic.overview.figures import build_hidden_chart_placeholder
from dashboard.logic.buildings import normalize_building_value
from dashboard.logic.overview.settings_merge import merge_app_settings, staff_capacity_for_month, sanitise_capacity_triple
from dashboard.logic.repair_orders_table import build_repair_orders_table, repair_order_filter_options
from dashboard.logic.replacement_table import build_replacement_table
from dashboard.logic.request_roster_table import build_request_roster_table
from dashboard.logic.service_scope import prepare_service_for_display
from dashboard.export.settings_codec import encode_settings
from dashboard.session_scope import (
    REPORT_KEYS,
    allowed_reports_for_session,
    apply_building_scope,
    normalize_building_scope,
)

from flask import session as flask_session


_ADD_FORM_DEFAULTS = ("", "", "user", 1, list(REPORT_KEYS), [])


def _hold_add_form():
    return (no_update, no_update, no_update, no_update, no_update, no_update)


def _reset_add_form():
    return _ADD_FORM_DEFAULTS


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


def _empty_state_style(visible: bool) -> dict:
    """Toggle the ``.empty-state`` panel's display without losing its CSS rules."""
    return {"display": "flex"} if visible else {"display": "none"}


def _building_options_from_data() -> list[dict]:
    vals: set[str] = set()
    for df in (df_repairs, df_service, df_req):
        for col in ("location", "Location", "building", "Building", "site", "Site"):
            if col in df.columns:
                vals.update(normalize_building_scope(df[col].dropna().tolist()))
    return [{"label": v, "value": v} for v in sorted(vals)]


def _reports_summary_for_user(db_path: str, user_id: int, role: str) -> str:
    if str(role or "").lower() == "admin":
        return "All"
    scopes = get_user_scopes(db_path, int(user_id))
    reports = scopes.get("reports") or list(REPORT_KEYS)
    if len(reports) >= len(REPORT_KEYS):
        return "All"
    return ", ".join(reports) if reports else "None"


def _buildings_scope_label(buildings: list[str]) -> str:
    if not buildings:
        return "All"
    n = len(buildings)
    return f"{n} selected" if n > 1 else buildings[0]


def _admin_users_table_rows(db_path: str) -> list[dict]:
    rows = []
    for display_id, user in enumerate(list_users(db_path), start=1):
        role = str(user.get("role") or "user")
        rows.append(
            {
                **user,
                "display_id": display_id,
                "active_label": "Active" if user.get("is_active") else "Disabled",
                "reports_summary": _reports_summary_for_user(db_path, int(user["id"]), role),
            }
        )
    return rows


def _repair_category_options() -> list[dict]:
    opts = [{"label": "All categories", "value": ""}]
    if df_repairs.empty or "equipCategory" not in df_repairs.columns:
        return opts
    for c in sorted(df_repairs["equipCategory"].dropna().astype(str).unique()):
        if c:
            opts.append({"label": c, "value": c})
    return opts


def _replacement_building_options() -> list[dict]:
    return [{"label": "All buildings", "value": ""}, *_building_options_from_data()]


def register_callbacks(app):
    @app.callback(
        Output("page-overview", "style"),
        Output("page-replacement", "style"),
        Output("page-orders", "style"),
        Output("page-requests", "style"),
        Output("page-settings", "style"),
        Output("page-admin", "style"),
        Output("nav-wrap-overview", "style"),
        Output("nav-wrap-replacement", "style"),
        Output("nav-wrap-orders", "style"),
        Output("nav-wrap-requests", "style"),
        Output("nav-wrap-settings", "style"),
        Output("nav-wrap-admin", "style"),
        Input("url", "pathname"),
    )
    def route_pages(pathname):
        if pathname in (None, ""):
            pathname = "/"
        on_rep = pathname == "/replacement"
        on_ord = pathname == "/orders"
        on_req = pathname == "/requests"
        on_set = pathname == "/settings"
        on_admin = pathname == "/admin"
        role = str(flask_session.get("role") or "")
        allowed_reports = allowed_reports_for_session()
        can_overview = "overview" in allowed_reports
        can_replacement = "replacement" in allowed_reports
        can_orders = "orders" in allowed_reports
        can_requests = can_overview
        can_settings = "settings" in allowed_reports
        # Layout spacing lives in CSS (`.app-page`); callback only toggles visibility.
        page_show = {"display": "block"}

        def nav_item(active: bool):
            return {
                "padding": "12px 16px",
                "borderRadius": 12,
                "marginBottom": 6,
                "background": (
                    "linear-gradient(135deg, #eff6ff 0%, #e0f2fe 100%)"
                    if active
                    else "transparent"
                ),
                "color": C.COLOR_TEXT_PRIMARY if active else C.COLOR_TEXT_SECONDARY,
                "fontWeight": 700 if active else 500,
                "fontSize": 14,
                "border": f"1px solid {'#bfdbfe' if active else 'transparent'}",
                "boxShadow": (
                    "0 2px 8px -2px rgba(59, 130, 246, 0.25), inset 0 1px 0 rgba(255,255,255,0.8)"
                    if active
                    else "none"
                ),
            }

        ov = not on_rep and not on_ord and not on_req and not on_set and not on_admin
        if ov and not can_overview:
            if can_replacement:
                on_rep = True
                ov = False
            elif can_orders:
                on_ord = True
                ov = False
            elif can_requests:
                on_req = True
                ov = False
            elif can_settings:
                on_set = True
                ov = False
        return (
            {**page_show, "display": "block" if ov and can_overview else "none"},
            {**page_show, "display": "block" if on_rep and can_replacement else "none"},
            {**page_show, "display": "block" if on_ord and can_orders else "none"},
            {**page_show, "display": "block" if on_req and can_requests else "none"},
            {**page_show, "display": "block" if on_set and can_settings else "none"},
            {**page_show, "display": "block" if on_admin and role == "admin" else "none"},
            ({**nav_item(ov), "display": "block"} if can_overview else {"display": "none"}),
            ({**nav_item(on_rep), "display": "block"} if can_replacement else {"display": "none"}),
            ({**nav_item(on_ord), "display": "block"} if can_orders else {"display": "none"}),
            ({**nav_item(on_req), "display": "block"} if can_requests else {"display": "none"}),
            ({**nav_item(on_set), "display": "block"} if can_settings else {"display": "none"}),
            ({**nav_item(on_admin), "display": "block"} if role == "admin" else {"display": "none"}),
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
        Output("monthly-parts-budget-chart", "figure"),
        Output("annual-parts-budget-chart", "figure"),
        Output("annual-parts-budget-wrap", "style"),
        Output("repair-count-mix-chart", "figure"),
        Output("repair-count-mix-wrap", "style"),
        Output("building-hours-chart", "figure"),
        Input("month-select", "value"),
        Input("settings-store", "data"),
    )
    def update_overview(month_key, settings_data):
        rep_all = df_repairs[df_repairs["month_key"].astype(str) != "NaT"]
        rep_all = apply_building_scope(rep_all)
        all_months = C.is_all_months(month_key)
        if all_months:
            req = df_req[df_req["month_key"].astype(str) != "NaT"]
            svc = df_service[df_service["month_key"].astype(str) != "NaT"]
            rep = rep_all
        else:
            req = df_req[df_req["month_key"] == month_key]
            svc = df_service[df_service["month_key"] == month_key]
            rep = df_repairs[df_repairs["month_key"] == month_key]
        req = apply_building_scope(req)
        svc = apply_building_scope(svc)
        rep = apply_building_scope(rep)
        svc = prepare_service_for_display(svc, month_key, df_service)
        out = build_overview(month_key, req, svc, rep, df_equip, settings_data, rep_full=rep_all)
        primary_budget, secondary_budget = out[9], out[10]
        annual_wrap = {"display": "none"}
        repair_wrap = {"display": "block"}
        annual_fig = (
            secondary_budget if secondary_budget is not None else build_hidden_chart_placeholder()
        )
        return (*out[:9], primary_budget, annual_fig, annual_wrap, out[11], repair_wrap, out[12])

    @app.callback(
        Output("overview-export-pdf", "href"),
        Input("month-select", "value"),
        Input("settings-store", "data"),
    )
    def overview_export_href(month_key, settings_data):
        params = {
            "month": month_key or C.ALL_MONTHS_KEY,
            "settings": encode_settings(settings_data if isinstance(settings_data, dict) else None),
        }
        return "/export/overview.pdf?" + urlencode(params)

    @app.callback(
        Output("url", "pathname"),
        Output("chart-drill-store", "data"),
        Input("hours-chart", "clickData"),
        Input("building-hours-chart", "clickData"),
        Input("calendar-chart", "clickData"),
        Input("repair-count-mix-chart", "clickData"),
        Input("turnaround-chart", "clickData"),
        Input("availability-chart", "clickData"),
        prevent_initial_call=True,
    )
    def drill_from_overview_charts(
        hours_click,
        building_click,
        calendar_click,
        repair_mix_click,
        turnaround_click,
        availability_click,
    ):
        allowed = allowed_reports_for_session()
        triggered = callback_context.triggered_id

        if triggered == "calendar-chart":
            if "overview" not in allowed:
                raise PreventUpdate
            click = calendar_click
            if not click or not click.get("points"):
                raise PreventUpdate
            cd = click["points"][0].get("customdata")
            if cd is None:
                raise PreventUpdate
            if isinstance(cd, (list, tuple)) and len(cd) >= 2:
                month_key = str(cd[0])
                day_raw = cd[1]
                try:
                    day = int(day_raw)
                except (TypeError, ValueError):
                    day = None
            elif isinstance(cd, str) and len(cd) >= 7:
                month_key = cd
                day = None
            else:
                raise PreventUpdate
            payload = {"page": "requests", "month_key": month_key}
            if day is not None:
                payload["day"] = day
            return "/requests", payload

        if triggered == "repair-count-mix-chart":
            if "replacement" not in allowed:
                raise PreventUpdate
            click = repair_mix_click
            if not click or not click.get("points"):
                raise PreventUpdate
            label = str(click["points"][0].get("label") or "").strip()
            if not label:
                raise PreventUpdate
            return "/replacement", {
                "page": "replacement",
                "category": "",
                "building": "",
                "repair_count_bin": label,
            }

        if triggered in ("turnaround-chart", "availability-chart"):
            if "orders" not in allowed:
                raise PreventUpdate
            click = turnaround_click if triggered == "turnaround-chart" else availability_click
            if not click or not click.get("points"):
                raise PreventUpdate
            axis_key = "y" if triggered == "turnaround-chart" else "x"
            label = str(click["points"][0].get(axis_key) or "").strip()
            if not label:
                raise PreventUpdate
            return "/orders", {"page": "orders", "category": label}

        if "replacement" not in allowed:
            raise PreventUpdate
        if triggered == "hours-chart":
            click = hours_click
            axis_key = "y"
        elif triggered == "building-hours-chart":
            click = building_click
            axis_key = "x"
        else:
            raise PreventUpdate
        if not click or not click.get("points"):
            raise PreventUpdate
        label = str(click["points"][0].get(axis_key) or "").strip()
        if not label:
            raise PreventUpdate
        if triggered == "hours-chart":
            return "/replacement", {
                "page": "replacement",
                "category": label,
                "building": "",
                "repair_count_bin": "",
            }
        return "/replacement", {
            "page": "replacement",
            "category": "",
            "building": label,
            "repair_count_bin": "",
        }

    @app.callback(
        Output("replace-filter-category", "value"),
        Output("replace-filter-building", "value"),
        Output("replace-filter-repair-count", "value"),
        Output("chart-drill-store", "data", allow_duplicate=True),
        Input("chart-drill-store", "data"),
        prevent_initial_call=True,
    )
    def apply_chart_drill_to_replacement(drill):
        if not drill or drill.get("page") != "replacement":
            raise PreventUpdate
        return (
            drill.get("category") or "",
            drill.get("building") or "",
            drill.get("repair_count_bin") or "",
            None,
        )

    @app.callback(
        Output("order-filter-category", "value", allow_duplicate=True),
        Output("chart-drill-store", "data", allow_duplicate=True),
        Input("chart-drill-store", "data"),
        prevent_initial_call=True,
    )
    def apply_chart_drill_to_orders(drill):
        if not drill or drill.get("page") != "orders":
            raise PreventUpdate
        return drill.get("category") or "", None

    @app.callback(
        Output("month-select", "value"),
        Output("request-filter-day", "value"),
        Output("request-filter-work-order", "value"),
        Output("request-filter-requestor", "value"),
        Output("request-filter-text", "value"),
        Output("chart-drill-store", "data", allow_duplicate=True),
        Input("chart-drill-store", "data"),
        prevent_initial_call=True,
    )
    def apply_chart_drill_to_requests(drill):
        if not drill or drill.get("page") != "requests":
            raise PreventUpdate
        month_key = drill.get("month_key")
        if not month_key:
            raise PreventUpdate
        day = drill.get("day")
        day_val = int(day) if day is not None and str(day).strip() != "" else None
        return month_key, day_val, "", "", "", None

    @app.callback(
        Output("replace-filter-category", "options"),
        Output("replace-filter-building", "options"),
        Input("url", "pathname"),
    )
    def sync_replacement_filter_options(pathname):
        if pathname != "/replacement":
            raise PreventUpdate
        return _repair_category_options(), _replacement_building_options()

    @app.callback(
        Output("replace-table", "columns"),
        Output("replace-table", "data"),
        Output("replace-table", "style_data_conditional"),
        Output("replace-table", "page_size"),
        Output("replace-row-count", "children"),
        Output("replace-empty-state", "style"),
        Input("settings-store", "data"),
        Input("replace-filter-status", "value"),
        Input("replace-filter-category", "value"),
        Input("replace-filter-building", "value"),
        Input("replace-filter-repair-count", "value"),
        Input("replace-filter-equipment", "value"),
        Input("replace-filter-id", "value"),
        Input("replace-page-size", "value"),
    )
    def update_replacement_table(
        settings_data,
        rep_status,
        rep_category,
        rep_building,
        rep_repair_count,
        rep_equip,
        rep_id,
        page_size_value,
    ):
        # Replacement is always **cumulative**: every repair row from every
        # loaded month (header month scope applies only to Overview & Order roster).
        rep = df_repairs[df_repairs["month_key"].astype(str) != "NaT"]
        rep = apply_building_scope(rep)
        rep_filters = {
            "status": rep_status or "All",
            "category": rep_category or "",
            "building": rep_building or "",
            "repair_count_bin": rep_repair_count or "",
            "equipment_substr": rep_equip or "",
            "id_substr": rep_id or "",
        }
        id_col = "equipIdNorm" if "equipIdNorm" in rep.columns else "equipId"
        total = int(rep[id_col].nunique()) if not rep.empty and id_col in rep.columns else 0
        cols, records, cond = build_replacement_table(rep, settings_data, rep_filters)
        return (
            cols,
            records,
            cond,
            C.resolve_page_size(page_size_value),
            _format_row_count(len(records), total, "equipment item"),
            _empty_state_style(len(records) == 0),
        )

    @app.callback(
        Output("order-roster-table", "columns"),
        Output("order-roster-table", "data"),
        Output("order-roster-table", "style_data_conditional"),
        Output("order-roster-table", "page_size"),
        Output("order-filter-category", "options"),
        Output("order-row-count", "children"),
        Output("order-empty-state", "style"),
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
        svc = apply_building_scope(svc)
        svc = prepare_service_for_display(svc, month_key, df_service)
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
            _empty_state_style(len(odata) == 0),
        )

    @app.callback(
        Output("request-roster-table", "columns"),
        Output("request-roster-table", "data"),
        Output("request-roster-table", "style_data_conditional"),
        Output("request-roster-table", "page_size"),
        Output("request-row-count", "children"),
        Output("request-empty-state", "style"),
        Input("month-select", "value"),
        Input("request-filter-day", "value"),
        Input("request-filter-work-order", "value"),
        Input("request-filter-requestor", "value"),
        Input("request-filter-text", "value"),
        Input("request-page-size", "value"),
    )
    def update_request_roster_table(
        month_key,
        filter_day,
        filter_wo,
        filter_requestor,
        filter_text,
        page_size_value,
    ):
        if C.is_all_months(month_key):
            req = df_req[df_req["month_key"].astype(str) != "NaT"]
        else:
            req = df_req[df_req["month_key"] == month_key]
        req = apply_building_scope(req)
        req_filters = {
            "day": str(filter_day).strip() if filter_day is not None else "",
            "work_order_substr": filter_wo or "",
            "requestor_substr": filter_requestor or "",
            "request_substr": filter_text or "",
        }
        total = int(len(req))
        rcols, rdata, rstyle = build_request_roster_table(req, req_filters)
        return (
            rcols,
            rdata,
            rstyle,
            C.resolve_page_size(page_size_value),
            _format_row_count(len(rdata), total, "request"),
            _empty_state_style(len(rdata) == 0),
        )

    @app.callback(
        Output("replace-export-pdf", "href"),
        Input("replace-filter-status", "value"),
        Input("replace-filter-category", "value"),
        Input("replace-filter-building", "value"),
        Input("replace-filter-repair-count", "value"),
        Input("replace-filter-equipment", "value"),
        Input("replace-filter-id", "value"),
    )
    def replace_export_href(rep_status, rep_category, rep_building, rep_repair_count, rep_equip, rep_id):
        params = {
            "status": rep_status or "All",
            "category": rep_category or "",
            "building": rep_building or "",
            "repair_count_bin": rep_repair_count or "",
            "equipment": rep_equip or "",
            "id": rep_id or "",
        }
        return "/export/replacement.pdf?" + urlencode(params)

    @app.callback(
        Output("order-export-pdf", "href"),
        Input("month-select", "value"),
        Input("order-filter-category", "value"),
        Input("order-filter-status", "value"),
        Input("order-filter-equipment", "value"),
        Input("order-filter-id", "value"),
    )
    def order_export_href(month_key, order_cat, order_status, order_equip, order_id):
        params = {
            "month": month_key or C.ALL_MONTHS_KEY,
            "category": order_cat or "",
            "status": order_status or "",
            "equipment": order_equip or "",
            "id": order_id or "",
        }
        return "/export/orders.pdf?" + urlencode(params)

    @app.callback(
        Output("request-export-pdf", "href"),
        Input("month-select", "value"),
        Input("request-filter-day", "value"),
        Input("request-filter-work-order", "value"),
        Input("request-filter-requestor", "value"),
        Input("request-filter-text", "value"),
    )
    def request_export_href(month_key, filter_day, filter_wo, filter_requestor, filter_text):
        params = {
            "month": month_key or C.ALL_MONTHS_KEY,
            "day": str(filter_day).strip() if filter_day is not None else "",
            "work_order": filter_wo or "",
            "requestor": filter_requestor or "",
            "request": filter_text or "",
        }
        return "/export/requests.pdf?" + urlencode(params)

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
        Output("nav-icon-requests", "children"),
        Output("nav-icon-settings", "children"),
        Output("replace-page-title-icon", "children"),
        Output("order-page-title-icon", "children"),
        Output("request-page-title-icon", "children"),
        Output("replace-legend-ico-replace", "children"),
        Output("replace-legend-ico-monitor", "children"),
        Output("replace-legend-ico-good", "children"),
        Input("settings-store", "data"),
    )
    def sync_chrome_icons(data):
        m = merge_app_settings(data)
        io = m["iconNavOrders"]
        ir = m["iconNavRequests"]
        irep = m["iconNavReplacement"]
        return (
            m["iconNavOverview"],
            irep,
            io,
            ir,
            m["iconNavSettings"],
            irep,
            io,
            ir,
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
        State("settings-monthly-parts-budget", "value"),
        State("settings-annual-parts-budget", "value"),
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
        State("settings-iconNavRequests", "value"),
        State("settings-iconNavSettings", "value"),
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
        monthly_parts_budget,
        annual_parts_budget,
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
        in_req,
        in_set,
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
        # staffCapacityByMonth is used **only by Overview** (staff utilization bar).
        # When "All months" is selected in the header, Apply only updates the
        # global defaults (the triple above), not any per-calendar-month override;
        # otherwise persist the override for the month shown in the header.
        if month_key is not None and not C.is_all_months(month_key):
            mks = str(month_key).strip()
            if mks and mks not in ("None", "nan", "NaT"):
                by_m[mks] = {"staffCount": sc, "hoursPerDay": hd, "workDays": wd}
        patch = {
            "staffCount": sc,
            "hoursPerDay": hd,
            "workDays": wd,
            "baseAvailDays": base_avail,
            "monthlyPartsBudget": monthly_parts_budget,
            "annualPartsBudget": annual_parts_budget,
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
            "iconNavRequests": in_req,
            "iconNavSettings": in_set,
            "iconReplaceTitle": in_rep,
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
        Output("settings-monthly-parts-budget", "value"),
        Output("settings-annual-parts-budget", "value"),
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
        Output("settings-iconNavRequests", "value"),
        Output("settings-iconNavSettings", "value"),
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
            m["monthlyPartsBudget"],
            m["annualPartsBudget"],
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
            m["iconNavRequests"],
            m["iconNavSettings"],
            m["iconReplaceStatusReplace"],
            m["iconReplaceStatusMonitor"],
            m["iconReplaceStatusGood"],
        )

    @app.callback(
        Output("auth-status", "children"),
        Input("url", "pathname"),
    )
    def render_auth_status(_pathname):
        username = flask_session.get("username")
        role = flask_session.get("role")
        if not username:
            return html.Div("Not signed in", style={"color": C.COLOR_TEXT_MUTED, "fontSize": 12})
        return html.Div(
            [
                html.Div(f"Signed in: {username} ({role})", style={"marginBottom": 6}),
                html.A(
                    "Logout",
                    href="/logout",
                    style={"color": "#3b82f6", "textDecoration": "none", "fontWeight": 700},
                ),
            ]
        )

    @app.callback(
        Output("admin-users-table", "data"),
        Output("admin-users-table", "columns"),
        Output("admin-users-table", "style_data_conditional"),
        Output("admin-edit-buildings", "options"),
        Output("admin-add-buildings", "options"),
        Input("url", "pathname"),
        Input("admin-add-user-btn", "n_clicks"),
        Input("admin-save-user-btn", "n_clicks"),
        Input("admin-delete-confirm", "submit_n_clicks"),
    )
    def load_admin_users(pathname, _add_clicks, _save_clicks, _delete_clicks):
        if pathname != "/admin":
            return no_update, no_update, no_update, no_update, no_update
        db_path = resolve_auth_db_path()
        users = _admin_users_table_rows(db_path)
        building_options = _building_options_from_data()
        columns = [
            {"name": "#", "id": "display_id"},
            {"name": "Username", "id": "username"},
            {"name": "Role", "id": "role"},
            {"name": "Active", "id": "active_label"},
            {"name": "Reports", "id": "reports_summary"},
            {"name": "Created", "id": "created_at"},
            {"name": "Last login", "id": "last_login_at"},
        ]
        current_user_id = flask_session.get("user_id")
        style_data_conditional = []
        if current_user_id is not None:
            style_data_conditional.append(
                {
                    "if": {"filter_query": f"{{id}} = {int(current_user_id)}"},
                    "backgroundColor": "#eff6ff",
                    "fontWeight": 700,
                }
            )
        return users, columns, style_data_conditional, building_options, building_options

    @app.callback(
        Output("admin-edit-active", "value"),
        Output("admin-edit-role", "value"),
        Output("admin-edit-password", "value"),
        Output("admin-edit-reports", "value"),
        Output("admin-edit-buildings", "value"),
        Output("admin-edit-username", "children"),
        Input("admin-users-table", "selected_rows"),
        State("admin-users-table", "data"),
    )
    def sync_admin_edit_fields(selected_rows, table_data):
        if not selected_rows or not table_data:
            return 1, "user", "", list(REPORT_KEYS), [], "Select a user row to edit."
        idx = selected_rows[0]
        if idx is None or idx >= len(table_data):
            return 1, "user", "", list(REPORT_KEYS), [], "Select a user row to edit."
        row = table_data[idx]
        active = 1 if bool(row.get("is_active")) else 0
        role = str(row.get("role") or "user")
        username = str(row.get("username") or "")
        db_path = resolve_auth_db_path()
        scopes = get_user_scopes(db_path, int(row.get("id")))
        reports = scopes.get("reports") or list(REPORT_KEYS)
        buildings = scopes.get("buildings") or []
        reports_label = "All" if role == "admin" or len(reports) >= len(REPORT_KEYS) else (
            ", ".join(reports) if reports else "None"
        )
        buildings_label = "All" if role == "admin" else _buildings_scope_label(buildings)
        return (
            active,
            role,
            "",
            reports,
            buildings,
            f"Editing: {username} · Reports: {reports_label} · Buildings: {buildings_label}",
        )

    @app.callback(
        Output("admin-edit-reports", "disabled"),
        Output("admin-edit-buildings", "disabled"),
        Output("admin-edit-scope-hint", "children"),
        Input("admin-edit-role", "value"),
    )
    def sync_admin_edit_scope_controls(role):
        is_admin = str(role or "").lower() == "admin"
        hint = "Admin accounts always have full report and building access." if is_admin else ""
        return is_admin, is_admin, hint

    @app.callback(
        Output("admin-add-reports", "disabled"),
        Output("admin-add-buildings", "disabled"),
        Output("admin-add-scope-hint", "children"),
        Input("admin-add-role", "value"),
    )
    def sync_admin_add_scope_controls(role):
        is_admin = str(role or "").lower() == "admin"
        hint = "Admin accounts always have full report and building access." if is_admin else ""
        return is_admin, is_admin, hint

    @app.callback(
        Output("admin-delete-confirm", "displayed"),
        Output("admin-message", "children", allow_duplicate=True),
        Input("admin-delete-user-btn", "n_clicks"),
        State("admin-users-table", "selected_rows"),
        State("admin-users-table", "data"),
        prevent_initial_call=True,
    )
    def prompt_delete_user(delete_clicks, selected_rows, table_data):
        if not delete_clicks:
            raise PreventUpdate
        if not selected_rows or not table_data:
            return False, html.Div("Select a user row first.", style={"color": "#b91c1c"})
        idx = selected_rows[0]
        if idx is None or idx >= len(table_data):
            return False, html.Div("Invalid selection.", style={"color": "#b91c1c"})
        return True, no_update

    @app.callback(
        Output("admin-users-table", "selected_rows"),
        Output("admin-message", "children", allow_duplicate=True),
        Output("admin-add-username", "value"),
        Output("admin-add-password", "value"),
        Output("admin-add-role", "value"),
        Output("admin-add-active", "value"),
        Output("admin-add-reports", "value"),
        Output("admin-add-buildings", "value"),
        Input("admin-add-user-btn", "n_clicks"),
        Input("admin-save-user-btn", "n_clicks"),
        Input("admin-delete-confirm", "submit_n_clicks"),
        State("admin-add-username", "value"),
        State("admin-add-password", "value"),
        State("admin-add-role", "value"),
        State("admin-add-active", "value"),
        State("admin-add-reports", "value"),
        State("admin-add-buildings", "value"),
        State("admin-users-table", "selected_rows"),
        State("admin-users-table", "data"),
        State("admin-edit-active", "value"),
        State("admin-edit-role", "value"),
        State("admin-edit-password", "value"),
        State("admin-edit-reports", "value"),
        State("admin-edit-buildings", "value"),
        prevent_initial_call=True,
    )
    def handle_admin_actions(
        add_clicks,
        save_clicks,
        delete_submit_clicks,
        add_username,
        add_password,
        add_role,
        add_active,
        add_reports,
        add_buildings,
        selected_rows,
        table_data,
        edit_active,
        edit_role,
        edit_password,
        edit_reports,
        edit_buildings,
    ):
        triggered = [t["prop_id"] for t in callback_context.triggered if t["prop_id"] != "."]
        if not triggered:
            raise PreventUpdate

        db_path = resolve_auth_db_path()
        tid = triggered[0].split(".")[0]
        current_user_id = flask_session.get("user_id")

        try:
            if tid == "admin-add-user-btn":
                username = (add_username or "").strip()
                password = add_password or ""
                role = str(add_role or "user").strip().lower()
                if not username or not password:
                    return (
                        no_update,
                        html.Div("Username and password are required.", style={"color": "#b91c1c"}),
                        *_hold_add_form(),
                    )
                is_active = 1 if int(add_active) == 1 else 0

                user_id = create_user(db_path, username, password, role, is_active=bool(is_active))
                if role != "admin":
                    set_user_scopes(
                        db_path,
                        user_id,
                        add_reports or [],
                        sorted(normalize_building_scope(add_buildings or [])),
                    )
                return (
                    no_update,
                    html.Div(f"User '{username}' created.", style={"color": "#047857"}),
                    *_reset_add_form(),
                )

            if tid == "admin-save-user-btn":
                if not selected_rows or not table_data:
                    return (
                        no_update,
                        html.Div("Select a user row first.", style={"color": "#b91c1c"}),
                        *_hold_add_form(),
                    )
                idx = selected_rows[0]
                if idx is None or idx >= len(table_data):
                    return (
                        no_update,
                        html.Div("Invalid selection.", style={"color": "#b91c1c"}),
                        *_hold_add_form(),
                    )
                row = table_data[idx]
                user_id = int(row.get("id"))
                desired_active = 1 if int(edit_active) == 1 else 0
                desired_role = str(edit_role or row.get("role") or "user").strip().lower()
                desired_password = (edit_password or "").strip()

                if str(user_id) == str(current_user_id) and desired_active == 0:
                    return (
                        no_update,
                        html.Div(
                            "You can't disable your own active admin account.",
                            style={"color": "#b91c1c"},
                        ),
                        *_hold_add_form(),
                    )

                current_active = 1 if bool(row.get("is_active")) else 0
                if desired_active != current_active:
                    set_user_active(db_path, user_id, desired_active == 1)
                current_role = str(row.get("role") or "user")
                if desired_role != current_role:
                    set_user_role(db_path, user_id, desired_role)

                if desired_password:
                    set_user_password(db_path, user_id, desired_password)
                if desired_role != "admin":
                    set_user_scopes(
                        db_path,
                        user_id,
                        edit_reports or [],
                        sorted(normalize_building_scope(edit_buildings or [])),
                    )

                return (
                    no_update,
                    html.Div("Changes saved.", style={"color": "#047857"}),
                    *_hold_add_form(),
                )

            if tid == "admin-delete-confirm":
                if not delete_submit_clicks:
                    raise PreventUpdate
                if not selected_rows or not table_data:
                    return (
                        no_update,
                        html.Div("Select a user row first.", style={"color": "#b91c1c"}),
                        *_hold_add_form(),
                    )
                idx = selected_rows[0]
                if idx is None or idx >= len(table_data):
                    return (
                        no_update,
                        html.Div("Invalid selection.", style={"color": "#b91c1c"}),
                        *_hold_add_form(),
                    )
                row = table_data[idx]
                user_id = int(row.get("id"))
                username = str(row.get("username") or "")

                if str(user_id) == str(current_user_id):
                    return (
                        no_update,
                        html.Div("You can't delete your own account.", style={"color": "#b91c1c"}),
                        *_hold_add_form(),
                    )

                delete_user(db_path, user_id)
                return (
                    [],
                    html.Div(f"User '{username}' deleted.", style={"color": "#047857"}),
                    *_hold_add_form(),
                )

            raise PreventUpdate
        except ValueError as e:
            return no_update, html.Div(str(e), style={"color": "#b91c1c"}), *_hold_add_form()
        except Exception:
            return (
                no_update,
                html.Div(
                    "Admin action failed. Check inputs and try again.",
                    style={"color": "#b91c1c"},
                ),
                *_hold_add_form(),
            )

"""Register Dash callbacks."""

from dash import Input, Output, State, callback_context, html, no_update
from dash.exceptions import PreventUpdate

from dashboard import constants as C
from dashboard.auth import (
    get_user_scopes,
    list_users,
    resolve_auth_db_path,
    set_user_scopes,
    set_user_active,
    set_user_password,
    set_user_role,
    upsert_user,
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

from flask import session as flask_session


_REPORT_KEYS = ("overview", "replacement", "orders", "settings")


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


def _allowed_reports_for_session() -> set[str]:
    role = str(flask_session.get("role") or "")
    if role == "admin":
        return set(_REPORT_KEYS)
    if "allowed_reports" not in flask_session:
        return set(_REPORT_KEYS)
    values = flask_session.get("allowed_reports") or []
    return {str(v).strip().lower() for v in values if str(v).strip()}


def _normalize_building_scope(values) -> set[str]:
    out: set[str] = set()
    for v in values or []:
        nv = normalize_building_value(v)
        if nv:
            out.add(nv)
    return out


def _apply_building_scope(df):
    allowed = _normalize_building_scope(flask_session.get("allowed_buildings") or [])
    if not allowed:
        return df
    for col in ("location", "Location", "building", "Building", "site", "Site"):
        if col in df.columns:
            normalized = df[col].map(normalize_building_value)
            return df[normalized.isin(allowed)]
    return df


def _building_options_from_data() -> list[dict]:
    vals: set[str] = set()
    for df in (df_repairs, df_service, df_req):
        for col in ("location", "Location", "building", "Building", "site", "Site"):
            if col in df.columns:
                vals.update(_normalize_building_scope(df[col].dropna().tolist()))
    return [{"label": v, "value": v} for v in sorted(vals)]


def register_callbacks(app):
    @app.callback(
        Output("page-overview", "style"),
        Output("page-replacement", "style"),
        Output("page-orders", "style"),
        Output("page-settings", "style"),
        Output("page-admin", "style"),
        Output("nav-wrap-overview", "style"),
        Output("nav-wrap-replacement", "style"),
        Output("nav-wrap-orders", "style"),
        Output("nav-wrap-settings", "style"),
        Output("nav-wrap-admin", "style"),
        Input("url", "pathname"),
    )
    def route_pages(pathname):
        if pathname in (None, ""):
            pathname = "/"
        on_rep = pathname == "/replacement"
        on_ord = pathname == "/orders"
        on_set = pathname == "/settings"
        on_admin = pathname == "/admin"
        role = str(flask_session.get("role") or "")
        allowed_reports = _allowed_reports_for_session()
        can_overview = "overview" in allowed_reports
        can_replacement = "replacement" in allowed_reports
        can_orders = "orders" in allowed_reports
        can_settings = "settings" in allowed_reports
        # Keep each page's intended outer spacing. The corresponding page
        # bodies in `dashboard/layouts/shell.py` already define padding and
        # maxWidth, but this callback overwrites the full `style` dict.
        page_overview = {"padding": "28px 36px 40px", "maxWidth": 1440, "margin": "0 auto", "minWidth": 0}
        page_replacement = {"padding": "28px 36px 40px", "maxWidth": 1280, "margin": "0 auto", "minWidth": 0}
        page_orders = {"padding": "28px 36px 40px", "maxWidth": 1280, "margin": "0 auto", "minWidth": 0}
        page_settings = {"padding": "24px 28px", "maxWidth": 1240, "margin": "0 auto", "minWidth": 0}
        page_admin = {"padding": "24px 28px 40px", "maxWidth": 1280, "margin": "0 auto", "minWidth": 0}

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

        ov = not on_rep and not on_ord and not on_set and not on_admin
        if ov and not can_overview:
            if can_replacement:
                on_rep = True
                ov = False
            elif can_orders:
                on_ord = True
                ov = False
            elif can_settings:
                on_set = True
                ov = False
        return (
            {**page_overview, "display": "block" if ov and can_overview else "none"},
            {**page_replacement, "display": "block" if on_rep and can_replacement else "none"},
            {**page_orders, "display": "block" if on_ord and can_orders else "none"},
            {**page_settings, "display": "block" if on_set and can_settings else "none"},
            {**page_admin, "display": "block" if on_admin and role == "admin" else "none"},
            ({**nav_item(ov), "display": "block"} if can_overview else {"display": "none"}),
            ({**nav_item(on_rep), "display": "block"} if can_replacement else {"display": "none"}),
            ({**nav_item(on_ord), "display": "block"} if can_orders else {"display": "none"}),
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
        rep_all = _apply_building_scope(rep_all)
        all_months = C.is_all_months(month_key)
        if all_months:
            req = df_req[df_req["month_key"].astype(str) != "NaT"]
            svc = df_service[df_service["month_key"].astype(str) != "NaT"]
            rep = rep_all
        else:
            req = df_req[df_req["month_key"] == month_key]
            svc = df_service[df_service["month_key"] == month_key]
            rep = df_repairs[df_repairs["month_key"] == month_key]
        req = _apply_building_scope(req)
        svc = _apply_building_scope(svc)
        rep = _apply_building_scope(rep)
        out = build_overview(month_key, req, svc, rep, df_equip, settings_data, rep_full=rep_all)
        primary_budget, secondary_budget = out[9], out[10]
        _square = {**C.CARD_STYLE, "gridColumn": "span 1", "padding": "16px 8px 8px"}
        annual_wrap = {**_square, "display": "none" if all_months else "block"}
        repair_wrap = {**_square, "display": "block" if all_months else "none"}
        annual_fig = (
            secondary_budget if secondary_budget is not None else build_hidden_chart_placeholder()
        )
        return (*out[:9], primary_budget, annual_fig, annual_wrap, out[11], repair_wrap, out[12])

    @app.callback(
        Output("replace-table", "columns"),
        Output("replace-table", "data"),
        Output("replace-table", "style_data_conditional"),
        Output("replace-table", "page_size"),
        Output("replace-row-count", "children"),
        Output("replace-empty-state", "style"),
        Input("settings-store", "data"),
        Input("replace-filter-status", "value"),
        Input("replace-filter-equipment", "value"),
        Input("replace-filter-id", "value"),
        Input("replace-page-size", "value"),
    )
    def update_replacement_table(
        settings_data,
        rep_status,
        rep_equip,
        rep_id,
        page_size_value,
    ):
        # Replacement is always **cumulative**: every repair row from every
        # loaded month (header month scope applies only to Overview & Order roster).
        rep = df_repairs[df_repairs["month_key"].astype(str) != "NaT"]
        rep = _apply_building_scope(rep)
        rep_filters = {
            "status": rep_status or "All",
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
        svc = _apply_building_scope(svc)
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
            m["iconNavSettings"],
            m["iconReplaceTitle"],
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
        Input("url", "pathname"),
        Input("admin-add-user-btn", "n_clicks"),
        Input("admin-save-user-btn", "n_clicks"),
    )
    def load_admin_users(pathname, _add_clicks, _save_clicks):
        if pathname != "/admin":
            return no_update, no_update, no_update, no_update
        db_path = resolve_auth_db_path()
        users = list_users(db_path)
        columns = [
            {"name": "ID", "id": "id"},
            {"name": "Username", "id": "username"},
            {"name": "Role", "id": "role"},
            {"name": "Active", "id": "is_active"},
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
        return users, columns, style_data_conditional, _building_options_from_data()

    @app.callback(
        Output("admin-edit-active", "value"),
        Output("admin-edit-role", "value"),
        Output("admin-edit-password", "value"),
        Output("admin-edit-reports", "value"),
        Output("admin-edit-buildings", "value"),
        Input("admin-users-table", "selected_rows"),
        State("admin-users-table", "data"),
    )
    def sync_admin_edit_fields(selected_rows, table_data):
        if not selected_rows or not table_data:
            return 1, "user", "", list(_REPORT_KEYS), []
        idx = selected_rows[0]
        if idx is None or idx >= len(table_data):
            return 1, "user", "", list(_REPORT_KEYS), []
        row = table_data[idx]
        active = 1 if bool(row.get("is_active")) else 0
        role = str(row.get("role") or "user")
        db_path = resolve_auth_db_path()
        scopes = get_user_scopes(db_path, int(row.get("id")))
        reports = scopes.get("reports") or list(_REPORT_KEYS)
        buildings = scopes.get("buildings") or []
        return active, role, "", reports, buildings

    @app.callback(
        Output("admin-message", "children"),
        Input("admin-add-user-btn", "n_clicks"),
        Input("admin-save-user-btn", "n_clicks"),
        State("admin-add-username", "value"),
        State("admin-add-password", "value"),
        State("admin-add-role", "value"),
        State("admin-add-active", "value"),
        State("admin-users-table", "selected_rows"),
        State("admin-users-table", "data"),
        State("admin-edit-active", "value"),
        State("admin-edit-role", "value"),
        State("admin-edit-password", "value"),
        State("admin-edit-reports", "value"),
        State("admin-edit-buildings", "value"),
    )
    def handle_admin_actions(
        add_clicks,
        save_clicks,
        add_username,
        add_password,
        add_role,
        add_active,
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
                    return html.Div("Username and password are required.", style={"color": "#b91c1c"})
                is_active = 1 if int(add_active) == 1 else 0

                upsert_user(db_path, username, password, role, is_active=bool(is_active))
                return html.Div(f"User '{username}' added/updated.", style={"color": "#047857"})

            if tid == "admin-save-user-btn":
                if not selected_rows or not table_data:
                    return html.Div("Select a user row first.", style={"color": "#b91c1c"})
                idx = selected_rows[0]
                if idx is None or idx >= len(table_data):
                    return html.Div("Invalid selection.", style={"color": "#b91c1c"})
                row = table_data[idx]
                user_id = int(row.get("id"))
                desired_active = 1 if int(edit_active) == 1 else 0
                desired_role = str(edit_role or row.get("role") or "user").strip().lower()
                desired_password = (edit_password or "").strip()

                # Prevent disabling the currently logged-in admin.
                if str(user_id) == str(current_user_id) and desired_active == 0:
                    return html.Div("You can't disable your own active admin account.", style={"color": "#b91c1c"})

                current_active = 1 if bool(row.get("is_active")) else 0
                if desired_active != current_active:
                    set_user_active(db_path, user_id, desired_active == 1)
                current_role = str(row.get("role") or "user")
                if desired_role != current_role:
                    set_user_role(db_path, user_id, desired_role)

                if desired_password:
                    set_user_password(db_path, user_id, desired_password)
                set_user_scopes(
                    db_path,
                    user_id,
                    edit_reports or [],
                    sorted(_normalize_building_scope(edit_buildings or [])),
                )

                return html.Div("Changes saved.", style={"color": "#047857"})

            return no_update
        except ValueError as e:
            return html.Div(str(e), style={"color": "#b91c1c"})
        except Exception:
            return html.Div("Admin action failed. Check inputs and try again.", style={"color": "#b91c1c"})

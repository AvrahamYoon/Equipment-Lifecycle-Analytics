"""Admin page body."""

from dash import dcc, html, dash_table

from dashboard import constants as C

_REPORT_OPTIONS = [
    {"label": "Overview", "value": "overview"},
    {"label": "Replacement", "value": "replacement"},
    {"label": "Order roster", "value": "orders"},
    {"label": "Settings", "value": "settings"},
]
_ROLE_OPTIONS = [
    {"label": "admin", "value": "admin"},
    {"label": "co-admin", "value": "co-admin"},
    {"label": "user", "value": "user"},
]
_DEFAULT_REPORTS = ["overview", "replacement", "orders", "settings"]


def admin_page_body():
    muted = {"fontSize": 13, "color": C.COLOR_TEXT_SECONDARY, "lineHeight": 1.5, "maxWidth": 720}
    label = {
        "fontSize": 11,
        "fontWeight": 600,
        "color": C.COLOR_TEXT_MUTED,
        "letterSpacing": "0.08em",
        "textTransform": "uppercase",
        "marginBottom": 6,
        "display": "block",
    }
    inp = {
        "width": "100%",
        "padding": "10px 12px",
        "borderRadius": 8,
        "border": f"1px solid {C.COLOR_BORDER}",
        "fontSize": 14,
        "fontFamily": "inherit",
        "boxSizing": "border-box",
    }
    field_hint = {"fontSize": 11, "color": C.COLOR_TEXT_MUTED, "marginTop": 4, "marginBottom": 10, "display": "block"}
    password_hint = "8-128 characters; letters, numbers, and common symbols only."
    username_hint = "2-32 characters; letters, numbers, . _ - only."

    return html.Div(
        [
            html.Div(
                [
                    html.H2(
                        "Admin - User management",
                        style={
                            "margin": "0 0 6px",
                            "fontSize": 22,
                            "fontWeight": 800,
                            "color": C.COLOR_TEXT_PRIMARY,
                        },
                    ),
                    html.P(
                        "Create accounts, manage roles and permissions, reset passwords, or remove users.",
                        style=muted,
                    ),
                ],
                style={**C.CARD_STYLE, "padding": "18px 22px", "marginBottom": 16},
            ),
            html.Div(
                dash_table.DataTable(
                    id="admin-users-table",
                    columns=[
                        {"name": "#", "id": "display_id"},
                        {"name": "Username", "id": "username"},
                        {"name": "Role", "id": "role"},
                        {"name": "Active", "id": "active_label"},
                        {"name": "Reports", "id": "reports_summary"},
                        {"name": "Created", "id": "created_at"},
                        {"name": "Last login", "id": "last_login_at"},
                    ],
                    data=[],
                    row_selectable="single",
                    selected_rows=[],
                    page_action="none",
                    style_table={"overflowX": "auto", "borderRadius": 0},
                    style_cell={
                        "fontFamily": "inherit",
                        "padding": "10px 8px",
                        "border": "none",
                        "whiteSpace": "nowrap",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                    },
                    style_header={
                        "background": "#f8fafc",
                        "color": "#64748b",
                        "fontWeight": 800,
                        "borderBottom": f"1px solid {C.COLOR_BORDER}",
                    },
                ),
                style={**C.CARD_STYLE, "padding": "18px 22px", "marginBottom": 16},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("Add user", style={"fontWeight": 800, "marginBottom": 12}),
                            html.Label("Username", style=label),
                            dcc.Input(id="admin-add-username", type="text", placeholder="e.g. analyst1", style=inp),
                            html.Span(username_hint, style=field_hint),
                            html.Label("Password", style=label),
                            dcc.Input(id="admin-add-password", type="password", placeholder="Set password", style=inp),
                            html.Span(password_hint, style=field_hint),
                            html.Label("Role", style=label),
                            dcc.Dropdown(
                                id="admin-add-role",
                                options=_ROLE_OPTIONS,
                                value="user",
                                clearable=False,
                                style={"fontSize": 13},
                            ),
                            html.Label("Active", style=label),
                            dcc.RadioItems(
                                id="admin-add-active",
                                options=[{"label": "Active", "value": 1}, {"label": "Disabled", "value": 0}],
                                value=1,
                                inline=True,
                            ),
                            html.Label("Visible reports", style=label),
                            dcc.Checklist(
                                id="admin-add-reports",
                                options=_REPORT_OPTIONS,
                                value=list(_DEFAULT_REPORTS),
                                inline=False,
                            ),
                            html.Label("Allowed buildings (empty = all)", style=label),
                            dcc.Dropdown(
                                id="admin-add-buildings",
                                options=[],
                                value=[],
                                multi=True,
                                placeholder="Select building/location values",
                                style={"fontSize": 13},
                            ),
                            html.Div(
                                id="admin-add-scope-hint",
                                style={"fontSize": 12, "color": C.COLOR_TEXT_MUTED, "marginTop": 8},
                            ),
                            html.Button(
                                "Add user",
                                id="admin-add-user-btn",
                                n_clicks=0,
                                className="btn-primary",
                                style={"marginTop": 14},
                            ),
                        ],
                        style={**C.CARD_STYLE, "padding": "18px 20px", "flex": "1", "minWidth": 320},
                    ),
                    html.Div(
                        [
                            html.Div("Edit selected user", style={"fontWeight": 800, "marginBottom": 12}),
                            html.Div(
                                id="admin-edit-username",
                                style={"fontSize": 13, "color": C.COLOR_TEXT_SECONDARY, "marginBottom": 10},
                            ),
                            html.Label("Active", style=label),
                            dcc.RadioItems(
                                id="admin-edit-active",
                                options=[{"label": "Active", "value": 1}, {"label": "Disabled", "value": 0}],
                                value=1,
                                inline=True,
                            ),
                            html.Label("Role", style=label),
                            dcc.Dropdown(
                                id="admin-edit-role",
                                options=_ROLE_OPTIONS,
                                value="user",
                                clearable=False,
                                style={"fontSize": 13},
                            ),
                            html.Label("New password (optional)", style=label),
                            dcc.Input(
                                id="admin-edit-password",
                                type="password",
                                placeholder="Leave blank to keep password",
                                style=inp,
                            ),
                            html.Span(password_hint, style=field_hint),
                            html.Label("Visible reports", style=label),
                            dcc.Checklist(
                                id="admin-edit-reports",
                                options=_REPORT_OPTIONS,
                                value=list(_DEFAULT_REPORTS),
                                inline=False,
                            ),
                            html.Label("Allowed buildings (empty = all)", style=label),
                            dcc.Dropdown(
                                id="admin-edit-buildings",
                                options=[],
                                value=[],
                                multi=True,
                                placeholder="Select building/location values",
                                style={"fontSize": 13},
                            ),
                            html.Div(
                                id="admin-edit-scope-hint",
                                style={"fontSize": 12, "color": C.COLOR_TEXT_MUTED, "marginTop": 8},
                            ),
                            html.Div(
                                [
                                    html.Button(
                                        "Save changes",
                                        id="admin-save-user-btn",
                                        n_clicks=0,
                                        className="btn-secondary",
                                    ),
                                    html.Button(
                                        "Delete user",
                                        id="admin-delete-user-btn",
                                        n_clicks=0,
                                        className="btn-danger",
                                        style={"marginLeft": 10},
                                    ),
                                ],
                                style={"marginTop": 14, "display": "flex", "flexWrap": "wrap", "gap": 10},
                            ),
                        ],
                        style={**C.CARD_STYLE, "padding": "18px 20px", "flex": "1", "minWidth": 320},
                    ),
                ],
                style={"display": "flex", "gap": 16, "flexWrap": "wrap"},
            ),
            dcc.ConfirmDialog(
                id="admin-delete-confirm",
                message="Delete this user permanently? Their permissions will be removed and this cannot be undone.",
            ),
            html.Div(id="admin-message", style={"marginTop": 10, "fontSize": 13, "color": C.COLOR_TEXT_SECONDARY}),
        ],
        id="page-admin",
        className="app-page app-page--standard",
        style={"display": "none"},
    )

"""Admin page body."""

from dash import dcc, html, dash_table

from dashboard import constants as C


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
                        "Add admin accounts, enable/disable users, and reset passwords.",
                        style=muted,
                    ),
                ],
                style={**C.CARD_STYLE, "padding": "18px 22px", "marginBottom": 16},
            ),
            html.Div(
                dash_table.DataTable(
                    id="admin-users-table",
                    columns=[
                        {"name": "Username", "id": "username"},
                        {"name": "Role", "id": "role"},
                        {"name": "Active", "id": "is_active"},
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
                            dcc.Input(id="admin-add-username", type="text", placeholder="e.g. admin2", style=inp),
                            html.Label("Password", style=label),
                            dcc.Input(id="admin-add-password", type="password", placeholder="Set password", style=inp),
                            html.Label("Role", style=label),
                            dcc.Dropdown(
                                id="admin-add-role",
                                options=[
                                    {"label": "admin", "value": "admin"},
                                    {"label": "co-admin", "value": "co-admin"},
                                    {"label": "user", "value": "user"},
                                ],
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
                                options=[
                                    {"label": "admin", "value": "admin"},
                                    {"label": "co-admin", "value": "co-admin"},
                                    {"label": "user", "value": "user"},
                                ],
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
                            html.Button(
                                "Save changes",
                                id="admin-save-user-btn",
                                n_clicks=0,
                                className="btn-secondary",
                                style={"marginTop": 14},
                            ),
                        ],
                        style={**C.CARD_STYLE, "padding": "18px 20px", "flex": "1", "minWidth": 320},
                    ),
                ],
                style={"display": "flex", "gap": 16, "flexWrap": "wrap"},
            ),
            html.Div(id="admin-message", style={"marginTop": 10, "fontSize": 13, "color": C.COLOR_TEXT_SECONDARY}),
        ],
        id="page-admin",
        style={
            "display": "none",
            "padding": "24px 28px 40px",
            "maxWidth": 1280,
            "margin": "0 auto",
            "minWidth": 0,
        },
    )

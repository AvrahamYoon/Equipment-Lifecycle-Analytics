"""Root layout: left nav + header + two page panels (toggle visibility)."""

from dash import dcc, html

from dashboard import constants as C


def overview_page_body():
    return html.Div(
        [
            html.Div(
                id="kpi-row",
                style={"display": "flex", "flexWrap": "wrap", "gap": 14, "marginBottom": 20},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Graph(
                                id="hours-chart",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 280},
                            ),
                        ],
                        style={**C.CARD_STYLE, "flex": "1", "minWidth": 320, "padding": "16px 8px 8px"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="calendar-chart",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 280},
                            ),
                        ],
                        style={**C.CARD_STYLE, "flex": "1", "minWidth": 320, "padding": "16px 8px 8px"},
                    ),
                ],
                style={"display": "flex", "gap": 16, "marginBottom": 20},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Graph(
                                id="completion-gauge",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 260},
                            ),
                        ],
                        style={**C.CARD_STYLE, "flex": "1", "minWidth": 240, "padding": "16px 8px 8px"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="avghours-gauge",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 260},
                            ),
                        ],
                        style={**C.CARD_STYLE, "flex": "1", "minWidth": 240, "padding": "16px 8px 8px"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="staff-chart",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 260},
                            ),
                        ],
                        style={**C.CARD_STYLE, "flex": "2", "minWidth": 320, "padding": "16px 8px 8px"},
                    ),
                ],
                style={"display": "flex", "gap": 16, "marginBottom": 20},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Graph(
                                id="turnaround-chart",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 300},
                            ),
                        ],
                        style={**C.CARD_STYLE, "flex": "1", "minWidth": 320, "padding": "16px 8px 8px"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="availability-chart",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 300},
                            ),
                        ],
                        style={**C.CARD_STYLE, "flex": "1", "minWidth": 320, "padding": "16px 8px 8px"},
                    ),
                ],
                style={"display": "flex", "gap": 16, "marginBottom": 20},
            ),
            html.Div(
                id="footer-text",
                style={
                    "textAlign": "center",
                    "fontSize": 11,
                    "color": C.COLOR_TEXT_MUTED,
                    "paddingBottom": 8,
                },
            ),
        ],
        id="page-overview",
        style={
            "display": "block",
            "padding": "24px 28px",
            "maxWidth": 1400,
            "margin": "0 auto",
            "flex": "1",
            "minWidth": 0,
        },
    )


def replacement_page_body():
    from dash import dash_table

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("🚦", style={"fontSize": 16, "marginRight": 8}),
                            html.Span(
                                "Equipment Replacement Indicator",
                                style={
                                    "fontSize": 14,
                                    "fontWeight": 700,
                                    "color": C.COLOR_TEXT_PRIMARY,
                                },
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center", "marginBottom": 6},
                    ),
                    html.Div(
                        [
                            html.Span("🔴 Replace", style={"color": "#dc2626", "fontWeight": 600, "marginRight": 16}),
                            html.Span(
                                "(Labor+Parts)×0.80 ≥ New Price",
                                style={"color": C.COLOR_TEXT_MUTED, "marginRight": 24},
                            ),
                            html.Span("🟡 Monitor", style={"color": "#d97706", "fontWeight": 600, "marginRight": 16}),
                            html.Span(
                                "(Labor+Parts)×0.60 ≥ New Price",
                                style={"color": C.COLOR_TEXT_MUTED, "marginRight": 24},
                            ),
                            html.Span("🟢 Good", style={"color": "#059669", "fontWeight": 600, "marginRight": 16}),
                            html.Span("Below threshold", style={"color": C.COLOR_TEXT_MUTED}),
                        ],
                        style={
                            "fontSize": 12,
                            "marginBottom": 16,
                            "flexWrap": "wrap",
                            "display": "flex",
                            "gap": 4,
                        },
                    ),
                ]
            ),
            dash_table.DataTable(
                id="replace-table",
                style_table={"overflowX": "auto", "borderRadius": 10, "overflow": "hidden"},
                style_header={
                    "backgroundColor": "#f8fafc",
                    "color": C.COLOR_TEXT_SECONDARY,
                    "fontWeight": "700",
                    "fontSize": 11,
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                    "borderBottom": f"2px solid {C.COLOR_BORDER}",
                    "padding": "10px 14px",
                    "border": "none",
                },
                style_cell={
                    "backgroundColor": C.BG_CARD,
                    "color": C.COLOR_TEXT_PRIMARY,
                    "fontSize": 13,
                    "padding": "10px 14px",
                    "border": "none",
                    "borderBottom": f"1px solid {C.COLOR_BORDER}",
                    "fontFamily": "'DM Sans','Segoe UI',sans-serif",
                },
                style_data_conditional=[],
            ),
        ],
        id="page-replacement",
        style={
            "display": "none",
            "padding": "24px 28px",
            "maxWidth": 1400,
            "margin": "0 auto",
            "flex": "1",
            "minWidth": 0,
        },
    )


def build_root_layout(month_options, default_month):
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            html.Div(
                [
                    html.Div("Navigation", style={"fontSize": 10, "color": C.COLOR_TEXT_MUTED, "marginBottom": 8}),
                    html.Div(
                        dcc.Link(
                            "Overview",
                            href="/",
                            style={"color": "inherit", "textDecoration": "none"},
                        ),
                        id="nav-wrap-overview",
                        style={
                            "padding": "10px 14px",
                            "borderRadius": 8,
                            "marginBottom": 4,
                            "background": "#e8f1fe",
                            "color": C.COLOR_TEXT_PRIMARY,
                            "fontWeight": 700,
                            "fontSize": 14,
                        },
                    ),
                    html.Div(
                        dcc.Link(
                            "Replacement table",
                            href="/replacement",
                            style={"color": "inherit", "textDecoration": "none"},
                        ),
                        id="nav-wrap-replacement",
                        style={
                            "padding": "10px 14px",
                            "borderRadius": 8,
                            "marginBottom": 4,
                            "background": "transparent",
                            "color": C.COLOR_TEXT_SECONDARY,
                            "fontWeight": 500,
                            "fontSize": 14,
                        },
                    ),
                ],
                style={
                    "width": 220,
                    "flexShrink": 0,
                    "background": C.BG_HEADER,
                    "borderRight": f"1px solid {C.COLOR_BORDER}",
                    "padding": "20px 16px",
                    "minHeight": "100vh",
                    "boxSizing": "border-box",
                },
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span(
                                        "Facilities Management Services",
                                        style={
                                            "fontSize": 10,
                                            "letterSpacing": "0.18em",
                                            "color": C.C_BLUE,
                                            "fontWeight": 700,
                                            "textTransform": "uppercase",
                                        },
                                    ),
                                    html.H1(
                                        "Work Order Dashboard",
                                        style={
                                            "margin": "4px 0 2px",
                                            "fontSize": 24,
                                            "color": C.COLOR_TEXT_PRIMARY,
                                            "fontWeight": 800,
                                            "lineHeight": 1.2,
                                        },
                                    ),
                                    html.Span(
                                        "Custodial Equipment Repair & Service Tracker",
                                        style={"fontSize": 13, "color": C.COLOR_TEXT_SECONDARY},
                                    ),
                                ]
                            ),
                            html.Div(
                                [
                                    html.Label(
                                        "Month",
                                        style={
                                            "fontSize": 11,
                                            "fontWeight": 600,
                                            "color": C.COLOR_TEXT_MUTED,
                                            "letterSpacing": "0.08em",
                                            "textTransform": "uppercase",
                                            "marginBottom": 5,
                                            "display": "block",
                                        },
                                    ),
                                    dcc.Dropdown(
                                        id="month-select",
                                        options=month_options,
                                        value=default_month,
                                        clearable=False,
                                        style={"width": 180, "fontFamily": "inherit", "fontSize": 13},
                                    ),
                                ]
                            ),
                        ],
                        style={
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "center",
                            "flexWrap": "wrap",
                            "gap": 16,
                            "background": C.BG_HEADER,
                            "borderBottom": f"1px solid {C.COLOR_BORDER}",
                            "padding": "20px 28px",
                            "boxShadow": "0 1px 3px rgba(0,0,0,0.05)",
                        },
                    ),
                    html.Div([overview_page_body(), replacement_page_body()]),
                ],
                style={"flex": "1", "minWidth": 0, "background": C.BG_PAGE},
            ),
        ],
        style={
            "display": "flex",
            "minHeight": "100vh",
            "fontFamily": "'DM Sans','Segoe UI',sans-serif",
            "color": C.COLOR_TEXT_PRIMARY,
        },
    )

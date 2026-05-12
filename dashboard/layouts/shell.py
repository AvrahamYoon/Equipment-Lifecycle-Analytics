"""Root layout: left nav + header + page panels (overview / replacement / settings)."""

from dash import dcc, html

from dashboard import constants as C

_DEFAULTS = C.default_app_settings()


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
                                style={"height": 320},
                            ),
                        ],
                        style={**C.CARD_STYLE, "flex": "1", "minWidth": 320, "padding": "16px 8px 8px"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="availability-chart",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 320},
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
            "maxWidth": 1240,
            "margin": "0 auto",
            "minWidth": 0,
        },
    )


def replacement_page_body():
    from dash import dash_table

    d = _DEFAULTS
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                id="replace-page-title-icon",
                                children=d["iconReplaceTitle"],
                                style={"fontSize": 16, "marginRight": 8, "lineHeight": 1},
                            ),
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
                            html.Span(
                                [
                                    html.Span(
                                        id="replace-legend-ico-replace",
                                        children=d["iconReplaceStatusReplace"],
                                        style={"fontWeight": 600},
                                    ),
                                    html.Span(" Replace", style={"color": "#dc2626", "fontWeight": 600}),
                                ],
                                style={"marginRight": 16, "display": "inline-flex", "alignItems": "baseline"},
                            ),
                            html.Span(
                                "(Labor+Parts)×0.80 ≥ New Price",
                                style={"color": C.COLOR_TEXT_MUTED, "marginRight": 24},
                            ),
                            html.Span(
                                [
                                    html.Span(
                                        id="replace-legend-ico-monitor",
                                        children=d["iconReplaceStatusMonitor"],
                                        style={"fontWeight": 600},
                                    ),
                                    html.Span(" Monitor", style={"color": "#d97706", "fontWeight": 600}),
                                ],
                                style={"marginRight": 16, "display": "inline-flex", "alignItems": "baseline"},
                            ),
                            html.Span(
                                "(Labor+Parts)×0.60 ≥ New Price",
                                style={"color": C.COLOR_TEXT_MUTED, "marginRight": 24},
                            ),
                            html.Span(
                                [
                                    html.Span(
                                        id="replace-legend-ico-good",
                                        children=d["iconReplaceStatusGood"],
                                        style={"fontWeight": 600},
                                    ),
                                    html.Span(" Good", style={"color": "#059669", "fontWeight": 600}),
                                ],
                                style={"marginRight": 16, "display": "inline-flex", "alignItems": "baseline"},
                            ),
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
            "maxWidth": 1240,
            "margin": "0 auto",
            "minWidth": 0,
        },
    )


def settings_page_body():
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
        "width": 120,
        "padding": "8px 10px",
        "borderRadius": 8,
        "border": f"1px solid {C.COLOR_BORDER}",
        "fontSize": 14,
        "fontFamily": "inherit",
    }

    def section(title, desc, children):
        return html.Div(
            [
                html.Div(title, style={"fontSize": 15, "fontWeight": 700, "marginBottom": 6}),
                html.Div(desc, style={**muted, "marginBottom": 14}),
                html.Div(children, style={"display": "flex", "flexWrap": "wrap", "gap": 20}),
            ],
            style={**C.CARD_STYLE, "padding": "20px 22px", "marginBottom": 16},
        )

    return html.Div(
        [
            html.Div(
                [
                    html.H2(
                        "Settings",
                        style={
                            "margin": "0 0 6px",
                            "fontSize": 22,
                            "fontWeight": 800,
                            "color": C.COLOR_TEXT_PRIMARY,
                        },
                    ),
                    html.P(
                        "Tune assumptions used on the Overview page. Values are saved in this browser "
                        "(local storage).",
                        style={**muted, "marginBottom": 20},
                    ),
                ]
            ),
            section(
                "Staff capacity (utilization bar)",
                "Saved per calendar month using the Month selector in the header. "
                "Choose the month, edit staff count / hours per day / work days in that month, then Apply. "
                "Months you have not saved yet use the global defaults shown in these fields (they are updated "
                "when you Apply). The Overview utilization bar always follows the month currently selected "
                "in the header.",
                [
                    html.Div(
                        [
                            html.Label("Staff count", style=label),
                            dcc.Input(
                                id="settings-staff-count",
                                type="number",
                                min=1,
                                step=1,
                                value=_DEFAULTS["staffCount"],
                                style=inp,
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Label("Hours per staff / day", style=label),
                            dcc.Input(
                                id="settings-hours-day",
                                type="number",
                                min=0.25,
                                step=0.25,
                                value=_DEFAULTS["hoursPerDay"],
                                style=inp,
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Label("Work days in month", style=label),
                            dcc.Input(
                                id="settings-work-days",
                                type="number",
                                min=1,
                                max=31,
                                step=1,
                                value=_DEFAULTS["workDays"],
                                style=inp,
                            ),
                        ]
                    ),
                ],
            ),
            section(
                "Availability model",
                "Base period (days) caps downtime per asset when computing the availability % chart.",
                [
                    html.Div(
                        [
                            html.Label("Base availability days", style=label),
                            dcc.Input(
                                id="settings-base-avail",
                                type="number",
                                min=1,
                                step=1,
                                value=_DEFAULTS["baseAvailDays"],
                                style=inp,
                            ),
                        ]
                    ),
                ],
            ),
            section(
                "Request calendar",
                "Choose whether the calendar grid labels start on Sunday or Monday.",
                [
                    html.Div(
                        [
                            html.Label("First day of week", style=label),
                            dcc.Dropdown(
                                id="settings-week-starts",
                                options=[
                                    {"label": "Sunday", "value": "sunday"},
                                    {"label": "Monday", "value": "monday"},
                                ],
                                value=_DEFAULTS["weekStartsOn"],
                                clearable=False,
                                style={"width": 220, "fontFamily": "inherit", "fontSize": 13},
                            ),
                        ]
                    ),
                ],
            ),
            section(
                "Icons",
                "Short text or emoji for KPI cards, left navigation, and the Replacement page. "
                "Leave blank to restore the built-in default for that slot.",
                [
                    html.Div(
                        [
                            html.Div("Overview KPIs", style={"fontWeight": 700, "fontSize": 12, "marginBottom": 10}),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label("Requests", style=label),
                                            dcc.Input(
                                                id="settings-iconKpiRequests",
                                                type="text",
                                                value=_DEFAULTS["iconKpiRequests"],
                                                style={**inp, "width": 88},
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.Label("Completed", style=label),
                                            dcc.Input(
                                                id="settings-iconKpiCompleted",
                                                type="text",
                                                value=_DEFAULTS["iconKpiCompleted"],
                                                style={**inp, "width": 88},
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.Label("Scheduled", style=label),
                                            dcc.Input(
                                                id="settings-iconKpiScheduled",
                                                type="text",
                                                value=_DEFAULTS["iconKpiScheduled"],
                                                style={**inp, "width": 88},
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.Label("Repair cost", style=label),
                                            dcc.Input(
                                                id="settings-iconKpiRepairCost",
                                                type="text",
                                                value=_DEFAULTS["iconKpiRepairCost"],
                                                style={**inp, "width": 88},
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.Label("Parts", style=label),
                                            dcc.Input(
                                                id="settings-iconKpiParts",
                                                type="text",
                                                value=_DEFAULTS["iconKpiParts"],
                                                style={**inp, "width": 88},
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.Label("Labor", style=label),
                                            dcc.Input(
                                                id="settings-iconKpiLabor",
                                                type="text",
                                                value=_DEFAULTS["iconKpiLabor"],
                                                style={**inp, "width": 88},
                                            ),
                                        ]
                                    ),
                                ],
                                style={"display": "flex", "flexWrap": "wrap", "gap": 16},
                            ),
                        ],
                        style={"width": "100%"},
                    ),
                    html.Div(
                        [
                            html.Div("Navigation", style={"fontWeight": 700, "fontSize": 12, "marginBottom": 10}),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label("Overview link", style=label),
                                            dcc.Input(
                                                id="settings-iconNavOverview",
                                                type="text",
                                                value=_DEFAULTS["iconNavOverview"],
                                                style={**inp, "width": 88},
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.Label("Replacement link", style=label),
                                            dcc.Input(
                                                id="settings-iconNavReplacement",
                                                type="text",
                                                value=_DEFAULTS["iconNavReplacement"],
                                                style={**inp, "width": 88},
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.Label("Settings link", style=label),
                                            dcc.Input(
                                                id="settings-iconNavSettings",
                                                type="text",
                                                value=_DEFAULTS["iconNavSettings"],
                                                style={**inp, "width": 88},
                                            ),
                                        ]
                                    ),
                                ],
                                style={"display": "flex", "flexWrap": "wrap", "gap": 16},
                            ),
                        ],
                        style={"width": "100%"},
                    ),
                    html.Div(
                        [
                            html.Div("Replacement page", style={"fontWeight": 700, "fontSize": 12, "marginBottom": 10}),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label("Title", style=label),
                                            dcc.Input(
                                                id="settings-iconReplaceTitle",
                                                type="text",
                                                value=_DEFAULTS["iconReplaceTitle"],
                                                style={**inp, "width": 88},
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.Label("Replace row", style=label),
                                            dcc.Input(
                                                id="settings-iconReplaceStatusReplace",
                                                type="text",
                                                value=_DEFAULTS["iconReplaceStatusReplace"],
                                                style={**inp, "width": 88},
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.Label("Monitor row", style=label),
                                            dcc.Input(
                                                id="settings-iconReplaceStatusMonitor",
                                                type="text",
                                                value=_DEFAULTS["iconReplaceStatusMonitor"],
                                                style={**inp, "width": 88},
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.Label("Good row", style=label),
                                            dcc.Input(
                                                id="settings-iconReplaceStatusGood",
                                                type="text",
                                                value=_DEFAULTS["iconReplaceStatusGood"],
                                                style={**inp, "width": 88},
                                            ),
                                        ]
                                    ),
                                ],
                                style={"display": "flex", "flexWrap": "wrap", "gap": 16},
                            ),
                        ],
                        style={"width": "100%"},
                    ),
                ],
            ),
            html.Div(
                [
                    html.Div("Data sources", style={"fontSize": 15, "fontWeight": 700, "marginBottom": 6}),
                    html.P(
                        "CSV folders and the equipment summary path are configured in "
                        "dashboard/constants.py (REQUESTS_DIR, SERVICE_DIR, REPAIRS_DIR, "
                        "EQUIPMENT_SUMMARY_CSV). Restart the app after changing paths.",
                        style=muted,
                    ),
                ],
                style={**C.CARD_STYLE, "padding": "20px 22px", "marginBottom": 20},
            ),
            html.Div(
                [
                    html.Button(
                        "Apply",
                        id="settings-apply",
                        n_clicks=0,
                        style={
                            "padding": "10px 22px",
                            "borderRadius": 8,
                            "border": "none",
                            "background": C.C_BLUE,
                            "color": "white",
                            "fontWeight": 700,
                            "fontSize": 14,
                            "cursor": "pointer",
                            "marginRight": 10,
                        },
                    ),
                    html.Button(
                        "Reset to defaults",
                        id="settings-reset",
                        n_clicks=0,
                        style={
                            "padding": "10px 22px",
                            "borderRadius": 8,
                            "border": f"1px solid {C.COLOR_BORDER}",
                            "background": C.BG_CARD,
                            "color": C.COLOR_TEXT_PRIMARY,
                            "fontWeight": 600,
                            "fontSize": 14,
                            "cursor": "pointer",
                        },
                    ),
                ],
                style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": 8},
            ),
        ],
        id="page-settings",
        style={
            "display": "none",
            "padding": "24px 28px",
            "maxWidth": 1240,
            "margin": "0 auto",
            "minWidth": 0,
        },
    )


def build_root_layout(month_options, default_month):
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="settings-store", storage_type="local", data=C.default_app_settings()),
            html.Div(
                [
                    html.Div("Navigation", style={"fontSize": 10, "color": C.COLOR_TEXT_MUTED, "marginBottom": 8}),
                    html.Div(
                        dcc.Link(
                            [
                                html.Span(
                                    id="nav-icon-overview",
                                    children=_DEFAULTS["iconNavOverview"],
                                    style={
                                        "marginRight": 8,
                                        "fontSize": 16,
                                        "lineHeight": 1,
                                        "display": "inline-block",
                                        "minWidth": "1.1em",
                                    },
                                ),
                                "Overview",
                            ],
                            href="/",
                            style={
                                "color": "inherit",
                                "textDecoration": "none",
                                "display": "flex",
                                "alignItems": "center",
                            },
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
                            [
                                html.Span(
                                    id="nav-icon-replacement",
                                    children=_DEFAULTS["iconNavReplacement"],
                                    style={
                                        "marginRight": 8,
                                        "fontSize": 16,
                                        "lineHeight": 1,
                                        "display": "inline-block",
                                        "minWidth": "1.1em",
                                    },
                                ),
                                "Replacement table",
                            ],
                            href="/replacement",
                            style={
                                "color": "inherit",
                                "textDecoration": "none",
                                "display": "flex",
                                "alignItems": "center",
                            },
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
                    html.Div(
                        dcc.Link(
                            [
                                html.Span(
                                    id="nav-icon-settings",
                                    children=_DEFAULTS["iconNavSettings"],
                                    style={
                                        "marginRight": 8,
                                        "fontSize": 16,
                                        "lineHeight": 1,
                                        "display": "inline-block",
                                        "minWidth": "1.1em",
                                    },
                                ),
                                "Settings",
                            ],
                            href="/settings",
                            style={
                                "color": "inherit",
                                "textDecoration": "none",
                                "display": "flex",
                                "alignItems": "center",
                            },
                        ),
                        id="nav-wrap-settings",
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
                    "height": "100vh",
                    "overflowY": "auto",
                    "overflowX": "hidden",
                    "background": C.BG_HEADER,
                    "borderRight": f"1px solid {C.COLOR_BORDER}",
                    "padding": "20px 16px",
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
                            "flexShrink": 0,
                        },
                    ),
                    html.Div(
                        [overview_page_body(), replacement_page_body(), settings_page_body()],
                        id="main-scroll",
                        style={
                            "flex": "1",
                            "minHeight": 0,
                            "overflowY": "auto",
                            "overflowX": "hidden",
                            "WebkitOverflowScrolling": "touch",
                        },
                    ),
                ],
                style={
                    "flex": "1",
                    "minWidth": 0,
                    "minHeight": 0,
                    "display": "flex",
                    "flexDirection": "column",
                    "overflow": "hidden",
                    "background": C.BG_PAGE,
                },
            ),
        ],
        style={
            "display": "flex",
            "height": "100vh",
            "overflow": "hidden",
            "fontFamily": "'DM Sans','Segoe UI',sans-serif",
            "color": C.COLOR_TEXT_PRIMARY,
        },
    )

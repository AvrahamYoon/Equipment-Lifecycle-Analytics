"""Settings page body."""

from dash import dcc, html

from dashboard import constants as C

_DEFAULTS = C.default_app_settings()


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
                        "These values drive the Overview page (KPIs, charts, staff utilization, availability, "
                        "request calendar) and how the header month selector scopes data. "
                        "The Replacement page always uses cumulative repair totals and ignores that selector.",
                        style={**muted, "marginBottom": 20},
                    ),
                ]
            ),
            section(
                "Staff capacity (Overview utilization bar)",
                "Overview only — does not affect Replacement. Saved per calendar month using the Month selector "
                "in the header: pick a month, edit staff / hours / day / work days, then Apply. "
                "When the header shows All months, Apply updates only the global defaults shown here; the "
                "Overview bar in that mode scales available capacity by how many months have data. "
                "Months you have not saved yet use those globals until you Apply for that month.",
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
                "Availability model (Overview)",
                "Overview only — base period (days) caps downtime per asset when computing the availability % chart.",
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
                "Request calendar (Overview)",
                "Overview only — choose whether the request calendar grid labels start on Sunday or Monday.",
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
                "Short text or emoji for KPI cards, left navigation, and replacement / order pages. "
                "Leave blank to restore the built-in default for that slot.",
                [
                    html.Div(
                        [
                            dcc.Input(id="settings-iconKpiRequests", type="text", value=_DEFAULTS["iconKpiRequests"], style={**inp, "width": 88}),
                            dcc.Input(id="settings-iconKpiCompleted", type="text", value=_DEFAULTS["iconKpiCompleted"], style={**inp, "width": 88}),
                            dcc.Input(id="settings-iconKpiScheduled", type="text", value=_DEFAULTS["iconKpiScheduled"], style={**inp, "width": 88}),
                            dcc.Input(id="settings-iconKpiRepairCost", type="text", value=_DEFAULTS["iconKpiRepairCost"], style={**inp, "width": 88}),
                            dcc.Input(id="settings-iconKpiParts", type="text", value=_DEFAULTS["iconKpiParts"], style={**inp, "width": 88}),
                            dcc.Input(id="settings-iconKpiLabor", type="text", value=_DEFAULTS["iconKpiLabor"], style={**inp, "width": 88}),
                            dcc.Input(id="settings-iconNavOverview", type="text", value=_DEFAULTS["iconNavOverview"], style={**inp, "width": 88}),
                            dcc.Input(id="settings-iconNavReplacement", type="text", value=_DEFAULTS["iconNavReplacement"], style={**inp, "width": 88}),
                            dcc.Input(id="settings-iconNavOrders", type="text", value=_DEFAULTS["iconNavOrders"], style={**inp, "width": 88}),
                            dcc.Input(id="settings-iconNavSettings", type="text", value=_DEFAULTS["iconNavSettings"], style={**inp, "width": 88}),
                            dcc.Input(id="settings-iconReplaceTitle", type="text", value=_DEFAULTS["iconReplaceTitle"], style={**inp, "width": 88}),
                            dcc.Input(id="settings-iconReplaceStatusReplace", type="text", value=_DEFAULTS["iconReplaceStatusReplace"], style={**inp, "width": 88}),
                            dcc.Input(id="settings-iconReplaceStatusMonitor", type="text", value=_DEFAULTS["iconReplaceStatusMonitor"], style={**inp, "width": 88}),
                            dcc.Input(id="settings-iconReplaceStatusGood", type="text", value=_DEFAULTS["iconReplaceStatusGood"], style={**inp, "width": 88}),
                        ],
                        style={"display": "flex", "flexWrap": "wrap", "gap": 12},
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
                        className="btn-primary",
                        style={"marginRight": 10},
                    ),
                    html.Button(
                        "Reset to defaults",
                        id="settings-reset",
                        n_clicks=0,
                        className="btn-secondary",
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

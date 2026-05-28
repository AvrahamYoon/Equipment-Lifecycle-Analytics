"""Overview page body."""

from dash import dcc, html

from dashboard import constants as C


def overview_page_body():
    return html.Div(
        [
            html.Div(
                id="kpi-row",
                style={"display": "flex", "flexWrap": "wrap", "gap": 16, "marginBottom": 22},
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
                        className="lift-on-hover",
                        style={**C.CARD_STYLE, "gridColumn": "span 2", "padding": "16px 8px 8px"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="calendar-chart",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 280},
                            ),
                        ],
                        className="lift-on-hover",
                        style={**C.CARD_STYLE, "gridColumn": "span 2", "padding": "16px 8px 8px"},
                    ),
                ],
                style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": 16, "marginBottom": 20},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Graph(
                                id="monthly-parts-budget-chart",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 280},
                            ),
                        ],
                        className="lift-on-hover",
                        style={**C.CARD_STYLE, "gridColumn": "span 1", "padding": "16px 8px 8px"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="annual-parts-budget-chart",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 280},
                            ),
                        ],
                        className="lift-on-hover",
                        style={**C.CARD_STYLE, "gridColumn": "span 1", "padding": "16px 8px 8px"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="repair-count-mix-chart",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 280},
                            ),
                        ],
                        className="lift-on-hover",
                        style={**C.CARD_STYLE, "gridColumn": "span 1", "padding": "16px 8px 8px"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="building-hours-chart",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 280},
                            ),
                        ],
                        className="lift-on-hover",
                        style={**C.CARD_STYLE, "gridColumn": "span 1", "padding": "16px 8px 8px"},
                    ),
                ],
                style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": 16, "marginBottom": 20},
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
                        className="lift-on-hover",
                        style={**C.CARD_STYLE, "gridColumn": "span 1", "padding": "16px 8px 8px"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="avghours-gauge",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 260},
                            ),
                        ],
                        className="lift-on-hover",
                        style={**C.CARD_STYLE, "gridColumn": "span 1", "padding": "16px 8px 8px"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="staff-chart",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 260},
                            ),
                        ],
                        className="lift-on-hover",
                        style={**C.CARD_STYLE, "gridColumn": "span 2", "padding": "16px 8px 8px"},
                    ),
                ],
                style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": 16, "marginBottom": 20},
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
                        className="lift-on-hover",
                        style={**C.CARD_STYLE, "gridColumn": "span 2", "padding": "16px 8px 8px"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="availability-chart",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": 320},
                            ),
                        ],
                        className="lift-on-hover",
                        style={**C.CARD_STYLE, "gridColumn": "span 2", "padding": "16px 8px 8px"},
                    ),
                ],
                style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": 16, "marginBottom": 20},
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
            "padding": "28px 36px 40px",
            "maxWidth": 1440,
            "margin": "0 auto",
            "minWidth": 0,
        },
    )

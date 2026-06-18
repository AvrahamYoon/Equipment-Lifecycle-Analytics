"""Overview page body."""

from dash import dcc, html


def _chart_card(graph_id: str, *, wide: bool = False, tall: bool = False, wrap_id: str | None = None):
    card_class = "overview-chart-card overview-chart-card--span-2" if wide else "overview-chart-card overview-chart-card--span-1"
    graph_class = "overview-graph overview-graph--tall" if tall else "overview-graph"
    card_kwargs = {"className": f"{card_class} lift-on-hover"}
    if wrap_id:
        card_kwargs["id"] = wrap_id
    return html.Div(
        [
            dcc.Graph(
                id=graph_id,
                config={"displayModeBar": False, "responsive": True},
                className=graph_class,
                style={"height": "100%", "width": "100%"},
            ),
        ],
        **card_kwargs,
    )


def overview_page_body():
    return html.Div(
        [
            html.Div(id="kpi-row"),
            html.Div(
                [
                    _chart_card("hours-chart", wide=True),
                    _chart_card("calendar-chart", wide=True),
                ],
                className="overview-grid",
            ),
            html.Div(
                [
                    _chart_card("monthly-parts-budget-chart"),
                    _chart_card("annual-parts-budget-chart", wrap_id="annual-parts-budget-wrap"),
                    _chart_card("repair-count-mix-chart", wrap_id="repair-count-mix-wrap"),
                    _chart_card("building-hours-chart", wide=True, tall=True),
                ],
                className="overview-grid",
            ),
            html.Div(
                [
                    _chart_card("completion-gauge"),
                    _chart_card("avghours-gauge"),
                    _chart_card("staff-chart", wide=True),
                ],
                className="overview-grid",
            ),
            html.Div(
                [
                    _chart_card("turnaround-chart", wide=True, tall=True),
                    _chart_card("availability-chart", wide=True, tall=True),
                ],
                className="overview-grid",
            ),
            html.Div(
                id="footer-text",
                style={
                    "textAlign": "center",
                    "fontSize": 11,
                    "color": "#94a3b8",
                    "paddingBottom": 8,
                },
            ),
        ],
        id="page-overview",
        className="app-page app-page--wide",
        style={"display": "block"},
    )

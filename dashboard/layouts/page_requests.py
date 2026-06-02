"""Request roster page body."""

from dash import dcc, html, dash_table

from dashboard import constants as C
from dashboard.layouts.page_common import table_info_bar

_DEFAULTS = C.default_app_settings()


def request_roster_page_body():
    d = _DEFAULTS
    flabel = {"className": "filter-label"}
    _hdr = {
        "backgroundColor": "transparent",
        "color": C.COLOR_TEXT_MUTED,
        "fontWeight": "700",
        "fontSize": 10,
        "textTransform": "uppercase",
        "letterSpacing": "0.1em",
        "borderBottom": f"1px solid {C.COLOR_BORDER}",
        "padding": "14px 16px",
        "border": "none",
    }
    _cell = {
        "backgroundColor": C.BG_CARD,
        "color": C.COLOR_TEXT_PRIMARY,
        "fontSize": 13,
        "padding": "14px 16px",
        "border": "none",
        "borderBottom": f"1px solid rgba(226, 232, 240, 0.7)",
        "fontFamily": "inherit",
    }
    _tbl = {"overflowX": "auto", "borderRadius": 0, "overflow": "hidden", "border": "none"}

    hero = html.Div(
        [
            html.Div(
                [
                    html.Span(
                        id="request-page-title-icon",
                        children=d.get("iconNavRequests", d["iconKpiRequests"]),
                        style={"fontSize": 26, "marginRight": 14, "lineHeight": 1},
                    ),
                    html.Div(
                        [
                            html.H2("Request roster"),
                            html.P(
                                "Work requests for the month selected in the header. "
                                "Click a day on the Overview calendar or a month on the volume chart to jump here with filters applied.",
                                className="page-hero-desc",
                            ),
                        ]
                    ),
                ],
                style={"display": "flex", "alignItems": "flex-start"},
            ),
        ],
        className="page-hero",
    )

    toolbar = html.Div(
        [
            html.Div(
                [
                    html.Label("Day of month", **flabel),
                    dcc.Input(
                        id="request-filter-day",
                        type="number",
                        min=1,
                        max=31,
                        placeholder="Any",
                        debounce=True,
                        className="filter-input",
                        style={"maxWidth": 100},
                    ),
                ],
                style={"minWidth": 120},
            ),
            html.Div(
                [
                    html.Label("Work order contains", **flabel),
                    dcc.Input(
                        id="request-filter-work-order",
                        type="text",
                        placeholder="e.g. FM-376392",
                        debounce=True,
                        className="filter-input",
                    ),
                ],
                style={"flex": "1", "minWidth": 160},
            ),
            html.Div(
                [
                    html.Label("Requestor contains", **flabel),
                    dcc.Input(
                        id="request-filter-requestor",
                        type="text",
                        debounce=True,
                        className="filter-input",
                    ),
                ],
                style={"flex": "1", "minWidth": 160},
            ),
            html.Div(
                [
                    html.Label("Request text contains", **flabel),
                    dcc.Input(
                        id="request-filter-text",
                        type="text",
                        debounce=True,
                        className="filter-input",
                    ),
                ],
                style={"flex": "2", "minWidth": 200},
            ),
        ],
        className="fm-toolbar",
        style={
            "display": "flex",
            "flexWrap": "wrap",
            "gap": 16,
            "alignItems": "flex-end",
        },
    )

    cell_cond = [
        {"if": {"column_id": "Work order"}, "minWidth": 120, "maxWidth": 150, "fontWeight": 600},
        {"if": {"column_id": "Request date"}, "minWidth": 110, "maxWidth": 130, "textAlign": "right"},
        {"if": {"column_id": "Requestor"}, "minWidth": 140, "maxWidth": 200},
        {"if": {"column_id": "Request"}, "minWidth": 280},
        {"if": {"column_id": "Assigned to"}, "minWidth": 140, "maxWidth": 200},
    ]
    header_cond = [
        {"if": {"column_id": "Request date"}, "textAlign": "right"},
    ]

    return html.Div(
        [
            hero,
            toolbar,
            table_info_bar(
                row_count_id="request-row-count",
                page_size_id="request-page-size",
                item_label="requests",
            ),
            html.Div(
                [
                    dash_table.DataTable(
                        id="request-roster-table",
                        style_table={**_tbl, "maxHeight": "62vh"},
                        style_header=_hdr,
                        style_cell=_cell,
                        style_cell_conditional=cell_cond,
                        style_header_conditional=header_cond,
                        style_data_conditional=[],
                        page_size=C.DEFAULT_PAGE_SIZE,
                        page_action="native",
                        sort_action="native",
                        fixed_rows={"headers": True},
                    ),
                    html.Div(
                        [
                            html.Div("📭", className="empty-state-icon"),
                            html.Div("No matching requests", className="empty-state-title"),
                            html.Div(
                                "Try another month, clear the day filter, or loosen the search boxes.",
                                className="empty-state-hint",
                            ),
                        ],
                        id="request-empty-state",
                        className="empty-state",
                    ),
                ],
                className="table-card",
            ),
        ],
        id="page-requests",
        style={
            "display": "none",
            "padding": "28px 36px 40px",
            "maxWidth": 1280,
            "margin": "0 auto",
            "minWidth": 0,
        },
    )

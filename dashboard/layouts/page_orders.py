"""Order roster page body."""

from dash import dcc, html, dash_table

from dashboard import constants as C
from dashboard.layouts.page_common import table_info_bar

_DEFAULTS = C.default_app_settings()


def order_roster_page_body():
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

    def filter_bar(children):
        return html.Div(
            children,
            style={
                "display": "flex",
                "flexWrap": "wrap",
                "gap": 16,
                "alignItems": "flex-end",
            },
        )

    hero = html.Div(
        [
            html.Div(
                [
                    html.Span(
                        id="order-page-title-icon",
                        children=d["iconNavOrders"],
                        style={"fontSize": 26, "marginRight": 14, "lineHeight": 1},
                    ),
                    html.Div(
                        [
                            html.H2("Order roster"),
                            html.P(
                                "Service lines for the selected month: scheduled date, completed date, and "
                                "business days between them (weekends and US federal holidays excluded).",
                                className="page-hero-desc",
                            ),
                        ]
                    ),
                ],
                style={"display": "flex", "alignItems": "flex-start"},
            ),
            html.Div(
                [
                    html.Span("Scheduled date", className="legend-chip legend-chip--info"),
                    html.Span("→", className="legend-hint", style={"margin": "0 4px"}),
                    html.Span("Completed date", className="legend-chip legend-chip--success"),
                    html.Span(
                        "Business-day span matches the Overview turnaround calendar",
                        className="legend-hint",
                    ),
                ],
                className="legend-row",
            ),
        ],
        className="page-hero",
    )

    toolbar = html.Div(
        filter_bar(
            [
                html.Div(
                    [
                        html.Label("Equipment class", **flabel),
                        dcc.Dropdown(
                            id="order-filter-category",
                            options=[{"label": "All categories", "value": ""}],
                            value="",
                            clearable=False,
                            style={"minWidth": 220, "fontFamily": "inherit", "fontSize": 13},
                        ),
                    ],
                    style={"minWidth": 230},
                ),
                html.Div(
                    [
                        html.Label("Status contains", **flabel),
                        dcc.Input(
                            id="order-filter-status",
                            type="text",
                            placeholder="e.g. completed",
                            debounce=True,
                            className="filter-input",
                        ),
                    ],
                    style={"flex": "1", "minWidth": 160},
                ),
                html.Div(
                    [
                        html.Label("Equipment contains", **flabel),
                        dcc.Input(
                            id="order-filter-equipment",
                            type="text",
                            debounce=True,
                            className="filter-input",
                        ),
                    ],
                    style={"flex": "1", "minWidth": 160},
                ),
                html.Div(
                    [
                        html.Label("Equipment ID contains", **flabel),
                        dcc.Input(
                            id="order-filter-id",
                            type="text",
                            debounce=True,
                            className="filter-input",
                        ),
                    ],
                    style={"flex": "1", "minWidth": 160},
                ),
            ]
        ),
        className="fm-toolbar",
    )

    bd_col = "Business days (excl. weekends & US holidays)"
    order_cell_cond = [
        {"if": {"column_id": "Equipment"}, "minWidth": 180, "maxWidth": 260},
        {"if": {"column_id": "Equipment ID"}, "minWidth": 130, "maxWidth": 170, "color": C.COLOR_TEXT_SECONDARY},
        {"if": {"column_id": "Building"}, "minWidth": 52, "width": 56, "maxWidth": 64, "textAlign": "center"},
        {"if": {"column_id": "Category"}, "minWidth": 150, "maxWidth": 200},
        {"if": {"column_id": "Status"}, "minWidth": 110, "maxWidth": 150, "fontWeight": 600},
        {"if": {"column_id": "Start (scheduled)"}, "minWidth": 130, "maxWidth": 150, "textAlign": "right"},
        {"if": {"column_id": "End (completed)"}, "minWidth": 130, "maxWidth": 150, "textAlign": "right"},
        {"if": {"column_id": bd_col}, "minWidth": 130, "maxWidth": 200, "textAlign": "right", "fontWeight": 600},
    ]
    order_header_cond = [
        {"if": {"column_id": "Start (scheduled)"}, "textAlign": "right"},
        {"if": {"column_id": "End (completed)"}, "textAlign": "right"},
        {"if": {"column_id": bd_col}, "textAlign": "right"},
    ]

    return html.Div(
        [
            hero,
            toolbar,
            table_info_bar(
                row_count_id="order-row-count",
                page_size_id="order-page-size",
                item_label="service lines",
                export_link_id="order-export-pdf",
            ),
            html.Div(
                [
                    dash_table.DataTable(
                        id="order-roster-table",
                        style_table={**_tbl, "maxHeight": "62vh"},
                        style_header=_hdr,
                        style_cell=_cell,
                        style_cell_conditional=order_cell_cond,
                        style_header_conditional=order_header_cond,
                        style_data_conditional=[],
                        page_size=C.DEFAULT_PAGE_SIZE,
                        page_action="native",
                        sort_action="native",
                        fixed_rows={"headers": True},
                    ),
                    html.Div(
                        [
                            html.Div("📭", className="empty-state-icon"),
                            html.Div("No matching service lines", className="empty-state-title"),
                            html.Div(
                                "No orders match the current month and filters. Try a different "
                                "Category, clear the Status / Equipment / ID text, or pick another month.",
                                className="empty-state-hint",
                            ),
                        ],
                        id="order-empty-state",
                        className="empty-state",
                    ),
                ],
                className="table-card",
            ),
        ],
        id="page-orders",
        className="app-page app-page--standard",
        style={"display": "none"},
    )

"""Replacement page body."""

from dash import dcc, html, dash_table

from dashboard import constants as C
from dashboard.equipment_pricing import PRICE_BASIS_TOOLTIP
from dashboard.layouts.page_common import table_info_bar

_DEFAULTS = C.default_app_settings()


def replacement_page_body():
    d = _DEFAULTS
    flabel = {"className": "filter-label"}
    _hdr = {
        "backgroundColor": "#f8fafc",
        "color": "#64748b",
        "fontWeight": "600",
        "fontSize": 11,
        "textTransform": "uppercase",
        "letterSpacing": "0.04em",
        "borderBottom": f"1px solid {C.COLOR_BORDER}",
        "padding": "13px 16px",
        "border": "none",
    }
    _cell = {
        "backgroundColor": C.BG_CARD,
        "color": C.COLOR_TEXT_PRIMARY,
        "fontSize": 14,
        "padding": "13px 16px",
        "border": "none",
        "borderBottom": f"1px solid rgba(226, 232, 240, 0.65)",
        "fontFamily": "inherit",
        "lineHeight": "1.45",
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
                        id="replace-page-title-icon",
                        children=d["iconReplaceTitle"],
                        style={"fontSize": 26, "marginRight": 14, "lineHeight": 1},
                    ),
                    html.Div(
                        [
                            html.H2("Equipment Replacement Indicator"),
                            html.P(
                                [
                                    "Per equipment: ",
                                    html.Strong("cumulative"),
                                    " parts + labor across every repair month loaded from ",
                                    html.Code("data/repairs/"),
                                    " (the header month control does ",
                                    html.Strong("not"),
                                    " apply here). Compare to estimated new price: Replace >= 80%, Monitor 60-80%, Good < 60%.",
                                ],
                                className="page-hero-desc",
                            ),
                        ]
                    ),
                ],
                style={"display": "flex", "alignItems": "flex-start"},
            ),
            html.Div(
                [
                    html.Span(
                        [
                            html.Span(
                                id="replace-legend-ico-replace",
                                children=d["iconReplaceStatusReplace"],
                            ),
                            " Replace",
                        ],
                        className="legend-chip legend-chip--replace",
                    ),
                    html.Span(
                        "Labor + parts >= 80% of new-equipment price",
                        className="legend-hint",
                    ),
                    html.Span(
                        [
                            html.Span(
                                id="replace-legend-ico-monitor",
                                children=d["iconReplaceStatusMonitor"],
                            ),
                            " Monitor",
                        ],
                        className="legend-chip legend-chip--monitor",
                    ),
                    html.Span(
                        ">= 60% and < 80% of new-equipment price",
                        className="legend-hint",
                    ),
                    html.Span(
                        [
                            html.Span(
                                id="replace-legend-ico-good",
                                children=d["iconReplaceStatusGood"],
                            ),
                            " Good",
                        ],
                        className="legend-chip legend-chip--good",
                    ),
                    html.Span(
                        "Below 60% of new-equipment price",
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
                        html.Label("Status", **flabel),
                        dcc.Dropdown(
                            id="replace-filter-status",
                            options=[
                                {"label": "All statuses", "value": "All"},
                                {"label": "Replace", "value": "Replace"},
                                {"label": "Monitor", "value": "Monitor"},
                                {"label": "Good", "value": "Good"},
                            ],
                            value="All",
                            clearable=False,
                            style={"minWidth": 200, "fontFamily": "inherit", "fontSize": 13},
                        ),
                    ],
                    style={"minWidth": 200},
                ),
                html.Div(
                    [
                        html.Label("Equipment contains", **flabel),
                        dcc.Input(
                            id="replace-filter-equipment",
                            type="text",
                            placeholder="Substring in equipment name",
                            debounce=True,
                            className="filter-input",
                        ),
                    ],
                    style={"flex": "1", "minWidth": 200},
                ),
                html.Div(
                    [
                        html.Label("Equipment ID contains", **flabel),
                        dcc.Input(
                            id="replace-filter-id",
                            type="text",
                            placeholder="Substring in ID",
                            debounce=True,
                            className="filter-input",
                        ),
                    ],
                    style={"flex": "1", "minWidth": 180},
                ),
            ]
        ),
        className="fm-toolbar",
    )

    _money_cols = ["Parts Cost", "Labor Cost", "Total Cost", "New Price", "80% of new price", "60% of new price"]
    _pill_col = {
        "textAlign": "center",
        "padding": "10px 8px",
        "border": "none",
        "backgroundColor": "transparent",
        "verticalAlign": "middle",
    }
    replace_cell_cond = [
        {
            "if": {"column_id": "Status"},
            "minWidth": 120,
            "width": 120,
            "maxWidth": 132,
            **_pill_col,
        },
        {"if": {"column_id": "Equipment"}, "minWidth": 200, "maxWidth": 300},
        {"if": {"column_id": "ID"}, "minWidth": 128, "maxWidth": 180},
        {"if": {"column_id": "Building"}, "minWidth": 150, "maxWidth": 220},
        {
            "if": {"column_id": "Price basis"},
            "minWidth": 118,
            "width": 118,
            "maxWidth": 132,
            **_pill_col,
        },
    ] + [
        {"if": {"column_id": c}, "textAlign": "right", "minWidth": 112, "maxWidth": 148, "fontWeight": 500}
        for c in _money_cols
    ]
    replace_header_cond = [
        {"if": {"column_id": c}, "textAlign": "right"} for c in _money_cols
    ]

    return html.Div(
        [
            hero,
            toolbar,
            table_info_bar(
                row_count_id="replace-row-count",
                page_size_id="replace-page-size",
                item_label="equipment items",
            ),
            html.Div(
                [
                    dash_table.DataTable(
                        id="replace-table",
                        style_table={**_tbl, "maxHeight": "62vh"},
                        style_header=_hdr,
                        style_cell=_cell,
                        style_cell_conditional=replace_cell_cond,
                        style_header_conditional=replace_header_cond,
                        style_data_conditional=[],
                        markdown_options={"html": True},
                        tooltip_header={"Price basis": PRICE_BASIS_TOOLTIP},
                        page_size=C.DEFAULT_PAGE_SIZE,
                        page_action="native",
                        sort_action="native",
                        fixed_rows={"headers": True},
                    ),
                    html.Div(
                        [
                            html.Div("🔍", className="empty-state-icon"),
                            html.Div("No matching equipment", className="empty-state-title"),
                            html.Div(
                                "No items match the current filters. Try clearing Status / "
                                "Equipment / ID above.",
                                className="empty-state-hint",
                            ),
                        ],
                        id="replace-empty-state",
                        className="empty-state",
                    ),
                ],
                className="table-card",
            ),
        ],
        id="page-replacement",
        style={
            "display": "none",
            "padding": "28px 36px 40px",
            "maxWidth": 1280,
            "margin": "0 auto",
            "minWidth": 0,
        },
    )

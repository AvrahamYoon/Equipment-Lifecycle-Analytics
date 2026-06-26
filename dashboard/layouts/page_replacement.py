"""Replacement page body."""

from dash import dcc, html, dash_table

from dashboard import constants as C
from dashboard.logic.repair_count_bins import REPAIR_COUNT_BIN_LABELS
from valuation import PRICE_BASIS_TOOLTIP
from dashboard.logic.depreciation import BOOK_VALUE_TOOLTIP
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
                        children=d["iconNavReplacement"],
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
                                    " apply here). ",
                                    html.Strong("Status"),
                                    " uses whichever signal is worse: repair spend vs new price ",
                                    "(Replace ≥ 80%, Monitor 60–80%), or age vs useful life ",
                                    "(Replace when fully depreciated, Monitor ≥ 80% of life). ",
                                    "Select a row below to ",
                                    html.Strong("extend useful life"),
                                    " after a field inspection (saved to ",
                                    html.Code("data/settings/equipment_life_overrides.csv"),
                                    "). ",
                                    html.Strong("Book value"),
                                    " is estimated remaining accounting value after straight-line ",
                                    "depreciation (down to 5% salvage).",
                                ],
                                className="page-hero-desc",
                                title=BOOK_VALUE_TOOLTIP,
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
                        html.Label("Equipment class", **flabel),
                        dcc.Dropdown(
                            id="replace-filter-category",
                            options=[{"label": "All categories", "value": ""}],
                            value="",
                            clearable=False,
                            style={"minWidth": 200, "fontFamily": "inherit", "fontSize": 13},
                        ),
                    ],
                    style={"minWidth": 200},
                ),
                html.Div(
                    [
                        html.Label("Building", **flabel),
                        dcc.Dropdown(
                            id="replace-filter-building",
                            options=[{"label": "All buildings", "value": ""}],
                            value="",
                            clearable=False,
                            style={"minWidth": 200, "fontFamily": "inherit", "fontSize": 13},
                        ),
                    ],
                    style={"minWidth": 200},
                ),
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
                        html.Label("Repair count", **flabel),
                        dcc.Dropdown(
                            id="replace-filter-repair-count",
                            options=[{"label": "Any", "value": ""}]
                            + [{"label": b, "value": b} for b in REPAIR_COUNT_BIN_LABELS],
                            value="",
                            clearable=False,
                            style={"minWidth": 160, "fontFamily": "inherit", "fontSize": 13},
                        ),
                    ],
                    style={"minWidth": 160},
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

    _money_cols = ["Parts Cost", "Labor Cost", "Total Cost", "New Price", "Book Value"]
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
        {"if": {"column_id": "Building"}, "minWidth": 52, "width": 56, "maxWidth": 64, "textAlign": "center"},
        {"if": {"column_id": "Life adj."}, "minWidth": 72, "width": 80, "maxWidth": 96, "textAlign": "center"},
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

    _inp = {
        "width": "100%",
        "padding": "10px 12px",
        "borderRadius": 8,
        "border": f"1px solid {C.COLOR_BORDER}",
        "fontSize": 14,
        "fontFamily": "inherit",
        "boxSizing": "border-box",
    }
    _field_label = {
        "fontSize": 11,
        "fontWeight": 600,
        "color": C.COLOR_TEXT_MUTED,
        "letterSpacing": "0.08em",
        "textTransform": "uppercase",
        "marginBottom": 6,
        "display": "block",
    }
    _field_hint = {
        "fontSize": 11,
        "color": C.COLOR_TEXT_MUTED,
        "marginTop": 4,
        "marginBottom": 10,
        "display": "block",
    }

    life_panel = html.Div(
        [
            html.Div("Extend useful life", style={"fontWeight": 800, "marginBottom": 8}),
            html.Div(
                "Select an equipment row in the table to adjust useful life after a field inspection.",
                id="replace-life-panel-hint",
                style={"fontSize": 13, "color": C.COLOR_TEXT_SECONDARY, "marginBottom": 12},
            ),
            html.Div(id="replace-life-panel-summary", style={"fontSize": 13, "marginBottom": 12}),
            html.Label("Extra years", style=_field_label),
            dcc.Input(
                id="replace-life-extra-years",
                type="number",
                min=0,
                max=20,
                step=0.5,
                placeholder="e.g. 2",
                className="filter-input",
                style={**_inp, "maxWidth": 160},
            ),
            html.Span(
                "Added on top of the system-estimated useful life (0 clears the override).",
                style=_field_hint,
            ),
            html.Label("Review by (optional)", style=_field_label),
            dcc.Input(
                id="replace-life-review-by",
                type="text",
                placeholder="YYYY-MM-DD",
                className="filter-input",
                style={**_inp, "maxWidth": 200},
            ),
            html.Label("Note (optional)", style=_field_label),
            dcc.Textarea(
                id="replace-life-note",
                placeholder="Inspection findings, condition, etc.",
                style={**_inp, "minHeight": 72, "resize": "vertical"},
            ),
            html.Div(
                [
                    html.Button(
                        "Save extension",
                        id="replace-life-save-btn",
                        n_clicks=0,
                        className="btn-primary",
                    ),
                    html.Button(
                        "Clear extension",
                        id="replace-life-clear-btn",
                        n_clicks=0,
                        className="btn-secondary",
                        style={"marginLeft": 10},
                    ),
                ],
                style={"marginTop": 14, "display": "flex", "flexWrap": "wrap", "gap": 10},
            ),
            html.Div(
                id="replace-life-message",
                style={"marginTop": 10, "fontSize": 13, "color": C.COLOR_TEXT_SECONDARY},
            ),
        ],
        id="replace-life-panel",
        style={**C.CARD_STYLE, "padding": "18px 20px", "marginTop": 16, "display": "none"},
    )

    return html.Div(
        [
            hero,
            toolbar,
            dcc.Store(id="replace-life-overrides-version", data=0),
            table_info_bar(
                row_count_id="replace-row-count",
                page_size_id="replace-page-size",
                item_label="equipment items",
                export_link_id="replace-export-pdf",
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
                        row_selectable="single",
                        selected_rows=[],
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
            life_panel,
        ],
        id="page-replacement",
        className="app-page app-page--standard",
        style={"display": "none"},
    )

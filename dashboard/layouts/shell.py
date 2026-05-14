"""Root layout: left nav + header + page panels (overview / replacement / settings)."""

from dash import dcc, html, dash_table

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
                        className="lift-on-hover",
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
                        className="lift-on-hover",
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
                        className="lift-on-hover",
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
                        className="lift-on-hover",
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
                        className="lift-on-hover",
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
                        className="lift-on-hover",
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
                        className="lift-on-hover",
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
            "maxWidth": 1440,
            "margin": "0 auto",
            "minWidth": 0,
        },
    )


def _table_info_bar(row_count_id: str, page_size_id: str, item_label: str = "rows"):
    """Strip above each DataTable: row-count pill on the left, segmented
    Rows-per-page control on the right."""
    return html.Div(
        [
            html.Div(
                f"Showing 0 of 0 {item_label}",
                id=row_count_id,
                className="row-count",
            ),
            html.Div(
                [
                    html.Span("Rows per page", className="page-size-caption"),
                    dcc.RadioItems(
                        id=page_size_id,
                        options=C.PAGE_SIZE_OPTIONS,
                        value=C.DEFAULT_PAGE_SIZE,
                        inline=True,
                        className="page-size-radio",
                        labelClassName="page-size-radio-label",
                        inputClassName="page-size-radio-input",
                        labelStyle={},  # override the default {display: inline-block}
                    ),
                ],
                className="page-size-wrap",
            ),
        ],
        className="table-info-bar",
    )


def replacement_page_body():
    """Full-page replacement indicator (equipment-level roll-up)."""
    d = _DEFAULTS
    flabel = {
        "fontSize": 11,
        "fontWeight": 600,
        "color": C.COLOR_TEXT_MUTED,
        "letterSpacing": "0.06em",
        "textTransform": "uppercase",
        "marginBottom": 6,
        "display": "block",
    }
    finp = {
        "width": "100%",
        "maxWidth": 280,
        "padding": "10px 12px",
        "borderRadius": 10,
        "border": f"1px solid {C.COLOR_BORDER}",
        "fontSize": 13,
        "fontFamily": "inherit",
        "boxSizing": "border-box",
        "background": "#fff",
    }
    _hdr = {
        "backgroundColor": "#f1f5f9",
        "color": C.COLOR_TEXT_SECONDARY,
        "fontWeight": "700",
        "fontSize": 11,
        "textTransform": "uppercase",
        "letterSpacing": "0.06em",
        "borderBottom": f"2px solid {C.COLOR_BORDER}",
        "padding": "12px 16px",
        "border": "none",
    }
    _cell = {
        "backgroundColor": C.BG_CARD,
        "color": C.COLOR_TEXT_PRIMARY,
        "fontSize": 13,
        "padding": "12px 16px",
        "border": "none",
        "borderBottom": f"1px solid {C.COLOR_BORDER}",
        "fontFamily": "'DM Sans','Segoe UI',sans-serif",
    }
    _tbl = {"overflowX": "auto", "borderRadius": 12, "overflow": "hidden", "border": f"1px solid {C.COLOR_BORDER}"}

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
                        style={
                            "fontSize": 22,
                            "marginRight": 12,
                            "lineHeight": 1,
                            "filter": "drop-shadow(0 1px 1px rgba(0,0,0,0.06))",
                        },
                    ),
                    html.Div(
                        [
                            html.H2(
                                "Equipment Replacement Indicator",
                                style={
                                    "margin": 0,
                                    "fontSize": 22,
                                    "fontWeight": 800,
                                    "color": C.COLOR_TEXT_PRIMARY,
                                    "letterSpacing": "-0.02em",
                                },
                            ),
                            html.P(
                                "Per equipment: sum of parts + labor vs. estimated new price. "
                                "Replace when spend reaches at least 80% of that price; Monitor from 60% up to 80%; "
                                "Good below 60%. Use the month selector (or All months) to choose the period.",
                                style={
                                    "margin": "6px 0 0",
                                    "fontSize": 13,
                                    "color": C.COLOR_TEXT_SECONDARY,
                                    "lineHeight": 1.45,
                                    "maxWidth": 720,
                                },
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
                                style={"fontWeight": 700},
                            ),
                            html.Span(" Replace", style={"color": "#b91c1c", "fontWeight": 700}),
                        ],
                        style={
                            "marginRight": 14,
                            "padding": "6px 12px",
                            "borderRadius": 999,
                            "background": "#fef2f2",
                            "border": "1px solid #fecaca",
                            "fontSize": 12,
                        },
                    ),
                    html.Span(
                        "Labor + parts ≥ 80% of new-equipment price",
                        style={"color": C.COLOR_TEXT_MUTED, "fontSize": 12, "marginRight": 18},
                    ),
                    html.Span(
                        [
                            html.Span(
                                id="replace-legend-ico-monitor",
                                children=d["iconReplaceStatusMonitor"],
                                style={"fontWeight": 700},
                            ),
                            html.Span(" Monitor", style={"color": "#b45309", "fontWeight": 700}),
                        ],
                        style={
                            "marginRight": 14,
                            "padding": "6px 12px",
                            "borderRadius": 999,
                            "background": "#fffbeb",
                            "border": "1px solid #fde68a",
                            "fontSize": 12,
                        },
                    ),
                    html.Span(
                        "≥ 60% and < 80% of new-equipment price",
                        style={"color": C.COLOR_TEXT_MUTED, "fontSize": 12, "marginRight": 18},
                    ),
                    html.Span(
                        [
                            html.Span(
                                id="replace-legend-ico-good",
                                children=d["iconReplaceStatusGood"],
                                style={"fontWeight": 700},
                            ),
                            html.Span(" Good", style={"color": "#047857", "fontWeight": 700}),
                        ],
                        style={
                            "marginRight": 14,
                            "padding": "6px 12px",
                            "borderRadius": 999,
                            "background": "#ecfdf5",
                            "border": "1px solid #a7f3d0",
                            "fontSize": 12,
                        },
                    ),
                    html.Span(
                        "Below 60% of new-equipment price",
                        style={"color": C.COLOR_TEXT_MUTED, "fontSize": 12},
                    ),
                ],
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": 8,
                    "alignItems": "center",
                    "marginTop": 16,
                },
            ),
        ],
        style={
            **C.CARD_STYLE,
            "padding": "24px 26px 22px",
            "marginBottom": 20,
            "borderLeft": f"4px solid {C.C_BLUE}",
            "boxShadow": "0 4px 24px rgba(15, 23, 42, 0.06)",
        },
    )

    toolbar = html.Div(
        filter_bar(
            [
                html.Div(
                    [
                        html.Label("Status", style=flabel),
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
                        html.Label("Equipment contains", style=flabel),
                        dcc.Input(
                            id="replace-filter-equipment",
                            type="text",
                            placeholder="Substring in equipment name",
                            debounce=True,
                            style=finp,
                        ),
                    ],
                    style={"flex": "1", "minWidth": 200},
                ),
                html.Div(
                    [
                        html.Label("Equipment ID contains", style=flabel),
                        dcc.Input(
                            id="replace-filter-id",
                            type="text",
                            placeholder="Substring in ID",
                            debounce=True,
                            style=finp,
                        ),
                    ],
                    style={"flex": "1", "minWidth": 180},
                ),
            ]
        ),
        className="fm-toolbar",
        style={
            "background": "linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%)",
            "border": f"1px solid {C.COLOR_BORDER}",
            "borderRadius": 12,
            "padding": "16px 18px",
            "marginBottom": 18,
        },
    )

    _money_cols = ["Parts Cost", "Labor Cost", "Total Cost", "New Price", "80% of new price", "60% of new price"]
    replace_cell_cond = [
        {"if": {"column_id": "Status"}, "minWidth": 130, "width": 130, "maxWidth": 150, "fontWeight": 600},
        {"if": {"column_id": "Equipment"}, "minWidth": 180, "maxWidth": 280},
        {"if": {"column_id": "ID"}, "minWidth": 130, "maxWidth": 170, "color": C.COLOR_TEXT_SECONDARY},
    ] + [
        {"if": {"column_id": c}, "textAlign": "right", "minWidth": 110, "maxWidth": 140}
        for c in _money_cols
    ]
    replace_header_cond = [
        {"if": {"column_id": c}, "textAlign": "right"} for c in _money_cols
    ]

    return html.Div(
        [
            hero,
            toolbar,
            _table_info_bar(
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
                                "No items match the current month and filters. Try clearing the "
                                "Status / Equipment / ID filters above, or switching the month.",
                                className="empty-state-hint",
                            ),
                        ],
                        id="replace-empty-state",
                        className="empty-state",
                    ),
                ],
                style={
                    **C.CARD_STYLE,
                    "padding": 0,
                    "overflow": "hidden",
                },
            ),
        ],
        id="page-replacement",
        style={
            "display": "none",
            "padding": "28px 32px 40px",
            "maxWidth": 1280,
            "margin": "0 auto",
            "minWidth": 0,
        },
    )


def order_roster_page_body():
    """Full-page service order lines (schedule → completion, business days)."""
    d = _DEFAULTS
    flabel = {
        "fontSize": 11,
        "fontWeight": 600,
        "color": C.COLOR_TEXT_MUTED,
        "letterSpacing": "0.06em",
        "textTransform": "uppercase",
        "marginBottom": 6,
        "display": "block",
    }
    finp = {
        "width": "100%",
        "maxWidth": 280,
        "padding": "10px 12px",
        "borderRadius": 10,
        "border": f"1px solid {C.COLOR_BORDER}",
        "fontSize": 13,
        "fontFamily": "inherit",
        "boxSizing": "border-box",
        "background": "#fff",
    }
    _hdr = {
        "backgroundColor": "#f1f5f9",
        "color": C.COLOR_TEXT_SECONDARY,
        "fontWeight": "700",
        "fontSize": 11,
        "textTransform": "uppercase",
        "letterSpacing": "0.06em",
        "borderBottom": f"2px solid {C.COLOR_BORDER}",
        "padding": "12px 16px",
        "border": "none",
    }
    _cell = {
        "backgroundColor": C.BG_CARD,
        "color": C.COLOR_TEXT_PRIMARY,
        "fontSize": 13,
        "padding": "12px 16px",
        "border": "none",
        "borderBottom": f"1px solid {C.COLOR_BORDER}",
        "fontFamily": "'DM Sans','Segoe UI',sans-serif",
    }
    _tbl = {"overflowX": "auto", "borderRadius": 12, "overflow": "hidden", "border": f"1px solid {C.COLOR_BORDER}"}

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
                        style={
                            "fontSize": 22,
                            "marginRight": 12,
                            "lineHeight": 1,
                            "filter": "drop-shadow(0 1px 1px rgba(0,0,0,0.06))",
                        },
                    ),
                    html.Div(
                        [
                            html.H2(
                                "Order roster",
                                style={
                                    "margin": 0,
                                    "fontSize": 22,
                                    "fontWeight": 800,
                                    "color": C.COLOR_TEXT_PRIMARY,
                                    "letterSpacing": "-0.02em",
                                },
                            ),
                            html.P(
                                "Service lines for the selected month: scheduled date, completed date, and "
                                "business days between them (weekends and US federal holidays excluded).",
                                style={
                                    "margin": "6px 0 0",
                                    "fontSize": 13,
                                    "color": C.COLOR_TEXT_SECONDARY,
                                    "lineHeight": 1.45,
                                    "maxWidth": 820,
                                },
                            ),
                        ]
                    ),
                ],
                style={"display": "flex", "alignItems": "flex-start"},
            ),
            html.Div(
                [
                    html.Span(
                        "Scheduled date",
                        style={
                            "color": C.COLOR_TEXT_PRIMARY,
                            "fontWeight": 700,
                            "fontSize": 12,
                            "padding": "6px 12px",
                            "borderRadius": 8,
                            "background": "#e0f2fe",
                            "border": "1px solid #bae6fd",
                        },
                    ),
                    html.Span("→", style={"color": C.COLOR_TEXT_MUTED, "margin": "0 8px", "fontWeight": 600}),
                    html.Span(
                        "Completed date",
                        style={
                            "color": C.COLOR_TEXT_PRIMARY,
                            "fontWeight": 700,
                            "fontSize": 12,
                            "padding": "6px 12px",
                            "borderRadius": 8,
                            "background": "#ecfdf5",
                            "border": "1px solid #a7f3d0",
                        },
                    ),
                    html.Span(
                        "·  Business-day span matches the Overview turnaround calendar",
                        style={"color": C.COLOR_TEXT_MUTED, "fontSize": 12, "marginLeft": 10},
                    ),
                ],
                style={"display": "flex", "flexWrap": "wrap", "alignItems": "center", "marginTop": 16},
            ),
        ],
        style={
            **C.CARD_STYLE,
            "padding": "24px 26px 22px",
            "marginBottom": 20,
            "borderLeft": f"4px solid {C.C_PURPLE}",
            "boxShadow": "0 4px 24px rgba(15, 23, 42, 0.06)",
        },
    )

    toolbar = html.Div(
        filter_bar(
            [
                html.Div(
                    [
                        html.Label("Equipment class", style=flabel),
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
                        html.Label("Status contains", style=flabel),
                        dcc.Input(
                            id="order-filter-status",
                            type="text",
                            placeholder="e.g. completed",
                            debounce=True,
                            style=finp,
                        ),
                    ],
                    style={"flex": "1", "minWidth": 160},
                ),
                html.Div(
                    [
                        html.Label("Equipment contains", style=flabel),
                        dcc.Input(
                            id="order-filter-equipment",
                            type="text",
                            debounce=True,
                            style=finp,
                        ),
                    ],
                    style={"flex": "1", "minWidth": 160},
                ),
                html.Div(
                    [
                        html.Label("Equipment ID contains", style=flabel),
                        dcc.Input(
                            id="order-filter-id",
                            type="text",
                            debounce=True,
                            style=finp,
                        ),
                    ],
                    style={"flex": "1", "minWidth": 160},
                ),
            ]
        ),
        className="fm-toolbar",
        style={
            "background": "linear-gradient(180deg, #faf5ff 0%, #f3e8ff 100%)",
            "border": f"1px solid {C.COLOR_BORDER}",
            "borderRadius": 12,
            "padding": "16px 18px",
            "marginBottom": 18,
        },
    )

    bd_col = "Business days (excl. weekends & US holidays)"
    order_cell_cond = [
        {"if": {"column_id": "Equipment"}, "minWidth": 180, "maxWidth": 260},
        {"if": {"column_id": "Equipment ID"}, "minWidth": 130, "maxWidth": 170, "color": C.COLOR_TEXT_SECONDARY},
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
            _table_info_bar(
                row_count_id="order-row-count",
                page_size_id="order-page-size",
                item_label="service lines",
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
                style={
                    **C.CARD_STYLE,
                    "padding": 0,
                    "overflow": "hidden",
                },
            ),
        ],
        id="page-orders",
        style={
            "display": "none",
            "padding": "28px 32px 40px",
            "maxWidth": 1280,
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
                "Short text or emoji for KPI cards, left navigation, and replacement / order pages. "
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
                                            html.Label("Order roster link", style=label),
                                            dcc.Input(
                                                id="settings-iconNavOrders",
                                                type="text",
                                                value=_DEFAULTS["iconNavOrders"],
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
                    html.Div(
                        "Workspace",
                        style={
                            "fontSize": 10,
                            "fontWeight": 700,
                            "letterSpacing": "0.14em",
                            "color": C.COLOR_TEXT_MUTED,
                            "textTransform": "uppercase",
                            "marginBottom": 12,
                            "paddingLeft": 4,
                        },
                    ),
                    html.Div(
                        dcc.Link(
                            [
                                html.Span(
                                    id="nav-icon-overview",
                                    children=_DEFAULTS["iconNavOverview"],
                                    style={
                                        "marginRight": 10,
                                        "fontSize": 17,
                                        "lineHeight": 1,
                                        "display": "inline-block",
                                        "minWidth": "1.15em",
                                    },
                                ),
                                html.Span("Overview", style={"letterSpacing": "-0.01em"}),
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
                            "padding": "11px 16px",
                            "borderRadius": 10,
                            "marginBottom": 6,
                            "background": "#e8f1fe",
                            "color": C.COLOR_TEXT_PRIMARY,
                            "fontWeight": 700,
                            "fontSize": 14,
                            "border": "1px solid transparent",
                        },
                    ),
                    html.Div(
                        dcc.Link(
                            [
                                html.Span(
                                    id="nav-icon-replacement",
                                    children=_DEFAULTS["iconNavReplacement"],
                                    style={
                                        "marginRight": 10,
                                        "fontSize": 17,
                                        "lineHeight": 1,
                                        "display": "inline-block",
                                        "minWidth": "1.15em",
                                    },
                                ),
                                html.Span("Replacement", style={"letterSpacing": "-0.01em"}),
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
                            "padding": "11px 16px",
                            "borderRadius": 10,
                            "marginBottom": 6,
                            "background": "transparent",
                            "color": C.COLOR_TEXT_SECONDARY,
                            "fontWeight": 500,
                            "fontSize": 14,
                            "border": "1px solid transparent",
                        },
                    ),
                    html.Div(
                        dcc.Link(
                            [
                                html.Span(
                                    id="nav-icon-orders",
                                    children=_DEFAULTS["iconNavOrders"],
                                    style={
                                        "marginRight": 10,
                                        "fontSize": 17,
                                        "lineHeight": 1,
                                        "display": "inline-block",
                                        "minWidth": "1.15em",
                                    },
                                ),
                                html.Span("Order roster", style={"letterSpacing": "-0.01em"}),
                            ],
                            href="/orders",
                            style={
                                "color": "inherit",
                                "textDecoration": "none",
                                "display": "flex",
                                "alignItems": "center",
                            },
                        ),
                        id="nav-wrap-orders",
                        style={
                            "padding": "11px 16px",
                            "borderRadius": 10,
                            "marginBottom": 6,
                            "background": "transparent",
                            "color": C.COLOR_TEXT_SECONDARY,
                            "fontWeight": 500,
                            "fontSize": 14,
                            "border": "1px solid transparent",
                        },
                    ),
                    html.Div(
                        style={
                            "height": 1,
                            "background": C.COLOR_BORDER,
                            "margin": "14px 4px 12px",
                        }
                    ),
                    html.Div(
                        "Preferences",
                        style={
                            "fontSize": 10,
                            "fontWeight": 700,
                            "letterSpacing": "0.14em",
                            "color": C.COLOR_TEXT_MUTED,
                            "textTransform": "uppercase",
                            "marginBottom": 10,
                            "paddingLeft": 4,
                        },
                    ),
                    html.Div(
                        dcc.Link(
                            [
                                html.Span(
                                    id="nav-icon-settings",
                                    children=_DEFAULTS["iconNavSettings"],
                                    style={
                                        "marginRight": 10,
                                        "fontSize": 17,
                                        "lineHeight": 1,
                                        "display": "inline-block",
                                        "minWidth": "1.15em",
                                    },
                                ),
                                html.Span("Settings", style={"letterSpacing": "-0.01em"}),
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
                            "padding": "11px 16px",
                            "borderRadius": 10,
                            "marginBottom": 6,
                            "background": "transparent",
                            "color": C.COLOR_TEXT_SECONDARY,
                            "fontWeight": 500,
                            "fontSize": 14,
                            "border": "1px solid transparent",
                        },
                    ),
                ],
                style={
                    "width": 248,
                    "flexShrink": 0,
                    "height": "100vh",
                    "overflowY": "auto",
                    "overflowX": "hidden",
                    "background": "linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)",
                    "borderRight": f"1px solid {C.COLOR_BORDER}",
                    "padding": "22px 14px 24px",
                    "boxSizing": "border-box",
                    "boxShadow": "inset -1px 0 0 rgba(148, 163, 184, 0.12)",
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
                        className="fm-header",
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
                        [overview_page_body(), replacement_page_body(), order_roster_page_body(), settings_page_body()],
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

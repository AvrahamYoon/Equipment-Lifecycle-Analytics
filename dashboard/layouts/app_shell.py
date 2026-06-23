"""Root shell layout composition."""

from dash import dcc, html

from dashboard import constants as C
from dashboard.layouts.page_admin import admin_page_body
from dashboard.layouts.page_orders import order_roster_page_body
from dashboard.layouts.page_requests import request_roster_page_body
from dashboard.layouts.page_overview import overview_page_body
from dashboard.layouts.page_replacement import replacement_page_body
from dashboard.layouts.page_settings import settings_page_body
from dashboard.settings_persist import load_dashboard_settings

_DEFAULTS = C.default_app_settings()


def _nav_item(href: str, icon_id: str, icon: str, label: str):
    return dcc.Link(
        [
            html.Span(
                id=icon_id,
                children=icon,
                style={
                    "marginRight": 10,
                    "fontSize": 17,
                    "lineHeight": 1,
                    "display": "inline-block",
                    "minWidth": "1.15em",
                },
            ),
            html.Span(label, style={"letterSpacing": "-0.01em"}),
        ],
        href=href,
        style={
            "color": "inherit",
            "textDecoration": "none",
            "display": "flex",
            "alignItems": "center",
        },
    )


def _nav_wrap(item_id: str, child, active: bool = False):
    return html.Div(
        child,
        id=item_id,
        style={
            "padding": "11px 16px",
            "borderRadius": 10,
            "marginBottom": 6,
            "background": "#e8f1fe" if active else "transparent",
            "color": C.COLOR_TEXT_PRIMARY if active else C.COLOR_TEXT_SECONDARY,
            "fontWeight": 700 if active else 500,
            "fontSize": 14,
            "border": "1px solid transparent",
        },
    )


def build_root_layout(month_options, default_month):
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="settings-store", data=load_dashboard_settings()),
            dcc.Store(id="chart-drill-store", storage_type="memory"),
            html.Div(
                [
                    html.Div(
                        "Workspace",
                        className="sidebar-brand section-eyebrow section-eyebrow--blue",
                    ),
                    _nav_wrap(
                        "nav-wrap-overview",
                        _nav_item("/", "nav-icon-overview", _DEFAULTS["iconNavOverview"], "Overview"),
                        active=True,
                    ),
                    _nav_wrap(
                        "nav-wrap-replacement",
                        _nav_item(
                            "/replacement",
                            "nav-icon-replacement",
                            _DEFAULTS["iconNavReplacement"],
                            "Replacement",
                        ),
                    ),
                    _nav_wrap(
                        "nav-wrap-orders",
                        _nav_item("/orders", "nav-icon-orders", _DEFAULTS["iconNavOrders"], "Order roster"),
                    ),
                    _nav_wrap(
                        "nav-wrap-requests",
                        _nav_item(
                            "/requests",
                            "nav-icon-requests",
                            _DEFAULTS["iconNavRequests"],
                            "Request roster",
                        ),
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
                    _nav_wrap(
                        "nav-wrap-settings",
                        _nav_item("/settings", "nav-icon-settings", _DEFAULTS["iconNavSettings"], "Settings"),
                    ),
                    _nav_wrap(
                        "nav-wrap-admin",
                        dcc.Link(
                            [
                                html.Span(
                                    "🔧",
                                    style={
                                        "marginRight": 10,
                                        "fontSize": 17,
                                        "lineHeight": 1,
                                        "display": "inline-block",
                                        "minWidth": "1.15em",
                                    },
                                ),
                                html.Span("Admin", style={"letterSpacing": "-0.01em"}),
                            ],
                            href="/admin",
                            style={
                                "color": "inherit",
                                "textDecoration": "none",
                                "display": "flex",
                                "alignItems": "center",
                            },
                        ),
                    ),
                    html.Div(
                        id="auth-status",
                        style={
                            "marginTop": "auto",
                            "paddingTop": 14,
                            "borderTop": f"1px solid {C.COLOR_BORDER}",
                            "fontSize": 12,
                            "color": C.COLOR_TEXT_MUTED,
                            "lineHeight": 1.4,
                        },
                    ),
                ],
                className="app-sidebar",
                style={
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
                                        className="app-eyebrow",
                                    ),
                                    html.H1("Work Order Dashboard"),
                                    html.Span(
                                        "Custodial Equipment Repair & Service Tracker",
                                        className="app-subtitle",
                                    ),
                                ],
                                className="app-header-brand",
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
                                        style={"width": "min(180px, 100%)", "fontFamily": "inherit", "fontSize": 13},
                                    ),
                                    html.Div(
                                        "Filters Overview, Request roster & Order roster. Replacement always rolls up every loaded month.",
                                        className="month-scope-hint",
                                    ),
                                ],
                                className="app-header-controls",
                            ),
                        ],
                        className="fm-header app-header-inner",
                    ),
                    html.Div(
                        [
                            overview_page_body(),
                            replacement_page_body(),
                            order_roster_page_body(),
                            request_roster_page_body(),
                            settings_page_body(),
                            admin_page_body(),
                        ],
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
                className="app-main",
            ),
        ],
        className="app-shell app-layout",
    )

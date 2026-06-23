"""Dash application factory."""

from dash import Dash

from dashboard import constants as C
from dashboard.auth import configure_auth
from dashboard.callbacks.wiring import register_callbacks
from dashboard.export import configure_exports
from dashboard.data_loaders import MONTH_OPTIONS, all_months
from dashboard.layouts.app_shell import build_root_layout


def create_app() -> Dash:
    # Avoid tab title stuck on Dash's default "Updating..." when many callbacks
    # fire from one interaction (e.g. Settings Apply → store → overview + table + icons).
    app = Dash(__name__, update_title=None, suppress_callback_exceptions=True)
    app.title = "Work Order Dashboard"
    configure_auth(app)
    configure_exports(app)
    # Default to the aggregate "All months" view when we have any data so the
    # dashboard lands on something useful; fall back to a single month if
    # somehow only one is loaded; finally None for a totally empty dataset.
    if all_months:
        default_month = C.ALL_MONTHS_KEY
    else:
        default_month = None
    app.layout = build_root_layout(MONTH_OPTIONS, default_month)
    register_callbacks(app)
    return app

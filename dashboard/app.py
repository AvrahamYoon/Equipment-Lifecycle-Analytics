"""Dash application factory."""

from dash import Dash

from dashboard.callbacks.wiring import register_callbacks
from dashboard.data_loaders import MONTH_OPTIONS, all_months
from dashboard.layouts.shell import build_root_layout


def create_app() -> Dash:
    # Avoid tab title stuck on Dash's default "Updating..." when many callbacks
    # fire from one interaction (e.g. Settings Apply → store → overview + table + icons).
    app = Dash(__name__, update_title=None)
    app.title = "Work Order Dashboard"
    default_month = all_months[0] if all_months else None
    app.layout = build_root_layout(MONTH_OPTIONS, default_month)
    register_callbacks(app)
    return app

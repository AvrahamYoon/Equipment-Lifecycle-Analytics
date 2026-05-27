"""Compatibility facade for shell layout builders."""

from dashboard.layouts.app_shell import build_root_layout
from dashboard.layouts.page_bodies import (
    admin_page_body,
    order_roster_page_body,
    overview_page_body,
    replacement_page_body,
    settings_page_body,
)

__all__ = [
    "build_root_layout",
    "overview_page_body",
    "replacement_page_body",
    "order_roster_page_body",
    "settings_page_body",
    "admin_page_body",
]

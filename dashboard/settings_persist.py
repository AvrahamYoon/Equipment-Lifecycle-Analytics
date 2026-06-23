"""Load / save dashboard settings to disk (shared across browsers on one server)."""

from __future__ import annotations

import json
import os

from dashboard import constants as C
from dashboard.logic.overview.settings_merge import merge_app_settings

SETTINGS_PATH = os.path.join("data", "settings", "app_settings.json")


def load_dashboard_settings() -> dict:
    """Read persisted settings or return merged defaults."""
    if os.path.isfile(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, encoding="utf-8") as fh:
                raw = json.load(fh)
            if isinstance(raw, dict):
                return merge_app_settings(raw)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    return merge_app_settings(C.default_app_settings())


def save_dashboard_settings(data: dict) -> None:
    """Write settings JSON after Apply / Reset."""
    merged = merge_app_settings(data)
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, indent=2, sort_keys=True)

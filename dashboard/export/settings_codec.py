"""Encode/decode persisted settings for export query strings."""

from __future__ import annotations

import base64
import json
from typing import Any


def encode_settings(settings: dict[str, Any] | None) -> str:
    payload = json.dumps(settings or {}, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii")


def decode_settings(token: str) -> dict[str, Any] | None:
    raw = (token or "").strip()
    if not raw:
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(raw.encode("ascii")).decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None

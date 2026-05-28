"""Building name normalization helpers for scopes and table display."""

from __future__ import annotations

import re

_NON_BUILDING_PATTERNS = (
    "total service orders",
    "total orders",
    "total requests",
    "summary",
)


def normalize_building_value(raw) -> str:
    s = str(raw or "").strip()
    if not s:
        return ""
    s = re.sub(r"^location:\s*", "", s, flags=re.IGNORECASE).strip()
    low = s.lower()
    if any(p in low for p in _NON_BUILDING_PATTERNS):
        return ""
    if re.fullmatch(r"[\d:\s]+", s):
        return ""
    # Collapse room-level labels to building-level labels.
    s = re.sub(r"\b(room|rm|suite|ste|apt)\b.*$", "", s, flags=re.IGNORECASE).strip(" -,:")
    s = re.sub(r"\s+\d+[a-zA-Z0-9-]*$", "", s).strip(" -,:")
    return s.strip()

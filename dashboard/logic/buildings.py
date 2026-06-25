"""Building name normalization helpers for scopes and table display."""

from __future__ import annotations

import re

_NON_BUILDING_PATTERNS = (
    "total service orders",
    "total orders",
    "total requests",
    "summary",
)

# Variant labels collapsed before lookup (filtering, charts, tables).
_BUILDING_ALIASES: dict[str, str] = {
    "Clarke South Stair": "Clarke",
    "Live Stock Center": "Livestock Center",
    "ETC Mechanic Shop": "ETC",
}

# Canonical full name → display code (campus-specific).
_BUILDING_ABBREV: dict[str, str] = {
    "AGM": "AGM",
    "Austin": "AUS",
    "BCTR": "BCTR",
    "Benson": "BEN",
    "Biddulph": "BID",
    "Clarke": "CLK",
    "ETC": "ETC",
    "Facilities Shops": "FMS",
    "Hart": "HAR",
    "Hinckley": "HIK",
    "Kimball": "KIM",
    "Livestock Center": "LSC",
    "Manwaring Center": "MC",
    "McKay Library": "MCK",
    "Ricks": "RKS",
    "Rigby": "RIG",
    "Romney": "ROM",
    "STC": "STC",
    "Snow": "SNW",
    "Spori": "SPR",
    "Student Health Center": "SHC",
    "Taylor": "TAY",
    "University Communications": "UC",
    "University Operations": "UO",
}


def _apply_building_aliases(name: str) -> str:
    if not name:
        return name
    if name in _BUILDING_ALIASES:
        return _BUILDING_ALIASES[name]
    low = name.lower()
    for alias, canonical in _BUILDING_ALIASES.items():
        if alias.lower() == low:
            return canonical
    return name


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
    return _apply_building_aliases(s.strip())


def _abbrev_fallback(name: str) -> str:
    """Derive a three-letter code when no explicit mapping exists."""
    name = name.strip()
    if not name:
        return ""
    alnum = re.sub(r"[^A-Za-z0-9]", "", name)
    if 1 <= len(alnum) <= 3:
        return alnum.upper()
    words = [
        w
        for w in re.split(r"[\s\-/]+", name)
        if w and w.lower() not in {"the", "of", "and", "a"}
    ]
    if not words:
        return name[:3].upper()
    if len(words) >= 2:
        return "".join(w[0].upper() for w in words[:3])[:3]
    word = words[0]
    if len(word) <= 3:
        return word.upper()
    return word[:3].upper()


def abbreviate_building(name: str) -> str:
    """Return a three-letter building label for compact table/chart display."""
    normalized = normalize_building_value(name)
    if not normalized:
        return ""
    if normalized in _BUILDING_ABBREV:
        return _BUILDING_ABBREV[normalized]
    return _abbrev_fallback(normalized)


def display_building_name(raw_or_normalized) -> str:
    """Normalize then abbreviate for UI display."""
    normalized = normalize_building_value(raw_or_normalized)
    if not normalized:
        return ""
    return abbreviate_building(normalized)


def resolve_building_filter_value(display_or_full: str) -> str:
    """Map abbreviated UI label back to normalized name for filters and scope."""
    token = str(display_or_full or "").strip()
    if not token:
        return ""
    normalized = normalize_building_value(token)
    if normalized and (normalized in _BUILDING_ABBREV or len(normalized) > 3):
        return normalized
    upper = token.upper()
    for full, abbr in _BUILDING_ABBREV.items():
        if abbr == token or abbr.upper() == upper:
            return full
    if normalized:
        return normalized
    return token

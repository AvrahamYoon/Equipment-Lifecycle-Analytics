"""Shared CSV parsing and equipment-name matching (dashboard + offline scripts)."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

TOKEN_MATCH_MIN_SCORE = 0.5


def norm_col_key(name: str) -> str:
    return str(name).lower().replace(" ", "").replace("_", "").replace("#", "")


def norm_equipment_name(name: str) -> str:
    if pd.isna(name):
        return ""
    s = unicodedata.normalize("NFKD", str(name))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_dollar_amount(value) -> float | None:
    if pd.isna(value):
        return None
    s = str(value).strip()
    if not s or s.lower() == "enter data":
        return None
    s = s.replace("$", "").replace(",", "")
    n = pd.to_numeric(s, errors="coerce")
    if pd.isna(n) or float(n) <= 0:
        return None
    return float(n)


def parse_purchase_year(value) -> int | None:
    if pd.isna(value):
        return None
    s = str(value).strip()
    if not s:
        return None
    m = re.search(r"(20\d{2}|19\d{2})", s)
    if m:
        return int(m.group(1))
    n = pd.to_numeric(s, errors="coerce")
    if pd.isna(n):
        return None
    year = int(n)
    return year if 1900 <= year <= 2100 else None


def pick_column(df: pd.DataFrame, *aliases: str) -> str | None:
    key_to_col = {norm_col_key(c): c for c in df.columns}
    for alias in aliases:
        key = norm_col_key(alias)
        if key in key_to_col:
            return key_to_col[key]
    return None


def match_equipment_key(norm_name: str, keys_sorted: list[str]) -> str | None:
    """Best normalized equipment/model key for a repair or purchase label."""
    if not norm_name or not keys_sorted:
        return None

    best_sub: str | None = None
    best_sub_len = 0
    for key in keys_sorted:
        if key in norm_name or norm_name in key:
            if len(key) > best_sub_len:
                best_sub_len = len(key)
                best_sub = key
    if best_sub is not None:
        return best_sub

    best_score = 0.0
    best_key: str | None = None
    best_key_len = 0
    for key in keys_sorted:
        tokens = [t for t in key.split() if len(t) >= 2]
        if not tokens:
            continue
        hits = sum(1 for t in tokens if t in norm_name)
        score = hits / len(tokens)
        if score < TOKEN_MATCH_MIN_SCORE:
            continue
        if score > best_score or (score == best_score and len(key) > best_key_len):
            best_score = score
            best_key = key
            best_key_len = len(key)
    return best_key

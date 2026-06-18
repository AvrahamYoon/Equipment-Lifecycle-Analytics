"""Report and building access from the Flask login session."""

from __future__ import annotations

import pandas as pd
from flask import session

from dashboard.logic.buildings import normalize_building_value

REPORT_KEYS = ("overview", "replacement", "orders", "settings")


def allowed_reports_for_session() -> set[str]:
    role = str(session.get("role") or "")
    if role == "admin":
        return set(REPORT_KEYS)
    if "allowed_reports" not in session:
        return set(REPORT_KEYS)
    values = session.get("allowed_reports") or []
    return {str(v).strip().lower() for v in values if str(v).strip()}


def normalize_building_scope(values) -> set[str]:
    out: set[str] = set()
    for v in values or []:
        nv = normalize_building_value(v)
        if nv:
            out.add(nv)
    return out


def apply_building_scope(df: pd.DataFrame) -> pd.DataFrame:
    allowed = normalize_building_scope(session.get("allowed_buildings") or [])
    if not allowed:
        return df
    for col in ("location", "Location", "building", "Building", "site", "Site"):
        if col in df.columns:
            normalized = df[col].map(normalize_building_value)
            return df[normalized.isin(allowed)]
    return df

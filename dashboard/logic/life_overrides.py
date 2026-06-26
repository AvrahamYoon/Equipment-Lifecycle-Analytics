"""Per-equipment useful-life extensions (manual inspection) stored as CSV."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

import pandas as pd

from dashboard import constants as C
from dashboard.taxonomy import norm_equip_id

_CSV_COLUMNS = ("equipId", "extraMonths", "note", "reviewBy", "updatedAt")
_MAX_EXTRA_MONTHS = 240


@dataclass(frozen=True)
class LifeOverride:
    equip_id: str
    extra_months: float
    note: str = ""
    review_by: str = ""
    updated_at: str = ""


def _coerce_extra_months(value) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    try:
        n = float(value)
    except (TypeError, ValueError):
        return 0.0
    if n <= 0:
        return 0.0
    return min(n, _MAX_EXTRA_MONTHS)


def _legacy_extra_months(row) -> float:
    """Read extraMonths, or convert legacy extraYears column to months."""
    raw = row.get("extraMonths")
    if raw is not None and not (isinstance(raw, float) and pd.isna(raw)) and str(raw).strip() != "":
        return _coerce_extra_months(raw)
    legacy_years = row.get("extraYears")
    if legacy_years is None or (isinstance(legacy_years, float) and pd.isna(legacy_years)):
        return 0.0
    try:
        years = float(legacy_years)
    except (TypeError, ValueError):
        return 0.0
    if years <= 0:
        return 0.0
    return min(years * 12.0, _MAX_EXTRA_MONTHS)


def _clean_text(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def load_life_overrides(path: str | None = None) -> dict[str, LifeOverride]:
    """Read overrides CSV into equipId → LifeOverride (empty dict if missing)."""
    path = path or C.EQUIPMENT_LIFE_OVERRIDES_CSV
    if not path or not os.path.isfile(path):
        return {}
    try:
        df = pd.read_csv(path, encoding_errors="replace")
    except OSError:
        return {}
    if df.empty:
        return {}

    out: dict[str, LifeOverride] = {}
    for _, row in df.iterrows():
        eid = norm_equip_id(row.get("equipId"))
        extra = _legacy_extra_months(row)
        if not eid or extra <= 0:
            continue
        out[eid] = LifeOverride(
            equip_id=eid,
            extra_months=extra,
            note=_clean_text(row.get("note")),
            review_by=_clean_text(row.get("reviewBy")),
            updated_at=_clean_text(row.get("updatedAt")),
        )
    return out


def save_life_overrides(
    overrides: dict[str, LifeOverride],
    path: str | None = None,
) -> None:
    """Write all overrides to CSV (sorted by equipId)."""
    path = path or C.EQUIPMENT_LIFE_OVERRIDES_CSV
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = []
    for eid in sorted(overrides):
        o = overrides[eid]
        if o.extra_months <= 0:
            continue
        rows.append(
            {
                "equipId": eid,
                "extraMonths": int(round(o.extra_months)),
                "note": o.note,
                "reviewBy": o.review_by,
                "updatedAt": o.updated_at,
            }
        )
    df = pd.DataFrame(rows, columns=list(_CSV_COLUMNS))
    df.to_csv(path, index=False)


def upsert_life_override(
    equip_id,
    extra_months,
    *,
    note: str = "",
    review_by: str = "",
    path: str | None = None,
) -> dict[str, LifeOverride]:
    """Insert, update, or remove one override; returns the full map after save."""
    path = path or C.EQUIPMENT_LIFE_OVERRIDES_CSV
    eid = norm_equip_id(equip_id)
    if not eid:
        raise ValueError("Equipment ID is required")

    overrides = load_life_overrides(path)
    extra = _coerce_extra_months(extra_months)
    if extra <= 0:
        overrides.pop(eid, None)
    else:
        overrides[eid] = LifeOverride(
            equip_id=eid,
            extra_months=extra,
            note=_clean_text(note),
            review_by=_clean_text(review_by),
            updated_at=date.today().isoformat(),
        )
    save_life_overrides(overrides, path)
    return overrides


def format_life_adj(extra_months: float | None) -> str:
    if extra_months is None or extra_months <= 0:
        return "—"
    return f"+{int(round(float(extra_months)))} mo"

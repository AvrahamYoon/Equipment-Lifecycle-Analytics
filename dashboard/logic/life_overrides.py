"""Per-equipment useful-life extensions (manual inspection) stored as CSV."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

import pandas as pd

from dashboard import constants as C
from dashboard.taxonomy import norm_equip_id

_CSV_COLUMNS = ("equipId", "extraYears", "note", "reviewBy", "updatedAt")
_MAX_EXTRA_YEARS = 20.0


@dataclass(frozen=True)
class LifeOverride:
    equip_id: str
    extra_years: float
    note: str = ""
    review_by: str = ""
    updated_at: str = ""


def _coerce_extra_years(value) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    try:
        n = float(value)
    except (TypeError, ValueError):
        return 0.0
    if n <= 0:
        return 0.0
    return min(n, _MAX_EXTRA_YEARS)


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
        extra = _coerce_extra_years(row.get("extraYears"))
        if not eid or extra <= 0:
            continue
        out[eid] = LifeOverride(
            equip_id=eid,
            extra_years=extra,
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
        if o.extra_years <= 0:
            continue
        rows.append(
            {
                "equipId": eid,
                "extraYears": round(o.extra_years, 2),
                "note": o.note,
                "reviewBy": o.review_by,
                "updatedAt": o.updated_at,
            }
        )
    df = pd.DataFrame(rows, columns=list(_CSV_COLUMNS))
    df.to_csv(path, index=False)


def upsert_life_override(
    equip_id,
    extra_years,
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
    extra = _coerce_extra_years(extra_years)
    if extra <= 0:
        overrides.pop(eid, None)
    else:
        overrides[eid] = LifeOverride(
            equip_id=eid,
            extra_years=extra,
            note=_clean_text(note),
            review_by=_clean_text(review_by),
            updated_at=date.today().isoformat(),
        )
    save_life_overrides(overrides, path)
    return overrides


def format_life_adj(extra_years: float | None) -> str:
    if extra_years is None or extra_years <= 0:
        return "—"
    if float(extra_years).is_integer():
        return f"+{int(extra_years)}y"
    return f"+{extra_years:.1f}y"

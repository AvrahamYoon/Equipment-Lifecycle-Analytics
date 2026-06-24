"""Equipment age, useful life, and book value for the Replacement table."""

from __future__ import annotations

import os
import statistics
from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd

from dashboard import constants as C
from dashboard.taxonomy import norm_equip_id, normalize_equip_type
from valuation import (
    equip_type_from_equipment_name,
    extract_keyword_key,
    parse_purchase_year,
    pick_column,
)

DEP_BASIS_COLUMN = "Depreciation basis"
DEP_BASIS_CONFIRMED = "Confirmed"
DEP_BASIS_ESTIMATED = "Estimated"
DEP_BASIS_UNKNOWN = "—"

BOOK_VALUE_TOOLTIP = (
    "Estimated accounting value after straight-line depreciation "
    "(original cost down to 5% salvage). Low book value means the asset "
    "is near the end of its useful life — not the same as repair spend."
)

_DIRECT_AGE_SOURCES = frozenset({"summary_date", "purchase_year"})
_DIRECT_LIFE_SOURCES = frozenset({"purchase_id", "summary"})


@dataclass(frozen=True)
class TypeDepreciationStats:
    median_age: float | None
    median_life: float | None
    n: int


@dataclass(frozen=True)
class PurchaseDepreciationStats:
    by_id: dict[str, dict[str, Any]]
    by_keyword: dict[str, TypeDepreciationStats]
    by_equip_type: dict[str, TypeDepreciationStats]
    fleet_median_age: float | None
    fleet_median_life: float | None


@dataclass(frozen=True)
class DepreciationResult:
    age_years: float | None
    useful_life_years: float | None
    book_value: float | None
    basis_label: str
    age_source: str
    life_source: str


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    return float(statistics.median(values))


def _coerce_life(value) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _age_from_year(year: int, *, today: date | None = None) -> float:
    ref = today or date.today()
    return (ref.year - int(year)) + 0.5


def _age_from_purchase_date(purchase_date, *, today: date | None = None) -> float | None:
    ts = pd.to_datetime(purchase_date, errors="coerce")
    if pd.isna(ts):
        return None
    ref = pd.Timestamp(today or date.today())
    days = (ref - ts).days
    if days < 0:
        return 0.0
    return days / 365.25


def build_equip_meta_lookup(df_equip: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Equipment ID → summary purchase date and depreciation years."""
    if df_equip is None or df_equip.empty:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for _, row in df_equip.iterrows():
        eid = norm_equip_id(row.get("equipIdNorm") or row.get("EquipmentId"))
        if not eid:
            continue
        purchase_date = pd.to_datetime(row.get("PurchaseDate"), errors="coerce")
        out[eid] = {
            "purchase_date": purchase_date if not pd.isna(purchase_date) else None,
            "depreciation_years": _coerce_life(row.get("DepreciationYears")),
            "equip_type": normalize_equip_type(row.get("EquipType")),
        }
    return out


def build_purchase_depreciation_stats(
    purchase_path: str,
    type_map: dict[str, str] | None = None,
    *,
    today: date | None = None,
) -> PurchaseDepreciationStats:
    """Median age/life cohorts from ``purchase.csv`` (keyword + EquipType)."""
    if not purchase_path or not os.path.isfile(purchase_path):
        return PurchaseDepreciationStats({}, {}, {}, None, None)

    try:
        df = pd.read_csv(purchase_path, encoding_errors="replace")
    except OSError:
        return PurchaseDepreciationStats({}, {}, {}, None, None)
    if df.empty:
        return PurchaseDepreciationStats({}, {}, {}, None, None)

    id_col = pick_column(df, "ID #", "ID", "Equipment ID", "EquipmentId")
    desc_col = pick_column(df, "Description", "Equip. Name", "Equipment Name")
    year_col = pick_column(df, "pur.", "pur", "Purchase Year", "Year", "Purch. Date")
    life_col = pick_column(df, "Life", "Depreciation Yrs", "DepreciationYears")
    if not id_col:
        return PurchaseDepreciationStats({}, {}, {}, None, None)

    type_map = type_map or {}
    ref = today or date.today()
    by_id: dict[str, dict[str, Any]] = {}
    keyword_ages: dict[str, list[float]] = {}
    keyword_lives: dict[str, list[float]] = {}
    type_ages: dict[str, list[float]] = {}
    type_lives: dict[str, list[float]] = {}
    fleet_ages: list[float] = []
    fleet_lives: list[float] = []

    for _, row in df.iterrows():
        eid = norm_equip_id(row.get(id_col))
        if not eid:
            continue

        year = parse_purchase_year(row.get(year_col)) if year_col else None
        life = _coerce_life(row.get(life_col)) if life_col else None
        if eid not in by_id:
            by_id[eid] = {"year": year, "life": life}

        description = str(row.get(desc_col, "")).strip() if desc_col else ""
        keyword = extract_keyword_key(description) if description else None
        equip_type = normalize_equip_type(type_map.get(eid, ""))
        if not equip_type and description:
            inferred = equip_type_from_equipment_name(description)
            if inferred:
                equip_type = normalize_equip_type(inferred)

        if year is not None:
            age = _age_from_year(year, today=ref)
            fleet_ages.append(age)
            if keyword:
                keyword_ages.setdefault(keyword, []).append(age)
            if equip_type:
                type_ages.setdefault(equip_type, []).append(age)

        if life is not None:
            fleet_lives.append(life)
            if keyword:
                keyword_lives.setdefault(keyword, []).append(life)
            if equip_type:
                type_lives.setdefault(equip_type, []).append(life)

    def _type_stats(
        ages: dict[str, list[float]],
        lives: dict[str, list[float]],
    ) -> dict[str, TypeDepreciationStats]:
        keys = set(ages) | set(lives)
        out: dict[str, TypeDepreciationStats] = {}
        for key in keys:
            age_vals = ages.get(key, [])
            life_vals = lives.get(key, [])
            out[key] = TypeDepreciationStats(
                median_age=_median(age_vals),
                median_life=_median(life_vals),
                n=max(len(age_vals), len(life_vals)),
            )
        return out

    return PurchaseDepreciationStats(
        by_id=by_id,
        by_keyword=_type_stats(keyword_ages, keyword_lives),
        by_equip_type=_type_stats(type_ages, type_lives),
        fleet_median_age=_median(fleet_ages),
        fleet_median_life=_median(fleet_lives),
    )


def _lookup_type_stats(
    stats: PurchaseDepreciationStats,
    *,
    equipment_name: str,
    equip_type: str,
) -> TypeDepreciationStats | None:
    keyword = extract_keyword_key(equipment_name or "")
    if keyword and keyword in stats.by_keyword:
        return stats.by_keyword[keyword]
    equip_type = normalize_equip_type(equip_type)
    if equip_type and equip_type in stats.by_equip_type:
        return stats.by_equip_type[equip_type]
    return None


def _book_value(cost: float, age: float, useful_life: float) -> float:
    dep_ratio = min(1.0, max(0.0, age / useful_life))
    floor = cost * C.DEPRECIATION_SALVAGE_PCT
    return max(floor, cost * (1.0 - dep_ratio))


def life_replace_status(
    age_years: float | None,
    useful_life_years: float | None,
) -> str | None:
    """Replace / Monitor from age vs useful life (book value near salvage)."""
    if age_years is None or useful_life_years is None or useful_life_years <= 0:
        return None
    ratio = float(age_years) / float(useful_life_years)
    if ratio >= C.LIFE_REPLACE_RATIO:
        return "Replace"
    if ratio >= C.LIFE_MONITOR_RATIO:
        return "Monitor"
    return "Good"


def resolve_depreciation(
    equip_id,
    equipment_name: str,
    *,
    equip_type: str = "",
    new_price: float | None = None,
    stats: PurchaseDepreciationStats | None = None,
    equip_meta: dict[str, dict[str, Any]] | None = None,
    today: date | None = None,
) -> DepreciationResult:
    """Resolve age, useful life, and straight-line book value for one asset."""
    stats = stats or PurchaseDepreciationStats({}, {}, {}, None, None)
    equip_meta = equip_meta or {}
    eid = norm_equip_id(equip_id)
    meta = equip_meta.get(eid, {})
    purchase_row = stats.by_id.get(eid, {})

    age_years: float | None = None
    age_source = "none"
    purchase_date = meta.get("purchase_date")
    if purchase_date is not None:
        age_years = _age_from_purchase_date(purchase_date, today=today)
        if age_years is not None:
            age_source = "summary_date"
    if age_years is None:
        year = purchase_row.get("year")
        if year is not None:
            age_years = _age_from_year(year, today=today)
            age_source = "purchase_year"
    if age_years is None:
        cohort = _lookup_type_stats(
            stats,
            equipment_name=equipment_name or "",
            equip_type=equip_type or meta.get("equip_type", ""),
        )
        if cohort and cohort.median_age is not None:
            age_years = cohort.median_age
            age_source = "purchase_type_median"
        elif stats.fleet_median_age is not None:
            age_years = stats.fleet_median_age
            age_source = "purchase_fleet_median"

    useful_life: float | None = None
    life_source = "none"
    life_from_purchase = _coerce_life(purchase_row.get("life"))
    if life_from_purchase is not None:
        useful_life = life_from_purchase
        life_source = "purchase_id"
    elif meta.get("depreciation_years") is not None:
        useful_life = meta["depreciation_years"]
        life_source = "summary"
    else:
        cohort = _lookup_type_stats(
            stats,
            equipment_name=equipment_name or "",
            equip_type=equip_type or meta.get("equip_type", ""),
        )
        if cohort and cohort.median_life is not None:
            useful_life = cohort.median_life
            life_source = "purchase_type_median"
        elif stats.fleet_median_life is not None:
            useful_life = stats.fleet_median_life
            life_source = "purchase_fleet_median"
        else:
            useful_life = float(C.DEFAULT_USEFUL_LIFE_YEARS)
            life_source = "default"

    try:
        cost = float(new_price or 0)
    except (TypeError, ValueError):
        cost = 0.0

    book_value: float | None = None
    basis_label = DEP_BASIS_UNKNOWN
    if (
        age_years is not None
        and useful_life is not None
        and useful_life > 0
        and cost > 0
    ):
        book_value = _book_value(cost, age_years, useful_life)
        if age_source in _DIRECT_AGE_SOURCES and life_source in _DIRECT_LIFE_SOURCES:
            basis_label = DEP_BASIS_CONFIRMED
        else:
            basis_label = DEP_BASIS_ESTIMATED

    return DepreciationResult(
        age_years=age_years,
        useful_life_years=useful_life,
        book_value=book_value,
        basis_label=basis_label,
        age_source=age_source,
        life_source=life_source,
    )

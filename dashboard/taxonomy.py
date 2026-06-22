"""Equipment category: EquipType from cleaned summary and purchase/Type.csv."""

from __future__ import annotations

import os
from collections.abc import Iterable

import pandas as pd


def norm_equip_id(x) -> str:
    """Canonical ID for matching, grouping, and display (spaces removed, uppercased).

    Raw columns (``equipId``, ``Equipment Id``, etc.) stay as exported; use this or
    ``equipIdNorm`` whenever IDs are consumed or shown.
    """
    if pd.isna(x):
        return ""
    return str(x).replace(" ", "").strip().upper()


def ensure_equip_id_norm_column(
    df: pd.DataFrame,
    raw_col: str = "equipId",
    norm_col: str = "equipIdNorm",
) -> pd.DataFrame:
    """Add or refresh ``norm_col`` from ``raw_col`` without modifying the raw column."""
    out = df.copy()
    if raw_col not in out.columns:
        out[norm_col] = ""
        return out
    out[norm_col] = out[raw_col].map(norm_equip_id)
    return out


def filter_equip_id_substr(series: pd.Series, query: str) -> pd.Series:
    """Case-insensitive substring filter on normalized IDs (ignores spaces in query)."""
    q = norm_equip_id(query).lower()
    if not q:
        return pd.Series(True, index=series.index)
    normed = series.map(norm_equip_id).str.lower()
    return normed.str.contains(q, na=False, regex=False)


def equipment_chart_class(text: str) -> str:
    """Fallback when EquipType is missing: infer a coarse bucket from equipment name."""
    t = str(text).strip().lower()
    if not t:
        return "Other"

    if "versamatic" in t:
        return "Versamatic"
    if "lindhaus" in t:
        return "Lindhaus"
    if "kaivac" in t:
        return "Kaivac"

    if "ladder" in t:
        return "Ladders"
    if "dispenser" in t or "chemical disp" in t:
        return "Dispensers"

    if any(
        k in t
        for k in ("burnisher", "buffer", "scrubber", "auto scrub", "autoscrub", "floor machine")
    ):
        return "Floor machines"
    if any(k in t for k in ("extractor", "carpet ", "carpet-", "spotter")):
        return "Carpet / extractors"

    if any(
        k in t
        for k in ("wet-dry", "wet dry", "wet/dry", "wetdry", "shop vac", "shop-vac", "shopvac")
    ):
        return "Wet-dry / shop vacuums"
    if "viper" in t:
        return "Wet-dry / shop vacuums"

    if "vacuum" in t or t.endswith(" vac") or " vac " in t:
        return "Other vacuums"

    if any(k in t for k in ("cart", "janitor", "mop bucket", "mop ", "wringer")):
        return "Janitorial / carts"

    return "Other"


_CHART_CLASS_TO_EQUIP_TYPE: dict[str, str] = {
    "Versamatic": "Vacuum",
    "Lindhaus": "Vacuum",
    "Kaivac": "Kaivac",
    "Ladders": "Ladder",
    "Dispensers": "Chemical Dispenser",
    "Floor machines": "Scrubber",
    "Carpet / extractors": "Carpet Cleaning",
    "Wet-dry / shop vacuums": "Vacuum",
    "Other vacuums": "Vacuum",
}

_NAME_COL_CANDIDATES = (
    "equipment",
    "Equipment Name",
    "Equipment name",
    "Name",
    "Equipment",
)


def pick_equipment_name_column(df: pd.DataFrame) -> str | None:
    for col in _NAME_COL_CANDIDATES:
        if col in df.columns:
            return col
    return None


def infer_equip_category_from_name(name) -> str | None:
    """Name fallback: valuation keyword rules, then legacy chart-class heuristics."""
    if pd.isna(name) or not str(name).strip():
        return None
    from valuation import equip_type_from_equipment_name

    hit = equip_type_from_equipment_name(str(name))
    if hit:
        return hit
    coarse = equipment_chart_class(str(name))
    return _CHART_CLASS_TO_EQUIP_TYPE.get(coarse)


def resolve_equip_category(
    equip_id,
    equipment_name,
    type_map: dict[str, str] | None,
    summary_lookup: dict[str, str] | None = None,
) -> str:
    """Resolve category: ``Type.csv`` → cleaned summary → name inference → Other."""
    eid = norm_equip_id(equip_id)
    if type_map and eid:
        from_purchase = normalize_equip_type(type_map.get(eid, ""))
        if from_purchase:
            return from_purchase
    if summary_lookup and eid:
        from_summary = normalize_equip_type(summary_lookup.get(eid, ""))
        if from_summary and from_summary != "Other":
            return from_summary
    inferred = infer_equip_category_from_name(equipment_name)
    if inferred:
        return inferred
    return "Other"


def normalize_equip_type(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def resolve_type_csv_path(path: str | None = None) -> str | None:
    """Return first existing Type.csv path (configured path, then purchase folder)."""
    candidates: list[str] = []
    if path:
        candidates.append(path)
    base = os.path.join("data", "equipment", "purchase")
    candidates.extend(os.path.join(base, name) for name in ("Type.csv", "type.csv"))
    for p in candidates:
        if p and os.path.isfile(p):
            return p
    return None


def load_equip_type_map(path: str | None = None) -> dict[str, str]:
    """Map normalized equipment ID → ``EquipType`` from purchase ``Type.csv``."""
    resolved = resolve_type_csv_path(path)
    if not resolved:
        return {}
    try:
        df = pd.read_csv(resolved, encoding_errors="replace")
    except Exception:
        return {}
    if df.empty:
        return {}

    id_col = next((c for c in df.columns if norm_equip_id(c) == "EQUIPMENTID"), None)
    type_col = next((c for c in df.columns if norm_equip_id(c) == "EQUIPTYPE"), None)
    if not id_col or not type_col:
        return {}

    lookup: dict[str, str] = {}
    for _, row in df.iterrows():
        eid = norm_equip_id(row[id_col])
        et = normalize_equip_type(row[type_col])
        if eid and et and eid not in lookup:
            lookup[eid] = et
    return lookup


def equipment_row_category(row, type_map: dict[str, str] | None = None) -> str:
    """Category: summary ``EquipType``, else ``Type.csv``, else name inference."""
    et = normalize_equip_type(row.get("EquipType", ""))
    if et:
        return et
    if type_map:
        eid = norm_equip_id(row.get("EquipmentId", row.get("equipIdNorm", "")))
        if eid and type_map.get(eid):
            return type_map[eid]
    name = row.get("Name", row.get("equipment", ""))
    return infer_equip_category_from_name(name) or "Other"


def build_summary_equip_type_map(df_equip: pd.DataFrame) -> dict[str, str]:
    """Equipment ID → ``EquipType`` from cleaned summary only (no name inference)."""
    out: dict[str, str] = {}
    if df_equip.empty or "equipIdNorm" not in df_equip.columns:
        return out
    if "EquipType" not in df_equip.columns:
        return out
    for _, row in df_equip.iterrows():
        eid = norm_equip_id(row["equipIdNorm"])
        et = normalize_equip_type(row.get("EquipType", ""))
        if eid and et:
            out[eid] = et
    return out


def build_equip_category_lookup(
    df_equip: pd.DataFrame,
    type_map: dict[str, str] | None = None,
) -> dict[str, str]:
    """ID → EquipType: ``Type.csv`` first; summary fills IDs not already in purchase types."""
    lookup: dict[str, str] = dict(type_map or {})
    summary = build_summary_equip_type_map(df_equip)
    for eid, et in summary.items():
        if eid not in lookup:
            lookup[eid] = et
    return lookup


def apply_equip_category(
    df: pd.DataFrame,
    summary_lookup: dict[str, str] | None,
    *,
    type_map: dict[str, str] | None = None,
    id_col: str = "equipIdNorm",
    name_col: str | None = None,
) -> pd.DataFrame:
    """Attach ``equipCategory``: purchase ``Type.csv`` → summary → name inference."""
    out = df.copy()
    resolved_name_col = name_col or pick_equipment_name_column(out)

    def _row_category(row: pd.Series) -> str:
        eid = row[id_col] if id_col in row.index else ""
        name = row[resolved_name_col] if resolved_name_col and resolved_name_col in row.index else ""
        return resolve_equip_category(eid, name, type_map, summary_lookup)

    if id_col in out.columns or resolved_name_col:
        out["equipCategory"] = out.apply(_row_category, axis=1)
    else:
        out["equipCategory"] = "Other"
    blank = out["equipCategory"].astype(str).str.strip() == ""
    out.loc[blank, "equipCategory"] = "Other"
    return out


def chart_category_rank(categories: Iterable[str]) -> dict[str, int]:
    """Sort key for chart axes: preferred EquipType order, then any extras alphabetically."""
    from dashboard import constants as C

    rank = {c: i for i, c in enumerate(C.CHART_CLASS_ORDER)}
    n = len(rank)
    for c in sorted({str(x) for x in categories if str(x).strip()}):
        if c not in rank:
            rank[c] = n
            n += 1
    return rank

"""Equipment name / type → chart bucket."""

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


def equipment_row_category(row) -> str:
    name = row.get("Name", "")
    if pd.notna(name) and str(name).strip():
        return equipment_chart_class(str(name))
    et = row.get("EquipType", "")
    if pd.notna(et) and str(et).strip():
        return equipment_chart_class(str(et))
    return "Other"

"""Equipment name / type → chart bucket."""

import pandas as pd


def norm_equip_id(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).replace(" ", "").strip().upper()


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

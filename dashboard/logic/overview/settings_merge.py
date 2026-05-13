"""Merge persisted settings with defaults and coerce to safe ranges."""

from dashboard import constants as C

_ICON_KEYS = (
    "iconKpiRequests",
    "iconKpiCompleted",
    "iconKpiScheduled",
    "iconKpiRepairCost",
    "iconKpiParts",
    "iconKpiLabor",
    "iconNavOverview",
    "iconNavReplacement",
    "iconNavOrders",
    "iconNavSettings",
    "iconReplaceTitle",
    "iconReplaceStatusReplace",
    "iconReplaceStatusMonitor",
    "iconReplaceStatusGood",
)


def _sanitize_icon(value, default: str, max_chars: int = 12) -> str:
    if value is None:
        return default
    t = str(value).strip()
    if not t:
        return default
    return t[:max_chars]


def _coerce_int(v, default: int, lo: int, hi: int) -> int:
    try:
        n = int(float(v))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def _coerce_float(v, default: float, lo: float, hi: float) -> float:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def _merge_month_capacity_map(raw_map, merged_globals: dict) -> dict[str, dict]:
    """Build sanitized staffCapacityByMonth from persisted dict."""
    out: dict[str, dict] = {}
    if not isinstance(raw_map, dict):
        return out
    g_sc = int(merged_globals["staffCount"])
    g_hd = float(merged_globals["hoursPerDay"])
    g_wd = int(merged_globals["workDays"])
    for mk, inner in raw_map.items():
        mk_s = str(mk).strip()
        if not mk_s or not isinstance(inner, dict):
            continue
        out[mk_s] = {
            "staffCount": _coerce_int(inner.get("staffCount"), g_sc, 1, 500),
            "hoursPerDay": _coerce_float(inner.get("hoursPerDay"), g_hd, 0.25, 24.0),
            "workDays": _coerce_int(inner.get("workDays"), g_wd, 1, 31),
        }
    return out


def staff_capacity_for_month(settings: dict, month_key: str | None) -> tuple[int, float, int]:
    """Resolved staff / hours / work_days for Overview (per-month override or global defaults)."""
    sc = int(settings["staffCount"])
    hd = float(settings["hoursPerDay"])
    wd = int(settings["workDays"])
    if month_key is None or (isinstance(month_key, float) and str(month_key) == "nan"):
        return sc, hd, wd
    mk = str(month_key).strip()
    if not mk or mk == "NaT":
        return sc, hd, wd
    bym = settings.get("staffCapacityByMonth")
    if not isinstance(bym, dict):
        return sc, hd, wd
    inner = bym.get(mk)
    if not isinstance(inner, dict):
        return sc, hd, wd
    return (
        _coerce_int(inner.get("staffCount"), sc, 1, 500),
        _coerce_float(inner.get("hoursPerDay"), hd, 0.25, 24.0),
        _coerce_int(inner.get("workDays"), wd, 1, 31),
    )


def sanitise_capacity_triple(staff, hours, days) -> tuple[int, float, int]:
    """Coerce staff / hours / work_days from form inputs (fallback = app defaults)."""
    d = C.default_app_settings()
    return (
        _coerce_int(staff, int(d["staffCount"]), 1, 500),
        _coerce_float(hours, float(d["hoursPerDay"]), 0.25, 24.0),
        _coerce_int(days, int(d["workDays"]), 1, 31),
    )


def merge_app_settings(raw) -> dict:
    d = C.default_app_settings()
    if not isinstance(raw, dict):
        return d.copy()

    def _int(key, lo, hi, default):
        v = raw.get(key, d[key])
        try:
            n = int(float(v))
        except (TypeError, ValueError):
            return default
        return max(lo, min(hi, n))

    def _float(key, lo, hi, default):
        v = raw.get(key, d[key])
        try:
            n = float(v)
        except (TypeError, ValueError):
            return default
        return max(lo, min(hi, n))

    out = d.copy()
    out["staffCount"] = _int("staffCount", 1, 500, d["staffCount"])
    out["hoursPerDay"] = _float("hoursPerDay", 0.25, 24.0, float(d["hoursPerDay"]))
    out["workDays"] = _int("workDays", 1, 31, d["workDays"])
    out["baseAvailDays"] = _int("baseAvailDays", 1, 3660, d["baseAvailDays"])
    wk = str(raw.get("weekStartsOn", d["weekStartsOn"])).lower()
    out["weekStartsOn"] = "monday" if wk == "monday" else "sunday"

    for key in _ICON_KEYS:
        out[key] = _sanitize_icon(raw.get(key, d[key]), d[key])

    raw_m = raw.get("staffCapacityByMonth") if isinstance(raw, dict) else None
    out["staffCapacityByMonth"] = _merge_month_capacity_map(raw_m, out)

    return out


def kpi_icon_list(settings: dict) -> list[str]:
    """Ordered icons for the six KPI cards."""
    keys = (
        "iconKpiRequests",
        "iconKpiCompleted",
        "iconKpiScheduled",
        "iconKpiRepairCost",
        "iconKpiParts",
        "iconKpiLabor",
    )
    d = C.default_app_settings()
    return [_sanitize_icon(settings.get(k, d.get(k)), d[k]) for k in keys]


def replace_status_icons(settings: dict) -> dict[str, str]:
    """Emoji/prefix for Replace / Monitor / Good table badges."""
    d = C.default_app_settings()
    return {
        "Replace": _sanitize_icon(
            settings.get("iconReplaceStatusReplace", d["iconReplaceStatusReplace"]),
            d["iconReplaceStatusReplace"],
        ),
        "Monitor": _sanitize_icon(
            settings.get("iconReplaceStatusMonitor", d["iconReplaceStatusMonitor"]),
            d["iconReplaceStatusMonitor"],
        ),
        "Good": _sanitize_icon(
            settings.get("iconReplaceStatusGood", d["iconReplaceStatusGood"]),
            d["iconReplaceStatusGood"],
        ),
    }

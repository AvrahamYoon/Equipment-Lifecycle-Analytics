"""Service order status and de-duplication for dashboard display.

Cleaned CSVs are unchanged; this module shapes what Overview / Orders show:

- **Effective status** — cross-month exports (April Scheduled + May Completed).
- **De-dupe** — same equipment, description, and schedule month: if one row is an
  open stub (no completion date) and another has completion data, keep one row.
  Applies to single-month views and **All months** so totals are not stacked.
"""

from __future__ import annotations

import re

import pandas as pd

from dashboard import constants as C
from dashboard.taxonomy import norm_equip_id


def _norm_desc(desc) -> str:
    s = str(desc or "").strip().lower()
    s = re.sub(r"\s*-\s*\(repair\)\s*$", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s)
    return s[:80]


def service_work_key(row) -> tuple[str, str]:
    eid = norm_equip_id(row.get("Equipment Id", row.get("equipIdNorm", "")))
    return eid, _norm_desc(row.get("Description", ""))


def display_work_key(row) -> tuple[str, str, str]:
    """Identity for display de-dupe: same job in two monthly exports."""
    eid, desc = service_work_key(row)
    sched = pd.to_datetime(row.get("Sched. Date"), errors="coerce")
    period = sched.to_period("M").strftime("%Y-%m") if pd.notna(sched) else ""
    return eid, desc, period


def _completion_index(svc_all: pd.DataFrame) -> dict[tuple[str, str], bool]:
    has_done: dict[tuple[str, str], bool] = {}
    if svc_all.empty:
        return has_done

    comp = pd.to_datetime(svc_all["Completed Date"], errors="coerce")
    for i, row in svc_all.iterrows():
        if pd.isna(comp.loc[i]):
            continue
        has_done[service_work_key(row)] = True
    return has_done


def _month_end(month_key: str) -> pd.Timestamp | None:
    try:
        return pd.Period(str(month_key), freq="M").to_timestamp(how="end")
    except (ValueError, TypeError):
        return None


def _raw_status(row) -> str:
    raw = str(row.get("Status", "")).strip().lower()
    return "Completed" if raw == "completed" else "Scheduled"


def _row_completeness_rank(row) -> tuple:
    """Pick the best row when two exports describe the same work."""
    comp = pd.to_datetime(row.get("Completed Date"), errors="coerce")
    sched = pd.to_datetime(row.get("Sched. Date"), errors="coerce")
    has_comp = pd.notna(comp)
    status_completed = str(row.get("Status", "")).strip().lower() == "completed"
    comp_ord = comp.value if has_comp else 0
    sched_ord = sched.value if pd.notna(sched) else 0
    return (int(has_comp), int(status_completed), comp_ord, sched_ord)


def apply_effective_service_status(
    svc: pd.DataFrame,
    month_key: str,
    svc_all: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Set ``Status`` for the month selector (before de-dupe)."""
    if svc.empty or "Status" not in svc.columns:
        return svc

    out = svc.copy()
    statuses: list[str] = []

    if C.is_all_months(month_key):
        catalog = svc_all if svc_all is not None else svc
        if "month_key" in catalog.columns:
            catalog = catalog[catalog["month_key"].astype(str) != "NaT"]
        has_done = _completion_index(catalog)
        for _, row in out.iterrows():
            if has_done.get(service_work_key(row)):
                statuses.append("Completed")
            else:
                statuses.append(_raw_status(row))
    else:
        period_end = _month_end(month_key)
        for _, row in out.iterrows():
            comp = pd.to_datetime(row.get("Completed Date"), errors="coerce")
            if period_end is not None and pd.notna(comp) and comp > period_end:
                statuses.append("Scheduled")
            else:
                statuses.append(_raw_status(row))

    out["Status"] = statuses
    return out


def _is_stale_duplicate_group(group: pd.DataFrame) -> bool:
    """True when one export row is an open stub and another has completion data."""
    if len(group) < 2:
        return False
    comp = pd.to_datetime(group["Completed Date"], errors="coerce")
    return comp.isna().any() and comp.notna().any()


def dedupe_service_for_display(svc: pd.DataFrame) -> pd.DataFrame:
    """Collapse stale + updated export pairs; keep unrelated lines separate."""
    if svc.empty:
        return svc

    work_keys = svc.apply(display_work_key, axis=1)
    svc = svc.copy()
    svc["_display_key"] = work_keys

    picked: list[pd.Series] = []
    for _, group in svc.groupby("_display_key", sort=False):
        if _is_stale_duplicate_group(group):
            best_idx = max(
                group.index,
                key=lambda i: _row_completeness_rank(group.loc[i]),
            )
            picked.append(group.loc[best_idx])
        else:
            for idx in group.index:
                picked.append(group.loc[idx])

    out = pd.DataFrame(picked)
    return out.drop(columns=["_display_key"], errors="ignore").reset_index(drop=True)


def prepare_service_for_display(
    svc: pd.DataFrame,
    month_key: str,
    svc_all: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Effective status, then drop stale duplicate export rows (all month scopes)."""
    svc = apply_effective_service_status(svc, month_key, svc_all)
    return dedupe_service_for_display(svc)

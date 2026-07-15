"""Service order status and de-duplication for dashboard display.

Cleaned CSVs are unchanged; this module shapes what Overview / Orders show:

- **Effective status** — cross-month exports (April Scheduled + May Completed).
- **De-dupe** — same equipment, description, and schedule month: if one row is an
  open stub (no completion date) and another has completion data, keep one row.
- **All months** — open stubs from earlier months are dropped (they show as
  unfinished in a single-month snapshot, but later months are treated as the
  outcome). Only the latest loaded month can still contribute Scheduled rows.
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


def _soft_norm_desc(desc) -> str:
    """Looser identity for matching near-duplicate found/lost notes."""
    s = _norm_desc(desc)
    s = re.sub(r"\b(rig|closet|room|bldg|building)\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:80]


def service_work_key(row) -> tuple[str, str]:
    eid = norm_equip_id(row.get("Equipment Id", row.get("equipIdNorm", "")))
    return eid, _norm_desc(row.get("Description", ""))


def display_work_key(row, *, soft: bool = False) -> tuple[str, str, str]:
    """Identity for display de-dupe: same job in two monthly exports."""
    eid = norm_equip_id(row.get("Equipment Id", row.get("equipIdNorm", "")))
    desc = (
        _soft_norm_desc(row.get("Description", ""))
        if soft
        else _norm_desc(row.get("Description", ""))
    )
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
        # Soft key so "Found in 154" matches "Found in RIG 154".
        eid = norm_equip_id(row.get("Equipment Id", row.get("equipIdNorm", "")))
        has_done[(eid, _soft_norm_desc(row.get("Description", "")))] = True
    return has_done


def _later_completion_by_equip(svc_all: pd.DataFrame) -> dict[str, pd.Timestamp]:
    """Earliest completion date per equipment (for resolving earlier open stubs)."""
    out: dict[str, pd.Timestamp] = {}
    if svc_all.empty:
        return out
    comp = pd.to_datetime(svc_all["Completed Date"], errors="coerce")
    for i, row in svc_all.iterrows():
        if pd.isna(comp.loc[i]):
            continue
        eid = norm_equip_id(row.get("Equipment Id", row.get("equipIdNorm", "")))
        if not eid:
            continue
        dt = comp.loc[i]
        prev = out.get(eid)
        if prev is None or dt < prev:
            out[eid] = dt
    return out


def _latest_month_key(catalog: pd.DataFrame) -> str | None:
    if catalog.empty or "month_key" not in catalog.columns:
        return None
    keys = [
        str(m)
        for m in catalog["month_key"].dropna().unique()
        if str(m) not in ("", "NaT", "nan", "None")
    ]
    return max(keys) if keys else None


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
        later_comp = _later_completion_by_equip(catalog)
        for _, row in out.iterrows():
            eid, desc = service_work_key(row)
            soft = (eid, _soft_norm_desc(row.get("Description", "")))
            if has_done.get((eid, desc)) or has_done.get(soft):
                statuses.append("Completed")
                continue
            sched = pd.to_datetime(row.get("Sched. Date"), errors="coerce")
            first_done = later_comp.get(eid)
            if first_done is not None and pd.notna(sched) and first_done > sched:
                statuses.append("Completed")
                continue
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


def _drop_prior_open_stubs(svc: pd.DataFrame, catalog: pd.DataFrame) -> pd.DataFrame:
    """In All months, unfinished rows from earlier months are historical snapshots.

    Later months are treated as the outcome, so prior open stubs should not
    remain in Completed/Total as Scheduled.
    """
    if svc.empty or "month_key" not in svc.columns:
        return svc
    latest = _latest_month_key(catalog if not catalog.empty else svc)
    if not latest:
        return svc
    comp = pd.to_datetime(svc["Completed Date"], errors="coerce")
    prior_open = comp.isna() & (svc["month_key"].astype(str) < latest)
    return svc.loc[~prior_open].reset_index(drop=True)


def _is_stale_duplicate_group(group: pd.DataFrame) -> bool:
    """True when one export row is an open stub and another has completion data."""
    if len(group) < 2:
        return False
    comp = pd.to_datetime(group["Completed Date"], errors="coerce")
    return comp.isna().any() and comp.notna().any()


def dedupe_service_for_display(svc: pd.DataFrame, *, soft: bool = False) -> pd.DataFrame:
    """Collapse stale + updated export pairs; keep unrelated lines separate."""
    if svc.empty:
        return svc

    work_keys = svc.apply(lambda r: display_work_key(r, soft=soft), axis=1)
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
    all_months = C.is_all_months(month_key)
    catalog = svc_all if svc_all is not None else svc
    if all_months and catalog is not None and "month_key" in catalog.columns:
        catalog = catalog[catalog["month_key"].astype(str) != "NaT"]

    svc = apply_effective_service_status(svc, month_key, svc_all)
    if all_months:
        svc = _drop_prior_open_stubs(svc, catalog if catalog is not None else svc)
    return dedupe_service_for_display(svc, soft=all_months)

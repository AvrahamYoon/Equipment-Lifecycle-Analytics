"""Service order status for the selected month scope.

Exports can list the same work twice (e.g. April extract still Scheduled, May
extract Completed). Dashboard logic resolves that without changing cleaned CSVs:

- **All months**: treat work as Completed when any loaded row has a completion date.
- **Single month**: Completed only if completion falls on or before that month-end
  (April plan / May finish → still Scheduled in April, Completed in All months).
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


def _completion_index(svc_all: pd.DataFrame) -> tuple[dict[tuple[str, str], bool], dict[tuple[str, str], pd.Timestamp]]:
    """Per work key: ever completed in loaded data, and latest completion date."""
    has_done: dict[tuple[str, str], bool] = {}
    max_done: dict[tuple[str, str], pd.Timestamp] = {}
    if svc_all.empty:
        return has_done, max_done

    comp = pd.to_datetime(svc_all["Completed Date"], errors="coerce")
    for i, row in svc_all.iterrows():
        key = service_work_key(row)
        c = comp.loc[i]
        if pd.isna(c):
            continue
        has_done[key] = True
        prev = max_done.get(key)
        max_done[key] = c if prev is None or c > prev else prev
    return has_done, max_done


def apply_effective_service_status(
    svc: pd.DataFrame,
    month_key: str,
    svc_all: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return ``svc`` with ``Status`` set for the current month selector."""
    if svc.empty or "Status" not in svc.columns:
        return svc

    catalog = svc_all if svc_all is not None else svc
    catalog = catalog[catalog["month_key"].astype(str) != "NaT"] if "month_key" in catalog.columns else catalog
    has_done, max_done = _completion_index(catalog)

    out = svc.copy()
    statuses: list[str] = []

    if C.is_all_months(month_key):
        for _, row in out.iterrows():
            key = service_work_key(row)
            if has_done.get(key):
                statuses.append("Completed")
                continue
            raw = str(row.get("Status", "")).strip().lower()
            statuses.append("Completed" if raw == "completed" else "Scheduled")
    else:
        try:
            period_end = pd.Period(str(month_key), freq="M").to_timestamp(how="end")
        except (ValueError, TypeError):
            period_end = None
        for _, row in out.iterrows():
            key = service_work_key(row)
            latest = max_done.get(key)
            if period_end is not None and latest is not None and latest <= period_end:
                statuses.append("Completed")
            else:
                raw = str(row.get("Status", "")).strip().lower()
                if (
                    period_end is not None
                    and latest is None
                    and raw == "completed"
                ):
                    comp = pd.to_datetime(row.get("Completed Date"), errors="coerce")
                    if pd.notna(comp) and comp <= period_end:
                        statuses.append("Completed")
                        continue
                statuses.append("Scheduled")

    out["Status"] = statuses
    return out

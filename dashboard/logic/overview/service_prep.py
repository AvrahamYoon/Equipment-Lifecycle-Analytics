"""Prepare completed service rows with business-day turnaround."""

import pandas as pd

from dashboard.calendar_util import business_days_inclusive


def prepare_done_svc_with_turnaround(svc: pd.DataFrame) -> pd.DataFrame:
    if svc.empty or "Status" not in svc.columns:
        return pd.DataFrame()

    sc = svc.copy()
    sc["status_l"] = sc["Status"].astype(str).str.strip().str.lower()
    done = sc[
        (sc["status_l"] == "completed")
        & sc["Sched. Date"].notna()
        & sc["Completed Date"].notna()
        & (sc["Completed Date"] >= sc["Sched. Date"])
    ]
    if done.empty:
        return done

    done = done.assign(
        turnaround_bd=done.apply(
            lambda r: business_days_inclusive(r["Sched. Date"], r["Completed Date"]),
            axis=1,
        )
    )
    return done[done["turnaround_bd"].notna()]

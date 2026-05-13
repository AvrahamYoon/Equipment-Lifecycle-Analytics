"""Overview page: KPIs + charts assembled from focused builders."""

from __future__ import annotations

from typing import Any

import pandas as pd

from dashboard import constants as C
from dashboard.logic.overview.figures import (
    build_avg_repair_hours_figure,
    build_availability_figure,
    build_completion_rate_figure,
    build_overview_footer,
    build_repair_hours_figure,
    build_request_calendar_figure,
    build_request_volume_by_month_figure,
    build_staff_capacity_figure,
    build_turnaround_figure,
)
from dashboard.logic.overview.kpis import build_kpi_children
from dashboard.logic.overview.service_prep import prepare_done_svc_with_turnaround
from dashboard.logic.overview.settings_merge import kpi_icon_list, merge_app_settings, staff_capacity_for_month


def _months_in_data(*frames: pd.DataFrame) -> set[str]:
    """Distinct, non-NaT month_key values present across the given frames."""
    months: set[str] = set()
    for f in frames:
        if f is None or f.empty or "month_key" not in f.columns:
            continue
        for m in f["month_key"].dropna().unique():
            ms = str(m)
            if ms and ms != "NaT":
                months.add(ms)
    return months


def build_overview(
    month_key: str,
    req: pd.DataFrame,
    svc: pd.DataFrame,
    rep: pd.DataFrame,
    df_equip: pd.DataFrame,
    app_settings: dict[str, Any] | None = None,
):
    """Returns (kpis, hours_fig, cal_fig, completion_fig, avghours_fig, staff_fig, turnaround_fig, avail_fig, footer)."""
    s = merge_app_settings(app_settings)
    all_months_mode = C.is_all_months(month_key)

    kpis = build_kpi_children(req, svc, rep, kpi_icon_list(s))
    hours_fig = build_repair_hours_figure(rep)
    if all_months_mode:
        cal_fig = build_request_volume_by_month_figure(req)
    else:
        cal_fig = build_request_calendar_figure(month_key, req, s["weekStartsOn"])
    footer = build_overview_footer(month_key, rep, svc)
    completion_fig = build_completion_rate_figure(svc)
    avghours_fig = build_avg_repair_hours_figure(rep)

    if all_months_mode:
        # Aggregate capacity: globals × (count of months that have any activity).
        # Avoids tying the bar to a single calendar month while still giving a
        # meaningful "used vs available" ratio across the whole period.
        num_months = max(len(_months_in_data(req, svc, rep)), 1)
        staff_fig = build_staff_capacity_figure(
            rep,
            int(s["staffCount"]),
            float(s["hoursPerDay"]),
            int(s["workDays"]) * num_months,
        )
    else:
        staff_fig = build_staff_capacity_figure(
            rep,
            *staff_capacity_for_month(s, month_key),
        )

    done_svc = prepare_done_svc_with_turnaround(svc)
    turnaround_fig = build_turnaround_figure(done_svc)
    avail_fig = build_availability_figure(done_svc, df_equip, float(s["baseAvailDays"]))

    return (
        kpis,
        hours_fig,
        cal_fig,
        completion_fig,
        avghours_fig,
        staff_fig,
        turnaround_fig,
        avail_fig,
        footer,
    )

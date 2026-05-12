"""Overview page: KPIs + charts assembled from focused builders."""

from __future__ import annotations

from typing import Any

import pandas as pd

from dashboard.logic.overview.figures import (
    build_avg_repair_hours_figure,
    build_availability_figure,
    build_completion_rate_figure,
    build_overview_footer,
    build_repair_hours_figure,
    build_request_calendar_figure,
    build_staff_capacity_figure,
    build_turnaround_figure,
)
from dashboard.logic.overview.kpis import build_kpi_children
from dashboard.logic.overview.service_prep import prepare_done_svc_with_turnaround
from dashboard.logic.overview.settings_merge import kpi_icon_list, merge_app_settings, staff_capacity_for_month


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

    kpis = build_kpi_children(req, svc, rep, kpi_icon_list(s))
    hours_fig = build_repair_hours_figure(rep)
    cal_fig = build_request_calendar_figure(month_key, req, s["weekStartsOn"])
    footer = build_overview_footer(month_key, rep, svc)
    completion_fig = build_completion_rate_figure(svc)
    avghours_fig = build_avg_repair_hours_figure(rep)
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

"""Overview page: KPIs + charts assembled from focused builders.

The ``req`` / ``svc`` / ``rep`` frames passed in must already be scoped by the
header **Month** control (single ``YYYY-MM`` or every month when ``ALL``).
That scoping happens in ``callbacks.wiring.update_overview`` — it is separate
from the Replacement page, which always aggregates cumulative repairs.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from dashboard import constants as C
from dashboard.logic.overview.figures import (
    build_avg_repair_hours_figure,
    build_availability_figure,
    build_completion_rate_figure,
    build_overview_footer,
    build_parts_budget_donut_figure,
    build_repair_count_distribution_figure,
    build_repair_hours_by_building_figure,
    build_repair_hours_figure,
    build_request_calendar_figure,
    build_request_volume_by_month_figure,
    build_staff_capacity_figure,
    build_turnaround_figure,
    _parts_spend,
)
from dashboard.logic.overview.kpis import build_kpi_children
from dashboard.logic.overview.service_prep import prepare_done_svc_with_turnaround
from dashboard.logic.overview.settings_merge import kpi_icon_list, merge_app_settings, staff_capacity_for_month


def _years_in_data(*frames: pd.DataFrame) -> set[int]:
    years: set[int] = set()
    for f in frames:
        if f is None or f.empty or "month_key" not in f.columns:
            continue
        for m in f["month_key"].dropna().unique():
            ms = str(m)
            if not ms or ms == "NaT":
                continue
            try:
                years.add(int(pd.Period(ms).year))
            except (ValueError, TypeError):
                continue
    return years


def _rep_for_calendar_year(rep_full: pd.DataFrame, year: int) -> pd.DataFrame:
    if rep_full.empty or "month_key" not in rep_full.columns:
        return rep_full.iloc[0:0]
    valid = rep_full["month_key"].notna() & (rep_full["month_key"].astype(str) != "NaT")
    sub = rep_full.loc[valid]
    if sub.empty:
        return sub.iloc[0:0]
    yrs = pd.PeriodIndex(sub["month_key"].astype(str), freq="M").year
    return sub.loc[yrs == year]


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
    rep_full: pd.DataFrame | None = None,
):
    """Assemble Overview outputs for one header scope.

    ``month_key`` mirrors the Month selector (including ``ALL``). Staff
    capacity uses ``staff_capacity_for_month`` in single-month mode and
    scaled globals in ``ALL`` mode — both are Overview-only concerns.

    ``rep_full`` is building-scoped repairs across all loaded months (for
    annual parts budget). When omitted, ``rep`` is used.

    Returns overview chart/kpi tuple including three new charts:
    monthly parts budget donut, annual parts budget donut, repair-count mix
    donut, and repair hours by building (vertical bars).
    """
    if rep_full is None:
        rep_full = rep
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

    monthly_budget = float(s["monthlyPartsBudget"])
    annual_budget = float(s["annualPartsBudget"])
    months_set = _months_in_data(rep)
    years_set = _years_in_data(rep_full if not rep_full.empty else rep)

    if all_months_mode:
        n_mo = max(len(months_set), 1)
        mo_spent = _parts_spend(rep)
        mo_cap = monthly_budget * n_mo
        mo_note = f"{n_mo} months · ${mo_spent:,.0f} / ${mo_cap:,.0f}"
        mo_title = "Monthly parts budget (all loaded months)"
        n_yr = max(len(years_set), 1)
        yr_spent = _parts_spend(rep_full)
        yr_cap = annual_budget * n_yr
        yr_note = f"{n_yr} yr(s) · ${yr_spent:,.0f} / ${yr_cap:,.0f}"
        yr_title = "Annual parts budget (all loaded months)"
    else:
        mo_spent = _parts_spend(rep)
        mo_cap = monthly_budget
        period = pd.Period(str(month_key))
        mo_note = f"{period.strftime('%b %Y')} · ${mo_spent:,.0f} / ${mo_cap:,.0f}"
        mo_title = "Monthly parts budget"
        yr = int(period.year)
        yr_rep = _rep_for_calendar_year(rep_full, yr)
        yr_spent = _parts_spend(yr_rep)
        yr_cap = annual_budget
        yr_note = f"{yr} · ${yr_spent:,.0f} / ${yr_cap:,.0f}"
        yr_title = "Annual parts budget"

    monthly_budget_fig = build_parts_budget_donut_figure(mo_spent, mo_cap, mo_title, mo_note)
    annual_budget_fig = build_parts_budget_donut_figure(yr_spent, yr_cap, yr_title, yr_note)
    repair_count_fig = build_repair_count_distribution_figure(rep)
    building_hours_fig = build_repair_hours_by_building_figure(rep)

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
        monthly_budget_fig,
        annual_budget_fig,
        repair_count_fig,
        building_hours_fig,
    )

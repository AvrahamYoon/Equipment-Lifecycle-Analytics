"""Plotly figures for the overview page (one builder per chart)."""

import calendar

import pandas as pd
import plotly.graph_objects as go

from dashboard import constants as C
from dashboard.logic.buildings import abbreviate_building, normalize_building_value
from dashboard.logic.repair_count_bins import REPAIR_COUNT_BIN_LABELS, repair_count_bin_label
from dashboard.taxonomy import chart_category_rank, equipment_chart_class


def _parts_spend(rep: pd.DataFrame) -> float:
    if rep is None or rep.empty or "parts" not in rep.columns:
        return 0.0
    return float(rep["parts"].sum())


def _building_series(rep: pd.DataFrame) -> pd.Series:
    for col in ("location", "Location", "building", "Building", "site", "Site"):
        if col in rep.columns:
            normed = rep[col].map(normalize_building_value)
            return normed.where(normed.astype(str).str.strip() != "", "Unknown")
    if rep.empty:
        return pd.Series(dtype=str)
    return pd.Series(["Unknown"] * len(rep), index=rep.index)


def build_parts_budget_donut_figure(
    spent: float,
    budget: float,
    title: str,
    scope_note: str = "",
) -> go.Figure:
    """Hollow ring: parts spend vs budget (remaining = budget available)."""
    budget = max(float(budget), 0.01)
    spent = max(float(spent), 0.0)
    available = max(budget - spent, 0.0)
    avail_pct = min(available / budget * 100.0, 100.0)
    over = spent > budget

    used_color = "#ef4444" if over else C.C_ORANGE
    fig = go.Figure(
        go.Pie(
            labels=["Spent", "Available"],
            values=[min(spent, budget), available] if not over else [budget, 0.01],
            hole=0.62,
            marker=dict(colors=[used_color, "#e2e8f0"], line=dict(color="white", width=2)),
            textinfo="none",
            hovertemplate="%{label}: $%{value:,.0f}<extra></extra>",
            sort=False,
            direction="clockwise",
        )
    )
    center = f"{avail_pct:.0f}%<br><span style='font-size:11px'>available</span>"
    if over:
        center = f"{spent / budget * 100:.0f}%<br><span style='font-size:11px'>of budget</span>"
    subtitle = scope_note or f"${spent:,.0f} / ${budget:,.0f}"
    fig.update_layout(
        title=dict(
            text=f"{title}<br><sup style='color:{C.COLOR_TEXT_MUTED}'>{subtitle}</sup>",
            font=dict(
                color=C.COLOR_TEXT_PRIMARY,
                size=13,
                family="'DM Sans','Segoe UI',sans-serif",
            ),
            x=0.5,
            xanchor="center",
        ),
        annotations=[
            dict(
                text=center,
                x=0.5,
                y=0.5,
                font=dict(
                    size=18,
                    color=C.COLOR_TEXT_PRIMARY,
                    family="'DM Sans','Segoe UI',sans-serif",
                ),
                showarrow=False,
            )
        ],
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.12,
            x=0.5,
            xanchor="center",
            font=dict(size=10, color=C.COLOR_TEXT_SECONDARY),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=56, b=36),
        height=280,
    )
    return fig


def build_repair_count_distribution_figure(rep: pd.DataFrame, scope_note: str = "") -> go.Figure:
    """Hollow ring: share of equipment by how many repairs in scope."""
    id_col = "equipIdNorm" if "equipIdNorm" in rep.columns else "equipId"
    if rep.empty or id_col not in rep.columns:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text="Repair count mix — no repair rows", font=dict(size=13), x=0.5, xanchor="center"),
            paper_bgcolor="rgba(0,0,0,0)",
            height=280,
        )
        return fig

    counts = rep.groupby(id_col, dropna=True).size()
    counts = counts[counts.index.astype(str).str.strip() != ""]
    if counts.empty:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text="Repair count mix — no equipment ids", font=dict(size=13), x=0.5, xanchor="center"),
            paper_bgcolor="rgba(0,0,0,0)",
            height=280,
        )
        return fig

    def _bin(n: int) -> str:
        return repair_count_bin_label(n)

    bins = counts.map(_bin).value_counts()
    order = list(REPAIR_COUNT_BIN_LABELS)
    labels = [b for b in order if b in bins.index]
    values = [int(bins[b]) for b in labels]
    _pal = [C.C_BLUE, C.C_PURPLE, C.C_GREEN, C.C_ORANGE, C.C_YELLOW]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.62,
            marker=dict(
                colors=[_pal[i % len(_pal)] for i in range(len(labels))],
                line=dict(color="white", width=2),
            ),
            textinfo="percent+label",
            textposition="outside",
            textfont=dict(size=10, color=C.COLOR_TEXT_SECONDARY),
            hovertemplate="%{label}: %{value} units (%{percent})<br><sup>Click to open Replacement table</sup><extra></extra>",
        )
    )
    total_units = sum(values)
    if scope_note:
        scope_line = f"{scope_note} · {total_units} units"
    else:
        scope_line = f"{total_units} units in scope"
    fig.update_layout(
        title=dict(
            text=f"Equipment by repair count<br><sup style='color:{C.COLOR_TEXT_MUTED}'>{scope_line} · click a slice to open Replacement table</sup>",
            font=dict(
                color=C.COLOR_TEXT_PRIMARY,
                size=13,
                family="'DM Sans','Segoe UI',sans-serif",
            ),
            x=0.5,
            xanchor="center",
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=56, b=20),
        height=280,
    )
    return fig


def build_repair_hours_by_building_figure(rep: pd.DataFrame) -> go.Figure:
    """Vertical bars: repair hours summed by building (normalized)."""
    if rep.empty or "hours" not in rep.columns:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text="Repair hours by building — no data", font=dict(size=14), x=0.02),
            paper_bgcolor="rgba(0,0,0,0)",
            height=280,
        )
        return fig

    buildings = _building_series(rep)
    tmp = rep.copy()
    tmp["_bld"] = buildings
    hours_map = tmp.groupby("_bld", dropna=False)["hours"].sum().to_dict()
    hours_map = {k: v for k, v in hours_map.items() if str(k).strip()}
    if not hours_map:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text="Repair hours by building — no location data", font=dict(size=14), x=0.02),
            paper_bgcolor="rgba(0,0,0,0)",
            height=280,
        )
        return fig

    names = sorted(hours_map.keys(), key=lambda k: (-hours_map[k], k))
    hours = [hours_map[n] for n in names]
    labels = [abbreviate_building(n) for n in names]
    _pal = [C.C_BLUE, C.C_PURPLE, C.C_GREEN, C.C_ORANGE, C.C_YELLOW, C.C_PINK, "#06b6d4", "#6366f1"]
    bar_colors = [_pal[i % len(_pal)] for i in range(len(names))]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=hours,
            customdata=names,
            marker=dict(color=bar_colors, opacity=0.85, line=dict(width=0)),
            text=[f"{h:.1f}" for h in hours],
            textposition="outside",
            textfont=dict(size=11, color=C.COLOR_TEXT_SECONDARY),
            cliponaxis=False,
            hovertemplate="%{customdata}<br>Hours: %{y:.1f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(
            text="Repair Hours by Building<br><sup style='color:#94a3b8'>Click a bar to view matching equipment</sup>",
            font=dict(
                color=C.COLOR_TEXT_PRIMARY,
                size=14,
                family="'DM Sans','Segoe UI',sans-serif",
            ),
            x=0.02,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=C.CHART_FONT,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            tickangle=-30,
            tickfont=dict(color=C.COLOR_TEXT_SECONDARY, size=10),
        ),
        yaxis=dict(
            gridcolor=C.COLOR_BORDER,
            zeroline=False,
            showline=False,
            title=dict(text="Hours", font=dict(size=11, color=C.COLOR_TEXT_MUTED)),
        ),
        margin=dict(l=10, r=24, t=56, b=72),
        bargap=0.35,
        height=300,
    )
    return fig


def build_hidden_chart_placeholder() -> go.Figure:
    """Minimal figure for a graph slot hidden via layout style."""
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=280,
    )
    return fig


def build_repair_hours_figure(rep: pd.DataFrame) -> go.Figure:
    hours_map = {}
    use_category = "equipCategory" in rep.columns
    for _, row in rep.iterrows():
        if use_category:
            eq = str(row.get("equipCategory") or "Other")
        else:
            eq = equipment_chart_class(str(row["equipment"]))
        hours_map[eq] = hours_map.get(eq, 0) + row["hours"]

    rank = chart_category_rank(hours_map.keys())
    eq_names = sorted(
        hours_map.keys(),
        key=lambda k: (rank.get(k, len(rank)), -hours_map[k]),
    )
    eq_hours = [hours_map[k] for k in eq_names]
    _pal = [
        C.C_BLUE,
        C.C_PURPLE,
        C.C_GREEN,
        C.C_ORANGE,
        C.C_YELLOW,
        C.C_PINK,
        "#06b6d4",
        "#6366f1",
        "#14b8a6",
        "#eab308",
    ]
    bar_colors = [_pal[i % len(_pal)] for i in range(len(eq_names))]

    fig = go.Figure(
        go.Bar(
            x=eq_hours,
            y=eq_names,
            orientation="h",
            marker=dict(color=bar_colors, opacity=0.85, line=dict(width=0)),
            text=[f"{h:.1f} hrs" for h in eq_hours],
            textposition="outside",
            textfont=dict(size=12, color=C.COLOR_TEXT_SECONDARY),
        )
    )
    fig.update_layout(
        title=dict(
            text="Repair Hours by Equipment<br><sup style='color:#94a3b8'>Click a bar to view matching equipment</sup>",
            font=dict(
                color=C.COLOR_TEXT_PRIMARY,
                size=14,
                family="'DM Sans','Segoe UI',sans-serif",
            ),
            x=0.02,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=C.CHART_FONT,
        xaxis=dict(
            gridcolor=C.COLOR_BORDER,
            tickcolor=C.COLOR_TEXT_MUTED,
            title=dict(text="Hours", font=dict(size=11, color=C.COLOR_TEXT_MUTED)),
            zeroline=False,
            showline=False,
        ),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", tickcolor=C.COLOR_TEXT_MUTED, showline=False),
        margin=dict(l=10, r=48, t=48, b=28),
        bargap=0.35,
    )
    return fig


def build_request_calendar_figure(month_key: str, req: pd.DataFrame, week_starts_on: str) -> go.Figure:
    period = pd.Period(month_key)
    year, mo = period.year, period.month
    first_wd = calendar.monthrange(year, mo)[0]
    monday_first = str(week_starts_on).lower() == "monday"
    first_col = first_wd if monday_first else (first_wd + 1) % 7
    days_in_mo = calendar.monthrange(year, mo)[1]

    count_by_day = {}
    if not req.empty and "Request Date" in req.columns:
        for dt in req["Request Date"].dropna():
            d = dt.day
            count_by_day[d] = count_by_day.get(d, 0) + 1

    max_count = max(count_by_day.values(), default=1)

    month_key = str(period)
    rows, cols, texts, colors, customdata = [], [], [], [], []
    col, row_i = first_col, 0
    for day in range(1, days_in_mo + 1):
        rows.append(row_i)
        cols.append(col)
        cnt = count_by_day.get(day, 0)
        texts.append(str(day))
        customdata.append([month_key, day, cnt])
        intensity = cnt / max_count if cnt else 0
        if cnt == 0:
            colors.append("#f1f5f9")
        elif intensity < 0.25:
            colors.append("#bfdbfe")
        elif intensity < 0.5:
            colors.append("#93c5fd")
        elif intensity < 0.75:
            colors.append("#60a5fa")
        else:
            colors.append(C.C_BLUE)
        col += 1
        if col > 6:
            col = 0
            row_i += 1

    max_row = max(rows, default=0)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=cols,
            y=[max_row - r for r in rows],
            mode="markers+text",
            marker=dict(
                size=32,
                color=colors,
                symbol="square",
                line=dict(color="#e2e8f0", width=1.5),
            ),
            text=texts,
            textposition="middle center",
            textfont=dict(
                color=C.COLOR_TEXT_PRIMARY,
                size=11,
                family="'DM Sans','Segoe UI',sans-serif",
            ),
            customdata=customdata,
            hovertemplate="%{text} — %{customdata[2]} request(s)<br><sup>Click to open roster</sup><extra></extra>",
        )
    )
    day_names = (
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        if monday_first
        else ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    )
    fig.update_layout(
        title=dict(
            text=f"Request Volume — {period.strftime('%B %Y')}<br><sup style='color:#94a3b8'>Click a day to open Request roster</sup>",
            font=dict(
                color=C.COLOR_TEXT_PRIMARY,
                size=14,
                family="'DM Sans','Segoe UI',sans-serif",
            ),
            x=0.02,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=C.CHART_FONT,
        xaxis=dict(
            tickvals=list(range(7)),
            ticktext=day_names,
            showgrid=False,
            zeroline=False,
            tickfont=dict(color=C.COLOR_TEXT_SECONDARY, size=11),
            showline=False,
        ),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, showline=False),
        margin=dict(l=10, r=10, t=45, b=10),
        showlegend=False,
    )
    return fig


def build_request_volume_by_month_figure(req: pd.DataFrame) -> go.Figure:
    """Aggregate-view replacement for the per-month calendar: one bar per month."""
    if req.empty or "month_key" not in req.columns:
        fig = go.Figure()
        fig.update_layout(
            title=dict(
                text="Request Volume — no requests loaded",
                font=dict(size=14, color=C.COLOR_TEXT_PRIMARY),
                x=0.02,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=C.CHART_FONT,
            margin=dict(l=10, r=10, t=45, b=30),
        )
        return fig

    counts = (
        req.loc[req["month_key"].notna() & (req["month_key"].astype(str) != "NaT"), "month_key"]
        .value_counts()
        .sort_index()
    )
    months = list(counts.index)
    labels = [pd.Period(m).strftime("%b %Y") for m in months]
    values = [int(v) for v in counts.values]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            customdata=list(months),
            marker=dict(color=C.C_BLUE, opacity=0.85, line=dict(width=0)),
            text=[str(v) for v in values],
            textposition="outside",
            textfont=dict(size=12, color=C.COLOR_TEXT_SECONDARY),
            cliponaxis=False,
            hovertemplate="%{x}: %{y} requests<br><sup>Click to open roster</sup><extra></extra>",
        )
    )
    total = sum(values)
    fig.update_layout(
        title=dict(
            text=f"Request Volume by Month  ·  {total} total<br><sup style='color:#94a3b8'>Click a bar to open Request roster</sup>",
            font=dict(
                color=C.COLOR_TEXT_PRIMARY,
                size=14,
                family="'DM Sans','Segoe UI',sans-serif",
            ),
            x=0.02,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=C.CHART_FONT,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            tickfont=dict(color=C.COLOR_TEXT_SECONDARY, size=11),
        ),
        yaxis=dict(
            gridcolor=C.COLOR_BORDER,
            zeroline=False,
            showline=False,
            title=dict(text="Requests", font=dict(size=11, color=C.COLOR_TEXT_MUTED)),
        ),
        margin=dict(l=10, r=20, t=45, b=30),
        bargap=0.4,
        showlegend=False,
    )
    return fig


def build_overview_footer(month_key: str, rep: pd.DataFrame, svc: pd.DataFrame) -> str:
    if C.is_all_months(month_key):
        scope = "all months"
    else:
        scope = pd.Period(month_key).strftime("%B %Y")
    return (
        f"Data reflects {scope}  ·  {len(rep)} repair records  ·  "
        f"{len(svc)} service orders"
    )


def build_completion_rate_figure(svc: pd.DataFrame) -> go.Figure:
    total_completed = (svc["Status"].str.strip().str.lower() == "completed").sum()
    total_scheduled = (svc["Status"].str.strip().str.lower() == "scheduled").sum()
    total_svc = total_completed + total_scheduled
    rate_val = (total_completed / total_svc * 100) if total_svc > 0 else 0
    gauge_color = C.C_GREEN if rate_val >= 80 else C.C_YELLOW if rate_val >= 50 else "#ef4444"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=rate_val,
            number={
                "suffix": "%",
                "font": {
                    "size": 32,
                    "color": C.COLOR_TEXT_PRIMARY,
                    "family": "'DM Sans','Segoe UI',sans-serif",
                },
            },
            title={
                "text": "Completion Rate",
                "font": {
                    "size": 13,
                    "color": C.COLOR_TEXT_SECONDARY,
                    "family": "'DM Sans','Segoe UI',sans-serif",
                },
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 1,
                    "tickcolor": C.COLOR_TEXT_MUTED,
                    "tickfont": {"size": 10, "color": C.COLOR_TEXT_MUTED},
                },
                "bar": {"color": gauge_color, "thickness": 0.25},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": "#fef2f2"},
                    {"range": [50, 80], "color": "#fffbeb"},
                    {"range": [80, 100], "color": "#f0fdf4"},
                ],
                "threshold": {
                    "line": {"color": gauge_color, "width": 3},
                    "thickness": 0.75,
                    "value": rate_val,
                },
            },
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=50, b=40),
        height=280,
    )
    return fig


def build_avg_repair_hours_figure(rep: pd.DataFrame) -> go.Figure:
    total_hours = rep["hours"].sum()
    repair_count = len(rep)
    avg_val = (total_hours / repair_count) if repair_count > 0 else 0
    max_gauge = max(avg_val * 2, 4)
    avg_color = (
        C.C_BLUE if avg_val < max_gauge * 0.5 else C.C_ORANGE if avg_val < max_gauge * 0.75 else "#ef4444"
    )

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=avg_val,
            number={
                "suffix": " hrs",
                "valueformat": ".1f",
                "font": {
                    "size": 32,
                    "color": C.COLOR_TEXT_PRIMARY,
                    "family": "'DM Sans','Segoe UI',sans-serif",
                },
            },
            title={
                "text": "Avg Repair Hours",
                "font": {
                    "size": 13,
                    "color": C.COLOR_TEXT_SECONDARY,
                    "family": "'DM Sans','Segoe UI',sans-serif",
                },
            },
            gauge={
                "axis": {
                    "range": [0, max_gauge],
                    "tickwidth": 1,
                    "tickcolor": C.COLOR_TEXT_MUTED,
                    "tickfont": {"size": 10, "color": C.COLOR_TEXT_MUTED},
                },
                "bar": {"color": avg_color, "thickness": 0.25},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, max_gauge * 0.5], "color": "#f0fdf4"},
                    {"range": [max_gauge * 0.5, max_gauge * 0.75], "color": "#fffbeb"},
                    {"range": [max_gauge * 0.75, max_gauge], "color": "#fef2f2"},
                ],
                "threshold": {
                    "line": {"color": avg_color, "width": 3},
                    "thickness": 0.75,
                    "value": avg_val,
                },
            },
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=50, b=40),
        height=280,
    )
    return fig


def build_staff_capacity_figure(
    rep: pd.DataFrame,
    staff_count: int,
    hours_per_day: float,
    work_days: int,
) -> go.Figure:
    capacity = float(staff_count) * float(hours_per_day) * float(work_days)
    used = float(rep["hours"].sum())
    remaining = max(capacity - used, 0.0)
    util_pct = used / capacity * 100 if capacity > 0 else 0

    util_color = C.C_GREEN if util_pct < 50 else C.C_YELLOW if util_pct < 80 else "#ef4444"

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[used],
            y=["Capacity"],
            orientation="h",
            name="Used on Repairs",
            marker=dict(color=util_color, opacity=0.9, line=dict(width=0)),
            text=[f"{used:.1f} hrs ({util_pct:.1f}%)"],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(size=12, color="white", family="'DM Sans','Segoe UI',sans-serif"),
        )
    )
    fig.add_trace(
        go.Bar(
            x=[remaining],
            y=["Capacity"],
            orientation="h",
            name="Available",
            marker=dict(color=C.COLOR_BORDER, opacity=0.6, line=dict(width=0)),
            text=[f"{remaining:.0f} hrs remaining"],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(size=12, color=C.COLOR_TEXT_MUTED, family="'DM Sans','Segoe UI',sans-serif"),
        )
    )
    cap_int = int(capacity) if capacity == int(capacity) else capacity
    fig.update_layout(
        title=dict(
            text=(
                f"Staff Capacity Utilization  ·  {staff_count} staff × {hours_per_day} hrs × "
                f"{work_days} days = {cap_int} hrs"
            ),
            font=dict(
                color=C.COLOR_TEXT_PRIMARY,
                size=13,
                family="'DM Sans','Segoe UI',sans-serif",
            ),
            x=0.02,
        ),
        barmode="stack",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=C.CHART_FONT,
        xaxis=dict(
            range=[0, capacity] if capacity > 0 else [0, 1],
            gridcolor=C.COLOR_BORDER,
            zeroline=False,
            showline=False,
            title=dict(text="Hours", font=dict(size=11, color=C.COLOR_TEXT_MUTED)),
            tickfont=dict(size=11, color=C.COLOR_TEXT_MUTED),
        ),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, showline=False),
        legend=dict(orientation="h", x=0.02, y=-0.15, font=dict(size=11, color=C.COLOR_TEXT_SECONDARY)),
        margin=dict(l=40, r=20, t=50, b=40),
        height=280,
    )
    return fig


def build_turnaround_figure(done_svc: pd.DataFrame) -> go.Figure:
    if done_svc.empty:
        fig = go.Figure()
        fig.update_layout(
            title=dict(
                text="Avg turnaround — no completed service rows with dates",
                font=dict(size=14),
                x=0.02,
                xanchor="left",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=C.CHART_FONT,
            margin=dict(l=40, r=20, t=50, b=40),
            height=280,
        )
        return fig

    avg_turn = done_svc.groupby("equipCategory", as_index=False)["turnaround_bd"].mean()
    # Filter to only show categories that actually have data
    avg_turn = avg_turn[avg_turn["turnaround_bd"] > 0]
    
    turn_rank = chart_category_rank(avg_turn["equipCategory"])
    avg_turn["_ord"] = avg_turn["equipCategory"].map(turn_rank)
    avg_turn = avg_turn.sort_values(
        ["_ord", "turnaround_bd"],
        ascending=[True, True],
        na_position="last",
    ).drop(columns=["_ord"])

    if avg_turn.empty:
        fig = go.Figure()
        fig.update_layout(
            title=dict(
                text="Avg turnaround — no completed service rows with dates",
                font=dict(size=14),
                x=0.02,
                xanchor="left",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=C.CHART_FONT,
            margin=dict(l=40, r=20, t=50, b=40),
            height=280,
        )
        return fig

    max_val = avg_turn["turnaround_bd"].max()
    xaxis_max = max(10, max_val * 1.25)

    fig = go.Figure(
        go.Bar(
            x=avg_turn["turnaround_bd"],
            y=avg_turn["equipCategory"],
            orientation="h",
            marker=dict(color=C.C_PURPLE, opacity=0.85, line=dict(width=0)),
            text=[f"{v:.1f} d" for v in avg_turn["turnaround_bd"]],
            textposition="outside",
            textfont=dict(size=12, color=C.COLOR_TEXT_SECONDARY),
            cliponaxis=False,
        )
    )
    
    fig.update_layout(
        title=dict(
            text="Avg turnaround by equipment type (schedule → completion)<br><sup style='color:#94a3b8'>Click a bar to open Order roster</sup>",
            font=dict(
                color=C.COLOR_TEXT_PRIMARY,
                size=14,
                family="'DM Sans','Segoe UI',sans-serif",
            ),
            x=0.02,
            xanchor="left",
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=C.CHART_FONT,
        xaxis=dict(
            gridcolor=C.COLOR_BORDER,
            title=dict(text="Days", font=dict(size=11, color=C.COLOR_TEXT_MUTED)),
            zeroline=False,
            showline=False,
            range=[0, xaxis_max],
            automargin=True,
        ),
        yaxis=dict(
            gridcolor="rgba(0,0,0,0)", 
            showline=False,
            automargin=True,
        ),
        margin=dict(l=10, r=60, t=52, b=30),
        bargap=0.35,
        height=320,
    )
    return fig


def build_availability_figure(
    done_svc: pd.DataFrame,
    df_equip: pd.DataFrame,
    base_avail_days: float,
) -> go.Figure:
    downtime_by_id: dict[str, float] = {}
    if not done_svc.empty and "turnaround_bd" in done_svc.columns:
        summed = done_svc.groupby("equipIdNorm", dropna=True)["turnaround_bd"].sum()
        downtime_by_id = {str(k): float(v) for k, v in summed.items() if str(k)}

    cat_set = set()
    if not done_svc.empty:
        cat_set |= set(done_svc["equipCategory"].dropna().unique())
    if not df_equip.empty and "category" in df_equip.columns:
        cat_set |= set(df_equip["category"].dropna().unique())

    base = float(base_avail_days)
    avail_by_cat: dict[str, float] = {}
    for cat in cat_set:
        ids_list = set()
        if not df_equip.empty and "category" in df_equip.columns:
            ids_list = set(
                df_equip.loc[df_equip["category"] == cat, "equipIdNorm"].dropna().astype(str).unique()
            )
            ids_list = {i for i in ids_list if i}
        ids_svc = set()
        if not done_svc.empty:
            ids_svc = set(
                done_svc.loc[done_svc["equipCategory"] == cat, "equipIdNorm"].dropna().astype(str).unique()
            )
            ids_svc = {i for i in ids_svc if i}
        all_ids = ids_list | ids_svc
        if not all_ids:
            continue
        terms = []
        for eid in all_ids:
            t = min(downtime_by_id.get(eid, 0.0), base)
            terms.append((base - t) / base)
        pct = (sum(terms) / len(all_ids)) * 100.0
        avail_by_cat[cat] = pct

    avail_rank = chart_category_rank(avail_by_cat.keys())
    avail_cats = sorted(avail_by_cat.keys(), key=lambda c: avail_rank.get(c, len(avail_rank)))
    avail_pcts = [avail_by_cat[c] for c in avail_cats]

    if not avail_cats:
        fig = go.Figure()
        fig.update_layout(
            title=dict(
                text="Availability — need service rows and/or equipment summary",
                font=dict(size=14),
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=C.CHART_FONT,
            margin=dict(l=40, r=20, t=50, b=40),
            height=280,
        )
        return fig

    y_max = max(avail_pcts) if avail_pcts else 100.0
    y_axis_hi = min(130.0, max(122.0, y_max * 1.22))

    fig = go.Figure(
        go.Bar(
            x=avail_cats,
            y=avail_pcts,
            marker=dict(color=C.C_GREEN, opacity=0.88, line=dict(width=0)),
            text=[f"{p:.1f}%" for p in avail_pcts],
            textposition="outside",
            textfont=dict(size=13, color=C.COLOR_TEXT_PRIMARY),
            cliponaxis=False,
        )
    )
    fig.update_layout(
        title=dict(
            text="Availability by equipment type<br><sup style='color:#94a3b8'>Click a bar to open Order roster</sup>",
            font=dict(
                color=C.COLOR_TEXT_PRIMARY,
                size=14,
                family="'DM Sans','Segoe UI',sans-serif",
            ),
            x=0.02,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=C.CHART_FONT,
        yaxis=dict(
            range=[0, y_axis_hi],
            gridcolor=C.COLOR_BORDER,
            title=dict(text="Availability %", font=dict(size=11, color=C.COLOR_TEXT_MUTED)),
            zeroline=False,
            showline=False,
        ),
        xaxis=dict(showline=False, tickangle=-25, automargin=True),
        margin=dict(l=8, r=12, t=44, b=88),
        height=320,
    )
    return fig

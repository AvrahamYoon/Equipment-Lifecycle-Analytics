"""KPIs, charts, and footer for the overview page (no replacement table)."""

import calendar

import pandas as pd
import plotly.graph_objects as go
from dash import html

from dashboard import constants as C
from dashboard.calendar_util import business_days_inclusive
from dashboard.taxonomy import equipment_chart_class


def build_overview(
    month_key: str,
    req: pd.DataFrame,
    svc: pd.DataFrame,
    rep: pd.DataFrame,
    df_equip: pd.DataFrame,
):
    """Returns (kpis_children, hours_fig, cal_fig, completion_fig, avghours_fig, staff_fig, turnaround_fig, avail_fig, footer)."""
    total_req = len(req)
    total_completed = (svc["Status"].str.strip().str.lower() == "completed").sum()
    total_scheduled = (svc["Status"].str.strip().str.lower() == "scheduled").sum()
    total_parts = rep["parts"].sum()
    total_labor = rep["labor"].sum()
    total_repair = rep["total"].sum()

    total_svc = total_completed + total_scheduled
    total_hours = rep["hours"].sum()
    repair_count = len(rep)

    def kpi_card(label, value, icon, accent):
        return html.Div(
            [
                html.Div(
                    [
                        html.Div(icon, style={"fontSize": 20}),
                        html.Div(
                            style={
                                "width": 6,
                                "height": 6,
                                "borderRadius": "50%",
                                "background": accent,
                                "marginLeft": "auto",
                            }
                        ),
                    ],
                    style={"display": "flex", "alignItems": "center", "marginBottom": 12},
                ),
                html.Div(
                    str(value),
                    style={
                        "fontSize": 26,
                        "fontWeight": 800,
                        "color": C.COLOR_TEXT_PRIMARY,
                        "lineHeight": 1,
                    },
                ),
                html.Div(
                    label,
                    style={
                        "fontSize": 11,
                        "color": C.COLOR_TEXT_SECONDARY,
                        "fontWeight": 600,
                        "textTransform": "uppercase",
                        "letterSpacing": "0.05em",
                        "marginTop": 6,
                    },
                ),
                html.Div(
                    style={
                        "height": 3,
                        "borderRadius": 2,
                        "background": accent,
                        "marginTop": 14,
                        "opacity": 0.7,
                    }
                ),
            ],
            style={
                **C.CARD_STYLE,
                "padding": "18px 18px 14px",
                "minWidth": 140,
                "flex": "1",
                "borderTop": f"3px solid {accent}",
            },
        )

    kpis = [
        kpi_card("Total Requests", total_req, "📋", C.C_BLUE),
        kpi_card("Completed / Total", f"{total_completed}/{total_svc}", "✅", C.C_GREEN),
        kpi_card("Scheduled", total_scheduled, "📅", C.C_PURPLE),
        kpi_card("Total Repair Cost", f"${total_repair:,.2f}", "💰", C.C_ORANGE),
        kpi_card("Parts Cost", f"${total_parts:,.2f}", "⚙️", C.C_YELLOW),
        kpi_card("Labor Cost", f"${total_labor:,.2f}", "👤", C.C_PINK),
    ]

    # Hours by equipment class
    hours_map = {}
    for _, row in rep.iterrows():
        eq = equipment_chart_class(str(row["equipment"]))
        hours_map[eq] = hours_map.get(eq, 0) + row["hours"]

    eq_names = sorted(
        hours_map.keys(),
        key=lambda k: (C.CHART_CLASS_RANK.get(k, len(C.CHART_CLASS_ORDER)), -hours_map[k]),
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

    hours_fig = go.Figure(
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
    hours_fig.update_layout(
        title=dict(
            text="Repair Hours by Equipment",
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
        margin=dict(l=10, r=40, t=45, b=25),
        bargap=0.35,
    )

    # Calendar
    period = pd.Period(month_key)
    year, mo = period.year, period.month
    first_wd = calendar.monthrange(year, mo)[0]
    first_col = (first_wd + 1) % 7
    days_in_mo = calendar.monthrange(year, mo)[1]

    count_by_day = {}
    if not req.empty and "Request Date" in req.columns:
        for dt in req["Request Date"].dropna():
            d = dt.day
            count_by_day[d] = count_by_day.get(d, 0) + 1

    max_count = max(count_by_day.values(), default=1)

    rows, cols, texts, colors, customdata = [], [], [], [], []
    col, row_i = first_col, 0
    for day in range(1, days_in_mo + 1):
        rows.append(row_i)
        cols.append(col)
        cnt = count_by_day.get(day, 0)
        texts.append(str(day))
        customdata.append(cnt)
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

    cal_fig = go.Figure()
    cal_fig.add_trace(
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
            hovertemplate="%{text} — %{customdata} request(s)<extra></extra>",
        )
    )
    day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    cal_fig.update_layout(
        title=dict(
            text=f"Request Volume — {period.strftime('%B %Y')}",
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

    footer = (
        f"Data reflects {period.strftime('%B %Y')}  ·  {len(rep)} repair records  ·  "
        f"{len(svc)} service orders"
    )

    # Gauges
    rate_val = (total_completed / total_svc * 100) if total_svc > 0 else 0
    gauge_color = C.C_GREEN if rate_val >= 80 else C.C_YELLOW if rate_val >= 50 else "#ef4444"
    completion_fig = go.Figure(
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
    completion_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=10),
        height=260,
    )

    avg_val = (total_hours / repair_count) if repair_count > 0 else 0
    max_gauge = max(avg_val * 2, 4)
    avg_color = (
        C.C_BLUE if avg_val < max_gauge * 0.5 else C.C_ORANGE if avg_val < max_gauge * 0.75 else "#ef4444"
    )
    avghours_fig = go.Figure(
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
    avghours_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=10),
        height=260,
    )

    staff_count = 4
    hours_per_day = 4
    work_days = 20
    capacity = staff_count * hours_per_day * work_days
    used = rep["hours"].sum()
    remaining = max(capacity - used, 0)
    util_pct = used / capacity * 100 if capacity > 0 else 0

    util_color = C.C_GREEN if util_pct < 50 else C.C_YELLOW if util_pct < 80 else "#ef4444"

    staff_fig = go.Figure()
    staff_fig.add_trace(
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
    staff_fig.add_trace(
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
    staff_fig.update_layout(
        title=dict(
            text=(
                f"Staff Capacity Utilization  ·  {staff_count} staff × {hours_per_day} hrs × "
                f"{work_days} days = {capacity} hrs"
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
            range=[0, capacity],
            gridcolor=C.COLOR_BORDER,
            zeroline=False,
            showline=False,
            title=dict(text="Hours", font=dict(size=11, color=C.COLOR_TEXT_MUTED)),
            tickfont=dict(size=11, color=C.COLOR_TEXT_MUTED),
        ),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, showline=False),
        legend=dict(orientation="h", x=0.02, y=-0.15, font=dict(size=11, color=C.COLOR_TEXT_SECONDARY)),
        margin=dict(l=10, r=20, t=50, b=40),
        height=260,
    )

    # Turnaround + availability
    sc = svc.copy()
    sc["status_l"] = sc["Status"].astype(str).str.strip().str.lower()
    done_svc = sc[
        (sc["status_l"] == "completed")
        & sc["Sched. Date"].notna()
        & sc["Completed Date"].notna()
        & (sc["Completed Date"] >= sc["Sched. Date"])
    ]
    if not done_svc.empty:
        done_svc = done_svc.assign(
            turnaround_bd=done_svc.apply(
                lambda r: business_days_inclusive(r["Sched. Date"], r["Completed Date"]),
                axis=1,
            )
        )
        done_svc = done_svc[done_svc["turnaround_bd"].notna()]
        avg_turn = done_svc.groupby("equipCategory", as_index=False)["turnaround_bd"].mean()
        avg_turn["_ord"] = avg_turn["equipCategory"].map(C.CHART_CLASS_RANK)
        avg_turn = avg_turn.sort_values(
            ["_ord", "turnaround_bd"],
            ascending=[True, True],
            na_position="last",
        ).drop(columns=["_ord"])
    else:
        avg_turn = pd.DataFrame(columns=["equipCategory", "turnaround_bd"])

    if not avg_turn.empty:
        turnaround_fig = go.Figure(
            go.Bar(
                x=avg_turn["turnaround_bd"],
                y=avg_turn["equipCategory"],
                orientation="h",
                marker=dict(color=C.C_PURPLE, opacity=0.85, line=dict(width=0)),
                text=[f"{v:.1f} d" for v in avg_turn["turnaround_bd"]],
                textposition="outside",
                textfont=dict(size=12, color=C.COLOR_TEXT_SECONDARY),
            )
        )
        turnaround_fig.update_layout(
            title=dict(
                text=(
                    "Avg turnaround by equipment class (schedule → completion)<br>"
                    "<sup>Classes from name keywords (same buckets as hours & availability). "
                    "Weekdays only; US federal holidays not counted</sup>"
                ),
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
                title=dict(text="Days", font=dict(size=11, color=C.COLOR_TEXT_MUTED)),
                zeroline=False,
                showline=False,
            ),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", showline=False),
            margin=dict(l=10, r=40, t=55, b=25),
            bargap=0.35,
        )
    else:
        turnaround_fig = go.Figure()
        turnaround_fig.update_layout(
            title=dict(text="Avg turnaround — no completed service rows with dates", font=dict(size=14)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=C.CHART_FONT,
            margin=dict(l=20, r=20, t=50, b=20),
            height=300,
        )

    downtime_by_id: dict[str, float] = {}
    if not done_svc.empty and "turnaround_bd" in done_svc.columns:
        summed = done_svc.groupby("equipIdNorm", dropna=True)["turnaround_bd"].sum()
        downtime_by_id = {str(k): float(v) for k, v in summed.items() if str(k)}

    cat_set = set()
    if not done_svc.empty:
        cat_set |= set(done_svc["equipCategory"].dropna().unique())
    if not df_equip.empty and "category" in df_equip.columns:
        cat_set |= set(df_equip["category"].dropna().unique())

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
            t = min(downtime_by_id.get(eid, 0.0), float(C.BASE_AVAIL_DAYS))
            terms.append((C.BASE_AVAIL_DAYS - t) / C.BASE_AVAIL_DAYS)
        pct = (sum(terms) / len(all_ids)) * 100.0
        avail_by_cat[cat] = pct

    avail_cats = [c for c in C.CHART_CLASS_ORDER if c in avail_by_cat]
    avail_pcts = [avail_by_cat[c] for c in avail_cats]

    if avail_cats:
        avail_fig = go.Figure(
            go.Bar(
                x=avail_cats,
                y=avail_pcts,
                marker=dict(color=C.C_GREEN, opacity=0.88, line=dict(width=0)),
                text=[f"{p:.1f}%" for p in avail_pcts],
                textposition="outside",
                textfont=dict(size=12, color=C.COLOR_TEXT_SECONDARY),
            )
        )
        avail_fig.update_layout(
            title=dict(
                text=(
                    "Availability by equipment group<br>"
                    "<sup>Per device: (311 − days down) ÷ 311. "
                    "Days down = sum of weekday schedule→completion days this month (cap 311). "
                    "Bar = mean over devices in group × 100%</sup>"
                ),
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
                range=[0, 105],
                gridcolor=C.COLOR_BORDER,
                title=dict(text="Availability %", font=dict(size=11, color=C.COLOR_TEXT_MUTED)),
                zeroline=False,
            ),
            xaxis=dict(showline=False, tickangle=-25),
            margin=dict(l=10, r=20, t=60, b=80),
            height=300,
        )
    else:
        avail_fig = go.Figure()
        avail_fig.update_layout(
            title=dict(
                text="Availability — need service rows and/or equipment summary",
                font=dict(size=14),
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=C.CHART_FONT,
            margin=dict(l=20, r=20, t=50, b=20),
            height=300,
        )

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

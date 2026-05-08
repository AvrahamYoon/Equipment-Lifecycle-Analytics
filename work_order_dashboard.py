"""
Work Order Dashboard — Facilities Mnagement Services
============================================
Run:  pip install dash pandas plotly
      python work_order_dashboard.py
Then open http://127.0.0.1:8050 in your browser.
"""

import math
import calendar
import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, dash_table

# ── Data ──────────────────────────────────────────────────────────────────────
REQUESTS_CSV  = "Work_Orders_April_2026_Request.csv"
SERVICE_CSV   = "April_Service_Orders_with_Prices.csv"
REPAIRS_CSV   = "April_Repair_List_All_Work_Orders.csv"


def load_requests(path: str) -> pd.DataFrame:
    raw = pd.read_csv(path, header=None)
    raw.columns = raw.iloc[1]
    df = raw.iloc[2:].reset_index(drop=True)
    df = df[df["Work Order #"].notna() & ~df["Work Order #"].str.startswith("Total")]
    df["Request Date"] = pd.to_datetime(df["Request Date"], format="%m/%d/%Y", errors="coerce")
    df["month_key"] = df["Request Date"].dt.to_period("M").astype(str)
    return df


def load_service(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Sched. Date"]    = pd.to_datetime(df["Sched. Date"],    errors="coerce")
    df["Completed Date"] = pd.to_datetime(df["Completed Date"], errors="coerce")
    df["month_key"] = df["Sched. Date"].dt.to_period("M").astype(str)
    return df


def load_repairs(path: str) -> pd.DataFrame:
    raw = pd.read_csv(path, skiprows=1, header=None)
    raw.columns = raw.iloc[0]
    df = raw.iloc[1:].reset_index(drop=True)
    df = df[df["#"].apply(lambda x: str(x).strip().isdigit())]
    df.columns = [c.replace("\n", " ").strip() for c in df.columns]
    df = df.rename(columns={
        "Completed Date":    "date",
        "Equipment Name":    "equipment",
        "Equipment ID":      "equipId",
        "Location":          "location",
        "# of Repairs":      "repairs",
        "Repair Person-Hrs": "hours",
        "Parts Cost $":      "parts",
        "Total Labor $":     "labor",
        "Est. Total $":      "total",
    })
    for col in ["repairs","hours","parts","labor","total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["month_key"] = df["date"].dt.to_period("M").astype(str)

    PRICE_MAP = {
        "versamatic": 1035,
        "lindhaus":    850,
        "kaivac":     5700,
        "big vacuum": 1050,
    }
    def get_price(name):
        n = str(name).lower()
        for k, v in PRICE_MAP.items():
            if k in n:
                return v
        return 1035
    df["newPrice"] = df["equipment"].apply(get_price)
    return df


# ── Load data ─────────────────────────────────────────────────────────────────
try:
    df_req     = load_requests(REQUESTS_CSV)
    df_service = load_service(SERVICE_CSV)
    df_repairs = load_repairs(REPAIRS_CSV)
except FileNotFoundError as e:
    raise SystemExit(f"CSV not found: {e}\nMake sure the CSV files are in the same folder as this script.")

all_months = sorted(
    m for m in (set(df_req["month_key"]) | set(df_service["month_key"]) | set(df_repairs["month_key"]))
    if pd.notna(m) and str(m) != "NaT"
)
MONTH_OPTIONS = [{"label": pd.Period(m).strftime("%B %Y"), "value": m} for m in all_months]


# ── Helper ────────────────────────────────────────────────────────────────────
def replace_status(labor, parts, new_price):
    combined = labor + parts
    if combined * 0.80 >= new_price:
        return "Replace"
    if combined * 0.60 >= new_price:
        return "Monitor"
    return "Good"


# ── Theme tokens ──────────────────────────────────────────────────────────────
BG_PAGE    = "#f0f4f8"
BG_CARD    = "#ffffff"
BG_HEADER  = "#ffffff"
COLOR_BORDER = "#e2e8f0"
COLOR_TEXT_PRIMARY   = "#1e293b"
COLOR_TEXT_SECONDARY = "#64748b"
COLOR_TEXT_MUTED     = "#94a3b8"

# Accent palette
C_BLUE   = "#3b82f6"
C_GREEN  = "#10b981"
C_PURPLE = "#8b5cf6"
C_ORANGE = "#f97316"
C_YELLOW = "#f59e0b"
C_PINK   = "#ec4899"

CHART_FONT = dict(family="'DM Sans','Segoe UI',sans-serif", color=COLOR_TEXT_SECONDARY, size=12)

CARD_STYLE = {
    "background": BG_CARD,
    "border": f"1px solid {COLOR_BORDER}",
    "borderRadius": 14,
    "boxShadow": "0 1px 4px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)",
}

# ── App ───────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__)
app.title = "Work Order Dashboard"

app.layout = html.Div([

    # ── Header ────────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Span("Facilities Mnagement Services", style={
                "fontSize": 10, "letterSpacing": "0.18em", "color": C_BLUE,
                "fontWeight": 700, "textTransform": "uppercase",
            }),
            html.H1("Work Order Dashboard", style={
                "margin": "4px 0 2px", "fontSize": 24,
                "color": COLOR_TEXT_PRIMARY, "fontWeight": 800, "lineHeight": 1.2,
            }),
            html.Span("Custodial Equipment Repair & Service Tracker", style={
                "fontSize": 13, "color": COLOR_TEXT_SECONDARY,
            }),
        ]),
        html.Div([
            html.Label("Month", style={
                "fontSize": 11, "fontWeight": 600, "color": COLOR_TEXT_MUTED,
                "letterSpacing": "0.08em", "textTransform": "uppercase",
                "marginBottom": 5, "display": "block",
            }),
            dcc.Dropdown(
                id="month-select",
                options=MONTH_OPTIONS,
                value=all_months[0],
                clearable=False,
                style={"width": 180, "fontFamily": "inherit", "fontSize": 13},
            ),
        ]),
    ], style={
        "display": "flex", "justifyContent": "space-between", "alignItems": "center",
        "flexWrap": "wrap", "gap": 16,
        "background": BG_HEADER,
        "borderBottom": f"1px solid {COLOR_BORDER}",
        "padding": "20px 28px",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.05)",
    }),

    # ── Body ──────────────────────────────────────────────────────────────────
    html.Div([

        # KPI Row
        html.Div(id="kpi-row", style={
            "display": "flex", "flexWrap": "wrap", "gap": 14, "marginBottom": 20,
        }),

        # Charts Row
        html.Div([
            html.Div([
                dcc.Graph(id="hours-chart", config={"displayModeBar": False, "responsive": True},
                          style={"height": 280}),
            ], style={**CARD_STYLE, "flex": "1", "minWidth": 320, "padding": "16px 8px 8px"}),

            html.Div([
                dcc.Graph(id="calendar-chart", config={"displayModeBar": False, "responsive": True},
                          style={"height": 280}),
            ], style={**CARD_STYLE, "flex": "1", "minWidth": 320, "padding": "16px 8px 8px"}),
        ], style={"display": "flex", "gap": 16, "marginBottom": 20}),

        # Gauge + Staff Row
        html.Div([
            html.Div([
                dcc.Graph(id="completion-gauge", config={"displayModeBar": False, "responsive": True},
                          style={"height": 260}),
            ], style={**CARD_STYLE, "flex": "1", "minWidth": 240, "padding": "16px 8px 8px"}),

            html.Div([
                dcc.Graph(id="avghours-gauge", config={"displayModeBar": False, "responsive": True},
                          style={"height": 260}),
            ], style={**CARD_STYLE, "flex": "1", "minWidth": 240, "padding": "16px 8px 8px"}),

            html.Div([
                dcc.Graph(id="staff-chart", config={"displayModeBar": False, "responsive": True},
                          style={"height": 260}),
            ], style={**CARD_STYLE, "flex": "2", "minWidth": 320, "padding": "16px 8px 8px"}),
        ], style={"display": "flex", "gap": 16, "marginBottom": 20}),

        # Replacement Table
        html.Div([
            html.Div([
                html.Div([
                    html.Span("🚦", style={"fontSize": 16, "marginRight": 8}),
                    html.Span("Equipment Replacement Indicator", style={
                        "fontSize": 14, "fontWeight": 700, "color": COLOR_TEXT_PRIMARY,
                    }),
                ], style={"display": "flex", "alignItems": "center", "marginBottom": 6}),
                html.Div([
                    html.Span("🔴 Replace", style={"color": "#dc2626", "fontWeight": 600, "marginRight": 16}),
                    html.Span("(Labor+Parts)×0.80 ≥ New Price", style={"color": COLOR_TEXT_MUTED, "marginRight": 24}),
                    html.Span("🟡 Monitor", style={"color": "#d97706", "fontWeight": 600, "marginRight": 16}),
                    html.Span("(Labor+Parts)×0.60 ≥ New Price", style={"color": COLOR_TEXT_MUTED, "marginRight": 24}),
                    html.Span("🟢 Good", style={"color": "#059669", "fontWeight": 600, "marginRight": 16}),
                    html.Span("Below threshold", style={"color": COLOR_TEXT_MUTED}),
                ], style={"fontSize": 12, "marginBottom": 16, "flexWrap": "wrap", "display": "flex", "gap": 4}),
            ]),
            dash_table.DataTable(
                id="replace-table",
                style_table={"overflowX": "auto", "borderRadius": 10, "overflow": "hidden"},
                style_header={
                    "backgroundColor": "#f8fafc",
                    "color": COLOR_TEXT_SECONDARY,
                    "fontWeight": "700",
                    "fontSize": 11,
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                    "borderBottom": f"2px solid {COLOR_BORDER}",
                    "padding": "10px 14px",
                    "border": "none",
                },
                style_cell={
                    "backgroundColor": BG_CARD,
                    "color": COLOR_TEXT_PRIMARY,
                    "fontSize": 13,
                    "padding": "10px 14px",
                    "border": "none",
                    "borderBottom": f"1px solid {COLOR_BORDER}",
                    "fontFamily": "'DM Sans','Segoe UI',sans-serif",
                },
                style_data_conditional=[],
            ),
        ], style={**CARD_STYLE, "padding": "20px 20px 8px", "marginBottom": 20}),

        # Footer
        html.Div(id="footer-text", style={
            "textAlign": "center", "fontSize": 11,
            "color": COLOR_TEXT_MUTED, "paddingBottom": 8,
        }),

    ], style={"padding": "24px 28px", "maxWidth": 1400, "margin": "0 auto"}),

], style={
    "minHeight": "100vh",
    "background": BG_PAGE,
    "fontFamily": "'DM Sans','Segoe UI',sans-serif",
    "color": COLOR_TEXT_PRIMARY,
})


# ── Callbacks ─────────────────────────────────────────────────────────────────
@app.callback(
    Output("kpi-row", "children"),
    Output("hours-chart", "figure"),
    Output("calendar-chart", "figure"),
    Output("completion-gauge", "figure"),
    Output("avghours-gauge", "figure"),
    Output("staff-chart", "figure"),
    Output("replace-table", "columns"),
    Output("replace-table", "data"),
    Output("replace-table", "style_data_conditional"),
    Output("footer-text", "children"),
    Input("month-select", "value"),
)
def update_all(month_key):
    req = df_req[df_req["month_key"] == month_key]
    svc = df_service[df_service["month_key"] == month_key]
    rep = df_repairs[df_repairs["month_key"] == month_key]

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total_req       = len(req)
    total_completed = (svc["Status"].str.strip().str.lower() == "completed").sum()
    total_scheduled = (svc["Status"].str.strip().str.lower() == "scheduled").sum()
    total_parts     = rep["parts"].sum()
    total_labor     = rep["labor"].sum()
    total_repair    = rep["total"].sum()

    total_svc       = total_completed + total_scheduled
    completion_rate = f"{total_completed / total_svc * 100:.0f}%" if total_svc > 0 else "N/A"
    total_hours     = rep["hours"].sum()
    repair_count    = len(rep)
    avg_hours       = f"{total_hours / repair_count:.1f} hrs" if repair_count > 0 else "N/A"

    def kpi_card(label, value, icon, accent):
        return html.Div([
            html.Div([
                html.Div(icon, style={"fontSize": 20}),
                html.Div(style={
                    "width": 6, "height": 6, "borderRadius": "50%",
                    "background": accent, "marginLeft": "auto",
                }),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": 12}),
            html.Div(str(value), style={
                "fontSize": 26, "fontWeight": 800,
                "color": COLOR_TEXT_PRIMARY, "lineHeight": 1,
            }),
            html.Div(label, style={
                "fontSize": 11, "color": COLOR_TEXT_SECONDARY,
                "fontWeight": 600, "textTransform": "uppercase",
                "letterSpacing": "0.05em", "marginTop": 6,
            }),
            html.Div(style={
                "height": 3, "borderRadius": 2,
                "background": accent, "marginTop": 14, "opacity": 0.7,
            }),
        ], style={
            **CARD_STYLE,
            "padding": "18px 18px 14px",
            "minWidth": 140, "flex": "1",
            "borderTop": f"3px solid {accent}",
        })

    kpis = [
        kpi_card("Total Requests",        total_req,              "📋", C_BLUE),
        kpi_card("Completed / Total", f"{total_completed}/{total_svc}", "✅", C_GREEN),
        kpi_card("Scheduled",             total_scheduled,        "📅", C_PURPLE),
        kpi_card("Total Repair Cost",     f"${total_repair:,.2f}","💰", C_ORANGE),
        kpi_card("Parts Cost",            f"${total_parts:,.2f}", "⚙️", C_YELLOW),
        kpi_card("Labor Cost",            f"${total_labor:,.2f}",  "👤", C_PINK),
    ]

    # ── Hours by Equipment ────────────────────────────────────────────────────
    hours_map = {}
    for _, row in rep.iterrows():
        name = str(row["equipment"]).lower()
        eq = "Versamatic" if "versamatic" in name else \
             "Lindhaus"   if "lindhaus"   in name else \
             "Kaivac"     if "kaivac"     in name else str(row["equipment"])
        hours_map[eq] = hours_map.get(eq, 0) + row["hours"]

    eq_names = list(hours_map.keys())
    eq_hours = [hours_map[k] for k in eq_names]
    bar_colors = [C_BLUE, C_PURPLE, C_GREEN, "#06b6d4"][:len(eq_names)]

    hours_fig = go.Figure(go.Bar(
        x=eq_hours, y=eq_names, orientation="h",
        marker=dict(
            color=bar_colors,
            opacity=0.85,
            line=dict(width=0),
        ),
        text=[f"{h:.1f} hrs" for h in eq_hours],
        textposition="outside",
        textfont=dict(size=12, color=COLOR_TEXT_SECONDARY),
    ))
    hours_fig.update_layout(
        title=dict(text="Repair Hours by Equipment", font=dict(color=COLOR_TEXT_PRIMARY, size=14, family="'DM Sans','Segoe UI',sans-serif"), x=0.02),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=CHART_FONT,
        xaxis=dict(
            gridcolor=COLOR_BORDER,
            tickcolor=COLOR_TEXT_MUTED,
            title=dict(text="Hours", font=dict(size=11, color=COLOR_TEXT_MUTED)),
            zeroline=False,
            showline=False,
        ),
        yaxis=dict(
            gridcolor="rgba(0,0,0,0)",
            tickcolor=COLOR_TEXT_MUTED,
            showline=False,
        ),
        margin=dict(l=10, r=40, t=45, b=25),
        bargap=0.35,
    )

    # ── Calendar Heatmap ──────────────────────────────────────────────────────
    period   = pd.Period(month_key)
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
        rows.append(row_i); cols.append(col)
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
            colors.append(C_BLUE)
        col += 1
        if col > 6:
            col = 0; row_i += 1

    max_row = max(rows, default=0)

    cal_fig = go.Figure()
    cal_fig.add_trace(go.Scatter(
        x=cols, y=[max_row - r for r in rows],
        mode="markers+text",
        marker=dict(
            size=32, color=colors, symbol="square",
            line=dict(color="#e2e8f0", width=1.5),
        ),
        text=texts, textposition="middle center",
        textfont=dict(color=COLOR_TEXT_PRIMARY, size=11, family="'DM Sans','Segoe UI',sans-serif"),
        customdata=customdata,
        hovertemplate="%{text} — %{customdata} request(s)<extra></extra>",
    ))
    day_names = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
    cal_fig.update_layout(
        title=dict(
            text=f"Request Volume — {period.strftime('%B %Y')}",
            font=dict(color=COLOR_TEXT_PRIMARY, size=14, family="'DM Sans','Segoe UI',sans-serif"),
            x=0.02,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=CHART_FONT,
        xaxis=dict(
            tickvals=list(range(7)), ticktext=day_names,
            showgrid=False, zeroline=False,
            tickfont=dict(color=COLOR_TEXT_SECONDARY, size=11),
            showline=False,
        ),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, showline=False),
        margin=dict(l=10, r=10, t=45, b=10),
        showlegend=False,
    )

    # ── Replacement Table ──────────────────────────────────────────────────────
    agg = rep.groupby("equipId").agg(
        equipment=("equipment","first"),
        equipId=("equipId","first"),
        newPrice=("newPrice","first"),
        parts=("parts","sum"),
        labor=("labor","sum"),
    ).reset_index(drop=True)

    agg["Total Cost"]     = agg["labor"] + agg["parts"]
    agg["80% Threshold"]  = agg["Total Cost"] * 0.80
    agg["60% Threshold"]  = agg["Total Cost"] * 0.60
    agg["Status"]         = agg.apply(lambda r: replace_status(r["labor"], r["parts"], r["newPrice"]), axis=1)
    agg = agg.sort_values("Status")

    table_data = agg.rename(columns={
        "equipment": "Equipment", "equipId": "ID", "newPrice": "New Price",
        "parts": "Parts Cost",   "labor":   "Labor Cost",
    })[["Status","Equipment","ID","Parts Cost","Labor Cost","Total Cost","New Price","80% Threshold","60% Threshold"]].copy()

    for c in ["Parts Cost","Labor Cost","Total Cost","New Price","80% Threshold","60% Threshold"]:
        table_data[c] = table_data[c].apply(lambda x: f"${x:,.2f}")

    records = table_data.to_dict("records")
    columns = [{"name": c, "id": c} for c in table_data.columns]

    STATUS_STYLES = {
        "Replace": {"bg": "#fef2f2", "color": "#dc2626", "badge": "🔴 Replace"},
        "Monitor": {"bg": "#fffbeb", "color": "#d97706", "badge": "🟡 Monitor"},
        "Good":    {"bg": "#f0fdf4", "color": "#059669", "badge": "🟢 Good"},
    }

    # Inject badge text into records
    for r in records:
        s = r.get("Status", "Good")
        r["Status"] = STATUS_STYLES.get(s, STATUS_STYLES["Good"])["badge"]

    cond_style = []
    for status, style in STATUS_STYLES.items():
        badge = style["badge"]
        cond_style.append({
            "if": {"filter_query": f'{{Status}} = "{badge}"'},
            "backgroundColor": style["bg"],
        })
        cond_style.append({
            "if": {"filter_query": f'{{Status}} = "{badge}"', "column_id": "Status"},
            "color": style["color"],
            "fontWeight": "700",
        })
    # Zebra stripe for non-status rows
    cond_style.append({
        "if": {"row_index": "odd"},
        "backgroundColor": "#fafbfc",
    })

    footer = f"Data reflects {period.strftime('%B %Y')}  ·  {len(rep)} repair records  ·  {len(svc)} service orders"

    # ── Completion Rate Gauge ─────────────────────────────────────────────────
    rate_val = (total_completed / total_svc * 100) if total_svc > 0 else 0
    gauge_color = C_GREEN if rate_val >= 80 else C_YELLOW if rate_val >= 50 else "#ef4444"
    completion_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=rate_val,
        number={"suffix": "%", "font": {"size": 32, "color": COLOR_TEXT_PRIMARY, "family": "'DM Sans','Segoe UI',sans-serif"}},
        title={"text": "Completion Rate", "font": {"size": 13, "color": COLOR_TEXT_SECONDARY, "family": "'DM Sans','Segoe UI',sans-serif"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": COLOR_TEXT_MUTED,
                     "tickfont": {"size": 10, "color": COLOR_TEXT_MUTED}},
            "bar": {"color": gauge_color, "thickness": 0.25},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50],  "color": "#fef2f2"},
                {"range": [50, 80], "color": "#fffbeb"},
                {"range": [80, 100],"color": "#f0fdf4"},
            ],
            "threshold": {"line": {"color": gauge_color, "width": 3}, "thickness": 0.75, "value": rate_val},
        },
    ))
    completion_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=10), height=260,
    )

    # ── Avg Hours Gauge ───────────────────────────────────────────────────────
    avg_val = (total_hours / repair_count) if repair_count > 0 else 0
    max_gauge = max(avg_val * 2, 4)
    avg_color = C_BLUE if avg_val < max_gauge * 0.5 else C_ORANGE if avg_val < max_gauge * 0.75 else "#ef4444"
    avghours_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg_val,
        number={"suffix": " hrs", "valueformat": ".1f", "font": {"size": 32, "color": COLOR_TEXT_PRIMARY, "family": "'DM Sans','Segoe UI',sans-serif"}},
        title={"text": "Avg Repair Hours", "font": {"size": 13, "color": COLOR_TEXT_SECONDARY, "family": "'DM Sans','Segoe UI',sans-serif"}},
        gauge={
            "axis": {"range": [0, max_gauge], "tickwidth": 1, "tickcolor": COLOR_TEXT_MUTED,
                     "tickfont": {"size": 10, "color": COLOR_TEXT_MUTED}},
            "bar": {"color": avg_color, "thickness": 0.25},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0,              max_gauge * 0.5],  "color": "#f0fdf4"},
                {"range": [max_gauge * 0.5, max_gauge * 0.75],"color": "#fffbeb"},
                {"range": [max_gauge * 0.75, max_gauge],       "color": "#fef2f2"},
            ],
            "threshold": {"line": {"color": avg_color, "width": 3}, "thickness": 0.75, "value": avg_val},
        },
    ))
    avghours_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=10), height=260,
    )

    # ── Capacity Utilization Chart ────────────────────────────────────────────
    STAFF_COUNT   = 4
    HOURS_PER_DAY = 4
    WORK_DAYS     = 20
    capacity      = STAFF_COUNT * HOURS_PER_DAY * WORK_DAYS   # 320 hrs
    used          = rep["hours"].sum()
    remaining     = max(capacity - used, 0)
    util_pct      = used / capacity * 100 if capacity > 0 else 0

    util_color = C_GREEN if util_pct < 50 else C_YELLOW if util_pct < 80 else "#ef4444"

    staff_fig = go.Figure()
    # Used bar
    staff_fig.add_trace(go.Bar(
        x=[used], y=["Capacity"],
        orientation="h",
        name="Used on Repairs",
        marker=dict(color=util_color, opacity=0.9, line=dict(width=0)),
        text=[f"{used:.1f} hrs ({util_pct:.1f}%)"],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=12, color="white", family="'DM Sans','Segoe UI',sans-serif"),
    ))
    # Remaining bar
    staff_fig.add_trace(go.Bar(
        x=[remaining], y=["Capacity"],
        orientation="h",
        name="Available",
        marker=dict(color=COLOR_BORDER, opacity=0.6, line=dict(width=0)),
        text=[f"{remaining:.0f} hrs remaining"],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=12, color=COLOR_TEXT_MUTED, family="'DM Sans','Segoe UI',sans-serif"),
    ))
    staff_fig.update_layout(
        title=dict(
            text=f"Staff Capacity Utilization  ·  {STAFF_COUNT} staff × {HOURS_PER_DAY} hrs × {WORK_DAYS} days = {capacity} hrs",
            font=dict(color=COLOR_TEXT_PRIMARY, size=13, family="'DM Sans','Segoe UI',sans-serif"),
            x=0.02,
        ),
        barmode="stack",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=CHART_FONT,
        xaxis=dict(
            range=[0, capacity],
            gridcolor=COLOR_BORDER, zeroline=False, showline=False,
            title=dict(text="Hours", font=dict(size=11, color=COLOR_TEXT_MUTED)),
            tickfont=dict(size=11, color=COLOR_TEXT_MUTED),
        ),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, showline=False),
        legend=dict(
            orientation="h", x=0.02, y=-0.15,
            font=dict(size=11, color=COLOR_TEXT_SECONDARY),
        ),
        margin=dict(l=10, r=20, t=50, b=40),
        height=260,
    )

    return kpis, hours_fig, cal_fig, completion_fig, avghours_fig, staff_fig, columns, records, cond_style, footer


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Dashboard running at http://127.0.0.1:8050")
    app.run(debug=True)

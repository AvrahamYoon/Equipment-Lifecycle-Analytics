"""
Work Order Dashboard — Facilities Management
============================================
Run:  pip install dash pandas plotly
      python work_order_dashboard.py
Then open http://127.0.0.1:8050 in your browser.

To add more months, place CSV files alongside this script and update
the three load_* functions below.  The month dropdown will expand
automatically once new data is loaded.
"""

import math
import calendar
import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, dash_table

# ── Data ──────────────────────────────────────────────────────────────────────
# Update these paths to point to your actual CSV files.
REQUESTS_CSV  = "Work_Orders_April_2026_Request.csv"
SERVICE_CSV   = "April_Service_Orders_with_Prices.csv"
REPAIRS_CSV   = "April_Repair_List_All_Work_Orders.csv"


def load_requests(path: str) -> pd.DataFrame:
    """Load the Work Order Request CSV."""
    raw = pd.read_csv(path, header=None)
    # Row 0 is a title, row 1 is the real header
    raw.columns = raw.iloc[1]
    df = raw.iloc[2:].reset_index(drop=True)
    df = df[df["Work Order #"].notna() & ~df["Work Order #"].str.startswith("Total")]
    df["Request Date"] = pd.to_datetime(df["Request Date"], format="%m/%d/%Y", errors="coerce")
    df["month_key"] = df["Request Date"].dt.to_period("M").astype(str)
    return df


def load_service(path: str) -> pd.DataFrame:
    """Load the Service Orders with Prices CSV."""
    df = pd.read_csv(path)
    df["Sched. Date"]     = pd.to_datetime(df["Sched. Date"],     errors="coerce")
    df["Completed Date"]  = pd.to_datetime(df["Completed Date"],  errors="coerce")
    df["month_key"] = df["Sched. Date"].dt.to_period("M").astype(str)
    return df


def load_repairs(path: str) -> pd.DataFrame:
    """Load the Repair List (All Work Orders) CSV."""
    raw = pd.read_csv(path, skiprows=1, header=None)
    # Row 0 is the real column header
    raw.columns = raw.iloc[0]
    df = raw.iloc[1:].reset_index(drop=True)
    # Keep only real data rows (exclude TOTALS / notes)
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

    # Map new-equipment prices by equipment type (update as needed)
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
        return 1035  # default
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


# ── Helper: replacement status ────────────────────────────────────────────────
def replace_status(labor, parts, new_price):
    combined = labor + parts
    if combined * 0.80 >= new_price:
        return "Replace 🔴"
    if combined * 0.60 >= new_price:
        return "Monitor 🟡"
    return "Good 🟢"


STATUS_BG = {
    "Replace 🔴": "#fee2e2",
    "Monitor 🟡": "#fef9c3",
    "Good 🟢":    "#dcfce7",
}


# ── App ───────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__)
app.title = "Work Order Dashboard"

app.layout = html.Div([
    # ── Header ────────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.P("FACILITIES MANAGEMENT", style={"fontSize":11,"letterSpacing":"0.15em","color":"#38bdf8","margin":0,"fontWeight":700}),
            html.H1("Work Order Dashboard", style={"margin":"4px 0 0","fontSize":28,"color":"#f8fafc","fontWeight":800}),
            html.P("Custodial Equipment Repair & Service Tracker", style={"margin":"4px 0 0","fontSize":13,"color":"#64748b"}),
        ]),
        html.Div([
            html.Label("SELECT MONTH", style={"fontSize":11,"fontWeight":700,"color":"#94a3b8","letterSpacing":"0.1em","marginBottom":6,"display":"block"}),
            dcc.Dropdown(
                id="month-select",
                options=MONTH_OPTIONS,
                value=all_months[0],
                clearable=False,
                style={"width":180,"fontFamily":"inherit"},
            ),
        ], style={"marginTop":8}),
    ], style={
        "display":"flex","justifyContent":"space-between","alignItems":"flex-start",
        "flexWrap":"wrap","gap":16,"marginBottom":28,
        "padding":"24px 24px 0",
    }),

    # ── KPI Row ───────────────────────────────────────────────────────────────
    html.Div(id="kpi-row", style={"display":"flex","flexWrap":"wrap","gap":14,"padding":"0 24px","marginBottom":20}),

    # ── Middle: Hours bar + Calendar ──────────────────────────────────────────
    html.Div([
        dcc.Graph(id="hours-chart", style={"flex":"1","minWidth":320}),
        dcc.Graph(id="calendar-chart", style={"flex":"1","minWidth":320}),
    ], style={"display":"flex","gap":16,"padding":"0 24px","marginBottom":20}),

    # ── Replacement Table ─────────────────────────────────────────────────────
    html.Div([
        html.Div("🚦 Equipment Replacement Indicator",
                 style={"fontSize":12,"fontWeight":700,"color":"#38bdf8","letterSpacing":"0.1em","textTransform":"uppercase","marginBottom":8}),
        html.P("🔴 Red: (Labor+Parts)×0.80 ≥ New Price  |  🟡 Yellow: (Labor+Parts)×0.60 ≥ New Price  |  🟢 Green: Below threshold",
               style={"fontSize":11,"color":"#94a3b8","marginBottom":12}),
        dash_table.DataTable(
            id="replace-table",
            style_table={"overflowX":"auto"},
            style_header={"backgroundColor":"#0f172a","color":"#64748b","fontWeight":"bold","fontSize":11},
            style_cell={"backgroundColor":"#1e293b","color":"#e2e8f0","fontSize":13,"padding":"9px 12px","border":"1px solid #334155"},
            style_data_conditional=[],
        ),
    ], style={"background":"#1e293b","border":"1px solid #1e3a5f","borderRadius":16,"padding":20,"margin":"0 24px","marginBottom":24}),

    # ── Footer ────────────────────────────────────────────────────────────────
    html.Div(id="footer-text", style={"textAlign":"center","fontSize":11,"color":"#475569","paddingBottom":24}),

], style={
    "minHeight":"100vh",
    "background":"linear-gradient(135deg,#0f172a 0%,#1e293b 50%,#0f172a 100%)",
    "fontFamily":"'DM Sans','Segoe UI',sans-serif",
    "color":"#e2e8f0",
})


# ── Callbacks ─────────────────────────────────────────────────────────────────
@app.callback(
    Output("kpi-row", "children"),
    Output("hours-chart", "figure"),
    Output("calendar-chart", "figure"),
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

    def kpi_card(label, value, icon, color):
        return html.Div([
            html.Div(icon, style={"fontSize":22,"marginBottom":6}),
            html.Div(str(value), style={"fontSize":22,"fontWeight":800,"color":color}),
            html.Div(label, style={"fontSize":11,"color":"#64748b","fontWeight":600,"textTransform":"uppercase","letterSpacing":"0.05em","marginTop":4}),
        ], style={
            "background":"linear-gradient(135deg,#1e293b,#0f172a)",
            "border":"1px solid #1e3a5f","borderRadius":16,"padding":"18px 16px",
            "minWidth":150,"flex":"1",
        })

    kpis = [
        kpi_card("Total Requests",         total_req,                       "📋", "#38bdf8"),
        kpi_card("Work Orders Completed",  total_completed,                 "✅", "#34d399"),
        kpi_card("Work Orders Scheduled",  total_scheduled,                 "📅", "#a78bfa"),
        kpi_card("Total Repair Cost",      f"${total_repair:,.2f}",         "🔧", "#fb923c"),
        kpi_card("Total Parts Cost",       f"${total_parts:,.2f}",          "⚙️", "#fbbf24"),
        kpi_card("Total Labor Cost",       f"${total_labor:,.2f}",          "👷", "#f472b6"),
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

    hours_fig = go.Figure(go.Bar(
        x=eq_hours, y=eq_names, orientation="h",
        marker=dict(color=["#2563eb","#38bdf8","#0ea5e9","#7dd3fc"][:len(eq_names)],
                    line=dict(width=0)),
        text=[f"{h:.1f} hrs" for h in eq_hours], textposition="auto",
    ))
    hours_fig.update_layout(
        title=dict(text="⏱ Repair Hours by Equipment Type", font=dict(color="#38bdf8",size=13)),
        plot_bgcolor="#0f172a", paper_bgcolor="#1e293b",
        font=dict(color="#cbd5e1", family="DM Sans"),
        xaxis=dict(gridcolor="#1e3a5f",tickcolor="#475569",title="Hours"),
        yaxis=dict(gridcolor="#1e3a5f",tickcolor="#475569"),
        margin=dict(l=20,r=20,t=50,b=20),
    )

    # ── Calendar Heatmap ──────────────────────────────────────────────────────
    period   = pd.Period(month_key)
    year, mo = period.year, period.month
    first_wd = calendar.monthrange(year, mo)[0]   # 0=Monday…6=Sunday (Python)
    # Convert to Sunday-first (0=Sun)
    first_col = (first_wd + 1) % 7
    days_in_mo = calendar.monthrange(year, mo)[1]

    # Count requests per day
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
        if cnt == 0:         colors.append("#1e293b")
        elif intensity < 0.2: colors.append("#bfdbfe")
        elif intensity < 0.4: colors.append("#93c5fd")
        elif intensity < 0.6: colors.append("#60a5fa")
        elif intensity < 0.8: colors.append("#2563eb")
        else:                  colors.append("#1e3a5f")
        col += 1
        if col > 6:
            col = 0; row_i += 1

    max_row = max(rows, default=0)

    cal_fig = go.Figure()
    cal_fig.add_trace(go.Scatter(
        x=cols, y=[max_row - r for r in rows],
        mode="markers+text",
        marker=dict(size=30, color=colors, symbol="square", line=dict(color="#0f172a",width=2)),
        text=texts, textposition="middle center",
        textfont=dict(color="#f8fafc", size=11, family="DM Sans"),
        customdata=customdata,
        hovertemplate="%{text} — %{customdata} request(s)<extra></extra>",
    ))
    day_names = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
    cal_fig.update_layout(
        title=dict(text=f"📆 Request Volume — {period.strftime('%B %Y')}", font=dict(color="#38bdf8",size=13)),
        plot_bgcolor="#0f172a", paper_bgcolor="#1e293b",
        font=dict(color="#cbd5e1", family="DM Sans"),
        xaxis=dict(tickvals=list(range(7)), ticktext=day_names, showgrid=False, zeroline=False),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        margin=dict(l=10,r=10,t=50,b=10),
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

    agg["Total Cost"] = agg["labor"] + agg["parts"]
    agg["80% Threshold"] = agg["Total Cost"] * 0.80
    agg["60% Threshold"] = agg["Total Cost"] * 0.60
    agg["Status"] = agg.apply(lambda r: replace_status(r["labor"], r["parts"], r["newPrice"]), axis=1)
    agg = agg.sort_values("Status")

    table_data = agg.rename(columns={
        "equipment":"Equipment","equipId":"ID","newPrice":"New Price",
        "parts":"Parts Cost","labor":"Labor Cost",
    })[["Status","Equipment","ID","Parts Cost","Labor Cost","Total Cost","New Price","80% Threshold","60% Threshold"]].copy()
    for col in ["Parts Cost","Labor Cost","Total Cost","New Price","80% Threshold","60% Threshold"]:
        table_data[col] = table_data[col].apply(lambda x: f"${x:,.2f}")
    records = table_data.to_dict("records")
    columns = [{"name": c, "id": c} for c in table_data.columns]

    cond_style = []
    for status, bg in STATUS_BG.items():
        cond_style.append({
            "if": {"filter_query": f'{{Status}} = "{status}"'},
            "backgroundColor": bg, "color": "#111",
        })

    footer = f"Data reflects {period.strftime('%B %Y')} · {len(rep)} repair records · {len(svc)} service orders"
    return kpis, hours_fig, cal_fig, columns, records, cond_style, footer


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Dashboard running at http://127.0.0.1:8050")
    app.run(debug=True)

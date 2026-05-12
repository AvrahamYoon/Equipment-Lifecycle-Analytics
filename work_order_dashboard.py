"""
Work Order Dashboard — Facilities Management Services
============================================
Run:  pip install dash pandas plotly
      python work_order_dashboard.py
Then open http://127.0.0.1:8050 in your browser.
"""

import math
import calendar
import glob
import os
import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, dash_table
from pandas.tseries.holiday import USFederalHolidayCalendar

# ── Data ──────────────────────────────────────────────────────────────────────
# Put exports under these folders (one type per folder). Every *.csv in a folder
# is loaded and concatenated (e.g. one file per month). Filenames are free-form.
REQUESTS_DIR = os.path.join("data", "requests")
SERVICE_DIR = os.path.join("data", "service")
REPAIRS_DIR = os.path.join("data", "repairs")
EQUIPMENT_SUMMARY_CSV = os.path.join("data", "equipment", "cleaned", "all_equipment_summary.csv")
# Annual baseline days (excludes weekends/holidays in your definition); downtime uses same Mon–Fri excl. US federal holidays.
BASE_AVAIL_DAYS = 311
# Shared buckets for hours, turnaround, availability (order = display order)
CHART_CLASS_ORDER = [
    "Versamatic",
    "Lindhaus",
    "Kaivac",
    "Wet-dry / shop vacuums",
    "Other vacuums",
    "Floor machines",
    "Carpet / extractors",
    "Ladders",
    "Dispensers",
    "Janitorial / carts",
    "Other",
]
_CHART_CLASS_RANK = {c: i for i, c in enumerate(CHART_CLASS_ORDER)}


def _norm_equip_id(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).replace(" ", "").strip().upper()


def _federal_holiday_norm_set():
    cal = USFederalHolidayCalendar()
    h = cal.holidays(start="2000-01-01", end="2035-12-31")
    return set(pd.Timestamp(ts).normalize() for ts in h)


_FED_HOLIDAYS_NORM = _federal_holiday_norm_set()


def business_days_inclusive(start, end) -> float:
    """Mon–Fri inclusive between start and end (calendar dates), excluding US federal holidays."""
    if pd.isna(start) or pd.isna(end):
        return float("nan")
    a = pd.Timestamp(start).normalize()
    b = pd.Timestamp(end).normalize()
    if b < a:
        return float("nan")
    n = 0
    for d in pd.date_range(a, b, freq="D"):
        if d.weekday() >= 5:
            continue
        if d.normalize() in _FED_HOLIDAYS_NORM:
            continue
        n += 1
    return float(n)


def equipment_chart_class(text: str) -> str:
    """
    One taxonomy for all equipment charts: not too many labels, not only 3 brands + Other.
    Uses name / type keywords; refine CHART_CLASS_ORDER if your fleet differs.
    """
    t = str(text).strip().lower()
    if not t:
        return "Other"

    if "versamatic" in t:
        return "Versamatic"
    if "lindhaus" in t:
        return "Lindhaus"
    if "kaivac" in t:
        return "Kaivac"

    if "ladder" in t:
        return "Ladders"
    if "dispenser" in t or "chemical disp" in t:
        return "Dispensers"

    if any(
        k in t
        for k in ("burnisher", "buffer", "scrubber", "auto scrub", "autoscrub", "floor machine")
    ):
        return "Floor machines"
    if any(k in t for k in ("extractor", "carpet ", "carpet-", "spotter")):
        return "Carpet / extractors"

    if any(
        k in t
        for k in ("wet-dry", "wet dry", "wet/dry", "wetdry", "shop vac", "shop-vac", "shopvac")
    ):
        return "Wet-dry / shop vacuums"
    if "viper" in t:
        return "Wet-dry / shop vacuums"

    if "vacuum" in t or t.endswith(" vac") or " vac " in t:
        return "Other vacuums"

    if any(k in t for k in ("cart", "janitor", "mop bucket", "mop ", "wringer")):
        return "Janitorial / carts"

    return "Other"


def _equipment_row_category(row) -> str:
    """Row from equipment summary: prefer Name, else EquipType."""
    name = row.get("Name", "")
    if pd.notna(name) and str(name).strip():
        return equipment_chart_class(str(name))
    et = row.get("EquipType", "")
    if pd.notna(et) and str(et).strip():
        return equipment_chart_class(str(et))
    return "Other"


def _load_equipment_summary() -> pd.DataFrame:
    if not os.path.isfile(EQUIPMENT_SUMMARY_CSV):
        return pd.DataFrame()
    try:
        df = pd.read_csv(EQUIPMENT_SUMMARY_CSV)
    except Exception:
        return pd.DataFrame()
    if df.empty or "EquipmentId" not in df.columns:
        return df
    df = df.copy()
    df["equipIdNorm"] = df["EquipmentId"].map(_norm_equip_id)
    df["category"] = df.apply(_equipment_row_category, axis=1)
    return df


def _csv_paths_in_dir(directory: str) -> list[str]:
    if not os.path.isdir(directory):
        return []
    paths = sorted(glob.glob(os.path.join(directory, "*.csv")))
    return [p for p in paths if os.path.isfile(p)]


def _load_requests_merged() -> pd.DataFrame:
    paths = _csv_paths_in_dir(REQUESTS_DIR)
    if not paths:
        raise FileNotFoundError(
            f"No *.csv under {REQUESTS_DIR!r}. Create the folder and add at least one request export."
        )
    return pd.concat([load_requests(p) for p in paths], ignore_index=True)


def _load_service_merged() -> pd.DataFrame:
    paths = _csv_paths_in_dir(SERVICE_DIR)
    if not paths:
        raise FileNotFoundError(
            f"No *.csv under {SERVICE_DIR!r}. Create the folder and add at least one service export."
        )
    return pd.concat([load_service(p) for p in paths], ignore_index=True)


def _load_repairs_merged() -> pd.DataFrame:
    paths = _csv_paths_in_dir(REPAIRS_DIR)
    if not paths:
        raise FileNotFoundError(
            f"No *.csv under {REPAIRS_DIR!r}. Create the folder and add at least one repair export."
        )
    return pd.concat([load_repairs(p) for p in paths], ignore_index=True)


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
    id_col = "Equipment Id" if "Equipment Id" in df.columns else None
    if id_col:
        df["equipIdNorm"] = df[id_col].map(_norm_equip_id)
    else:
        df["equipIdNorm"] = ""
    name_col = "Equipment Name" if "Equipment Name" in df.columns else None
    if name_col:
        df["equipCategory"] = df[name_col].map(equipment_chart_class)
    else:
        df["equipCategory"] = "Other"
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
    df_req = _load_requests_merged()
    df_service = _load_service_merged()
    df_repairs = _load_repairs_merged()
    df_equip = _load_equipment_summary()
except FileNotFoundError as e:
    raise SystemExit(
        f"{e}\n"
        "Add one or more *.csv files under data/requests, data/service, and data/repairs "
        "(run the script from the project root so those paths resolve)."
    ) from e

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
            html.Span("Facilities Management Services", style={
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

        # Turnaround + availability (business days; 311-day basis)
        html.Div([
            html.Div([
                dcc.Graph(id="turnaround-chart", config={"displayModeBar": False, "responsive": True},
                          style={"height": 300}),
            ], style={**CARD_STYLE, "flex": "1", "minWidth": 320, "padding": "16px 8px 8px"}),
            html.Div([
                dcc.Graph(id="availability-chart", config={"displayModeBar": False, "responsive": True},
                          style={"height": 300}),
            ], style={**CARD_STYLE, "flex": "1", "minWidth": 320, "padding": "16px 8px 8px"}),
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
    Output("turnaround-chart", "figure"),
    Output("availability-chart", "figure"),
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
        eq = equipment_chart_class(str(row["equipment"]))
        hours_map[eq] = hours_map.get(eq, 0) + row["hours"]

    eq_names = sorted(
        hours_map.keys(),
        key=lambda k: (_CHART_CLASS_RANK.get(k, len(CHART_CLASS_ORDER)), -hours_map[k]),
    )
    eq_hours = [hours_map[k] for k in eq_names]
    _pal = [C_BLUE, C_PURPLE, C_GREEN, C_ORANGE, C_YELLOW, C_PINK, "#06b6d4", "#6366f1", "#14b8a6", "#eab308"]
    bar_colors = [_pal[i % len(_pal)] for i in range(len(eq_names))]

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

    # ── Avg turnaround: sched. → completed (business days) ───────────────────
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
        avg_turn["_ord"] = avg_turn["equipCategory"].map(_CHART_CLASS_RANK)
        avg_turn = avg_turn.sort_values(
            ["_ord", "turnaround_bd"],
            ascending=[True, True],
            na_position="last",
        ).drop(columns=["_ord"])
    else:
        avg_turn = pd.DataFrame(columns=["equipCategory", "turnaround_bd"])

    if not avg_turn.empty:
        turnaround_fig = go.Figure(go.Bar(
            x=avg_turn["turnaround_bd"],
            y=avg_turn["equipCategory"],
            orientation="h",
            marker=dict(color=C_PURPLE, opacity=0.85, line=dict(width=0)),
            text=[f"{v:.1f} d" for v in avg_turn["turnaround_bd"]],
            textposition="outside",
            textfont=dict(size=12, color=COLOR_TEXT_SECONDARY),
        ))
        turnaround_fig.update_layout(
            title=dict(
                text=(
                    "Avg turnaround by equipment class (schedule → completion)<br>"
                    "<sup>Classes from name keywords (same buckets as hours & availability). "
                    "Weekdays only; US federal holidays not counted</sup>"
                ),
                font=dict(color=COLOR_TEXT_PRIMARY, size=14, family="'DM Sans','Segoe UI',sans-serif"),
                x=0.02,
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=CHART_FONT,
            xaxis=dict(
                gridcolor=COLOR_BORDER,
                title=dict(text="Days", font=dict(size=11, color=COLOR_TEXT_MUTED)),
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
            font=CHART_FONT,
            margin=dict(l=20, r=20, t=50, b=20),
            height=300,
        )

    # ── Availability: (1/n) Σ((311 − downtime)/311)×100, downtime = sum of business days ──
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
            t = min(downtime_by_id.get(eid, 0.0), float(BASE_AVAIL_DAYS))
            terms.append((BASE_AVAIL_DAYS - t) / BASE_AVAIL_DAYS)
        pct = (sum(terms) / len(all_ids)) * 100.0
        avail_by_cat[cat] = pct

    avail_cats = [c for c in CHART_CLASS_ORDER if c in avail_by_cat]
    avail_pcts = [avail_by_cat[c] for c in avail_cats]

    if avail_cats:
        avail_fig = go.Figure(go.Bar(
            x=avail_cats,
            y=avail_pcts,
            marker=dict(color=C_GREEN, opacity=0.88, line=dict(width=0)),
            text=[f"{p:.1f}%" for p in avail_pcts],
            textposition="outside",
            textfont=dict(size=12, color=COLOR_TEXT_SECONDARY),
        ))
        avail_fig.update_layout(
            title=dict(
                text=(
                    "Availability by equipment group<br>"
                    "<sup>Per device: (311 − days down) ÷ 311. "
                    "Days down = sum of weekday schedule→completion days this month (cap 311). "
                    "Bar = mean over devices in group × 100%</sup>"
                ),
                font=dict(color=COLOR_TEXT_PRIMARY, size=14, family="'DM Sans','Segoe UI',sans-serif"),
                x=0.02,
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=CHART_FONT,
            yaxis=dict(
                range=[0, 105],
                gridcolor=COLOR_BORDER,
                title=dict(text="Availability %", font=dict(size=11, color=COLOR_TEXT_MUTED)),
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
            font=CHART_FONT,
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
        columns,
        records,
        cond_style,
        footer,
    )


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Dashboard running at http://127.0.0.1:8050")
    app.run(debug=True)

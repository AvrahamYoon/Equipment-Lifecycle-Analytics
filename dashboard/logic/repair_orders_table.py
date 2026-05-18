"""Service lines for the Order roster table (schedule → completion, business days)."""

import pandas as pd

from dashboard.calendar_util import business_days_inclusive
from dashboard.taxonomy import filter_equip_id_substr, norm_equip_id


def _pick_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _fmt_dt(x) -> str:
    if pd.isna(x):
        return ""
    try:
        return pd.Timestamp(x).strftime("%Y-%m-%d")
    except Exception:
        return ""


def build_repair_orders_table(svc: pd.DataFrame, filters: dict | None = None):
    """Returns (columns, records, style_data_conditional) for Dash DataTable."""
    filters = filters or {}
    cols = [
        {"name": "Equipment", "id": "Equipment"},
        {"name": "Equipment ID", "id": "Equipment ID"},
        {"name": "Category", "id": "Category"},
        {"name": "Status", "id": "Status"},
        {"name": "Start (scheduled)", "id": "Start (scheduled)"},
        {"name": "End (completed)", "id": "End (completed)"},
        {"name": "Business days (excl. weekends & US holidays)", "id": "Business days (excl. weekends & US holidays)"},
    ]
    if svc.empty:
        return cols, [], []

    df = svc.copy()
    name_col = _pick_col(df, ("Equipment Name", "Equipment name", "equipment"))
    id_col = _pick_col(df, ("Equipment Id", "Equipment ID", "Equipment Id"))
    sched_col = _pick_col(df, ("Sched. Date", "Sched Date", "Scheduled Date"))
    done_col = _pick_col(df, ("Completed Date", "Completed date", "Completion Date"))
    status_col = _pick_col(df, ("Status", "status"))

    if "equipCategory" not in df.columns:
        df["equipCategory"] = "Other"

    rows_out = []
    for _, r in df.iterrows():
        sd = r[sched_col] if sched_col else pd.NaT
        ed = r[done_col] if done_col else pd.NaT
        bd_str = ""
        if sched_col and done_col and pd.notna(sd) and pd.notna(ed):
            if pd.Timestamp(ed) >= pd.Timestamp(sd):
                bd = business_days_inclusive(sd, ed)
                if bd == bd:
                    bd_str = f"{bd:.0f}"

        name = str(r[name_col]) if name_col and pd.notna(r.get(name_col)) else ""
        raw_eid = r[id_col] if id_col and pd.notna(r.get(id_col)) else ""
        eid = norm_equip_id(raw_eid) if raw_eid != "" else ""
        cat = str(r.get("equipCategory", "") or "")
        st = str(r.get(status_col, "") or "").strip() if status_col else ""

        rows_out.append(
            {
                "Equipment": name,
                "Equipment ID": eid,
                "Category": cat,
                "Status": st,
                "Start (scheduled)": _fmt_dt(sd) if sched_col else "",
                "End (completed)": _fmt_dt(ed) if done_col else "",
                "Business days (excl. weekends & US holidays)": bd_str,
            }
        )

    tdf = pd.DataFrame(rows_out)

    cat_f = (filters.get("category") or "").strip()
    if cat_f:
        tdf = tdf[tdf["Category"] == cat_f]

    st_f = (filters.get("status_substr") or "").strip().lower()
    if st_f:
        tdf = tdf[tdf["Status"].str.lower().str.contains(st_f, na=False)]

    eq_f = (filters.get("equipment_substr") or "").strip().lower()
    if eq_f:
        tdf = tdf[tdf["Equipment"].str.lower().str.contains(eq_f, na=False)]

    id_f = (filters.get("id_substr") or "").strip()
    if id_f:
        tdf = tdf[filter_equip_id_substr(tdf["Equipment ID"], id_f)]

    cond = [
        {
            "if": {"row_index": "odd"},
            "backgroundColor": "#fafbfc",
        }
    ]
    return cols, tdf.to_dict("records"), cond


def repair_order_filter_options(svc: pd.DataFrame) -> list[dict]:
    """Dropdown options for repair-order category filter."""
    cat_opts = [{"label": "All categories", "value": ""}]
    if not svc.empty and "equipCategory" in svc.columns:
        for c in sorted(svc["equipCategory"].dropna().astype(str).unique()):
            if c:
                cat_opts.append({"label": c, "value": c})
    return cat_opts

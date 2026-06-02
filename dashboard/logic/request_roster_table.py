"""Work-request lines for the Request roster table."""

from __future__ import annotations

import pandas as pd


def _fmt_date(x) -> str:
    if pd.isna(x):
        return ""
    try:
        return pd.Timestamp(x).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""


def build_request_roster_table(req: pd.DataFrame, filters: dict | None = None):
    """Returns (columns, records, style_data_conditional) for Dash DataTable."""
    filters = filters or {}
    cols = [
        {"name": "Work order", "id": "Work order"},
        {"name": "Request date", "id": "Request date"},
        {"name": "Requestor", "id": "Requestor"},
        {"name": "Request", "id": "Request"},
        {"name": "Assigned to", "id": "Assigned to"},
    ]
    if req.empty:
        return cols, [], []

    df = req.copy()
    if "Request Date" in df.columns:
        df["_req_dt"] = pd.to_datetime(df["Request Date"], errors="coerce")
    else:
        df["_req_dt"] = pd.NaT

    day_f = (filters.get("day") or "").strip()
    if day_f:
        try:
            day_n = int(day_f)
            df = df[df["_req_dt"].dt.day == day_n]
        except ValueError:
            pass

    wo_f = (filters.get("work_order_substr") or "").strip().lower()
    if wo_f and "Work Order #" in df.columns:
        df = df[df["Work Order #"].astype(str).str.lower().str.contains(wo_f, na=False)]

    req_f = (filters.get("requestor_substr") or "").strip().lower()
    if req_f and "Requestor" in df.columns:
        df = df[df["Requestor"].astype(str).str.lower().str.contains(req_f, na=False)]

    text_f = (filters.get("request_substr") or "").strip().lower()
    if text_f and "Request" in df.columns:
        df = df[df["Request"].astype(str).str.lower().str.contains(text_f, na=False)]

    rows_out = []
    for _, r in df.iterrows():
        rows_out.append(
            {
                "Work order": str(r.get("Work Order #", "") or ""),
                "Request date": _fmt_date(r.get("Request Date")),
                "Requestor": str(r.get("Requestor", "") or ""),
                "Request": str(r.get("Request", "") or ""),
                "Assigned to": str(r.get("Assigned To", "") or ""),
            }
        )

    tdf = pd.DataFrame(rows_out)
    if not tdf.empty and "Request date" in tdf.columns:
        tdf = tdf.sort_values("Request date", ascending=False)

    cond = [{"if": {"row_index": "odd"}, "backgroundColor": "#fafbfc"}]
    return cols, tdf.to_dict("records"), cond

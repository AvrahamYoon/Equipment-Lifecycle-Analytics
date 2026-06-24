"""Assemble the Overview dashboard into a multi-page PDF report."""

from __future__ import annotations

from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

import plotly.graph_objects as go
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from dashboard import constants as C
from dashboard.data_loaders import df_equip, df_req, df_repairs, df_service
from dashboard.logic.overview import build_overview
from dashboard.logic.overview.kpis import compute_kpi_values
from dashboard.logic.service_scope import prepare_service_for_display
from dashboard.export.chart_text import plain_chart_text, sanitize_figure_for_export
from dashboard.export.kaleido_render import render_figures_batch
from dashboard.session_scope import apply_building_scope


def _month_label(month_key: str) -> str:
    if C.is_all_months(month_key):
        return C.ALL_MONTHS_LABEL
    try:
        return pd_period_label(month_key)
    except Exception:
        return str(month_key)


def pd_period_label(month_key: str) -> str:
    import pandas as pd

    return pd.Period(str(month_key)).strftime("%B %Y")


def _scope_overview_frames(month_key: str):
    rep_all = df_repairs[df_repairs["month_key"].astype(str) != "NaT"]
    rep_all = apply_building_scope(rep_all)
    if C.is_all_months(month_key):
        req = df_req[df_req["month_key"].astype(str) != "NaT"]
        svc = df_service[df_service["month_key"].astype(str) != "NaT"]
        rep = rep_all
    else:
        req = df_req[df_req["month_key"] == month_key]
        svc = df_service[df_service["month_key"] == month_key]
        rep = df_repairs[df_repairs["month_key"] == month_key]
    req = apply_building_scope(req)
    svc = apply_building_scope(svc)
    rep = apply_building_scope(rep)
    svc = prepare_service_for_display(svc, month_key, df_service)
    return req, svc, rep, rep_all


def _is_placeholder_figure(fig: go.Figure) -> bool:
    return len(fig.data) == 0


def _figure_title(fig: go.Figure, fallback: str) -> str:
    title = fig.layout.title
    if title is not None and title.text:
        plain = plain_chart_text(str(title.text))
        if plain:
            return plain
    return fallback


_SIZE_PRESETS = {
    "wide": (1100, 420),
    "tall": (1100, 520),
    "donut": (640, 420),
    "gauge": (520, 360),
}


def _prepare_figure(fig: go.Figure, *, width: int, height: int) -> go.Figure:
    export_fig = sanitize_figure_for_export(fig)
    export_fig.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        width=width,
        height=height,
    )
    return export_fig


def _collect_png_jobs(
    charts: list[tuple[str, go.Figure, str]],
) -> tuple[list[tuple[go.Figure, int, int]], list[dict[str, int | str]]]:
    """Build Kaleido batch jobs and a render plan for the PDF story."""
    jobs: list[tuple[go.Figure, int, int]] = []
    plan: list[dict[str, int | str]] = []
    i = 0
    while i < len(charts):
        _title, fig, hint = charts[i]
        if hint == "gauge" and i + 1 < len(charts) and charts[i + 1][2] == "gauge":
            w, h = _SIZE_PRESETS["gauge"]
            start = len(jobs)
            jobs.append((_prepare_figure(fig, width=w, height=h), w, h))
            jobs.append((_prepare_figure(charts[i + 1][1], width=w, height=h), w, h))
            plan.append({"kind": "gauge_pair", "chart_i": i, "png_i": start})
            i += 2
            continue
        w, h = _SIZE_PRESETS.get(hint, _SIZE_PRESETS["wide"])
        jobs.append((_prepare_figure(fig, width=w, height=h), w, h))
        plan.append({"kind": "single", "chart_i": i, "png_i": len(jobs) - 1})
        i += 1
    return jobs, plan


def _scaled_image(png_bytes: bytes, max_width: float, max_height: float) -> Image:
    reader = ImageReader(BytesIO(png_bytes))
    iw, ih = reader.getSize()
    if iw <= 0 or ih <= 0:
        return Image(BytesIO(png_bytes), width=max_width, height=max_height * 0.5)
    aspect = ih / float(iw)
    width = max_width
    height = width * aspect
    if height > max_height:
        height = max_height
        width = height / aspect
    return Image(BytesIO(png_bytes), width=width, height=height)


def _kpi_table(
    rows: list[tuple[str, str]],
    usable_width: float,
    value_style,
    label_style,
) -> Table:
    pairs = list(rows)
    while len(pairs) < 6:
        pairs.append(("", ""))
    pairs = pairs[:6]
    col_w = usable_width / 3
    data = [
        [Paragraph(escape(pairs[i][0]), label_style) for i in range(3)],
        [Paragraph(escape(pairs[i][1]), value_style) for i in range(3)],
        [Paragraph(escape(pairs[i][0]), label_style) for i in range(3, 6)],
        [Paragraph(escape(pairs[i][1]), value_style) for i in range(3, 6)],
    ]
    table = Table(data, colWidths=[col_w, col_w, col_w])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#f8fafc")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#e2e8f0")),
                ("LINEBELOW", (0, 1), (-1, 1), 0.5, colors.HexColor("#f1f5f9")),
                ("LINEBELOW", (0, 2), (-1, 2), 0.5, colors.HexColor("#e2e8f0")),
                ("LINEBELOW", (0, 3), (-1, 3), 0.5, colors.HexColor("#f1f5f9")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def _chart_sections(
    month_key: str,
    settings: dict[str, Any] | None,
) -> tuple[str, list[tuple[str, str]], list[tuple[str, go.Figure, str]]]:
    """Return footer text and ordered (title, figure, size_hint) chart sections."""
    req, svc, rep, rep_all = _scope_overview_frames(month_key)
    out = build_overview(month_key, req, svc, rep, df_equip, settings, rep_full=rep_all)
    footer = str(out[8])
    kpi_rows = compute_kpi_values(req, svc, rep)

    hours_fig = out[1]
    cal_fig = out[2]
    completion_fig = out[3]
    avghours_fig = out[4]
    staff_fig = out[5]
    turnaround_fig = out[6]
    avail_fig = out[7]
    primary_budget = out[9]
    secondary_budget = out[10]
    repair_count_fig = out[11]
    building_hours_fig = out[12]

    charts: list[tuple[str, go.Figure, str]] = [
        (_figure_title(hours_fig, "Repair Hours by Category"), hours_fig, "wide"),
        (
            _figure_title(
                cal_fig,
                "Request Volume by Month" if C.is_all_months(month_key) else "Request Calendar",
            ),
            cal_fig,
            "wide",
        ),
        (_figure_title(primary_budget, "Parts Budget"), primary_budget, "donut"),
        (_figure_title(repair_count_fig, "Repair Count Mix"), repair_count_fig, "donut"),
        (_figure_title(building_hours_fig, "Repair Hours by Building"), building_hours_fig, "tall"),
        (_figure_title(completion_fig, "Completion Rate"), completion_fig, "gauge"),
        (_figure_title(avghours_fig, "Avg Repair Hours"), avghours_fig, "gauge"),
        (_figure_title(staff_fig, "Staff Capacity"), staff_fig, "wide"),
        (_figure_title(turnaround_fig, "Turnaround"), turnaround_fig, "tall"),
        (_figure_title(avail_fig, "Availability"), avail_fig, "tall"),
    ]
    if secondary_budget is not None and not _is_placeholder_figure(secondary_budget):
        charts.insert(
            3,
            (_figure_title(secondary_budget, "Annual Parts Budget"), secondary_budget, "donut"),
        )

    charts = [(t, f, h) for t, f, h in charts if not _is_placeholder_figure(f)]
    return footer, kpi_rows, charts


def build_overview_pdf(
    month_key: str,
    settings: dict[str, Any] | None = None,
    *,
    pdf_subtitle: str | None = None,
) -> bytes:
    """Render the Overview page charts and KPIs into a PDF report."""
    footer, kpi_rows, charts = _chart_sections(month_key, settings)
    scope = _month_label(month_key)
    subtitle = pdf_subtitle or f"Scope: {scope}"

    buffer = BytesIO()
    page_size = landscape(A4)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.45 * inch,
        bottomMargin=0.45 * inch,
        title="Overview Report",
    )
    usable_width = page_size[0] - doc.leftMargin - doc.rightMargin
    usable_height = page_size[1] - doc.topMargin - doc.bottomMargin

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "OverviewTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceAfter=4,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "OverviewSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=6,
    )
    footer_style = ParagraphStyle(
        "OverviewFooter",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#94a3b8"),
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        "ChartSection",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=4,
        spaceAfter=6,
        textColor=colors.HexColor("#0f172a"),
    )
    kpi_label_style = ParagraphStyle(
        "KpiLabel",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748b"),
        fontName="Helvetica-Bold",
    )
    kpi_value_style = ParagraphStyle(
        "KpiValue",
        parent=styles["Normal"],
        fontSize=11,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
    )

    story: list = [
        Paragraph(escape("Work Order Dashboard — Overview"), title_style),
        Paragraph(escape(subtitle), subtitle_style),
        Paragraph(escape(footer), footer_style),
        _kpi_table(kpi_rows, usable_width, kpi_value_style, kpi_label_style),
    ]

    png_jobs, render_plan = _collect_png_jobs(charts)
    png_bytes = render_figures_batch(png_jobs) if png_jobs else []

    for step in render_plan:
        chart_i = int(step["chart_i"])
        png_i = int(step["png_i"])
        if step["kind"] == "gauge_pair":
            title_a = charts[chart_i][0]
            title_b = charts[chart_i + 1][0]
            story.append(PageBreak())
            story.append(Paragraph(escape(f"{title_a} · {title_b}"), section_style))
            story.append(Spacer(1, 8))
            half_w = (usable_width - 16) / 2
            img_a = _scaled_image(png_bytes[png_i], half_w, usable_height * 0.55)
            img_b = _scaled_image(png_bytes[png_i + 1], half_w, usable_height * 0.55)
            pair = Table([[img_a, img_b]], colWidths=[half_w, half_w], hAlign="CENTER")
            pair.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(pair)
            continue

        title_a = charts[chart_i][0]
        hint_a = charts[chart_i][2]
        story.append(PageBreak())
        story.append(Paragraph(escape(title_a), section_style))
        story.append(Spacer(1, 8))
        max_h = usable_height * (0.82 if hint_a == "tall" else 0.72)
        story.append(_scaled_image(png_bytes[png_i], usable_width, max_h))

    doc.build(story)
    return buffer.getvalue()

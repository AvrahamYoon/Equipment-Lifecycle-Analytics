"""Build PDF documents from Dash-style table columns and records."""

from __future__ import annotations

import re
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def plain_cell(value) -> str:
    """Strip Dash HTML pills / markdown before writing to PDF."""
    text = "" if value is None else str(value)
    if "<" in text:
        text = _HTML_TAG_RE.sub("", text)
    return text.strip()


def _records_matrix(columns: list[dict], records: list[dict]) -> list[list[str]]:
    col_ids = [c["id"] for c in columns]
    headers = [str(c.get("name") or c["id"]) for c in columns]
    rows = [headers]
    for rec in records:
        rows.append([plain_cell(rec.get(cid, "")) for cid in col_ids])
    return rows


def build_table_pdf(
    title: str,
    subtitle: str,
    columns: list[dict],
    records: list[dict],
    *,
    landscape_page: bool = True,
) -> bytes:
    """Return PDF bytes for a single data table."""
    buffer = BytesIO()
    page_size = landscape(A4) if landscape_page else A4
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=0.45 * inch,
        rightMargin=0.45 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        title=title,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PdfTitle",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        spaceAfter=4,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "PdfSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=10,
    )
    cell_style = ParagraphStyle(
        "PdfCell",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#0f172a"),
    )
    header_style = ParagraphStyle(
        "PdfHeader",
        parent=cell_style,
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#475569"),
        fontName="Helvetica-Bold",
    )

    story = [
        Paragraph(escape(title), title_style),
        Paragraph(escape(subtitle), subtitle_style),
    ]

    if not records:
        story.append(Paragraph("No rows match the current filters.", styles["Normal"]))
    else:
        matrix = _records_matrix(columns, records)
        header_row = [Paragraph(escape(cell), header_style) for cell in matrix[0]]
        body_rows = [
            [Paragraph(escape(cell), cell_style) for cell in row]
            for row in matrix[1:]
        ]
        table_data = [header_row, *body_rows]
        ncols = len(header_row)
        usable_width = page_size[0] - doc.leftMargin - doc.rightMargin
        col_width = usable_width / max(ncols, 1)

        table = Table(
            table_data,
            colWidths=[col_width] * ncols,
            repeatRows=1,
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#475569")),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.HexColor("#e2e8f0")),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#f1f5f9")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
                + [
                    ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafbfc"))
                    for i in range(2, len(table_data), 2)
                ]
            )
        )
        story.append(table)

    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            escape(f"{len(records):,} row(s)"),
            ParagraphStyle(
                "PdfFooter",
                parent=styles["Normal"],
                fontSize=8,
                textColor=colors.HexColor("#94a3b8"),
            ),
        )
    )

    doc.build(story)
    return buffer.getvalue()

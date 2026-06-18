"""Strip dashboard HTML / drill-down hints from chart text before PDF export."""

from __future__ import annotations

import re

import plotly.graph_objects as go

_BR_RE = re.compile(r"<br\s*/?>", re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_CLICK_HINT_RE = re.compile(r"\bclick\b", re.I)


def _strip_tags(text: str) -> str:
    return _TAG_RE.sub("", str(text or "")).strip()


def _is_click_hint(text: str) -> bool:
    plain = _strip_tags(text)
    if not plain:
        return True
    return bool(_CLICK_HINT_RE.search(plain))


def _subtitle_without_click_hints(text: str) -> str:
    plain = _strip_tags(text)
    if not plain:
        return ""
    kept = [seg.strip() for seg in plain.split("·") if seg.strip() and not _is_click_hint(seg)]
    return " · ".join(kept)


def plain_chart_text(raw: str) -> str:
    """Title text for PDF headings and exported chart images."""
    if not raw:
        return ""
    parts = _BR_RE.split(str(raw))
    main = _strip_tags(parts[0])
    subtitles: list[str] = []
    for part in parts[1:]:
        subtitle = _subtitle_without_click_hints(part)
        if subtitle:
            subtitles.append(subtitle)
    if main and subtitles:
        return f"{main} · {subtitles[0]}"
    return main or (subtitles[0] if subtitles else "")


def plain_annotation_text(raw: str) -> str:
    """Center labels and other in-chart annotations (no HTML)."""
    if not raw:
        return ""
    lines = [_strip_tags(part) for part in _BR_RE.split(str(raw))]
    return "\n".join(line for line in lines if line)


def sanitize_figure_for_export(fig: go.Figure) -> go.Figure:
    """Remove drill-down HTML from titles/annotations while keeping useful subtitles."""
    export_fig = go.Figure(fig)
    layout = export_fig.layout

    if layout.title is not None and layout.title.text:
        title_patch = layout.title.to_plotly_json()
        title_patch["text"] = plain_chart_text(layout.title.text)
        export_fig.update_layout(title=title_patch)

    if layout.annotations:
        patched = []
        for ann in layout.annotations:
            data = ann.to_plotly_json()
            if data.get("text"):
                data["text"] = plain_annotation_text(data["text"])
            patched.append(data)
        export_fig.update_layout(annotations=patched)

    return export_fig

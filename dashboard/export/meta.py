"""Export metadata from the active Flask session."""

from __future__ import annotations

from datetime import datetime, timezone

from flask import request, session


def export_actor() -> dict:
    """Current user and scope for PDF exports and audit rows."""
    user_id = session.get("user_id")
    try:
        user_id = int(user_id) if user_id is not None else None
    except (TypeError, ValueError):
        user_id = None
    buildings = session.get("allowed_buildings") or []
    return {
        "username": str(session.get("username") or "unknown"),
        "user_id": user_id,
        "role": str(session.get("role") or ""),
        "building_scope": [str(b) for b in buildings if str(b).strip()],
        "ip": (request.remote_addr or "").strip(),
    }


def build_pdf_subtitle(scope_note: str, actor: dict | None = None) -> str:
    """Subtitle line shown on exported PDFs."""
    actor = actor or export_actor()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    username = actor.get("username") or "unknown"
    role = str(actor.get("role") or "").strip()
    who = f"{username} ({role})" if role else username
    parts = [scope_note, f"Exported by {who}", f"Generated {stamp}"]
    scope = actor.get("building_scope") or []
    if scope:
        parts.insert(1, f"Building scope: {', '.join(scope)}")
    return " · ".join(parts)

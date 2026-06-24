"""SQLite audit log for PDF export events."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

DEFAULT_AUDIT_DB = os.path.join("data", "audit", "events.db")

EXPORT_EVENT_TYPES = (
    "export.pdf.replacement",
    "export.pdf.orders",
    "export.pdf.requests",
    "export.pdf.overview",
)


def resolve_audit_db_path() -> str:
    env_path = os.getenv("AUDIT_DB_PATH", "").strip()
    return env_path or DEFAULT_AUDIT_DB


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def init_audit_db(db_path: str | None = None) -> None:
    """Create export audit tables if missing."""
    path = db_path or resolve_audit_db_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with _connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS export_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                event_type TEXT NOT NULL,
                username TEXT NOT NULL,
                user_id INTEGER,
                role TEXT,
                month_key TEXT,
                filters_json TEXT,
                row_count INTEGER,
                building_scope_json TEXT,
                status TEXT NOT NULL CHECK(status IN ('ok', 'fail')),
                error_message TEXT,
                ip TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_export_events_created_at "
            "ON export_events (created_at DESC)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_export_events_username "
            "ON export_events (username)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_export_events_event_type "
            "ON export_events (event_type)"
        )


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def log_pdf_export(
    *,
    event_type: str,
    status: str,
    username: str,
    user_id: int | None = None,
    role: str = "",
    month_key: str = "",
    filters: dict | None = None,
    row_count: int | None = None,
    building_scope: list | None = None,
    error_message: str = "",
    ip: str = "",
    db_path: str | None = None,
) -> int:
    """Append one PDF export audit row. Returns the new row id."""
    if event_type not in EXPORT_EVENT_TYPES:
        raise ValueError(f"Unknown export event type: {event_type}")
    if status not in ("ok", "fail"):
        raise ValueError(f"Invalid export status: {status}")

    path = db_path or resolve_audit_db_path()
    init_audit_db(path)
    filters_json = _json_dumps(filters or {})
    building_scope_json = _json_dumps(building_scope or [])
    with _connect(path) as conn:
        cur = conn.execute(
            """
            INSERT INTO export_events (
                event_type, username, user_id, role, month_key,
                filters_json, row_count, building_scope_json,
                status, error_message, ip
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_type,
                username,
                user_id,
                role or None,
                month_key or None,
                filters_json,
                row_count,
                building_scope_json,
                status,
                (error_message or None),
                (ip or None),
            ),
        )
        return int(cur.lastrowid)


def list_export_events(
    *,
    limit: int = 200,
    offset: int = 0,
    db_path: str | None = None,
) -> list[dict]:
    """Return recent export events (newest first) for a future admin panel."""
    path = db_path or resolve_audit_db_path()
    if not os.path.isfile(path):
        return []
    limit = max(1, min(int(limit), 1000))
    offset = max(0, int(offset))
    with _connect(path) as conn:
        rows = conn.execute(
            """
            SELECT
                id, created_at, event_type, username, user_id, role,
                month_key, filters_json, row_count, building_scope_json,
                status, error_message, ip
            FROM export_events
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
    out: list[dict] = []
    for row in rows:
        rec = dict(row)
        try:
            rec["filters"] = json.loads(rec.pop("filters_json") or "{}")
        except json.JSONDecodeError:
            rec["filters"] = {}
            rec.pop("filters_json", None)
        try:
            rec["building_scope"] = json.loads(rec.pop("building_scope_json") or "[]")
        except json.JSONDecodeError:
            rec["building_scope"] = []
            rec.pop("building_scope_json", None)
        out.append(rec)
    return out

"""SQLite-backed auth storage for admin-only MVP."""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass

from werkzeug.security import check_password_hash, generate_password_hash


DEFAULT_AUTH_DB = os.path.join("data", "auth", "users.db")


@dataclass(frozen=True)
class AuthUser:
    id: int
    username: str
    role: str
    is_active: bool


def resolve_auth_db_path() -> str:
    """Resolve auth DB path from env or project default."""
    env_path = os.getenv("AUTH_DB_PATH", "").strip()
    return env_path or DEFAULT_AUTH_DB


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def init_auth_db(db_path: str) -> None:
    """Create users table if missing."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin')),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_login_at TEXT
            )
            """
        )
        conn.commit()


def upsert_admin(db_path: str, username: str, password: str) -> None:
    """Create or update an admin account."""
    username = (username or "").strip()
    if not username:
        raise ValueError("username cannot be empty")
    if not password:
        raise ValueError("password cannot be empty")

    pwd_hash = generate_password_hash(password)
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO users (username, password_hash, role, is_active)
            VALUES (?, ?, 'admin', 1)
            ON CONFLICT(username) DO UPDATE SET
                password_hash=excluded.password_hash,
                role='admin',
                is_active=1
            """,
            (username, pwd_hash),
        )
        conn.commit()


def verify_admin_credentials(db_path: str, username: str, password: str) -> AuthUser | None:
    """Return user when admin credentials are valid and active."""
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, username, role, is_active, password_hash
            FROM users
            WHERE username = ?
            """,
            ((username or "").strip(),),
        ).fetchone()
        if row is None:
            return None
        if int(row["is_active"]) != 1:
            return None
        if row["role"] != "admin":
            return None
        if not check_password_hash(row["password_hash"], password or ""):
            return None
        conn.execute(
            "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?",
            (int(row["id"]),),
        )
        conn.commit()
        return AuthUser(
            id=int(row["id"]),
            username=str(row["username"]),
            role=str(row["role"]),
            is_active=bool(row["is_active"]),
        )

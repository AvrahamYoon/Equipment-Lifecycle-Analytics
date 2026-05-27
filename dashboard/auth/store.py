"""SQLite-backed auth storage for dashboard authentication."""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass

from werkzeug.security import check_password_hash, generate_password_hash


DEFAULT_AUTH_DB = os.path.join("data", "auth", "users.db")
VALID_ROLES = ("admin", "co-admin", "user")


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
    """Create users table if missing and migrate legacy admin-only role check."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if row is not None:
            sql = (row["sql"] or "").lower()
            if "check(role in ('admin'))" in sql:
                conn.execute("ALTER TABLE users RENAME TO users_old")
                conn.execute(
                    """
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL CHECK(role IN ('admin','co-admin','user')),
                        is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        last_login_at TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO users (id, username, password_hash, role, is_active, created_at, last_login_at)
                    SELECT id, username, password_hash, role, is_active, created_at, last_login_at
                    FROM users_old
                    """
                )
                conn.execute("DROP TABLE users_old")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin','co-admin','user')),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_login_at TEXT
            )
            """
        )
        conn.commit()


def upsert_admin(db_path: str, username: str, password: str) -> None:
    """Create or update an admin account (role is always 'admin')."""
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


def upsert_user(db_path: str, username: str, password: str, role: str, is_active: bool = True) -> None:
    """Create or update any user role."""
    username = (username or "").strip()
    role = (role or "").strip().lower()
    if not username:
        raise ValueError("username cannot be empty")
    if not password:
        raise ValueError("password cannot be empty")
    if role not in VALID_ROLES:
        raise ValueError(f"invalid role: {role}")
    pwd_hash = generate_password_hash(password)
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO users (username, password_hash, role, is_active)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password_hash=excluded.password_hash,
                role=excluded.role,
                is_active=excluded.is_active
            """,
            (username, pwd_hash, role, 1 if is_active else 0),
        )
        conn.commit()

def list_users(db_path: str) -> list[dict]:
    """List all users for admin management UI."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, username, role, is_active, created_at, last_login_at
            FROM users
            ORDER BY id ASC
            """
        ).fetchall()
    return [
        {
            "id": int(r["id"]),
            "username": str(r["username"]),
            "role": str(r["role"]),
            "is_active": bool(r["is_active"]),
            "created_at": str(r["created_at"]) if r["created_at"] is not None else "",
            "last_login_at": str(r["last_login_at"]) if r["last_login_at"] is not None else "",
        }
        for r in rows
    ]


def _count_active_users(db_path: str) -> int:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM users WHERE is_active = 1").fetchone()
    return int(row["n"])


def _count_active_admins(db_path: str) -> int:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM users WHERE is_active = 1 AND role = 'admin'"
        ).fetchone()
    return int(row["n"])


def set_user_active(db_path: str, user_id: int, is_active: bool) -> None:
    """Enable/disable a user.

    MVP safety: don't allow disabling the last active admin.
    """
    user_id = int(user_id)
    is_active_i = 1 if is_active else 0
    with _connect(db_path) as conn:
        current = conn.execute(
            "SELECT id, role, is_active FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if current is None:
            raise ValueError("user not found")
        current_active = int(current["is_active"]) == 1
        current_role = str(current["role"] or "")
        if current_active and not is_active and current_role == "admin":
            admin_count = _count_active_admins(db_path)
            if admin_count <= 1:
                raise ValueError("Cannot disable the last active admin.")
        conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (is_active_i, user_id))
        conn.commit()


def set_user_password(db_path: str, user_id: int, password: str) -> None:
    """Reset a user's password (admin-only MVP)."""
    user_id = int(user_id)
    password = password or ""
    if not password:
        raise ValueError("password cannot be empty")
    pwd_hash = generate_password_hash(password)
    with _connect(db_path) as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pwd_hash, user_id))
        conn.commit()


def set_user_role(db_path: str, user_id: int, role: str) -> None:
    """Update role for one user."""
    user_id = int(user_id)
    role = (role or "").strip().lower()
    if role not in VALID_ROLES:
        raise ValueError(f"invalid role: {role}")
    with _connect(db_path) as conn:
        current = conn.execute("SELECT role, is_active FROM users WHERE id = ?", (user_id,)).fetchone()
        if current is None:
            raise ValueError("user not found")
        current_role = str(current["role"] or "")
        current_active = int(current["is_active"]) == 1
        if current_role == "admin" and role != "admin" and current_active:
            admin_count = _count_active_admins(db_path)
            if admin_count <= 1:
                raise ValueError("Cannot downgrade the last active admin.")
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        conn.commit()


def verify_credentials(db_path: str, username: str, password: str) -> AuthUser | None:
    """Return user when credentials are valid and active."""
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


def verify_admin_credentials(db_path: str, username: str, password: str) -> AuthUser | None:
    """Backward-compatible alias."""
    return verify_credentials(db_path, username, password)

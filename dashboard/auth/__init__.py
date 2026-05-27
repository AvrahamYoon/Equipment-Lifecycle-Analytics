"""Authentication helpers for dashboard app."""

from dashboard.auth.store import init_auth_db, resolve_auth_db_path, upsert_admin, verify_admin_credentials
from dashboard.auth.web import configure_auth

__all__ = [
    "configure_auth",
    "init_auth_db",
    "resolve_auth_db_path",
    "upsert_admin",
    "verify_admin_credentials",
]

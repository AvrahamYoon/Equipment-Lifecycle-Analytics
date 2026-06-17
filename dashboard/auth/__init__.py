"""Authentication helpers for dashboard app."""

from dashboard.auth.store import (
    delete_user,
    get_user_scopes,
    init_auth_db,
    set_user_scopes,
    resolve_auth_db_path,
    upsert_admin,
    upsert_user,
    verify_admin_credentials,
    verify_credentials,
    list_users,
    set_user_active,
    set_user_password,
    set_user_role,
)
from dashboard.auth.web import configure_auth

__all__ = [
    "configure_auth",
    "delete_user",
    "get_user_scopes",
    "init_auth_db",
    "set_user_scopes",
    "resolve_auth_db_path",
    "upsert_admin",
    "upsert_user",
    "verify_admin_credentials",
    "verify_credentials",
    "list_users",
    "set_user_active",
    "set_user_password",
    "set_user_role",
]

"""Flask routes and request guard for dashboard authentication."""

from __future__ import annotations

import os
from html import escape
from urllib.parse import quote

from dash import Dash
from flask import redirect, request, session

from dashboard.auth.store import init_auth_db, resolve_auth_db_path, verify_credentials

_PUBLIC_PATH_PREFIXES = (
    "/login",
    "/assets/",
    "/favicon.ico",
)


def _is_authenticated() -> bool:
    return bool(session.get("user_id")) and bool(session.get("role"))


def _is_public_path(path: str) -> bool:
    return any(path == p or path.startswith(p) for p in _PUBLIC_PATH_PREFIXES)


def _login_html(error_msg: str = "") -> str:
    safe_err = escape(error_msg or "")
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Dashboard Login</title>
    <style>
      body {{
        margin: 0;
        font-family: "Segoe UI", Arial, sans-serif;
        background: #eef2f7;
        color: #0f172a;
        min-height: 100vh;
        display: grid;
        place-items: center;
      }}
      .card {{
        width: min(420px, 92vw);
        background: #fff;
        border-radius: 14px;
        box-shadow: 0 16px 40px -20px rgba(15, 23, 42, 0.45);
        padding: 22px 22px 18px;
        border: 1px solid #e2e8f0;
      }}
      h1 {{
        margin: 0 0 14px;
        font-size: 22px;
      }}
      .muted {{
        color: #475569;
        font-size: 13px;
        margin: 0 0 16px;
      }}
      label {{
        display: block;
        font-size: 12px;
        font-weight: 600;
        color: #64748b;
        margin: 12px 0 6px;
      }}
      input {{
        width: 100%;
        box-sizing: border-box;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 10px 12px;
        font-size: 14px;
      }}
      button {{
        margin-top: 14px;
        width: 100%;
        border: 0;
        border-radius: 10px;
        padding: 11px 12px;
        background: #2563eb;
        color: #fff;
        font-size: 14px;
        font-weight: 700;
        cursor: pointer;
      }}
      .error {{
        margin: 0 0 8px;
        color: #b91c1c;
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 10px;
        padding: 8px 10px;
        font-size: 13px;
      }}
    </style>
  </head>
  <body>
    <form class="card" method="post" action="/login">
      <h1>Sign in</h1>
      <p class="muted">Sign in to access Equipment Lifecycle Analytics.</p>
      {"<p class='error'>" + safe_err + "</p>" if safe_err else ""}
      <label for="username">Username</label>
      <input id="username" name="username" autocomplete="username" required />
      <label for="password">Password</label>
      <input id="password" name="password" type="password" autocomplete="current-password" required />
      <input type="hidden" name="next" value="{escape(request.args.get("next", "/"))}" />
      <button type="submit">Sign in</button>
    </form>
  </body>
</html>
"""


def configure_auth(app: Dash) -> None:
    """Attach auth DB initialization, login/logout routes, and request guard."""
    db_path = resolve_auth_db_path()
    init_auth_db(db_path)

    server = app.server
    server.config["SECRET_KEY"] = os.getenv("DASHBOARD_SECRET_KEY", "change-me-in-env")
    server.config["SESSION_COOKIE_HTTPONLY"] = True
    server.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    server.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"

    @server.before_request
    def _auth_guard():
        path = request.path or "/"
        if _is_public_path(path):
            return None
        if _is_authenticated():
            if path.startswith("/admin") and session.get("role") != "admin":
                return redirect("/")
            return None
        next_path = quote(path, safe="/?=&")
        return redirect(f"/login?next={next_path}")

    @server.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return _login_html(request.args.get("error", ""))

        username = request.form.get("username", "")
        password = request.form.get("password", "")
        next_path = request.form.get("next", "/")
        user = verify_credentials(db_path, username, password)
        if user is None:
            return _login_html("Invalid username or password.")

        session.clear()
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role
        if not str(next_path).startswith("/"):
            next_path = "/"
        return redirect(next_path)

    @server.route("/logout", methods=["GET"])
    def logout():
        session.clear()
        return redirect("/login")

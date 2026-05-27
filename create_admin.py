"""Bootstrap or rotate the admin account for dashboard auth."""

from __future__ import annotations

import argparse

from dashboard.auth import init_auth_db, resolve_auth_db_path, upsert_admin

def _args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create/update dashboard admin credentials.")
    p.add_argument("--username", default=DEFAULT_ADMIN_USERNAME, help="Admin username")
    p.add_argument("--password", default="", help="Admin password (omit to prompt securely)")
    p.add_argument(
        "--use-default-password",
        action="store_true",
        help=f"Use built-in default password ({DEFAULT_ADMIN_PASSWORD}) without prompt",
    )
    return p.parse_args()


def main() -> None:
    args = _args()
    password = args.password
    if args.use_default_password and not password:
        password = DEFAULT_ADMIN_PASSWORD
    elif not password:
        # MVP convenience: running without args creates/updates default admin credentials.
        password = DEFAULT_ADMIN_PASSWORD

    db_path = resolve_auth_db_path()
    init_auth_db(db_path)
    upsert_admin(db_path, args.username, password)
    print(f"Admin user '{args.username}' created/updated in {db_path}")


if __name__ == "__main__":
    main()

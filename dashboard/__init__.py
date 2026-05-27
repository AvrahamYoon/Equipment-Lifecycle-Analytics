"""Work order dashboard package."""

__all__ = ["create_app"]


def create_app():
    """Lazy import to avoid loading heavy app deps at package import time."""
    from dashboard.app import create_app as _create_app

    return _create_app()

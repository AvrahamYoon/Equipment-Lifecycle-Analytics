"""Shared Kaleido / Chromium setup for Overview chart PNG export.

Kaleido v1+ starts a fresh Chrome process on every ``to_image`` call unless a
sync server is running. Overview exports ~9 charts, so without reuse exports
take ~1 minute and are more likely to fail on locked-down machines.
"""

from __future__ import annotations

import atexit
import logging
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import plotly.graph_objects as go

_log = logging.getLogger(__name__)

_lock = threading.Lock()
_chrome_ready = False
_server_started = False

KALEIDO_SETUP_HINT = (
    "Overview PDF needs Kaleido and a one-time Chromium download.\n"
    "1) pip install kaleido reportlab\n"
    "2) python -m dashboard.export.kaleido_render\n"
    "3) Restart the dashboard and try Export PDF report again.\n"
    "The setup step needs internet access on each machine (once per user)."
)


class KaleidoNotReadyError(RuntimeError):
    """Raised when chart PNG export cannot start Chromium."""


def ensure_kaleido_ready(*, prewarm_server: bool = False) -> None:
    """Download Chromium if needed and optionally keep Kaleido's sync server up."""
    global _chrome_ready, _server_started
    with _lock:
        try:
            import kaleido
        except ImportError as exc:
            raise KaleidoNotReadyError(
                "Python package 'kaleido' is not installed. "
                f"Run: pip install kaleido\n\n{KALEIDO_SETUP_HINT}"
            ) from exc

        if not _chrome_ready:
            try:
                kaleido.get_chrome_sync(verbose=False)
            except Exception as exc:
                raise KaleidoNotReadyError(
                    "Could not download or locate Chromium for Kaleido. "
                    f"Run: python -m dashboard.export.kaleido_render\n\n{KALEIDO_SETUP_HINT}"
                ) from exc
            _chrome_ready = True
            _log.info("Kaleido Chromium is ready.")

        if prewarm_server and not _server_started:
            kaleido.start_sync_server(silence_warnings=True)
            _server_started = True
            _log.info("Kaleido sync server started for faster chart export.")


def render_figure_png(
    fig: go.Figure,
    *,
    width: int,
    height: int,
    scale: int = 1,
) -> bytes:
    """Render one Plotly figure to PNG bytes using a shared Kaleido server."""
    ensure_kaleido_ready(prewarm_server=True)
    return fig.to_image(format="png", width=width, height=height, scale=scale)


def render_figures_batch(
    figures: list[tuple[go.Figure, int, int]],
    *,
    scale: int = 1,
) -> list[bytes]:
    """Render multiple figures in one Kaleido session (much faster than one-by-one)."""
    ensure_kaleido_ready(prewarm_server=True)
    out: list[bytes] = []
    for fig, width, height in figures:
        out.append(render_figure_png(fig, width=width, height=height, scale=scale))
    return out


def _stop_sync_server() -> None:
    global _server_started
    if not _server_started:
        return
    try:
        import kaleido

        kaleido.stop_sync_server()
    except Exception:
        pass
    finally:
        _server_started = False


atexit.register(_stop_sync_server)


def warm_kaleido(*, verbose: bool = True) -> None:
    """CLI / startup helper: install Chromium and start the sync server once."""
    ensure_kaleido_ready(prewarm_server=True)
    if verbose:
        print("Kaleido is ready for Overview PDF export.")


if __name__ == "__main__":
    warm_kaleido(verbose=True)

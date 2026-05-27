"""
Entry point for the Dash app. Implementation lives in the `dashboard/` package.
Run from project root:  python work_order_dashboard.py
"""

import argparse
import socket

from dashboard.app import create_app

app = create_app()


def _args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run Equipment Lifecycle Analytics dashboard.")
    p.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    p.add_argument("--port", type=int, default=8050, help="Bind port (default: 8050)")
    p.add_argument("--debug", action="store_true", help="Enable Dash debug mode")
    return p.parse_args()


def _resolve_lan_ip() -> str:
    """Best-effort local LAN IP detection."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No traffic is sent; this only asks OS for the selected outbound iface.
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    args = _args()
    lan_ip = _resolve_lan_ip()
    print(f"Local access: http://127.0.0.1:{args.port}")
    print(f"LAN access:   http://{lan_ip}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)

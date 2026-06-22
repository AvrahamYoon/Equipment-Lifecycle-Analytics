"""Flask download routes for table PDF exports."""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from html import escape

from dash import Dash
from flask import Response, abort, request

from dashboard import constants as C
from dashboard.data_loaders import df_req, df_repairs, df_service
from dashboard.export.kaleido_render import KALEIDO_SETUP_HINT, KaleidoNotReadyError, warm_kaleido
from dashboard.export.overview_pdf import build_overview_pdf
from dashboard.export.pdf_tables import build_table_pdf
from dashboard.export.settings_codec import decode_settings
from dashboard.logic.repair_orders_table import build_repair_orders_table
from dashboard.logic.replacement_table import build_replacement_table
from dashboard.logic.request_roster_table import build_request_roster_table
from dashboard.logic.service_scope import prepare_service_for_display
from dashboard.session_scope import allowed_reports_for_session, apply_building_scope

_log = logging.getLogger(__name__)


def _arg(name: str, default: str = "") -> str:
    return (request.args.get(name) or default).strip()


def _month_label(month_key: str) -> str:
    if C.is_all_months(month_key):
        return C.ALL_MONTHS_LABEL
    return month_key or C.ALL_MONTHS_LABEL


def _pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _generated_subtitle(scope_note: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"{scope_note} · Generated {stamp}"


def _kaleido_error_html(message: str) -> str:
    safe = escape(message)
    hint = escape(KALEIDO_SETUP_HINT)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8" /><title>Overview PDF export</title>
<style>
body {{ font-family: "Segoe UI", Arial, sans-serif; margin: 2rem; color: #0f172a; max-width: 640px; }}
h1 {{ font-size: 1.25rem; }}
pre {{ white-space: pre-wrap; background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 8px; }}
a {{ color: #2563eb; }}
</style></head><body>
<h1>Overview PDF export is not ready on this computer</h1>
<p>{safe}</p>
<pre>{hint}</pre>
<p><a href="/">Back to dashboard</a></p>
</body></html>"""


def configure_exports(app: Dash) -> None:
    """Register ``/export/*.pdf`` routes on the Dash Flask server."""
    server = app.server

    def _prewarm_kaleido() -> None:
        try:
            warm_kaleido(verbose=False)
            _log.info("Kaleido prewarmed for Overview PDF export.")
        except KaleidoNotReadyError as exc:
            _log.warning("Kaleido prewarm skipped: %s", exc)
        except Exception as exc:
            _log.warning("Kaleido prewarm failed: %s", exc)

    threading.Thread(target=_prewarm_kaleido, daemon=True, name="kaleido-prewarm").start()

    @server.route("/export/replacement.pdf")
    def export_replacement_pdf():
        if "replacement" not in allowed_reports_for_session():
            abort(403)

        rep = df_repairs[df_repairs["month_key"].astype(str) != "NaT"]
        rep = apply_building_scope(rep)
        filters = {
            "status": _arg("status", "All"),
            "category": _arg("category"),
            "building": _arg("building"),
            "repair_count_bin": _arg("repair_count_bin"),
            "equipment_substr": _arg("equipment"),
            "id_substr": _arg("id"),
        }
        _cols, records, _cond = build_replacement_table(rep, None, filters)
        subtitle = _generated_subtitle("Cumulative across all loaded repair months")
        pdf = build_table_pdf(
            "Equipment Replacement",
            subtitle,
            _cols,
            records,
            landscape_page=True,
        )
        return _pdf_response(pdf, "replacement.pdf")

    @server.route("/export/orders.pdf")
    def export_orders_pdf():
        if "orders" not in allowed_reports_for_session():
            abort(403)

        month_key = _arg("month", C.ALL_MONTHS_KEY)
        if C.is_all_months(month_key):
            svc = df_service[df_service["month_key"].astype(str) != "NaT"]
        else:
            svc = df_service[df_service["month_key"] == month_key]
        svc = apply_building_scope(svc)
        svc = prepare_service_for_display(svc, month_key, df_service)
        filters = {
            "category": _arg("category"),
            "status_substr": _arg("status"),
            "equipment_substr": _arg("equipment"),
            "id_substr": _arg("id"),
        }
        cols, records, _cond = build_repair_orders_table(svc, filters)
        subtitle = _generated_subtitle(f"Month: {_month_label(month_key)}")
        pdf = build_table_pdf(
            "Order Roster",
            subtitle,
            cols,
            records,
            landscape_page=True,
        )
        return _pdf_response(pdf, "orders.pdf")

    @server.route("/export/requests.pdf")
    def export_requests_pdf():
        if "overview" not in allowed_reports_for_session():
            abort(403)

        month_key = _arg("month", C.ALL_MONTHS_KEY)
        if C.is_all_months(month_key):
            req = df_req[df_req["month_key"].astype(str) != "NaT"]
        else:
            req = df_req[df_req["month_key"] == month_key]
        req = apply_building_scope(req)
        filters = {
            "day": _arg("day"),
            "work_order_substr": _arg("work_order"),
            "requestor_substr": _arg("requestor"),
            "request_substr": _arg("request"),
        }
        cols, records, _cond = build_request_roster_table(req, filters)
        subtitle = _generated_subtitle(f"Month: {_month_label(month_key)}")
        pdf = build_table_pdf(
            "Request Roster",
            subtitle,
            cols,
            records,
            landscape_page=False,
        )
        return _pdf_response(pdf, "requests.pdf")

    @server.route("/export/overview.pdf")
    def export_overview_pdf():
        if "overview" not in allowed_reports_for_session():
            abort(403)

        month_key = _arg("month", C.ALL_MONTHS_KEY)
        settings = decode_settings(_arg("settings"))
        try:
            pdf = build_overview_pdf(month_key, settings)
        except KaleidoNotReadyError as exc:
            return Response(_kaleido_error_html(str(exc)), status=503, mimetype="text/html")
        except Exception as exc:
            _log.exception("Overview PDF export failed")
            return Response(
                _kaleido_error_html(f"Unexpected error while building the report: {exc}"),
                status=500,
                mimetype="text/html",
            )
        label = "all-months" if C.is_all_months(month_key) else month_key.replace("/", "-")
        return _pdf_response(pdf, f"overview-{label}.pdf")

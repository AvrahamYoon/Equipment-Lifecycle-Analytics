"""Flask download routes for table PDF exports."""

from __future__ import annotations

import logging
import threading
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
from dashboard.audit import init_audit_db, log_pdf_export
from dashboard.export.meta import build_pdf_subtitle, export_actor

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


def _audit_pdf_export(
    event_type: str,
    *,
    actor: dict,
    month_key: str = "",
    filters: dict | None = None,
    row_count: int | None = None,
    status: str,
    error_message: str = "",
) -> None:
    try:
        log_pdf_export(
            event_type=event_type,
            status=status,
            username=actor["username"],
            user_id=actor.get("user_id"),
            role=actor.get("role", ""),
            month_key=month_key,
            filters=filters,
            row_count=row_count,
            building_scope=actor.get("building_scope"),
            error_message=error_message,
            ip=actor.get("ip", ""),
        )
    except Exception:
        _log.exception("Failed to write PDF export audit event (%s)", event_type)


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
    init_audit_db()

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
        actor = export_actor()
        if "replacement" not in allowed_reports_for_session():
            _audit_pdf_export(
                "export.pdf.replacement",
                actor=actor,
                status="fail",
                error_message="forbidden",
            )
            abort(403)

        filters = {
            "status": _arg("status", "All"),
            "category": _arg("category"),
            "building": _arg("building"),
            "repair_count_bin": _arg("repair_count_bin"),
            "equipment_substr": _arg("equipment"),
            "id_substr": _arg("id"),
        }
        try:
            rep = df_repairs[df_repairs["month_key"].astype(str) != "NaT"]
            rep = apply_building_scope(rep)
            _cols, records, _cond = build_replacement_table(rep, None, filters)
            subtitle = build_pdf_subtitle(
                "Cumulative across all loaded repair months",
                actor,
            )
            pdf = build_table_pdf(
                "Equipment Replacement",
                subtitle,
                _cols,
                records,
                landscape_page=True,
            )
            _audit_pdf_export(
                "export.pdf.replacement",
                actor=actor,
                filters=filters,
                row_count=len(records),
                status="ok",
            )
            return _pdf_response(pdf, "replacement.pdf")
        except Exception as exc:
            _log.exception("Replacement PDF export failed")
            _audit_pdf_export(
                "export.pdf.replacement",
                actor=actor,
                filters=filters,
                status="fail",
                error_message=str(exc),
            )
            raise

    @server.route("/export/orders.pdf")
    def export_orders_pdf():
        actor = export_actor()
        if "orders" not in allowed_reports_for_session():
            _audit_pdf_export(
                "export.pdf.orders",
                actor=actor,
                status="fail",
                error_message="forbidden",
            )
            abort(403)

        month_key = _arg("month", C.ALL_MONTHS_KEY)
        filters = {
            "category": _arg("category"),
            "status_substr": _arg("status"),
            "equipment_substr": _arg("equipment"),
            "id_substr": _arg("id"),
        }
        try:
            if C.is_all_months(month_key):
                svc = df_service[df_service["month_key"].astype(str) != "NaT"]
            else:
                svc = df_service[df_service["month_key"] == month_key]
            svc = apply_building_scope(svc)
            svc = prepare_service_for_display(svc, month_key, df_service)
            cols, records, _cond = build_repair_orders_table(svc, filters)
            subtitle = build_pdf_subtitle(f"Month: {_month_label(month_key)}", actor)
            pdf = build_table_pdf(
                "Order Roster",
                subtitle,
                cols,
                records,
                landscape_page=True,
            )
            _audit_pdf_export(
                "export.pdf.orders",
                actor=actor,
                month_key=month_key,
                filters=filters,
                row_count=len(records),
                status="ok",
            )
            return _pdf_response(pdf, "orders.pdf")
        except Exception as exc:
            _log.exception("Orders PDF export failed")
            _audit_pdf_export(
                "export.pdf.orders",
                actor=actor,
                month_key=month_key,
                filters=filters,
                status="fail",
                error_message=str(exc),
            )
            raise

    @server.route("/export/requests.pdf")
    def export_requests_pdf():
        actor = export_actor()
        if "overview" not in allowed_reports_for_session():
            _audit_pdf_export(
                "export.pdf.requests",
                actor=actor,
                status="fail",
                error_message="forbidden",
            )
            abort(403)

        month_key = _arg("month", C.ALL_MONTHS_KEY)
        filters = {
            "day": _arg("day"),
            "work_order_substr": _arg("work_order"),
            "requestor_substr": _arg("requestor"),
            "request_substr": _arg("request"),
        }
        try:
            if C.is_all_months(month_key):
                req = df_req[df_req["month_key"].astype(str) != "NaT"]
            else:
                req = df_req[df_req["month_key"] == month_key]
            req = apply_building_scope(req)
            cols, records, _cond = build_request_roster_table(req, filters)
            subtitle = build_pdf_subtitle(f"Month: {_month_label(month_key)}", actor)
            pdf = build_table_pdf(
                "Request Roster",
                subtitle,
                cols,
                records,
                landscape_page=False,
            )
            _audit_pdf_export(
                "export.pdf.requests",
                actor=actor,
                month_key=month_key,
                filters=filters,
                row_count=len(records),
                status="ok",
            )
            return _pdf_response(pdf, "requests.pdf")
        except Exception as exc:
            _log.exception("Requests PDF export failed")
            _audit_pdf_export(
                "export.pdf.requests",
                actor=actor,
                month_key=month_key,
                filters=filters,
                status="fail",
                error_message=str(exc),
            )
            raise

    @server.route("/export/overview.pdf")
    def export_overview_pdf():
        actor = export_actor()
        if "overview" not in allowed_reports_for_session():
            _audit_pdf_export(
                "export.pdf.overview",
                actor=actor,
                status="fail",
                error_message="forbidden",
            )
            abort(403)

        month_key = _arg("month", C.ALL_MONTHS_KEY)
        settings = decode_settings(_arg("settings"))
        filters = {"settings": settings}
        subtitle = build_pdf_subtitle(f"Scope: {_month_label(month_key)}", actor)
        try:
            pdf = build_overview_pdf(month_key, settings, pdf_subtitle=subtitle)
            _audit_pdf_export(
                "export.pdf.overview",
                actor=actor,
                month_key=month_key,
                filters=filters,
                status="ok",
            )
            label = "all-months" if C.is_all_months(month_key) else month_key.replace("/", "-")
            return _pdf_response(pdf, f"overview-{label}.pdf")
        except KaleidoNotReadyError as exc:
            _audit_pdf_export(
                "export.pdf.overview",
                actor=actor,
                month_key=month_key,
                filters=filters,
                status="fail",
                error_message=str(exc),
            )
            return Response(_kaleido_error_html(str(exc)), status=503, mimetype="text/html")
        except Exception as exc:
            _log.exception("Overview PDF export failed")
            _audit_pdf_export(
                "export.pdf.overview",
                actor=actor,
                month_key=month_key,
                filters=filters,
                status="fail",
                error_message=str(exc),
            )
            return Response(
                _kaleido_error_html(f"Unexpected error while building the report: {exc}"),
                status=500,
                mimetype="text/html",
            )

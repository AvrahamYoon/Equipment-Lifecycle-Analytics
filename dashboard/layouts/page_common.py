"""Shared layout fragments used by page body modules."""

from dash import dcc, html

from dashboard import constants as C


def table_info_bar(
    row_count_id: str,
    page_size_id: str,
    item_label: str = "rows",
    export_link_id: str | None = None,
):
    actions = []
    if export_link_id:
        actions.append(
            html.A(
                "Export PDF",
                id=export_link_id,
                href="#",
                target="_blank",
                className="pdf-export-link",
                title="Download the current filtered table as PDF",
            )
        )
    actions.append(
        html.Div(
            [
                html.Span("Rows per page", className="page-size-caption"),
                dcc.RadioItems(
                    id=page_size_id,
                    options=C.PAGE_SIZE_OPTIONS,
                    value=C.DEFAULT_PAGE_SIZE,
                    inline=True,
                    className="page-size-radio",
                    labelClassName="page-size-radio-label",
                    inputClassName="page-size-radio-input",
                    labelStyle={},
                ),
            ],
            className="page-size-wrap",
        )
    )
    return html.Div(
        [
            html.Div(
                f"Showing 0 of 0 {item_label}",
                id=row_count_id,
                className="row-count",
            ),
            html.Div(actions, className="table-info-bar-actions"),
        ],
        className="table-info-bar",
    )

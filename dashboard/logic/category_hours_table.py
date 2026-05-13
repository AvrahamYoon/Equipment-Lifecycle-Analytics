"""Overview: tabular summary of repair hours by equipment class (same buckets as charts)."""

import pandas as pd

from dashboard import constants as C
from dashboard.taxonomy import equipment_chart_class


def build_category_hours_table(rep: pd.DataFrame):
    """Returns (columns, records) for Dash DataTable."""
    hours_map: dict[str, float] = {}
    for _, row in rep.iterrows():
        eq = equipment_chart_class(str(row["equipment"]))
        hours_map[eq] = hours_map.get(eq, 0.0) + float(row.get("hours", 0) or 0)

    keys = sorted(
        hours_map.keys(),
        key=lambda k: (C.CHART_CLASS_RANK.get(k, len(C.CHART_CLASS_ORDER)), -hours_map[k]),
    )
    records = [
        {"Equipment class": k, "Total repair hours (person-hrs)": f"{hours_map[k]:,.1f}"} for k in keys
    ]
    columns = [
        {"name": "Equipment class", "id": "Equipment class"},
        {"name": "Total repair hours (person-hrs)", "id": "Total repair hours (person-hrs)"},
    ]
    return columns, records

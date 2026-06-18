"""Repair-count bucket labels shared by overview chart and replacement drill-down."""

from __future__ import annotations

import pandas as pd

REPAIR_COUNT_BIN_LABELS = (
    "1 repair",
    "2 repairs",
    "3 repairs",
    "4 repairs",
    "5+ repairs",
)


def repair_count_bin_label(n: int) -> str:
    if n <= 1:
        return "1 repair"
    if n == 2:
        return "2 repairs"
    if n == 3:
        return "3 repairs"
    if n == 4:
        return "4 repairs"
    return "5+ repairs"


def count_matches_bin(count: int, bin_label: str) -> bool:
    label = (bin_label or "").strip()
    if not label:
        return True
    return repair_count_bin_label(int(count)) == label


def equip_ids_for_repair_count_bin(rep: pd.DataFrame, bin_label: str) -> set[str]:
    """Equipment IDs whose repair-row count falls in the given bin."""
    label = (bin_label or "").strip()
    if not label or rep is None or rep.empty:
        return set()

    id_col = "equipIdNorm" if "equipIdNorm" in rep.columns else "equipId"
    if id_col not in rep.columns:
        return set()

    counts = rep.groupby(id_col, dropna=True).size()
    counts = counts[counts.index.astype(str).str.strip() != ""]
    return {str(k) for k, n in counts.items() if count_matches_bin(int(n), label)}

"""DuckDB + SQL file helpers for data loading."""

from __future__ import annotations

import os

import duckdb
import pandas as pd

_SQL_DIR = os.path.join(os.path.dirname(__file__), "sql")


def load_sql(filename: str) -> str:
    path = os.path.join(_SQL_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


def run_csv_sql(sql_filename: str, csv_path: str) -> pd.DataFrame:
    sql = load_sql(sql_filename)
    con = duckdb.connect(database=":memory:")
    try:
        return con.execute(sql, [csv_path]).df()
    finally:
        con.close()


def merge_frames_by_name(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Stack frames with DuckDB UNION ALL BY NAME."""
    if not frames:
        return pd.DataFrame()
    if len(frames) == 1:
        return frames[0].reset_index(drop=True)

    template = load_sql("merge_union_by_name.sql")
    con = duckdb.connect(database=":memory:")
    try:
        names: list[str] = []
        for i, fr in enumerate(frames):
            name = f"_merge_{i}"
            con.register(name, fr)
            names.append(name)
        union_body = " UNION ALL BY NAME ".join(f"SELECT * FROM {n}" for n in names)
        sql = template.replace("{{UNION_BODY}}", union_body)
        return con.execute(sql).df()
    finally:
        con.close()

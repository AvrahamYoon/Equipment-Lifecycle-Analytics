# Equipment Lifecycle Analytics

Python utilities for work-order analytics (Dash dashboard) and equipment list cleanup.

## Layout

| Path | Role |
|------|------|
| `work_order_dashboard.py` | Web app: reads CSVs, month filter, KPIs, charts, replacement table |
| `list_clean.py` | Batch-clean equipment CSVs from `input/` → `Output/` |
| `data/requests/*.csv` | Work **request** exports (same column layout as your source system) |
| `data/service/*.csv` | **Service** order exports |
| `data/repairs/*.csv` | **Repair** work order exports |

Use **any filenames** you like. Every `*.csv` in a folder is loaded and merged; add more files (e.g. one per month) as you go.

## Requirements

```bash
pip install dash pandas plotly
```

Python 3.10+ recommended.

## Run the dashboard

1. Ensure these folders exist and each contains **at least one** `.csv`:
   - `data/requests/`
   - `data/service/`
   - `data/repairs/`
2. From the **project root**:

```bash
python work_order_dashboard.py
```

Open `http://127.0.0.1:8050`.

If startup fails with “No *.csv under …”, create the missing folder or add exports there. Run from the repo root so `data/...` paths resolve.

## Run the equipment cleaner

1. Put raw equipment CSVs in `input/`.
2. Run:

```bash
python list_clean.py
```

Outputs: `Output/<name>_cleaned.csv` and `Output/all_equipment_summary.csv`.

## Replacement rule (dashboard)

- **Replace** if `(labor + parts) * 0.80 >= newPrice`
- **Monitor** if `(labor + parts) * 0.60 >= newPrice`
- **Good** otherwise

`newPrice` is inferred from equipment name (see `load_repairs` in `work_order_dashboard.py`).

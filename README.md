# Equipment Lifecycle Analytics

Python utilities for work-order analytics (Dash dashboard) and equipment list cleanup.

## Layout

| Path | Role |
|------|------|
| `work_order_dashboard.py` | Launches the Dash app (implementation in `dashboard/`) |
| `dashboard/` | App package: `app.py`, `layouts/shell.py` (nav + pages), `callbacks/wiring.py`, `data_loaders.py`, `logic/` (charts + replacement table), `constants.py`, `taxonomy.py`, `calendar_util.py` |
| `list_clean.py` | Batch-clean Compuclean equipment exports: `data/equipment/raw/` → `data/equipment/cleaned/` |
| `data/equipment/raw/*.csv` | **Raw** equipment list downloads (before clean) |
| `data/equipment/cleaned/*.csv` | **Cleaned** per-file outputs + `all_equipment_summary.csv` |
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

Open `http://127.0.0.1:8050`. Use the **left nav**: **Overview** (KPIs + charts) and **Replacement table** (large indicator table on its own page).

If startup fails with “No *.csv under …”, create the missing folder or add exports there. Run from the repo root so `data/...` paths resolve.

## Run the equipment cleaner

1. Put Compuclean equipment exports in `data/equipment/raw/` (any `*.csv` filenames).
2. From the project root:

```bash
python list_clean.py
```

Outputs in `data/equipment/cleaned/`:

- `<original_name>_cleaned.csv` per input file  
- `all_equipment_summary.csv` merged and deduped by `EquipmentId`

## Replacement rule (dashboard)

- **Replace** if `(labor + parts) * 0.80 >= newPrice`
- **Monitor** if `(labor + parts) * 0.60 >= newPrice`
- **Good** otherwise

`newPrice` is inferred from equipment name (see `load_repairs` in `dashboard/data_loaders.py`).

# Equipment Lifecycle Analytics

Python utilities for work-order analytics (Dash dashboard) and equipment list cleanup.

## Layout

| Path | Role |
|------|------|
| `work_order_dashboard.py` | Launches the Dash app (implementation in `dashboard/`) |
| `dashboard/` | App package: `app.py`, `layouts/shell.py`, `callbacks/wiring.py`, `data_loaders.py`, `constants.py`, `taxonomy.py`, `calendar_util.py` |
| `dashboard/logic/overview/` | Overview charts and KPI assembly (`figures.py`, `kpis.py`, `service_prep.py`, `settings_merge.py`) |
| `dashboard/logic/replacement_table.py` | Replacement indicator `DataTable` |
| `dashboard/logic/category_hours_table.py` | Overview summary: repair hours by equipment class |
| `dashboard/logic/repair_orders_table.py` | **Order roster** `DataTable` (service lines + business-day span) |
| `dashboard/logic/overview_charts.py` | Thin re-export of `build_overview` (compat) |
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

Open `http://127.0.0.1:8050`.

### UI

- **Left navigation** (fixed; main content scrolls): **Workspace** — Overview, Replacement (`/replacement`), Order roster (`/orders`); **Preferences** — Settings. Active item is highlighted; sidebar uses a light gradient.
- **Header**: title, subtitle, and **Month** dropdown (filters all pages that use month-scoped data).
- **Overview**: KPI row, charts, then at the **bottom** a **Monthly repair hours by equipment class** table (same classes as the repair-hours chart).
- **Replacement** (`/replacement`): full-width **Equipment Replacement Indicator** — hero card, rule chips, filter toolbar, replacement `DataTable`.
- **Order roster** (`/orders`): full-width service-line roster — hero card, filter toolbar, order `DataTable` (scheduled → completed, business days). Icons for the Order roster nav link and page hero share **Order roster link** in Settings.
- **Settings**: preferences in browser local storage (**Apply** / **Reset**). Icons include **Order roster link** for nav + page title.
  - **Staff capacity**: saved **per calendar month** using the same **Month** control in the header. Pick a month, edit values, Apply. Months without a saved entry use the global defaults (also written on Apply).
  - **Availability model**: base days used in the availability chart.
  - **Request calendar**: week starts on Sunday or Monday.
  - **Icons**: KPI cards, nav links (including Order roster), replacement table badge prefixes, and replacement page title icon.
  - **Data paths** for CSV inputs are not editable in the UI; they are defined in `dashboard/constants.py` (`REQUESTS_DIR`, `SERVICE_DIR`, `REPAIRS_DIR`, `EQUIPMENT_SUMMARY_CSV`). Restart the app after changing paths.

The app is created with `update_title=None` so the browser tab title stays **Work Order Dashboard** instead of Dash’s temporary “Updating…” during callbacks.

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

# Equipment Lifecycle Analytics

Work-order analytics in a Dash dashboard plus an offline pipeline to normalize Compuclean equipment exports. CSVs under `data/` are the source of truth; the app loads them at startup and keeps chart logic in pandas.

## Requirements

```bash
pip install dash pandas plotly duckdb
```

Python 3.10+ recommended.

## Run

**Dashboard** — from the repo root, with at least one `*.csv` in each of `data/requests/`, `data/service/`, and `data/repairs/`:

```bash
python work_order_dashboard.py
```

Open `http://127.0.0.1:8050`. Paths are fixed in `dashboard/constants.py`; change them there and restart. If startup reports a missing folder, create it or add exports. Run from the project root so `data/...` resolves.

**Equipment cleaner** — put Compuclean exports in `data/equipment/raw/`, then:

```bash
python list_clean.py
```

Writes per-file `*_cleaned.csv` and merged `all_equipment_summary.csv` (deduped by `EquipmentId`) under `data/equipment/cleaned/`.

---

## Layout (paths)

| Path | Role |
|------|------|
| `work_order_dashboard.py` | Entry point for the Dash server |
| `dashboard/` | Application package (factory, layout, callbacks, loaders, theme constants, taxonomy helpers, calendar helpers) |
| `dashboard/sql/` | DuckDB SQL used for stacking multi-file exports and for selected `read_csv_auto` reads (wired from `data_loaders.py`) |
| `dashboard/assets/dashboard.css` | Global styles: tables, header/toolbar focus, pills, empty states |
| `dashboard/logic/overview/` | Overview KPIs, Plotly figures, service prep, settings merge |
| `dashboard/logic/replacement_table.py` | Replacement `DataTable` (cumulative repair cost vs. estimated new price) |
| `dashboard/logic/repair_orders_table.py` | Order roster `DataTable` (service lines, business-day span, filters) |
| `dashboard/logic/overview_charts.py` | Compatibility re-export for `build_overview` |
| `list_clean.py` | Batch equipment list cleanup |
| `data/equipment/raw/`, `data/equipment/cleaned/` | Raw exports vs. cleaned outputs and summary |
| `data/requests/`, `data/service/`, `data/repairs/` | Work request, service, and repair CSV exports (any filenames; all `*.csv` in a folder are merged) |

---

## Modules

Each block below is one slice of the codebase; the trickier areas (export formats and loading) get a bit more detail.

### Data loading (`data_loaders.py`, `dashboard/sql/`, `taxonomy.py`)

Repair and request exports often ship with one or more preamble rows before the real header. Loaders scan the raw grid for sentinels (e.g. first-column `#` for repairs, `Work Order #` for requests), then normalize duplicate or blank header cells, map alias column names into stable fields, and coerce dates and numerics. Repair rows without a usable completed date are counted per file and logged so silent parse drift is visible.

After each file is shaped in Python, all CSVs in a folder are stacked with DuckDB (`UNION ALL BY NAME` via `dashboard/sql/merge_union_by_name.sql`) instead of a large `pandas.concat`. Service files and the equipment summary are read through `read_csv_auto` in `dashboard/sql/`; taxonomy helpers (`norm_equip_id`, equipment classes, replacement price hints) still run in Python. Downstream callbacks receive the same pandas `DataFrame` objects as before.

### Application shell (`app.py`, `layouts/shell.py`, `callbacks/wiring.py`)

`create_app` registers callbacks and builds the root layout. The sidebar drives routes (`/`, `/replacement`, `/orders`, settings). Callbacks wire the month selector and `dcc.Store` settings into overview figures, the replacement table, and the order roster; `update_title=None` avoids the browser tab flashing Dash’s default “Updating…” during burst updates.

### Overview (`logic/overview/`)

Assembles KPIs and charts from filtered request, service, and repair frames plus the equipment summary. In **All months** mode the request calendar is replaced by a monthly volume bar chart, staff-capacity “available” hours scale with the number of months in the slice, and the footer summarizes repair and service counts; in a single-month view the day-of-month calendar returns. Staff capacity, availability base days, and week start come from merged settings, including per-month capacity overrides where applicable.

### Replacement and order roster (`replacement_table.py`, `repair_orders_table.py`)

Replacement rolls up **all** loaded repair months by equipment: cumulative labor and parts vs. an estimated new price from the equipment name, with Replace / Monitor / Good thresholds. The order roster lists service lines for the selected month (or all months), with filters and business-day calculations between scheduled and completed dates.

### Styling (`dashboard/assets/dashboard.css`)

Dash loads this automatically. It centralizes table hover, numeric alignment, filter-toolbar focus rings, row-count pills, page-size segments, empty-state panels, and small layout utilities so layouts mostly set `className` instead of duplicating inline style.

### Offline cleaning (`list_clean.py`)

Standalone script: reads raw equipment CSVs, normalizes fields, writes cleaned per-site files, and merges a deduplicated summary used by the dashboard’s availability and equipment-class logic when present.

---

## Dashboard pages (short tour)

- **Overview** — KPI row and charts; respects the header **Month** (or **All months**) and Settings (staff, availability, calendar week start, icons where noted).
- **Replacement** (`/replacement`) — Ignores the month dropdown; always cumulative across every repair file under `data/repairs/`.
- **Order roster** (`/orders`) — Service lines for the selected month scope; filters for class, status, equipment text, and ID.
- **Settings** — Mostly Overview-only; staff capacity can be overridden per calendar month. Preferences persist in the browser (Apply / Reset).

---

## Replacement rule

Per **equipment ID**, let **R** = cumulative labor + parts over **all** repair rows (excluding invalid `NaT` months). Let **N** = estimated new price from the repair loader’s name-based map in `data_loaders.py`. The header month control does **not** change this view.

- **Replace** if **R ≥ 0.80 × N**
- **Monitor** if **0.60 × N ≤ R < 0.80 × N**
- **Good** if **R < 0.60 × N**, or if **N** is missing or not positive

The table labels the 80% and 60% dollar cutoffs next to total cost. To change the time horizon, add or remove files under `data/repairs/` and restart.

---

## CSS building blocks

| Class | What it does |
|-------|----------------|
| `lift-on-hover` | Slight lift and stronger shadow on hover (use next to `CARD_STYLE` cards). |
| `fm-header`, `fm-toolbar` | Scope for header and filter bars: unified focus ring and dropdown menu styling for nested inputs. |
| `row-count` | “Showing X of Y …” pill with a leading dot. |
| `page-size-radio` (+ `page-size-radio-label`, `page-size-radio-input`) | Segmented page-size control from `dcc.RadioItems`. |
| `empty-state` (+ `empty-state-icon`, `empty-state-title`, `empty-state-hint`) | No-results panel; callbacks toggle `display`. |
| `section-eyebrow` (+ `--blue / --purple / --green / --orange / --muted`) | Small uppercase section label with a colored dot. |
| `tag-pill` (+ `--red / --yellow / --green / --blue / --purple / --slate`) | Compact status or category chip. |

DataTables also get row hover, sort-icon tweaks, tabular numerals, and a softer focus outline on cells.

# Equipment Lifecycle Analytics

Python utilities for work-order analytics (Dash dashboard) and equipment list cleanup.

## Layout

| Path | Role |
|------|------|
| `work_order_dashboard.py` | Launches the Dash app (implementation in `dashboard/`) |
| `dashboard/` | App package: `app.py`, `layouts/shell.py`, `callbacks/wiring.py`, `data_loaders.py`, `constants.py`, `taxonomy.py`, `calendar_util.py` |
| `dashboard/assets/dashboard.css` | Auto-loaded styling for the DataTables, info bar, focus states, hover lift, empty state, status pills, etc. |
| `dashboard/logic/overview/` | Overview charts and KPI assembly (`figures.py`, `kpis.py`, `service_prep.py`, `settings_merge.py`) |
| `dashboard/logic/replacement_table.py` | Replacement indicator `DataTable` |
| `dashboard/logic/repair_orders_table.py` | **Order roster** `DataTable` (service lines + business-day span) |
| `dashboard/logic/overview_charts.py` | Thin re-export of `build_overview` (compat) |
| `list_clean.py` | Batch-clean Compuclean equipment exports: `data/equipment/raw/` → `data/equipment/cleaned/` |
| `data/equipment/raw/*.csv` | **Raw** equipment list downloads (before clean) |
| `data/equipment/cleaned/*.csv` | **Cleaned** per-file outputs + `all_equipment_summary.csv` |
| `data/requests/*.csv` | Work **request** exports (same column layout as your source system) |
| `data/service/*.csv` | **Service** order exports |
| `data/repairs/*.csv` | **Repair** work order exports |

Use **any filenames** you like. Every `*.csv` in a folder is loaded and merged; add more files (e.g. one per month) as you go.

The repair-list loader auto-detects the column row by scanning for the leading `#` cell, so exports with 1, 2, or 3 preamble rows (title / generated-at / group header) all parse correctly. When a file ends up with rows whose `Completed Date` could not be parsed, the count is printed to the console so format drift surfaces early instead of silently emptying the dashboard.

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
- **Header**: title, subtitle, and **Month** dropdown. The first option, **All months**, aggregates across every month loaded into the dashboard; pick a specific month (e.g. *March 2026*) to drill in. On first load the dashboard lands on **All months**.
- **Overview**: KPI row + charts. In **All months** mode the calendar card is replaced by a **Request Volume by Month** bar chart, the staff-capacity bar scales its "available" total by the number of months in the data, and the footer reads *"Data reflects all months · N repair records · M service orders."* In a single-month view, the original day-of-month calendar returns.
- **Replacement** (`/replacement`): full-width **Equipment Replacement Indicator** — hero card with rule chips, filter toolbar (Status / Equipment contains / ID contains), then a polished `DataTable`:
  - Native column sort, sticky header, hover-row highlight, right-aligned money columns with `tabular-nums`.
  - Above the table: a *"Showing X of Y equipment items"* pill on the left and a segmented **Rows per page** selector (10 / 20 / 50 / 100 / All) on the right.
  - When filters return zero rows, a friendly empty-state panel ("No matching equipment") appears in place of the table body.
- **Order roster** (`/orders`): full-width service-line roster — hero card, filter toolbar (Equipment class / Status / Equipment / ID), order `DataTable` (scheduled → completed → business days). Same polish set as Replacement: sticky header, native sort, hover, page-size selector, *"Showing X of Y service lines"* pill, and a *"No matching service lines"* empty state. Icons for the Order-roster nav link and page hero share **Order roster link** in Settings.
- **Settings**: preferences in browser local storage (**Apply** / **Reset**). Icons include **Order roster link** for nav + page title.
  - **Staff capacity**: saved **per calendar month** using the same **Month** control in the header. Pick a month, edit values, Apply. Months without a saved entry use the global defaults (also written on Apply). When the header is on **All months**, Apply only updates the global defaults — it does not write per-month overrides.
  - **Availability model**: base days used in the availability chart.
  - **Request calendar**: week starts on Sunday or Monday.
  - **Icons**: KPI cards, nav links (including Order roster), replacement table badge prefixes, and replacement page title icon.
  - **Data paths** for CSV inputs are not editable in the UI; they are defined in `dashboard/constants.py` (`REQUESTS_DIR`, `SERVICE_DIR`, `REPAIRS_DIR`, `EQUIPMENT_SUMMARY_CSV`). Restart the app after changing paths.

The app is created with `update_title=None` so the browser tab title stays **Work Order Dashboard** instead of Dash's temporary "Updating…" during callbacks.

If startup fails with "No *.csv under …", create the missing folder or add exports there. Run from the repo root so `data/...` paths resolve.

### Reusable UI components (`dashboard/assets/dashboard.css`)

The stylesheet is loaded automatically by Dash. It defines a small set of class-based components you can apply via `className=` without touching builders:

| Class | What it does |
|-------|--------------|
| `lift-on-hover` | Subtle elevation (`translateY(-2px)` + deeper shadow) on hover. Drop next to any `CARD_STYLE` Div (KPIs, chart cards, hero cards). |
| `fm-header`, `fm-toolbar` | Scope class for the header bar and any filter toolbar. All `dcc.Input` / `dcc.Dropdown` descendants get a unified blue focus ring + 10px-radius, white-card dropdown menu with hover/selected option styling. |
| `row-count` | Pill-shaped *"Showing X of Y items"* caption with a leading status dot. Used above each DataTable. |
| `page-size-radio` (+ `page-size-radio-label`, `page-size-radio-input`) | Segmented control built from `dcc.RadioItems` — works in place of a dropdown when there are only a handful of options. |
| `empty-state` (+ `empty-state-icon`, `empty-state-title`, `empty-state-hint`) | Friendly "no results" panel; default `display: none` and toggled to `flex` by a callback when filtered rows hit zero. |
| `section-eyebrow` (+ `--blue / --purple / --green / --orange / --muted`) | Small uppercase eyebrow label with a colored leading dot. |
| `tag-pill` (+ `--red / --yellow / --green / --blue / --purple / --slate`) | Compact status / category chip with a leading dot in the current text color. |

All DataTables additionally get: row hover (`#eef4fb`), sort-icon polish, `font-variant-numeric: tabular-nums` for vertically aligned digits, and a softened focused-cell outline.

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

Costs are summed by `equipId` over the selected month (or across every month when **All months** is chosen). `newPrice` is inferred from the equipment name (see `load_repairs` in `dashboard/data_loaders.py`).

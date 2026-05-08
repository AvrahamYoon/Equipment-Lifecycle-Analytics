# Equipment Lifecycle Analytics

Simple Python tools for work order analysis and equipment data cleanup.

## Project Structure

- `work_order_dashboard.py` - Dash/Plotly web dashboard for repair and service metrics.
- `list_clean.py` - CSV cleaner for equipment lists (dedupe, normalize fields, export summary).
- `Work_Orders_April_2026_Request.csv` - request work orders input.
- `April_Service_Orders_with_Prices.csv` - service orders input.
- `April_Repair_List_All_Work_Orders.csv` - repair records input.

## Requirements

```bash
pip install dash pandas plotly
```

Python 3.10+ recommended.

## Run Dashboard

Keep the three dashboard CSV files in the project root, then run:

```bash
python work_order_dashboard.py
```

Open: `http://127.0.0.1:8050`

## Run Data Cleaner

1. Put source CSV files in `input/`.
2. Run:

```bash
python list_clean.py
```

Outputs are written to `Output/`, including:

- per-file `*_cleaned.csv`
- merged `all_equipment_summary.csv`

## Core Rule (Replacement Status)

In the dashboard:

- `Replace`: `(labor + parts) * 0.80 >= newPrice`
- `Monitor`: `(labor + parts) * 0.60 >= newPrice`
- `Good`: otherwise


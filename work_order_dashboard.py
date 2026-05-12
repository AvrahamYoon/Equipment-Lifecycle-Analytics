"""
Entry point for the Dash app. Implementation lives in the `dashboard/` package.
Run from project root:  python work_order_dashboard.py
"""

from dashboard.app import create_app

app = create_app()

if __name__ == "__main__":
    print("Dashboard running at http://127.0.0.1:8050")
    app.run(debug=True)

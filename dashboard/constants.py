"""Theme, paths, and shared numeric constants."""

import os

REQUESTS_DIR = os.path.join("data", "requests")
SERVICE_DIR = os.path.join("data", "service")
REPAIRS_DIR = os.path.join("data", "repairs")
EQUIPMENT_SUMMARY_CSV = os.path.join("data", "equipment", "cleaned", "all_equipment_summary.csv")

BASE_AVAIL_DAYS = 311

DEFAULT_STAFF_COUNT = 4
DEFAULT_HOURS_PER_STAFF_DAY = 4
DEFAULT_WORK_DAYS_PER_MONTH = 20


def default_app_settings():
    """Defaults for user-tunable dashboard assumptions (persisted via dcc.Store)."""
    return {
        "staffCount": DEFAULT_STAFF_COUNT,
        "hoursPerDay": DEFAULT_HOURS_PER_STAFF_DAY,
        "workDays": DEFAULT_WORK_DAYS_PER_MONTH,
        "baseAvailDays": int(BASE_AVAIL_DAYS),
        "weekStartsOn": "sunday",
        # Icons (UTF-8 text / emoji); trimmed in merge_app_settings
        "iconKpiRequests": "📋",
        "iconKpiCompleted": "✅",
        "iconKpiScheduled": "📅",
        "iconKpiRepairCost": "💰",
        "iconKpiParts": "⚙️",
        "iconKpiLabor": "👤",
        "iconNavOverview": "📊",
        "iconNavReplacement": "🚦",
        "iconNavOrders": "📋",
        "iconNavSettings": "⚙️",
        "iconReplaceTitle": "🚦",
        "iconReplaceStatusReplace": "🔴",
        "iconReplaceStatusMonitor": "🟡",
        "iconReplaceStatusGood": "🟢",
        # month_key (str) -> { staffCount, hoursPerDay, workDays }; months not listed use top-level defaults
        "staffCapacityByMonth": {},
    }


CHART_CLASS_ORDER = [
    "Versamatic",
    "Lindhaus",
    "Kaivac",
    "Wet-dry / shop vacuums",
    "Other vacuums",
    "Floor machines",
    "Carpet / extractors",
    "Ladders",
    "Dispensers",
    "Janitorial / carts",
    "Other",
]
CHART_CLASS_RANK = {c: i for i, c in enumerate(CHART_CLASS_ORDER)}

BG_PAGE = "#f0f4f8"
BG_CARD = "#ffffff"
BG_HEADER = "#ffffff"
COLOR_BORDER = "#e2e8f0"
COLOR_TEXT_PRIMARY = "#1e293b"
COLOR_TEXT_SECONDARY = "#64748b"
COLOR_TEXT_MUTED = "#94a3b8"

C_BLUE = "#3b82f6"
C_GREEN = "#10b981"
C_PURPLE = "#8b5cf6"
C_ORANGE = "#f97316"
C_YELLOW = "#f59e0b"
C_PINK = "#ec4899"

CHART_FONT = dict(
    family="'DM Sans','Segoe UI',sans-serif",
    color=COLOR_TEXT_SECONDARY,
    size=12,
)

CARD_STYLE = {
    "background": BG_CARD,
    "border": f"1px solid {COLOR_BORDER}",
    "borderRadius": 14,
    "boxShadow": "0 1px 4px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)",
}


def replace_status(labor, parts, new_price):
    combined = labor + parts
    if combined * 0.80 >= new_price:
        return "Replace"
    if combined * 0.60 >= new_price:
        return "Monitor"
    return "Good"

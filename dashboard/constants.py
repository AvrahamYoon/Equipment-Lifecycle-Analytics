"""Theme, paths, and shared numeric constants."""

import os

REQUESTS_DIR = os.path.join("data", "requests")
SERVICE_DIR = os.path.join("data", "service")
REPAIRS_DIR = os.path.join("data", "repairs")
EQUIPMENT_SUMMARY_CSV = os.path.join("data", "equipment", "cleaned", "all_equipment_summary.csv")
PURCHASE_CSV = os.path.join("data", "equipment", "purchase", "purchase.csv")
EQUIPMENT_TYPE_CSV = os.path.join("data", "equipment", "purchase", "Type.csv")

BASE_AVAIL_DAYS = 311

DEFAULT_STAFF_COUNT = 4
DEFAULT_HOURS_PER_STAFF_DAY = 4
DEFAULT_WORK_DAYS_PER_MONTH = 20
DEFAULT_MONTHLY_PARTS_BUDGET = 1000
DEFAULT_ANNUAL_PARTS_BUDGET = DEFAULT_MONTHLY_PARTS_BUDGET * 12

# Sentinel value used in the month dropdown to mean "aggregate across every
# month loaded into the dashboard"; treated specially by callbacks and figure
# builders so they skip the usual per-month filter.
ALL_MONTHS_KEY = "ALL"
ALL_MONTHS_LABEL = "All months"


def is_all_months(month_key) -> bool:
    """True when the month selector is on the aggregate 'All months' option."""
    return str(month_key).strip().upper() == ALL_MONTHS_KEY


# Rows-per-page dropdown values used on the Replacement and Order Roster
# tables. ``ALL_PAGE_SIZE_VALUE`` is the user-facing sentinel that the
# callback converts into ``ALL_PAGE_SIZE_LIMIT`` (a number large enough that
# Dash effectively renders every row on a single page).
DEFAULT_PAGE_SIZE = 20
ALL_PAGE_SIZE_VALUE = "all"
ALL_PAGE_SIZE_LIMIT = 100_000
PAGE_SIZE_OPTIONS = [
    {"label": "10", "value": 10},
    {"label": "20", "value": 20},
    {"label": "50", "value": 50},
    {"label": "100", "value": 100},
    {"label": "All", "value": ALL_PAGE_SIZE_VALUE},
]


def resolve_page_size(value) -> int:
    """Map a dropdown choice (int or the 'all' sentinel) to a Dash page_size."""
    if value is None:
        return DEFAULT_PAGE_SIZE
    if isinstance(value, str) and value.strip().lower() == ALL_PAGE_SIZE_VALUE:
        return ALL_PAGE_SIZE_LIMIT
    try:
        n = int(value)
    except (TypeError, ValueError):
        return DEFAULT_PAGE_SIZE
    return max(1, min(ALL_PAGE_SIZE_LIMIT, n))


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
        "iconNavRequests": "📝",
        "iconNavSettings": "⚙️",
        "iconReplaceTitle": "🚦",
        "iconReplaceStatusReplace": "🔴",
        "iconReplaceStatusMonitor": "🟡",
        "iconReplaceStatusGood": "🟢",
        # month_key (str) -> { staffCount, hoursPerDay, workDays }; months not listed use top-level defaults
        "staffCapacityByMonth": {},
        "monthlyPartsBudget": DEFAULT_MONTHLY_PARTS_BUDGET,
        "annualPartsBudget": DEFAULT_ANNUAL_PARTS_BUDGET,
    }


# Preferred chart order for ``EquipType`` (cleaned summary + purchase/Type.csv).
CHART_CLASS_ORDER = [
    "Vacuum",
    "Backpack Vacuum",
    "Battery-powered vacuum",
    "Floor Fan",
    "Chemical Dispenser",
    "Carpet Cleaning",
    "Carpet Cleaning Machine",
    "Upholstery Cleaner",
    "Upholstery machine",
    "Scrubber",
    "Burnisher",
    "Buffer",
    "Kaivac",
    "Swing Arm",
    "Ladder",
    "Chariot",
    "Agitator",
    "Other",
]
CHART_CLASS_RANK = {c: i for i, c in enumerate(CHART_CLASS_ORDER)}

BG_PAGE = "#eef2f7"
BG_CARD = "#ffffff"
BG_HEADER = "rgba(255, 255, 255, 0.88)"
COLOR_BORDER = "#e2e8f0"
COLOR_TEXT_PRIMARY = "#0f172a"
COLOR_TEXT_SECONDARY = "#475569"
COLOR_TEXT_MUTED = "#94a3b8"

C_BLUE = "#3b82f6"
C_GREEN = "#10b981"
C_PURPLE = "#8b5cf6"
C_ORANGE = "#f97316"
C_YELLOW = "#f59e0b"
C_PINK = "#ec4899"

CHART_FONT = dict(
    family="'Nunito','Segoe UI',system-ui,sans-serif",
    color=COLOR_TEXT_SECONDARY,
    size=12,
)

CARD_STYLE = {
    "background": "linear-gradient(165deg, #ffffff 0%, #fafbfd 100%)",
    "border": "none",
    "borderRadius": 16,
    "boxShadow": "0 4px 24px -8px rgba(15, 23, 42, 0.08)",
}


def replace_status(labor, parts, new_price):
    """Replace / Monitor / Good from cumulative repair vs. new-equipment price.

    Rules use **repair as a share of estimated new price** (not ``repair×0.8``):
    Replace if labor+parts ≥ 80% of new price; Monitor if ≥ 60% and < 80%;
    Good if < 60%. If new price is missing or non-positive, treat as Good.
    """
    try:
        np = float(new_price)
    except (TypeError, ValueError):
        np = 0.0
    try:
        combined = float(labor or 0) + float(parts or 0)
    except (TypeError, ValueError):
        combined = 0.0
    if np <= 0:
        return "Good"
    if combined >= 0.80 * np:
        return "Replace"
    if combined >= 0.60 * np:
        return "Monitor"
    return "Good"

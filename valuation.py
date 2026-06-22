"""Equipment valuation and replacement pricing.

- Keyword grouping + valuation sheet load/lookup
- Replacement price rules (purchase ID → valuation sheet → service)
- CLI: ``python -m valuation`` generates ``Equipment Valuation Sheet.csv``
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import statistics
import unicodedata
from dataclasses import dataclass, field

import pandas as pd

from dashboard.taxonomy import ensure_equip_id_norm_column, norm_equip_id

TOKEN_MATCH_MIN_SCORE = 0.5

# --- CSV helpers -----------------------------------------------------------------

def norm_col_key(name: str) -> str:
    return str(name).lower().replace(" ", "").replace("_", "").replace("#", "")


def norm_equipment_name(name: str) -> str:
    if pd.isna(name):
        return ""
    s = unicodedata.normalize("NFKD", str(name))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_dollar_amount(value) -> float | None:
    if pd.isna(value):
        return None
    s = str(value).strip()
    if not s or s.lower() == "enter data":
        return None
    s = s.replace("$", "").replace(",", "")
    n = pd.to_numeric(s, errors="coerce")
    if pd.isna(n) or float(n) <= 0:
        return None
    return float(n)


def parse_purchase_year(value) -> int | None:
    if pd.isna(value):
        return None
    s = str(value).strip()
    if not s:
        return None
    m = re.search(r"(20\d{2}|19\d{2})", s)
    if m:
        return int(m.group(1))
    n = pd.to_numeric(s, errors="coerce")
    if pd.isna(n):
        return None
    year = int(n)
    return year if 1900 <= year <= 2100 else None


def pick_column(df: pd.DataFrame, *aliases: str) -> str | None:
    key_to_col = {norm_col_key(c): c for c in df.columns}
    for alias in aliases:
        key = norm_col_key(alias)
        if key in key_to_col:
            return key_to_col[key]
    return None


def match_equipment_key(norm_name: str, keys_sorted: list[str]) -> str | None:
    if not norm_name or not keys_sorted:
        return None

    best_sub: str | None = None
    best_sub_len = 0
    for key in keys_sorted:
        if key in norm_name or norm_name in key:
            if len(key) > best_sub_len:
                best_sub_len = len(key)
                best_sub = key
    if best_sub is not None:
        return best_sub

    best_score = 0.0
    best_key: str | None = None
    best_key_len = 0
    for key in keys_sorted:
        tokens = [t for t in key.split() if len(t) >= 2]
        if not tokens:
            continue
        hits = sum(1 for t in tokens if t in norm_name)
        score = hits / len(tokens)
        if score < TOKEN_MATCH_MIN_SCORE:
            continue
        if score > best_score or (score == best_score and len(key) > best_key_len):
            best_score = score
            best_key = key
            best_key_len = len(key)
    return best_key


# --- Keyword grouping ------------------------------------------------------------

_CATEGORY_RULES: tuple[tuple[str, str], ...] = (
    (r"\b(back\s*pak|bac\s*pak|backpack|back\s*pack)\b", "backpack"),
    (r"\b(auto[\s-]?scrub|scrubber|i[\s-]?scrubber|orbital)\b", "scrubber"),
    (r"\bburnish", "burnisher"),
    (r"\bbuffer\b", "buffer"),
    (r"\b(carpet\s*fan|air\s*mover|air\s*blower|airblower|carpet\s*blower)\b", "carpet_fan"),
    (r"\b(carpet\s*extract|extractor)\b", "extractor"),
    (r"\bcarpet\s*clean(ing)?\b", "carpet_cleaning"),
    (r"\b(dispenser|chemical\s*disp)\b", "chemical_dispenser"),
    (r"\b(battery[\s-]?powered|cordless)\b", "battery_vacuum"),
    (r"\b(upholstery|puzzi|priza|minni[\s-]?capsol|i[\s-]?capsol)\b", "upholstery"),
    (r"\bchariot\b", "chariot"),
    (r"\bkaivac\b", "kaivac"),
    (r"\bsweeper\b", "sweeper"),
    (r"\bladder\b", "ladder"),
    (r"\bswing\s*arm\b", "swing_arm"),
    (r"\bagitator\b", "agitator"),
    (r"\b(wet[\s/-]?dry|vacuum|versamatic|tennant|colt|pig)\b", "vacuum"),
)

_BRAND_ALIASES: dict[str, str] = {
    "versamatic": "versamatic",
    "waxie": "waxie",
    "ice": "ice",
    "advance": "advance",
    "nss": "nss",
    "windsor": "windsor",
    "tennant": "tennant",
    "karcher": "karcher",
    "karcker": "karcher",
    "rubbermaid": "rubbermaid",
    "proteam": "proteam",
    "pro": "proteam",
    "team": "proteam",
    "milwaukee": "milwaukee",
    "viper": "viper",
    "clarke": "clarke",
    "lindhaus": "lindhaus",
    "lindhause": "lindhaus",
    "sandia": "sandia",
    "powerflite": "powerflite",
    "duplex": "duplex",
    "everest": "everest",
    "hydraforce": "hydraforce",
    "rotovac": "rotovac",
    "hako": "hako",
    "sterling": "sterling",
    "ster": "sterling",
    "pacific": "pacific",
    "olympian": "olympian",
    "radius": "radius",
    "champ": "nss",
    "es4000": "advance",
    "puzzi": "karcher",
    "priza": "priza",
    "minuteman": "minuteman",
}

_TOKEN_TYPO: dict[str, str] = {
    "lindhause": "lindhaus",
    "lindhous": "lindhaus",
    "tennent": "tennant",
    "tenent": "tennant",
    "versamaticc": "versamatic",
    "winser": "windsor",
}

_KNOWN_BRAND_SLUGS: tuple[str, ...] = tuple(
    sorted({v for v in _BRAND_ALIASES.values()}, key=len, reverse=True)
)

_CATEGORY_LABEL: dict[str, str] = {
    "backpack": "Backpack",
    "scrubber": "Scrubber",
    "burnisher": "Burnisher",
    "buffer": "Buffer",
    "carpet_fan": "Carpet Fan",
    "extractor": "Carpet Extractor",
    "upholstery": "Upholstery Cleaner",
    "chariot": "Chariot",
    "kaivac": "Kaivac",
    "sweeper": "Sweeper",
    "ladder": "Ladder",
    "agitator": "Agitator",
    "vacuum": "Vacuum",
    "chemical_dispenser": "Chemical Dispenser",
    "battery_vacuum": "Battery-powered vacuum",
    "carpet_cleaning": "Carpet Cleaning",
    "swing_arm": "Swing Arm",
}

# Dashboard ``EquipType`` labels (from Type.csv) for keyword-based name inference.
_KEYWORD_SLUG_TO_EQUIP_TYPE: dict[str, str] = {
    "backpack": "Backpack Vacuum",
    "scrubber": "Scrubber",
    "burnisher": "Burnisher",
    "buffer": "Buffer",
    "carpet_fan": "Floor Fan",
    "extractor": "Carpet Cleaning Machine",
    "carpet_cleaning": "Carpet Cleaning",
    "upholstery": "Upholstery Cleaner",
    "chariot": "Chariot",
    "kaivac": "Kaivac",
    "sweeper": "Vacuum",
    "ladder": "Ladder",
    "agitator": "Agitator",
    "swing_arm": "Swing Arm",
    "vacuum": "Vacuum",
    "chemical_dispenser": "Chemical Dispenser",
    "battery_vacuum": "Battery-powered vacuum",
}

_BRAND_LABEL: dict[str, str] = {
    "ice": "ICE",
    "nss": "NSS",
    "proteam": "ProTeam",
    "kaivac": "KaiVac",
    "karcher": "Karcher",
}

_DEFAULT_BRAND_CATEGORY: dict[str, str] = {
    "advance": "scrubber",
    "nss": "scrubber",
    "ice": "scrubber",
    "windsor": "scrubber",
    "everest": "scrubber",
    "duplex": "scrubber",
    "tennant": "vacuum",
    "versamatic": "vacuum",
    "clarke": "vacuum",
    "olympian": "vacuum",
    "lindhaus": "vacuum",
    "rubbermaid": "backpack",
    "milwaukee": "backpack",
    "proteam": "backpack",
    "waxie": "buffer",
    "karcher": "carpet_fan",
    "sandia": "carpet_fan",
    "powerflite": "carpet_fan",
    "viper": "burnisher",
    "hako": "buffer",
    "sterling": "buffer",
    "pacific": "buffer",
    "rotovac": "extractor",
    "priza": "upholstery",
    "radius": "sweeper",
    "minuteman": "buffer",
}

_SIZE_RE = re.compile(r"\b(1[3-9]|2[0-9]|3[0-9]|4[0-9]|5[0-5])\b")
_JUNK_RE = re.compile(
    r"\b(storage\s*area|shop\s*vac|trash\s*can|tailvac)\b|"
    r"^brad\b|"
    r"\b\d{4,}\b"
)
_STRIP_RE = re.compile(r"\s*#\s*\d+\s*$|\s+number\s+\d+\s*$", re.I)


def _clean_norm(norm: str) -> str:
    norm = _STRIP_RE.sub("", norm).strip()
    return re.sub(r"\s+", " ", norm)


def _detect_category(norm: str) -> str | None:
    for pattern, slug in _CATEGORY_RULES:
        if re.search(pattern, norm):
            return slug
    return None


def _canonical_brand_token(token: str) -> str:
    t = _TOKEN_TYPO.get(token.strip().lower(), token.strip().lower())
    return _BRAND_ALIASES.get(t, t)


def _detect_brands(norm: str) -> list[str]:
    tokens = norm.split()
    found: list[str] = []

    if "pro" in tokens and "team" in tokens:
        found.append("proteam")

    for raw in tokens:
        slug = _canonical_brand_token(raw)
        if slug in _BRAND_ALIASES.values() and slug not in found:
            found.append(slug)

    if not found and tokens:
        first = _canonical_brand_token(tokens[0])
        if first in _BRAND_ALIASES.values():
            found.append(first)

    if not found:
        for brand_slug in _KNOWN_BRAND_SLUGS:
            if norm == brand_slug or norm.startswith(brand_slug + " "):
                found.append(brand_slug)
                break
            for typo, canonical in _TOKEN_TYPO.items():
                if canonical == brand_slug and (
                    norm == typo or norm.startswith(typo + " ")
                ):
                    found.append(brand_slug)
                    break
            if found:
                break

    if not found:
        for alias, brand in _BRAND_ALIASES.items():
            if len(alias) >= 4 and re.search(rf"\b{re.escape(alias)}\b", norm):
                found.append(brand)
                break

    return found[:1]


def _detect_size(norm: str, category: str | None) -> str | None:
    if category == "ladder":
        m = re.search(r"\bladder\s+(\d+)\b", norm)
        if m:
            return f"{m.group(1)}ft"
        m = re.search(r"\b(\d+)\s*(?:ft|foot|feet)\b", norm)
        if m:
            return f"{m.group(1)}ft"
        return None
    if category == "scrubber":
        for pattern, size in (
            (r"\bi\s*18\b|i18b|i18c", "18"),
            (r"\bi\s*20\b|i20", "20"),
        ):
            if re.search(pattern, norm):
                return size
    if category not in {"scrubber", "burnisher", "buffer", "chariot", "vacuum"}:
        return None
    m = _SIZE_RE.search(norm)
    return m.group(1) if m else None


def _parse_keyword_parts(key: str) -> tuple[str, str | None, str | None]:
    parts = key.split("|")
    if not parts:
        return "", None, None
    category = parts[0]
    brand: str | None = None
    size: str | None = None
    for part in parts[1:]:
        if part.isdigit() or part.endswith("ft"):
            size = part
        elif part in _BRAND_ALIASES.values() or part in _BRAND_ALIASES:
            brand = part
    return category, brand, size


def _find_price_for_keyword(sheet: ValuationSheet, key: str) -> float | None:
    """Match sheet row by keyword key; never map branded equipment to generic rows."""
    if key in sheet.prices:
        return sheet.prices[key]

    category, brand, size = _parse_keyword_parts(key)
    if brand:
        best_score = -1
        best_price: float | None = None
        for sheet_key, price in sheet.prices.items():
            sk_cat, sk_brand, sk_size = _parse_keyword_parts(sheet_key)
            if sk_brand != brand:
                continue
            score = 0
            if sk_cat == category:
                score += 4
            if size and sk_size == size:
                score += 2
            elif size and sk_size:
                continue
            if score > best_score:
                best_score = score
                best_price = price
        return best_price

    for sheet_key, price in sheet.prices.items():
        sk_cat, sk_brand, sk_size = _parse_keyword_parts(sheet_key)
        if sk_brand:
            continue
        if sk_cat == category and (not size or sk_size == size):
            return price

    return None


def extract_keyword_key(description: str) -> str | None:
    """Canonical dedupe key, e.g. ``vacuum|versamatic`` or ``scrubber|ice|18``."""
    norm = _clean_norm(norm_equipment_name(description))
    if not norm or _JUNK_RE.search(norm):
        return None

    brands = _detect_brands(norm)
    category = _detect_category(norm)
    size = _detect_size(norm, category)

    if not category and brands:
        category = _DEFAULT_BRAND_CATEGORY.get(brands[0])
    if not category:
        return None
    if category == "ladder" and not size:
        return None

    parts: list[str] = [category]
    parts.extend(brands[:1])
    if size:
        parts.append(size)
    return "|".join(parts)


def equip_type_from_equipment_name(description: str) -> str | None:
    """Infer dashboard ``EquipType`` from an equipment description when ID lookup fails."""
    if pd.isna(description) or not str(description).strip():
        return None
    key = extract_keyword_key(description)
    if not key:
        return None
    slug = key.split("|", 1)[0]
    return _KEYWORD_SLUG_TO_EQUIP_TYPE.get(slug)


def format_keyword_label(key: str) -> str:
    parts = key.split("|")
    if not parts:
        return key

    category = parts[0]
    brand: str | None = None
    size: str | None = None
    for part in parts[1:]:
        if part.isdigit() or part.endswith("ft"):
            size = part
        elif part in _BRAND_ALIASES or part in _BRAND_LABEL:
            brand = part

    cat_label = _CATEGORY_LABEL.get(category, category.replace("_", " ").title())
    brand_label = _BRAND_LABEL.get(brand, brand.title() if brand else "")

    if category == "ladder" and size:
        return f"{size.replace('ft', '')}' Ladder"
    if brand_label and size and not size.endswith("ft"):
        return f'{brand_label} {size}" {cat_label}'
    if brand_label:
        return f"{brand_label} {cat_label}"
    if size and not size.endswith("ft"):
        return f'{size}" {cat_label}'
    if size:
        return f"{size.replace('ft', '')}' {cat_label}"
    return cat_label


# --- Valuation sheet (read once at dashboard startup) -----------------------------

@dataclass
class ValuationSheet:
    """Preloaded valuation rows keyed by canonical equipment keywords."""

    prices: dict[str, float] = field(default_factory=dict)
    keys_sorted: list[str] = field(default_factory=list)


def load_valuation_sheet(path: str) -> ValuationSheet:
    """Read valuation CSV. Missing file → empty sheet."""
    if not path or not os.path.isfile(path):
        return ValuationSheet()

    try:
        df = pd.read_csv(path, encoding_errors="replace")
    except Exception:
        return ValuationSheet()
    if df.empty:
        return ValuationSheet()

    equip_col = pick_column(df, "Equipment", "Model", "Equipment Name")
    cost_col = pick_column(
        df,
        "Original Purchase Cost",
        "Original Purchase Cost*",
        "Original purchase cost",
    )
    if not equip_col or not cost_col:
        return ValuationSheet()

    prices: dict[str, float] = {}
    for _, row in df.iterrows():
        label = str(row.get(equip_col, "")).strip()
        if not label:
            continue
        cost = parse_dollar_amount(row.get(cost_col))
        if cost is None:
            continue
        key = extract_keyword_key(label) or norm_equipment_name(label)
        if key and key not in prices:
            prices[key] = cost

    keys_sorted = sorted(prices.keys(), key=len, reverse=True)
    return ValuationSheet(prices=prices, keys_sorted=keys_sorted)


def build_keyword_prices_from_service(df_service: pd.DataFrame) -> dict[str, float]:
    """Median Estimated Price per keyword — fills gaps when purchase.csv has no row."""
    if df_service is None or df_service.empty:
        return {}

    name_col = pick_column(df_service, "Equipment Name", "Equipment", "Description")
    price_col = pick_column(
        df_service,
        "Estimated Price",
        "New Price",
        "Equipment Price",
        "Est. Price",
    )
    if not name_col or not price_col:
        return {}

    groups: dict[str, list[float]] = {}
    for _, row in df_service.iterrows():
        price = parse_dollar_amount(row.get(price_col))
        if price is None:
            continue
        key = extract_keyword_key(row.get(name_col))
        if not key:
            continue
        groups.setdefault(key, []).append(price)

    return {k: float(statistics.median(v)) for k, v in groups.items() if v}


def build_keyword_prices_from_repairs(df_repairs: pd.DataFrame) -> set[str]:
    """Keyword keys seen in repair exports (for discovery only)."""
    if df_repairs is None or df_repairs.empty:
        return set()
    col = None
    for candidate in ("equipment", "Equipment Name", "Equipment"):
        if candidate in df_repairs.columns:
            col = candidate
            break
    if not col:
        return set()
    keys: set[str] = set()
    for name in df_repairs[col].dropna().unique():
        key = extract_keyword_key(name)
        if key:
            keys.add(key)
    return keys


def merge_valuation_sheet(
    base: ValuationSheet,
    extra_prices: dict[str, float],
    *,
    overwrite: bool = False,
) -> ValuationSheet:
    prices = dict(base.prices)
    for key, price in extra_prices.items():
        if overwrite or key not in prices:
            prices[key] = price
    keys_sorted = sorted(prices.keys(), key=len, reverse=True)
    return ValuationSheet(prices=prices, keys_sorted=keys_sorted)


def load_service_csvs(service_dir: str) -> pd.DataFrame:
    paths = sorted(glob.glob(os.path.join(service_dir, "*.csv")))
    frames = []
    for path in paths:
        try:
            frames.append(pd.read_csv(path, encoding_errors="replace"))
        except Exception:
            continue
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def lookup_valuation_price(equipment_name, sheet: ValuationSheet | None) -> float | None:
    if not sheet or not sheet.prices:
        return None

    key = extract_keyword_key(equipment_name)
    if not key:
        return None
    return _find_price_for_keyword(sheet, key)


# --- Replacement pricing (dashboard) --------------------------------------------

def load_purchase_price_map(path: str) -> dict[str, float]:
    """Map normalized equipment ID → purchase cost from ``purchase.csv``."""
    if not path or not os.path.isfile(path):
        return {}
    try:
        df = pd.read_csv(path, encoding_errors="replace")
    except Exception:
        return {}
    if df.empty:
        return {}

    id_col = pick_column(df, "ID #", "ID", "Equipment ID", "EquipmentId")
    cost_col = pick_column(df, "Cost", "Purch. Cost", "Purchase Cost")
    if not id_col or not cost_col:
        return {}

    out: dict[str, float] = {}
    for _, row in df.iterrows():
        eid = norm_equip_id(row.get(id_col))
        if not eid or eid in out:
            continue
        cost = parse_dollar_amount(row.get(cost_col))
        if cost is not None:
            out[eid] = cost
    return out


def build_service_price_map(df_service: pd.DataFrame) -> dict[str, float]:
    """Map normalized equipment ID → estimated price from service exports."""
    if df_service is None or df_service.empty:
        return {}

    id_col = pick_column(df_service, "Equipment Id", "Equipment ID", "equipId")
    price_col = pick_column(
        df_service,
        "Estimated Price",
        "New Price",
        "Equipment Price",
        "Est. Price",
    )
    if not id_col or not price_col:
        return {}

    out: dict[str, float] = {}
    for _, row in df_service.iterrows():
        eid = norm_equip_id(row.get(id_col))
        if not eid or eid in out:
            continue
        price = parse_dollar_amount(row.get(price_col))
        if price is not None:
            out[eid] = price
    return out


PRICE_SOURCE_PURCHASE = "purchase"
PRICE_SOURCE_VALUATION = "valuation"
PRICE_SOURCE_SERVICE = "service"
PRICE_SOURCE_NONE = ""

PRICE_SOURCE_LABEL = {
    PRICE_SOURCE_PURCHASE: "Accurate",
    PRICE_SOURCE_VALUATION: "Valuation",
    PRICE_SOURCE_SERVICE: "Estimated",
    PRICE_SOURCE_NONE: "—",
}

PRICE_BASIS_COLUMN = "Price basis"
PRICE_BASIS_TOOLTIP = (
    "Purchase.csv cost by equipment ID; else Original Purchase Cost from "
    "Equipment Valuation Sheet.csv (regenerate with "
    "python -m valuation when data changes); else service estimated price."
)


def resolve_price_source(
    equip_id,
    equipment_name,
    purchase_map: dict[str, float],
    service_map: dict[str, float],
    valuation_sheet: ValuationSheet | None = None,
) -> str:
    eid = norm_equip_id(equip_id)
    if eid and eid in purchase_map:
        return PRICE_SOURCE_PURCHASE
    if lookup_valuation_price(equipment_name, valuation_sheet) is not None:
        return PRICE_SOURCE_VALUATION
    if eid and eid in service_map:
        return PRICE_SOURCE_SERVICE
    return PRICE_SOURCE_NONE


def resolve_new_price(
    equip_id,
    equipment_name,
    purchase_map: dict[str, float],
    service_map: dict[str, float],
    valuation_sheet: ValuationSheet | None = None,
) -> float:
    eid = norm_equip_id(equip_id)
    if eid and eid in purchase_map:
        return purchase_map[eid]
    val = lookup_valuation_price(equipment_name, valuation_sheet)
    if val is not None:
        return val
    if eid and eid in service_map:
        return service_map[eid]
    return 0.0


def apply_new_prices_to_repairs(
    df: pd.DataFrame,
    purchase_map: dict[str, float],
    service_map: dict[str, float],
    valuation_sheet: ValuationSheet | None = None,
) -> pd.DataFrame:
    if df.empty:
        out = df.copy()
        out["newPrice"] = pd.Series(dtype=float)
        out["priceSource"] = pd.Series(dtype=str)
        return out
    out = ensure_equip_id_norm_column(df, raw_col="equipId", norm_col="equipIdNorm")
    equip_col = "equipment" if "equipment" in out.columns else None

    def _row_prices(row):
        name = row[equip_col] if equip_col else ""
        eid = row["equipIdNorm"]
        price = resolve_new_price(
            eid, name, purchase_map, service_map, valuation_sheet
        )
        source = resolve_price_source(
            eid, name, purchase_map, service_map, valuation_sheet
        )
        return price, source

    priced = out.apply(_row_prices, axis=1, result_type="expand")
    out["newPrice"] = priced[0]
    out["priceSource"] = priced[1]
    return out


# --- Generate valuation sheet (CLI) ---------------------------------------------

DEFAULT_PURCHASE_CSV = os.path.join("data", "equipment", "purchase", "purchase.csv")
DEFAULT_SERVICE_DIR = os.path.join("data", "service")
DEFAULT_OUTPUT_CSV = os.path.join(
    "data", "equipment", "purchase", "Equipment Valuation Sheet.csv"
)

_SHEET_COLUMNS = [
    "Equipment",
    "Original Purchase Cost*",
    "2026 Replacement Cost",
    "Estimated Current Value",
    "Lifetime Repair Cost",
]
_MANUAL_PLACEHOLDER = "Enter Data"


def _format_dollar(amount: float) -> str:
    rounded = round(amount, 2)
    if abs(rounded - round(rounded)) < 0.005:
        return f"${int(round(rounded)):,}"
    return f"${rounded:,.2f}"


def _purchase_keyword_prices(
    purchase_path: str,
    recent_years: int = 0,
    reference_year: int | None = None,
) -> dict[str, float]:
    df = pd.read_csv(purchase_path, encoding_errors="replace")
    if df.empty:
        return {}

    desc_col = pick_column(df, "Description", "Equip. Name", "Equipment Name")
    cost_col = pick_column(df, "Cost", "Purch. Cost", "Purchase Cost")
    year_col = pick_column(df, "pur.", "pur", "Purchase Year", "Year", "Purch. Date")
    if not desc_col or not cost_col:
        raise SystemExit(f"Missing Description/Cost columns in {purchase_path}")

    ref_year = reference_year or pd.Timestamp.today().year
    groups: dict[str, list[tuple[int | None, float]]] = {}
    skipped = 0

    for _, row in df.iterrows():
        label = str(row.get(desc_col, "")).strip()
        if not label:
            continue
        cost = parse_dollar_amount(row.get(cost_col))
        if cost is None:
            continue
        key = extract_keyword_key(label)
        if not key:
            skipped += 1
            continue
        year = parse_purchase_year(row.get(year_col)) if year_col else None
        groups.setdefault(key, []).append((year, cost))

    if skipped:
        print(f"Skipped {skipped} purchase row(s) with no equipment keywords.")

    prices: dict[str, float] = {}
    for key, records in groups.items():
        pool = records
        if recent_years > 0:
            windowed = [
                rec
                for rec in records
                if rec[0] is not None and (ref_year - rec[0]) <= recent_years
            ]
            if windowed:
                pool = windowed
        prices[key] = float(statistics.median(c for _, c in pool))
    return prices


def build_valuation_rows(
    purchase_path: str,
    service_dir: str = DEFAULT_SERVICE_DIR,
    recent_years: int = 0,
    reference_year: int | None = None,
    *,
    fill_from_service: bool = True,
) -> list[dict[str, str]]:
    prices: dict[str, float] = {}
    if os.path.isfile(purchase_path):
        prices.update(
            _purchase_keyword_prices(purchase_path, recent_years, reference_year)
        )

    added_from_service = 0
    if fill_from_service and os.path.isdir(service_dir):
        service_prices = build_keyword_prices_from_service(load_service_csvs(service_dir))
        for key, price in service_prices.items():
            if key not in prices:
                prices[key] = price
                added_from_service += 1
        if added_from_service:
            print(
                f"Added {added_from_service} keyword row(s) from service "
                f"(not in purchase.csv)."
            )

    if not prices:
        return []

    return [
        {
            "Equipment": format_keyword_label(key),
            "Original Purchase Cost*": _format_dollar(price),
            "2026 Replacement Cost": _MANUAL_PLACEHOLDER,
            "Estimated Current Value": _MANUAL_PLACEHOLDER,
            "Lifetime Repair Cost": _MANUAL_PLACEHOLDER,
        }
        for key, price in sorted(
            prices.items(), key=lambda item: format_keyword_label(item[0]).lower()
        )
    ]


def main() -> None:
    p = argparse.ArgumentParser(
        description="Generate Equipment Valuation Sheet.csv from purchase + service."
    )
    p.add_argument("--input", default=DEFAULT_PURCHASE_CSV, help="purchase.csv path")
    p.add_argument("--service-dir", default=DEFAULT_SERVICE_DIR, help="service CSV folder")
    p.add_argument("--output", default=DEFAULT_OUTPUT_CSV, help="output valuation CSV")
    p.add_argument(
        "--recent-years",
        type=int,
        default=0,
        metavar="N",
        help="Median uses only purchases within the last N calendar years.",
    )
    p.add_argument(
        "--no-service-fill",
        action="store_true",
        help="Do not add keyword rows from service Estimated Price.",
    )
    args = p.parse_args()

    if not os.path.isfile(args.input) and not os.path.isdir(args.service_dir):
        raise SystemExit(f"Need {args.input} and/or service CSVs under {args.service_dir}")

    rows = build_valuation_rows(
        args.input,
        service_dir=args.service_dir,
        recent_years=args.recent_years,
        fill_from_service=not args.no_service_fill,
    )
    if not rows:
        raise SystemExit("No keyword-grouped rows from purchase or service.")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    pd.DataFrame(rows, columns=_SHEET_COLUMNS).to_csv(args.output, index=False)
    print(f"Wrote {len(rows)} equipment rows → {args.output}")


if __name__ == "__main__":
    main()

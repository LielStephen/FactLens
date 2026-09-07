import re
from typing import Dict, Any, Optional, Tuple
from app.facts.schema import TimeContext


# Numerical multipliers
SCALE_MULTIPLIERS = {
    "k": 1e3,
    "thousand": 1e3,
    "m": 1e6,
    "mn": 1e6,
    "million": 1e6,
    "millions": 1e6,
    "b": 1e9,
    "bn": 1e9,
    "billion": 1e9,
    "billions": 1e9,
    "t": 1e12,
    "tn": 1e12,
    "trillion": 1e12,
    "trillions": 1e12,
    "lakh": 1e5,
    "crore": 1e7,
}

# Currency mappings
CURRENCY_MAP = {
    "$": "USD",
    "usd": "USD",
    "dollar": "USD",
    "dollars": "USD",
    "€": "EUR",
    "eur": "EUR",
    "euro": "EUR",
    "euros": "EUR",
    "£": "GBP",
    "gbp": "GBP",
    "pound": "GBP",
    "pounds": "GBP",
    "₹": "INR",
    "inr": "INR",
    "rupee": "INR",
    "rupees": "INR",
}

# Canonical predicate standardizations
PREDICATE_CANONICAL_MAP = {
    "annual turnover": "revenue",
    "yearly revenue": "revenue",
    "total revenue": "revenue",
    "sales revenue": "revenue",
    "turnover": "revenue",
    "revenue from operations": "revenue",
    "revenue from services": "revenue",
    "revenue from customers": "revenue",
    "service revenue": "revenue",
    "total income": "revenue",
    "net turnover": "net_revenue",
    "gross turnover": "gross_revenue",
    "net sales": "net_revenue",
    "gross sales": "gross_revenue",
    "adjusted ebitda": "ebitda",
    "reported ebitda": "ebitda",
    "service ebitda": "ebitda",
    "operating ebitda": "ebitda",
    "operating profit": "operating_income",
    "operating earnings": "operating_income",
    "net profit": "net_income",
    "net earnings": "net_income",
    "express parcels shipped": "express_parcel_volume",
    "express parcel shipments": "express_parcel_volume",
    "express parcels": "express_parcel_volume",
    "express parcel": "express_parcel_volume",
    "ptl freight delivered": "freight_volume",
    "ptl freight tonnage": "freight_volume",
    "freight tonnage": "freight_volume",
    "pin codes covered": "pincode_reach",
    "pin-code reach": "pincode_reach",
    "pincode reach": "pincode_reach",
    "no. of active customers": "active_customers",
    "active customers": "active_customers",
    "headquarters": "headquarters",
    "hq": "headquarters",
    "head office": "headquarters",
    "registered office": "headquarters",
    "corporate address": "headquarters",
    "office address": "headquarters",
    "chief executive officer": "ceo",
    "managing director": "director",
    "board member": "director",
    "headcount": "employees",
    "total employees": "employees",
    "workforce": "employees",
    "workforce strength": "employees",
    # Macroeconomic canonical indicators
    "real gdp growth": "real_gdp_growth",
    "gdp growth": "real_gdp_growth",
    "real gdp growth rate": "real_gdp_growth",
    "economic growth": "real_gdp_growth",
    "gross domestic product": "real_gdp_growth",
    "gross domestic product growth": "real_gdp_growth",
    "cpi inflation": "cpi_inflation",
    "headline cpi inflation": "cpi_inflation",
    "headline inflation": "cpi_inflation",
    "retail inflation": "cpi_inflation",
    "consumer price index": "cpi_inflation",
    "cpi c": "cpi_inflation",
    "wpi inflation": "wpi_inflation",
    "wholesale price inflation": "wpi_inflation",
    "wholesale price index": "wpi_inflation",
    "fiscal deficit": "fiscal_deficit",
    "gross fiscal deficit": "fiscal_deficit",
    "fiscal deficit percent of gdp": "fiscal_deficit",
    "fiscal deficit of gdp": "fiscal_deficit",
    "current account deficit": "current_account_deficit",
    "cad percent of gdp": "current_account_deficit",
    "foreign exchange reserves": "forex_reserves",
    "forex reserves": "forex_reserves",
    "foreign currency assets": "forex_reserves",
    "policy repo rate": "repo_rate",
    "repo rate": "repo_rate",
    "policy rate": "repo_rate",
}


def normalize_currency(raw_text: str) -> Optional[str]:
    """Detects and canonicalizes currency from text."""
    lower = raw_text.lower()
    for symbol, code in CURRENCY_MAP.items():
        if symbol in lower:
            return code
    return None


def normalize_number(raw_val: str) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """
    Parses arbitrary numerical strings into normalized float, unit, and currency.
    Handles:
    - $1.2B, 1200 million USD, USD 1,200,000,000 -> 1200000000.0
    - ($1,200), -$1,200 -> -1200.0
    - 15%, -15% -> 0.15, -0.15
    - 10,000 employees -> 10000.0, unit='employees'
    """
    if not raw_val:
        return None, None, None

    clean = str(raw_val).strip()
    currency = normalize_currency(clean)

    # Check for negative accounting format: ($1,200) or -$1200
    is_negative = False
    if clean.startswith("(") and clean.endswith(")"):
        is_negative = True
        clean = clean[1:-1].strip()
    elif clean.startswith("-") or "negative" in clean.lower():
        is_negative = True
        clean = clean.lstrip("-").strip()

    # Percentage check
    if "%" in clean or "percent" in clean.lower():
        pct_match = re.search(r'([\d,]+(?:\.\d+)?)', clean)
        if pct_match:
            try:
                val = float(pct_match.group(1).replace(",", ""))
                normalized = round(val / 100.0, 6)
                if is_negative:
                    normalized = -normalized
                return normalized, "%", None
            except ValueError:
                pass

    # Scale check (million, billion, B, M, etc.)
    scale_factor = 1.0
    detected_scale = None
    lower_clean = clean.lower()

    for scale_key, mult in SCALE_MULTIPLIERS.items():
        # Look for word boundary or suffix
        pattern = rf'(?:\b|(?<=\d)){scale_key}(?:\b|$)'
        if re.search(pattern, lower_clean):
            scale_factor = mult
            detected_scale = scale_key
            break

    # Extract primary numeric part
    num_match = re.search(r'([\d,]+(?:\.\d+)?)', clean)
    if not num_match:
        return None, None, currency

    try:
        base_num = float(num_match.group(1).replace(",", ""))
        normalized = base_num * scale_factor
        if is_negative:
            normalized = -normalized

        unit = currency if currency else None
        # Check for non-currency units (e.g. employees, stores, units)
        unit_match = re.search(r'\b(employees|stores|units|metric tons|shares|locations|users|subscribers)\b', clean, re.IGNORECASE)
        if unit_match:
            unit = unit_match.group(1).lower()

        return normalized, unit, currency
    except ValueError:
        return None, None, currency


def normalize_temporal(time_input: Any) -> TimeContext:
    """
    Normalizes time strings, quarters, fiscal years, calendar years, and date ranges.
    Distinguishes FY2024 from calendar year 2024.
    """
    if isinstance(time_input, dict):
        return TimeContext(
            label=time_input.get("label"),
            start=time_input.get("start"),
            end=time_input.get("end"),
            precision=time_input.get("precision")
        )

    if not time_input or not isinstance(time_input, str):
        return TimeContext()

    raw = time_input.strip()

    # Indian / Multi-Year Fiscal: 2024-25 / FY2024-25 / FY24-25 / FY2024/25 -> FY2025
    fy_span_match = re.search(r'\b(?:FY|Fiscal|Financial\s*Year)?\s*(?:20)?(\d{2})[-/](\d{2})\b', raw, re.IGNORECASE)
    if fy_span_match:
        y1, y2 = int(fy_span_match.group(1)), int(fy_span_match.group(2))
        if y2 == (y1 + 1) % 100:
            target_year = 2000 + y2
            return TimeContext(
                label=f"FY{target_year}",
                precision="fiscal_year"
            )

    # FY 2024 / Fiscal 2024 / FY24
    fy_match = re.search(r'\b(?:FY|Fiscal|Financial\s*Year)\s*(\d{2,4})\b', raw, re.IGNORECASE)
    if fy_match:
        year = fy_match.group(1)
        if len(year) == 2:
            year = "20" + year
        return TimeContext(
            label=f"FY{year}",
            start=None,
            end=None,
            precision="fiscal_year"
        )

    # Q1 2024 / Q4 FY23
    quarter_match = re.search(r'\b(Q[1-4])\s*(?:FY)?\s*(\d{2,4})\b', raw, re.IGNORECASE)
    if quarter_match:
        q = quarter_match.group(1).upper()
        year = quarter_match.group(2)
        if len(year) == 2:
            year = "20" + year
        return TimeContext(
            label=f"{q} {year}",
            precision="quarter"
        )

    # Range: 2024-01-01 to 2024-12-31
    range_match = re.search(r'(\d{4}-\d{2}-\d{2})\s*(?:to|–|-)\s*(\d{4}-\d{2}-\d{2})', raw)
    if range_match:
        return TimeContext(
            label=raw,
            start=range_match.group(1),
            end=range_match.group(2),
            precision="range"
        )

    # Single 4-digit calendar year: 2024
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', raw)
    if year_match:
        year = year_match.group(1)
        return TimeContext(
            label=year,
            start=f"{year}-01-01",
            end=f"{year}-12-31",
            precision="year"
        )

    # As of / point in time: "as of March 2025"
    if "as of" in raw.lower():
        return TimeContext(
            label=raw,
            precision="point_in_time"
        )

    return TimeContext(label=raw, precision="unspecified")


def normalize_entity(raw_entity: str) -> str:
    """
    Produces a canonical entity representation while preserving core name identity.
    Acme Corp. -> Acme Corporation
    """
    if not raw_entity:
        return ""
    clean = raw_entity.strip()
    # Institutional & Macroeconomic entities
    if re.search(r'\b(Reserve Bank of India|RBI)\b', clean, re.IGNORECASE):
        return "Reserve Bank of India"
    if re.search(r'\b(Ministry of Finance|Government of India|Department of Economic Affairs)\b', clean, re.IGNORECASE):
        return "Government of India"
    if re.search(r'\b(International Monetary Fund|IMF)\b', clean, re.IGNORECASE):
        return "International Monetary Fund"
    if re.search(r'\b(National Statistical Office|NSO|MoSPI)\b', clean, re.IGNORECASE):
        return "National Statistical Office"
    if re.search(r'\b(Delhivery\s*(?:Limited|Ltd\.?|Corporate)?)\b', clean, re.IGNORECASE):
        return "Delhivery Limited"

    # Normalize common corporate legal forms
    normalized = re.sub(r'\b(Corp\b\.?|Corporation)\b', 'Corporation', clean, flags=re.IGNORECASE)
    normalized = re.sub(r'\b(Inc\b\.?|Incorporated)\b', 'Inc.', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\b(Ltd\b\.?|Limited)\b', 'Ltd.', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\b(LLC|L\.L\.C\.)\b', 'LLC', normalized, flags=re.IGNORECASE)
    # Strip any trailing period if not part of Inc. or Ltd.
    if normalized.endswith(".") and not (normalized.endswith("Inc.") or normalized.endswith("Ltd.")):
        normalized = normalized[:-1].strip()
    # Remove excessive whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def normalize_predicate(raw_predicate: str) -> str:
    """
    Maps semantic equivalents (e.g. annual turnover -> revenue)
    while strictly keeping distinct accounting concepts separated (gross revenue != net revenue).
    """
    if not raw_predicate:
        return ""
    clean = raw_predicate.strip().lower()
    clean = re.sub(r'[_\-]+', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return PREDICATE_CANONICAL_MAP.get(clean, clean)

import pytest
from app.facts.normalizer import (
    normalize_number,
    normalize_temporal,
    normalize_entity,
    normalize_predicate
)


def test_numerical_normalization_scales():
    # $1.2B vs 1200 million vs USD 1,200,000,000
    val1, unit1, curr1 = normalize_number("$1.2 billion")
    val2, unit2, curr2 = normalize_number("1200 million USD")
    val3, unit3, curr3 = normalize_number("1.2B USD")
    val4, unit4, curr4 = normalize_number("USD 1,200,000,000")

    assert val1 == 1200000000.0
    assert val2 == 1200000000.0
    assert val3 == 1200000000.0
    assert val4 == 1200000000.0
    assert curr1 == "USD"
    assert curr2 == "USD"


def test_numerical_percentages_and_negatives():
    # 15% -> 0.15
    pct, unit, curr = normalize_number("15%")
    assert pct == 0.15
    assert unit == "%"

    # Negative percentage
    pct_neg, unit_neg, _ = normalize_number("-15%")
    assert pct_neg == -0.15

    # Parentheses accounting format: ($1,200) -> -1200.0
    neg_val, _, _ = normalize_number("($1,200)")
    assert neg_val == -1200.0

    # Explicit minus: -$1,200
    neg_val2, _, _ = normalize_number("-$1,200")
    assert neg_val2 == -1200.0


def test_temporal_normalization():
    # FY2024
    t_fy = normalize_temporal("FY2024")
    assert t_fy.label == "FY2024"
    assert t_fy.precision == "fiscal_year"
    # Must NOT assume standard calendar alignment
    assert t_fy.start is None

    # Calendar year 2024
    t_cal = normalize_temporal("2024")
    assert t_cal.label == "2024"
    assert t_cal.precision == "year"
    assert t_cal.start == "2024-01-01"
    assert t_cal.end == "2024-12-31"

    # Quarter
    t_q = normalize_temporal("Q1 2024")
    assert t_q.label == "Q1 2024"
    assert t_q.precision == "quarter"


def test_entity_normalization():
    assert normalize_entity("Acme Corp.") == "Acme Corporation"
    assert normalize_entity("Acme Inc.") == "Acme Inc."
    assert normalize_entity("Acme Corporation") == "Acme Corporation"


def test_predicate_normalization():
    assert normalize_predicate("annual turnover") == "revenue"
    assert normalize_predicate("yearly revenue") == "revenue"
    assert normalize_predicate("total revenue") == "revenue"
    assert normalize_predicate("head office") == "headquarters"
    # Ensure distinct accounting metrics are NOT merged
    assert normalize_predicate("gross sales") == "gross_revenue"
    assert normalize_predicate("operating profit") == "operating_income"

import pytest
from app.database.models import FactModel
from app.resolution.deterministic import resolve_deterministic


def test_corroboration_same_fact():
    fact1 = FactModel(
        id="f1",
        document_id="doc1",
        subject="Acme Corporation",
        predicate="revenue",
        raw_value="$125 million",
        normalized_value=125000000.0,
        unit="USD",
        time_data={"label": "FY2024", "precision": "fiscal_year"},
        scope="global"
    )
    fact2 = FactModel(
        id="f2",
        document_id="doc2",
        subject="Acme Corporation",
        predicate="revenue",
        raw_value="125 million USD",
        normalized_value=125000000.0,
        unit="USD",
        time_data={"label": "FY2024", "precision": "fiscal_year"},
        scope="global"
    )

    result = resolve_deterministic(fact1, fact2)
    assert result is not None
    assert result.relationship_type == "CORROBORATES"
    assert result.confidence >= 0.95


def test_contextual_difference_different_periods():
    # FY2023 vs FY2024
    fact1 = FactModel(
        id="f1",
        document_id="doc1",
        subject="Acme Corporation",
        predicate="revenue",
        raw_value="$100 million",
        normalized_value=100000000.0,
        unit="USD",
        time_data={"label": "FY2023", "precision": "fiscal_year"},
        scope="global"
    )
    fact2 = FactModel(
        id="f2",
        document_id="doc2",
        subject="Acme Corporation",
        predicate="revenue",
        raw_value="$125 million",
        normalized_value=125000000.0,
        unit="USD",
        time_data={"label": "FY2024", "precision": "fiscal_year"},
        scope="global"
    )

    result = resolve_deterministic(fact1, fact2)
    assert result is not None
    # MUST NOT be classified as contradiction!
    assert result.relationship_type == "CONTEXTUAL_DIFFERENCE"
    assert "different reporting periods" in result.explanation.lower()


def test_contradiction_same_period_different_values():
    # Same entity, same predicate, same FY2024, but $125M vs $142M!
    fact1 = FactModel(
        id="f1",
        document_id="doc1",
        subject="Acme Corporation",
        predicate="revenue",
        raw_value="$125 million",
        normalized_value=125000000.0,
        unit="USD",
        time_data={"label": "FY2024", "precision": "fiscal_year"},
        scope="global"
    )
    fact2 = FactModel(
        id="f2",
        document_id="doc2",
        subject="Acme Corporation",
        predicate="revenue",
        raw_value="$142 million",
        normalized_value=142000000.0,
        unit="USD",
        time_data={"label": "FY2024", "precision": "fiscal_year"},
        scope="global"
    )

    result = resolve_deterministic(fact1, fact2)
    assert result is not None
    assert result.relationship_type == "CONTRADICTS"
    assert result.confidence >= 0.90
    assert "conflict" in result.explanation.lower() or "source a reports" in result.explanation.lower()


def test_contextual_difference_different_scopes():
    # Global vs US Subsidiary
    fact1 = FactModel(
        id="f1",
        document_id="doc1",
        subject="Acme Corporation",
        predicate="revenue",
        raw_value="$125 million",
        normalized_value=125000000.0,
        unit="USD",
        time_data={"label": "FY2024"},
        scope="global"
    )
    fact2 = FactModel(
        id="f2",
        document_id="doc2",
        subject="Acme Corporation",
        predicate="revenue",
        raw_value="$45 million",
        normalized_value=45000000.0,
        unit="USD",
        time_data={"label": "FY2024"},
        scope="US subsidiary"
    )

    result = resolve_deterministic(fact1, fact2)
    assert result is not None
    assert result.relationship_type == "CONTEXTUAL_DIFFERENCE"
    assert "scope" in result.explanation.lower()

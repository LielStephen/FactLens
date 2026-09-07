import pytest
from app.extraction.layout import ExtractedDocument, ExtractedPage, ExtractedBlock
from app.facts.validator import validate_evidence_grounding


def build_mock_doc():
    block1 = ExtractedBlock(
        id="p1_b1",
        page_number=1,
        block_index=0,
        block_type="text",
        text="Acme Corporation achieved revenue of $125 million in FY2024.",
        bbox=[50, 50, 500, 100]
    )
    page1 = ExtractedPage(
        page_number=1,
        width=595,
        height=842,
        extraction_method="native",
        quality_score=1.0,
        raw_text=block1.text,
        blocks=[block1]
    )
    return ExtractedDocument(
        document_id="doc_test_1",
        filename="report.pdf",
        file_hash="hash123",
        page_count=1,
        pages=[page1]
    )


def test_evidence_validation_exact_match():
    doc = build_mock_doc()
    status, score, bbox = validate_evidence_grounding(
        evidence_quote="revenue of $125 million in FY2024",
        page_number=1,
        block_id="p1_b1",
        extracted_doc=doc
    )
    assert status == "grounded"
    assert score >= 0.95
    assert bbox == [50, 50, 500, 100]


def test_evidence_validation_fuzzy_match():
    doc = build_mock_doc()
    # Minor typographical variation
    status, score, bbox = validate_evidence_grounding(
        evidence_quote="Acme Corporation revenue $125 million FY2024",
        page_number=1,
        block_id="p1_b1",
        extracted_doc=doc
    )
    assert status in ["grounded", "grounded_with_warning"]
    assert score >= 0.70


def test_evidence_validation_unsupported_rejection():
    doc = build_mock_doc()
    # Hallucinated quote not in the document!
    status, score, bbox = validate_evidence_grounding(
        evidence_quote="Acme Corporation lost 50 million dollars in Europe",
        page_number=1,
        block_id="p1_b1",
        extracted_doc=doc
    )
    assert status == "unsupported"
    assert score == 0.0
    assert bbox is None

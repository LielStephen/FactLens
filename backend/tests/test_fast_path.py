import pytest
from app.extraction.layout import ExtractedDocument, ExtractedPage, ExtractedBlock
from app.facts.candidate_detector import compute_information_density_score, detect_candidate_chunks
from app.facts.table_extractor import extract_facts_from_tables

def test_information_density_scoring():
    # Boilerplate text should receive negative penalty score
    score_bp, sigs_bp = compute_information_density_score("All rights reserved. Confidential. Page 12 of 100.", "text")
    assert score_bp < 0
    assert len(sigs_bp) == 0

    # High-signal financial disclosure should receive high score
    text_fin = "Delhivery revenue from operations reached ₹5,310.62 Cr in FY2022 with adjusted EBITDA of ₹120 Cr."
    score_fin, sigs_fin = compute_information_density_score(text_fin, "text")
    assert score_fin >= 10.0
    assert "financial_metrics" in sigs_fin
    assert "temporal" in sigs_fin
    assert "currency_scales" in sigs_fin

def test_fast_path_table_extraction():
    table_block = ExtractedBlock(
        id="tbl_1",
        page_number=1,
        block_index=0,
        block_type="table",
        text="TABLE",
        bbox=[50, 50, 500, 200],
        table_data={
            "headers": ["Particulars", "FY21", "FY22"],
            "rows": [
                ["Revenue from operations", "3,646.52", "5,310.62"],
                ["Adjusted EBITDA", "(150.2)", "120.5"],
            ]
        }
    )
    doc = ExtractedDocument(
        document_id="doc_test_123",
        filename="delhivery_prospectus.pdf",
        file_hash="hash123",
        page_count=1,
        pages=[
            ExtractedPage(
                page_number=1,
                width=595.0,
                height=842.0,
                extraction_method="native",
                quality_score=1.0,
                raw_text="Sample text",
                blocks=[table_block]
            )
        ]
    )

    facts = extract_facts_from_tables(doc)
    assert len(facts) >= 2
    # Verify FY22 revenue
    fy22_rev = next((f for f in facts if f.time and f.time.label == "FY2022" and f.predicate == "revenue"), None)
    assert fy22_rev is not None
    assert fy22_rev.normalized_value == 5310.62
    assert fy22_rev.confidence == 0.98
    assert fy22_rev.evidence.validation_status == "grounded"

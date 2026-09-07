import os
import fitz
import pytest
from app.extraction.quality import evaluate_page_quality
from app.extraction.pdf_parser import extract_pdf, compute_file_hash, detect_block_type


def test_quality_evaluation():
    # 1. Normal dense page
    normal_text = "Acme Corporation reported revenue of $125 million for the fiscal year ended December 31, 2024."
    score, is_poor, reasons = evaluate_page_quality(normal_text, 612, 792, has_images=False)
    assert score >= 0.8
    assert not is_poor

    # 2. Blank page
    score, is_poor, reasons = evaluate_page_quality("", 612, 792, has_images=False)
    assert not is_poor

    # 3. Image-only page with no text (scanned)
    score, is_poor, reasons = evaluate_page_quality("", 612, 792, has_images=True)
    assert is_poor
    assert score == 0.0
    assert "Scanned/Image-only" in reasons[0]


def test_detect_block_type():
    assert detect_block_type("FINANCIAL HIGHLIGHTS") == "heading"
    assert detect_block_type("TABLE: A | B", is_table=True) == "table"
    assert detect_block_type("• Total workforce increased by 10%") == "list"
    assert detect_block_type("1. First item on the agenda") == "list"
    assert detect_block_type("Revenue grew across all business segments in 2024.") == "text"


def test_pdf_extraction_with_fitz(tmp_path):
    # Create a synthetic test PDF
    pdf_path = str(tmp_path / "sample_test.pdf")
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 80), "FINANCIAL OVERVIEW", fontsize=16)
    page.insert_text((50, 120), "Acme Corporation achieved revenue of $125 million in FY2024.", fontsize=11)
    doc.save(pdf_path)
    doc.close()

    extracted = extract_pdf(pdf_path, "doc_test_123", "sample_test.pdf")
    assert extracted.page_count == 1
    assert len(extracted.pages) == 1
    assert extracted.pages[0].quality_score >= 0.8
    assert len(extracted.pages[0].blocks) >= 2
    
    # Check block bboxes are preserved
    b = extracted.pages[0].blocks[0]
    assert len(b.bbox) == 4
    assert b.bbox[0] >= 0

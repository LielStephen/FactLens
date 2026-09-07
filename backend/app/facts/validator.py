import re
import difflib
from typing import Tuple, Optional, List
from app.extraction.layout import ExtractedDocument, ExtractedPage, ExtractedBlock


def clean_text_for_comparison(text: str) -> str:
    """Normalizes whitespace, punctuation, and casing for evidence matching."""
    text = text.lower()
    text = re.sub(r'[\s\n\r\t]+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()


def validate_evidence_grounding(
    evidence_quote: str,
    page_number: int,
    block_id: str,
    extracted_doc: ExtractedDocument
) -> Tuple[str, float, Optional[List[float]]]:
    """
    Independently validates that the LLM's cited evidence quote exists in the source document.
    Returns:
        status: 'grounded', 'grounded_with_warning', or 'unsupported'
        validation_score: float [0.0 - 1.0]
        bbox: bounding box [x0, y0, x1, y1] of matching block
    """
    if not evidence_quote or not evidence_quote.strip():
        return "unsupported", 0.0, None

    quote_clean = clean_text_for_comparison(evidence_quote)
    if not quote_clean:
        return "unsupported", 0.0, None

    # Find the target page
    target_page: Optional[ExtractedPage] = None
    for p in extracted_doc.pages:
        if p.page_number == page_number:
            target_page = p
            break

    if not target_page:
        return "unsupported", 0.0, None

    # Step 1: Target block check
    target_block: Optional[ExtractedBlock] = None
    for b in target_page.blocks:
        if b.id == block_id:
            target_block = b
            break

    if target_block:
        block_clean = clean_text_for_comparison(target_block.text)
        # Exact substring match in designated block
        if quote_clean in block_clean:
            return "grounded", 1.0, target_block.bbox

        # Fuzzy overlap in target block
        matcher = difflib.SequenceMatcher(None, quote_clean, block_clean)
        ratio = matcher.ratio()
        if ratio > 0.80:
            return "grounded", round(ratio, 2), target_block.bbox
        elif ratio > 0.65:
            return "grounded_with_warning", round(ratio, 2), target_block.bbox

    # Step 2: Search across all blocks on the specified page
    for b in target_page.blocks:
        block_clean = clean_text_for_comparison(b.text)
        if quote_clean in block_clean:
            return "grounded", 0.95, b.bbox

        matcher = difflib.SequenceMatcher(None, quote_clean, block_clean)
        ratio = matcher.ratio()
        if ratio > 0.82:
            return "grounded_with_warning", round(ratio, 2), b.bbox

    # Step 3: Search entire page raw text
    page_clean = clean_text_for_comparison(target_page.raw_text)
    if quote_clean in page_clean:
        # Quote exists on page, return page center or approximate bbox
        return "grounded_with_warning", 0.85, [50.0, 50.0, target_page.width - 50.0, 150.0]

    matcher = difflib.SequenceMatcher(None, quote_clean, page_clean)
    page_ratio = matcher.ratio()
    if page_ratio > 0.78:
        return "grounded_with_warning", round(page_ratio, 2), [50.0, 50.0, target_page.width - 50.0, 150.0]

    # Unsupported: Hallucinated quote or citation not present in source!
    return "unsupported", 0.0, None

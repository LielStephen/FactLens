import re
from typing import Dict, Any, Tuple, List


def evaluate_page_quality(page_text: str, page_width: float, page_height: float, has_images: bool = False) -> Tuple[float, bool, List[str]]:
    """
    Evaluates extraction quality of a PDF page.
    Returns:
        quality_score: Float between 0.0 and 1.0
        is_poor: Boolean indicating whether OCR fallback should be triggered
        reasons: List of diagnostic issues found
    """
    reasons = []
    text_len = len(page_text.strip())
    
    # 1. Check for virtually empty page
    if text_len == 0:
        if has_images:
            reasons.append("Scanned/Image-only page with no native text")
            return 0.0, True, reasons
        else:
            reasons.append("Blank page with no content")
            return 1.0, False, reasons  # Normal blank page, not poor extraction

    # 2. Suspiciously low character count
    # A standard page area is ~ 500,000 pt^2. If area is large and chars < 30, it's suspect
    page_area = page_width * page_height
    if text_len < 35 and page_area > 200000:
        if has_images:
            reasons.append("Suspiciously low character count on page containing images")
            return 0.2, True, reasons
        else:
            reasons.append("Low character count (likely title or separator page)")
            return 0.8, False, reasons

    # 3. Check garbage / non-printable character ratio
    printable_chars = len(re.findall(r'[a-zA-Z0-9\s.,;:$\-–—%()\/\"\'#@&+=*<>\[\]]', page_text))
    garbage_ratio = 1.0 - (printable_chars / max(text_len, 1))
    
    if garbage_ratio > 0.35:
        reasons.append(f"High ratio of unprintable or corrupt glyphs ({garbage_ratio:.1%})")
        return max(0.1, 1.0 - garbage_ratio), True, reasons

    # 4. Normal native extraction
    score = max(0.6, min(1.0, 1.0 - garbage_ratio))
    return round(score, 2), False, reasons

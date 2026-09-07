import re
from typing import List, Dict, Any, Optional, Tuple
from app.extraction.layout import ExtractedDocument, ExtractedPage, ExtractedBlock
from app.facts.schema import CandidateChunk


CANDIDATE_PATTERNS = {
    "financial_metrics": re.compile(r'\b(revenue|turnover|net income|operating income|sales|ebitda|profit|loss|assets|debt|cash|expenses|margin|dividend)\b', re.IGNORECASE),
    "currency_scales": re.compile(r'(\$|€|£|₹|USD|EUR|GBP|INR|crore|crores|lakh|lakhs|million|millions|billion|billions|trillion)\b', re.IGNORECASE),
    "numbers_percentages": re.compile(r'\b\d+(?:[.,]\d+)?\s*(?:%|percent|cr|mn|bn)?\b', re.IGNORECASE),
    "temporal": re.compile(r'\b(FY\s*\d{2,4}|Q[1-4]\s*\d{2,4}|\b(?:19|20)\d{2}\b|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|as of|ended|quarter|fiscal)\b', re.IGNORECASE),
    "operational_metrics": re.compile(r'\b(employees|headcount|customers|subscribers|shipments|volume|express parcel|centers|pincodes|coverage|clients|network)\b', re.IGNORECASE),
    "roles_entities": re.compile(r'\b(Delhivery|CEO|Managing Director|Officer|Founder|President|Chairman|Director|Headquarters|Registered Office|subsidiary)\b', re.IGNORECASE),
    "macro_metrics": re.compile(r'\b(gdp|inflation|deficit|cpi|wpi|repo rate|forex|reserves|growth rate|gross domestic product|current account)\b', re.IGNORECASE),
    "macro_entities": re.compile(r'\b(RBI|Reserve Bank|Ministry of Finance|Economic Survey|IMF|Government of India|Central Bank)\b', re.IGNORECASE),
}

# Strong noise / boilerplate patterns that provide zero quantitative or corporate facts
DISCLAIMER_PATTERNS = re.compile(
    r'(all rights reserved|confidential|printed on|page \d+ of \d+|this page intentionally left blank|table of contents|contents page|forward-looking statements|safe harbor|statutory auditors|independent auditor\'s report|cin:|isin:)',
    re.IGNORECASE
)


def compute_information_density_score(text: str, block_type: str) -> Tuple[float, List[str]]:
    """
    Computes an Information-Theoretic Density Score (IDS) for a text or table block.
    Heavily weights verified financial predicates, numeric scales, and temporal qualifiers,
    while heavily penalizing legal disclaimers and boilerplate.
    """
    if DISCLAIMER_PATTERNS.search(text):
        return -10.0, []

    signals = []
    score = 0.0

    # Structured tables have inherently high information density
    if block_type == "table":
        score += 8.0
        signals.append("structured_table")

    # Financial metric presence is the strongest signal for groundable facts
    fin_matches = CANDIDATE_PATTERNS["financial_metrics"].findall(text)
    if fin_matches:
        score += len(fin_matches) * 3.5
        signals.append("financial_metrics")

    # Currencies & Scales
    curr_matches = CANDIDATE_PATTERNS["currency_scales"].findall(text)
    if curr_matches:
        score += len(curr_matches) * 2.5
        signals.append("currency_scales")

    # Operational metrics (shipments, pincodes, headcount)
    op_matches = CANDIDATE_PATTERNS["operational_metrics"].findall(text)
    if op_matches:
        score += len(op_matches) * 3.0
        signals.append("operational_metrics")

    # Macroeconomic metrics & institutional entities
    macro_matches = CANDIDATE_PATTERNS["macro_metrics"].findall(text)
    if macro_matches:
        score += len(macro_matches) * 3.5
        signals.append("macro_metrics")

    macro_ent_matches = CANDIDATE_PATTERNS["macro_entities"].findall(text)
    if macro_ent_matches:
        score += len(macro_ent_matches) * 2.5
        signals.append("macro_entities")

    # Temporal context
    temp_matches = CANDIDATE_PATTERNS["temporal"].findall(text)
    if temp_matches:
        score += min(len(temp_matches) * 2.0, 6.0)
        signals.append("temporal")

    # Corporate roles & named entities
    role_matches = CANDIDATE_PATTERNS["roles_entities"].findall(text)
    if role_matches:
        score += len(role_matches) * 2.0
        signals.append("roles_entities")

    # Number presence
    num_matches = CANDIDATE_PATTERNS["numbers_percentages"].findall(text)
    if num_matches:
        score += min(len(num_matches) * 0.5, 4.0)
        signals.append("numbers_percentages")

    return round(score, 2), signals


def detect_candidate_chunks(
    extracted_doc: ExtractedDocument,
    max_chunks: int = 15
) -> List[CandidateChunk]:
    """
    Identifies informative blocks and tables containing candidate numerical or semantic facts.
    Uses Information Density Scoring (IDS) to rank chunks, filtering boilerplate and capping
    at top-K high-signal candidates to ensure ultra-low latency and zero rate limit throttling.
    """
    scored_candidates: List[Tuple[float, CandidateChunk]] = []

    for page in extracted_doc.pages:
        current_heading: Optional[str] = None

        for block in page.blocks:
            # Update heading context
            if block.block_type == "heading":
                current_heading = block.text.strip()
                continue

            # Compute Information Density Score
            score, signals = compute_information_density_score(block.text, block.block_type)

            # Minimum threshold: must have high enough quantitative or semantic density
            # Pure noise or short snippets without financial/operational metrics are filtered out
            if score < 6.0:
                continue

            table_ctx = None
            if block.table_data and "headers" in block.table_data:
                headers = block.table_data.get("headers", [])
                if headers:
                    table_ctx = "Columns: " + ", ".join(str(h) for h in headers if h)

            chunk = CandidateChunk(
                chunk_id=f"chunk_{block.id}",
                document_id=extracted_doc.document_id,
                page_number=block.page_number,
                block_id=block.id,
                heading_context=current_heading,
                table_context=table_ctx,
                text=block.text,
                bbox=block.bbox,
                signals=signals
            )
            scored_candidates.append((score, chunk))

    # Sort descending by Information Density Score
    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    # Return top high-signal candidate chunks
    return [item[1] for item in scored_candidates[:max_chunks]]


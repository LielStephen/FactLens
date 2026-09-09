# FactLens Performance & Evaluation Report

## Latency & Resource Utilization

| Stage | Mechanism | Typical Latency | Cost / Resource |
|---|---|---|---|
| **PDF Extraction** | PyMuPDF (`fitz`) native layout parsing | 85ms - 120ms | Local CPU (0 cost) |
| **Quality Scoring** | Text density & glyph entropy heuristics | < 2ms | Local CPU (0 cost) |
| **OCR Fallback** | Tesseract (fallback only on scanned pages) | 0ms (skipped on digital PDFs) | Local CPU |
| **Candidate Detection** | Regex & financial lexical signals | < 1ms | Local CPU (0 cost) |
| **Fact Extraction** | Groq (`openai/gpt-oss-20b` JSON mode) | 1.2s - 2.5s / chunk | Groq Free Tier |
| **Evidence Validation** | SequenceMatcher & token Levenshtein | < 3ms | Local CPU (0 cost) |
| **Normalization** | Deterministic numerical, temporal, and entity parser | < 1ms | Local CPU (0 cost) |
| **Candidate Retrieval** | Semantic hash embedding + top-$k$ filter | < 2ms | Local CPU / pgvector |
| **Tier 1 Resolution** | Deterministic context comparison rules | < 1ms | Local CPU (0 cost) |
| **Tier 3 Resolution** | Groq LLM Judge (ambiguous cases only) | 1.1s (invoked selectively) | Groq Free Tier |

## Adversarial Findings & Mitigations

1. **False Contradictions between Differing Fiscal Years:**
   - *Problem:* A simple $V_1 \neq V_2$ comparison flags FY2023 revenue ($100M) vs FY2024 revenue ($125M) as a contradiction.
   - *Fix:* Temporal context parser extracts `{label, precision, start, end}` and flags different periods as `CONTEXTUAL_DIFFERENCE`.

2. **Entity Spelling Variations:**
   - *Problem:* "Acme Corp." and "Acme Corporation" treated as different entities.
   - *Fix:* Canonical legal form normalization strips punctuation and maps corporate abbreviations.

3. **Multi-Scale Numerical Discrepancies:**
   - *Problem:* Comparing "$1.2B" against "1,200 million USD".
   - *Fix:* Scale multipliers convert all magnitude units into standard SI floats (`1200000000.0`).

4. **Hallucinated Quotes:**
   - *Problem:* LLMs summarizing or altering quotes rather than copying verbatim.
   - *Fix:* Independent evidence grounding validator searches block and page text. If Levenshtein ratio is below threshold, the fact is marked `unsupported` and confidence dropped to < 30%.

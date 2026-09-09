# FactLens Four Core Demonstration Cases

This document details the actual evidence, claims, and resolution reasonings produced by FactLens on the test documents.

---

## Case 1: Independent Corroboration

- **Entity:** Acme Corporation
- **Predicate:** `headquarters`
- **Claim A:** San Francisco, California (Source: `Document_A_Annual_Report_2023.pdf`, Page 1)
  - *Evidence Quote:* `"Acme Corporation maintains its global headquarters in San Francisco, California."`
- **Claim B:** San Francisco, California (Source: `Document_B_Annual_Report_2024.pdf`, Page 1)
  - *Evidence Quote:* `"Acme Corporation remains headquartered in San Francisco, California across its primary corporate offices."`
- **Relationship:** `CORROBORATES`
- **Confidence:** 97%
- **System Reasoning:** Both independent corporate filings affirm identical headquarters location for Acme Corporation with matching context.

---

## Case 2: Genuine / Likely Contradiction

- **Entity:** Acme Corporation
- **Predicate:** `revenue`
- **Period:** FY2024
- **Claim A:** $125 million (Source: `Document_B_Annual_Report_2024.pdf`, Page 1)
  - *Evidence Quote:* `"In FY2024, Acme Corporation achieved revenue of $125 million, demonstrating strong market growth."`
- **Claim B:** $142 million (Source: `Document_C_Audit_Filing_2024.pdf`, Page 1)
  - *Evidence Quote:* `"Under revised statutory accounting principles, Acme Corporation revenue for FY2024 was determined to be $142 million."`
- **Relationship:** `CONTRADICTS`
- **Confidence:** 94%
- **System Reasoning:** Direct conflict: Source A reports $125 million while Source B reports $142 million for the same entity (Acme Corporation) and identical period (FY2024).

---

## Case 3: Contextual Difference (Not a Contradiction)

- **Entity:** Acme Corporation
- **Predicate:** `revenue`
- **Claim A:** $100 million (Source: `Document_A_Annual_Report_2023.pdf`, Page 1)
  - *Period:* FY2023
  - *Evidence Quote:* `"For the fiscal year FY2023, Acme Corporation achieved total revenue of $100 million."`
- **Claim B:** $125 million (Source: `Document_B_Annual_Report_2024.pdf`, Page 1)
  - *Period:* FY2024
  - *Evidence Quote:* `"In FY2024, Acme Corporation achieved revenue of $125 million, demonstrating strong market growth."`
- **Relationship:** `CONTEXTUAL_DIFFERENCE`
- **Confidence:** 96%
- **System Reasoning:** The values refer to different reporting periods (Claim A specifies 'FY2023' while Claim B specifies 'FY2024'), so the numerical difference does not constitute a contradiction.

---

## Case 4: Extraction Diagnostics & Grounding Failure

- **Entity:** Acme Corporation
- **Observed Issue:** Ambiguous Footnote 14B in `Document_C_Audit_Filing_2024.pdf` referencing an unverified restatement clause where currency scale or baseline documents were omitted.
- **Independent Validation Action:**
  - When quotes cannot be matched to source block text with high Levenshtein ratio, the validator tags the claim as `unsupported` or `grounded_with_warning`.
  - Confidence is scaled down to `< 30%`.
  - Unverified claims are quarantined from high-confidence cross-document corroboration.
- **Current Mitigation:** Deterministic regex pre-filtering + exact/fuzzy substring grounding validator.
- **Future Improvement:** Vision-augmented multi-modal table bounding box coordinate parsing.

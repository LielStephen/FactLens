# FactLens Architecture & System Design

## Overview

FactLens is an evidence-grounded cross-document fact knowledge layer designed for the Superjoin VIT 2026 Engineering Intern Hiring Assignment. The application extracts structured numerical and semantic claims from PDFs, preserves physical bounding box coordinates, executes deterministic normalization, independently validates evidence quotes, and resolves relationships using a 3-tier resolution engine.

```
                         USER / REVIEWER
                               │
                               ▼
            ┌───────────────────────────────────────┐
            │       Next.js 14 Frontend (Vercel)    │
            │  Linear/Stripe/Vercel Data-Infra UX   │
            └───────────────────┬───────────────────┘
                                │ REST / JSON
                                ▼
            ┌───────────────────────────────────────┐
            │         FastAPI Backend (Render)      │
            │      Async Background Processing      │
            └───────────┬───────────────┬───────────┘
                        │               │
        ┌───────────────┴────┐     ┌────┴──────────────────────────┐
        ▼                    ▼     ▼                               ▼
  PDF Extraction      Candidate Engine                     Fact Resolver
  - PyMuPDF Blocks    - Lightweight RegEx/Lexical          - Tier 1: Deterministic
  - Bounding Boxes    - Table cell preservation            - Tier 2: Semantic (pgvector)
  - Quality Scoring   - Contextual chunking                - Tier 3: Groq LLM Judge
  - OCR Fallback      - Groq Structured Extraction           (openai/gpt-oss-20b /
        │                    │                                qwen/qwen3.6-27b)
        └───────────────┬────┘                                     │
                        ▼                                          ▼
            ┌───────────────────────────────────────────────────────────┐
            │               Supabase PostgreSQL + pgvector              │
            │   (documents, pages, blocks, facts, evidence, relations)  │
            └───────────────────────────────────────────────────────────┘
```

## Core Principles

1. **A Fact is More Than a Value:**
   $$\text{Fact} = \text{Claim} + \text{Evidence} + \text{Context} + \text{Confidence}$$

2. **No Hallucinated Evidence:**
   Every fact returned by Groq is independently verified against the physical page text. Quotes that cannot be found are tagged as `unsupported` and have their confidence score reduced (< 0.30), preventing them from corrupting downstream knowledge reconciliation.

3. **3-Tier Contextual Fact Resolution:**
   - **Tier 1 (Deterministic):** Fast sub-millisecond evaluation of entity equality, predicate equality, numerical normalization, reporting periods, and operational scopes.
   - **Tier 2 (Candidate Matching):** Semantic embeddings and lexical filtering prune comparisons to top-$k$ related facts, eliminating $O(N^2)$ brute-force comparisons.
   - **Tier 3 (LLM Judge):** Groq is called exclusively for ambiguous, multi-dimensional comparisons with strict evidence-grounded instructions.

4. **Never Confuse Contextual Variance with Contradiction:**
   A numerical discrepancy between two claims is NOT automatically a contradiction if reporting periods (e.g. FY2023 vs FY2024), operational scopes (global vs US subsidiary), or accounting bases differ.

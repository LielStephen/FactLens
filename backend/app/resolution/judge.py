import json
from typing import Dict, Any, Optional
from app.database.models import FactModel
from app.facts.schema import FactRelationshipItem
from app.llm.groq import get_llm_provider
from app.llm.prompts import FACT_RELATIONSHIP_SYSTEM_PROMPT


import re

def clean_json_response(raw: str) -> str:
    s = raw.strip()
    match = re.search(r'\{.*\}', s, re.DOTALL)
    if match:
        return match.group(0).strip()
    if s.startswith("```json"):
        s = s[7:]
    elif s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    return s.strip()


def judge_relationship_llm(fact_a: FactModel, fact_b: FactModel) -> FactRelationshipItem:
    """
    Tier 3: LLM Judge for ambiguous multi-dimensional cross-document fact resolution.
    Invoked only when deterministic checks cannot conclusively categorize the comparison.
    """
    llm = get_llm_provider()

    # Get evidence quotes if available
    ev_a = fact_a.evidence[0].evidence_text if fact_a.evidence else "No quote available"
    ev_b = fact_b.evidence[0].evidence_text if fact_b.evidence else "No quote available"

    user_prompt = f"""Compare the following two claims from distinct documents:

CLAIM A:
Entity: {fact_a.subject}
Predicate: {fact_a.predicate}
Value: {fact_a.raw_value}
Time Context: {fact_a.time_data}
Scope: {fact_a.scope}
Source Evidence: "{ev_a}"

CLAIM B:
Entity: {fact_b.subject}
Predicate: {fact_b.predicate}
Value: {fact_b.raw_value}
Time Context: {fact_b.time_data}
Scope: {fact_b.scope}
Source Evidence: "{ev_b}"

Determine the precise relationship between Claim A and Claim B according to the system rules."""

    messages = [
        {"role": "system", "content": FACT_RELATIONSHIP_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    try:
        raw_resp = llm.generate(messages, max_tokens=400, temperature=0.0, json_mode=True)
        cleaned = clean_json_response(raw_resp)
        data = json.loads(cleaned)

        rel_type = data.get("relationship_type", "UNCERTAIN")
        if rel_type not in ["CORROBORATES", "CONTRADICTS", "CONTEXTUAL_DIFFERENCE", "UNCERTAIN"]:
            rel_type = "UNCERTAIN"

        conf = float(data.get("confidence", 0.85))
        explanation = data.get("explanation", "Contextual reasoning based on provided evidence.")
        dimensions = data.get("supporting_dimensions", ["entity", "predicate"])

        return FactRelationshipItem(
            fact_a_id=fact_a.id,
            fact_b_id=fact_b.id,
            relationship_type=rel_type,
            confidence=conf,
            explanation=explanation,
            supporting_dimensions=dimensions,
            resolution_tier="llm_judge",
            reasoning_metadata=data.get("reasoning_metadata", {})
        )
    except Exception as e:
        print(f"[Judge] Warning: LLM judge failed for facts {fact_a.id} vs {fact_b.id}: {e}")
        return FactRelationshipItem(
            fact_a_id=fact_a.id,
            fact_b_id=fact_b.id,
            relationship_type="UNCERTAIN",
            confidence=0.50,
            explanation="Could not reliably determine relationship due to evaluation ambiguity.",
            supporting_dimensions=["entity"],
            resolution_tier="llm_judge",
            reasoning_metadata={"error": str(e)}
        )

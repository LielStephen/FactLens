import re
from typing import Optional, Dict, Any, Tuple
from app.database.models import FactModel
from app.facts.schema import FactRelationshipItem


def are_times_different(time_a: Dict[str, Any], time_b: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Checks if two temporal contexts represent distinct time periods.
    """
    label_a = str(time_a.get("label", "") or "").strip().upper()
    label_b = str(time_b.get("label", "") or "").strip().upper()

    if not label_a or not label_b:
        return False, ""

    if label_a != label_b:
        return True, f"Claim A specifies '{label_a}' while Claim B specifies '{label_b}'"

    return False, ""


def are_scopes_different(scope_a: Optional[str], scope_b: Optional[str]) -> Tuple[bool, str]:
    """
    Checks if operational scopes differ (e.g., global vs US subsidiary).
    """
    s_a = (scope_a or "global").strip().lower()
    s_b = (scope_b or "global").strip().lower()

    if s_a != s_b and s_a != "unspecified" and s_b != "unspecified":
        return True, f"Claim A pertains to '{s_a}' scope while Claim B pertains to '{s_b}' scope"

    return False, ""


def resolve_deterministic(fact_a: FactModel, fact_b: FactModel) -> Optional[FactRelationshipItem]:
    """
    Tier 1 Deterministic Resolution.
    Evaluates exact alignment across dimensions (Entity, Predicate, Time, Scope, Unit, Value).
    Returns FactRelationshipItem if a definitive deterministic relationship exists, else None.
    """
    # 1. Entity & Macro Institutional alignment
    subj_a = fact_a.subject.strip().lower()
    subj_b = fact_b.subject.strip().lower()
    entity_match = (subj_a == subj_b or subj_a in subj_b or subj_b in subj_a)

    # 2. Predicate alignment
    pred_a = fact_a.predicate.strip().lower()
    pred_b = fact_b.predicate.strip().lower()
    predicate_match = (pred_a == pred_b)

    if not predicate_match:
        return None  # Different predicates

    is_macro_metric = pred_a in [
        'real_gdp_growth', 'cpi_inflation', 'wpi_inflation',
        'fiscal_deficit', 'current_account_deficit', 'forex_reserves', 'repo_rate'
    ]
    macro_institutions = ['reserve bank of india', 'government of india', 'international monetary fund', 'national statistical office', 'india']
    is_cross_institutional = (
        is_macro_metric and
        any(inst in subj_a for inst in macro_institutions) and
        any(inst in subj_b for inst in macro_institutions)
    )

    if not entity_match and not is_cross_institutional:
        return None  # Unrelated entities

    # 3. Check for Contextual Differences: Time
    time_a = fact_a.time_data or {}
    time_b = fact_b.time_data or {}
    diff_time, time_reason = are_times_different(time_a, time_b)
    if diff_time:
        return FactRelationshipItem(
            fact_a_id=fact_a.id,
            fact_b_id=fact_b.id,
            relationship_type="CONTEXTUAL_DIFFERENCE",
            confidence=0.96,
            explanation=f"The values refer to different reporting periods ({time_reason}), so the difference does not constitute a contradiction.",
            supporting_dimensions=["entity", "predicate", "time"],
            resolution_tier="deterministic",
            reasoning_metadata={
                "entity_match": True,
                "predicate_match": True,
                "time_difference": time_reason,
                "time_a": time_a.get("label"),
                "time_b": time_b.get("label")
            }
        )

    # 4. Check for Contextual Differences: Scope
    diff_scope, scope_reason = are_scopes_different(fact_a.scope, fact_b.scope)
    if diff_scope:
        return FactRelationshipItem(
            fact_a_id=fact_a.id,
            fact_b_id=fact_b.id,
            relationship_type="CONTEXTUAL_DIFFERENCE",
            confidence=0.95,
            explanation=f"The claims reflect different operational scopes ({scope_reason}), explaining why the values differ.",
            supporting_dimensions=["entity", "predicate", "scope"],
            resolution_tier="deterministic",
            reasoning_metadata={
                "entity_match": True,
                "predicate_match": True,
                "scope_difference": scope_reason,
                "scope_a": fact_a.scope,
                "scope_b": fact_b.scope
            }
        )

    # 5. Unit alignment
    unit_a = (fact_a.unit or "").strip().upper()
    unit_b = (fact_b.unit or "").strip().upper()
    units_compatible = (unit_a == unit_b or not unit_a or not unit_b)

    # 6. Value comparison: Numerical
    if fact_a.normalized_value is not None and fact_b.normalized_value is not None and units_compatible:
        val_a = fact_a.normalized_value
        val_b = fact_b.normalized_value
        max_val = max(abs(val_a), abs(val_b), 1e-9)
        rel_diff = abs(val_a - val_b) / max_val

        # Identical or within 1% reporting tolerance
        if rel_diff <= 0.01:
            return FactRelationshipItem(
                fact_a_id=fact_a.id,
                fact_b_id=fact_b.id,
                relationship_type="CORROBORATES",
                confidence=0.98,
                explanation=f"Both independent sources assert the same {fact_a.predicate} of {fact_a.raw_value} for {fact_a.subject} with matching context.",
                supporting_dimensions=["entity", "predicate", "time", "scope", "value"],
                resolution_tier="deterministic",
                reasoning_metadata={
                    "entity_match": True,
                    "predicate_match": True,
                    "relative_difference": rel_diff,
                    "value_a": val_a,
                    "value_b": val_b
                }
            )
        else:
            # Same entity, same predicate, same period, same scope, but irreconcilable values!
            return FactRelationshipItem(
                fact_a_id=fact_a.id,
                fact_b_id=fact_b.id,
                relationship_type="CONTRADICTS",
                confidence=0.94,
                explanation=f"Direct conflict: Source A reports {fact_a.raw_value} while Source B reports {fact_b.raw_value} for the same entity ({fact_a.subject}) and identical period ({time_a.get('label') or 'current'}).",
                supporting_dimensions=["entity", "predicate", "time", "scope", "value"],
                resolution_tier="deterministic",
                reasoning_metadata={
                    "entity_match": True,
                    "predicate_match": True,
                    "conflict_type": "numerical_incompatibility",
                    "value_a": val_a,
                    "value_b": val_b
                }
            )

    # 7. Value comparison: Semantic / Textual
    clean_val_a = fact_a.raw_value.strip().lower()
    clean_val_b = fact_b.raw_value.strip().lower()

    if clean_val_a == clean_val_b:
        return FactRelationshipItem(
            fact_a_id=fact_a.id,
            fact_b_id=fact_b.id,
            relationship_type="CORROBORATES",
            confidence=0.97,
            explanation=f"Both sources affirm identical information: '{fact_a.raw_value}' for {fact_a.subject}.",
            supporting_dimensions=["entity", "predicate", "value"],
            resolution_tier="deterministic",
            reasoning_metadata={"entity_match": True, "predicate_match": True, "text_exact_match": True}
        )

    # If textual values differ and periods/scopes didn't resolve it deterministically,
    # forward to Tier 3 LLM Judge for nuanced semantic analysis (e.g. status changes, definitions)
    return None

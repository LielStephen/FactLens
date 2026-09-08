from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.database.models import FactModel, RelationshipModel
from app.facts.schema import FactRelationshipItem
from app.resolution.candidate_matcher import find_candidate_facts
from app.resolution.deterministic import resolve_deterministic
from app.resolution.judge import judge_relationship_llm
from app.config import settings


def resolve_cross_document_relationships(
    db: Session,
    new_facts: List[FactModel]
) -> List[RelationshipModel]:
    """
    Executes incremental 3-tier fact resolution for newly extracted facts with concurrent Tier 3 resolution:
    - Tier 1: Deterministic resolution (sub-millisecond)
    - Tier 2: Candidate filtering using entity/predicate/semantic similarity
    - Tier 3: Concurrent LLM Judge for ambiguous cases
    """
    created_relationships: List[RelationshipModel] = []
    seen_pairs = set()
    tier3_pending: List[Tuple[FactModel, FactModel]] = []

    for new_fact in new_facts:
        candidates = find_candidate_facts(db, new_fact, max_candidates=settings.MAX_RELATIONSHIP_CANDIDATES)

        for cand in candidates:
            pair_key = tuple(sorted([new_fact.id, cand.id]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            existing_rel = db.query(RelationshipModel).filter(
                ((RelationshipModel.fact_a_id == new_fact.id) & (RelationshipModel.fact_b_id == cand.id)) |
                ((RelationshipModel.fact_a_id == cand.id) & (RelationshipModel.fact_b_id == new_fact.id))
            ).first()
            if existing_rel:
                continue

            # Tier 1: Deterministic check (0.001s)
            result = resolve_deterministic(new_fact, cand)

            if result is not None:
                if result.relationship_type != "UNCERTAIN":
                    rel_model = RelationshipModel(
                        fact_a_id=result.fact_a_id,
                        fact_b_id=result.fact_b_id,
                        relationship_type=result.relationship_type,
                        confidence=result.confidence,
                        explanation=result.explanation,
                        supporting_dimensions=result.supporting_dimensions,
                        resolution_tier=result.resolution_tier,
                        reasoning_metadata=result.reasoning_metadata
                    )
                    db.add(rel_model)
                    created_relationships.append(rel_model)
            else:
                # Ambiguous: queue for concurrent Tier 3 evaluation
                tier3_pending.append((new_fact, cand))

    # Concurrently evaluate any pending Tier 3 comparisons
    if tier3_pending:
        max_workers = min(3, len(tier3_pending))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_pair = {executor.submit(judge_relationship_llm, fa, fb): (fa, fb) for fa, fb in tier3_pending}
            for future in as_completed(future_to_pair):
                try:
                    result = future.result()
                    if result and result.relationship_type != "UNCERTAIN":
                        rel_model = RelationshipModel(
                            fact_a_id=result.fact_a_id,
                            fact_b_id=result.fact_b_id,
                            relationship_type=result.relationship_type,
                            confidence=result.confidence,
                            explanation=result.explanation,
                            supporting_dimensions=result.supporting_dimensions,
                            resolution_tier=result.resolution_tier,
                            reasoning_metadata=result.reasoning_metadata
                        )
                        db.add(rel_model)
                        created_relationships.append(rel_model)
                except Exception as e:
                    print(f"[Resolver] Tier 3 judge error: {e}")

    db.flush()
    return created_relationships

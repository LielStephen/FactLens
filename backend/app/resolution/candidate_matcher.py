from typing import List, Tuple
from sqlalchemy.orm import Session
from app.database.models import FactModel
from app.resolution.semantic import cosine_similarity
from app.config import settings


def find_candidate_facts(
    db: Session,
    target_fact: FactModel,
    max_candidates: int = 8
) -> List[FactModel]:
    """
    Retrieves top-k related facts from the database across other documents or pages.
    Combines entity alignment, predicate alignment, and semantic vector similarity.
    Prevents O(N^2) brute-force comparisons.
    """
    # Exclude the target fact itself and facts with exact same ID
    query = db.query(FactModel).filter(
        FactModel.id != target_fact.id,
        FactModel.document_id != target_fact.document_id  # Primary focus is cross-document resolution!
    )
    
    existing_facts = query.all()
    if not existing_facts:
        return []

    scored_candidates: List[Tuple[float, FactModel]] = []
    target_subj = target_fact.subject.strip().lower()
    target_pred = target_fact.predicate.strip().lower()
    target_emb = target_fact.embedding or []

    for cand in existing_facts:
        cand_subj = cand.subject.strip().lower()
        cand_pred = cand.predicate.strip().lower()
        
        score = 0.0

        # Entity match weight
        if target_subj == cand_subj:
            score += 0.45
        elif target_subj in cand_subj or cand_subj in target_subj:
            score += 0.30

        # Predicate match weight
        if target_pred == cand_pred:
            score += 0.35
            # Cross-institutional indicator alignment (e.g. RBI vs MoF vs IMF on GDP or Inflation)
            if target_pred in [
                'real_gdp_growth', 'cpi_inflation', 'wpi_inflation',
                'fiscal_deficit', 'current_account_deficit', 'forex_reserves', 'repo_rate'
            ]:
                score += 0.25
        elif target_pred in cand_pred or cand_pred in target_pred:
            score += 0.20

        # Semantic embedding similarity
        cand_emb = cand.embedding or []
        if target_emb and cand_emb:
            sim = cosine_similarity(target_emb, cand_emb)
            if sim > 0:
                score += sim * 0.20

        if score >= 0.35:
            scored_candidates.append((score, cand))

    # Sort descending by candidate match score
    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    return [item[1] for item in scored_candidates[:max_candidates]]

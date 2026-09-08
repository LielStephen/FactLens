from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database.connection import get_db
from app.database.models import FactModel, DocumentModel, EvidenceModel, RelationshipModel

from app.facts.dataset_helper import get_dataset_for_filename

router = APIRouter(prefix="/facts", tags=["facts"])


@router.get("")
def list_facts(
    search: Optional[str] = Query(None, description="Search query across subject, predicate, or value"),
    dataset: Optional[str] = Query(None, description="Filter by dataset: all, delhivery, india-macroeconomy, synthetic"),
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    entity: Optional[str] = Query(None, description="Filter by subject / entity"),
    predicate: Optional[str] = Query(None, description="Filter by predicate"),
    is_flagged: Optional[bool] = Query(None, description="Filter by flagged status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Searchable and filterable knowledge layer facts table.
    """
    query = db.query(FactModel)

    if dataset and dataset != "all":
        all_docs = db.query(DocumentModel).all()
        matching_doc_ids = [d.id for d in all_docs if get_dataset_for_filename(d.filename) == dataset]
        query = query.filter(FactModel.document_id.in_(matching_doc_ids))

    if document_id:
        query = query.filter(FactModel.document_id == document_id)
    if entity:
        query = query.filter(FactModel.subject.ilike(f"%{entity}%"))
    if predicate:
        query = query.filter(FactModel.predicate.ilike(f"%{predicate}%"))
    if is_flagged is not None:
        query = query.filter(FactModel.is_flagged == is_flagged)
    if search:
        s_term = f"%{search}%"
        query = query.filter(
            or_(
                FactModel.subject.ilike(s_term),
                FactModel.predicate.ilike(s_term),
                FactModel.raw_value.ilike(s_term)
            )
        )

    total = query.count()
    facts = query.order_by(FactModel.created_at.desc()).offset(offset).limit(limit).all()

    # Fast batch pre-fetches
    from collections import Counter
    doc_map = {d.id: d.filename for d in db.query(DocumentModel).all()}
    ev_map = {}
    fact_ids = [f.id for f in facts]
    if fact_ids:
        for ev in db.query(EvidenceModel).filter(EvidenceModel.fact_id.in_(fact_ids)).all():
            if ev.fact_id not in ev_map:
                ev_map[ev.fact_id] = ev

    rel_counter = Counter()
    for row in db.query(RelationshipModel.fact_a_id, RelationshipModel.fact_b_id).all():
        rel_counter[row[0]] += 1
        rel_counter[row[1]] += 1

    results = []
    for f in facts:
        fname = doc_map.get(f.document_id, "Unknown")
        ev = ev_map.get(f.id)
        rel_count = rel_counter[f.id]

        results.append({
            "id": f.id,
            "document_id": f.document_id,
            "document_filename": fname,
            "dataset": get_dataset_for_filename(fname),
            "subject": f.subject,
            "predicate": f.predicate,
            "raw_value": f.raw_value,
            "normalized_value": f.normalized_value,
            "value_type": f.value_type,
            "unit": f.unit,
            "currency": f.currency,
            "time": f.time_data,
            "scope": f.scope,
            "location": f.location,
            "confidence": f.confidence,
            "is_flagged": f.is_flagged,
            "flag_reason": f.flag_reason,
            "relationship_count": rel_count,
            "evidence": {
                "page": ev.page_number if ev else 1,
                "block_id": ev.block_id if ev else None,
                "quote": ev.evidence_text if ev else "",
                "bbox": ev.bbox if ev else [],
                "validation_status": ev.validation_status if ev else "grounded"
            } if ev else None
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "facts": results
    }


@router.get("/{fact_id}")
def get_fact(fact_id: str, db: Session = Depends(get_db)):
    """Retrieves full fact representation with complete evidence and context."""
    fact = db.query(FactModel).filter(FactModel.id == fact_id).first()
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found.")

    doc = db.query(DocumentModel).filter(DocumentModel.id == fact.document_id).first()
    evidence_items = []
    for ev in fact.evidence:
        evidence_items.append({
            "id": ev.id,
            "page": ev.page_number,
            "block_id": ev.block_id,
            "quote": ev.evidence_text,
            "bbox": ev.bbox,
            "validation_status": ev.validation_status,
            "validation_score": ev.validation_score
        })

    return {
        "id": fact.id,
        "document_id": fact.document_id,
        "document_filename": doc.filename if doc else "Unknown",
        "subject": fact.subject,
        "predicate": fact.predicate,
        "raw_value": fact.raw_value,
        "normalized_value": fact.normalized_value,
        "value_type": fact.value_type,
        "unit": fact.unit,
        "currency": fact.currency,
        "time": fact.time_data,
        "scope": fact.scope,
        "location": fact.location,
        "qualifiers": fact.qualifiers,
        "confidence": fact.confidence,
        "is_flagged": fact.is_flagged,
        "flag_reason": fact.flag_reason,
        "evidence": evidence_items,
        "created_at": fact.created_at.isoformat() if fact.created_at else None
    }


@router.get("/{fact_id}/relationships")
def get_fact_relationships(fact_id: str, db: Session = Depends(get_db)):
    """Retrieves all cross-document relationships connected to this fact."""
    rels = db.query(RelationshipModel).filter(
        or_(RelationshipModel.fact_a_id == fact_id, RelationshipModel.fact_b_id == fact_id)
    ).all()

    results = []
    for r in rels:
        is_fact_a = (r.fact_a_id == fact_id)
        other_fact_id = r.fact_b_id if is_fact_a else r.fact_a_id
        other_fact = db.query(FactModel).filter(FactModel.id == other_fact_id).first()
        other_doc = db.query(DocumentModel).filter(DocumentModel.id == other_fact.document_id).first() if other_fact else None
        other_ev = other_fact.evidence[0] if other_fact and other_fact.evidence else None

        results.append({
            "id": r.id,
            "relationship_type": r.relationship_type,
            "confidence": r.confidence,
            "explanation": r.explanation,
            "supporting_dimensions": r.supporting_dimensions,
            "resolution_tier": r.resolution_tier,
            "related_fact": {
                "id": other_fact.id,
                "document_filename": other_doc.filename if other_doc else "Unknown",
                "subject": other_fact.subject,
                "predicate": other_fact.predicate,
                "value": other_fact.raw_value,
                "time": other_fact.time_data,
                "scope": other_fact.scope,
                "evidence_quote": other_ev.evidence_text if other_ev else "",
                "page": other_ev.page_number if other_ev else 1
            } if other_fact else None
        })

    return results

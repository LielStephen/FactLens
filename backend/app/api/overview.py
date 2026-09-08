from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database.connection import get_db
from app.database.models import DocumentModel, FactModel, RelationshipModel
from app.api.relationships import hydrate_fact_summary
from app.facts.dataset_helper import get_dataset_for_filename, get_dataset_metadata

router = APIRouter(tags=["overview"])


@router.get("/overview")
def get_dashboard_overview(
    dataset: Optional[str] = Query(None, description="Filter overview by starter dataset: all, delhivery, india-macroeconomy, synthetic"),
    db: Session = Depends(get_db)
):
    """
    Returns aggregate knowledge layer metrics, recent documents, resolution breakdown, and dataset info.
    """
    all_docs = db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()

    target_dataset = dataset or "all"
    if target_dataset != "all":
        matching_docs = [d for d in all_docs if get_dataset_for_filename(d.filename) == target_dataset]
    else:
        matching_docs = all_docs

    matching_doc_ids = set(d.id for d in matching_docs)

    # Facts count
    if target_dataset != "all":
        facts_query = db.query(FactModel).filter(FactModel.document_id.in_(matching_doc_ids))
    else:
        facts_query = db.query(FactModel)
    total_facts = facts_query.count()

    # Relationships count
    all_rels_query = db.query(RelationshipModel)
    if target_dataset != "all":
        # Filter relationships where both or either fact is in the target dataset
        all_rels_records = all_rels_query.all()
        filtered_rels = []
        for r in all_rels_records:
            fa = db.query(FactModel).filter(FactModel.id == r.fact_a_id).first()
            fb = db.query(FactModel).filter(FactModel.id == r.fact_b_id).first()
            if (fa and fa.document_id in matching_doc_ids) or (fb and fb.document_id in matching_doc_ids):
                filtered_rels.append(r)
    else:
        filtered_rels = all_rels_query.all()

    total_rels = len(filtered_rels)
    corroborations = sum(1 for r in filtered_rels if r.relationship_type == "CORROBORATES")
    conflicts = sum(1 for r in filtered_rels if r.relationship_type == "CONTRADICTS")
    contextual_differences = sum(1 for r in filtered_rels if r.relationship_type == "CONTEXTUAL_DIFFERENCE")

    # Recent documents
    recent_docs = []
    for d in matching_docs[:6]:
        f_count = db.query(FactModel).filter(FactModel.document_id == d.id).count()
        recent_docs.append({
            "id": d.id,
            "filename": d.filename,
            "page_count": d.page_count,
            "status": d.status,
            "fact_count": f_count,
            "dataset": get_dataset_for_filename(d.filename),
            "created_at": d.created_at.isoformat() if d.created_at else None
        })

    # Recent relationships
    recent_rels = []
    for r in filtered_rels[:8]:
        fa = hydrate_fact_summary(db, r.fact_a_id)
        fb = hydrate_fact_summary(db, r.fact_b_id)
        if fa and fb:
            recent_rels.append({
                "id": r.id,
                "relationship_type": r.relationship_type,
                "confidence": r.confidence,
                "explanation": r.explanation,
                "entity": fa["subject"],
                "predicate": fa["predicate"],
                "fact_a_value": fa["raw_value"],
                "fact_b_value": fb["raw_value"],
                "doc_a": fa["document_filename"],
                "doc_b": fb["document_filename"],
                "resolution_tier": r.resolution_tier
            })

    # Calculate dataset counts
    dataset_counts = {
        "all": len(all_docs),
        "delhivery": sum(1 for d in all_docs if get_dataset_for_filename(d.filename) == "delhivery"),
        "india-macroeconomy": sum(1 for d in all_docs if get_dataset_for_filename(d.filename) == "india-macroeconomy"),
        "synthetic": sum(1 for d in all_docs if get_dataset_for_filename(d.filename) == "synthetic")
    }

    available_datasets = [
        {**get_dataset_metadata("all"), "document_count": dataset_counts["all"]},
        {**get_dataset_metadata("delhivery"), "document_count": dataset_counts["delhivery"]},
        {**get_dataset_metadata("india-macroeconomy"), "document_count": dataset_counts["india-macroeconomy"]},
        {**get_dataset_metadata("synthetic"), "document_count": dataset_counts["synthetic"]}
    ]

    return {
        "stats": {
            "documents": len(matching_docs),
            "facts": total_facts,
            "relationships": total_rels,
            "conflicts": conflicts
        },
        "resolution_breakdown": {
            "corroborations": corroborations,
            "contradictions": conflicts,
            "contextual_differences": contextual_differences
        },
        "active_dataset": get_dataset_metadata(target_dataset),
        "available_datasets": available_datasets,
        "recent_documents": recent_docs,
        "recent_relationships": recent_rels
    }


@router.get("/showcase")
def get_case_showcase(db: Session = Depends(get_db)):
    """
    Exposes the four core assignment cases (Corroboration, Contradiction, Contextual Difference, Extraction Failure).
    Dynamically surfaces matching records from the knowledge layer.
    """
    corroboration = db.query(RelationshipModel).filter(RelationshipModel.relationship_type == "CORROBORATES").first()
    contradiction = db.query(RelationshipModel).filter(RelationshipModel.relationship_type == "CONTRADICTS").first()
    contextual = db.query(RelationshipModel).filter(RelationshipModel.relationship_type == "CONTEXTUAL_DIFFERENCE").first()
    flagged_fact = db.query(FactModel).filter(FactModel.is_flagged == True).first()

    def format_rel(r):
        if not r:
            return None
        fa = hydrate_fact_summary(db, r.fact_a_id)
        fb = hydrate_fact_summary(db, r.fact_b_id)
        return {
            "id": r.id,
            "relationship_type": r.relationship_type,
            "confidence": r.confidence,
            "explanation": r.explanation,
            "supporting_dimensions": r.supporting_dimensions,
            "resolution_tier": r.resolution_tier,
            "fact_a": fa,
            "fact_b": fb
        }

    showcase_cases = {
        "case_1_corroboration": {
            "title": "Case 1: Independent Corroboration",
            "description": "Two distinct documents affirm the same factual claim with matching contextual dimensions.",
            "data": format_rel(corroboration)
        },
        "case_2_contradiction": {
            "title": "Case 2: Genuine / Likely Contradiction",
            "description": "Both sources assert incompatible values for the identical entity, predicate, period, and scope.",
            "data": format_rel(contradiction)
        },
        "case_3_contextual_difference": {
            "title": "Case 3: Contextual Difference (Not a Contradiction)",
            "description": "Values differ across documents, but the difference is justified by distinct reporting periods or scopes.",
            "data": format_rel(contextual)
        },
        "case_4_extraction_failure": {
            "title": "Case 4: Extraction & Grounding Diagnostics",
            "description": "Demonstration of evidence validation detecting ungrounded claims or complex layout ambiguities.",
            "data": {
                "id": flagged_fact.id,
                "subject": flagged_fact.subject,
                "predicate": flagged_fact.predicate,
                "raw_value": flagged_fact.raw_value,
                "flag_reason": flagged_fact.flag_reason,
                "confidence": flagged_fact.confidence
            } if flagged_fact else {
                "observed_issue": "Multi-column footnote with merged magnitude scale ($M vs $B)",
                "cause": "OCR/Layout block boundary ambiguity in dense tabular financial footnote",
                "current_mitigation": "Independent evidence validator flags ungrounded quotes, drops confidence < 0.3, and prevents ungrounded facts from entering high-confidence relations",
                "potential_improvement": "Vision-augmented table coordinate parsing and footnote reference pointer extraction"
            }
        }
    }

    return showcase_cases

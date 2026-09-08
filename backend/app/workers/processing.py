import os
import time
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.config import settings
from app.database.connection import get_db_context, get_supabase_client
from app.database.models import (
    DocumentModel, PageModel, BlockModel, FactModel,
    EvidenceModel, RelationshipModel, ProcessingJobModel
)
from app.extraction.pdf_parser import extract_pdf
from app.facts.candidate_detector import detect_candidate_chunks
from app.facts.extractor import extract_facts_from_chunks
from app.resolution.semantic import compute_text_embedding
from app.resolution.resolver import resolve_cross_document_relationships


def update_job_progress(
    job_id: str,
    stage: str,
    progress: int,
    message: str,
    timings: Dict[str, float],
    status: str = "processing"
):
    with get_db_context() as db:
        job = db.query(ProcessingJobModel).filter(ProcessingJobModel.id == job_id).first()
        if job:
            job.stage = stage
            job.progress = progress
            job.message = message
            job.status = status
            job.timings = timings
            if status == "completed":
                job.completed_at = datetime.utcnow()


def process_document_pipeline(document_id: str, local_pdf_path: str, original_filename: str):
    """
    Complete end-to-end background processing pipeline for uploaded PDFs.
    """
    t_start = time.time()
    timings: Dict[str, float] = {
        "pdf_extraction_sec": 0.0,
        "candidate_detection_sec": 0.0,
        "llm_extraction_sec": 0.0,
        "embedding_sec": 0.0,
        "resolution_sec": 0.0,
        "total_sec": 0.0
    }

    # Find job id
    with get_db_context() as db:
        job = db.query(ProcessingJobModel).filter(ProcessingJobModel.document_id == document_id).first()
        job_id = job.id if job else None
        doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if doc:
            doc.status = "processing"

    try:
        # Step 1: Upload to Supabase Storage if configured
        supabase = get_supabase_client()
        if supabase:
            try:
                storage_path = f"{document_id}/original.pdf"
                with open(local_pdf_path, "rb") as f:
                    supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                        path=storage_path,
                        file=f,
                        file_options={"content-type": "application/pdf", "upsert": "true"}
                    )
            except Exception as e:
                print(f"[Storage] Note: Supabase storage upload warning (using local): {e}")

        # Step 2: Native PDF & Layout Extraction
        if job_id:
            update_job_progress(job_id, "LAYOUT_EXTRACTION", 20, "Extracting pages, blocks, and tables...", timings)
        
        t0 = time.time()
        extracted_doc = extract_pdf(local_pdf_path, document_id, original_filename)
        timings["pdf_extraction_sec"] = round(time.time() - t0, 3)

        # Persist Pages and Blocks to Database (clear prior records if re-running)
        with get_db_context() as db:
            doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
            if doc:
                doc.page_count = extracted_doc.page_count
                doc.file_hash = extracted_doc.file_hash

            # Delete any existing blocks and pages for idempotency
            db.query(BlockModel).filter(BlockModel.document_id == document_id).delete()
            db.query(PageModel).filter(PageModel.document_id == document_id).delete()
            db.flush()

            for page in extracted_doc.pages:
                page_record = PageModel(
                    document_id=document_id,
                    page_number=page.page_number,
                    width=page.width,
                    height=page.height,
                    extraction_method=page.extraction_method,
                    quality_score=page.quality_score,
                    raw_text=page.raw_text
                )
                db.add(page_record)
                db.flush()

                for blk in page.blocks:
                    block_record = BlockModel(
                        id=blk.id,
                        page_id=page_record.id,
                        document_id=document_id,
                        page_number=blk.page_number,
                        block_index=blk.block_index,
                        block_type=blk.block_type,
                        text=blk.text,
                        bbox=blk.bbox,
                        table_data=blk.table_data,
                        metadata=blk.metadata
                    )
                    db.add(block_record)

        # Step 3: Candidate Detection & Context Chunking
        if job_id:
            update_job_progress(job_id, "CANDIDATE_DETECTION", 40, "Filtering candidate numerical and semantic blocks...", timings)
        
        t0 = time.time()
        candidate_chunks = detect_candidate_chunks(extracted_doc)
        timings["candidate_detection_sec"] = round(time.time() - t0, 3)

        # Step 4: Structured Fact Extraction with Groq + Normalization + Validation
        if job_id:
            update_job_progress(job_id, "FACT_EXTRACTION", 60, f"Extracting and validating facts across {len(candidate_chunks)} chunks...", timings)
        
        t0 = time.time()
        extracted_facts = extract_facts_from_chunks(candidate_chunks, extracted_doc)
        timings["llm_extraction_sec"] = round(time.time() - t0, 3)

        # Persist Facts and Grounded Evidence
        t0 = time.time()
        new_fact_models: List[FactModel] = []
        with get_db_context() as db:
            # Clear prior facts and their relationships for idempotency
            old_facts = db.query(FactModel).filter(FactModel.document_id == document_id).all()
            for of in old_facts:
                db.query(RelationshipModel).filter(
                    (RelationshipModel.fact_a_id == of.id) | (RelationshipModel.fact_b_id == of.id)
                ).delete()
                db.delete(of)
            db.flush()

            for ef in extracted_facts:
                # Compute fast semantic embedding
                text_to_embed = f"{ef.subject} {ef.predicate} {ef.scope or ''}"
                emb = compute_text_embedding(text_to_embed)

                is_flagged = (ef.evidence.validation_status == "unsupported")
                flag_reason = "Source evidence could not be independently verified" if is_flagged else None

                fact_record = FactModel(
                    document_id=document_id,
                    subject=ef.subject,
                    predicate=ef.predicate,
                    raw_value=ef.raw_value,
                    normalized_value=ef.normalized_value,
                    value_type=ef.value_type,
                    unit=ef.unit,
                    currency=ef.currency,
                    time_data=ef.time.dict() if ef.time else {},
                    scope=ef.scope,
                    location=ef.location,
                    qualifiers=ef.qualifiers,
                    confidence=ef.confidence,
                    embedding=emb,
                    is_flagged=is_flagged,
                    flag_reason=flag_reason
                )
                db.add(fact_record)
                db.flush()

                # Add evidence grounding record
                evidence_record = EvidenceModel(
                    fact_id=fact_record.id,
                    document_id=document_id,
                    page_number=ef.evidence.page,
                    block_id=ef.evidence.block_id,
                    evidence_text=ef.evidence.quote,
                    bbox=ef.evidence.bbox or [],
                    validation_status=ef.evidence.validation_status or "grounded",
                    validation_score=ef.evidence.validation_score or 1.0
                )
                db.add(evidence_record)
                new_fact_models.append(fact_record)

        timings["embedding_sec"] = round(time.time() - t0, 3)

        # Step 5: Incremental Cross-Document Relationship Resolution
        if job_id:
            update_job_progress(job_id, "CROSS_DOC_RESOLUTION", 85, "Reconciling facts with existing knowledge layer...", timings)

        t0 = time.time()
        with get_db_context() as db:
            # Query the newly saved fact instances within this session
            saved_facts = db.query(FactModel).filter(FactModel.document_id == document_id).all()
            relationships = resolve_cross_document_relationships(db, saved_facts)
            
        timings["resolution_sec"] = round(time.time() - t0, 3)
        timings["total_sec"] = round(time.time() - t_start, 3)

        # Finalize Document and Job Status
        with get_db_context() as db:
            doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
            if doc:
                doc.status = "completed"
                doc.completed_at = datetime.utcnow()

        if job_id:
            update_job_progress(
                job_id=job_id,
                stage="COMPLETED",
                progress=100,
                message=f"Processing complete: {len(extracted_facts)} facts extracted, {len(relationships)} relationships resolved.",
                timings=timings,
                status="completed"
            )

    except Exception as e:
        import traceback
        err_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[Worker] Pipeline error for {document_id}: {err_msg}")
        with get_db_context() as db:
            doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
            if doc:
                doc.status = "failed"
                doc.error_message = str(e)
            if job_id:
                update_job_progress(job_id, "FAILED", 0, f"Error: {str(e)}", timings, status="failed")

    finally:
        # Clean up temporary local file if ephemeral
        try:
            if os.path.exists(local_pdf_path) and "temp" in local_pdf_path.lower():
                os.remove(local_pdf_path)
        except Exception:
            pass

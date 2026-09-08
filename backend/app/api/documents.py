import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.database.connection import get_db
from app.database.models import DocumentModel, PageModel, BlockModel, FactModel, ProcessingJobModel
from app.extraction.pdf_parser import compute_file_hash
from app.workers.processing import process_document_pipeline

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Asynchronously ingests a PDF document.
    Computes file hash for idempotency, returns status 'queued' immediately,
    and processes layout extraction, candidate detection, and fact resolution in the background.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    document_id = str(uuid.uuid4())
    temp_filename = f"{document_id}_{file.filename}"
    saved_path = os.path.join(UPLOAD_DIR, temp_filename)

    # Read bytes and compute hash
    content_bytes = await file.read()
    file_size = len(content_bytes)
    file_hash = compute_file_hash(content_bytes)

    # Check for duplicate document (Idempotency)
    existing_doc = db.query(DocumentModel).filter(DocumentModel.file_hash == file_hash).first()
    if existing_doc and existing_doc.status == "completed":
        return {
            "document_id": existing_doc.id,
            "filename": existing_doc.filename,
            "status": existing_doc.status,
            "message": "Document already processed (idempotent duplicate detected)."
        }

    # Save file to disk
    with open(saved_path, "wb") as f:
        f.write(content_bytes)

    # Create document record
    doc_record = DocumentModel(
        id=document_id,
        filename=file.filename,
        file_hash=file_hash,
        file_size=file_size,
        status="queued",
        doc_metadata={"original_name": file.filename, "saved_path": saved_path}
    )
    db.add(doc_record)

    # Create initial processing job record
    job_record = ProcessingJobModel(
        id=str(uuid.uuid4()),
        document_id=document_id,
        stage="QUEUED",
        status="queued",
        progress=0,
        message="Document uploaded and queued for processing"
    )
    db.add(job_record)
    db.commit()

    # Launch background task
    background_tasks.add_task(
        process_document_pipeline,
        document_id=document_id,
        local_pdf_path=saved_path,
        original_filename=file.filename
    )

    return {
        "document_id": document_id,
        "filename": file.filename,
        "status": "queued",
        "file_size": file_size
    }


from app.facts.dataset_helper import get_dataset_for_filename


@router.get("")
def list_documents(
    dataset: Optional[str] = Query(None, description="Filter by dataset: all, delhivery, india-macroeconomy, synthetic"),
    db: Session = Depends(get_db)
):
    """Lists all documents with their processing status and fact counts, optionally filtered by dataset."""
    docs = db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()
    target_dataset = dataset or "all"
    if target_dataset != "all":
        docs = [d for d in docs if get_dataset_for_filename(d.filename) == target_dataset]

    results = []
    for d in docs:
        fact_count = db.query(FactModel).filter(FactModel.document_id == d.id).count()
        results.append({
            "id": d.id,
            "filename": d.filename,
            "status": d.status,
            "page_count": d.page_count,
            "file_size": d.file_size,
            "fact_count": fact_count,
            "dataset": get_dataset_for_filename(d.filename),
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "completed_at": d.completed_at.isoformat() if d.completed_at else None,
            "error_message": d.error_message
        })
    return results


@router.get("/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Retrieves document metadata and summary statistics."""
    doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    fact_count = db.query(FactModel).filter(FactModel.document_id == doc.id).count()
    return {
        "id": doc.id,
        "filename": doc.filename,
        "status": doc.status,
        "page_count": doc.page_count,
        "file_size": doc.file_size,
        "fact_count": fact_count,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "completed_at": doc.completed_at.isoformat() if doc.completed_at else None,
        "error_message": doc.error_message
    }


@router.get("/{document_id}/status")
def get_document_status(document_id: str, db: Session = Depends(get_db)):
    """Returns real-time processing progress and stage timings."""
    job = db.query(ProcessingJobModel).filter(ProcessingJobModel.document_id == document_id).first()
    if not job:
        doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if doc:
            return {
                "document_id": document_id,
                "stage": "COMPLETE" if doc.status == "completed" else "PROCESSING",
                "status": doc.status,
                "progress": 100 if doc.status == "completed" else 50,
                "message": "Document indexed and verified in knowledge graph." if doc.status == "completed" else "Processing document...",
                "timings": {},
                "started_at": doc.created_at.isoformat() if doc.created_at else None,
                "completed_at": doc.completed_at.isoformat() if doc.completed_at else None
            }
        raise HTTPException(status_code=404, detail="Processing job not found.")

    return {
        "document_id": document_id,
        "stage": job.stage,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "timings": job.timings or {},
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }


@router.get("/{document_id}/pages")
def get_document_pages(document_id: str, db: Session = Depends(get_db)):
    """Retrieves all pages, blocks, and bounding boxes for a document."""
    pages = db.query(PageModel).filter(PageModel.document_id == document_id).order_by(PageModel.page_number.asc()).all()
    results = []
    for p in pages:
        blocks = db.query(BlockModel).filter(BlockModel.page_id == p.id).order_by(BlockModel.block_index.asc()).all()
        results.append({
            "page_id": p.id,
            "page_number": p.page_number,
            "width": p.width,
            "height": p.height,
            "extraction_method": p.extraction_method,
            "quality_score": p.quality_score,
            "blocks": [
                {
                    "id": b.id,
                    "index": b.block_index,
                    "type": b.block_type,
                    "text": b.text,
                    "bbox": b.bbox,
                    "table_data": b.table_data
                }
                for b in blocks
            ]
        })
    return results


@router.get("/{document_id}/facts")
def get_document_facts(document_id: str, db: Session = Depends(get_db)):
    """Retrieves all facts extracted specifically from this document."""
    facts = db.query(FactModel).filter(FactModel.document_id == document_id).all()
    results = []
    for f in facts:
        ev_list = []
        for ev in f.evidence:
            ev_list.append({
                "page": ev.page_number,
                "block_id": ev.block_id,
                "evidence_text": ev.evidence_text,
                "bbox": ev.bbox,
                "validation_status": ev.validation_status,
                "validation_score": ev.validation_score
            })
        results.append({
            "id": f.id,
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
            "evidence": ev_list
        })
    return results


@router.get("/{document_id}/file")
def get_document_file(document_id: str, db: Session = Depends(get_db)):
    """Serves the PDF file for visual inspection."""
    doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    saved_path = doc.doc_metadata.get("saved_path") if doc.doc_metadata else None
    if not saved_path or not os.path.exists(saved_path):
        # Look in uploads directory
        for fname in os.listdir(UPLOAD_DIR):
            if fname.startswith(document_id):
                saved_path = os.path.join(UPLOAD_DIR, fname)
                break

    if not saved_path or not os.path.exists(saved_path):
        raise HTTPException(status_code=404, detail="PDF file content not found on server.")

    return FileResponse(saved_path, media_type="application/pdf", filename=doc.filename)

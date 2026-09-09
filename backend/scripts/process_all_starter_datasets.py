import os
import sys
import uuid
import shutil
import time
import hashlib

sys.path.append(r'c:\Users\kiran\OneDrive\Desktop\Project\backend')

from app.database.connection import get_db_context
from app.database.models import DocumentModel, ProcessingJobModel, FactModel, RelationshipModel
from app.workers.processing import process_document_pipeline

STARTER_DATASETS = [
    # India Macroeconomy
    {
        "category": "india-macroeconomy",
        "dir": r"c:\Users\kiran\OneDrive\Desktop\Project\starter-datasets\india-macroeconomy",
        "files": [
            "01-india-economic-survey-2024-25-excerpt.pdf",
            "02-rbi-annual-report-2024-25-excerpt.pdf",
            "03-imf-india-2025-article-iv-excerpt.pdf",
        ]
    }
]

uploads_dir = r"c:\Users\kiran\OneDrive\Desktop\Project\backend\uploads"
os.makedirs(uploads_dir, exist_ok=True)

print("=================================================================", flush=True)
print("STARTING FULL INGESTION OF INDIA MACROECONOMY STARTER DATASET", flush=True)
print("=================================================================", flush=True)

overall_start = time.time()

for group in STARTER_DATASETS:
    category = group["category"]
    base_dir = group["dir"]
    print(f"\n--- Processing Category: {category} ---", flush=True)

    for fname in group["files"]:
        src_path = os.path.join(base_dir, fname)
        if not os.path.exists(src_path):
            print(f"Warning: {src_path} does not exist. Skipping.", flush=True)
            continue

        with open(src_path, "rb") as f:
            content = f.read()
        file_hash = hashlib.sha256(content).hexdigest()
        file_size = len(content)

        # Check if already in DB
        with get_db_context() as db:
            existing_doc = db.query(DocumentModel).filter(DocumentModel.filename == fname).first()
            if existing_doc and existing_doc.status == "completed":
                fc = db.query(FactModel).filter(FactModel.document_id == existing_doc.id).count()
                if fc > 0:
                    print(f"Document '{fname}' already completed with {fc} facts. Skipping re-extraction.", flush=True)
                    continue
                else:
                    doc_id = existing_doc.id
            else:
                doc_id = str(uuid.uuid4())
                dest_path = os.path.join(uploads_dir, f"{doc_id}_{fname}")
                shutil.copy2(src_path, dest_path)

                doc = DocumentModel(
                    id=doc_id,
                    filename=fname,
                    file_hash=file_hash,
                    file_size=file_size,
                    status="queued",
                    doc_metadata={"saved_path": dest_path, "dataset": category}
                )
                db.add(doc)
                job = ProcessingJobModel(
                    id=str(uuid.uuid4()),
                    document_id=doc_id,
                    status="queued",
                    stage="QUEUED",
                    progress=0,
                    message="Queued for processing"
                )
                db.add(job)
                db.commit()

        # Find target local path
        with get_db_context() as db:
            doc = db.query(DocumentModel).filter(DocumentModel.filename == fname).first()
            doc_id = doc.id
            meta = doc.doc_metadata or {}
            local_pdf_path = meta.get("saved_path") or os.path.join(uploads_dir, f"{doc_id}_{fname}")

        if not os.path.exists(local_pdf_path):
            dest_path = os.path.join(uploads_dir, f"{doc_id}_{fname}")
            shutil.copy2(src_path, dest_path)
            local_pdf_path = dest_path

        print(f"\n>>> INGESTING: {fname} (ID: {doc_id})", flush=True)
        t0 = time.time()
        process_document_pipeline(doc_id, local_pdf_path, fname)
        duration = time.time() - t0
        print(f">>> COMPLETED {fname} in {duration:.2f} seconds.", flush=True)

total_elapsed = time.time() - overall_start
print(f"\n=======================================================", flush=True)
print(f"ALL DATASETS PROCESSED IN {total_elapsed:.2f} SECONDS TOTAL!", flush=True)
print(f"=======================================================", flush=True)

# Print Summary
with get_db_context() as db:
    print("\n--- COMPLETE KNOWLEDGE LAYER DATABASE STATUS ---", flush=True)
    all_docs = db.query(DocumentModel).all()
    for d in all_docs:
        fc = db.query(FactModel).filter(FactModel.document_id == d.id).count()
        print(f"File: {d.filename[:38]:38} | pages={d.page_count:3} | status={d.status:9} | facts={fc:3}", flush=True)

    all_facts = db.query(FactModel).count()
    all_rels = db.query(RelationshipModel).count()
    conflicts = db.query(RelationshipModel).filter(RelationshipModel.relationship_type == "CONTRADICTS").count()
    corrobs = db.query(RelationshipModel).filter(RelationshipModel.relationship_type == "CORROBORATES").count()
    contexts = db.query(RelationshipModel).filter(RelationshipModel.relationship_type == "CONTEXTUAL_DIFFERENCE").count()

    print(f"\nTOTAL FACTS IN SYSTEM: {all_facts}", flush=True)
    print(f"TOTAL RELATIONSHIPS IN SYSTEM: {all_rels}", flush=True)
    print(f" - Corroborations: {corrobs}", flush=True)
    print(f" - Contradictions: {conflicts}", flush=True)
    print(f" - Contextual Differences: {contexts}", flush=True)

# Also copy this script into backend/scripts
backend_script = r"c:\Users\kiran\OneDrive\Desktop\Project\backend\scripts\process_all_starter_datasets.py"
shutil.copy2(__file__, backend_script)
print(f"\nSaved master script to {backend_script}")

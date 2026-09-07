import os
import hashlib
import re
from typing import List, Dict, Any, Optional, Tuple
import fitz  # PyMuPDF
from app.extraction.layout import ExtractedDocument, ExtractedPage, ExtractedBlock
from app.extraction.quality import evaluate_page_quality
from app.extraction.ocr import get_ocr_provider


def compute_file_hash(file_bytes: bytes) -> str:
    """Computes SHA-256 hash of file content for idempotency."""
    hasher = hashlib.sha256()
    hasher.update(file_bytes)
    return hasher.hexdigest()


def detect_block_type(text: str, is_table: bool = False) -> str:
    """Classifies block into heading, table, list, or text."""
    if is_table:
        return "table"
    clean = text.strip()
    if not clean:
        return "text"
    # Heading heuristic: short length, no ending period, uppercase or title case
    if len(clean) < 80 and not clean.endswith(('.', ':', ';')) and (clean.isupper() or clean.istitle()):
        return "heading"
    # List heuristic: starts with bullet or number
    if re.match(r'^(\*|-|•|\d+[\.\)])\s+', clean):
        return "list"
    return "text"


def extract_pdf(pdf_path: str, document_id: str, original_filename: str) -> ExtractedDocument:
    """
    Parses a PDF file using PyMuPDF preserving:
    - Page dimensions
    - Layout blocks with exact bounding boxes [x0, y0, x1, y1]
    - Structured tables formatted with headers and rows
    - Quality scoring per page with OCR fallback
    """
    with open(pdf_path, "rb") as f:
        content_bytes = f.read()
    file_hash = compute_file_hash(content_bytes)
    
    doc = fitz.open(pdf_path)
    page_count = len(doc)
    doc_metadata = doc.metadata or {}
    
    extracted_pages: List[ExtractedPage] = []
    ocr_provider = get_ocr_provider()

    for page_idx in range(page_count):
        page = doc[page_idx]
        page_num = page_idx + 1
        page_rect = page.rect
        width = float(page_rect.width)
        height = float(page_rect.height)
        
        # Check for images on page
        image_list = page.get_images()
        has_images = len(image_list) > 0

        # 1. Native block extraction
        # Each block: (x0, y0, x1, y1, "lines\n", block_no, block_type)
        raw_blocks = page.get_text("blocks")
        page_full_text = page.get_text("text")

        # 2. Extract structured tables using PyMuPDF table finder for focused filings (page_count <= 10)
        table_bboxes = []
        structured_tables = []
        try:
            if page_count <= 10:
                tabs = page.find_tables()
                for tab in tabs:
                    table_bboxes.append(list(tab.bbox))
                    df_rows = tab.extract()
                    if df_rows and len(df_rows) > 0:
                        cleaned_rows = [[str(cell or "").strip().replace("\n", " ") for cell in row] for row in df_rows]
                        header = cleaned_rows[0]
                        body = cleaned_rows[1:] if len(cleaned_rows) > 1 else []
                        
                        table_str = "TABLE:\n" + " | ".join(header) + "\n"
                        table_str += " | ".join(["---"] * len(header)) + "\n"
                        for row in body:
                            table_str += " | ".join(row) + "\n"
                        
                        structured_tables.append({
                            "bbox": list(tab.bbox),
                            "text": table_str.strip(),
                            "headers": header,
                            "rows": body
                        })
        except Exception:
            pass

        # 3. Evaluate extraction quality
        quality_score, is_poor, quality_reasons = evaluate_page_quality(
            page_text=page_full_text,
            page_width=width,
            page_height=height,
            has_images=has_images
        )

        extraction_method = "native"
        blocks: List[ExtractedBlock] = []

        # 4. OCR fallback if quality is poor and OCR provider is available
        if is_poor and ocr_provider.is_available():
            pix = page.get_pixmap(dpi=150)
            ocr_text, ocr_blocks = ocr_provider.extract_page_ocr(pix.tobytes("png"))
            if ocr_text:
                page_full_text = ocr_text
                extraction_method = "ocr"
                quality_score = 0.85
                quality_reasons.append("Applied OCR fallback successfully")
                for i, ob in enumerate(ocr_blocks):
                    block_id = f"{document_id[:8]}_p{page_num}_b{i}"
                    blocks.append(ExtractedBlock(
                        id=block_id,
                        page_number=page_num,
                        block_index=i,
                        block_type="text",
                        text=ob["text"],
                        bbox=ob["bbox"],
                        metadata={"confidence": ob.get("confidence", 0.8)}
                    ))
        
        # If native extraction is used (the standard case for digital PDFs)
        if extraction_method == "native":
            # Add structured tables first as priority table blocks
            block_counter = 0
            for t_idx, st in enumerate(structured_tables):
                block_id = f"{document_id[:8]}_p{page_num}_t{t_idx}"
                blocks.append(ExtractedBlock(
                    id=block_id,
                    page_number=page_num,
                    block_index=block_counter,
                    block_type="table",
                    text=st["text"],
                    bbox=st["bbox"],
                    table_data={"headers": st["headers"], "rows": st["rows"]},
                    metadata={"is_table": True}
                ))
                block_counter += 1

            # Then add text blocks that don't heavily overlap with already extracted tables
            for b in raw_blocks:
                bx0, by0, bx1, by1, btext, bno, btype = b
                bclean = btext.strip()
                if not bclean:
                    continue
                
                # Check if this block is inside any extracted table
                inside_table = False
                for tb in table_bboxes:
                    # Intersection over block area
                    ix0 = max(bx0, tb[0])
                    iy0 = max(by0, tb[1])
                    ix1 = min(bx1, tb[2])
                    iy1 = min(by1, tb[3])
                    if ix1 > ix0 and iy1 > iy0:
                        inter_area = (ix1 - ix0) * (iy1 - iy0)
                        block_area = max(1.0, (bx1 - bx0) * (by1 - by0))
                        if inter_area / block_area > 0.65:
                            inside_table = True
                            break
                
                if inside_table:
                    continue  # Table block already represents this content with structure!

                b_type = detect_block_type(bclean)
                block_id = f"{document_id[:8]}_p{page_num}_b{block_counter}"
                blocks.append(ExtractedBlock(
                    id=block_id,
                    page_number=page_num,
                    block_index=block_counter,
                    block_type=b_type,
                    text=bclean,
                    bbox=[round(bx0, 2), round(by0, 2), round(bx1, 2), round(by1, 2)],
                    metadata={"raw_block_no": bno}
                ))
                block_counter += 1

        extracted_pages.append(ExtractedPage(
            page_number=page_num,
            width=width,
            height=height,
            extraction_method=extraction_method,
            quality_score=quality_score,
            raw_text=page_full_text,
            blocks=blocks,
            quality_issues=quality_reasons
        ))

    doc.close()

    return ExtractedDocument(
        document_id=document_id,
        filename=original_filename,
        file_hash=file_hash,
        page_count=page_count,
        pages=extracted_pages,
        metadata=doc_metadata
    )

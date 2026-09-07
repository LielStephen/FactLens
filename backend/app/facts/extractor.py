import json
import re
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple
from app.extraction.layout import ExtractedDocument
from app.facts.schema import CandidateChunk, ExtractedFactItem, EvidencePayload, TimeContext
from app.facts.normalizer import (
    normalize_number,
    normalize_temporal,
    normalize_entity,
    normalize_predicate
)
from app.facts.validator import validate_evidence_grounding
from app.facts.table_extractor import extract_facts_from_tables
from app.llm.groq import get_llm_provider
from app.llm.prompts import FACT_EXTRACTION_SYSTEM_PROMPT

# In-memory content-addressed cache for chunk extraction results
_CHUNK_FACTS_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def compute_chunk_cache_key(chunk: CandidateChunk) -> str:
    """Computes SHA-256 key for caching LLM extraction results."""
    raw = f"{chunk.text}|{chunk.heading_context or ''}|{chunk.table_context or ''}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def clean_json_response(raw_resp: str) -> str:
    """Strips markdown code fences and extracts outermost valid JSON object."""
    raw = raw_resp.strip()
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        return match.group(0).strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    elif raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return raw.strip()


def _process_chunk_batch(batch: List[CandidateChunk]) -> List[Tuple[CandidateChunk, List[Dict[str, Any]]]]:
    """
    Processes a packed batch of 3-4 candidate chunks in a single high-speed LLM call,
    reducing API round-trips by 75%+ while preserving chunk-level provenance.
    """
    results: List[Tuple[CandidateChunk, List[Dict[str, Any]]]] = []
    uncached: List[CandidateChunk] = []

    for chunk in batch:
        cache_key = compute_chunk_cache_key(chunk)
        if cache_key in _CHUNK_FACTS_CACHE:
            results.append((chunk, _CHUNK_FACTS_CACHE[cache_key]))
        else:
            uncached.append(chunk)

    if not uncached:
        return results

    llm = get_llm_provider()

    # Pack multiple chunks into a unified structured prompt
    user_content = "You are given the following numbered text chunks from a document.\n"
    user_content += "Extract all explicit numerical and semantic facts from each chunk.\n"
    user_content += "In your JSON output, include the exact 'chunk_id' for each fact.\n\n"

    for ch in uncached:
        user_content += f"--- BEGIN CHUNK [chunk_id: {ch.chunk_id}, page: {ch.page_number}] ---\n"
        if ch.heading_context:
            user_content += f"Section: {ch.heading_context}\n"
        if ch.table_context:
            user_content += f"Table Context: {ch.table_context}\n"
        user_content += f"Content:\n{ch.text}\n"
        user_content += f"--- END CHUNK [{ch.chunk_id}] ---\n\n"

    messages = [
        {"role": "system", "content": FACT_EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]

    try:
        raw_response = llm.generate(messages, max_tokens=1000, temperature=0.0, json_mode=True)
        cleaned_json = clean_json_response(raw_response)
        parsed = json.loads(cleaned_json)
        raw_facts = parsed.get("facts", [])

        # Group facts by chunk_id
        chunk_map: Dict[str, List[Dict[str, Any]]] = {ch.chunk_id: [] for ch in uncached}
        for rf in raw_facts:
            target_cid = rf.get("chunk_id")
            if target_cid and target_cid in chunk_map:
                chunk_map[target_cid].append(rf)
            else:
                # Fallback matching: match quote against chunk texts
                ev = rf.get("evidence", {})
                quote = ev.get("quote", "") if isinstance(ev, dict) else ""
                matched = False
                if quote:
                    for ch in uncached:
                        if quote.lower() in ch.text.lower():
                            chunk_map[ch.chunk_id].append(rf)
                            matched = True
                            break
                if not matched and uncached:
                    chunk_map[uncached[0].chunk_id].append(rf)

        for ch in uncached:
            ch_facts = chunk_map.get(ch.chunk_id, [])
            _CHUNK_FACTS_CACHE[compute_chunk_cache_key(ch)] = ch_facts
            results.append((ch, ch_facts))

    except Exception as e:
        print(f"[Extractor] Batch extraction warning: {e}. Falling back to individual chunks.")
        for ch in uncached:
            try:
                single_msg = [
                    {"role": "system", "content": FACT_EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Source Page: {ch.page_number}\nText:\n{ch.text}"}
                ]
                resp = llm.generate(single_msg, max_tokens=400, temperature=0.0, json_mode=True)
                p = json.loads(clean_json_response(resp))
                f_list = p.get("facts", [])
                _CHUNK_FACTS_CACHE[compute_chunk_cache_key(ch)] = f_list
                results.append((ch, f_list))
            except Exception as single_e:
                print(f"[Extractor] Single chunk fallback error: {single_e}")
                results.append((ch, []))

    return results


def extract_facts_from_chunks(
    chunks: List[CandidateChunk],
    extracted_doc: ExtractedDocument
) -> List[ExtractedFactItem]:
    """
    Executes hybrid extraction combining:
    1. Deterministic Fast-Path Table Matrix Parser (0ms latency, exact cell bboxes)
    2. Multi-Block Chunk Packing over Groq LPU with ThreadPoolExecutor
    """
    all_facts: List[ExtractedFactItem] = []
    seen_signatures = set()

    # 1. Fast-Path Deterministic Table Fact Extraction
    table_facts = extract_facts_from_tables(extracted_doc)
    for tf in table_facts:
        sig = f"{tf.subject.lower()}|{tf.predicate.lower()}|{tf.normalized_value}|{tf.time.label if tf.time else ''}|{tf.evidence.page}"
        if sig not in seen_signatures:
            seen_signatures.add(sig)
            all_facts.append(tf)

    if not chunks:
        return all_facts

    # 2. Multi-Block Chunk Packing: Pack into batches of 5 chunks
    batch_size = 5
    chunk_batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]

    max_workers = min(3, len(chunk_batches))
    chunk_results: List[Tuple[CandidateChunk, List[Dict[str, Any]]]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_batch = {executor.submit(_process_chunk_batch, b): b for b in chunk_batches}
        for future in as_completed(future_to_batch):
            try:
                batch_res = future.result()
                chunk_results.extend(batch_res)
            except Exception as e:
                print(f"[Extractor] Batch worker failed: {e}")

    # 3. Process and validate all candidate facts deterministically
    for chunk, raw_facts in chunk_results:
        for rf in raw_facts:
            subj = rf.get("subject", "").strip()
            pred = rf.get("predicate", "").strip()
            val = str(rf.get("raw_value", "")).strip()

            if not subj or not pred or not val:
                continue

            ev_dict = rf.get("evidence", {})
            quote = ev_dict.get("quote", "").strip() if isinstance(ev_dict, dict) else ""

            # Independent Evidence Grounding Validation
            status, val_score, matched_bbox = validate_evidence_grounding(
                evidence_quote=quote,
                page_number=chunk.page_number,
                block_id=chunk.block_id,
                extracted_doc=extracted_doc
            )

            # Deterministic Normalization
            norm_val, detected_unit, detected_curr = normalize_number(val)
            norm_subj = normalize_entity(subj)
            norm_pred = normalize_predicate(pred)
            norm_time = normalize_temporal(rf.get("time"))

            # Unit / currency resolution
            unit = detected_unit or rf.get("unit")
            currency = detected_curr or rf.get("currency")
            if not currency and unit in ["USD", "EUR", "GBP", "INR"]:
                currency = unit

            # Confidence calculation: adjust down if evidence is weak or unsupported
            base_conf = float(rf.get("confidence", 0.90))
            if status == "grounded":
                final_conf = min(0.99, max(0.85, base_conf))
            elif status == "grounded_with_warning":
                final_conf = round(base_conf * 0.85, 2)
            else:
                final_conf = round(base_conf * 0.30, 2)

            # De-duplication signature
            sig = f"{norm_subj.lower()}|{norm_pred.lower()}|{norm_val if norm_val is not None else val.lower()}|{norm_time.label}|{chunk.page_number}"
            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)

            evidence_payload = EvidencePayload(
                quote=quote if quote else chunk.text[:120],
                page=chunk.page_number,
                block_id=chunk.block_id,
                bbox=matched_bbox or chunk.bbox,
                validation_status=status,
                validation_score=val_score
            )

            fact_item = ExtractedFactItem(
                subject=norm_subj,
                predicate=norm_pred,
                raw_value=val,
                normalized_value=norm_val,
                value_type=rf.get("value_type", "number" if norm_val is not None else "text"),
                unit=unit,
                currency=currency,
                time=norm_time,
                scope=rf.get("scope", "global"),
                location=rf.get("location"),
                qualifiers=rf.get("qualifiers", {}),
                evidence=evidence_payload,
                confidence=final_conf
            )
            all_facts.append(fact_item)

    return all_facts

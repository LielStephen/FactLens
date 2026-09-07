from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ExtractedBlock:
    id: str
    page_number: int
    block_index: int
    block_type: str  # text, heading, table, list, unknown
    text: str
    bbox: List[float]  # [x0, y0, x1, y1]
    table_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedPage:
    page_number: int
    width: float
    height: float
    extraction_method: str  # native, ocr
    quality_score: float
    raw_text: str
    blocks: List[ExtractedBlock] = field(default_factory=list)
    quality_issues: List[str] = field(default_factory=list)


@dataclass
class ExtractedDocument:
    document_id: str
    filename: str
    file_hash: str
    page_count: int
    pages: List[ExtractedPage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

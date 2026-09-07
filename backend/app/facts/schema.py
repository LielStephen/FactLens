from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class TimeContext(BaseModel):
    label: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    precision: Optional[str] = None  # year, fiscal_year, quarter, month, day, range


class EvidencePayload(BaseModel):
    quote: str
    page: int
    block_id: str
    bbox: Optional[List[float]] = None
    validation_status: Optional[str] = "grounded"
    validation_score: Optional[float] = 1.0


class ExtractedFactItem(BaseModel):
    subject: str = Field(..., description="Canonical or extracted entity name")
    predicate: str = Field(..., description="Fact predicate, e.g. revenue, director, employees, address")
    raw_value: str = Field(..., description="Exact textual value extracted from source")
    normalized_value: Optional[float] = Field(None, description="Normalized numeric value if applicable")
    value_type: str = Field("text", description="number, percentage, currency, date, text, status")
    unit: Optional[str] = Field(None, description="USD, %, employees, etc.")
    currency: Optional[str] = Field(None, description="USD, EUR, GBP, INR, etc.")
    time: Optional[TimeContext] = Field(default_factory=TimeContext)
    scope: Optional[str] = Field("global", description="global, consolidated, US subsidiary, etc.")
    location: Optional[str] = Field(None, description="Geographic location if applicable")
    qualifiers: Optional[Dict[str, Any]] = Field(default_factory=dict)
    evidence: EvidencePayload
    confidence: float = Field(0.90, ge=0.0, le=1.0)


class LLMExtractionResponse(BaseModel):
    facts: List[ExtractedFactItem] = Field(default_factory=list)


class FactRelationshipItem(BaseModel):
    fact_a_id: str
    fact_b_id: str
    relationship_type: str  # CORROBORATES, CONTRADICTS, CONTEXTUAL_DIFFERENCE, UNCERTAIN
    confidence: float = Field(0.90, ge=0.0, le=1.0)
    explanation: str
    supporting_dimensions: List[str] = Field(default_factory=list)
    resolution_tier: str = "deterministic"
    reasoning_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CandidateChunk(BaseModel):
    chunk_id: str
    document_id: str
    page_number: int
    block_id: str
    heading_context: Optional[str] = None
    table_context: Optional[str] = None
    text: str
    bbox: List[float]
    signals: List[str] = Field(default_factory=list)

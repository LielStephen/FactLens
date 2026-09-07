import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON, Boolean
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    file_size = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="queued", index=True)
    page_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    doc_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    pages = relationship("PageModel", back_populates="document", cascade="all, delete-orphan")
    facts = relationship("FactModel", back_populates="document", cascade="all, delete-orphan")
    jobs = relationship("ProcessingJobModel", back_populates="document", cascade="all, delete-orphan")


class PageModel(Base):
    __tablename__ = "pages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    width = Column(Float, default=595.0)
    height = Column(Float, default=842.0)
    extraction_method = Column(String(32), default="native")
    quality_score = Column(Float, default=1.0)
    raw_text = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("DocumentModel", back_populates="pages")
    blocks = relationship("BlockModel", back_populates="page", cascade="all, delete-orphan")


class BlockModel(Base):
    __tablename__ = "blocks"

    id = Column(String(64), primary_key=True)
    page_id = Column(String(36), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    block_index = Column(Integer, nullable=False)
    block_type = Column(String(32), default="text")
    text = Column(Text, nullable=False)
    bbox = Column(JSON, default=list)  # [x0, y0, x1, y1]
    table_data = Column(JSON, nullable=True)
    block_metadata = Column("metadata", JSON, default=dict)

    page = relationship("PageModel", back_populates="blocks")


class FactModel(Base):
    __tablename__ = "facts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(255), nullable=False, index=True)
    predicate = Column(String(255), nullable=False, index=True)
    raw_value = Column(Text, nullable=False)
    normalized_value = Column(Float, nullable=True)
    value_type = Column(String(64), default="text")
    unit = Column(String(64), nullable=True)
    currency = Column(String(32), nullable=True)
    time_data = Column(JSON, default=dict)
    scope = Column(String(128), nullable=True)
    location = Column(String(128), nullable=True)
    qualifiers = Column(JSON, default=dict)
    confidence = Column(Float, default=0.90)
    embedding = Column(JSON, nullable=True)
    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("DocumentModel", back_populates="facts")
    evidence = relationship("EvidenceModel", back_populates="fact", cascade="all, delete-orphan")


class EvidenceModel(Base):
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    fact_id = Column(String(36), ForeignKey("facts.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String(36), nullable=True)
    page_number = Column(Integer, nullable=False)
    block_id = Column(String(64), nullable=False)
    evidence_text = Column(Text, nullable=False)
    bbox = Column(JSON, default=list)  # [x0, y0, x1, y1]
    validation_status = Column(String(32), default="grounded")  # grounded, grounded_with_warning, unsupported
    validation_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    fact = relationship("FactModel", back_populates="evidence")


class RelationshipModel(Base):
    __tablename__ = "relationships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    fact_a_id = Column(String(36), ForeignKey("facts.id", ondelete="CASCADE"), nullable=False, index=True)
    fact_b_id = Column(String(36), ForeignKey("facts.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(64), nullable=False, index=True)  # CORROBORATES, CONTRADICTS, CONTEXTUAL_DIFFERENCE, UNCERTAIN
    confidence = Column(Float, default=0.90)
    explanation = Column(Text, nullable=False)
    supporting_dimensions = Column(JSON, default=list)
    resolution_tier = Column(String(32), default="deterministic")
    reasoning_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    fact_a = relationship("FactModel", foreign_keys=[fact_a_id])
    fact_b = relationship("FactModel", foreign_keys=[fact_b_id])


class ProcessingJobModel(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String(64), default="QUEUED")
    status = Column(String(32), default="queued")
    progress = Column(Integer, default=0)
    message = Column(Text, default="Job queued")
    timings = Column(JSON, default=dict)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    document = relationship("DocumentModel", back_populates="jobs")

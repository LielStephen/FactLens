-- =========================================================================
-- FactLens - PostgreSQL / Supabase Initial Schema Migration
-- =========================================================================

-- Enable pgvector if available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'pgvector extension not enabled or not available on this tier, falling back to JSON embeddings';
END $$;

-- Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'queued',
    page_count INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);

-- Pages Table
CREATE TABLE IF NOT EXISTS pages (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    width DOUBLE PRECISION DEFAULT 595.0,
    height DOUBLE PRECISION DEFAULT 842.0,
    extraction_method VARCHAR(32) DEFAULT 'native',
    quality_score DOUBLE PRECISION DEFAULT 1.0,
    raw_text TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pages_doc_id ON pages(document_id);
CREATE INDEX IF NOT EXISTS idx_pages_number ON pages(document_id, page_number);

-- Blocks Table
CREATE TABLE IF NOT EXISTS blocks (
    id VARCHAR(64) PRIMARY KEY,
    page_id VARCHAR(36) NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    document_id VARCHAR(36) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    block_index INTEGER NOT NULL,
    block_type VARCHAR(32) DEFAULT 'text',
    text TEXT NOT NULL,
    bbox JSONB DEFAULT '[]'::jsonb,
    table_data JSONB,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_blocks_page_id ON blocks(page_id);
CREATE INDEX IF NOT EXISTS idx_blocks_doc_id ON blocks(document_id);

-- Facts Table
CREATE TABLE IF NOT EXISTS facts (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    subject VARCHAR(255) NOT NULL,
    predicate VARCHAR(255) NOT NULL,
    raw_value TEXT NOT NULL,
    normalized_value DOUBLE PRECISION,
    value_type VARCHAR(64) DEFAULT 'text',
    unit VARCHAR(64),
    currency VARCHAR(32),
    time_data JSONB DEFAULT '{}'::jsonb,
    scope VARCHAR(128),
    location VARCHAR(128),
    qualifiers JSONB DEFAULT '{}'::jsonb,
    confidence DOUBLE PRECISION DEFAULT 0.90,
    embedding JSONB,
    is_flagged BOOLEAN DEFAULT FALSE,
    flag_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_facts_doc_id ON facts(document_id);
CREATE INDEX IF NOT EXISTS idx_facts_subject ON facts(subject);
CREATE INDEX IF NOT EXISTS idx_facts_predicate ON facts(predicate);

-- Evidence Table
CREATE TABLE IF NOT EXISTS evidence (
    id VARCHAR(36) PRIMARY KEY,
    fact_id VARCHAR(36) NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
    document_id VARCHAR(36) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_id VARCHAR(36),
    page_number INTEGER NOT NULL,
    block_id VARCHAR(64) NOT NULL,
    evidence_text TEXT NOT NULL,
    bbox JSONB DEFAULT '[]'::jsonb,
    validation_status VARCHAR(32) DEFAULT 'grounded',
    validation_score DOUBLE PRECISION DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_fact_id ON evidence(fact_id);
CREATE INDEX IF NOT EXISTS idx_evidence_doc_id ON evidence(document_id);

-- Relationships Table
CREATE TABLE IF NOT EXISTS relationships (
    id VARCHAR(36) PRIMARY KEY,
    fact_a_id VARCHAR(36) NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
    fact_b_id VARCHAR(36) NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
    relationship_type VARCHAR(64) NOT NULL,
    confidence DOUBLE PRECISION DEFAULT 0.90,
    explanation TEXT NOT NULL,
    supporting_dimensions JSONB DEFAULT '[]'::jsonb,
    resolution_tier VARCHAR(32) DEFAULT 'deterministic',
    reasoning_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rel_fact_a ON relationships(fact_a_id);
CREATE INDEX IF NOT EXISTS idx_rel_fact_b ON relationships(fact_b_id);
CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(relationship_type);

-- Processing Jobs Table
CREATE TABLE IF NOT EXISTS processing_jobs (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    stage VARCHAR(64) DEFAULT 'QUEUED',
    status VARCHAR(32) DEFAULT 'queued',
    progress INTEGER DEFAULT 0,
    message TEXT DEFAULT 'Job queued',
    timings JSONB DEFAULT '{}'::jsonb,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_jobs_doc_id ON processing_jobs(document_id);

export interface TimeContext {
  label?: string | null;
  start?: string | null;
  end?: string | null;
  precision?: string | null;
}

export interface Evidence {
  page: number;
  block_id?: string | null;
  quote: string;
  bbox?: number[];
  validation_status?: 'grounded' | 'grounded_with_warning' | 'unsupported';
  validation_score?: number;
}

export interface Fact {
  id: string;
  document_id: string;
  document_filename?: string;
  subject: string;
  predicate: string;
  raw_value: string;
  normalized_value?: number | null;
  value_type: string;
  unit?: string | null;
  currency?: string | null;
  time?: TimeContext;
  scope?: string | null;
  location?: string | null;
  confidence: number;
  is_flagged?: boolean;
  flag_reason?: string | null;
  relationship_count?: number;
  evidence?: Evidence | null;
}

export interface RelatedFactSummary {
  id: string;
  document_filename: string;
  subject: string;
  predicate: string;
  value: string;
  time?: TimeContext;
  scope?: string | null;
  evidence_quote?: string;
  page?: number;
}

export interface FactRelationship {
  id: string;
  relationship_type: 'CORROBORATES' | 'CONTRADICTS' | 'CONTEXTUAL_DIFFERENCE' | 'UNCERTAIN';
  confidence: number;
  explanation: string;
  supporting_dimensions: string[];
  resolution_tier: string;
  reasoning_metadata?: Record<string, any>;
  fact_a?: Fact;
  fact_b?: Fact;
  related_fact?: RelatedFactSummary;
  created_at?: string;
}

export interface DocumentItem {
  id: string;
  filename: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  page_count: number;
  file_size: number;
  fact_count: number;
  created_at: string;
  completed_at?: string | null;
  error_message?: string | null;
}

export interface DocumentStatus {
  document_id: string;
  stage: string;
  status: string;
  progress: number;
  message: string;
  timings: Record<string, number>;
}

export interface DocumentPageBlock {
  id: string;
  index: number;
  type: string;
  text: string;
  bbox: number[];
  table_data?: any;
}

export interface DocumentPage {
  page_id: string;
  page_number: number;
  width: number;
  height: number;
  extraction_method: string;
  quality_score: number;
  blocks: DocumentPageBlock[];
}

export interface DashboardStats {
  documents: number;
  facts: number;
  relationships: number;
  conflicts: number;
}

export interface ResolutionBreakdown {
  corroborations: number;
  contradictions: number;
  contextual_differences: number;
}

export interface DatasetInfo {
  id: string;
  name: string;
  badge?: string;
  description?: string;
  document_count?: number;
}

export interface DashboardOverview {
  stats: DashboardStats;
  resolution_breakdown?: ResolutionBreakdown;
  active_dataset?: DatasetInfo;
  available_datasets?: DatasetInfo[];
  recent_documents: DocumentItem[];
  recent_relationships: any[];
}

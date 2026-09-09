import {
  DashboardOverview,
  DocumentItem,
  DocumentStatus,
  DocumentPage,
  Fact,
  FactRelationship
} from '@/types';

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000'
    : 'https://factlens-sgdu.onrender.com')
).replace(/\/+$/, '');

export async function fetchOverview(dataset?: string): Promise<DashboardOverview> {
  const url = dataset && dataset !== 'all' ? `${API_BASE_URL}/api/overview?dataset=${dataset}` : `${API_BASE_URL}/api/overview`;
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch dashboard overview');
  return res.json();
}

export async function fetchDocuments(dataset?: string): Promise<DocumentItem[]> {
  const url = dataset && dataset !== 'all' ? `${API_BASE_URL}/api/documents?dataset=${dataset}` : `${API_BASE_URL}/api/documents`;
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function fetchDocument(documentId: string): Promise<DocumentItem> {
  const res = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch document');
  return res.json();
}

export async function fetchDocumentStatus(documentId: string): Promise<DocumentStatus> {
  const res = await fetch(`${API_BASE_URL}/api/documents/${documentId}/status`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch document status');
  return res.json();
}

export async function fetchDocumentPages(documentId: string): Promise<DocumentPage[]> {
  const res = await fetch(`${API_BASE_URL}/api/documents/${documentId}/pages`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch document pages');
  return res.json();
}

export async function uploadDocument(file: File): Promise<{ document_id: string; filename: string; status: string; message?: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE_URL}/api/documents`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function fetchFacts(params?: {
  search?: string;
  dataset?: string;
  document_id?: string;
  entity?: string;
  predicate?: string;
  is_flagged?: boolean;
  limit?: number;
  offset?: number;
}): Promise<{ total: number; facts: Fact[] }> {
  const query = new URLSearchParams();
  if (params?.search) query.set('search', params.search);
  if (params?.dataset && params.dataset !== 'all') query.set('dataset', params.dataset);
  if (params?.document_id) query.set('document_id', params.document_id);
  if (params?.entity) query.set('entity', params.entity);
  if (params?.predicate) query.set('predicate', params.predicate);
  if (params?.is_flagged !== undefined) query.set('is_flagged', String(params.is_flagged));
  if (params?.limit) query.set('limit', String(params.limit));
  if (params?.offset) query.set('offset', String(params.offset));

  const res = await fetch(`${API_BASE_URL}/api/facts?${query.toString()}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch facts');
  return res.json();
}

export async function fetchFact(factId: string): Promise<Fact> {
  const res = await fetch(`${API_BASE_URL}/api/facts/${factId}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch fact');
  return res.json();
}

export async function fetchFactRelationships(factId: string): Promise<FactRelationship[]> {
  const res = await fetch(`${API_BASE_URL}/api/facts/${factId}/relationships`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch fact relationships');
  return res.json();
}

export async function fetchRelationships(params?: {
  relationship_type?: string;
  dataset?: string;
  limit?: number;
}): Promise<{ total: number; relationships: FactRelationship[] }> {
  const query = new URLSearchParams();
  if (params?.relationship_type && params.relationship_type !== 'ALL') {
    query.set('relationship_type', params.relationship_type);
  }
  if (params?.dataset && params.dataset !== 'all') {
    query.set('dataset', params.dataset);
  }
  if (params?.limit) query.set('limit', String(params.limit));

  const res = await fetch(`${API_BASE_URL}/api/relationships?${query.toString()}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch relationships');
  return res.json();
}

export async function fetchConflicts(dataset?: string): Promise<{
  total_conflicts: number;
  contradictions: FactRelationship[];
  total_flagged_facts: number;
  flagged_facts: any[];
}> {
  const query = new URLSearchParams();
  if (dataset && dataset !== 'all') {
    query.set('dataset', dataset);
  }
  const qStr = query.toString() ? `?${query.toString()}` : '';
  const res = await fetch(`${API_BASE_URL}/api/relationships/conflicts${qStr}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch conflicts');
  return res.json();
}

export async function fetchShowcase(): Promise<Record<string, any>> {
  const res = await fetch(`${API_BASE_URL}/api/showcase`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch showcase cases');
  return res.json();
}

export function getPdfFileUrl(documentId: string): string {
  return `${API_BASE_URL}/api/documents/${documentId}/file`;
}

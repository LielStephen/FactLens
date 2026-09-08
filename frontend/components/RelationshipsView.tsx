'use client';

import React, { useState } from 'react';
import { GitCompare, CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck, Download, Search, X } from 'lucide-react';
import { FactRelationship } from '@/types';
import { EvidenceInspectorModal } from './EvidenceInspectorModal';

interface RelationshipsViewProps {
  relationships: FactRelationship[];
  loading: boolean;
  onRefresh?: () => void;
}

export const RelationshipsView: React.FC<RelationshipsViewProps> = ({
  relationships,
  loading
}) => {
  const [activeFilter, setActiveFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedRel, setSelectedRel] = useState<FactRelationship | null>(null);

  const filterTabs = [
    { id: 'ALL', label: 'All Relations' },
    { id: 'CORROBORATES', label: 'Corroborated' },
    { id: 'CONTRADICTS', label: 'Contradictions' },
    { id: 'CONTEXTUAL_DIFFERENCE', label: 'Contextual Variance' },
  ];

  const filtered = relationships.filter(r => {
    const matchesFilter = activeFilter === 'ALL' ? true : r.relationship_type === activeFilter;
    const matchesSearch =
      !searchQuery ||
      (r.fact_a?.subject || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.fact_a?.predicate || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.fact_a?.raw_value || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.fact_b?.raw_value || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.explanation || '').toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const handleExportCsv = () => {
    if (!filtered.length) return;
    const headers = ["Relationship Type", "Confidence", "Entity", "Predicate", "Doc A", "Value A", "Doc B", "Value B", "Explanation"];
    const rows = filtered.map(r => [
      `"${r.relationship_type}"`,
      `"${(r.confidence * 100).toFixed(0)}%"`,
      `"${(r.fact_a?.subject || '').replace(/"/g, '""')}"`,
      `"${(r.fact_a?.predicate || '').replace(/"/g, '""')}"`,
      `"${(r.fact_a?.document_filename || '').replace(/"/g, '""')}"`,
      `"${(r.fact_a?.raw_value || '').replace(/"/g, '""')}"`,
      `"${(r.fact_b?.document_filename || '').replace(/"/g, '""')}"`,
      `"${(r.fact_b?.raw_value || '').replace(/"/g, '""')}"`,
      `"${(r.explanation || '').replace(/"/g, '""')}"`
    ]);

    const csvContent = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `factlens_relationships_export.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Cross-Document Relationship Explorer</h2>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold">
              {filtered.length} of {relationships.length} resolved
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Evidence-grounded resolution distinguishing genuine contradictions from contextual variances
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCsv}
            disabled={!filtered.length}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium transition-colors cursor-pointer disabled:opacity-50"
            title="Download CSV table"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by entity, predicate, or explanation..."
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-7 py-1.5 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          {filterTabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveFilter(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer shrink-0 ${
                activeFilter === tab.id
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Cards Stream */}
      <div className="space-y-4">
        {filtered.length > 0 ? (
          filtered.map(rel => {
            const isContradiction = rel.relationship_type === 'CONTRADICTS';
            const isCorroboration = rel.relationship_type === 'CORROBORATES';
            const isContextual = rel.relationship_type === 'CONTEXTUAL_DIFFERENCE';

            const badgeColor = isCorroboration
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
              : isContradiction
              ? 'bg-rose-50 text-rose-800 border-rose-200'
              : 'bg-amber-50 text-amber-800 border-amber-200';

            const fa = rel.fact_a;
            const fb = rel.fact_b;

            return (
              <div
                key={rel.id}
                onClick={() => setSelectedRel(rel)}
                className="p-5 rounded-xl border border-slate-200 bg-white hover:border-slate-300 hover:shadow-xs transition-all cursor-pointer space-y-4"
              >
                {/* Top Card Bar */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full border ${badgeColor}`}>
                      {rel.relationship_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs font-semibold text-slate-900">
                      {fa?.subject || 'Entity'} · <span className="text-slate-500 font-normal">{fa?.predicate}</span>
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-[11px] text-slate-400">
                    <span>Tier: {rel.resolution_tier}</span>
                    <span>•</span>
                    <span className="font-mono text-slate-600 font-medium">
                      {Math.round(rel.confidence * 100)}% Confidence
                    </span>
                  </div>
                </div>

                {/* Evidence Comparison Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-50 p-3.5 rounded-lg border border-slate-100">
                  <div className="space-y-1 text-xs">
                    <div className="flex items-center justify-between text-slate-500 text-[11px]">
                      <span className="font-medium text-slate-800">{fa?.document_filename}</span>
                      <span>Page {fa?.evidence?.page || 1}</span>
                    </div>
                    <div className="font-bold text-slate-900 text-sm">
                      {fa?.raw_value}
                      {fa?.time?.label && <span className="text-xs font-normal text-slate-500 ml-1.5">({fa.time.label})</span>}
                    </div>
                    <p className="text-[11px] text-slate-600 italic line-clamp-1">
                      "{fa?.evidence?.quote || 'No quote'}"
                    </p>
                  </div>

                  <div className="space-y-1 text-xs border-t md:border-t-0 md:border-l border-slate-200 pt-2 md:pt-0 md:pl-4">
                    <div className="flex items-center justify-between text-slate-500 text-[11px]">
                      <span className="font-medium text-slate-800">{fb?.document_filename}</span>
                      <span>Page {fb?.evidence?.page || 1}</span>
                    </div>
                    <div className="font-bold text-slate-900 text-sm">
                      {fb?.raw_value}
                      {fb?.time?.label && <span className="text-xs font-normal text-slate-500 ml-1.5">({fb.time.label})</span>}
                    </div>
                    <p className="text-[11px] text-slate-600 italic line-clamp-1">
                      "{fb?.evidence?.quote || 'No quote'}"
                    </p>
                  </div>
                </div>

                {/* Grounded Explanation */}
                <div className="flex items-center justify-between text-xs text-slate-600">
                  <p className="line-clamp-1 italic">
                    "{rel.explanation}"
                  </p>
                  <span className="text-emerald-700 font-medium text-[11px] flex items-center gap-1 shrink-0 ml-4">
                    Inspect Evidence <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-16 bg-white border border-slate-200 rounded-xl text-slate-400 text-xs">
            {loading ? 'Resolving relationships...' : 'No relationships found under this filter.'}
          </div>
        )}
      </div>

      {/* Split-screen Modal */}
      {selectedRel && (
        <EvidenceInspectorModal
          relationship={selectedRel}
          onClose={() => setSelectedRel(null)}
        />
      )}
    </div>
  );
};

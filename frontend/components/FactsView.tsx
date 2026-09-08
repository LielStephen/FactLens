'use client';

import React, { useState } from 'react';
import { Database, Search, Filter, ShieldCheck, AlertCircle, ChevronRight, FileText, Download, X } from 'lucide-react';
import { Fact } from '@/types';
import { FactDetailDrawer } from './FactDetailDrawer';

interface FactsViewProps {
  facts: Fact[];
  loading: boolean;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  onRefresh?: () => void;
}

export const FactsView: React.FC<FactsViewProps> = ({
  facts,
  loading,
  searchQuery,
  setSearchQuery
}) => {
  const [selectedFact, setSelectedFact] = useState<Fact | null>(null);
  const [selectedPredicate, setSelectedPredicate] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'HIGH_CONF' | 'FLAGGED'>('ALL');

  // Unique predicates for filtering
  const uniquePredicates = ['ALL', ...Array.from(new Set(facts.map(f => f.predicate)))];

  const filteredFacts = facts.filter(f => {
    const matchesPred = selectedPredicate === 'ALL' || f.predicate === selectedPredicate;
    const matchesStatus =
      statusFilter === 'ALL' ? true :
      statusFilter === 'HIGH_CONF' ? f.confidence >= 0.90 :
      Boolean(f.is_flagged || f.confidence < 0.70);

    const matchesSearch =
      !searchQuery ||
      f.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.predicate.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.raw_value.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (f.document_filename && f.document_filename.toLowerCase().includes(searchQuery.toLowerCase()));

    return matchesPred && matchesStatus && matchesSearch;
  });

  const handleExportCsv = () => {
    if (!filteredFacts.length) return;
    const headers = ["Subject", "Predicate", "Raw Value", "Normalized Value", "Unit", "Time", "Document", "Page", "Confidence", "Quote"];
    const rows = filteredFacts.map(f => [
      `"${(f.subject || '').replace(/"/g, '""')}"`,
      `"${(f.predicate || '').replace(/"/g, '""')}"`,
      `"${(f.raw_value || '').replace(/"/g, '""')}"`,
      `"${f.normalized_value ?? ''}"`,
      `"${f.unit || ''}"`,
      `"${f.time?.label || ''}"`,
      `"${f.document_filename || ''}"`,
      `"${f.evidence?.page || 1}"`,
      `"${(f.confidence * 100).toFixed(0)}%"`,
      `"${(f.evidence?.quote || '').replace(/"/g, '""')}"`
    ]);

    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `factlens_facts_export.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Facts Knowledge Explorer</h2>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold">
              {filteredFacts.length} of {facts.length} facts
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Every fact is bound to verifiable text quotes, coordinates, and normalized dimensions
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCsv}
            disabled={!filteredFacts.length}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium transition-colors cursor-pointer disabled:opacity-50"
            title="Download CSV table"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Search & Quick Filter Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter facts by keyword, entity, value..."
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

        {/* Status Filters */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setStatusFilter('ALL')}
            className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors cursor-pointer ${
              statusFilter === 'ALL' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            All Facts
          </button>
          <button
            onClick={() => setStatusFilter('HIGH_CONF')}
            className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors cursor-pointer ${
              statusFilter === 'HIGH_CONF' ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            High Conf (≥90%)
          </button>
          <button
            onClick={() => setStatusFilter('FLAGGED')}
            className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors cursor-pointer ${
              statusFilter === 'FLAGGED' ? 'bg-rose-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Flagged / Low Conf
          </button>
        </div>

        {/* Predicate Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-xs">
          {uniquePredicates.slice(0, 5).map((pred) => (
            <button
              key={pred}
              onClick={() => setSelectedPredicate(pred)}
              className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors cursor-pointer shrink-0 capitalize ${
                selectedPredicate === pred
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300 font-semibold'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {pred.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Facts Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/75 text-slate-500 font-semibold uppercase text-[10px] tracking-wider">
              <th className="py-3 px-4">Entity</th>
              <th className="py-3 px-4">Predicate</th>
              <th className="py-3 px-4">Asserted Value</th>
              <th className="py-3 px-4">Time Context</th>
              <th className="py-3 px-4">Source Evidence</th>
              <th className="py-3 px-4">Confidence</th>
              <th className="py-3 px-4 text-right"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {filteredFacts.length > 0 ? (
              filteredFacts.map((fact) => {
                const isHighConf = fact.confidence >= 0.90;
                const isWarning = fact.confidence < 0.70 || fact.is_flagged;

                return (
                  <tr
                    key={fact.id}
                    onClick={() => setSelectedFact(fact)}
                    className="hover:bg-slate-50/70 transition-colors group cursor-pointer"
                  >
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      {fact.subject}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="font-mono text-[11px] bg-slate-100 px-2 py-0.5 rounded text-slate-700">
                        {fact.predicate}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-bold text-slate-900">
                      {fact.raw_value}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      {fact.time?.label || <span className="text-slate-400">—</span>}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1.5 text-slate-600">
                        <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="truncate max-w-[140px] text-[11px]">
                          {fact.document_filename || 'Document'}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          p.{fact.evidence?.page || 1}
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                        isWarning
                          ? 'bg-rose-50 text-rose-700 border-rose-200'
                          : isHighConf
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-amber-50 text-amber-700 border-amber-200'
                      }`}>
                        {isWarning ? <AlertCircle className="w-3 h-3" /> : <ShieldCheck className="w-3 h-3" />}
                        {Math.round(fact.confidence * 100)}%
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-700 transition-colors inline-block" />
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={7} className="py-12 text-center text-slate-400 text-xs">
                  {loading ? 'Loading facts...' : 'No facts found matching search query.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Fact Detail Slide-over Drawer */}
      {selectedFact && (
        <FactDetailDrawer
          fact={selectedFact}
          onClose={() => setSelectedFact(null)}
        />
      )}
    </div>
  );
};

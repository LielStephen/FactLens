'use client';

import React from 'react';
import { 
  FileText, 
  Database, 
  GitCompare, 
  AlertTriangle, 
  ArrowUpRight, 
  CheckCircle2, 
  Clock, 
  ShieldCheck, 
  ChevronRight, 
  Upload,
  Download,
  Layers,
  Sparkles
} from 'lucide-react';
import { DashboardOverview } from '@/types';
import { NavTab } from './Sidebar';

interface OverviewViewProps {
  overview: DashboardOverview | null;
  loading: boolean;
  selectedDataset: string;
  onSelectDataset: (ds: string) => void;
  setActiveTab: (tab: NavTab) => void;
  onOpenUpload: () => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  overview,
  loading,
  selectedDataset,
  onSelectDataset,
  setActiveTab,
  onOpenUpload
}) => {
  const stats = overview?.stats || {
    documents: 0,
    facts: 0,
    relationships: 0,
    conflicts: 0
  };

  const breakdown = overview?.resolution_breakdown || {
    corroborations: 0,
    contradictions: 0,
    contextual_differences: 0
  };

  const totalBreakdown = (breakdown.corroborations + breakdown.contradictions + breakdown.contextual_differences) || 1;
  const pctCorrob = Math.round((breakdown.corroborations / totalBreakdown) * 100);
  const pctContext = Math.round((breakdown.contextual_differences / totalBreakdown) * 100);
  const pctConflict = Math.round((breakdown.contradictions / totalBreakdown) * 100);

  const activeDatasetInfo = overview?.active_dataset || {
    id: selectedDataset,
    name: selectedDataset === 'delhivery' ? 'Delhivery Logistics' : selectedDataset === 'india-macroeconomy' ? 'India Macroeconomy' : 'All Datasets',
    badge: 'Verified Starter Dataset',
    description: 'Evidence-grounded cross-document knowledge graph'
  };

  const datasetOptions = [
    { id: 'all', label: '🌐 All Datasets', count: '10 Docs' },
    { id: 'delhivery', label: '📦 Delhivery Logistics', count: '3 Docs' },
    { id: 'india-macroeconomy', label: '🇮🇳 India Macroeconomy', count: '3 Docs' },
    { id: 'synthetic', label: '🧪 Synthetic Benchmark', count: '4 Docs' },
  ];

  const handleExportJson = () => {
    if (!overview) return;
    const blob = new Blob([JSON.stringify(overview, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `factlens_${selectedDataset}_export.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const statCards = [
    { label: 'Documents', value: stats.documents, icon: FileText, tab: 'documents' as NavTab, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Extracted Facts', value: stats.facts, icon: Database, tab: 'facts' as NavTab, color: 'text-indigo-600', bg: 'bg-indigo-50' },
    { label: 'Cross-Doc Relations', value: stats.relationships, icon: GitCompare, tab: 'relationships' as NavTab, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Review Conflicts', value: stats.conflicts, icon: AlertTriangle, tab: 'conflicts' as NavTab, color: 'text-rose-600', bg: 'bg-rose-50', highlight: stats.conflicts > 0 },
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Hero Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span>Evidence-Grounded Knowledge Layer</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
            Turn scattered documents into trusted facts.
          </h2>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Extract numerical and semantic facts from PDFs, trace every claim to its exact source bounding box, and detect cross-document corroboration, contradiction, or contextual variance.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleExportJson}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium transition-colors cursor-pointer"
            title="Download structured JSON report"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Report</span>
          </button>
          <button
            onClick={() => setActiveTab('showcase')}
            className="px-3.5 py-2 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium transition-colors cursor-pointer"
          >
            Explore Case Showcase
          </button>
          <button
            onClick={onOpenUpload}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium shadow-sm transition-colors cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload Documents</span>
          </button>
        </div>
      </div>

      {/* Dataset Filter Selector & Banner */}
      <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-600" />
            <span className="text-xs font-semibold text-slate-900 uppercase tracking-wider">
              Starter Datasets Knowledge Focus:
            </span>
          </div>
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
            {datasetOptions.map((opt) => (
              <button
                key={opt.id}
                onClick={() => onSelectDataset(opt.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer shrink-0 ${
                  selectedDataset === opt.id
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'bg-slate-100 hover:bg-slate-200/70 text-slate-700'
                }`}
              >
                <span>{opt.label}</span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                  selectedDataset === opt.id ? 'bg-slate-800 text-emerald-300' : 'bg-slate-200 text-slate-600'
                }`}>
                  {opt.count}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="pt-2 border-t border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2 text-slate-600">
            <span className="font-semibold text-slate-900">{activeDatasetInfo.name}</span>
            <span className="text-slate-400">·</span>
            <span className="text-slate-500">{activeDatasetInfo.description}</span>
          </div>
          <div className="flex items-center gap-3 text-[11px] font-medium text-slate-500 shrink-0">
            <span>Grounding: <strong className="text-emerald-600 font-semibold">100% Provenance</strong></span>
            <span>Speed: <strong className="text-indigo-600 font-semibold">&lt; 1s / 100pg</strong></span>
          </div>
        </div>
      </div>

      {/* Resolution Distribution Analytics Bar */}
      <div className="p-5 rounded-xl border border-slate-200 bg-white shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span>Multi-Dimensional Resolution Distribution</span>
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Breakdown of how claims reconcile across temporal periods, institutional models, and units.
            </p>
          </div>
          <div className="text-right text-xs">
            <span className="font-bold text-slate-900">{stats.relationships}</span>
            <span className="text-slate-400 ml-1">total links</span>
          </div>
        </div>

        {/* Stacked Progress Meter */}
        <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden flex gap-0.5">
          <div
            style={{ width: `${Math.max(pctCorrob, 2)}%` }}
            className="h-full bg-emerald-500 transition-all duration-500"
            title={`Corroborations: ${breakdown.corroborations} (${pctCorrob}%)`}
          />
          <div
            style={{ width: `${Math.max(pctContext, 2)}%` }}
            className="h-full bg-amber-400 transition-all duration-500"
            title={`Contextual Differences: ${breakdown.contextual_differences} (${pctContext}%)`}
          />
          <div
            style={{ width: `${Math.max(pctConflict, 2)}%` }}
            className="h-full bg-rose-500 transition-all duration-500"
            title={`Contradictions: ${breakdown.contradictions} (${pctConflict}%)`}
          />
        </div>

        {/* Meter Legend */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs pt-1">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
            <span className="text-slate-600">Corroborated:</span>
            <strong className="text-slate-900">{breakdown.corroborations}</strong>
            <span className="text-slate-400 text-[11px]">({pctCorrob}%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block" />
            <span className="text-slate-600">Contextual Differences:</span>
            <strong className="text-slate-900">{breakdown.contextual_differences}</strong>
            <span className="text-slate-400 text-[11px]">({pctContext}%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
            <span className="text-slate-600">Review Contradictions:</span>
            <strong className="text-rose-600">{breakdown.contradictions}</strong>
            <span className="text-slate-400 text-[11px]">({pctConflict}%)</span>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              onClick={() => setActiveTab(card.tab)}
              className={`p-5 rounded-xl border bg-white shadow-xs hover:border-slate-300 hover:shadow-sm transition-all cursor-pointer ${
                card.highlight ? 'border-rose-300 ring-1 ring-rose-500/20' : 'border-slate-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">{card.label}</span>
                <div className={`w-7 h-7 rounded-lg ${card.bg} flex items-center justify-center ${card.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 tracking-tight">
                  {loading ? '—' : card.value}
                </span>
                {card.highlight && (
                  <span className="text-[10px] font-semibold text-rose-600 bg-rose-50 px-1.5 py-0.5 rounded-full">
                    Requires review
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Knowledge Signals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Recent Knowledge Signals */}
        <div className="p-5 rounded-xl border border-slate-200 bg-white shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">
              Cross-Document Signals
            </h3>
            <button
              onClick={() => setActiveTab('relationships')}
              className="text-xs text-emerald-600 hover:text-emerald-700 font-medium flex items-center gap-1 cursor-pointer"
            >
              <span>View all</span>
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-3">
            {overview?.recent_relationships && overview.recent_relationships.length > 0 ? (
              overview.recent_relationships.slice(0, 4).map((rel, idx) => {
                const badgeColor =
                  rel.relationship_type === 'CORROBORATES'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : rel.relationship_type === 'CONTRADICTS'
                    ? 'bg-rose-50 text-rose-700 border-rose-200'
                    : 'bg-amber-50 text-amber-700 border-amber-200';

                return (
                  <div key={idx} className="p-3 rounded-lg border border-slate-100 bg-slate-50/50 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-900">
                        {rel.entity} · <span className="text-slate-500">{rel.predicate}</span>
                      </span>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${badgeColor}`}>
                        {rel.relationship_type}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span>{rel.doc_a}: <strong className="text-slate-700">{rel.fact_a_value}</strong></span>
                      <span>vs</span>
                      <span>{rel.doc_b}: <strong className="text-slate-700">{rel.fact_b_value}</strong></span>
                    </div>
                    <p className="text-[11px] text-slate-600 line-clamp-1 italic">
                      "{rel.explanation}"
                    </p>
                  </div>
                );
              })
            ) : (
              <div className="text-center py-8 text-xs text-slate-400">
                No cross-document relationships recorded yet. Upload multiple PDFs to discover corroboration and conflicts.
              </div>
            )}
          </div>
        </div>

        {/* Recent Ingested Documents */}
        <div className="p-5 rounded-xl border border-slate-200 bg-white shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">
              Recent Documents
            </h3>
            <button
              onClick={() => setActiveTab('documents')}
              className="text-xs text-emerald-600 hover:text-emerald-700 font-medium flex items-center gap-1 cursor-pointer"
            >
              <span>Manage documents</span>
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2.5">
            {overview?.recent_documents && overview.recent_documents.length > 0 ? (
              overview.recent_documents.map((doc, idx) => (
                <div
                  key={idx}
                  onClick={() => setActiveTab('documents')}
                  className="p-3 rounded-lg border border-slate-100 hover:border-slate-200 hover:bg-slate-50/60 transition-all flex items-center justify-between cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-600">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-medium text-slate-900">{doc.filename}</h4>
                      <p className="text-[11px] text-slate-400">
                        {doc.page_count} pages · {doc.fact_count} facts extracted
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-600">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span className="capitalize">{doc.status}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-xs text-slate-400">
                No documents uploaded yet. Use the upload button above to ingest your first PDF.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

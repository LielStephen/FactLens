'use client';

import React, { useState, useEffect } from 'react';
import { 
  X, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  Calendar, 
  Globe, 
  ShieldCheck,
  ExternalLink,
  GitCompare,
  ArrowRight
} from 'lucide-react';
import { Fact, FactRelationship } from '@/types';
import { fetchFactRelationships } from '@/lib/api';

interface FactDetailDrawerProps {
  fact: Fact | null;
  onClose: () => void;
  onInspectRelationship?: (rel: FactRelationship) => void;
}

export const FactDetailDrawer: React.FC<FactDetailDrawerProps> = ({
  fact,
  onClose,
  onInspectRelationship
}) => {
  const [relationships, setRelationships] = useState<FactRelationship[]>([]);
  const [loadingRel, setLoadingRel] = useState<boolean>(false);

  useEffect(() => {
    if (!fact) return;
    setLoadingRel(true);
    fetchFactRelationships(fact.id)
      .then(res => setRelationships(res))
      .catch(err => console.error(err))
      .finally(() => setLoadingRel(false));
  }, [fact]);

  if (!fact) return null;

  const ev = fact.evidence;
  const isHighConf = fact.confidence >= 0.90;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end">
      <div className="w-full max-w-md bg-white h-full shadow-2xl border-l border-slate-200 flex flex-col animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between shrink-0 bg-slate-50/75">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              Fact Intelligence Detail
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-md transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Drawer Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Main Fact Card */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">
              {fact.subject}
            </span>
            <div className="flex items-baseline justify-between gap-2">
              <h3 className="text-xl font-bold text-slate-900 tracking-tight">
                {fact.predicate}
              </h3>
              <span className="text-xl font-bold text-emerald-700">
                {fact.raw_value}
              </span>
            </div>

            {/* Confidence Pill */}
            <div className="pt-2 flex items-center gap-2">
              <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                isHighConf
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border border-amber-200'
              }`}>
                <ShieldCheck className="w-3.5 h-3.5" />
                Confidence: {Math.round(fact.confidence * 100)}%
              </span>
              <span className="text-[11px] text-slate-400">
                {isHighConf ? 'Grounded & Validated' : 'Needs Review'}
              </span>
            </div>
          </div>

          {/* Context Dimensions */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5 text-xs">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Context Dimensions
            </div>
            <div className="flex items-center justify-between text-slate-600">
              <span className="flex items-center gap-1.5 text-slate-500">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                Time Period:
              </span>
              <span className="font-semibold text-slate-800">
                {fact.time?.label || 'Not specified'}
              </span>
            </div>
            <div className="flex items-center justify-between text-slate-600">
              <span className="flex items-center gap-1.5 text-slate-500">
                <Globe className="w-3.5 h-3.5 text-slate-400" />
                Scope:
              </span>
              <span className="font-semibold text-slate-800 capitalize">
                {fact.scope || 'Global'}
              </span>
            </div>
            {fact.unit && (
              <div className="flex items-center justify-between text-slate-600">
                <span className="text-slate-500">Reporting Unit:</span>
                <span className="font-semibold text-slate-800">{fact.unit}</span>
              </div>
            )}
          </div>

          {/* Grounded Evidence Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Source Document Grounding
              </h4>
              <span className="text-[10px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                {ev?.validation_status === 'grounded' ? 'Exact Match Grounded' : 'Grounded'}
              </span>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-600">
                <div className="flex items-center gap-1.5 font-medium text-slate-900">
                  <FileText className="w-3.5 h-3.5 text-slate-400" />
                  <span className="truncate max-w-[200px]">{fact.document_filename || 'Source Document'}</span>
                </div>
                <span className="text-slate-500 font-mono text-[11px]">
                  Page {ev?.page || 1}
                </span>
              </div>

              {/* Exact Quote */}
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-800 italic leading-relaxed">
                "{ev?.quote || 'Exact evidence quote registered in database.'}"
              </div>

              {/* Bounding Box Coordinates */}
              {ev?.bbox && ev.bbox.length === 4 && (
                <div className="text-[10px] font-mono text-slate-400 flex items-center justify-between">
                  <span>Bounding Box:</span>
                  <span>[{ev.bbox.map(n => Math.round(n)).join(', ')}]</span>
                </div>
              )}
            </div>
          </div>

          {/* Cross-Document Relationships Section */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Cross-Document Relationships ({relationships.length})
            </h4>

            <div className="space-y-2.5">
              {loadingRel ? (
                <div className="text-center py-6 text-xs text-slate-400">Loading relationships...</div>
              ) : relationships.length > 0 ? (
                relationships.map((rel) => {
                  const badgeColor =
                    rel.relationship_type === 'CORROBORATES'
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : rel.relationship_type === 'CONTRADICTS'
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : 'bg-amber-50 text-amber-700 border-amber-200';

                  const otherFact = rel.related_fact;

                  return (
                    <div
                      key={rel.id}
                      className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-xs space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${badgeColor}`}>
                          {rel.relationship_type}
                        </span>
                        <span className="text-[10px] text-slate-400">
                          {Math.round(rel.confidence * 100)}% Conf
                        </span>
                      </div>

                      {otherFact && (
                        <div className="text-xs text-slate-700">
                          <p className="font-medium text-slate-900">
                            {otherFact.document_filename} (p. {otherFact.page})
                          </p>
                          <p className="text-slate-500 mt-0.5">
                            Reported Value: <strong className="text-slate-800">{otherFact.value}</strong>
                            {otherFact.time?.label && ` · ${otherFact.time.label}`}
                          </p>
                        </div>
                      )}

                      <p className="text-[11px] text-slate-600 italic bg-slate-50 p-2 rounded border border-slate-100">
                        "{rel.explanation}"
                      </p>
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-6 text-xs text-slate-400 border border-dashed border-slate-200 rounded-xl">
                  No cross-document relationships identified yet.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

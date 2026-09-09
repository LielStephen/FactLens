'use client';

import React, { useState, useEffect } from 'react';
import { AlertTriangle, ShieldAlert, ArrowRight, FileText, CheckCircle2 } from 'lucide-react';
import { FactRelationship } from '@/types';
import { fetchConflicts } from '@/lib/api';
import { EvidenceInspectorModal } from './EvidenceInspectorModal';

interface ConflictsViewProps {
  selectedDataset?: string;
}

export const ConflictsView: React.FC<ConflictsViewProps> = ({ selectedDataset = 'all' }) => {
  const [contradictions, setContradictions] = useState<FactRelationship[]>([]);
  const [flaggedFacts, setFlaggedFacts] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedRel, setSelectedRel] = useState<FactRelationship | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchConflicts(selectedDataset)
      .then(res => {
        setContradictions(res.contradictions || []);
        setFlaggedFacts(res.flagged_facts || []);
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedDataset]);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-200 pb-5">
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Review Conflicts</h2>
          <span className="text-xs px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 font-semibold">
            {contradictions.length} potential conflicts
          </span>
        </div>
        <p className="text-xs text-slate-500 mt-0.5">
          High-priority contradictions across documents where claims align in entity and period but conflict in asserted values
        </p>
      </div>

      {/* Contradictions Stream */}
      <div className="space-y-4">
        {contradictions.length > 0 ? (
          contradictions.map(rel => {
            const fa = rel.fact_a;
            const fb = rel.fact_b;

            return (
              <div
                key={rel.id}
                className="p-5 rounded-xl border border-rose-200 bg-white hover:border-rose-300 shadow-xs transition-all space-y-4"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-1">
                      <ShieldAlert className="w-3 h-3" />
                      Likely Conflict
                    </span>
                    <span className="text-xs font-bold text-slate-900">
                      {fa?.subject} · <span className="font-medium text-slate-600">{fa?.predicate}</span>
                    </span>
                  </div>

                  <span className="text-xs font-mono font-semibold text-rose-700">
                    {Math.round(rel.confidence * 100)}% Conflict Certainty
                  </span>
                </div>

                {/* Values Comparison Strip */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-rose-50/40 p-4 rounded-lg border border-rose-100">
                  <div className="space-y-1">
                    <div className="text-[11px] text-slate-500 font-medium">
                      {fa?.document_filename} (p.{fa?.evidence?.page || 1})
                    </div>
                    <div className="text-base font-bold text-slate-900">
                      {fa?.raw_value}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Period: <strong className="text-slate-700">{fa?.time?.label || 'Current'}</strong>
                    </div>
                    <p className="text-[11px] text-slate-700 italic pt-1">
                      "{fa?.evidence?.quote || 'No quote'}"
                    </p>
                  </div>

                  <div className="space-y-1 border-t md:border-t-0 md:border-l border-rose-200 pt-3 md:pt-0 md:pl-4">
                    <div className="text-[11px] text-slate-500 font-medium">
                      {fb?.document_filename} (p.{fb?.evidence?.page || 1})
                    </div>
                    <div className="text-base font-bold text-slate-900">
                      {fb?.raw_value}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Period: <strong className="text-slate-700">{fb?.time?.label || 'Current'}</strong>
                    </div>
                    <p className="text-[11px] text-slate-700 italic pt-1">
                      "{fb?.evidence?.quote || 'No quote'}"
                    </p>
                  </div>
                </div>

                {/* Conflict Explanation & Review Trigger */}
                <div className="flex items-center justify-between pt-1">
                  <p className="text-xs text-slate-700 max-w-2xl leading-relaxed">
                    <strong>Resolution Reasoning:</strong> {rel.explanation}
                  </p>

                  <button
                    onClick={() => setSelectedRel(rel)}
                    className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer shrink-0"
                  >
                    <span>Inspect Evidence</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-16 bg-white border border-slate-200 rounded-xl space-y-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
            <p className="text-xs font-medium text-slate-700">No unresolved contradictions found</p>
            <p className="text-[11px] text-slate-400">
              All extracted facts either corroborate or have valid contextual explanations (differing periods or scopes).
            </p>
          </div>
        )}
      </div>

      {/* Flagged Facts with Extraction Ambiguities */}
      {flaggedFacts.length > 0 && (
        <div className="pt-6 border-t border-slate-200 space-y-4">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-900">Extraction Quality Exceptions</h3>
            <span className="text-[10px] bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-semibold">
              {flaggedFacts.length} flagged
            </span>
          </div>

          <div className="space-y-3">
            {flaggedFacts.map((ff, idx) => (
              <div key={idx} className="p-4 rounded-xl border border-amber-200 bg-amber-50/40 text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-900">{ff.subject} · {ff.predicate}</span>
                  <span className="text-amber-800 font-mono text-[11px]">Flag: {ff.flag_reason}</span>
                </div>
                <div className="text-slate-600">
                  Asserted: <strong>{ff.raw_value}</strong> ({ff.document_filename}, p.{ff.page})
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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

'use client';

import React from 'react';
import { X, FileText, CheckCircle2, AlertTriangle, HelpCircle, ShieldAlert, ArrowDown } from 'lucide-react';
import { FactRelationship } from '@/types';

interface EvidenceInspectorModalProps {
  relationship: FactRelationship | null;
  onClose: () => void;
}

export const EvidenceInspectorModal: React.FC<EvidenceInspectorModalProps> = ({
  relationship,
  onClose
}) => {
  if (!relationship) return null;

  const fa = relationship.fact_a;
  const fb = relationship.fact_b;

  const isContradiction = relationship.relationship_type === 'CONTRADICTS';
  const isCorroboration = relationship.relationship_type === 'CORROBORATES';
  const isContextual = relationship.relationship_type === 'CONTEXTUAL_DIFFERENCE';

  const badgeColor = isCorroboration
    ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
    : isContradiction
    ? 'bg-rose-50 text-rose-800 border-rose-300'
    : 'bg-amber-50 text-amber-800 border-amber-300';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50 shrink-0">
          <div>
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
              Cross-Document Evidence Inspector
            </span>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              {fa?.subject || 'Entity'} · {fa?.predicate || 'Predicate'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-md transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Side-by-Side Document Panels */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Document A */}
            <div className="p-5 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-slate-500" />
                  <span className="text-xs font-semibold text-slate-900">
                    {fa?.document_filename || 'Document A'}
                  </span>
                </div>
                <span className="text-[11px] font-mono bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-600">
                  Page {fa?.evidence?.page || 1}
                </span>
              </div>

              <div className="bg-white p-3 rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider">Asserted Value</span>
                <div className="text-lg font-bold text-slate-900 mt-0.5">
                  {fa?.raw_value}
                </div>
                <div className="text-[11px] text-slate-500 mt-1">
                  Period: <strong className="text-slate-700">{fa?.time?.label || 'Not specified'}</strong> · Scope: <strong className="text-slate-700">{fa?.scope || 'Global'}</strong>
                </div>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider">Exact Source Evidence</span>
                <div className="p-3 bg-white rounded-lg border-l-3 border-slate-400 border border-slate-200 text-xs text-slate-800 italic leading-relaxed">
                  "{fa?.evidence?.quote || 'No quote'}"
                </div>
              </div>
            </div>

            {/* Document B */}
            <div className="p-5 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-slate-500" />
                  <span className="text-xs font-semibold text-slate-900">
                    {fb?.document_filename || 'Document B'}
                  </span>
                </div>
                <span className="text-[11px] font-mono bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-600">
                  Page {fb?.evidence?.page || 1}
                </span>
              </div>

              <div className="bg-white p-3 rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider">Asserted Value</span>
                <div className="text-lg font-bold text-slate-900 mt-0.5">
                  {fb?.raw_value}
                </div>
                <div className="text-[11px] text-slate-500 mt-1">
                  Period: <strong className="text-slate-700">{fb?.time?.label || 'Not specified'}</strong> · Scope: <strong className="text-slate-700">{fb?.scope || 'Global'}</strong>
                </div>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider">Exact Source Evidence</span>
                <div className="p-3 bg-white rounded-lg border-l-3 border-slate-400 border border-slate-200 text-xs text-slate-800 italic leading-relaxed">
                  "{fb?.evidence?.quote || 'No quote'}"
                </div>
              </div>
            </div>
          </div>

          {/* Center Connector */}
          <div className="flex justify-center">
            <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-500">
              <ArrowDown className="w-4 h-4" />
            </div>
          </div>

          {/* Relationship Decision & Explanation Card */}
          <div className={`p-6 rounded-xl border ${badgeColor} space-y-3`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold tracking-tight uppercase">
                  {relationship.relationship_type.replace(/_/g, ' ')}
                </span>
                <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-white/70 border border-current/20">
                  Confidence: {Math.round(relationship.confidence * 100)}%
                </span>
              </div>
              <span className="text-[11px] font-mono capitalize text-slate-600">
                Tier: {relationship.resolution_tier}
              </span>
            </div>

            {/* Explanation */}
            <p className="text-xs leading-relaxed font-medium">
              {relationship.explanation}
            </p>

            {/* Dimensions Checklist */}
            <div className="pt-2 border-t border-current/15 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                <span>Same Entity</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                <span>Same Predicate</span>
              </div>
              <div className="flex items-center gap-1.5">
                {isContradiction || isCorroboration ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                ) : (
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                )}
                <span>Aligned Time Period</span>
              </div>
              <div className="flex items-center gap-1.5">
                {isContradiction ? (
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                ) : (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                )}
                <span>Value Consistency</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};

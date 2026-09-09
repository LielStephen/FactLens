'use client';

import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  CheckCircle2, 
  ShieldAlert, 
  Clock, 
  AlertTriangle, 
  FileText,
  ArrowRight,
  HelpCircle,
  ShieldCheck
} from 'lucide-react';
import { fetchShowcase } from '@/lib/api';
import { EvidenceInspectorModal } from './EvidenceInspectorModal';

export const ShowcaseView: React.FC = () => {
  const [showcaseData, setShowcaseData] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedRel, setSelectedRel] = useState<any>(null);

  useEffect(() => {
    fetchShowcase()
      .then(res => setShowcaseData(res))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const cases = [
    {
      key: 'case_1_corroboration',
      number: '1',
      title: 'Independent Corroboration',
      badge: 'CORROBORATES',
      badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      icon: CheckCircle2,
      subtitle: 'Two independent sources affirm identical factual claims.',
      sampleDocA: 'Document A (Annual Report 2023)',
      sampleDocB: 'Document B (Annual Report 2024)',
      sampleFact: 'Acme Corporation Headquarters → San Francisco, California',
      why: 'Both documents independently declare San Francisco as the corporate headquarters. Same entity, same predicate, same value.',
    },
    {
      key: 'case_2_contradiction',
      number: '2',
      title: 'Genuine / Likely Contradiction',
      badge: 'CONTRADICTS',
      badgeColor: 'bg-rose-50 text-rose-700 border-rose-200',
      icon: ShieldAlert,
      subtitle: 'Both sources assert incompatible figures for the identical entity and fiscal period.',
      sampleDocA: 'Document B (Annual Report FY2024) — p. 1',
      sampleDocB: 'Document C (Audit Filing FY2024) — p. 1',
      sampleFact: 'Acme Corporation FY2024 Revenue → $125M vs $142M',
      why: 'Direct numerical conflict: Entity matches, predicate matches, reporting period is identical (FY2024), but asserted revenue values differ by $17M without an explanatory contextual qualifier.',
    },
    {
      key: 'case_3_contextual_difference',
      number: '3',
      title: 'Contextual Difference (Not a Contradiction)',
      badge: 'CONTEXTUAL DIFFERENCE',
      badgeColor: 'bg-amber-50 text-amber-700 border-amber-200',
      icon: Clock,
      subtitle: 'Numerical values differ, but the variance is justified by distinct reporting years.',
      sampleDocA: 'Document A (FY2023 Report) — $100M',
      sampleDocB: 'Document B (FY2024 Report) — $125M',
      sampleFact: 'Acme Corporation Annual Revenue → FY2023 vs FY2024',
      why: 'Different reporting periods explain the difference: Document A reports FY2023 revenue while Document B reports FY2024 revenue. The system recognizes this as normal temporal variance rather than a false contradiction.',
    },
    {
      key: 'case_4_extraction_failure',
      number: '4',
      title: 'Extraction Diagnostics & Grounding Failures',
      badge: 'VALIDATION EXCEPTION',
      badgeColor: 'bg-slate-100 text-slate-700 border-slate-300',
      icon: AlertTriangle,
      subtitle: 'Handling ungrounded quotes, multi-column footnotes, and OCR ambiguity.',
      sampleDocA: 'Document C — Ambiguous Footnote 14B',
      sampleDocB: 'Evidence Grounding Validator',
      sampleFact: 'Unverifiable Restatement Clause (* currency scale omission)',
      why: 'Independent Evidence Validation catches ungrounded or ambiguous claims before they can corrupt the knowledge graph. Facts lacking verifiable source quotes have their confidence reduced to < 30% and are excluded from high-confidence relationships.',
    }
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-200 pb-5">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-emerald-600" />
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Assignment Case Showcase</h2>
        </div>
        <p className="text-xs text-slate-500 mt-0.5">
          End-to-end demonstration of the four core evaluation cases required by the Superjoin Fact Knowledge Layer specification
        </p>
      </div>

      {/* 4 Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {cases.map((c) => {
          const Icon = c.icon;
          const liveData = showcaseData[c.key]?.data;

          return (
            <div
              key={c.key}
              className="p-6 rounded-xl border border-slate-200 bg-white shadow-xs space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-slate-900 text-white font-bold text-xs flex items-center justify-center">
                      {c.number}
                    </span>
                    <h3 className="text-sm font-bold text-slate-900">{c.title}</h3>
                  </div>
                  <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${c.badgeColor}`}>
                    {c.badge}
                  </span>
                </div>

                <p className="text-xs text-slate-500 leading-relaxed">
                  {c.subtitle}
                </p>

                {/* Evidence Comparison Box */}
                <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-2 text-xs">
                  <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-slate-400" />
                    <span>{liveData?.fact_a ? `${liveData.fact_a.subject} · ${liveData.fact_a.predicate}` : c.sampleFact}</span>
                  </div>

                  <div className="text-[11px] text-slate-600 flex items-center justify-between">
                    <span>Source 1: <strong>{liveData?.fact_a?.document_filename || c.sampleDocA}</strong></span>
                    <span>Source 2: <strong>{liveData?.fact_b?.document_filename || c.sampleDocB}</strong></span>
                  </div>

                  {liveData?.explanation && (
                    <div className="p-2 rounded bg-white border border-slate-200 text-[11px] text-slate-700 italic">
                      "{liveData.explanation}"
                    </div>
                  )}
                </div>

                {/* Grounding Rationale */}
                <div className="space-y-1">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                    Engineering Rationale
                  </span>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {c.why}
                  </p>
                </div>
              </div>

              {/* Action */}
              {liveData?.id && (
                <button
                  onClick={() => setSelectedRel(liveData)}
                  className="w-full mt-2 py-2 px-3 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-medium text-slate-700 flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                >
                  <span>Inspect Live Evidence Pair</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Modal */}
      {selectedRel && (
        <EvidenceInspectorModal
          relationship={selectedRel}
          onClose={() => setSelectedRel(null)}
        />
      )}
    </div>
  );
};

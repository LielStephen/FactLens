'use client';

import React, { useState, useEffect } from 'react';
import { X, FileText, CheckCircle2, AlertTriangle, Layers, Table as TableIcon } from 'lucide-react';
import { fetchDocumentPages } from '@/lib/api';
import { DocumentItem, DocumentPage } from '@/types';

interface DocumentDetailModalProps {
  document: DocumentItem | null;
  onClose: () => void;
}

export const DocumentDetailModal: React.FC<DocumentDetailModalProps> = ({
  document,
  onClose
}) => {
  const [pages, setPages] = useState<DocumentPage[]>([]);
  const [selectedPageNumber, setSelectedPageNumber] = useState<number>(1);
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!document) return;
    setLoading(true);
    fetchDocumentPages(document.id)
      .then(res => {
        setPages(res);
        if (res.length > 0) {
          setSelectedPageNumber(res[0].page_number);
        }
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [document]);

  if (!document) return null;

  const activePage = pages.find(p => p.page_number === selectedPageNumber);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-5xl h-[85vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between shrink-0 bg-slate-50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center text-blue-700">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">{document.filename}</h3>
              <p className="text-[11px] text-slate-500">
                {document.page_count} Pages · {document.fact_count} Facts Extracted · Extraction Quality Verified
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-md transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Column: Page Selector */}
          <div className="w-48 border-r border-slate-200 p-3 overflow-y-auto space-y-1 shrink-0 bg-slate-50/50">
            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-2 mb-2">
              Document Pages
            </div>
            {pages.map((p) => {
              const isSelected = p.page_number === selectedPageNumber;
              return (
                <button
                  key={p.page_number}
                  onClick={() => setSelectedPageNumber(p.page_number)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                    isSelected
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <span>Page {p.page_number}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded ${
                    isSelected ? 'bg-slate-800 text-slate-300' : 'bg-slate-200 text-slate-600'
                  }`}>
                    {p.blocks.length} blk
                  </span>
                </button>
              );
            })}
          </div>

          {/* Right Column: Visual Page & Layout Blocks */}
          <div className="flex-1 flex flex-col overflow-hidden bg-slate-100">
            {/* Page Header Bar */}
            <div className="px-6 py-2.5 bg-white border-b border-slate-200 flex items-center justify-between text-xs text-slate-600">
              <div className="flex items-center gap-4">
                <span>Page {selectedPageNumber} of {pages.length}</span>
                <span className="text-slate-300">|</span>
                <span className="flex items-center gap-1 text-emerald-600 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Method: {activePage?.extraction_method || 'native'}
                </span>
                <span className="text-slate-300">|</span>
                <span>Quality Score: {Math.round((activePage?.quality_score || 1) * 100)}%</span>
              </div>
              <div className="text-[11px] text-slate-400">
                Click any block to highlight its bounding box
              </div>
            </div>

            {/* Page Canvas / Block Stream */}
            <div className="flex-1 p-6 overflow-y-auto space-y-3">
              {activePage ? (
                activePage.blocks.map((b) => {
                  const isSelected = selectedBlockId === b.id;
                  const isTable = b.type === 'table';

                  return (
                    <div
                      key={b.id}
                      onClick={() => setSelectedBlockId(isSelected ? null : b.id)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer ${
                        isSelected
                          ? 'border-emerald-500 bg-white shadow-md ring-2 ring-emerald-500/20'
                          : 'border-slate-200 bg-white hover:border-slate-300 shadow-xs'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full ${
                            isTable ? 'bg-purple-50 text-purple-700 border border-purple-200' :
                            b.type === 'heading' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
                            'bg-slate-100 text-slate-700'
                          }`}>
                            {b.type}
                          </span>
                          <span className="text-[10px] font-mono text-slate-400">
                            {b.id}
                          </span>
                        </div>

                        {b.bbox && b.bbox.length === 4 && (
                          <span className="text-[10px] font-mono text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                            bbox: [{b.bbox.map(n => Math.round(n)).join(', ')}]
                          </span>
                        )}
                      </div>

                      <div className="text-xs text-slate-800 font-sans leading-relaxed whitespace-pre-wrap">
                        {b.text}
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-20 text-xs text-slate-400">
                  Select a page to inspect layout blocks.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

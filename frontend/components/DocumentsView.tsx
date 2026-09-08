'use client';

import React, { useState } from 'react';
import { FileText, Upload, CheckCircle2, AlertCircle, Loader2, ArrowRight } from 'lucide-react';
import { DocumentItem } from '@/types';
import { DocumentDetailModal } from './DocumentDetailModal';

interface DocumentsViewProps {
  documents: DocumentItem[];
  loading: boolean;
  onOpenUpload: () => void;
}

export const DocumentsView: React.FC<DocumentsViewProps> = ({
  documents,
  loading,
  onOpenUpload
}) => {
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);
  const [filterQuery, setFilterQuery] = useState<string>('');

  const filteredDocs = documents.filter(d =>
    d.filename.toLowerCase().includes(filterQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Documents</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Ingested PDF source files, layout structures, and extraction quality
          </p>
        </div>

        <button
          onClick={onOpenUpload}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium shadow-sm transition-colors cursor-pointer"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>Upload New PDF</span>
        </button>
      </div>

      {/* Search Input */}
      <div className="max-w-xs">
        <input
          type="text"
          value={filterQuery}
          onChange={(e) => setFilterQuery(e.target.value)}
          placeholder="Filter documents by filename..."
          className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
        />
      </div>

      {/* Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/75 text-slate-500 font-semibold uppercase text-[10px] tracking-wider">
              <th className="py-3 px-4">Document</th>
              <th className="py-3 px-4">Pages</th>
              <th className="py-3 px-4">Facts Extracted</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {filteredDocs.length > 0 ? (
              filteredDocs.map((doc) => (
                <tr
                  key={doc.id}
                  className="hover:bg-slate-50/60 transition-colors group cursor-pointer"
                  onClick={() => setSelectedDoc(doc)}
                >
                  <td className="py-3.5 px-4 font-medium text-slate-900 flex items-center gap-2.5">
                    <FileText className="w-4 h-4 text-slate-400 group-hover:text-emerald-600 transition-colors shrink-0" />
                    <span className="truncate max-w-sm">{doc.filename}</span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-500">
                    {doc.page_count} {doc.page_count === 1 ? 'page' : 'pages'}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="font-semibold text-slate-800">{doc.fact_count}</span> facts
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-1.5">
                      {doc.status === 'completed' && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                          <CheckCircle2 className="w-3 h-3" />
                          Ready
                        </span>
                      )}
                      {doc.status === 'processing' && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded-full">
                          <Loader2 className="w-3 h-3 animate-spin" />
                          Processing
                        </span>
                      )}
                      {doc.status === 'failed' && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded-full">
                          <AlertCircle className="w-3 h-3" />
                          Failed
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedDoc(doc);
                      }}
                      className="text-xs font-medium text-slate-600 hover:text-slate-900 inline-flex items-center gap-1 px-2.5 py-1 rounded-md border border-slate-200 hover:bg-slate-100 transition-all cursor-pointer"
                    >
                      <span>Inspect Layout</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="py-12 text-center text-slate-400 text-xs">
                  {loading ? 'Loading documents...' : 'No documents found matching the filter.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Document Detail Modal */}
      {selectedDoc && (
        <DocumentDetailModal
          document={selectedDoc}
          onClose={() => setSelectedDoc(null)}
        />
      )}
    </div>
  );
};

'use client';

import React, { useState, useRef } from 'react';
import { X, UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { uploadDocument, fetchDocumentStatus } from '@/lib/api';
import { DocumentStatus } from '@/types';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
}

interface UploadingFileState {
  file: File;
  documentId?: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  stage: string;
  message: string;
  error?: string;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess
}) => {
  const [uploadStates, setUploadStates] = useState<UploadingFileState[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFiles = async (files: FileList | File[]) => {
    const pdfFiles = Array.from(files).filter(f => f.name.toLowerCase().endsWith('.pdf'));
    if (pdfFiles.length === 0) {
      alert('Please select valid PDF documents.');
      return;
    }

    const initialStates: UploadingFileState[] = pdfFiles.map(file => ({
      file,
      status: 'uploading',
      progress: 10,
      stage: 'UPLOADING',
      message: 'Uploading to server...'
    }));

    setUploadStates(prev => [...prev, ...initialStates]);

    // Process uploads
    for (let i = 0; i < pdfFiles.length; i++) {
      const file = pdfFiles[i];
      try {
        const res = await uploadDocument(file);
        const docId = res.document_id;

        if (res.status === 'completed') {
          setUploadStates(prev =>
            prev.map(item =>
              item.file === file
                ? {
                    ...item,
                    documentId: docId,
                    status: 'completed',
                    progress: 100,
                    stage: 'COMPLETE',
                    message: res.message || 'Document already indexed & verified in knowledge graph.'
                  }
                : item
            )
          );
          onUploadSuccess();
          continue;
        }

        setUploadStates(prev =>
          prev.map(item =>
            item.file === file
              ? {
                  ...item,
                  documentId: docId,
                  status: 'processing',
                  progress: 25,
                  stage: 'LAYOUT_EXTRACTION',
                  message: 'Analyzing PDF blocks and tables...'
                }
              : item
          )
        );

        // Poll for processing completion
        pollDocumentStatus(docId, file);
      } catch (err: any) {
        setUploadStates(prev =>
          prev.map(item =>
            item.file === file
              ? {
                  ...item,
                  status: 'failed',
                  progress: 100,
                  stage: 'FAILED',
                  message: err.message || 'Upload failed',
                  error: err.message
                }
              : item
          )
        );
      }
    }
  };

  const pollDocumentStatus = (documentId: string, file: File) => {
    const interval = setInterval(async () => {
      try {
        const statusRes: DocumentStatus = await fetchDocumentStatus(documentId);
        
        setUploadStates(prev =>
          prev.map(item => {
            if (item.file === file) {
              return {
                ...item,
                status: statusRes.status === 'completed' ? 'completed' : statusRes.status === 'failed' ? 'failed' : 'processing',
                progress: statusRes.progress || 50,
                stage: statusRes.stage,
                message: statusRes.message,
                error: statusRes.status === 'failed' ? statusRes.message : undefined
              };
            }
            return item;
          })
        );

        if (statusRes.status === 'completed' || statusRes.status === 'failed') {
          clearInterval(interval);
          onUploadSuccess();
        }
      } catch (err) {
        clearInterval(interval);
      }
    }, 1500);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Upload PDF Documents</h3>
            <p className="text-xs text-slate-500 mt-0.5">Ingest unstructured reports into the evidence-grounded fact layer</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          {/* Dropzone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
              isDragging
                ? 'border-emerald-500 bg-emerald-50/50'
                : 'border-slate-200 hover:border-slate-300 bg-slate-50/60'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => e.target.files && handleFiles(e.target.files)}
              multiple
              accept=".pdf"
              className="hidden"
            />
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-500 mb-3">
              <UploadCloud className="w-6 h-6 text-slate-600" />
            </div>
            <p className="text-xs font-semibold text-slate-800">
              Click to choose or drag and drop PDFs here
            </p>
            <p className="text-[11px] text-slate-500 mt-1">
              Supports multi-page financial statements, filings, corporate reports (PDF only)
            </p>
          </div>

          {/* Upload Progress List */}
          {uploadStates.length > 0 && (
            <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                Active Ingestion Pipeline
              </div>
              {uploadStates.map((item, idx) => (
                <div key={idx} className="p-3 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0">
                      <FileText className="w-4 h-4 text-slate-500 shrink-0" />
                      <span className="text-xs font-medium text-slate-800 truncate max-w-[260px]">
                        {item.file.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      {item.status === 'processing' && (
                        <Loader2 className="w-3.5 h-3.5 text-emerald-600 animate-spin" />
                      )}
                      {item.status === 'completed' && (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      )}
                      {item.status === 'failed' && (
                        <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                      )}
                      <span className="text-[11px] font-medium text-slate-600 capitalize">
                        {item.status}
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 rounded-full ${
                        item.status === 'failed'
                          ? 'bg-rose-500'
                          : item.status === 'completed'
                          ? 'bg-emerald-500'
                          : 'bg-emerald-600'
                      }`}
                      style={{ width: `${item.progress}%` }}
                    />
                  </div>

                  <p className="text-[10px] text-slate-500 truncate">
                    {item.message}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium text-slate-700 hover:text-slate-900 transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

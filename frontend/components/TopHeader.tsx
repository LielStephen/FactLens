'use client';

import React from 'react';
import { Search, Upload, CheckCircle2 } from 'lucide-react';

interface TopHeaderProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  selectedDataset: string;
  onSelectDataset: (ds: string) => void;
  onOpenUpload: () => void;
  onSearchSubmit?: () => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  searchQuery,
  setSearchQuery,
  selectedDataset,
  onSelectDataset,
  onOpenUpload,
  onSearchSubmit
}) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && onSearchSubmit) {
      onSearchSubmit();
    }
  };

  const datasets = [
    { id: 'all', label: '🌐 All Datasets (10 Docs, 384 Facts)' },
    { id: 'delhivery', label: '📦 Delhivery Logistics (3 Docs, 133 Facts)' },
    { id: 'india-macroeconomy', label: '🇮🇳 India Macroeconomy (3 Docs, 230 Facts)' },
    { id: 'synthetic', label: '🧪 Synthetic Showcase (4 Docs, 21 Facts)' },
  ];

  return (
    <header className="h-14 border-b border-slate-200 bg-white px-6 flex items-center justify-between shrink-0 gap-4">
      {/* Global Search Bar */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search facts, entities, predicates (e.g. GDP, Delhivery, Revenue)..."
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-4 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500 transition-all"
          />
        </div>
      </div>

      {/* Dataset Filter Selector */}
      <div className="flex items-center gap-2">
        <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider hidden lg:inline">
          Dataset:
        </span>
        <select
          value={selectedDataset}
          onChange={(e) => onSelectDataset(e.target.value)}
          aria-label="Filter dataset"
          className="bg-slate-100 hover:bg-slate-200/70 border border-slate-200 text-slate-800 text-xs font-medium rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 cursor-pointer transition-colors"
        >
          {datasets.map((d) => (
            <option key={d.id} value={d.id}>
              {d.label}
            </option>
          ))}
        </select>
      </div>

      {/* Action Buttons & Status */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-[11px] font-medium">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          <span>Knowledge Layer Live</span>
        </div>

        <button
          onClick={onOpenUpload}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium shadow-sm transition-colors cursor-pointer"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>Upload PDFs</span>
        </button>
      </div>
    </header>
  );
};

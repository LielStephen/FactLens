'use client';

import React from 'react';
import { 
  LayoutDashboard, 
  FileText, 
  Database, 
  GitCompare, 
  AlertTriangle, 
  Layers, 
  Activity,
  Sparkles
} from 'lucide-react';

export type NavTab = 'overview' | 'documents' | 'facts' | 'relationships' | 'conflicts' | 'showcase' | 'diagnostics';

interface SidebarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  conflictCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  conflictCount = 0
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard, section: 'MAIN' },
    { id: 'documents', label: 'Documents', icon: FileText, section: 'KNOWLEDGE' },
    { id: 'facts', label: 'Facts', icon: Database, section: 'KNOWLEDGE' },
    { id: 'relationships', label: 'Relationships', icon: GitCompare, section: 'KNOWLEDGE' },
    { id: 'conflicts', label: 'Conflicts', icon: AlertTriangle, section: 'REVIEW', badge: conflictCount > 0 ? conflictCount : undefined },
    { id: 'showcase', label: 'Case Showcase', icon: Sparkles, section: 'EVALUATION' },
    { id: 'diagnostics', label: 'System & Quality', icon: Activity, section: 'SYSTEM' },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 text-slate-300 flex flex-col h-screen select-none shrink-0">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-slate-950 border border-slate-700/80 flex items-center justify-center p-1.5 shadow-sm">
            <svg viewBox="0 0 64 64" className="w-full h-full" fill="none">
              <line x1="12" y1="32" x2="20" y2="32" stroke="#334155" strokeWidth="2.5" strokeLinecap="round"/>
              <line x1="44" y1="32" x2="52" y2="32" stroke="#334155" strokeWidth="2.5" strokeLinecap="round"/>
              <line x1="32" y1="12" x2="32" y2="20" stroke="#334155" strokeWidth="2.5" strokeLinecap="round"/>
              <line x1="32" y1="44" x2="32" y2="52" stroke="#334155" strokeWidth="2.5" strokeLinecap="round"/>
              <path d="M 21 27 L 21 21 L 27 21" stroke="#6366f1" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M 43 27 L 43 21 L 37 21" stroke="#6366f1" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M 21 37 L 21 43 L 27 43" stroke="#06b6d4" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M 43 37 L 43 43 L 37 43" stroke="#06b6d4" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="32" cy="32" r="7" stroke="#38bdf8" strokeWidth="2.5" strokeDasharray="3 2"/>
              <circle cx="32" cy="32" r="3" fill="#38bdf8"/>
            </svg>
          </div>
          <div>
            <h1 className="font-semibold text-white tracking-tight text-base leading-none">FactLens</h1>
            <p className="text-[11px] text-slate-400 font-normal mt-1 leading-none">Evidence Knowledge Layer</p>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-6 overflow-y-auto">
        {['MAIN', 'KNOWLEDGE', 'REVIEW', 'EVALUATION', 'SYSTEM'].map((sectionName) => {
          const sectionItems = navItems.filter(item => item.section === sectionName);
          if (sectionItems.length === 0) return null;

          return (
            <div key={sectionName}>
              <div className="px-3 mb-2 text-[10px] font-semibold text-slate-400 tracking-wider uppercase">
                {sectionName}
              </div>
              <div className="space-y-1">
                {sectionItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id as NavTab)}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                        isActive
                          ? 'bg-slate-800 text-white shadow-sm border border-slate-700/60'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                        <span>{item.label}</span>
                      </div>
                      {item.badge !== undefined && (
                        <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-full">
                          {item.badge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Superjoin Engine v1.0</span>
        </div>
        <span className="text-[10px] text-slate-400 font-mono">Groq+PyMuPDF</span>
      </div>
    </aside>
  );
};

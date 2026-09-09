'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar, NavTab } from '@/components/Sidebar';
import { TopHeader } from '@/components/TopHeader';
import { OverviewView } from '@/components/OverviewView';
import { DocumentsView } from '@/components/DocumentsView';
import { FactsView } from '@/components/FactsView';
import { RelationshipsView } from '@/components/RelationshipsView';
import { ConflictsView } from '@/components/ConflictsView';
import { ShowcaseView } from '@/components/ShowcaseView';
import { DiagnosticsView } from '@/components/DiagnosticsView';
import { UploadModal } from '@/components/UploadModal';
import {
  fetchOverview,
  fetchDocuments,
  fetchFacts,
  fetchRelationships
} from '@/lib/api';
import { DashboardOverview, DocumentItem, Fact, FactRelationship } from '@/types';

export default function Home() {
  const [activeTab, setActiveTab] = useState<NavTab>('overview');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedDataset, setSelectedDataset] = useState<string>('all');
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);

  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [facts, setFacts] = useState<Fact[]>([]);
  const [relationships, setRelationships] = useState<FactRelationship[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [connectionError, setConnectionError] = useState<boolean>(false);
  const [retryCount, setRetryCount] = useState<number>(0);

  const loadAllData = useCallback(async () => {
    try {
      setLoading(true);
      const [overviewData, docsData, factsData, relsData] = await Promise.allSettled([
        fetchOverview(selectedDataset),
        fetchDocuments(selectedDataset),
        fetchFacts({ limit: 150, dataset: selectedDataset }),
        fetchRelationships({ limit: 150, dataset: selectedDataset })
      ]);

      const anyRejected = overviewData.status === 'rejected' || docsData.status === 'rejected';

      if (overviewData.status === 'fulfilled') setOverview(overviewData.value);
      if (docsData.status === 'fulfilled') setDocuments(docsData.value);
      if (factsData.status === 'fulfilled') setFacts(factsData.value.facts);
      if (relsData.status === 'fulfilled') setRelationships(relsData.value.relationships);

      if (anyRejected) {
        setConnectionError(true);
        // Auto-retry up to 4 times if backend is cold-starting
        setRetryCount(prev => {
          if (prev < 4) {
            setTimeout(() => {
              loadAllData();
            }, 4000);
            return prev + 1;
          }
          return prev;
        });
      } else {
        setConnectionError(false);
        setRetryCount(0);
      }
    } catch (e) {
      console.error('Error loading data:', e);
      setConnectionError(true);
    } finally {
      setLoading(false);
    }
  }, [selectedDataset]);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  const handleSearchSubmit = () => {
    if (searchQuery.trim()) {
      setActiveTab('facts');
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-100 font-sans">
      {/* Persistent Left Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        conflictCount={overview?.stats?.conflicts || 0}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Header */}
        <TopHeader
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          selectedDataset={selectedDataset}
          onSelectDataset={setSelectedDataset}
          onOpenUpload={() => setIsUploadOpen(true)}
          onSearchSubmit={handleSearchSubmit}
        />

        {/* Scrollable Viewport */}
        <main className="flex-1 overflow-y-auto p-8">
          {connectionError && (
            <div className="mb-6 max-w-6xl mx-auto p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-center justify-between text-xs shadow-xs">
              <div className="flex items-center gap-2.5">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500"></span>
                </span>
                <span>
                  <strong>Connecting to Cloud Knowledge Base:</strong> Backend instance is waking up (takes ~25s on cold start). Auto-reconnecting...
                </span>
              </div>
              <button
                onClick={() => loadAllData()}
                className="px-3 py-1 rounded-md bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs transition-colors cursor-pointer"
              >
                Reconnect Now
              </button>
            </div>
          )}

          {activeTab === 'overview' && (
            <OverviewView
              overview={overview}
              loading={loading}
              selectedDataset={selectedDataset}
              onSelectDataset={setSelectedDataset}
              setActiveTab={setActiveTab}
              onOpenUpload={() => setIsUploadOpen(true)}
            />
          )}

          {activeTab === 'documents' && (
            <DocumentsView
              documents={documents}
              loading={loading}
              onOpenUpload={() => setIsUploadOpen(true)}
            />
          )}

          {activeTab === 'facts' && (
            <FactsView
              facts={facts}
              loading={loading}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              onRefresh={loadAllData}
            />
          )}

          {activeTab === 'relationships' && (
            <RelationshipsView
              relationships={relationships}
              loading={loading}
              onRefresh={loadAllData}
            />
          )}

          {activeTab === 'conflicts' && (
            <ConflictsView selectedDataset={selectedDataset} />
          )}

          {activeTab === 'showcase' && (
            <ShowcaseView />
          )}

          {activeTab === 'diagnostics' && (
            <DiagnosticsView />
          )}
        </main>
      </div>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={loadAllData}
      />
    </div>
  );
}

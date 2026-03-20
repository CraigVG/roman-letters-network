'use client';

import dynamic from 'next/dynamic';
import { useState } from 'react';
import Link from 'next/link';

interface NetworkGraphLoaderProps {
  wymanMode?: boolean;
  onWymanModeChange?: (value: boolean) => void;
}

const NetworkGraph = dynamic(() => import('@/components/viz/NetworkGraph'), {
  ssr: false,
  loading: () => (
    <div
      className="flex-1 flex items-center justify-center text-lg rounded-xl"
      style={{
        color: 'var(--color-accent)',
        background: '#0f1520',
        minHeight: 500,
      }}
    >
      Loading network visualization...
    </div>
  ),
});

/* ------------------------------------------------------------------ */
/*  Types for selected node data                                       */
/* ------------------------------------------------------------------ */

export interface SelectedNode {
  id: number;
  name: string;
  slug: string;
  role: string | null;
  location: string | null;
  birth_year: number | null;
  death_year: number | null;
  bio: string | null;
  letters_sent: number;
  letters_received: number;
}

/* ------------------------------------------------------------------ */
/*  Role colors (shared with graph)                                    */
/* ------------------------------------------------------------------ */

const legendItems = [
  { label: 'Pope', color: '#c9a959' },
  { label: 'Bishop', color: '#5b8c5a' },
  { label: 'Senator', color: '#8b5cf6' },
  { label: 'Emperor', color: '#e74c3c' },
  { label: 'Priest / Scholar', color: '#3b82f6' },
  { label: 'Monk', color: '#a78bfa' },
  { label: 'Other', color: '#6b7b8d' },
];

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function NetworkGraphLoader({ wymanMode = false, onWymanModeChange }: NetworkGraphLoaderProps = {}) {
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);
  const [mobileDetailOpen, setMobileDetailOpen] = useState(false);

  const handleNodeClick = (node: SelectedNode) => {
    setSelectedNode(node);
    setMobileDetailOpen(true);
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6">
      {/* Graph area */}
      <div
        className="flex-1 rounded-xl overflow-hidden border border-theme"
        style={{ background: '#0f1520', minHeight: 500 }}
      >
        <div className="relative w-full" style={{ height: 'calc(max(500px, 70vh))' }}>
          <NetworkGraph onNodeClick={handleNodeClick} wymanMode={wymanMode} />
        </div>
      </div>

      {/* Sidebar - desktop: always visible, mobile: collapsible below graph */}
      <aside className="w-full lg:w-80 xl:w-96 shrink-0 flex flex-col gap-4">
        {/* Selected node detail */}
        <div className="rounded-xl border border-theme bg-theme-surface p-5">
          <h3
            className="text-sm font-semibold uppercase tracking-wide text-theme-muted mb-3"
            style={{ fontFamily: 'var(--font-sans)' }}
          >
            Selected Author
          </h3>

          {selectedNode ? (
            <div>
              <h4
                className="text-lg text-theme-text"
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                {selectedNode.name}
              </h4>
              <div className="mt-2 space-y-1 text-sm text-theme-muted">
                {selectedNode.role && (
                  <p className="capitalize">{selectedNode.role}</p>
                )}
                {selectedNode.location && <p>{selectedNode.location}</p>}
                <p>
                  {selectedNode.birth_year ?? '?'}&ndash;
                  {selectedNode.death_year ?? '?'} AD
                </p>
              </div>
              {selectedNode.bio && (
                <p
                  className="mt-3 text-sm text-theme-muted leading-relaxed line-clamp-4"
                  style={{ fontFamily: 'var(--font-serif)' }}
                >
                  {selectedNode.bio}
                </p>
              )}
              <div className="mt-4 flex items-center gap-4 text-sm">
                <span className="text-theme-accent font-medium tabular-nums">
                  {selectedNode.letters_sent} sent
                </span>
                <span className="text-theme-accent font-medium tabular-nums">
                  {selectedNode.letters_received} received
                </span>
              </div>
              <Link
                href={`/authors/${selectedNode.slug}`}
                className="mt-4 inline-flex items-center text-sm text-theme-accent hover:underline transition-colors"
              >
                View profile &rarr;
              </Link>
            </div>
          ) : (
            <p className="text-sm text-theme-muted italic">
              Click a node in the graph to see details about that author.
            </p>
          )}
        </div>

        {/* Wyman Mode toggle */}
        <div
          className="rounded-xl border border-theme bg-theme-surface p-5"
          style={{ background: wymanMode ? 'color-mix(in srgb, var(--color-accent) 8%, var(--color-surface))' : undefined }}
        >
          <h3
            className="text-sm font-semibold uppercase tracking-wide text-theme-muted mb-3"
            style={{ fontFamily: 'var(--font-sans)' }}
          >
            Dataset Filter
          </h3>
          <label className="flex items-center gap-3 cursor-pointer">
            <button
              role="switch"
              aria-checked={wymanMode}
              onClick={() => onWymanModeChange?.(!wymanMode)}
              className="relative shrink-0 w-10 h-5 rounded-full transition-colors focus:outline-none focus-visible:ring-2"
              style={{ background: wymanMode ? 'var(--color-accent)' : 'var(--color-border)' }}
            >
              <span
                className="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform"
                style={{ transform: wymanMode ? 'translateX(20px)' : 'translateX(0)' }}
              />
            </button>
            <span className="text-sm font-medium text-theme-text">Wyman Mode</span>
            <span className="relative group ml-auto">
              <span
                className="w-4 h-4 rounded-full text-xs flex items-center justify-center cursor-help"
                style={{ background: 'var(--color-border)', color: 'var(--color-muted)' }}
              >?</span>
              <span
                className="absolute right-0 bottom-full mb-1 w-56 text-xs rounded-md px-3 py-2 shadow-lg pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity z-50"
                style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-muted)' }}
              >
                Filters to Patrick Wyman&apos;s dissertation parameters: Latin West collections only, 450&ndash;650 AD.
              </span>
            </span>
          </label>
          {wymanMode && (
            <p className="mt-1.5 text-xs" style={{ color: 'var(--color-accent)', opacity: 0.85 }}>
              Latin West 450&ndash;650 AD active
            </p>
          )}
        </div>

        {/* Legend */}
        <div className="rounded-xl border border-theme bg-theme-surface p-5">
          <h3
            className="text-sm font-semibold uppercase tracking-wide text-theme-muted mb-3"
            style={{ fontFamily: 'var(--font-sans)' }}
          >
            Legend
          </h3>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
            {legendItems.map((item) => (
              <div key={item.label} className="flex items-center gap-2 text-sm text-theme-text">
                <span
                  className="inline-block w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ background: item.color }}
                />
                {item.label}
              </div>
            ))}
          </div>
          <div className="mt-3 pt-3 border-t border-theme text-xs text-theme-muted space-y-1">
            <p>Line thickness = letter volume between two people</p>
            <p>Node size = total correspondence</p>
          </div>
        </div>

        {/* Tips */}
        <div className="rounded-xl border border-theme bg-theme-surface p-5">
          <h3
            className="text-sm font-semibold uppercase tracking-wide text-theme-muted mb-3"
            style={{ fontFamily: 'var(--font-sans)' }}
          >
            Controls
          </h3>
          <ul className="text-sm text-theme-muted space-y-1.5">
            <li>Scroll to zoom in/out</li>
            <li>Click and drag to pan</li>
            <li>Drag a node to reposition it</li>
            <li>Click a node for details</li>
            <li>Use the filter to view a single collection</li>
          </ul>
        </div>
      </aside>

      {/* Mobile bottom sheet for selected node */}
      {selectedNode && mobileDetailOpen && (
        <div className="fixed inset-x-0 bottom-0 z-40 lg:hidden">
          <div className="bg-theme-surface border-t border-theme rounded-t-2xl p-5 shadow-xl max-h-[50vh] overflow-y-auto">
            <div className="flex items-start justify-between mb-3">
              <h4
                className="text-lg text-theme-text"
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                {selectedNode.name}
              </h4>
              <button
                onClick={() => setMobileDetailOpen(false)}
                className="w-8 h-8 rounded-lg bg-theme-bg border border-theme flex items-center justify-center text-theme-muted hover:text-theme-text transition-colors"
                aria-label="Close details"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-4 h-4"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="space-y-1 text-sm text-theme-muted">
              {selectedNode.role && (
                <p className="capitalize">{selectedNode.role}</p>
              )}
              {selectedNode.location && <p>{selectedNode.location}</p>}
              <p>
                {selectedNode.birth_year ?? '?'}&ndash;
                {selectedNode.death_year ?? '?'} AD
              </p>
            </div>
            {selectedNode.bio && (
              <p
                className="mt-3 text-sm text-theme-muted leading-relaxed line-clamp-3"
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                {selectedNode.bio}
              </p>
            )}
            <div className="mt-3 flex items-center gap-4 text-sm">
              <span className="text-theme-accent font-medium tabular-nums">
                {selectedNode.letters_sent} sent
              </span>
              <span className="text-theme-accent font-medium tabular-nums">
                {selectedNode.letters_received} received
              </span>
            </div>
            <Link
              href={`/authors/${selectedNode.slug}`}
              className="mt-3 inline-flex items-center text-sm text-theme-accent hover:underline"
            >
              View profile &rarr;
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

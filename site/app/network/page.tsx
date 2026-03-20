'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import type { SelectedNode } from '@/components/viz/NetworkGraphLoader';

const NetworkGraphV2 = dynamic(() => import('@/components/viz/NetworkGraphV2'), {
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
/*  Region legend                                                      */
/* ------------------------------------------------------------------ */

const regionLegend = [
  { label: 'Italy', color: '#c9a959' },
  { label: 'Gaul & Britain', color: '#5b8c5a' },
  { label: 'Iberia', color: '#e67e22' },
  { label: 'North Africa', color: '#e74c3c' },
  { label: 'Eastern Mediterranean', color: '#3b82f6' },
  { label: 'Unknown', color: '#6b7b8d' },
];

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function NetworkPage() {
  const [wymanMode, setWymanMode] = useState(false);
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);

  return (
    <div className="max-w-[90rem] mx-auto px-4 sm:px-6 pb-12">
      <Breadcrumbs segments={[{ label: 'Network' }]} />

      <section className="pt-2 pb-6">
        <h1
          className="text-3xl sm:text-4xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Communication Network
        </h1>
        <p className="mt-3 text-theme-muted max-w-2xl leading-relaxed">
          Interactive force-directed graph clustered by geographic region. Shows
          the top correspondents by default &mdash; use the density slider to
          reveal more. Click any node to highlight its connections.
        </p>
      </section>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Graph area */}
        <div
          className="flex-1 rounded-xl overflow-hidden border border-theme"
          style={{ background: '#0f1520', minHeight: 500 }}
        >
          <div className="relative w-full" style={{ height: 'calc(max(500px, 70vh))' }}>
            <NetworkGraphV2 onNodeClick={setSelectedNode} wymanMode={wymanMode} />
          </div>
        </div>

        {/* Sidebar */}
        <aside className="w-full lg:w-80 xl:w-96 shrink-0 flex flex-col gap-4">
          {/* Selected node */}
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

          {/* Wyman Mode */}
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
                onClick={() => setWymanMode(!wymanMode)}
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

          {/* Legend - regions */}
          <div className="rounded-xl border border-theme bg-theme-surface p-5">
            <h3
              className="text-sm font-semibold uppercase tracking-wide text-theme-muted mb-3"
              style={{ fontFamily: 'var(--font-sans)' }}
            >
              Regions
            </h3>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
              {regionLegend.map((item) => (
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
              <p>Node size = total correspondence</p>
              <p>Line thickness = letters exchanged</p>
              <p>Colors = geographic region</p>
            </div>
          </div>

          {/* Controls */}
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
              <li>Click a node to highlight connections</li>
              <li>Click background to deselect</li>
              <li>Adjust density slider to show more/fewer people</li>
              <li>Use &ldquo;Min letters&rdquo; to filter weak connections</li>
            </ul>
          </div>
        </aside>
      </div>
    </div>
  );
}

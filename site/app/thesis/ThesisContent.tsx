'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { RegionalizationChart } from '@/components/viz/RegionalizationChart';

interface Summary {
  total_letters_with_distance: number;
  peak_decade: number;
  peak_avg_distance: number;
  trough_decade: number;
  trough_avg_distance: number;
  pct_decline: number;
}

export function ThesisContent() {
  const [wymanMode, setWymanMode] = useState(true);
  const [summary, setSummary] = useState<Summary | null>(null);

  useEffect(() => {
    fetch('/data/regionalization.json')
      .then((r) => r.json())
      .then((d) => setSummary(d.summary))
      .catch(console.error);
  }, []);

  return (
    <>
      {/* Chart section */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 pb-12">
        {/* Wyman mode toggle */}
        <div className="flex items-center justify-between mb-6">
          <h2
            className="text-xl sm:text-2xl tracking-tight"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Communication radius over time
          </h2>
          <button
            onClick={() => setWymanMode(!wymanMode)}
            className={`
              inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium
              border transition-all duration-200
              ${
                wymanMode
                  ? 'bg-[var(--color-secondary)] text-white border-[var(--color-secondary)]'
                  : 'bg-theme-surface border-theme text-theme-muted hover:text-theme-text hover:border-[var(--color-accent)]'
              }
            `}
          >
            <span
              className={`inline-block w-2 h-2 rounded-full transition-colors ${
                wymanMode ? 'bg-white' : 'bg-[var(--color-secondary)]'
              }`}
            />
            Wyman Mode
            <span className="hidden sm:inline text-[10px] opacity-70">
              (Latin West, 450-650)
            </span>
          </button>
        </div>

        {/* Chart */}
        <div className="rounded-lg border border-theme bg-theme-surface p-4 sm:p-6">
          <RegionalizationChart wymanMode={wymanMode} />
          <p className="mt-4 text-xs text-theme-muted text-center">
            {wymanMode
              ? 'Latin West collections only (450-650 AD), matching Wyman\'s corpus. Same-city letters excluded. Trend: 50-year weighted moving average.'
              : 'All collections, excluding same-city letters (distance = 0). Decades with fewer than 10 letters excluded. Trend: 50-year weighted moving average; dots show raw decade averages.'}
          </p>
        </div>
      </section>

      {/* Stats cards */}
      {summary && (
        <section className="max-w-4xl mx-auto px-4 sm:px-6 pb-12">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-lg border border-theme bg-theme-surface p-5">
              <div className="text-xs text-theme-muted uppercase tracking-wider mb-2">
                Peak average distance
              </div>
              <div
                className="text-3xl font-light text-theme-accent"
                style={{
                  fontFamily: 'var(--font-serif)',
                  fontVariantNumeric: 'oldstyle-nums',
                }}
              >
                {summary.peak_avg_distance.toLocaleString()} km
              </div>
              <div className="text-sm text-theme-muted mt-1">
                {summary.peak_decade}s AD
              </div>
            </div>

            <div className="rounded-lg border border-theme bg-theme-surface p-5">
              <div className="text-xs text-theme-muted uppercase tracking-wider mb-2">
                Lowest average distance
              </div>
              <div
                className="text-3xl font-light text-theme-accent"
                style={{
                  fontFamily: 'var(--font-serif)',
                  fontVariantNumeric: 'oldstyle-nums',
                }}
              >
                {summary.trough_avg_distance.toLocaleString()} km
              </div>
              <div className="text-sm text-theme-muted mt-1">
                {summary.trough_decade}s AD
              </div>
            </div>

            <div className="rounded-lg border border-theme bg-theme-surface p-5">
              <div className="text-xs text-theme-muted uppercase tracking-wider mb-2">
                Decline in reach
              </div>
              <div
                className="text-3xl font-light text-theme-accent"
                style={{
                  fontFamily: 'var(--font-serif)',
                  fontVariantNumeric: 'oldstyle-nums',
                }}
              >
                {summary.pct_decline}%
              </div>
              <div className="text-sm text-theme-muted mt-1">
                From {summary.peak_decade}s to {summary.trough_decade}s
              </div>
            </div>
          </div>

          <p className="mt-4 text-sm text-theme-muted leading-relaxed">
            Based on {summary.total_letters_with_distance.toLocaleString()}{' '}
            letters with computable sender-to-recipient distances. The{' '}
            {summary.pct_decline}% decline from the {summary.peak_decade}s to
            the {summary.trough_decade}s captures the contraction of the Roman
            communication network as political fragmentation disrupted
            long-distance travel.
          </p>
        </section>
      )}

      {/* CTA to map */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 pb-12">
        <div className="rounded-lg border border-theme bg-theme-surface p-6 sm:p-8 text-center">
          <h3
            className="text-xl sm:text-2xl tracking-tight mb-3"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            See it on the map
          </h3>
          <p className="text-theme-muted text-sm mb-5 max-w-lg mx-auto">
            Watch these letters move across the Mediterranean in real time.
            The animated map timelapse shows individual arcs between senders
            and recipients, decade by decade.
          </p>
          <Link
            href="/map"
            className="inline-flex items-center px-5 py-2.5 rounded-lg text-sm font-medium
              text-white transition-colors hover:opacity-90"
            style={{ backgroundColor: 'var(--color-accent)' }}
          >
            Open map timelapse
          </Link>
        </div>
      </section>
    </>
  );
}

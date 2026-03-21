'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import Link from 'next/link';
import { scaleLinear } from 'd3-scale';
import { max as d3Max } from 'd3-array';
import { select } from 'd3-selection';
import RomanMapLoader from '@/components/viz/RomanMapLoader';
import RoadHeatmap from '@/components/viz/RoadHeatmap';
import { YEAR_MIN, YEAR_MAX, YEAR_START } from '@/components/viz/map-types';
import type { HistoricalEvent, HubCity, MapStats, TimelineRow } from '@/components/viz/map-types';

// ── Legend data ───────────────────────────────────────────────────────
const ROLE_LEGEND = [
  { color: '#c9a959', label: 'Pope / Church Leader' },
  { color: '#5b8c5a', label: 'Bishop' },
  { color: '#8b5cf6', label: 'Senator / Aristocrat' },
  { color: '#e74c3c', label: 'Emperor / Official' },
  { color: '#3b82f6', label: 'Scholar / Priest' },
  { color: '#6b7b8d', label: 'Other' },
];

const CENTURY_LEGEND = [
  { color: '#7ec8e3', label: '1st-2nd c.' },
  { color: '#a8d8a8', label: '3rd c.' },
  { color: '#e8c05a', label: '4th c.' },
  { color: '#e07a3a', label: '5th c.' },
  { color: '#c0392b', label: '6th c.' },
  { color: '#a050c0', label: '7th+ c.' },
];

// ── Page component ───────────────────────────────────────────────────
export default function MapV2Page() {
  const [currentYear, setCurrentYear] = useState(YEAR_START);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [windowSize] = useState(10);
  const [filterCollection, setFilterCollection] = useState('');
  const [wymanMode, setWymanMode] = useState(false);
  const [arcOpacity, setArcOpacity] = useState(0.5);
  const [showTrail, setShowTrail] = useState(true);
  const [showDots, setShowDots] = useState(true);
  const [showEvents, setShowEvents] = useState(true);
  const [collections, setCollections] = useState<string[]>([]);
  const [stats, setStats] = useState<MapStats>({ visible: 0, total: 0, people: 0 });
  const [events, setEvents] = useState<HistoricalEvent[]>([]);
  const [timeline, setTimeline] = useState<TimelineRow[]>([]);
  const [, setMapLoading] = useState(true);
  const [selectedHub, setSelectedHub] = useState<HubCity | null>(null);

  const histogramRef = useRef<HTMLDivElement>(null);

  const handleStatsChange = useCallback((s: MapStats) => setStats(s), []);
  const handleCollections = useCallback((c: string[]) => setCollections(c), []);
  const handleEvents = useCallback((e: HistoricalEvent[]) => setEvents(e), []);
  const handleTimeline = useCallback((t: TimelineRow[]) => setTimeline(t), []);
  const handleLoading = useCallback((l: boolean) => setMapLoading(l), []);
  const handleHubCityClick = useCallback((city: HubCity) => setSelectedHub(city), []);

  const nearestEventIdx = events.length > 0
    ? events.reduce((bestIdx, ev, idx) => {
        const bestDist = Math.abs(events[bestIdx].year - currentYear);
        const thisDist = Math.abs(ev.year - currentYear);
        return thisDist < bestDist ? idx : bestIdx;
      }, 0)
    : -1;

  const jumpToYear = useCallback((year: number) => {
    setIsPlaying(false);
    setCurrentYear(Math.min(YEAR_MAX, Math.max(YEAR_MIN, year)));
  }, []);

  const handlePlayPause = useCallback(() => {
    if (isPlaying) {
      setIsPlaying(false);
    } else {
      if (currentYear >= YEAR_MAX) {
        setCurrentYear(YEAR_START);
      }
      setIsPlaying(true);
    }
  }, [isPlaying, currentYear]);

  const handleReset = useCallback(() => {
    setIsPlaying(false);
    setCurrentYear(YEAR_START);
  }, []);

  // ── Build histogram ────────────────────────────────────────────────
  useEffect(() => {
    const container = histogramRef.current;
    if (!container || timeline.length === 0) return;

    const W = container.clientWidth;
    const H = 100;

    select(container).select('svg').remove();

    const byDecade = new Map<number, number>();
    for (const d of timeline) {
      byDecade.set(d.decade, (byDecade.get(d.decade) || 0) + d.count);
    }

    const decades = Array.from(byDecade.entries())
      .filter(([yr]) => yr >= YEAR_MIN && yr <= YEAR_MAX)
      .sort((a, b) => a[0] - b[0]);

    if (!decades.length) return;

    const x = scaleLinear().domain([YEAR_MIN, YEAR_MAX]).range([0, W]);
    const maxCount = d3Max(decades, (d) => d[1]) || 1;
    const y = scaleLinear().domain([0, maxCount]).range([H - 4, 4]);

    const chartSvg = select(container)
      .append('svg')
      .attr('width', W)
      .attr('height', H)
      .style('display', 'block');

    const barW = Math.max(2, x(10) - x(0) - 1);

    chartSvg
      .selectAll('.hist-bar')
      .data(decades)
      .join('rect')
      .attr('class', 'hist-bar')
      .attr('x', (d) => x(d[0]))
      .attr('y', (d) => y(d[1]))
      .attr('width', barW)
      .attr('height', (d) => H - 4 - y(d[1]))
      .attr('rx', 1)
      .attr('fill', (d) => (Math.abs(d[0] - currentYear) <= windowSize ? 'var(--color-accent)' : 'var(--color-border)'))
      .attr('opacity', (d) => (Math.abs(d[0] - currentYear) <= windowSize ? 0.9 : 0.5));

    chartSvg
      .append('line')
      .attr('x1', x(currentYear))
      .attr('x2', x(currentYear))
      .attr('y1', 0)
      .attr('y2', H)
      .attr('stroke', 'var(--color-accent)')
      .attr('stroke-width', 2)
      .attr('opacity', 0.8);

    events
      .filter((ev) => ev.year >= YEAR_MIN && ev.year <= YEAR_MAX)
      .forEach((ev) => {
        chartSvg
          .append('line')
          .attr('x1', x(ev.year))
          .attr('x2', x(ev.year))
          .attr('y1', 0)
          .attr('y2', H)
          .attr('stroke', '#c0392b')
          .attr('stroke-width', 1)
          .attr('opacity', 0.4);
      });

    const labelYears = [100, 200, 300, 400, 500, 600, 700];
    labelYears.forEach((yr) => {
      chartSvg
        .append('text')
        .attr('x', x(yr))
        .attr('y', H - 1)
        .attr('text-anchor', 'middle')
        .attr('fill', 'var(--color-muted)')
        .attr('font-size', '9px')
        .attr('font-family', 'var(--font-sans)')
        .text(yr);
    });
  }, [timeline, events, currentYear, windowSize]);

  const activeEventRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    activeEventRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [nearestEventIdx]);

  return (
    <div>
      {/* Breadcrumbs + header */}
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6">
        <nav aria-label="Breadcrumb" className="py-3">
          <ol className="flex items-center gap-1.5 text-sm text-theme-muted">
            <li>
              <Link href="/" className="hover:text-theme-text transition-colors">Home</Link>
            </li>
            <li className="flex items-center gap-1.5">
              <span className="text-theme-muted/50" aria-hidden="true">&rsaquo;</span>
              <span className="text-theme-text">Map</span>
            </li>
          </ol>
        </nav>

        <header className="pt-2 pb-4">
          <div className="flex items-center gap-3 mb-2">
            <p className="text-xs font-medium tracking-[0.2em] uppercase text-theme-accent">
              Geographic Timelapse
            </p>
          </div>
          <h1
            className="text-2xl sm:text-3xl tracking-tight"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            The Roman World in Letters
          </h1>
          <p className="mt-2 text-theme-muted max-w-2xl leading-relaxed text-sm">
            DARE historical map with Roman road network overlay. Letters flow along ancient roads, 250&ndash;750 AD.
          </p>
        </header>
      </div>

      {/* ── Historical events - horizontal scrolling strip ───────── */}
      {events.length > 0 && (
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 mb-4">
          <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-thin" style={{ scrollbarWidth: 'thin' }}>
            <span className="text-xs text-theme-muted font-medium uppercase tracking-wide whitespace-nowrap shrink-0">Events:</span>
            {events.map((ev, idx) => {
              const isActive = idx === nearestEventIdx;
              const isPast = ev.year <= currentYear;
              return (
                <button
                  key={`${ev.year}-${idx}`}
                  ref={isActive ? activeEventRef : undefined}
                  onClick={() => jumpToYear(ev.year)}
                  className={`shrink-0 px-3 py-1.5 rounded-full text-xs transition-all whitespace-nowrap ${
                    isActive
                      ? 'border border-[var(--color-accent)] text-theme-accent font-semibold'
                      : isPast
                        ? 'border border-theme text-theme-muted hover:text-theme-text hover:border-[var(--color-accent)]'
                        : 'border border-transparent text-theme-muted/50 hover:text-theme-muted hover:border-theme'
                  }`}
                  style={isActive ? { background: 'color-mix(in srgb, var(--color-accent) 10%, transparent)' } : undefined}
                >
                  <span className="font-semibold tabular-nums" style={{ fontFamily: 'var(--font-serif)' }}>{ev.year}</span>
                  {' '}
                  {ev.short}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Main content: map + controls */}
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6">
        <div className="flex flex-col lg:flex-row gap-4">

          {/* ── Map column ──────────────────────────────────────── */}
          <div className="flex-1 min-w-0">
            <div
              className="relative rounded-lg overflow-hidden border border-theme"
              style={{ minHeight: 'max(500px, 60vh)' }}
            >
              <RomanMapLoader
                currentYear={currentYear}
                onYearChange={setCurrentYear}
                isPlaying={isPlaying}
                onPlayingChange={setIsPlaying}
                speed={speed}
                windowSize={windowSize}
                filterCollection={filterCollection}
                arcOpacity={arcOpacity}
                showTrail={showTrail}
                showDots={showDots}
                showEvents={showEvents}
                wymanMode={wymanMode}
                onStatsChange={handleStatsChange}
                onCollectionsLoaded={handleCollections}
                onEventsLoaded={handleEvents}
                onTimelineLoaded={handleTimeline}
                onLoadingChange={handleLoading}
                onHubCityClick={handleHubCityClick}
              />
            </div>

            {/* Year slider + playback controls */}
            <div className="mt-3 flex items-center gap-3">
              <button
                onClick={handlePlayPause}
                className="shrink-0 inline-flex items-center px-4 py-1.5 rounded-lg text-sm font-medium text-white transition-colors hover:opacity-90"
                style={{ backgroundColor: 'var(--color-accent)' }}
              >
                {isPlaying ? '\u23F8' : '\u25B6'}
              </button>
              <span className="text-xs text-theme-muted font-medium tabular-nums whitespace-nowrap shrink-0">
                100
              </span>
              <input
                type="range"
                min={YEAR_MIN}
                max={YEAR_MAX}
                value={currentYear}
                step={1}
                onChange={(e) => {
                  setIsPlaying(false);
                  setCurrentYear(parseInt(e.target.value));
                }}
                className="flex-1 h-1.5 rounded-sm cursor-pointer"
                style={{
                  accentColor: 'var(--color-accent)',
                  background: 'var(--color-border)',
                }}
              />
              <span className="text-xs text-theme-muted font-medium tabular-nums whitespace-nowrap shrink-0">
                750
              </span>
              <div
                className="shrink-0 text-2xl font-light text-theme-accent tabular-nums"
                style={{ fontFamily: 'var(--font-serif)', fontVariantNumeric: 'oldstyle-nums', minWidth: 80, textAlign: 'right' }}
              >
                {currentYear} <span className="text-sm text-theme-muted">AD</span>
              </div>
            </div>

            <div className="mt-1.5 flex items-center gap-4 text-xs text-theme-muted">
              <span className="hidden lg:inline">Space = play/pause &middot; Arrows = &plusmn;5 yr &middot; R = reset</span>
              <span className="ml-auto tabular-nums">{stats.visible.toLocaleString()} letters visible of {stats.total.toLocaleString()}</span>
            </div>
          </div>

          {/* ── Sidebar - compact controls only ─────────────────── */}
          <aside className="lg:w-[280px] shrink-0 flex flex-col gap-4 lg:sticky lg:top-4 lg:self-start lg:max-h-[calc(100vh-2rem)] lg:overflow-y-auto">

            {/* Controls */}
            <div className="p-4 rounded-lg border border-theme bg-theme-surface">
              <div className="flex items-center gap-3 mb-3">
                <label className="text-xs text-theme-muted uppercase tracking-wide">Speed</label>
                <select
                  value={speed}
                  onChange={(e) => setSpeed(parseFloat(e.target.value))}
                  className="rounded-md border border-theme bg-theme-surface text-theme-text text-xs px-2 py-1 cursor-pointer"
                >
                  <option value={0.5}>0.5x</option>
                  <option value={1}>1x</option>
                  <option value={2}>2x</option>
                  <option value={5}>5x</option>
                </select>
                <button
                  onClick={handleReset}
                  className="ml-auto text-xs text-theme-muted hover:text-theme-accent transition-colors"
                >
                  &#8634; Reset
                </button>
              </div>

              {/* Wyman Mode */}
              <div
                className="mb-3 p-2.5 rounded-md border border-theme"
                style={{ background: wymanMode ? 'color-mix(in srgb, var(--color-accent) 8%, transparent)' : undefined }}
              >
                <label className="flex items-center gap-2.5 cursor-pointer">
                  <button
                    role="switch"
                    aria-checked={wymanMode}
                    onClick={() => setWymanMode((v) => !v)}
                    className="relative shrink-0 w-9 h-[18px] rounded-full transition-colors focus:outline-none focus-visible:ring-2"
                    style={{ background: wymanMode ? 'var(--color-accent)' : 'var(--color-border)' }}
                  >
                    <span
                      className="absolute top-[2px] left-[2px] w-[14px] h-[14px] rounded-full bg-white shadow transition-transform"
                      style={{ transform: wymanMode ? 'translateX(18px)' : 'translateX(0)' }}
                    />
                  </button>
                  <span className="text-xs font-medium text-theme-text">Wyman Mode</span>
                  <span className="relative group ml-auto">
                    <span
                      className="w-3.5 h-3.5 rounded-full text-[9px] flex items-center justify-center cursor-help"
                      style={{ background: 'var(--color-border)', color: 'var(--color-muted)' }}
                    >?</span>
                    <span
                      className="absolute right-0 bottom-full mb-1 w-48 text-[10px] rounded-md px-2.5 py-1.5 shadow-lg pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity z-50"
                      style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-muted)' }}
                    >
                      Latin West only, 450&ndash;650 AD (Wyman&apos;s dissertation scope)
                    </span>
                  </span>
                </label>
              </div>

              {/* Collection */}
              <div className="mb-3">
                <select
                  value={filterCollection}
                  onChange={(e) => setFilterCollection(e.target.value)}
                  className="w-full rounded-md border border-theme bg-theme-surface text-theme-text text-xs px-2 py-1.5 cursor-pointer"
                >
                  <option value="">All collections</option>
                  {collections.map((c) => (
                    <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>
                  ))}
                </select>
              </div>

              {/* Opacity */}
              <div className="mb-3">
                <label className="flex items-center gap-2">
                  <span className="text-xs text-theme-muted">Opacity</span>
                  <input
                    type="range"
                    min={10}
                    max={100}
                    value={arcOpacity * 100}
                    onChange={(e) => setArcOpacity(parseInt(e.target.value) / 100)}
                    className="flex-1 h-1 rounded-sm cursor-pointer"
                    style={{ accentColor: 'var(--color-accent)' }}
                  />
                  <span className="text-[10px] text-theme-muted tabular-nums w-6 text-right">
                    {Math.round(arcOpacity * 100)}%
                  </span>
                </label>
              </div>

              {/* Toggles */}
              <div className="flex flex-wrap gap-x-4 gap-y-1.5">
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input type="checkbox" checked={showTrail} onChange={(e) => setShowTrail(e.target.checked)} className="rounded border-theme" style={{ accentColor: 'var(--color-accent)', width: 14, height: 14 }} />
                  <span className="text-xs text-theme-text">Trail</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input type="checkbox" checked={showDots} onChange={(e) => setShowDots(e.target.checked)} className="rounded border-theme" style={{ accentColor: 'var(--color-accent)', width: 14, height: 14 }} />
                  <span className="text-xs text-theme-text">People</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input type="checkbox" checked={showEvents} onChange={(e) => setShowEvents(e.target.checked)} className="rounded border-theme" style={{ accentColor: 'var(--color-accent)', width: 14, height: 14 }} />
                  <span className="text-xs text-theme-text">Events</span>
                </label>
              </div>
            </div>

            {/* Hub City Profile - shown when a hub is clicked */}
            {selectedHub && (
              <div className="p-4 rounded-lg border border-theme bg-theme-surface">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="text-base text-theme-accent" style={{ fontFamily: 'var(--font-serif)' }}>
                    {selectedHub.name}
                  </h4>
                  <button onClick={() => setSelectedHub(null)} className="text-theme-muted hover:text-theme-text text-xs" aria-label="Close">&times;</button>
                </div>
                <div className="grid grid-cols-2 gap-2 mb-2">
                  <div>
                    <div className="text-lg font-light text-theme-accent tabular-nums" style={{ fontFamily: 'var(--font-serif)' }}>{selectedHub.total_sent.toLocaleString()}</div>
                    <div className="text-[10px] text-theme-muted">Sent</div>
                  </div>
                  <div>
                    <div className="text-lg font-light text-theme-accent tabular-nums" style={{ fontFamily: 'var(--font-serif)' }}>{selectedHub.total_received.toLocaleString()}</div>
                    <div className="text-[10px] text-theme-muted">Received</div>
                  </div>
                </div>
                {selectedHub.top_correspondents.length > 0 && (
                  <div className="space-y-0.5">
                    {selectedHub.top_correspondents.slice(0, 4).map((tc) => (
                      <div key={tc.city} className="flex items-center gap-1.5 text-[10px]">
                        <div className="h-0.5 rounded-sm" style={{ width: `${Math.round((tc.count / selectedHub.top_correspondents[0].count) * 60)}px`, minWidth: 3, background: 'var(--color-accent)', opacity: 0.7 }} />
                        <span className="text-theme-text">{tc.city}</span>
                        <span className="text-theme-muted ml-auto tabular-nums">{tc.count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Legend - compact */}
            <div className="p-4 rounded-lg border border-theme bg-theme-surface">
              <div className="grid grid-cols-2 gap-x-3 gap-y-1">
                {ROLE_LEGEND.map((item) => (
                  <div key={item.label} className="flex items-center gap-1.5 text-[10px] text-theme-text">
                    <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: item.color }} />
                    {item.label}
                  </div>
                ))}
              </div>
              <div className="border-t border-theme mt-2 pt-2 grid grid-cols-2 gap-x-3 gap-y-1">
                {CENTURY_LEGEND.map((item) => (
                  <div key={item.label} className="flex items-center gap-1.5 text-[10px] text-theme-text">
                    <div className="w-3 h-0.5 rounded-sm shrink-0" style={{ background: item.color }} />
                    {item.label}
                  </div>
                ))}
              </div>
            </div>

          </aside>
        </div>
      </div>

      {/* ── Timeline histogram ──────────────────────────────────────── */}
      <section className="max-w-[1400px] mx-auto px-4 sm:px-6 mt-8 mb-12">
        <div className="border-t border-theme pt-6">
          <h2
            className="text-lg tracking-tight mb-1"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Letter Volume by Decade
          </h2>
          <p className="text-xs text-theme-muted mb-4 max-w-xl">
            Each bar = one decade. Vertical line = current year.
          </p>
          <div
            ref={histogramRef}
            className="w-full rounded-lg overflow-hidden"
            style={{ height: 80 }}
          />
          <div className="flex justify-between mt-1 text-[10px] text-theme-muted">
            <span>100 AD</span>
            <span>200</span>
            <span>300</span>
            <span>400</span>
            <span>500</span>
            <span>600</span>
            <span>700 AD</span>
          </div>
        </div>
      </section>

      {/* ── Road traffic heatmap comparison ──────────────────────────── */}
      <RoadHeatmap />
    </div>
  );
}

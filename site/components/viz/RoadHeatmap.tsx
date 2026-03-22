'use client';

import { useRef, useEffect, useState, useCallback } from 'react';

// ── Types ─────────────────────────────────────────────────────────────
interface Era {
  label: string;
  start: number;
  end: number;
}

interface SegmentEraData {
  count: number;
  avgDist: number;
}

interface HeatmapData {
  eras: Era[];
  segments: Record<string, Record<string, SegmentEraData>>;
  maxTraffic: number;
  maxAvgDist: number;
  seaLanes: Record<string, Record<string, SegmentEraData>>;
  seaLaneCoords: Record<string, [number, number][]>;
  maxSeaTraffic: number;
  maxSeaAvgDist: number;
}

type GeoJSONFeatureCollection = {
  type: 'FeatureCollection';
  features: Array<{
    type: 'Feature';
    geometry: {
      type: 'MultiLineString' | 'LineString';
      coordinates: number[][][] | number[][];
    };
  }>;
};

type OutlineFeatureCollection = {
  type: 'FeatureCollection';
  features: Array<{
    type: 'Feature';
    properties: Record<string, unknown>;
    geometry: {
      type: 'Polygon' | 'MultiPolygon';
      coordinates: number[][][] | number[][][][];
    };
  }>;
};

interface MapLetter {
  id: number;
  year_approx: number;
  s_lat: number;
  s_lon: number;
  r_lat: number;
  r_lon: number;
  [key: string]: unknown;
}

// ── Era definitions ──────────────────────────────────────────────────
const ERA_OPTIONS = [
  { key: '300', label: '300s' },
  { key: '350', label: '350s' },
  { key: '400', label: '400s' },
  { key: '450', label: '450s' },
  { key: '500', label: '500s' },
];

// Sea lanes are now pre-computed in road-heatmap.json (seaLanes + seaLaneCoords)

// ── Projection constants ──────────────────────────────────────────────
const BBOX = { minLon: -12, maxLon: 48, minLat: 22, maxLat: 58 };

function projectMercator(
  lon: number,
  lat: number,
  width: number,
  height: number,
): [number, number] {
  const x = ((lon - BBOX.minLon) / (BBOX.maxLon - BBOX.minLon)) * width;
  const latRad = (lat * Math.PI) / 180;
  const minLatRad = (BBOX.minLat * Math.PI) / 180;
  const maxLatRad = (BBOX.maxLat * Math.PI) / 180;
  const yMerc = Math.log(Math.tan(Math.PI / 4 + latRad / 2));
  const yMin = Math.log(Math.tan(Math.PI / 4 + minLatRad / 2));
  const yMax = Math.log(Math.tan(Math.PI / 4 + maxLatRad / 2));
  const y = height - ((yMerc - yMin) / (yMax - yMin)) * height;
  return [x, y];
}

// ── Color mode type ──────────────────────────────────────────────────
type ColorMode = 'volume' | 'distance';

// ── Color interpolation ──────────────────────────────────────────────
function trafficColor(count: number, maxTraffic: number): string {
  if (count <= 0) return 'rgba(80,80,80,0.15)';
  const t = Math.min(count / maxTraffic, 1);

  // Three-stop gradient: blue(0) -> orange(0.3) -> red/gold(1)
  let r: number, g: number, b: number;
  if (t < 0.15) {
    // Low: cool teal-blue
    const s = t / 0.15;
    r = 40 + s * 60;
    g = 160 + s * 40;
    b = 200 - s * 40;
  } else if (t < 0.4) {
    // Medium: warm orange
    const s = (t - 0.15) / 0.25;
    r = 100 + s * 155;
    g = 200 - s * 80;
    b = 160 - s * 120;
  } else {
    // High: bright red-gold
    const s = (t - 0.4) / 0.6;
    r = 255;
    g = 120 - s * 50;
    b = 40 - s * 30;
  }
  const alpha = 0.5 + t * 0.5;
  return `rgba(${Math.round(r)},${Math.round(g)},${Math.round(b)},${alpha.toFixed(2)})`;
}

function trafficWidth(count: number, maxTraffic: number): number {
  if (count <= 0) return 0.3;
  const t = Math.min(count / maxTraffic, 1);
  return 0.5 + t * 3;
}

// ── Distance-based color ─────────────────────────────────────────────
function distanceColor(avgDist: number, _maxAvgDist: number): string {
  if (avgDist <= 0) return 'rgba(80,80,80,0.15)';
  // Tighter scale: /1500 instead of /2000 to maximize contrast in the 800-1800km range
  const t = Math.min(avgDist / 1500, 1);

  let r: number, g: number, b: number;
  if (t < 0.33) {
    // <500km: deep blue/teal
    const s = t / 0.33;
    r = 40 + s * 60;
    g = 140 + s * 60;
    b = 180 - s * 20;
  } else if (t < 0.67) {
    // 500-1000km: transition to warm orange
    const s = (t - 0.33) / 0.34;
    r = 100 + s * 155;
    g = 200 - s * 80;
    b = 160 - s * 130;
  } else {
    // 1000-1500km+: bright orange-red to gold/white
    const s = (t - 0.67) / 0.33;
    r = 255;
    g = 120 + s * 100; // goes toward gold/white
    b = 30 + s * 170;  // goes toward gold/white
  }
  const alpha = 0.5 + t * 0.5;
  return `rgba(${Math.round(r)},${Math.round(g)},${Math.round(b)},${alpha.toFixed(2)})`;
}

function distanceWidth(avgDist: number, maxAvgDist: number): number {
  if (avgDist <= 0) return 0.3;
  const t = Math.min(avgDist / maxAvgDist, 1);
  return 0.5 + t * 3;
}

// Sea traffic is now pre-computed in road-heatmap.json

// ── Drawing ──────────────────────────────────────────────────────────
function drawHeatmap(
  canvas: HTMLCanvasElement,
  roads: GeoJSONFeatureCollection,
  heatmap: HeatmapData,
  eraStartYear: string,
  colorMode: ColorMode = 'distance',
  outline: OutlineFeatureCollection | null = null,
  animProgress: number = 1,
) {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.scale(dpr, dpr);

  // Dark background
  ctx.fillStyle = '#0d1117';
  ctx.fillRect(0, 0, width, height);

  // Draw coastline fill — very subtle, just for geographic context
  if (outline) {
    ctx.fillStyle = 'rgba(0,0,0,0.04)';
    ctx.strokeStyle = 'rgba(0,0,0,0.1)';
    ctx.lineWidth = 0.5;

    for (const feature of outline.features) {
      const { type, coordinates } = feature.geometry;
      const rings: number[][][] =
        type === 'Polygon'
          ? (coordinates as number[][][])
          : type === 'MultiPolygon'
            ? (coordinates as number[][][][]).flat()
            : [];

      for (const ring of rings) {
        if (ring.length < 3) continue;
        ctx.beginPath();
        const [x0, y0] = projectMercator(ring[0][0], ring[0][1], width, height);
        ctx.moveTo(x0, y0);
        for (let i = 1; i < ring.length; i++) {
          const [x, y] = projectMercator(ring[i][0], ring[i][1], width, height);
          ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      }
    }
  }

  // Draw all road segments as thin gray background lines
  ctx.strokeStyle = 'rgba(80,80,80,0.15)';
  ctx.lineWidth = 0.3;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  for (let i = 0; i < roads.features.length; i++) {
    const feature = roads.features[i];
    const geom = feature.geometry;
    const lines: number[][][] =
      geom.type === 'MultiLineString'
        ? (geom.coordinates as number[][][])
        : [geom.coordinates as number[][]];

    for (const line of lines) {
      if (line.length < 2) continue;
      ctx.beginPath();
      const [x0, y0] = projectMercator(line[0][0], line[0][1], width, height);
      ctx.moveTo(x0, y0);
      for (let j = 1; j < line.length; j++) {
        const [x, y] = projectMercator(line[j][0], line[j][1], width, height);
        ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
  }

  // Draw sea lanes as faint background lines (from pre-computed coords)
  ctx.save();
  ctx.setLineDash([4, 6]);
  ctx.strokeStyle = 'rgba(60,80,120,0.15)';
  ctx.lineWidth = 0.5;
  if (heatmap.seaLaneCoords) {
    for (const coords of Object.values(heatmap.seaLaneCoords)) {
      if (coords.length < 2) continue;
      ctx.beginPath();
      const [x0, y0] = projectMercator(coords[0][0], coords[0][1], width, height);
      ctx.moveTo(x0, y0);
      for (let j = 1; j < coords.length; j++) {
        const [x, y] = projectMercator(coords[j][0], coords[j][1], width, height);
        ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
  }
  ctx.restore();

  // Draw road segments with traffic data — sorted low-to-high so high values render on top
  const segEntries: Array<[number, number]> = [];
  for (const [segIdx, eras] of Object.entries(heatmap.segments)) {
    const segData = eras[eraStartYear];
    if (segData) {
      const sortVal = colorMode === 'distance' ? segData.avgDist : segData.count;
      if (sortVal > 0) {
        segEntries.push([parseInt(segIdx), sortVal]);
      }
    }
  }
  segEntries.sort((a, b) => a[1] - b[1]);

  // Apply animation progress: only draw a portion of segments
  // segEntries is sorted low-to-high; for animation we want high-traffic first
  // So we draw from the end (highest) backwards
  const totalSegs = segEntries.length;
  const segsToDraw = animProgress < 1
    ? Math.ceil(animProgress * totalSegs)
    : totalSegs;
  // Start index: draw the top `segsToDraw` entries (highest values)
  const startIdx = totalSegs - segsToDraw;

  for (let si = startIdx; si < totalSegs; si++) {
    const [segIdx] = segEntries[si];
    if (segIdx >= roads.features.length) continue;
    const segData = heatmap.segments[String(segIdx)]?.[eraStartYear];
    if (!segData) continue;

    const feature = roads.features[segIdx];
    const geom = feature.geometry;
    const lines: number[][][] =
      geom.type === 'MultiLineString'
        ? (geom.coordinates as number[][][])
        : [geom.coordinates as number[][]];

    // Skip low-traffic noise (segments with fewer than 3 letters)
    if (segData.count < 3) continue;

    if (colorMode === 'distance') {
      // Color = average distance, Width = volume (busy roads are thick)
      ctx.strokeStyle = distanceColor(segData.avgDist, heatmap.maxAvgDist);
      ctx.lineWidth = trafficWidth(segData.count, heatmap.maxTraffic);
    } else {
      ctx.strokeStyle = trafficColor(segData.count, heatmap.maxTraffic);
      ctx.lineWidth = trafficWidth(segData.count, heatmap.maxTraffic);
    }

    for (const line of lines) {
      if (line.length < 2) continue;
      ctx.beginPath();
      const [x0, y0] = projectMercator(line[0][0], line[0][1], width, height);
      ctx.moveTo(x0, y0);
      for (let j = 1; j < line.length; j++) {
        const [x, y] = projectMercator(line[j][0], line[j][1], width, height);
        ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
  }

  // Draw sea lanes with traffic from pre-computed data — sorted low-to-high
  if (heatmap.seaLanes && heatmap.seaLaneCoords) {
    const seaEntries: Array<[string, SegmentEraData]> = [];
    for (const [connIdx, eras] of Object.entries(heatmap.seaLanes)) {
      const seaData = eras[eraStartYear];
      if (seaData && seaData.count >= 2) {
        seaEntries.push([connIdx, seaData]);
      }
    }
    // Sort by the value used for coloring (low to high so high renders on top)
    seaEntries.sort((a, b) => {
      const aVal = colorMode === 'distance' ? a[1].avgDist : a[1].count;
      const bVal = colorMode === 'distance' ? b[1].avgDist : b[1].count;
      return aVal - bVal;
    });

    if (seaEntries.length > 0) {
      ctx.save();
      ctx.setLineDash([6, 4]);
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      const effectiveSeaMax = Math.max(heatmap.maxSeaTraffic, 1);
      for (const [connIdx, seaData] of seaEntries) {
        const coords = heatmap.seaLaneCoords[connIdx];
        if (!coords || coords.length < 2) continue;

        if (colorMode === 'distance') {
          ctx.strokeStyle = distanceColor(seaData.avgDist, heatmap.maxAvgDist);
          ctx.lineWidth = trafficWidth(seaData.count, effectiveSeaMax);
        } else {
          ctx.strokeStyle = trafficColor(seaData.count, effectiveSeaMax);
          ctx.lineWidth = trafficWidth(seaData.count, effectiveSeaMax);
        }

        ctx.beginPath();
        const [x0, y0] = projectMercator(coords[0][0], coords[0][1], width, height);
        ctx.moveTo(x0, y0);
        for (let j = 1; j < coords.length; j++) {
          const [x, y] = projectMercator(coords[j][0], coords[j][1], width, height);
          ctx.lineTo(x, y);
        }
        ctx.stroke();
      }
      ctx.restore();
    }
  }

  // Draw average distance ring centered on Rome
  const avgDist = computeAvgDistForEra(heatmap, eraStartYear);
  if (avgDist > 0) {
    const [romX, romY] = projectMercator(12.5, 41.9, width, height);
    // Convert km to approximate pixels (rough: 1 degree ~ 111km, scale from projection)
    const degreesRadius = avgDist / 111;
    const [edgeX] = projectMercator(12.5 + degreesRadius, 41.9, width, height);
    const pixelRadius = Math.abs(edgeX - romX);

    ctx.save();
    ctx.strokeStyle = 'rgba(255, 200, 50, 0.3)';
    ctx.lineWidth = 2;
    ctx.setLineDash([8, 4]);
    ctx.beginPath();
    ctx.arc(romX, romY, pixelRadius, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }

  // Draw large distance stat overlay
  if (avgDist > 0) {
    ctx.save();
    ctx.font = 'bold 28px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillStyle = 'rgba(255,255,255,0.85)';
    ctx.shadowColor = 'rgba(0,0,0,0.5)';
    ctx.shadowBlur = 4;
    ctx.fillText(`${avgDist.toLocaleString()} km`, width / 2, height - 20);
    ctx.font = '12px sans-serif';
    ctx.fillStyle = 'rgba(255,255,255,0.6)';
    ctx.fillText('avg. letter distance', width / 2, height - 6);
    ctx.restore();
  }
}

// ── Legend ────────────────────────────────────────────────────────────
function Legend({ maxTraffic, maxAvgDist, colorMode }: { maxTraffic: number; maxAvgDist: number; colorMode: ColorMode }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = 200 * dpr;
    canvas.height = 12 * dpr;
    ctx.scale(dpr, dpr);

    for (let i = 0; i < 200; i++) {
      if (colorMode === 'distance') {
        const dist = (i / 200) * maxAvgDist;
        ctx.fillStyle = distanceColor(dist, maxAvgDist);
      } else {
        const count = (i / 200) * maxTraffic;
        ctx.fillStyle = trafficColor(count, maxTraffic);
      }
      ctx.fillRect(i, 0, 1, 12);
    }
  }, [maxTraffic, maxAvgDist, colorMode]);

  return (
    <div className="flex items-center gap-2 text-[10px] text-theme-muted">
      <span>0</span>
      <canvas
        ref={canvasRef}
        style={{ width: 200, height: 12, borderRadius: 2 }}
      />
      <span>
        {colorMode === 'distance'
          ? `${maxAvgDist} km avg.`
          : `${maxTraffic} letters`}
      </span>
    </div>
  );
}

// ── Era selector ─────────────────────────────────────────────────────
function EraSelector({
  label,
  selected,
  onSelect,
  letterCounts,
}: {
  label: string;
  selected: string;
  onSelect: (era: string) => void;
  letterCounts: Record<string, number>;
}) {
  return (
    <div className="flex flex-col items-center gap-1.5">
      <span className="text-[11px] font-medium tracking-wide uppercase text-theme-muted">
        {label}
      </span>
      <div className="flex gap-1">
        {ERA_OPTIONS.map((era) => {
          const isActive = selected === era.key;
          const count = letterCounts[era.key] || 0;
          const countLabel = count >= 1000
            ? `${(count / 1000).toFixed(1).replace(/\.0$/, '')}K`
            : `${count}`;
          return (
            <button
              key={era.key}
              onClick={() => onSelect(era.key)}
              className={`
                px-2 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer border
                ${
                  isActive
                    ? 'bg-[var(--color-accent)] text-white border-[var(--color-accent)]'
                    : 'bg-theme-surface text-theme-muted border-theme hover:text-theme-text hover:border-[var(--color-accent)]'
                }
              `}
            >
              {era.label}
              <span className={`block text-[9px] leading-tight ${isActive ? 'text-white/70' : 'text-theme-muted'}`}>
                {countLabel}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ── Compute letter counts per era ─────────────────────────────────────
function computeLetterCounts(letters: MapLetter[]): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const letter of letters) {
    const eraStart = Math.floor(letter.year_approx / 50) * 50;
    const key = String(eraStart);
    counts[key] = (counts[key] || 0) + 1;
  }
  return counts;
}

// ── Compute total road traffic for a given era ────────────────────────
function computeRoadTrafficTotal(heatmap: HeatmapData, eraKey: string): number {
  let total = 0;
  for (const eras of Object.values(heatmap.segments)) {
    total += eras[eraKey]?.count || 0;
  }
  return total;
}

// ── Compute total sea traffic for a given era ────────────────────────
function computeSeaTrafficTotal(heatmap: HeatmapData, eraKey: string): number {
  let total = 0;
  if (!heatmap.seaLanes) return 0;
  for (const eras of Object.values(heatmap.seaLanes)) {
    total += eras[eraKey]?.count || 0;
  }
  return total;
}

// ── Compute weighted average distance across all segments for an era ──
function computeAvgDistForEra(heatmap: HeatmapData, eraKey: string): number {
  let totalDist = 0;
  let totalCount = 0;
  for (const eras of Object.values(heatmap.segments)) {
    const d = eras[eraKey];
    if (d) {
      totalDist += d.avgDist * d.count;
      totalCount += d.count;
    }
  }
  return totalCount > 0 ? Math.round(totalDist / totalCount) : 0;
}

// ── Main component ───────────────────────────────────────────────────
export default function RoadHeatmap() {
  const leftCanvasRef = useRef<HTMLCanvasElement>(null);
  const rightCanvasRef = useRef<HTMLCanvasElement>(null);
  const [heatmap, setHeatmap] = useState<HeatmapData | null>(null);
  const [roads, setRoads] = useState<GeoJSONFeatureCollection | null>(null);
  const [letters, setLetters] = useState<MapLetter[] | null>(null);
  const [outline, setOutline] = useState<OutlineFeatureCollection | null>(null);
  const [loading, setLoading] = useState(true);
  const [leftEra, setLeftEra] = useState('350');
  const [rightEra, setRightEra] = useState('500');
  const [colorMode, setColorMode] = useState<ColorMode>('distance');

  // Animation state
  const [isAnimating, setIsAnimating] = useState(false);
  const [animProgress, setAnimProgress] = useState(1); // 0-1, starts at 1 (fully drawn)
  const animRef = useRef<number>(0);

  function startAnimation() {
    if (animRef.current) cancelAnimationFrame(animRef.current);
    setAnimProgress(0);
    setIsAnimating(true);
    const startTime = performance.now();
    const duration = 2000; // 2 seconds

    function frame(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      setAnimProgress(progress);

      if (progress < 1) {
        animRef.current = requestAnimationFrame(frame);
      } else {
        setIsAnimating(false);
      }
    }
    animRef.current = requestAnimationFrame(frame);
  }

  // Cleanup animation on unmount
  useEffect(() => {
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, []);

  // Load data
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetch('/data/road-heatmap.json').then((r) => r.json()),
      fetch('/data/roman-roads.json').then((r) => r.json()),
      fetch('/data/map-letters.json').then((r) => r.json()),
      fetch('/data/mediterranean-outline.json').then((r) => r.json()),
    ]).then(([hm, rd, ml, ol]) => {
      if (cancelled) return;
      setHeatmap(hm as HeatmapData);
      setRoads(rd as GeoJSONFeatureCollection);
      setLetters((ml as { letters: MapLetter[] }).letters);
      setOutline(ol as OutlineFeatureCollection);
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // Compute letter counts for era badges
  const letterCounts = letters ? computeLetterCounts(letters) : {};

  // Render both canvases (sea traffic is now pre-computed in heatmap data)
  const render = useCallback(() => {
    if (!heatmap || !roads) return;
    if (leftCanvasRef.current) {
      drawHeatmap(leftCanvasRef.current, roads, heatmap, leftEra, colorMode, outline, animProgress);
    }
    if (rightCanvasRef.current) {
      drawHeatmap(rightCanvasRef.current, roads, heatmap, rightEra, colorMode, outline, animProgress);
    }
  }, [heatmap, roads, leftEra, rightEra, colorMode, outline, animProgress]);

  useEffect(() => {
    if (loading) return;
    // Small delay to ensure canvas is laid out
    const id = requestAnimationFrame(render);
    return () => cancelAnimationFrame(id);
  }, [loading, render]);

  // Re-render on resize
  useEffect(() => {
    if (loading) return;
    const handleResize = () => render();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [loading, render]);

  // Era change handlers that also trigger animation
  function handleLeftEraChange(era: string) {
    setLeftEra(era);
    startAnimation();
  }
  function handleRightEraChange(era: string) {
    setRightEra(era);
    startAnimation();
  }

  // Compute traffic totals for panel labels
  const leftRoadTotal = heatmap ? computeRoadTrafficTotal(heatmap, leftEra) : 0;
  const rightRoadTotal = heatmap ? computeRoadTrafficTotal(heatmap, rightEra) : 0;
  const leftSeaTotal = heatmap
    ? computeSeaTrafficTotal(heatmap, leftEra)
    : 0;
  const rightSeaTotal = heatmap
    ? computeSeaTrafficTotal(heatmap, rightEra)
    : 0;
  const leftAvgDist = heatmap ? computeAvgDistForEra(heatmap, leftEra) : 0;
  const rightAvgDist = heatmap ? computeAvgDistForEra(heatmap, rightEra) : 0;

  function formatTraffic(n: number): string {
    if (n >= 1000) return `${(n / 1000).toFixed(1).replace(/\.0$/, '')}K`;
    return String(n);
  }

  return (
    <section className="max-w-[1400px] mx-auto px-4 sm:px-6 mt-8 mb-12">
      <div className="border-t border-theme pt-6">
        <h2
          className="text-lg tracking-tight mb-1"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Road and Sea Traffic: Before and After
        </h2>
        <p className="text-xs text-theme-muted mb-4 max-w-2xl leading-relaxed">
          Select two eras to compare how letter traffic shifted across the Roman
          world. Solid lines show road traffic; dashed lines show sea routes.
        </p>

        {loading ? (
          <div
            className="flex items-center justify-center rounded-lg border border-theme"
            style={{
              height: 300,
              background: 'var(--color-surface)',
            }}
          >
            <span className="text-sm text-theme-muted animate-pulse">
              Loading road network...
            </span>
          </div>
        ) : (
          <>
            {/* Era selectors + Replay button */}
            <div className="flex flex-wrap justify-center items-end gap-8 mb-4">
              <EraSelector
                label="Before"
                selected={leftEra}
                onSelect={handleLeftEraChange}
                letterCounts={letterCounts}
              />
              <button
                onClick={startAnimation}
                disabled={isAnimating}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium
                  bg-theme-surface border border-theme text-theme-muted
                  hover:text-theme-accent hover:border-[var(--color-accent)] transition-colors
                  disabled:opacity-40 cursor-pointer"
              >
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M4 2l10 6-10 6V2z" />
                </svg>
                {isAnimating ? 'Playing...' : 'Replay'}
              </button>
              <EraSelector
                label="After"
                selected={rightEra}
                onSelect={handleRightEraChange}
                letterCounts={letterCounts}
              />
            </div>

            <div className="flex justify-center mb-3">
              <div className="inline-flex items-center gap-1 text-xs text-theme-muted">
                <span className="mr-1">Color by:</span>
                <button
                  onClick={() => setColorMode('distance')}
                  className={`px-2 py-0.5 rounded transition-colors cursor-pointer ${
                    colorMode === 'distance'
                      ? 'bg-[var(--color-accent)] text-white'
                      : 'bg-theme-surface text-theme-muted hover:text-theme-text'
                  }`}
                >
                  Distance
                </button>
                <button
                  onClick={() => setColorMode('volume')}
                  className={`px-2 py-0.5 rounded transition-colors cursor-pointer ${
                    colorMode === 'volume'
                      ? 'bg-[var(--color-accent)] text-white'
                      : 'bg-theme-surface text-theme-muted hover:text-theme-text'
                  }`}
                >
                  Volume
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Left panel */}
              <div>
                <canvas
                  ref={leftCanvasRef}
                  className="w-full rounded-lg border-2 border-theme"
                  style={{ aspectRatio: '16 / 10', display: 'block', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}
                />
                <p
                  className="mt-2 text-sm text-center"
                  style={{ fontFamily: 'var(--font-serif)' }}
                >
                  <span className="text-theme-accent font-medium">
                    {parseInt(leftEra)}&ndash;{parseInt(leftEra) + 49} AD
                  </span>{' '}
                  <span className="text-theme-muted text-xs">
                    {colorMode === 'distance'
                      ? `(Avg. distance: ${leftAvgDist} km)`
                      : `(${formatTraffic(leftRoadTotal)} road + ${formatTraffic(leftSeaTotal)} sea)`}
                  </span>
                </p>
              </div>

              {/* Right panel */}
              <div>
                <canvas
                  ref={rightCanvasRef}
                  className="w-full rounded-lg border-2 border-theme"
                  style={{ aspectRatio: '16 / 10', display: 'block', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}
                />
                <p
                  className="mt-2 text-sm text-center"
                  style={{ fontFamily: 'var(--font-serif)' }}
                >
                  <span className="text-theme-accent font-medium">
                    {parseInt(rightEra)}&ndash;{parseInt(rightEra) + 49} AD
                  </span>{' '}
                  <span className="text-theme-muted text-xs">
                    {colorMode === 'distance'
                      ? `(Avg. distance: ${rightAvgDist} km)`
                      : `(${formatTraffic(rightRoadTotal)} road + ${formatTraffic(rightSeaTotal)} sea)`}
                  </span>
                </p>
              </div>
            </div>

            {/* Shared legend */}
            <div className="mt-3 flex flex-col items-center gap-1">
              <Legend maxTraffic={heatmap?.maxTraffic ?? 340} maxAvgDist={heatmap?.maxAvgDist ?? 2000} colorMode={colorMode} />
              <div className="flex items-center gap-3 text-[10px] text-theme-muted">
                <span className="flex items-center gap-1">
                  <span style={{ display: 'inline-block', width: 20, height: 2, background: 'rgba(200,120,40,0.8)' }} />
                  Roads
                </span>
                <span className="flex items-center gap-1">
                  <span
                    style={{
                      display: 'inline-block',
                      width: 20,
                      height: 0,
                      borderTop: '2px dashed rgba(200,120,40,0.8)',
                    }}
                  />
                  Sea routes
                </span>
                <span>
                  {colorMode === 'distance' ? 'Average letter distance' : 'Letter volume'}
                </span>
              </div>
            </div>
          </>
        )}
      </div>
    </section>
  );
}

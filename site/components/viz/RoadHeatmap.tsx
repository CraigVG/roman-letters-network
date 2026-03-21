'use client';

import { useRef, useEffect, useState, useCallback } from 'react';

// ── Types ─────────────────────────────────────────────────────────────
interface Era {
  label: string;
  start: number;
  end: number;
}

interface HeatmapData {
  eras: Era[];
  segments: Record<string, Record<string, number>>;
  maxTraffic: number;
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

// ── Drawing ──────────────────────────────────────────────────────────
function drawHeatmap(
  canvas: HTMLCanvasElement,
  roads: GeoJSONFeatureCollection,
  heatmap: HeatmapData,
  eraStartYear: string,
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

  // Draw segments with traffic data — sorted low-to-high so high values render on top
  const segEntries: Array<[number, number]> = [];
  for (const [segIdx, eras] of Object.entries(heatmap.segments)) {
    const count = eras[eraStartYear] || 0;
    if (count > 0) {
      segEntries.push([parseInt(segIdx), count]);
    }
  }
  segEntries.sort((a, b) => a[1] - b[1]);

  for (const [segIdx, count] of segEntries) {
    if (segIdx >= roads.features.length) continue;
    const feature = roads.features[segIdx];
    const geom = feature.geometry;
    const lines: number[][][] =
      geom.type === 'MultiLineString'
        ? (geom.coordinates as number[][][])
        : [geom.coordinates as number[][]];

    ctx.strokeStyle = trafficColor(count, heatmap.maxTraffic);
    ctx.lineWidth = trafficWidth(count, heatmap.maxTraffic);

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
}

// ── Legend ────────────────────────────────────────────────────────────
function Legend({ maxTraffic }: { maxTraffic: number }) {
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
      const count = (i / 200) * maxTraffic;
      ctx.fillStyle = trafficColor(count, maxTraffic);
      ctx.fillRect(i, 0, 1, 12);
    }
  }, [maxTraffic]);

  return (
    <div className="flex items-center gap-2 text-[10px] text-theme-muted">
      <span>0</span>
      <canvas
        ref={canvasRef}
        style={{ width: 200, height: 12, borderRadius: 2 }}
      />
      <span>{maxTraffic} letters</span>
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────
export default function RoadHeatmap() {
  const leftCanvasRef = useRef<HTMLCanvasElement>(null);
  const rightCanvasRef = useRef<HTMLCanvasElement>(null);
  const [heatmap, setHeatmap] = useState<HeatmapData | null>(null);
  const [roads, setRoads] = useState<GeoJSONFeatureCollection | null>(null);
  const [loading, setLoading] = useState(true);

  // Load data
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetch('/data/road-heatmap.json').then((r) => r.json()),
      fetch('/data/roman-roads.json').then((r) => r.json()),
    ]).then(([hm, rd]) => {
      if (cancelled) return;
      setHeatmap(hm as HeatmapData);
      setRoads(rd as GeoJSONFeatureCollection);
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // Render both canvases
  const render = useCallback(() => {
    if (!heatmap || !roads) return;
    if (leftCanvasRef.current) {
      drawHeatmap(leftCanvasRef.current, roads, heatmap, '350');
    }
    if (rightCanvasRef.current) {
      drawHeatmap(rightCanvasRef.current, roads, heatmap, '500');
    }
  }, [heatmap, roads]);

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

  return (
    <section className="max-w-[1400px] mx-auto px-4 sm:px-6 mt-8 mb-12">
      <div className="border-t border-theme pt-6">
        <h2
          className="text-lg tracking-tight mb-1"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          The Network Before and After
        </h2>
        <p className="text-xs text-theme-muted mb-4 max-w-2xl leading-relaxed">
          Roman road segments colored by letter traffic. At its peak the network
          connected every corner of the Mediterranean; after fragmentation, only
          the eastern corridors survived.
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
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Left panel: peak */}
              <div>
                <canvas
                  ref={leftCanvasRef}
                  className="w-full rounded-lg border border-theme"
                  style={{ aspectRatio: '16 / 10', display: 'block' }}
                />
                <p
                  className="mt-2 text-sm text-center"
                  style={{ fontFamily: 'var(--font-serif)' }}
                >
                  <span className="text-theme-accent font-medium">Peak:</span>{' '}
                  <span className="text-theme-muted">350 &ndash; 399 AD</span>
                </p>
              </div>

              {/* Right panel: post-collapse */}
              <div>
                <canvas
                  ref={rightCanvasRef}
                  className="w-full rounded-lg border border-theme"
                  style={{ aspectRatio: '16 / 10', display: 'block' }}
                />
                <p
                  className="mt-2 text-sm text-center"
                  style={{ fontFamily: 'var(--font-serif)' }}
                >
                  <span className="text-theme-accent font-medium">
                    After Fragmentation:
                  </span>{' '}
                  <span className="text-theme-muted">500 &ndash; 549 AD</span>
                </p>
              </div>
            </div>

            {/* Shared legend */}
            <div className="mt-3 flex justify-center">
              <Legend maxTraffic={heatmap?.maxTraffic ?? 340} />
            </div>
          </>
        )}
      </div>
    </section>
  );
}

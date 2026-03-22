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

// ── Era definitions ──────────────────────────────────────────────────
const ERAS = ['350', '400', '450', '500'];

const ERA_SUBTITLES: Record<string, string> = {
  '350': 'Peak: letters cross the entire Mediterranean',
  '400': 'The first cracks appear',
  '450': 'The Western provinces regionalize',
  '500': 'New kingdoms, shrinking networks',
};

// Sea lanes are now pre-computed in road-heatmap.json (seaLanes + seaLaneCoords)

// ── Projection ───────────────────────────────────────────────────────
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

// ── Color functions (distance-based, from RoadHeatmap) ───────────────
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
    g = 120 + s * 100;
    b = 30 + s * 170;
  }
  const alpha = 0.5 + t * 0.5;
  return `rgba(${Math.round(r)},${Math.round(g)},${Math.round(b)},${alpha.toFixed(2)})`;
}

function distanceColorRGBA(avgDist: number, _maxAvgDist: number): [number, number, number, number] {
  if (avgDist <= 0) return [80, 80, 80, 0.15];
  const t = Math.min(avgDist / 1500, 1);
  let r: number, g: number, b: number;
  if (t < 0.33) {
    const s = t / 0.33;
    r = 40 + s * 60;
    g = 140 + s * 60;
    b = 180 - s * 20;
  } else if (t < 0.67) {
    const s = (t - 0.33) / 0.34;
    r = 100 + s * 155;
    g = 200 - s * 80;
    b = 160 - s * 130;
  } else {
    const s = (t - 0.67) / 0.33;
    r = 255;
    g = 120 + s * 100;
    b = 30 + s * 170;
  }
  const alpha = 0.5 + t * 0.5;
  return [Math.round(r), Math.round(g), Math.round(b), alpha];
}

function trafficWidth(count: number, maxTraffic: number): number {
  if (count <= 0) return 0.3;
  const t = Math.min(count / maxTraffic, 1);
  return 0.5 + t * 3;
}

function trafficColor(count: number, maxTraffic: number): string {
  if (count <= 0) return 'rgba(80,80,80,0.15)';
  const t = Math.min(count / maxTraffic, 1);
  let r: number, g: number, b: number;
  if (t < 0.15) {
    const s = t / 0.15;
    r = 40 + s * 60;
    g = 160 + s * 40;
    b = 200 - s * 40;
  } else if (t < 0.4) {
    const s = (t - 0.15) / 0.25;
    r = 100 + s * 155;
    g = 200 - s * 80;
    b = 160 - s * 120;
  } else {
    const s = (t - 0.4) / 0.6;
    r = 255;
    g = 120 - s * 50;
    b = 40 - s * 30;
  }
  const alpha = 0.5 + t * 0.5;
  return `rgba(${Math.round(r)},${Math.round(g)},${Math.round(b)},${alpha.toFixed(2)})`;
}

// Sea traffic is now pre-computed in road-heatmap.json

// ── Compute weighted average distance for an era ─────────────────────
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

// ── Ease-out cubic ───────────────────────────────────────────────────
function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

// ── Timing constants ─────────────────────────────────────────────────
const ERA_DURATION = 2500; // ms each era shows
const CROSSFADE_DURATION = 500; // ms for crossfade
const BUILDUP_DURATION = 500; // ms for road buildup at start of era
const TOTAL_ERA_TIME = ERA_DURATION + CROSSFADE_DURATION;
const TOTAL_CYCLE = ERAS.length * TOTAL_ERA_TIME;

// ── Draw a single frame for a given era ──────────────────────────────
function drawEraFrame(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  roads: GeoJSONFeatureCollection,
  heatmap: HeatmapData,
  outline: OutlineFeatureCollection | null,
  eraKey: string,
  buildupProgress: number, // 0-1, how much of roads to show
  globalAlpha: number, // for crossfade
  glowPhase: number, // 0-2pi for glow pulse
) {
  ctx.save();
  ctx.globalAlpha = globalAlpha;

  // Draw coastline outline
  if (outline) {
    ctx.fillStyle = 'rgba(30,40,55,0.3)';
    ctx.strokeStyle = 'rgba(60,80,100,0.2)';
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

  // All roads as faint gray background
  ctx.strokeStyle = 'rgba(80,80,80,0.15)';
  ctx.lineWidth = 0.3;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  for (const feature of roads.features) {
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

  // Background sea lanes (from pre-computed coords)
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

  // Traffic-colored road segments, sorted low-to-high, with buildup
  const segEntries: Array<[number, number, number]> = []; // [segIdx, sortVal, avgDist]
  for (const [segIdx, eras] of Object.entries(heatmap.segments)) {
    const segData = eras[eraKey];
    if (segData && segData.avgDist > 0 && segData.count >= 3) {
      segEntries.push([parseInt(segIdx), segData.avgDist, segData.count]);
    }
  }
  segEntries.sort((a, b) => a[1] - b[1]);

  const easedProgress = easeOutCubic(buildupProgress);
  const segsToDraw = Math.ceil(easedProgress * segEntries.length);
  const startIdx = segEntries.length - segsToDraw;

  // Glow multiplier for brightest roads
  const glowMult = 1 + 0.15 * Math.sin(glowPhase);

  for (let si = startIdx; si < segEntries.length; si++) {
    const [segIdx, , segCount] = segEntries[si];
    if (segIdx >= roads.features.length) continue;
    const segData = heatmap.segments[String(segIdx)]?.[eraKey];
    if (!segData) continue;

    const feature = roads.features[segIdx];
    const geom = feature.geometry;
    const lines: number[][][] =
      geom.type === 'MultiLineString'
        ? (geom.coordinates as number[][][])
        : [geom.coordinates as number[][]];

    // Apply glow to high-traffic segments
    const isHighTraffic = segCount / heatmap.maxTraffic > 0.4;
    if (isHighTraffic) {
      const [r, g, b, a] = distanceColorRGBA(segData.avgDist, heatmap.maxAvgDist);
      const glowAlpha = Math.min(a * glowMult, 1);
      ctx.strokeStyle = `rgba(${r},${g},${b},${glowAlpha.toFixed(2)})`;
      ctx.lineWidth = trafficWidth(segData.count, heatmap.maxTraffic) * glowMult;
    } else {
      ctx.strokeStyle = distanceColor(segData.avgDist, heatmap.maxAvgDist);
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

  // Sea lanes with traffic (from pre-computed data)
  if (heatmap.seaLanes && heatmap.seaLaneCoords) {
    const seaEntries: Array<[string, SegmentEraData]> = [];
    for (const [connIdx, eras] of Object.entries(heatmap.seaLanes)) {
      const seaData = eras[eraKey];
      if (seaData && seaData.count >= 2) {
        seaEntries.push([connIdx, seaData]);
      }
    }
    seaEntries.sort((a, b) => a[1].count - b[1].count);

    if (seaEntries.length > 0) {
      ctx.save();
      ctx.setLineDash([6, 4]);
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      const effectiveMax = Math.max(heatmap.maxSeaTraffic, 1);
      for (const [connIdx, seaData] of seaEntries) {
        const coords = heatmap.seaLaneCoords[connIdx];
        if (!coords || coords.length < 2) continue;
        ctx.strokeStyle = trafficColor(seaData.count, effectiveMax);
        ctx.lineWidth = trafficWidth(seaData.count, effectiveMax);
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
  const avgDist = computeAvgDistForEra(heatmap, eraKey);
  if (avgDist > 0) {
    const [romX, romY] = projectMercator(12.5, 41.9, width, height);
    const degreesRadius = avgDist / 111;
    const [edgeX] = projectMercator(12.5 + degreesRadius, 41.9, width, height);
    const pixelRadius = Math.abs(edgeX - romX);

    ctx.save();
    ctx.globalAlpha = globalAlpha; // respect crossfade
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
    ctx.globalAlpha = globalAlpha; // respect crossfade
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

  ctx.restore();
}

// ── Draw text overlays ───────────────────────────────────────────────
function drawTextOverlays(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  eraKey: string,
  avgDist: number,
  textAlpha: number,
) {
  ctx.save();
  ctx.globalAlpha = textAlpha;

  // Title
  ctx.font = 'bold 36px Georgia, "Times New Roman", serif';
  ctx.fillStyle = 'rgba(255,255,255,0.92)';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';

  // Text shadow for readability
  ctx.shadowColor = 'rgba(0,0,0,0.7)';
  ctx.shadowBlur = 8;
  ctx.shadowOffsetX = 0;
  ctx.shadowOffsetY = 2;

  ctx.fillText('The Shrinking World', width / 2, 30);

  // Era label
  ctx.font = '22px Georgia, "Times New Roman", serif';
  ctx.fillStyle = 'rgba(255,255,255,0.8)';
  ctx.fillText(`Roman Letter Networks, ${eraKey}s AD`, width / 2, 74);

  // Subtitle
  const subtitle = ERA_SUBTITLES[eraKey] || '';
  ctx.font = 'italic 16px Georgia, "Times New Roman", serif';
  ctx.fillStyle = 'rgba(255,255,255,0.6)';
  ctx.fillText(subtitle, width / 2, 104);

  // Bottom left: avg distance
  ctx.textAlign = 'left';
  ctx.textBaseline = 'bottom';
  ctx.font = '14px Georgia, "Times New Roman", serif';
  ctx.fillStyle = 'rgba(255,255,255,0.65)';
  ctx.fillText(`Average letter distance: ${avgDist} km`, 20, height - 20);

  // Bottom right: branding
  ctx.textAlign = 'right';
  ctx.font = '14px Georgia, "Times New Roman", serif';
  ctx.fillStyle = 'rgba(255,255,255,0.5)';
  ctx.fillText('romanletters.org', width - 20, height - 20);

  ctx.restore();
}

// ── Main component ───────────────────────────────────────────────────
export function HeatmapTimelapse() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loading, setLoading] = useState(true);
  const [paused, setPaused] = useState(false);
  const pausedRef = useRef(false);
  const dataRef = useRef<{
    heatmap: HeatmapData;
    roads: GeoJSONFeatureCollection;
    outline: OutlineFeatureCollection;
    avgDists: Record<string, number>;
  } | null>(null);
  const animRef = useRef<number>(0);
  const timeRef = useRef(0); // accumulated time in ms

  // Sync paused ref
  useEffect(() => {
    pausedRef.current = paused;
  }, [paused]);

  // Load data
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetch('/data/road-heatmap.json').then((r) => r.json()),
      fetch('/data/roman-roads.json').then((r) => r.json()),
      fetch('/data/mediterranean-outline.json').then((r) => r.json()),
    ]).then(([hm, rd, ol]) => {
      if (cancelled) return;
      const heatmap = hm as HeatmapData;
      const roads = rd as GeoJSONFeatureCollection;
      const outline = ol as OutlineFeatureCollection;

      // Precompute avg distances per era
      const avgDists: Record<string, number> = {};
      for (const era of ERAS) {
        avgDists[era] = computeAvgDistForEra(heatmap, era);
      }

      dataRef.current = {
        heatmap,
        roads,
        outline,
        avgDists,
      };
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, []);

  // Animation loop
  const animate = useCallback(() => {
    const canvas = canvasRef.current;
    const data = dataRef.current;
    if (!canvas || !data) return;

    let lastTime = performance.now();

    function frame(now: number) {
      const c = canvasRef.current;
      const d = dataRef.current;
      if (!c || !d) return;

      const ctx = c.getContext('2d');
      if (!ctx) return;

      const dpr = window.devicePixelRatio || 1;
      const rect = c.getBoundingClientRect();
      const width = rect.width;
      const height = rect.height;
      c.width = width * dpr;
      c.height = height * dpr;
      ctx.scale(dpr, dpr);

      const dt = now - lastTime;
      lastTime = now;

      if (!pausedRef.current) {
        timeRef.current = (timeRef.current + dt) % TOTAL_CYCLE;
      }

      const t = timeRef.current;
      const eraIndex = Math.floor(t / TOTAL_ERA_TIME);
      const eraLocalTime = t - eraIndex * TOTAL_ERA_TIME;

      const currentEra = ERAS[eraIndex];
      const nextEra = ERAS[(eraIndex + 1) % ERAS.length];

      // Clear
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#0d1117';
      ctx.fillRect(0, 0, width, height);

      // Glow phase (continuous)
      const glowPhase = (now / 800) % (Math.PI * 2);

      if (eraLocalTime < ERA_DURATION) {
        // Within the era display period
        const buildupProgress = Math.min(eraLocalTime / BUILDUP_DURATION, 1);
        const textAlpha = Math.min(eraLocalTime / 300, 1); // text fades in 300ms

        drawEraFrame(
          ctx, width, height,
          d.roads, d.heatmap, d.outline,
          currentEra,
          buildupProgress, 1, glowPhase,
        );
        drawTextOverlays(ctx, width, height, currentEra, d.avgDists[currentEra], textAlpha);
      } else {
        // Crossfade period
        const fadeProgress = (eraLocalTime - ERA_DURATION) / CROSSFADE_DURATION;
        const outAlpha = 1 - fadeProgress;
        const inAlpha = fadeProgress;

        // Draw outgoing era
        drawEraFrame(
          ctx, width, height,
          d.roads, d.heatmap, d.outline,
          currentEra,
          1, outAlpha, glowPhase,
        );
        drawTextOverlays(ctx, width, height, currentEra, d.avgDists[currentEra], outAlpha);

        // Draw incoming era
        drawEraFrame(
          ctx, width, height,
          d.roads, d.heatmap, d.outline,
          nextEra,
          Math.min(fadeProgress * 2, 1), inAlpha, glowPhase,
        );
        drawTextOverlays(ctx, width, height, nextEra, d.avgDists[nextEra], inAlpha);
      }

      // Pause indicator (small, bottom-center)
      if (pausedRef.current) {
        ctx.save();
        ctx.globalAlpha = 0.5;
        ctx.fillStyle = '#ffffff';
        // Two vertical bars for pause icon
        const cx = width / 2;
        const cy = height - 50;
        ctx.fillRect(cx - 8, cy - 8, 5, 16);
        ctx.fillRect(cx + 3, cy - 8, 5, 16);
        ctx.restore();
      }

      animRef.current = requestAnimationFrame(frame);
    }

    animRef.current = requestAnimationFrame(frame);
  }, []);

  // Start animation when data loads
  useEffect(() => {
    if (loading) return;
    animate();
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [loading, animate]);

  // Handle resize
  useEffect(() => {
    if (loading) return;
    const handleResize = () => {
      // Cancel and restart animation to pick up new dimensions
      if (animRef.current) cancelAnimationFrame(animRef.current);
      animate();
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [loading, animate]);

  // Click to pause/resume
  const handleClick = useCallback(() => {
    setPaused((p) => !p);
  }, []);

  if (loading) {
    return (
      <div
        style={{
          width: '100vw',
          height: '100vh',
          background: '#0d1117',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <span style={{ color: 'rgba(255,255,255,0.4)', fontFamily: 'Georgia, serif', fontSize: 18 }}>
          Loading road network...
        </span>
      </div>
    );
  }

  return (
    <canvas
      ref={canvasRef}
      onClick={handleClick}
      style={{
        width: '100vw',
        height: '100vh',
        display: 'block',
        background: '#0d1117',
        cursor: 'pointer',
      }}
    />
  );
}

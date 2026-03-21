'use client';

import { useRef, useEffect, useState, useCallback } from 'react';
import Link from 'next/link';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface HeroArcsData {
  arcs: [number, number, number, number, number, 'w' | 'e'][]; // [s_lon, s_lat, r_lon, r_lat, decade, region]
  eras: { start: number; end: number; count: number }[];
}

interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: {
    type: 'Feature';
    geometry: {
      type: string;
      coordinates: number[][][] | number[][][][];
    };
  }[];
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

// Geographic bounds (Mediterranean region)
const GEO_BOUNDS = { minLon: -12, maxLon: 48, minLat: 22, maxLat: 58 };

// Animation phases (seconds)
const PHASE_BUILD = 2;
const PHASE_PEAK = 0.5;
const PHASE_FRAGMENT = 2;
const PHASE_TEXT = 0.5;
const TOTAL_DURATION = PHASE_BUILD + PHASE_PEAK + PHASE_FRAGMENT + PHASE_TEXT;

/* ------------------------------------------------------------------ */
/*  Projection: lon/lat -> canvas pixels                               */
/* ------------------------------------------------------------------ */

// Center point: Rome
const CENTER_LON = 12.5;
const CENTER_LAT = 41.9;

// Pre-compute Mercator helpers
const toMercY = (lat: number) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360));
const MERC_MIN = toMercY(GEO_BOUNDS.minLat);
const MERC_MAX = toMercY(GEO_BOUNDS.maxLat);
const MERC_RANGE = MERC_MAX - MERC_MIN;
const LON_RANGE = GEO_BOUNDS.maxLon - GEO_BOUNDS.minLon;
// Natural aspect ratio of the geo bounds in Mercator
const GEO_ASPECT = (LON_RANGE * Math.PI / 180) / MERC_RANGE;

function project(
  lon: number,
  lat: number,
  width: number,
  height: number,
  padding: number,
): [number, number] {
  const drawW = width - padding * 2;
  const drawH = height - padding * 2;
  const screenAspect = drawW / drawH;

  // "Cover" strategy: fill whichever dimension is tighter, centered on Rome
  // On wide screens: fill width, center vertically
  // On tall screens (mobile): fill height, center horizontally on Rome
  let scale: number;
  if (screenAspect > GEO_ASPECT) {
    // Wide screen: fit to width
    scale = drawW / (LON_RANGE * Math.PI / 180);
  } else {
    // Tall screen (mobile): fit to height, edges will overflow
    scale = drawH / MERC_RANGE;
  }

  const mapW = scale * (LON_RANGE * Math.PI / 180);
  const mapH = scale * MERC_RANGE;

  // Center on Rome
  const centerMerc = toMercY(CENTER_LAT);
  const centerNormX = (CENTER_LON - GEO_BOUNDS.minLon) / LON_RANGE;
  const centerNormY = 1 - (centerMerc - MERC_MIN) / MERC_RANGE;

  // Offset so Rome is at center of viewport
  const offsetX = padding + drawW / 2 - centerNormX * mapW;
  const offsetY = padding + drawH / 2 - centerNormY * mapH;

  const normX = (lon - GEO_BOUNDS.minLon) / LON_RANGE;
  const mercY = toMercY(lat);
  const normY = 1 - (mercY - MERC_MIN) / MERC_RANGE;

  return [offsetX + normX * mapW, offsetY + normY * mapH];
}

/* ------------------------------------------------------------------ */
/*  Pre-compute arc bezier paths                                       */
/* ------------------------------------------------------------------ */

interface ComputedArc {
  sx: number;
  sy: number;
  rx: number;
  ry: number;
  cx: number;
  cy: number;
  era: number;
  region: 'w' | 'e';
  fadeGroup: number; // 0-1, used for staggered west fade (based on longitude)
}

function computeArcs(
  arcs: HeroArcsData['arcs'],
  width: number,
  height: number,
  padding: number,
): ComputedArc[] {
  return arcs.map((a) => {
    const [sLon, sLat, rLon, rLat, era, region] = a;
    const [sx, sy] = project(sLon, sLat, width, height, padding);
    const [rx, ry] = project(rLon, rLat, width, height, padding);

    // Bezier control point: perpendicular to midpoint
    const mx = (sx + rx) / 2;
    const my = (sy + ry) / 2;
    const dx = rx - sx;
    const dy = ry - sy;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const offset = Math.min(dist * 0.2, 40);
    // Perpendicular direction (rotate 90 degrees, always curve upward)
    const nx = -dy / (dist || 1);
    const ny = dx / (dist || 1);
    const cx = mx + nx * offset * (ny > 0 ? -1 : 1);
    const cy = my - Math.abs(offset);

    // Fade group for western arcs: 0 = farthest west (fades first), 1 = near east border
    const avgLon = (sLon + rLon) / 2;
    const fadeGroup = region === 'w' ? Math.max(0, Math.min(1, (avgLon + 12) / 37)) : 1;

    return { sx, sy, rx, ry, cx, cy, era, region, fadeGroup };
  });
}

/* ------------------------------------------------------------------ */
/*  Draw functions                                                     */
/* ------------------------------------------------------------------ */

function drawCoastline(
  ctx: CanvasRenderingContext2D,
  outline: GeoJSONFeatureCollection,
  width: number,
  height: number,
  padding: number,
  fillColor: string,
  strokeColor: string,
) {
  ctx.beginPath();

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
      const [x0, y0] = project(ring[0][0], ring[0][1], width, height, padding);
      ctx.moveTo(x0, y0);
      for (let i = 1; i < ring.length; i++) {
        const [x, y] = project(ring[i][0], ring[i][1], width, height, padding);
        ctx.lineTo(x, y);
      }
      ctx.closePath();
    }
  }

  ctx.fillStyle = fillColor;
  ctx.fill();
  ctx.strokeStyle = strokeColor;
  ctx.lineWidth = 0.8;
  ctx.stroke();
}

function drawArcs(
  ctx: CanvasRenderingContext2D,
  arcs: ComputedArc[],
  t: number, // 0 to TOTAL_DURATION
  accentColor: string,
) {
  ctx.lineWidth = 0.8;
  ctx.lineCap = 'round';

  for (const arc of arcs) {
    let opacity = 0;

    if (t < PHASE_BUILD) {
      // Phase 1: Build - arcs appear by era
      const buildProgress = t / PHASE_BUILD;
      // Normalize era to 0-1 range
      const eraProgress = (arc.era - 200) / 400; // 200-600 range
      if (buildProgress > eraProgress) {
        // Fade in over 0.15 of the build phase
        const fadeIn = Math.min(1, (buildProgress - eraProgress) / 0.15);
        opacity = fadeIn * 0.55;
      }
    } else if (t < PHASE_BUILD + PHASE_PEAK) {
      // Phase 2: Peak - all visible, gentle pulse
      const peakT = (t - PHASE_BUILD) / PHASE_PEAK;
      opacity = 0.5 + 0.1 * Math.sin(peakT * Math.PI * 2);
    } else if (t < PHASE_BUILD + PHASE_PEAK + PHASE_FRAGMENT) {
      // Phase 3: Fragment - west fades, east stays
      const fragProgress = (t - PHASE_BUILD - PHASE_PEAK) / PHASE_FRAGMENT;

      if (arc.region === 'w') {
        // Western arcs fade based on their fadeGroup (longitude)
        // fadeGroup 0 = farthest west, fades first
        const fadeStart = arc.fadeGroup * 0.5; // stagger: 0-0.5 of fragment phase
        if (fragProgress > fadeStart) {
          const fadeOut = Math.max(0, 1 - (fragProgress - fadeStart) / 0.4);
          opacity = fadeOut * 0.55;
        } else {
          opacity = 0.55;
        }
      } else {
        // Eastern arcs stay visible
        opacity = 0.55;
      }
    } else {
      // Phase 4: Text - dim everything
      const textProgress = (t - PHASE_BUILD - PHASE_PEAK - PHASE_FRAGMENT) / PHASE_TEXT;
      if (arc.region === 'e') {
        opacity = 0.55 * (1 - textProgress * 0.7); // dim to 0.15
      } else {
        opacity = 0; // western already gone
      }
    }

    if (opacity < 0.01) continue;

    ctx.strokeStyle = accentColor;
    ctx.globalAlpha = opacity;
    ctx.beginPath();
    ctx.moveTo(arc.sx, arc.sy);
    ctx.quadraticCurveTo(arc.cx, arc.cy, arc.rx, arc.ry);
    ctx.stroke();
  }

  ctx.globalAlpha = 1;
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function HeroAnimation() {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loaded, setLoaded] = useState(false);
  const [showText, setShowText] = useState(false);
  const dataRef = useRef<{
    outline: GeoJSONFeatureCollection;
    arcsData: HeroArcsData;
  } | null>(null);
  const animRef = useRef<number>(0);
  const startTimeRef = useRef<number>(0);

  // Load data
  useEffect(() => {
    Promise.all([
      fetch('/data/mediterranean-outline.json').then((r) => r.json()),
      fetch('/data/hero-arcs.json').then((r) => r.json()),
    ])
      .then(([outline, arcsData]) => {
        dataRef.current = { outline, arcsData };
        setLoaded(true);
      })
      .catch(console.error);
  }, []);

  // Get theme colors
  const getColors = useCallback(() => {
    const styles = window.getComputedStyle(document.documentElement);
    return {
      accent: styles.getPropertyValue('--color-accent').trim() || '#b45a3c',
      surface: styles.getPropertyValue('--color-surface').trim() || '#faf8f5',
      border: styles.getPropertyValue('--color-border').trim() || '#d4c5b5',
    };
  }, []);

  // Animation loop
  useEffect(() => {
    if (!loaded || !canvasRef.current || !containerRef.current || !dataRef.current) return;

    const canvas = canvasRef.current;
    const container = containerRef.current;
    const { outline, arcsData } = dataRef.current;
    const colors = getColors();

    const dpr = window.devicePixelRatio || 1;
    let width = container.clientWidth;
    let height = container.clientHeight;
    let computedArcs: ComputedArc[] = [];
    const padding = Math.min(width, height) * 0.05;

    function resize() {
      width = container.clientWidth;
      height = container.clientHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      computedArcs = computeArcs(arcsData.arcs, width, height, padding);
    }

    resize();

    const observer = new ResizeObserver(() => {
      resize();
    });
    observer.observe(container);

    startTimeRef.current = performance.now();
    let hasShownText = false;

    function frame(now: number) {
      const elapsed = (now - startTimeRef.current) / 1000;
      const t = Math.min(elapsed, TOTAL_DURATION);

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, width, height);

      // Draw coastline
      const coastFill = colors.border + '50'; // ~31% opacity
      const coastStroke = colors.border + '80'; // ~50% opacity
      drawCoastline(ctx, outline, width, height, padding, coastFill, coastStroke);

      // Draw arcs
      drawArcs(ctx, computedArcs, t, colors.accent);

      // Trigger text fade-in
      if (t >= PHASE_BUILD + PHASE_PEAK + PHASE_FRAGMENT && !hasShownText) {
        hasShownText = true;
        setShowText(true);
      }

      if (t < TOTAL_DURATION) {
        animRef.current = requestAnimationFrame(frame);
      }
    }

    animRef.current = requestAnimationFrame(frame);

    return () => {
      cancelAnimationFrame(animRef.current);
      observer.disconnect();
    };
  }, [loaded, getColors]);

  return (
    <section
      ref={containerRef}
      className="relative w-full overflow-hidden"
      style={{
        height: '100vh',
        minHeight: '500px',
        maxHeight: '900px',
        backgroundColor: 'var(--color-surface)',
      }}
    >
      <canvas
        ref={canvasRef}
        className="absolute inset-0"
        style={{ width: '100%', height: '100%' }}
      />

      {/* Text overlay */}
      <div
        className={`absolute inset-0 flex flex-col items-center justify-center text-center px-6 z-10
          transition-opacity duration-1000 ${showText ? 'opacity-100' : 'opacity-0'}`}
      >
        <h1
          className="text-4xl sm:text-5xl md:text-6xl tracking-tight text-theme-text"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          7,049 letters from the late Roman world.
        </h1>
        <p className="mt-4 text-base sm:text-lg text-theme-muted max-w-xl">
          The largest collection of late Roman letters ever assembled in English.
        </p>
        <Link
          href="/letters/"
          className="mt-8 inline-flex items-center px-6 py-3 rounded-lg text-sm font-medium
            text-white transition-colors hover:opacity-90"
          style={{ backgroundColor: 'var(--color-accent)' }}
        >
          Explore the letters
        </Link>
      </div>

      {/* Scroll indicator */}
      <div
        className={`absolute bottom-8 left-1/2 -translate-x-1/2 z-10
          transition-opacity duration-1000 ${showText ? 'opacity-60' : 'opacity-0'}`}
      >
        <div className="flex flex-col items-center gap-2 text-theme-muted">
          <span className="text-xs tracking-wide">Scroll to explore</span>
          <svg
            className="w-4 h-4 animate-bounce"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 14l-7 7m0 0l-7-7" />
          </svg>
        </div>
      </div>
    </section>
  );
}

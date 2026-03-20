#!/usr/bin/env node
/**
 * generate-hero-data.js
 *
 * Generates two files for the hero/landing page visualization:
 *   1. public/data/mediterranean-outline.json  — clipped Natural Earth land polygons
 *   2. public/data/hero-arcs.json              — sampled letter arcs with era buckets
 *
 * Usage:  cd site && node scripts/generate-hero-data.js
 *
 * Prerequisites:
 *   - /tmp/ne_50m_land.geojson  (Natural Earth 50m land polygons)
 *   - public/data/map-letters.json (pre-generated letter data)
 */

const fs = require('fs');
const path = require('path');

const OUT_DIR = path.join(__dirname, '..', 'public', 'data');

// ─── File 1: Mediterranean outline ──────────────────────────────────────────

function generateMediterraneanOutline() {
  const SRC = '/tmp/ne_50m_land.geojson';
  const OUT = path.join(OUT_DIR, 'mediterranean-outline.json');

  const BBOX = { minLon: -15, minLat: 20, maxLon: 50, maxLat: 60 };

  console.log('Reading', SRC, '…');
  const raw = JSON.parse(fs.readFileSync(SRC, 'utf8'));

  function coordInBbox([lon, lat]) {
    return (
      lon >= BBOX.minLon &&
      lon <= BBOX.maxLon &&
      lat >= BBOX.minLat &&
      lat <= BBOX.maxLat
    );
  }

  function anyCoordInBbox(coords) {
    // coords can be nested arrays (rings, multi-polygons)
    if (typeof coords[0] === 'number') {
      return coordInBbox(coords);
    }
    return coords.some((c) => anyCoordInBbox(c));
  }

  function clampCoord([lon, lat]) {
    return [
      Math.round(Math.max(BBOX.minLon, Math.min(BBOX.maxLon, lon)) * 100) / 100,
      Math.round(Math.max(BBOX.minLat, Math.min(BBOX.maxLat, lat)) * 100) / 100,
    ];
  }

  function roundCoords(coords) {
    if (typeof coords[0] === 'number') {
      return [
        Math.round(coords[0] * 100) / 100,
        Math.round(coords[1] * 100) / 100,
      ];
    }
    return coords.map((c) => roundCoords(c));
  }

  // Douglas-Peucker line simplification
  function perpDist(pt, a, b) {
    const dx = b[0] - a[0], dy = b[1] - a[1];
    const lenSq = dx * dx + dy * dy;
    if (lenSq === 0) return Math.hypot(pt[0] - a[0], pt[1] - a[1]);
    const t = Math.max(0, Math.min(1, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / lenSq));
    return Math.hypot(pt[0] - (a[0] + t * dx), pt[1] - (a[1] + t * dy));
  }

  function simplify(ring, tolerance) {
    if (ring.length <= 4) return ring;
    let maxDist = 0, maxIdx = 0;
    for (let i = 1; i < ring.length - 1; i++) {
      const d = perpDist(ring[i], ring[0], ring[ring.length - 1]);
      if (d > maxDist) { maxDist = d; maxIdx = i; }
    }
    if (maxDist > tolerance) {
      const left = simplify(ring.slice(0, maxIdx + 1), tolerance);
      const right = simplify(ring.slice(maxIdx), tolerance);
      return left.slice(0, -1).concat(right);
    }
    return [ring[0], ring[ring.length - 1]];
  }

  const SIMPLIFY_TOL = 0.08; // degrees (~8-9 km)

  // Clamp ring coordinates to bbox, simplify, and deduplicate
  function clipRing(ring) {
    const clamped = ring.map(clampCoord);
    // Remove consecutive duplicates
    const deduped = [clamped[0]];
    for (let i = 1; i < clamped.length; i++) {
      if (clamped[i][0] !== deduped[deduped.length - 1][0] ||
          clamped[i][1] !== deduped[deduped.length - 1][1]) {
        deduped.push(clamped[i]);
      }
    }
    if (deduped.length < 4) return null;
    // Simplify
    const simplified = simplify(deduped, SIMPLIFY_TOL);
    if (simplified.length < 4) return null;
    return simplified;
  }

  function clipPolygonCoords(rings) {
    const clipped = rings.map(clipRing).filter(Boolean);
    return clipped.length > 0 ? clipped : null;
  }

  const filtered = raw.features.filter((f) =>
    anyCoordInBbox(f.geometry.coordinates)
  );

  const cleaned = [];
  for (const f of filtered) {
    if (f.geometry.type === 'Polygon') {
      const coords = clipPolygonCoords(f.geometry.coordinates);
      if (coords) {
        cleaned.push({ type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: coords } });
      }
    } else if (f.geometry.type === 'MultiPolygon') {
      const polys = f.geometry.coordinates.map(clipPolygonCoords).filter(Boolean);
      if (polys.length > 0) {
        cleaned.push({ type: 'Feature', properties: {}, geometry: { type: 'MultiPolygon', coordinates: polys } });
      }
    } else {
      cleaned.push({ type: 'Feature', properties: {}, geometry: { type: f.geometry.type, coordinates: roundCoords(f.geometry.coordinates) } });
    }
  }

  const out = { type: 'FeatureCollection', features: cleaned };
  const json = JSON.stringify(out);
  fs.writeFileSync(OUT, json);

  const sizeKB = (Buffer.byteLength(json) / 1024).toFixed(1);
  console.log(`✓ ${OUT}  (${sizeKB} KB, ${cleaned.length} features)`);
}

// ─── File 2: Hero arcs ─────────────────────────────────────────────────────

function generateHeroArcs() {
  const MAP_LETTERS_PATH = path.resolve(
    __dirname,
    '../public/data/map-letters.json'
  );
  const OUT = path.join(OUT_DIR, 'hero-arcs.json');
  const TARGET_ARCS = 500;
  const ERA_SIZE = 50;

  console.log('Reading', MAP_LETTERS_PATH, '…');
  const { letters } = JSON.parse(fs.readFileSync(MAP_LETTERS_PATH, 'utf8'));

  // Filter to letters with valid coordinates and year
  const valid = letters.filter(
    (l) =>
      l.s_lat && l.s_lon && l.r_lat && l.r_lon &&
      l.s_lat !== 0 && l.s_lon !== 0 && l.r_lat !== 0 && l.r_lon !== 0 &&
      l.year_approx != null
  );

  // Sort by year
  valid.sort((a, b) => a.year_approx - b.year_approx);

  // Sample evenly to ~TARGET_ARCS
  const step = Math.max(1, Math.floor(valid.length / TARGET_ARCS));
  const sampled = [];
  for (let i = 0; i < valid.length; i += step) {
    sampled.push(valid[i]);
    if (sampled.length >= TARGET_ARCS) break;
  }

  // Build arcs and era buckets
  const eraCounts = {};

  const arcs = sampled.map((l) => {
    const sLon = Math.round(l.s_lon * 100) / 100;
    const sLat = Math.round(l.s_lat * 100) / 100;
    const rLon = Math.round(l.r_lon * 100) / 100;
    const rLat = Math.round(l.r_lat * 100) / 100;
    const avgLon = (sLon + rLon) / 2;
    const region = avgLon < 25 ? 'w' : 'e';

    const eraStart = Math.floor(l.year_approx / ERA_SIZE) * ERA_SIZE;
    const eraKey = `${eraStart}`;
    eraCounts[eraKey] = (eraCounts[eraKey] || 0) + 1;

    // decade_bucket for finer grouping within the arc data
    const decadeBucket = Math.floor(l.year_approx / 10) * 10;

    return [sLon, sLat, rLon, rLat, decadeBucket, region];
  });

  const eras = Object.keys(eraCounts)
    .map(Number)
    .sort((a, b) => a - b)
    .map((start) => ({
      start,
      end: start + ERA_SIZE - 1,
      count: eraCounts[String(start)],
    }));

  const out = { arcs, eras };
  const json = JSON.stringify(out);
  fs.writeFileSync(OUT, json);

  const sizeKB = (Buffer.byteLength(json) / 1024).toFixed(1);
  console.log(
    `✓ ${OUT}  (${sizeKB} KB, ${arcs.length} arcs, ${eras.length} eras)`
  );
}

// ─── Main ───────────────────────────────────────────────────────────────────

generateMediterraneanOutline();
generateHeroArcs();
console.log('Done.');

#!/usr/bin/env node
/**
 * Renders a high-quality static PNG showing Roman road heatmap across 5 eras.
 * Uses node-canvas for server-side rendering.
 *
 * Output: /tmp/roman-heatmap-comparison.png
 */

const { createCanvas } = require('canvas');
const fs = require('fs');
const path = require('path');

// ── Configuration ────────────────────────────────────────────────────
const WIDTH = 2400;
const HEIGHT = 700;
const TITLE_H = 60;
const BOTTOM_H = 50;
const GAP = 8;
const NUM_PANELS = 5;
const PANEL_W = Math.floor((WIDTH - GAP * (NUM_PANELS + 1)) / NUM_PANELS);
const PANEL_H = HEIGHT - TITLE_H - BOTTOM_H;
const BG = '#0d1117';

const BBOX = { minLon: -12, maxLon: 48, minLat: 22, maxLat: 58 };

const ERAS = [
  { start: 350, label: '350-399 AD', avgDist: '1,864 km', subtitle: 'Peak Empire' },
  { start: 400, label: '400-449 AD', avgDist: '1,636 km', subtitle: 'First Cracks' },
  { start: 450, label: '450-499 AD', avgDist: '1,472 km', subtitle: 'Fragmentation' },
  { start: 500, label: '500-549 AD', avgDist: '1,171 km', subtitle: 'New Kingdoms' },
  { start: 550, label: '550-599 AD', avgDist: '1,075 km', subtitle: "Gregory's Rome" },
];

// ── Load data ────────────────────────────────────────────────────────
const dataDir = path.join(__dirname, '..', 'site', 'public', 'data');
const coastline = JSON.parse(fs.readFileSync(path.join(dataDir, 'mediterranean-outline.json'), 'utf8'));
const roads = JSON.parse(fs.readFileSync(path.join(dataDir, 'roman-roads.json'), 'utf8'));
const heatmap = JSON.parse(fs.readFileSync(path.join(dataDir, 'road-heatmap.json'), 'utf8'));

// ── Mercator projection (matches RoadHeatmap.tsx) ────────────────────
function projectMercator(lon, lat, w, h) {
  const x = ((lon - BBOX.minLon) / (BBOX.maxLon - BBOX.minLon)) * w;
  const latRad = (lat * Math.PI) / 180;
  const minLatRad = (BBOX.minLat * Math.PI) / 180;
  const maxLatRad = (BBOX.maxLat * Math.PI) / 180;
  const yMerc = Math.log(Math.tan(Math.PI / 4 + latRad / 2));
  const yMin = Math.log(Math.tan(Math.PI / 4 + minLatRad / 2));
  const yMax = Math.log(Math.tan(Math.PI / 4 + maxLatRad / 2));
  const y = h - ((yMerc - yMin) / (yMax - yMin)) * h;
  return [x, y];
}

// ── Distance-based color (matches component) ────────────────────────
function distanceColor(avgDist) {
  if (avgDist <= 0) return 'rgba(80,80,80,0.15)';
  const t = Math.min(avgDist / 2000, 1);
  let r, g, b;
  if (t < 0.2) {
    const s = t / 0.2;
    r = 40 + s * 40;
    g = 160 + s * 40;
    b = 220 - s * 40;
  } else if (t < 0.5) {
    const s = (t - 0.2) / 0.3;
    r = 80 + s * 175;
    g = 200 - s * 80;
    b = 180 - s * 140;
  } else {
    const s = (t - 0.5) / 0.5;
    r = 255;
    g = 120 - s * 50;
    b = 40 - s * 30;
  }
  const alpha = 0.5 + t * 0.5;
  return `rgba(${Math.round(r)},${Math.round(g)},${Math.round(b)},${alpha.toFixed(2)})`;
}

function distanceWidth(avgDist) {
  if (avgDist <= 0) return 0.3;
  const t = Math.min(avgDist / heatmap.maxAvgDist, 1);
  return 0.5 + t * 3;
}

// ── Create canvas ────────────────────────────────────────────────────
const canvas = createCanvas(WIDTH, HEIGHT);
const ctx = canvas.getContext('2d');

// Fill background
ctx.fillStyle = BG;
ctx.fillRect(0, 0, WIDTH, HEIGHT);

// ── Title bar ────────────────────────────────────────────────────────
ctx.textAlign = 'center';
ctx.fillStyle = '#e6edf3';
ctx.font = 'bold 26px "Georgia", "Times New Roman", serif';
ctx.fillText('The Shrinking World', WIDTH / 2, 28);

ctx.fillStyle = '#8b949e';
ctx.font = '14px "Helvetica", "Arial", sans-serif';
ctx.fillText('How Roman letter networks contracted 350\u2013600 AD', WIDTH / 2, 48);

// ── Draw each panel ──────────────────────────────────────────────────
for (let p = 0; p < NUM_PANELS; p++) {
  const era = ERAS[p];
  const eraKey = String(era.start).slice(0, 2) + '0'; // "350" -> "350", but heatmap uses decades
  // Heatmap keys use century-start: "350", "400", "450", "500", "550"
  const hKey = String(era.start);

  const panelX = GAP + p * (PANEL_W + GAP);
  const panelY = TITLE_H;

  // Save state and clip to panel
  ctx.save();
  ctx.beginPath();
  ctx.rect(panelX, panelY, PANEL_W, PANEL_H);
  ctx.clip();

  // Panel background - slightly lighter than main
  ctx.fillStyle = '#0f1419';
  ctx.fillRect(panelX, panelY, PANEL_W, PANEL_H);

  // ── Draw coastline ──────────────────────────────────────────────
  ctx.fillStyle = 'rgba(30, 40, 55, 0.7)';
  ctx.strokeStyle = 'rgba(48, 64, 80, 0.5)';
  ctx.lineWidth = 0.5;

  for (const feature of coastline.features) {
    if (feature.geometry.type === 'Polygon') {
      for (const ring of feature.geometry.coordinates) {
        const [x0, y0] = projectMercator(ring[0][0], ring[0][1], PANEL_W, PANEL_H);
        ctx.beginPath();
        ctx.moveTo(panelX + x0, panelY + y0);
        for (let i = 1; i < ring.length; i++) {
          const [x, y] = projectMercator(ring[i][0], ring[i][1], PANEL_W, PANEL_H);
          ctx.lineTo(panelX + x, panelY + y);
        }
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      }
    }
  }

  // ── Draw all roads as faint lines ───────────────────────────────
  ctx.strokeStyle = 'rgba(60, 70, 85, 0.25)';
  ctx.lineWidth = 0.3;

  for (const feature of roads.features) {
    const multiLine = feature.geometry.coordinates;
    for (const line of multiLine) {
      if (line.length < 2) continue;
      const [x0, y0] = projectMercator(line[0][0], line[0][1], PANEL_W, PANEL_H);
      ctx.beginPath();
      ctx.moveTo(panelX + x0, panelY + y0);
      for (let j = 1; j < line.length; j++) {
        const [x, y] = projectMercator(line[j][0], line[j][1], PANEL_W, PANEL_H);
        ctx.lineTo(panelX + x, panelY + y);
      }
      ctx.stroke();
    }
  }

  // ── Draw heatmap segments ───────────────────────────────────────
  const segments = heatmap.segments;
  for (const segId of Object.keys(segments)) {
    const segData = segments[segId];
    const eraData = segData[hKey];
    if (!eraData || eraData.count < 3) continue;

    const featureIdx = parseInt(segId, 10);
    if (featureIdx >= roads.features.length) continue;

    const feature = roads.features[featureIdx];
    const multiLine = feature.geometry.coordinates;

    ctx.strokeStyle = distanceColor(eraData.avgDist);
    ctx.lineWidth = distanceWidth(eraData.avgDist);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    for (const line of multiLine) {
      if (line.length < 2) continue;
      const [x0, y0] = projectMercator(line[0][0], line[0][1], PANEL_W, PANEL_H);
      ctx.beginPath();
      ctx.moveTo(panelX + x0, panelY + y0);
      for (let j = 1; j < line.length; j++) {
        const [x, y] = projectMercator(line[j][0], line[j][1], PANEL_W, PANEL_H);
        ctx.lineTo(panelX + x, panelY + y);
      }
      ctx.stroke();
    }
  }

  // ── Draw sea lanes with traffic ────────────────────────────────
  if (heatmap.seaLanes && heatmap.seaLaneCoords) {
    // Background sea lanes (faint dashed)
    ctx.save();
    ctx.setLineDash([4, 6]);
    ctx.strokeStyle = 'rgba(60, 80, 120, 0.15)';
    ctx.lineWidth = 0.5;
    for (const coords of Object.values(heatmap.seaLaneCoords)) {
      if (coords.length < 2) continue;
      const [x0, y0] = projectMercator(coords[0][0], coords[0][1], PANEL_W, PANEL_H);
      ctx.beginPath();
      ctx.moveTo(panelX + x0, panelY + y0);
      for (let j = 1; j < coords.length; j++) {
        const [x, y] = projectMercator(coords[j][0], coords[j][1], PANEL_W, PANEL_H);
        ctx.lineTo(panelX + x, panelY + y);
      }
      ctx.stroke();
    }
    ctx.restore();

    // Traffic sea lanes (colored dashed)
    ctx.save();
    ctx.setLineDash([6, 4]);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    const maxSea = Math.max(heatmap.maxSeaTraffic || 1, 1);
    for (const [connIdx, eras] of Object.entries(heatmap.seaLanes)) {
      const d = eras[hKey];
      if (!d || d.count < 2) continue;
      const coords = heatmap.seaLaneCoords[connIdx];
      if (!coords || coords.length < 2) continue;
      ctx.strokeStyle = distanceColor(d.avgDist);
      ctx.lineWidth = 1 + Math.min(d.count / maxSea, 1) * 3;
      const [x0, y0] = projectMercator(coords[0][0], coords[0][1], PANEL_W, PANEL_H);
      ctx.beginPath();
      ctx.moveTo(panelX + x0, panelY + y0);
      for (let j = 1; j < coords.length; j++) {
        const [x, y] = projectMercator(coords[j][0], coords[j][1], PANEL_W, PANEL_H);
        ctx.lineTo(panelX + x, panelY + y);
      }
      ctx.stroke();
    }
    ctx.restore();
  }

  ctx.restore();

  // ── Panel labels ────────────────────────────────────────────────
  const labelX = panelX + PANEL_W / 2;
  const labelY = panelY + PANEL_H + 14;

  ctx.textAlign = 'center';
  ctx.fillStyle = '#e6edf3';
  ctx.font = 'bold 14px "Helvetica", "Arial", sans-serif';
  ctx.fillText(era.label, labelX, labelY);

  ctx.fillStyle = '#58a6ff';
  ctx.font = '12px "Helvetica", "Arial", sans-serif';
  ctx.fillText(`Avg: ${era.avgDist}`, labelX, labelY + 16);

  ctx.fillStyle = '#8b949e';
  ctx.font = 'italic 11px "Georgia", "Times New Roman", serif';
  ctx.fillText(era.subtitle, labelX, labelY + 30);
}

// ── Attribution ──────────────────────────────────────────────────────
ctx.textAlign = 'right';
ctx.fillStyle = '#484f58';
ctx.font = '11px "Helvetica", "Arial", sans-serif';
ctx.fillText('romanletters.org', WIDTH - 16, HEIGHT - 8);

// ── Color legend ─────────────────────────────────────────────────────
const legendX = 16;
const legendY = HEIGHT - 14;
ctx.textAlign = 'left';
ctx.fillStyle = '#8b949e';
ctx.font = '10px "Helvetica", "Arial", sans-serif';

// Draw color swatches
const swatches = [
  { dist: 200, label: '<400 km' },
  { dist: 800, label: '400-1200 km' },
  { dist: 1600, label: '>1200 km' },
];
let swX = legendX;
for (const sw of swatches) {
  ctx.fillStyle = distanceColor(sw.dist);
  ctx.fillRect(swX, legendY - 6, 20, 8);
  ctx.fillStyle = '#8b949e';
  ctx.fillText(sw.label, swX + 24, legendY + 2);
  swX += 90;
}

ctx.fillStyle = '#6e7681';
ctx.fillText('Color = avg letter distance on road segment  |  Width = letter volume', swX + 10, legendY + 2);

// ── Save ─────────────────────────────────────────────────────────────
const outPath = '/tmp/roman-heatmap-comparison.png';
const buffer = canvas.toBuffer('image/png');
fs.writeFileSync(outPath, buffer);
console.log(`Saved ${(buffer.length / 1024).toFixed(0)} KB to ${outPath}`);

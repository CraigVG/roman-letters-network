#!/usr/bin/env node
/**
 * generate-road-heatmap.js
 *
 * Pre-computes road traffic heatmap data for the Roman Letters map.
 * For each era (50-year bucket), counts how many letters pass through each road segment.
 *
 * Usage: node site/scripts/generate-road-heatmap.js
 * Output: site/public/data/road-heatmap.json
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const ROADS_PATH = path.join(ROOT, 'public/data/roman-roads.json');
const LETTERS_PATH = path.join(ROOT, 'public/data/map-letters.json');
const OUTPUT_PATH = path.join(ROOT, 'public/data/road-heatmap.json');

const ERAS = [
  { label: '300-349 AD', start: 300, end: 349 },
  { label: '350-399 AD', start: 350, end: 399 },
  { label: '400-449 AD', start: 400, end: 449 },
  { label: '450-499 AD', start: 450, end: 499 },
  { label: '500-549 AD', start: 500, end: 549 },
  { label: '550-599 AD', start: 550, end: 599 },
];

// ── Utility ──────────────────────────────────────────────────────────────────

function distSq(lon1, lat1, lon2, lat2) {
  const dx = lon1 - lon2;
  const dy = lat1 - lat2;
  return dx * dx + dy * dy;
}

// ── Road network graph (mirrors RomanMap.tsx logic) ──────────────────────────

function buildRoadNetwork(geojson) {
  const nodeMap = new Map(); // "lon,lat" -> index
  const nodes = [];          // { lon, lat, edges: [{ neighbor, featureIdx }] }
  const gridSize = 0.5;
  const grid = new Map();

  function getOrCreateNode(lon, lat) {
    const key = `${lon.toFixed(3)},${lat.toFixed(3)}`;
    let idx = nodeMap.get(key);
    if (idx !== undefined) return idx;
    idx = nodes.length;
    nodeMap.set(key, idx);
    nodes.push({ lon, lat, edges: [] });
    const gx = Math.floor(lon / gridSize);
    const gy = Math.floor(lat / gridSize);
    const gKey = `${gx},${gy}`;
    const cell = grid.get(gKey);
    if (cell) cell.push(idx);
    else grid.set(gKey, [idx]);
    return idx;
  }

  for (let fi = 0; fi < geojson.features.length; fi++) {
    const feature = geojson.features[fi];
    const geom = feature.geometry;

    if (geom.type === 'MultiLineString') {
      for (const line of geom.coordinates) {
        for (let i = 0; i < line.length - 1; i++) {
          const a = getOrCreateNode(line[i][0], line[i][1]);
          const b = getOrCreateNode(line[i + 1][0], line[i + 1][1]);
          if (a !== b) {
            // Store edges with feature index, avoiding duplicates
            if (!nodes[a].edges.some(e => e.neighbor === b && e.featureIdx === fi)) {
              nodes[a].edges.push({ neighbor: b, featureIdx: fi });
            }
            if (!nodes[b].edges.some(e => e.neighbor === a && e.featureIdx === fi)) {
              nodes[b].edges.push({ neighbor: a, featureIdx: fi });
            }
          }
        }
      }
    } else {
      // LineString
      const coords = geom.coordinates;
      for (let i = 0; i < coords.length - 1; i++) {
        const a = getOrCreateNode(coords[i][0], coords[i][1]);
        const b = getOrCreateNode(coords[i + 1][0], coords[i + 1][1]);
        if (a !== b) {
          if (!nodes[a].edges.some(e => e.neighbor === b && e.featureIdx === fi)) {
            nodes[a].edges.push({ neighbor: b, featureIdx: fi });
          }
          if (!nodes[b].edges.some(e => e.neighbor === a && e.featureIdx === fi)) {
            nodes[b].edges.push({ neighbor: a, featureIdx: fi });
          }
        }
      }
    }
  }

  return { nodes, grid, gridSize, nodeMap };
}

// ── Connect disconnected components by adding bridge edges ──────────────────
// The Roman roads GeoJSON has ~900 disconnected components due to data gaps.
// This finds nearby endpoints between components and adds bridge edges so A*
// can route across the full network.

function connectComponents(net) {
  const { nodes } = net;
  const n = nodes.length;

  // Find connected components via BFS
  const comp = new Int32Array(n).fill(-1);
  let numComp = 0;
  const compNodes = []; // compId -> [nodeIdx, ...]
  for (let i = 0; i < n; i++) {
    if (comp[i] >= 0) continue;
    const id = numComp++;
    const members = [];
    const stack = [i];
    while (stack.length) {
      const cur = stack.pop();
      if (comp[cur] >= 0) continue;
      comp[cur] = id;
      members.push(cur);
      for (const e of nodes[cur].edges) {
        if (comp[e.neighbor] < 0) stack.push(e.neighbor);
      }
    }
    compNodes.push(members);
  }

  console.log(`  Connected components: ${numComp}`);
  if (numComp <= 1) return;

  // For each component, collect "boundary" nodes (degree-1 endpoints or just all nodes)
  // To bridge efficiently: use spatial grid to find nearest node in a *different* component
  const BRIDGE_THRESHOLD = 0.15; // ~0.15 degrees, roughly 15km — close enough for a bridge
  let bridgesAdded = 0;

  // Build a simple spatial index of all nodes by component
  const bridgeGrid = new Map();
  const bgSize = 0.2;
  for (let i = 0; i < n; i++) {
    const gx = Math.floor(nodes[i].lon / bgSize);
    const gy = Math.floor(nodes[i].lat / bgSize);
    const key = `${gx},${gy}`;
    if (!bridgeGrid.has(key)) bridgeGrid.set(key, []);
    bridgeGrid.get(key).push(i);
  }

  // For each component, find the nearest node in any other component
  // Use Union-Find to merge components as we add bridges
  const uf = new Int32Array(numComp);
  for (let i = 0; i < numComp; i++) uf[i] = i;
  function find(x) { while (uf[x] !== x) x = uf[x] = uf[uf[x]]; return x; }
  function union(a, b) { a = find(a); b = find(b); if (a !== b) uf[a] = b; }

  // For each node, check nearby nodes in different components
  const bridged = new Set(); // "compA-compB" pairs already bridged
  for (let i = 0; i < n; i++) {
    const ci = find(comp[i]);
    const gx = Math.floor(nodes[i].lon / bgSize);
    const gy = Math.floor(nodes[i].lat / bgSize);

    for (let dx = -1; dx <= 1; dx++) {
      for (let dy = -1; dy <= 1; dy++) {
        const cell = bridgeGrid.get(`${gx + dx},${gy + dy}`);
        if (!cell) continue;
        for (const j of cell) {
          const cj = find(comp[j]);
          if (ci === cj) continue;
          const pairKey = ci < cj ? `${ci}-${cj}` : `${cj}-${ci}`;
          if (bridged.has(pairKey)) continue;

          const d = distSq(nodes[i].lon, nodes[i].lat, nodes[j].lon, nodes[j].lat);
          if (d < BRIDGE_THRESHOLD * BRIDGE_THRESHOLD) {
            // Add bridge edge (featureIdx = -1, meaning no real feature)
            nodes[i].edges.push({ neighbor: j, featureIdx: -1 });
            nodes[j].edges.push({ neighbor: i, featureIdx: -1 });
            union(ci, cj);
            bridged.add(pairKey);
            bridgesAdded++;
          }
        }
      }
    }
  }

  console.log(`  Bridge edges added: ${bridgesAdded}`);

  // Count remaining components
  const remaining = new Set();
  for (let i = 0; i < numComp; i++) remaining.add(find(i));
  console.log(`  Components after bridging: ${remaining.size}`);
}

// ── Nearest node (expanding grid search) ────────────────────────────────────

function findNearestNode(net, lon, lat, maxDist = 3.0) {
  const gx = Math.floor(lon / net.gridSize);
  const gy = Math.floor(lat / net.gridSize);

  let bestIdx = null;
  let bestDist = maxDist * maxDist;

  for (let ring = 1; ring <= 3; ring++) {
    for (let dx = -ring; dx <= ring; dx++) {
      for (let dy = -ring; dy <= ring; dy++) {
        const cell = net.grid.get(`${gx + dx},${gy + dy}`);
        if (!cell) continue;
        for (const idx of cell) {
          const d = distSq(lon, lat, net.nodes[idx].lon, net.nodes[idx].lat);
          if (d < bestDist) {
            bestDist = d;
            bestIdx = idx;
          }
        }
      }
    }
    if (bestIdx !== null) break;
  }
  return bestIdx;
}

// ── Binary min-heap for A* ──────────────────────────────────────────────────

class MinHeap {
  constructor() { this.data = []; }
  push(item) {
    this.data.push(item);
    this._siftUp(this.data.length - 1);
  }
  pop() {
    const top = this.data[0];
    const last = this.data.pop();
    if (this.data.length > 0) {
      this.data[0] = last;
      this._siftDown(0);
    }
    return top;
  }
  get length() { return this.data.length; }
  _siftUp(i) {
    const d = this.data;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (d[p][0] <= d[i][0]) break;
      [d[p], d[i]] = [d[i], d[p]];
      i = p;
    }
  }
  _siftDown(i) {
    const d = this.data;
    const n = d.length;
    while (true) {
      let smallest = i;
      const l = 2 * i + 1, r = 2 * i + 2;
      if (l < n && d[l][0] < d[smallest][0]) smallest = l;
      if (r < n && d[r][0] < d[smallest][0]) smallest = r;
      if (smallest === i) break;
      [d[smallest], d[i]] = [d[i], d[smallest]];
      i = smallest;
    }
  }
}

// ── A* pathfinding returning feature indices along the path ─────────────────

function findRoadPathFeatures(net, startIdx, endIdx, maxSteps = 200000) {
  if (startIdx === endIdx) return [];

  const endNode = net.nodes[endIdx];
  const parent = new Map();       // nodeIdx -> { from: nodeIdx, featureIdx }
  const gScore = new Map();
  gScore.set(startIdx, 0);

  const open = new MinHeap();
  open.push([distSq(net.nodes[startIdx].lon, net.nodes[startIdx].lat, endNode.lon, endNode.lat), startIdx]);
  const inClosed = new Set();

  let steps = 0;
  while (open.length > 0 && steps < maxSteps) {
    const [, current] = open.pop();

    if (current === endIdx) {
      // Reconstruct path as list of feature indices
      const features = [];
      let node = endIdx;
      while (parent.has(node)) {
        const p = parent.get(node);
        features.push(p.featureIdx);
        node = p.from;
      }
      return features;
    }

    if (inClosed.has(current)) continue;
    inClosed.add(current);
    steps++;

    const currentG = gScore.get(current) ?? Infinity;
    const currentNode = net.nodes[current];

    for (const edge of currentNode.edges) {
      const { neighbor, featureIdx } = edge;
      if (inClosed.has(neighbor)) continue;

      const nNode = net.nodes[neighbor];
      const edgeCost = distSq(currentNode.lon, currentNode.lat, nNode.lon, nNode.lat);
      const tentativeG = currentG + edgeCost;

      const prevG = gScore.get(neighbor);
      if (prevG !== undefined && tentativeG >= prevG) continue;

      gScore.set(neighbor, tentativeG);
      parent.set(neighbor, { from: current, featureIdx });

      const h = distSq(nNode.lon, nNode.lat, endNode.lon, endNode.lat);
      open.push([tentativeG + h, neighbor]);
    }
  }
  return null; // No path found
}

// ── Era bucket lookup ───────────────────────────────────────────────────────

function getEraBucket(year) {
  for (const era of ERAS) {
    if (year >= era.start && year <= era.end) return era.start;
  }
  return null;
}

// ── Main ────────────────────────────────────────────────────────────────────

function main() {
  console.log('Loading data...');
  const roadsData = JSON.parse(fs.readFileSync(ROADS_PATH, 'utf-8'));
  const lettersData = JSON.parse(fs.readFileSync(LETTERS_PATH, 'utf-8'));

  console.log(`  Roads: ${roadsData.features.length} features`);
  console.log(`  Letters: ${lettersData.letters.length} total`);

  // Filter letters: need coords and a year that falls in one of our eras
  const letters = lettersData.letters.filter(l =>
    l.s_lat && l.s_lon && l.r_lat && l.r_lon && l.year_approx && getEraBucket(l.year_approx) !== null
  );
  console.log(`  Letters in era range (300-599): ${letters.length}`);

  console.log('Building road network graph...');
  const t0 = Date.now();
  const net = buildRoadNetwork(roadsData);
  console.log(`  ${net.nodes.length} nodes, built in ${Date.now() - t0}ms`);

  console.log('Connecting disconnected road segments...');
  connectComponents(net);

  // segments: { featureIdx: { eraStart: count } }
  const segments = {};
  let routed = 0;
  let noStart = 0;
  let noEnd = 0;
  let noPath = 0;

  console.log(`Routing ${letters.length} letters...`);
  const tRoute = Date.now();

  for (let i = 0; i < letters.length; i++) {
    const letter = letters[i];

    if (i > 0 && i % 100 === 0) {
      const pct = ((i / letters.length) * 100).toFixed(1);
      const elapsed = ((Date.now() - tRoute) / 1000).toFixed(1);
      console.log(`  [${pct}%] ${i}/${letters.length} letters processed (${elapsed}s elapsed)`);
    }

    const startNode = findNearestNode(net, letter.s_lon, letter.s_lat);
    if (startNode === null) { noStart++; continue; }

    const endNode = findNearestNode(net, letter.r_lon, letter.r_lat);
    if (endNode === null) { noEnd++; continue; }

    if (startNode === endNode) { routed++; continue; } // Same node, no road segments

    const pathFeatures = findRoadPathFeatures(net, startNode, endNode);
    if (pathFeatures === null) { noPath++; continue; }

    const era = getEraBucket(letter.year_approx);
    // Deduplicate features in a single path (a road feature can appear multiple times)
    // Skip bridge edges (featureIdx = -1) which connect disconnected components
    const seen = new Set();
    for (const fi of pathFeatures) {
      if (fi < 0 || seen.has(fi)) continue;
      seen.add(fi);
      if (!segments[fi]) segments[fi] = {};
      segments[fi][era] = (segments[fi][era] || 0) + 1;
    }
    routed++;
  }

  const routeTime = ((Date.now() - tRoute) / 1000).toFixed(1);
  console.log(`Routing complete in ${routeTime}s`);
  console.log(`  Routed: ${routed}`);
  console.log(`  No start node: ${noStart}`);
  console.log(`  No end node: ${noEnd}`);
  console.log(`  No path (A* exhausted): ${noPath}`);

  // Compute max traffic
  let maxTraffic = 0;
  let busiestFeature = null;
  let busiestEra = null;
  for (const [fi, eraCounts] of Object.entries(segments)) {
    for (const [era, count] of Object.entries(eraCounts)) {
      if (count > maxTraffic) {
        maxTraffic = count;
        busiestFeature = fi;
        busiestEra = era;
      }
    }
  }

  const segmentCount = Object.keys(segments).length;
  console.log(`\nStats:`);
  console.log(`  Segments with traffic: ${segmentCount} / ${roadsData.features.length}`);
  console.log(`  Max traffic: ${maxTraffic} (feature #${busiestFeature}, era ${busiestEra})`);

  // Per-era totals
  for (const era of ERAS) {
    let total = 0;
    for (const eraCounts of Object.values(segments)) {
      total += eraCounts[era.start] || 0;
    }
    console.log(`  ${era.label}: ${total} segment-traversals`);
  }

  // Build output
  const output = {
    eras: ERAS,
    segments,
    maxTraffic,
  };

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(output));
  const fileSize = fs.statSync(OUTPUT_PATH).size;
  console.log(`\nOutput: ${OUTPUT_PATH}`);
  console.log(`  File size: ${(fileSize / 1024).toFixed(1)} KB`);
  console.log('Done.');
}

main();

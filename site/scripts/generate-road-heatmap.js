#!/usr/bin/env node
/**
 * generate-road-heatmap.js
 *
 * Pre-computes road + sea traffic heatmap data for the Roman Letters map.
 * For each era (50-year bucket), counts how many letters pass through each road segment
 * and each sea lane, using hybrid road+sea routing (matching RomanMap.tsx logic).
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

// ── Port network (copied from RomanMap.tsx) ──────────────────────────────────

const PORTS = [
  { name: 'Ostia', lon: 12.29, lat: 41.76 },        // 0
  { name: 'Puteoli', lon: 14.12, lat: 40.82 },       // 1
  { name: 'Brundisium', lon: 17.94, lat: 40.64 },    // 2
  { name: 'Syracuse', lon: 15.29, lat: 37.07 },       // 3
  { name: 'Ravenna', lon: 12.20, lat: 44.42 },        // 4
  { name: 'Genoa', lon: 8.95, lat: 44.42 },           // 5
  { name: 'Massilia', lon: 5.38, lat: 43.30 },        // 6
  { name: 'Narbo', lon: 3.00, lat: 43.18 },           // 7
  { name: 'Tarraco', lon: 1.25, lat: 41.12 },         // 8
  { name: 'Carthage', lon: 10.18, lat: 36.81 },       // 9
  { name: 'Hippo', lon: 7.75, lat: 36.88 },           // 10
  { name: 'Leptis', lon: 14.29, lat: 32.64 },         // 11
  { name: 'Alexandria', lon: 29.92, lat: 31.20 },     // 12
  { name: 'Caesarea', lon: 34.89, lat: 32.50 },       // 13
  { name: 'Antioch', lon: 36.16, lat: 36.20 },        // 14
  { name: 'Constantinople', lon: 28.98, lat: 41.01 }, // 15
  { name: 'Thessalonica', lon: 22.94, lat: 40.64 },   // 16
  { name: 'Athens', lon: 23.65, lat: 37.94 },         // 17
  { name: 'Corinth', lon: 22.88, lat: 37.91 },        // 18
  { name: 'Ephesus', lon: 27.34, lat: 37.94 },        // 19
  { name: 'Smyrna', lon: 27.14, lat: 38.42 },         // 20
  { name: 'Cyrene', lon: 21.86, lat: 32.82 },         // 21
  { name: 'Seleucia', lon: 35.92, lat: 36.09 },       // 22
];

// Sea connections between ports - [portIndex1, portIndex2, waypoints]
const SEA_CONNECTIONS = [
  // Western Mediterranean
  [0, 3, [[13.5, 39.5], [14.5, 38.0]]],           // 0: Ostia - Syracuse
  [0, 9, [[12.0, 38.5]]],                          // 1: Ostia - Carthage
  [0, 5, [[10.5, 42.5]]],                          // 2: Ostia - Genoa
  [1, 3, [[14.5, 39.0]]],                          // 3: Puteoli - Syracuse
  [1, 9, [[13.0, 38.0], [11.5, 37.5]]],            // 4: Puteoli - Carthage
  [3, 9, [[13.0, 36.0]]],                          // 5: Syracuse - Carthage
  [5, 6, [[7.0, 43.5]]],                           // 6: Genoa - Massilia
  [6, 7, [[4.0, 43.0]]],                           // 7: Massilia - Narbo
  [7, 8, [[2.0, 42.0]]],                           // 8: Narbo - Tarraco
  [6, 9, [[5.0, 40.5], [7.0, 38.0]]],              // 9: Massilia - Carthage
  [9, 10, [[9.0, 36.8]]],                          // 10: Carthage - Hippo
  [10, 6, [[6.5, 38.5], [5.5, 41.0]]],             // 11: Hippo - Massilia (via Balearics)

  // Central Mediterranean
  [3, 12, [[18.0, 35.0], [24.0, 33.0]]],           // 12: Syracuse - Alexandria
  [9, 12, [[15.0, 34.0], [22.0, 32.5]]],           // 13: Carthage - Alexandria
  [9, 11, [[12.0, 34.5]]],                         // 14: Carthage - Leptis
  [11, 12, [[18.0, 32.0], [24.0, 31.5]]],          // 15: Leptis - Alexandria
  [11, 21, [[18.0, 32.5]]],                        // 16: Leptis - Cyrene
  [21, 12, [[25.0, 32.0]]],                        // 17: Cyrene - Alexandria

  // Eastern Mediterranean
  [12, 13, [[32.0, 31.5]]],                        // 18: Alexandria - Caesarea
  [13, 14, [[35.5, 34.0]]],                        // 19: Caesarea - Antioch/Seleucia
  [12, 14, [[32.0, 33.0], [34.5, 35.0]]],          // 20: Alexandria - Antioch
  [15, 12, [[27.0, 37.0], [30.0, 33.0]]],          // 21: Constantinople - Alexandria
  [15, 14, [[30.0, 38.0], [34.0, 36.5]]],          // 22: Constantinople - Antioch
  [15, 19, [[28.0, 39.5]]],                        // 23: Constantinople - Ephesus
  [19, 20, []],                                    // 24: Ephesus - Smyrna (very close, direct)
  [17, 18, []],                                    // 25: Athens - Corinth (close)
  [17, 19, [[25.5, 37.8]]],                        // 26: Athens - Ephesus
  [16, 15, [[25.0, 40.5]]],                        // 27: Thessalonica - Constantinople
  [16, 17, [[23.5, 39.0]]],                        // 28: Thessalonica - Athens

  // Adriatic
  [4, 15, [[16.0, 41.0], [20.0, 39.0], [25.0, 39.5]]], // 29: Ravenna - Constantinople
  [2, 17, [[19.0, 39.5], [21.5, 38.5]]],           // 30: Brundisium - Athens
  [2, 15, [[19.0, 39.5], [23.0, 39.0], [26.0, 40.0]]], // 31: Brundisium - Constantinople
  [4, 2, [[14.0, 42.5], [16.0, 41.5]]],            // 32: Ravenna - Brundisium (coastal)

  // Cross-basin connections
  [3, 17, [[17.0, 37.0], [20.5, 37.5]]],           // 33: Syracuse - Athens
  [0, 14, [[16.0, 38.0], [22.0, 36.0], [30.0, 35.5]]], // 34: Ostia - Antioch
  [6, 12, [[5.0, 40.0], [7.0, 37.5], [15.0, 34.0], [24.0, 32.0]]], // 35: Massilia - Alexandria
];

// Build sea route adjacency for BFS
const SEA_ADJ = new Map();
for (let ci = 0; ci < SEA_CONNECTIONS.length; ci++) {
  const [a, b] = SEA_CONNECTIONS[ci];
  if (!SEA_ADJ.has(a)) SEA_ADJ.set(a, []);
  if (!SEA_ADJ.has(b)) SEA_ADJ.set(b, []);
  SEA_ADJ.get(a).push({ neighbor: b, connIdx: ci });
  SEA_ADJ.get(b).push({ neighbor: a, connIdx: ci });
}

// ── Utility ──────────────────────────────────────────────────────────────────

function distSq(lon1, lat1, lon2, lat2) {
  const dx = lon1 - lon2;
  const dy = lat1 - lat2;
  return dx * dx + dy * dy;
}

function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180) * Math.cos(lat2*Math.PI/180) * Math.sin(dLon/2)**2;
  return R * 2 * Math.asin(Math.sqrt(a));
}

// haversineKm with (lon, lat) argument order — matches RomanMap.tsx
function haversineKm(lon1, lat1, lon2, lat2) {
  return haversine(lat1, lon1, lat2, lon2);
}

// ── Port helpers (mirrors RomanMap.tsx) ──────────────────────────────────────

function findNearestPort(lon, lat, maxDistKm = 500) {
  let bestIdx = null;
  let bestDist = maxDistKm;
  for (let i = 0; i < PORTS.length; i++) {
    const d = haversineKm(lon, lat, PORTS[i].lon, PORTS[i].lat);
    if (d < bestDist) {
      bestDist = d;
      bestIdx = i;
    }
  }
  return bestIdx;
}

// BFS to find shortest sea route between two ports
// Returns { coords: [[lon,lat],...], connIndices: [seaConnIdx,...] } or null
function findSeaRoute(fromPortIdx, toPortIdx) {
  if (fromPortIdx === toPortIdx) return { coords: [], connIndices: [] };

  const visited = new Set([fromPortIdx]);
  const queue = [[fromPortIdx, [fromPortIdx]]];

  while (queue.length > 0) {
    const [current, portPath] = queue.shift();
    const neighbors = SEA_ADJ.get(current);
    if (!neighbors) continue;

    for (const { neighbor } of neighbors) {
      if (visited.has(neighbor)) continue;
      visited.add(neighbor);
      const newPath = [...portPath, neighbor];

      if (neighbor === toPortIdx) {
        // Reconstruct full coordinate path and collect connection indices
        const coords = [];
        const connIndices = [];
        for (let i = 0; i < newPath.length - 1; i++) {
          const pA = newPath[i];
          const pB = newPath[i + 1];
          // Find the connection between pA and pB
          let connIdx = -1;
          const conn = SEA_CONNECTIONS.find(([a, b], idx) => {
            if ((a === pA && b === pB) || (a === pB && b === pA)) {
              connIdx = idx;
              return true;
            }
            return false;
          });
          if (!conn) continue;
          connIndices.push(connIdx);
          const [cA, , waypoints] = conn;
          const portStart = PORTS[pA];
          const portEnd = PORTS[pB];

          if (i === 0) coords.push([portStart.lon, portStart.lat]);

          if (cA === pA) {
            for (const wp of waypoints) coords.push(wp);
          } else {
            for (let w = waypoints.length - 1; w >= 0; w--) coords.push(waypoints[w]);
          }

          coords.push([portEnd.lon, portEnd.lat]);
        }
        return { coords, connIndices };
      }

      queue.push([neighbor, newPath]);
    }
  }

  return null;
}

// Compute approximate road distance from A* path (sum of haversine between consecutive nodes)
function computeRoadDistance(net, startIdx, endIdx, pathFeatures) {
  if (!pathFeatures || pathFeatures.length === 0) return 0;
  // We reconstruct the node path from parent links -- but we don't store it.
  // Instead, use an approximation: the haversine between start and end road nodes
  // multiplied by a road-winding factor (~1.3).
  const sNode = net.nodes[startIdx];
  const eNode = net.nodes[endIdx];
  return haversineKm(sNode.lon, sNode.lat, eNode.lon, eNode.lat) * 1.3;
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

function connectComponents(net) {
  const { nodes } = net;
  const n = nodes.length;

  const comp = new Int32Array(n).fill(-1);
  let numComp = 0;
  const compNodes = [];
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

  const BRIDGE_THRESHOLD = 0.15;
  let bridgesAdded = 0;

  const bridgeGrid = new Map();
  const bgSize = 0.2;
  for (let i = 0; i < n; i++) {
    const gx = Math.floor(nodes[i].lon / bgSize);
    const gy = Math.floor(nodes[i].lat / bgSize);
    const key = `${gx},${gy}`;
    if (!bridgeGrid.has(key)) bridgeGrid.set(key, []);
    bridgeGrid.get(key).push(i);
  }

  const uf = new Int32Array(numComp);
  for (let i = 0; i < numComp; i++) uf[i] = i;
  function find(x) { while (uf[x] !== x) x = uf[x] = uf[uf[x]]; return x; }
  function union(a, b) { a = find(a); b = find(b); if (a !== b) uf[a] = b; }

  const bridged = new Set();
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
  const parent = new Map();
  const gScore = new Map();
  gScore.set(startIdx, 0);

  const open = new MinHeap();
  open.push([distSq(net.nodes[startIdx].lon, net.nodes[startIdx].lat, endNode.lon, endNode.lat), startIdx]);
  const inClosed = new Set();

  let steps = 0;
  while (open.length > 0 && steps < maxSteps) {
    const [, current] = open.pop();

    if (current === endIdx) {
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
  return null;
}

// ── Era bucket lookup ───────────────────────────────────────────────────────

function getEraBucket(year) {
  for (const era of ERAS) {
    if (year >= era.start && year <= era.end) return era.start;
  }
  return null;
}

// ── Helper: record road segment features into segments accumulator ──────────

function recordRoadFeatures(segments, pathFeatures, era, tripDist) {
  const seen = new Set();
  for (const fi of pathFeatures) {
    if (fi < 0 || seen.has(fi)) continue;
    seen.add(fi);
    if (!segments[fi]) segments[fi] = {};
    if (!segments[fi][era]) segments[fi][era] = { count: 0, totalDist: 0 };
    segments[fi][era].count += 1;
    segments[fi][era].totalDist += tripDist;
  }
}

// ── Main ────────────────────────────────────────────────────────────────────

function main() {
  console.log('Loading data...');
  const roadsData = JSON.parse(fs.readFileSync(ROADS_PATH, 'utf-8'));
  const lettersData = JSON.parse(fs.readFileSync(LETTERS_PATH, 'utf-8'));

  console.log(`  Roads: ${roadsData.features.length} features`);
  console.log(`  Letters: ${lettersData.letters.length} total`);
  console.log(`  Ports: ${PORTS.length}`);
  console.log(`  Sea connections: ${SEA_CONNECTIONS.length}`);

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

  // segments: { featureIdx: { eraStart: { count, totalDist } } }
  const segments = {};
  // seaLanes: { connIdx: { eraStart: { count, totalDist } } }
  const seaLaneTraffic = {};
  // Track which sea connection indices are used, with their full waypoint coords
  const seaLaneCoordsMap = new Map(); // connIdx -> [[lon,lat],...]

  let roadOnlyCount = 0;
  let hybridCount = 0;
  let failedCount = 0;

  console.log(`Routing ${letters.length} letters with hybrid road+sea...`);
  const tRoute = Date.now();

  for (let i = 0; i < letters.length; i++) {
    const letter = letters[i];

    if (i > 0 && i % 100 === 0) {
      const pct = ((i / letters.length) * 100).toFixed(1);
      const elapsed = ((Date.now() - tRoute) / 1000).toFixed(1);
      console.log(`  [${pct}%] ${i}/${letters.length} letters processed (${elapsed}s elapsed)`);
    }

    const tripDist = haversine(letter.s_lat, letter.s_lon, letter.r_lat, letter.r_lon);
    const era = getEraBucket(letter.year_approx);
    const crowFlightDist = haversineKm(letter.s_lon, letter.s_lat, letter.r_lon, letter.r_lat);

    const startNode = findNearestNode(net, letter.s_lon, letter.s_lat);
    const endNode = findNearestNode(net, letter.r_lon, letter.r_lat);

    // Step 1: Try hybrid road+sea route FIRST for long-distance letters
    // Sea travel was faster and preferred in antiquity for cross-water routes
    const port1Idx = findNearestPort(letter.s_lon, letter.s_lat, 500);
    const port2Idx = findNearestPort(letter.r_lon, letter.r_lat, 500);

    if (port1Idx !== null && port2Idx !== null && port1Idx !== port2Idx) {
      const seaRoute = findSeaRoute(port1Idx, port2Idx);
      if (seaRoute !== null) {
        // (a) Road: sender -> port1
        const port1 = PORTS[port1Idx];
        const p1Node = findNearestNode(net, port1.lon, port1.lat);
        if (startNode !== null && p1Node !== null && startNode !== p1Node) {
          const legA = findRoadPathFeatures(net, startNode, p1Node, 100000);
          if (legA !== null) {
            recordRoadFeatures(segments, legA, era, tripDist);
          }
        }

        // (b) Sea: port1 -> port2 — record sea lane traffic
        for (const connIdx of seaRoute.connIndices) {
          if (!seaLaneTraffic[connIdx]) seaLaneTraffic[connIdx] = {};
          if (!seaLaneTraffic[connIdx][era]) seaLaneTraffic[connIdx][era] = { count: 0, totalDist: 0 };
          seaLaneTraffic[connIdx][era].count += 1;
          seaLaneTraffic[connIdx][era].totalDist += tripDist;

          // Store the full waypoint coords for this connection
          if (!seaLaneCoordsMap.has(connIdx)) {
            const [pA, pB, waypoints] = SEA_CONNECTIONS[connIdx];
            const coords = [
              [PORTS[pA].lon, PORTS[pA].lat],
              ...waypoints,
              [PORTS[pB].lon, PORTS[pB].lat],
            ];
            seaLaneCoordsMap.set(connIdx, coords);
          }
        }

        // (c) Road: port2 -> recipient
        const port2 = PORTS[port2Idx];
        const p2Node = findNearestNode(net, port2.lon, port2.lat);
        if (endNode !== null && p2Node !== null && p2Node !== endNode) {
          const legC = findRoadPathFeatures(net, p2Node, endNode, 100000);
          if (legC !== null) {
            recordRoadFeatures(segments, legC, era, tripDist);
          }
        }

        hybridCount++;
        continue;
      }
    }

    // Step 2: Try direct A* road route (for same-continent or short routes)
    let usedRoadOnly = false;

    if (startNode !== null && endNode !== null) {
      if (startNode === endNode) {
        roadOnlyCount++;
        continue; // Same node, local letter
      }

      const pathFeatures = findRoadPathFeatures(net, startNode, endNode);
      if (pathFeatures !== null) {
        const roadDist = computeRoadDistance(net, startNode, endNode, pathFeatures);
        if (roadDist < crowFlightDist * 2.5) {
          recordRoadFeatures(segments, pathFeatures, era, tripDist);
          roadOnlyCount++;
          usedRoadOnly = true;
        }
      }
    }

    if (usedRoadOnly) continue;

    // Step 3: Fallback — skip
    failedCount++;
  }

  const routeTime = ((Date.now() - tRoute) / 1000).toFixed(1);
  console.log(`\nRouting complete in ${routeTime}s`);
  console.log(`  Road only: ${roadOnlyCount}`);
  console.log(`  Hybrid (road+sea): ${hybridCount}`);
  console.log(`  Failed to route: ${failedCount}`);

  // ── Process road segments ──────────────────────────────────────────────────

  let maxTraffic = 0;
  let maxAvgDist = 0;
  let busiestFeature = null;
  let busiestEra = null;
  const outputSegments = {};

  for (const [fi, eraData] of Object.entries(segments)) {
    outputSegments[fi] = {};
    for (const [era, data] of Object.entries(eraData)) {
      const count = data.count;
      const avgDist = Math.round(data.totalDist / count);
      outputSegments[fi][era] = { count, avgDist };
      if (count > maxTraffic) {
        maxTraffic = count;
        busiestFeature = fi;
        busiestEra = era;
      }
      if (avgDist > maxAvgDist) {
        maxAvgDist = avgDist;
      }
    }
  }

  // ── Process sea lanes ──────────────────────────────────────────────────────

  let maxSeaTraffic = 0;
  let maxSeaAvgDist = 0;
  const outputSeaLanes = {};

  for (const [connIdx, eraData] of Object.entries(seaLaneTraffic)) {
    outputSeaLanes[connIdx] = {};
    for (const [era, data] of Object.entries(eraData)) {
      const count = data.count;
      const avgDist = Math.round(data.totalDist / count);
      outputSeaLanes[connIdx][era] = { count, avgDist };
      if (count > maxSeaTraffic) maxSeaTraffic = count;
      if (avgDist > maxSeaAvgDist) maxSeaAvgDist = avgDist;
    }
  }

  // Build seaLaneCoords array indexed by connection index
  const seaLaneCoords = {};
  for (const [connIdx, coords] of seaLaneCoordsMap) {
    seaLaneCoords[connIdx] = coords;
  }

  // ── Statistics ──────────────────────────────────────────────────────────────

  const segmentCount = Object.keys(outputSegments).length;
  const seaLaneCount = Object.keys(outputSeaLanes).length;
  console.log(`\nStats:`);
  console.log(`  Road segments with traffic: ${segmentCount} / ${roadsData.features.length}`);
  console.log(`  Sea lanes with traffic: ${seaLaneCount} / ${SEA_CONNECTIONS.length}`);
  console.log(`  Max road traffic: ${maxTraffic} (feature #${busiestFeature}, era ${busiestEra})`);
  console.log(`  Max road avg distance: ${maxAvgDist} km`);
  console.log(`  Max sea traffic: ${maxSeaTraffic}`);
  console.log(`  Max sea avg distance: ${maxSeaAvgDist} km`);

  // Per-era totals
  for (const era of ERAS) {
    let roadTotal = 0;
    for (const eraData of Object.values(outputSegments)) {
      roadTotal += (eraData[era.start]?.count) || 0;
    }
    let seaTotal = 0;
    for (const eraData of Object.values(outputSeaLanes)) {
      seaTotal += (eraData[era.start]?.count) || 0;
    }
    console.log(`  ${era.label}: ${roadTotal} road-segment-traversals, ${seaTotal} sea-lane-traversals`);
  }

  // Busiest sea lane per era
  console.log(`\nBusiest sea lane per era:`);
  for (const era of ERAS) {
    let bestConn = null;
    let bestCount = 0;
    for (const [connIdx, eraData] of Object.entries(outputSeaLanes)) {
      const d = eraData[era.start];
      if (d && d.count > bestCount) {
        bestCount = d.count;
        bestConn = connIdx;
      }
    }
    if (bestConn !== null) {
      const [pA, pB] = SEA_CONNECTIONS[bestConn];
      console.log(`  ${era.label}: ${PORTS[pA].name} - ${PORTS[pB].name} (${bestCount} letters)`);
    } else {
      console.log(`  ${era.label}: (none)`);
    }
  }

  // ── Build output ───────────────────────────────────────────────────────────

  const output = {
    eras: ERAS,
    segments: outputSegments,
    maxTraffic,
    maxAvgDist,
    seaLanes: outputSeaLanes,
    seaLaneCoords,
    maxSeaTraffic,
    maxSeaAvgDist,
  };

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(output));
  const fileSize = fs.statSync(OUTPUT_PATH).size;
  console.log(`\nOutput: ${OUTPUT_PATH}`);
  console.log(`  File size: ${(fileSize / 1024).toFixed(1)} KB`);
  console.log('Done.');
}

main();

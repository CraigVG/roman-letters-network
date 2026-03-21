'use client';

import { useRef, useEffect, useState, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import {
  YEAR_MIN,
  YEAR_MAX,
  YEAR_START,
  WYMAN_EXCLUDED_COLLECTIONS,
  WYMAN_YEAR_MIN,
  WYMAN_YEAR_MAX,
  type HistoricalEvent,
  type HubCity,
  type MapTimelapseProps,
  type MapStats,
} from './map-types';

// Re-export for convenience
export { YEAR_MIN, YEAR_MAX, YEAR_START };
export type { HistoricalEvent, MapStats, MapTimelapseProps };

// ── Types ─────────────────────────────────────────────────────────────

interface MapLetter {
  id: number;
  collection: string;
  letter_number: number;
  year_approx: number;
  sender_name: string;
  s_lat: number;
  s_lon: number;
  sender_role: string | null;
  recipient_name: string;
  r_lat: number;
  r_lon: number;
  recipient_role: string | null;
  quick_summary: string | null;
  interesting_note: string | null;
}

interface MapPerson {
  id: number;
  name: string;
  role: string | null;
  location: string | null;
  lat: number;
  lon: number;
  birth_year: number | null;
  death_year: number | null;
  sent: number;
  received: number;
}

interface TimelineRow {
  decade: number;
  collection: string;
  count: number;
}

// ── Constants ─────────────────────────────────────────────────────────

const DARE_TILE_URL = 'https://dh.gu.se/tiles/imperium/{z}/{x}/{y}.png';
const AWMC_ROADS_URL = '/data/roman-roads.json'; // Pre-processed TopoJSON

const MED_CENTER: [number, number] = [18, 38]; // lon, lat - Mediterranean center
const MED_ZOOM = 4.2;
const MED_BOUNDS: [[number, number], [number, number]] = [[-15, 20], [50, 58]];

const CENTURY_COLORS: Record<number, string> = {
  1: '#7ec8e3',
  2: '#7ec8e3',
  3: '#a8d8a8',
  4: '#e8c05a',
  5: '#e07a3a',
  6: '#c0392b',
  7: '#a050c0',
  8: '#a050c0',
};

const ROLE_COLORS: Record<string, string> = {
  pope: '#c9a959',
  bishop: '#5b8c5a',
  senator: '#8b5cf6',
  emperor: '#e74c3c',
  priest: '#3b82f6',
  scholar: '#3b82f6',
  monk: '#a78bfa',
  default: '#6b7b8d',
};

// Travel speeds for animation (km per year-tick at 1x speed)
const LAND_SPEED_KM_DAY = 30;
const SEA_SPEED_KM_DAY = 100;

// Major Roman ports with coordinates
const PORTS: { name: string; lon: number; lat: number }[] = [
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
// Waypoints create curved routes over water (not straight lines)
const SEA_CONNECTIONS: [number, number, [number, number][]][] = [
  // Western Mediterranean
  [0, 3, [[13.5, 39.5], [14.5, 38.0]]],           // Ostia - Syracuse
  [0, 9, [[12.0, 38.5]]],                          // Ostia - Carthage
  [0, 5, [[10.5, 42.5]]],                          // Ostia - Genoa
  [1, 3, [[14.5, 39.0]]],                          // Puteoli - Syracuse
  [1, 9, [[13.0, 38.0], [11.5, 37.5]]],            // Puteoli - Carthage
  [3, 9, [[13.0, 36.0]]],                          // Syracuse - Carthage
  [5, 6, [[7.0, 43.5]]],                           // Genoa - Massilia
  [6, 7, [[4.0, 43.0]]],                           // Massilia - Narbo
  [7, 8, [[2.0, 42.0]]],                           // Narbo - Tarraco
  [6, 9, [[5.0, 40.5], [7.0, 38.0]]],              // Massilia - Carthage
  [9, 10, [[9.0, 36.8]]],                          // Carthage - Hippo
  [10, 6, [[6.5, 38.5], [5.5, 41.0]]],             // Hippo - Massilia (via Balearics)

  // Central Mediterranean
  [3, 12, [[18.0, 35.0], [24.0, 33.0]]],           // Syracuse - Alexandria
  [9, 12, [[15.0, 34.0], [22.0, 32.5]]],           // Carthage - Alexandria
  [9, 11, [[12.0, 34.5]]],                         // Carthage - Leptis
  [11, 12, [[18.0, 32.0], [24.0, 31.5]]],          // Leptis - Alexandria
  [11, 21, [[18.0, 32.5]]],                        // Leptis - Cyrene
  [21, 12, [[25.0, 32.0]]],                        // Cyrene - Alexandria

  // Eastern Mediterranean
  [12, 13, [[32.0, 31.5]]],                        // Alexandria - Caesarea
  [13, 14, [[35.5, 34.0]]],                        // Caesarea - Antioch/Seleucia
  [12, 14, [[32.0, 33.0], [34.5, 35.0]]],          // Alexandria - Antioch
  [15, 12, [[27.0, 37.0], [30.0, 33.0]]],          // Constantinople - Alexandria
  [15, 14, [[30.0, 38.0], [34.0, 36.5]]],          // Constantinople - Antioch
  [15, 19, [[28.0, 39.5]]],                        // Constantinople - Ephesus
  [19, 20, []],                                    // Ephesus - Smyrna (very close, direct)
  [17, 18, []],                                    // Athens - Corinth (close)
  [17, 19, [[25.5, 37.8]]],                        // Athens - Ephesus
  [16, 15, [[25.0, 40.5]]],                        // Thessalonica - Constantinople
  [16, 17, [[23.5, 39.0]]],                        // Thessalonica - Athens

  // Adriatic
  [4, 15, [[16.0, 41.0], [20.0, 39.0], [25.0, 39.5]]], // Ravenna - Constantinople
  [2, 17, [[19.0, 39.5], [21.5, 38.5]]],           // Brundisium - Athens
  [2, 15, [[19.0, 39.5], [23.0, 39.0], [26.0, 40.0]]], // Brundisium - Constantinople
  [4, 2, [[14.0, 42.5], [16.0, 41.5]]],            // Ravenna - Brundisium (coastal)

  // Cross-basin connections
  [3, 17, [[17.0, 37.0], [20.5, 37.5]]],           // Syracuse - Athens
  [0, 14, [[16.0, 38.0], [22.0, 36.0], [30.0, 35.5]]], // Ostia - Antioch
  [6, 12, [[5.0, 40.0], [7.0, 37.5], [15.0, 34.0], [24.0, 32.0]]], // Massilia - Alexandria
];

// Build sea route adjacency for BFS
const SEA_ADJ: Map<number, { neighbor: number; connIdx: number }[]> = new Map();
for (let ci = 0; ci < SEA_CONNECTIONS.length; ci++) {
  const [a, b] = SEA_CONNECTIONS[ci];
  if (!SEA_ADJ.has(a)) SEA_ADJ.set(a, []);
  if (!SEA_ADJ.has(b)) SEA_ADJ.set(b, []);
  SEA_ADJ.get(a)!.push({ neighbor: b, connIdx: ci });
  SEA_ADJ.get(b)!.push({ neighbor: a, connIdx: ci });
}

// BFS to find shortest sea route between two ports in the port network
function findSeaRoute(fromPortIdx: number, toPortIdx: number): [number, number][] | null {
  if (fromPortIdx === toPortIdx) return [];

  const visited = new Set<number>([fromPortIdx]);
  // Queue entries: [currentPortIdx, path of port indices]
  const queue: [number, number[]][] = [[fromPortIdx, [fromPortIdx]]];

  while (queue.length > 0) {
    const [current, path] = queue.shift()!;
    const neighbors = SEA_ADJ.get(current);
    if (!neighbors) continue;

    for (const { neighbor } of neighbors) {
      if (visited.has(neighbor)) continue;
      visited.add(neighbor);
      const newPath = [...path, neighbor];

      if (neighbor === toPortIdx) {
        // Reconstruct full coordinate path from port chain
        const coords: [number, number][] = [];
        for (let i = 0; i < newPath.length - 1; i++) {
          const pA = newPath[i];
          const pB = newPath[i + 1];
          // Find the connection between pA and pB
          const conn = SEA_CONNECTIONS.find(
            ([a, b]) => (a === pA && b === pB) || (a === pB && b === pA)
          );
          if (!conn) continue;
          const [cA, , waypoints] = conn;
          const portStart = PORTS[pA];
          const portEnd = PORTS[pB];

          // Add start port (skip if not first segment, already added)
          if (i === 0) coords.push([portStart.lon, portStart.lat]);

          // Add waypoints (reverse if connection is stored in opposite direction)
          if (cA === pA) {
            for (const wp of waypoints) coords.push(wp);
          } else {
            for (let w = waypoints.length - 1; w >= 0; w--) coords.push(waypoints[w]);
          }

          // Add end port
          coords.push([portEnd.lon, portEnd.lat]);
        }
        return coords;
      }

      queue.push([neighbor, newPath]);
    }
  }

  return null; // No sea route between these ports
}

// Find nearest port to a given lon/lat (within maxDistKm)
function findNearestPort(lon: number, lat: number, maxDistKm: number = 300): number | null {
  let bestIdx: number | null = null;
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

// Map from road segment key to set of letter IDs using that segment (for heatmap)
const roadSegmentTraffic = new Map<string, Set<number>>();

// Record road segment usage for a letter route
function recordSegmentTraffic(letterId: number, roadPathIndices: number[]): void {
  for (let i = 0; i < roadPathIndices.length - 1; i++) {
    const a = roadPathIndices[i];
    const b = roadPathIndices[i + 1];
    // Normalize key so segment a-b and b-a are the same
    const key = a < b ? `${a}-${b}` : `${b}-${a}`;
    let set = roadSegmentTraffic.get(key);
    if (!set) {
      set = new Set();
      roadSegmentTraffic.set(key, set);
    }
    set.add(letterId);
  }
}

// ── Road network spatial index ───────────────────────────────────────

interface RoadNode {
  lon: number;
  lat: number;
  edges: number[]; // indices into roadNodes
}

interface RoadNetwork {
  nodes: RoadNode[];
  // Grid-based spatial index: key = "gridX,gridY" -> node indices
  grid: Map<string, number[]>;
  gridSize: number; // degrees per grid cell
}

// Haversine distance in km
function haversineKm(lon1: number, lat1: number, lon2: number, lat2: number): number {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// Simple squared distance for quick comparisons
function distSq(lon1: number, lat1: number, lon2: number, lat2: number): number {
  const dx = lon1 - lon2;
  const dy = lat1 - lat2;
  return dx * dx + dy * dy;
}

// Build a road network graph from GeoJSON
function buildRoadNetwork(geojson: { features: Array<{ geometry: { type: string; coordinates: number[][] | number[][][] }; properties: Record<string, unknown> }> }): RoadNetwork {
  const nodeMap = new Map<string, number>(); // "lon,lat" -> index
  const nodes: RoadNode[] = [];
  const gridSize = 0.5; // 0.5 degree grid cells (~50km)
  const grid = new Map<string, number[]>();

  function getOrCreateNode(lon: number, lat: number): number {
    // Round to 3 decimals to merge nearby points
    const key = `${lon.toFixed(3)},${lat.toFixed(3)}`;
    let idx = nodeMap.get(key);
    if (idx !== undefined) return idx;
    idx = nodes.length;
    nodeMap.set(key, idx);
    nodes.push({ lon, lat, edges: [] });
    // Add to grid
    const gx = Math.floor(lon / gridSize);
    const gy = Math.floor(lat / gridSize);
    const gKey = `${gx},${gy}`;
    const cell = grid.get(gKey);
    if (cell) cell.push(idx);
    else grid.set(gKey, [idx]);
    return idx;
  }

  for (const feature of geojson.features) {
    const geom = feature.geometry;
    // Handle both LineString and MultiLineString
    const lineStrings: number[][] = geom.type === 'MultiLineString'
      ? (geom.coordinates as number[][][]).flat()
      : geom.coordinates as number[][];

    // For MultiLineString, coordinates is number[][][], we need to iterate line by line
    if (geom.type === 'MultiLineString') {
      for (const line of geom.coordinates as number[][][]) {
        for (let i = 0; i < line.length - 1; i++) {
          const a = getOrCreateNode(line[i][0], line[i][1]);
          const b = getOrCreateNode(line[i + 1][0], line[i + 1][1]);
          if (a !== b) {
            if (!nodes[a].edges.includes(b)) nodes[a].edges.push(b);
            if (!nodes[b].edges.includes(a)) nodes[b].edges.push(a);
          }
        }
      }
    } else {
      const coords = lineStrings;
      for (let i = 0; i < coords.length - 1; i++) {
        const a = getOrCreateNode(coords[i][0], coords[i][1]);
        const b = getOrCreateNode(coords[i + 1][0], coords[i + 1][1]);
        if (a !== b) {
          if (!nodes[a].edges.includes(b)) nodes[a].edges.push(b);
          if (!nodes[b].edges.includes(a)) nodes[b].edges.push(a);
        }
      }
    }
  }

  return { nodes, grid, gridSize };
}

// Find the nearest road node to a given lon/lat (expanding grid search)
function findNearestNode(net: RoadNetwork, lon: number, lat: number, maxDist: number = 3.0): number | null {
  const gx = Math.floor(lon / net.gridSize);
  const gy = Math.floor(lat / net.gridSize);

  let bestIdx: number | null = null;
  let bestDist = maxDist * maxDist; // squared degree threshold

  // Search expanding rings: 3x3, then 5x5, then 7x7
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
    if (bestIdx !== null) break; // Found one in this ring, no need to expand
  }
  return bestIdx;
}

// A* pathfinding between two road nodes - uses Euclidean distance heuristic
// Much faster than BFS for long-distance routes across the 83K-node graph
function findRoadPath(net: RoadNetwork, startIdx: number, endIdx: number, maxSteps: number = 50000): number[] | null {
  if (startIdx === endIdx) return [startIdx];

  const endNode = net.nodes[endIdx];
  const parent = new Map<number, number>();

  // g = cost from start, f = g + heuristic
  const gScore = new Map<number, number>();
  gScore.set(startIdx, 0);

  // Min-heap using array + manual sift (faster than sorting for A*)
  // Each entry: [fScore, nodeIdx]
  const open: [number, number][] = [[distSq(net.nodes[startIdx].lon, net.nodes[startIdx].lat, endNode.lon, endNode.lat), startIdx]];
  const inClosed = new Set<number>();

  let steps = 0;
  while (open.length > 0 && steps < maxSteps) {
    // Find minimum f-score (simple linear scan - fast enough for typical path lengths)
    let minI = 0;
    for (let i = 1; i < open.length; i++) {
      if (open[i][0] < open[minI][0]) minI = i;
    }
    const [, current] = open[minI];
    open[minI] = open[open.length - 1];
    open.pop();

    if (current === endIdx) {
      // Reconstruct path
      const path: number[] = [endIdx];
      let node = endIdx;
      while (parent.has(node)) {
        node = parent.get(node)!;
        path.unshift(node);
      }
      return path;
    }

    if (inClosed.has(current)) continue;
    inClosed.add(current);
    steps++;

    const currentG = gScore.get(current) ?? Infinity;
    const currentNode = net.nodes[current];

    for (const neighbor of currentNode.edges) {
      if (inClosed.has(neighbor)) continue;

      const nNode = net.nodes[neighbor];
      const edgeCost = distSq(currentNode.lon, currentNode.lat, nNode.lon, nNode.lat);
      const tentativeG = currentG + edgeCost;

      const prevG = gScore.get(neighbor);
      if (prevG !== undefined && tentativeG >= prevG) continue;

      gScore.set(neighbor, tentativeG);
      parent.set(neighbor, current);

      const h = distSq(nNode.lon, nNode.lat, endNode.lon, endNode.lat);
      open.push([tentativeG + h, neighbor]);
    }
  }
  return null; // No path found within budget
}

// Get the route coords (lon/lat pairs) for a letter, using road network, hybrid road+sea, or fallback
function getLetterRoute(
  net: RoadNetwork | null,
  sLon: number, sLat: number,
  rLon: number, rLat: number,
  letterId?: number,
): { coords: [number, number][]; isSea: boolean; roadPath?: number[] } {
  const senderPt: [number, number] = [sLon, sLat];
  const recipPt: [number, number] = [rLon, rLat];
  const directDistKm = haversineKm(sLon, sLat, rLon, rLat);

  // 1. Try direct A* road route
  if (net) {
    const startNode = findNearestNode(net, sLon, sLat);
    const endNode = findNearestNode(net, rLon, rLat);

    if (startNode !== null && endNode !== null) {
      const path = findRoadPath(net, startNode, endNode);
      if (path && path.length >= 2) {
        const coords: [number, number][] = [senderPt];
        for (const nodeIdx of path) {
          coords.push([net.nodes[nodeIdx].lon, net.nodes[nodeIdx].lat]);
        }
        coords.push(recipPt);
        const routeDist = routeDistanceKm(coords);

        // Use road route if it's not excessively long compared to straight-line
        if (routeDist < directDistKm * 1.5) {
          return { coords, isSea: false, roadPath: path };
        }
      }
    }
  }

  // 2. Try hybrid road + sea routing through ports
  const senderPort = findNearestPort(sLon, sLat);
  const recipPort = findNearestPort(rLon, rLat);

  if (senderPort !== null && recipPort !== null && senderPort !== recipPort) {
    const seaCoords = findSeaRoute(senderPort, recipPort);
    if (seaCoords && seaCoords.length >= 2) {
      // Build hybrid route: road to port -> sea -> road from port
      const allCoords: [number, number][] = [];
      const roadPathIndices: number[] = [];

      // Segment A: sender -> nearest port (by road if possible)
      const portStart = PORTS[senderPort];
      if (net) {
        const sNode = findNearestNode(net, sLon, sLat);
        const pNode = findNearestNode(net, portStart.lon, portStart.lat);
        if (sNode !== null && pNode !== null && sNode !== pNode) {
          const roadToPort = findRoadPath(net, sNode, pNode, 20000);
          if (roadToPort && roadToPort.length >= 2) {
            allCoords.push(senderPt);
            for (const ni of roadToPort) {
              allCoords.push([net.nodes[ni].lon, net.nodes[ni].lat]);
            }
            roadPathIndices.push(...roadToPort);
          } else {
            allCoords.push(senderPt);
            allCoords.push([portStart.lon, portStart.lat]);
          }
        } else {
          allCoords.push(senderPt);
          if (sNode !== pNode) allCoords.push([portStart.lon, portStart.lat]);
        }
      } else {
        allCoords.push(senderPt);
        allCoords.push([portStart.lon, portStart.lat]);
      }

      // Segment B: sea route between ports
      for (const sc of seaCoords) {
        allCoords.push(sc);
      }

      // Segment C: port -> recipient (by road if possible)
      const portEnd = PORTS[recipPort];
      if (net) {
        const pNode = findNearestNode(net, portEnd.lon, portEnd.lat);
        const eNode = findNearestNode(net, rLon, rLat);
        if (pNode !== null && eNode !== null && pNode !== eNode) {
          const roadFromPort = findRoadPath(net, pNode, eNode, 20000);
          if (roadFromPort && roadFromPort.length >= 2) {
            for (const ni of roadFromPort) {
              allCoords.push([net.nodes[ni].lon, net.nodes[ni].lat]);
            }
            allCoords.push(recipPt);
            roadPathIndices.push(...roadFromPort);
          } else {
            allCoords.push(recipPt);
          }
        } else {
          if (pNode !== eNode) allCoords.push(recipPt);
        }
      } else {
        allCoords.push(recipPt);
      }

      if (allCoords.length >= 2) {
        return { coords: allCoords, isSea: true, roadPath: roadPathIndices.length > 0 ? roadPathIndices : undefined };
      }
    }
  }

  // 3. Fallback: bezier arc (direct line - rendered as curve by canvas)
  return { coords: [senderPt, recipPt], isSea: false };
}


// Calculate total distance of a route in km
function routeDistanceKm(coords: [number, number][]): number {
  let total = 0;
  for (let i = 1; i < coords.length; i++) {
    total += haversineKm(coords[i - 1][0], coords[i - 1][1], coords[i][0], coords[i][1]);
  }
  return total;
}

// Cache for letter routes (computed once when road network loads)
const letterRouteCache = new Map<number, { coords: [number, number][]; isSea: boolean; distKm: number; roadPath?: number[] }>();

// ── Helpers ───────────────────────────────────────────────────────────

function roleColor(role: string | null): string {
  if (!role) return ROLE_COLORS.default;
  const r = role.toLowerCase();
  for (const [key, color] of Object.entries(ROLE_COLORS)) {
    if (r.includes(key)) return color;
  }
  return ROLE_COLORS.default;
}

function centuryColor(year: number | null): string {
  if (!year) return '#8899aa';
  const century = Math.ceil(year / 100);
  return CENTURY_COLORS[century] ?? '#8899aa';
}

// Generate a curved arc between two points (for Canvas rendering)
function generateArc(
  p1: { x: number; y: number },
  p2: { x: number; y: number },
  segments: number = 30,
): { x: number; y: number }[] {
  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  const len = Math.sqrt(dx * dx + dy * dy);
  if (len === 0) return [p1, p2];
  const curve = Math.min(len * 0.2, 60);
  const mx = (p1.x + p2.x) / 2;
  const my = (p1.y + p2.y) / 2;
  const nx = (-dy / len) * curve;
  const ny = (dx / len) * curve;
  const cx = mx + nx;
  const cy = my + ny;

  const points: { x: number; y: number }[] = [];
  for (let i = 0; i <= segments; i++) {
    const t = i / segments;
    const x = (1 - t) * (1 - t) * p1.x + 2 * (1 - t) * t * cx + t * t * p2.x;
    const y = (1 - t) * (1 - t) * p1.y + 2 * (1 - t) * t * cy + t * t * p2.y;
    points.push({ x, y });
  }
  return points;
}

// ── Animated letter particle ──────────────────────────────────────────

interface LetterParticle {
  letter: MapLetter;
  arcPoints: { x: number; y: number }[];
  progress: number; // 0-1
  color: string;
}

// Screen-space position of an active particle (for hit-testing clicks/hovers)
interface ActiveParticle {
  x: number;
  y: number;
  letter: MapLetter;
}

// ── Component ─────────────────────────────────────────────────────────

export default function RomanMap({
  currentYear,
  onYearChange,
  isPlaying,
  onPlayingChange,
  speed,
  windowSize,
  filterCollection,
  arcOpacity,
  showTrail,
  showDots,
  showEvents,
  wymanMode = false,
  onStatsChange,
  onCollectionsLoaded,
  onEventsLoaded,
  onTimelineLoaded,
  onLoadingChange,
  onError,
  onHubCityClick,
}: MapTimelapseProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const bannerRef = useRef<HTMLDivElement>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data refs
  const dataRef = useRef<{
    letters: MapLetter[];
    people: MapPerson[];
    events: HistoricalEvent[];
    timeline: TimelineRow[];
    hubCities: HubCity[];
    roadNetwork: RoadNetwork | null;
    roadsLoaded: boolean;
    lastBannerYear: number | null;
    bannerTimer: ReturnType<typeof setTimeout> | null;
    animationFrame: number | null;
    activeParticles: ActiveParticle[];
  }>({
    letters: [],
    people: [],
    events: [],
    timeline: [],
    hubCities: [],
    roadNetwork: null,
    roadsLoaded: false,
    lastBannerYear: null,
    bannerTimer: null,
    animationFrame: null,
    activeParticles: [],
  });

  const playRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const currentYearRef = useRef(YEAR_START);

  useEffect(() => {
    currentYearRef.current = currentYear;
  }, [currentYear]);

  // Political borders removed - need verified historical GeoJSON source

  // ── Canvas rendering ────────────────────────────────────────────────

  const renderCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const map = mapRef.current;
    if (!canvas || !map) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { letters, events, people } = dataRef.current;
    const year = currentYearRef.current;
    const dpr = window.devicePixelRatio || 1;

    // Derive dimensions from MapLibre's own canvas to stay perfectly in sync
    const mapCanvas = map.getCanvas();
    const W = mapCanvas.clientWidth;
    const H = mapCanvas.clientHeight;

    // Ensure canvas resolution matches map
    if (canvas.width !== W * dpr || canvas.height !== H * dpr) {
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      canvas.style.width = W + 'px';
      canvas.style.height = H + 'px';
    }

    // Reset transform on every frame (ctx.scale is cumulative - never use it)
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);

    // Political borders removed - need verified historical GeoJSON data

    // Progressive detail: zoom level determines rendering mode
    const zoom = map.getZoom();

    // Filter letters by current year + options
    const win = windowSize;
    const collection = filterCollection;
    const wyman = wymanMode;
    const trail = showTrail;
    const opacity = arcOpacity;

    const yearLetters = letters.filter((l) => {
      if (collection && l.collection !== collection) return false;
      if (!l.year_approx) return false;
      if (wyman) {
        if (WYMAN_EXCLUDED_COLLECTIONS.has(l.collection)) return false;
        if (l.year_approx < WYMAN_YEAR_MIN || l.year_approx > WYMAN_YEAR_MAX) return false;
      }
      if (trail) {
        return l.year_approx <= year + win;
      }
      return Math.abs(l.year_approx - year) <= win;
    });

    // Progressive detail based on zoom level
    // zoom < 5: aggregate mode (wider, more transparent arcs, fewer particles)
    // zoom 5-7: mixed mode
    // zoom > 7: detail mode (individual letter arcs with particles)
    const isZoomedIn = zoom > 7;
    const isZoomedOut = zoom < 3.5;
    const arcWidthMultiplier = isZoomedOut ? 2.5 : isZoomedIn ? 1.0 : 1.5;
    const arcOpacityMultiplier = isZoomedOut ? 0.5 : 1.0;
    const maxRender = isZoomedOut ? 300 : isZoomedIn ? 800 : 600;

    let renderLetters = yearLetters;
    if (yearLetters.length > maxRender) {
      renderLetters = yearLetters
        .slice()
        .sort((a, b) => Math.abs(a.year_approx - year) - Math.abs(b.year_approx - year))
        .slice(0, maxRender);
    }

    // Project helper
    const project = (lon: number, lat: number): { x: number; y: number } | null => {
      const point = map.project([lon, lat]);
      return { x: point.x, y: point.y };
    };

    // Draw arcs + collect particles for animation
    const particles: LetterParticle[] = [];
    const now = Date.now();

    renderLetters.forEach((l) => {
      const cached = letterRouteCache.get(l.id);
      const age = year - l.year_approx;
      let ageOpacity = opacity;
      if (trail && age > 0) {
        ageOpacity = opacity * Math.max(0.15, 1 - age / 200);
      }
      const isNew = Math.abs(l.year_approx - year) <= win;
      const color = centuryColor(l.year_approx);

      let arcPoints: { x: number; y: number }[];

      if (cached && cached.coords.length >= 2) {
        // Project the road route coords to screen space
        arcPoints = cached.coords.map(([lon, lat]) => {
          const pt = map.project([lon, lat]);
          return { x: pt.x, y: pt.y };
        });
      } else {
        // Fallback to bezier arc
        const s = project(l.s_lon, l.s_lat);
        const r = project(l.r_lon, l.r_lat);
        if (!s || !r) return;
        arcPoints = generateArc(s, r);
      }

      if (arcPoints.length < 2) return;

      // Draw the route line
      ctx.beginPath();
      ctx.moveTo(arcPoints[0].x, arcPoints[0].y);
      for (let i = 1; i < arcPoints.length; i++) {
        ctx.lineTo(arcPoints[i].x, arcPoints[i].y);
      }

      // Sea routes get a dashed style
      if (cached?.isSea) {
        ctx.setLineDash([6, 4]);
      }

      ctx.strokeStyle = color;
      ctx.lineWidth = (isNew ? 1.8 : 0.7) * arcWidthMultiplier;
      ctx.globalAlpha = ageOpacity * arcOpacityMultiplier;

      if (isNew) {
        ctx.shadowColor = color;
        ctx.shadowBlur = isZoomedOut ? 8 : 4; // Bigger glow when zoomed out for "flow" effect
      }
      ctx.stroke();
      ctx.shadowBlur = 0;
      ctx.setLineDash([]);

      // Animated letter dots for letters in the current window
      if (isNew && arcPoints.length > 1) {
        // Travel time based on route distance: longer routes = slower progress
        const distKm = cached?.distKm || 500;
        const speedKmDay = cached?.isSea ? SEA_SPEED_KM_DAY : LAND_SPEED_KM_DAY;
        const travelDays = Math.max(5, distKm / speedKmDay);
        // Cycle period: proportional to travel time (1 day = ~100ms at 1x speed)
        const cyclePeriodMs = travelDays * 100;
        const phase = (l.id * 137.5) % 1;
        const progress = ((now / cyclePeriodMs + phase) % 1);
        particles.push({ letter: l, arcPoints, progress, color });
      }
    });

    // Draw animated letter particles (glowing dots moving along routes)
    // When zoomed out: fewer/no particles - the glow on arcs provides aggregate flow
    // When zoomed in: individual particles visible along roads
    const frameParticles: ActiveParticle[] = [];
    if (particles.length > 0 && !isZoomedOut) {
      const baseMax = speed >= 5 ? 100 : speed >= 2 ? 200 : 400;
      // Scale particles with zoom: fewer at medium zoom, full at high zoom
      const zoomFactor = isZoomedIn ? 1.0 : 0.5;
      const maxParticles = Math.floor(baseMax * zoomFactor);
      const renderParticles = particles.length > maxParticles
        ? particles.slice(0, maxParticles)
        : particles;

      renderParticles.forEach((p) => {
        // Interpolate position along the polyline based on progress
        const totalLen = p.arcPoints.reduce((acc, pt, i) => {
          if (i === 0) return 0;
          const prev = p.arcPoints[i - 1];
          return acc + Math.sqrt((pt.x - prev.x) ** 2 + (pt.y - prev.y) ** 2);
        }, 0);
        const targetDist = p.progress * totalLen;

        let accDist = 0;
        let pt = p.arcPoints[0];
        for (let i = 1; i < p.arcPoints.length; i++) {
          const prev = p.arcPoints[i - 1];
          const curr = p.arcPoints[i];
          const segLen = Math.sqrt((curr.x - prev.x) ** 2 + (curr.y - prev.y) ** 2);
          if (accDist + segLen >= targetDist) {
            const t = segLen > 0 ? (targetDist - accDist) / segLen : 0;
            pt = { x: prev.x + t * (curr.x - prev.x), y: prev.y + t * (curr.y - prev.y) };
            break;
          }
          accDist += segLen;
          pt = curr;
        }

        // Store position for hit-testing
        frameParticles.push({ x: pt.x, y: pt.y, letter: p.letter });

        // Trail behind the dot (small comet tail)
        const tailLen = 3;
        const tailStart = Math.max(0, p.progress - 0.05);
        const tailTargetDist = tailStart * totalLen;
        let tailAccDist = 0;
        let tailPt = p.arcPoints[0];
        for (let i = 1; i < p.arcPoints.length; i++) {
          const prev = p.arcPoints[i - 1];
          const curr = p.arcPoints[i];
          const segLen = Math.sqrt((curr.x - prev.x) ** 2 + (curr.y - prev.y) ** 2);
          if (tailAccDist + segLen >= tailTargetDist) {
            const t = segLen > 0 ? (tailTargetDist - tailAccDist) / segLen : 0;
            tailPt = { x: prev.x + t * (curr.x - prev.x), y: prev.y + t * (curr.y - prev.y) };
            break;
          }
          tailAccDist += segLen;
          tailPt = curr;
        }

        // Draw comet tail
        const gradient = ctx.createLinearGradient(tailPt.x, tailPt.y, pt.x, pt.y);
        gradient.addColorStop(0, 'rgba(255,255,255,0)');
        gradient.addColorStop(1, p.color);
        ctx.beginPath();
        ctx.moveTo(tailPt.x, tailPt.y);
        ctx.lineTo(pt.x, pt.y);
        ctx.strokeStyle = gradient;
        ctx.lineWidth = tailLen;
        ctx.globalAlpha = 0.4;
        ctx.stroke();

        // Outer glow
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 6, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = 0.15;
        ctx.fill();

        // Mid ring
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 3.5, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.globalAlpha = 0.7;
        ctx.fill();

        // Bright core
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 1.8, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = 1;
        ctx.fill();
      });
    }
    // Update active particles for hit-testing in mousemove/click handlers
    dataRef.current.activeParticles = frameParticles;

    // Draw people dots
    if (showDots) {
      people.forEach((p) => {
        const pt = project(p.lon, p.lat);
        if (!pt) return;
        const total = (p.sent || 0) + (p.received || 0);
        const radius = Math.max(1.5, Math.min(5, 1.5 + Math.sqrt(total) * 0.2));

        ctx.beginPath();
        ctx.arc(pt.x, pt.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = roleColor(p.role);
        ctx.globalAlpha = 0.85;
        ctx.fill();
        ctx.strokeStyle = '#1a1a2e';
        ctx.lineWidth = 0.8;
        ctx.globalAlpha = 1;
        ctx.stroke();
      });
    }

    // Draw historical events
    if (showEvents) {
      const visibleEvents = events.filter(
        (ev) => ev.year <= year && ev.lon != null && ev.lat != null,
      );

      visibleEvents.forEach((ev) => {
        const pt = project(ev.lon, ev.lat);
        if (!pt) return;
        const age = year - ev.year;
        const baseOpacity = age <= 15 ? 1 : Math.max(0.28, 1 - (age - 15) / 55);

        // Pulse ring for recent events
        if (age <= 20) {
          const pulseR = 4 + Math.sin(Date.now() / 300) * 3;
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, pulseR, 0, Math.PI * 2);
          ctx.strokeStyle = '#e74c3c';
          ctx.lineWidth = 1.5;
          ctx.globalAlpha = baseOpacity * 0.5;
          ctx.stroke();
        }

        // Event dot
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#e74c3c';
        ctx.globalAlpha = baseOpacity;
        ctx.fill();
        ctx.strokeStyle = '#ff8080';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Event label
        ctx.globalAlpha = Math.min(baseOpacity, 0.85);
        ctx.font = 'italic 8px Georgia, serif';
        ctx.fillStyle = '#ff9f9f';
        ctx.fillText(ev.short, pt.x + 7, pt.y + 3);

        ctx.globalAlpha = Math.min(baseOpacity * 0.75, 0.7);
        ctx.font = 'bold 7.5px Georgia, serif';
        ctx.fillStyle = '#c0392b';
        ctx.fillText(`${ev.year} AD`, pt.x + 7, pt.y + 11);
      });
    }

    ctx.globalAlpha = 1;

    // Update stats
    onStatsChange?.({
      visible: yearLetters.length,
      total: letters.length,
      people: people.length,
    });

    // Event banner
    const banner = bannerRef.current;
    const justArrived = events.find(
      (ev) => ev.year === year && ev.year !== dataRef.current.lastBannerYear,
    );
    if (justArrived && banner) {
      dataRef.current.lastBannerYear = justArrived.year;
      const yearSpan = banner.querySelector('.ev-year') as HTMLElement;
      const descSpan = banner.querySelector('.ev-desc') as HTMLElement;
      if (yearSpan) yearSpan.textContent = `${justArrived.year} AD \u2014`;
      if (descSpan) descSpan.textContent = ` ${justArrived.label}`;
      banner.style.opacity = '1';
      if (dataRef.current.bannerTimer) clearTimeout(dataRef.current.bannerTimer);
      dataRef.current.bannerTimer = setTimeout(() => {
        if (banner) banner.style.opacity = '0';
      }, 3500);
    }
  }, [
    windowSize,
    filterCollection,
    wymanMode,
    showTrail,
    arcOpacity,
    showDots,
    showEvents,
    speed,
    onStatsChange,
  ]);

  // ── Animation loop - driven by MapLibre's render cycle ─────────────

  const startRenderLoop = useCallback(() => {
    // Rendering is now driven by map.on('render') - just trigger the first repaint
    mapRef.current?.triggerRepaint();
  }, []);

  const stopRenderLoop = useCallback(() => {
    if (dataRef.current.animationFrame) {
      cancelAnimationFrame(dataRef.current.animationFrame);
      dataRef.current.animationFrame = null;
    }
  }, []);

  // ── Set year (main update) ─────────────────────────────────────────
  const setYearAndRender = useCallback(
    (year: number) => {
      const clamped = Math.min(YEAR_MAX, Math.max(YEAR_MIN, year));
      onYearChange(clamped);
    },
    [onYearChange],
  );

  // ── Play/pause logic ───────────────────────────────────────────────
  useEffect(() => {
    if (isPlaying) {
      const tickMs = Math.max(40, 1000 / (speed * 5));
      playRef.current = setInterval(() => {
        const yr = currentYearRef.current;
        if (yr >= YEAR_MAX) {
          onPlayingChange(false);
          return;
        }
        setYearAndRender(yr + 1);
      }, tickMs);
    } else {
      if (playRef.current) {
        clearInterval(playRef.current);
        playRef.current = null;
      }
    }
    return () => {
      if (playRef.current) {
        clearInterval(playRef.current);
        playRef.current = null;
      }
    };
  }, [isPlaying, speed, setYearAndRender, onPlayingChange]);

  // ── Re-render on option changes - trigger MapLibre render cycle ─────
  useEffect(() => {
    if (loading) return;
    // Trigger MapLibre repaint which will call our render callback
    mapRef.current?.triggerRepaint();
  }, [
    currentYear,
    filterCollection,
    arcOpacity,
    showTrail,
    windowSize,
    showEvents,
    showDots,
    wymanMode,
    loading,
    renderCanvas,
  ]);

  // ── Initialize map ─────────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          'dare-tiles': {
            type: 'raster',
            tiles: [DARE_TILE_URL],
            tileSize: 256,
            attribution: '&copy; <a href="https://dh.gu.se/dare/" target="_blank">DARE</a> Johan Åhlfeldt, University of Gothenburg (CC BY 4.0)',
            maxzoom: 11,
          },
        },
        layers: [
          {
            id: 'background',
            type: 'background',
            paint: { 'background-color': '#0a1628' },
          },
          {
            id: 'dare-tiles',
            type: 'raster',
            source: 'dare-tiles',
            paint: {
              'raster-opacity': 0.9,
              'raster-brightness-max': 0.85,
              'raster-contrast': 0.1,
              'raster-saturation': -0.15,
            },
          },
        ],
        glyphs: 'https://fonts.openmaptiles.org/{fontstack}/{range}.pbf',
      },
      center: MED_CENTER,
      zoom: MED_ZOOM,
      maxBounds: MED_BOUNDS,
      minZoom: 3,
      maxZoom: 11,
      attributionControl: false,
    });

    map.addControl(
      new maplibregl.AttributionControl({ compact: true }),
      'bottom-right',
    );
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');

    mapRef.current = map;
    console.log('MapLibre initialized, container size:', containerRef.current?.clientWidth, 'x', containerRef.current?.clientHeight);

    // Handle tile load errors - fall back to Stamen terrain if DARE tiles fail
    let tileErrorCount = 0;
    map.on('error', (e) => {
      if (e.error?.message?.includes('dh.gu.se') || e.error?.status === 404) {
        tileErrorCount++;
        if (tileErrorCount === 3) {
          console.warn('DARE tiles failing, adding OSM fallback');
          try {
            map.addSource('osm-fallback', {
              type: 'raster',
              tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
              tileSize: 256,
              attribution: '&copy; OpenStreetMap contributors',
              maxzoom: 19,
            });
            // Insert OSM between background and DARE so it shows through where DARE is missing
            map.addLayer(
              {
                id: 'osm-fallback',
                type: 'raster',
                source: 'osm-fallback',
                paint: {
                  'raster-opacity': 0.5,
                  'raster-saturation': -0.7,
                  'raster-brightness-max': 0.5,
                },
              },
              'dare-tiles',
            );
          } catch {
            // Ignore errors during fallback setup
          }
        }
      }
    });

    map.on('load', () => {
      // Load all data
      Promise.all([
        fetch('/data/map-letters.json').then((r) => r.json()),
        fetch('/data/historical-events.json').then((r) => r.json()),
        fetch('/data/timeline.json').then((r) => r.json()),
        fetch('/data/hub-cities.json').then((r) => r.json()).catch(() => [] as HubCity[]),
      ])
        .then(([mapData, events, timeline, hubCities]: [
          { letters: MapLetter[]; people: MapPerson[] },
          HistoricalEvent[],
          TimelineRow[],
          HubCity[],
        ]) => {
          dataRef.current.letters = mapData.letters;
          dataRef.current.people = mapData.people;
          dataRef.current.events = events;
          dataRef.current.timeline = timeline;
          dataRef.current.hubCities = hubCities;

          // Collections
          const cols = [...new Set(mapData.letters.map((l) => l.collection))].sort();
          onCollectionsLoaded?.(cols);
          onEventsLoaded?.(events);
          onTimelineLoaded?.(timeline);
          onStatsChange?.({ visible: 0, total: mapData.letters.length, people: mapData.people.length });

          // Try loading road network
          fetch(AWMC_ROADS_URL)
            .then((r) => {
              if (!r.ok) throw new Error('Roads not available yet');
              return r.json();
            })
            .then((roadsGeoJSON) => {
              // Add roads as a GeoJSON source
              map.addSource('roman-roads', {
                type: 'geojson',
                data: roadsGeoJSON,
              });

              // Road glow (behind the main line for a soft bloom effect)
              map.addLayer({
                id: 'roads-major-glow',
                type: 'line',
                source: 'roman-roads',
                filter: ['==', ['get', 'm'], 1],
                paint: {
                  'line-color': '#dab44e',
                  'line-width': [
                    'interpolate', ['linear'], ['zoom'],
                    3, 5, 4, 7, 5, 9, 8, 14, 11, 18,
                  ],
                  'line-opacity': 0.15,
                  'line-blur': 5,
                },
              });

              // Major roads (m=1) - prominent gold lines
              map.addLayer({
                id: 'roads-major',
                type: 'line',
                source: 'roman-roads',
                filter: ['==', ['get', 'm'], 1],
                paint: {
                  'line-color': '#dab44e',
                  'line-width': [
                    'interpolate', ['linear'], ['zoom'],
                    3, 1.2, 4, 1.8, 5, 2.5, 7, 3.5, 10, 5.0,
                  ],
                  'line-opacity': [
                    'interpolate', ['linear'], ['zoom'],
                    3, 0.6, 4, 0.7, 5, 0.8, 8, 0.9,
                  ],
                },
                layout: {
                  'line-cap': 'round',
                  'line-join': 'round',
                },
              });

              // Minor roads (m=0)
              map.addLayer({
                id: 'roads-minor',
                type: 'line',
                source: 'roman-roads',
                filter: ['==', ['get', 'm'], 0],
                paint: {
                  'line-color': '#c9a040',
                  'line-width': [
                    'interpolate', ['linear'], ['zoom'],
                    3, 0.4, 4, 0.7, 5, 1.0, 7, 1.8, 10, 2.5,
                  ],
                  'line-opacity': [
                    'interpolate', ['linear'], ['zoom'],
                    3, 0.3, 4, 0.4, 5, 0.5, 8, 0.6,
                  ],
                  'line-dasharray': [4, 3],
                },
                layout: {
                  'line-cap': 'round',
                  'line-join': 'round',
                },
              });

              dataRef.current.roadsLoaded = true;
              console.log(`Roman roads GeoJSON loaded: ${roadsGeoJSON.features.length} features`);

              // Build road network graph for route-finding
              const net = buildRoadNetwork(roadsGeoJSON);
              dataRef.current.roadNetwork = net;
              console.log(`Road network: ${net.nodes.length} nodes, ${net.grid.size} grid cells`);

              // Pre-compute routes for all letters (async batch to avoid blocking)
              const letters = dataRef.current.letters;
              let batchIdx = 0;
              const batchSize = 200;
              let roadRoutes = 0;
              let seaRoutes = 0;
              let fallbackArcs = 0;
              let noStartNode = 0;
              let noEndNode = 0;
              let noPath = 0;
              let hybridRoutes = 0;
              function computeBatch() {
                const end = Math.min(batchIdx + batchSize, letters.length);
                for (let i = batchIdx; i < end; i++) {
                  const l = letters[i];
                  if (!letterRouteCache.has(l.id)) {
                    // Detailed tracking: check why road routing fails
                    const startNode = findNearestNode(net, l.s_lon, l.s_lat);
                    const endNode = findNearestNode(net, l.r_lon, l.r_lat);

                    const route = getLetterRoute(net, l.s_lon, l.s_lat, l.r_lon, l.r_lat, l.id);
                    const distKm = routeDistanceKm(route.coords);
                    letterRouteCache.set(l.id, { coords: route.coords, isSea: route.isSea, distKm, roadPath: route.roadPath });

                    // Record road segment traffic for heatmap
                    if (route.roadPath && route.roadPath.length >= 2) {
                      recordSegmentTraffic(l.id, route.roadPath);
                    }

                    if (route.isSea && route.roadPath) {
                      hybridRoutes++;
                    } else if (route.isSea) {
                      seaRoutes++;
                    } else if (route.coords.length > 2) {
                      roadRoutes++;
                    } else {
                      fallbackArcs++;
                      if (startNode === null) noStartNode++;
                      else if (endNode === null) noEndNode++;
                      else noPath++;
                    }
                  }
                }
                batchIdx = end;
                if (batchIdx < letters.length) {
                  requestAnimationFrame(computeBatch);
                } else {
                  console.log(`Routes computed for ${letterRouteCache.size} letters: ${roadRoutes} road, ${seaRoutes} sea, ${hybridRoutes} hybrid (road+sea), ${fallbackArcs} fallback straight-line`);
                  console.log(`Road segment traffic: ${roadSegmentTraffic.size} unique segments tracked`);
                  if (fallbackArcs > 0) {
                    console.log(`Fallback reasons: ${noStartNode} no start node, ${noEndNode} no end node, ${noPath} no path found (A* exhausted)`);
                  }
                }
              }
              computeBatch();
            })
            .catch(() => {
              console.log('Roman road data not yet available at', AWMC_ROADS_URL);
            });

          // Add hub city markers
          const hubFeatures = hubCities.map((hub) => ({
            type: 'Feature' as const,
            geometry: {
              type: 'Point' as const,
              coordinates: [hub.lon, hub.lat],
            },
            properties: {
              name: hub.name,
              total: hub.total_sent + hub.total_received,
            },
          }));

          map.addSource('hub-cities', {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: hubFeatures },
          });

          map.addLayer({
            id: 'hub-cities-glow',
            type: 'circle',
            source: 'hub-cities',
            paint: {
              'circle-radius': 8,
              'circle-color': '#c9a959',
              'circle-opacity': 0.15,
              'circle-blur': 1,
            },
          });

          map.addLayer({
            id: 'hub-cities-dots',
            type: 'circle',
            source: 'hub-cities',
            paint: {
              'circle-radius': 4,
              'circle-color': '#c9a959',
              'circle-stroke-color': '#e8c878',
              'circle-stroke-width': 1,
            },
          });

          map.addLayer({
            id: 'hub-cities-labels',
            type: 'symbol',
            source: 'hub-cities',
            layout: {
              'text-field': ['get', 'name'],
              'text-font': ['Open Sans Regular'],
              'text-size': 10,
              'text-offset': [0.8, 0],
              'text-anchor': 'left',
            },
            paint: {
              'text-color': '#c9a959',
              'text-opacity': 0.8,
              'text-halo-color': '#0a1628',
              'text-halo-width': 1,
            },
          });

          // Hub city click handler
          map.on('click', 'hub-cities-dots', (e) => {
            if (e.features && e.features[0]) {
              const name = e.features[0].properties?.name;
              const hub = hubCities.find((h) => h.name === name);
              if (hub) onHubCityClick?.(hub);
            }
          });

          map.on('mouseenter', 'hub-cities-dots', () => {
            map.getCanvas().style.cursor = 'pointer';
          });
          map.on('mouseleave', 'hub-cities-dots', () => {
            map.getCanvas().style.cursor = '';
          });

          // People dot hover/click via hit-testing on MapLibre events
          map.on('mousemove', (e) => {
            const tooltip = tooltipRef.current;
            if (!tooltip) return;
            const { people, activeParticles } = dataRef.current;
            const mx = e.point.x;
            const my = e.point.y;

            // Check animated letter particles first (they're on top visually)
            let foundParticle: ActiveParticle | null = null;
            const particleHitRadius = 12;
            for (const ap of activeParticles) {
              const dx = ap.x - mx;
              const dy = ap.y - my;
              if (dx * dx + dy * dy <= particleHitRadius * particleHitRadius) {
                foundParticle = ap;
                break;
              }
            }

            if (foundParticle) {
              map.getCanvas().style.cursor = 'pointer';
              const nameEl = tooltip.querySelector('.tt-name') as HTMLElement;
              const infoEl = tooltip.querySelector('.tt-info') as HTMLElement;
              const l = foundParticle.letter;
              if (nameEl) nameEl.textContent = `${l.sender_name} \u2192 ${l.recipient_name}`;
              if (infoEl) {
                const summary = l.quick_summary
                  ? (l.quick_summary.length > 100 ? l.quick_summary.slice(0, 100) + '\u2026' : l.quick_summary)
                  : '';
                infoEl.innerHTML = `~${l.year_approx} AD \u00b7 ${l.collection.replace(/_/g, ' ')}${summary ? `<br/><span style="color:#aab8c8;font-style:italic">${summary}</span>` : ''}<br/><span style="color:var(--color-accent)">Click to read \u2192</span>`;
              }
              tooltip.style.opacity = '1';
              tooltip.style.left = `${mx + 12}px`;
              tooltip.style.top = `${my - 10}px`;
              return;
            }

            // Check people dots
            let found: MapPerson | null = null;
            for (const p of people) {
              const pt = map.project([p.lon, p.lat]);
              const dx = pt.x - mx;
              const dy = pt.y - my;
              const total = (p.sent || 0) + (p.received || 0);
              const radius = Math.max(4, Math.min(8, 3 + Math.sqrt(total) * 0.3));
              if (dx * dx + dy * dy <= radius * radius) {
                found = p;
                break;
              }
            }

            if (found) {
              map.getCanvas().style.cursor = 'pointer';
              const nameEl = tooltip.querySelector('.tt-name') as HTMLElement;
              const infoEl = tooltip.querySelector('.tt-info') as HTMLElement;
              if (nameEl) nameEl.textContent = found.name;
              if (infoEl) {
                const parts: string[] = [];
                if (found.role) parts.push(found.role);
                if (found.location) parts.push(found.location);
                parts.push(`${found.sent} sent, ${found.received} received`);
                infoEl.innerHTML = parts.join('<br/>');
              }
              tooltip.style.opacity = '1';
              tooltip.style.left = `${mx + 12}px`;
              tooltip.style.top = `${my - 10}px`;
            } else {
              // Only reset if not hovering a MapLibre interactive layer
              const features = map.queryRenderedFeatures(e.point, { layers: ['hub-cities-dots'] });
              if (!features.length) {
                map.getCanvas().style.cursor = '';
                tooltip.style.opacity = '0';
              }
            }
          });

          map.on('click', (e) => {
            const { people, activeParticles } = dataRef.current;
            const mx = e.point.x;
            const my = e.point.y;

            // Check animated letter particles first
            const particleHitRadius = 12;
            for (const ap of activeParticles) {
              const dx = ap.x - mx;
              const dy = ap.y - my;
              if (dx * dx + dy * dy <= particleHitRadius * particleHitRadius) {
                window.open(`/letters/${ap.letter.collection}/${ap.letter.letter_number}`, '_blank');
                return;
              }
            }

            // Check people dots
            for (const p of people) {
              const pt = map.project([p.lon, p.lat]);
              const dx = pt.x - mx;
              const dy = pt.y - my;
              const total = (p.sent || 0) + (p.received || 0);
              const radius = Math.max(4, Math.min(8, 3 + Math.sqrt(total) * 0.3));
              if (dx * dx + dy * dy <= radius * radius) {
                const slug = p.name
                  .toLowerCase()
                  .replace(/[^a-z0-9]+/g, '-')
                  .replace(/(^-|-$)/g, '');
                window.open(`/authors/${slug}`, '_blank');
                return;
              }
            }
          });

          // Political borders removed - need verified historical GeoJSON data

          // Setup canvas overlay
          const mapCanvas = map.getCanvas();
          const overlay = canvasRef.current;
          if (overlay) {
            overlay.width = mapCanvas.width;
            overlay.height = mapCanvas.height;
            overlay.style.width = mapCanvas.style.width;
            overlay.style.height = mapCanvas.style.height;
          }

          setLoading(false);
          onLoadingChange?.(false);

          // Start render loop
          startRenderLoop();
        })
        .catch((err) => {
          console.error('Failed to load map data:', err);
          setError(err.message);
          onError?.(err.message);
          setLoading(false);
          onLoadingChange?.(false);
        });
    });

    // Sync canvas to MapLibre's render cycle - eliminates smearing
    map.on('render', () => {
      renderCanvas();
      // Keep requesting repaints while playing (for particle animation)
      if (playRef.current) {
        map.triggerRepaint();
      }
    });

    // Resize canvas with map
    const resizeObserver = new ResizeObserver(() => {
      renderCanvas();
      map.triggerRepaint();
    });
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      stopRenderLoop();
      resizeObserver.disconnect();
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Keyboard shortcuts ─────────────────────────────────────────────
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;

      if (e.code === 'Space') {
        e.preventDefault();
        if (isPlaying) {
          onPlayingChange(false);
        } else {
          if (currentYearRef.current >= YEAR_MAX) {
            setYearAndRender(YEAR_START);
          }
          onPlayingChange(true);
        }
      } else if (e.code === 'ArrowRight') {
        onPlayingChange(false);
        setYearAndRender(currentYearRef.current + 5);
      } else if (e.code === 'ArrowLeft') {
        onPlayingChange(false);
        setYearAndRender(currentYearRef.current - 5);
      } else if (e.code === 'KeyR') {
        onPlayingChange(false);
        dataRef.current.lastBannerYear = null;
        if (bannerRef.current) bannerRef.current.style.opacity = '0';
        setYearAndRender(YEAR_START);
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isPlaying, setYearAndRender, onPlayingChange]);

  // ── Render ─────────────────────────────────────────────────────────

  return (
    <div className="relative w-full h-full" style={{ background: '#0a1628', minHeight: 500 }}>
      {/* Loading */}
      {loading && (
        <div
          className="absolute inset-0 flex flex-col items-center justify-center gap-3.5 z-50"
          style={{ background: 'rgba(10,22,40,0.9)' }}
        >
          {error ? (
            <>
              <p style={{ color: '#e74c3c', fontSize: '1.1em' }}>Error loading data</p>
              <small style={{ color: '#8899aa' }}>{error}</small>
            </>
          ) : (
            <>
              <div className="map-spinner" />
              <p
                style={{
                  color: 'var(--color-accent)',
                  fontSize: '1.1em',
                  letterSpacing: 1,
                  fontFamily: 'var(--font-serif)',
                }}
              >
                Loading the Roman World...
              </p>
              <small style={{ color: '#8899aa' }}>
                Initializing DARE historical map tiles
              </small>
            </>
          )}
        </div>
      )}

      {/* MapLibre container */}
      <div ref={containerRef} className="absolute inset-0" style={{ minHeight: 500, width: '100%' }} />

      {/* Canvas overlay for arcs, dots, events */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 pointer-events-none"
        style={{ zIndex: 10 }}
      />

      {/* Tooltip */}
      <div
        ref={tooltipRef}
        style={{
          position: 'absolute',
          background: 'rgba(22, 33, 62, 0.95)',
          border: '1px solid var(--color-accent)',
          padding: '10px 14px',
          borderRadius: 6,
          fontSize: '0.8em',
          pointerEvents: 'none',
          opacity: 0,
          transition: 'opacity 0.15s',
          maxWidth: 280,
          zIndex: 300,
          fontFamily: 'var(--font-sans)',
        }}
      >
        <div
          className="tt-name"
          style={{ color: 'var(--color-accent)', fontWeight: 'bold', marginBottom: 4 }}
        />
        <div className="tt-info" style={{ color: '#8899aa', lineHeight: 1.5 }} />
      </div>

      {/* Event banner */}
      <div
        ref={bannerRef}
        style={{
          position: 'absolute',
          top: 12,
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(120, 20, 20, 0.88)',
          border: '1px solid #c0392b',
          borderRadius: 6,
          padding: '6px 16px',
          fontSize: '0.8em',
          color: '#ffc8c8',
          zIndex: 160,
          pointerEvents: 'none',
          opacity: 0,
          transition: 'opacity 0.5s ease',
          maxWidth: 480,
          textAlign: 'center',
          whiteSpace: 'nowrap',
          fontFamily: 'var(--font-sans)',
        }}
      >
        <span
          className="ev-year"
          style={{ color: '#ff8080', fontWeight: 'bold', marginRight: 6 }}
        />
        <span className="ev-desc" />
      </div>

      {/* CSS */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .map-spinner {
          width: 40px;
          height: 40px;
          border: 3px solid #2a3a5c;
          border-top-color: var(--color-accent);
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }
        .maplibregl-ctrl-attrib {
          font-size: 10px !important;
          background: rgba(10, 22, 40, 0.7) !important;
          color: #5a7a9a !important;
        }
        .maplibregl-ctrl-attrib a {
          color: #7a9aba !important;
        }
      `}</style>
    </div>
  );
}

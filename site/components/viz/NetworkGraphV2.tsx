'use client';

import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { select } from 'd3-selection';
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
  forceX,
  forceY,
  type SimulationNodeDatum,
  type SimulationLinkDatum,
} from 'd3-force';
import { zoom, zoomIdentity, type ZoomBehavior } from 'd3-zoom';
import { scaleLinear, scaleSqrt } from 'd3-scale';
import { drag } from 'd3-drag';
import type { SelectedNode } from './NetworkGraphLoader';
import { WYMAN_EXCLUDED_COLLECTIONS, WYMAN_YEAR_MIN, WYMAN_YEAR_MAX } from './map-types';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface NetworkNode extends SimulationNodeDatum {
  id: number;
  name: string;
  role: string | null;
  location: string | null;
  lat: number | null;
  lon: number | null;
  birth_year: number | null;
  death_year: number | null;
  bio: string | null;
  letters_sent: number;
  letters_received: number;
  // Computed
  region?: string;
  totalLetters?: number;
  degree?: number;
}

interface NetworkEdge extends SimulationLinkDatum<NetworkNode> {
  source: number | NetworkNode;
  target: number | NetworkNode;
  weight: number;
  collection: string;
}

interface NetworkData {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  collections: { collection: string; count: number }[];
}

export interface NetworkGraphV2Props {
  onNodeClick?: (node: SelectedNode) => void;
  wymanMode?: boolean;
}

/* ------------------------------------------------------------------ */
/*  Region classification by lat/lon                                   */
/* ------------------------------------------------------------------ */

const REGIONS = {
  'Italy': { color: '#c9a959', cx: 0, cy: 0 },
  'Gaul & Britain': { color: '#5b8c5a', cx: -1, cy: -1 },
  'Iberia': { color: '#e67e22', cx: -1.5, cy: 0.5 },
  'North Africa': { color: '#e74c3c', cx: -0.5, cy: 1 },
  'Eastern Mediterranean': { color: '#3b82f6', cx: 1, cy: 0 },
  'Unknown': { color: '#6b7b8d', cx: 0, cy: -1 },
} as const;

type RegionName = keyof typeof REGIONS;

const regionColors = Object.fromEntries(
  Object.entries(REGIONS).map(([k, v]) => [k, v.color])
);

function classifyRegion(lat: number | null, lon: number | null, location: string | null): RegionName {
  // Text-based fallback
  const loc = (location ?? '').toLowerCase();
  if (loc.includes('rome') || loc.includes('raven') || loc.includes('milan') || loc.includes('pavia') || loc.includes('naples') || loc.includes('italy') || loc.includes('sicily') || loc.includes('sardinia')) return 'Italy';
  if (loc.includes('gaul') || loc.includes('lyon') || loc.includes('arles') || loc.includes('metz') || loc.includes('trier') || loc.includes('clermont') || loc.includes('tours') || loc.includes('provence') || loc.includes('cahors') || loc.includes('paris') || loc.includes('autun') || loc.includes('britain') || loc.includes('auxerre') || loc.includes('vienne') || loc.includes('poitiers') || loc.includes('reims') || loc.includes('bordeaux') || loc.includes('rouen') || loc.includes('sens')) return 'Gaul & Britain';
  if (loc.includes('toledo') || loc.includes('seville') || loc.includes('spain') || loc.includes('iberia') || loc.includes('braga') || loc.includes('tarragona') || loc.includes('merida')) return 'Iberia';
  if (loc.includes('hippo') || loc.includes('carthage') || loc.includes('africa') || loc.includes('numidia') || loc.includes('cyrene') || loc.includes('cyrenaica') || loc.includes('libya') || loc.includes('ptolemais') || loc.includes('egypt') || loc.includes('alexandria') || loc.includes('pelusium')) return 'North Africa';
  if (loc.includes('antioch') || loc.includes('constantinople') || loc.includes('caesarea') || loc.includes('cyrrhus') || loc.includes('jerusalem') || loc.includes('cappadocia') || loc.includes('syria') || loc.includes('asia minor') || loc.includes('ephesus') || loc.includes('palestine')) return 'Eastern Mediterranean';

  // Lat/lon based
  if (lat != null && lon != null) {
    if (lat < 32) return 'North Africa';
    if (lon > 28) return 'Eastern Mediterranean';
    if (lon < -3) return 'Iberia';
    if (lat > 43 && lon < 8) return 'Gaul & Britain';
    if (lon >= 8 && lon <= 20 && lat >= 36 && lat <= 47) return 'Italy';
    if (lat >= 32 && lon >= 20 && lon <= 40) return 'Eastern Mediterranean';
    if (lat >= 32 && lon < 20 && lat < 37) return 'North Africa';
    if (lat >= 43) return 'Gaul & Britain';
    return 'Italy'; // Mediterranean default
  }

  return 'Unknown';
}

function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

/* ------------------------------------------------------------------ */
/*  Century helper                                                     */
/* ------------------------------------------------------------------ */

function getCentury(node: NetworkNode): number | null {
  const year = node.birth_year ?? node.death_year;
  if (year == null) return null;
  // Use the middle of their active period
  const mid = node.birth_year && node.death_year
    ? Math.round((node.birth_year + node.death_year) / 2)
    : year;
  return Math.floor(mid / 100) + 1;
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function NetworkGraphV2({ onNodeClick, wymanMode = false }: NetworkGraphV2Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const zoomRef = useRef<ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const simRef = useRef<ReturnType<typeof forceSimulation<NetworkNode>> | null>(null);

  const [data, setData] = useState<NetworkData | null>(null);
  const [loading, setLoading] = useState(true);
  const [nodeLimit, setNodeLimit] = useState(150);
  const [minEdgeWeight, setMinEdgeWeight] = useState(2);
  const [centuryFilter, setCenturyFilter] = useState<number | ''>('');
  const [regionFilter, setRegionFilter] = useState<string>('');
  const [highlightedNode, setHighlightedNode] = useState<number | null>(null);

  // Fetch data
  useEffect(() => {
    fetch('/data/network.json')
      .then((r) => r.json())
      .then((d: NetworkData) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Process data: assign regions, compute degrees, filter
  const processed = useMemo(() => {
    if (!data) return null;

    // Deep copy nodes, assign regions and totals
    const allNodes = data.nodes.map((n) => ({
      ...n,
      region: classifyRegion(n.lat, n.lon, n.location),
      totalLetters: n.letters_sent + n.letters_received,
      degree: 0,
    }));

    // Filter edges
    let edges = data.edges.map((e) => ({ ...e }));
    if (wymanMode) {
      edges = edges.filter((e) => !WYMAN_EXCLUDED_COLLECTIONS.has(e.collection));
    }

    // Aggregate edges by source+target
    const edgeMap = new Map<string, NetworkEdge>();
    for (const e of edges) {
      const s = typeof e.source === 'object' ? (e.source as NetworkNode).id : e.source;
      const t = typeof e.target === 'object' ? (e.target as NetworkNode).id : e.target;
      const key = `${Math.min(s as number, t as number)}-${Math.max(s as number, t as number)}`;
      if (edgeMap.has(key)) {
        edgeMap.get(key)!.weight += e.weight;
      } else {
        edgeMap.set(key, { ...e, source: s, target: t });
      }
    }
    const aggregatedEdges = Array.from(edgeMap.values());

    // Compute degree (number of connections per node, weighted)
    const nodeMap = new Map(allNodes.map((n) => [n.id, n]));
    for (const e of aggregatedEdges) {
      const s = typeof e.source === 'number' ? e.source : (e.source as NetworkNode).id;
      const t = typeof e.target === 'number' ? e.target : (e.target as NetworkNode).id;
      if (nodeMap.has(s)) nodeMap.get(s)!.degree! += e.weight;
      if (nodeMap.has(t)) nodeMap.get(t)!.degree! += e.weight;
    }

    // Wyman date filter
    if (wymanMode) {
      const wymanNodeIds = new Set<number>();
      for (const n of allNodes) {
        const active = (n.birth_year ?? 0) <= WYMAN_YEAR_MAX &&
          (n.death_year ?? WYMAN_YEAR_MAX) >= WYMAN_YEAR_MIN;
        if (active) wymanNodeIds.add(n.id);
      }
      return {
        allNodes: allNodes.filter((n) => wymanNodeIds.has(n.id)),
        allEdges: aggregatedEdges,
      };
    }

    return { allNodes, allEdges: aggregatedEdges };
  }, [data, wymanMode]);

  // Available centuries for filter
  const centuries = useMemo(() => {
    if (!processed) return [];
    const set = new Set<number>();
    for (const n of processed.allNodes) {
      const c = getCentury(n);
      if (c) set.add(c);
    }
    return Array.from(set).sort();
  }, [processed]);

  // Available regions
  const regions = useMemo(() => {
    if (!processed) return [];
    const set = new Set<string>();
    for (const n of processed.allNodes) {
      if (n.region) set.add(n.region);
    }
    return Array.from(set).sort();
  }, [processed]);

  // Reset zoom handler
  const handleResetZoom = useCallback(() => {
    if (!svgRef.current || !zoomRef.current) return;
    const svg = select(svgRef.current);
    svg
      .transition()
      .duration(500)
      .call(zoomRef.current.transform, zoomIdentity.translate(0, 0).scale(0.7));
  }, []);

  // Main render
  const renderGraph = useCallback(() => {
    if (!processed || !svgRef.current || !containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Filter edges by minimum weight
    let edges = processed.allEdges.filter((e) => e.weight >= minEdgeWeight);

    // Get node IDs that appear in filtered edges
    const edgeNodeIds = new Set<number>();
    for (const e of edges) {
      const s = typeof e.source === 'number' ? e.source : (e.source as NetworkNode).id;
      const t = typeof e.target === 'number' ? e.target : (e.target as NetworkNode).id;
      edgeNodeIds.add(s);
      edgeNodeIds.add(t);
    }

    // Filter nodes
    let filteredNodes = processed.allNodes.filter((n) => edgeNodeIds.has(n.id));

    // Century filter
    if (centuryFilter) {
      filteredNodes = filteredNodes.filter((n) => getCentury(n) === centuryFilter);
    }

    // Region filter
    if (regionFilter) {
      filteredNodes = filteredNodes.filter((n) => n.region === regionFilter);
    }

    // Sort by degree (total connectivity) and take top N
    filteredNodes.sort((a, b) => (b.degree ?? 0) - (a.degree ?? 0));
    const topNodes = filteredNodes.slice(0, nodeLimit);
    const topNodeIds = new Set(topNodes.map((n) => n.id));

    // Filter edges to only connect visible nodes
    edges = edges.filter((e) => {
      const s = typeof e.source === 'number' ? e.source : (e.source as NetworkNode).id;
      const t = typeof e.target === 'number' ? e.target : (e.target as NetworkNode).id;
      return topNodeIds.has(s) && topNodeIds.has(t);
    });

    // Deep copy for simulation
    const nodes: NetworkNode[] = topNodes.map((n) => ({ ...n }));
    const simEdges: NetworkEdge[] = edges.map((e) => ({ ...e }));

    // Clear SVG
    const svg = select(svgRef.current);
    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', height);

    // Defs for edge gradient and glow
    const defs = svg.append('defs');

    // Glow filter for highlighted nodes
    const filter = defs.append('filter').attr('id', 'glow');
    filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur');
    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    const g = svg.append('g');

    // Zoom
    const zoomBehavior = zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 8])
      .on('zoom', (event) => g.attr('transform', event.transform));
    svg.call(zoomBehavior);
    zoomRef.current = zoomBehavior;

    if (nodes.length === 0) {
      svg
        .append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', '#8899aa')
        .text('No nodes match current filters. Try adjusting settings.');
      return;
    }

    // Scales
    const maxWeight = Math.max(...simEdges.map((d) => d.weight), 1);
    const edgeWidthScale = scaleLinear().domain([1, maxWeight]).range([0.5, 8]);
    const edgeOpacityScale = scaleLinear().domain([1, maxWeight]).range([0.15, 0.6]);
    const maxLetters = Math.max(...nodes.map((d) => d.totalLetters ?? 1), 1);
    const nodeScale = scaleSqrt().domain([1, maxLetters]).range([5, 45]);
    const labelThreshold = Math.max(maxLetters * 0.05, 20); // Only label nodes above this

    // Cluster positions
    const clusterCenters: Record<string, { x: number; y: number }> = {};
    const regionSpread = Math.min(width, height) * 0.25;
    for (const [name, info] of Object.entries(REGIONS)) {
      clusterCenters[name] = {
        x: width / 2 + info.cx * regionSpread,
        y: height / 2 + info.cy * regionSpread,
      };
    }

    // Links layer
    const linkGroup = g.append('g').attr('class', 'links');
    const link = linkGroup
      .selectAll<SVGLineElement, NetworkEdge>('line')
      .data(simEdges)
      .join('line')
      .attr('stroke', '#4a5a7c')
      .attr('stroke-opacity', (d) => edgeOpacityScale(d.weight))
      .attr('stroke-width', (d) => edgeWidthScale(d.weight))
      .attr('stroke-linecap', 'round');

    // Node groups
    const nodeGroup = g.append('g').attr('class', 'nodes');
    const node = nodeGroup
      .selectAll<SVGGElement, NetworkNode>('g')
      .data(nodes, (d) => String(d.id))
      .join('g')
      .style('cursor', 'pointer');

    // Circles
    node
      .append('circle')
      .attr('r', (d) => nodeScale(d.totalLetters ?? 1))
      .attr('fill', (d) => regionColors[d.region as RegionName] ?? regionColors.Unknown)
      .attr('fill-opacity', 0.85)
      .attr('stroke', (d) => regionColors[d.region as RegionName] ?? regionColors.Unknown)
      .attr('stroke-opacity', 0.4)
      .attr('stroke-width', 2);

    // Labels - only for large/important nodes
    node
      .filter((d) => (d.totalLetters ?? 0) >= labelThreshold)
      .append('text')
      .attr('dx', (d) => nodeScale(d.totalLetters ?? 1) + 5)
      .attr('dy', 4)
      .attr('fill', '#d0c8b8')
      .attr('font-size', (d) => {
        const t = d.totalLetters ?? 0;
        if (t > maxLetters * 0.5) return '13px';
        if (t > maxLetters * 0.2) return '11px';
        return '10px';
      })
      .attr('font-family', "'Merriweather', Georgia, serif")
      .attr('font-weight', (d) => (d.totalLetters ?? 0) > maxLetters * 0.3 ? '700' : '400')
      .attr('pointer-events', 'none')
      .text((d) => {
        // Shorten long names
        const name = d.name;
        if (name.length > 20) return name.slice(0, 18) + '\u2026';
        return name;
      });

    // Simulation with cluster force
    const sim = forceSimulation<NetworkNode>(nodes)
      .force(
        'link',
        forceLink<NetworkNode, NetworkEdge>(simEdges)
          .id((d) => d.id)
          .distance((d) => 100 / Math.sqrt(d.weight))
          .strength((d) => Math.min(0.7, (d.weight / maxWeight) * 1.5)),
      )
      .force(
        'charge',
        forceManyBody<NetworkNode>().strength(
          (d) => -100 - nodeScale(d.totalLetters ?? 1) * 8,
        ),
      )
      .force('center', forceCenter(width / 2, height / 2).strength(0.05))
      .force(
        'collision',
        forceCollide<NetworkNode>().radius(
          (d) => nodeScale(d.totalLetters ?? 1) + 12,
        ).strength(0.8),
      )
      // Cluster force: pull nodes toward their region center
      .force(
        'clusterX',
        forceX<NetworkNode>((d) => clusterCenters[d.region ?? 'Unknown']?.x ?? width / 2).strength(0.15),
      )
      .force(
        'clusterY',
        forceY<NetworkNode>((d) => clusterCenters[d.region ?? 'Unknown']?.y ?? height / 2).strength(0.15),
      )
      .on('tick', () => {
        link
          .attr('x1', (d) => ((d.source as NetworkNode).x ?? 0))
          .attr('y1', (d) => ((d.source as NetworkNode).y ?? 0))
          .attr('x2', (d) => ((d.target as NetworkNode).x ?? 0))
          .attr('y2', (d) => ((d.target as NetworkNode).y ?? 0));
        node.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
      });

    simRef.current = sim;

    // Drag behavior
    const dragBehavior = drag<SVGGElement, NetworkNode>()
      .on('start', (event, d) => {
        if (!event.active) sim.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) sim.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });
    node.call(dragBehavior);

    // Tooltip
    const tooltip = tooltipRef.current;
    node
      .on('mouseover', (event, d) => {
        if (!tooltip) return;
        tooltip.innerHTML = `
          <div style="font-family:'Merriweather',Georgia,serif;font-size:14px;color:var(--color-text);font-weight:700;margin-bottom:4px">${d.name}</div>
          <div style="font-family:'Inter',system-ui,sans-serif;font-size:12px;color:var(--color-muted);line-height:1.6">
            ${d.role ? `<span style="text-transform:capitalize">${d.role}</span> · ` : ''}${d.location || 'Unknown location'}<br/>
            <span style="color:${regionColors[d.region as RegionName] ?? regionColors.Unknown}">● ${d.region}</span><br/>
            ${d.birth_year ?? '?'}-${d.death_year ?? '?'} AD<br/>
            Sent: ${d.letters_sent} · Received: ${d.letters_received}
          </div>
        `;
        tooltip.style.opacity = '1';
        tooltip.style.left = event.pageX + 14 + 'px';
        tooltip.style.top = event.pageY - 12 + 'px';
      })
      .on('mousemove', (event) => {
        if (!tooltip) return;
        tooltip.style.left = event.pageX + 14 + 'px';
        tooltip.style.top = event.pageY - 12 + 'px';
      })
      .on('mouseout', () => {
        if (!tooltip) return;
        tooltip.style.opacity = '0';
      });

    // Click: highlight connections
    node.on('click', (_event, d) => {
      const nodeId = d.id;

      // Find connected node IDs
      const connectedIds = new Set<number>();
      connectedIds.add(nodeId);
      for (const e of simEdges) {
        const s = typeof e.source === 'object' ? (e.source as NetworkNode).id : (e.source as number);
        const t = typeof e.target === 'object' ? (e.target as NetworkNode).id : (e.target as number);
        if (s === nodeId) connectedIds.add(t);
        if (t === nodeId) connectedIds.add(s);
      }

      // Dim everything, then highlight connected
      node.select('circle')
        .transition()
        .duration(300)
        .attr('fill-opacity', (n) => connectedIds.has(n.id) ? 0.95 : 0.12)
        .attr('stroke-opacity', (n) => connectedIds.has(n.id) ? 0.8 : 0.05);
      node.select('text')
        .transition()
        .duration(300)
        .attr('fill-opacity', (n) => connectedIds.has(n.id) ? 1 : 0.1);

      // Highlight the clicked node with glow
      node.select('circle')
        .attr('filter', (n) => n.id === nodeId ? 'url(#glow)' : 'none');

      link
        .transition()
        .duration(300)
        .attr('stroke-opacity', (e) => {
          const s = typeof e.source === 'object' ? (e.source as NetworkNode).id : (e.source as number);
          const t = typeof e.target === 'object' ? (e.target as NetworkNode).id : (e.target as number);
          return (s === nodeId || t === nodeId) ? 0.7 : 0.03;
        })
        .attr('stroke', (e) => {
          const s = typeof e.source === 'object' ? (e.source as NetworkNode).id : (e.source as number);
          const t = typeof e.target === 'object' ? (e.target as NetworkNode).id : (e.target as number);
          return (s === nodeId || t === nodeId)
            ? (regionColors[d.region as RegionName] ?? '#c9a959')
            : '#4a5a7c';
        });

      setHighlightedNode(nodeId);

      // Fire callback
      if (onNodeClick) {
        onNodeClick({
          id: d.id,
          name: d.name,
          slug: toSlug(d.name),
          role: d.role,
          location: d.location,
          birth_year: d.birth_year,
          death_year: d.death_year,
          bio: d.bio,
          letters_sent: d.letters_sent,
          letters_received: d.letters_received,
        });
      }
    });

    // Click background to reset highlight
    svg.on('click', (event) => {
      if (event.target === svgRef.current) {
        node.select('circle')
          .transition()
          .duration(300)
          .attr('fill-opacity', 0.85)
          .attr('stroke-opacity', 0.4)
          .attr('filter', 'none');
        node.select('text')
          .transition()
          .duration(300)
          .attr('fill-opacity', 1);
        link
          .transition()
          .duration(300)
          .attr('stroke-opacity', (d) => edgeOpacityScale(d.weight))
          .attr('stroke', '#4a5a7c');
        setHighlightedNode(null);
      }
    });

    // Region labels (subtle background labels)
    const regionLabelGroup = g.append('g').attr('class', 'region-labels');
    const regionCounts: Record<string, number> = {};
    for (const n of nodes) {
      const r = n.region ?? 'Unknown';
      regionCounts[r] = (regionCounts[r] ?? 0) + 1;
    }
    for (const [name, center] of Object.entries(clusterCenters)) {
      if ((regionCounts[name] ?? 0) < 2) continue;
      regionLabelGroup
        .append('text')
        .attr('x', center.x)
        .attr('y', center.y - regionSpread * 0.55)
        .attr('text-anchor', 'middle')
        .attr('fill', regionColors[name as RegionName] ?? '#6b7b8d')
        .attr('fill-opacity', 0.25)
        .attr('font-size', '16px')
        .attr('font-family', "'Inter', system-ui, sans-serif")
        .attr('font-weight', '600')
        .attr('letter-spacing', '2px')
        .attr('text-transform', 'uppercase')
        .attr('pointer-events', 'none')
        .text(name.toUpperCase());
    }

    // Initial zoom
    svg.call(zoomBehavior.transform, zoomIdentity.translate(0, 0).scale(0.7));

    return () => {
      sim.stop();
    };
  }, [processed, nodeLimit, minEdgeWeight, centuryFilter, regionFilter, onNodeClick]);

  useEffect(() => {
    const cleanup = renderGraph();
    return () => cleanup?.();
  }, [renderGraph]);

  // Re-render on resize
  useEffect(() => {
    let resizeTimer: ReturnType<typeof setTimeout>;
    const handleResize = () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => renderGraph(), 200);
    };
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      clearTimeout(resizeTimer);
    };
  }, [renderGraph]);

  const totalVisible = useMemo(() => {
    if (!processed) return 0;
    let count = processed.allNodes.filter((n) => {
      if (centuryFilter && getCentury(n) !== centuryFilter) return false;
      if (regionFilter && n.region !== regionFilter) return false;
      return true;
    }).length;
    return count;
  }, [processed, centuryFilter, regionFilter]);

  return (
    <div ref={containerRef} className="relative w-full h-full" style={{ background: '#0f1520' }}>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center text-lg" style={{ color: 'var(--color-accent)' }}>
          Loading network data...
        </div>
      )}

      {/* Controls bar */}
      {data && (
        <div className="absolute top-3 left-3 right-3 z-10 flex items-center gap-2 flex-wrap">
          {/* Node density slider */}
          <div
            className="flex items-center gap-2 px-3 py-2 rounded-lg border text-sm"
            style={{
              background: 'var(--color-surface)',
              borderColor: 'var(--color-border)',
              color: 'var(--color-text)',
              fontFamily: 'var(--font-sans)',
            }}
          >
            <label className="whitespace-nowrap" style={{ color: 'var(--color-muted)', fontSize: '11px' }}>
              Nodes
            </label>
            <input
              type="range"
              min={10}
              max={Math.min(300, totalVisible)}
              value={nodeLimit}
              onChange={(e) => setNodeLimit(Number(e.target.value))}
              className="w-20 accent-[#c9a959]"
            />
            <span className="tabular-nums w-8 text-right" style={{ color: 'var(--color-accent)', fontSize: '12px' }}>
              {nodeLimit}
            </span>
          </div>

          {/* Min edge weight */}
          <div
            className="flex items-center gap-2 px-3 py-2 rounded-lg border text-sm"
            style={{
              background: 'var(--color-surface)',
              borderColor: 'var(--color-border)',
              color: 'var(--color-text)',
              fontFamily: 'var(--font-sans)',
            }}
          >
            <label className="whitespace-nowrap" style={{ color: 'var(--color-muted)', fontSize: '11px' }}>
              Min letters
            </label>
            <input
              type="range"
              min={1}
              max={20}
              value={minEdgeWeight}
              onChange={(e) => setMinEdgeWeight(Number(e.target.value))}
              className="w-16 accent-[#c9a959]"
            />
            <span className="tabular-nums w-6 text-right" style={{ color: 'var(--color-accent)', fontSize: '12px' }}>
              {minEdgeWeight}
            </span>
          </div>

          {/* Century filter */}
          <select
            value={centuryFilter}
            onChange={(e) => setCenturyFilter(e.target.value ? Number(e.target.value) : '')}
            className="px-3 py-2 text-sm rounded-lg border transition-colors"
            style={{
              background: 'var(--color-surface)',
              borderColor: 'var(--color-border)',
              color: 'var(--color-text)',
              fontFamily: 'var(--font-sans)',
            }}
          >
            <option value="">All centuries</option>
            {centuries.map((c) => (
              <option key={c} value={c}>
                {c}{c === 1 ? 'st' : c === 2 ? 'nd' : c === 3 ? 'rd' : 'th'} century
              </option>
            ))}
          </select>

          {/* Region filter */}
          <select
            value={regionFilter}
            onChange={(e) => setRegionFilter(e.target.value)}
            className="px-3 py-2 text-sm rounded-lg border transition-colors"
            style={{
              background: 'var(--color-surface)',
              borderColor: 'var(--color-border)',
              color: 'var(--color-text)',
              fontFamily: 'var(--font-sans)',
            }}
          >
            <option value="">All regions</option>
            {regions.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>

          {/* Reset zoom */}
          <button
            onClick={handleResetZoom}
            className="px-3 py-2 text-sm rounded-lg border transition-colors hover:opacity-90"
            style={{
              background: 'var(--color-surface)',
              borderColor: 'var(--color-border)',
              color: 'var(--color-text)',
              fontFamily: 'var(--font-sans)',
            }}
          >
            Reset zoom
          </button>
        </div>
      )}

      {/* Stats bar */}
      {data && (
        <div
          className="absolute bottom-3 left-3 z-10 px-3 py-1.5 rounded-lg text-xs"
          style={{
            background: 'rgba(15, 21, 32, 0.85)',
            color: 'var(--color-muted)',
            fontFamily: 'var(--font-sans)',
            backdropFilter: 'blur(4px)',
          }}
        >
          Showing top {Math.min(nodeLimit, totalVisible)} of {totalVisible} people
          {highlightedNode && ' · Click background to deselect'}
        </div>
      )}

      {/* Tooltip */}
      <div
        ref={tooltipRef}
        className="fixed pointer-events-none z-50 rounded-lg px-4 py-3 shadow-lg"
        style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          opacity: 0,
          transition: 'opacity 0.15s',
          maxWidth: 300,
        }}
      />

      {/* SVG */}
      <svg ref={svgRef} className="w-full h-full touch-none" />
    </div>
  );
}

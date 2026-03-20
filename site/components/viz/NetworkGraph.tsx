'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { select } from 'd3-selection';
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
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

interface NetworkGraphProps {
  onNodeClick?: (node: SelectedNode) => void;
  wymanMode?: boolean;
}

/* ------------------------------------------------------------------ */
/*  Role colors                                                        */
/* ------------------------------------------------------------------ */

const roleColors: Record<string, string> = {
  pope: '#c9a959',
  bishop: '#5b8c5a',
  senator: '#8b5cf6',
  emperor: '#e74c3c',
  'priest/scholar': '#3b82f6',
  monk: '#a78bfa',
  default: '#6b7b8d',
};

function roleColor(role: string | null): string {
  if (!role) return roleColors.default;
  const r = role.toLowerCase();
  for (const [key, color] of Object.entries(roleColors)) {
    if (r.includes(key)) return color;
  }
  return roleColors.default;
}

function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function NetworkGraph({ onNodeClick, wymanMode = false }: NetworkGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const zoomRef = useRef<ZoomBehavior<SVGSVGElement, unknown> | null>(null);

  const [data, setData] = useState<NetworkData | null>(null);
  const [collection, setCollection] = useState('');
  const [loading, setLoading] = useState(true);

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

  // Reset zoom handler
  const handleResetZoom = useCallback(() => {
    if (!svgRef.current || !zoomRef.current) return;
    const svg = select(svgRef.current);
    svg
      .transition()
      .duration(500)
      .call(zoomRef.current.transform, zoomIdentity.translate(0, 0).scale(0.8));
  }, []);

  // Render graph
  const renderGraph = useCallback(() => {
    if (!data || !svgRef.current || !containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Filter edges by collection and/or Wyman Mode
    let edges = data.edges.map((e) => ({ ...e }));
    if (collection) {
      edges = edges.filter((e) => e.collection === collection);
    }
    if (wymanMode) {
      edges = edges.filter((e) => !WYMAN_EXCLUDED_COLLECTIONS.has(e.collection));
    }

    // Filter nodes by Wyman date range when wymanMode is on
    const wymanNodeIds: Set<number> | null = wymanMode
      ? (() => {
          const ids = new Set<number>();
          for (const n of data.nodes) {
            const active = (n.birth_year ?? 0) <= WYMAN_YEAR_MAX &&
              (n.death_year ?? WYMAN_YEAR_MAX) >= WYMAN_YEAR_MIN;
            if (active) ids.add(n.id);
          }
          return ids;
        })()
      : null;

    // Aggregate edges by source+target
    const edgeMap = new Map<string, NetworkEdge>();
    for (const e of edges) {
      const key = `${typeof e.source === 'object' ? (e.source as NetworkNode).id : e.source}-${typeof e.target === 'object' ? (e.target as NetworkNode).id : e.target}`;
      if (edgeMap.has(key)) {
        edgeMap.get(key)!.weight += e.weight;
      } else {
        edgeMap.set(key, { ...e });
      }
    }
    edges = Array.from(edgeMap.values());

    // Only include nodes that appear in the filtered edges (and optionally pass wyman date filter)
    const nodeIds = new Set<number>();
    for (const e of edges) {
      nodeIds.add(
        typeof e.source === 'object' ? (e.source as NetworkNode).id : (e.source as number),
      );
      nodeIds.add(
        typeof e.target === 'object' ? (e.target as NetworkNode).id : (e.target as number),
      );
    }

    const nodes: NetworkNode[] = data.nodes
      .filter((n) => nodeIds.has(n.id) && (!wymanNodeIds || wymanNodeIds.has(n.id)))
      .map((n) => ({ ...n }));

    // Clear
    const svg = select(svgRef.current);
    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', height);

    const g = svg.append('g');

    // Zoom - supports mouse wheel + touch pinch/pan
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
        .text('No network data for this collection.');
      return;
    }

    // Scales
    const maxWeight = Math.max(...edges.map((d) => d.weight), 1);
    const edgeScale = scaleLinear().domain([1, maxWeight]).range([0.5, 6]);
    const maxLetters = Math.max(
      ...nodes.map((d) => d.letters_sent + d.letters_received),
      1,
    );
    const nodeScale = scaleSqrt().domain([1, maxLetters]).range([4, 30]);

    // Links
    const link = g
      .append('g')
      .selectAll<SVGLineElement, NetworkEdge>('line')
      .data(edges)
      .join('line')
      .attr('stroke', '#4a5a7c')
      .attr('stroke-opacity', 0.4)
      .attr('stroke-width', (d) => edgeScale(d.weight));

    // Node groups
    const node = g
      .append('g')
      .selectAll<SVGGElement, NetworkNode>('g')
      .data(nodes, (d) => String(d.id))
      .join('g')
      .style('cursor', 'pointer');

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

    node
      .append('circle')
      .attr('r', (d) => nodeScale(d.letters_sent + d.letters_received))
      .attr('fill', (d) => roleColor(d.role))
      .attr('stroke', '#2a3a5c')
      .attr('stroke-width', 1.5);

    node
      .append('text')
      .attr('dx', (d) => nodeScale(d.letters_sent + d.letters_received) + 4)
      .attr('dy', 3)
      .attr('fill', '#b0a590')
      .attr('font-size', '10px')
      .attr('font-family', 'Inter, system-ui, sans-serif')
      .attr('pointer-events', 'none')
      .text((d) => (d.name.length > 25 ? d.name.slice(0, 22) + '...' : d.name));

    // Tooltip - styled with site typography
    const tooltip = tooltipRef.current;
    node
      .on('mouseover', (event, d) => {
        if (!tooltip) return;
        tooltip.innerHTML = `
          <div style="font-family:'Merriweather',Georgia,serif;font-size:14px;color:var(--color-text);font-weight:700;margin-bottom:4px">${d.name}</div>
          <div style="font-family:'Inter',system-ui,sans-serif;font-size:12px;color:var(--color-muted);line-height:1.6">
            ${d.role ? `<span style="text-transform:capitalize">${d.role}</span> &middot; ` : ''}${d.location || 'Unknown location'}<br/>
            ${d.birth_year ?? '?'}&ndash;${d.death_year ?? '?'} AD<br/>
            Sent: ${d.letters_sent} &middot; Received: ${d.letters_received}
          </div>
        `;
        tooltip.style.opacity = '1';
        tooltip.style.left = event.pageX + 12 + 'px';
        tooltip.style.top = event.pageY - 10 + 'px';
      })
      .on('mousemove', (event) => {
        if (!tooltip) return;
        tooltip.style.left = event.pageX + 12 + 'px';
        tooltip.style.top = event.pageY - 10 + 'px';
      })
      .on('mouseout', () => {
        if (!tooltip) return;
        tooltip.style.opacity = '0';
      })
      .on('click', (_event, d) => {
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

    // Hover highlight
    node.on('mouseenter', function () {
      select(this).select('circle').attr('stroke', '#c9a959').attr('stroke-width', 2);
    });
    node.on('mouseleave', function () {
      select(this).select('circle').attr('stroke', '#2a3a5c').attr('stroke-width', 1.5);
    });

    // Simulation
    const sim = forceSimulation<NetworkNode>(nodes)
      .force(
        'link',
        forceLink<NetworkNode, NetworkEdge>(edges)
          .id((d) => d.id)
          .distance((d) => 120 / Math.sqrt(d.weight))
          .strength((d) => Math.min(0.5, d.weight / maxWeight)),
      )
      .force(
        'charge',
        forceManyBody<NetworkNode>().strength(
          (d) => -80 - nodeScale(d.letters_sent + d.letters_received) * 5,
        ),
      )
      .force('center', forceCenter(width / 2, height / 2))
      .force(
        'collision',
        forceCollide<NetworkNode>().radius(
          (d) => nodeScale(d.letters_sent + d.letters_received) + 8,
        ),
      )
      .on('tick', () => {
        link
          .attr('x1', (d) => ((d.source as NetworkNode).x ?? 0))
          .attr('y1', (d) => ((d.source as NetworkNode).y ?? 0))
          .attr('x2', (d) => ((d.target as NetworkNode).x ?? 0))
          .attr('y2', (d) => ((d.target as NetworkNode).y ?? 0));
        node.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
      });

    // Initial zoom out a bit
    svg.call(zoomBehavior.transform, zoomIdentity.translate(0, 0).scale(0.8));

    // Cleanup
    return () => {
      sim.stop();
    };
  }, [data, collection, wymanMode, onNodeClick]);

  useEffect(() => {
    renderGraph();
  }, [renderGraph]);

  // Re-render on resize
  useEffect(() => {
    const handleResize = () => renderGraph();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [renderGraph]);

  return (
    <div ref={containerRef} className="relative w-full h-full" style={{ background: '#0f1520' }}>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center text-lg" style={{ color: 'var(--color-accent)' }}>
          Loading network data...
        </div>
      )}

      {/* Top controls bar */}
      {data && (
        <div className="absolute top-3 left-3 right-3 z-10 flex items-center gap-2 flex-wrap">
          {/* Collection filter */}
          <select
            value={collection}
            onChange={(e) => setCollection(e.target.value)}
            className="px-3 py-2 text-sm rounded-lg border transition-colors"
            style={{
              background: 'var(--color-surface)',
              borderColor: 'var(--color-border)',
              color: 'var(--color-text)',
              fontFamily: 'var(--font-sans)',
            }}
          >
            <option value="">All Collections</option>
            {data.collections.map((c) => (
              <option key={c.collection} value={c.collection}>
                {c.collection.replace(/_/g, ' ')} ({c.count})
              </option>
            ))}
          </select>

          {/* Reset zoom button */}
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

      {/* Tooltip - styled in site theme */}
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

      {/* SVG - touch-none prevents scroll-jacking on mobile */}
      <svg ref={svgRef} className="w-full h-full touch-none" />
    </div>
  );
}

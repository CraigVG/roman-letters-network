'use client';

import { useRef, useEffect, useCallback } from 'react';
import * as d3 from 'd3';

interface DecadeData {
  decade: number;
  count: number;
}

interface Props {
  decades: DecadeData[];
  from: number | null;
  to: number | null;
  onRangeChange: (from: number | null, to: number | null) => void;
}

const MARGIN = { top: 4, right: 16, bottom: 20, left: 16 };
const BAR_HEIGHT = 100;
const TOTAL_HEIGHT = BAR_HEIGHT + MARGIN.top + MARGIN.bottom + 6;

export default function TimelineHistogram({
  decades,
  from,
  to,
  onRangeChange,
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const brushRef = useRef<d3.BrushBehavior<unknown> | null>(null);
  const isBrushingRef = useRef(false);

  const getColors = useCallback(() => {
    const root = document.documentElement;
    const styles = window.getComputedStyle(root);
    return {
      accent: styles.getPropertyValue('--color-accent').trim() || '#b45a3c',
      surface: styles.getPropertyValue('--color-surface').trim() || '#faf8f5',
      border: styles.getPropertyValue('--color-border').trim() || '#d4c5b5',
      text: styles.getPropertyValue('--color-text').trim() || '#3d3329',
      fontSans: styles.getPropertyValue('--font-sans').trim() || 'system-ui, sans-serif',
    };
  }, []);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg || decades.length === 0) return;

    const colors = getColors();
    const containerWidth = svg.parentElement?.clientWidth ?? 600;
    const width = containerWidth;
    const innerWidth = width - MARGIN.left - MARGIN.right;
    const innerHeight = BAR_HEIGHT;

    // Clear previous content
    d3.select(svg).selectAll('*').remove();

    const root = d3
      .select(svg)
      .attr('width', width)
      .attr('height', TOTAL_HEIGHT)
      .attr('viewBox', `0 0 ${width} ${TOTAL_HEIGHT}`);

    const g = root
      .append('g')
      .attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    // Scales
    const sortedDecades = [...decades].sort((a, b) => a.decade - b.decade);
    const decadeExtent = d3.extent(sortedDecades, (d) => d.decade) as [number, number];
    const minDecade = decadeExtent[0];
    const maxDecade = decadeExtent[1] + 10; // include the last decade width

    const x = d3.scaleLinear().domain([minDecade, maxDecade]).range([0, innerWidth]);

    const maxCount = d3.max(sortedDecades, (d) => d.count) ?? 1;
    const y = d3.scaleLinear().domain([0, maxCount]).range([innerHeight, 0]);

    const barWidth = Math.max(1, (innerWidth / ((maxDecade - minDecade) / 10)) - 1);

    // Bars
    g.selectAll('.bar')
      .data(sortedDecades)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', (d) => x(d.decade))
      .attr('y', (d) => y(d.count))
      .attr('width', Math.max(1, barWidth - 1))
      .attr('height', (d) => innerHeight - y(d.count))
      .attr('fill', colors.accent)
      .attr('opacity', (d) => {
        if (from !== null && to !== null) {
          return d.decade >= from && d.decade <= to ? 1 : 0.25;
        }
        return 0.6;
      })
      .attr('rx', 1);

    // X-axis labels every 100 years
    const centuryTicks: number[] = [];
    for (let yr = Math.ceil(minDecade / 100) * 100; yr <= maxDecade; yr += 100) {
      centuryTicks.push(yr);
    }

    g.selectAll('.tick-label')
      .data(centuryTicks)
      .enter()
      .append('text')
      .attr('x', (d) => x(d))
      .attr('y', innerHeight + 14)
      .attr('text-anchor', 'middle')
      .attr('fill', colors.text)
      .attr('opacity', 0.6)
      .attr('font-size', '10px')
      .attr('font-family', colors.fontSans)
      .text((d) => d.toString());

    // Tooltip
    const tooltip = d3
      .select(svg.parentElement!)
      .selectAll<HTMLDivElement, unknown>('.timeline-tooltip')
      .data([null])
      .join('div')
      .attr('class', 'timeline-tooltip')
      .style('position', 'absolute')
      .style('pointer-events', 'none')
      .style('background', colors.surface)
      .style('border', `1px solid ${colors.border}`)
      .style('border-radius', '4px')
      .style('padding', '4px 8px')
      .style('font-size', '12px')
      .style('font-family', colors.fontSans)
      .style('color', colors.text)
      .style('white-space', 'nowrap')
      .style('opacity', 0)
      .style('z-index', '10')
      .style('box-shadow', '0 1px 3px rgba(0,0,0,0.12)');

    // Hover overlay rects (invisible, on top of bars)
    g.selectAll('.hover-rect')
      .data(sortedDecades)
      .enter()
      .append('rect')
      .attr('class', 'hover-rect')
      .attr('x', (d) => x(d.decade))
      .attr('y', 0)
      .attr('width', Math.max(1, barWidth - 1))
      .attr('height', innerHeight)
      .attr('fill', 'transparent')
      .style('cursor', 'pointer')
      .on('mouseenter', (event: MouseEvent, d: DecadeData) => {
        const parentRect = svg.parentElement!.getBoundingClientRect();
        const svgRect = svg.getBoundingClientRect();
        tooltip
          .html(`${d.decade}s: ${d.count.toLocaleString()} letter${d.count !== 1 ? 's' : ''}`)
          .style('opacity', 1)
          .style('left', `${event.clientX - parentRect.left + 10}px`)
          .style('top', `${svgRect.top - parentRect.top - 30}px`);
      })
      .on('mousemove', (event: MouseEvent, d: DecadeData) => {
        const parentRect = svg.parentElement!.getBoundingClientRect();
        const svgRect = svg.getBoundingClientRect();
        tooltip
          .html(`${d.decade}s: ${d.count.toLocaleString()} letter${d.count !== 1 ? 's' : ''}`)
          .style('left', `${event.clientX - parentRect.left + 10}px`)
          .style('top', `${svgRect.top - parentRect.top - 30}px`);
      })
      .on('mouseleave', () => {
        tooltip.style('opacity', 0);
      })
      .on('click', (_event: MouseEvent, d: DecadeData) => {
        if (from === d.decade && to === d.decade + 9) {
          onRangeChange(null, null);
        } else {
          onRangeChange(d.decade, d.decade + 9);
        }
      });

    // Brush
    const brush = d3
      .brushX()
      .extent([
        [0, 0],
        [innerWidth, innerHeight],
      ])
      .on('start', () => {
        isBrushingRef.current = true;
      })
      .on('end', (event: d3.D3BrushEvent<unknown>) => {
        isBrushingRef.current = false;
        if (!event.selection) {
          // Click on empty area clears selection
          if (!event.sourceEvent) return; // programmatic clear, ignore
          onRangeChange(null, null);
          return;
        }
        const [x0, x1] = event.selection as [number, number];
        const decadeFrom = Math.floor(x.invert(x0) / 10) * 10;
        const decadeTo = Math.floor(x.invert(x1) / 10) * 10 + 9;
        // Snap the brush to decade boundaries
        const snappedX0 = x(decadeFrom);
        const snappedX1 = x(decadeTo - 9 + 10);
        const brushGroup = g.select<SVGGElement>('.brush');
        brushGroup.call(brush.move as any, [snappedX0, snappedX1]);
        onRangeChange(
          Math.max(decadeFrom, minDecade),
          Math.min(decadeTo, maxDecade - 1),
        );
      });

    brushRef.current = brush;

    const brushGroup = g.append('g').attr('class', 'brush').call(brush);

    // Style the brush overlay
    brushGroup.select('.overlay').style('cursor', 'crosshair');
    brushGroup.select('.selection')
      .attr('fill', colors.accent)
      .attr('fill-opacity', 0.15)
      .attr('stroke', colors.accent)
      .attr('stroke-width', 1);

    // Set initial brush position from props
    if (from !== null && to !== null) {
      const x0 = x(from);
      const x1 = x(to + 1); // +1 so the brush covers through end of the decade
      brushGroup.call(brush.move as any, [x0, x1]);
    }

    // Cleanup
    return () => {
      tooltip.remove();
    };
  }, [decades, from, to, onRangeChange, getColors]);

  // Responsive resize
  useEffect(() => {
    const svg = svgRef.current;
    if (!svg || !svg.parentElement) return;

    const observer = new ResizeObserver(() => {
      // Force re-render by dispatching a state-independent effect
      // The main useEffect will re-run because we trigger a resize
      const event = new Event('resize');
      window.dispatchEvent(event);
    });

    observer.observe(svg.parentElement);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      className="relative w-full"
      style={{
        border: '1px solid var(--color-border)',
        borderRadius: '8px',
        background: 'var(--color-surface)',
        padding: '4px 0',
        minHeight: `${TOTAL_HEIGHT + 8}px`,
      }}
    >
      <svg
        ref={svgRef}
        style={{
          display: 'block',
          width: '100%',
          height: TOTAL_HEIGHT,
          overflow: 'visible',
        }}
      />
    </div>
  );
}

'use client';

import { useRef, useEffect, useState, useCallback } from 'react';
import { select } from 'd3-selection';
import { scaleLinear } from 'd3-scale';
import { line, curveMonotoneX, area } from 'd3-shape';
import { axisBottom, axisLeft } from 'd3-axis';
import { bisector } from 'd3-array';
import 'd3-transition';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface DecadeData {
  decade: number;
  avg_distance: number;
  max_distance: number;
  letter_count: number;
  unique_city_pairs: number;
  pct_long_distance: number;
}

interface RegionalizationData {
  summary: {
    total_letters_with_distance: number;
    peak_decade: number;
    peak_avg_distance: number;
    trough_decade: number;
    trough_avg_distance: number;
    pct_decline: number;
  };
  all_decades: DecadeData[];
  wyman_decades: DecadeData[];
}

interface RegionalizationChartProps {
  wymanMode: boolean;
}

/* ------------------------------------------------------------------ */
/*  Historical events for annotations                                  */
/* ------------------------------------------------------------------ */

const EVENTS = [
  { year: 378, short: 'Adrianople 378' },
  { year: 410, short: 'Rome sacked 410' },
  { year: 439, short: 'Carthage falls 439' },
  { year: 476, short: 'West falls 476' },
  { year: 535, short: 'Reconquest 535' },
];

/* ------------------------------------------------------------------ */
/*  Utility: weighted moving average                                   */
/* ------------------------------------------------------------------ */

interface SmoothedPoint {
  decade: number;
  value: number;
}

function weightedMovingAverage(
  data: DecadeData[],
  windowYears: number = 50
): SmoothedPoint[] {
  const halfWindow = windowYears / 2;
  const result: SmoothedPoint[] = [];

  for (const point of data) {
    const center = point.decade + 5;
    let weightedSum = 0;
    let totalWeight = 0;

    for (const other of data) {
      const otherCenter = other.decade + 5;
      const dist = Math.abs(center - otherCenter);
      if (dist <= halfWindow) {
        const proximityWeight = 1 - dist / halfWindow;
        const sampleWeight = Math.sqrt(other.letter_count);
        const w = proximityWeight * sampleWeight;
        weightedSum += other.avg_distance * w;
        totalWeight += w;
      }
    }

    if (totalWeight > 0) {
      result.push({ decade: point.decade, value: weightedSum / totalWeight });
    }
  }

  return result;
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function RegionalizationChart({ wymanMode }: RegionalizationChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<RegionalizationData | null>(null);
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    d: DecadeData;
    smoothed: number;
  } | null>(null);

  const MIN_LETTERS = 10;

  useEffect(() => {
    fetch('/data/regionalization.json')
      .then((r) => r.json())
      .then((d) => setData(d))
      .catch(console.error);
  }, []);

  const drawChart = useCallback(() => {
    if (!data || !svgRef.current || !containerRef.current) return;

    const svg = select(svgRef.current);
    svg.selectAll('*').remove();

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = Math.min(400, Math.max(280, width * 0.5));

    svg.attr('width', width).attr('height', height);

    const margin = { top: 32, right: 24, bottom: 48, left: 64 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const decades = wymanMode ? data.wyman_decades : data.all_decades;
    const reliable = decades.filter(
      (d) => d.decade >= 240 && d.decade <= 760 && d.letter_count >= MIN_LETTERS
    );

    if (reliable.length < 2) {
      g.append('text')
        .attr('x', w / 2)
        .attr('y', h / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', 'var(--color-muted)')
        .style('font-family', 'var(--font-sans)')
        .style('font-size', '14px')
        .text('Not enough data for this filter range.');
      return;
    }

    const smoothed = weightedMovingAverage(reliable, 50);

    // Scales
    const xExtent = [
      Math.min(...reliable.map((d) => d.decade)),
      Math.max(...reliable.map((d) => d.decade)) + 10,
    ];
    const allVals = [
      ...reliable.map((d) => d.avg_distance),
      ...smoothed.map((d) => d.value),
    ];
    const yMax = Math.max(...allVals) * 1.15;

    const x = scaleLinear().domain(xExtent).range([0, w]);
    const y = scaleLinear().domain([0, yMax]).range([h, 0]).nice();

    const accentColor = wymanMode
      ? 'var(--color-secondary)'
      : 'var(--color-accent)';

    // Grid lines
    g.selectAll('.grid-line')
      .data(y.ticks(5))
      .enter()
      .append('line')
      .attr('x1', 0)
      .attr('x2', w)
      .attr('y1', (d) => y(d))
      .attr('y2', (d) => y(d))
      .attr('stroke', 'var(--color-border)')
      .attr('stroke-dasharray', '2,4')
      .attr('opacity', 0.5);

    // Historical event annotations
    EVENTS.filter((e) => e.year >= xExtent[0] && e.year <= xExtent[1]).forEach(
      (evt, i) => {
        const ex = x(evt.year);
        g.append('line')
          .attr('x1', ex)
          .attr('x2', ex)
          .attr('y1', 0)
          .attr('y2', h)
          .attr('stroke', 'var(--color-muted)')
          .attr('stroke-dasharray', '4,4')
          .attr('opacity', 0.25);

        g.append('text')
          .attr('x', ex)
          .attr('y', 4 + (i % 2) * 14)
          .attr('text-anchor', 'middle')
          .attr('fill', 'var(--color-muted)')
          .style('font-family', 'var(--font-sans)')
          .style('font-size', '9px')
          .style('font-weight', '500')
          .attr('opacity', 0.65)
          .text(width < 500 ? `${evt.year}` : evt.short);
      }
    );

    // Area fill under trend
    const areaGen = area<SmoothedPoint>()
      .x((d) => x(d.decade + 5))
      .y0(h)
      .y1((d) => y(d.value))
      .curve(curveMonotoneX);

    g.append('path')
      .datum(smoothed)
      .attr('d', areaGen)
      .attr('fill', accentColor)
      .attr('opacity', 0.08);

    // Smoothed trend line
    const trendLine = line<SmoothedPoint>()
      .x((d) => x(d.decade + 5))
      .y((d) => y(d.value))
      .curve(curveMonotoneX);

    const trendPath = g
      .append('path')
      .datum(smoothed)
      .attr('d', trendLine)
      .attr('fill', 'none')
      .attr('stroke', accentColor)
      .attr('stroke-width', 3)
      .attr('stroke-linecap', 'round');

    // Animate
    const totalLength =
      (trendPath.node() as SVGPathElement)?.getTotalLength?.() || 0;
    if (totalLength) {
      trendPath
        .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
        .attr('stroke-dashoffset', totalLength)
        .transition()
        .duration(1500)
        .attr('stroke-dashoffset', 0);
    }

    // Raw data dots (sized by letter count)
    g.selectAll('.dot')
      .data(reliable)
      .enter()
      .append('circle')
      .attr('cx', (d) => x(d.decade + 5))
      .attr('cy', (d) => y(d.avg_distance))
      .attr('r', (d) =>
        Math.max(3, Math.min(8, Math.sqrt(d.letter_count) * 0.5))
      )
      .attr('fill', accentColor)
      .attr('stroke', 'var(--color-bg)')
      .attr('stroke-width', 1.5)
      .attr('opacity', 0)
      .transition()
      .delay(1500)
      .duration(400)
      .attr('opacity', 0.6);

    // Sample-size labels
    g.selectAll('.count-label')
      .data(reliable)
      .enter()
      .append('text')
      .attr('x', (d) => x(d.decade + 5))
      .attr('y', (d) => y(d.avg_distance) + 16)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--color-muted)')
      .style('font-family', 'var(--font-sans)')
      .style('font-size', '8px')
      .attr('opacity', 0.5)
      .text((d) => `n=${d.letter_count}`);

    // Axes
    const xTickValues = reliable
      .filter((_, i, arr) =>
        arr.length <= 12 ? true : i % 2 === 0 || i === arr.length - 1
      )
      .map((d) => d.decade);

    g.append('g')
      .attr('transform', `translate(0,${h})`)
      .call(
        axisBottom(x)
          .tickValues(xTickValues)
          .tickFormat((d) => `${d}s`)
      )
      .call((s) => s.select('.domain').attr('stroke', 'var(--color-border)'))
      .call((s) =>
        s.selectAll('.tick line').attr('stroke', 'var(--color-border)')
      )
      .call((s) =>
        s
          .selectAll('.tick text')
          .attr('fill', 'var(--color-muted)')
          .style('font-family', 'var(--font-sans)')
          .style('font-size', '10px')
      );

    g.append('g')
      .call(
        axisLeft(y)
          .ticks(5)
          .tickFormat((d) => `${d} km`)
      )
      .call((s) => s.select('.domain').remove())
      .call((s) =>
        s.selectAll('.tick line').attr('stroke', 'var(--color-border)')
      )
      .call((s) =>
        s
          .selectAll('.tick text')
          .attr('fill', 'var(--color-muted)')
          .style('font-family', 'var(--font-sans)')
          .style('font-size', '10px')
      );

    // Axis labels
    g.append('text')
      .attr('x', w / 2)
      .attr('y', h + 42)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--color-muted)')
      .style('font-family', 'var(--font-sans)')
      .style('font-size', '11px')
      .text('Decade');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -h / 2)
      .attr('y', -50)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--color-muted)')
      .style('font-family', 'var(--font-sans)')
      .style('font-size', '11px')
      .text('Average letter distance (km)');

    // Legend
    const legendY = -20;
    g.append('line')
      .attr('x1', w - 180)
      .attr('x2', w - 160)
      .attr('y1', legendY)
      .attr('y2', legendY)
      .attr('stroke', accentColor)
      .attr('stroke-width', 3)
      .attr('stroke-linecap', 'round');
    g.append('text')
      .attr('x', w - 155)
      .attr('y', legendY + 3.5)
      .attr('fill', 'var(--color-muted)')
      .style('font-family', 'var(--font-sans)')
      .style('font-size', '9px')
      .text('50-yr weighted trend');
    g.append('circle')
      .attr('cx', w - 70)
      .attr('cy', legendY)
      .attr('r', 3)
      .attr('fill', accentColor)
      .attr('opacity', 0.6);
    g.append('text')
      .attr('x', w - 63)
      .attr('y', legendY + 3.5)
      .attr('fill', 'var(--color-muted)')
      .style('font-family', 'var(--font-sans)')
      .style('font-size', '9px')
      .text('raw decade avg');

    // Tooltip hover
    const tooltipLine = g
      .append('line')
      .attr('stroke', 'var(--color-muted)')
      .attr('stroke-dasharray', '3,3')
      .attr('opacity', 0);

    g.append('rect')
      .attr('width', w)
      .attr('height', h)
      .attr('fill', 'none')
      .attr('pointer-events', 'all')
      .on('mousemove', (event: MouseEvent) => {
        const mx = event.offsetX - margin.left;
        const xVal = x.invert(mx);
        const bis = bisector<DecadeData, number>((d) => d.decade + 5).left;
        const idx = Math.max(
          0,
          Math.min(reliable.length - 1, bis(reliable, xVal) - 1)
        );
        let closest = reliable[idx];
        if (idx + 1 < reliable.length) {
          const next = reliable[idx + 1];
          if (
            Math.abs(xVal - (closest.decade + 5)) >
            Math.abs(xVal - (next.decade + 5))
          )
            closest = next;
        }
        const cx = x(closest.decade + 5);
        const cy = y(closest.avg_distance);
        tooltipLine
          .attr('x1', cx)
          .attr('x2', cx)
          .attr('y1', 0)
          .attr('y2', h)
          .attr('opacity', 0.4);

        const sp = smoothed.find((s) => s.decade === closest.decade);
        setTooltip({
          x: cx + margin.left,
          y: cy + margin.top,
          d: closest,
          smoothed: sp?.value ?? closest.avg_distance,
        });
      })
      .on('mouseleave', () => {
        tooltipLine.attr('opacity', 0);
        setTooltip(null);
      });
  }, [data, wymanMode]);

  useEffect(() => {
    drawChart();
    const handleResize = () => drawChart();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [drawChart]);

  if (!data) {
    return (
      <div className="h-64 flex items-center justify-center text-theme-muted text-sm">
        Loading chart data...
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative w-full">
      <svg ref={svgRef} className="w-full" />
      {tooltip && (
        <div
          className="absolute pointer-events-none z-10 bg-theme-surface border border-theme rounded-lg px-3 py-2 shadow-lg text-xs"
          style={{
            left: `${tooltip.x}px`,
            top: `${tooltip.y - 80}px`,
            transform: 'translateX(-50%)',
          }}
        >
          <div className="font-medium text-theme-text">
            {tooltip.d.decade}s AD
          </div>
          <div className="text-theme-muted mt-1">
            Avg distance:{' '}
            <span className="text-theme-accent font-medium">
              {tooltip.d.avg_distance.toLocaleString()} km
            </span>
          </div>
          <div className="text-theme-muted">
            Trend:{' '}
            <span className="text-theme-text font-medium">
              {Math.round(tooltip.smoothed).toLocaleString()} km
            </span>
          </div>
          <div className="text-theme-muted mt-0.5">
            {tooltip.d.letter_count} letters | {tooltip.d.unique_city_pairs}{' '}
            city pairs | {tooltip.d.pct_long_distance}% &gt;500 km
          </div>
        </div>
      )}
    </div>
  );
}

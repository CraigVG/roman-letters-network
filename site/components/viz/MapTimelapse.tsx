'use client';

import { useRef, useEffect, useState, useCallback } from 'react';
import { select } from 'd3-selection';
import { geoMercator, geoPath, geoGraticule } from 'd3-geo';
import { zoom as d3Zoom, zoomIdentity } from 'd3-zoom';
import * as topojson from 'topojson-client';
import {
  YEAR_MIN,
  YEAR_MAX,
  WYMAN_EXCLUDED_COLLECTIONS,
  WYMAN_YEAR_MIN,
  WYMAN_YEAR_MAX,
  type HistoricalEvent,
  type HubCity,
  type MapTimelapseProps,
  type MapStats,
} from './map-types';

// Re-export for convenience
export { YEAR_MIN, YEAR_MAX };
export type { HistoricalEvent, MapStats, MapTimelapseProps };

// ── Internal types ───────────────────────────────────────────────────────

interface MapLetter {
  id: number;
  collection: string;
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
const MAX_VISIBLE_ARCS = 500;
const MED_BOUNDS = [-10, 25, 45, 55] as const; // [lon_min, lat_min, lon_max, lat_max]

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

// ── Component ────────────────────────────────────────────────────────────

export default function MapTimelapse({
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
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const bannerRef = useRef<HTMLDivElement>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Refs for data that doesn't trigger re-render
  const dataRef = useRef<{
    letters: MapLetter[];
    people: MapPerson[];
    events: HistoricalEvent[];
    timeline: TimelineRow[];
    hubCities: HubCity[];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    projection: any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    path: any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    arcG: any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    dotG: any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    eventG: any;
    lastBannerYear: number | null;
    bannerTimer: ReturnType<typeof setTimeout> | null;
  }>({
    letters: [],
    people: [],
    events: [],
    timeline: [],
    hubCities: [],
    projection: null,
    path: null,
    arcG: null,
    dotG: null,
    eventG: null,
    lastBannerYear: null,
    bannerTimer: null,
  });

  const playRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const currentYearRef = useRef(YEAR_MIN);

  // Keep ref in sync with prop
  useEffect(() => {
    currentYearRef.current = currentYear;
  }, [currentYear]);

  // ── Arc path helper ──────────────────────────────────────────────────
  const arcPathD = useCallback(
    (sLon: number, sLat: number, rLon: number, rLat: number): string | null => {
      const proj = dataRef.current.projection;
      if (!proj) return null;
      const s = proj([sLon, sLat]);
      const r = proj([rLon, rLat]);
      if (!s || !r) return null;
      const [sx, sy] = s;
      const [rx, ry] = r;
      const mx = (sx + rx) / 2;
      const my = (sy + ry) / 2;
      const dx = rx - sx;
      const dy = ry - sy;
      const len = Math.sqrt(dx * dx + dy * dy);
      if (len === 0) return null;
      const curve = Math.min(len * 0.25, 80);
      const px = (-dy / len) * curve;
      const py = (dx / len) * curve;
      return `M ${sx},${sy} Q ${mx + px},${my + py} ${rx},${ry}`;
    },
    [],
  );

  // ── Render arcs ──────────────────────────────────────────────────────
  const renderArcs = useCallback(
    (year: number, collection: string, opacity: number, trail: boolean, win: number, wyman: boolean) => {
      const { letters, arcG } = dataRef.current;
      if (!arcG) return;

      const effectiveYearMin = wyman ? WYMAN_YEAR_MIN : null;
      const effectiveYearMax = wyman ? WYMAN_YEAR_MAX : null;

      const yearLetters = letters.filter((l) => {
        if (collection && l.collection !== collection) return false;
        if (!l.year_approx) return false;
        if (wyman) {
          if (WYMAN_EXCLUDED_COLLECTIONS.has(l.collection)) return false;
          if (l.year_approx < WYMAN_YEAR_MIN || l.year_approx > WYMAN_YEAR_MAX) return false;
        }
        if (effectiveYearMin !== null && year < effectiveYearMin) return false;
        if (effectiveYearMax !== null && year > effectiveYearMax) return false;
        if (trail) {
          return l.year_approx <= year + win;
        }
        return Math.abs(l.year_approx - year) <= win;
      });

      arcG.selectAll('.arc-path').remove();

      let renderLetters = yearLetters;
      if (yearLetters.length > MAX_VISIBLE_ARCS) {
        renderLetters = yearLetters
          .slice()
          .sort(
            (a: MapLetter, b: MapLetter) =>
              Math.abs(a.year_approx - year) - Math.abs(b.year_approx - year),
          )
          .slice(0, MAX_VISIBLE_ARCS);
      }

      const tooltip = tooltipRef.current;

      renderLetters.forEach((l: MapLetter) => {
        const d = arcPathD(l.s_lon, l.s_lat, l.r_lon, l.r_lat);
        if (!d) return;

        const age = year - l.year_approx;
        let ageOpacity = opacity;
        if (trail && age > 0) {
          ageOpacity = opacity * Math.max(0.15, 1 - age / 200);
        }
        const isNew = Math.abs(l.year_approx - year) <= win;

        arcG
          .append('path')
          .attr('class', isNew ? 'arc-path arc-active' : 'arc-path')
          .attr('d', d)
          .attr('stroke', centuryColor(l.year_approx))
          .attr('stroke-width', isNew ? 1.5 : 0.6)
          .attr('stroke-opacity', ageOpacity)
          .attr('fill', 'none')
          .attr('filter', isNew ? 'url(#glow)' : null)
          .style('pointer-events', 'stroke')
          .style('cursor', 'pointer')
          .on('mouseover', (event: MouseEvent) => {
            select(event.currentTarget as Element).attr('stroke-width', 2.5).attr('stroke-opacity', 1);
            if (tooltip) {
              const nameEl = tooltip.querySelector('.tt-name') as HTMLElement;
              const infoEl = tooltip.querySelector('.tt-info') as HTMLElement;
              if (nameEl) nameEl.textContent = `${l.sender_name} \u2192 ${l.recipient_name}`;
              if (infoEl) {
                infoEl.innerHTML =
                  `${l.collection.replace(/_/g, ' ')} \u00b7 ~${l.year_approx} AD` +
                  (l.quick_summary
                    ? `<br><em>${l.quick_summary.slice(0, 150)}...</em>`
                    : '') +
                  (l.interesting_note
                    ? `<br><span style="color:#c9a959">${l.interesting_note}</span>`
                    : '');
              }
              tooltip.style.opacity = '1';
              tooltip.style.left = event.pageX + 14 + 'px';
              tooltip.style.top = event.pageY - 10 + 'px';
            }
          })
          .on('mousemove', (event: MouseEvent) => {
            if (tooltip) {
              tooltip.style.left = event.pageX + 14 + 'px';
              tooltip.style.top = event.pageY - 10 + 'px';
            }
          })
          .on('mouseout', (event: MouseEvent) => {
            select(event.currentTarget as Element)
              .attr('stroke-width', isNew ? 1.5 : 0.6)
              .attr('stroke-opacity', ageOpacity);
            if (tooltip) tooltip.style.opacity = '0';
          })
          .on('click', () => {
            window.location.href = `/letters/${l.id}`;
          });
      });

      onStatsChange?.({ visible: yearLetters.length, total: dataRef.current.letters.length, people: dataRef.current.people.length });
    },
    [arcPathD, onStatsChange],
  );

  // ── Render historical events ─────────────────────────────────────────
  const renderHistoricalEvents = useCallback(
    (year: number, visible: boolean) => {
      const { events, eventG, projection } = dataRef.current;
      if (!eventG) return;

      eventG.selectAll('.event-group').remove();
      if (!visible) return;

      const tooltip = tooltipRef.current;
      const banner = bannerRef.current;

      const visibleEvents = events.filter(
        (ev) => ev.year <= year && ev.lon != null && ev.lat != null,
      );

      visibleEvents.forEach((ev) => {
        const projected = projection([ev.lon, ev.lat]);
        if (!projected) return;
        const [px, py] = projected;
        const age = year - ev.year;
        const baseOpacity = age <= 15 ? 1 : Math.max(0.28, 1 - (age - 15) / 55);

        const g = eventG.append('g').attr('class', 'event-group').attr('data-year', ev.year);

        if (age <= 20) {
          g.append('circle')
            .attr('class', 'event-pulse-ring')
            .attr('cx', px)
            .attr('cy', py)
            .attr('r', 4)
            .attr('opacity', baseOpacity * 0.5);
        }

        g.append('circle')
          .attr('class', 'event-dot')
          .attr('cx', px)
          .attr('cy', py)
          .attr('r', 3)
          .attr('fill', '#e74c3c')
          .attr('stroke', '#ff8080')
          .attr('stroke-width', 1)
          .attr('fill-opacity', baseOpacity)
          .attr('stroke-opacity', baseOpacity)
          .style('cursor', 'pointer')
          .on('mouseover', (event: MouseEvent) => {
            select(event.currentTarget as Element).attr('r', 5);
            if (tooltip) {
              const nameEl = tooltip.querySelector('.tt-name') as HTMLElement;
              const infoEl = tooltip.querySelector('.tt-info') as HTMLElement;
              if (nameEl) nameEl.textContent = `${ev.year} AD`;
              if (infoEl) infoEl.innerHTML = ev.label;
              tooltip.style.opacity = '1';
              tooltip.style.left = event.pageX + 14 + 'px';
              tooltip.style.top = event.pageY - 10 + 'px';
            }
          })
          .on('mousemove', (event: MouseEvent) => {
            if (tooltip) {
              tooltip.style.left = event.pageX + 14 + 'px';
              tooltip.style.top = event.pageY - 10 + 'px';
            }
          })
          .on('mouseout', (event: MouseEvent) => {
            select(event.currentTarget as Element).attr('r', 3);
            if (tooltip) tooltip.style.opacity = '0';
          });

        g.append('text')
          .attr('class', 'event-label')
          .attr('x', px + 7)
          .attr('y', py + 3)
          .attr('fill', '#ff9f9f')
          .attr('font-size', '8px')
          .attr('font-family', 'Georgia, serif')
          .attr('font-style', 'italic')
          .attr('pointer-events', 'none')
          .attr('opacity', Math.min(baseOpacity, 0.85))
          .text(ev.short);

        g.append('text')
          .attr('class', 'event-year-tag')
          .attr('x', px + 7)
          .attr('y', py + 11)
          .attr('fill', '#c0392b')
          .attr('font-size', '7.5px')
          .attr('font-family', 'Georgia, serif')
          .attr('font-weight', 'bold')
          .attr('pointer-events', 'none')
          .attr('opacity', Math.min(baseOpacity * 0.75, 0.7))
          .text(`${ev.year} AD`);
      });

      // Banner for newly arrived events
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
    },
    [],
  );

  // ── Set year (main update) ───────────────────────────────────────────
  const setYearAndRender = useCallback(
    (
      year: number,
      collection: string,
      opacity: number,
      trail: boolean,
      win: number,
      eventsVisible: boolean,
      wyman: boolean,
    ) => {
      const clamped = Math.min(YEAR_MAX, Math.max(YEAR_MIN, year));
      onYearChange(clamped);
      renderArcs(clamped, collection, opacity, trail, win, wyman);
      renderHistoricalEvents(clamped, eventsVisible);
    },
    [onYearChange, renderArcs, renderHistoricalEvents],
  );

  // ── Play/pause logic ─────────────────────────────────────────────────
  useEffect(() => {
    if (isPlaying) {
      const tickMs = Math.max(40, 1000 / (speed * 5));
      playRef.current = setInterval(() => {
        const yr = currentYearRef.current;
        if (yr >= YEAR_MAX) {
          onPlayingChange(false);
          return;
        }
        setYearAndRender(
          yr + 1,
          filterCollection,
          arcOpacity,
          showTrail,
          windowSize,
          showEvents,
          wymanMode,
        );
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
  }, [isPlaying, speed, filterCollection, arcOpacity, showTrail, windowSize, showEvents, wymanMode, setYearAndRender, onPlayingChange]);

  // ── Draw people dots ─────────────────────────────────────────────────
  const drawPeople = useCallback((people: MapPerson[], visible: boolean) => {
    const { dotG, projection } = dataRef.current;
    if (!dotG) return;
    dotG.selectAll('.person-dot').remove();
    if (!visible) return;

    const tooltip = tooltipRef.current;

    dotG
      .selectAll('.person-dot')
      .data(people)
      .join('circle')
      .attr('class', 'person-dot')
      .attr('cx', (d: MapPerson) => projection([d.lon, d.lat])?.[0] ?? 0)
      .attr('cy', (d: MapPerson) => projection([d.lon, d.lat])?.[1] ?? 0)
      .attr('r', (d: MapPerson) => {
        const total = (d.sent || 0) + (d.received || 0);
        return Math.max(1.5, Math.min(5, 1.5 + Math.sqrt(total) * 0.2));
      })
      .attr('fill', (d: MapPerson) => roleColor(d.role))
      .attr('fill-opacity', 0.85)
      .attr('stroke', '#1a1a2e')
      .attr('stroke-width', 0.8)
      .style('cursor', 'pointer')
      .on('mouseover', (event: MouseEvent, d: MapPerson) => {
        select(event.currentTarget as Element).attr('stroke', '#fff').attr('stroke-width', 2);
        if (tooltip) {
          const nameEl = tooltip.querySelector('.tt-name') as HTMLElement;
          const infoEl = tooltip.querySelector('.tt-info') as HTMLElement;
          if (nameEl) nameEl.textContent = d.name;
          if (infoEl) {
            infoEl.innerHTML =
              `${d.role || 'Unknown role'} \u00b7 ${d.location || 'Unknown location'}<br>` +
              `${d.birth_year || '?'}\u2013${d.death_year || '?'} AD<br>` +
              `${d.sent || 0} sent \u00b7 ${d.received || 0} received`;
          }
          tooltip.style.opacity = '1';
          tooltip.style.left = event.pageX + 14 + 'px';
          tooltip.style.top = event.pageY - 10 + 'px';
        }
      })
      .on('mousemove', (event: MouseEvent) => {
        if (tooltip) {
          tooltip.style.left = event.pageX + 14 + 'px';
          tooltip.style.top = event.pageY - 10 + 'px';
        }
      })
      .on('mouseout', (event: MouseEvent) => {
        select(event.currentTarget as Element).attr('stroke', '#1a1a2e').attr('stroke-width', 0.8);
        if (tooltip) tooltip.style.opacity = '0';
      });
  }, []);

  // ── Initialize map + load data ───────────────────────────────────────
  useEffect(() => {
    if (!svgRef.current) return;

    const container = svgRef.current.parentElement;
    if (!container) return;
    const W = container.clientWidth;
    const H = container.clientHeight;

    const svgSel = select(svgRef.current)
      .attr('viewBox', `0 0 ${W} ${H}`)
      .attr('preserveAspectRatio', 'xMidYMid meet');

    // Clear any previous content
    svgSel.selectAll('*').remove();

    // Sea background
    svgSel.append('rect').attr('class', 'sea').attr('width', W).attr('height', H).attr('fill', '#0d1829');

    // Mercator projection fitted to Mediterranean
    const medFeature = {
      type: 'Feature' as const,
      geometry: {
        type: 'Polygon' as const,
        coordinates: [
          [
            [MED_BOUNDS[0], MED_BOUNDS[1]],
            [MED_BOUNDS[2], MED_BOUNDS[1]],
            [MED_BOUNDS[2], MED_BOUNDS[3]],
            [MED_BOUNDS[0], MED_BOUNDS[3]],
            [MED_BOUNDS[0], MED_BOUNDS[1]],
          ],
        ],
      },
      properties: {},
    };

    const projection = geoMercator().fitSize([W, H], medFeature);
    const pathGen = geoPath(projection);

    dataRef.current.projection = projection;
    dataRef.current.path = pathGen;

    // Layers
    const mapG = svgSel.append('g').attr('class', 'map-layer');
    const arcG = svgSel.append('g').attr('class', 'arc-layer');
    const dotG = svgSel.append('g').attr('class', 'dot-layer');
    const eventG = svgSel.append('g').attr('class', 'event-layer');

    dataRef.current.arcG = arcG;
    dataRef.current.dotG = dotG;
    dataRef.current.eventG = eventG;

    // Glow filter
    const defs = svgSel.append('defs');
    const filter = defs
      .append('filter')
      .attr('id', 'glow')
      .attr('x', '-50%')
      .attr('y', '-50%')
      .attr('width', '200%')
      .attr('height', '200%');
    filter.append('feGaussianBlur').attr('stdDeviation', '2').attr('result', 'coloredBlur');
    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    // Zoom + pan (touch-friendly)
    const zoomBehavior = d3Zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 20])
      .on('zoom', (event) => {
        mapG.attr('transform', event.transform);
        arcG.attr('transform', event.transform);
        dotG.attr('transform', event.transform);
        eventG.attr('transform', event.transform);
      });

    svgSel.call(zoomBehavior);

    // Initial zoom to Mediterranean
    const [pxW, pxN] = projection([MED_BOUNDS[0], MED_BOUNDS[3]]) || [0, 0];
    const [pxE, pxS] = projection([MED_BOUNDS[2], MED_BOUNDS[1]]) || [W, H];
    const regionW = pxE - pxW;
    const regionH = pxS - pxN;
    const zoomScale = Math.min(W / regionW, H / regionH) * 0.95;
    const regionCenterX = (pxW + pxE) / 2;
    const regionCenterY = (pxN + pxS) / 2;
    const translateX = W / 2 - zoomScale * regionCenterX;
    const translateY = H / 2 - zoomScale * regionCenterY;
    svgSel.call(
      zoomBehavior.transform,
      zoomIdentity.translate(translateX, translateY).scale(zoomScale),
    );

    // ── Load data ────────────────────────────────────────────────────
    Promise.all([
      fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/land-110m.json').then((r) => r.json()),
      fetch('/data/map-letters.json').then((r) => r.json()),
      fetch('/data/historical-events.json').then((r) => r.json()),
      fetch('/data/timeline.json').then((r) => r.json()),
      fetch('/data/hub-cities.json').then((r) => r.json()).catch(() => [] as HubCity[]),
    ])
      .then(([world, mapData, events, timeline, hubCities]: [
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        any,
        { letters: MapLetter[]; people: MapPerson[] },
        HistoricalEvent[],
        TimelineRow[],
        HubCity[],
      ]) => {
        // Draw base map
        const land = topojson.feature(world, world.objects.land);
        const graticule = geoGraticule().step([10, 10])();

        mapG
          .append('path')
          .datum(graticule)
          .attr('d', pathGen)
          .attr('fill', 'none')
          .attr('stroke', '#1e2a3e')
          .attr('stroke-width', 0.3);

        mapG
          .append('path')
          .datum(land)
          .attr('d', pathGen)
          .attr('fill', '#1e2d45')
          .attr('stroke', '#2e4060')
          .attr('stroke-width', 0.5);

        // Region labels
        const labels = [
          { name: 'BRITANNIA', lon: -2, lat: 52.5 },
          { name: 'GALLIA', lon: 2, lat: 47 },
          { name: 'HISPANIA', lon: -4, lat: 40 },
          { name: 'AFRICA', lon: 10, lat: 32.5 },
          { name: 'AEGYPTUS', lon: 30, lat: 27.5 },
          { name: 'SYRIA', lon: 37, lat: 35 },
          { name: 'ASIA MINOR', lon: 32, lat: 39.5 },
          { name: 'ITALIA', lon: 12, lat: 42 },
          { name: 'GRAECIA', lon: 22, lat: 39 },
          { name: 'PANNONIA', lon: 18, lat: 47 },
          { name: 'THRACIA', lon: 26, lat: 42 },
          { name: 'CARTHAGO', lon: 10, lat: 37 },
        ];

        labels.forEach((l) => {
          const pt = projection([l.lon, l.lat]);
          if (!pt) return;
          mapG
            .append('text')
            .attr('x', pt[0])
            .attr('y', pt[1])
            .attr('text-anchor', 'middle')
            .attr('fill', '#2e4a6e')
            .attr('font-size', '7.5px')
            .attr('font-family', 'Georgia, serif')
            .attr('letter-spacing', '1.5px')
            .attr('pointer-events', 'none')
            .attr('opacity', 0.5)
            .text(l.name);
        });

        // Key cities - hub cities are clickable to show profile
        const citiesBase = [
          { name: 'Roma',          hubName: 'Rome',           lon: 12.5,  lat: 41.9   },
          { name: 'Constantinople',hubName: 'Constantinople', lon: 28.97, lat: 41.01  },
          { name: 'Carthago',      hubName: 'Carthage',       lon: 10.2,  lat: 36.85  },
          { name: 'Alexandria',    hubName: 'Alexandria',     lon: 29.9,  lat: 31.2   },
          { name: 'Antioch',       hubName: 'Antioch',        lon: 36.2,  lat: 36.2   },
          { name: 'Mediolanum',    hubName: 'Milan',          lon: 9.19,  lat: 45.46  },
          { name: 'Thessalonica',  hubName: null,             lon: 22.94, lat: 40.64  },
          { name: 'Ravenna',       hubName: 'Ravenna',        lon: 12.2,  lat: 44.42  },
          { name: 'Arelate',       hubName: 'Arles',          lon: 4.628, lat: 43.677 },
          { name: 'Massilia',      hubName: 'Marseille',      lon: 5.381, lat: 43.297 },
          { name: 'Lugdunum',      hubName: 'Lyon',           lon: 4.847, lat: 45.748 },
          { name: 'Hippo',         hubName: 'Hippo Regius',   lon: 7.75,  lat: 36.883 },
          { name: 'Caesarea',      hubName: 'Caesarea',       lon: 35.478,lat: 38.731 },
          { name: 'Hierosolyma',   hubName: 'Jerusalem',      lon: 35.2,  lat: 31.705 },
        ];

        const tooltip = tooltipRef.current;

        citiesBase.forEach((c) => {
          const pt = projection([c.lon, c.lat]);
          if (!pt) return;
          const hubData = c.hubName ? hubCities.find((h) => h.name === c.hubName) : null;
          const isHub = !!hubData;

          mapG
            .append('circle')
            .attr('cx', pt[0])
            .attr('cy', pt[1])
            .attr('r', isHub ? 4 : 3)
            .attr('fill', isHub ? '#c9a959' : '#3a4a6a')
            .attr('stroke', isHub ? '#e8c878' : '#5a7aaa')
            .attr('stroke-width', isHub ? 1 : 0.5)
            .attr('pointer-events', isHub ? 'all' : 'none')
            .style('cursor', isHub ? 'pointer' : 'default')
            .on('mouseover', isHub ? ((event: MouseEvent) => {
              select(event.currentTarget as Element).attr('r', 6).attr('stroke-width', 2);
              if (tooltip) {
                const nameEl = tooltip.querySelector('.tt-name') as HTMLElement;
                const infoEl = tooltip.querySelector('.tt-info') as HTMLElement;
                if (nameEl) nameEl.textContent = c.name;
                if (infoEl) infoEl.innerHTML = `Hub city \u00b7 ${hubData!.total_sent + hubData!.total_received} letters<br><em>Click for full profile</em>`;
                tooltip.style.opacity = '1';
                tooltip.style.left = event.pageX + 14 + 'px';
                tooltip.style.top = event.pageY - 10 + 'px';
              }
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            }) as any : null)
            .on('mousemove', isHub ? ((event: MouseEvent) => {
              if (tooltip) {
                tooltip.style.left = event.pageX + 14 + 'px';
                tooltip.style.top = event.pageY - 10 + 'px';
              }
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            }) as any : null)
            .on('mouseout', isHub ? ((event: MouseEvent) => {
              select(event.currentTarget as Element).attr('r', 4).attr('stroke-width', 1);
              if (tooltip) tooltip.style.opacity = '0';
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            }) as any : null)
            .on('click', isHub ? (() => {
              if (tooltip) tooltip.style.opacity = '0';
              onHubCityClick?.(hubData!);
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            }) as any : null);

          mapG
            .append('text')
            .attr('x', pt[0] + 5)
            .attr('y', pt[1] + 3)
            .attr('fill', isHub ? '#c9a959' : '#5a7aaa')
            .attr('font-size', '7px')
            .attr('font-family', 'Georgia, serif')
            .attr('pointer-events', 'none')
            .attr('opacity', isHub ? 0.9 : 0.7)
            .text(c.name);
        });

        // Store data
        dataRef.current.letters = mapData.letters;
        dataRef.current.people = mapData.people;
        dataRef.current.events = events;
        dataRef.current.timeline = timeline;
        dataRef.current.hubCities = hubCities;

        // Collections for filter
        const cols = [...new Set(mapData.letters.map((l: MapLetter) => l.collection))].sort();
        onCollectionsLoaded?.(cols);
        onEventsLoaded?.(events);
        onTimelineLoaded?.(timeline);

        // Stats
        onStatsChange?.({
          visible: 0,
          total: mapData.letters.length,
          people: mapData.people.length,
        });

        // Draw people
        drawPeople(mapData.people, true);

        // Initial render
        renderArcs(YEAR_MIN, '', 0.5, true, 10, false);
        renderHistoricalEvents(YEAR_MIN, true);

        setLoading(false);
        onLoadingChange?.(false);
      })
      .catch((err) => {
        console.error('Failed to load map data:', err);
        setError(err.message);
        onError?.(err.message);
        setLoading(false);
        onLoadingChange?.(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Re-render on filter / option changes ─────────────────────────────
  useEffect(() => {
    if (loading) return;
    renderArcs(currentYear, filterCollection, arcOpacity, showTrail, windowSize, wymanMode);
    renderHistoricalEvents(currentYear, showEvents);
  }, [filterCollection, arcOpacity, showTrail, windowSize, showEvents, wymanMode]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Re-draw dots when toggled ────────────────────────────────────────
  useEffect(() => {
    if (loading) return;
    drawPeople(dataRef.current.people, showDots);
  }, [showDots, loading, drawPeople]);

  // ── Keyboard shortcuts ───────────────────────────────────────────────
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      // Don't capture keys when user is in an input/select
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;

      if (e.code === 'Space') {
        e.preventDefault();
        if (isPlaying) {
          onPlayingChange(false);
        } else {
          if (currentYearRef.current >= YEAR_MAX) {
            setYearAndRender(YEAR_MIN, filterCollection, arcOpacity, showTrail, windowSize, showEvents, wymanMode);
          }
          onPlayingChange(true);
        }
      } else if (e.code === 'ArrowRight') {
        onPlayingChange(false);
        setYearAndRender(
          currentYearRef.current + 5,
          filterCollection,
          arcOpacity,
          showTrail,
          windowSize,
          showEvents,
          wymanMode,
        );
      } else if (e.code === 'ArrowLeft') {
        onPlayingChange(false);
        setYearAndRender(
          currentYearRef.current - 5,
          filterCollection,
          arcOpacity,
          showTrail,
          windowSize,
          showEvents,
          wymanMode,
        );
      } else if (e.code === 'KeyR') {
        onPlayingChange(false);
        dataRef.current.lastBannerYear = null;
        if (bannerRef.current) bannerRef.current.style.opacity = '0';
        setYearAndRender(YEAR_MIN, filterCollection, arcOpacity, showTrail, windowSize, showEvents, wymanMode);
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isPlaying, filterCollection, arcOpacity, showTrail, windowSize, showEvents, wymanMode, setYearAndRender, onPlayingChange]);

  // ── Render ───────────────────────────────────────────────────────────

  return (
    <div className="relative w-full h-full" style={{ background: '#0d1829' }}>
      {/* Loading */}
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3.5 z-50"
          style={{ background: 'rgba(13,24,41,0.85)' }}>
          {error ? (
            <>
              <p style={{ color: '#e74c3c', fontSize: '1.1em' }}>Error loading data</p>
              <small style={{ color: '#8899aa' }}>{error}</small>
            </>
          ) : (
            <>
              <div className="map-spinner" />
              <p style={{ color: 'var(--color-accent)', fontSize: '1.1em', letterSpacing: 1, fontFamily: 'var(--font-serif)' }}>
                Loading the Roman World...
              </p>
              <small style={{ color: '#8899aa' }}>Fetching letters and geographic data</small>
            </>
          )}
        </div>
      )}

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
        <div className="tt-name" style={{ color: 'var(--color-accent)', fontWeight: 'bold', marginBottom: 4 }} />
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
        <span className="ev-year" style={{ color: '#ff8080', fontWeight: 'bold', marginRight: 6 }} />
        <span className="ev-desc" />
      </div>

      {/* Map SVG */}
      <svg ref={svgRef} style={{ width: '100%', height: '100%', touchAction: 'none' }} />

      {/* CSS keyframes */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes dash {
          to { stroke-dashoffset: -40; }
        }
        .arc-active {
          animation: dash 0.8s linear infinite;
          stroke-dasharray: 12 8;
        }
        @keyframes eventPulse {
          0%   { r: 5; opacity: 1; }
          50%  { r: 9; opacity: 0.5; }
          100% { r: 5; opacity: 1; }
        }
        .event-pulse-ring {
          fill: none;
          stroke: #e74c3c;
          stroke-width: 1.5;
          animation: eventPulse 1.8s ease-in-out infinite;
          pointer-events: none;
        }
        .map-spinner {
          width: 40px;
          height: 40px;
          border: 3px solid #2a3a5c;
          border-top-color: var(--color-accent);
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }
      `}</style>
    </div>
  );
}

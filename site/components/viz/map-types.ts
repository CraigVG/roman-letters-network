// Shared types and constants for the map timelapse feature.
// Kept separate from the component to avoid pulling in D3 dependencies.

export interface HubCity {
  name: string;
  lat: number;
  lon: number;
  total_sent: number;
  total_received: number;
  outgoing_by_decade: Record<string, number>;
  incoming_by_decade: Record<string, number>;
  connectivity_by_decade: Record<string, number>;
  top_correspondents: { city: string; count: number }[];
}

export interface HistoricalEvent {
  year: number;
  lat: number;
  lon: number;
  label: string;
  short: string;
}

export interface MapStats {
  visible: number;
  total: number;
  people: number;
}

export interface TimelineRow {
  decade: number;
  collection: string;
  count: number;
}

export interface MapTimelapseProps {
  currentYear: number;
  onYearChange: (year: number) => void;
  isPlaying: boolean;
  onPlayingChange: (playing: boolean) => void;
  speed: number;
  windowSize: number;
  filterCollection: string;
  arcOpacity: number;
  showTrail: boolean;
  showDots: boolean;
  showEvents: boolean;
  wymanMode?: boolean;
  onStatsChange?: (stats: MapStats) => void;
  onCollectionsLoaded?: (collections: string[]) => void;
  onEventsLoaded?: (events: HistoricalEvent[]) => void;
  onTimelineLoaded?: (timeline: TimelineRow[]) => void;
  onLoadingChange?: (loading: boolean) => void;
  onError?: (error: string | null) => void;
  onHubCityClick?: (city: HubCity) => void;
}

// Collections that are Greek / Eastern and excluded in Wyman Mode
export const WYMAN_EXCLUDED_COLLECTIONS = new Set([
  'basil_caesarea',
  'gregory_nazianzus',
  'libanius',
  'isidore_pelusium',
  'synesius_cyrene',
  'julian_emperor',
  'chrysostom',
  'athanasius_alexandria',
  'theodoret_cyrrhus',
]);

export const WYMAN_YEAR_MIN = 380;
export const WYMAN_YEAR_MAX = 630;

export const YEAR_MIN = 100;
export const YEAR_MAX = 750;
export const YEAR_START = 380; // Default start - beginning of the main late antique corpus

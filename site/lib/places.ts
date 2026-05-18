import { getDb } from './db';

/* ------------------------------------------------------------------ */
/*  Types                                                             */
/* ------------------------------------------------------------------ */

export interface PlaceSummary {
  name: string;
  lat: number | null;
  lon: number | null;
  region: string;
  letter_count: number;
  top_authors: string[];
}

/* ------------------------------------------------------------------ */
/*  Region mapping                                                    */
/* ------------------------------------------------------------------ */

const REGION_MAP: Record<string, string> = {
  // Gaul
  Metz: 'Gaul',
  Cahors: 'Gaul',
  Clermont: 'Gaul',
  Arles: 'Gaul',
  Vienne: 'Gaul',
  Orleans: 'Gaul',
  Paris: 'Gaul',
  Reims: 'Gaul',
  Lyon: 'Gaul',
  Tours: 'Gaul',
  Poitiers: 'Gaul',
  Toulouse: 'Gaul',
  Limoges: 'Gaul',
  'Chalon-sur-Saone': 'Gaul',
  Macon: 'Gaul',
  Epaone: 'Gaul',
  Gaul: 'Gaul',
  Trier: 'Gaul',
  Bordeaux: 'Gaul',
  // Hispania
  Zaragoza: 'Hispania',
  Toledo: 'Hispania',
  Seville: 'Hispania',
  Valencia: 'Hispania',
  // Italia
  Rome: 'Italia',
  Pavia: 'Italia',
  Milan: 'Italia',
  Ravenna: 'Italia',
  Nola: 'Italia',
  // Africa
  'Hippo Regius': 'Africa',
  Carthage: 'Africa',
  // Eastern Empire
  Constantinople: 'Eastern Empire',
  Antioch: 'Eastern Empire',
  Caesarea: 'Eastern Empire',
  Bethlehem: 'Eastern Empire',
  Nazianzus: 'Eastern Empire',
  Cyrrhus: 'Eastern Empire',
  'Ptolemais, Cyrenaica (Libya)': 'Eastern Empire',
};

function assignRegion(name: string): string {
  return REGION_MAP[name] ?? 'Other';
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

export function toPlaceSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

/* ------------------------------------------------------------------ */
/*  Queries                                                           */
/* ------------------------------------------------------------------ */

export function getAllPlaces(): PlaceSummary[] {
  const db = getDb();

  // Get places from letter origins (primary source with coordinates)
  const originPlaces = db
    .prepare(
      `SELECT
         l.origin_place AS name,
         l.origin_lat AS lat,
         l.origin_lon AS lon,
         COUNT(*) AS letter_count,
         GROUP_CONCAT(DISTINCT a.name) AS author_names
       FROM letters l
       LEFT JOIN authors a ON a.id = l.sender_id
       WHERE l.origin_place IS NOT NULL
       GROUP BY l.origin_place
       ORDER BY letter_count DESC`,
    )
    .all() as {
    name: string;
    lat: number | null;
    lon: number | null;
    letter_count: number;
    author_names: string | null;
  }[];

  // Get author locations (secondary — places where authors are based)
  const authorLocations = db
    .prepare(
      `SELECT
         location AS name,
         GROUP_CONCAT(DISTINCT name) AS author_names
       FROM authors
       WHERE location IS NOT NULL
       GROUP BY location`,
    )
    .all() as { name: string; author_names: string | null }[];

  // Build map keyed by place name
  const placeMap = new Map<string, PlaceSummary>();

  for (const row of originPlaces) {
    const authors = row.author_names?.split(',') ?? [];
    placeMap.set(row.name, {
      name: row.name,
      lat: row.lat,
      lon: row.lon,
      region: assignRegion(row.name),
      letter_count: row.letter_count,
      top_authors: authors.slice(0, 3),
    });
  }

  // Merge author locations (add new places, enrich existing)
  for (const row of authorLocations) {
    const authors = row.author_names?.split(',') ?? [];
    const existing = placeMap.get(row.name);
    if (existing) {
      // Merge authors from author table
      const combined = new Set([...existing.top_authors, ...authors]);
      existing.top_authors = [...combined].slice(0, 3);
    } else {
      placeMap.set(row.name, {
        name: row.name,
        lat: null,
        lon: null,
        region: assignRegion(row.name),
        letter_count: 0,
        top_authors: authors.slice(0, 3),
      });
    }
  }

  // Sort by letter count desc, then alphabetically
  return [...placeMap.values()].sort(
    (a, b) => b.letter_count - a.letter_count || a.name.localeCompare(b.name),
  );
}

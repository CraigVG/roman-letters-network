#!/usr/bin/env node
/**
 * generate-regionalization-data.js
 *
 * Reads the SQLite database and produces regionalization.json for the thesis page.
 * Computes per-decade metrics: avg_distance, max_distance, letter_count,
 * unique_city_pairs, pct_long_distance (>500km).
 *
 * Also produces a "wyman" subset (Latin West only, 450-650 AD).
 */

const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const DB_PATH = path.resolve(__dirname, '../../data/roman_letters.db');
const OUT_DIR = path.resolve(__dirname, '../public/data');

fs.mkdirSync(OUT_DIR, { recursive: true });

const db = new Database(DB_PATH, { readonly: true });

// Latin West collections (for Wyman Mode)
const LATIN_WEST_COLLECTIONS = [
  'sidonius_apollinaris',
  'ruricius_limoges',
  'avitus_vienne',
  'ennodius_pavia',
  'cassiodorus',
  'gregory_great',
  'leo_great',
  'gelasius_i',
  'hormisdas',
  'pelagius_i',
  'innocent_i',
  'simplicius_pope',
  'pope_felix_iii',
  'pope_hilary',
  'ambrose_milan',
  'augustine_hippo',
  'jerome',
  'paulinus_nola',
  'salvian_marseille',
  'sulpicius_severus',
  'cyprian_carthage',
  'ferrandus_carthage',
  'desiderius_cahors',
  'columbanus',
  'boniface',
  'alcuin_york',
  'bede',
  'symmachus',
  'pliny_younger',
];

// Greek East collections
const GREEK_EAST_COLLECTIONS = [
  'basil_caesarea',
  'gregory_nazianzus',
  'chrysostom',
  'theodoret_cyrrhus',
  'synesius_cyrene',
  'isidore_pelusium',
  'libanius',
  'julian_emperor',
  'athanasius_alexandria',
];

function computeDecadeMetrics(rows) {
  // Group by decade
  const byDecade = {};
  for (const row of rows) {
    const decade = Math.floor(row.year_approx / 10) * 10;
    if (!byDecade[decade]) byDecade[decade] = [];
    byDecade[decade].push(row);
  }

  const decades = Object.keys(byDecade)
    .map(Number)
    .sort((a, b) => a - b);

  return decades.map((decade) => {
    const letters = byDecade[decade];
    const distances = letters.map((l) => l.distance_km);
    const avg = distances.reduce((a, b) => a + b, 0) / distances.length;
    const max = Math.max(...distances);
    const longDistance = distances.filter((d) => d > 500).length;
    const pairs = new Set(letters.map((l) => `${l.sender_id}-${l.recipient_id}`));

    return {
      decade,
      avg_distance: Math.round(avg),
      max_distance: Math.round(max),
      letter_count: letters.length,
      unique_city_pairs: pairs.size,
      pct_long_distance: Math.round((100 * longDistance) / letters.length),
    };
  });
}

// Fetch all letters with distances > 0
// Letters with distance_km = 0 are same-city correspondence (sender and recipient
// share coordinates). These don't demonstrate long-range connectivity and drag
// every decade's average down, masking the real decline in communication radius.
const allLetters = db
  .prepare(
    `
  SELECT l.id, l.collection, l.year_approx, l.distance_km, l.sender_id, l.recipient_id
  FROM letters l
  WHERE l.distance_km IS NOT NULL AND l.distance_km > 0 AND l.year_approx IS NOT NULL
  ORDER BY l.year_approx
`
  )
  .all();

console.log(`Total letters with non-zero distance data: ${allLetters.length}`);

// All decades
const allDecades = computeDecadeMetrics(allLetters);

// Wyman Mode: Latin West only, 380-630 AD (captures peak AND trough)
const wymanLetters = allLetters.filter(
  (l) =>
    LATIN_WEST_COLLECTIONS.includes(l.collection) &&
    l.year_approx >= 380 &&
    l.year_approx <= 630
);
const wymanDecades = computeDecadeMetrics(wymanLetters);

console.log(`Wyman subset: ${wymanLetters.length} letters`);

// Compute peak and trough for summary stats (require >= 10 letters for reliability)
const decadesInRange = allDecades.filter(
  (d) => d.decade >= 300 && d.decade <= 700 && d.letter_count >= 10
);
const peak = decadesInRange.reduce((a, b) =>
  a.avg_distance > b.avg_distance ? a : b
);
const trough = decadesInRange.reduce((a, b) =>
  a.avg_distance < b.avg_distance ? a : b
);

const output = {
  generated: new Date().toISOString(),
  summary: {
    total_letters_with_distance: allLetters.length,
    peak_decade: peak.decade,
    peak_avg_distance: peak.avg_distance,
    trough_decade: trough.decade,
    trough_avg_distance: trough.avg_distance,
    pct_decline: Math.round(
      ((peak.avg_distance - trough.avg_distance) / peak.avg_distance) * 100
    ),
  },
  all_decades: allDecades,
  wyman_decades: wymanDecades,
  latin_west_collections: LATIN_WEST_COLLECTIONS,
  greek_east_collections: GREEK_EAST_COLLECTIONS,
};

const outPath = path.join(OUT_DIR, 'regionalization.json');
fs.writeFileSync(outPath, JSON.stringify(output, null, 2));
console.log(`Wrote ${outPath}`);

db.close();

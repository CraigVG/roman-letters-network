#!/usr/bin/env node
/**
 * generate-map-data.js
 *
 * Reads the SQLite database and produces three JSON files for the map visualization:
 *   - public/data/map-letters.json
 *   - public/data/timeline.json
 *   - public/data/historical-events.json
 */

const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const DB_PATH = path.resolve(__dirname, '../../data/roman_letters.db');
const OUT_DIR = path.resolve(__dirname, '../public/data');

// Ensure output directory exists
fs.mkdirSync(OUT_DIR, { recursive: true });

const db = new Database(DB_PATH, { readonly: true });

// ── 1. map-letters.json ──────────────────────────────────────────────────
// Letters with sender/recipient coordinates, year, collection
const letters = db.prepare(`
  SELECT
    l.id,
    l.collection,
    l.letter_number,
    l.year_approx,
    l.quick_summary,
    l.interesting_note,
    s.name   AS sender_name,
    s.lat    AS s_lat,
    s.lon    AS s_lon,
    s.role   AS sender_role,
    r.name   AS recipient_name,
    r.lat    AS r_lat,
    r.lon    AS r_lon,
    r.role   AS recipient_role
  FROM letters l
  JOIN authors s ON l.sender_id = s.id
  JOIN authors r ON l.recipient_id = r.id
  WHERE l.year_approx IS NOT NULL
    AND s.lat IS NOT NULL AND s.lon IS NOT NULL
    AND r.lat IS NOT NULL AND r.lon IS NOT NULL
    AND NOT (s.lat = r.lat AND s.lon = r.lon)
  ORDER BY l.year_approx
`).all();

// Also get all people with locations (for dots)
const people = db.prepare(`
  SELECT
    a.id,
    a.name,
    a.role,
    a.location,
    a.lat,
    a.lon,
    a.birth_year,
    a.death_year,
    (SELECT COUNT(*) FROM letters WHERE sender_id = a.id) AS sent,
    (SELECT COUNT(*) FROM letters WHERE recipient_id = a.id) AS received
  FROM authors a
  WHERE a.lat IS NOT NULL AND a.lon IS NOT NULL
  ORDER BY a.name
`).all();

// Combine letters and people into one file for fewer fetches
const mapData = {
  letters: letters.map(l => ({
    id: l.id,
    collection: l.collection,
    letter_number: l.letter_number,
    year_approx: l.year_approx,
    sender_name: l.sender_name,
    s_lat: l.s_lat,
    s_lon: l.s_lon,
    sender_role: l.sender_role,
    recipient_name: l.recipient_name,
    r_lat: l.r_lat,
    r_lon: l.r_lon,
    recipient_role: l.recipient_role,
    quick_summary: l.quick_summary || null,
    interesting_note: l.interesting_note || null,
  })),
  people: people.map(p => ({
    id: p.id,
    name: p.name,
    role: p.role,
    location: p.location,
    lat: p.lat,
    lon: p.lon,
    birth_year: p.birth_year,
    death_year: p.death_year,
    sent: p.sent,
    received: p.received,
  })),
};

fs.writeFileSync(
  path.join(OUT_DIR, 'map-letters.json'),
  JSON.stringify(mapData),
);
console.log(`map-letters.json: ${mapData.letters.length} letters, ${mapData.people.length} people`);

// ── 2. timeline.json ─────────────────────────────────────────────────────
// Letter counts by decade + collection
const timeline = db.prepare(`
  SELECT
    (year_approx / 10) * 10 AS decade,
    collection,
    COUNT(*) AS count
  FROM letters
  WHERE year_approx IS NOT NULL
  GROUP BY decade, collection
  ORDER BY decade, collection
`).all();

fs.writeFileSync(
  path.join(OUT_DIR, 'timeline.json'),
  JSON.stringify(timeline),
);
console.log(`timeline.json: ${timeline.length} decade/collection rows`);

// ── 3. historical-events.json ────────────────────────────────────────────
// 22 curated historical events with year, lat/lon, label
const historicalEvents = [
  { year: 260, lat: 36.20, lon: 36.16, label: 'Valerian captured by Persians', short: 'Valerian captured' },
  { year: 312, lat: 41.90, lon: 12.47, label: 'Constantine wins Battle of Milvian Bridge', short: 'Milvian Bridge' },
  { year: 325, lat: 40.43, lon: 29.72, label: 'Council of Nicaea', short: 'Council of Nicaea' },
  { year: 330, lat: 41.01, lon: 28.98, label: 'Constantinople founded', short: 'Constantinople founded' },
  { year: 378, lat: 41.68, lon: 26.56, label: 'Battle of Adrianople — Goths destroy Roman army', short: 'Battle of Adrianople' },
  { year: 381, lat: 41.01, lon: 28.98, label: 'Council of Constantinople', short: 'Council of Constantinople' },
  { year: 395, lat: 41.01, lon: 28.98, label: 'Roman Empire permanently divided', short: 'Empire divided' },
  { year: 410, lat: 41.90, lon: 12.48, label: "Sack of Rome by Alaric's Visigoths", short: 'Sack of Rome' },
  { year: 430, lat: 36.88, lon: 7.75, label: 'Augustine dies as Vandals besiege Hippo', short: 'Augustine dies at Hippo' },
  { year: 431, lat: 37.94, lon: 27.34, label: 'Council of Ephesus', short: 'Council of Ephesus' },
  { year: 439, lat: 36.81, lon: 10.18, label: 'Vandals capture Carthage', short: 'Vandals take Carthage' },
  { year: 451, lat: 41.01, lon: 28.98, label: 'Council of Chalcedon / Battle of Catalaunian Plains', short: 'Council of Chalcedon' },
  { year: 455, lat: 41.90, lon: 12.48, label: 'Vandals sack Rome', short: 'Vandals sack Rome' },
  { year: 476, lat: 44.42, lon: 12.20, label: 'Last Western Emperor deposed (Ravenna)', short: 'Western Empire falls' },
  { year: 493, lat: 44.42, lon: 12.20, label: 'Theoderic the Ostrogoth takes Italy (Ravenna)', short: 'Theoderic takes Italy' },
  { year: 529, lat: 41.49, lon: 13.81, label: 'Benedict founds Monte Cassino', short: 'Monte Cassino founded' },
  { year: 535, lat: 41.90, lon: 12.48, label: "Justinian's reconquest of Italy begins", short: 'Justinian reconquers Italy' },
  { year: 568, lat: 45.46, lon: 9.19, label: 'Lombard invasion of Italy (Milan)', short: 'Lombard invasion' },
  { year: 590, lat: 41.90, lon: 12.48, label: 'Gregory the Great becomes Pope', short: 'Gregory the Great' },
  { year: 596, lat: 51.50, lon: -0.12, label: "Augustine's mission to England", short: 'Mission to England' },
  { year: 622, lat: 24.47, lon: 39.61, label: "Muhammad's Hijra — start of Islamic expansion", short: 'Islamic Hijra' },
  { year: 711, lat: 36.13, lon: -5.35, label: 'Islamic conquest of Spain (Gibraltar)', short: 'Islamic conquest of Spain' },
];

fs.writeFileSync(
  path.join(OUT_DIR, 'historical-events.json'),
  JSON.stringify(historicalEvents),
);
console.log(`historical-events.json: ${historicalEvents.length} events`);

db.close();
console.log('Done.');

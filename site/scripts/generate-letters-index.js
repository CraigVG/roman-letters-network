#!/usr/bin/env node
/**
 * generate-letters-index.js
 *
 * Reads the SQLite database and produces letters-index.json for the
 * letters browse page. Contains the static corpus with short keys,
 * featured letters for Letter of the Day, topic counts, collection
 * metadata, decade histogram, and curated pathways.
 */

const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const DB_PATH = path.resolve(__dirname, '../../data/roman_letters.db');
const OUT_DIR = path.resolve(__dirname, '../public/data');

fs.mkdirSync(OUT_DIR, { recursive: true });

const db = new Database(DB_PATH, { readonly: true });

const EXISTING_TRANSLATION_SOURCES = [
  '',
  'existing',
  'existing_newadvent',
  'existing_tertullian',
  'existing_fordham',
  'existing_celt',
  'existing_attalus',
  'existing_livius',
  'existing_rogerpearse',
  'existing_haines',
  'gutenberg_winstedt',
  'topostext_shuckburgh_repair_v1',
  'Gummere (Loeb Classical Library, 1917-25)',
  'existing_kalvesmaki_evagrius_2014',
];

const existingTranslationSqlList = EXISTING_TRANSLATION_SOURCES.map((source) => `'${source.replace(/'/g, "''")}'`).join(',');

// ---------------------------------------------------------------------------
// Seeded random shuffle (reproducible builds)
// ---------------------------------------------------------------------------
function seededShuffle(arr, seed = 42) {
  const result = [...arr];
  let s = seed;
  for (let i = result.length - 1; i > 0; i--) {
    s = (s * 1664525 + 1013904223) & 0x7fffffff;
    const j = s % (i + 1);
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

// ---------------------------------------------------------------------------
// Helper: omit null/undefined fields from an object
// ---------------------------------------------------------------------------
function omitNulls(obj) {
  const out = {};
  for (const [k, v] of Object.entries(obj)) {
    if (v !== null && v !== undefined) {
      out[k] = v;
    }
  }
  return out;
}

function routeKeyOrUndefined(row) {
  const key = String(row.route_key || row.letter_number);
  return key === String(row.letter_number) ? undefined : key;
}

// ---------------------------------------------------------------------------
// Helper: format topic slug -> label
// ---------------------------------------------------------------------------
function topicLabel(slug) {
  return slug
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

// ---------------------------------------------------------------------------
// 1. letters — all letters with short keys
// ---------------------------------------------------------------------------
const lettersRows = db
  .prepare(
    `
    WITH duplicate_numbers AS (
      SELECT collection, letter_number, COUNT(*) AS route_count
      FROM letters
      GROUP BY collection, letter_number
    )
    SELECT l.id, l.collection, l.letter_number,
           CASE
             WHEN d.route_count > 1 AND l.ref_id IS NOT NULL AND trim(l.ref_id) != ''
               THEN l.ref_id
             ELSE CAST(l.letter_number AS TEXT)
           END AS route_key,
           l.year_approx,
           a1.name as sender_name, a2.name as recipient_name,
           l.topics, substr(l.quick_summary, 1, 120) as summary,
           l.distance_km,
           CASE WHEN l.modern_english IS NOT NULL
                AND (l.english_text IS NULL OR l.english_text = '')
                AND coalesce(l.translation_source, '') NOT IN (${existingTranslationSqlList})
           THEN 1 ELSE 0 END as first_english
    FROM letters l
    JOIN duplicate_numbers d
      ON d.collection = l.collection AND d.letter_number = l.letter_number
    LEFT JOIN authors a1 ON l.sender_id = a1.id
    LEFT JOIN authors a2 ON l.recipient_id = a2.id
    ORDER BY l.year_approx ASC NULLS LAST, l.collection, l.letter_number
    `
  )
  .all();

const letters = lettersRows.map((row) =>
  omitNulls({
    id: row.id,
    c: row.collection,
    n: row.letter_number,
    k: routeKeyOrUndefined(row),
    y: row.year_approx,
    s: row.sender_name,
    r: row.recipient_name,
    t: row.topics,
    q: row.summary,
    d: row.distance_km,
    f: row.first_english ? 1 : undefined,
  })
);

console.log(`Letters: ${letters.length}`);

// ---------------------------------------------------------------------------
// 2. featured — letters with interesting_note for Letter of the Day
// ---------------------------------------------------------------------------
const featuredRows = db
  .prepare(
    `
    WITH duplicate_numbers AS (
      SELECT collection, letter_number, COUNT(*) AS route_count
      FROM letters
      GROUP BY collection, letter_number
    )
    SELECT l.id, l.collection, l.letter_number,
           CASE
             WHEN d.route_count > 1 AND l.ref_id IS NOT NULL AND trim(l.ref_id) != ''
               THEN l.ref_id
             ELSE CAST(l.letter_number AS TEXT)
           END AS route_key,
           l.year_approx,
           a1.name as sender_name, a2.name as recipient_name,
           l.quick_summary, substr(l.interesting_note, 1, 250) as note,
           l.topics
    FROM letters l
    JOIN duplicate_numbers d
      ON d.collection = l.collection AND d.letter_number = l.letter_number
    LEFT JOIN authors a1 ON l.sender_id = a1.id
    LEFT JOIN authors a2 ON l.recipient_id = a2.id
    WHERE l.interesting_note IS NOT NULL AND length(l.interesting_note) > 10
    ORDER BY l.id
    `
  )
  .all();

const featured = seededShuffle(featuredRows).map((row) =>
  omitNulls({
    id: row.id,
    c: row.collection,
    n: row.letter_number,
    k: routeKeyOrUndefined(row),
    y: row.year_approx,
    s: row.sender_name,
    r: row.recipient_name,
    q: row.quick_summary,
    note: row.note,
    topics: row.topics
      ? row.topics.split(',').map((t) => t.trim())
      : undefined,
  })
);

console.log(`Featured: ${featured.length}`);

// ---------------------------------------------------------------------------
// 3. topics — distinct topic counts
// ---------------------------------------------------------------------------
const topicLetters = db
  .prepare(`SELECT topics FROM letters WHERE topics IS NOT NULL AND topics != ''`)
  .all();

const topicCounts = {};
for (const row of topicLetters) {
  const slugs = row.topics.split(',').map((t) => t.trim());
  for (const slug of slugs) {
    if (slug) {
      topicCounts[slug] = (topicCounts[slug] || 0) + 1;
    }
  }
}

const topics = Object.entries(topicCounts)
  .map(([slug, count]) => ({ slug, label: topicLabel(slug), count }))
  .sort((a, b) => b.count - a.count);

console.log(`Topics: ${topics.length}`);

// ---------------------------------------------------------------------------
// 4. collections — from the collections table
// ---------------------------------------------------------------------------
const collectionsRows = db
  .prepare(
    `
    SELECT slug, author_name, title, letter_count, date_range
    FROM collections
    ORDER BY letter_count DESC
    `
  )
  .all();

const collections = collectionsRows.map((row) => ({
  slug: row.slug,
  name: row.author_name,
  title: row.title,
  count: row.letter_count,
  dateRange: row.date_range,
}));

console.log(`Collections: ${collections.length}`);

// ---------------------------------------------------------------------------
// 5. decades — for timeline histogram
// ---------------------------------------------------------------------------
const decades = db
  .prepare(
    `
    SELECT (year_approx / 10) * 10 as decade, COUNT(*) as count
    FROM letters
    WHERE year_approx IS NOT NULL
    GROUP BY decade
    ORDER BY decade
    `
  )
  .all();

console.log(`Decades: ${decades.length}`);

// ---------------------------------------------------------------------------
// 6. pathways — curated filter combinations
// ---------------------------------------------------------------------------
const pathwayDefs = [
  {
    slug: 'watching-rome-fall',
    title: 'Watching Rome Fall',
    description: 'Letters from the Western provinces as the Empire fragmented',
    filters: { from: 400, to: 500, topic: 'barbarian_invasion' },
  },
  {
    slug: 'women-of-the-late-empire',
    title: 'Women of the Late Empire',
    description: 'Letters by and about women in the Roman world',
    filters: { topic: 'women' },
  },
  {
    slug: 'plague-and-famine',
    title: 'Plague and Famine',
    description: 'Disease and food crisis across the Mediterranean',
    filters: { topic: 'famine_plague' },
  },
  {
    slug: 'imperial-politics',
    title: 'Imperial Politics',
    description: 'Navigating power, patronage, and the imperial court',
    filters: { topic: 'imperial_politics' },
  },
  {
    slug: 'the-monastic-world',
    title: 'The Monastic World',
    description: 'Monasteries, asceticism, and the contemplative life',
    filters: { topic: 'monasticism' },
  },
  {
    slug: 'humor-in-antiquity',
    title: 'Humor in Antiquity',
    description: 'Wit, sarcasm, and comedy in ancient letters',
    filters: { topic: 'humor' },
  },
  {
    slug: 'grief-and-loss',
    title: 'Grief and Loss',
    description: 'Mourning, consolation, and the art of the funeral letter',
    filters: { topic: 'grief_death' },
  },
  {
    slug: 'the-eastern-empire',
    title: 'The Roman Empire in the East',
    description: 'Letters from Constantinople, Antioch, and the Greek-speaking world',
    filters: {
      collection:
        'basil_caesarea,gregory_nazianzus,libanius,chrysostom,theodoret_cyrrhus,synesius_cyrene,isidore_pelusium,julian_emperor,athanasius_alexandria',
    },
  },
  {
    slug: 'first-english-translations',
    title: 'First English Translations',
    description: 'Letters translated into English for the first time by this project',
    filters: { firstEnglish: true },
  },
];

// Compute actual counts for each pathway
function countPathway(filters) {
  const conditions = [];
  const params = [];

  if (filters.from) {
    conditions.push('l.year_approx >= ?');
    params.push(filters.from);
  }
  if (filters.to) {
    conditions.push('l.year_approx <= ?');
    params.push(filters.to);
  }
  if (filters.topic) {
    // topics is CSV, match with LIKE
    conditions.push("(',' || l.topics || ',') LIKE '%,' || ? || ',%'");
    params.push(filters.topic);
  }
  if (filters.collection) {
    const slugs = filters.collection.split(',');
    const placeholders = slugs.map(() => '?').join(',');
    conditions.push(`l.collection IN (${placeholders})`);
    params.push(...slugs);
  }
  if (filters.firstEnglish) {
    conditions.push(`l.modern_english IS NOT NULL`);
    conditions.push(`(l.english_text IS NULL OR l.english_text = '')`);
    conditions.push(`coalesce(l.translation_source, '') NOT IN (${existingTranslationSqlList})`);
  }

  const where = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
  const sql = `SELECT COUNT(*) as count FROM letters l ${where}`;
  return db.prepare(sql).get(...params).count;
}

const pathways = pathwayDefs.map((p) => ({
  ...p,
  count: countPathway(p.filters),
}));

console.log(`Pathways: ${pathways.length}`);
for (const p of pathways) {
  console.log(`  ${p.title}: ${p.count} letters`);
}

// ---------------------------------------------------------------------------
// Write output
// ---------------------------------------------------------------------------
const output = {
  letters,
  featured,
  topics,
  collections,
  decades,
  pathways,
};

const outPath = path.join(OUT_DIR, 'letters-index.json');
const json = JSON.stringify(output);
fs.writeFileSync(outPath, json);

const sizeMB = (Buffer.byteLength(json) / (1024 * 1024)).toFixed(2);
console.log(`\nWrote ${outPath}`);
console.log(`File size: ${sizeMB} MB`);

db.close();

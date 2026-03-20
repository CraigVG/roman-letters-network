#!/usr/bin/env node
/**
 * generate-viz-data.js
 *
 * Reads the SQLite DB and writes public/data/network.json
 * with nodes (authors) and edges (sender->recipient with weight).
 *
 * Usage:  cd site && node scripts/generate-viz-data.js
 */

const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const DB_PATH = path.join(__dirname, '..', '..', 'data', 'roman_letters.db');
const OUT_DIR = path.join(__dirname, '..', 'public', 'data');
const OUT_FILE = path.join(OUT_DIR, 'network.json');

const db = new Database(DB_PATH, { readonly: true });

// --- Nodes: authors with letter counts ---
const authors = db
  .prepare(
    `SELECT
       a.id, a.name, a.role, a.location, a.lat, a.lon,
       a.birth_year, a.death_year, a.bio,
       COALESCE(s.cnt, 0) AS letters_sent,
       COALESCE(r.cnt, 0) AS letters_received
     FROM authors a
     LEFT JOIN (SELECT sender_id, COUNT(*) AS cnt FROM letters GROUP BY sender_id) s
       ON s.sender_id = a.id
     LEFT JOIN (SELECT recipient_id, COUNT(*) AS cnt FROM letters GROUP BY recipient_id) r
       ON r.recipient_id = a.id
     WHERE COALESCE(s.cnt, 0) + COALESCE(r.cnt, 0) > 0
     ORDER BY COALESCE(s.cnt, 0) + COALESCE(r.cnt, 0) DESC`
  )
  .all();

// --- Edges: sender -> recipient with weight + collection ---
const edges = db
  .prepare(
    `SELECT
       sender_id   AS source,
       recipient_id AS target,
       collection,
       COUNT(*)     AS weight
     FROM letters
     WHERE sender_id IS NOT NULL AND recipient_id IS NOT NULL
     GROUP BY sender_id, recipient_id, collection`
  )
  .all();

// --- Collections list (for filter dropdown) ---
const collections = db
  .prepare(
    `SELECT DISTINCT collection, COUNT(*) AS count
     FROM letters
     WHERE sender_id IS NOT NULL AND recipient_id IS NOT NULL
     GROUP BY collection
     ORDER BY count DESC`
  )
  .all();

// Build output
const nodeIds = new Set(authors.map((a) => a.id));

// Only include edges where both endpoints are in the node set
const filteredEdges = edges.filter(
  (e) => nodeIds.has(e.source) && nodeIds.has(e.target)
);

const output = {
  nodes: authors.map((a) => ({
    id: a.id,
    name: a.name,
    role: a.role,
    location: a.location,
    lat: a.lat,
    lon: a.lon,
    birth_year: a.birth_year,
    death_year: a.death_year,
    bio: a.bio,
    letters_sent: a.letters_sent,
    letters_received: a.letters_received,
  })),
  edges: filteredEdges.map((e) => ({
    source: e.source,
    target: e.target,
    weight: e.weight,
    collection: e.collection,
  })),
  collections: collections.map((c) => ({
    collection: c.collection,
    count: c.count,
  })),
};

fs.mkdirSync(OUT_DIR, { recursive: true });
fs.writeFileSync(OUT_FILE, JSON.stringify(output));

console.log(
  `Wrote ${output.nodes.length} nodes, ${output.edges.length} edges, ${output.collections.length} collections to ${OUT_FILE}`
);
console.log(`File size: ${(fs.statSync(OUT_FILE).size / 1024).toFixed(1)} KB`);

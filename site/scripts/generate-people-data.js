#!/usr/bin/env node
/**
 * generate-people-data.js
 *
 * Reads the SQLite DB and writes public/data/people.json
 * with all authors + their mention counts for the /people/ page.
 *
 * Usage:  cd site && node scripts/generate-people-data.js
 */

const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const DB_PATH = path.join(__dirname, '..', '..', 'data', 'roman_letters.db');
const OUT_DIR = path.join(__dirname, '..', 'public', 'data');
const OUT_FILE = path.join(OUT_DIR, 'people.json');

const db = new Database(DB_PATH, { readonly: true });

const people = db
  .prepare(
    `SELECT
       a.id, a.name, a.name_latin, a.role, a.location,
       a.birth_year, a.death_year,
       COALESCE(s.cnt, 0) AS sent_count,
       COALESCE(r.cnt, 0) AS received_count,
       COALESCE(m.cnt, 0) AS mentioned_count
     FROM authors a
     LEFT JOIN (SELECT sender_id, COUNT(*) AS cnt FROM letters GROUP BY sender_id) s
       ON s.sender_id = a.id
     LEFT JOIN (SELECT recipient_id, COUNT(*) AS cnt FROM letters GROUP BY recipient_id) r
       ON r.recipient_id = a.id
     LEFT JOIN (SELECT person_id, COUNT(*) AS cnt FROM people_mentioned GROUP BY person_id) m
       ON m.person_id = a.id
     ORDER BY a.name`
  )
  .all();

// Extract distinct roles for filters
const roles = [...new Set(people.map((p) => p.role).filter(Boolean))].sort();

const output = { people, roles };

fs.mkdirSync(OUT_DIR, { recursive: true });
fs.writeFileSync(OUT_FILE, JSON.stringify(output));

console.log(
  `Wrote ${people.length} people and ${roles.length} roles to ${OUT_FILE} (${(fs.statSync(OUT_FILE).size / 1024).toFixed(1)} KB)`
);

db.close();

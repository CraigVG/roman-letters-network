import assert from 'node:assert/strict';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import Database from 'better-sqlite3';

const HERE = dirname(fileURLToPath(import.meta.url));
const DB_PATH = resolve(HERE, '../../data/roman_letters.db');

const db = new Database(DB_PATH, { readonly: true });

const routeRows = db
  .prepare(
    `WITH duplicate_numbers AS (
       SELECT collection, letter_number, COUNT(*) AS route_count
       FROM letters
       GROUP BY collection, letter_number
     )
     SELECT
       l.id,
       l.collection,
       l.book,
       l.letter_number,
       l.ref_id,
       d.route_count,
       CASE
         WHEN d.route_count > 1 AND l.ref_id IS NOT NULL AND trim(l.ref_id) != ''
           THEN l.ref_id
         ELSE CAST(l.letter_number AS TEXT)
       END AS route_key
     FROM letters l
     JOIN duplicate_numbers d
       ON d.collection = l.collection AND d.letter_number = l.letter_number
     WHERE l.collection IN ('cicero_familiares', 'cicero_atticus')
     ORDER BY l.collection, l.book, l.letter_number, l.id`,
  )
  .all();

const routeByRefId = new Map(routeRows.map((row) => [row.ref_id, row]));

const famStats = db
  .prepare(
    `SELECT
       COUNT(*) AS rows,
       COUNT(DISTINCT letter_number) AS distinct_numbers,
       COUNT(DISTINCT ref_id) AS distinct_ref_ids
     FROM letters
     WHERE collection = 'cicero_familiares'`,
  )
  .get();

assert.equal(famStats.rows, 425);
assert.equal(famStats.distinct_numbers, 79);
assert.equal(famStats.distinct_ref_ids, 425);

const famTenOne = routeByRefId.get('cic.fam.10.i');
assert.ok(famTenOne, 'Cicero Familiares Book 10 letter 1 has a ref_id row');
assert.equal(famTenOne.book, 10);
assert.equal(famTenOne.letter_number, 1);
assert.equal(famTenOne.route_key, 'cic.fam.10.i');
assert.equal(famTenOne.route_count, 16);

const famOneOne = routeByRefId.get('cic.fam.1.i');
assert.ok(famOneOne, 'Cicero Familiares Book 1 letter 1 has a ref_id row');
assert.equal(famOneOne.book, 1);
assert.equal(famOneOne.letter_number, 1);
assert.equal(famOneOne.route_key, 'cic.fam.1.i');

const atticusOne = routeRows.find(
  (row) => row.collection === 'cicero_atticus' && row.letter_number === 1,
);
assert.ok(atticusOne, 'Cicero Atticus letter 1 is present');
assert.equal(atticusOne.route_count, 1);
assert.equal(atticusOne.route_key, '1');

const routeKeys = new Set(routeRows.map((row) => `${row.collection}/${row.route_key}`));
assert.ok(routeKeys.has('cicero_familiares/cic.fam.10.i'));
assert.ok(routeKeys.has('cicero_atticus/1'));

db.close();

import { getDb } from './db';

/* ------------------------------------------------------------------ */
/*  Types                                                             */
/* ------------------------------------------------------------------ */

export interface LetterParam {
  collection: string;
  number: string;
}

export interface LetterRouteFields {
  collection: string;
  letter_number: number;
  book?: number | null;
  ref_id?: string | null;
  route_key?: string | null;
}

export interface LetterSummary {
  id: number;
  collection: string;
  letter_number: number;
  book: number | null;
  ref_id: string | null;
  route_key: string;
  year_approx: number | null;
  quick_summary: string | null;
  sender_name: string | null;
  recipient_name: string | null;
}

export interface LetterFull {
  id: number;
  collection: string;
  book: number | null;
  letter_number: number;
  ref_id: string | null;
  route_key: string;
  sender_id: number | null;
  recipient_id: number | null;
  sender_name: string | null;
  sender_name_latin: string | null;
  recipient_name: string | null;
  recipient_name_latin: string | null;
  year_approx: number | null;
  year_min: number | null;
  year_max: number | null;
  origin_place: string | null;
  dest_place: string | null;
  subject_summary: string | null;
  english_text: string | null;
  latin_text: string | null;
  modern_english: string | null;
  quick_summary: string | null;
  interesting_note: string | null;
  topics: string | null;
  source_url: string | null;
  scan_url: string | null;
  translation_source: string | null;
}

export interface CollectionInfo {
  slug: string;
  author_name: string;
  title: string | null;
  letter_count: number | null;
  date_range: string | null;
  scan_url: string | null;
}

export function getLetterRouteSegment(letter: LetterRouteFields): string {
  return String(letter.route_key || letter.letter_number);
}

export function getLetterHref(letter: LetterRouteFields): string {
  return `/letters/${encodeURIComponent(letter.collection)}/${encodeURIComponent(
    getLetterRouteSegment(letter),
  )}/`;
}

export function getLetterDisplayNumber(letter: LetterRouteFields): string {
  const routeSegment = getLetterRouteSegment(letter);
  if (letter.book != null && routeSegment !== String(letter.letter_number)) {
    return `${letter.book}.${letter.letter_number}`;
  }
  return String(letter.letter_number);
}

/* ------------------------------------------------------------------ */
/*  Queries                                                           */
/* ------------------------------------------------------------------ */

export function getAllLetterParams(): LetterParam[] {
  const db = getDb();
  const rows = db
    .prepare(
      `WITH duplicate_numbers AS (
         SELECT collection, letter_number, COUNT(*) AS route_count
         FROM letters
         GROUP BY collection, letter_number
       )
       SELECT
         l.collection,
         l.letter_number,
         l.ref_id,
         CASE
           WHEN d.route_count > 1 AND l.ref_id IS NOT NULL AND trim(l.ref_id) != ''
             THEN l.ref_id
           ELSE CAST(l.letter_number AS TEXT)
         END AS route_key
       FROM letters l
       JOIN duplicate_numbers d
         ON d.collection = l.collection AND d.letter_number = l.letter_number
       ORDER BY l.collection, l.book, l.letter_number, l.id`,
    )
    .all() as {
      collection: string;
      letter_number: number;
      ref_id: string | null;
      route_key: string;
    }[];

  const params = new Map<string, LetterParam>();
  for (const row of rows) {
    const canonical = {
      collection: row.collection,
      number: row.route_key,
    };
    params.set(`${canonical.collection}/${canonical.number}`, canonical);

    // Preserve legacy numeric static pages for old links and search results.
    const legacy = {
      collection: row.collection,
      number: String(row.letter_number),
    };
    params.set(`${legacy.collection}/${legacy.number}`, legacy);
  }

  return [...params.values()];
}

export function getLetterByCollectionAndNumber(
  collection: string,
  number: number | string,
): LetterFull | undefined {
  const db = getDb();
  const identifier = String(number);
  const isNumericIdentifier = /^\d+$/.test(identifier);
  const predicate = isNumericIdentifier
    ? 'l.collection = ? AND l.letter_number = ?'
    : 'l.collection = ? AND l.ref_id = ?';

  return db
    .prepare(
      `WITH duplicate_numbers AS (
         SELECT collection, letter_number, COUNT(*) AS route_count
         FROM letters
         GROUP BY collection, letter_number
       )
       SELECT
         l.*,
         CASE
           WHEN d.route_count > 1 AND l.ref_id IS NOT NULL AND trim(l.ref_id) != ''
             THEN l.ref_id
           ELSE CAST(l.letter_number AS TEXT)
         END AS route_key,
         s.name   AS sender_name,
         s.name_latin AS sender_name_latin,
         r.name   AS recipient_name,
         r.name_latin AS recipient_name_latin
       FROM letters l
       JOIN duplicate_numbers d
         ON d.collection = l.collection AND d.letter_number = l.letter_number
       LEFT JOIN authors s ON s.id = l.sender_id
       LEFT JOIN authors r ON r.id = l.recipient_id
       WHERE ${predicate}
       ORDER BY l.book IS NULL, l.book, l.letter_number, l.id
       LIMIT 1`,
    )
    .get(collection, isNumericIdentifier ? Number(identifier) : identifier) as
    | LetterFull
    | undefined;
}

export function getLettersByCollection(collection: string): LetterSummary[] {
  const db = getDb();
  return db
    .prepare(
      `WITH duplicate_numbers AS (
         SELECT collection, letter_number, COUNT(*) AS route_count
         FROM letters
         GROUP BY collection, letter_number
       )
       SELECT
         l.id, l.collection, l.letter_number, l.book, l.ref_id,
         CASE
           WHEN d.route_count > 1 AND l.ref_id IS NOT NULL AND trim(l.ref_id) != ''
             THEN l.ref_id
           ELSE CAST(l.letter_number AS TEXT)
         END AS route_key,
         l.year_approx, l.quick_summary,
         s.name AS sender_name,
         r.name AS recipient_name
       FROM letters l
       JOIN duplicate_numbers d
         ON d.collection = l.collection AND d.letter_number = l.letter_number
       LEFT JOIN authors s ON s.id = l.sender_id
       LEFT JOIN authors r ON r.id = l.recipient_id
       WHERE l.collection = ?
       ORDER BY l.book, l.letter_number`,
    )
    .all(collection) as LetterSummary[];
}

export function getCollections(): CollectionInfo[] {
  const db = getDb();
  return db
    .prepare(
      `SELECT slug, author_name, title, letter_count, date_range, scan_url
       FROM collections
       ORDER BY author_name`,
    )
    .all() as CollectionInfo[];
}

export function getAllLetters(): LetterSummary[] {
  const db = getDb();
  return db
    .prepare(
      `WITH duplicate_numbers AS (
         SELECT collection, letter_number, COUNT(*) AS route_count
         FROM letters
         GROUP BY collection, letter_number
       )
       SELECT
         l.id, l.collection, l.letter_number, l.book, l.ref_id,
         CASE
           WHEN d.route_count > 1 AND l.ref_id IS NOT NULL AND trim(l.ref_id) != ''
             THEN l.ref_id
           ELSE CAST(l.letter_number AS TEXT)
         END AS route_key,
         l.year_approx, l.quick_summary,
         s.name AS sender_name,
         r.name AS recipient_name
       FROM letters l
       JOIN duplicate_numbers d
         ON d.collection = l.collection AND d.letter_number = l.letter_number
       LEFT JOIN authors s ON s.id = l.sender_id
       LEFT JOIN authors r ON r.id = l.recipient_id
       ORDER BY l.collection, l.book, l.letter_number`,
    )
    .all() as LetterSummary[];
}

export function getCollectionBySlug(slug: string): CollectionInfo | undefined {
  const db = getDb();
  return db
    .prepare(
      `SELECT slug, author_name, title, letter_count, date_range, scan_url
       FROM collections
       WHERE slug = ?`,
    )
    .get(slug) as CollectionInfo | undefined;
}

export function getCollectionSlugs(): string[] {
  const db = getDb();
  const rows = db
    .prepare('SELECT slug FROM collections ORDER BY author_name')
    .all() as { slug: string }[];
  return rows.map((r) => r.slug);
}

export function getAdjacentLetters(
  collection: string,
  letterId: number,
): { prev: LetterParam | null; next: LetterParam | null } {
  const letters = getLettersByCollection(collection);
  const index = letters.findIndex((letter) => letter.id === letterId);
  const prev = index > 0 ? letters[index - 1] : undefined;
  const next = index >= 0 && index < letters.length - 1 ? letters[index + 1] : undefined;

  return {
    prev: prev
      ? { collection: prev.collection, number: getLetterRouteSegment(prev) }
      : null,
    next: next
      ? { collection: next.collection, number: getLetterRouteSegment(next) }
      : null,
  };
}

export function getRelatedLetters(
  letterId: number,
  topicTags: string | null,
  recipientId: number | null,
  yearApprox: number | null,
): LetterSummary[] {
  const db = getDb();

  // Strategy: same recipient first, then overlapping topics, then nearby year
  // Union them and deduplicate, limit 5
  const parts: string[] = [];
  const params: (string | number)[] = [];

  if (recipientId) {
    parts.push(
      `SELECT l.id, l.collection, l.letter_number, l.book, l.ref_id,
              l.year_approx, l.quick_summary,
              s.name AS sender_name, r.name AS recipient_name,
              1 AS priority
       FROM letters l
       LEFT JOIN authors s ON s.id = l.sender_id
       LEFT JOIN authors r ON r.id = l.recipient_id
       WHERE l.recipient_id = ? AND l.id != ?`,
    );
    params.push(recipientId, letterId);
  }

  if (yearApprox) {
    parts.push(
      `SELECT l.id, l.collection, l.letter_number, l.book, l.ref_id,
              l.year_approx, l.quick_summary,
              s.name AS sender_name, r.name AS recipient_name,
              2 AS priority
       FROM letters l
       LEFT JOIN authors s ON s.id = l.sender_id
       LEFT JOIN authors r ON r.id = l.recipient_id
       WHERE l.year_approx BETWEEN ? AND ? AND l.id != ?`,
    );
    params.push(yearApprox - 10, yearApprox + 10, letterId);
  }

  if (parts.length === 0) {
    return [];
  }

  const sql = `
    WITH duplicate_numbers AS (
      SELECT collection, letter_number, COUNT(*) AS route_count
      FROM letters
      GROUP BY collection, letter_number
    )
    SELECT id, collection, letter_number, book, ref_id,
           CASE
             WHEN route_count > 1 AND ref_id IS NOT NULL AND trim(ref_id) != ''
               THEN ref_id
             ELSE CAST(letter_number AS TEXT)
           END AS route_key,
           year_approx, quick_summary, sender_name, recipient_name
    FROM (
      ${parts.join(' UNION ALL ')}
    ) candidates
    JOIN duplicate_numbers USING (collection, letter_number)
    GROUP BY id
    ORDER BY MIN(priority), RANDOM()
    LIMIT 5
  `;

  return db.prepare(sql).all(...params) as LetterSummary[];
}

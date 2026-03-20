import { getDb } from './db';

/* ------------------------------------------------------------------ */
/*  Types                                                             */
/* ------------------------------------------------------------------ */

export interface LetterParam {
  collection: string;
  number: string;
}

export interface LetterSummary {
  id: number;
  collection: string;
  letter_number: number;
  book: number | null;
  ref_id: string | null;
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

/* ------------------------------------------------------------------ */
/*  Queries                                                           */
/* ------------------------------------------------------------------ */

export function getAllLetterParams(): LetterParam[] {
  const db = getDb();
  const rows = db
    .prepare('SELECT collection, letter_number FROM letters ORDER BY collection, letter_number')
    .all() as { collection: string; letter_number: number }[];

  return rows.map((r) => ({
    collection: r.collection,
    number: String(r.letter_number),
  }));
}

export function getLetterByCollectionAndNumber(
  collection: string,
  number: number,
): LetterFull | undefined {
  const db = getDb();
  return db
    .prepare(
      `SELECT
         l.*,
         s.name   AS sender_name,
         s.name_latin AS sender_name_latin,
         r.name   AS recipient_name,
         r.name_latin AS recipient_name_latin
       FROM letters l
       LEFT JOIN authors s ON s.id = l.sender_id
       LEFT JOIN authors r ON r.id = l.recipient_id
       WHERE l.collection = ? AND l.letter_number = ?`,
    )
    .get(collection, number) as LetterFull | undefined;
}

export function getLettersByCollection(collection: string): LetterSummary[] {
  const db = getDb();
  return db
    .prepare(
      `SELECT
         l.id, l.collection, l.letter_number, l.book, l.ref_id,
         l.year_approx, l.quick_summary,
         s.name AS sender_name,
         r.name AS recipient_name
       FROM letters l
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
      `SELECT
         l.id, l.collection, l.letter_number, l.book, l.ref_id,
         l.year_approx, l.quick_summary,
         s.name AS sender_name,
         r.name AS recipient_name
       FROM letters l
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
  letterNumber: number,
): { prev: LetterParam | null; next: LetterParam | null } {
  const db = getDb();

  const prev = db
    .prepare(
      `SELECT collection, letter_number FROM letters
       WHERE collection = ? AND letter_number < ?
       ORDER BY letter_number DESC LIMIT 1`,
    )
    .get(collection, letterNumber) as
    | { collection: string; letter_number: number }
    | undefined;

  const next = db
    .prepare(
      `SELECT collection, letter_number FROM letters
       WHERE collection = ? AND letter_number > ?
       ORDER BY letter_number ASC LIMIT 1`,
    )
    .get(collection, letterNumber) as
    | { collection: string; letter_number: number }
    | undefined;

  return {
    prev: prev
      ? { collection: prev.collection, number: String(prev.letter_number) }
      : null,
    next: next
      ? { collection: next.collection, number: String(next.letter_number) }
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
    SELECT id, collection, letter_number, book, ref_id,
           year_approx, quick_summary, sender_name, recipient_name
    FROM (
      ${parts.join(' UNION ALL ')}
    )
    GROUP BY id
    ORDER BY MIN(priority), RANDOM()
    LIMIT 5
  `;

  return db.prepare(sql).all(...params) as LetterSummary[];
}

import { getDb } from './db';
import { toSlug } from './authors';

/* ------------------------------------------------------------------ */
/*  Types                                                             */
/* ------------------------------------------------------------------ */

export interface CorrespondencePair {
  person1Slug: string;
  person2Slug: string;
  person1Name: string;
  person2Name: string;
  letterCount: number;
}

export interface ThreadLetter {
  id: number;
  collection: string;
  letter_number: number;
  book: number | null;
  ref_id: string | null;
  year_approx: number | null;
  sender_name: string;
  recipient_name: string;
  quick_summary: string | null;
  english_text: string | null;
  modern_english: string | null;
}

/* ------------------------------------------------------------------ */
/*  Queries                                                           */
/* ------------------------------------------------------------------ */

export function getCorrespondencePairs(minLetters = 3): CorrespondencePair[] {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT
         s.name AS sender_name,
         r.name AS recipient_name,
         COUNT(*) AS letter_count
       FROM letters l
       JOIN authors s ON s.id = l.sender_id
       JOIN authors r ON r.id = l.recipient_id
       GROUP BY
         MIN(l.sender_id, l.recipient_id),
         MAX(l.sender_id, l.recipient_id)
       HAVING COUNT(*) >= ?
       ORDER BY letter_count DESC`,
    )
    .all(minLetters) as {
    sender_name: string;
    recipient_name: string;
    letter_count: number;
  }[];

  return rows.map((r) => {
    const names = [r.sender_name, r.recipient_name].sort();
    return {
      person1Slug: toSlug(names[0]),
      person2Slug: toSlug(names[1]),
      person1Name: names[0],
      person2Name: names[1],
      letterCount: r.letter_count,
    };
  });
}

export function getThread(
  person1Slug: string,
  person2Slug: string,
): ThreadLetter[] {
  const db = getDb();

  // Resolve slugs to author IDs by scanning all authors
  const authors = db
    .prepare('SELECT id, name FROM authors')
    .all() as { id: number; name: string }[];

  const person1 = authors.find((a) => toSlug(a.name) === person1Slug);
  const person2 = authors.find((a) => toSlug(a.name) === person2Slug);

  if (!person1 || !person2) return [];

  return db
    .prepare(
      `SELECT
         l.id, l.collection, l.letter_number, l.book, l.ref_id,
         l.year_approx, l.quick_summary, l.english_text, l.modern_english,
         s.name AS sender_name,
         r.name AS recipient_name
       FROM letters l
       JOIN authors s ON s.id = l.sender_id
       JOIN authors r ON r.id = l.recipient_id
       WHERE (l.sender_id = ? AND l.recipient_id = ?)
          OR (l.sender_id = ? AND l.recipient_id = ?)
       ORDER BY l.year_approx, l.collection, l.book, l.letter_number`,
    )
    .all(person1.id, person2.id, person2.id, person1.id) as ThreadLetter[];
}

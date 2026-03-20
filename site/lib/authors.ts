import { getDb } from './db';

/* ------------------------------------------------------------------ */
/*  Types                                                             */
/* ------------------------------------------------------------------ */

export interface AuthorSlug {
  slug: string;
}

export interface AuthorSummary {
  id: number;
  name: string;
  name_latin: string | null;
  role: string | null;
  location: string | null;
  birth_year: number | null;
  death_year: number | null;
  sent_count: number;
  received_count: number;
}

export interface TopCorrespondent {
  id: number;
  name: string;
  letter_count: number;
}

export interface AuthorFull {
  id: number;
  name: string;
  name_latin: string | null;
  birth_year: number | null;
  death_year: number | null;
  role: string | null;
  location: string | null;
  lat: number | null;
  lon: number | null;
  bio: string | null;
  sent_count: number;
  received_count: number;
  top_correspondents: TopCorrespondent[];
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

export function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

/* ------------------------------------------------------------------ */
/*  Queries                                                           */
/* ------------------------------------------------------------------ */

export function getAllAuthorSlugs(): AuthorSlug[] {
  const db = getDb();
  const rows = db
    .prepare('SELECT name FROM authors ORDER BY name')
    .all() as { name: string }[];

  return rows.map((r) => ({ slug: toSlug(r.name) }));
}

export function getAuthorBySlug(slug: string): AuthorFull | undefined {
  const db = getDb();
  const rows = db
    .prepare('SELECT * FROM authors ORDER BY name')
    .all() as {
    id: number;
    name: string;
    name_latin: string | null;
    birth_year: number | null;
    death_year: number | null;
    role: string | null;
    location: string | null;
    lat: number | null;
    lon: number | null;
    bio: string | null;
  }[];

  const author = rows.find((r) => toSlug(r.name) === slug);
  if (!author) return undefined;

  const sent = db
    .prepare('SELECT COUNT(*) AS cnt FROM letters WHERE sender_id = ?')
    .get(author.id) as { cnt: number };

  const received = db
    .prepare('SELECT COUNT(*) AS cnt FROM letters WHERE recipient_id = ?')
    .get(author.id) as { cnt: number };

  const correspondents = db
    .prepare(
      `SELECT a.id, a.name, COUNT(*) AS letter_count
       FROM (
         SELECT recipient_id AS other_id FROM letters WHERE sender_id = ?
         UNION ALL
         SELECT sender_id AS other_id FROM letters WHERE recipient_id = ?
       ) pairs
       JOIN authors a ON a.id = pairs.other_id
       GROUP BY a.id
       ORDER BY letter_count DESC
       LIMIT 10`,
    )
    .all(author.id, author.id) as TopCorrespondent[];

  return {
    ...author,
    sent_count: sent.cnt,
    received_count: received.cnt,
    top_correspondents: correspondents,
  };
}

export function getAllAuthors(): AuthorSummary[] {
  const db = getDb();
  return db
    .prepare(
      `SELECT
         a.id, a.name, a.name_latin, a.role, a.location,
         a.birth_year, a.death_year,
         COALESCE(s.cnt, 0) AS sent_count,
         COALESCE(r.cnt, 0) AS received_count
       FROM authors a
       LEFT JOIN (SELECT sender_id, COUNT(*) AS cnt FROM letters GROUP BY sender_id) s
         ON s.sender_id = a.id
       LEFT JOIN (SELECT recipient_id, COUNT(*) AS cnt FROM letters GROUP BY recipient_id) r
         ON r.recipient_id = a.id
       ORDER BY a.name`,
    )
    .all() as AuthorSummary[];
}

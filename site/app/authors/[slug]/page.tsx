import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import {
  getAllAuthorSlugs,
  getAuthorBySlug,
  toSlug,
} from '@/lib/authors';
import { authorJsonLd } from '@/lib/seo';
import { getDb } from '@/lib/db';

/* ------------------------------------------------------------------ */
/*  Static generation                                                  */
/* ------------------------------------------------------------------ */

export function generateStaticParams() {
  return getAllAuthorSlugs(); // [{ slug: '...' }, ...]
}

/* ------------------------------------------------------------------ */
/*  SEO metadata                                                       */
/* ------------------------------------------------------------------ */

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const author = getAuthorBySlug(slug);
  if (!author) return {};

  const dates =
    author.birth_year || author.death_year
      ? ` (${author.birth_year ?? '?'}\u2013${author.death_year ?? '?'})`
      : '';

  return {
    title: `${author.name}${dates}`,
    description: author.bio
      ? author.bio.replace(/<[^>]*>/g, '').slice(0, 160)
      : `Letters sent and received by ${author.name} in the late Roman Empire.`,
  };
}

/* ------------------------------------------------------------------ */
/*  Helper: get letters involving this author                          */
/* ------------------------------------------------------------------ */

interface AuthorLetter {
  id: number;
  collection: string;
  letter_number: number;
  year_approx: number | null;
  quick_summary: string | null;
  sender_name: string;
  recipient_name: string;
  direction: 'sent' | 'received';
}

function getAuthorLetters(authorId: number): AuthorLetter[] {
  const db = getDb();
  return db
    .prepare(
      `SELECT
         l.id, l.collection, l.letter_number, l.year_approx, l.quick_summary,
         s.name AS sender_name,
         r.name AS recipient_name,
         CASE WHEN l.sender_id = ? THEN 'sent' ELSE 'received' END AS direction
       FROM letters l
       JOIN authors s ON s.id = l.sender_id
       JOIN authors r ON r.id = l.recipient_id
       WHERE l.sender_id = ? OR l.recipient_id = ?
       ORDER BY l.year_approx, l.collection, l.letter_number`,
    )
    .all(authorId, authorId, authorId) as AuthorLetter[];
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default async function AuthorProfilePage({ params }: PageProps) {
  const { slug } = await params;
  const author = getAuthorBySlug(slug);
  if (!author) notFound();

  const letters = getAuthorLetters(author.id);
  const totalLetters = author.sent_count + author.received_count;
  const correspondentCount = author.top_correspondents.length;

  const dates =
    author.birth_year || author.death_year
      ? `${author.birth_year ?? '?'}\u2013${author.death_year ?? '?'}`
      : null;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6">
      <Breadcrumbs
        segments={[
          { label: 'Authors', href: '/authors' },
          { label: author.name },
        ]}
      />

      {/* JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(authorJsonLd(author)) }}
      />

      {/* Header */}
      <header className="pt-8 pb-8 border-b border-theme">
        <h1
          className="text-3xl sm:text-4xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          {author.name}
        </h1>
        {author.name_latin && (
          <p className="mt-1.5 text-sm text-theme-muted italic" style={{ fontFamily: 'var(--font-serif)' }}>
            {author.name_latin}
          </p>
        )}

        <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-theme-muted">
          {author.role && <span>{author.role}</span>}
          {author.role && dates && <span className="text-theme-muted/40">|</span>}
          {dates && <span className="tabular-nums">{dates}</span>}
          {(author.role || dates) && author.location && <span className="text-theme-muted/40">|</span>}
          {author.location && <span>{author.location}</span>}
        </div>
      </header>

      {/* Bio */}
      {author.bio && (
        <section className="py-8 border-b border-theme">
          <div
            className="prose prose-sm dark:prose-invert max-w-3xl text-theme-text leading-relaxed"
            dangerouslySetInnerHTML={{ __html: author.bio }}
          />
        </section>
      )}

      {/* Stats */}
      <section className="py-10 border-b border-theme">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-8">
          {[
            { label: 'Letters sent', value: author.sent_count },
            { label: 'Letters received', value: author.received_count },
            { label: 'Total letters', value: totalLetters },
            { label: 'Correspondents', value: correspondentCount },
          ].map((stat) => (
            <div key={stat.label}>
              <div
                className="text-3xl sm:text-4xl font-light text-theme-accent tabular-nums"
                style={{ fontFamily: 'var(--font-serif)', fontVariantNumeric: 'oldstyle-nums' }}
              >
                {stat.value}
              </div>
              <div className="mt-2 text-xs text-theme-muted tracking-wide">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Top Correspondents */}
      {author.top_correspondents.length > 0 && (
        <section className="py-10 border-b border-theme">
          <h2
            className="text-xl tracking-tight mb-6"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Top correspondents
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {author.top_correspondents.map((c) => {
              const slugs = [slug, toSlug(c.name)].sort();
              return (
                <Link
                  key={c.id}
                  href={`/correspondence/${slugs[0]}/${slugs[1]}`}
                  className="group flex items-center justify-between p-4 rounded-lg border border-theme
                    bg-theme-surface hover:border-[var(--color-accent)] transition-all duration-200"
                >
                  <span className="text-sm font-medium text-theme-text group-hover:text-theme-accent transition-colors">
                    {c.name}
                  </span>
                  <span
                    className="text-sm text-theme-accent tabular-nums font-light"
                    style={{ fontFamily: 'var(--font-serif)', fontVariantNumeric: 'oldstyle-nums' }}
                  >
                    {c.letter_count}
                  </span>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {/* Letter list */}
      <section className="py-10 pb-16">
        <h2
          className="text-xl tracking-tight mb-6"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          All letters ({totalLetters})
        </h2>
        <div className="divide-y divide-[var(--color-border)]">
          {letters.map((letter, i) => (
            <Link
              key={letter.id}
              href={`/letters/${encodeURIComponent(letter.collection)}/${letter.letter_number}`}
              className={`flex items-start gap-3 py-3.5 px-4 -mx-4
                hover:bg-theme-surface transition-colors group rounded-lg ${
                  i % 2 === 0 ? '' : 'bg-theme-surface/50'
                }`}
            >
              <span
                className={`shrink-0 w-5 h-5 rounded-full text-[10px] font-medium flex items-center justify-center mt-0.5 ${
                  letter.direction === 'sent'
                    ? 'bg-theme-accent/15 text-theme-accent'
                    : 'bg-theme-surface border border-theme text-theme-muted'
                }`}
              >
                {letter.direction === 'sent' ? '\u2192' : '\u2190'}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                  <span className="text-sm font-medium text-theme-text group-hover:text-theme-accent transition-colors truncate">
                    {letter.direction === 'sent'
                      ? `To ${letter.recipient_name}`
                      : `From ${letter.sender_name}`}
                  </span>
                  {letter.year_approx && (
                    <span className="shrink-0 text-xs text-theme-muted tabular-nums">
                      c.&thinsp;{letter.year_approx}
                    </span>
                  )}
                </div>
                {letter.quick_summary && (
                  <p className="text-xs text-theme-muted mt-0.5 truncate">
                    {letter.quick_summary}
                  </p>
                )}
              </div>
              <span className="shrink-0 text-xs text-theme-muted capitalize">
                {letter.collection.replace(/_/g, ' ')} #{letter.letter_number}
              </span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

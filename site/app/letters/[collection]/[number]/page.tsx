import Link from 'next/link';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { existsSync } from 'fs';
import path from 'path';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import { Badge } from '@/components/ui/Badge';
import {
  getAllLetterParams,
  getLetterByCollectionAndNumber,
  getCollectionBySlug,
  getAdjacentLetters,
  getRelatedLetters,
} from '@/lib/letters';
import { letterJsonLd } from '@/lib/seo';
import { VersionTabs } from './VersionTabs';

interface Props {
  params: Promise<{ collection: string; number: string }>;
}

export function generateStaticParams() {
  return getAllLetterParams();
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { collection, number } = await params;
  const letter = getLetterByCollectionAndNumber(collection, Number(number));
  if (!letter) return {};

  const sender = letter.sender_name ?? 'Unknown';
  const yearStr = letter.year_approx ? ` (~${letter.year_approx} AD)` : '';

  const title = letter.recipient_name
    ? `${sender} to ${letter.recipient_name}${yearStr}`
    : `${sender} - Letter ${letter.letter_number}${yearStr}`;

  const rawDesc =
    (letter.quick_summary && letter.quick_summary.length <= 200
      ? letter.quick_summary
      : null)
    ?? letter.modern_english
    ?? letter.english_text;

  const description = rawDesc
    ? rawDesc.replace(/\s+/g, ' ').trim().slice(0, 160).replace(/\s\S*$/, '…')
    : `Letter ${letter.letter_number} from ${sender} in the ${collection.replace(/_/g, ' ')} collection.`;

  // Resolve OG image: prefer letter-specific, fall back to collection, then none
  const ogDir = path.join(process.cwd(), 'public', 'og');
  const letterImg = `${collection}-${number}.png`;
  const collectionImg = `collection-${collection}.png`;
  const ogImage = existsSync(path.join(ogDir, letterImg))
    ? `/og/${letterImg}`
    : existsSync(path.join(ogDir, collectionImg))
    ? `/og/${collectionImg}`
    : undefined;

  return {
    title,
    description,
    openGraph: {
      title: `${title} | Roman Letters`,
      description,
      type: 'article',
      ...(ogImage && {
        images: [{ url: ogImage, width: 1200, height: 630, alt: title }],
      }),
    },
  };
}

export default async function LetterPage({ params }: Props) {
  const { collection: collectionSlug, number } = await params;
  const letterNumber = Number(number);
  const letter = getLetterByCollectionAndNumber(collectionSlug, letterNumber);
  if (!letter) notFound();

  const collection = getCollectionBySlug(collectionSlug);
  const adjacent = getAdjacentLetters(collectionSlug, letterNumber);
  const related = getRelatedLetters(
    letter.id,
    letter.topics,
    letter.recipient_id,
    letter.year_approx,
  );

  const collectionLabel = collectionSlug.replace(/_/g, ' ');
  const jsonLd = letterJsonLd(letter);
  const topics = letter.topics
    ? letter.topics.split(',').map((t) => t.trim()).filter(Boolean)
    : [];

  const title = letter.quick_summary
    ? `Letter ${letter.letter_number}: ${letter.quick_summary}`
    : `Letter ${letter.letter_number}`;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8" data-pagefind-body>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Breadcrumbs */}
      <Breadcrumbs
        segments={[
          { label: 'Letters', href: '/letters/' },
          {
            label: collection?.author_name ?? collectionLabel,
            href: `/letters/${collectionSlug}/`,
          },
          { label: `Letter ${letter.letter_number}` },
        ]}
      />

      {/* Header */}
      <header className="mt-6">
        <h1
          className="text-2xl sm:text-3xl lg:text-4xl tracking-tight leading-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
          data-pagefind-meta="title"
        >
          {title}
        </h1>

        {/* Metadata bar */}
        <div className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-theme-muted">
          {(letter.sender_name || letter.recipient_name) && (
            <span className="flex items-center gap-2">
              <strong className="text-theme-text font-medium">
                {letter.sender_name ?? 'Unknown'}
              </strong>
              <span className="text-theme-accent">{'\u2192'}</span>
              <strong className="text-theme-text font-medium">
                {letter.recipient_name ?? 'Unknown'}
              </strong>
            </span>
          )}
          {letter.year_approx && (
            <>
              <span className="text-theme-muted/40">|</span>
              <span className="tabular-nums" style={{ fontVariantNumeric: 'oldstyle-nums' }}>
                c.&thinsp;{letter.year_approx} AD
              </span>
            </>
          )}
          <span className="text-theme-muted/40">|</span>
          <span className="capitalize" data-pagefind-filter="collection">{collectionLabel}</span>
          {letter.origin_place && (
            <>
              <span className="text-theme-muted/40">|</span>
              <span>From {letter.origin_place}</span>
            </>
          )}
          {letter.dest_place && (
            <>
              <span className="text-theme-muted/40">|</span>
              <span>To {letter.dest_place}</span>
            </>
          )}
        </div>

        {/* Topic pills */}
        {topics.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {topics.map((topic) => (
              <Badge key={topic} topic={topic} />
            ))}
          </div>
        )}

        {/* Interesting note */}
        {letter.interesting_note && (
          <div
            className="mt-5 p-4 rounded-r-lg bg-theme-surface text-sm text-theme-muted leading-relaxed"
            style={{ borderLeft: '3px solid var(--color-accent)' }}
          >
            {letter.interesting_note}
          </div>
        )}
      </header>

      {/* Hidden text for Pagefind indexing (client tabs aren't in static HTML) */}
      {letter.modern_english && (
        <div data-pagefind-weight="2" className="hidden">
          {letter.modern_english}
        </div>
      )}
      {letter.english_text && (
        <div data-pagefind-weight="1" className="hidden">
          {letter.english_text}
        </div>
      )}
      {letter.latin_text && (
        <div data-pagefind-weight="1" className="hidden">
          {letter.latin_text}
        </div>
      )}

      {/* Divider between metadata and letter text */}
      <div className="mt-8 mb-8 flex items-center gap-3">
        <span className="h-px flex-1" style={{ backgroundColor: 'var(--color-border)' }} />
        <span className="text-theme-accent text-[10px]">&#9670;</span>
        <span className="h-px flex-1" style={{ backgroundColor: 'var(--color-border)' }} />
      </div>

      {/* Version tabs + letter content */}
      <section>
        <VersionTabs
          modernEnglish={letter.modern_english}
          english={letter.english_text}
          latin={letter.latin_text}
        />
      </section>

      {/* Source links */}
      {(letter.source_url || letter.scan_url) && (
        <div className="mt-6 flex flex-wrap gap-4 text-sm">
          {letter.source_url && (
            <a
              href={letter.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-theme-accent hover:underline"
            >
              Translation source &rarr;
            </a>
          )}
          {letter.scan_url && (
            <a
              href={letter.scan_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-theme-accent hover:underline"
            >
              Original scan &rarr;
            </a>
          )}
        </div>
      )}

      {/* Related letters */}
      {related.length > 0 && (
        <section className="mt-16 border-t border-theme pt-8 overflow-hidden">
          <h2
            className="text-lg sm:text-xl tracking-tight"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Related Letters
          </h2>
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2">
            {related.map((r) => (
              <Link
                key={r.id}
                href={`/letters/${r.collection}/${r.letter_number}/`}
                className="group block py-3 px-4 rounded-lg border border-theme bg-theme-surface
                  hover:border-[var(--color-accent)] transition-colors overflow-hidden"
              >
                <div className="flex items-baseline justify-between gap-2 text-sm min-w-0">
                  <span className="font-medium group-hover:text-theme-accent transition-colors truncate min-w-0">
                    {r.sender_name ?? 'Unknown'}
                    <span className="text-theme-accent mx-1.5">{'\u2192'}</span>
                    {r.recipient_name ?? 'Unknown'}
                  </span>
                  <span className="shrink-0 text-xs text-theme-muted tabular-nums">
                    {r.year_approx && <>c.&thinsp;{r.year_approx} &middot; </>}
                    <span className="capitalize">{r.collection.replace(/_/g, ' ')}</span> #{r.letter_number}
                  </span>
                </div>
                {r.quick_summary && (
                  <p className="mt-1 text-sm text-theme-muted line-clamp-2">
                    {r.quick_summary}
                  </p>
                )}
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Prev/Next navigation */}
      <nav className="mt-16 border-t border-theme pt-8 pb-4">
        <div className="grid grid-cols-2 sm:grid-cols-3 items-center gap-4">
          {adjacent.prev ? (
            <Link
              href={`/letters/${adjacent.prev.collection}/${adjacent.prev.number}/`}
              className="group flex flex-col items-start gap-1 py-3 px-4 rounded-lg border border-theme
                bg-theme-surface hover:border-[var(--color-accent)] transition-colors"
            >
              <span className="text-xs text-theme-muted group-hover:text-theme-accent transition-colors">&larr; Previous</span>
              <span className="text-sm font-medium text-theme-text group-hover:text-theme-accent transition-colors">
                Letter {adjacent.prev.number}
              </span>
            </Link>
          ) : (
            <span />
          )}
          <div className="hidden sm:block text-center">
            <Link
              href={`/letters/${collectionSlug}/`}
              className="text-sm text-theme-muted hover:text-theme-accent transition-colors"
            >
              All {collectionLabel}
            </Link>
          </div>
          {adjacent.next ? (
            <Link
              href={`/letters/${adjacent.next.collection}/${adjacent.next.number}/`}
              className="group flex flex-col items-end gap-1 py-3 px-4 rounded-lg border border-theme
                bg-theme-surface hover:border-[var(--color-accent)] transition-colors"
            >
              <span className="text-xs text-theme-muted group-hover:text-theme-accent transition-colors">Next &rarr;</span>
              <span className="text-sm font-medium text-theme-text group-hover:text-theme-accent transition-colors">
                Letter {adjacent.next.number}
              </span>
            </Link>
          ) : (
            <span />
          )}
        </div>
        <div className="mt-4 text-center sm:hidden">
          <Link
            href={`/letters/${collectionSlug}/`}
            className="text-sm text-theme-muted hover:text-theme-accent transition-colors"
          >
            All {collectionLabel}
          </Link>
        </div>
      </nav>
    </div>
  );
}

import Link from 'next/link';
import type { Metadata } from 'next';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import {
  getCollectionSlugs,
  getCollectionBySlug,
  getLettersByCollection,
} from '@/lib/letters';
import { collectionJsonLd } from '@/lib/seo';
import { notFound } from 'next/navigation';

interface Props {
  params: Promise<{ collection: string }>;
}

export function generateStaticParams() {
  return getCollectionSlugs().map((slug) => ({ collection: slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { collection: slug } = await params;
  const collection = getCollectionBySlug(slug);
  if (!collection) return {};

  const title = collection.title ?? `${collection.author_name} Letters`;
  const description = `Read ${collection.letter_count ?? 'the'} surviving letters of ${collection.author_name}${collection.date_range ? ` (${collection.date_range})` : ''} in modern English translation.`;

  return {
    title,
    description,
    openGraph: {
      title: `${title} | Roman Letters`,
      description,
      type: 'website',
    },
  };
}

export default async function CollectionPage({ params }: Props) {
  const { collection: slug } = await params;
  const collection = getCollectionBySlug(slug);
  if (!collection) notFound();

  const letters = getLettersByCollection(slug);
  const title = collection.title ?? `${collection.author_name} Letters`;

  // Compute date range from actual letters if collection doesn't have one
  const years = letters
    .map((l) => l.year_approx)
    .filter((y): y is number => y !== null);
  const minYear = years.length > 0 ? Math.min(...years) : null;
  const maxYear = years.length > 0 ? Math.max(...years) : null;
  const dateRange = collection.date_range ?? (minYear && maxYear ? `${minYear}-${maxYear} AD` : null);

  const jsonLd = collectionJsonLd(collection);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <Breadcrumbs
        segments={[
          { label: 'Letters', href: '/letters/' },
          { label: collection.author_name },
        ]}
      />

      <header className="mt-4">
        <h1
          className="text-3xl sm:text-4xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          {title}
        </h1>

        {/* Metadata bar */}
        <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-theme-muted">
          <span>
            <strong className="text-theme-text">{letters.length}</strong> letters
          </span>
          {dateRange && (
            <span>
              <strong className="text-theme-text">{dateRange}</strong>
            </span>
          )}
          <span>
            by <strong className="text-theme-text">{collection.author_name}</strong>
          </span>
        </div>

        {collection.scan_url && (
          <p className="mt-3 text-sm">
            <a
              href={collection.scan_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-theme-accent hover:underline"
            >
              View original scans on Internet Archive &rarr;
            </a>
          </p>
        )}
      </header>

      {/* Letter list */}
      <section className="mt-10">
        <div className="divide-y divide-[var(--color-border)]">
          {letters.map((letter) => (
            <Link
              key={letter.id}
              href={`/letters/${slug}/${letter.letter_number}/`}
              className="group block py-3 hover:bg-theme-surface transition-colors -mx-3 px-3 rounded"
            >
              <div className="flex items-start gap-3 overflow-hidden">
                <span className="text-xs text-theme-muted tabular-nums shrink-0 mt-0.5 w-8 text-right">
                  #{letter.letter_number}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline gap-2 flex-wrap">
                    <span className="text-sm font-medium group-hover:text-theme-accent transition-colors truncate">
                      {letter.sender_name ?? 'Unknown'}
                      {' \u2192 '}
                      {letter.recipient_name ?? 'Unknown'}
                    </span>
                    {letter.year_approx && (
                      <span className="text-xs text-theme-muted tabular-nums">
                        ~{letter.year_approx} AD
                      </span>
                    )}
                  </div>
                  {letter.quick_summary && (
                    <p className="mt-0.5 text-sm text-theme-muted truncate">
                      {letter.quick_summary}
                    </p>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {letters.length === 0 && (
        <p className="mt-8 text-theme-muted text-center py-12">
          No letters found in this collection yet.
        </p>
      )}
    </div>
  );
}

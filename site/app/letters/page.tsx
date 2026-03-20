import Link from 'next/link';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import { getAllLetters, getCollections } from '@/lib/letters';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Browse Letters',
  description:
    'Browse over 6,000 surviving letters from the late Roman Empire (300-600 AD), including correspondence from Augustine, Gregory the Great, Basil, Jerome, and more.',
};

const LETTERS_PER_PAGE = 50;

export default function LettersBrowsePage() {
  const letters = getAllLetters();
  const collections = getCollections();
  const totalPages = Math.ceil(letters.length / LETTERS_PER_PAGE);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      <Breadcrumbs segments={[{ label: 'Letters' }]} />

      <h1
        className="text-3xl sm:text-4xl tracking-tight mt-4"
        style={{ fontFamily: 'var(--font-serif)' }}
      >
        Browse Letters
      </h1>
      <p className="mt-2 text-theme-muted max-w-2xl">
        {letters.length.toLocaleString()} letters from {collections.length} collections
        spanning the late Roman Empire.
      </p>

      {/* Collections grid */}
      <section className="mt-10">
        <h2
          className="text-xl sm:text-2xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Collections
        </h2>
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {collections.map((c) => (
            <Link
              key={c.slug}
              href={`/letters/${c.slug}/`}
              className="group block p-4 rounded-lg border border-theme bg-theme-surface
                hover:border-[var(--color-accent)] transition-colors"
            >
              <div className="flex items-baseline justify-between">
                <h3
                  className="text-base group-hover:text-theme-accent transition-colors"
                  style={{ fontFamily: 'var(--font-serif)' }}
                >
                  {c.author_name}
                </h3>
                {c.date_range && (
                  <span className="text-xs text-theme-muted tabular-nums ml-2 shrink-0">
                    {c.date_range}
                  </span>
                )}
              </div>
              {c.title && (
                <p className="mt-1 text-sm text-theme-muted truncate">{c.title}</p>
              )}
              <div className="mt-2 text-xs text-theme-accent font-medium">
                {c.letter_count ?? '?'} letters
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* All letters list */}
      <section className="mt-12">
        <h2
          className="text-xl sm:text-2xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          All Letters
        </h2>
        <div className="mt-4 divide-y divide-[var(--color-border)]">
          {letters.map((letter) => (
            <Link
              key={letter.id}
              href={`/letters/${letter.collection}/${letter.letter_number}/`}
              className="group block py-3 hover:bg-theme-surface transition-colors -mx-3 px-3 rounded"
            >
              <div className="flex items-start gap-3 overflow-hidden">
                <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                  bg-theme-surface border border-theme text-theme-muted whitespace-nowrap shrink-0">
                  {letter.collection.replace(/_/g, ' ')}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline gap-2 flex-wrap">
                    <span className="text-sm font-medium group-hover:text-theme-accent transition-colors truncate">
                      {letter.sender_name ?? 'Unknown'}
                      {' \u2192 '}
                      {letter.recipient_name ?? 'Unknown'}
                    </span>
                    {letter.year_approx && (
                      <span className="text-xs text-theme-muted tabular-nums shrink-0">
                        ~{letter.year_approx} AD
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 text-xs text-theme-muted sm:hidden capitalize">
                    {letter.collection.replace(/_/g, ' ')}
                  </p>
                  {letter.quick_summary && (
                    <p className="mt-0.5 text-sm text-theme-muted truncate">
                      {letter.quick_summary}
                    </p>
                  )}
                </div>
                <span className="text-xs text-theme-muted tabular-nums shrink-0">
                  #{letter.letter_number}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

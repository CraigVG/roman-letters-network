import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import { getCorrespondencePairs, getThread } from '@/lib/correspondence';
import { toSlug } from '@/lib/authors';

/* ------------------------------------------------------------------ */
/*  Static generation                                                  */
/* ------------------------------------------------------------------ */

export function generateStaticParams() {
  const pairs = getCorrespondencePairs(3);
  return pairs.map((p) => ({
    person1: p.person1Slug,
    person2: p.person2Slug,
  }));
}

/* ------------------------------------------------------------------ */
/*  SEO metadata                                                       */
/* ------------------------------------------------------------------ */

interface PageProps {
  params: Promise<{ person1: string; person2: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { person1, person2 } = await params;
  const letters = getThread(person1, person2);
  if (letters.length === 0) return {};

  const name1 = letters[0].sender_name;
  const name2 = letters[0].recipient_name;

  // Use the names from the first letter - pick correct ordering
  const names = [name1, name2].sort();

  return {
    title: `${names[0]} & ${names[1]} \u2014 Correspondence`,
    description: `${letters.length} surviving letters exchanged between ${names[0]} and ${names[1]} in the late Roman Empire.`,
  };
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default async function CorrespondencePage({ params }: PageProps) {
  const { person1, person2 } = await params;
  const letters = getThread(person1, person2);
  if (letters.length === 0) notFound();

  // Determine canonical person names from letters
  const allNames = new Set<string>();
  letters.forEach((l) => {
    allNames.add(l.sender_name);
    allNames.add(l.recipient_name);
  });
  const sortedNames = Array.from(allNames).sort();
  const personA = sortedNames[0];
  const personB = sortedNames[1] ?? sortedNames[0];

  // Year range
  const years = letters
    .map((l) => l.year_approx)
    .filter((y): y is number => y !== null);
  const yearRange =
    years.length > 0
      ? `c. ${Math.min(...years)}\u2013${Math.max(...years)}`
      : null;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6">
      <Breadcrumbs
        segments={[
          { label: 'Authors', href: '/authors' },
          { label: personA, href: `/authors/${toSlug(personA)}` },
          { label: `& ${personB}` },
        ]}
      />

      {/* Header */}
      <header className="pt-8 pb-8 border-b border-theme">
        <h1
          className="text-2xl sm:text-3xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          {personA} & {personB}
        </h1>
        <p className="mt-3 text-theme-muted leading-relaxed">
          {letters.length} surviving letters between{' '}
          <Link
            href={`/authors/${toSlug(personA)}`}
            className="text-theme-accent hover:underline"
          >
            {personA}
          </Link>{' '}
          and{' '}
          <Link
            href={`/authors/${toSlug(personB)}`}
            className="text-theme-accent hover:underline"
          >
            {personB}
          </Link>
          {yearRange ? `, spanning ${yearRange}` : ''}.
        </p>
      </header>

      {/* Thread */}
      <section className="py-8 pb-16">
        <div className="space-y-6">
          {letters.map((letter, i) => {
            const isSenderA = letter.sender_name === personA;
            const openingLine = getOpeningLine(
              letter.modern_english ?? letter.english_text,
            );

            return (
              <div
                key={letter.id}
                className={`flex ${isSenderA ? 'justify-start' : 'justify-end'}`}
              >
                <Link
                  href={`/letters/${encodeURIComponent(letter.collection)}/${letter.letter_number}`}
                  className={`block max-w-lg w-full sm:w-[85%] p-4 rounded-lg border border-theme
                    bg-theme-surface hover:border-[var(--color-accent)] transition-colors group
                    ${isSenderA ? 'rounded-tl-none' : 'rounded-tr-none'}`}
                >
                  {/* Sender + date */}
                  <div className="flex items-baseline justify-between gap-2 mb-2">
                    <span className="text-xs font-medium text-theme-accent">
                      {letter.sender_name}
                    </span>
                    {letter.year_approx && (
                      <span className="text-xs text-theme-muted tabular-nums">
                        c. {letter.year_approx}
                      </span>
                    )}
                  </div>

                  {/* Summary or opening line */}
                  {letter.quick_summary ? (
                    <p className="text-sm text-theme-text leading-relaxed group-hover:text-theme-accent transition-colors">
                      {letter.quick_summary}
                    </p>
                  ) : openingLine ? (
                    <p className="text-sm text-theme-muted italic leading-relaxed">
                      &ldquo;{openingLine}&rdquo;
                    </p>
                  ) : (
                    <p className="text-sm text-theme-muted italic">
                      [No text available]
                    </p>
                  )}

                  {/* Reference */}
                  <div className="mt-2 text-xs text-theme-muted">
                    {letter.collection.replace(/_/g, ' ')}, Letter{' '}
                    {letter.letter_number}
                    {letter.book ? ` (Book ${letter.book})` : ''}
                  </div>
                </Link>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function getOpeningLine(text: string | null): string | null {
  if (!text) return null;
  // Strip HTML tags and grab first sentence or first ~120 chars
  const plain = text.replace(/<[^>]*>/g, '').trim();
  if (!plain) return null;

  const firstSentence = plain.match(/^[^.!?]+[.!?]/);
  if (firstSentence && firstSentence[0].length <= 150) {
    return firstSentence[0];
  }
  return plain.slice(0, 120) + '\u2026';
}

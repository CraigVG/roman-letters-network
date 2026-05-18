import type { Metadata } from 'next';
import Link from 'next/link';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import { CORPUS } from '@/lib/corpus';
import { getPublishedRevisionSummaries } from '@/lib/letter-revisions';

export const metadata: Metadata = {
  title: 'Corrections',
  description:
    'Correction workflow and revision log for Roman Letters source texts, translations, and metadata.',
};

const issueLinks = [
  {
    label: 'Transcription correction',
    href: `${CORPUS.githubUrl}/issues/new?template=transcription-correction.md&labels=correction,transcription`,
  },
  {
    label: 'Translation correction',
    href: `${CORPUS.githubUrl}/issues/new?template=translation-correction.md&labels=correction,translation`,
  },
  {
    label: 'Person or metadata correction',
    href: `${CORPUS.githubUrl}/issues/new?template=metadata-correction.md&labels=correction,metadata`,
  },
  {
    label: 'Source-link correction',
    href: `${CORPUS.githubUrl}/issues/new?template=source-link-correction.md&labels=correction,sources`,
  },
];

export default function CorrectionsPage() {
  const revisions = getPublishedRevisionSummaries();

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <Breadcrumbs segments={[{ label: 'Corrections' }]} />

      <header className="mt-6 pb-8">
        <h1
          className="text-3xl sm:text-4xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Corrections and revisions
        </h1>
        <p className="mt-4 text-theme-muted leading-relaxed">
          Roman Letters is a working corpus, not a closed edition. Source texts,
          OCR, translations, people, dates, and places can all be improved when
          better evidence is available.
        </p>
      </header>

      <section className="border border-theme bg-theme-surface p-5">
        <h2
          className="text-xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Submit a correction
        </h2>
        <p className="mt-3 text-sm text-theme-muted leading-relaxed">
          The fastest path is to open a GitHub issue with the letter URL, the
          proposed change, and a source citation or scan link. Individual letter
          pages include a prefilled correction link.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {issueLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-2 border border-theme bg-theme-bg text-sm text-theme-muted hover:text-theme-accent hover:border-[var(--color-accent)] transition-colors"
            >
              {link.label}
            </a>
          ))}
        </div>
      </section>

      <section className="mt-10">
        <h2
          className="text-xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Published revision log
        </h2>
        {revisions.length > 0 ? (
          <ol className="mt-4 space-y-4">
            {revisions.map((revision) => (
              <li key={revision.version} className="border-l-2 border-theme pl-4">
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <span className="text-sm font-medium text-theme-text">
                    {revision.date}
                  </span>
                  <span className="text-xs text-theme-muted">
                    {revision.version}
                  </span>
                </div>
                <p className="mt-1 text-sm text-theme-text leading-relaxed">
                  {revision.summary}
                </p>
                <p className="mt-1 text-xs text-theme-muted">
                  Fields: {revision.fields}. Source: {revision.source}
                </p>
              </li>
            ))}
          </ol>
        ) : (
          <p className="mt-4 text-theme-muted">
            No post-publication corrections have been published yet.
          </p>
        )}
      </section>

      <section className="mt-10 border-t border-theme pt-6">
        <Link href="/about#methodology" className="text-sm text-theme-accent hover:underline">
          Read the methodology notes &rarr;
        </Link>
      </section>
    </div>
  );
}

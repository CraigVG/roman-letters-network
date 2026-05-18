import type { LetterFull, CollectionInfo } from '@/lib/letters';
import { getTextProvenance } from '@/lib/provenance';

interface TextProvenanceProps {
  letter: LetterFull;
  collection?: CollectionInfo;
}

export function TextProvenance({ letter, collection }: TextProvenanceProps) {
  const provenance = getTextProvenance(letter, collection);
  const letterPath = `/letters/${letter.collection}/${letter.letter_number}/`;

  const rows = [
    ['Translation', provenance.translationLabel],
    ['Source type', provenance.sourceType],
    ['Original text', provenance.originalStatus],
    ['Review status', provenance.reviewStatus],
  ];

  return (
    <aside
      className="mb-8 border border-theme bg-theme-surface p-4 sm:p-5 text-sm"
      aria-labelledby="text-provenance-heading"
    >
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div>
          <h2
            id="text-provenance-heading"
            className="text-base tracking-tight text-theme-text"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Text provenance
          </h2>
          <p className="mt-1 text-theme-muted leading-relaxed">
            This project treats the text as improvable: sources, OCR, translations,
            and metadata can all be corrected with evidence.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <a
            href={`${letterPath}?view=original`}
            className="px-3 py-2 border border-theme bg-theme-bg text-theme-muted hover:text-theme-accent hover:border-[var(--color-accent)] transition-colors"
          >
            Original view
          </a>
          <a
            href={provenance.issueUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-2 border border-[var(--color-accent)] text-theme-accent hover:bg-theme-bg transition-colors"
          >
            Suggest correction
          </a>
        </div>
      </div>

      <dl className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt className="text-xs uppercase tracking-[0.12em] text-theme-muted">
              {label}
            </dt>
            <dd className="mt-1 text-theme-text leading-relaxed">{value}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-4 flex flex-wrap gap-3 text-sm">
        {provenance.primarySourceUrl && (
          <a
            href={provenance.primarySourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-theme-accent hover:underline"
          >
            View source
          </a>
        )}
        <span className="text-theme-muted">
          Source label: {provenance.sourceLabel}
        </span>
      </div>
    </aside>
  );
}

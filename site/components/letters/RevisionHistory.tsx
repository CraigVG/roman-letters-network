import type { LetterRevision } from '@/lib/letter-revisions';

interface RevisionHistoryProps {
  revisions: LetterRevision[];
}

export function RevisionHistory({ revisions }: RevisionHistoryProps) {
  return (
    <section className="mt-12 border-t border-theme pt-8">
      <h2
        className="text-lg sm:text-xl tracking-tight"
        style={{ fontFamily: 'var(--font-serif)' }}
      >
        Revision history
      </h2>
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
    </section>
  );
}

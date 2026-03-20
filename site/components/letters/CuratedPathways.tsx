'use client';

interface Pathway {
  slug: string;
  title: string;
  description: string;
  filters: Record<string, any>;
  count: number;
}

interface Props {
  pathways: Pathway[];
  onPathwayClick: (filters: Record<string, any>) => void;
}

export default function CuratedPathways({ pathways, onPathwayClick }: Props) {
  return (
    <section className="space-y-3">
      <h3
        className="text-xs font-semibold uppercase tracking-widest text-theme-muted"
        style={{ fontVariant: 'small-caps', fontFamily: 'var(--font-sans)' }}
      >
        Explore by theme
      </h3>

      <div
        className="flex gap-3 overflow-x-auto pb-2"
        style={{
          scrollSnapType: 'x mandatory',
          scrollbarWidth: 'none',
          WebkitOverflowScrolling: 'touch',
        }}
      >
        <style>{`
          .curated-scroll::-webkit-scrollbar { display: none; }
        `}</style>

        {pathways.map((pathway) => (
          <button
            key={pathway.slug}
            onClick={() => onPathwayClick(pathway.filters)}
            className="curated-scroll group flex w-[200px] min-w-[200px] cursor-pointer flex-col justify-between rounded-lg border border-theme bg-theme-surface p-4 text-left transition-colors hover:border-[var(--color-accent)]"
            style={{
              scrollSnapAlign: 'start',
              height: '160px',
            }}
          >
            <div className="space-y-1.5">
              <h4
                className="text-sm font-bold leading-tight text-theme-text"
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                {pathway.title}
              </h4>
              <p className="line-clamp-3 text-xs leading-relaxed text-theme-muted">
                {pathway.description}
              </p>
            </div>

            <span className="text-xs font-medium text-theme-accent">
              {pathway.count} letters
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}

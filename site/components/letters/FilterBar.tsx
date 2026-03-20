'use client';

import { useCallback } from 'react';
import { Badge } from '@/components/ui/Badge';

interface TopicInfo {
  slug: string;
  label: string;
  count: number;
}

interface CollectionInfo {
  slug: string;
  name: string;
  count: number;
  dateRange?: string;
}

interface Props {
  topics: TopicInfo[];
  collections: CollectionInfo[];
  selectedTopics: string[];
  onTopicsChange: (topics: string[] | ((old: string[]) => string[])) => void;
  selectedCollection: string | null;
  onCollectionChange: (collection: string | null) => void;
  from: number | null;
  to: number | null;
  onFromChange: (from: number | null) => void;
  onToChange: (to: number | null) => void;
  firstEnglish: boolean | null;
  onFirstEnglishChange: (v: boolean | null) => void;
  hasActiveFilters: boolean;
  onClearAll: () => void;
}

const CENTURIES = [
  { label: '1st-2nd c.', from: 50, to: 199 },
  { label: '3rd c.', from: 200, to: 299 },
  { label: '4th c.', from: 300, to: 399 },
  { label: '5th c.', from: 400, to: 499 },
  { label: '6th c.', from: 500, to: 599 },
  { label: '7th c.', from: 600, to: 699 },
  { label: '8th c.+', from: 700, to: 899 },
];

export function FilterBar({
  topics,
  collections,
  selectedTopics,
  onTopicsChange,
  selectedCollection,
  onCollectionChange,
  from,
  to,
  onFromChange,
  onToChange,
  firstEnglish,
  onFirstEnglishChange,
  hasActiveFilters,
  onClearAll,
}: Props) {
  const toggleTopic = useCallback(
    (slug: string) => {
      onTopicsChange((prev: string[]) =>
        prev.includes(slug) ? prev.filter((t) => t !== slug) : [...prev, slug],
      );
    },
    [onTopicsChange],
  );

  const isCenturyActive = (c: { from: number; to: number }) =>
    from === c.from && to === c.to;

  const toggleCentury = useCallback(
    (c: { from: number; to: number }) => {
      if (isCenturyActive(c)) {
        onFromChange(null);
        onToChange(null);
      } else {
        onFromChange(c.from);
        onToChange(c.to);
      }
    },
    [from, to, onFromChange, onToChange],
  );

  return (
    <div className="space-y-4">
      {/* Topic pills */}
      <div>
        <div
          className="flex gap-1.5 overflow-x-auto pb-1"
          style={{ scrollbarWidth: 'none' }}
        >
          {topics.map((topic) => {
            const isActive = selectedTopics.includes(topic.slug);
            return (
              <button
                key={topic.slug}
                onClick={() => toggleTopic(topic.slug)}
                className={`
                  inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium
                  whitespace-nowrap transition-all cursor-pointer border
                  ${
                    isActive
                      ? 'border-[var(--color-accent)] ring-1 ring-[var(--color-accent)]'
                      : 'border-transparent'
                  }
                `}
              >
                <Badge topic={topic.slug} />
                <span className="text-theme-muted text-[10px] tabular-nums">
                  {topic.count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Second row: Collection, Century, First English */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Collection dropdown */}
        <select
          value={selectedCollection ?? ''}
          onChange={(e) => onCollectionChange(e.target.value || null)}
          className="text-sm rounded-md border border-theme bg-theme-surface text-theme-text
            px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]
            cursor-pointer max-w-[200px]"
          aria-label="Filter by collection"
        >
          <option value="">All collections</option>
          {collections.map((c) => (
            <option key={c.slug} value={c.slug}>
              {c.name} ({c.count})
            </option>
          ))}
        </select>

        {/* Century pills */}
        <div className="flex gap-1">
          {CENTURIES.map((c) => (
            <button
              key={c.label}
              onClick={() => toggleCentury(c)}
              className={`
                px-2 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer border
                ${
                  isCenturyActive(c)
                    ? 'bg-[var(--color-accent)] text-white border-[var(--color-accent)]'
                    : 'bg-theme-surface text-theme-muted border-theme hover:text-theme-text hover:border-[var(--color-accent)]'
                }
              `}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* First English toggle */}
        <button
          onClick={() => onFirstEnglishChange(firstEnglish ? null : true)}
          className={`
            inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium
            transition-colors cursor-pointer border
            ${
              firstEnglish
                ? 'bg-[var(--color-accent)] text-white border-[var(--color-accent)]'
                : 'bg-theme-surface text-theme-muted border-theme hover:text-theme-text hover:border-[var(--color-accent)]'
            }
          `}
        >
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
          </svg>
          First English translations
        </button>
      </div>

      {/* Active filter chips */}
      {hasActiveFilters && (
        <div className="flex flex-wrap items-center gap-2">
          {selectedTopics.map((slug) => (
            <span
              key={slug}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs
                bg-theme-surface border border-theme text-theme-text"
            >
              {slug.replace(/_/g, ' ')}
              <button
                onClick={() => toggleTopic(slug)}
                className="text-theme-muted hover:text-theme-text"
                aria-label={`Remove ${slug} filter`}
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          ))}
          {selectedCollection && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs
              bg-theme-surface border border-theme text-theme-text">
              {selectedCollection.replace(/_/g, ' ')}
              <button
                onClick={() => onCollectionChange(null)}
                className="text-theme-muted hover:text-theme-text"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          )}
          {from != null && to != null && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs
              bg-theme-surface border border-theme text-theme-text">
              {from}-{to} AD
              <button
                onClick={() => { onFromChange(null); onToChange(null); }}
                className="text-theme-muted hover:text-theme-text"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          )}
          {firstEnglish && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs
              bg-theme-surface border border-theme text-theme-text">
              First English
              <button
                onClick={() => onFirstEnglishChange(null)}
                className="text-theme-muted hover:text-theme-text"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          )}
          <button
            onClick={onClearAll}
            className="text-xs text-theme-accent hover:underline"
          >
            Clear all
          </button>
        </div>
      )}
    </div>
  );
}

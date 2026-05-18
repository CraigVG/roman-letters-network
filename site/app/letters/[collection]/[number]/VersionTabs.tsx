'use client';

import { useEffect, useState } from 'react';
import { LetterText } from '@/components/letters/LetterText';

type TabKey = 'modern' | 'english' | 'latin';

interface VersionTabsProps {
  modernEnglish: string | null;
  english: string | null;
  latin: string | null;
  sourceUrl?: string | null;
}

const tabs: { key: TabKey; label: string }[] = [
  { key: 'modern', label: 'Modern English' },
  { key: 'english', label: '19th-Century Translation' },
  { key: 'latin', label: 'Latin / Greek Original' },
];

export function VersionTabs({ modernEnglish, english, latin, sourceUrl }: VersionTabsProps) {
  // Find available tabs. Keep the original-language tab visible even when it
  // needs an explicit missing-text state.
  const availableTabs = tabs.filter((t) => {
    if (t.key === 'modern') return !!modernEnglish;
    if (t.key === 'english') return !!english;
    if (t.key === 'latin') return true;
    return false;
  });

  const [active, setActive] = useState<TabKey>(
    availableTabs[0]?.key ?? 'modern',
  );

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const view = params.get('view');
    if (view === 'original' || params.get('scholarly') === 'true') {
      setActive('latin');
    } else if (view === 'english' && english) {
      setActive('english');
    } else if (view === 'modern' && modernEnglish) {
      setActive('modern');
    }
  }, [english, modernEnglish]);

  if (availableTabs.length === 0) {
    return (
      <div className="py-8 text-center text-theme-muted">
        No text available for this letter yet.
      </div>
    );
  }

  const content: Record<TabKey, string | null> = {
    modern: modernEnglish,
    english,
    latin,
  };

  const activeText = content[active];

  return (
    <div>
      {/* Tab bar - only show if more than one version is available */}
      {availableTabs.length > 1 && (
        <div className="flex gap-1 border-b border-theme mb-6 overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0 scrollbar-hide">
          {availableTabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => {
                setActive(tab.key);
                const url = new URL(window.location.href);
                if (tab.key === 'latin') {
                  url.searchParams.set('view', 'original');
                } else if (tab.key === 'english') {
                  url.searchParams.set('view', 'english');
                  url.searchParams.delete('scholarly');
                } else {
                  url.searchParams.delete('view');
                  url.searchParams.delete('scholarly');
                }
                window.history.replaceState(null, '', url.toString());
              }}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px whitespace-nowrap shrink-0 ${
                active === tab.key
                  ? 'border-[var(--color-accent)] text-theme-accent'
                  : 'border-transparent text-theme-muted hover:text-theme-text'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      {activeText ? (
        <LetterText text={activeText} />
      ) : active === 'latin' ? (
        <div className="py-8 border border-theme bg-theme-surface px-4 text-theme-muted">
          <p className="text-theme-text font-medium">
            Original text not yet available in this corpus.
          </p>
          <p className="mt-2 text-sm leading-relaxed">
            This letter still needs a Latin or Greek source-text backfill. The
            source link, when available, is preserved so the text can be checked
            and added later.
          </p>
          {sourceUrl && (
            <a
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-block text-sm text-theme-accent hover:underline"
            >
              View source
            </a>
          )}
        </div>
      ) : (
        <div className="py-8 text-center text-theme-muted">
          No text available for this version.
        </div>
      )}

      {/* Attribution note for the translation */}
      {active === 'modern' && (
        <p className="mt-6 text-xs text-theme-muted">
          Modern English rendering for readability. Use the provenance panel,
          19th-century translation, and original Latin/Greek tab for source checks.
        </p>
      )}
    </div>
  );
}

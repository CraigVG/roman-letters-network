'use client';

import { useState } from 'react';
import { LetterText } from '@/components/letters/LetterText';

type TabKey = 'modern' | 'english' | 'latin';

interface VersionTabsProps {
  modernEnglish: string | null;
  english: string | null;
  latin: string | null;
}

const tabs: { key: TabKey; label: string }[] = [
  { key: 'modern', label: 'Modern English' },
  { key: 'english', label: '19th-Century Translation' },
  { key: 'latin', label: 'Latin / Greek Original' },
];

export function VersionTabs({ modernEnglish, english, latin }: VersionTabsProps) {
  // Find the first available tab
  const availableTabs = tabs.filter((t) => {
    if (t.key === 'modern') return !!modernEnglish;
    if (t.key === 'english') return !!english;
    if (t.key === 'latin') return !!latin;
    return false;
  });

  const [active, setActive] = useState<TabKey>(
    availableTabs[0]?.key ?? 'modern',
  );

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
              onClick={() => setActive(tab.key)}
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
      ) : (
        <div className="py-8 text-center text-theme-muted">
          No text available for this version.
        </div>
      )}

      {/* Attribution note for the translation */}
      {active === 'modern' && (
        <p className="mt-6 text-xs text-theme-muted">
          Modern English rendering for readability. See the 19th-century translation
          or original Latin/Greek for scholarly use.
        </p>
      )}
    </div>
  );
}

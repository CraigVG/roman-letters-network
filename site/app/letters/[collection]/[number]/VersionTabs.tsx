'use client';

import { useState, useEffect } from 'react';
import { LetterText } from '@/components/letters/LetterText';
import { useScholarlyMode } from '@/components/layout/ScholarlyModeContext';

type TabKey = 'modern' | 'english' | 'latin';

interface VersionTabsProps {
  modernEnglish: string | null;
  english: string | null;
  latin: string | null;
  translationSource: string | null;
}

const SCHOLARLY_SOURCES = new Set([
  'existing_newadvent',
  'existing_tertullian',
  'existing_fordham',
  'existing_celt',
  'existing_attalus',
  'existing_livius',
  'existing_rogerpearse',
]);

export function VersionTabs({ modernEnglish, english, latin, translationSource }: VersionTabsProps) {
  const { scholarlyMode } = useScholarlyMode();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // In scholarly mode, hide AI-generated modern English
  // Keep it if the source is a known scholarly translation
  const isScholarlyTranslation = translationSource != null && SCHOLARLY_SOURCES.has(translationSource);
  const hideModern = mounted && scholarlyMode && !isScholarlyTranslation;

  const tabs: { key: TabKey; label: string }[] = [
    { key: 'modern', label: hideModern ? 'Modern English' : (isScholarlyTranslation ? 'English Translation' : 'Modern English') },
    { key: 'english', label: '19th-Century Translation' },
    { key: 'latin', label: 'Latin / Greek Original' },
  ];

  const availableTabs = tabs.filter((t) => {
    if (t.key === 'modern') return !hideModern && !!modernEnglish;
    if (t.key === 'english') return !!english;
    if (t.key === 'latin') return !!latin;
    return false;
  });

  const [active, setActive] = useState<TabKey>(
    availableTabs[0]?.key ?? 'latin',
  );

  // Reset active tab when scholarly mode changes
  useEffect(() => {
    if (hideModern && active === 'modern') {
      const fallback = english ? 'english' : latin ? 'latin' : 'modern';
      setActive(fallback);
    }
  }, [hideModern, active, english, latin]);

  if (availableTabs.length === 0) {
    return (
      <div className="py-8 text-center text-theme-muted">
        {scholarlyMode
          ? 'No scholarly translation available for this letter. The original Latin/Greek text may be available below.'
          : 'No text available for this letter yet.'}
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
      {/* Scholarly mode banner */}
      {mounted && scholarlyMode && hideModern && (
        <div className="mb-4 px-3 py-2 rounded-md text-xs bg-theme-surface border border-theme text-theme-muted">
          Scholarly mode is on. AI-assisted translations are hidden. Showing only pre-existing scholarly translations and original texts.
        </div>
      )}

      {/* Tab bar */}
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

      {/* Attribution note */}
      {active === 'modern' && !isScholarlyTranslation && (
        <p className="mt-6 text-xs text-theme-muted">
          Modern English rendering for readability. See the 19th-century translation
          or original Latin/Greek for scholarly use.
        </p>
      )}
    </div>
  );
}

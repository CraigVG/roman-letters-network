'use client';

import { useState, useEffect } from 'react';
import { LetterText } from '@/components/letters/LetterText';
import { useScholarlyMode } from '@/components/layout/ScholarlyModeContext';

type TranslationKey = 'modern' | 'english';

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

  // Translation tabs (Latin/Greek is no longer a tab — it's always shown below)
  const tabs: { key: TranslationKey; label: string }[] = [
    { key: 'modern', label: isScholarlyTranslation ? 'English Translation' : 'Modern English' },
    { key: 'english', label: '19th-Century Translation' },
  ];

  const availableTabs = tabs.filter((t) => {
    if (t.key === 'modern') return !hideModern && !!modernEnglish;
    if (t.key === 'english') return !!english;
    return false;
  });

  const hasTranslation = availableTabs.length > 0;

  const [active, setActive] = useState<TranslationKey>(
    availableTabs[0]?.key ?? 'modern',
  );

  // Reset active tab when scholarly mode changes
  useEffect(() => {
    if (hideModern && active === 'modern') {
      const fallback = english ? 'english' : 'modern';
      setActive(fallback);
    }
  }, [hideModern, active, english]);

  // If no translation and no Latin, show empty state
  if (!hasTranslation && !latin) {
    return (
      <div className="py-8 text-center text-theme-muted">
        {scholarlyMode
          ? 'No scholarly translation available for this letter.'
          : 'No text available for this letter yet.'}
      </div>
    );
  }

  // If only Latin exists (no translations available), show it as primary content
  if (!hasTranslation && latin) {
    return (
      <div>
        {mounted && scholarlyMode && hideModern && (
          <div className="mb-4 px-3 py-2 rounded-md text-xs bg-theme-surface border border-theme text-theme-muted">
            Scholarly mode is on. AI-assisted translations are hidden. Showing only pre-existing scholarly translations and original texts.
          </div>
        )}
        <div className="italic" style={{ fontFamily: 'var(--font-serif)' }}>
          <LetterText text={latin} />
        </div>
      </div>
    );
  }

  const content: Record<TranslationKey, string | null> = {
    modern: modernEnglish,
    english,
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

      {/* Translation tab bar */}
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

      {/* Translation content */}
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

      {/* Latin/Greek original — always visible below translation */}
      {latin && (
        <details open className="group/orig mt-8 border-t border-theme pt-6">
          <summary className="cursor-pointer text-sm font-medium text-theme-muted hover:text-theme-text select-none list-none flex items-center gap-2 [&::-webkit-details-marker]:hidden">
            <svg
              className="w-3 h-3 transition-transform group-open/orig:rotate-90"
              viewBox="0 0 12 12"
              fill="currentColor"
            >
              <path d="M4 2l5 4-5 4V2z" />
            </svg>
            Latin / Greek Original
          </summary>
          <div className="mt-4 italic" style={{ fontFamily: 'var(--font-serif)' }}>
            <LetterText text={latin} />
          </div>
        </details>
      )}
    </div>
  );
}

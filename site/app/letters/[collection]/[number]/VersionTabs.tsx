'use client';

import { useEffect, useState } from 'react';
import { LetterText } from '@/components/letters/LetterText';
import { useScholarlyMode } from '@/components/layout/ScholarlyModeContext';
import { SCHOLARLY_SOURCES } from '@/lib/scholarlySources';

type TranslationKey = 'modern' | 'english';

interface VersionTabsProps {
  modernEnglish: string | null;
  english: string | null;
  latin: string | null;
  translationSource: string | null;
  sourceUrl?: string | null;
}

const SOURCE_LABELS: Record<string, string> = {
  existing: 'Public-domain scholarly translation',
  existing_newadvent: 'New Advent (NPNF / ANF series)',
  existing_tertullian: 'Tertullian Project',
  existing_fordham: 'Fordham Medieval Sourcebook',
  existing_celt: 'CELT (Corpus of Electronic Texts)',
  existing_attalus: 'Attalus.org',
  existing_livius: 'Livius.org',
  existing_rogerpearse: 'Roger Pearse (additional translations)',
  existing_haines: 'Haines (public-domain edition)',
  gutenberg_winstedt: 'Project Gutenberg / Winstedt',
  topostext_shuckburgh_repair_v1: 'ToposText / Shuckburgh',
  'Gummere (Loeb Classical Library, 1917-25)': 'Gummere (Loeb Classical Library, 1917-25)',
  existing_kalvesmaki_evagrius_2014: 'Kalvesmaki 2014 (CC BY 4.0)',
};

function OriginalTextBlock({
  latin,
  sourceUrl,
}: {
  latin: string | null;
  sourceUrl?: string | null;
}) {
  if (latin) {
    return (
      <div className="mt-4 italic" style={{ fontFamily: 'var(--font-serif)' }}>
        <LetterText text={latin} />
      </div>
    );
  }

  return (
    <div className="mt-4 border border-theme bg-theme-surface px-4 py-5 text-theme-muted">
      <p className="font-medium text-theme-text">
        Original text not yet available in this corpus.
      </p>
      <p className="mt-2 text-sm leading-relaxed">
        This letter still needs a Latin or Greek source-text backfill. The source
        link, when available, is preserved so the text can be checked and added
        later.
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
  );
}

export function VersionTabs({
  modernEnglish,
  english,
  latin,
  translationSource,
  sourceUrl,
}: VersionTabsProps) {
  const { scholarlyMode } = useScholarlyMode();
  const [mounted, setMounted] = useState(false);
  const [showOriginalFirst, setShowOriginalFirst] = useState(false);

  useEffect(() => {
    setMounted(true);
    const params = new URLSearchParams(window.location.search);
    setShowOriginalFirst(params.get('view') === 'original');
  }, []);

  const isScholarlyTranslation =
    translationSource != null && SCHOLARLY_SOURCES.has(translationSource);
  const hideModern = mounted && scholarlyMode && !isScholarlyTranslation;

  const tabs: { key: TranslationKey; label: string }[] = [
    { key: 'modern', label: isScholarlyTranslation ? 'English Translation' : 'Modern English' },
    { key: 'english', label: isScholarlyTranslation ? 'Published English' : '19th-Century Translation' },
  ];

  const availableTabs = tabs.filter((tab) => {
    if (tab.key === 'modern') return !hideModern && !!modernEnglish;
    if (tab.key === 'english') return !!english;
    return false;
  });

  const [active, setActive] = useState<TranslationKey>(
    availableTabs[0]?.key ?? 'modern',
  );

  useEffect(() => {
    if (hideModern && active === 'modern') {
      const fallback = english ? 'english' : 'modern';
      setActive(fallback);
    }
  }, [hideModern, active, english]);

  const clearOriginalView = () => {
    setShowOriginalFirst(false);
    const url = new URL(window.location.href);
    if (url.searchParams.has('view')) {
      url.searchParams.delete('view');
      window.history.replaceState(null, '', url.toString());
    }
  };

  const hasTranslation = availableTabs.length > 0;
  const content: Record<TranslationKey, string | null> = {
    modern: modernEnglish,
    english,
  };
  const activeText = content[active];

  return (
    <div>
      {mounted && scholarlyMode && hideModern && (
        <div className="mb-4 px-3 py-2 rounded-md text-xs bg-theme-surface border border-theme text-theme-muted">
          Scholarly mode is on. AI-assisted translations are hidden. Showing only
          pre-existing scholarly translations and original texts.
        </div>
      )}

      {showOriginalFirst && (
        <section className="mb-8">
          <h2
            className="text-lg tracking-tight"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Latin / Greek Original
          </h2>
          <OriginalTextBlock latin={latin} sourceUrl={sourceUrl} />
        </section>
      )}

      {hasTranslation && availableTabs.length > 1 && (
        <div className="flex gap-1 border-b border-theme mb-6 overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0 scrollbar-hide">
          {availableTabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => {
                setActive(tab.key);
                clearOriginalView();
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

      {hasTranslation && activeText ? (
        <LetterText text={activeText} />
      ) : !latin && !showOriginalFirst ? (
        <div className="py-8 text-center text-theme-muted">
          {scholarlyMode
            ? 'No scholarly translation available for this letter.'
            : 'No translation available for this letter yet.'}
        </div>
      ) : null}

      {hasTranslation && active === 'modern' && activeText && (
        isScholarlyTranslation ? (
          <div className="mt-6 flex items-start gap-2 px-3 py-2.5 rounded-md bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/50">
            <svg className="w-4 h-4 mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
            </svg>
            <p className="text-xs text-emerald-800 dark:text-emerald-300">
              <strong className="font-semibold">Human translation</strong>
              {translationSource && SOURCE_LABELS[translationSource] && (
                <> - {SOURCE_LABELS[translationSource]}</>
              )}
            </p>
          </div>
        ) : (
          <div className="mt-6 flex items-start gap-2 px-3 py-2.5 rounded-md bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50">
            <svg className="w-4 h-4 mt-0.5 shrink-0 text-amber-600 dark:text-amber-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
            <p className="text-xs text-amber-800 dark:text-amber-300">
              <strong className="font-semibold">AI-assisted translation</strong> - This translation was produced with AI assistance and has not been peer-reviewed. See the 19th-century translation or original Latin/Greek below for scholarly use.
            </p>
          </div>
        )
      )}

      {!showOriginalFirst && (
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
          <OriginalTextBlock latin={latin} sourceUrl={sourceUrl} />
        </details>
      )}
    </div>
  );
}

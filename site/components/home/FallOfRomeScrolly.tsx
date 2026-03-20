'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import type { Chapter } from './FallOfRomeStory';

/* ------------------------------------------------------------------ */
/*  Decorative diamond divider                                         */
/* ------------------------------------------------------------------ */

function Diamond() {
  return (
    <div className="flex items-center gap-3 max-w-[6rem] mx-auto my-8 sm:my-10">
      <span
        className="h-px flex-1"
        style={{ backgroundColor: 'var(--color-accent)', opacity: 0.3 }}
      />
      <span
        className="text-theme-accent text-[10px] leading-none"
        style={{ fontFamily: 'var(--font-serif)' }}
      >
        &#9670;
      </span>
      <span
        className="h-px flex-1"
        style={{ backgroundColor: 'var(--color-accent)', opacity: 0.3 }}
      />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Single chapter card                                                */
/* ------------------------------------------------------------------ */

function ChapterCard({ chapter, isActive }: { chapter: Chapter; isActive: boolean }) {
  return (
    <div
      className={`
        relative rounded-xl border transition-all duration-700 ease-out
        ${isActive ? 'opacity-100 translate-y-0' : 'opacity-40 translate-y-2'}
      `}
      style={{
        borderColor: isActive ? 'var(--color-accent)' : 'var(--color-border)',
        backgroundColor: chapter.bgTone,
      }}
    >
      {/* Chapter header */}
      <div className="px-6 pt-6 pb-0 sm:px-8 sm:pt-8">
        <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 mb-1">
          <span
            className="text-xs font-medium tracking-[0.15em] uppercase text-theme-accent"
            style={{ fontFamily: 'var(--font-sans)' }}
          >
            Chapter {chapter.id}
          </span>
          <span className="text-xs text-theme-muted tabular-nums">{chapter.dateRange}</span>
        </div>

        <h3
          className="text-xl sm:text-2xl tracking-tight leading-snug"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          {chapter.era}
        </h3>

        {/* Event badge */}
        {chapter.event && (
          <div className="mt-3 inline-flex items-center gap-2 text-xs text-theme-accent">
            <span
              className="inline-block w-1.5 h-1.5 rounded-full flex-shrink-0"
              style={{ backgroundColor: 'var(--color-accent)' }}
            />
            <span className="font-medium">{chapter.event}</span>
          </div>
        )}
      </div>

      {/* Narrative */}
      <div className="px-6 pt-4 sm:px-8">
        <p className="text-sm sm:text-[0.9375rem] text-theme-muted leading-relaxed max-w-prose">
          {chapter.narrative}
        </p>
      </div>

      {/* Quote card */}
      <div className="px-6 pt-5 pb-1 sm:px-8">
        <blockquote
          className="relative pl-4 border-l-2"
          style={{ borderColor: 'var(--color-accent)' }}
        >
          <p
            className="text-base sm:text-lg italic leading-relaxed text-theme-text"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            &ldquo;{chapter.quote}&rdquo;
          </p>
          <footer className="mt-2">
            <Link
              href={chapter.letterHref}
              className="text-xs text-theme-muted hover:text-theme-accent transition-colors"
            >
              - {chapter.attribution}
            </Link>
          </footer>
        </blockquote>
      </div>

      {/* Stat badge */}
      {chapter.stat && (
        <div className="px-6 pt-5 pb-6 sm:px-8 sm:pb-8">
          <div
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium text-theme-accent"
            style={{
              backgroundColor: 'color-mix(in srgb, var(--color-accent) 8%, transparent)',
              border: '1px solid color-mix(in srgb, var(--color-accent) 20%, transparent)',
            }}
          >
            <svg
              className="w-3 h-3 flex-shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            {chapter.stat}
          </div>
        </div>
      )}

      {/* CTA for final chapter */}
      {chapter.id === 7 && (
        <div className="px-6 pb-6 sm:px-8 sm:pb-8">
          <Link
            href="/letters"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium
              text-white transition-colors hover:opacity-90"
            style={{ backgroundColor: 'var(--color-accent)' }}
          >
            Explore the letters
            <span aria-hidden="true">&rarr;</span>
          </Link>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Scrollytelling client component                                    */
/* ------------------------------------------------------------------ */

export function FallOfRomeScrolly({ chapters }: { chapters: Chapter[] }) {
  const [activeId, setActiveId] = useState(1);
  const chapterRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        let bestEntry: IntersectionObserverEntry | null = null;
        let bestRatio = 0;

        for (const entry of entries) {
          if (entry.intersectionRatio > bestRatio) {
            bestRatio = entry.intersectionRatio;
            bestEntry = entry;
          }
        }

        if (bestEntry && bestEntry.intersectionRatio > 0.15) {
          const id = Number(bestEntry.target.getAttribute('data-chapter'));
          if (id) setActiveId(id);
        }
      },
      {
        rootMargin: '-20% 0px -20% 0px',
        threshold: [0, 0.15, 0.3, 0.5, 0.7, 1],
      }
    );

    chapterRefs.current.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  const setChapterRef = (id: number) => (el: HTMLDivElement | null) => {
    if (el) {
      chapterRefs.current.set(id, el);
    } else {
      chapterRefs.current.delete(id);
    }
  };

  return (
    <section>
      {/* Section header */}
      <div className="max-w-3xl mx-auto px-4 sm:px-6 pt-16 sm:pt-24 pb-2 text-center">
        <p className="text-xs font-medium tracking-[0.2em] uppercase text-theme-accent mb-4">
          A story told in letters
        </p>
        <h2
          className="text-3xl sm:text-4xl tracking-tight leading-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          The Fall of Rome in Letters
        </h2>
        <p className="mt-4 text-base sm:text-lg text-theme-muted max-w-xl mx-auto leading-relaxed">
          How the Western Roman provinces lost their voice, and how the East carried on.
          Told through the letters that stopped being written.
        </p>
        <Diamond />
      </div>

      {/* Desktop: sticky side-nav + scrolling chapters */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 pb-16 sm:pb-24">
        <div className="lg:grid lg:grid-cols-[180px_1fr] lg:gap-10">
          {/* Side progress nav */}
          <nav
            className="hidden lg:block"
            aria-label="Story chapters"
          >
            <div className="sticky top-28">
              <ol className="space-y-1">
                {chapters.map((ch) => (
                  <li key={ch.id}>
                    <button
                      onClick={() => {
                        const el = chapterRefs.current.get(ch.id);
                        el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                      }}
                      className={`
                        w-full text-left px-3 py-2 rounded-md text-xs transition-all duration-300
                        ${
                          activeId === ch.id
                            ? 'text-theme-accent font-medium bg-theme-surface'
                            : 'text-theme-muted hover:text-theme-text'
                        }
                      `}
                    >
                      <span className="tabular-nums mr-1.5">{ch.id}.</span>
                      {ch.era}
                    </button>
                  </li>
                ))}
              </ol>
            </div>
          </nav>

          {/* Chapters */}
          <div className="space-y-8 sm:space-y-10">
            {chapters.map((ch) => (
              <div
                key={ch.id}
                ref={setChapterRef(ch.id)}
                data-chapter={ch.id}
                style={{ contentVisibility: 'auto' }}
              >
                <ChapterCard chapter={ch} isActive={activeId === ch.id} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

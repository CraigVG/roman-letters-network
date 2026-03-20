'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Badge } from '@/components/ui/Badge';

interface FeaturedLetter {
  id: number;
  c: string;      // collection
  n: number;      // letter_number
  y?: number;     // year_approx
  s?: string;     // sender_name
  r?: string;     // recipient_name
  q?: string;     // quick_summary
  note?: string;  // interesting_note excerpt
  topics?: string[];
}

interface Props {
  featured: FeaturedLetter[];
}

export function LetterOfTheDay({ featured }: Props) {
  const [letter, setLetter] = useState<FeaturedLetter | null>(null);

  useEffect(() => {
    const dayIndex = Math.floor(Date.now() / 86400000) % featured.length;
    setLetter(featured[dayIndex]);
  }, [featured]);

  function handleSurprise() {
    const candidates = featured.filter((l) => l.id !== letter?.id);
    if (candidates.length === 0) return;
    const pick = candidates[Math.floor(Math.random() * candidates.length)];
    setLetter(pick);
  }

  // Skeleton placeholder before hydration
  if (!letter) {
    return (
      <div className="rounded-lg border border-theme bg-theme-surface p-5 animate-pulse"
           style={{ borderLeft: '4px solid var(--color-accent)' }}>
        <div className="flex items-center justify-between mb-4">
          <div className="h-4 w-32 rounded bg-current opacity-10" />
          <div className="h-4 w-20 rounded bg-current opacity-10" />
        </div>
        <div className="h-6 w-3/4 rounded bg-current opacity-10 mb-3" />
        <div className="space-y-2">
          <div className="h-4 w-full rounded bg-current opacity-10" />
          <div className="h-4 w-5/6 rounded bg-current opacity-10" />
        </div>
      </div>
    );
  }

  const heading = [
    letter.s,
    letter.r ? `to ${letter.r}` : null,
    letter.y ? `~${letter.y} AD` : null,
  ]
    .filter(Boolean)
    .join(', ');

  return (
    <div
      className="rounded-lg border border-theme bg-theme-surface p-5"
      style={{ borderLeft: '4px solid var(--color-accent)' }}
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-3">
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-theme-muted uppercase tracking-wide">
          <svg
            className="w-3.5 h-3.5"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="2" y="3" width="12" height="11" rx="1" />
            <path d="M2 6h12" />
            <path d="M5 3V1.5" />
            <path d="M11 3V1.5" />
          </svg>
          Letter of the Day
        </span>

        <button
          onClick={handleSurprise}
          className="inline-flex items-center gap-1 text-xs text-theme-muted hover:text-theme-accent transition-colors cursor-pointer"
        >
          <svg
            className="w-3.5 h-3.5"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M1 4h3.5a3.5 3.5 0 0 1 3.5 3.5v0A3.5 3.5 0 0 1 4.5 11H1" />
            <path d="M15 4h-3.5A3.5 3.5 0 0 0 8 7.5v0a3.5 3.5 0 0 0 3.5 3.5H15" />
            <path d="M3 2l-2 2 2 2" />
            <path d="M13 9l2 2-2 2" />
          </svg>
          Surprise me
        </button>
      </div>

      {/* Title */}
      <h3
        className="text-lg font-semibold text-theme-text mb-2"
        style={{ fontFamily: 'var(--font-serif)' }}
      >
        {heading}
      </h3>

      {/* Note / excerpt */}
      {letter.note && (
        <p
          className="text-sm text-theme-muted leading-relaxed mb-3"
          style={{ fontFamily: 'var(--font-sans)' }}
        >
          {letter.note}
        </p>
      )}

      {/* Topic badges */}
      {letter.topics && letter.topics.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {letter.topics.map((t) => (
            <Badge key={t} topic={t} />
          ))}
        </div>
      )}

      {/* Read link */}
      <Link
        href={`/letters/${letter.c}/${letter.n}`}
        className="inline-flex items-center gap-1 text-sm text-theme-accent hover:underline"
      >
        Read this letter
        <svg
          className="w-3.5 h-3.5"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3 8h10" />
          <path d="M9 4l4 4-4 4" />
        </svg>
      </Link>
    </div>
  );
}

import { Suspense } from 'react';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import { LetterBrowser } from '@/components/letters/LetterBrowser';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Browse Letters',
  description:
    'Browse over 7,000 surviving letters from the late Roman world (97-800 AD). Search by topic, collection, era, or discover the letter of the day. Includes 3,000+ first-ever English translations.',
};

export default function LettersBrowsePage() {
  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      <Breadcrumbs segments={[{ label: 'Letters' }]} />

      <h1
        className="text-3xl sm:text-4xl tracking-tight mt-4"
        style={{ fontFamily: 'var(--font-serif)' }}
      >
        Browse Letters
      </h1>
      <p className="mt-2 text-theme-muted max-w-2xl">
        7,049 letters from 54 collections spanning the late Roman world.
        Search by topic, collection, era, or discover something unexpected.
      </p>

      <div className="mt-8">
        <Suspense
          fallback={
            <div className="space-y-6">
              <div
                className="rounded-lg border border-theme bg-theme-surface p-5 animate-pulse"
                style={{ borderLeft: '4px solid var(--color-accent)' }}
              >
                <div className="h-4 w-32 rounded bg-current opacity-10 mb-4" />
                <div className="h-6 w-3/4 rounded bg-current opacity-10 mb-3" />
                <div className="space-y-2">
                  <div className="h-4 w-full rounded bg-current opacity-10" />
                  <div className="h-4 w-5/6 rounded bg-current opacity-10" />
                </div>
              </div>
              <div className="h-11 rounded-lg bg-theme-surface animate-pulse" />
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 py-3">
                  <div className="hidden sm:block h-6 w-24 rounded bg-theme-surface animate-pulse" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-64 rounded bg-theme-surface animate-pulse" />
                    <div className="h-3 w-96 rounded bg-theme-surface animate-pulse" />
                  </div>
                </div>
              ))}
            </div>
          }
        >
          <LetterBrowser />
        </Suspense>
      </div>
    </div>
  );
}

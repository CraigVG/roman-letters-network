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
        <Suspense fallback={null}>
          <LetterBrowser />
        </Suspense>
      </div>
    </div>
  );
}

import type { Metadata } from 'next';
import Link from 'next/link';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import { getAllPlaces } from '@/lib/places';

export const metadata: Metadata = {
  title: 'Places',
  description:
    'Browse locations across the late Roman Empire connected by surviving letters — from Rome and Constantinople to Gaul, Hispania, and beyond.',
};

export default function PlacesIndexPage() {
  const places = getAllPlaces();
  const withLetters = places.filter((p) => p.letter_count > 0);
  const totalLetters = withLetters.reduce((s, p) => s + p.letter_count, 0);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6">
      <Breadcrumbs segments={[{ label: 'Places' }]} />

      <header className="pt-8 pb-10">
        <h1
          className="text-3xl sm:text-4xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Places
        </h1>
        <p className="mt-3 text-theme-muted max-w-2xl leading-relaxed">
          {places.length} locations across the late Roman Empire linked to{' '}
          {totalLetters.toLocaleString()} letters in the corpus.
        </p>
      </header>

      <div className="pb-16">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-theme text-left text-theme-muted">
              <th className="pb-3 font-medium">Place</th>
              <th className="pb-3 font-medium hidden sm:table-cell">Region</th>
              <th className="pb-3 font-medium hidden md:table-cell">
                Notable Authors
              </th>
              <th className="pb-3 font-medium text-right">Letters</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-theme">
            {places.map((place) => (
              <tr key={place.name} className="group">
                <td className="py-3 pr-4">
                  {place.letter_count > 0 ? (
                    <Link
                      href={`/letters?origin=${encodeURIComponent(place.name)}`}
                      className="text-theme-text group-hover:text-theme-accent transition-colors font-medium"
                    >
                      {place.name}
                    </Link>
                  ) : (
                    <span className="text-theme-text font-medium">
                      {place.name}
                    </span>
                  )}
                  <span className="block text-xs text-theme-muted sm:hidden">
                    {place.region}
                  </span>
                </td>
                <td className="py-3 pr-4 text-theme-muted hidden sm:table-cell">
                  {place.region}
                </td>
                <td className="py-3 pr-4 text-theme-muted hidden md:table-cell">
                  {place.top_authors.length > 0
                    ? place.top_authors.join(', ')
                    : '\u2014'}
                </td>
                <td className="py-3 text-right tabular-nums">
                  {place.letter_count > 0 ? (
                    <span className="text-theme-accent font-medium">
                      {place.letter_count}
                    </span>
                  ) : (
                    <span className="text-theme-muted">\u2014</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

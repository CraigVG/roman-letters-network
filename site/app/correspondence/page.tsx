import type { Metadata } from 'next';
import Link from 'next/link';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import { getCorrespondencePairs } from '@/lib/correspondence';

export const metadata: Metadata = {
  title: 'Correspondence',
  description:
    'Browse correspondence threads between individuals in the Roman Letters corpus - letters exchanged between senators, bishops, and officials of the late Roman Empire.',
};

export default function CorrespondenceIndexPage() {
  const pairs = getCorrespondencePairs(3);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6">
      <Breadcrumbs segments={[{ label: 'Correspondence' }]} />

      <header className="pt-8 pb-10">
        <h1
          className="text-3xl sm:text-4xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Correspondence
        </h1>
        <p className="mt-3 text-theme-muted max-w-2xl leading-relaxed">
          {pairs.length} correspondence threads with 3 or more surviving
          letters, ranked by volume.
        </p>
      </header>

      <div className="pb-16">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-theme text-left text-xs text-theme-muted uppercase tracking-wide">
              <th className="pb-3 pr-4">Correspondents</th>
              <th className="pb-3 pr-4 text-right">Letters</th>
            </tr>
          </thead>
          <tbody>
            {pairs.map((pair) => (
              <tr
                key={`${pair.person1Slug}-${pair.person2Slug}`}
                className="border-b border-theme/50"
              >
                <td className="py-3 pr-4">
                  <Link
                    href={`/correspondence/${pair.person1Slug}/${pair.person2Slug}`}
                    className="text-theme-accent hover:underline"
                    style={{ fontFamily: 'var(--font-serif)' }}
                  >
                    {pair.person1Name} &amp; {pair.person2Name}
                  </Link>
                </td>
                <td className="py-3 pr-4 text-right tabular-nums text-theme-muted">
                  {pair.letterCount}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import type { Metadata } from 'next';
import Link from 'next/link';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import { getAllAuthors, toSlug } from '@/lib/authors';

export const metadata: Metadata = {
  title: 'Authors',
  description:
    'Browse all authors in the Roman Letters corpus - senators, bishops, and officials of the late Roman Empire (300-600 AD).',
};

export default function AuthorsIndexPage() {
  const authors = getAllAuthors();

  // Sort by total letters (sent + received) descending
  const sorted = [...authors].sort(
    (a, b) =>
      b.sent_count + b.received_count - (a.sent_count + a.received_count),
  );

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6">
      <Breadcrumbs segments={[{ label: 'Authors' }]} />

      <header className="pt-8 pb-10">
        <h1
          className="text-3xl sm:text-4xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Authors
        </h1>
        <p className="mt-3 text-theme-muted max-w-2xl leading-relaxed">
          {sorted.length} individuals whose letters survive from the late Roman
          Empire, ranked by total correspondence.
        </p>
      </header>

      <div className="pb-16">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-theme text-left text-theme-muted">
              <th className="pb-3 font-medium">Name</th>
              <th className="pb-3 font-medium hidden sm:table-cell">Role</th>
              <th className="pb-3 font-medium hidden md:table-cell">Dates</th>
              <th className="pb-3 font-medium hidden md:table-cell">Location</th>
              <th className="pb-3 font-medium text-right">Letters</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-theme">
            {sorted.map((author) => {
              const total = author.sent_count + author.received_count;
              const dates =
                author.birth_year || author.death_year
                  ? `${author.birth_year ?? '?'}\u2013${author.death_year ?? '?'}`
                  : null;

              return (
                <tr key={author.id} className="group">
                  <td className="py-3 pr-4">
                    <Link
                      href={`/authors/${toSlug(author.name)}`}
                      className="text-theme-text group-hover:text-theme-accent transition-colors font-medium"
                    >
                      {author.name}
                    </Link>
                    {author.role && (
                      <span className="block text-xs text-theme-muted sm:hidden">
                        {author.role}
                      </span>
                    )}
                  </td>
                  <td className="py-3 pr-4 text-theme-muted hidden sm:table-cell">
                    {author.role ?? '\u2014'}
                  </td>
                  <td className="py-3 pr-4 text-theme-muted tabular-nums hidden md:table-cell">
                    {dates ?? '\u2014'}
                  </td>
                  <td className="py-3 pr-4 text-theme-muted hidden md:table-cell">
                    {author.location ?? '\u2014'}
                  </td>
                  <td className="py-3 text-right tabular-nums">
                    <span className="text-theme-accent font-medium">{total}</span>
                    <span className="text-theme-muted ml-1 text-xs">
                      ({author.sent_count}s / {author.received_count}r)
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

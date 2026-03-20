import Link from 'next/link';
import { FallOfRomeStory } from '@/components/home/FallOfRomeStory';

const stats = [
  { value: '7,049', label: 'Letters preserved' },
  { value: '54', label: 'Collections' },
  { value: '4,410', label: 'First-ever English translations' },
];

const collections = [
  {
    name: 'Augustine',
    count: 308,
    period: '386-430',
    century: '4th-5th c.',
    description: 'Bishop of Hippo\u2019s theological and pastoral correspondence',
  },
  {
    name: 'Gregory the Great',
    count: 854,
    period: '590-604',
    century: '6th-7th c.',
    description: 'Papal administration across a fragmenting Western empire',
  },
  {
    name: 'Symmachus',
    count: 900,
    period: '365-402',
    century: '4th-5th c.',
    description: 'The last great pagan senator\u2019s aristocratic network',
  },
  {
    name: 'Basil of Caesarea',
    count: 368,
    period: '357-378',
    century: '4th c.',
    description: 'Cappadocian Father navigating Arian controversy',
  },
];

export default function HomePage() {
  return (
    <div>
      {/* Fall of Rome scrollytelling - the hero */}
      <FallOfRomeStory />

      {/* Stats */}
      <section className="border-y border-theme">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-[var(--color-border)]">
            {stats.map((stat) => (
              <div key={stat.label} className="py-8 sm:py-12 sm:px-8 first:sm:pl-0 last:sm:pr-0">
                <div
                  className="text-4xl sm:text-5xl font-light tracking-tight text-theme-accent"
                  style={{ fontFamily: 'var(--font-serif)', fontVariantNumeric: 'oldstyle-nums' }}
                >
                  {stat.value}
                </div>
                <div className="mt-2 text-sm text-theme-muted tracking-wide">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Collections */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-24">
        <h2
          className="text-2xl sm:text-3xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Explore collections
        </h2>
        <p className="mt-3 text-theme-muted max-w-xl leading-relaxed">
          Each collection represents the surviving letters of a single author,
          preserved across centuries of manuscript transmission.
        </p>

        <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {collections.map((c) => (
            <Link
              key={c.name}
              href={`/letters?collection=${encodeURIComponent(c.name)}`}
              className="group block p-6 rounded-lg border border-theme bg-theme-surface
                hover:border-[var(--color-accent)] transition-all duration-200"
            >
              <div className="flex items-start justify-between gap-3">
                <h3
                  className="text-lg group-hover:text-theme-accent transition-colors"
                  style={{ fontFamily: 'var(--font-serif)' }}
                >
                  {c.name}
                </h3>
                <span
                  className="shrink-0 text-sm tabular-nums text-theme-accent font-light mt-0.5"
                  style={{ fontFamily: 'var(--font-serif)', fontVariantNumeric: 'oldstyle-nums' }}
                >
                  {c.period}
                </span>
              </div>
              <p className="mt-2 text-sm text-theme-muted leading-relaxed">
                {c.description}
              </p>
              <div className="mt-4 flex items-center justify-between">
                <span className="text-xs text-theme-accent font-medium tabular-nums">
                  {c.count} letters
                </span>
                <span className="text-xs text-theme-muted">{c.century}</span>
              </div>
            </Link>
          ))}
        </div>

        <div className="mt-10 text-center">
          <Link
            href="/letters"
            className="text-sm text-theme-muted hover:text-theme-accent transition-colors"
          >
            View all 54 collections &rarr;
          </Link>
        </div>
      </section>

      {/* Pull quote */}
      <section className="border-t border-theme">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-16 sm:py-24 text-center">
          <div className="flex justify-center mb-6">
            <span className="text-theme-accent text-2xl leading-none" style={{ fontFamily: 'var(--font-serif)' }}>&ldquo;</span>
          </div>
          <blockquote>
            <p
              className="text-xl sm:text-2xl text-theme-text italic leading-relaxed"
              style={{ fontFamily: 'var(--font-serif)' }}
            >
              The world is a great book, of which they who never stir from home
              read only a page.
            </p>
            <footer className="mt-6">
              <div className="flex items-center justify-center gap-3 mb-2">
                <span className="h-px w-8" style={{ backgroundColor: 'var(--color-accent)', opacity: 0.4 }} />
                <span className="text-theme-accent text-xs">&#9670;</span>
                <span className="h-px w-8" style={{ backgroundColor: 'var(--color-accent)', opacity: 0.4 }} />
              </div>
              <cite className="not-italic text-sm text-theme-muted">
                Augustine of Hippo, <span className="italic">Letter 28</span>
              </cite>
            </footer>
          </blockquote>
        </div>
      </section>
    </div>
  );
}

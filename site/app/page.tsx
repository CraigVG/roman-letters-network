import Link from 'next/link';
import { FallOfRomeStory } from '@/components/home/FallOfRomeStory';
import { HeroAnimation } from '@/components/home/HeroAnimation';
import { getDb } from '@/lib/db';

function getStats() {
  const db = getDb();
  const count = (sql: string) => (db.prepare(sql).get() as { c: number }).c;
  return {
    totalLetters: count("SELECT COUNT(*) as c FROM letters"),
    collections: count("SELECT COUNT(*) as c FROM collections WHERE letter_count > 0"),
    firstEnglish: count("SELECT COUNT(*) as c FROM letters WHERE modern_english IS NOT NULL AND (english_text IS NULL OR english_text = '') AND translation_source NOT IN ('existing_newadvent','existing_tertullian','existing_fordham','existing_celt','existing_attalus','existing_livius','existing_rogerpearse')"),
  };
}

function getTopCollections() {
  const db = getDb();
  return db.prepare(`
    SELECT slug, author_name, letter_count, date_range
    FROM collections
    WHERE letter_count > 0
    ORDER BY letter_count DESC
    LIMIT 4
  `).all() as { slug: string; author_name: string; letter_count: number; date_range: string }[];
}

const descriptionMap: Record<string, string> = {
  libanius: 'Last great pagan rhetorician of Antioch',
  symmachus: "The last pagan senator's aristocratic network",
  isidore_pelusium: "Egyptian monk's moral counsel from the desert",
  cassiodorus: 'Ostrogothic state correspondence',
};

export default function HomePage() {
  const stats = getStats();
  const topCollections = getTopCollections();

  const statsDisplay = [
    { value: stats.totalLetters.toLocaleString(), label: 'Letters preserved' },
    { value: String(stats.collections), label: 'Collections' },
    { value: stats.firstEnglish.toLocaleString(), label: 'First-ever English translations' },
  ];

  return (
    <div>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": "Roman Letters: 7,049 Letters from the Late Roman World",
            "description": "A comprehensive corpus of 7,049 surviving letters from the late Roman world (100-800 AD) with modern English translations, Latin/Greek originals, geographic coordinates, topic tags, and social network metadata. 3,068 letters translated to English for the first time.",
            "url": "https://romanletters.org",
            "identifier": "https://doi.org/10.5281/zenodo.19142059",
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "creator": {
              "@type": "Person",
              "name": "Craig Vander Galien",
              "url": "https://craigvandergalien.com"
            },
            "datePublished": "2026-03-20",
            "temporalCoverage": "100/800",
            "spatialCoverage": {
              "@type": "Place",
              "name": "Mediterranean Basin",
              "geo": {
                "@type": "GeoShape",
                "box": "20.0 -10.0 55.0 45.0"
              }
            },
            "distribution": {
              "@type": "DataDownload",
              "encodingFormat": "application/x-sqlite3",
              "contentUrl": "https://github.com/CraigVG/roman-letters-network/releases"
            },
            "keywords": ["late antiquity", "Roman Empire", "ancient letters", "epistolography", "network analysis", "digital humanities", "Latin", "Greek", "communication networks"]
          })
        }}
      />
      <HeroAnimation />

      <FallOfRomeStory />

      <section className="border-y border-theme">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-[var(--color-border)]">
            {statsDisplay.map((stat) => (
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
          {topCollections.map((c) => (
            <Link
              key={c.slug}
              href={`/letters/${c.slug}/`}
              className="group block p-6 rounded-lg border border-theme bg-theme-surface
                hover:border-[var(--color-accent)] transition-all duration-200"
            >
              <div className="flex items-start justify-between gap-3">
                <h3
                  className="text-lg group-hover:text-theme-accent transition-colors"
                  style={{ fontFamily: 'var(--font-serif)' }}
                >
                  {c.author_name}
                </h3>
                <span
                  className="shrink-0 text-sm tabular-nums text-theme-accent font-light mt-0.5"
                  style={{ fontFamily: 'var(--font-serif)', fontVariantNumeric: 'oldstyle-nums' }}
                >
                  {c.date_range}
                </span>
              </div>
              <p className="mt-2 text-sm text-theme-muted leading-relaxed">
                {descriptionMap[c.slug] || ''}
              </p>
              <div className="mt-4 flex items-center justify-between">
                <span className="text-xs text-theme-accent font-medium tabular-nums">
                  {c.letter_count} letters
                </span>
              </div>
            </Link>
          ))}
        </div>

        <div className="mt-10 text-center">
          <Link
            href="/letters"
            className="text-sm text-theme-muted hover:text-theme-accent transition-colors"
          >
            View all {stats.collections} collections &rarr;
          </Link>
        </div>
      </section>

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

import type { Metadata } from 'next';
import Link from 'next/link';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import { getDb } from '@/lib/db';

export const metadata: Metadata = {
  title: 'About',
  description:
    'About the Roman Letters project: mapping the communication networks of the late Roman Empire through surviving correspondence (97-800 AD).',
};

/* ------------------------------------------------------------------ */
/*  DB stats (computed at build time)                                  */
/* ------------------------------------------------------------------ */

function getProjectStats() {
  const db = getDb();
  const letters = db
    .prepare('SELECT COUNT(*) AS cnt FROM letters')
    .get() as { cnt: number };
  const authors = db
    .prepare('SELECT COUNT(*) AS cnt FROM authors')
    .get() as { cnt: number };
  const collections = db
    .prepare('SELECT COUNT(*) AS cnt FROM collections')
    .get() as { cnt: number };
  const firstEnglish = db
    .prepare(
      "SELECT COUNT(*) AS cnt FROM letters WHERE (english_text IS NULL OR english_text = '') AND modern_english IS NOT NULL AND modern_english != ''",
    )
    .get() as { cnt: number };
  const withDistance = db
    .prepare('SELECT COUNT(*) AS cnt FROM letters WHERE distance_km IS NOT NULL')
    .get() as { cnt: number };
  const withCarriers = db
    .prepare('SELECT COUNT(*) AS cnt FROM letters WHERE carrier_mentioned = 1')
    .get() as { cnt: number };
  const topicTagged = db
    .prepare(
      "SELECT COUNT(*) AS cnt FROM letters WHERE topics IS NOT NULL AND topics != ''",
    )
    .get() as { cnt: number };
  const authorBios = db
    .prepare(
      "SELECT COUNT(*) AS cnt FROM authors WHERE bio IS NOT NULL AND bio != ''",
    )
    .get() as { cnt: number };

  return {
    totalLetters: letters.cnt,
    totalAuthors: authors.cnt,
    totalCollections: collections.cnt,
    firstEnglish: firstEnglish.cnt,
    withDistance: withDistance.cnt,
    withCarriers: withCarriers.cnt,
    topicTagged: topicTagged.cnt,
    authorBios: authorBios.cnt,
  };
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function AboutPage() {
  const stats = getProjectStats();

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6">
      <Breadcrumbs segments={[{ label: 'About' }]} />

      <header className="pt-8 pb-8">
        <h1
          className="text-3xl sm:text-4xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          About this project
        </h1>
      </header>

      <div className="prose prose-sm dark:prose-invert max-w-none pb-16 space-y-10">

        {/* Origin */}
        <section>
          <h2
            className="text-xl tracking-tight"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Origin
          </h2>
          <p className="text-theme-text leading-relaxed mt-3">
            Roman Letters grows out of a simple observation in Patrick Wyman&apos;s
            2016 USC dissertation,{' '}
            <em>Letters, Mobility, and the Fall of the Roman Empire</em>: the late
            Roman world left behind an extraordinary volume of surviving
            correspondence. Senators, bishops, monks, and imperial officials all
            relied on letters to maintain relationships across vast distances,
            and many of those letters still exist, scattered across digital
            archives and critical editions.
          </p>
          <p className="text-theme-text leading-relaxed mt-3">
            This project collects that scattered corpus into a single,
            structured database and provides tools for exploring the
            communication networks it reveals.
          </p>
        </section>

        {/* Dataset */}
        <section>
          <h2
            className="text-xl tracking-tight"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            The dataset
          </h2>
          <p className="text-theme-text leading-relaxed mt-3">
            The database currently contains:
          </p>
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-4">
            {[
              { value: stats.totalLetters.toLocaleString(), label: 'Letters' },
              { value: stats.totalCollections.toLocaleString(), label: 'Collections' },
              { value: stats.totalAuthors.toLocaleString(), label: 'People identified' },
              { value: stats.firstEnglish.toLocaleString(), label: 'First English translations' },
              { value: stats.withDistance.toLocaleString(), label: 'With distance data' },
              { value: stats.topicTagged.toLocaleString(), label: 'Topic-tagged' },
              { value: stats.withCarriers.toLocaleString(), label: 'Carrier mentions' },
              { value: stats.authorBios.toLocaleString(), label: 'Author bios' },
            ].map((s) => (
              <div
                key={s.label}
                className="p-4 rounded-lg border border-theme bg-theme-surface"
              >
                <div
                  className="text-2xl font-light text-theme-accent tabular-nums"
                  style={{ fontFamily: 'var(--font-serif)' }}
                >
                  {s.value}
                </div>
                <div className="mt-1 text-xs text-theme-muted">{s.label}</div>
              </div>
            ))}
          </div>
          <p className="text-theme-text leading-relaxed mt-4">
            Letters span from roughly 97 to 800 AD, covering the transition
            from the unified Roman Empire to the early medieval kingdoms of
            western Europe. Major collections include the letters of Augustine,
            Gregory the Great, Symmachus, Basil of Caesarea, Jerome, Cassiodorus,
            and Sidonius Apollinaris, among others.
          </p>
        </section>

        {/* Methodology */}
        <section id="methodology">
          <h2
            className="text-xl tracking-tight"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Methodology
          </h2>

          <h3
            className="text-base font-semibold mt-6 mb-2"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Text collection
          </h3>
          <p className="text-theme-text leading-relaxed">
            Texts were collected by scraping and parsing freely available digital
            sources. Each source required a custom parser to handle its markup,
            encoding, and structure. Latin and Greek originals came primarily from
            The Latin Library, Tertullian.org, Perseus Digital Library, and
            OpenGreekAndLatin&apos;s First1KGreek project (CSEL XML editions). English
            translations came primarily from New Advent (the Nicene and
            Post-Nicene Fathers series) and Tertullian.org. Additional volumes
            were drawn from Internet Archive scans of MGH and CSEL print editions,
            Latin Wikisource, the Fordham Medieval Sourcebook, Livius.org, and
            Demonax.info. Where OCR-sourced text was used (particularly Patrologia
            Graeca volumes from Internet Archive), the raw text was cleaned to
            remove scanning artifacts before import.
          </p>

          <h3
            className="text-base font-semibold mt-6 mb-2"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Translations
          </h3>
          <p className="text-theme-text leading-relaxed">
            Every letter has a modern English translation. For letters where a
            public-domain English translation already existed (primarily the NPNF
            series), the modern translation was produced by modernizing that
            19th-century text using Claude (Anthropic). For the{' '}
            {stats.firstEnglish.toLocaleString()} letters with no prior English
            translation, the modern translation was produced directly from the
            Latin or Greek original using Claude, guided by a detailed internal
            translation guide covering late antique epistolary conventions,
            register, and rhetorical style. All AI-assisted translations are
            labeled in the interface. They are provided for accessibility and
            research convenience, not as authoritative scholarly translations.
            The original Latin or Greek text is preserved alongside every
            translation.
          </p>
          <p className="text-theme-text leading-relaxed mt-3">
            A quality note: bulk translations of Greek collections (particularly
            Isidore of Pelusium and Libanius) are thematic renderings rather than
            precise philological translations. OCR-sourced texts from Patrologia
            Graeca may contain scanning artifacts in the Latin and Greek originals.
            Corrections from domain experts are welcome.
          </p>

          <h3
            className="text-base font-semibold mt-6 mb-2"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Recipient and sender identification
          </h3>
          <p className="text-theme-text leading-relaxed">
            Sender and recipient names were extracted by automated parsing of
            letter headers (e.g., &quot;To Eusebius&quot;, &quot;Augustine to
            Paulinus&quot;) and then reconciled against a shared people table.
            Common variants, nicknames, and titles were normalized during a manual
            review pass. Where a letter&apos;s addressee is unknown or disputed,
            the recipient is recorded as &quot;Unknown&quot; or left blank.
          </p>

          <h3
            className="text-base font-semibold mt-6 mb-2"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Location assignment and confidence levels
          </h3>
          <p className="text-theme-text leading-relaxed">
            Geographic coordinates for letter origins and destinations were
            assigned in three tiers, following Wyman&apos;s methodology:
          </p>
          <ul className="mt-2 space-y-1 text-theme-text list-disc list-inside">
            <li>
              <strong>Strong</strong> - historically established location, confirmed
              by prosopographic data or explicit mention in the letter
            </li>
            <li>
              <strong>Approximate</strong> - inferred from collection context,
              known residence periods, or regional information
            </li>
            <li>
              <strong>Unknown</strong> - no reliable location data; coordinates
              not used in distance calculations
            </li>
          </ul>
          <p className="text-theme-text leading-relaxed mt-3">
            Confidence levels are displayed on individual letter pages and used
            to filter the map and network visualizations.
          </p>

          <h3
            className="text-base font-semibold mt-6 mb-2"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Distance calculation
          </h3>
          <p className="text-theme-text leading-relaxed">
            Straight-line distances between sender and recipient locations are
            computed using the haversine formula (great-circle distance between
            two latitude/longitude coordinates). Only letters with
            &quot;strong&quot; or &quot;approximate&quot; confidence on both
            endpoints are included in distance calculations.
          </p>

          <h3
            className="text-base font-semibold mt-6 mb-2"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Road routing
          </h3>
          <p className="text-theme-text leading-relaxed">
            The map timelapse can optionally display routed paths along the ancient
            Roman road network rather than straight-line arcs. Road data comes
            from the Ancient World Mapping Center (AWMC) Barrington Atlas road
            network, provided as GeoJSON. Paths are computed using BFS (breadth-first
            search) over the road graph, snapping letter endpoints to the nearest
            road node. Where no road path can be found, the display falls back to
            a straight-line arc.
          </p>
        </section>

        {/* Sources */}
        <section id="sources">
          <h2
            className="text-xl tracking-tight"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Sources
          </h2>

          <h3
            className="text-base font-semibold mt-6 mb-2"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Digital text sources
          </h3>
          <ul className="mt-2 space-y-2 text-theme-text">
            <li>
              <a
                href="https://www.newadvent.org/fathers/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                New Advent
              </a>{' '}
              - English translations of patristic letters from the Nicene and
              Post-Nicene Fathers series (public domain)
            </li>
            <li>
              <a
                href="http://www.thelatinlibrary.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                The Latin Library
              </a>{' '}
              - Latin originals from standard critical editions
            </li>
            <li>
              <a
                href="https://www.tertullian.org"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                Tertullian.org
              </a>{' '}
              (Roger Pearse) - Latin texts and English translations for several
              minor collections
            </li>
            <li>
              <a
                href="https://www.perseus.tufts.edu"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                Perseus Digital Library
              </a>{' '}
              - Greek and Latin originals with TEI XML markup
            </li>
            <li>
              <a
                href="https://archive.org"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                Internet Archive
              </a>{' '}
              - OCR scans of Patrologia Graeca volumes, MGH volumes, and CSEL
              print editions
            </li>
            <li>
              <a
                href="https://la.wikisource.org"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                Latin Wikisource
              </a>{' '}
              - Braulio of Zaragoza and other Iberian authors
            </li>
            <li>
              <a
                href="https://github.com/OpenGreekAndLatin/First1KGreek"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                OpenGreekAndLatin / First1KGreek
              </a>{' '}
              - CSEL XML editions of Ennodius, Ruricius of Limoges, Avitus of
              Vienne, and Paulinus of Nola
            </li>
            <li>
              <a
                href="https://github.com/openMGH"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                openMGH
              </a>{' '}
              - Avitus of Vienne (MGH edition)
            </li>
            <li>
              <a
                href="https://sourcebooks.fordham.edu/basis/boniface-letters.asp"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                Fordham Medieval Sourcebook
              </a>{' '}
              - Selected letters of Boniface
            </li>
            <li>
              <a
                href="https://www.livius.org/sources/content/synesius/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                Livius.org
              </a>{' '}
              and{' '}
              <a
                href="https://demonax.info/doku.php?id=text:synesius_letters"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                Demonax.info
              </a>{' '}
              - Synesius of Cyrene
            </li>
          </ul>

          <h3
            className="text-base font-semibold mt-6 mb-2"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Map and geographic data
          </h3>
          <ul className="mt-2 space-y-2 text-theme-text">
            <li>
              <a
                href="https://dh.gu.se/dare/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                DARE (Digital Atlas of the Roman Empire)
              </a>{' '}
              - Historical map tiles (CC BY 4.0)
            </li>
            <li>
              <a
                href="https://awmc.unc.edu/wordpress/blog/map-files/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                AWMC (Ancient World Mapping Center)
              </a>{' '}
              - Barrington Atlas road network GeoJSON (ODbL)
            </li>
          </ul>

          <h3
            className="text-base font-semibold mt-6 mb-2"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Scholarly references
          </h3>
          <ul className="mt-2 space-y-2 text-theme-text">
            <li>
              Patrick Wyman, <em>Letters, Mobility, and the Fall of the Roman
              Empire</em> (PhD dissertation, University of Southern California,
              2016) - the primary scholarly framework for network analysis and
              geographic scope
            </li>
            <li>
              Cristiana Sogno, Bradley K. Storin, and Edward J. Watts (eds.),{' '}
              <em>Late Antique Letter Collections: A Critical Introduction and
              Reference Guide</em> (University of California Press, 2017) -
              reference for collection scope and authorship context
            </li>
          </ul>
        </section>

        {/* AI transparency */}
        <section>
          <h2
            className="text-xl tracking-tight"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            AI translation transparency
          </h2>
          <p className="text-theme-text leading-relaxed mt-3">
            Modern English translations were produced using Claude (Anthropic),
            working from either the Latin/Greek original or an existing
            19th-century English version. Translation work was guided by two
            internal documents: a translation guide covering late antique
            epistolary conventions, rhetorical register, and how to handle common
            formulaic phrases; and a modern voice guide specifying tone,
            vocabulary level, and how to avoid archaism while remaining faithful
            to the original.
          </p>
          <p className="text-theme-text leading-relaxed mt-3">
            AI-generated translations are clearly marked in the interface. They
            are provided for accessibility and research convenience, not as
            authoritative scholarly translations. The original Latin or Greek is
            preserved alongside every translation, and 19th-century English
            versions are shown where available. Corrections from domain experts
            are welcome.
          </p>
        </section>

        {/* License */}
        <section id="license">
          <h2
            className="text-xl tracking-tight"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            License
          </h2>
          <ul className="mt-3 space-y-2 text-theme-text">
            <li>
              <strong>Code</strong> - MIT License. Source available on GitHub.
            </li>
            <li>
              <strong>Data and translations</strong> -{' '}
              <a
                href="https://creativecommons.org/licenses/by/4.0/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                CC BY 4.0
              </a>
              . Attribution: Roman Letters / romanletters.org.
            </li>
            <li>
              <strong>Map tiles</strong> - DARE tiles are CC BY 4.0. Credit:
              Johan Ahlfeldt, Digital Atlas of the Roman Empire.
            </li>
            <li>
              <strong>Road data</strong> - AWMC Barrington Atlas road network,
              available under ODbL.
            </li>
          </ul>
        </section>

        {/* Credits */}
        <section id="credits">
          <h2
            className="text-xl tracking-tight"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Credits
          </h2>
          <ul className="mt-3 space-y-2 text-theme-text">
            <li>
              Created by{' '}
              <a
                href="https://craigvandergalien.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                Craig Vander Galien
              </a>
            </li>
            <li>
              Inspired by Patrick Wyman and his dissertation on late Roman
              epistolary networks
            </li>
            <li>
              Translations assisted by{' '}
              <a
                href="https://anthropic.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                Claude (Anthropic)
              </a>
            </li>
          </ul>
        </section>

        {/* Open source */}
        <section>
          <h2
            className="text-xl tracking-tight"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Open source
          </h2>
          <p className="text-theme-text leading-relaxed mt-3">
            The full dataset, scraping scripts, and this website are open source.
            The dataset is permanently archived and available on multiple platforms.
          </p>
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <a
              href="https://github.com/CraigVG/roman-letters-network"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium
                bg-theme-surface border border-theme text-theme-text
                hover:text-theme-accent hover:border-[var(--color-accent)] transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
              </svg>
              GitHub
            </a>
            <a
              href="https://doi.org/10.5281/zenodo.19142059"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium
                bg-theme-surface border border-theme text-theme-text
                hover:text-theme-accent hover:border-[var(--color-accent)] transition-colors"
            >
              Zenodo (DOI)
            </a>
            <a
              href="https://www.kaggle.com/datasets/craigvandergalien/late-roman-empire-letters-100-800-ad"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium
                bg-theme-surface border border-theme text-theme-text
                hover:text-theme-accent hover:border-[var(--color-accent)] transition-colors"
            >
              Kaggle
            </a>
            <a
              href="https://huggingface.co/datasets/craigvg/roman-letters-network"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium
                bg-theme-surface border border-theme text-theme-text
                hover:text-theme-accent hover:border-[var(--color-accent)] transition-colors"
            >
              HuggingFace
            </a>
            <a
              href="https://archive.org/details/roman_letters"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium
                bg-theme-surface border border-theme text-theme-text
                hover:text-theme-accent hover:border-[var(--color-accent)] transition-colors"
            >
              Internet Archive
            </a>
            <a
              href="https://github.com/CraigVG/roman-letters-network/releases/tag/v1.0.0"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium
                bg-theme-surface border border-theme text-theme-text
                hover:text-theme-accent hover:border-[var(--color-accent)] transition-colors"
            >
              Download v1.0.0
            </a>
          </div>
          <p className="mt-4 text-sm text-theme-muted">
            <strong>Cite this dataset:</strong> Vander Galien, Craig. (2026). Roman Letters: 7,049 Letters
            from the Late Roman World (100-800 AD). Zenodo.{' '}
            <a href="https://doi.org/10.5281/zenodo.19142059" className="text-theme-accent hover:underline">
              doi.org/10.5281/zenodo.19142059
            </a>
          </p>
        </section>

        {/* Navigation */}
        <section className="pt-4 border-t border-theme">
          <div className="flex flex-wrap gap-4">
            <Link
              href="/letters"
              className="text-sm text-theme-accent hover:underline"
            >
              Browse letters &rarr;
            </Link>
            <Link
              href="/authors"
              className="text-sm text-theme-accent hover:underline"
            >
              Browse authors &rarr;
            </Link>
            <Link
              href="/network"
              className="text-sm text-theme-accent hover:underline"
            >
              View network graph &rarr;
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}

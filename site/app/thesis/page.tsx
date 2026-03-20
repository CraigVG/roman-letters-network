import type { Metadata } from 'next';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import { ThesisContent } from './ThesisContent';

export const metadata: Metadata = {
  title: 'The Shrinking World',
  description:
    'How letter-travel distances reveal the breakdown of Roman connectivity. Based on Patrick Wyman\'s dissertation on letters, mobility, and the fall of the Roman Empire.',
};

export default function ThesisPage() {
  return (
    <>
      <div className="max-w-4xl mx-auto px-4 sm:px-6">
        <Breadcrumbs segments={[{ label: 'The Shrinking World' }]} />
      </div>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 pt-4 pb-8 sm:pt-12 sm:pb-12">
        <p className="text-xs font-medium tracking-[0.2em] uppercase text-theme-accent mb-4">
          Regionalization Analysis
        </p>
        <h1
          className="text-3xl sm:text-4xl lg:text-5xl tracking-tight leading-[1.1]"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          The Shrinking World
        </h1>
        <p
          className="mt-4 text-lg sm:text-xl text-theme-muted max-w-2xl leading-relaxed italic"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          How the Roman communication network contracted, decade by decade,
          as the empire fragmented into successor kingdoms
        </p>

        {/* Decorative rule */}
        <div className="mt-8 flex items-center gap-3 max-w-xs">
          <span
            className="h-px flex-1"
            style={{ backgroundColor: 'var(--color-accent)', opacity: 0.4 }}
          />
          <span className="text-theme-accent text-xs">&#9670;</span>
          <span
            className="h-px flex-1"
            style={{ backgroundColor: 'var(--color-accent)', opacity: 0.4 }}
          />
        </div>
      </section>

      {/* Introduction */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 pb-12">
        <div className="space-y-5 text-theme-text leading-relaxed">
          <p>
            Every surviving letter from the late Roman world is a{' '}
            <strong>fossilized moment of movement</strong>. Someone had to carry
            it, on foot or horseback, along a specific road or across a specific
            stretch of sea. The letter itself is just parchment and ink, but the
            journey it represents reveals the connective tissue of an empire:
            the roads, the routes, the relationships that kept a vast political
            entity coherent across thousands of kilometers.
          </p>
          <p>
            Patrick Wyman&rsquo;s 2016 USC dissertation,{' '}
            <em>
              &ldquo;The Fall of the Roman Empire and the Rise of Its Successor
              States: Letters, Mobility, and the Transition from Late Antiquity
              to the Early Middle Ages&rdquo;
            </em>
            , made a deceptively simple argument: if you measure the distances
            these letters traveled and plot them over time, you can watch the
            Roman world shrink. Long-distance connections that once spanned the
            Mediterranean basin gave way to regional networks confined within
            the borders of Visigothic Spain, Frankish Gaul, or Ostrogothic
            Italy. The fall of Rome was, at its core, a{' '}
            <strong>mobility crisis</strong>.
          </p>
          <p>
            Our dataset of over 7,000 letters lets us extend Wyman&rsquo;s
            analysis. Where he focused on the Latin West from 450 to 650 AD
            with 2,895 letters, we can see the broader picture: both East and
            West, from the 1st to the 9th century. The chart below tracks the
            average distance between sender and recipient for every
            inter-city letter with known coordinates, grouped by decade. We
            exclude same-city correspondence (where sender and recipient
            share a location) to isolate the long-range connectivity that
            defined the Roman communication network.
          </p>
        </div>
      </section>

      {/* Interactive content (client component) */}
      <ThesisContent />

      {/* Letter quotes */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
        <h2
          className="text-2xl sm:text-3xl tracking-tight mb-8"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Voices from a fragmenting world
        </h2>

        <div className="space-y-8">
          {/* Quote 1 */}
          <blockquote className="border-l-2 pl-6" style={{ borderColor: 'var(--color-accent)' }}>
            <p
              className="text-base sm:text-lg italic leading-relaxed text-theme-text"
              style={{ fontFamily: 'var(--font-serif)' }}
            >
              &ldquo;The roads are blocked, the seas are shut, the provinces are
              cut off from each other by the movements of peoples hostile and
              unknown.&rdquo;
            </p>
            <footer className="mt-3 text-sm text-theme-muted">
              - Sidonius Apollinaris, <em>Letter 3.4</em> (c. 470 AD),
              writing from Clermont as Visigothic armies encircled Gaul
            </footer>
          </blockquote>

          {/* Quote 2 */}
          <blockquote className="border-l-2 pl-6" style={{ borderColor: 'var(--color-accent)' }}>
            <p
              className="text-base sm:text-lg italic leading-relaxed text-theme-text"
              style={{ fontFamily: 'var(--font-serif)' }}
            >
              &ldquo;I have sent this letter by the hand of the deacon Candidus,
              who goes to manage the patrimony of the blessed Peter in Gaul.
              Through him, if it please you, send me whatever response you
              wish.&rdquo;
            </p>
            <footer className="mt-3 text-sm text-theme-muted">
              - Gregory the Great, <em>Letter 6.6</em> (c. 595 AD),
              to Queen Brunhild - papal correspondence still crossing
              the Alps, but now routing through church administrators
            </footer>
          </blockquote>

          {/* Quote 3 */}
          <blockquote className="border-l-2 pl-6" style={{ borderColor: 'var(--color-accent)' }}>
            <p
              className="text-base sm:text-lg italic leading-relaxed text-theme-text"
              style={{ fontFamily: 'var(--font-serif)' }}
            >
              &ldquo;We have been separated by so great a distance that the very
              occasion of writing seems to have perished, since there is no one
              traveling from your region to ours.&rdquo;
            </p>
            <footer className="mt-3 text-sm text-theme-muted">
              - Ruricius of Limoges, <em>Letter 2.33</em> (c. 500 AD),
              lamenting the collapse of routine communication between
              Aquitaine and Italy
            </footer>
          </blockquote>
        </div>
      </section>

      {/* Methodology */}
      <section className="border-t border-theme">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
          <h2
            className="text-2xl sm:text-3xl tracking-tight mb-6"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Methodology
          </h2>
          <div className="space-y-4 text-theme-muted leading-relaxed text-sm">
            <p>
              Distances are calculated as great-circle (haversine) distances
              between the primary locations of the sender and recipient, as
              recorded in our authors database. This is an approximation:
              authors sometimes wrote from locations other than their primary
              residence, and we assign each person a single coordinate. Still,
              for the overwhelming majority of letters - especially
              bishops writing from their sees or officials at their posts
              - this is a reasonable proxy.
            </p>
            <p>
              Same-city letters (where sender and recipient share coordinates)
              are excluded, as they represent local correspondence rather than
              inter-city mobility. Decades with fewer than 10 inter-city
              letters are also excluded to avoid misleading averages from small
              samples. The dot size reflects the number of letters in each
              decade, and sample sizes are labeled. The trend line is a 50-year
              weighted moving average that accounts for both temporal proximity
              and sample size, smoothing decade-to-decade noise to reveal the
              underlying trajectory. Gaps in the timeline reflect genuine
              holes in the surviving letter corpus, not suppressed data.
            </p>
            <p>
              The &ldquo;Wyman Mode&rdquo; toggle filters to Latin West
              collections only (roughly corresponding to the Western Roman
              Empire and its successor states), within the 450-650 AD
              range that Wyman studied. This is the subset most directly
              comparable to his dissertation findings.
            </p>
          </div>

          <div className="mt-8 p-4 rounded-lg bg-theme-surface border border-theme">
            <p className="text-sm text-theme-muted">
              <strong className="text-theme-text">Citation:</strong> Patrick
              Wyman, &ldquo;The Fall of the Roman Empire and the Rise of Its
              Successor States: Letters, Mobility, and the Transition from Late
              Antiquity to the Early Middle Ages&rdquo; (PhD diss., University
              of Southern California, 2016). Our analysis builds on his
              methodology with a larger dataset covering both the Greek East
              and Latin West.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}

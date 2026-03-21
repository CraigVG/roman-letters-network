import Link from 'next/link';

export function Footer() {
  return (
    <footer className="border-t border-theme mt-auto">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
          {/* Branding column */}
          <div>
            <p
              className="text-base font-light tracking-tight text-theme-text"
              style={{ fontFamily: 'var(--font-serif)' }}
            >
              Roman Letters
            </p>
            <p className="mt-2 text-sm text-theme-muted leading-relaxed">
              Mapping the communication networks of the late Roman Empire
              through 7,049 surviving letters.
            </p>
            <p className="mt-2 text-sm text-theme-muted leading-relaxed">
              Created by{' '}
              <a
                href="https://craigvandergalien.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-theme-accent hover:underline"
              >
                Craig Vander Galien
              </a>
            </p>
          </div>

          {/* Navigation column */}
          <div>
            <p className="text-xs font-medium tracking-[0.15em] uppercase text-theme-muted mb-3">
              Explore
            </p>
            <nav className="flex flex-col gap-2">
              <Link
                href="/letters"
                className="text-sm text-theme-muted hover:text-theme-accent transition-colors"
              >
                Letters
              </Link>
              <Link
                href="/authors"
                className="text-sm text-theme-muted hover:text-theme-accent transition-colors"
              >
                Authors
              </Link>
              <Link
                href="/network"
                className="text-sm text-theme-muted hover:text-theme-accent transition-colors"
              >
                Network Graph
              </Link>
              <Link
                href="/map"
                className="text-sm text-theme-muted hover:text-theme-accent transition-colors"
              >
                Map
              </Link>
              <Link
                href="/thesis"
                className="text-sm text-theme-muted hover:text-theme-accent transition-colors"
              >
                Thesis
              </Link>
            </nav>
          </div>

          {/* Project column */}
          <div>
            <p className="text-xs font-medium tracking-[0.15em] uppercase text-theme-muted mb-3">
              Project
            </p>
            <nav className="flex flex-col gap-2">
              <Link
                href="/about"
                className="text-sm text-theme-muted hover:text-theme-accent transition-colors"
              >
                About
              </Link>
              <Link
                href="/about#sources"
                className="text-sm text-theme-muted hover:text-theme-accent transition-colors"
              >
                Sources
              </Link>
              <a
                href="https://github.com/CraigVG/roman-letters-network"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-theme-muted hover:text-theme-accent transition-colors"
              >
                GitHub
              </a>
            </nav>
          </div>
        </div>

        {/* Bottom rule + copyright */}
        <div className="mt-10 pt-6 border-t border-theme flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <p className="text-xs text-theme-muted">
            An open-source project mapping late Roman correspondence networks (97-800 AD).
          </p>
          <p
            className="text-xs text-theme-muted italic"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            97-800 AD
          </p>
        </div>
      </div>
    </footer>
  );
}

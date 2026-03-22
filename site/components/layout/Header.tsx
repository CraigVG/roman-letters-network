'use client';

import Link from 'next/link';
import { useState } from 'react';
import { ThemeToggle } from './ThemeToggle';
import { useScholarlyMode } from './ScholarlyModeContext';

function ScholarlyToggle() {
  const { scholarlyMode, setScholarlyMode } = useScholarlyMode();
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setScholarlyMode(!scholarlyMode)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className={`w-9 h-9 rounded-lg border flex items-center justify-center transition-colors ${
          scholarlyMode
            ? 'bg-[var(--color-accent)] border-[var(--color-accent)] text-white'
            : 'bg-theme-surface border-theme text-theme-muted hover:text-theme-text'
        }`}
        aria-label={scholarlyMode ? 'Scholarly mode on (hiding AI translations)' : 'Scholarly mode off (showing all translations)'}
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
        </svg>
      </button>
      {showTooltip && (
        <div className="absolute top-full right-0 mt-2 w-56 px-3 py-2 rounded-lg bg-theme-surface border border-theme shadow-lg z-50 text-xs text-theme-text">
          <div className="font-medium mb-1">
            Scholarly Mode {scholarlyMode ? '(ON)' : '(OFF)'}
          </div>
          <p className="text-theme-muted leading-relaxed">
            {scholarlyMode
              ? 'AI-assisted translations are hidden. Only pre-existing scholarly translations and original Latin/Greek are shown.'
              : 'Click to hide AI-assisted translations and show only scholarly translations and original texts.'}
          </p>
        </div>
      )}
    </div>
  );
}

const navItems = [
  { label: 'Letters', href: '/letters' },
  { label: 'People', href: '/people' },
  { label: 'Authors', href: '/authors' },
  { label: 'Places', href: '/places' },
  { label: 'Map', href: '/map' },
  { label: 'Network', href: '/network' },
  { label: 'Thesis', href: '/thesis' },
  { label: 'About', href: '/about' },
];

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="border-b border-theme">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Wordmark */}
          <Link
            href="/"
            className="font-serif text-xl tracking-tight text-theme-text hover:text-theme-accent transition-colors"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Roman Letters
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="px-3 py-2 text-sm text-theme-muted hover:text-theme-accent transition-colors rounded-md"
              >
                {item.label}
              </Link>
            ))}
            <button
              onClick={() =>
                document.dispatchEvent(
                  new KeyboardEvent('keydown', { key: 'k', metaKey: true }),
                )
              }
              className="ml-2 w-9 h-9 rounded-lg bg-theme-surface border border-theme flex items-center justify-center text-theme-muted hover:text-theme-text transition-colors"
              aria-label="Search (Cmd+K)"
              title="Search (Cmd+K)"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-4 h-4"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </button>
            <div className="ml-1">
              <ScholarlyToggle />
            </div>
            <div className="ml-1">
              <ThemeToggle />
            </div>
          </nav>

          {/* Mobile controls */}
          <div className="flex items-center gap-2 md:hidden">
            <ScholarlyToggle />
            <button
              onClick={() =>
                document.dispatchEvent(
                  new KeyboardEvent('keydown', { key: 'k', metaKey: true }),
                )
              }
              className="w-9 h-9 rounded-lg bg-theme-surface border border-theme flex items-center justify-center text-theme-muted hover:text-theme-text transition-colors"
              aria-label="Search"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-4 h-4"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </button>
            <ThemeToggle />
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="w-9 h-9 rounded-lg bg-theme-surface border border-theme flex items-center justify-center"
              aria-label={menuOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={menuOpen}
            >
              {menuOpen ? (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-4 h-4"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              ) : (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-4 h-4"
                >
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <nav className="md:hidden border-t border-theme py-3 pb-4">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMenuOpen(false)}
                className="block px-2 py-2.5 text-sm text-theme-muted hover:text-theme-accent transition-colors"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        )}
      </div>
    </header>
  );
}

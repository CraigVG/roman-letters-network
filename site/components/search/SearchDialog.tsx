'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';

interface PagefindResult {
  id: string;
  url: string;
  excerpt: string;
  meta: {
    title?: string;
    image?: string;
  };
  filters: {
    collection?: string[];
  };
  sub_results: {
    title: string;
    url: string;
    excerpt: string;
  }[];
}

interface PagefindSearchResult {
  id: string;
  data: () => Promise<PagefindResult>;
}

interface PagefindResponse {
  results: PagefindSearchResult[];
}

interface Pagefind {
  init: () => Promise<void>;
  search: (query: string) => Promise<PagefindResponse>;
}

export function SearchDialog() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<PagefindResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const pagefindRef = useRef<Pagefind | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Load Pagefind
  const loadPagefind = useCallback(async () => {
    if (pagefindRef.current) return pagefindRef.current;
    try {
      // Pagefind JS is generated at build time into out/pagefind/
      const pfPath = '/pagefind/pagefind.js';
      const pf = (await import(/* webpackIgnore: true */ pfPath)) as unknown as Pagefind;
      await pf.init();
      pagefindRef.current = pf;
      return pf;
    } catch {
      console.warn('Pagefind not available - run a production build first.');
      return null;
    }
  }, []);

  // Keyboard shortcut: Cmd+K / Ctrl+K
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, []);

  // Focus input when dialog opens
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery('');
      setResults([]);
      setSelectedIndex(0);
    }
  }, [open]);

  // Search on query change
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setSelectedIndex(0);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      const pf = await loadPagefind();
      if (!pf) {
        setLoading(false);
        return;
      }
      const response = await pf.search(query);
      const loaded = await Promise.all(
        response.results.slice(0, 10).map((r) => r.data()),
      );
      setResults(loaded);
      setSelectedIndex(0);
      setLoading(false);
    }, 200);

    return () => clearTimeout(timer);
  }, [query, loadPagefind]);

  // Navigate to result
  const navigateTo = useCallback(
    (url: string) => {
      setOpen(false);
      router.push(url);
    },
    [router],
  );

  // Keyboard navigation inside dialog
  function onInputKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape') {
      setOpen(false);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && results[selectedIndex]) {
      navigateTo(results[selectedIndex].url);
    }
  }

  // Click outside to close
  function onBackdropClick(e: React.MouseEvent) {
    if (dialogRef.current && !dialogRef.current.contains(e.target as Node)) {
      setOpen(false);
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
      onClick={onBackdropClick}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

      {/* Dialog */}
      <div
        ref={dialogRef}
        className="relative w-full max-w-xl mx-4 rounded-xl shadow-2xl border border-theme overflow-hidden"
        style={{ backgroundColor: 'var(--color-bg)' }}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 border-b border-theme">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-4 h-4 text-theme-muted shrink-0"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onInputKeyDown}
            placeholder="Search letters..."
            className="flex-1 py-3.5 bg-transparent text-theme-text placeholder:text-theme-muted outline-none text-sm"
          />
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium text-theme-muted border border-theme rounded">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-[50vh] overflow-y-auto">
          {loading && (
            <div className="px-4 py-8 text-center text-sm text-theme-muted">
              Searching...
            </div>
          )}

          {!loading && query.trim() && results.length === 0 && (
            <div className="px-4 py-8 text-center text-sm text-theme-muted">
              No results for &ldquo;{query}&rdquo;
            </div>
          )}

          {!loading && results.length > 0 && (
            <ul className="py-2">
              {results.map((result, i) => {
                const collection = result.filters.collection?.[0];
                return (
                  <li key={result.id ?? i}>
                    <button
                      onClick={() => navigateTo(result.url)}
                      onMouseEnter={() => setSelectedIndex(i)}
                      className={`w-full text-left px-4 py-3 flex flex-col gap-1 transition-colors ${
                        i === selectedIndex
                          ? 'bg-theme-surface'
                          : 'hover:bg-theme-surface'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-theme-text truncate">
                          {result.meta.title || 'Untitled'}
                        </span>
                        {collection && (
                          <span className="shrink-0 px-1.5 py-0.5 text-[10px] font-medium rounded bg-[var(--color-accent)]/10 text-theme-accent capitalize">
                            {collection}
                          </span>
                        )}
                      </div>
                      {result.excerpt && (
                        <p
                          className="text-xs text-theme-muted line-clamp-2 [&_mark]:bg-[var(--color-accent)]/20 [&_mark]:text-theme-accent [&_mark]:rounded-sm [&_mark]:px-0.5"
                          dangerouslySetInnerHTML={{ __html: result.excerpt }}
                        />
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}

          {!loading && !query.trim() && (
            <div className="px-4 py-8 text-center text-sm text-theme-muted">
              Start typing to search across all letters...
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-theme flex items-center gap-4 text-[10px] text-theme-muted">
          <span className="flex items-center gap-1">
            <kbd className="px-1 py-0.5 border border-theme rounded text-[9px]">&uarr;</kbd>
            <kbd className="px-1 py-0.5 border border-theme rounded text-[9px]">&darr;</kbd>
            navigate
          </span>
          <span className="flex items-center gap-1">
            <kbd className="px-1 py-0.5 border border-theme rounded text-[9px]">Enter</kbd>
            open
          </span>
          <span className="flex items-center gap-1">
            <kbd className="px-1 py-0.5 border border-theme rounded text-[9px]">Esc</kbd>
            close
          </span>
        </div>
      </div>
    </div>
  );
}

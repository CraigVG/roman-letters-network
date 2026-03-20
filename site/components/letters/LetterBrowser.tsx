'use client';

import { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { useLetterFilters } from './useLetterFilters';
import { LetterList } from './LetterList';
import { FilterBar } from './FilterBar';
import { LetterOfTheDay } from './LetterOfTheDay';
import CuratedPathways from './CuratedPathways';
import dynamic from 'next/dynamic';
import type { LetterItem } from './LetterList';

const TimelineHistogram = dynamic(() => import('./TimelineHistogram'), { ssr: false });

interface FeaturedLetter {
  id: number;
  c: string;
  n: number;
  y?: number;
  s?: string;
  r?: string;
  q?: string;
  note?: string;
  topics?: string[];
}

interface LettersIndex {
  letters: LetterItem[];
  featured: FeaturedLetter[];
  topics: { slug: string; label: string; count: number }[];
  collections: { slug: string; name: string; count: number; dateRange?: string }[];
  decades: { decade: number; count: number }[];
  pathways: {
    slug: string;
    title: string;
    description: string;
    filters: Record<string, unknown>;
    count: number;
  }[];
}

const PER_PAGE = 50;

function sortLetters(letters: LetterItem[], sortKey: string): LetterItem[] {
  const sorted = [...letters];
  switch (sortKey) {
    case 'date-asc':
      return sorted.sort((a, b) => (a.y ?? 9999) - (b.y ?? 9999));
    case 'date-desc':
      return sorted.sort((a, b) => (b.y ?? 0) - (a.y ?? 0));
    case 'collection-asc':
      return sorted.sort((a, b) => a.c.localeCompare(b.c) || a.n - b.n);
    case 'sender-asc':
      return sorted.sort((a, b) =>
        (a.s ?? '').localeCompare(b.s ?? '') || (a.y ?? 9999) - (b.y ?? 9999),
      );
    default:
      return sorted;
  }
}

export function LetterBrowser() {
  const [data, setData] = useState<LettersIndex | null>(null);
  const [loading, setLoading] = useState(true);

  const {
    query,
    setQuery,
    topics,
    setTopics,
    collection,
    setCollection,
    from,
    setFrom,
    to,
    setTo,
    firstEnglish,
    setFirstEnglish,
    sort,
    setSort,
    page,
    setPage,
    hasActiveFilters,
    clearAll,
  } = useLetterFilters();

  // Debounced search input
  const [searchInput, setSearchInput] = useState(query);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleSearchChange = useCallback(
    (value: string) => {
      setSearchInput(value);
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        setQuery(value);
      }, 200);
    },
    [setQuery],
  );

  // Sync search input when URL query changes externally
  useEffect(() => {
    setSearchInput(query);
  }, [query]);

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  // Fetch index on mount
  useEffect(() => {
    fetch('/data/letters-index.json')
      .then((res) => res.json())
      .then((json: LettersIndex) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load letters index:', err);
        setLoading(false);
      });
  }, []);

  // Handle timeline histogram range change
  const handleRangeChange = useCallback(
    (newFrom: number | null, newTo: number | null) => {
      setFrom(newFrom);
      setTo(newTo);
    },
    [setFrom, setTo],
  );

  // Handle pathway click - set appropriate filters
  const handlePathwayClick = useCallback(
    (filters: Record<string, unknown>) => {
      clearAll();
      if (filters.topic) setTopics([filters.topic as string]);
      if (filters.from) setFrom(filters.from as number);
      if (filters.to) setTo(filters.to as number);
      if (filters.collection) {
        // Multi-collection pathways use comma-separated - pick the first for now
        const cols = (filters.collection as string).split(',');
        if (cols.length === 1) {
          setCollection(cols[0]);
        }
        // For multi-collection, we'd need a different approach
        // For now, just set the topic/date filters
      }
      if (filters.firstEnglish) setFirstEnglish(true);
    },
    [clearAll, setTopics, setFrom, setTo, setCollection, setFirstEnglish],
  );

  // Filter + sort
  const filtered = useMemo(() => {
    if (!data) return [];

    let result = data.letters;

    // Text search
    if (query) {
      const q = query.toLowerCase();
      result = result.filter(
        (l) =>
          (l.s && l.s.toLowerCase().includes(q)) ||
          (l.r && l.r.toLowerCase().includes(q)) ||
          (l.q && l.q.toLowerCase().includes(q)),
      );
    }

    // Topics filter (OR within facet)
    if (topics.length > 0) {
      result = result.filter((l) => {
        if (!l.t) return false;
        const letterTopics = l.t.split(',').map((t) => t.trim());
        return topics.some((slug) => letterTopics.includes(slug));
      });
    }

    // Collection filter
    if (collection) {
      result = result.filter((l) => l.c === collection);
    }

    // Year range
    if (from != null) {
      result = result.filter((l) => l.y != null && l.y >= from);
    }
    if (to != null) {
      result = result.filter((l) => l.y != null && l.y <= to);
    }

    // First English translation filter
    if (firstEnglish) {
      result = result.filter((l) => l.f === 1);
    }

    return sortLetters(result, sort);
  }, [data, query, topics, collection, from, to, firstEnglish, sort]);

  // Loading skeleton
  if (loading) {
    return (
      <div className="space-y-6">
        {/* Letter of the Day skeleton */}
        <div className="rounded-lg border border-theme bg-theme-surface p-5 animate-pulse"
             style={{ borderLeft: '4px solid var(--color-accent)' }}>
          <div className="h-4 w-32 rounded bg-current opacity-10 mb-4" />
          <div className="h-6 w-3/4 rounded bg-current opacity-10 mb-3" />
          <div className="space-y-2">
            <div className="h-4 w-full rounded bg-current opacity-10" />
            <div className="h-4 w-5/6 rounded bg-current opacity-10" />
          </div>
        </div>

        {/* Pathways skeleton */}
        <div className="flex gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="w-[200px] min-w-[200px] h-[160px] rounded-lg bg-theme-surface animate-pulse border border-theme" />
          ))}
        </div>

        {/* Search skeleton */}
        <div className="h-11 rounded-lg bg-theme-surface animate-pulse" />

        {/* Rows skeleton */}
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 py-3">
            <div className="hidden sm:block h-6 w-24 rounded bg-theme-surface animate-pulse" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-64 rounded bg-theme-surface animate-pulse" />
              <div className="h-3 w-96 rounded bg-theme-surface animate-pulse" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* Letter of the Day */}
      <LetterOfTheDay featured={data.featured} />

      {/* Curated Pathways */}
      <CuratedPathways pathways={data.pathways} onPathwayClick={handlePathwayClick} />

      {/* Search bar */}
      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
          <svg
            className="h-4 w-4 text-theme-muted"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <input
          type="text"
          value={searchInput}
          onChange={(e) => handleSearchChange(e.target.value)}
          placeholder="Search by sender, recipient, or summary..."
          className="w-full rounded-lg border border-theme bg-theme-surface py-2.5 pl-10 pr-10
            text-sm text-theme-text placeholder:text-theme-muted
            focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] focus:border-transparent
            transition-shadow"
          aria-label="Search letters"
        />
        {searchInput && (
          <button
            onClick={() => handleSearchChange('')}
            className="absolute inset-y-0 right-0 flex items-center pr-3 text-theme-muted
              hover:text-theme-text transition-colors"
            aria-label="Clear search"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Timeline histogram */}
      {data.decades.length > 0 && (
        <TimelineHistogram
          decades={data.decades}
          from={from}
          to={to}
          onRangeChange={handleRangeChange}
        />
      )}

      {/* Filter bar */}
      <FilterBar
        topics={data.topics}
        collections={data.collections}
        selectedTopics={topics}
        onTopicsChange={setTopics}
        selectedCollection={collection}
        onCollectionChange={setCollection}
        from={from}
        to={to}
        onFromChange={setFrom}
        onToChange={setTo}
        firstEnglish={firstEnglish}
        onFirstEnglishChange={setFirstEnglish}
        hasActiveFilters={hasActiveFilters}
        onClearAll={clearAll}
      />

      {/* Letter list with pagination */}
      <LetterList
        letters={filtered}
        page={page}
        perPage={PER_PAGE}
        onPageChange={setPage}
        sort={sort}
        onSortChange={setSort}
      />
    </div>
  );
}

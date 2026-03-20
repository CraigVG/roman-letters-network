'use client';

import { useQueryState, parseAsInteger, parseAsString, parseAsArrayOf, parseAsBoolean } from 'nuqs';
import { useCallback, useMemo } from 'react';

export function useLetterFilters() {
  const [query, setQueryRaw] = useQueryState('q', parseAsString.withDefault(''));
  const [topics, setTopicsRaw] = useQueryState(
    'topics',
    parseAsArrayOf(parseAsString, ',').withDefault([]),
  );
  const [collection, setCollectionRaw] = useQueryState('collection', parseAsString);
  const [from, setFromRaw] = useQueryState('from', parseAsInteger);
  const [to, setToRaw] = useQueryState('to', parseAsInteger);
  const [firstEnglish, setFirstEnglishRaw] = useQueryState('firstEnglish', parseAsBoolean);
  const [sort, setSortRaw] = useQueryState('sort', parseAsString.withDefault('date-asc'));
  const [page, setPage] = useQueryState('page', parseAsInteger.withDefault(1));

  // Wrappers that reset page to 1 when a filter changes
  const setQuery = useCallback(
    (v: string | ((old: string) => string)) => {
      setQueryRaw(v);
      setPage(1);
    },
    [setQueryRaw, setPage],
  );

  const setTopics = useCallback(
    (v: string[] | ((old: string[]) => string[])) => {
      setTopicsRaw(v);
      setPage(1);
    },
    [setTopicsRaw, setPage],
  );

  const setCollection = useCallback(
    (v: string | null | ((old: string | null) => string | null)) => {
      setCollectionRaw(v);
      setPage(1);
    },
    [setCollectionRaw, setPage],
  );

  const setFrom = useCallback(
    (v: number | null | ((old: number | null) => number | null)) => {
      setFromRaw(v);
      setPage(1);
    },
    [setFromRaw, setPage],
  );

  const setTo = useCallback(
    (v: number | null | ((old: number | null) => number | null)) => {
      setToRaw(v);
      setPage(1);
    },
    [setToRaw, setPage],
  );

  const setFirstEnglish = useCallback(
    (v: boolean | null | ((old: boolean | null) => boolean | null)) => {
      setFirstEnglishRaw(v);
      setPage(1);
    },
    [setFirstEnglishRaw, setPage],
  );

  const setSort = useCallback(
    (v: string | ((old: string) => string)) => {
      setSortRaw(v);
      setPage(1);
    },
    [setSortRaw, setPage],
  );

  const clearAll = useCallback(() => {
    setQueryRaw('');
    setTopicsRaw([]);
    setCollectionRaw(null);
    setFromRaw(null);
    setToRaw(null);
    setFirstEnglishRaw(null);
    setSortRaw('date-asc');
    setPage(1);
  }, [setQueryRaw, setTopicsRaw, setCollectionRaw, setFromRaw, setToRaw, setFirstEnglishRaw, setSortRaw, setPage]);

  const hasActiveFilters = useMemo(
    () =>
      query !== '' ||
      topics.length > 0 ||
      collection !== null ||
      from !== null ||
      to !== null ||
      firstEnglish === true,
    [query, topics, collection, from, to, firstEnglish],
  );

  return {
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
    clearAll,
    hasActiveFilters,
  };
}

'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';

/* ------------------------------------------------------------------ */
/*  Types                                                             */
/* ------------------------------------------------------------------ */

interface Person {
  id: number;
  name: string;
  name_latin: string | null;
  role: string | null;
  location: string | null;
  birth_year: number | null;
  death_year: number | null;
  sent_count: number;
  received_count: number;
  mentioned_count: number;
}

interface PeopleData {
  people: Person[];
  roles: string[];
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

type SortKey = 'letters' | 'name' | 'mentioned';
type RelFilter = 'all' | 'senders' | 'recipients' | 'mentioned';

/* ------------------------------------------------------------------ */
/*  Page                                                              */
/* ------------------------------------------------------------------ */

export default function PeopleIndexPage() {
  const [data, setData] = useState<PeopleData | null>(null);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [relFilter, setRelFilter] = useState<RelFilter>('all');
  const [sortKey, setSortKey] = useState<SortKey>('letters');

  useEffect(() => {
    fetch('/data/people.json')
      .then((r) => r.json())
      .then((d: PeopleData) => setData(d));
  }, []);

  const filtered = useMemo(() => {
    if (!data) return [];
    let list = data.people;

    // Search
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          (p.name_latin && p.name_latin.toLowerCase().includes(q)),
      );
    }

    // Role filter
    if (roleFilter) {
      list = list.filter((p) => p.role === roleFilter);
    }

    // Relationship filter
    if (relFilter === 'senders') {
      list = list.filter((p) => p.sent_count > 0);
    } else if (relFilter === 'recipients') {
      list = list.filter((p) => p.received_count > 0);
    } else if (relFilter === 'mentioned') {
      list = list.filter((p) => p.mentioned_count > 0);
    }

    // Sort
    if (sortKey === 'letters') {
      list = [...list].sort(
        (a, b) =>
          b.sent_count + b.received_count - (a.sent_count + a.received_count),
      );
    } else if (sortKey === 'name') {
      list = [...list].sort((a, b) => a.name.localeCompare(b.name));
    } else if (sortKey === 'mentioned') {
      list = [...list].sort((a, b) => b.mentioned_count - a.mentioned_count);
    }

    return list;
  }, [data, search, roleFilter, relFilter, sortKey]);

  if (!data) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <Breadcrumbs segments={[{ label: 'People' }]} />
        <div className="animate-pulse mt-8 space-y-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="h-10 bg-theme-surface rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6">
      <Breadcrumbs segments={[{ label: 'People' }]} />

      <header className="pt-8 pb-6">
        <h1
          className="text-3xl sm:text-4xl tracking-tight"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          People
        </h1>
        <p className="mt-3 text-theme-muted max-w-2xl leading-relaxed">
          {data.people.length.toLocaleString()} individuals from the late Roman
          world — letter writers, recipients, and those mentioned within.
          Unlike{' '}
          <a href="/authors" className="text-theme-accent hover:underline">
            Authors
          </a>
          , this page includes people who never sent or received a letter but
          appear in the correspondence of others.
        </p>
      </header>

      {/* Controls */}
      <div className="sticky top-0 z-10 bg-[var(--color-bg)] pb-4 pt-2 border-b border-theme mb-4 flex flex-wrap gap-3 items-center">
        {/* Search */}
        <input
          type="text"
          placeholder="Search by name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-2 text-sm rounded-lg border border-theme bg-theme-surface text-theme-text placeholder:text-theme-muted focus:outline-none focus:border-[var(--color-accent)] w-full sm:w-56"
        />

        {/* Role filter */}
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="px-3 py-2 text-sm rounded-lg border border-theme bg-theme-surface text-theme-text focus:outline-none focus:border-[var(--color-accent)]"
        >
          <option value="">All roles</option>
          {data.roles.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>

        {/* Relationship filter */}
        <select
          value={relFilter}
          onChange={(e) => setRelFilter(e.target.value as RelFilter)}
          className="px-3 py-2 text-sm rounded-lg border border-theme bg-theme-surface text-theme-text focus:outline-none focus:border-[var(--color-accent)]"
        >
          <option value="all">All people</option>
          <option value="senders">Senders</option>
          <option value="recipients">Recipients</option>
          <option value="mentioned">Mentioned in letters</option>
        </select>

        {/* Sort */}
        <select
          value={sortKey}
          onChange={(e) => setSortKey(e.target.value as SortKey)}
          className="px-3 py-2 text-sm rounded-lg border border-theme bg-theme-surface text-theme-text focus:outline-none focus:border-[var(--color-accent)]"
        >
          <option value="letters">Most letters</option>
          <option value="name">Name A-Z</option>
          <option value="mentioned">Most mentioned</option>
        </select>

        {/* Result count */}
        <span className="text-xs text-theme-muted tabular-nums ml-auto">
          {filtered.length.toLocaleString()} result
          {filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Table */}
      <div className="pb-16">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-theme text-left text-theme-muted">
              <th className="pb-3 font-medium">Name</th>
              <th className="pb-3 font-medium hidden sm:table-cell">Role</th>
              <th className="pb-3 font-medium hidden md:table-cell">Dates</th>
              <th className="pb-3 font-medium hidden md:table-cell">
                Location
              </th>
              <th className="pb-3 font-medium text-right">Letters</th>
              <th className="pb-3 font-medium text-right">Mentioned</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-theme">
            {filtered.map((person) => {
              const total = person.sent_count + person.received_count;
              const dates =
                person.birth_year || person.death_year
                  ? `${person.birth_year ?? '?'}\u2013${person.death_year ?? '?'}`
                  : null;

              return (
                <tr key={person.id} className="group">
                  <td className="py-3 pr-4">
                    <Link
                      href={`/authors/${toSlug(person.name)}`}
                      className="text-theme-text group-hover:text-theme-accent transition-colors font-medium"
                    >
                      {person.name}
                    </Link>
                    {person.role && (
                      <span className="block text-xs text-theme-muted sm:hidden">
                        {person.role}
                      </span>
                    )}
                  </td>
                  <td className="py-3 pr-4 text-theme-muted hidden sm:table-cell">
                    {person.role ?? '\u2014'}
                  </td>
                  <td className="py-3 pr-4 text-theme-muted tabular-nums hidden md:table-cell">
                    {dates ?? '\u2014'}
                  </td>
                  <td className="py-3 pr-4 text-theme-muted hidden md:table-cell">
                    {person.location ?? '\u2014'}
                  </td>
                  <td className="py-3 text-right tabular-nums">
                    <span className="text-theme-accent font-medium">
                      {total}
                    </span>
                    {total > 0 && (
                      <span className="text-theme-muted ml-1 text-xs">
                        ({person.sent_count}s / {person.received_count}r)
                      </span>
                    )}
                  </td>
                  <td className="py-3 text-right tabular-nums">
                    {person.mentioned_count > 0 ? (
                      <span className="text-theme-text">
                        {person.mentioned_count}
                      </span>
                    ) : (
                      <span className="text-theme-muted">&mdash;</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {filtered.length === 0 && (
          <p className="text-center text-theme-muted py-12">
            No people match your filters.
          </p>
        )}
      </div>
    </div>
  );
}

'use client';

import Link from 'next/link';
import { Pagination } from './Pagination';

export interface LetterItem {
  id: number;
  /** collection slug */
  c: string;
  /** letter number */
  n: number;
  /** year approx */
  y?: number;
  /** sender name */
  s?: string;
  /** recipient name */
  r?: string;
  /** topics CSV */
  t?: string;
  /** quick summary */
  q?: string;
  /** distance km */
  d?: number;
  /** first English translation flag */
  f?: number;
}

interface Props {
  letters: LetterItem[];
  page: number;
  perPage: number;
  onPageChange: (page: number) => void;
  sort: string;
  onSortChange: (sort: string) => void;
}

const SORT_OPTIONS = [
  { value: 'date-asc', label: 'Date oldest first' },
  { value: 'date-desc', label: 'Date newest first' },
  { value: 'collection-asc', label: 'Collection A\u2013Z' },
  { value: 'sender-asc', label: 'Sender A\u2013Z' },
];

export function LetterList({ letters, page, perPage, onPageChange, sort, onSortChange }: Props) {
  const totalPages = Math.ceil(letters.length / perPage);
  const start = (page - 1) * perPage;
  const end = Math.min(start + perPage, letters.length);
  const visible = letters.slice(start, end);

  return (
    <div>
      {/* Results header */}
      <div className="flex items-center justify-between gap-4 mb-4">
        <p className="text-sm text-theme-muted">
          Showing{' '}
          <span className="font-medium text-theme-text">
            {letters.length === 0 ? 0 : start + 1}&ndash;{end}
          </span>{' '}
          of{' '}
          <span className="font-medium text-theme-text">
            {letters.length.toLocaleString()}
          </span>{' '}
          letters
        </p>
        <select
          value={sort}
          onChange={(e) => onSortChange(e.target.value)}
          className="text-sm rounded-md border border-theme bg-theme-surface text-theme-text
            px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]
            cursor-pointer"
          aria-label="Sort letters by"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Letter rows */}
      {letters.length === 0 ? (
        <div className="py-16 text-center">
          <p className="text-theme-muted">No letters match your filters.</p>
        </div>
      ) : (
        <div className="divide-y divide-[var(--color-border)]">
          {visible.map((letter) => (
            <Link
              key={letter.id}
              href={`/letters/${letter.c}/${letter.n}/`}
              className="group block py-3 hover:bg-theme-surface transition-colors -mx-3 px-3 rounded"
            >
              <div className="flex items-start gap-3 overflow-hidden">
                {/* Collection badge - hidden on mobile */}
                <span
                  className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                    bg-theme-surface border border-theme text-theme-muted whitespace-nowrap shrink-0"
                >
                  {letter.c.replace(/_/g, ' ')}
                </span>

                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline gap-2 flex-wrap">
                    <span className="text-sm font-medium group-hover:text-theme-accent transition-colors truncate">
                      {letter.s ?? 'Unknown'}
                      {' \u2192 '}
                      {letter.r ?? 'Unknown'}
                    </span>
                    {letter.y != null && (
                      <span className="text-xs text-theme-muted tabular-nums shrink-0">
                        ~{letter.y} AD
                      </span>
                    )}
                  </div>
                  {/* Collection on mobile */}
                  <p className="mt-0.5 text-xs text-theme-muted sm:hidden capitalize">
                    {letter.c.replace(/_/g, ' ')}
                  </p>
                  {letter.q && (
                    <p className="mt-0.5 text-sm text-theme-muted truncate">
                      {letter.q}
                    </p>
                  )}
                </div>

                {/* Letter number */}
                <span className="text-xs text-theme-muted tabular-nums shrink-0">
                  #{letter.n}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Pagination */}
      <Pagination page={page} totalPages={totalPages} onPageChange={onPageChange} />
    </div>
  );
}

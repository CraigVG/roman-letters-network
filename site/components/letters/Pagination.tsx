'use client';

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

function getPageNumbers(current: number, total: number): (number | 'ellipsis')[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  const pages: (number | 'ellipsis')[] = [];

  // Always show first page
  pages.push(1);

  // Determine range around current page
  const rangeStart = Math.max(2, current - 1);
  const rangeEnd = Math.min(total - 1, current + 1);

  if (rangeStart > 2) {
    pages.push('ellipsis');
  }

  for (let i = rangeStart; i <= rangeEnd; i++) {
    pages.push(i);
  }

  if (rangeEnd < total - 1) {
    pages.push('ellipsis');
  }

  // Always show last page
  pages.push(total);

  return pages;
}

export function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  const pages = getPageNumbers(page, totalPages);

  return (
    <nav
      className="flex items-center justify-center gap-1 mt-8"
      aria-label="Pagination"
    >
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="px-3 py-2 text-sm rounded-md border border-theme text-theme-muted
          hover:bg-theme-surface hover:text-theme-accent transition-colors
          disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent
          disabled:hover:text-theme-muted"
        aria-label="Previous page"
      >
        &lsaquo; Prev
      </button>

      {pages.map((p, i) =>
        p === 'ellipsis' ? (
          <span
            key={`ellipsis-${i}`}
            className="px-2 py-2 text-sm text-theme-muted select-none"
            aria-hidden="true"
          >
            &hellip;
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            disabled={p === page}
            aria-current={p === page ? 'page' : undefined}
            className={`px-3 py-2 text-sm rounded-md border transition-colors ${
              p === page
                ? 'border-[var(--color-accent)] bg-[var(--color-accent)] text-white font-medium cursor-default'
                : 'border-theme text-theme-muted hover:bg-theme-surface hover:text-theme-accent'
            }`}
          >
            {p}
          </button>
        ),
      )}

      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="px-3 py-2 text-sm rounded-md border border-theme text-theme-muted
          hover:bg-theme-surface hover:text-theme-accent transition-colors
          disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent
          disabled:hover:text-theme-muted"
        aria-label="Next page"
      >
        Next &rsaquo;
      </button>
    </nav>
  );
}

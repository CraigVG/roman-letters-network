import Link from 'next/link';

interface BreadcrumbSegment {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  segments: BreadcrumbSegment[];
}

export function Breadcrumbs({ segments }: BreadcrumbsProps) {
  return (
    <nav aria-label="Breadcrumb" className="py-3">
      <ol className="flex items-center gap-1.5 text-sm text-theme-muted">
        <li>
          <Link
            href="/"
            className="hover:text-theme-text transition-colors"
          >
            Home
          </Link>
        </li>
        {segments.map((segment, i) => (
          <li key={i} className="flex items-center gap-1.5">
            <span className="text-theme-muted/50" aria-hidden="true">
              &rsaquo;
            </span>
            {segment.href ? (
              <Link
                href={segment.href}
                className="hover:text-theme-text transition-colors"
              >
                {segment.label}
              </Link>
            ) : (
              <span className="text-theme-text">{segment.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

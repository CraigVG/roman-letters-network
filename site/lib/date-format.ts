export function formatYear(year: number | null | undefined): string | null {
  if (year == null || !Number.isFinite(year)) return null;
  if (year < 0) return `${Math.abs(year)} BC`;
  if (year > 0) return `${year} AD`;
  return '0';
}

export function formatApproxYear(year: number | null | undefined): string | null {
  const formatted = formatYear(year);
  return formatted ? `c. ${formatted}` : null;
}

export function formatYearRange(
  startYear: number | null | undefined,
  endYear: number | null | undefined,
): string | null {
  if (startYear == null && endYear == null) return null;

  if (startYear == null) {
    const end = formatYear(endYear);
    return end ? `?-${end}` : null;
  }

  if (endYear == null) {
    const start = formatYear(startYear);
    return start ? `${start}-?` : null;
  }

  if (startYear === endYear) return formatYear(startYear);

  if (startYear < 0 && endYear < 0) {
    return `${Math.abs(startYear)}-${Math.abs(endYear)} BC`;
  }

  if (startYear > 0 && endYear > 0) {
    return `${startYear}-${endYear} AD`;
  }

  const start = formatYear(startYear);
  const end = formatYear(endYear);
  return start && end ? `${start}-${end}` : null;
}

const DATE_RANGE_LABEL = '66 BC-817 AD';

export const CORPUS = {
  title: `Roman Letters: Latin and Greek Correspondence, ${DATE_RANGE_LABEL}`,
  shortTitle: 'Roman Letters',
  dateRangeLabel: DATE_RANGE_LABEL,
  temporalCoverage: '66 BC/817 AD',
  description:
    `Latin and Greek correspondence from the Roman world, ${DATE_RANGE_LABEL}, with modern English translations, source links, and network metadata.`,
  totalLetters: 9471,
  totalCollections: 70,
  totalAuthors: 2935,
  modernEnglishTranslations: 8309,
  firstEnglishTranslations: 3546,
  originalTextAvailable: 7748,
  sourceLinksAvailable: 9198,
  distanceDataLetters: 4309,
  carrierMentions: 539,
  datasetVersion: 'v2.2.34',
  datasetDate: '2026-05-27',
  doi: '10.5281/zenodo.19142059',
  githubUrl: 'https://github.com/CraigVG/roman-letters-network',
};

export function formatCount(value: number) {
  return value.toLocaleString('en-US');
}

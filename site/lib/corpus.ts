export const CORPUS = {
  title: 'Roman Letters: Latin and Greek Correspondence, 100-800 AD',
  shortTitle: 'Roman Letters',
  description:
    'Latin and Greek correspondence from the Roman world, 100-800 AD, with modern English translations, source links, and network metadata.',
  totalLetters: 8112,
  totalCollections: 60,
  totalAuthors: 1888,
  firstEnglishTranslations: 3123,
  originalTextAvailable: 6155,
  sourceLinksAvailable: 7839,
  distanceDataLetters: 5751,
  carrierMentions: 460,
  datasetVersion: 'v2.1.0',
  datasetDate: '2026-03-20',
  doi: '10.5281/zenodo.19142059',
  githubUrl: 'https://github.com/CraigVG/roman-letters-network',
};

export function formatCount(value: number) {
  return value.toLocaleString('en-US');
}

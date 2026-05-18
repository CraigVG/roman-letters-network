export const CORPUS = {
  title: 'Roman Letters: Latin and Greek Correspondence, 100-800 AD',
  shortTitle: 'Roman Letters',
  description:
    'Latin and Greek correspondence from the Roman world, 100-800 AD, with modern English translations, source links, and network metadata.',
  totalLetters: 7049,
  totalCollections: 54,
  totalAuthors: 1850,
  firstEnglishTranslations: 3068,
  originalTextAvailable: 4263,
  sourceLinksAvailable: 6693,
  distanceDataLetters: 5863,
  carrierMentions: 478,
  datasetVersion: 'v1.0.0',
  datasetDate: '2026-03-20',
  doi: '10.5281/zenodo.19142059',
  githubUrl: 'https://github.com/CraigVG/roman-letters-network',
};

export function formatCount(value: number) {
  return value.toLocaleString('en-US');
}

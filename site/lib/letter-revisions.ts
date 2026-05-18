import type { LetterFull } from './letters';
import { CORPUS } from './corpus';
import { getSourceLabel } from './provenance';

export interface LetterRevision {
  version: string;
  date: string;
  summary: string;
  fields: string;
  source: string;
}

const KNOWN_REVISIONS: Record<string, LetterRevision[]> = {
  'pliny_younger:1015': [
    {
      version: '2026-05-18-hn-pliny-1015',
      date: '2026-05-18',
      summary:
        'Identified Septicius as Gaius Septicius Clarus and added context for the Roman delicacy translated as sow\'s matrices.',
      fields: 'recipient metadata, contextual note',
      source: 'Hacker News feedback; Pliny Epistulae I.15 source check',
    },
  ],
};

function keyFor(letter: LetterFull) {
  return `${letter.collection}:${letter.letter_number}`;
}

export function getLetterRevisions(letter: LetterFull): LetterRevision[] {
  const seeded = KNOWN_REVISIONS[keyFor(letter)] ?? [];
  return [
    ...seeded,
    {
      version: `${CORPUS.datasetVersion}-import`,
      date: CORPUS.datasetDate,
      summary: `Initial corpus import from ${getSourceLabel(letter)}.`,
      fields: 'letter text, metadata, source links',
      source: letter.source_url ?? letter.scan_url ?? 'project source import',
    },
  ];
}

export function getPublishedRevisionSummaries(): LetterRevision[] {
  return Object.values(KNOWN_REVISIONS)
    .flat()
    .sort((a, b) => b.date.localeCompare(a.date));
}

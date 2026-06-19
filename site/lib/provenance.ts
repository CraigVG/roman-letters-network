import {
  getLetterDisplayNumber,
  getLetterHref,
  type LetterFull,
  type CollectionInfo,
} from './letters';

const PUBLIC_DOMAIN_TRANSLATION_SOURCES: Record<string, string> = {
  existing: 'Public-domain English translation',
  existing_newadvent: 'Public-domain English translation modernized for readability',
  existing_tertullian: 'Public-domain English translation modernized for readability',
  existing_fordham: 'Public-domain English translation modernized for readability',
  existing_celt: 'Public-domain English translation modernized for readability',
  existing_attalus: 'Public-domain English translation',
  existing_livius: 'Public-domain English translation',
  existing_rogerpearse: 'Public-domain English translation',
  existing_haines: 'Public-domain English translation',
  gutenberg_winstedt: 'Public-domain English translation',
  topostext_shuckburgh_repair_v1: 'Public-domain English translation',
  'Gummere (Loeb Classical Library, 1917-25)': 'Public-domain English translation',
  existing_kalvesmaki_evagrius_2014: 'CC BY 4.0 English translation',
};

const SOURCE_LABELS: Record<string, string> = {
  existing: 'Public-domain scholarly source',
  existing_newadvent: 'New Advent / NPNF',
  existing_tertullian: 'Tertullian.org',
  existing_fordham: 'Fordham Medieval Sourcebook',
  existing_celt: 'CELT',
  existing_attalus: 'Attalus.org',
  existing_livius: 'Livius.org',
  existing_rogerpearse: 'Roger Pearse / Tertullian.org',
  existing_haines: 'Haines public-domain edition',
  gutenberg_winstedt: 'Project Gutenberg / Winstedt',
  topostext_shuckburgh_repair_v1: 'ToposText / Shuckburgh',
  'Gummere (Loeb Classical Library, 1917-25)': 'Gummere, Loeb Classical Library',
  existing_kalvesmaki_evagrius_2014: 'Kalvesmaki 2014 / TAN-Evagrius',
  ai_translated: 'AI-assisted translation from original text',
  seeck_ocr_ia: 'Seeck edition OCR from Internet Archive',
  pg78_ocr: 'Patrologia Graeca 78 OCR',
  latin_only: 'Original-language source text',
  none: 'Unreviewed source import',
  pending: 'Pending source review',
  needs_translation: 'Needs translation review',
};

export interface TextProvenance {
  translationLabel: string;
  sourceLabel: string;
  sourceType: string;
  originalStatus: string;
  reviewStatus: string;
  primarySourceUrl: string | null;
  issueUrl: string;
}

function normalizedSource(letter: LetterFull) {
  return (letter.translation_source ?? '').trim();
}

function hasTranslation(letter: LetterFull) {
  return Boolean(letter.modern_english?.trim() || letter.english_text?.trim());
}

function sourceLooksOcr(letter: LetterFull, sourceUrl: string | null) {
  const source = normalizedSource(letter).toLowerCase();
  const url = (sourceUrl ?? '').toLowerCase();
  return (
    source.includes('ocr') ||
    source.includes('pg78') ||
    url.includes('archive.org') ||
    url.includes('patrologia') ||
    url.includes('migne')
  );
}

export function getSourceLabel(letter: LetterFull) {
  const source = normalizedSource(letter);
  if (!source && letter.latin_text?.trim()) return 'Original-language source text';
  if (!source) return 'Unspecified import source';
  return SOURCE_LABELS[source] ?? source.replace(/_/g, ' ');
}

export function getTextProvenance(
  letter: LetterFull,
  collection?: CollectionInfo,
): TextProvenance {
  const source = normalizedSource(letter);
  const primarySourceUrl =
    letter.source_url ?? letter.scan_url ?? collection?.scan_url ?? null;
  const hasOriginal = Boolean(letter.latin_text?.trim());
  const hasEnglish = hasTranslation(letter);
  const isOcr = sourceLooksOcr(letter, primarySourceUrl);
  const isPublicDomainTranslation = Boolean(PUBLIC_DOMAIN_TRANSLATION_SOURCES[source]);

  const translationLabel = !hasEnglish
    ? 'No English translation available yet'
    : isPublicDomainTranslation
      ? PUBLIC_DOMAIN_TRANSLATION_SOURCES[source]
      : isOcr
        ? 'AI-assisted translation from OCR-derived source text'
        : 'AI-assisted modern English translation';

  const sourceType = isOcr
    ? 'Scanned edition / OCR-derived import'
    : primarySourceUrl
      ? 'Digital text source'
      : 'Source link pending';

  const originalStatus = hasOriginal
    ? 'Original Latin or Greek text available'
    : 'Original text not yet available in this corpus';

  const reviewStatus = !hasOriginal
    ? 'Needs original-text backfill'
    : !hasEnglish
      ? 'Original text imported; translation pending'
    : isOcr
      ? 'Needs transcription review'
      : isPublicDomainTranslation
        ? 'Existing translation source; not newly peer reviewed here'
        : 'Imported text; not peer reviewed here';

  return {
    translationLabel,
    sourceLabel: getSourceLabel(letter),
    sourceType,
    originalStatus,
    reviewStatus,
    primarySourceUrl,
    issueUrl: buildCorrectionIssueUrl(letter, primarySourceUrl),
  };
}

export function buildCorrectionIssueUrl(
  letter: LetterFull,
  primarySourceUrl: string | null = letter.source_url ?? letter.scan_url ?? null,
) {
  const displayNumber = getLetterDisplayNumber(letter);
  const title = `Correction: ${letter.collection} ${displayNumber}`;
  const pageUrl = `https://romanletters.org${getLetterHref(letter)}`;
  const body = [
    `Letter: ${letter.collection} ${displayNumber}`,
    `Page: ${pageUrl}`,
    `Current source: ${primarySourceUrl ?? 'none listed'}`,
    `Translation source: ${letter.translation_source ?? 'none listed'}`,
    '',
    'What should be corrected?',
    '',
    'What source or evidence supports the correction?',
    '',
  ].join('\n');

  const params = new URLSearchParams({
    template: 'correction.md',
    labels: 'correction',
    title,
    body,
  });

  return `https://github.com/CraigVG/roman-letters-network/issues/new?${params.toString()}`;
}

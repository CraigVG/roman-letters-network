// Single source of truth for which `translation_source` values count as pre-existing
// scholarly / public-domain human translations (as opposed to AI-assisted ones).
//
// Scholarly mode and the green/amber translation badge both key off this set, so it MUST
// stay in one place — previously it was duplicated in VersionTabs.tsx and
// ScholarlyModeContext.tsx and could silently drift. Any new AI source tag (e.g.
// `modern_<collection>_workflow_v1`) is deliberately NOT listed here, so it is treated as
// AI: amber badge, hidden in scholarly mode.

export const SCHOLARLY_SOURCES: ReadonlySet<string> = new Set([
  'existing',
  'existing_newadvent',
  'existing_tertullian',
  'existing_fordham',
  'existing_celt',
  'existing_attalus',
  'existing_livius',
  'existing_rogerpearse',
  'existing_haines',
  'gutenberg_winstedt',
  'topostext_shuckburgh_repair_v1',
  'Gummere (Loeb Classical Library, 1917-25)',
  'existing_kalvesmaki_evagrius_2014',
]);

export function isScholarlySource(source: string | null | undefined): boolean {
  return source != null && SCHOLARLY_SOURCES.has(source);
}

// For build-time SQL: a quoted, comma-separated list of the source values that count as
// pre-existing/human (the scholarly set PLUS '' to cover empty/untagged sources). Used in
// `... translation_source NOT IN (<list>)` "first-ever English translation" counts so those
// queries can never drift from the badge / scholarly-mode logic.
export function scholarlySourcesSqlList(): string {
  return ['', ...SCHOLARLY_SOURCES].map((s) => `'${s.replace(/'/g, "''")}'`).join(',');
}

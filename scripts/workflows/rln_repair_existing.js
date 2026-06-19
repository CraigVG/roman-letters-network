export const meta = {
  name: 'rln-repair-existing',
  description: 'Verify EXISTING translations against source; re-translate confirmed failures from the original; re-verify. Disk-as-truth, idempotent, throttled. No DB writes (a deterministic applier overwrites confirmed fixes afterward).',
  phases: [
    { title: 'Verify', detail: 'judge each existing translation against source' },
    { title: 'Retranslate', detail: 'Opus re-translates confirmed failures from the original' },
    { title: 'Reverify', detail: 'judge each re-translation against source' },
  ],
}

const A = typeof args === 'string' ? JSON.parse(args) : args
const DIR = A.dir              // /tmp/rln-review/<segment>
const IDMAP = A.idmap          // { id: collection }
const IDS = (A.ids && A.ids.length) ? A.ids : Object.keys(IDMAP).map(Number)

const FAIL_RETRANSLATABLE = ['FAIL_FABRICATION', 'FAIL_PARAPHRASE', 'FAIL_PERSON_NUMBER', 'FAIL_UNTRANSLATED', 'FAIL_HEADER']

const VERIFY_RULES = (id, kind) =>
`You are an adversarial reviewer of ${kind} modern-English translation of a Roman letter (id ${id}). Decide whether the translation is faithful to the source; CATCH fabrication, paraphrase, person/number errors, untranslated runs, headers. Default to a FAIL verdict if not trustworthy. Deliverable is a verdict FILE.

Step 0. IDEMPOTENCY: if ${DIR}/${kind === 'a RE-DONE' ? 'reverdict' : 'verdict'}/${id}.json already has a "verdict" key, stop.
Step 1. Read ${DIR}/src/${id}.json : "latin" (ORIGINAL source, Latin OR Greek), ${kind === 'a RE-DONE' ? `and the NEW translation from ${DIR}/tx/${id}.json (field "modern_english")` : '"modern_english" (the stored translation to judge)'}, collection, letter_number.
Step 2. The source field MAY be OCR-garbled or contain MORE THAN ONE letter concatenated or leading editorial apparatus. Judge whether the translation faithfully renders the LETTER CONTENT actually present. Length mismatch alone is NOT failure when explained by OCR noise / apparatus / concatenation.
Step 3. Verdict (one of): FAIL_FABRICATION (different topic / invented names/content), FAIL_PARAPHRASE (drops real content of this letter / summarizes / far too short unexplained), FAIL_PERSON_NUMBER (plural "we/us" rendered singular etc.), FAIL_UNTRANSLATED (large Greek/Latin runs left), FAIL_HEADER (From:/To:/Date: blocks), FAIL_GARBLED_SOURCE (source too OCR-garbled/wrong-language to trust — a SOURCE problem, re-translation cannot fix), PASS.
Step 4. Write ${DIR}/${kind === 'a RE-DONE' ? 'reverdict' : 'verdict'}/${id}.json (Write tool): {"id": ${id}, "verdict": "<one>", "issues": ["specific source-word vs translation-word evidence"], "source_is_concatenated": <bool>, "source_is_garbled": <bool>}. Ensure it is written and valid.`

phase('Verify')
const CHUNK = 10
const chunks = []
for (let i = 0; i < IDS.length; i += CHUNK) chunks.push(IDS.slice(i, i + CHUNK))

for (let pass = 1; pass <= 1; pass++) {
  for (const ch of chunks) {
    await parallel(ch.map((id) => () => agent(VERIFY_RULES(id, 'an EXISTING'),
      { label: `verify:${IDMAP[id]}:${id}`, phase: 'Verify', model: 'sonnet' })))
  }
}

// Read which ones failed (and are retranslatable) — but the workflow can't read files.
// Instead, the RETRANSLATE agents are launched for ALL ids and self-skip when the verdict is PASS
// or FAIL_GARBLED_SOURCE or a tx already exists. This keeps the workflow file-driven.

phase('Retranslate')
for (let pass = 1; pass <= 1; pass++) {
  for (const ch of chunks) {
    await parallel(ch.map((id) => () => {
      const col = IDMAP[id]
      return agent(
`Conditionally re-translate ONE Roman letter (id ${id}, collection ${col}). Deliverable is a file — OR doing nothing if not needed.

Step 0. Read ${DIR}/verdict/${id}.json . If verdict is "PASS" or "FAIL_GARBLED_SOURCE", DO NOTHING and stop (PASS needs no fix; garbled source cannot be fixed by re-translation). If ${DIR}/tx/${id}.json already has "modern_english">50 chars, stop (already redone).
Step 1. Otherwise read ${DIR}/src/${id}.json ("latin" = ORIGINAL, Latin or Greek) and note the verdict "issues" (the specific defect to fix).
Step 2. Translate the letter FRESH from the original, fixing the named defect. Rules: faithful to source, every sentence corresponds to the source, NO rearranging/omitting/paraphrasing/inventing. PRESERVE person/number exactly (epistolary plural "we/us/our" stays plural). Translate ALL Greek and Latin into English (no leftover runs). Output ONLY the letter text — no From:/To:/Date: headers, no commentary. Brief factual [bracket] glosses allowed at first mention. If the source is partly OCR-garbled, translate the legible content and mark genuine gaps [...]; NEVER fabricate. Collection ${col}: late-antique/Roman letter — match its register; render Latin/Greek honorifics and titles in English.
Step 3. Write ${DIR}/tx/${id}.json (Write tool): {"id": ${id}, "letter_number": <from src>, "modern_english": "<translation>", "source_proper_names": [...], "source_topic": "<one sentence>"}.`,
        { label: `retx:${col}:${id}`, phase: 'Retranslate' }
      )
    }))
  }
}

phase('Reverify')
for (let pass = 1; pass <= 1; pass++) {
  for (const ch of chunks) {
    await parallel(ch.map((id) => () => agent(
`Re-verify a RE-DONE translation (id ${id}) — but only if one exists.
Step 0. If ${DIR}/tx/${id}.json does NOT exist or has no "modern_english">50 chars, DO NOTHING and stop (this letter was not re-translated). If ${DIR}/reverdict/${id}.json already has a "verdict", stop.
` + VERIFY_RULES(id, 'a RE-DONE').split('\n').slice(1).join('\n'),
      { label: `reverify:${IDMAP[id]}:${id}`, phase: 'Reverify', model: 'sonnet' })))
  }
}

return { processed: IDS.length, dir: DIR }

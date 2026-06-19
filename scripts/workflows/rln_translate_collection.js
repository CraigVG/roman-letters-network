export const meta = {
  name: 'rln-translate-collection',
  description: 'Translate one collection’s untranslated letters from the original text with adversarial source-fidelity verification, then write only verified rows to the DB and run the validation cascade. Disk-as-truth: agents write files, idempotent and resumable.',
  phases: [
    { title: 'Translate', detail: 'translate each letter from the original to a tx json file (idempotent)' },
    { title: 'Verify', detail: 'independently verify fidelity to source, write verdict files (idempotent)' },
    { title: 'Apply', detail: 'serial DB write of verified rows + validation cascade' },
  ],
}

// args = { collection, ids:[...], source_tag, voice, has_english19c:bool }
const A = typeof args === 'string' ? JSON.parse(args) : args
const REPO = '/Users/craigvandergalien/Documents/GitHub/roman-letters-network'
const COLLECTION = A.collection
const IDS = Array.isArray(A.ids) ? A.ids : JSON.parse(A.ids)
const TX_SOURCE = A.source_tag
const VOICE = A.voice
const SRC_DIR = `/tmp/rln-tx/${COLLECTION}`
const HAS_E19 = !!A.has_english19c

const TRANSLATE_RULES = `You are a specialist translator of Latin and Greek letters (late Republic through the medieval Roman world) producing scholarly-quality modern English. CORE PRINCIPLE: FIDELITY TO THE SOURCE. Your translation must read like a published scholarly translation. Every sentence in your output must correspond to a sentence in the original. Do NOT rearrange, omit, paraphrase, summarize, or add material not in the original.
RULES:
1. Translate from the ORIGINAL text (the "latin" field, which may be Latin OR Greek).${HAS_E19 ? ' The 19th-century English ("english19c") is a meaning guide ONLY — do not copy its archaic phrasing; produce fresh modern English.' : ' There is NO English crib — translate carefully and conservatively directly from the original; if a passage is genuinely unreadable mark it [...] rather than guessing.'}
2. PRESERVE exact person and number. THIS IS THE #1 SOURCE OF ERRORS — check every main verb. Latin/Greek epistolary style routinely uses the FIRST PERSON PLURAL ("we") where English would say "I"; you MUST keep it plural. "rogamus"=we ask (never "I ask"); "scripsimus"=we have written; "misimus"=we have sent; "avemus/cupimus"=we long/wish; "nos"=we/us; "nobiscum"=with us; "noster/nostra"=our. Do NOT collapse any plural verb or pronoun to the singular for "naturalness." If the Latin verb ends in -mus or the pronoun is nos/nobis, render "we/us/our".
3. PRESERVE specific vocabulary; do not soften ("danger of betrayal" not "feels like betrayal").
4. PRESERVE sentence order and the author's rhetorical structure. Break a sentence only when truly unreadable.
5. Mention every proper name the original mentions. Discuss the same topics the original discusses.
6. Output ONLY the translated letter text — optionally led by a SINGLE recipient-address heading line that renders the letter's address (e.g. "To Peter the Presbyter."), which is the expected scholarly convention for these collections. Do NOT add multi-field metadata blocks ("From:"/"Date:"/"Subject:"/"Context:" lines), NO commentary, NO summary.
7. Add brief [bracketed] factual context notes only at first mention of a term/name a modern reader could not know (a few words, never a full clause of interpretation). Use scholarly honorific renderings (e.g. beatitudo vestra = "Your Beatitude"). Do NOT add interpretive commentary, arguments, or claims not in the source — only a terse identifying gloss.
8. TRANSLATE EVERYTHING into English. Many of these letters are bilingual (e.g. a Latin letter with embedded Greek quotations, or vice versa). Translate ALL embedded Greek AND Latin into English — leave NO untranslated Greek or Latin runs of any length (not even short tags like "miles gloriosus"). You may note [originally in Greek] once at first occurrence if helpful, but the words themselves must be rendered in English.
9. If the source is fragmentary or OCR-damaged, translate what is present and mark genuinely illegible gaps as [...]; NEVER fabricate to fill a gap.
AUTHOR VOICE: ${VOICE}`

const txPrompt = (id) =>
`Translate ONE Roman letter (collection ${COLLECTION}, id ${id}) from its original text to scholarly modern English, and WRITE the result to a file. There is no structured output — your deliverable is the file.

Step 0. IDEMPOTENCY: first check whether ${SRC_DIR}/tx/${id}.json already exists and contains a "modern_english" string longer than 50 characters (use: cat ${SRC_DIR}/tx/${id}.json). If it already does, do nothing and stop — it is already done.
Step 1. Read the source file: ${SRC_DIR}/src/${id}.json (fields: id, letter_number, year, latin [the ORIGINAL, Latin or Greek], english19c, sender, recipient).
Step 2. Translate the "latin" field following these rules EXACTLY:
${TRANSLATE_RULES}
Step 3. Write valid JSON to ${SRC_DIR}/tx/${id}.json (use the Write tool) with keys:
  - "id": ${id}
  - "letter_number": (from source)
  - "modern_english": your full translation (string)
  - "source_proper_names": array of every proper name (people/places) in the original
  - "source_topic": one-sentence summary of what the original letter is actually about

CRITICAL: Only translate id ${id}. Read the actual original text before translating. Never invent content from the letter number. The file is the only thing that matters — make sure it is written and valid before you finish.`

const verifyPrompt = (id) =>
`You are an adversarial fidelity checker for ONE translated Roman letter (collection ${COLLECTION}, id ${id}). CATCH fabrication and paraphrase; do not be agreeable. Default to FAIL if uncertain. Your deliverable is a verdict FILE.

Step 0. IDEMPOTENCY: if ${SRC_DIR}/verdict/${id}.json already exists with a "verdict" key, stop — already done.
Step 1. Confirm the translation exists: read ${SRC_DIR}/tx/${id}.json . If it is MISSING or has no "modern_english" longer than 50 chars, do NOT write any verdict file — just stop (a later retry pass will translate it, and the missing verdict signals "not done yet").
Step 2. Read the source independently: ${SRC_DIR}/src/${id}.json (use the "latin" field = the original).
Step 3. Check the translation against the ORIGINAL (not the english19c crib):
  (a) NAMES: every proper name in the original appears in modern_english (correctly — a substituted/wrong name like writing "Capito" for "Atticus" => FAIL); invented names => FAIL.
  (b) TOPIC: same subject as the original; a different topic => FAIL (fabrication signature).
  (c) LENGTH: len(modern_english) >= 25% of len(original); far shorter => FAIL (paraphrase).
  (d) HEADERS: a SINGLE recipient-address heading line (e.g. "To Peter the Presbyter." or "To the same person.") is EXPECTED and ALLOWED by the translation spec — do NOT fail it. FAIL only for genuine AI metadata: a "From:"/"Date:"/"Subject:"/"Context:" line, or a multi-field sender/date metadata block.
  (e) PERSON/NUMBER: first/second/third person and singular/plural MUST match the original. A "we"->"I" (or singular<->plural) shift => FAIL. This is the most common real defect — check the verbs.
  (f) LANGUAGE: output is fully English. ANY untranslated Greek or Latin run, even a short phrase or tag (e.g. "miles gloriosus", or a Greek quotation), => FAIL.
  (g) NOT TEMPLATED: a unique translation, not boilerplate.
  (h) BRACKETED NOTES ARE ALLOWED: brief factual [context] glosses at first mention (e.g. "[the imperial villa]", "[Herodes Atticus, the Greek orator]") are PERMITTED by the translation rules and are NOT fabrication — do NOT fail for these. Only fail (b)-style if a bracket adds a substantive CLAIM or ARGUMENT not in the source, or if untracked content materially changes meaning.
Step 4. Write ${SRC_DIR}/verdict/${id}.json (Write tool) with keys: id (${id}), verdict ("PASS" or "FAIL"), issues (array of specific problems; empty if PASS). Make sure the file is written and valid before finishing.`

// Throttle to avoid API rate limiting: process in small sequential chunks,
// interleaving Opus translate + Sonnet verify so the token-rate limiter recovers between bursts.
// Two passes over all chunks so a rate-limited id gets a second attempt (idempotent skips the done ones).
const CHUNK = 8
const chunks = []
for (let i = 0; i < IDS.length; i += CHUNK) chunks.push(IDS.slice(i, i + CHUNK))

for (let pass = 1; pass <= 2; pass++) {
  phase(pass === 1 ? 'Translate' : 'Translate (retry)')
  for (const ch of chunks) {
    await parallel(ch.map((id) => () => agent(txPrompt(id), { label: `tx:${id}`, phase: pass === 1 ? 'Translate' : 'Translate (retry)' })))
    await parallel(ch.map((id) => () => agent(verifyPrompt(id), { label: `verify:${id}`, phase: 'Verify', model: 'sonnet' })))
  }
}

// NOTE: Apply + validation is intentionally NOT done by an agent here.
// The DB write is performed deterministically by the orchestrator via
// scripts/apply_workflow_translations.py after this workflow completes, so the
// critical serial write never depends on a flaky StructuredOutput call.
// This workflow's job is only to produce verified tx/ + verdict/ files on disk.

log(`${COLLECTION}: translate+verify complete. Apply with: python3 scripts/apply_workflow_translations.py ${COLLECTION} ${TX_SOURCE}`)

return { collection: COLLECTION, requested: IDS.length, src_dir: SRC_DIR, source_tag: TX_SOURCE }

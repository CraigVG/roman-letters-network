export const meta = {
  name: 'rln-retranslate-all',
  description: 'Re-translate EVERY given letter fresh from the original (mixed collections), then adversarially verify the new translation. Overwrites legacy translations. Disk-as-truth, idempotent, throttled.',
  phases: [
    { title: 'Translate', detail: 'Opus re-translates each letter fresh from the original' },
    { title: 'Verify', detail: 'Sonnet judges each new translation against source' },
  ],
}

const A = typeof args === 'string' ? JSON.parse(args) : args
const DIR = A.dir              // /tmp/rln-review/<segment>
const IDMAP = A.idmap          // { id: collection }
const IDS = (A.ids && A.ids.length) ? A.ids : Object.keys(IDMAP).map(Number)

const CHUNK = 5
const chunks = []
for (let i = 0; i < IDS.length; i += CHUNK) chunks.push(IDS.slice(i, i + CHUNK))

phase('Translate')
for (let pass = 1; pass <= 3; pass++) {  // 3 passes: pass 2 fills rate-limited stragglers (idempotent skip)
  for (const ch of chunks) {
    await parallel(ch.map((id) => () => {
      const col = IDMAP[id]
      return agent(
`Translate ONE Roman letter (id ${id}, collection ${col}) FRESH from its original text. Deliverable is a file.

Step 0. IDEMPOTENCY: if ${DIR}/tx/${id}.json already has "modern_english">50 chars, stop.
Step 1. Read ${DIR}/src/${id}.json — field "latin" is the ORIGINAL (Latin OR Greek). (Ignore any "modern_english" field there; it is a known-suspect legacy translation you are REPLACING — do not copy it.)
Step 2. Translate faithfully into scholarly modern English: every sentence corresponds to a sentence in the original; NO rearranging, omitting, paraphrasing, summarizing, or inventing. PRESERVE person/number exactly — epistolary plural "we/us/our" (-mus verbs, nos/nobis) MUST stay plural, never "I". Translate ALL Greek AND Latin into English — leave NO untranslated run of any length. Output ONLY the letter text — no From:/To:/Date:/Context: headers, no commentary. Brief factual [bracket] glosses allowed at first mention; render Latin/Greek honorifics and titles in English. The source MAY be OCR-garbled or contain editorial apparatus or multiple concatenated letters — translate the legible letter content, mark genuine illegible gaps [...], and NEVER fabricate to fill a gap. Collection ${col}: match its late-antique/Roman register.
Step 3. Write ${DIR}/tx/${id}.json (Write tool): {"id": ${id}, "letter_number": <from src>, "modern_english": "<translation>", "source_proper_names": [...], "source_topic": "<one sentence>"}.`,
        { label: `tx:${col}:${id}`, phase: 'Translate' }
      )
    }))
  }
}

phase('Verify')
for (const ch of chunks) {
  await parallel(ch.map((id) => () => {
    const col = IDMAP[id]
    return agent(
`Adversarial fidelity check of a NEW translation (id ${id}, collection ${col}). CATCH fabrication/paraphrase; default FAIL if uncertain. Deliverable is a verdict FILE.

Step 0. IDEMPOTENCY: if ${DIR}/verdict/${id}.json already has a "verdict", stop.
Step 1. If ${DIR}/tx/${id}.json is missing or has no "modern_english">50 chars, do NOT write a verdict (a retry will handle it); stop.
Step 2. Read source ${DIR}/src/${id}.json (field "latin" = ORIGINAL) and the new translation ${DIR}/tx/${id}.json.
Step 3. The source MAY be OCR-garbled / apparatus-padded / multi-letter concatenated — length mismatch alone is NOT failure when so explained. Verdict (one of): PASS; FAIL_FABRICATION (different topic / invented names/content); FAIL_PARAPHRASE (drops real content / summarizes / unexplained too-short); FAIL_PERSON_NUMBER (plural rendered singular etc.); FAIL_UNTRANSLATED (Greek/Latin runs left); FAIL_HEADER; FAIL_GARBLED_SOURCE (source too garbled/wrong-language to trust — re-translation can't fix, flag for re-OCR).
Step 4. Write ${DIR}/verdict/${id}.json (Write tool): {"id": ${id}, "verdict": "<one>", "issues": ["specific evidence"], "source_is_garbled": <bool>}.`,
      { label: `verify:${col}:${id}`, phase: 'Verify', model: 'sonnet' }
    )
  }))
}

return { processed: IDS.length, dir: DIR }

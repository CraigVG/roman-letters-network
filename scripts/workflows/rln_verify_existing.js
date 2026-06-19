export const meta = {
  name: 'rln-verify-existing',
  description: 'Adversarially verify EXISTING translations against their source to find fabrication/paraphrase/defects. Sonnet verifiers write verdict files. Disk-as-truth; measurement + triage, no DB writes.',
  phases: [
    { title: 'Verify', detail: 'judge each existing translation against its source' },
  ],
}

const A = typeof args === 'string' ? JSON.parse(args) : args
const DIR = A.dir            // e.g. /tmp/rln-review/pilot
const IDMAP = A.idmap        // { id: segment }
const IDS = (A.ids && A.ids.length) ? A.ids : Object.keys(IDMAP).map(Number)

phase('Verify')

const CHUNK = 10
const chunks = []
for (let i = 0; i < IDS.length; i += CHUNK) chunks.push(IDS.slice(i, i + CHUNK))

for (let pass = 1; pass <= 2; pass++) {
  for (const ch of chunks) {
    await parallel(ch.map((id) => () => agent(
`You are an adversarial reviewer of an EXISTING modern-English translation of a Roman letter (id ${id}). Your job: decide whether the stored translation is faithful to the source, and CATCH fabrication, paraphrase, and defects. Default to FAIL if the translation is not trustworthy. Your deliverable is a verdict FILE.

Step 0. IDEMPOTENCY: if ${DIR}/verdict/${id}.json already has a "verdict" key, stop.
Step 1. Read ${DIR}/src/${id}.json : fields "latin" (the ORIGINAL source — may be Latin OR Greek), "modern_english" (the stored translation to judge), collection, letter_number, segment.
Step 2. IMPORTANT context about the source field: it may be OCR-garbled (stray characters, broken words, footnote/apparatus noise) and it OCCASIONALLY contains MORE THAN ONE letter concatenated, or leading editorial headers/apparatus. Judge whether the translation faithfully renders the LETTER CONTENT that is actually present in the source — do NOT fail merely because the translation is shorter than a garbled/multi-letter/apparatus-padded source. Length mismatch alone is not a failure when explained by OCR noise, apparatus, or concatenation.
Step 3. Assign a verdict by these rules:
  - "FAIL_FABRICATION": the translation discusses a DIFFERENT topic than the source, names people/places NOT in the source, or invents content not supported by the source. (the worst defect)
  - "FAIL_PARAPHRASE": the translation drops substantial real content of THIS letter, summarizes instead of translates, or is far too short to cover the actual letter (not explained by OCR/apparatus/concatenation).
  - "FAIL_PERSON_NUMBER": systematic person/number errors (e.g. source plural "we/us" rendered singular "I/me").
  - "FAIL_UNTRANSLATED": large untranslated Greek/Latin runs left in the English.
  - "FAIL_HEADER": contains From:/To:/Date:/Context: metadata blocks.
  - "FAIL_GARBLED_SOURCE": the source is so OCR-garbled or wrong-language that the translation cannot be trusted and the letter needs source repair/re-OCR (note this — it is a source problem, not just a translation problem).
  - "PASS": the translation faithfully renders the letter content present in the source.
Step 4. Write ${DIR}/verdict/${id}.json (Write tool): {"id": ${id}, "verdict": "<one of the above>", "issues": ["specific evidence, citing source words vs translation words"], "source_is_concatenated": <true|false>, "source_is_garbled": <true|false>}.
Make sure the file is written and valid before finishing.`,
      { label: `verify:${IDMAP[id]}:${id}`, phase: 'Verify', model: 'sonnet' }
    )))
  }
}

return { verified: IDS.length, dir: DIR }

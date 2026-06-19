export const meta = {
  name: 'rln-repair-translations',
  description: 'Re-translate a mixed set of previously-failed Roman letters, injecting each letter’s prior verdict feedback so the specific defect is avoided, with adversarial re-verification. Disk-as-truth.',
  phases: [
    { title: 'Repair', detail: 'translate each failed letter avoiding its prior defect' },
    { title: 'Verify', detail: 'independently re-verify fidelity to source' },
  ],
}

const REP = '/tmp/rln-tx/_repair'
// args.idmap = { "<id>": "<collection>", ... } passed by the launcher (workflow cannot read files)
const A = typeof args === 'string' ? JSON.parse(args) : args
const IDMAP = A.idmap
const IDS = (A.ids && A.ids.length) ? A.ids : Object.keys(IDMAP).map(Number)

const VOICES = {
  cicero_atticus: "Cicero to Atticus: candid, witty, politically sharp late-Republican Latin. Preserve epistolary plural ('we' stays 'we') and every proper name EXACTLY.",
  fronto: "Fronto (Latin, some bilingual with Greek): warm rhetorician-to-imperial-pupil. Translate ALL embedded Greek into English. Preserve epistolary plural exactly.",
  ausonius: "Ausonius (late-4th-c Gallo-Roman poet): learned, playful verse/prose epistles. Preserve epistolary plural exactly; render verse as dignified English prose-poetry.",
  cicero_quintus: "Cicero to his brother Quintus: intimate family counsel + political advice, late-Republican Latin. Translate ALL Latin (no leftover Latin phrases). Preserve epistolary plural exactly.",
  symmachus: "Symmachus (late-4th-c senator, first-ever English): mannered Plinian elegance. Render ALL Latin office-titles/honorifics in English (vir clarissimus = 'a most distinguished man'; agens in rebus = 'an imperial courier-agent'; relatio = 'official report'; protectores = 'imperial guardsmen'; lustrum = 'five-year period'; unciae = 'twelfths'). For OCR-garbled gaps, mark [...] and NEVER fabricate. Preserve epistolary plural exactly.",
  theodore_studite: "Theodore the Studite (early-9th-c Greek, first-ever English): icon-defender abbot. Translate ALL Greek into English (no leftover Greek). Preserve epistolary/monastic plural exactly.",
}

const BASE_RULES = `Produce a scholarly-quality modern English translation faithful to the ORIGINAL. Every sentence must correspond to a sentence in the original; do not rearrange, omit, paraphrase, or invent. PRESERVE person/number exactly — Latin/Greek epistolary first-person PLURAL ("we/us/our": -mus verbs, nos/nobis, scripsimus, misimus, rogamus) MUST stay plural; never collapse to "I". Translate EVERYTHING into English — leave NO untranslated Greek or Latin run of any length (not even short tags). Output ONLY the translated letter text — no From:/To:/Date: headers, no commentary. Brief factual [bracketed] glosses at first mention are allowed but must add no claim absent from the source. For fragmentary/OCR-garbled source, translate what is legible and mark genuine gaps [...]; NEVER fabricate.`

phase('Repair')

const CHUNK = 8
const chunks = []
for (let i = 0; i < IDS.length; i += CHUNK) chunks.push(IDS.slice(i, i + CHUNK))

for (let pass = 1; pass <= 2; pass++) {
  for (const ch of chunks) {
    await parallel(ch.map((id) => () => {
      const col = IDMAP[id]
      const voice = VOICES[col] || 'Translate faithfully in modern English.'
      return agent(
`Re-translate ONE previously-FAILED Roman letter (id ${id}, collection ${col}) and WRITE the result to a file. Your deliverable is the file.

Step 0. IDEMPOTENCY: if ${REP}/tx/${id}.json already has "modern_english" longer than 50 chars, stop.
Step 1. Read the source: ${REP}/src/${id}.json (field "latin" = the original, Latin or Greek).
Step 2. Read the PRIOR DEFECT feedback: ${REP}/feedback/${id}.json (field "prior_issues"). The previous translation was REJECTED for exactly these problems. You MUST fix every one of them this time.
Step 3. Translate per these rules:
${BASE_RULES}
AUTHOR VOICE: ${voice}
Step 4. Write valid JSON to ${REP}/tx/${id}.json (Write tool): {"id": ${id}, "letter_number": <from source>, "modern_english": "<your translation>", "source_proper_names": [...], "source_topic": "<one sentence>"}.

CRITICAL: read the actual original AND the prior_issues before translating. Fix the named defects. Never fabricate.`,
        { label: `repair:${col}:${id}`, phase: 'Repair' }
      )
    }))
  }
}

phase('Verify')

for (const ch of chunks) {
  await parallel(ch.map((id) => () => {
    const col = IDMAP[id]
    return agent(
`Adversarial fidelity check for ONE re-translated Roman letter (id ${id}, collection ${col}). CATCH fabrication/paraphrase; default FAIL if uncertain. Deliverable is a verdict FILE.

Step 0. IDEMPOTENCY: if ${REP}/verdict/${id}.json already has a "verdict" key, stop.
Step 1. If ${REP}/tx/${id}.json is missing or has no modern_english>50 chars, do NOT write a verdict (a retry pass will handle it); stop.
Step 2. Read source ${REP}/src/${id}.json ("latin" = original) and the translation ${REP}/tx/${id}.json. Also read ${REP}/feedback/${id}.json to confirm the PRIOR defects are now fixed.
Step 3. FAIL if any: (a) a proper name in the original is missing or substituted; (b) different topic than the original; (c) modern_english < 25% of original length; (d) From:/To:/Date: headers present; (e) PERSON/NUMBER mismatch — any epistolary plural "we/us/our" collapsed to singular => FAIL; (f) ANY untranslated Greek or Latin run, even one short phrase => FAIL; (g) the prior_issues defect is NOT actually fixed => FAIL. Brief factual [bracket] glosses are ALLOWED (not fabrication) unless they add a claim absent from the source.
Step 4. Write ${REP}/verdict/${id}.json (Write tool): {"id": ${id}, "verdict": "PASS"|"FAIL", "issues": [...]}.`,
      { label: `verify:${col}:${id}`, phase: 'Verify', model: 'sonnet' }
    )
  }))
}

return { repaired: IDS.length, src_dir: REP }

export const meta = {
  name: 'rln-enrich-correspondents',
  description: 'Letter-grounded biographical enrichment of the major Nilus/Isidore correspondents. Each bio is built from the ACTUAL letters addressed to the person (primary evidence), then adversarially checked for fabrication. Honest "otherwise unattested" for obscure figures; never invents dates/offices/events. Disk-as-truth, idempotent, rate-limit resilient.',
  phases: [
    { title: 'Enrich', detail: 'letter-grounded bio + conservative geodata per correspondent' },
    { title: 'Verify', detail: 'adversarial fabrication check against the supplied letters' },
  ],
}

const A = typeof args === 'string' ? JSON.parse(args) : args
const DIR = '/tmp/rln-people-major'
const IDS = Array.isArray(A.ids) ? A.ids : JSON.parse(A.ids)
const CHUNK = 5

const enrichPrompt = (id) =>
`You are writing a scholarly biographical note for ONE person from a late-antique letter corpus, and WRITING it to a file. Your deliverable is the file. GROUND EVERYTHING IN THE SUPPLIED LETTERS — they are the primary evidence.

Step 0. IDEMPOTENCY: if ${DIR}/out/${id}.json already exists with a "bio" string > 60 chars, stop — done.
Step 1. Read ${DIR}/src/${id}.json. Fields: id, name, role_from_address (the honorific in the letter's address, may be null), sender (the letter-writer), collection, milieu (period/place context), letter_count, letters[] (the actual modern-English translations of letters addressed to this person — THE EVIDENCE).
Step 2. Write a biography GROUNDED in that evidence. RULES (this is the core of the task):
  - Build the bio from what the letters themselves reveal: the person's role/office (from the address honorific AND the letters' content), the topics the sender writes to them about, the nature and tenor of the relationship (e.g. a junior cleric repeatedly corrected, a learned friend, an official asked for favors, a monk given spiritual direction).
  - State plainly that the person is known chiefly/only as a correspondent of the sender, UNLESS this is an independently and famously attested historical figure (e.g. a reigning emperor, a major Church Father, the Gothic general Gainas) — in which case give the genuine well-known facts. When in doubt, treat as obscure.
  - HARD ANTI-FABRICATION RULE: do NOT invent birth/death dates, specific offices, careers, events, family, or relationships that are not either (a) evident in the supplied letters or (b) genuinely well-known history. "Otherwise unattested" is the correct, honest ending for most of these people. Confident fabrication is the worst possible outcome.
  - You MAY state the general period and region as context (from the milieu field) — e.g. "active in the early-5th-century Pelusium milieu" — since that follows from being this sender's correspondent. Phrase it as context, not as a documented fact about the individual.
  - Length: 2-4 sentences. Specific and readable where the letters support it; brief and honest where they do not.
Step 3. GEODATA — be conservative. The sender's city is NOT automatically the recipient's location (letters travel). Set "location" + lat/lon ONLY if the letters themselves place this person somewhere, OR they are a famous figure with a known seat. Otherwise location=null, lat=null, lon=null, location_confidence="unknown". For genuinely identifiable places use standard coords (Pelusium 31.04/32.54, Ancyra 39.93/32.86, Constantinople 41.01/28.98, Alexandria 31.20/29.92, Antioch 36.20/36.16).
Step 4. Write ${DIR}/out/${id}.json (Write tool), valid JSON, keys:
  - "id": ${id}
  - "bio": the note (string)
  - "role": short role/title grounded in the evidence (e.g. "deacon", "grammarian", "monk", "provincial official"; or "correspondent of ${'$'}{sender}")
  - "location": place name or null
  - "lat": number or null
  - "lon": number or null
  - "location_confidence": "strong" | "approximate" | "unknown"
  - "birth_year": integer or null — ONLY if genuinely known
  - "death_year": integer or null — ONLY if genuinely known
  - "attestation": "well_attested" | "obscure"
Make sure the file is written and valid before finishing. Use the person's name as given.`

const verifyPrompt = (id) =>
`You are an adversarial fact-checker for ONE biographical note. Your job is to CATCH fabrication. Default to FAILING if the bio asserts specifics that are not grounded in the supplied letters and are not genuinely well-known history. Your deliverable is a verdict FILE.

Step 0. IDEMPOTENCY: if ${DIR}/verdict/${id}.json already has a "verdict", stop.
Step 1. Read ${DIR}/out/${id}.json. If missing or "bio" <= 60 chars, do NOT write a verdict (stop; a retry will produce it).
Step 2. Read ${DIR}/src/${id}.json — the inputs and the actual letters (the only primary evidence available).
Step 3. Judge the bio against the evidence:
  (a) FABRICATION: does it assert any birth/death date, specific office/title, career step, event, place of origin, or family/relationship that is NOT supported by the supplied letters AND is not famous, independently-attested history for a clearly-identifiable major figure? Any such unsupported specific => FAIL_FABRICATION.
  (b) GEO: is a location/lat-lon asserted that the letters do not support (and the person is not a famous figure with a known seat)? Sender's-city assumed as recipient's location without letter support => FAIL_GEO.
  (c) ATTESTATION HONESTY: an obscure correspondent must be labeled attestation "obscure" and the bio must not read as if richly documented. Mislabeled => FAIL_FABRICATION.
  (d) Otherwise, if every specific is grounded in the letters or genuine well-known history, and obscurity is handled honestly => PASS.
Step 4. Write ${DIR}/verdict/${id}.json (Write tool): {"id": ${id}, "verdict": "PASS" | "FAIL_FABRICATION" | "FAIL_GEO", "issues": [specific problems; empty if PASS]}.`

phase('Enrich')
for (let pass = 1; pass <= 2; pass++) {
  for (let i = 0; i < IDS.length; i += CHUNK) {
    const ch = IDS.slice(i, i + CHUNK)
    await parallel(ch.map((id) => () => agent(enrichPrompt(id), { label: `enrich:${id}`, phase: 'Enrich' })))
  }
}

phase('Verify')
for (let i = 0; i < IDS.length; i += CHUNK) {
  const ch = IDS.slice(i, i + CHUNK)
  await parallel(ch.map((id) => () => agent(verifyPrompt(id), { label: `verify:${id}`, phase: 'Verify', model: 'sonnet' })))
}

return { processed: IDS.length, dir: DIR }

export const meta = {
  name: 'rln-enrich-people',
  description: 'Research each person (sender/recipient in the corpus) and produce a scholarly bio + geodata (location, lat/lon, dates, role). Honest about obscure figures; never fabricates biography. Disk-as-truth, idempotent, throttled.',
  phases: [
    { title: 'Enrich', detail: 'research each person -> bio + geodata file' },
    { title: 'Verify', detail: 'check each enrichment for fabrication / unsupported claims' },
  ],
}

const A = typeof args === 'string' ? JSON.parse(args) : args
const DIR = '/tmp/rln-people'
const IDS = A.ids

const CHUNK = 5
const chunks = []
for (let i = 0; i < IDS.length; i += CHUNK) chunks.push(IDS.slice(i, i + CHUNK))

phase('Enrich')
for (let pass = 1; pass <= 3; pass++) {
  for (const ch of chunks) {
    await parallel(ch.map((id) => () => agent(
`Research ONE person from the Roman Letters corpus (a sender or recipient of ancient/late-antique/medieval Roman letters) and write a structured enrichment file.

Step 0. IDEMPOTENCY: if ${DIR}/out/${id}.json already has a "bio" string >40 chars, stop.
Step 1. Read ${DIR}/src/${id}.json — fields: id, name, name_latin, role, location, lat, lon, birth_year, death_year, letters_sent, letters_received, collections (which letter collections this person appears in).
Step 2. Using your historical knowledge, produce an accurate, engaging, SCHOLARLY biography and geodata. CRITICAL ANTI-FABRICATION RULES:
  - If this is a well-attested historical figure (e.g. an emperor, Church Father, famous bishop, known senator), write a rich 2-4 sentence bio that conveys who they were, when they lived, their role, and why they matter — specific and lively, not generic.
  - If this is an OBSCURE figure known ONLY as a correspondent (e.g. "a recipient of several letters from Libanius", a minor official, a name attested only in this correspondence), DO NOT invent a biography. State honestly what is genuinely known: e.g. "Otherwise little attested; known chiefly as a correspondent of [author], probably a [inferred role] active in [place/period] based on the letters." Mark this clearly.
  - NEVER invent specific dates, offices, events, or relationships you do not actually know. Honest uncertainty beats confident fabrication.
  - Use the collections field as context for the person's likely period and milieu.
Step 3. Geodata: give the person's primary place of activity (city/region) and its modern lat/lon if you can identify it with reasonable confidence (these are well-known ancient places — Rome 41.89/12.49, Constantinople 41.01/28.98, Antioch 36.20/36.16, Alexandria 31.20/29.92, Milan 45.46/9.19, etc.). Set location_confidence: "strong" (historically established seat), "approximate" (reasonable inference), or "unknown" (cannot place — leave lat/lon null).
Step 4. Write ${DIR}/out/${id}.json (Write tool) with keys:
  - "id": ${id}
  - "bio": the biography text (string; for obscure figures, the honest brief note)
  - "role": short role/title (e.g. "bishop of Pavia", "praetorian prefect", "correspondent of Libanius")
  - "location": primary place name (string, or null)
  - "lat": number or null
  - "lon": number or null
  - "location_confidence": "strong" | "approximate" | "unknown"
  - "birth_year": integer or null (negative for BC) — only if genuinely known
  - "death_year": integer or null — only if genuinely known
  - "attestation": "well_attested" | "obscure"  (your honest assessment)
Make sure the file is valid JSON and written before finishing.`,
      { label: `enrich:${id}`, phase: 'Enrich' })))
  }
}

phase('Verify')
for (const ch of chunks) {
  await parallel(ch.map((id) => () => agent(
`Adversarially check ONE person-enrichment for fabrication. Default to FLAGGING if the bio asserts specific facts about an obscure figure that cannot be genuinely known.

Step 0. If ${DIR}/verdict/${id}.json already has a "verdict", stop.
Step 1. Read ${DIR}/src/${id}.json (the known inputs) and ${DIR}/out/${id}.json (the enrichment).
Step 2. Judge: Does the bio invent specific dates/offices/events/relationships for a figure who is only attested as a corpus correspondent? Does it confidently place someone whose location is genuinely unknown? Is the lat/lon plausible for the stated location? Is attestation honestly labeled?
  - PASS: bio is accurate for a known figure, OR is honestly hedged for an obscure one; geodata is plausible.
  - FAIL_FABRICATION: invents unsupported specifics for an obscure figure, or asserts false facts about a known one.
  - FAIL_GEO: lat/lon clearly wrong for the stated location, or confident coords on an unknown location.
Step 3. Write ${DIR}/verdict/${id}.json (Write tool): {"id": ${id}, "verdict": "PASS"|"FAIL_FABRICATION"|"FAIL_GEO", "issues": [...]}.`,
    { label: `verify:${id}`, phase: 'Verify', model: 'sonnet' })))
}

return { processed: IDS.length, dir: DIR }

# Next Phase: OCR Greek Letter Collections

## Overview
The Patrologia Graeca (Migne) contains massive letter collections that exist only as scanned PDFs on Internet Archive. Running OCR with Gemini on these volumes could add 3,000-4,000+ letters to the database.

## Volumes to OCR

### Priority 1: Isidore of Pelusium — PG vol. 78
- ~2,000 letters in Greek (5 books)
- 5th century Egyptian monk, contemporary of Cyril of Alexandria
- Most have NEVER been translated to English
- Archive.org: https://archive.org/details/PatrologiaGraeca (vol. 78)
- Also try: https://archive.org/details/Patrologia_Graeca_vol_078
- Columns 177-1645 of PG 78

### Priority 2: Nilus of Ancyra — PG vol. 79
- ~1,061 letters in Greek (4 books)
- 5th century monk of Cappadocia
- Authenticity disputed for some letters (may include Evagrius Ponticus excerpts)
- Columns 81-585 of PG 79

### Priority 3: John Chrysostom (remaining) — PG vol. 52
- ~230 letters total, we only have 12
- 4th-5th century, Archbishop of Constantinople, letters from exile
- One of the most important Church Fathers

## Process
1. Download PDF volumes from Internet Archive
2. Run Gemini OCR to extract Greek text
3. Parse individual letters (look for EPISTOLA headers with Greek numerals)
4. Store Greek text in the database (latin_text column works for Greek too)
5. Translate Greek→modern English using Claude agents
6. Assign dates, recipients, geolocations

## Notes
- Craig does OCR with Gemini at scale for DrillerDB, same pipeline applies here
- PG volumes have parallel Latin translations alongside Greek — OCR could capture both
- The PG layout has two columns per page — OCR needs to handle this
- Letter boundaries marked by "ΕΠΙΣΤΟΛΗ" + Greek numeral headers

## Quality Pass Required: Greek Translations

The Greek-source translations (Libanius, Isidore of Pelusium, and some Nilus/Chrysostom) need a quality review pass:

- **Isidore of Pelusium (630 letters)**: Early batches (1-130) are high quality with specific detail from the Greek. Later bulk translations (240-1155) are thematically accurate but formulaic — generated from Greek keyword analysis rather than close reading. These need individual attention.
- **Libanius (837 letters)**: Most translations are good quality from direct Greek reading. Some letters in the 500-837 range may have OCR artifacts from the First1KGreek XML that affected translation accuracy.
- **General Greek OCR issues**: The PG78 DjVu OCR has dual-column Latin/Greek text where columns sometimes bleed together. Some letter boundaries may be misidentified.

### Recommended approach for quality pass:
1. Priority: Isidore bulk translations (294 letters, batch 6+) — these are the most formulaic
2. Read each letter's Greek text and compare against the modern_english
3. Flag any where the translation doesn't match the actual Greek content
4. Re-translate flagged letters with closer attention to the source text

# Letter Corpus Expansion Plan

## Vision
The site narrative stays focused on late antiquity, but the database becomes the comprehensive corpus of ALL surviving Roman letters — from Cicero (68 BC) through the early medieval period (800 AD).

## Phase 1: Big Wins (existing translations available)

### 1A. Cicero (~813 letters, 68-43 BC)
- **Ad Atticum**: 426 letters in 16 books
- **Ad Familiares**: ~200 letters in 16 books
- **Ad Quintum Fratrem**: 27 letters in 3 books
- **Ad M. Brutum**: ~25 letters
- **Latin source**: The Latin Library (thelatinlibrary.com/cicero/)
- **English translation**: Project Gutenberg (Shuckburgh 1900, public domain)
- **Network value**: ENORMOUS — maps the entire Roman political elite (Pompey, Caesar, Brutus, Cato, Atticus, etc.)
- **Action**: Write scraper for Latin Library + Gutenberg, import with geographic/date metadata

### 1B. Seneca's Epistulae Morales (124 letters, 62-65 AD)
- **Latin source**: The Latin Library (thelatinlibrary.com/sen/)
- **English translation**: Gummere (Loeb 1917, public domain), available on Wikisource
- **Network value**: Moderate (all to one recipient, Lucilius)
- **Action**: Scrape Latin + English, import

### 1C. Fronto / Marcus Aurelius (~200 letters, 130-166 AD)
- **Latin source**: Archive.org (Haines Loeb 1919)
- **English translation**: Haines (Loeb 1919, public domain)
- **Network value**: HIGH — correspondence between emperor and tutor
- **Action**: Download Loeb PDFs from Archive.org, OCR if needed, import

### 1D. Chrysostom remaining exile letters (~230 letters)
- **Greek source**: PG vol. 52 (already have OCR pipeline)
- **English translation**: NPNF available on New Advent for some
- **Action**: Scrape New Advent for available translations, OCR PG52 for Greek, AI-translate remainder

### 1E. Cyril of Alexandria (~60 letters)
- **Source**: New Advent NPNF, PG vol. 77
- **Action**: Scrape New Advent translations, add Greek from PG77

### 1F. Ignatius of Antioch (7 letters, ~110 AD)
- **Source**: New Advent (ANF series)
- **Action**: Quick scrape + import

**Phase 1 Total: ~1,434 new letters**

## Phase 2: OCR Pipeline (Gemini 3)

### 2A. Nilus of Ancyra (~1,000 letters)
- Source: PG vol. 79 on Internet Archive
- Use existing Gemini OCR pipeline (updated to gemini-3-flash-preview)

### 2B. Chrysostom additional from PG52
- For letters not available on New Advent

### 2C. Evagrius Ponticus (~62 letters)
- Syriac/Greek fragments in PG

**Phase 2 Total: ~1,300 new letters**

## Phase 3: Scholarly Research Required

### 3A. Complete MGH Epistolae III
- Merovingian/Visigothic/Lombard correspondence
- Estimated 100-200 additional letters
- Requires structured extraction from MGH digital editions

### 3B. Oxyrhynchus Papyrus Letters
- Thousands of documentary letters from Roman Egypt
- Requires identifying letter documents within the larger corpus
- Major research project

### 3C. Horace's Epistles (23 verse letters, 20-14 BC)
- Literary epistles, not personal correspondence
- Include with appropriate categorization

## Priority Order
1. **Cicero** (biggest impact on network viz + most letters)
2. **Seneca** (fills 1st century gap)
3. **Fronto** (fills 2nd century gap)
4. **Chrysostom remaining** (fills existing collection gap)
5. **Cyril + Ignatius** (quick wins)
6. **Nilus** (OCR pipeline, large collection)
7. **Everything else**

## Updated Database Stats After Phase 1
| Metric | Current | After Phase 1 |
|--------|---------|--------------|
| Total letters | 6,914 | ~8,348 |
| Date range | 100-800 AD | 68 BC - 800 AD |
| Collections | 54 | ~60 |
| People in network | 1,848 | ~2,500+ |

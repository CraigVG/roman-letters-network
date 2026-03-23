# Roman Letters

## Project Overview

**Live site: https://romanletters.org**
**Scholarly subdomain: https://scholarly.romanletters.org**
**GitHub: https://github.com/CraigVG/roman-letters-network**

6,949 letters from the late ancient world (100-800 AD) with modern English translations, original Latin/Greek texts, interactive network and geographic visualizations. Inspired by Patrick Wyman's USC dissertation "Letters, Mobility, and the Fall of the Roman Empire" (2016).

## Tech Stack

- **Site**: Next.js 15 + TypeScript + Tailwind CSS v4 (static export, ~7,000 pages)
- **Database**: SQLite at `data/roman_letters.db` (62MB, read at build time via better-sqlite3)
- **Visualizations**: D3.js (force-directed network graph, geographic map timelapse, regionalization chart)
- **Map tiles**: DARE (Digital Atlas of the Roman Empire) historical tiles
- **Search**: Pagefind (WASM, client-side, 505K+ words indexed)

## Project Structure

```
roman-letters-network/
├── site/                          # Next.js application
│   ├── app/                       # App Router pages
│   │   ├── page.tsx               # Home (scrollytelling + collections)
│   │   ├── letters/               # Letter browse + individual pages
│   │   │   └── [collection]/[number]/
│   │   │       ├── page.tsx       # Individual letter page
│   │   │       └── VersionTabs.tsx # Translation tabs + source badges
│   │   ├── authors/               # Author profiles
│   │   ├── correspondence/        # Thread views
│   │   ├── thesis/                # "The Shrinking World" analysis
│   │   ├── map/                   # Geographic timelapse
│   │   ├── network/               # Force-directed graph
│   │   └── about/                 # Project info
│   ├── components/                # React components
│   │   ├── home/                  # Scrollytelling (FallOfRomeStory)
│   │   ├── letters/               # LetterText, VersionTabs, TopicPills
│   │   ├── viz/                   # D3 visualizations
│   │   ├── layout/                # Header, Footer, ThemeToggle, ScholarlyModeContext
│   │   ├── search/                # Pagefind SearchDialog
│   │   └── ui/                    # Badge, Pagination
│   ├── lib/                       # Data access (db.ts, letters.ts, authors.ts, seo.ts)
│   ├── public/data/               # Pre-generated JSON for visualizations
│   └── scripts/                   # Build scripts (sitemap, viz data, hub cities)
├── data/
│   ├── roman_letters.db           # SQLite database (all letter data)
│   ├── author_prompts.json        # Author-specific voice/style profiles (54 collections)
│   ├── translation_guide.md       # 44KB guide on late antique epistolary conventions
│   ├── modern_voice_guide.md      # Translation quality guidelines (updated: no headers)
│   ├── benchmark_results/         # Translation quality benchmark scores
│   └── NEXT_PHASE_OCR.md          # Future: OCR Greek letter collections
├── scripts/                       # Python data scripts (~384 files)
│   ├── scholarly_translate.py     # ★ Current translation pipeline (scholarly quality)
│   ├── scholarly_validate.py      # ★ Post-translation quality checks
│   ├── benchmark_translations.py  # ★ Blind comparison scoring system
│   ├── audit_translation_quality.py # Quality audit (Latin contamination, OCR artifacts)
│   ├── strip_ai_headers.py        # Strip From:/To:/Date:/Context: headers
│   ├── clean_english_text.py      # Strip New Advent ads from english_text
│   ├── translate_modern.py        # OLD translation pipeline (DO NOT USE — produces paraphrases)
│   └── [380+ other scripts]       # Scrapers, batch translators, data enrichment
├── schema.sql                     # Database schema
├── Dockerfile                     # Docker build (outdated — use rsync deploy)
└── deploy.sh                      # Cloud Run deploy (outdated — use rsync deploy)
```

## Database

**File**: `data/roman_letters.db` (SQLite, 62MB)

### Stats

| Metric | Value |
|--------|-------|
| Total letters | 6,949 |
| Collections | 54 |
| With modern English translation | 6,859 (98.7%) |
| With 19th-century English | 2,244 |
| With Latin/Greek original | 5,206 |
| People (authors table) | 1,848 |
| Letters with distance data | 4,441 |
| Letters with carrier mentions | 478 |

### Key Tables

**letters** — main table (6,949 rows):
- `id`, `collection`, `letter_number`, `ref_id`
- `sender_id`, `recipient_id` (FK to `authors`)
- `year_approx`, `year_min`, `year_max`
- `origin_place`, `origin_lat`, `origin_lon`, `dest_place`, `dest_lat`, `dest_lon`
- `latin_text` — original Latin or Greek text
- `english_text` — 19th-century scholarly English translation (when available)
- `modern_english` — modern English translation (AI-assisted unless translation_source says otherwise)
- `translation_source` — provenance of the translation (see below)
- `quick_summary`, `interesting_note`, `topics`
- `distance_km`, `origin_confidence`, `dest_confidence`
- `carrier_name`, `carrier_role`, `carrier_mentioned`

**authors** — people (1,848 rows):
- `id`, `name`, `name_latin`, `birth_year`, `death_year`
- `role`, `location`, `lat`, `lon`, `notes`

**collections** — collection metadata

### Translation Sources

| Source | Count | Type |
|--------|-------|------|
| `existing_newadvent` | 1,634 | Human (NPNF/ANF via New Advent) |
| `existing_attalus` | 365 | Human (Attalus.org) |
| `existing_livius` | 159 | Human (Livius.org) |
| `existing_tertullian` | 99 | Human (Tertullian Project) |
| `existing_rogerpearse` | 54 | Human (Roger Pearse) |
| `existing_fordham` | 48 | Human (Fordham Sourcebook) |
| `existing_celt` | 5 | Human (CELT) |
| `ai_translated` | 821 | AI (Claude) |
| `seeck_ocr_ia` | 677 | AI from OCR Latin (Seeck/Internet Archive) |
| `pg78_ocr` | 576 | AI from OCR Greek (Patrologia Graeca 78) |
| `none` / NULL | 2,285 | Mixed (older pipeline, source not tracked) |
| `latin_only` | 146 | Has Latin, no English translation |
| `pending` / `needs_translation` | 80 | Awaiting translation |

## Translation Quality System

### Current Pipeline

**ALWAYS use `scripts/scholarly_translate.py`** for new translations. NEVER use the old `scripts/translate_modern.py` — it produces paraphrases, not translations.

The scholarly pipeline emphasizes FIDELITY over readability:
- Preserves exact person/number from source (no "we"→"I" shifts)
- Preserves specific vocabulary (no softening "danger of betrayal"→"feels like a betrayal")
- Preserves sentence order (no rearranging for "flow")
- No metadata headers (no "From:/To:/Date:/Context:" blocks)
- Author-specific voice profiles in `data/author_prompts.json`

### Quality Benchmark

50-letter blind comparison system in `scripts/benchmark_translations.py`:
- Scores on 5 dimensions (semantic fidelity, vocabulary precision, structural fidelity, register/voice, naturalness)
- Baseline (old prompts): 3.54/5.0
- Current (scholarly prompts): 4.38/5.0
- Human reference: 4.14/5.0
- Pass threshold: 4.0

### Validation

`scripts/scholarly_validate.py` checks for:
- AI metadata headers (From:/To: blocks)
- Length ratio anomalies (translation < 20% of source = likely paraphrase)
- Template/duplicate detection
- Vocabulary softening patterns
- Placeholder text
- Untranslated Greek/Latin

### Translation Source Labels (UI)

Every letter page shows a colored badge:
- **Green** (checkmark): "Human translation" + source name — for `existing_*` sources
- **Amber** (warning): "AI-assisted translation" + disclaimer — for all other sources

Defined in `VersionTabs.tsx` (`SCHOLARLY_SOURCES` set) and `page.tsx` (header metadata).

### Scholarly Mode

Toggle in header hides all AI translations, shows only pre-existing scholarly sources + Latin/Greek originals.
- URL param: `?scholarly=true`
- Context: `ScholarlyModeContext.tsx`
- `SCHOLARLY_SOURCES` set defines which `translation_source` values are considered scholarly

## Key Features

- **Individual letter pages** with modern English (primary), 19th-century English, Latin/Greek original
- **Translation source badges** (green=human, amber=AI) on every letter
- **"The Shrinking World" thesis page** with D3 regionalization chart
- **"Fall of Rome in Letters"** scrollytelling on home page (8 chapters)
- **Wyman Mode** toggle on map/network (filters to Latin West, 380-630 AD)
- **Scholarly Mode** toggle (hides AI translations)
- **Hub city profiles** (15 cities with per-decade connectivity)
- **Pagefind search** (Cmd+K, 505K+ words)
- **Light/dark theme** toggle

## Build & Deploy

```bash
# Development
cd site && npm run dev

# Production build (generates ~7,000 static pages)
cd site
NODE_OPTIONS='--max-old-space-size=8192' npm run build

# Deploy to romanletters.org (primary)
rsync -avz --delete site/out/ cvg-primary:/var/www/lateromanletters.org/public_html/

# Deploy to scholarly.romanletters.org (scholarly subdomain)
rsync -avz --delete site/out/ cvg-primary:/var/www/scholarly.romanletters.org/public_html/
```

**Server**: `cvg-primary` (SSH alias, production server)
**Web server**: Apache with Let's Encrypt SSL
**Primary domain**: `romanletters.org` → DocumentRoot `/var/www/lateromanletters.org/public_html/`
**Scholarly subdomain**: `scholarly.romanletters.org` → DocumentRoot `/var/www/scholarly.romanletters.org/public_html/`
**Note**: Directory name `lateromanletters.org` is a legacy artifact — the domain is `romanletters.org`.

The SQLite DB is read-only at build time. No runtime database needed. The `deploy.sh` and `Dockerfile` are outdated — use rsync.

## Important Rules

- **Never use the word "Byzantine"** — the Eastern Roman Empire was the Roman Empire
- **Never use `translate_modern.py`** for new translations — use `scholarly_translate.py`
- **Never produce "From:/To:" headers** in translations — output only the translated text
- **Never produce template/generic translations** — each letter must have unique content matching its source
- **Always verify translations match their source text** — fabricated translations (wrong letter) have been a recurring problem, especially in Augustine and Ennodius
- Modern translations are AI-assisted (Claude) and labeled as such on the site
- Location confidence: `strong` (historically established), `approximate` (inferred), `unknown` (default assigned)
- Translation quality benchmark target: average ≥ 4.0 on the 5-dimension rubric

## Known Data Issues

- **90 Symmachus letters** have no Latin source text and no translation (Book 10 + scattered fragments — source doesn't exist)
- **Gregory the Great**: 14 records have multi-letter concatenation in `latin_text` (documented in `data/benchmark_results/gregory_data_issues.txt`); 1 record (id=1155) contains Decretals of Gregory IX (wrong text)
- **Gregory the Great**: 34 duplicate `latin_text` pairs from overlapping PL77 book numbering
- **Isidore of Pelusium**: Greek OCR from Patrologia Graeca vol. 78 is often garbled; planned Gemini vision OCR pipeline to re-OCR from page images
- Translation source labeling is incomplete — 2,285 letters have `none`/NULL source (older pipeline didn't track this)

## Next Steps

- **Gemini OCR pipeline**: Use Gemini vision to properly OCR Patrologia Graeca page images for cleaner Greek source text (Isidore, and potentially Nilus/Chrysostom for 3,000+ new letters)
- **ORBIS-style route visualization**: Roman roads instead of straight-line arcs on the map
- **Political borders overlay**: Animated borders on the map timelapse
- See `data/NEXT_PHASE_OCR.md` for details

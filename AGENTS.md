# Agents Guide — Roman Letters

## For AI Agents Working on This Project

### What This Is

A Next.js static site at https://romanletters.org with 7,049 ancient letters (97-800 AD) translated into modern English. The site is statically generated from a SQLite database at build time. There is no runtime server or database — everything is pre-rendered HTML.

### Critical Rules

1. **Never use the word "Byzantine."** The Eastern Roman Empire was the Roman Empire. Call it the "Eastern Roman Empire" or "the Roman Empire in the East."

2. **Modern translations should be clear, literate modern English** — like well-written nonfiction. See `data/modern_voice_guide.md` for the quality bar. Honorifics are fine; archaic language is not.

3. **The SQLite database is read-only at build time.** Changes to the DB require a full rebuild (`npm run build`) to appear on the site.

4. **Use `data/translation_guide.md`** for late antique epistolary conventions when translating.

### Project Layout

```
site/                  # Next.js app (the live website)
  app/                 # Pages (App Router)
  components/          # React components
  lib/                 # Data access (reads SQLite at build time)
  public/data/         # Pre-generated JSON for D3 visualizations
  scripts/             # Build-time scripts (sitemap, viz data)

data/                  # SQLite database + documentation
scripts/               # Python data scripts (scrapers, translators)
```

### How to Build

```bash
cd site
npm install
NODE_OPTIONS='--max-old-space-size=8192' npm run build
node scripts/generate-sitemap.js
```

### How to Add Data

1. Modify `data/roman_letters.db` using Python scripts in `scripts/`
2. If adding a new collection: create entries in both `collections` and `letters` tables
3. Run enrichment scripts: `scripts/extract_recipients.py`, `scripts/enrich_data.py`
4. Rebuild the site (the build reads the DB and generates all pages)

### How to Add a New Page

1. Create `site/app/[route]/page.tsx` (server component for static data)
2. Use `lib/db.ts` to query SQLite at build time
3. For dynamic routes: add `generateStaticParams()` and `generateMetadata()`
4. For D3 visualizations: create a `'use client'` component, load via `dynamic()` with `ssr: false`

### Key Data Files

| File | Purpose |
|------|---------|
| `data/roman_letters.db` | All letter data (7,049 letters, 1,516 people, 54 collections) |
| `site/public/data/network.json` | Pre-computed network graph |
| `site/public/data/map-letters.json` | Letters with coordinates for map timelapse |
| `site/public/data/regionalization.json` | Per-decade distance metrics for thesis chart |
| `site/public/data/hub-cities.json` | City profiles with connectivity data |
| `site/public/data/historical-events.json` | Events for map overlay |

### Database Schema (Key Tables)

**letters**: id, collection, letter_number, sender_id, recipient_id, year_approx, english_text, latin_text, modern_english, quick_summary, topics, distance_km, carrier_name, carrier_role, carrier_mentioned, origin_confidence, dest_confidence

**authors**: id, name, name_latin, birth_year, death_year, role, location, lat, lon, bio, location_confidence

**collections**: id, slug, author_name, title, letter_count, date_range, scan_url

### Translation Approach

- Use `data/modern_voice_guide.md` for the quality standard
- Use `data/translation_guide.md` for late antique epistolary conventions
- Modern English first, 19th-century and original as secondary versions
- Add `[context]` notes for terms modern readers wouldn't know
- Preserve each author's personality (Jerome is sarcastic, Augustine is warm, Gregory is direct)

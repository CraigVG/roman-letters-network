# Roman Letters

## Project Overview

**Live site: https://romanletters.org**
**GitHub: https://github.com/CraigVG/roman-letters-network**

7,049 letters from the late ancient world (100-800 AD) translated into modern English, with interactive network and geographic visualizations. Inspired by Patrick Wyman's USC dissertation "Letters, Mobility, and the Fall of the Roman Empire" (2016). 3,068 letters translated to English for the first time.

## Tech Stack

- **Site**: Next.js 15 + TypeScript + Tailwind CSS v4 (static export, 5,000+ pages)
- **Database**: SQLite at `data/roman_letters.db` (51MB, read at build time via better-sqlite3)
- **Visualizations**: D3.js (force-directed network graph, geographic map timelapse, regionalization chart)
- **Map tiles**: DARE (Digital Atlas of the Roman Empire) historical tiles
- **Search**: Pagefind (WASM, client-side, 400K+ words indexed)

## Project Structure

```
roman-letters-network/
├── site/                          # Next.js application
│   ├── app/                       # App Router pages
│   │   ├── page.tsx               # Home (scrollytelling + collections)
│   │   ├── letters/               # Letter browse + individual pages
│   │   ├── authors/               # Author profiles
│   │   ├── correspondence/        # Thread views
│   │   ├── thesis/                # "The Shrinking World" analysis
│   │   ├── map/                   # Geographic timelapse
│   │   ├── network/               # Force-directed graph
│   │   └── about/                 # Project info
│   ├── components/                # React components
│   │   ├── home/                  # Scrollytelling (FallOfRomeStory)
│   │   ├── letters/               # LetterText, VersionTabs, TopicPills
│   │   ├── viz/                   # D3 visualizations (NetworkGraph, MapTimelapse, RegionalizationChart)
│   │   ├── layout/                # Header, Footer, ThemeToggle, Breadcrumbs
│   │   ├── search/                # Pagefind SearchDialog
│   │   └── ui/                    # Badge, Pagination
│   ├── lib/                       # Data access (db.ts, letters.ts, authors.ts, seo.ts)
│   ├── public/data/               # Pre-generated JSON for visualizations
│   └── scripts/                   # Build scripts (sitemap, viz data, hub cities)
├── data/
│   ├── roman_letters.db           # SQLite database (all letter data)
│   ├── translation_guide.md       # 44KB guide on late antique epistolary style
│   ├── modern_voice_guide.md      # Translation quality guidelines
│   └── NEXT_PHASE_OCR.md          # Future: OCR Greek letter collections
├── scripts/                       # Python data scripts (scrapers, translators, enrichment)
├── Dockerfile                     # Docker build for deployment
├── nginx.conf                     # nginx config for static serving
├── deploy.sh                      # Build + deploy script
└── schema.sql                     # Database schema
```

## Database Stats

| Metric | Value |
|--------|-------|
| Total letters | 7,049 |
| Collections | 54 |
| Modern English translations | ~100% |
| First-ever English translations | 3,068 |
| People identified | 1,516 |
| Letters with distance data | 2,433 |
| Letters with carrier mentions | 478 |

## Key Features

- **Individual letter pages** with modern English (primary), 19th-century English, Latin/Greek original
- **"The Shrinking World" thesis page** with D3 regionalization chart (Wyman's mobility thesis)
- **"Fall of Rome in Letters"** scrollytelling on home page (8 chapters)
- **Wyman Mode** toggle on map/network (filters to Latin West, 380-630 AD)
- **Hub city profiles** (15 cities with per-decade connectivity)
- **Letter-carrier data** (478 letters with carrier mentions)
- **Location confidence** levels (strong/approximate/unknown per Wyman's methodology)
- **Pagefind search** (Cmd+K, 400K+ words)
- **Light/dark theme** toggle

## Build & Deploy

```bash
# Development
cd site && npm run dev

# Production build (generates 5,000+ static pages)
cd site
NODE_OPTIONS='--max-old-space-size=8192' npm run build
node scripts/generate-sitemap.js
```

The SQLite DB is read-only at build time. No runtime database needed.

## Deployment

The site is a static Next.js export served by Apache on `cvg-primary`. Build locally, then rsync.

```bash
# Build
cd site && NODE_OPTIONS='--max-old-space-size=8192' npm run build

# Deploy to romanletters.org (primary)
rsync -avz --delete site/out/ cvg-primary:/var/www/lateromanletters.org/public_html/

# Deploy to scholarly.romanletters.org (scholarly subdomain)
rsync -avz --delete site/out/ cvg-primary:/var/www/scholarly.romanletters.org/public_html/
```

**Server**: `cvg-primary` (SSH alias, production server)
**Web server**: Apache with Let's Encrypt SSL
**Primary domain**: `romanletters.org` → DocumentRoot `/var/www/lateromanletters.org/public_html/`
**Scholarly subdomain**: `scholarly.romanletters.org` → DocumentRoot `/var/www/scholarly.romanletters.org/public_html/`
**Note**: The directory name `lateromanletters.org` is a legacy artifact — the actual domain is `romanletters.org`. Apache config redirects `lateromanletters.org` and `www.*` variants to `romanletters.org`.

The `deploy.sh` script (Google Cloud Run) is outdated — use rsync instead.

## Important Notes

- Never use the word "Byzantine" — the Eastern Roman Empire was the Roman Empire
- Modern translations are AI-assisted (Claude) and marked as such — not peer-reviewed
- Location confidence: `strong` (historically established), `approximate` (inferred), `unknown` (default assigned)
- The SQLite DB is read-only at build time — no runtime database needed

## Next Steps

See `data/NEXT_PHASE_OCR.md` for:
- OCR Patrologia Graeca volumes 78, 79, 52 (Isidore of Pelusium, Nilus, Chrysostom — potentially 3,000+ more letters)
- ORBIS-style route visualization (Roman roads instead of straight-line arcs)
- Political borders overlay animation on the map timelapse

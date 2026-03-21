# Roman Letters

**7,049 letters from the ancient world, translated into modern English.**

[**romanletters.org**](https://romanletters.org)

---

The first public resource to bring together 54 late antique letter collections spanning 700 years (100-800 AD), with modern English translations for over 7,000 letters — including 3,068 translated into English for the first time.

## What This Is

As the Roman Empire fragmented between the 4th and 7th centuries, its communication networks — the web of letters that connected bishops, senators, emperors, and monks across the Mediterranean — slowly fell apart. Cities that had exchanged letters for centuries went silent. The world became smaller.

This project maps that transformation through the letters themselves.

Inspired by [Patrick Wyman's doctoral dissertation](https://www.proquest.com/openview/df57be3de3bbe46bf99fa230d530082a/1) at USC, *"Letters, Mobility, and the Fall of the Roman Empire"* (2016), which traced how communication networks frayed as new kingdoms emerged and political instability grew. Wyman's core insight: every letter is a "fossilized moment of movement" — someone had to carry it, on foot or horseback, along a specific road. When you measure the distances these letters traveled and plot them over time, you can watch the Roman world shrink.

## The Dataset

| Metric | Value |
|--------|-------|
| Total letters | 7,049 |
| Collections | 54 |
| Time span | 100-800 AD |
| Modern English translations | ~100% |
| First-ever English translations | 3,068 |
| People identified | 1,516 |
| Letters with distance data | 2,433 |
| Letters with carrier mentions | 478 |

### Major Collections

| Author | Letters | Period | Notable For |
|--------|---------|--------|-------------|
| Libanius | 837 | 314-393 | Last great pagan rhetorician of Antioch |
| Symmachus | 677 | 365-402 | Last pagan senator's aristocratic network |
| Isidore of Pelusium | 630 | 360-435 | Egyptian monk's moral counsel |
| Cassiodorus | 477 | 506-538 | Ostrogothic state correspondence |
| Gregory the Great | 421 | 590-604 | Pope holding the network together |
| Pliny the Younger | 365 | 97-113 | Roman senator at the empire's height |
| Basil of Caesarea | 325 | 357-378 | Cappadocian Father's pastoral letters |
| Ennodius of Pavia | 297 | 493-521 | Literary bishop in Ostrogothic Italy |
| Augustine | 261 | 386-430 | Bishop of Hippo's theological correspondence |
| Hormisdas | 249 | 514-523 | Pope resolving the Acacian Schism |
| Theodoret of Cyrrhus | 181 | 423-466 | Theologian in Christological controversies |
| Sidonius Apollinaris | 171 | 455-480 | Watching Roman Gaul collapse |
| Synesius of Cyrene | 159 | 394-413 | Philosopher-bishop in collapsing Roman Libya |
| + 29 more collections | | | |

## Features

### Content
- **Individual letter pages** — every letter has its own URL with modern translation, 19th-century English, and Latin/Greek original
- **Author profiles** — biographies, letter statistics, top correspondents
- **Correspondence threads** — back-and-forth exchanges between pairs of writers (140+ threads)
- **"Fall of Rome in Letters"** — 8-chapter scrollytelling narrative on the home page

### Analysis (Wyman Thesis)
- **"The Shrinking World"** — thesis page with D3 regionalization chart showing average letter distance declining over two centuries
- **"Wyman Mode"** — toggle on map and network to filter to Latin West, 380-630 AD (matching his corpus)
- **Hub city profiles** — 15 major cities with per-decade connectivity data
- **Letter-carrier data** — 478 letters with identified carriers (clergy as dominant role)
- **Location confidence levels** — strong/approximate/unknown per Wyman's methodology

### Visualizations
- **Interactive network graph** — D3.js force-directed graph with sidebar details, collection filter
- **Geographic timelapse** — animated map with DARE historical tiles showing letter flows across 700 years
- **Regionalization chart** — average letter distance by decade with Wyman Mode toggle

### Infrastructure
- **Full-text search** — Pagefind (Cmd+K, 400K+ words indexed)
- **Light/dark theme** toggle
- **44 sitemaps** for Google Search Console
- **JSON-LD structured data** on all pages

## Tech Stack

- **Frontend**: Next.js 15, Tailwind CSS v4, TypeScript
- **Data**: SQLite (51MB, read at build time via better-sqlite3)
- **Map**: MapLibre GL JS with DARE (Digital Atlas of the Roman Empire) tiles
- **Visualizations**: D3.js (force-directed graph, geographic projection, line charts)
- **Search**: Pagefind (WASM, client-side)
- **Build**: Static site generation — 5,000+ pre-rendered HTML pages

## Development

```bash
# Clone
git clone https://github.com/CraigVG/roman-letters-network.git
cd roman-letters-network

# Install dependencies
cd site && npm install

# Run dev server
npm run dev

# Build static site (generates 5,000+ pages)
NODE_OPTIONS='--max-old-space-size=8192' npm run build

# Generate sitemaps
node scripts/generate-sitemap.js
```

The SQLite database at `data/roman_letters.db` contains all letter data. The Next.js build reads it at build time — no runtime database needed.

## Data Sources

Latin and Greek texts gathered from:
- [New Advent Church Fathers Library](https://www.newadvent.org/fathers/)
- [The Latin Library](https://www.thelatinlibrary.com/)
- [Tertullian Project](https://www.tertullian.org/fathers/)
- [Perseus Digital Library](https://www.perseus.tufts.edu/)
- [Internet Archive](https://archive.org/) (Patrologia Graeca, MGH, CSEL editions)
- [OpenGreekAndLatin / First1KGreek](https://github.com/OpenGreekAndLatin/First1KGreek)
- [Latin Wikisource](https://la.wikisource.org/) (Braulio of Zaragoza)
- MGH Epistolae volumes (Austrasicae, Wisigothicae, Desiderius)

Links to original scanned editions on the Internet Archive are included for every collection.

## A Note on the Translations

The modern English translations were produced with the assistance of AI (Claude by Anthropic). They are **not** peer-reviewed scholarly translations. They aim to make these letters accessible to a general audience — anyone who wants to hear the voices of the late Roman world.

Where both a Latin/Greek original and a 19th-century English translation existed, both were used as sources. Each letter page provides access to all available versions. For the 3,068 letters translated to English for the first time, the modern translation was produced directly from the Latin or Greek text.

We welcome corrections. If you spot an error or want to contribute a more accurate translation, please open an issue.

## Future Work

- **OCR Phase**: Patrologia Graeca volumes 78, 79, 52 could add 3,000+ Greek letters (Isidore of Pelusium, Nilus of Ancyra, John Chrysostom)
- **Quality pass**: Greek translation review, especially bulk Isidore translations
- **ORBIS integration**: Roman road routes instead of straight-line distance arcs
- **Political borders animation**: Animate the successor kingdom borders on the map timelapse
- **Eastern Roman narrative**: Expand the scrollytelling with the Eastern Empire's continuation until the Arab invasions

## License

Code: [MIT License](LICENSE)
Data and Translations: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Credits

Built by [Craig Vander Galien](https://craigvandergalien.com). Inspired by Patrick Wyman's doctoral research on the fall of Rome. Modern translations assisted by Claude (Anthropic).

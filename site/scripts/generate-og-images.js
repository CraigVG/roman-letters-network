#!/usr/bin/env node
/**
 * generate-og-images.js
 *
 * Generates 1200×630 Open Graph preview images for letter pages using satori.
 * - Top 500 individual letters (most complete data, ranked by quality)
 * - One image per collection (generic fallback)
 *
 * Usage:  cd site && node scripts/generate-og-images.js
 * Output: site/public/og/
 */

const satori = require('satori').default ?? require('satori');
const { Resvg } = require('@resvg/resvg-js');
const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');
const https = require('https');

const DB_PATH = path.join(__dirname, '..', '..', 'data', 'roman_letters.db');
const OG_DIR = path.join(__dirname, '..', 'public', 'og');
const LIMIT = 500;

// Colors from the site theme
const PARCHMENT = '#faf8f5';
const TERRACOTTA = '#b45530';
const DARK = '#2c1a0e';
const MUTED = '#7a6352';
const BORDER = '#e8e0d4';

// Fetch a font buffer from URL
function fetchBuffer(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => resolve(Buffer.concat(chunks)));
      res.on('error', reject);
    }).on('error', reject);
  });
}

// Download fonts once
async function loadFonts() {
  console.log('Downloading fonts…');
  // Use Crimson Pro from Google Fonts — good classical serif (TTF required by satori)
  // URLs from: curl -s "https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,600;1,400" -H "User-Agent: Mozilla/5.0"
  const regularUrl =
    'https://fonts.gstatic.com/s/crimsonpro/v28/q5uUsoa5M_tv7IihmnkabC5XiXCAlXGks1WZEGp8OA.ttf';
  const italicUrl =
    'https://fonts.gstatic.com/s/crimsonpro/v28/q5uSsoa5M_tv7IihmnkabAReu49Y_Bo-HVKMBi6Ue5s7.ttf';
  const semiBoldUrl =
    'https://fonts.gstatic.com/s/crimsonpro/v28/q5uUsoa5M_tv7IihmnkabC5XiXCAlXGks1WZzm18OA.ttf';

  const [regular, italic, semiBold] = await Promise.all([
    fetchBuffer(regularUrl),
    fetchBuffer(italicUrl),
    fetchBuffer(semiBoldUrl),
  ]);

  console.log('Fonts loaded.');
  return [
    { name: 'Crimson Pro', data: regular, weight: 400, style: 'normal' },
    { name: 'Crimson Pro', data: semiBold, weight: 600, style: 'normal' },
    { name: 'Crimson Pro', data: italic, weight: 400, style: 'italic' },
  ];
}

// Truncate text to ~n characters at word boundary
function truncate(text, n) {
  if (!text) return '';
  const t = text.replace(/\s+/g, ' ').trim();
  if (t.length <= n) return t;
  return t.slice(0, n).replace(/\s\S*$/, '') + '…';
}

// Helper to create satori element nodes more concisely
function el(type, style, children) {
  return { type, props: { style, children: Array.isArray(children) ? children : [children] } };
}

// Build the satori element tree for a letter OG image
function letterCard({ sender, recipient, year, collection, snippet, isCollection }) {
  const senderText = sender || 'Unknown';
  const recipientText = recipient || 'Unknown';
  const yearText = year ? `~${year} AD` : '';
  const collectionLabel = collection.replace(/_/g, ' ');
  const metaText = yearText ? `${yearText}  ·  ${collectionLabel}` : collectionLabel;

  // Main heading: collection name or sender → recipient
  const heading = isCollection
    ? el('div', {
        display: 'flex',
        fontSize: 58,
        fontWeight: 600,
        color: DARK,
        lineHeight: 1.15,
        marginBottom: 16,
        flexWrap: 'wrap',
      }, [collectionLabel])
    : el('div', {
        display: 'flex',
        alignItems: 'center',
        gap: 20,
        flexWrap: 'wrap',
        marginBottom: 16,
      }, [
        el('span', { fontSize: 50, fontWeight: 600, color: DARK, lineHeight: 1.15 }, [senderText]),
        el('span', { fontSize: 34, color: TERRACOTTA, fontWeight: 400 }, ['→']),
        el('span', { fontSize: 50, fontWeight: 400, color: DARK, lineHeight: 1.15 }, [recipientText]),
      ]);

  const metaRow = el('div', {
    display: 'flex',
    fontSize: 24,
    color: MUTED,
    marginBottom: snippet ? 28 : 0,
    textTransform: 'capitalize',
  }, [metaText]);

  const snippetBlock = snippet
    ? el('div', {
        display: 'flex',
        borderLeft: `4px solid ${TERRACOTTA}`,
        paddingLeft: 24,
        marginTop: 4,
      }, [
        el('span', {
          fontSize: 27,
          fontStyle: 'italic',
          color: DARK,
          lineHeight: 1.5,
        }, [`"${snippet}"`]),
      ])
    : null;

  const mainChildren = snippetBlock
    ? [heading, metaRow, snippetBlock]
    : [heading, metaRow];

  return {
    type: 'div',
    props: {
      style: {
        width: 1200,
        height: 630,
        background: PARCHMENT,
        display: 'flex',
        flexDirection: 'column',
        padding: '56px 72px',
        fontFamily: 'Crimson Pro',
      },
      children: [
        // Top bar: accent mark + site name
        el('div', {
          display: 'flex',
          alignItems: 'center',
          gap: 14,
          marginBottom: 44,
        }, [
          el('div', {
            display: 'flex',
            width: 5,
            height: 30,
            background: TERRACOTTA,
            borderRadius: 2,
          }, [' ']),
          el('span', {
            fontSize: 20,
            fontWeight: 600,
            color: TERRACOTTA,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
          }, ['ROMAN LETTERS']),
        ]),

        // Main content (flex:1 to fill remaining space)
        el('div', {
          display: 'flex',
          flexDirection: 'column',
          flex: 1,
        }, mainChildren),

        // Bottom bar
        el('div', {
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingTop: 20,
          borderTop: `1px solid ${BORDER}`,
          marginTop: 32,
        }, [
          el('span', { fontSize: 20, color: MUTED, letterSpacing: '0.05em' }, ['romanletters.org']),
          el('span', { fontSize: 18, color: MUTED, fontStyle: 'italic' }, ['Late Roman epistolary network · 97–800 AD']),
        ]),
      ],
    },
  };
}

async function renderPng(element, fonts) {
  const svg = await satori(element, {
    width: 1200,
    height: 630,
    fonts,
  });
  const resvg = new Resvg(svg, { fitTo: { mode: 'width', value: 1200 } });
  return resvg.render().asPng();
}

async function main() {
  fs.mkdirSync(OG_DIR, { recursive: true });

  const fonts = await loadFonts();
  const db = new Database(DB_PATH, { readonly: true });

  // --- 1. Per-collection images ---
  const collections = db.prepare(`
    SELECT slug, author_name FROM collections ORDER BY slug
  `).all();

  console.log(`Generating ${collections.length} collection images…`);
  for (const col of collections) {
    const outPath = path.join(OG_DIR, `collection-${col.slug}.png`);
    if (fs.existsSync(outPath)) continue;

    const element = letterCard({
      sender: null,
      recipient: null,
      year: null,
      collection: col.slug,
      snippet: null,
      isCollection: true,
    });
    const png = await renderPng(element, fonts);
    fs.writeFileSync(outPath, png);
    process.stdout.write('c');
  }
  console.log('\nCollection images done.');

  // --- 2. Top individual letter images ---
  // Rank: has quick_summary desc, has all fields, then by year
  const letters = db.prepare(`
    SELECT
      l.id,
      l.collection,
      l.letter_number,
      l.year_approx,
      l.modern_english,
      l.quick_summary,
      a_s.name AS sender_name,
      a_r.name AS recipient_name
    FROM letters l
    LEFT JOIN authors a_s ON a_s.id = l.sender_id
    LEFT JOIN authors a_r ON a_r.id = l.recipient_id
    WHERE l.sender_id IS NOT NULL
      AND l.recipient_id IS NOT NULL
      AND l.year_approx IS NOT NULL
      AND (l.modern_english IS NOT NULL OR l.english_text IS NOT NULL)
    ORDER BY
      (l.quick_summary IS NOT NULL) DESC,
      (l.interesting_note IS NOT NULL) DESC,
      l.year_approx ASC
    LIMIT ${LIMIT}
  `).all();

  console.log(`Generating ${letters.length} letter images…`);
  let count = 0;
  for (const letter of letters) {
    const fname = `${letter.collection}-${letter.letter_number}.png`;
    const outPath = path.join(OG_DIR, fname);
    if (fs.existsSync(outPath)) {
      count++;
      continue;
    }

    const snippet = truncate(letter.quick_summary || letter.modern_english, 160);
    const element = letterCard({
      sender: letter.sender_name,
      recipient: letter.recipient_name,
      year: letter.year_approx,
      collection: letter.collection,
      snippet,
      isCollection: false,
    });

    try {
      const png = await renderPng(element, fonts);
      fs.writeFileSync(outPath, png);
      count++;
      if (count % 50 === 0) console.log(`  ${count}/${letters.length}`);
      else process.stdout.write('.');
    } catch (err) {
      console.error(`\nError on ${fname}:`, err.message);
    }
  }
  console.log(`\nLetter images done. Total: ${count}`);
  db.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

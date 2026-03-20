#!/usr/bin/env node
/**
 * generate-sitemap.js
 *
 * Reads the SQLite DB and generates sitemap XML files in the out/ directory.
 * Run after `next build` (which populates out/).
 *
 * Usage:  cd site && node scripts/generate-sitemap.js
 */

const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const DB_PATH = path.join(__dirname, '..', '..', 'data', 'roman_letters.db');
const OUT_DIR = path.join(__dirname, '..', 'out');
const BASE_URL = 'https://romanletters.org';
const TODAY = new Date().toISOString().split('T')[0];

const db = new Database(DB_PATH, { readonly: true });

/** Must match lib/authors.ts toSlug() exactly */
function toSlug(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

function xmlEscape(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function urlsetHeader() {
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n`;
}

function urlsetFooter() {
  return `</urlset>\n`;
}

function urlEntry(loc, lastmod) {
  return `  <url>\n    <loc>${xmlEscape(loc)}</loc>\n    <lastmod>${lastmod}</lastmod>\n  </url>\n`;
}

function sitemapIndexXml(sitemapUrls) {
  let xml = `<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n`;
  for (const url of sitemapUrls) {
    xml += `  <sitemap>\n    <loc>${xmlEscape(url)}</loc>\n    <lastmod>${TODAY}</lastmod>\n  </sitemap>\n`;
  }
  xml += `</sitemapindex>\n`;
  return xml;
}

// --- Static pages ---
function generatePagesSitemap() {
  const pages = ['/', '/about/', '/map/', '/network/', '/letters/', '/authors/', '/thesis/'];
  let xml = urlsetHeader();
  for (const p of pages) {
    xml += urlEntry(`${BASE_URL}${p}`, TODAY);
  }
  xml += urlsetFooter();
  return xml;
}

// --- Letters by collection ---
function generateLettersSitemap(collection) {
  const rows = db
    .prepare('SELECT letter_number FROM letters WHERE collection = ? ORDER BY letter_number')
    .all(collection);

  let xml = urlsetHeader();
  // Collection index page
  xml += urlEntry(`${BASE_URL}/letters/${collection}/`, TODAY);
  for (const row of rows) {
    xml += urlEntry(`${BASE_URL}/letters/${collection}/${row.letter_number}/`, TODAY);
  }
  xml += urlsetFooter();
  return xml;
}

// --- Authors ---
function generateAuthorsSitemap() {
  const rows = db
    .prepare('SELECT name FROM authors ORDER BY name')
    .all();

  let xml = urlsetHeader();
  for (const row of rows) {
    const slug = toSlug(row.name);
    xml += urlEntry(`${BASE_URL}/authors/${slug}/`, TODAY);
  }
  xml += urlsetFooter();
  return xml;
}

// --- Correspondence pages (mirrors getCorrespondencePairs with minLetters=3) ---
function generateCorrespondenceSitemap() {
  const rows = db
    .prepare(
      `SELECT
         s.name AS sender_name,
         r.name AS recipient_name,
         COUNT(*) AS letter_count
       FROM letters l
       JOIN authors s ON s.id = l.sender_id
       JOIN authors r ON r.id = l.recipient_id
       GROUP BY
         MIN(l.sender_id, l.recipient_id),
         MAX(l.sender_id, l.recipient_id)
       HAVING COUNT(*) >= 3
       ORDER BY letter_count DESC`
    )
    .all();

  let xml = urlsetHeader();
  for (const row of rows) {
    const names = [row.sender_name, row.recipient_name].sort();
    const slug1 = toSlug(names[0]);
    const slug2 = toSlug(names[1]);
    xml += urlEntry(`${BASE_URL}/correspondence/${slug1}/${slug2}/`, TODAY);
  }
  xml += urlsetFooter();
  return xml;
}

// --- Main ---
function main() {
  if (!fs.existsSync(OUT_DIR)) {
    console.error(`Error: out/ directory not found. Run 'next build' first.`);
    process.exit(1);
  }

  const sitemapFiles = [];

  // 1. Static pages
  const pagesFile = 'sitemap-pages.xml';
  fs.writeFileSync(path.join(OUT_DIR, pagesFile), generatePagesSitemap());
  sitemapFiles.push(`${BASE_URL}/${pagesFile}`);
  console.log(`  wrote ${pagesFile}`);

  // 2. Per-collection letter sitemaps
  const collections = db
    .prepare('SELECT DISTINCT collection FROM letters ORDER BY collection')
    .all();

  for (const { collection } of collections) {
    const filename = `sitemap-letters-${collection}.xml`;
    fs.writeFileSync(path.join(OUT_DIR, filename), generateLettersSitemap(collection));
    sitemapFiles.push(`${BASE_URL}/${filename}`);
    console.log(`  wrote ${filename}`);
  }

  // 3. Authors
  const authorsFile = 'sitemap-authors.xml';
  fs.writeFileSync(path.join(OUT_DIR, authorsFile), generateAuthorsSitemap());
  sitemapFiles.push(`${BASE_URL}/${authorsFile}`);
  console.log(`  wrote ${authorsFile}`);

  // 4. Correspondence
  const corrFile = 'sitemap-correspondence.xml';
  fs.writeFileSync(path.join(OUT_DIR, corrFile), generateCorrespondenceSitemap());
  sitemapFiles.push(`${BASE_URL}/${corrFile}`);
  console.log(`  wrote ${corrFile}`);

  // 5. Sitemap index (written as both sitemap-index.xml and sitemap.xml)
  const indexXml = sitemapIndexXml(sitemapFiles);
  fs.writeFileSync(path.join(OUT_DIR, 'sitemap-index.xml'), indexXml);
  fs.writeFileSync(path.join(OUT_DIR, 'sitemap.xml'), indexXml);
  console.log(`  wrote sitemap-index.xml + sitemap.xml`);

  // 6. robots.txt
  const robotsTxt = [
    'User-agent: *',
    'Allow: /',
    '',
    `Sitemap: ${BASE_URL}/sitemap.xml`,
    '',
  ].join('\n');
  fs.writeFileSync(path.join(OUT_DIR, 'robots.txt'), robotsTxt);
  console.log(`  wrote robots.txt`);

  console.log(`\nDone: ${sitemapFiles.length} sitemaps + index + robots.txt`);
}

main();

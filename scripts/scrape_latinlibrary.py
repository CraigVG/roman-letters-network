#!/usr/bin/env python3
"""
Scrape Latin texts of letters from The Latin Library (thelatinlibrary.com).
These are public domain Latin texts.

Collections available:
- Sidonius Apollinaris: thelatinlibrary.com/sidonius/
- Symmachus: thelatinlibrary.com/symmachus/
- Cassiodorus: thelatinlibrary.com/cassiodorus/
- Augustine (Epistulae): thelatinlibrary.com/augustine/
- Jerome (Epistulae): thelatinlibrary.com/jerome/
- Gregory the Great: thelatinlibrary.com/gregory/
"""

import sqlite3
import os
import re
import time
import urllib.request
import urllib.parse
from html.parser import HTMLParser

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_body = False
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.in_body = True
        if tag in ('script', 'style'):
            self.skip += 1
        if tag in ('p', 'br'):
            self.text_parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip -= 1
        if tag == 'p':
            self.text_parts.append('\n')

    def handle_data(self, data):
        if self.in_body and self.skip <= 0:
            self.text_parts.append(data)

    def get_text(self):
        return re.sub(r'\n{3,}', '\n\n', ''.join(self.text_parts)).strip()


def fetch_url(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'RomanLettersResearch/1.0 (academic research)'
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                content_type = resp.headers.get('Content-Type', '')
                # Latin Library often uses latin-1 encoding
                if 'charset' in content_type:
                    encoding = content_type.split('charset=')[-1].strip()
                else:
                    encoding = 'latin-1'
                return resp.read().decode(encoding, errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1 * (attempt + 1))
            else:
                print(f"  Failed: {url} - {e}")
                return None
    return None


def find_subpage_links(html, index_url):
    """Find links to individual letter pages from a collection index.
    Uses proper URL resolution relative to the index page URL."""
    links = []
    seen = set()
    for match in re.finditer(r'href=["\']([^"\']+\.s?html?)["\']', html, re.IGNORECASE):
        href = match.group(1)
        # Resolve relative to the index page
        full_url = urllib.parse.urljoin(index_url, href)
        if full_url not in seen and 'thelatinlibrary.com' in full_url:
            seen.add(full_url)
            links.append(full_url)
    return links


def split_letters_from_text(full_text, collection_slug):
    """Split a page containing multiple letters into individual letters."""
    letters = []

    # Common patterns for letter boundaries in Latin texts:
    # "EPISTULA I", "EPISTOLA I", "Ep. I", "LIBER I", "I.", etc.
    patterns = [
        r'(?:EPISTULA|EPISTOLA|EP\.?)\s+([IVXLCDM]+|\d+)',
        r'(?:LETTER|LETTRE)\s+([IVXLCDM]+|\d+)',
    ]

    for pattern in patterns:
        splits = list(re.finditer(pattern, full_text, re.IGNORECASE))
        if len(splits) >= 2:
            for i, match in enumerate(splits):
                start = match.start()
                end = splits[i + 1].start() if i + 1 < len(splits) else len(full_text)
                letter_text = full_text[start:end].strip()
                if len(letter_text) > 30:
                    letters.append({
                        'number': i + 1,
                        'text': letter_text,
                        'header': match.group(0),
                    })
            break

    # If no split pattern found, treat the whole page as one letter
    if not letters and len(full_text) > 50:
        letters.append({
            'number': 1,
            'text': full_text,
            'header': '',
        })

    return letters


# Collection configurations with their Latin Library structure
# NOTE: base_url is no longer used - we resolve links relative to index_url
LATIN_COLLECTIONS = {
    'sidonius_apollinaris': {
        'index_url': 'https://www.thelatinlibrary.com/sidonius.html',
    },
    'cassiodorus': {
        'index_url': 'https://www.thelatinlibrary.com/cassiodorus.html',
    },
    'augustine_hippo': {
        'index_url': 'https://www.thelatinlibrary.com/augustine.html',
    },
    'ambrose_milan': {
        'index_url': 'https://www.thelatinlibrary.com/ambrose.html',
    },
    'gregory_great': {
        'index_url': 'https://www.thelatinlibrary.com/gregory.html',
    },
    'paulinus_nola': {
        'index_url': 'https://www.thelatinlibrary.com/paulinus.html',
    },
}


def scrape_collection(slug, config, conn):
    """Scrape Latin texts for a collection."""
    cursor = conn.cursor()
    print(f"\nScraping Latin texts for {slug}...")

    index_html = fetch_url(config['index_url'])
    if not index_html:
        print(f"  Could not fetch index")
        return 0

    # Extract text from index
    extractor = TextExtractor()
    extractor.feed(index_html)

    # Find sub-pages (individual books or letter groups)
    subpages = find_subpage_links(index_html, config['index_url'])
    # Filter out navigation links (index, classics, christian, misc non-letter works)
    skip_keywords = ['index.html', 'classics.html', 'christian.html']
    letter_pages = [u for u in subpages
                    if not any(kw in u.lower() for kw in skip_keywords)
                    and 'thelatinlibrary.com' in u]

    # Only keep pages that look like epistulae, books, or author-specific content
    # (exclude carmina/poems unless they're the only content)
    epistulae_pages = [u for u in letter_pages if any(kw in u.lower() for kw in
                       ['ep', 'letter', 'varia', 'registr'])]
    if not epistulae_pages:
        # For authors like Sidonius where books contain both letters and poems,
        # take all non-navigation pages but skip obvious non-letter works
        epistulae_pages = [u for u in letter_pages
                           if not any(kw in u.lower() for kw in ['carmin', 'poem', 'misc', 'anima', 'musica', 'orat'])]
    if not epistulae_pages:
        epistulae_pages = letter_pages[:20]
    letter_pages = epistulae_pages

    print(f"  Found {len(letter_pages)} sub-pages")

    total_letters = 0
    for page_url in letter_pages:
        time.sleep(0.5)
        html = fetch_url(page_url)
        if not html:
            continue

        extractor = TextExtractor()
        extractor.feed(html)
        page_text = extractor.get_text()

        if len(page_text) < 50:
            continue

        letters = split_letters_from_text(page_text, slug)
        for letter in letters:
            total_letters += 1
            ref_id = f"{slug}.lat.{total_letters}"

            # Check if we already have an English version
            cursor.execute('''
                SELECT id FROM letters
                WHERE collection = ? AND letter_number = ?
            ''', (slug, letter['number']))
            existing = cursor.fetchone()

            if existing:
                # Update with Latin text
                cursor.execute('''
                    UPDATE letters SET latin_text = ?, source_url = ?
                    WHERE id = ?
                ''', (letter['text'], page_url, existing[0]))
            else:
                # Insert new record with Latin only
                cursor.execute('''
                    INSERT OR IGNORE INTO letters
                        (collection, letter_number, ref_id, latin_text, source_url)
                    VALUES (?, ?, ?, ?, ?)
                ''', (slug, letter['number'], ref_id, letter['text'], page_url))

        if total_letters % 50 == 0:
            conn.commit()
            print(f"  Processed {total_letters} letters...")

    conn.commit()
    print(f"  Done: {total_letters} Latin texts for {slug}")
    return total_letters


def main():
    conn = sqlite3.connect(DB_PATH)
    total = 0

    for slug, config in LATIN_COLLECTIONS.items():
        count = scrape_collection(slug, config, conn)
        total += count

    print(f"\nTotal Latin texts scraped: {total}")

    cursor = conn.cursor()
    cursor.execute('''
        SELECT collection, COUNT(*) as total,
               SUM(CASE WHEN latin_text IS NOT NULL THEN 1 ELSE 0 END) as latin,
               SUM(CASE WHEN english_text IS NOT NULL THEN 1 ELSE 0 END) as english
        FROM letters GROUP BY collection
    ''')
    print(f"\n{'Collection':<25} {'Total':>6} {'Latin':>6} {'English':>8}")
    print('-' * 50)
    for row in cursor.fetchall():
        print(f"{row[0]:<25} {row[1]:>6} {row[2]:>6} {row[3]:>8}")

    conn.close()


if __name__ == '__main__':
    main()

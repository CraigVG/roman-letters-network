#!/usr/bin/env python3
"""
Scrape English translations of Libanius letters from freely available online sources.

Libanius of Antioch (~314-393 AD): the great pagan rhetorician, teacher of John Chrysostom.
His corpus preserves ~1,500 letters — the single largest surviving collection from antiquity.

Available free English sources:
1. Tertullian.org: 16 letters to Julian the Apostate (1784 translation, public domain)
   URL: https://www.tertullian.org/fathers/libanius_02_16_letters_to_julian.htm

Note on the larger corpus:
- Foerster critical edition (1921-22): Greek-only, vols 10-11 of Opera (Internet Archive)
- A.F. Norman Loeb edition (1993): 193 selected letters - access-restricted on Archive.org
- Bradbury TTH vol.41 (2004): 183 letters from 355-365 AD - not freely available online
- Bradbury & Moncur TTH vol.82 (2023): letters 388-393 AD - not freely available online

The 16 Julian letters from Tertullian.org are the only free English text available online.
Letter numbers used are Foerster numbering (the standard critical edition).
"""

import sqlite3
import os
import re
import time
import urllib.request
from html.parser import HTMLParser

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
DELAY = 0.5

# Foerster letter numbers for the 16 Julian letters (from the page itself)
# Note: "Letter 3 of Book 2" and "Letter 14 of Book 2" are Zambicari's Wolf edition refs
# The Foerster numbers are provided in the page
JULIAN_LETTERS_FOERSTER = [33, 224, 372, 525, 586, 591, 602, 670, 712, 622, 1035, 1125, 1392, 1490]
# The last two are from Wolf's Book 2 — we'll assign pseudo-numbers W2.3 and W2.14

TERTULLIAN_URL = 'https://www.tertullian.org/fathers/libanius_02_16_letters_to_julian.htm'


class LetterHTMLParser(HTMLParser):
    """Parse Tertullian.org page to extract individual letter texts."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_body = False
        self.skip_tags = {'script', 'style', 'nav', 'header', 'footer'}
        self.current_skip = 0
        self.in_skip = False

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.current_skip += 1
        if tag == 'body':
            self.in_body = True
        if tag in ('p', 'br', 'h1', 'h2', 'h3', 'h4'):
            self.text_parts.append('\n')

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.current_skip -= 1
        if tag in ('p', 'h1', 'h2', 'h3', 'h4'):
            self.text_parts.append('\n')

    def handle_data(self, data):
        if self.in_body and self.current_skip <= 0:
            self.text_parts.append(data)

    def get_text(self):
        text = ''.join(self.text_parts)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


def fetch_url(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'RomanLettersResearch/1.0 (academic research)'
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(DELAY * (attempt + 1))
            else:
                print(f"  Failed to fetch {url}: {e}")
                return None
    return None


def extract_text(html):
    parser = LetterHTMLParser()
    parser.feed(html)
    return parser.get_text()


def parse_julian_letters(html):
    """
    Parse the Tertullian.org page directly from HTML into individual letters.

    The page uses <h3> tags for letter headings, like:
      <h3>8.</SPAN>&nbsp;Letter\\r\\n670 (A.D.362)</h3>
      <p>letter text...</p>
      ...
      <h3>9....</h3>

    The last two letters (15, 16) are from Wolf's Book 2:
      "Letter 3 of book 2" -> foerster_num = 'wolf2.3'
      "Letter 14 of book 2" -> foerster_num = 'wolf2.14'

    Returns list of dicts: {foerster_num, year, text, header}
    """
    letters = []

    # Split on <h3> tags — each letter has its own h3 heading
    # Pattern: <h3>...N. Letter NNNN (A.D.NNN)...</h3>
    h3_pattern = re.compile(r'<h3[^>]*>(.*?)</h3>', re.IGNORECASE | re.DOTALL)
    h3_matches = list(h3_pattern.finditer(html))

    # Find the first h3 that looks like a letter header (has "Letter" + number)
    letter_h3s = []
    for m in h3_matches:
        header_text = m.group(1)
        # Strip tags from header
        clean = re.sub(r'<[^>]+>', ' ', header_text)
        clean = re.sub(r'&nbsp;', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        if re.search(r'Letter\s*\d+', clean, re.IGNORECASE):
            letter_h3s.append((m, clean))

    if not letter_h3s:
        return letters

    for i, (h3_match, header_clean) in enumerate(letter_h3s):
        # Parse header: extract letter number, book, year
        # Examples:
        # "1. Letter 33 (358 AD)"
        # "8. Letter 670 (A.D.362)"
        # "15. Letter 3 of book 2 (363 A.D.)"

        # Extract year — handle "358 AD", "A.D.362", "(A.D.362)", "(362 AD)"
        year = None
        year_match = re.search(
            r'(?:A\.D\.?\s*(\d{3,4})|(\d{3,4})\s*A\.D\.?|'
            r'\((\d{3,4})\s*AD?\)|AD?\s*(\d{3,4}))',
            header_clean, re.IGNORECASE
        )
        if year_match:
            yr_str = next(g for g in year_match.groups() if g is not None)
            year = int(yr_str)

        # Extract letter number (Foerster or Wolf Book 2)
        book2_match = re.search(r'Letter\s*(\d+)\s+of\s+book\s+2', header_clean, re.IGNORECASE)
        num_match = re.search(r'Letter\s*\n?\s*(\d+)', header_clean, re.IGNORECASE)

        if book2_match:
            wolf_num = int(book2_match.group(1))
            foerster_num = f'wolf2.{wolf_num}'
        elif num_match:
            foerster_num = int(num_match.group(1))
        else:
            continue

        # Get body HTML: from end of this h3 to start of next letter h3
        body_start = h3_match.end()
        if i + 1 < len(letter_h3s):
            next_h3_match = letter_h3s[i + 1][0]
            body_end = next_h3_match.start()
        else:
            body_end = len(html)

        body_html = html[body_start:body_end]

        # Convert body HTML to text, stripping footnote superscripts
        body_text = re.sub(r'<sup>[^<]*</sup>', '', body_html, flags=re.IGNORECASE)
        body_text = re.sub(r'<br\s*/?>', '\n', body_text, flags=re.IGNORECASE)
        body_text = re.sub(r'<p[^>]*>', '\n', body_text, flags=re.IGNORECASE)
        body_text = re.sub(r'</p>', '\n', body_text, flags=re.IGNORECASE)
        body_text = re.sub(r'<[^>]+>', '', body_text)
        body_text = re.sub(r'&nbsp;', ' ', body_text)
        body_text = re.sub(r'&amp;', '&', body_text)
        body_text = re.sub(r'&quot;', '"', body_text)
        body_text = re.sub(r'&#x[0-9A-Fa-f]+;', '', body_text)
        body_text = re.sub(r'&#\d+;', '', body_text)
        body_text = re.sub(r'[ \t]+', ' ', body_text)
        body_text = re.sub(r'\n{3,}', '\n\n', body_text)

        # Trim footnote section: footnotes appear after the letter body,
        # marked by standalone digit lines like "1 This letter is one of..."
        # They start with a line that is just a number
        body_lines = body_text.split('\n')
        main_lines = []
        footnote_started = False
        for line in body_lines:
            stripped = line.strip()
            if not footnote_started and re.match(r'^\d+\s+[A-Z]', stripped) and len(main_lines) > 3:
                footnote_started = True
            if not footnote_started:
                main_lines.append(stripped)

        body_clean = ' '.join(l for l in main_lines if l).strip()
        body_clean = re.sub(r'\s+', ' ', body_clean).strip()

        if len(body_clean) < 50:
            continue

        letters.append({
            'foerster_num': foerster_num,
            'year': year,
            'text': body_clean,
            'header': header_clean,
        })

    return letters


def ensure_collection_and_author(conn):
    cursor = conn.cursor()

    # Ensure author exists
    cursor.execute('''
        INSERT OR IGNORE INTO authors (name, name_latin, birth_year, death_year, role, location, lat, lon, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Libanius',
        'Libanius Antiochenus',
        314,
        393,
        'rhetorician',
        'Antioch',
        36.2021,
        36.1601,
        'Pagan rhetorician of Antioch. Teacher of John Chrysostom and Basil of Caesarea. '
        'His corpus preserves ~1,500 letters — the single largest surviving letter collection from antiquity. '
        'Also 64 surviving orations. Wrote in Greek. Major figure in the Second Sophistic.'
    ))
    conn.commit()

    cursor.execute('SELECT id FROM authors WHERE name = ?', ('Libanius',))
    author_id = cursor.fetchone()[0]

    # Ensure collection exists
    cursor.execute('''
        INSERT OR IGNORE INTO collections
            (slug, author_name, title, letter_count, date_range,
             english_source_url, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        'libanius',
        'Libanius',
        'Letters of Libanius',
        1544,
        '314-393 AD',
        'https://www.tertullian.org/fathers/libanius_02_16_letters_to_julian.htm',
        'The single largest surviving letter collection from antiquity (~1,544 letters in Foerster ed.). '
        'Greek text: Foerster Opera vols.10-11 (1921-22, Leipzig: Teubner), available at archive.org. '
        'English translations: A.F. Norman Loeb vols.478-479 (1993, 193 selected letters); '
        'Bradbury TTH vol.41 (2004, 183 letters from 355-365); '
        'Bradbury & Moncur TTH vol.82 (2023, letters 388-393). '
        'Only 16 Julian letters (1784 translation) are freely available online at tertullian.org.'
    ))
    conn.commit()

    return author_id


def scrape_libanius(conn):
    cursor = conn.cursor()

    author_id = ensure_collection_and_author(conn)

    # Check existing
    cursor.execute('SELECT COUNT(*) FROM letters WHERE collection = ?', ('libanius',))
    existing = cursor.fetchone()[0]
    print(f"  Existing Libanius letters in DB: {existing}")

    print(f"\nFetching Tertullian.org page: {TERTULLIAN_URL}")
    html = fetch_url(TERTULLIAN_URL)
    if not html:
        print("  ERROR: Could not fetch Tertullian.org page")
        return 0

    full_text = extract_text(html)
    print(f"  Page text length: {len(full_text)} chars")

    letters = parse_julian_letters(html)
    print(f"  Parsed {len(letters)} letters from page")

    count = 0
    for letter in letters:
        fn = letter['foerster_num']
        if fn is None:
            continue

        # Build ref_id
        if isinstance(fn, str):
            ref_id = f'libanius.ep.{fn}'
        else:
            ref_id = f'libanius.ep.{fn}'

        # Check if already exists
        cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
        if cursor.fetchone():
            print(f"  Skipping {ref_id} (already exists)")
            count += 1
            continue

        letter_num = fn if isinstance(fn, int) else None
        year = letter.get('year')

        # All these letters are to Julian
        recipient_id = None
        cursor.execute('SELECT id FROM authors WHERE name LIKE ?', ('%Julian%',))
        row = cursor.fetchone()
        if row:
            recipient_id = row[0]

        cursor.execute('''
            INSERT OR REPLACE INTO letters
                (collection, letter_number, ref_id, sender_id, recipient_id,
                 year_approx, year_min, year_max,
                 subject_summary, english_text, translation_source, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'libanius',
            letter_num,
            ref_id,
            author_id,
            recipient_id,
            year,
            year,
            year,
            f'Letter {fn} to Julian (Foerster numbering)',
            letter['text'],
            'existing_tertullian',
            TERTULLIAN_URL
        ))
        count += 1
        print(f"  Saved: {ref_id} (year={year}, {len(letter['text'])} chars)")

    conn.commit()
    cursor.execute("UPDATE collections SET scrape_status = 'partial' WHERE slug = 'libanius'")
    conn.commit()

    return count


def main():
    print("=" * 60)
    print("LIBANIUS LETTER SCRAPER")
    print("=" * 60)
    print()
    print("Source: Tertullian.org — 16 letters to Julian the Apostate")
    print("(1784 English translation, public domain)")
    print()
    print("NOTE: The full Libanius corpus (~1,544 letters) exists only in:")
    print("  - Greek: Foerster Opera vols.10-11 (1921, archive.org)")
    print("  - English: Norman Loeb 1993 (193 letters, access-restricted)")
    print("  - English: Bradbury TTH 2004 (183 letters, not freely available)")
    print("  - English: Bradbury+Moncur TTH 2023 (not freely available)")
    print()

    conn = sqlite3.connect(DB_PATH, timeout=30)

    try:
        count = scrape_libanius(conn)
        print(f"\nTotal Libanius letters saved/verified: {count}")
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM letters WHERE collection = ?', ('libanius',))
        total = cursor.fetchone()[0]
        print(f"Total in DB: {total}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()

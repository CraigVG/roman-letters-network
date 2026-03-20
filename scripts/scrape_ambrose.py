#!/usr/bin/env python3
"""
Scrape Ambrose of Milan letters from New Advent.

Index page: https://www.newadvent.org/fathers/3409.htm
Individual letters linked as: 340917.htm, 340918.htm, etc.

The existing scrape_newadvent.py incorrectly used 3403.htm (On the Death of
Satyrus, a funeral oration — not letters). The correct index is 3409.htm.

Also scrapes Gregory of Nazianzus from New Advent:
Index: https://www.newadvent.org/fathers/3103.htm
Letters are on three division pages (3103a, 3103b, 3103c) with all letter
text inline (not individual subpages).

DB: data/roman_letters.db
"""

import sqlite3
import os
import re
import time
import urllib.request
from html.parser import HTMLParser

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
BASE_URL = 'https://www.newadvent.org/fathers/'


# ── HTML utilities ───────────────────────────────────────────────────────────

class BodyTextExtractor(HTMLParser):
    """Extract all visible body text, skipping script/style."""

    def __init__(self):
        super().__init__()
        self.parts = []
        self.in_body = False
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.in_body = True
        if tag in ('script', 'style'):
            self.skip += 1
        if tag in ('p', 'br', 'h1', 'h2', 'h3', 'h4', 'li'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip -= 1
        if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'li'):
            self.parts.append('\n')

    def handle_data(self, data):
        if self.in_body and self.skip <= 0:
            self.parts.append(data)

    def get_text(self):
        text = ''.join(self.parts)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


class LinkExtractor(HTMLParser):
    """Extract all href links from a page."""

    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs_dict = dict(attrs)
            href = attrs_dict.get('href', '')
            if href:
                self.links.append(href)


def fetch_url(url, retries=3, delay=1.0):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'RomanLettersResearch/1.0 (academic research project)'
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                print(f"  Failed to fetch {url}: {e}")
                return None
    return None


def html_to_text(html):
    p = BodyTextExtractor()
    p.feed(html)
    return p.get_text()


def strip_newadvent_boilerplate(text):
    """
    Remove New Advent navigation header and fundraising footer.

    The useful content starts after the breadcrumb line that matches:
      "Home > Fathers of the Church > ..."
    and ends before fundraising/support text.
    """
    # Strip everything before the breadcrumb
    breadcrumb_match = re.search(
        r'Home\s*[>»]\s*Fathers of the Church', text
    )
    if breadcrumb_match:
        text = text[breadcrumb_match.start():]
        # Skip past the first line (the breadcrumb itself)
        newline_pos = text.find('\n')
        if newline_pos != -1:
            text = text[newline_pos + 1:]

    # Strip fundraising / support footer text
    fundraising_patterns = [
        r'Help\s+support\s+New\s+Advent',
        r'Please\s+consider\s+donating',
        r'Copyright.*?Kevin\s+Knight',
        r'Nihil\s+Obstat',
        r'New\s+Advent\s+is\s+dedicated',
    ]
    for pattern in fundraising_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            text = text[:m.start()]

    return text.strip()


def parse_letter_header(text):
    """Extract recipient and subject from letter text."""
    info = {'recipient': None, 'subject': None}
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    for line in lines[:20]:
        # "To Emperor Valentinian" or "Ambrose to Valentinian"
        to_match = re.match(r'^(?:Ambrose[,\s]+(?:Bishop[,\s]+)?)?[Tt]o\s+(.+?)[\.,]?\s*$', line)
        if to_match:
            info['recipient'] = to_match.group(1).strip()
            break
        # "Ambrose, Bishop, to Emperor …"
        to_match2 = re.match(r'^Ambrose.{0,30}to\s+(.+?)[\.,]?\s*$', line, re.IGNORECASE)
        if to_match2:
            info['recipient'] = to_match2.group(1).strip()
            break

    # Subject from first substantial paragraph after the first 3 lines
    for line in lines[3:25]:
        if len(line) > 60:
            info['subject'] = line[:200]
            break

    return info


# ── Ambrose scraper ──────────────────────────────────────────────────────────

AMBROSE_INDEX = 'https://www.newadvent.org/fathers/3409.htm'
AMBROSE_SENDER_ID = 1  # Ambrose of Milan


def find_ambrose_letter_links(index_html):
    """Find links to individual Ambrose letter pages from the index."""
    extractor = LinkExtractor()
    extractor.feed(index_html)

    links = []
    seen = set()
    for href in extractor.links:
        # Pattern: ../fathers/3409NN.htm  or  3409NN.htm  or  fathers/3409NN.htm
        m = re.search(r'3409(\d+)\.htm', href)
        if m:
            letter_num = int(m.group(1))
            full_url = f"{BASE_URL}3409{m.group(1)}.htm"
            if full_url not in seen:
                seen.add(full_url)
                links.append((letter_num, full_url))

    links.sort(key=lambda x: x[0])
    return links


def scrape_ambrose(conn):
    cursor = conn.cursor()
    print("\n" + "=" * 60)
    print("Scraping Ambrose letters from New Advent...")
    print(f"Index: {AMBROSE_INDEX}")

    # First clear out bad existing records (the ones from the wrong URL)
    cursor.execute(
        "SELECT COUNT(*) FROM letters WHERE collection='ambrose_milan' AND english_text IS NOT NULL"
    )
    existing_eng = cursor.fetchone()[0]
    if existing_eng > 0:
        print(f"  Found {existing_eng} existing Ambrose English records — checking sources...")
        cursor.execute(
            "SELECT id, ref_id, source_url FROM letters WHERE collection='ambrose_milan' AND english_text IS NOT NULL"
        )
        for row in cursor.fetchall():
            # Delete records from wrong source (3403.htm or epistvaria.html with no real text)
            if '3403' in str(row[2]) or 'epistvaria' in str(row[2]):
                print(f"  Removing bad record: {row[1]} (source: {row[2]})")
                cursor.execute("DELETE FROM letters WHERE id=?", (row[0],))
        conn.commit()

    index_html = fetch_url(AMBROSE_INDEX)
    if not index_html:
        print("  ERROR: Could not fetch Ambrose index")
        return 0

    letter_links = find_ambrose_letter_links(index_html)
    print(f"  Found {len(letter_links)} letter links: {[n for n, _ in letter_links]}")

    if not letter_links:
        print("  ERROR: No letter links found!")
        return 0

    count = 0
    for letter_num, url in letter_links:
        ref_id = f"ambrose_milan.{letter_num}"

        # Skip if already scraped properly
        cursor.execute(
            "SELECT id FROM letters WHERE ref_id=? AND english_text IS NOT NULL AND source_url LIKE '%3409%'",
            (ref_id,)
        )
        if cursor.fetchone():
            print(f"  Letter {letter_num}: already in DB, skipping")
            count += 1
            continue

        time.sleep(0.5)
        print(f"  Fetching Letter {letter_num}: {url}")
        html = fetch_url(url)
        if not html:
            print(f"  WARNING: Could not fetch {url}")
            continue

        raw_text = html_to_text(html)
        text = strip_newadvent_boilerplate(raw_text)

        if len(text) < 100:
            print(f"  WARNING: Very short text for letter {letter_num} ({len(text)} chars)")
            continue

        info = parse_letter_header(text)

        # Look up recipient
        recipient_id = None
        if info['recipient']:
            cursor.execute(
                "SELECT id FROM authors WHERE name LIKE ?",
                (f"%{info['recipient'][:20]}%",)
            )
            row = cursor.fetchone()
            if row:
                recipient_id = row[0]

        cursor.execute('''
            INSERT OR REPLACE INTO letters
                (collection, letter_number, ref_id, sender_id, recipient_id,
                 subject_summary, english_text, translation_source, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'existing_newadvent', ?)
        ''', ('ambrose_milan', letter_num, ref_id, AMBROSE_SENDER_ID,
              recipient_id, info['subject'], text, url))

        count += 1
        print(f"  Saved Letter {letter_num} ({len(text)} chars, recipient: {info['recipient']})")

    conn.commit()

    # Update collection status
    cursor.execute(
        "UPDATE collections SET scrape_status='complete' WHERE slug='ambrose_milan'"
    )
    conn.commit()

    print(f"  Done: {count} Ambrose letters saved")
    return count


# ── Gregory of Nazianzus scraper ─────────────────────────────────────────────

GREGORY_NAZ_DIVISIONS = [
    'https://www.newadvent.org/fathers/3103a.htm',
    'https://www.newadvent.org/fathers/3103b.htm',
    'https://www.newadvent.org/fathers/3103c.htm',
]
GREGORY_NAZ_COLLECTION = 'gregory_nazianzus'


def get_or_create_gregory_naz_author(cursor):
    """Get or create Gregory of Nazianzus author record."""
    cursor.execute("SELECT id FROM authors WHERE name = 'Gregory of Nazianzus'")
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute('''
        INSERT INTO authors (name, name_latin, birth_year, death_year, role, location)
        VALUES ('Gregory of Nazianzus', 'Gregorius Nazianzenus', 329, 390, 'bishop', 'Nazianzus')
    ''')
    return cursor.lastrowid


def get_or_create_gregory_naz_collection(cursor):
    """Ensure collections table has Gregory of Nazianzus entry."""
    cursor.execute("SELECT id FROM collections WHERE slug=?", (GREGORY_NAZ_COLLECTION,))
    if cursor.fetchone():
        return
    cursor.execute('''
        INSERT OR IGNORE INTO collections
            (slug, author_name, title, letter_count, date_range,
             english_source_url, scrape_status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
    ''', (
        GREGORY_NAZ_COLLECTION,
        'Gregory of Nazianzus',
        'Letters',
        249,
        '362-390',
        'https://www.newadvent.org/fathers/3103.htm',
    ))


def split_gregory_letters(text):
    """
    Split a Gregory of Nazianzus division page into individual letters.

    Patterns seen on these pages:
      "Epistle 1. To Basil His Comrade"     (Division I, II)
      "Epistle CI. To Nectarius"
      "Ep. VII."                             (Division III - short form)
      "Ep. XLII."
    """
    # Try both "Epistle N." and "Ep. N." patterns (Roman or Arabic numerals)
    header_pattern = re.compile(
        r'(?:^|\n)((?:Epistle|Ep\.)\s+([IVXLCDM]+|\d+)\.?\s*(?:[^\n]*))',
        re.IGNORECASE
    )
    headers = list(header_pattern.finditer(text))

    if not headers:
        # Fallback: return whole page as one block
        return [{'number_str': '1', 'text': text}]

    letters = []
    for i, match in enumerate(headers):
        start = match.start(1)
        end = headers[i + 1].start(1) if i + 1 < len(headers) else len(text)
        letter_text = text[start:end].strip()
        num_str = match.group(2).strip()
        if len(letter_text) > 30:
            letters.append({'number_str': num_str, 'text': letter_text})

    return letters


def roman_to_int(s):
    """Convert roman numeral string to integer, or return int(s) for arabic."""
    try:
        return int(s)
    except ValueError:
        pass
    roman = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result = 0
    prev = 0
    for ch in reversed(s.upper()):
        val = roman.get(ch, 0)
        if val < prev:
            result -= val
        else:
            result += val
        prev = val
    return result


def scrape_gregory_nazianzus(conn):
    cursor = conn.cursor()
    print("\n" + "=" * 60)
    print("Scraping Gregory of Nazianzus letters from New Advent...")

    author_id = get_or_create_gregory_naz_author(cursor)
    get_or_create_gregory_naz_collection(cursor)
    conn.commit()

    total_count = 0
    # Track letter numbers across divisions to avoid duplicates
    seen_letter_nums = set()

    for div_url in GREGORY_NAZ_DIVISIONS:
        print(f"\n  Fetching division: {div_url}")
        time.sleep(0.5)
        html = fetch_url(div_url)
        if not html:
            print(f"  WARNING: Could not fetch {div_url}")
            continue

        raw_text = html_to_text(html)
        text = strip_newadvent_boilerplate(raw_text)

        letters = split_gregory_letters(text)
        print(f"  Found {len(letters)} letters in this division")

        for letter_data in letters:
            num_str = letter_data['number_str']
            letter_num = roman_to_int(num_str)

            if letter_num in seen_letter_nums:
                print(f"  Skipping duplicate letter {letter_num}")
                continue
            seen_letter_nums.add(letter_num)

            ref_id = f"{GREGORY_NAZ_COLLECTION}.{letter_num}"

            # Skip if already in DB
            cursor.execute(
                "SELECT id FROM letters WHERE ref_id=? AND english_text IS NOT NULL",
                (ref_id,)
            )
            if cursor.fetchone():
                total_count += 1
                continue

            letter_text = letter_data['text']
            info = parse_letter_header(letter_text)

            recipient_id = None
            if info['recipient']:
                cursor.execute(
                    "SELECT id FROM authors WHERE name LIKE ?",
                    (f"%{info['recipient'][:20]}%",)
                )
                row = cursor.fetchone()
                if row:
                    recipient_id = row[0]

            cursor.execute('''
                INSERT OR REPLACE INTO letters
                    (collection, letter_number, ref_id, sender_id, recipient_id,
                     subject_summary, english_text, translation_source, source_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'existing_newadvent', ?)
            ''', (GREGORY_NAZ_COLLECTION, letter_num, ref_id, author_id,
                  recipient_id, info['subject'], letter_text, div_url))

            total_count += 1

        conn.commit()
        print(f"  Running total: {total_count} letters")

    # Update collection status
    cursor.execute(
        "UPDATE collections SET scrape_status='complete' WHERE slug=?",
        (GREGORY_NAZ_COLLECTION,)
    )
    conn.commit()

    print(f"\n  Done: {total_count} Gregory of Nazianzus letters saved")
    return total_count


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)

    ambrose_count = scrape_ambrose(conn)
    gregory_count = scrape_gregory_nazianzus(conn)

    print("\n" + "=" * 60)
    print(f"Ambrose letters saved:            {ambrose_count}")
    print(f"Gregory of Nazianzus letters:     {gregory_count}")

    cursor = conn.cursor()
    cursor.execute('''
        SELECT collection, COUNT(*) as total,
               SUM(CASE WHEN english_text IS NOT NULL THEN 1 ELSE 0 END) as english
        FROM letters
        WHERE collection IN ('ambrose_milan', 'gregory_nazianzus')
        GROUP BY collection
    ''')
    print("\nDB verification:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} total, {row[2]} with English text")

    conn.close()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Scrape Cassiodorus Variae (Latin text) from The Latin Library.

Index:   https://www.thelatinlibrary.com/cassiodorus.html
Books:   https://www.thelatinlibrary.com/cassiodorus/varia1.shtml  (Books 1-12)
Prefatio: https://www.thelatinlibrary.com/cassiodorus/varia.praef.shtml

Each book page contains multiple letters separated by Roman-numeral headers:
  "I. ANASTASIO IMPERATORI THEODERICUS REX."
  "II. THEONI V. S. THEODERICUS REX."
  ...

Approximately 468 letters across 12 books.

DB: data/roman_letters.db
Uses SQLite timeout=30 to handle concurrent writers.
"""

import sqlite3
import os
import re
import time
import urllib.request
from html.parser import HTMLParser

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
BASE_URL = 'https://www.thelatinlibrary.com/'

CASSIODORUS_SENDER_ID = 7  # 'Cassiodorus' in authors table
COLLECTION = 'cassiodorus'

BOOK_URLS = [
    ('praef', f'{BASE_URL}cassiodorus/varia.praef.shtml'),
] + [
    (str(book_num), f'{BASE_URL}cassiodorus/varia{book_num}.shtml')
    for book_num in range(1, 13)
]


# ── HTML utility ─────────────────────────────────────────────────────────────

class BodyTextExtractor(HTMLParser):
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
        if tag in ('p', 'br'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip -= 1
        if tag == 'p':
            self.parts.append('\n')

    def handle_data(self, data):
        if self.in_body and self.skip <= 0:
            self.parts.append(data)

    def get_text(self):
        text = ''.join(self.parts)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


def fetch_url(url, retries=3, delay=1.0):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'RomanLettersResearch/1.0 (academic research project)'
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                content_type = resp.headers.get('Content-Type', '')
                if 'charset=' in content_type:
                    encoding = content_type.split('charset=')[-1].strip()
                else:
                    encoding = 'latin-1'
                return resp.read().decode(encoding, errors='replace')
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


def strip_latinlibrary_boilerplate(text):
    """Remove The Latin Library navigation footer."""
    # The Latin Library pages end with a nav block containing "The Latin Library" links
    footer_patterns = [
        r'\s*The Latin Library\s*$',
        r'\s*The Classics Page\s*',
        r'\s*Christian Latin\s*',
    ]
    for pattern in footer_patterns:
        m = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if m:
            text = text[:m.start()]
    return text.strip()


# ── Letter splitter ───────────────────────────────────────────────────────────

def roman_to_int(s):
    """Convert roman numeral string to int."""
    try:
        return int(s)
    except ValueError:
        pass
    val_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result = 0
    prev = 0
    for ch in reversed(s.strip().upper()):
        v = val_map.get(ch, 0)
        if v < prev:
            result -= v
        else:
            result += v
        prev = v
    return result if result > 0 else None


# Pattern matching Roman numeral letter headers in the Variae.
# Books 1-5, 8-12: "I. ANASTASIO IMPERATORI THEODERICUS REX."
# Books 6-7: "I. FORMULA CONSULATUS."  (administrative formulas)
# The header is at the start of a line (possibly with leading whitespace).
# We match: Roman numerals (including IIII) + period + ALL-CAPS text of 5+ chars.
LETTER_HEADER_RE = re.compile(
    r'(?:^|\n)\s*((?:[IVXLCDM]{1,10}|IIII)\.\s+[A-Z][A-Z0-9\s\.\,\(\)\/]{4,})',
    re.MULTILINE
)


def strip_page_title_block(text):
    """
    Remove the Latin Library page title block that appears before letter I.

    The block looks like:
        Cassiodorus: Variae I
        MAGNI AURELII CASSIODORI SENATORIS
        V. C. ET INL. ...
        VARIARUM LIBRI DUODECIM
        LIBER PRIMUS

    We strip everything up to and including the "LIBER ..." line.
    """
    # Find the last occurrence of LIBER (PRIMUS/SECUNDUS/etc. or a roman numeral)
    liber_re = re.compile(
        r'\nLIBER\s+(?:PRIMUS|SECUNDUS|TERTIUS|QUARTUS|QUINTUS|SEXTUS|SEPTIMUS|OCTAVUS|NONUS|DECIMUS|[IVXLCDM]+|XI|XII)\b[^\n]*',
        re.IGNORECASE
    )
    matches = list(liber_re.finditer(text))
    if matches:
        last_match = matches[-1]
        text = text[last_match.end():]
    return text


def split_book_into_letters(text, book_label):
    """
    Split a book page into individual letters using Roman numeral headers.

    Returns list of dicts: {roman, number, header, text}
    """
    text = strip_latinlibrary_boilerplate(text)
    text = strip_page_title_block(text)

    # Normalize: prepend newline so first letter can be matched
    if not text.startswith('\n'):
        text = '\n' + text

    # Find all letter headers
    headers = list(LETTER_HEADER_RE.finditer(text))

    if len(headers) < 2:
        loose_re = re.compile(
            r'(?:^|\n)\s*((?:[IVXLCDM]{1,8}|IIII)\.\s+[A-Z][^\n]{5,})',
            re.MULTILINE
        )
        headers = list(loose_re.finditer(text))

    if not headers:
        print(f"    [{book_label}] No letter headers found — treating as single text")
        return [{'roman': 'praef', 'number': 0, 'header': f'Book {book_label}', 'text': text}]

    letters = []
    for i, match in enumerate(headers):
        header_line = match.group(1).strip()

        roman_match = re.match(r'^((?:[IVXLCDM]{1,10}|IIII))\.', header_line)
        if not roman_match:
            continue
        roman_str = roman_match.group(1)
        number = roman_to_int(roman_str)
        if number is None:
            continue

        start = match.start(1)
        end = headers[i + 1].start(1) if i + 1 < len(headers) else len(text)
        letter_text = text[start:end].strip()

        if len(letter_text) > 20:
            letters.append({
                'roman': roman_str,
                'number': number,
                'header': header_line,
                'text': letter_text,
            })

    return letters


def parse_cassiodorus_recipient(header):
    """
    Extract recipient name from a Cassiodorus header like:
    "I. ANASTASIO IMPERATORI THEODERICUS REX."
    Returns a cleaned name string or None.
    """
    # Remove the leading roman numeral + period
    header = re.sub(r'^[IVXLCDM]+\.\s*', '', header.strip())
    # Remove the sender part ("THEODERICUS REX.", "CASSIODORUS SENATOR PP." etc.)
    sender_patterns = [
        r'\s+THEODERICUS\s+REX\.?$',
        r'\s+CASSIODORUS\s+SENATOR\s*\.?$',
        r'\s+CASSIODORUS\s+PP\.?$',
        r'\s+REX\.?$',
    ]
    for pattern in sender_patterns:
        header = re.sub(pattern, '', header, flags=re.IGNORECASE).strip()
    # Title-case the result
    name = header.strip(' .')
    if name:
        return name[:100]
    return None


# ── Database helpers ──────────────────────────────────────────────────────────

def get_sender_id(cursor):
    """Get Cassiodorus author id."""
    cursor.execute("SELECT id FROM authors WHERE id=?", (CASSIODORUS_SENDER_ID,))
    row = cursor.fetchone()
    return row[0] if row else None


def ensure_collection(cursor):
    cursor.execute("SELECT id FROM collections WHERE slug=?", (COLLECTION,))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT OR IGNORE INTO collections
                (slug, author_name, title, letter_count, date_range,
                 latin_source_url, scrape_status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        ''', (
            COLLECTION,
            'Cassiodorus',
            'Variae',
            468,
            '506-538',
            'https://www.thelatinlibrary.com/cassiodorus.html',
        ))


# ── Main scraper ──────────────────────────────────────────────────────────────

def scrape_cassiodorus(conn):
    cursor = conn.cursor()
    print("\n" + "=" * 60)
    print("Scraping Cassiodorus Variae (Latin) from The Latin Library...")

    ensure_collection(cursor)
    conn.commit()

    sender_id = get_sender_id(cursor)
    if not sender_id:
        print(f"  WARNING: No author record for sender_id {CASSIODORUS_SENDER_ID}")

    # Remove the single bad existing Cassiodorus record if it came from a bad scrape
    cursor.execute(
        "SELECT id, ref_id, source_url FROM letters WHERE collection=? LIMIT 5",
        (COLLECTION,)
    )
    existing = cursor.fetchall()
    print(f"  Existing Cassiodorus records: {len(existing)}")
    for row in existing:
        print(f"    {row[1]} | {row[2]}")

    total_inserted = 0
    total_updated = 0

    for book_label, url in BOOK_URLS:
        is_praef = book_label == 'praef'
        try:
            book_num = int(book_label)
        except ValueError:
            book_num = 0

        print(f"\n  Book {book_label}: {url}")
        time.sleep(0.5)

        html = fetch_url(url)
        if not html:
            print(f"  WARNING: Could not fetch {url}")
            continue

        page_text = html_to_text(html)
        if len(page_text) < 50:
            print(f"  WARNING: Very short page content ({len(page_text)} chars)")
            continue

        letters = split_book_into_letters(page_text, book_label)
        print(f"  Split into {len(letters)} letter(s)")

        for letter in letters:
            letter_num_in_book = letter['number']
            roman = letter['roman']
            text = letter['text']
            header = letter['header']

            if is_praef:
                ref_id = f"{COLLECTION}.praef"
                global_letter_num = 0
            else:
                ref_id = f"{COLLECTION}.{book_num}.{letter_num_in_book}"
                global_letter_num = letter_num_in_book

            recipient_name = parse_cassiodorus_recipient(header)
            subject = f"Book {book_label}, Letter {roman}: {recipient_name}" if recipient_name else f"Book {book_label}, Letter {roman}"

            # Check for existing record
            cursor.execute(
                "SELECT id, latin_text FROM letters WHERE ref_id=?",
                (ref_id,)
            )
            existing_row = cursor.fetchone()

            if existing_row:
                if not existing_row[1]:
                    cursor.execute(
                        "UPDATE letters SET latin_text=?, source_url=?, subject_summary=? WHERE id=?",
                        (text, url, subject, existing_row[0])
                    )
                    total_updated += 1
                # else already has Latin text, skip
            else:
                cursor.execute('''
                    INSERT OR IGNORE INTO letters
                        (collection, book, letter_number, ref_id, sender_id,
                         subject_summary, latin_text, source_url,
                         year_min, year_max, year_approx)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 506, 538, 522)
                ''', (
                    COLLECTION,
                    book_num,
                    global_letter_num,
                    ref_id,
                    sender_id,
                    subject,
                    text,
                    url,
                ))
                total_inserted += 1

        if (total_inserted + total_updated) % 50 == 0 and (total_inserted + total_updated) > 0:
            conn.commit()
            print(f"  Progress: {total_inserted} inserted, {total_updated} updated")

    conn.commit()

    # Update collection status
    cursor.execute(
        "UPDATE collections SET scrape_status='complete' WHERE slug=?",
        (COLLECTION,)
    )
    conn.commit()

    total = total_inserted + total_updated
    print(f"\n  Done: {total_inserted} new, {total_updated} updated = {total} Cassiodorus letters")
    return total


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)

    total = scrape_cassiodorus(conn)

    print("\n" + "=" * 60)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT collection,
               COUNT(*) as total,
               SUM(CASE WHEN latin_text IS NOT NULL THEN 1 ELSE 0 END) as latin,
               SUM(CASE WHEN english_text IS NOT NULL THEN 1 ELSE 0 END) as english
        FROM letters
        WHERE collection='cassiodorus'
        GROUP BY collection
    ''')
    print("\nDB verification:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} total, {row[2]} with Latin, {row[3]} with English")

    conn.close()


if __name__ == '__main__':
    main()

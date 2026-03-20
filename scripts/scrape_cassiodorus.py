#!/usr/bin/env python3
"""
scrape_cassiodorus.py — Scrape ALL of Cassiodorus's Variae from The Latin Library.

Sources:
  Preface:  https://www.thelatinlibrary.com/cassiodorus/varia.praef.shtml
  Books:    https://www.thelatinlibrary.com/cassiodorus/varia1.shtml  (1-12)
  Epistulae: https://www.thelatinlibrary.com/cassiodorus/epist.shtml

Two header formats appear in the Variae:
  1. Inline (books 1-5, 8-12):
       I. ANASTASIO IMPERATORI THEODERICUS REX.
  2. Two-line (books 6-7, epist, praef bodies):
       I.
       FORMULA CONSULATUS.

Both are handled by split_into_letters().

Encoding: Latin Library pages default to latin-1.
DB timeout: 30 seconds (SQLite WAL mode safe for concurrent use).
Request delay: 0.5 s between pages.
"""

import os
import re
import sqlite3
import time
import urllib.request
from html.parser import HTMLParser

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
BASE_URL = 'https://www.thelatinlibrary.com/cassiodorus/'
COLLECTION = 'cassiodorus'
REQUEST_DELAY = 0.5  # seconds between HTTP requests

PAGES = [
    # (label, book_number_int_or_None, url_suffix)
    ('praef',   0,    'varia.praef.shtml'),
] + [
    (str(n),    n,    f'varia{n}.shtml')
    for n in range(1, 13)
] + [
    ('epist',   0,    'epist.shtml'),
]


# ---------------------------------------------------------------------------
# HTML extraction
# ---------------------------------------------------------------------------

class BodyTextExtractor(HTMLParser):
    """Strip HTML and return body text with paragraph breaks preserved."""

    def __init__(self):
        super().__init__()
        self.parts = []
        self.in_body = False
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.in_body = True
        if tag in ('script', 'style'):
            self._skip += 1
        if tag in ('p', 'br'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self._skip -= 1
        if tag == 'p':
            self.parts.append('\n')

    def handle_data(self, data):
        if self.in_body and self._skip <= 0:
            self.parts.append(data)

    def get_text(self):
        raw = ''.join(self.parts)
        # Collapse more-than-2 consecutive newlines
        return re.sub(r'\n{3,}', '\n\n', raw).strip()


def html_to_text(html: str) -> str:
    p = BodyTextExtractor()
    p.feed(html)
    return p.get_text()


def strip_footer(text: str) -> str:
    """Remove The Latin Library navigation boilerplate at page end."""
    # The footer starts with a line like "Cassiodorus" followed by "Christian Latin" etc.
    # It's always near the bottom — find the first occurrence of these nav tokens.
    for marker in ('Cassiodorus \t', 'The Latin Library \t', 'The Classics Page'):
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx]
    return text.strip()


# ---------------------------------------------------------------------------
# HTTP fetch
# ---------------------------------------------------------------------------

def fetch_url(url: str, retries: int = 3) -> str | None:
    headers = {'User-Agent': 'RomanLettersResearch/1.0 (academic project)'}
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                content_type = resp.headers.get('Content-Type', '')
                if 'charset=' in content_type:
                    enc = content_type.split('charset=')[-1].strip()
                else:
                    enc = 'latin-1'
                return resp.read().decode(enc, errors='replace')
        except Exception as exc:
            wait = 1.5 * (attempt + 1)
            print(f'    [warn] fetch failed (attempt {attempt + 1}): {exc}')
            if attempt < retries - 1:
                time.sleep(wait)
    return None


# ---------------------------------------------------------------------------
# Roman numeral helpers
# ---------------------------------------------------------------------------

_ROMAN_VALUES = {'I': 1, 'V': 5, 'X': 10, 'L': 50,
                 'C': 100, 'D': 500, 'M': 1000}


def roman_to_int(s: str) -> int | None:
    """Convert a Roman numeral string to int; return None on failure."""
    s = s.strip().upper()
    # Sanity: must consist only of valid Roman numeral characters
    if not re.fullmatch(r'[IVXLCDM]+', s):
        return None
    result = 0
    prev = 0
    for ch in reversed(s):
        v = _ROMAN_VALUES.get(ch, 0)
        if v == 0:
            return None
        if v < prev:
            result -= v
        else:
            result += v
        prev = v
    return result if result > 0 else None


# ---------------------------------------------------------------------------
# Letter splitting
# ---------------------------------------------------------------------------

# Pattern A: Roman numeral + period + space + ALL-CAPS title on same line
#   "I. ANASTASIO IMPERATORI THEODERICUS REX."
PATTERN_INLINE = re.compile(
    r'(?:^|\n)([ \t]*)([IVXLCDM]{1,10})\.([ \t]+)([\[A-Z][A-Z0-9\s\.\,\(\)\/\[\]]{4,})',
    re.MULTILINE
)

# Pattern B: Roman numeral on its own line, title on next line
#   "I. \n FORMULA CONSULATUS."  or  "I.\nFORMULA CONSULATUS."
#   Also handles "[GELASIUS] THEODERICO REGI." (bracket-prefixed names)
PATTERN_TWOLINE = re.compile(
    r'(?:^|\n)([ \t]*)([IVXLCDM]{1,10})\.[ \t]*\n[ \t]*([\[A-Z][A-Z0-9\s\.\,\(\)\/\[\]]{4,})',
    re.MULTILINE
)


def _find_headers(text: str):
    """
    Return list of (match_start, roman_str, title_str) for all letter headers,
    automatically detecting whether the page uses inline or two-line format.
    """
    inline_matches = list(PATTERN_INLINE.finditer(text))
    twoline_matches = list(PATTERN_TWOLINE.finditer(text))

    # Exclude the book title line which also matches the inline pattern:
    # "V. C. ET INL. EXQUAEST. PAL. ..." — this starts with "V." at position 0 and
    # is part of the author byline.  Skip any match whose roman numeral is V and
    # the title contains "C. ET INL" (the standard abbreviation for vir clarissimus).
    def is_byline(m, title):
        return bool(re.search(r'C\.\s+ET\s+INL', title))

    if len(inline_matches) >= len(twoline_matches):
        result = []
        for m in inline_matches:
            roman = m.group(2)
            title = m.group(4).strip()
            if is_byline(m, title):
                continue
            result.append((m.start(), roman, title))
        return result
    else:
        result = []
        for m in twoline_matches:
            roman = m.group(2)
            title = m.group(3).strip()
            if is_byline(m, title):
                continue
            result.append((m.start(), roman, title))
        return result


def split_into_letters(text: str, page_label: str):
    """
    Split page text into individual letters/formulae.

    Returns list of dicts:
        roman    — Roman numeral string ("I", "II", …)
        number   — Integer value of roman numeral
        header   — Full header line(s) as found on page
        text     — Full letter text including header
    """
    text = strip_footer(text)
    headers = _find_headers(text)

    if not headers:
        print(f'    [{page_label}] No letter headers found — treating page as single entry')
        return [{'roman': page_label, 'number': 0, 'header': page_label, 'text': text}]

    letters = []
    for i, (start, roman_str, title_str) in enumerate(headers):
        end = headers[i + 1][0] if i + 1 < len(headers) else len(text)
        letter_text = text[start:end].strip()
        number = roman_to_int(roman_str)
        if number is None:
            print(f'    [{page_label}] Could not parse Roman numeral: {roman_str!r} — skipping')
            continue
        if len(letter_text) < 20:
            continue
        letters.append({
            'roman':  roman_str,
            'number': number,
            'header': title_str,
            'text':   letter_text,
        })

    return letters


# ---------------------------------------------------------------------------
# Recipient extraction
# ---------------------------------------------------------------------------

_SENDER_SUFFIXES = [
    r'\s+THEODERICUS\s+REX\.?',
    r'\s+CASSIODORUS\s+(?:SENATOR|PP|V\.?\s*C\.?)\.?',
    r'\s+REX\.?',
]
_SENDER_RE = re.compile('(?:' + '|'.join(_SENDER_SUFFIXES) + r')\s*$', re.IGNORECASE)


def extract_recipient(header: str, roman_str: str) -> str | None:
    """
    Attempt to extract a recipient name from a header like:
        "ANASTASIO IMPERATORI THEODERICUS REX."
    Returns up to 100 chars, or None.
    """
    h = header.strip()
    # Remove trailing period
    h = h.rstrip('.')
    # Remove known sender suffixes
    h = _SENDER_RE.sub('', h).strip()
    if h:
        return h[:100]
    return None


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_cassiodorus_sender_id(cur) -> int | None:
    cur.execute("SELECT id FROM authors WHERE name LIKE '%assio%'")
    row = cur.fetchone()
    if row:
        return row[0]
    print('  [warn] Cassiodorus author not found in authors table!')
    return None


def ensure_collection(cur):
    cur.execute("SELECT id FROM collections WHERE slug = ?", (COLLECTION,))
    if not cur.fetchone():
        cur.execute('''
            INSERT OR IGNORE INTO collections
                (slug, author_name, title, letter_count, date_range,
                 latin_source_url, scrape_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            COLLECTION, 'Cassiodorus', 'Variae',
            468, '506-538',
            'https://www.thelatinlibrary.com/cassiodorus.html',
            'pending',
        ))


def upsert_letter(cur, *, collection, book, letter_number, ref_id,
                  sender_id, subject, latin_text, source_url) -> str:
    """Insert or update a letter. Returns 'inserted', 'updated', or 'skipped'."""
    cur.execute("SELECT id, latin_text FROM letters WHERE ref_id = ?", (ref_id,))
    existing = cur.fetchone()
    if existing:
        existing_id, existing_latin = existing
        if not existing_latin:
            cur.execute(
                "UPDATE letters SET latin_text=?, source_url=?, subject_summary=? WHERE id=?",
                (latin_text, source_url, subject, existing_id)
            )
            return 'updated'
        return 'skipped'
    else:
        cur.execute('''
            INSERT OR IGNORE INTO letters
                (collection, book, letter_number, ref_id, sender_id,
                 subject_summary, latin_text, source_url,
                 year_min, year_max, year_approx)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 506, 538, 522)
        ''', (collection, book, letter_number, ref_id, sender_id,
              subject, latin_text, source_url))
        return 'inserted'


# ---------------------------------------------------------------------------
# Main scraper
# ---------------------------------------------------------------------------

def scrape_cassiodorus(conn):
    cur = conn.cursor()
    print('=' * 65)
    print('Scraping Cassiodorus Variae from The Latin Library')
    print('=' * 65)

    ensure_collection(cur)
    conn.commit()

    sender_id = get_cassiodorus_sender_id(cur)

    counts = {'inserted': 0, 'updated': 0, 'skipped': 0}

    for label, book_num, url_suffix in PAGES:
        url = BASE_URL + url_suffix
        is_epist = (label == 'epist')
        is_praef = (label == 'praef')

        print(f'\n  [{label}] {url}')
        time.sleep(REQUEST_DELAY)

        html = fetch_url(url)
        if not html:
            print(f'  [ERROR] Could not fetch {url}')
            continue

        page_text = html_to_text(html)
        if len(page_text) < 50:
            print(f'  [warn] Very short page ({len(page_text)} chars) — skipping')
            continue

        letters = split_into_letters(page_text, label)
        print(f'    Found {len(letters)} letters/formulae')

        for letter in letters:
            num = letter['number']
            roman = letter['roman']
            title = letter['header']
            text = letter['text']

            # Build ref_id
            if is_praef:
                ref_id = f'{COLLECTION}.praef.{num}' if num > 0 else f'{COLLECTION}.praef'
            elif is_epist:
                ref_id = f'{COLLECTION}.epist.{num}'
            else:
                ref_id = f'{COLLECTION}.{book_num}.{num}'

            recipient = extract_recipient(title, roman)
            if recipient:
                subject = f'Book {label}, Letter {roman}: {recipient}'
            else:
                subject = f'Book {label}, Letter {roman}: {title[:60]}'

            result = upsert_letter(
                cur,
                collection=COLLECTION,
                book=book_num if not (is_praef or is_epist) else None,
                letter_number=num,
                ref_id=ref_id,
                sender_id=sender_id,
                subject=subject,
                latin_text=text,
                source_url=url,
            )
            counts[result] += 1

        conn.commit()
        total_so_far = counts['inserted'] + counts['updated']
        print(f'    Running total — inserted: {counts["inserted"]}, '
              f'updated: {counts["updated"]}, skipped: {counts["skipped"]}')

    # Final commit and collection status update
    cur.execute(
        "UPDATE collections SET scrape_status='complete' WHERE slug=?",
        (COLLECTION,)
    )
    conn.commit()

    print()
    print('=' * 65)
    print(f'Done: {counts["inserted"]} inserted, {counts["updated"]} updated, '
          f'{counts["skipped"]} skipped')

    # Verification summary
    cur.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN latin_text IS NOT NULL THEN 1 ELSE 0 END) as has_latin,
            SUM(CASE WHEN book IS NOT NULL THEN 1 ELSE 0 END) as in_books
        FROM letters
        WHERE collection = ?
    ''', (COLLECTION,))
    row = cur.fetchone()
    print(f'\nDB summary for {COLLECTION!r}:')
    print(f'  Total records : {row[0]}')
    print(f'  With Latin    : {row[1]}')
    print(f'  In books 1-12 : {row[2]}')

    cur.execute('''
        SELECT book, COUNT(*) as cnt
        FROM letters
        WHERE collection = ? AND book IS NOT NULL
        GROUP BY book ORDER BY CAST(book AS INTEGER)
    ''', (COLLECTION,))
    print('\n  Per-book counts:')
    for brow in cur.fetchall():
        print(f'    Book {brow[0]:>2}: {brow[1]}')

    return counts


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    conn = sqlite3.connect(DB_PATH, timeout=30)
    try:
        scrape_cassiodorus(conn)
    finally:
        conn.close()

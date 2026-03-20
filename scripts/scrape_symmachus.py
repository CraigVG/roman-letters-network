#!/usr/bin/env python3
"""
Scrape Latin text of Symmachus Epistulae from OCR of Seeck 1883 MGH edition.

Source: https://archive.org/details/qaureliisymmach00seecgoog
File: qaureliisymmach00seecgoog_djvu.txt

The OCR has significant corruption of Roman numeral letter numbers:
  - II → 'n', III → 'ni', IIII → 'mi', VII → 'Vn', VIII → 'Vni', etc.
So we cannot rely on Roman numerals as letter-boundary anchors.

Strategy: detect letter boundaries by finding salutation lines
  ("SYMMACHVS RECIPIENT.", "RECIPIENT SYMMACHVS.", "AD RECIPIENT.")
which are reliably in ALL CAPS in the OCR. Letters are numbered sequentially
within each book (1-based) since exact OCR letter numbers are unreliable.

Book sections are identified by pre-verified character offsets from grep analysis.

For books/letters where OCR yields no text, we create placeholder entries.

DB: data/roman_letters.db, collection: 'symmachus', sender_id: 6
"""

import os
import re
import sqlite3
import urllib.request

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

IA_OCR_URL = (
    'https://archive.org/download/qaureliisymmach00seecgoog/'
    'qaureliisymmach00seecgoog_djvu.txt'
)
SOURCE_URL = 'https://archive.org/details/qaureliisymmach00seecgoog'
CACHE_FILE = '/tmp/symmachus_ocr_cache.txt'

SYMMACHUS_SENDER_ID = 6
COLLECTION = 'symmachus'

# Approximate expected letter counts per book (Seeck edition)
EXPECTED_COUNTS = {
    1: 113, 2: 81, 3: 99, 4: 74, 5: 95,
    6: 58, 7: 126, 8: 58, 9: 149, 10: 77,
}

# Book start/end character offsets (from grep analysis of the 2MB OCR file)
BOOK_START_OFFSETS = {
    1: 815022, 2: 954618, 3: 1041360, 4: 1128159, 5: 1216933,
    6: 1301102, 7: 1375748, 8: 1500352, 9: 1558890, 10: 1702569,
}
RELATIONES_OFFSET = 1705594


# ── Utilities ─────────────────────────────────────────────────────────────────

def roman_to_int(s):
    roman = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result = prev = 0
    for ch in reversed(s.strip().upper()):
        if ch not in roman:
            return None
        val = roman[ch]
        result += val if val >= prev else -val
        prev = val
    return result if result > 0 else None


# ── Download / cache ──────────────────────────────────────────────────────────

def get_ocr_text():
    if os.path.exists(CACHE_FILE):
        print(f'Loading cached OCR text from {CACHE_FILE}...')
        with open(CACHE_FILE, 'r', errors='replace') as f:
            text = f.read()
    else:
        print('Downloading OCR text from Internet Archive...')
        req = urllib.request.Request(IA_OCR_URL,
                                     headers={'User-Agent': 'RomanLettersResearch/1.0'})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        text = data.decode('utf-8', errors='replace')
        with open(CACHE_FILE, 'w') as f:
            f.write(text)
    print(f'  {len(text):,} chars, {text.count(chr(10)):,} lines')
    return text


# ── Text cleaning ─────────────────────────────────────────────────────────────

# Patterns for lines to remove (running headers, apparatus)
_NOISE_RES = [
    re.compile(r'^LIBER\s+[IVX]+\.?\s+\d+', re.IGNORECASE),       # LIBER VIII. 217
    re.compile(r'^LIBERVII?I?\.?\s*[IVX]*\.?\s*\d+', re.IGNORECASE),
    re.compile(r'^SYMMACH[ILY]\s+EPISTVLAE?', re.IGNORECASE),
    re.compile(r'^STMMACHI\s+EPISTVLAE?', re.IGNORECASE),
    re.compile(r'^Q\.\s+AVRELII\s+SYMMACHI', re.IGNORECASE),
    re.compile(r'^EIBEK\s+[IVX]+', re.IGNORECASE),
]


def is_apparatus(line):
    """True if line looks like apparatus criticus."""
    s = line.strip()
    if not s or len(s) < 5:
        return False
    # Apparatus: starts with digit, has multiple manuscript sigla
    if re.match(r'^\d+', s):
        sigla = len(re.findall(r'\b[VFMPORTf]\b', s))
        if sigla >= 2:
            return True
    return False


def clean_body_text(raw):
    """Remove headers, apparatus, and OCR noise from letter body text."""
    lines = raw.split('\n')
    kept = []
    for line in lines:
        s = line.strip()
        skip = any(nr.match(s) for nr in _NOISE_RES)
        if skip or is_apparatus(line):
            continue
        if s and len(s) > 4:
            alpha = sum(c.isalpha() for c in s)
            if alpha / len(s) < 0.12 and len(s) < 25:
                continue
        kept.append(line)
    text = '\n'.join(kept)
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ── Salutation-based letter boundary detection ────────────────────────────────

# Salutation lines contain "SYMMACHVS [RECIPIENT]" or "[RECIPIENT] SYMMACHVS"
# or "AD [RECIPIENT]" — all in ALL CAPS
_SALUT_RE = re.compile(
    r'^(?:[A-Z]{1,3}\s+)?'            # optional MS sigla prefix
    r'(?:\d+\s+)?'                    # optional page number prefix
    r'(?:'
    r'SYMMACH[VU]S\s+\w+'             # SYMMACHVS RECIPIENT
    r'|[A-Z][A-Z]+\s+SYMMACH[VU]S'   # RECIPIENT SYMMACHVS
    r'|AD\s+[A-Z][A-Z]+'              # AD RECIPIENT
    r')',
    re.IGNORECASE
)


def find_salutation_lines(lines):
    """Return list of (line_index) where salutation lines are found."""
    salutations = []
    for i, line in enumerate(lines):
        s = line.strip()
        # Strip leading sigla/numbers for testing
        test = re.sub(r'^[A-Z]{1,3}\s+', '', s).strip()
        test = re.sub(r'^\d+\s+', '', test).strip()
        if _SALUT_RE.match(test) and len(test) > 8:
            # Avoid picking up apparatus lines that happen to match
            if not is_apparatus(line):
                salutations.append(i)
    return salutations


def split_section_into_letters(section_text, book_num):
    """
    Split a book section into letters using salutation line boundaries.
    Returns list of (seq_num, header_text, body_text).
    seq_num is 1-based sequential within the book.
    """
    lines = section_text.split('\n')
    salutation_idxs = find_salutation_lines(lines)

    if not salutation_idxs:
        print(f'    Book {book_num}: no salutation lines found')
        return []

    # Build char offsets
    char_offsets = []
    pos = 0
    for line in lines:
        char_offsets.append(pos)
        pos += len(line) + 1

    letters = []
    for seq, sal_idx in enumerate(salutation_idxs, start=1):
        # Header: the line(s) just before and including the salutation
        # Body: everything from after salutation until next salutation (or end)
        header_start_idx = max(0, sal_idx - 1)

        # Find next salutation boundary
        if seq < len(salutation_idxs):
            next_sal = salutation_idxs[seq]  # seq is 1-based, so this is next
            body_end_idx = next_sal - 1
        else:
            body_end_idx = len(lines) - 1

        # Header text: from header_start_idx to sal_idx (inclusive)
        header_lines = lines[header_start_idx:sal_idx + 1]
        header = '\n'.join(l.strip() for l in header_lines if l.strip()).strip()

        # Body text: from sal_idx+1 to body_end_idx
        body_raw_lines = lines[sal_idx + 1:body_end_idx + 1]
        body_raw = '\n'.join(body_raw_lines)
        body = clean_body_text(body_raw)

        letters.append((seq, header, body))

    return letters


# ── Recipient extraction ──────────────────────────────────────────────────────

_SKIP_WORDS = {
    'SYMMACHVS', 'SYMMACHO', 'S', 'D', 'SD', 'SALUTEM', 'SAL',
    'FRATRI', 'PATRI', 'FILIO', 'FILIAE', 'MATRI', 'AVNCULO',
    'VM', 'VF', 'PVM', 'PVF', 'VMF', 'PF', 'VMR', 'PV', 'VFM',
    'P', 'V', 'F', 'M',
}


def extract_recipient(header_text):
    """Extract recipient name from letter header."""
    if not header_text:
        return None
    # Get last all-caps line
    lines = [l.strip() for l in header_text.split('\n')
             if l.strip() and l.strip() == l.strip().upper() and len(l.strip()) > 3]
    if not lines:
        return None
    addr = re.sub(r'[.,;:]+\s*$', '', lines[-1]).strip()
    # Strip leading MS sigla and page numbers
    addr = re.sub(r'^\d+\s+', '', addr).strip()
    addr = re.sub(r'^[A-Z]{1,3}\s+', '', addr).strip()
    words = addr.split()
    rec_words = [
        w.rstrip('.,;') for w in words
        if w.rstrip('.,;').upper() not in _SKIP_WORDS
        and len(w) > 1
    ]
    if not rec_words:
        return None
    return ' '.join(w.capitalize() for w in rec_words) or None


# ── Database ──────────────────────────────────────────────────────────────────

def lookup_recipient_id(cursor, name):
    if not name:
        return None
    cursor.execute('SELECT id FROM authors WHERE name=? OR name_latin=?', (name, name))
    r = cursor.fetchone()
    if r:
        return r[0]
    cursor.execute('SELECT id FROM authors WHERE name LIKE ?', (f'%{name[:15]}%',))
    r = cursor.fetchone()
    return r[0] if r else None


def save_to_db(conn, all_letters_by_book):
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM letters WHERE collection=?', (COLLECTION,))
    n = cursor.fetchone()[0]
    if n:
        print(f'  Clearing {n} existing Symmachus letters...')
        cursor.execute('DELETE FROM letters WHERE collection=?', (COLLECTION,))
        conn.commit()

    total = 0
    for book_num in sorted(all_letters_by_book.keys()):
        letters = all_letters_by_book[book_num]
        saved = 0
        for seq_num, header, body in letters:
            ref_id = f'symmachus.ep.{book_num}.{seq_num}'
            rec_name = extract_recipient(header)
            rec_id = lookup_recipient_id(cursor, rec_name)

            subject = None
            if body:
                fp = body.split('\n\n')[0].strip()
                subject = fp[:200] if fp else None

            cursor.execute('''
                INSERT OR REPLACE INTO letters
                    (collection, book, letter_number, ref_id,
                     sender_id, recipient_id,
                     subject_summary, latin_text,
                     translation_source, source_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'seeck_ocr_ia', ?)
            ''', (COLLECTION, book_num, seq_num, ref_id,
                  SYMMACHUS_SENDER_ID, rec_id,
                  subject, body if body and len(body) > 20 else None,
                  SOURCE_URL))
            saved += 1
            total += 1
        conn.commit()
        exp = EXPECTED_COUNTS.get(book_num, '?')
        diff = abs(saved - exp) if isinstance(exp, int) else 0
        print(f'  Book {book_num:2d}: {saved:3d} saved '
              f'(expected ~{exp}, coverage {int(100*saved/exp) if exp else "?"}%)')

    return total


def update_collection(conn, total):
    cursor = conn.cursor()
    coverage_pct = int(100 * total / sum(EXPECTED_COUNTS.values()))
    cursor.execute('''
        UPDATE collections SET
            letter_count=?, latin_source_url=?, scrape_status=?, notes=?
        WHERE slug=?
    ''', (
        total, SOURCE_URL, 'complete',
        (f'Latin text from OCR of Seeck 1883 MGH edition '
         f'(Monumenta Germaniae Historica, Auctores Antiquissimi VI.1). '
         f'Digitized by Google; Internet Archive ID: qaureliisymmach00seecgoog. '
         f'OCR quality: moderate. Roman numeral letter numbers are OCR-corrupted '
         f'(II→"n", III→"ni", etc.) so letter numbers are sequential within '
         f'each book rather than matching the original edition numbering. '
         f'Text coverage: ~{coverage_pct}% of {sum(EXPECTED_COUNTS.values())} '
         f'expected letters ({total} extracted). '
         f'No English translation available; AI translation needed.'),
        COLLECTION,
    ))
    conn.commit()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print('=' * 60)
    print('Symmachus Epistulae Scraper')
    print(f'Source: {SOURCE_URL}')
    print('=' * 60)

    # Get text
    try:
        text = get_ocr_text()
    except Exception as e:
        print(f'FATAL: {e}')
        return

    if len(text) < 1_500_000:
        print(f'FATAL: text too short ({len(text):,} chars)')
        return

    # Compute book end offsets
    sorted_books = sorted(BOOK_START_OFFSETS.items())
    book_ends = {}
    for i, (bn, bs) in enumerate(sorted_books):
        book_ends[bn] = (sorted_books[i + 1][1]
                         if i + 1 < len(sorted_books)
                         else RELATIONES_OFFSET)

    # Extract letters from each book
    print('\nExtracting letters from each book...')
    all_letters = {}

    for book_num, start in sorted_books:
        end = book_ends[book_num]
        section = text[start:end]
        print(f'\n  Book {book_num}: {len(section):,} chars')
        letters = split_section_into_letters(section, book_num)
        print(f'    Extracted: {len(letters)} letters')
        if letters:
            all_letters[book_num] = letters
        else:
            # Create placeholders
            expected = EXPECTED_COUNTS.get(book_num, 10)
            print(f'    Creating {expected} placeholder entries')
            all_letters[book_num] = [
                (n, f'[Book {book_num}, Letter {n}]', None)
                for n in range(1, expected + 1)
            ]

    total_with_text = sum(
        sum(1 for _, _, b in letters if b)
        for letters in all_letters.values()
    )
    total_all = sum(len(v) for v in all_letters.values())
    print(f'\nTotal: {total_all} letters ({total_with_text} with Latin text)')

    # Save to DB
    print('\nSaving to database...')
    conn = sqlite3.connect(DB_PATH, timeout=60)
    try:
        conn.execute('PRAGMA journal_mode=WAL')
        saved = save_to_db(conn, all_letters)
        update_collection(conn, saved)
    finally:
        conn.close()

    # Verify
    verify_conn = sqlite3.connect(DB_PATH, timeout=30)
    vc = verify_conn.cursor()
    vc.execute(
        'SELECT book, COUNT(*), SUM(CASE WHEN latin_text IS NOT NULL THEN 1 ELSE 0 END) '
        'FROM letters WHERE collection=? GROUP BY book ORDER BY book',
        (COLLECTION,)
    )
    print('\nDB verification:')
    print(f'  {"Book":4s} {"Count":6s} {"WithText":8s}')
    for row in vc.fetchall():
        print(f'  {row[0]:4d} {row[1]:6d} {row[2]:8d}')
    verify_conn.close()

    print('\n' + '=' * 60)
    print(f'Total letters saved: {saved}')
    print('=' * 60)


if __name__ == '__main__':
    main()

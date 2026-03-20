#!/usr/bin/env python3
"""
Scrape Gregory the Great's Register of Letters from Patrologia Latina vol 77 (Migne, 1849).
Source: /tmp/pl77_gregory.txt (OCR of PL vol 77)

PL 77 contains all 14 books of Gregory's Registrum Epistolarum (591-604 AD).
The register starts at line ~36757 with LIBER PRIMUS through LIBER DECIMUS QUARTUS.

Letter structure:
- Book headers: LIBER PRIMUS., LIBER SECUNDUS., etc.
- Letter headers: EPISTOLA PRIMA., EPISTOLA II., EPISTOLA III., etc.
- Two-column OCR = footnotes mixed in

We insert only letters NOT already in the database (ref_id based check).
"""

import sqlite3
import re
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'roman_letters.db')
TEXT_PATH = '/tmp/pl77_gregory.txt'
SOURCE_URL = 'https://archive.org/details/bim_early-english-books-1641-1700_1849_77'

COLLECTION = 'gregory_great'

# Line where the register starts
REGISTER_START = 36700
# Line where the register ends (after Book XIV)
REGISTER_END = 117829  # Start of the index section

# Book name -> book number mapping
BOOK_NAMES = {
    'PRIMUS': 1, 'SECUNDUS': 2, 'TERTIUS': 3, 'QUARTUS': 4,
    'QUINTUS': 5, 'QUINTTUS': 5, 'SEXTUS': 6, 'SEATUS': 6, 'SEPTIMUS': 7, 'OCTAVUS': 8,
    'NONUS': 9, 'DECIMUS': 10,
    'UNDECIMUS': 11,
    'DUODECIMUS': 12,
    'DECIMUS TERTIUS': 13,
    'DECIMUS QUARTUS': 14,
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6,
    'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12,
    'XIII': 13, 'XIV': 14,
}

# Roman numeral to integer for letter numbers
ROMAN_VALS = {
    'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000,
}

def roman_to_int(s):
    """Convert Roman numeral string to integer, with OCR error correction."""
    s = s.strip().upper()
    # Handle PRIMA, SECUNDA etc.
    ordinals = {
        'PRIMA': 1, 'SECUNDA': 2, 'TERTIA': 3, 'QUARTA': 4, 'QUINTA': 5,
        'SEXTA': 6, 'SEPTIMA': 7, 'OCTAVA': 8, 'NONA': 9, 'DECIMA': 10,
        'IL': 2, 'IIL': 3,  # OCR errors: IL for II, IIL for III
    }
    if s in ordinals:
        return ordinals[s]

    # Apply OCR correction for PL 77 two-column format
    # Common OCR errors: Y->V, J->I, A->X (in certain positions), N->M, H->M
    # Also: YV->IV, VIL->VII, VIIL->VIII, XIY->XIV, XVYII->XVII
    ocr_fixed = s
    # Fix specific known patterns before stripping
    ocr_fixed = re.sub(r'YV', 'IV', ocr_fixed)    # YV -> IV
    ocr_fixed = re.sub(r'Y([IVX])', r'V\1', ocr_fixed)   # Y followed by roman -> V
    ocr_fixed = re.sub(r'([IVX])Y', r'\1V', ocr_fixed)   # roman followed by Y -> V
    ocr_fixed = re.sub(r'^Y', 'V', ocr_fixed)     # leading Y -> V
    ocr_fixed = re.sub(r'Y$', 'V', ocr_fixed)     # trailing Y -> V
    ocr_fixed = re.sub(r'J', 'I', ocr_fixed)      # J -> I
    ocr_fixed = re.sub(r'l', 'I', ocr_fixed)      # lowercase l -> I (common OCR)
    ocr_fixed = re.sub(r't', '', ocr_fixed)       # trailing 't' is artifact
    # Specific patterns
    ocr_fixed = re.sub(r'IL$', 'II', ocr_fixed)   # IL at end -> II
    ocr_fixed = re.sub(r'IIL$', 'III', ocr_fixed) # IIL at end -> III
    ocr_fixed = re.sub(r'VIL$', 'VII', ocr_fixed) # VIL at end -> VII
    ocr_fixed = re.sub(r'VIIL$', 'VIII', ocr_fixed) # VIIL at end -> VIII
    ocr_fixed = re.sub(r'XIY', 'XIV', ocr_fixed)
    ocr_fixed = re.sub(r'[^IVXLCDM]', '', ocr_fixed)  # Keep only valid Roman chars

    if not ocr_fixed:
        return None

    result = 0
    prev = 0
    for ch in reversed(ocr_fixed):
        if ch not in ROMAN_VALS:
            return None
        val = ROMAN_VALS[ch]
        if val < prev:
            result -= val
        else:
            result += val
        prev = val
    return result if result > 0 else None


def is_page_header(line):
    """Detect running page headers in PL 77."""
    s = line.strip()
    # Pattern: NNN SANCTI GREGORII MAGNI NNN
    if re.match(r'^\d{3,4}\s+SANCTI\s+GREG', s):
        return True
    if re.match(r'^SANCTI\s+GREG[O0]R[I1]\s+MAGNI\s*\d*$', s):
        return True
    # Just page numbers
    if re.match(r'^#?\d{2,4}$', s):
        return True
    # EPISTOLARUM LIB. headings (running headers not letter starts)
    if re.match(r'^\d+\s*\|\s*EPISTOLARUM', s):
        return True
    if re.match(r'^EPISTOLARUM LIB\.', s):
        return True
    return False


def is_footnote_line(line):
    """Detect footnote lines in PL 77 (two-column OCR)."""
    s = line.strip()
    if not s:
        return False
    # Footnote markers: single letter + period/paren at start, or Erisr., Erist.
    if re.match(r'^Eri[s$][rt][\.\,]', s):  # OCR of EPIST. in footnotes
        return True
    # Lines starting with footnote reference like "a ", "b ", etc. + text about manuscripts
    # These typically reference edit/cod/mss etc.
    if re.match(r'^[a-z] ', s) and re.search(r'Edit|Cod|mss|lege|var|Vat|ib\.', s):
        return True
    # Lines with pipe separator (two-column split)
    if re.match(r'^\|', s) or re.match(r'.*\|\s+\w', s) and '|' in s[:20]:
        return True
    # Lines that start with "A ", "B " etc. followed by lowercase (footnote continuation)
    if re.match(r'^[A-H] [a-z]', s) and len(s) < 100:
        return True
    return False


def clean_pl77_text(lines):
    """
    Clean PL 77 two-column OCR text for a letter.

    The two-column layout means footnotes are interleaved with main text.
    Strategy: keep lines that look like main text, skip footnotes/headers.
    """
    cleaned = []
    in_footnote = False

    for raw in lines:
        s = raw.strip()

        if not s:
            if cleaned and cleaned[-1]:
                cleaned.append('')
            in_footnote = False
            continue

        if is_page_header(s):
            continue

        # Detect footnote start indicators
        # Footnotes: lines like "Erisr. |. — * Ita Edit..."
        if re.match(r'^Eri[s$][rt][\.\,]', s):
            in_footnote = True
            continue

        # Lines starting with lowercase letter then space = likely footnote continuation
        if re.match(r'^[a-z]\s', s) and not re.match(r'^(et|in|ad|de|ex|ut|si|se|ac|ab|id)\s', s):
            in_footnote = True
            continue

        # Lines starting with capital letter followed by lowercase and referencing manuscripts
        if in_footnote:
            # End footnote when we see what looks like real letter text
            # Real text: starts with uppercase word that's part of the letter
            if re.match(r'^[A-Z][a-z]{2,}', s) and len(s) > 30:
                # Could be main text resuming
                in_footnote = False
                cleaned.append(s)
            elif re.match(r'^Gregorius\s', s, re.I):
                in_footnote = False
                cleaned.append(s)
            # else skip
            continue

        # Skip lines that are clearly column artifacts
        if s in ('=', '—', '——', '———', '————', '-', '--'):
            continue
        if re.match(r'^[=\-—]+\s*$', s):
            continue

        cleaned.append(s)

    text = '\n'.join(cleaned)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


def parse_pl77_gregory(filepath):
    """
    Parse Gregory's register from PL 77.
    Returns list of {book, ep_num, text, header, ref_id}
    """
    with open(filepath, 'r', errors='replace') as f:
        lines = f.readlines()

    print(f"  Loaded {len(lines)} lines from {os.path.basename(filepath)}")

    # Book header patterns - handle OCR variants
    # LIBER QUINTTUS -> QUINTUS, LIBER SEATUS -> SEXTUS, _ LIBER SEPTIMUS-
    book_re = re.compile(
        r'^(?:[_\s]*LIBER\s+)'
        r'(PRIMUS|SECUNDUS|TERTIUS|QUARTUS|QUINTT?US|SEATUS|SEXTUS?|SEPTIMUS|OCTAVUS|NONUS'
        r'|DECIMUS\s+TERTIUS|DECIMUS\s+QUARTUS|UNDECIMUS|DUODECIMUS|DECIMUS)'
        r'[\s,.\-\*]*',
        re.IGNORECASE
    )
    # Also match "LIBER I.", "LIBER II." etc. and "LIBER XII. Al, LIBER X."
    book_roman_re = re.compile(r'^(?:[_\s]*)?LIBER\s+(XIV|XIII|XII|XI|IX|VIII|VII|VI|V|IV|III|II|I)[\s,.\*]*')

    # Letter header: "EPISTOLA PRIMA." or "EPISTOLA II." etc.
    # Must handle OCR noise: "485 EPISTOLA PRIMA." or "« EPISTOLA VII."
    # Also handle OCR-corrupted Roman numerals: YV=IV, VIL=VII, XIY=XIV, XVYII=XVII etc.
    ep_re = re.compile(
        r'(?:^|\d+\s+|[«\*\$a-z|\-—_]\s*|\*\s*)'
        r'EPISTOLA\s+'
        r'(PRIMA|SECUNDA|TERTIA|QUARTA|QUINTA|SEXTA|SEPTIMA|OCTAVA|NONA|DECIMA'
        r'|[MDCLXVIYJmdclxviyj]{1,10}[Ll]?)'  # Allow OCR chars Y,J,l mixed in
        r'[it]*[\s,.\*\|]*$',
        re.IGNORECASE
    )

    current_book = None
    current_ep = None
    current_lines = []
    results = []

    def save_current():
        nonlocal current_ep, current_lines
        if current_book is None or current_ep is None:
            return
        text = clean_pl77_text(current_lines)
        if len(text.strip()) > 50:
            results.append({
                'book': current_book,
                'ep_num': current_ep,
                'text': text,
                'header': '\n'.join(s.strip() for s in current_lines[:5] if s.strip())[:300],
            })
        current_ep = None
        current_lines = []

    for i in range(REGISTER_START, min(REGISTER_END, len(lines))):
        raw = lines[i]
        s = raw.strip()

        if not s:
            if current_ep is not None:
                current_lines.append('')
            continue

        # Check for book header (only on short lines to avoid false positives)
        m = book_re.match(s)
        if not m and len(s) < 60:
            m = book_roman_re.match(s)

        if m:
            save_current()
            book_str = m.group(1).strip().upper()
            # Try named first, then Roman numeral
            new_book = BOOK_NAMES.get(book_str)
            if new_book is None:
                new_book = roman_to_int(book_str)
            if new_book:
                current_book = new_book
                current_ep = None
                current_lines = []
            continue

        # Check for letter header
        m = ep_re.match(s)
        if m:
            save_current()
            ep_str = m.group(1).upper()
            ep_num = roman_to_int(ep_str)
            if ep_num and 1 <= ep_num <= 300:
                current_ep = ep_num
                current_lines = []
            continue

        if current_ep is not None:
            current_lines.append(s)

    save_current()
    return results


def get_existing_ref_ids(conn):
    """Get all existing ref_ids for gregory_great."""
    cur = conn.cursor()
    cur.execute("SELECT ref_id FROM letters WHERE collection = ?", (COLLECTION,))
    return {row[0] for row in cur.fetchall()}


def get_author_id(conn):
    """Get Gregory the Great's author ID."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM authors WHERE name LIKE '%Gregory%Great%' OR name = 'Gregory I'")
    row = cur.fetchone()
    if row:
        return row[0]
    # Try collection lookup
    cur.execute("SELECT id FROM authors WHERE name LIKE '%Gregory%' AND role = 'pope'")
    row = cur.fetchone()
    if row:
        return row[0]
    return None


def main():
    print("=== PL 77 Gregory the Great Register Scraper ===\n")

    if not os.path.exists(TEXT_PATH):
        print(f"ERROR: {TEXT_PATH} not found!")
        return 1

    print(f"Parsing {TEXT_PATH}...")
    letters = parse_pl77_gregory(TEXT_PATH)
    print(f"  Parsed {len(letters)} letters total")

    # Show book breakdown
    from collections import Counter
    book_counts = Counter(l['book'] for l in letters)
    print("  Book breakdown:")
    for book in sorted(book_counts.keys()):
        print(f"    Book {book}: {book_counts[book]} letters")

    if not letters:
        print("No letters found - check parsing logic")
        return 1

    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    # Get author ID
    author_id = get_author_id(conn)
    if not author_id:
        print("ERROR: Could not find Gregory the Great author ID")
        conn.close()
        return 1
    print(f"  Author ID: {author_id}")

    # Get existing ref_ids to avoid duplicates
    existing_refs = get_existing_ref_ids(conn)
    print(f"  Existing Gregory letters in DB: {len(existing_refs)}")

    # Get max letter_number
    cur.execute("SELECT COALESCE(MAX(letter_number), 0) FROM letters WHERE collection = ?", (COLLECTION,))
    max_letter_num = cur.fetchone()[0]

    inserted = 0
    skipped = 0

    for letter in letters:
        book = letter['book']
        ep_num = letter['ep_num']

        # Build ref_id matching new advent format: gregory_great.B.EEE
        ref_id = f"gregory_great.{book}.{ep_num}"
        # Also check MGH-style ref: gregory_great.mgh.B.EEE
        ref_id_mgh = f"gregory_great.mgh.{book}.{ep_num}"

        # Build BBLLL letter_number
        letter_number = book * 1000 + ep_num

        # Check if we already have this letter (by letter_number)
        cur.execute(
            "SELECT id FROM letters WHERE collection = ? AND letter_number = ?",
            (COLLECTION, letter_number)
        )
        if cur.fetchone():
            skipped += 1
            continue

        # Also check by ref_id variants
        if ref_id in existing_refs or ref_id_mgh in existing_refs:
            skipped += 1
            continue

        max_letter_num += 1
        summary = f"PL77 Book {book}, Ep {ep_num}: {letter['header'][:120]}"

        cur.execute("""
            INSERT INTO letters (
                collection, letter_number, ref_id,
                sender_id, latin_text, subject_summary, source_url,
                translation_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            COLLECTION, letter_number, ref_id,
            author_id, letter['text'], summary, SOURCE_URL,
            'none'
        ))
        inserted += 1

        if inserted % 50 == 0:
            conn.commit()
            print(f"  ... inserted {inserted} so far")

    conn.commit()

    print(f"\n{'='*50}")
    print(f"Inserted: {inserted}")
    print(f"Skipped (already in DB): {skipped}")

    cur.execute("SELECT COUNT(*) FROM letters WHERE collection = ?", (COLLECTION,))
    total = cur.fetchone()[0]
    print(f"Total Gregory letters in DB: {total}")

    # Show final book breakdown
    cur.execute("""
        SELECT letter_number/1000 as book, COUNT(*) as cnt
        FROM letters WHERE collection = ? AND letter_number > 0
        GROUP BY letter_number/1000
        ORDER BY letter_number/1000
    """, (COLLECTION,))
    print("\nFinal book breakdown:")
    for row in cur.fetchall():
        print(f"  Book {row[0]}: {row[1]} letters")

    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
Scrape Symmachus letters from the Archive.org OCR text of Seeck's edition.
Source: https://archive.org/details/qaureliisymmach00seecgoog
"""

import sqlite3
import re
import os
import sys
from collections import Counter

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'roman_letters.db')
OCR_PATH = '/tmp/symmachus_hocr.txt'
SOURCE_URL = 'https://archive.org/details/qaureliisymmach00seecgoog'


def roman_to_int(s):
    """Convert Roman numeral string to integer, handling OCR noise from old print.

    In this OCR text (Seeck edition, late 19th century German printing):
    - 'm' at end of Roman numeral = 'iii' (three I's resemble m in old typefaces)
    - 'mi' = 'iiii' = 4
    - 'n' before/after Roman chars often = 'ii'
    - 'Vm' = 'VIII' (special case)
    """
    # Remove parenthetical alternate numbers: "CVn (CI)" -> "CVn"
    s = re.sub(r'\([^)]*\)', '', s).strip()
    if not s:
        return None

    s_clean = s

    # Specific OCR substitutions (order matters - most specific first)
    ocr_fixes = [
        # VIII variants (V followed by noise)
        (r'\bVm\b', 'VIII'), (r'\bVni\b', 'VIII'), (r'\bVnn\b', 'VIII'),
        (r'\bVmi\b', 'VIII'), (r'\bVIUI\b', 'VIIII'),
        (r'\bVIU\b', 'VIII'), (r'\bVlll\b', 'VIII'), (r'\bVUI\b', 'VIII'),
        (r'\bVHI\b', 'VIII'), (r'\bVIllI\b', 'VIII'),
        # 'mi' = IIII = 4 (three I's + one I)
        (r'\bmi\b', 'IIII'),
        # 'ni' = III = 3
        (r'\bni\b', 'III'),
        # 'm' at end = III (three I's)
        (r'm\b', 'III'),
        # 'n' = II (two I's)
        (r'n\b', 'II'),
        # 'n' before another letter = 'II'
        (r'n(?=[IVXLCDivxlcd])', 'II'),
    ]

    for pattern, replacement in ocr_fixes:
        s_clean = re.sub(pattern, replacement, s_clean, flags=re.IGNORECASE)

    # Uppercase and strip non-Roman chars
    s_clean = s_clean.upper()
    s_clean = re.sub(r'[^IVXLCD]', '', s_clean)  # no M - we treated m as iii

    if not s_clean:
        return None

    vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500}
    result = 0
    prev = 0
    for ch in reversed(s_clean):
        val = vals.get(ch, 0)
        if val == 0:
            return None
        if val < prev:
            result -= val
        else:
            result += val
        prev = val

    # Sanity check: max letters per Symmachus book is ~170
    if result <= 0 or result > 200:
        return None
    return result


def is_apparatus_line(line):
    """Detect critical apparatus / footnote lines."""
    # Lines with: digit, word, manuscript sigla, corrections
    if re.search(r'\bom[.,]\s+[PVFMABHn]\b', line):
        return True
    if re.search(r'\]\s*[A-Z][a-z]+[,;]', line):  # like "contumeliam] LeeUus,"
        return True
    # Lines starting with digit and containing sigla + corrections
    if re.match(r'^\d+\s+\S+\s+[PVFMAn]{1,5}\b', line) and (
        re.search(r'\bom\b|\bfort\b|\bcf\b|\badd\b', line) or
        re.search(r'\]', line)
    ):
        return True
    return False


def is_page_running_header(line):
    """Detect running page headers."""
    # "LIBER I.  5", "LIBER III.  71", "LIBER Vnn.  X.  277"
    if re.match(r'^(?:[A-Z]{0,5}\s+)?LIBER\s+[IVXivxmnun]+[.]?\s+\d', line):
        return True
    if re.match(r'^SYMMACHI\s+EPISTVLAE', line):
        return True
    if re.match(r'^EIBER\s+', line):
        return True
    if re.match(r'^Q\.\s+A[tu][re]', line):  # "Q. Aurelits Stmmachts. 13"
        return True
    if re.match(r'^Q\.\s+FABIO', line):
        return True
    return False


def detect_book_marker(line):
    """Returns book number if line is a book header, else None."""
    # Strip leading manuscript sigla (PF, PVM, pv, etc.) but NOT 'LIBER' itself
    # Sigla are 1-4 chars not starting with 'LIBER'
    clean = re.sub(r'^(?:(?!LIBER)[A-Za-z]{1,4})\s+', '', line).strip()

    m = re.match(r'^LIBER\s+([A-Za-z]+)', clean)
    if not m:
        return None

    word = m.group(1).upper()

    # Reject if followed immediately by a digit (page running header like "LIBER I. 5")
    rest = clean[m.end():].strip()
    if rest and rest[0].isdigit():
        return None

    book_map = {
        'PRIMVS': 1, 'PRIMUS': 1,
        'SECVNDVS': 2, 'SECUNDUS': 2,
        'TERTIVS': 3, 'TERTIUS': 3,
        'QVARTVS': 4, 'QUARTUS': 4,
        'QVINTVS': 5, 'QUINTUS': 5, 'AVINTUS': 5, 'AVINTYS': 5, 'AVINTVS': 5,
        'SEXTVS': 6, 'SEXTUS': 6,
        'SEPTIMVS': 7, 'SEPTIMUS': 7,
        'OCTAVVS': 8, 'OCTAVUS': 8, 'OCTAVYS': 8,
        'NONVS': 9, 'NONUS': 9,
        'DECIMVS': 10, 'DECIMUS': 10, 'DECMVS': 10,
    }

    # Handle OCR variants for QVINTVS: "aVINTVS" -> word = "AVINTVS"
    if 'VINT' in word:
        return 5
    # Handle OCR variants for DECIMVS: "DECmVS" etc.
    if word.startswith('DEC') and len(word) >= 5:
        return 10

    return book_map.get(word)


def parse_letters_from_ocr(text):
    """
    Parse individual Symmachus letters from the OCR text.

    Letter formats encountered:
    1. Standard: "I  a.  375. PATRI  SYMMACHVS," (num + date + recipient on same line)
    2. Split:    "CVn  (CI)   a.  380—382.  lo"  followed by "PVF  SYMMACHVS  SYAGRIO."
    3. Date-only section: "I." followed by "AD RECIPIENT."
    4. Number + recipient only: "I.  5" then "SYMMACHVS STILICHONI."
    """

    main_start = text.find('LIBER  PRIMVS.')
    if main_start == -1:
        main_start = text.find('LIBER PRIMVS.')
    if main_start == -1:
        print("ERROR: Cannot find LIBER PRIMVS")
        return []

    text = text[main_start:]
    lines = text.split('\n')

    # Pattern 1: Roman numeral + date
    # e.g. "I  a.  375.", "CVn  (CI)   a.  380—382.", "XVm   a.  396. AD  PROTADIVM."
    letter_with_date_re = re.compile(
        r'^([IVXCLDivxcldm]{1,12}(?:\s*\([^)]{1,20}\))?)\s+'
        r'(?:(?:ante|post)\s+)?'
        r'a\.\s+'
        r'([\d—\-–.?]+)',
        re.IGNORECASE
    )

    # Pattern 2: Roman numeral alone (like "I.", "II.", "m.", "im.")
    # These appear in Books 8 etc.
    letter_num_only_re = re.compile(
        r'^([IVXCLDivxcld]{1,10})\.\s*$',
        re.IGNORECASE
    )

    current_book = 1
    current_letter_num = None
    current_letter_lines = []
    current_header = ''
    parsed_letters = []

    def save_current():
        nonlocal current_letter_num, current_letter_lines, current_header
        if current_letter_num is not None and current_letter_lines:
            body = clean_letter_text('\n'.join(current_letter_lines))
            if len(body) > 30:
                parsed_letters.append({
                    'book': current_book,
                    'letter_num': current_letter_num,
                    'header': current_header,
                    'text': body,
                })
        current_letter_num = None
        current_letter_lines = []
        current_header = ''

    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        if not line:
            if current_letter_num is not None:
                current_letter_lines.append('')
            i += 1
            continue

        # Check book marker
        bk = detect_book_marker(line)
        if bk is not None:
            save_current()
            current_book = bk
            i += 1
            continue

        # Skip page running headers
        if is_page_running_header(line):
            i += 1
            continue

        # Skip section dedications "AD FLAVIANVM." etc. (standalone)
        if re.match(r'^AD\s+[A-Z]+(?:\s+[A-Z]+)*\.?\s*$', line) and len(line) < 50:
            # But not if current letter is collecting body (it could be recipient)
            if current_letter_num is None:
                i += 1
                continue

        # Check for letter header with date
        hm = letter_with_date_re.match(line)
        if hm:
            save_current()
            roman_str = hm.group(1)
            current_letter_num = roman_to_int(roman_str)
            current_header = line
            current_letter_lines = []

            # Check if recipient is on next line
            rest = line[hm.end():].strip()
            rest_clean = re.sub(r'^[PVFMABn]{1,5}\s+', '', rest).strip()
            rest_clean = re.sub(r'\s+\d+\s*$', '', rest_clean).strip()

            if not rest_clean:
                # Look ahead for recipient
                j = i + 1
                while j < min(i + 4, len(lines)):
                    nl = lines[j].strip()
                    if not nl:
                        j += 1
                        continue
                    if (re.match(r'^[A-Z][A-Z\s,\.]{3,60}\.?\s*$', nl) and
                            not letter_with_date_re.match(nl) and
                            not is_page_running_header(nl) and
                            not detect_book_marker(nl) and
                            len(nl) < 70):
                        current_header += ' | ' + nl
                        i = j
                    break

            i += 1
            continue

        # Check for letter number only (Book 8 style: "I.", "II.", "VII.")
        nm = letter_num_only_re.match(line)
        if nm:
            # Look ahead to confirm this is a letter (followed by AD ... or body text)
            j = i + 1
            next_meaningful = None
            while j < min(i + 5, len(lines)):
                nl = lines[j].strip()
                if nl and not is_apparatus_line(nl) and not is_page_running_header(nl):
                    next_meaningful = nl
                    break
                j += 1

            # Confirm it's a letter if followed by body text or AD recipient
            if next_meaningful and (
                re.match(r'^AD\s+[A-Z]', next_meaningful) or
                re.match(r'^SYMMACHVS\s+', next_meaningful) or
                (len(next_meaningful) > 40 and re.search(r'[a-z]{3}', next_meaningful))
            ):
                save_current()
                roman_str = nm.group(1)
                current_letter_num = roman_to_int(roman_str)
                current_header = line
                current_letter_lines = []
                # If next line is recipient header, grab it
                if next_meaningful and re.match(r'^(?:AD\s+|SYMMACHVS\s+)', next_meaningful):
                    current_header += ' | ' + next_meaningful
                    i = j + 1
                    continue
                i += 1
                continue

        # Collect body text
        if current_letter_num is not None:
            if not is_apparatus_line(line):
                current_letter_lines.append(line)

        i += 1

    save_current()
    return parsed_letters


def clean_letter_text(text):
    """Clean up OCR noise from letter body text."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        s = line.strip()
        if not s:
            if cleaned and cleaned[-1]:
                cleaned.append('')
            continue
        if is_apparatus_line(s):
            continue
        if is_page_running_header(s):
            continue
        # Remove leading manuscript sigla
        s = re.sub(r'^[PVFMABn]{1,5}\s+', '', s)
        # Remove trailing page numbers (just digits)
        s = re.sub(r'\s+\d+\s*$', '', s)
        if s:
            cleaned.append(s)

    text = '\n'.join(cleaned).strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def get_author_id(conn, name_fragment):
    cur = conn.cursor()
    cur.execute("SELECT id FROM authors WHERE name LIKE ?", (f'%{name_fragment}%',))
    row = cur.fetchone()
    return row[0] if row else None


def insert_letters(conn, letters_data, symmachus_id):
    cur = conn.cursor()
    inserted = 0
    updated = 0
    skipped = 0

    for letter in letters_data:
        book = letter['book']
        letter_num = letter['letter_num']
        if letter_num is None:
            skipped += 1
            continue

        ref_id = f"symmachus.ep.{book}.{letter_num}"
        summary = f"Book {book}, Letter {letter_num}: {letter['header'][:120]}"
        text = letter['text']

        cur.execute("SELECT id, latin_text FROM letters WHERE ref_id = ?", (ref_id,))
        existing = cur.fetchone()

        if existing:
            existing_len = len(existing[1]) if existing[1] else 0
            if existing_len >= len(text):
                skipped += 1
                continue
            cur.execute("""
                UPDATE letters SET latin_text=?, source_url=?, subject_summary=?
                WHERE ref_id=?
            """, (text, SOURCE_URL, summary, ref_id))
            updated += 1
        else:
            cur.execute("""
                INSERT INTO letters (
                    collection, book, letter_number, ref_id,
                    sender_id, latin_text, subject_summary, source_url,
                    translation_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'symmachus', book, letter_num, ref_id,
                symmachus_id, text, summary, SOURCE_URL, 'none'
            ))
            inserted += 1

    conn.commit()
    return inserted, updated, skipped


def main():
    print("=== Symmachus Letter Scraper (Archive.org OCR) ===\n")

    if not os.path.exists(OCR_PATH):
        print(f"ERROR: OCR not found: {OCR_PATH}")
        sys.exit(1)

    with open(OCR_PATH, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()

    print(f"OCR text: {len(text):,} chars, {text.count(chr(10)):,} lines")

    print("\nParsing letters...")
    letters = parse_letters_from_ocr(text)
    print(f"Found {len(letters)} letters total")

    book_counts = Counter(l['book'] for l in letters)
    for b in sorted(book_counts.keys()):
        print(f"  Book {b}: {book_counts[b]} letters")

    # Duplicate check
    seen = {}
    dups = []
    for l in letters:
        key = (l['book'], l['letter_num'])
        if key in seen:
            dups.append(key)
        else:
            seen[key] = l
    if dups:
        print(f"\n  Duplicates: {len(dups)} - {dups[:5]}")

    conn = sqlite3.connect(DB_PATH, timeout=30)
    symmachus_id = get_author_id(conn, 'symmachus')
    print(f"\nSymmachus author_id: {symmachus_id}")

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM letters WHERE collection='symmachus'")
    print(f"Existing: {cur.fetchone()[0]}")

    print("\nInserting...")
    inserted, updated, skipped = insert_letters(conn, letters, symmachus_id)
    print(f"Inserted: {inserted}, Updated: {updated}, Skipped: {skipped}")

    cur.execute("SELECT COUNT(*) FROM letters WHERE collection='symmachus'")
    print(f"\nTotal now: {cur.fetchone()[0]}")

    cur.execute("""
        SELECT book, COUNT(*) FROM letters
        WHERE collection='symmachus'
        GROUP BY book ORDER BY book
    """)
    for row in cur.fetchall():
        print(f"  Book {row[0]}: {row[1]} letters")

    conn.close()
    print("\nDone!")


if __name__ == '__main__':
    main()

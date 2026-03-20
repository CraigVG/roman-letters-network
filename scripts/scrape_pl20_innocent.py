#!/usr/bin/env python3
"""
Scrape Innocent I papal letters from Patrologia Latina vol. 20 (Migne, 1845).

Source: https://archive.org/details/patrologiaecursu20mign
OCR text at: /tmp/pl20_innocent.txt

Innocent I section: lines 33258-47439 (approximately)
Uses Roman numeral letter headers: "EPISTOLA I.", "EPISTOLA II.", etc.
"""

import sqlite3
import re
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'roman_letters.db')
SOURCE_URL = 'https://archive.org/details/patrologiaecursu20mign'
TEXT_PATH = '/tmp/pl20_innocent.txt'

# Innocent I section line range (from inspection)
START_LINE = 33258
END_LINE = 47439


def roman_to_int(s):
    """Convert Roman numeral string to integer, handling PL20 OCR artifacts."""
    s = s.strip().upper()
    # OCR fix: backslash -> I (common in PL OCR), 1 -> I
    s = s.replace('\\', 'I').replace('1', 'I')
    # Remove non-roman characters
    s = re.sub(r'[^IVXLCDM]', '', s)
    if not s:
        return None
    roman_vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result = 0
    prev = 0
    for ch in reversed(s):
        val = roman_vals.get(ch, 0)
        if val == 0:
            return None
        if val < prev:
            result -= val
        else:
            result += val
        prev = val
    return result if result > 0 else None


def ensure_author(conn, name, name_latin=None, role='pope', death_year=None, birth_year=None, location='Rome'):
    """Get or create an author record."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM authors WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("""
        INSERT INTO authors (name, name_latin, role, location, death_year, birth_year)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, name_latin, role, location, death_year, birth_year))
    conn.commit()
    return cur.lastrowid


def is_page_header(line):
    """Detect running page headers."""
    s = line.strip()
    # "EPISTOL/E ET DECRETA. 486"
    if re.match(r'^EPISTOL', s) and re.search(r'\d{3}', s):
        return True
    # "457 S. INNOCENTIUS I PAPA. PROLEGOMENA. M"
    if re.match(r'^\d{3}', s) and 'PAPA' in s:
        return True
    # "S. INNOCENTII I PAP2E" or "S. INNOCENTII I PAVE" etc
    if re.match(r'^S\.\s+INNO', s):
        return True
    return False


def clean_letter_text(lines):
    """Clean letter text lines."""
    cleaned = []
    skip_footnote = False

    for raw in lines:
        s = raw.strip()
        if not s:
            if cleaned and cleaned[-1]:
                cleaned.append('')
            skip_footnote = False
            continue

        if is_page_header(s):
            continue

        # Footnote indicators: lines starting with lowercase letters (a, b, c, ...) followed by )
        if re.match(r'^[a-z]\)', s) or re.match(r'^[a-z]\s+', s) and len(s) < 80 and s[0].islower():
            skip_footnote = True
            continue

        if skip_footnote:
            # Footnotes end at blank line (already handled above) or new uppercase
            if s[0].isupper() and len(s) > 30:
                skip_footnote = False
                cleaned.append(s)
            continue

        cleaned.append(s)

    text = '\n'.join(cleaned).strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def parse_innocent_letters(lines):
    """Parse Innocent I letters from PL20 lines."""
    # Pattern: "EPISTOLA  IV." or "EPISTOLA  XLII." etc.
    # PL20 has many OCR artifacts between EPISTOLA and the number, like:
    # "EPISTOLA  «  IX.", "EPISTOLA  i>  XI.", "EPISTOLA  '  XL.", "EPISTOL  \\  11."
    # "EPISTOLA  IV>>.", "EPISTOLA  V  c.", "EPISTOLA  XVIIIe."
    # Strategy: find EPISTOL at start, then find the Roman numeral component anywhere in line
    epistola_re = re.compile(
        r'^["\s]*EPi?STOL[A/\\E]?\s+(.+)$',
        re.IGNORECASE
    )

    letters = []
    current_num = None
    current_roman = None
    current_lines = []

    def save_current():
        nonlocal current_num, current_roman, current_lines
        if current_num is None:
            return
        body = clean_letter_text(current_lines)
        if len(body.strip()) > 50:
            letters.append({
                'letter_num': current_num,
                'roman': current_roman,
                'text': body,
                'header': '\n'.join(current_lines[:5])[:300],
            })
        current_num = None
        current_roman = None
        current_lines = []

    for i in range(START_LINE, min(END_LINE, len(lines))):
        raw = lines[i]
        line = raw.strip()

        if not line:
            if current_num is not None:
                current_lines.append('')
            continue

        m = epistola_re.match(line)
        if m:
            rest = m.group(1).strip()
            # Skip lines that are clearly NOT letter headers:
            # "EPISTOLAE ET DECRETA", "EPISTOLA EADEM", page headers with trailing digits
            if re.search(r'^(EADEM|ET\s|\/E|\.E|jE|jG|iE|_E)', rest, re.IGNORECASE):
                pass  # not a letter header
            elif re.search(r'\d{3}', rest):
                pass  # has page number - it's a page header
            elif re.search(r'^\s*$', rest):
                pass  # empty
            else:
                # Extract Roman numeral: look for sequence of Roman chars at start (after junk)
                # Remove leading junk (non-Roman): «, i>, i-, ', », •, f, <, >, =, k, c, etc.
                cleaned_rest = re.sub(r'^[^IVXLCDMivxlcdm\\1]+', '', rest)
                # Extract the Roman numeral portion (stop at non-Roman chars)
                roman_match = re.match(r'([IVXLCDMivxlcdm\\1]{1,8})', cleaned_rest)
                if roman_match:
                    roman_str = roman_match.group(1).upper()
                    num = roman_to_int(roman_str)
                    if num and 1 <= num <= 50:
                        save_current()
                        current_num = num
                        current_roman = roman_str
                        current_lines = []
                        continue

        if current_num is not None:
            current_lines.append(line)

    save_current()
    return letters


def insert_letters(conn, letters):
    """Insert Innocent I letters into the database."""
    cur = conn.cursor()

    # Ensure author exists
    sender_id = ensure_author(
        conn, 'Innocent I', 'Innocentius I', 'pope', 417, 370
    )

    cur.execute("""
        SELECT COALESCE(MAX(letter_number), 0) FROM letters
        WHERE collection = 'innocent_i'
    """)
    counter = cur.fetchone()[0]

    inserted = 0
    skipped = 0

    for letter in letters:
        ref_id = f"innocent_i.ep.pl20.{letter['letter_num']}"
        cur.execute("SELECT id FROM letters WHERE ref_id = ?", (ref_id,))
        if cur.fetchone():
            skipped += 1
            continue

        counter += 1
        summary = f"PL20 Ep. {letter['roman']}: {letter['header'][:100]}"

        cur.execute("""
            INSERT INTO letters (
                collection, letter_number, ref_id,
                sender_id, latin_text, subject_summary, source_url,
                translation_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'innocent_i', counter, ref_id,
            sender_id, letter['text'], summary, SOURCE_URL, 'none'
        ))
        inserted += 1

    conn.commit()
    return inserted, skipped


def main():
    print("=== PL20 Innocent I Scraper ===\n")

    if not os.path.exists(TEXT_PATH):
        print(f"Missing: {TEXT_PATH}")
        return

    print(f"Loading {TEXT_PATH}...")
    with open(TEXT_PATH, 'r', encoding='utf-8', errors='replace') as f:
        all_lines = f.readlines()
    print(f"  Loaded {len(all_lines)} lines")
    print(f"  Processing lines {START_LINE}-{END_LINE}")

    letters = parse_innocent_letters(all_lines)
    print(f"  Found {len(letters)} letters")

    if letters:
        nums = sorted(l['letter_num'] for l in letters)
        print(f"  Letter numbers: {nums}")

    if not letters:
        print("No letters found")
        return

    conn = sqlite3.connect(DB_PATH, timeout=30)
    ins, skp = insert_letters(conn, letters)
    print(f"Inserted: {ins}, Skipped: {skp}")

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM letters WHERE collection='innocent_i'")
    cnt = cur.fetchone()[0]
    print(f"  innocent_i: {cnt} letters in DB")

    conn.close()
    print("\nDone!")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Scrape papal letters from Thiel's Epistolae Romanorum Pontificum Genuinae (1868).
Covers: Hilarus (461-468), Simplicius (468-483), Felix III (483-492), Gelasius I (492-496),
        Anastasius II (496-498), Symmachus (498-514), Hormisdas (514-523).

Source: https://archive.org/details/epistolaeromano00thiegoog
OCR text at: /tmp/thiel_papal_letters.txt
"""

import sqlite3
import re
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'roman_letters.db')
SOURCE_URL = 'https://archive.org/details/epistolaeromano00thiegoog'
TEXT_PATH = '/tmp/thiel_papal_letters.txt'

COLLECTION_META = {
    'simplicius_pope': {
        'name': 'Simplicius', 'name_latin': 'Simplicius',
        'role': 'pope', 'death_year': 483, 'birth_year': 420,
    },
    'gelasius_i': {
        'name': 'Gelasius I', 'name_latin': 'Gelasius I',
        'role': 'pope', 'death_year': 496, 'birth_year': 445,
    },
    'hormisdas': {
        'name': 'Hormisdas', 'name_latin': 'Hormisdas',
        'role': 'pope', 'death_year': 523, 'birth_year': 450,
    },
}

# Hardcoded line ranges based on inspection of the text
# (pope_key, collection, start_line, end_line)
POPE_LINE_RANGES = [
    ('simplicius', 'simplicius_pope', 13842, 16755),
    ('gelasius_i', 'gelasius_i', 20913, 44036),
    ('hormisdas', 'hormisdas', 50366, 68352),
]


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


def is_footnote_line(line):
    """Detect footnote apparatus lines."""
    s = line.strip()
    if not s:
        return False
    # Lines starting with superscript markers: *), ^), numbers followed by )
    if re.match(r'^[\*\^]+\)', s):
        return True
    if re.match(r'^\d{1,3}\)', s):
        return True
    return False


def is_page_header(line):
    """Detect running page headers like 'EPISTOLA  1.  289' or '290  S. GELASII PAPAE'."""
    s = line.strip()
    # Pattern: EPISTOLA + number + page number (all caps, ends with digit)
    if re.match(r'^EPISTOLA\s+\d+', s) and re.search(r'\d+\s*$', s):
        return True
    # Pattern: page number + S. POPE PAPAE
    if re.match(r'^\d{2,3}\s+S\.\s+\w+', s):
        return True
    # Pattern: pure page number followed by section header
    if re.match(r'^S\.\s+\w+\s+PAPAE', s):
        return True
    return False


def clean_letter_text(lines):
    """Clean a list of lines into letter body text."""
    cleaned = []
    in_footnote_block = False

    for raw in lines:
        s = raw.strip()
        if not s:
            if cleaned and cleaned[-1]:
                cleaned.append('')
            in_footnote_block = False
            continue

        if is_page_header(s):
            continue

        if is_footnote_line(s):
            in_footnote_block = True
            continue

        if in_footnote_block:
            # Footnotes end when we see a line starting with uppercase letter that looks like real text
            # Heuristic: if the line starts with uppercase and has > 30 chars, it's probably text
            if re.match(r'^[A-Z][a-z]', s) and len(s) > 20:
                in_footnote_block = False
                cleaned.append(s)
            else:
                continue
        else:
            cleaned.append(s)

    text = '\n'.join(cleaned).strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def parse_thiel_section(all_lines, start_line, end_line, collection):
    """
    Parse letters from a line range of the Thiel text.

    Real letter headers: "Epistola  N." (lowercase 'p', minimal trailing space or period)
    These are distinct from page headers: "EPISTOLA  N.  289" (all caps, trailing page number)
    """
    letters = []

    # Pattern: lowercase "Epistola" at start of stripped line, followed by number
    # Must not have a page number after (no trailing digits > 3 chars = page number)
    epistola_re = re.compile(r'^Epistola\s+(\d+)\s*\.?\s*$', re.IGNORECASE)
    # Also match "Epistola  N.  a 488d." date forms
    epistola_dated_re = re.compile(r'^Epistola\s+(\d+)\s*\.\s+[a-z\.\s\d]+$')

    current_num = None
    current_lines = []

    def save_current():
        nonlocal current_num, current_lines
        if current_num is None:
            return
        body = clean_letter_text(current_lines)
        if len(body.strip()) > 50:
            letters.append({
                'thiel_num': current_num,
                'collection': collection,
                'text': body,
                'header': '\n'.join(current_lines[:5])[:300],
            })
        current_num = None
        current_lines = []

    for i in range(start_line, min(end_line, len(all_lines))):
        raw = all_lines[i]
        line = raw.strip()

        if not line:
            if current_num is not None:
                current_lines.append('')
            continue

        # Check for letter header (case-sensitive: must be lowercase 'E' then 'pistola')
        if raw[0:1] == 'E' or (raw[0:2] in ('  ', ' E') and 'E' in raw[:3]):
            pass  # might match

        m = epistola_re.match(line)
        if not m:
            m = epistola_dated_re.match(line)

        if m:
            num = int(m.group(1))
            # Validate: letter numbers should be 1-200 range
            if 1 <= num <= 200:
                save_current()
                current_num = num
                current_lines = []
                continue

        if current_num is not None:
            current_lines.append(line)

    save_current()
    return letters


def insert_letters(conn, letters, source_url):
    """Insert letters from Thiel into the database."""
    cur = conn.cursor()

    # Ensure authors exist
    author_ids = {}
    for coll_key, meta in COLLECTION_META.items():
        aid = ensure_author(
            conn, meta['name'], meta.get('name_latin'),
            meta.get('role'), meta.get('death_year'), meta.get('birth_year')
        )
        author_ids[coll_key] = aid

    inserted = 0
    skipped = 0
    collection_counters = {}

    for letter in letters:
        collection = letter['collection']
        if collection not in COLLECTION_META:
            continue

        if collection not in collection_counters:
            cur.execute("""
                SELECT COALESCE(MAX(letter_number), 0) FROM letters
                WHERE collection = ?
            """, (collection,))
            max_num = cur.fetchone()[0]
            collection_counters[collection] = max_num

        collection_counters[collection] += 1
        letter_num = collection_counters[collection]

        # Use Thiel number as unique identifier
        ref_id = f"{collection}.ep.thiel.{letter['thiel_num']}"

        cur.execute("SELECT id FROM letters WHERE ref_id = ?", (ref_id,))
        if cur.fetchone():
            skipped += 1
            collection_counters[collection] -= 1
            continue

        summary = f"Thiel Ep. {letter['thiel_num']}: {letter['header'][:100]}"
        sender_id = author_ids.get(collection)

        cur.execute("""
            INSERT INTO letters (
                collection, letter_number, ref_id,
                sender_id, latin_text, subject_summary, source_url,
                translation_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            collection, letter_num, ref_id,
            sender_id, letter['text'], summary, source_url, 'none'
        ))
        inserted += 1

    conn.commit()
    return inserted, skipped


def main():
    print("=== Thiel Papal Letters Scraper ===\n")

    if not os.path.exists(TEXT_PATH):
        print(f"Missing: {TEXT_PATH}")
        print("Download with: curl -L 'https://archive.org/download/epistolaeromano00thiegoog/epistolaeromano00thiegoog_djvu.txt' -o /tmp/thiel_papal_letters.txt")
        return

    print(f"Loading {TEXT_PATH}...")
    with open(TEXT_PATH, 'r', encoding='utf-8', errors='replace') as f:
        all_lines = f.readlines()
    print(f"  Loaded {len(all_lines)} lines")

    all_letters = []

    for pope_key, collection, start_line, end_line in POPE_LINE_RANGES:
        print(f"\nParsing {pope_key} (lines {start_line}-{end_line}) -> {collection}...")
        letters = parse_thiel_section(all_lines, start_line, end_line, collection)
        print(f"  Found {len(letters)} letters")
        if letters:
            nums = sorted(set(l['thiel_num'] for l in letters))
            print(f"  Letter numbers: {nums[:20]}{'...' if len(nums) > 20 else ''}")

        all_letters.extend(letters)

    print(f"\nTotal letters parsed: {len(all_letters)}")

    if not all_letters:
        print("No letters found - check parsing logic")
        return

    conn = sqlite3.connect(DB_PATH, timeout=30)
    ins, skp = insert_letters(conn, all_letters, SOURCE_URL)
    print(f"Inserted: {ins}, Skipped: {skp}")

    cur = conn.cursor()
    for coll in ['simplicius_pope', 'gelasius_i', 'hormisdas']:
        cur.execute("SELECT COUNT(*) FROM letters WHERE collection=?", (coll,))
        cnt = cur.fetchone()[0]
        print(f"  {coll}: {cnt} letters in DB")

    conn.close()
    print("\nDone!")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Scrape papal letters from Thiel (1868) for popes we're missing:
- Hilary/Hilarus (461-468): lines 10904-13820
- Felix III (483-492): lines 17000-20913
- Anastasius II (496-498): lines 43750-44242
- Symmachus (pope, 498-514): lines 44242-50366

Also handles the Avellana collection for:
- John I (523-526), John II (533-535), Agapetus I (535-536)

Source: /tmp/thiel_papal_letters.txt
"""

import sqlite3
import re
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'roman_letters.db')
TEXT_PATH = '/tmp/thiel_papal_letters.txt'
SOURCE_URL = 'https://archive.org/details/epistolaeromano00thiegoog'

# Pope sections in Thiel file (line ranges based on analysis)
THIEL_SECTIONS = [
    {
        'collection': 'pope_hilary',
        'name': 'Hilary of Rome',
        'name_latin': 'Hilarius Papa',
        'birth_year': 420, 'death_year': 468,
        'pontificate': '461-468',
        'start_line': 10904,
        'end_line': 13820,
    },
    {
        'collection': 'pope_felix_iii',
        'name': 'Felix III',
        'name_latin': 'Felix II Papa',
        'birth_year': 430, 'death_year': 492,
        'pontificate': '483-492',
        'start_line': 16900,
        'end_line': 20913,
    },
    {
        'collection': 'pope_anastasius_ii',
        'name': 'Anastasius II',
        'name_latin': 'Anastasius II Papa',
        'birth_year': 450, 'death_year': 498,
        'pontificate': '496-498',
        'start_line': 43750,
        'end_line': 44242,
    },
    {
        'collection': 'pope_symmachus',
        'name': 'Symmachus (Pope)',
        'name_latin': 'Symmachus Papa',
        'birth_year': 450, 'death_year': 514,
        'pontificate': '498-514',
        'start_line': 44242,
        'end_line': 50366,
    },
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


def ensure_collection(conn, slug, name, description=''):
    """Ensure collection record exists."""
    cur = conn.cursor()
    cur.execute("SELECT slug FROM collections WHERE slug = ?", (slug,))
    if not cur.fetchone():
        try:
            cur.execute("""
                INSERT INTO collections (slug, author_name, description, scrape_status)
                VALUES (?, ?, ?, 'partial')
            """, (slug, name, description))
            conn.commit()
        except Exception:
            pass  # May not have all required columns


def is_page_header(line):
    """Detect running page headers."""
    s = line.strip()
    # Pattern: NNN  S.  PAPAL NAME  PAPAE
    if re.match(r'^\d{2,3}\s+S\.\s+\w+', s):
        return True
    if re.match(r'^S\.\s+\w+\s+PAPAE', s):
        return True
    return False


def is_footnote_line(line):
    """Detect footnote apparatus lines."""
    s = line.strip()
    if re.match(r'^\*\)', s) or re.match(r'^\d{1,3}\)', s):
        return True
    # Lines with lots of footnote markers
    if re.match(r'^[a-z]\)', s) or re.match(r'^\^+\)', s):
        return True
    return False


def clean_text(raw_lines):
    """Clean OCR text removing headers, footnotes, apparatus."""
    cleaned = []
    skip_footnotes = False

    for raw in raw_lines:
        s = raw.strip()
        if not s:
            if cleaned and cleaned[-1]:
                cleaned.append('')
            skip_footnotes = False
            continue

        if is_page_header(s):
            continue

        if is_footnote_line(s):
            skip_footnotes = True
            continue

        if skip_footnotes:
            # End footnote block when we see a proper sentence start
            if re.match(r'^[A-Z][a-z]', s) and len(s) > 20:
                skip_footnotes = False
                cleaned.append(s)
            # Also end footnote for new section headers
            elif re.match(r'^Epistola\s+\d+', s, re.I):
                skip_footnotes = False
                cleaned.append(s)
            continue

        cleaned.append(s)

    text = '\n'.join(cleaned)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_section(all_lines, start_line, end_line):
    """
    Parse letters from a line range in the Thiel text.
    Returns list of {letter_num, text, header_text}.
    """
    letters = []
    ep_re = re.compile(r'^Epistola\s+(\d+)\s*\.?\s*$', re.IGNORECASE)
    # Also match "Epistola N. a.NNNd." date forms
    ep_dated_re = re.compile(r'^Epistola\s+(\d+)\s*[.\s]+.*$')

    current_num = None
    current_lines = []

    def save_current():
        nonlocal current_num, current_lines
        if current_num is None:
            return
        body = clean_text(current_lines)
        if len(body.strip()) > 30:
            letters.append({
                'thiel_num': current_num,
                'text': body,
                'header': '\n'.join(current_lines[:6])[:400],
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

        # Skip page headers
        if is_page_header(line):
            continue

        # Check for letter header
        m = ep_re.match(line)
        if not m:
            # Try dated form but be careful not to grab junk
            m2 = ep_dated_re.match(line)
            if m2:
                num = int(re.search(r'\d+', line).group())
                if 1 <= num <= 300:
                    m = m2
                    # Create fake group(1)
                    class FakeMatch:
                        def group(self, n): return str(num)
                    m = FakeMatch()

        if m:
            try:
                num = int(m.group(1)) if hasattr(m, 'group') else int(re.search(r'\d+', line).group())
            except:
                if current_num is not None:
                    current_lines.append(line)
                continue
            if 1 <= num <= 300:
                save_current()
                current_num = num
                current_lines = []
                continue

        if current_num is not None:
            current_lines.append(line)

    save_current()
    return letters


def insert_letters(conn, letters, collection, author_id, source_url):
    """Insert parsed letters into the database."""
    cur = conn.cursor()
    inserted = 0
    skipped = 0

    # Get current max letter number for this collection
    cur.execute("SELECT COALESCE(MAX(letter_number), 0) FROM letters WHERE collection = ?", (collection,))
    counter = cur.fetchone()[0]

    for letter in letters:
        ref_id = f"{collection}.thiel.{letter['thiel_num']}"

        cur.execute("SELECT id FROM letters WHERE ref_id = ?", (ref_id,))
        if cur.fetchone():
            skipped += 1
            continue

        counter += 1
        summary = f"Ep. {letter['thiel_num']}: {letter['header'][:120]}"

        # Try to guess year from pontificate dates
        year_approx = None
        thiel_num = letter['thiel_num']

        cur.execute("""
            INSERT INTO letters (
                collection, letter_number, ref_id,
                sender_id, latin_text, subject_summary, source_url,
                translation_source, year_min, year_max
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            collection, counter, ref_id,
            author_id, letter['text'], summary, source_url,
            'none', None, None
        ))
        inserted += 1

    conn.commit()
    return inserted, skipped


def main():
    print("=== Thiel Missing Papal Letters Scraper ===\n")

    if not os.path.exists(TEXT_PATH):
        print(f"ERROR: {TEXT_PATH} not found!")
        print("Download with: wget -O /tmp/thiel_papal_letters.txt 'https://archive.org/download/epistolaeromano00thiegoog/epistolaeromano00thiegoog_djvu.txt'")
        return 1

    print(f"Loading {TEXT_PATH}...")
    with open(TEXT_PATH, 'r', errors='replace') as f:
        all_lines = f.readlines()
    print(f"  Loaded {len(all_lines)} lines")

    conn = sqlite3.connect(DB_PATH, timeout=30)

    total_inserted = 0
    total_skipped = 0

    for section in THIEL_SECTIONS:
        collection = section['collection']
        name = section['name']
        print(f"\n--- {name} ({section['pontificate']}) ---")
        print(f"  Lines {section['start_line']}-{section['end_line']}")

        # Ensure author exists
        author_id = ensure_author(
            conn, name, section.get('name_latin'), 'pope',
            section.get('death_year'), section.get('birth_year')
        )

        # Ensure collection record
        ensure_collection(conn, collection, name)

        # Parse letters
        letters = parse_section(all_lines, section['start_line'], section['end_line'])
        print(f"  Parsed {len(letters)} letters: {sorted(l['thiel_num'] for l in letters)[:15]}")

        if not letters:
            print(f"  WARNING: No letters found!")
            continue

        # Insert
        ins, skp = insert_letters(conn, letters, collection, author_id, SOURCE_URL)
        print(f"  Inserted: {ins}, Skipped (already exist): {skp}")
        total_inserted += ins
        total_skipped += skp

    # Summary
    print(f"\n{'='*50}")
    print(f"Total inserted: {total_inserted}")
    print(f"Total skipped: {total_skipped}")

    cur = conn.cursor()
    print("\nFinal collection counts:")
    for section in THIEL_SECTIONS:
        cur.execute("SELECT COUNT(*) FROM letters WHERE collection=?", (section['collection'],))
        cnt = cur.fetchone()[0]
        print(f"  {section['collection']}: {cnt}")

    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())

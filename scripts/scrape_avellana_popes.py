#!/usr/bin/env python3
"""
Extract letters of John II (533-535) and Agapetus I (535-536) from the Avellana collection.
Also extracts Vigilius letters present in the collection.

Source: /tmp/avellana1_ocr.txt (Corpus Scriptorum Ecclesiasticorum Latinorum vol 35/1)
The Avellana covers letters from ~367 to 553 AD.

Key letter markers in Avellana:
- (N.) = letter number
- Then SENDER TITLE / RECIPIENT TITLE header
- Then letter text

John II: letters 81, 82, 83, 84 (to Justinian)
Agapetus I: letters 86, 87, 91, 92
Vigilius: letters 93, 94 (and fragments)
"""

import sqlite3
import re
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'roman_letters.db')
TEXT_PATH = '/tmp/avellana1_ocr.txt'
SOURCE_URL = 'https://archive.org/details/epistulaeimperatorum'

# Avellana letter numbers and their pope assignments
# Based on the index analysis we did
POPE_LETTERS = {
    'pope_john_ii': {
        'name': 'John II (Pope)',
        'name_latin': 'Iohannes II Papa',
        'birth_year': 470, 'death_year': 535,
        'pontificate': '533-535',
        'avellana_letters': [81, 82, 83, 84],
        'description': 'John II letters to Justinian (533-535)'
    },
    'pope_agapetus_i': {
        'name': 'Agapetus I',
        'name_latin': 'Agapetus I Papa',
        'birth_year': 480, 'death_year': 536,
        'pontificate': '535-536',
        'avellana_letters': [86, 87, 91, 92],
        'description': 'Agapetus I letters to emperors and bishops'
    },
    'pope_vigilius': {
        'name': 'Vigilius (Pope)',
        'name_latin': 'Vigilius Papa',
        'birth_year': 500, 'death_year': 555,
        'pontificate': '537-555',
        'avellana_letters': [93, 94],
        'description': 'Vigilius letters on Three Chapters'
    },
}


def ensure_author(conn, name, name_latin, death_year, birth_year):
    cur = conn.cursor()
    cur.execute("SELECT id FROM authors WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("""
        INSERT INTO authors (name, name_latin, role, location, death_year, birth_year)
        VALUES (?, ?, 'pope', 'Rome', ?, ?)
    """, (name, name_latin, death_year, birth_year))
    conn.commit()
    return cur.lastrowid


def is_apparatus_line(line):
    """Detect critical apparatus lines."""
    s = line.strip()
    if not s:
        return False
    # Citation reference lines: "1 Cor. 12, 13 14 Gal. 3, 28"
    if re.match(r'^\d+\s+[A-Z][a-z]+\.\s+\d+', s):
        return True
    # Manuscript variant notation: "1 uestas V, corr. a 2 ..."
    if re.match(r'^\d+\s+\w+\s+\w+:', s) and ('V' in s or 'corr' in s or 'Bar' in s):
        return True
    # "Epist. LXX 5 — LXXI 3. 289"
    if re.match(r'^Epist\.\s+[MDCLXVI]+', s):
        return True
    # Line numbers alone
    if re.match(r'^\d{1,2}\s*$', s) and len(s) < 5:
        return True
    return False


def extract_avellana_letter(lines, start_idx, end_idx):
    """Extract letter text between two markers."""
    text_lines = []
    in_apparatus = False

    for i in range(start_idx, min(end_idx, len(lines))):
        raw = lines[i]
        s = raw.strip()

        if not s:
            if text_lines and text_lines[-1]:
                text_lines.append('')
            in_apparatus = False
            continue

        # Detect apparatus lines
        if is_apparatus_line(s):
            in_apparatus = True
            continue

        if in_apparatus:
            # Resume main text after apparatus
            if re.match(r'^[A-Z][a-z]', s) and len(s) > 20:
                in_apparatus = False
                text_lines.append(s)
            continue

        text_lines.append(s)

    text = '\n'.join(text_lines)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


def parse_avellana(filepath, wanted_letter_nums):
    """
    Parse Avellana for specific letter numbers.

    Returns dict: {avellana_num: {text, header}}
    """
    with open(filepath, 'r', errors='replace') as f:
        lines = f.readlines()

    print(f"  Loaded {len(lines)} lines from {os.path.basename(filepath)}")

    # Find letter markers: lines matching '(N.)'
    letter_marker_re = re.compile(r'^\((\d+)\.\)\s*$')

    # First pass: find all letter markers and their positions
    all_markers = []
    for i, raw in enumerate(lines):
        s = raw.strip()
        m = letter_marker_re.match(s)
        if m:
            num = int(m.group(1))
            all_markers.append((i, num))

    print(f"  Found {len(all_markers)} letter markers")

    # Filter to wanted letters
    wanted = set(wanted_letter_nums)
    results = {}

    for idx, (line_idx, letter_num) in enumerate(all_markers):
        if letter_num not in wanted:
            continue

        # Find end of this letter
        end_line = all_markers[idx + 1][0] if idx + 1 < len(all_markers) else len(lines)

        # Get header (2 lines after marker)
        header_lines = []
        for j in range(line_idx + 1, min(line_idx + 4, end_line)):
            s = lines[j].strip()
            if s:
                header_lines.append(s)
                if len(header_lines) >= 2:
                    break

        header = ' | '.join(header_lines)

        # Extract text
        text = extract_avellana_letter(lines, line_idx + 1, end_line)

        if len(text) > 50:
            results[letter_num] = {
                'text': text,
                'header': header[:300],
                'avellana_num': letter_num
            }
            print(f"    Ep {letter_num}: {header[:80]}, text={len(text)} chars")

    return results


def main():
    print("=== Avellana Papal Letters Scraper ===\n")

    if not os.path.exists(TEXT_PATH):
        print(f"ERROR: {TEXT_PATH} not found!")
        return 1

    # Collect all wanted letter numbers
    all_wanted = []
    for collection, meta in POPE_LETTERS.items():
        all_wanted.extend(meta['avellana_letters'])

    print(f"Extracting letters: {sorted(set(all_wanted))}")

    avellana_letters = parse_avellana(TEXT_PATH, set(all_wanted))
    print(f"\nTotal letters extracted: {len(avellana_letters)}")

    if not avellana_letters:
        print("No letters found - check parsing logic")
        return 1

    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    total_inserted = 0
    total_skipped = 0

    for collection, meta in POPE_LETTERS.items():
        print(f"\n--- {meta['name']} ({meta['pontificate']}) ---")

        # Ensure author
        author_id = ensure_author(
            conn, meta['name'], meta['name_latin'],
            meta['death_year'], meta['birth_year']
        )

        # Get current max
        cur.execute("SELECT COALESCE(MAX(letter_number), 0) FROM letters WHERE collection=?", (collection,))
        counter = cur.fetchone()[0]

        inserted = 0
        for av_num in meta['avellana_letters']:
            if av_num not in avellana_letters:
                print(f"  Ep {av_num}: NOT FOUND in Avellana")
                continue

            letter = avellana_letters[av_num]
            ref_id = f"{collection}.avellana.{av_num}"

            cur.execute("SELECT id FROM letters WHERE ref_id=?", (ref_id,))
            if cur.fetchone():
                total_skipped += 1
                continue

            counter += 1
            summary = f"Avellana ep {av_num}: {letter['header'][:150]}"

            cur.execute("""
                INSERT INTO letters (
                    collection, letter_number, ref_id, sender_id,
                    latin_text, subject_summary, source_url, translation_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                collection, counter, ref_id, author_id,
                letter['text'], summary, SOURCE_URL, 'none'
            ))
            inserted += 1
            total_inserted += 1

        conn.commit()
        print(f"  Inserted: {inserted} new letters")

        cur.execute("SELECT COUNT(*) FROM letters WHERE collection=?", (collection,))
        print(f"  Total in DB: {cur.fetchone()[0]}")

    print(f"\n{'='*50}")
    print(f"Total inserted: {total_inserted}")
    print(f"Total skipped: {total_skipped}")

    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())

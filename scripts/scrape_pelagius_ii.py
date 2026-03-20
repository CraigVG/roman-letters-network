#!/usr/bin/env python3
"""
Extract Pelagius II letters from PL 72 OCR text.
Pelagius II (579-590) was the immediate predecessor of Gregory the Great.
PL 72 covers his works at cols. ~703-760.

Source: archive.org/details/bim_early-english-books-1641-1700_1849_72
"""

import sqlite3
import re
import os
import time
import urllib.request

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
TEXT_CACHE = '/tmp/pl72_papal.txt'
ARCHIVE_URL = 'https://archive.org/download/bim_early-english-books-1641-1700_1849_72/bim_early-english-books-1641-1700_1849_72_djvu.txt'
SOURCE_URL = 'https://archive.org/details/bim_early-english-books-1641-1700_1849_72'

# Position in text where Pelagius II section starts
PL2_START = 1955050
PL2_END = 3234730  # Where Benedict I starts

# Known letter positions from inspection
PELAGIUS_II_LETTERS = [
    # (section_start, marker_text, roman_numeral, letter_num)
    # These were found by manual inspection of the OCR text
]


def roman_to_int(s: str) -> int:
    s = s.upper().strip()
    vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    n, prev = 0, 0
    for c in reversed(s):
        v = vals.get(c, 0)
        if v < prev:
            n -= v
        else:
            n += v
        prev = v
    return n


def clean_text(text: str) -> str:
    """Clean OCR text."""
    replacements = [
        (r'\$', 's'), (r'ﬁ', 'fi'), (r'ﬂ', 'fl'),
        (r'8upra', 'supra'), (r'8ub', 'sub'), (r'8int', 'sint'),
        (r'8e ', 'se '), (r'8it ', 'sit '), (r'8unt', 'sunt'),
        (r'8anct', 'sanct'),
    ]
    for p, r in replacements:
        text = re.sub(p, r, text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def extract_letters_from_section(text: str, section_start: int, section_end: int) -> list:
    """Extract letter blocks from a pope section."""
    section = text[section_start:section_end]
    letters = []

    # Find EPISTOLA headers - these mark individual letters
    ep_pattern = re.compile(
        r'\nEPISTOLA\s+([IVX]+)\s*[\[\*\|]?[^\n]*?\n',
        re.IGNORECASE
    )
    markers = list(ep_pattern.finditer(section))

    if not markers:
        return letters

    for i, marker in enumerate(markers):
        rn = marker.group(1).upper()

        # Filter footnote references
        pre = section[max(0, marker.start() - 150):marker.start()]
        if re.search(r'epistola\s+\d{2,3}', pre, re.I):
            continue

        try:
            letter_num = roman_to_int(rn)
        except Exception:
            continue

        if letter_num <= 0 or letter_num > 50:
            continue

        # Get block to next marker
        block_start = marker.start()
        block_end = markers[i + 1].start() if i + 1 < len(markers) else len(section)
        block = section[block_start:block_end]

        if len(block.strip()) < 80:
            continue

        # Extract recipient from AD header
        ad_match = re.search(r'AD\s+([A-Z][A-Z\s,\.\-]+?)\s*[\.\n(]', block[:400])
        recipient = ad_match.group(1).strip().title() if ad_match else ''

        # Extract letter text (after salutation)
        salut_match = re.search(r'((?:Dilectiss|Pelagius|Frater)\w*\s+\w+.*?\.)\s*\n', block[:600])
        text_start = salut_match.end() if salut_match else block.find('\n\n')
        letter_text = block[max(0, text_start):text_start + 6000]

        # Clean up
        letter_text = clean_text(letter_text)

        if len(letter_text) < 50:
            continue

        letters.append({
            'letter_num': letter_num,
            'recipient': recipient,
            'latin_text': letter_text,
            'header': block[:200].strip(),
        })

    return letters


def ensure_author(db: sqlite3.Connection, name: str, role: str = 'pope',
                  birth_year: int = None, death_year: int = None) -> int:
    row = db.execute("SELECT id FROM authors WHERE name = ?", (name,)).fetchone()
    if row:
        return row[0]
    db.execute(
        "INSERT INTO authors (name, role, birth_year, death_year, location, lat, lon) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, role, birth_year, death_year, 'Rome', 41.8967, 12.4822)
    )
    return db.execute("SELECT id FROM authors WHERE name = ?", (name,)).fetchone()[0]


def main():
    # Load or download text
    if os.path.exists(TEXT_CACHE):
        print(f'Loading {TEXT_CACHE}')
        with open(TEXT_CACHE) as f:
            text = f.read()
    else:
        print('Downloading PL 72...')
        req = urllib.request.Request(ARCHIVE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode('utf-8', errors='replace')
        with open(TEXT_CACHE, 'w') as f:
            f.write(text)

    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")

    # Ensure Pelagius II author exists
    pl2_id = ensure_author(db, 'Pope Pelagius II', death_year=590, birth_year=520)
    print(f'Pelagius II author id: {pl2_id}')

    # Extract Pelagius II letters
    pl2_letters = extract_letters_from_section(text, PL2_START, PL2_END)
    print(f'Extracted {len(pl2_letters)} Pelagius II letters from PL 72')

    inserted = 0
    for letter in pl2_letters:
        letter_num = letter['letter_num']
        ref_id = f'pelagius_ii.ep.pl72.{letter_num}'

        # Check if already exists
        existing = db.execute("SELECT id FROM letters WHERE ref_id = ?", (ref_id,)).fetchone()
        if existing:
            continue

        db.execute("""
            INSERT INTO letters (
                collection, letter_number, ref_id,
                sender_id, year_approx, year_min, year_max,
                subject_summary, latin_text, english_text,
                translation_source, source_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
        """, (
            'pelagius_ii',
            letter_num,
            ref_id,
            pl2_id,
            585,  # approximate middle of Pelagius II's pontificate
            579, 590,
            f'Letter {letter_num} to {letter["recipient"]}' if letter['recipient'] else f'Pelagius II Letter {letter_num}',
            letter['latin_text'],
            'needs_translation',
            SOURCE_URL
        ))
        inserted += 1
        print(f'  Inserted: Pelagius II Letter {letter_num} - To {letter["recipient"][:50]}')

    db.commit()
    print(f'\nInserted {inserted} new Pelagius II letters')

    # Final count
    count = db.execute("SELECT COUNT(*) FROM letters WHERE collection='pelagius_ii'").fetchone()[0]
    print(f'Pelagius II total in DB: {count}')

    # Also check if there are Vigilius letters in PL 72
    print('\nChecking for Vigilius letters in PL 72...')
    vigilius_mentions = [m.start() for m in re.finditer(r'VIGILI[UI]S?\s+PAPA', text)]
    print(f'Vigilius Papa mentions: {len(vigilius_mentions)}')
    for pos in vigilius_mentions[:5]:
        print(f'  at {pos}: {repr(text[pos:pos+150])}')


if __name__ == '__main__':
    main()

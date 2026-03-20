#!/usr/bin/env python3
"""
Extract remaining papal letters from PL 72 OCR text that aren't already in DB.
Covers:
- Pelagius II additional letters (I/PRIMA, III, plus Olim-numbered and un-numbered ones)
- Benedict I epistola to Bishop David (the genuine one)
- John III epistola to bishops of Germany and Gaul

Source: archive.org/download/bim_early-english-books-1641-1700_1849_72/..._djvu.txt
"""

import sqlite3
import re
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
TEXT_CACHE = '/tmp/pl72_papal.txt'
SOURCE_URL = 'https://archive.org/details/bim_early-english-books-1641-1700_1849_72'


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
    replacements = [
        (r'\$', 's'), (r'ﬁ', 'fi'), (r'ﬂ', 'fl'),
        (r'8upra', 'supra'), (r'8ub', 'sub'), (r'8int', 'sint'),
        (r'8e ', 'se '), (r'8it ', 'sit '), (r'8unt', 'sunt'),
        (r'8anct', 'sanct'), (r'8ic', 'sic'), (r'8ed', 'sed'),
        (r'ij\b', 'ii'),
    ]
    for p, r in replacements:
        text = re.sub(p, r, text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def ensure_author(db, name, role='pope', birth_year=None, death_year=None):
    row = db.execute("SELECT id FROM authors WHERE name = ?", (name,)).fetchone()
    if row:
        return row[0]
    db.execute(
        "INSERT INTO authors (name, role, birth_year, death_year, location, lat, lon) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, role, birth_year, death_year, 'Rome', 41.8967, 12.4822)
    )
    return db.execute("SELECT id FROM authors WHERE name = ?", (name,)).fetchone()[0]


def insert_letter(db, collection, ref_id, sender_id, letter_num, year_approx,
                  year_min, year_max, subject, latin_text):
    existing = db.execute("SELECT id FROM letters WHERE ref_id = ?", (ref_id,)).fetchone()
    if existing:
        return False
    db.execute("""
        INSERT INTO letters (
            collection, letter_number, ref_id,
            sender_id, year_approx, year_min, year_max,
            subject_summary, latin_text, english_text,
            translation_source, source_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
    """, (
        collection, letter_num, ref_id,
        sender_id, year_approx, year_min, year_max,
        subject, latin_text, 'needs_translation', SOURCE_URL
    ))
    return True


def extract_block(text, start, end, max_chars=8000):
    """Extract and clean a block of text."""
    block = text[start:end]
    return clean_text(block)[:max_chars]


def main():
    print('Loading PL 72 text...')
    with open(TEXT_CACHE) as f:
        text = f.read()
    print(f'  {len(text)} chars')

    db = sqlite3.connect(DB_PATH, timeout=30)
    db.execute("PRAGMA journal_mode=WAL")

    total_inserted = 0

    # ================================================================
    # 1. PELAGIUS II - additional letters not yet in DB
    # ================================================================
    print('\n=== Pelagius II ===')
    pl2_id = ensure_author(db, 'Pope Pelagius II', death_year=590, birth_year=520)
    print(f'  Author id: {pl2_id}')

    # Check what's already in DB
    existing_refs = set(row[0] for row in db.execute(
        "SELECT ref_id FROM letters WHERE collection = 'pelagius_ii'"
    ))
    print(f'  Existing letters: {len(existing_refs)} - {sorted(existing_refs)}')

    # Specific letter positions in PL 72 main text section (1955050 - 3230695)
    # These were found by manual inspection
    PL2_LETTERS = [
        # (abs_start, next_start, ref_suffix, letter_num, subject)
        (1961247, 1963563, 'pl72.1', 8,  'EPISTOLA PRIMA: To Gregory Deacon - requesting imperial aid against Lombards'),
        (1963563, 1968165, 'pl72.2', 9,  'EPISTOLA II: To Aunacharius Bishop of Autissidorum'),
        (1968165, 1996575, 'pl72.3', 10, 'EPISTOLA III: First letter to Elias and bishops of Istria (Three Chapters)'),
        (1996575, 2067242, 'pl72.5', 11, 'EPISTOLA V: Third letter to Elias and bishops of Istria'),
        (2067242, 2086227, 'pl72.6', 12, 'EPISTOLA VI: To John Bishop of Constantinople'),
        (2086227, 2093447, 'pl72.7', 13, 'EPISTOLA VII: To Aunarius Bishop of Autissidorum'),
        # Additional letters after the fragmenta section
        (2099071, 2118956, 'pl72.olim1', 14, 'EPISTOLA (Olim I): To Benignum Archbishop'),
        (2118956, 2128129, 'pl72.olim3', 15, 'EPISTOLA (Olim III): To bishops of Italy'),
        (2128129, 2150529, 'pl72.olim9', 16, 'EPISTOLA (Olim IX): To bishops of Germany and Gaul'),
        (2150529, 2152042, 'pl72.stephen', 17, 'EPISTOLA: To Stephen Abbot'),
        (2152042, 2317315, 'pl72.aunarius2', 18, 'EPISTOLA: To Saint Aunarius Bishop of Autissidorum'),
    ]

    for abs_start, abs_end, ref_suffix, letter_num, subject in PL2_LETTERS:
        ref_id = f'pelagius_ii.ep.{ref_suffix}'
        if ref_id in existing_refs:
            print(f'  Skipping {ref_id} (already in DB)')
            continue

        latin_text = extract_block(text, abs_start, abs_end, max_chars=8000)
        if len(latin_text) < 80:
            print(f'  Skipping {ref_id} - too short ({len(latin_text)} chars)')
            continue

        ok = insert_letter(
            db, 'pelagius_ii', ref_id, pl2_id, letter_num,
            585, 579, 590, subject, latin_text
        )
        if ok:
            total_inserted += 1
            print(f'  Inserted: {ref_id} - {subject[:60]}')

    # ================================================================
    # 2. BENEDICT I
    # ================================================================
    print('\n=== Benedict I ===')
    ben1_id = ensure_author(db, 'Pope Benedict I', death_year=579, birth_year=510)
    print(f'  Author id: {ben1_id}')

    existing_ben = set(row[0] for row in db.execute(
        "SELECT ref_id FROM letters WHERE collection = 'benedict_i'"
    ))

    BEN1_LETTERS = [
        # Fragment to patriarch of Grado - labeled PALEA (spurious/questionable) in PL
        (1907203, 1909604, 'pl72.grandensem', 1,
         'FRAGMENTUM EPISTOLAE: To the Patriarch of Grado (PALEA - authenticity questioned by PL editors)'),
        # Letter to Bishop David
        (1909604, 1955050, 'pl72.david', 2,
         'EPISTOLA: To David Bishop - On the Trinity'),
    ]

    for abs_start, abs_end, ref_suffix, letter_num, subject in BEN1_LETTERS:
        ref_id = f'benedict_i.ep.{ref_suffix}'
        if ref_id in existing_ben:
            print(f'  Skipping {ref_id} (already in DB)')
            continue

        # For the David letter, trim at next section
        end_pos = min(abs_end, abs_start + 10000)
        latin_text = extract_block(text, abs_start, end_pos, max_chars=8000)
        if len(latin_text) < 80:
            print(f'  Skipping {ref_id} - too short ({len(latin_text)} chars)')
            continue

        ok = insert_letter(
            db, 'benedict_i', ref_id, ben1_id, letter_num,
            576, 575, 579, subject, latin_text
        )
        if ok:
            total_inserted += 1
            print(f'  Inserted: {ref_id} - {subject[:70]}')

    # ================================================================
    # 3. JOHN III
    # ================================================================
    print('\n=== John III ===')
    john3_id = ensure_author(db, 'Pope John III', death_year=574, birth_year=520)
    print(f'  Author id: {john3_id}')

    existing_john3 = set(row[0] for row in db.execute(
        "SELECT ref_id FROM letters WHERE collection = 'pope_john_iii'"
    ))

    # The letter to bishops of Germany and Gaul is in the introductory section
    # at position 19304. It ends around position 33500 (before the next section).
    JOHN3_LETTERS = [
        (19304, 33500, 'pl72.german_gaul', 1,
         'EPISTOLA: To bishops of Germany and Gaul - on chorepiscopos'),
    ]

    for abs_start, abs_end, ref_suffix, letter_num, subject in JOHN3_LETTERS:
        ref_id = f'pope_john_iii.ep.{ref_suffix}'
        if ref_id in existing_john3:
            print(f'  Skipping {ref_id} (already in DB)')
            continue

        latin_text = extract_block(text, abs_start, abs_end, max_chars=8000)
        if len(latin_text) < 80:
            print(f'  Skipping {ref_id} - too short ({len(latin_text)} chars)')
            continue

        ok = insert_letter(
            db, 'pope_john_iii', ref_id, john3_id, letter_num,
            567, 561, 574, subject, latin_text
        )
        if ok:
            total_inserted += 1
            print(f'  Inserted: {ref_id} - {subject[:70]}')

    db.commit()
    print(f'\nTotal inserted: {total_inserted}')

    # Final counts
    print('\nFinal counts:')
    for coll in ['pelagius_ii', 'benedict_i', 'pope_john_iii']:
        count = db.execute(
            "SELECT COUNT(*) FROM letters WHERE collection = ?", (coll,)
        ).fetchone()[0]
        print(f'  {coll}: {count}')


if __name__ == '__main__':
    main()

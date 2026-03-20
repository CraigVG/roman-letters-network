#!/usr/bin/env python3
"""
Scrape papal letters from the Collectio Avellana (CSEL 35).
Part 1: Epistulae I-CIV (contains Innocent I, Simplicius, Gelasius I)
Part 2: Epistulae CV-CCXXXXIIII (contains Hormisdas and others)

Sources:
- https://archive.org/details/collectioavellan00guen (Part 1)
- https://archive.org/details/collectioavellan00guen_926 (Part 2)
"""

import sqlite3
import re
import os
import sys
import time

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'roman_letters.db')
SOURCE_URL_1 = 'https://archive.org/details/collectioavellan00guen'
SOURCE_URL_2 = 'https://archive.org/details/collectioavellan00guen_926'

# Known letter number ranges per collection based on scholarly identification.
# These are Avellana letter numbers (the Arabic numbers in parentheses in CSEL 35).
# Part 1 (letters 1-104):
#   Innocent I: letters 41, 42, 43 (letters 1-40 are imperial docs, not papal)
#   Simplicius: 56-69
#   Gelasius I: 49, 80, 81, 94-101
#   Felix III: 70-71 (synod letters from Felix's pontificate)
# Part 2 (letters 105+):
#   Hormisdas: 106-244 (most are to/from Hormisdas)
#
# Strategy: use text-based identification first (scanning letter text and header),
# then fall back to number ranges for unidentified letters.

# Text patterns to scan the FULL letter text (not just header) for sender ID
# Order matters: more specific patterns first
SENDER_PATTERNS = [
    # Innocent I - must appear as sender (in salutation or header)
    (r'\bINNOCENTIUS\b.*\b(?:AURELI|IOHAN|DILECT|FRATR)', 'innocent_i', 'Innocent I'),
    (r'(?:DILECT|FRATR).*\bINNOCENTIUS\b', 'innocent_i', 'Innocent I'),
    (r'\bINNOCENTII\s+AD\b', 'innocent_i', 'Innocent I'),
    (r'\bSANCTI\s+INNOCENTII\b', 'innocent_i', 'Innocent I'),
    # Simplicius - sender
    (r'\bSIMPLICIUS\s+EPISCOPUS\b', 'simplicius_pope', 'Simplicius'),
    (r'\bSINPLICIUS\s+EPISCOPUS\b', 'simplicius_pope', 'Simplicius'),
    (r'\bSIMPLICI\s+EPISCOPI\b', 'simplicius_pope', 'Simplicius'),
    # Gelasius I - sender (various forms in OCR)
    (r'\bGELASIUS\s+EPISCOPUS\b', 'gelasius_i', 'Gelasius I'),
    (r'\bGELASI\s+EPISCOPI\b', 'gelasius_i', 'Gelasius I'),
    (r'\bGELASII\s+(?:EPISTOLA|PAPAE)\b', 'gelasius_i', 'Gelasius I'),
    (r'\bPAPAE\s+GELASI', 'gelasius_i', 'Gelasius I'),
    (r'\bEIUSDEM\s+PAPAE\s+GELASI', 'gelasius_i', 'Gelasius I'),
    (r'\bEPISTOLA\s+GELASII\s+PAPAE\b', 'gelasius_i', 'Gelasius I'),
    (r'\bGELASIUS\s+EPISCOPIS\b', 'gelasius_i', 'Gelasius I'),  # "GELASIUS EPISCOPIS PER..."
    (r'\bGELASIUS\.\s*(?:Miramur|Licet|Ualde|Sicut|Audientes)', 'gelasius_i', 'Gelasius I'),  # salutation ending with GELASIUS
    (r'\bHONORIO\s+GELASIUS\b', 'gelasius_i', 'Gelasius I'),   # DILECTISSIMO FRATRI HONORIO GELASIUS
    (r'\bFRATRI\s+\w+\s+GELASIUS\b', 'gelasius_i', 'Gelasius I'),  # DILECTISSIMO FRATRI X GELASIUS
    # Hormisdas - sender (must appear as sender, not just recipient)
    (r'\bHORMISDA\s+(?:ANASTASIO|IUSTINO|EPIPHANIO|DOROTHEO|ENNODIO|AUITO|POSSESSORI|GERMANO|TIMOTHEO|IOHAN|UNIUERS|LEGATIS|CLERO|SYNODO|PRESBYTERIS|EPISCOPIS)\b', 'hormisdas', 'Hormisdas'),
    (r'\bHORMISDAS?\s+EPISCOPUS\b', 'hormisdas', 'Hormisdas'),
    # Hormisdas more general (appears as sender before addressee)
    (r'^(?:HORI?MISDA|HORMTSDA|HOR[MN]ISDA)\s+[A-Z]', 'hormisdas', 'Hormisdas'),
]

# Number-range fallback: ONLY for cases where text matching doesn't catch it
# These are specifically verified from the CSEL 35 edition
# NOTE: Part 1 number ranges are NOT used because the OCR has non-sequential pages
# and many letters in the 80-101 range are from OTHER popes (Leo, Agapitus, Vigilius)
NUMBER_RANGES = [
    # Part 2 only: Hormisdas (letters 106-244)
    # Part 1 Gelasius uses text-only matching due to OCR ordering issues
    (106, 244, 'hormisdas', 'Hormisdas'),
]


def clean_text(text):
    """Clean OCR noise from letter text."""
    # Remove lines that look like apparatus (digit + word + manuscript sigla)
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        s = line.strip()
        if not s:
            if cleaned and cleaned[-1]:
                cleaned.append('')
            continue
        # Skip footnote apparatus lines
        if re.match(r'^\d+\s+\w+\s+[A-Z]\b', s) and re.search(r'\bom\b|\bcorr\b|\bscripsi\b|\bBar\b|\bCar\b|\bThiel\b', s):
            continue
        if re.match(r'^\d+\.\s+Dat\.\s', s):
            continue
        cleaned.append(s)
    text = '\n'.join(cleaned).strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def identify_sender_by_text(full_text, avellana_num):
    """Identify sender by scanning the letter text, then fall back to number ranges."""
    # First try text pattern matching on the full letter content (first 600 chars = header area)
    check_text = full_text[:600]
    for pattern, collection, name in SENDER_PATTERNS:
        if re.search(pattern, check_text, re.IGNORECASE | re.MULTILINE):
            return collection, name

    # Fall back to number ranges (Part 2 only - Part 1 is excluded due to OCR ordering issues)
    for (low, high, collection, name) in NUMBER_RANGES:
        if low <= avellana_num <= high:
            return collection, name

    return None, None


def parse_avellana_letters(text, source_url):
    """
    Parse Collectio Avellana letters.
    Letters are numbered like: (1.) ... (2.) ... (105.) etc.
    The header looks like: "(105.) HORMISDA DOROTHEO..."
    or: "DILECTISSIMIS FRATRIBUS... INNOCENTIUS."

    Also handles variant formats from OCR:
    - "(41.)" at start of line
    - Lines that start with just the number in parens
    - Roman numeral headers like "XLI." or "(XLI.)"
    """
    lines = text.split('\n')
    letters = []

    # Pattern for letter number: "(NN.)" possibly with alternate numbers
    # e.g. "(41.)", "(105.)", "(49.)", "(81.)"
    # Also match "(NN. [alt])" variants
    letter_num_re = re.compile(r'^\((\d+)[\.\,]\)?')

    # Also try to catch Roman numeral markers that OCR might produce
    # e.g. lines that are just "(XLI.)" without conversion
    roman_num_re = re.compile(r'^\(([IVXLCDM]+)[\.\,]\)?', re.IGNORECASE)

    current_num = None
    current_header_lines = []
    current_body_lines = []

    def save_current():
        nonlocal current_num, current_header_lines, current_body_lines
        if current_num is None:
            return
        header = ' '.join(current_header_lines[:5])  # First few header lines
        body_raw = '\n'.join(current_body_lines)
        body = clean_text(body_raw)
        if len(body) > 30:
            # Use the full beginning of letter (header + first part of body) for ID
            id_text = header + ' ' + body[:300]
            collection, sender_name = identify_sender_by_text(id_text, current_num)
            letters.append({
                'avellana_num': current_num,
                'collection': collection,
                'sender_name': sender_name,
                'header': header[:300],
                'text': body,
            })
        current_num = None
        current_header_lines = []
        current_body_lines = []

    in_header = False

    for i, raw in enumerate(lines):
        line = raw.strip()

        if not line:
            if current_num is not None:
                current_body_lines.append('')
            continue

        # Check for letter number (Arabic)
        m = letter_num_re.match(line)
        if m:
            save_current()
            current_num = int(m.group(1))
            rest = line[m.end():].strip()
            # Strip trailing ) if present (e.g. "(41.) TEXT" -> "41" + " TEXT")
            rest = re.sub(r'^\)', '', rest).strip()
            current_header_lines = [rest] if rest else []
            current_body_lines = []
            in_header = True
            continue

        if current_num is not None:
            # Determine if we're still in header or body
            # Header ends when we hit lowercase-starting text (body text)
            if in_header:
                # All-caps lines are still header
                if re.match(r'^[A-Z][A-Z\s,\-\.]+\.?\s*$', line) and len(line) < 120:
                    current_header_lines.append(line)
                else:
                    in_header = False
                    current_body_lines.append(line)
            else:
                current_body_lines.append(line)

    save_current()
    return letters


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


def insert_letters(conn, letters, source_url):
    """Insert letters into the database."""
    cur = conn.cursor()

    # Author cache
    author_ids = {}

    # Metadata for each collection
    collection_meta = {
        'innocent_i': {
            'name': 'Innocent I', 'name_latin': 'Innocentius I',
            'role': 'pope', 'death_year': 417, 'birth_year': 370,
        },
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

    # Ensure all authors exist
    for coll_key, meta in collection_meta.items():
        aid = ensure_author(
            conn, meta['name'], meta.get('name_latin'),
            meta.get('role'), meta.get('death_year'), meta.get('birth_year')
        )
        author_ids[coll_key] = aid

    inserted = 0
    skipped = 0

    # Counter per collection for sequential numbering
    collection_counters = {}

    for letter in letters:
        if letter['collection'] is None:
            continue  # Skip letters not from our target authors

        collection = letter['collection']
        if collection not in collection_meta:
            continue

        # Use sequential numbering per collection
        if collection not in collection_counters:
            # Find existing max letter_number
            cur.execute("""
                SELECT COALESCE(MAX(letter_number), 0) FROM letters
                WHERE collection = ?
            """, (collection,))
            max_num = cur.fetchone()[0]
            collection_counters[collection] = max_num

        collection_counters[collection] += 1
        letter_num = collection_counters[collection]

        # Use avellana number as unique identifier
        ref_id = f"{collection}.ep.avellana.{letter['avellana_num']}"

        cur.execute("SELECT id FROM letters WHERE ref_id = ?", (ref_id,))
        if cur.fetchone():
            skipped += 1
            collection_counters[collection] -= 1  # revert counter
            continue

        summary = f"Collectio Avellana {letter['avellana_num']}: {letter['header'][:100]}"
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
    print("=== Collectio Avellana Scraper ===\n")

    results = []

    for path, url in [
        ('/tmp/avellana1_ocr.txt', SOURCE_URL_1),
        ('/tmp/avellana2_ocr.txt', SOURCE_URL_2),
    ]:
        if not os.path.exists(path):
            print(f"Missing: {path}")
            continue

        print(f"Processing {path}...")
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()

        letters = parse_avellana_letters(text, url)
        print(f"  Found {len(letters)} letters total")

        # Count by collection
        from collections import Counter
        coll_counts = Counter(l['collection'] for l in letters if l['collection'])
        unid = sum(1 for l in letters if l['collection'] is None)
        for coll, cnt in sorted(coll_counts.items()):
            print(f"    {coll}: {cnt}")
        if unid:
            print(f"    (unidentified): {unid}")

        # Debug: show first 10 letter numbers found
        nums = [l['avellana_num'] for l in letters[:10]]
        print(f"  First letter numbers: {nums}")

        results.extend((l, url) for l in letters)

    print(f"\nTotal processable letters: {len(results)}")

    # Show breakdown
    from collections import Counter
    all_colls = Counter(r[0]['collection'] for r in results if r[0]['collection'])
    for coll, cnt in sorted(all_colls.items()):
        print(f"  {coll}: {cnt}")

    conn = sqlite3.connect(DB_PATH, timeout=30)

    # Insert all
    total_inserted = 0
    total_skipped = 0
    for letters_batch, url in [(
        [r[0] for r in results if r[1] == SOURCE_URL_1], SOURCE_URL_1
    ), (
        [r[0] for r in results if r[1] == SOURCE_URL_2], SOURCE_URL_2
    )]:
        if letters_batch:
            ins, skp = insert_letters(conn, letters_batch, url)
            total_inserted += ins
            total_skipped += skp

    print(f"\nInserted: {total_inserted}, Skipped: {total_skipped}")

    cur = conn.cursor()
    for coll in ['innocent_i', 'simplicius_pope', 'gelasius_i', 'hormisdas']:
        cur.execute("SELECT COUNT(*) FROM letters WHERE collection=?", (coll,))
        cnt = cur.fetchone()[0]
        print(f"  {coll}: {cnt} letters in DB")

    conn.close()
    print("\nDone!")


if __name__ == '__main__':
    main()

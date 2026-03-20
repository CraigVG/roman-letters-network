#!/usr/bin/env python3
"""
Parse Gregory the Great's letters from Patrologia Latina vol. 77 OCR text.
Extracts letters NOT already in the DB (the ~433 not in the NPNF translation).

Source: archive.org/download/bim_early-english-books-1641-1700_1849_77/..._djvu.txt
This is the PL 77 OCR text (2nd impression of Migne's edition, 1849).

Letter numbering: PL 77 uses its own sequential numbering per book.
We store as gregory_great collection with letter_number = book*100000 + pl_letter_num
(using 100000 to distinguish from NPNF numbers which are book*1000 + letter).
Actually we'll use book*10000 + letter_num to fit in reasonable integer range.

NOTE: PL 77 numbering may differ from MGH/NPNF numbering for the same letters.
We use pl77_ prefix in ref_id to distinguish from NPNF-sourced letters.
"""

import sqlite3
import re
import os
import sys
import time
import urllib.request

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
TEXT_CACHE = '/tmp/pl77_gregory.txt'
ARCHIVE_URL = 'https://archive.org/download/bim_early-english-books-1641-1700_1849_77/bim_early-english-books-1641-1700_1849_77_djvu.txt'

# Book positions in PL 77 OCR text (start byte offsets)
BOOK_POSITIONS = [
    (1, 1314291),
    (2, 1634654),
    (3, 1840654),
    (4, 2049068),
    (5, 2224493),
    (6, 2449482),
    (7, 2630299),
    (8, 2793129),
    (9, 2901634),
    (10, 3298033),
    (11, 3457855),
    (12, 3778281),
    (13, 3882034),
    (14, 4035508),
]
TEXT_END = 4200000

# Gregory's sender_id in DB
GREGORY_AUTHOR_SLUG = 'gregory_i'


def roman_to_int(s: str) -> int:
    """Convert Roman numeral string to integer."""
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


def clean_ocr_text(text: str) -> str:
    """Clean common OCR errors in PL 77 Latin text."""
    # Common OCR substitutions in 19th century Latin
    replacements = [
        (r'ﬁ', 'fi'), (r'ﬂ', 'fl'), (r'ﬀ', 'ff'),
        (r'\$', 's'), (r'&', 'et'),
        (r'8upra', 'supra'), (r'8ub', 'sub'), (r'8int', 'sint'),
        (r'8e ', 'se '), (r'8it ', 'sit '), (r'8unt', 'sunt'),
        (r'8i ', 'si '), (r'8ed', 'sed'), (r'8ic', 'sic'),
        (r'8ancti', 'sancti'), (r'8acri', 'sacri'), (r'8acra', 'sacra'),
        (r'8acerdos', 'sacerdos'), (r'8olum', 'solum'),
        (r'ij', 'ii'), (r'ij ', 'ii '),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
    # Clean extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def remove_footnotes(block: str) -> str:
    """Remove obvious footnote content from a letter block."""
    lines = block.split('\n')
    result = []
    skip_mode = False
    for line in lines:
        stripped = line.strip()
        # Footnote/apparatus markers: lines starting with footnote references
        if re.match(r'^(?:Eersr|Eptisr|Eprsr|Epist|EPIST|Eerst|EERST)\s*[\.\-—]', stripped, re.I):
            skip_mode = True
        elif re.match(r'^[a-z]\s+(?:[A-Z]|In |De |Cf |Vide |Al \.)', stripped):
            # Footnote: starts with lowercase letter followed by comment
            skip_mode = True
        elif skip_mode and re.match(r'^[A-Z]{2}', stripped) and 'EPISTOLA' in stripped:
            # Back to letter content
            skip_mode = False
            result.append(line)
        elif not skip_mode:
            result.append(line)
    return '\n'.join(result)


def extract_recipient(block: str) -> str:
    """Extract recipient from AD [NAME] header."""
    # Pattern: AD [RECIPIENT NAME] on a line by itself or after EPISTOLA line
    m = re.search(r'AD\s+([A-Z][A-Z\s,\.]+?)[\.\n]', block[:500])
    if m:
        name = m.group(1).strip()
        # Clean it up
        name = re.sub(r'\s+', ' ', name)
        return name.title()
    return ''


def extract_salutation(block: str) -> str:
    """Extract Gregory's salutation (first sentence)."""
    m = re.search(r'Gregorius\s+(\w[^\.]{5,100}\.)', block)
    if m:
        return 'Gregorius ' + m.group(1)
    return ''


def extract_letter_text(block: str) -> str:
    """Extract the main letter text from a block."""
    # Find where the actual letter text starts (after the summary/description)
    # The letter text starts after "Gregorius [salutation]."
    m = re.search(r'(Gregorius\s+\w[^\.]+\.\s*\n)', block)
    if m:
        text = block[m.start():]
        # Remove footnote sections
        text = remove_footnotes(text)
        return clean_ocr_text(text)
    # Fall back: return everything after the AD line
    m2 = re.search(r'\nAD\s+', block)
    if m2:
        text = block[m2.end():]
        return clean_ocr_text(remove_footnotes(text))
    return clean_ocr_text(remove_footnotes(block))


def parse_book(book_num: int, text: str) -> list:
    """Parse all letters from a book section of PL 77 text."""
    letters = []

    # Find all EPISTOLA markers
    ep_pattern = re.compile(
        r'\bEPISTOL[AEO]+\s+([IVX]+)\b',
        re.IGNORECASE
    )
    markers = list(ep_pattern.finditer(text))

    if not markers:
        return letters

    for i, marker in enumerate(markers):
        rn = marker.group(1).upper()

        # Skip if it looks like a footnote reference (preceded by Epist. etc.)
        pre = text[max(0, marker.start()-100):marker.start()]
        if re.search(r'(?:epist|eerst|eptisr|eprsr)\s*\.\s*$', pre, re.I):
            continue
        # Also skip short Roman numerals that could be footnote refs
        if re.search(r'\.\s+$', pre.strip()) and len(rn) <= 2:
            # Could be footnote "lib. IX. Al." type reference
            pass

        try:
            letter_num = roman_to_int(rn)
        except Exception:
            continue

        if letter_num <= 0 or letter_num > 300:
            continue

        # Get the block from this marker to the next marker (or end)
        block_start = marker.start()
        block_end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        block = text[block_start:block_end]

        # Filter: block should be reasonably long (a real letter)
        if len(block.strip()) < 100:
            continue

        recipient = extract_recipient(block)
        salutation = extract_salutation(block)
        letter_text = extract_letter_text(block)

        if len(letter_text) < 50:
            continue

        letters.append({
            'book': book_num,
            'pl_letter_num': letter_num,
            'recipient_name': recipient,
            'salutation': salutation,
            'latin_text': letter_text[:8000],  # Limit to 8KB
        })

    return letters


def get_gregory_sender_id(db: sqlite3.Connection) -> int | None:
    """Get Gregory the Great's author ID."""
    row = db.execute("SELECT id FROM authors WHERE name = 'Pope Gregory the Great'").fetchone()
    return row[0] if row else None


def insert_letter(db: sqlite3.Connection, letter: dict, sender_id: int | None,
                   existing_pl77: set) -> bool:
    """Insert a letter into the DB if not already present."""
    book = letter['book']
    pl_num = letter['pl_letter_num']

    # Use a unique letter_number for PL 77 letters to distinguish from NPNF
    # Format: book * 10000 + pl_letter_num (e.g., book 1 letter 15 = 10015... wait that overlaps)
    # Better: use book * 100000 + pl_letter_num, so book 1 letter 15 = 100015
    # But letter_number is an INTEGER field - that's fine
    # Actually, to avoid conflict with NPNF numbers (which are book*1000 + letter),
    # we use a different scheme: 900000 + book*1000 + pl_letter_num for PL77 letters
    # This ensures no overlap with NPNF numbers (max NPNF = 14017)
    pl77_num = 900000 + book * 1000 + pl_num

    # Check if this PL77 letter is already in DB
    if pl77_num in existing_pl77:
        return False

    ref_id = f'gregory_pl77.{book}.{pl_num}'

    # Check if ref_id already exists
    existing = db.execute("SELECT id FROM letters WHERE ref_id = ?", (ref_id,)).fetchone()
    if existing:
        return False

    year_approx = 590 + book  # Approximate: Book 1 = 590, Book 2 = 591, etc.

    db.execute("""
        INSERT INTO letters (
            collection, book, letter_number, ref_id,
            sender_id, year_approx, year_min, year_max,
            subject_summary, latin_text, english_text,
            translation_source, source_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
    """, (
        'gregory_great',
        book,
        pl77_num,
        ref_id,
        sender_id,
        year_approx,
        589, 604,  # Gregory's pontificate
        f'To {letter["recipient_name"]}' if letter["recipient_name"] else f'Gregory the Great Book {book} Letter {pl_num}',
        letter['latin_text'],
        'needs_translation',
        f'https://archive.org/download/bim_early-english-books-1641-1700_1849_77/bim_early-english-books-1641-1700_1849_77_djvu.txt'
    ))

    return True


def main():
    # Load or download text
    if os.path.exists(TEXT_CACHE):
        print(f'Loading cached text from {TEXT_CACHE}')
        with open(TEXT_CACHE) as f:
            full_text = f.read()
    else:
        print(f'Downloading PL 77 OCR text...')
        req = urllib.request.Request(ARCHIVE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            full_text = resp.read().decode('utf-8', errors='replace')
        with open(TEXT_CACHE, 'w') as f:
            f.write(full_text)
        print(f'Downloaded {len(full_text)} chars')

    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")

    # Get existing NPNF letter numbers for Gregory
    existing_npnf = set(row[0] for row in db.execute(
        "SELECT letter_number FROM letters WHERE collection = 'gregory_great' AND letter_number < 900000"
    ))
    existing_pl77 = set(row[0] for row in db.execute(
        "SELECT letter_number FROM letters WHERE collection = 'gregory_great' AND letter_number >= 900000"
    ))
    print(f'Existing NPNF letters: {len(existing_npnf)}')
    print(f'Existing PL77 letters already in DB: {len(existing_pl77)}')

    # Get Gregory's sender ID
    sender_id = get_gregory_sender_id(db)
    print(f'Gregory sender_id: {sender_id}')

    total_inserted = 0
    total_parsed = 0

    for i, (book_num, book_start) in enumerate(BOOK_POSITIONS):
        book_end = BOOK_POSITIONS[i + 1][1] if i + 1 < len(BOOK_POSITIONS) else TEXT_END
        book_text = full_text[book_start:book_end]

        letters = parse_book(book_num, book_text)
        total_parsed += len(letters)

        inserted = 0
        for letter in letters:
            if insert_letter(db, letter, sender_id, existing_pl77):
                inserted += 1

        total_inserted += inserted
        print(f'Book {book_num:2d}: parsed {len(letters)} letters, inserted {inserted} new')

    db.commit()
    print(f'\nTotal: parsed {total_parsed}, inserted {total_inserted} new letters')

    # Summary
    final_count = db.execute(
        "SELECT COUNT(*) FROM letters WHERE collection = 'gregory_great'"
    ).fetchone()[0]
    print(f'Gregory total in DB: {final_count}')


if __name__ == '__main__':
    main()

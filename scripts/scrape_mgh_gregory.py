#!/usr/bin/env python3
"""
Scrape Gregory the Great letters from MGH (Monumenta Germaniae Historica) OCR text.

Sources:
- /tmp/mgh_greg_v1_sample.txt = MGH Epp I, Tomus II Pars II (Books X-XIV)  
- /tmp/mgh_greg_v2_sample.txt = MGH Epp I fragment (Books VIII-IX)

Both are Latin-only critical editions. We add letters NOT already in the DB.
Letter numbering: BBLLL format (book * 1000 + letter_num)
"""

import sqlite3
import re
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'roman_letters.db')

FILES = [
    ('/tmp/mgh_greg_v1_sample.txt', 'https://archive.org/details/gregoriiipapaer00greggoog', 'Books X-XIV'),
    ('/tmp/mgh_greg_v2_sample.txt', 'https://archive.org/details/gregoriiipapaer00churgoog', 'Books VIII-IX'),
]

# Book number mapping from Roman numerals to integers
ROMAN_TO_INT = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7,
    'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14,
}


def roman_to_int(s):
    s = s.strip()
    return ROMAN_TO_INT.get(s, None)


def is_apparatus_line(line):
    """Detect footnote/apparatus lines that should be skipped."""
    s = line.strip()
    if not s:
        return False
    # Footnote markers: a) b) ... or *) or 1) 2)
    if re.match(r'^[a-z]\s*\)', s) or re.match(r'^\*+\)', s):
        return True
    if re.match(r'^[a-zA-Z]\)', s) and len(s) > 3:
        return True
    # Manuscript reference lines (lots of abbreviations: codd, mss, Rl, Q*)
    if re.match(r'^[A-Z][a-z]+\s+[A-Z]', s) and ('cod' in s.lower() or 'mss' in s.lower()):
        return True
    # Long strings of superscripts/variant readings
    if s.count('^') > 2 or (s.count(',') > 5 and len(s) < 100):
        return True
    return False


def is_page_header(line):
    """Detect running headers."""
    s = line.strip()
    # Pattern: INDICTIO N. MONTH (X, N-M). PAGE
    if re.match(r'^INDICTIO\s+', s):
        return True
    if re.match(r'^GREGORII\s+\d+\.\s+REGISTRI', s):
        return True
    # Page numbers alone
    if re.match(r'^\d{1,3}\s*$', s):
        return True
    return False


def clean_letter_text(raw_lines):
    """Clean a letter's text lines."""
    cleaned = []
    skip_apparatus = False

    for raw in raw_lines:
        s = raw.strip()
        if not s:
            if cleaned and cleaned[-1]:
                cleaned.append('')
            skip_apparatus = False
            continue

        if is_page_header(s):
            continue

        if is_apparatus_line(s):
            skip_apparatus = True
            continue

        if skip_apparatus:
            # Return to main text when we see proper Latin starting with capital
            if re.match(r'^[A-Z][a-z]', s) and len(s) > 30:
                skip_apparatus = False
                cleaned.append(s)
            elif re.match(r'^[A-Z]{2,}\s+[A-Z]', s):  # GREGORIUS SOMEONE or similar
                skip_apparatus = False
                cleaned.append(s)
            continue

        cleaned.append(s)

    text = '\n'.join(cleaned)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_mgh_file(filepath):
    """
    Parse an MGH Gregory file and extract letters.
    
    Returns list of {book_num, letter_num, recipient_line, latin_text, summary}
    """
    letters = []

    with open(filepath, 'r', errors='replace') as f:
        lines = f.readlines()

    print(f"  Loaded {len(lines)} lines from {os.path.basename(filepath)}")

    # Pattern to find "BOOK_ROMAN, LETTER_NUM."
    # These appear as standalone lines: "X,  3." or "IX,  240."
    book_letter_re = re.compile(
        r'^(XIV|XIII|XII|XI|IX|VIII|VII|VI|V|IV|III|II|I)X*,\s+(\d+)\.\s*$'
    )

    # Find all letter positions
    letter_positions = []  # [(line_idx, book_num, letter_num), ...]

    for i, raw in enumerate(lines):
        s = raw.strip()
        m = book_letter_re.match(s)
        if m:
            book_roman = m.group(1)
            letter_n = int(m.group(2))
            book_n = roman_to_int(book_roman)
            if book_n and 1 <= letter_n <= 500:
                letter_positions.append((i, book_n, letter_n))

    print(f"  Found {len(letter_positions)} letter position markers")

    if not letter_positions:
        return letters

    # For each letter position, find the GREGORIVS header and extract text
    greg_re = re.compile(r'^GREGOR[IO][UV][SV]\s+(.+?)\.?\s*$')

    for idx, (line_idx, book_num, letter_num) in enumerate(letter_positions):
        # Find the next letter position
        end_line = letter_positions[idx + 1][0] if idx + 1 < len(letter_positions) else len(lines)

        # Search for GREGORIUS header within this section
        greg_header = None
        greg_line = None
        for j in range(line_idx, min(line_idx + 30, end_line)):
            m = greg_re.match(lines[j].strip())
            if m:
                greg_header = m.group(1).strip()
                greg_line = j
                break

        if greg_line is None:
            continue

        # Get the summary (lines between position marker and GREGORIUS header)
        summary_lines = []
        for j in range(line_idx + 1, greg_line):
            s = lines[j].strip()
            if s and not re.match(r'^Codd|^Edd|^$', s):
                summary_lines.append(s)

        # Extract letter text (from after GREGORIUS header to end of section)
        text_lines = list(lines[greg_line + 1:end_line])
        latin_text = clean_letter_text(text_lines)

        if len(latin_text) < 50:
            continue

        summary_text = ' '.join(summary_lines)[:400] if summary_lines else f"Gregory {book_num}.{letter_num}: {greg_header}"

        letters.append({
            'book_num': book_num,
            'letter_num': letter_num,
            'letter_number_db': book_num * 1000 + letter_num,
            'ref_id': f'gregory_great.{book_num:02d}.{letter_num:03d}',
            'recipient_line': greg_header,
            'latin_text': latin_text,
            'summary': summary_text[:400],
        })

    print(f"  Parsed {len(letters)} complete letters")
    return letters


def insert_letters(conn, letters, existing_numbers, source_url):
    """Insert new letters into the database."""
    cur = conn.cursor()

    # Get Gregory's author ID
    cur.execute("SELECT id FROM authors WHERE name = 'Gregory the Great' OR name = 'Gregory I'")
    row = cur.fetchone()
    if not row:
        cur.execute("SELECT id FROM authors WHERE name LIKE '%Gregory%' AND name LIKE '%Great%'")
        row = cur.fetchone()
    if not row:
        print("  ERROR: Could not find Gregory the Great author record!")
        return 0, 0

    author_id = row[0]

    # Get current max letter_number
    cur.execute("SELECT COALESCE(MAX(letter_number), 0) FROM letters WHERE collection='gregory_great'")
    max_letter_num = cur.fetchone()[0]

    inserted = 0
    skipped = 0

    for letter in letters:
        db_num = letter['letter_number_db']

        # Skip if already in DB (by letter_number)
        if db_num in existing_numbers:
            skipped += 1
            continue

        # Also check by ref_id
        cur.execute("SELECT id FROM letters WHERE ref_id = ?", (letter['ref_id'],))
        if cur.fetchone():
            skipped += 1
            existing_numbers.add(db_num)
            continue

        max_letter_num += 1  # We'll use the sequential counter for letter_number

        cur.execute("""
            INSERT INTO letters (
                collection, letter_number, ref_id, book,
                sender_id, latin_text, subject_summary, source_url,
                translation_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'gregory_great',
            db_num,  # Use BBLLL format to maintain ordering
            letter['ref_id'],
            letter['book_num'],
            author_id,
            letter['latin_text'],
            letter['summary'],
            source_url,
            'none',
        ))
        inserted += 1
        existing_numbers.add(db_num)

        if inserted % 25 == 0:
            conn.commit()
            print(f"  Inserted {inserted} so far...")

    conn.commit()
    return inserted, skipped


def main():
    print("=== MGH Gregory the Great Scraper ===\n")

    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    # Get existing Gregory letter numbers
    cur.execute("SELECT letter_number FROM letters WHERE collection='gregory_great'")
    existing_numbers = set(row[0] for row in cur.fetchall())
    print(f"Existing Gregory letters in DB: {len(existing_numbers)}")

    total_inserted = 0
    total_skipped = 0

    for filepath, source_url, description in FILES:
        if not os.path.exists(filepath):
            print(f"\nMISSING: {filepath}")
            continue

        print(f"\n--- {description} ---")
        print(f"  File: {filepath}")

        letters = parse_mgh_file(filepath)
        if not letters:
            print("  No letters parsed!")
            continue

        # Show what we found
        by_book = {}
        for l in letters:
            b = l['book_num']
            by_book[b] = by_book.get(b, 0) + 1
        for b in sorted(by_book.keys()):
            print(f"  Book {b}: {by_book[b]} letters")

        ins, skp = insert_letters(conn, letters, existing_numbers, source_url)
        print(f"  Inserted: {ins}, Skipped: {skp}")
        total_inserted += ins
        total_skipped += skp

    # Final summary
    print(f"\n{'='*50}")
    cur.execute("SELECT COUNT(*) FROM letters WHERE collection='gregory_great'")
    total = cur.fetchone()[0]
    print(f"Total Gregory letters now: {total}")
    print(f"Newly inserted: {total_inserted}")

    # Show new distribution
    cur.execute("SELECT book, COUNT(*) FROM letters WHERE collection='gregory_great' GROUP BY book")
    print("\nBy book (book column):")
    for row in sorted(cur.fetchall()):
        print(f"  Book {row[0]}: {row[1]}")

    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())

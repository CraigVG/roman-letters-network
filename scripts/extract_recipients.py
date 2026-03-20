#!/usr/bin/env python3
"""
Parse letter texts to extract recipient information and link to authors table.
This creates the edges needed for the network visualization.

Late antique letters typically begin with patterns like:
- "To Marcellinus"
- "Augustine to Marcellinus"
- "Letter I. (A.D. 386) To Hermogenianus."
- "To the Emperor Theodosius"
- "Book I. Letter I. To Januarius, Bishop"
"""

import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')


def normalize_name(name):
    """Clean up a recipient name for matching."""
    name = name.strip()
    # Remove titles and prefixes
    for prefix in ['St.', 'Saint', 'Bishop', 'Pope', 'Emperor', 'the', 'his', 'her',
                   'Rev.', 'Lord', 'Lady', 'King', 'Queen', 'Count', 'Deacon',
                   'Priest', 'Prefect', 'Consul', 'Tribune']:
        name = re.sub(rf'\b{prefix}\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+', ' ', name).strip()
    # Remove trailing punctuation
    name = name.rstrip('.,;:')
    return name


def extract_recipient_from_text(text, collection):
    """Extract recipient name from letter text using various patterns."""
    if not text:
        return None

    lines = text.split('\n')
    candidates = []

    for line in lines[:30]:  # Check first 30 lines
        line = line.strip()
        if not line or len(line) < 3:
            continue

        # Pattern: "To NAME" at start of line
        m = re.match(r'^To\s+(?:the\s+)?(.+?)[\.\,\s]*$', line, re.IGNORECASE)
        if m and len(m.group(1)) > 2 and len(m.group(1)) < 100:
            candidates.append(m.group(1))

        # Pattern: "SENDER to RECIPIENT"
        m = re.match(r'^(?:\w+\s+){1,3}to\s+(.+?)[\.\,\s]*$', line, re.IGNORECASE)
        if m and len(m.group(1)) > 2 and len(m.group(1)) < 100:
            # Make sure it's not a sentence
            if not any(w in m.group(1).lower() for w in ['which', 'that', 'this', 'what', 'where', 'when']):
                candidates.append(m.group(1))

        # Pattern: "Letter N. To NAME" or "Epistle N. To NAME"
        m = re.match(r'^(?:Letter|Epistle|Ep\.?)\s+[IVXLCDM\d]+\.?\s+(?:\([^)]+\)\s*)?To\s+(.+?)[\.\,]*$', line, re.IGNORECASE)
        if m:
            candidates.append(m.group(1))

        # Pattern: "Book N. Letter N. To NAME"
        m = re.match(r'^Book\s+[IVXLCDM\d]+\.?\s+(?:Letter|Epistle)\s+[IVXLCDM\d]+\.?\s+To\s+(.+?)[\.\,]*$', line, re.IGNORECASE)
        if m:
            candidates.append(m.group(1))

        # Gregory the Great specific: "To PETER, Bishop of..."
        if collection == 'gregory_great':
            m = re.match(r'^(?:Epistle\s+[IVXLCDM\d]+\.?\s+)?To\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', line)
            if m:
                candidates.append(m.group(1))

    # Return first valid candidate
    for c in candidates:
        name = normalize_name(c)
        if name and len(name) > 1 and len(name) < 80:
            return name

    return None


def find_or_create_author(cursor, name):
    """Find an existing author by name or create a new one."""
    if not name:
        return None

    clean = normalize_name(name)
    if not clean or len(clean) < 2:
        return None

    # Try exact match
    cursor.execute('SELECT id FROM authors WHERE name = ?', (clean,))
    row = cursor.fetchone()
    if row:
        return row[0]

    # Try partial match
    cursor.execute('SELECT id, name FROM authors WHERE name LIKE ?', (f'%{clean}%',))
    row = cursor.fetchone()
    if row:
        return row[0]

    # Try matching just the first word (many recipients are single names)
    first_word = clean.split()[0] if clean else ''
    if first_word and len(first_word) > 2:
        cursor.execute('SELECT id, name FROM authors WHERE name LIKE ?', (f'%{first_word}%',))
        row = cursor.fetchone()
        if row:
            return row[0]

    # Create new author
    cursor.execute('INSERT INTO authors (name) VALUES (?)', (clean,))
    return cursor.lastrowid


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()

    # Get all letters with English text
    cursor.execute('''
        SELECT id, collection, english_text, sender_id
        FROM letters
        WHERE english_text IS NOT NULL AND recipient_id IS NULL
    ''')
    letters = cursor.fetchall()
    print(f"Processing {len(letters)} letters without recipients...")

    matched = 0
    created = 0
    failed = 0

    for letter_id, collection, text, sender_id in letters:
        recipient_name = extract_recipient_from_text(text, collection)

        if recipient_name:
            # Check if this creates an existing author match or new
            cursor.execute('SELECT COUNT(*) FROM authors WHERE name LIKE ?', (f'%{recipient_name.split()[0]}%',))
            existed_before = cursor.fetchone()[0] > 0

            recipient_id = find_or_create_author(cursor, recipient_name)
            if recipient_id:
                cursor.execute('UPDATE letters SET recipient_id = ? WHERE id = ?', (recipient_id, letter_id))
                if existed_before:
                    matched += 1
                else:
                    created += 1
        else:
            failed += 1

    conn.commit()

    print(f"\nResults:")
    print(f"  Matched to existing people: {matched}")
    print(f"  Created new people: {created}")
    print(f"  Could not extract recipient: {failed}")

    # Show network stats
    cursor.execute('''
        SELECT COUNT(DISTINCT sender_id || '-' || recipient_id)
        FROM letters
        WHERE sender_id IS NOT NULL AND recipient_id IS NOT NULL
    ''')
    print(f"  Unique connections: {cursor.fetchone()[0]}")

    cursor.execute('SELECT COUNT(*) FROM authors')
    print(f"  Total people in database: {cursor.fetchone()[0]}")

    # Show top connections
    cursor.execute('''
        SELECT s.name, r.name, COUNT(*) as cnt
        FROM letters l
        JOIN authors s ON l.sender_id = s.id
        JOIN authors r ON l.recipient_id = r.id
        GROUP BY l.sender_id, l.recipient_id
        ORDER BY cnt DESC
        LIMIT 20
    ''')
    print(f"\nTop letter connections:")
    for row in cursor.fetchall():
        print(f"  {row[0]} -> {row[1]}: {row[2]} letters")

    conn.close()


if __name__ == '__main__':
    main()

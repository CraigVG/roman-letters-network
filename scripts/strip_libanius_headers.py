#!/usr/bin/env python3
"""
Strip 'From:/To:/Date:/Context:' header blocks from Libanius letters 168-328.
These headers are inconsistent with letters 1-167 and 329+.
The recipient/date info is already in the body text itself.
"""

import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')


def strip_header(text):
    """Remove the From:/To:/Date:/Context: header block from a modern_english field."""
    if not text:
        return text
    if not text.startswith('From:'):
        return text

    lines = text.split('\n')
    # Find the first blank line after the header (header is 4 lines: From, To, Date, Context)
    content_start = None
    for i, line in enumerate(lines):
        if line.strip() == '' and i >= 3:
            content_start = i + 1
            break

    if content_start is None:
        return text

    content = '\n'.join(lines[content_start:]).strip()
    return content


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    cur.execute("""
        SELECT id, letter_number, modern_english
        FROM letters
        WHERE collection = 'libanius'
          AND letter_number BETWEEN 168 AND 328
          AND modern_english LIKE 'From:%'
        ORDER BY letter_number
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} letters with headers to strip")

    updated = 0
    for row in rows:
        letter_id, letter_num, modern_english = row
        stripped = strip_header(modern_english)
        if stripped != modern_english and stripped:
            conn.execute(
                'UPDATE letters SET modern_english = ? WHERE id = ?',
                (stripped, letter_id)
            )
            updated += 1

    conn.commit()
    print(f"Stripped headers from {updated} letters")

    # Verify
    cur.execute("""
        SELECT letter_number, modern_english FROM letters
        WHERE collection = 'libanius' AND letter_number IN (168, 200, 250, 300, 328)
        ORDER BY letter_number
    """)
    print("\nSample after strip:")
    for r in cur.fetchall():
        print(f"  Letter {r[0]}: {(r[1] or '')[:80]!r}")

    conn.close()


if __name__ == '__main__':
    main()

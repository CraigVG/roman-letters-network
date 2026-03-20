#!/usr/bin/env python3
"""
Add 'To [Name]. (date)' line to Libanius letters 168-328 that had it stripped.
Matches the format of letters 1-167.
"""
import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')


def extract_date(greek_text):
    """Extract date from Greek text opening like 'Ἀνατολίῳ. (358)'."""
    if not greek_text:
        return None
    m = re.search(r'\(([^)]+)\)', greek_text[:120])
    return m.group(1) if m else None


def clean_recipient(name):
    """Clean up recipient name for display."""
    if not name:
        return 'Unknown'
    # Take first name if multiple
    if ';' in name:
        name = name.split(';')[0].strip()
    # Remove trailing descriptors like ", sophist" or ", general" for the header
    # Actually keep them - they're useful context
    return name.strip()


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    cur.execute("""
        SELECT l.id, l.letter_number, l.modern_english, l.latin_text, l.year_approx,
               r.name AS recipient_name
        FROM letters l
        LEFT JOIN authors r ON l.recipient_id = r.id
        WHERE l.collection = 'libanius'
          AND l.letter_number BETWEEN 168 AND 328
          AND (l.modern_english NOT LIKE 'To %' OR l.modern_english IS NULL)
        ORDER BY l.letter_number
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} letters needing 'To' header")

    updated = 0
    for row in rows:
        letter_id, letter_num, modern_english, greek_text, year_approx, recipient_name = row

        if not modern_english:
            continue

        # Get date
        date_str = extract_date(greek_text)
        if not date_str and year_approx:
            date_str = str(year_approx)
        if not date_str:
            date_str = '?'

        # Clean recipient
        recip = clean_recipient(recipient_name)

        # Build header line
        header = f"To {recip}. ({date_str})"

        # Prepend to modern_english
        new_text = header + "\n\n" + modern_english.strip()

        conn.execute(
            'UPDATE letters SET modern_english = ? WHERE id = ?',
            (new_text, letter_id)
        )
        updated += 1

    conn.commit()
    print(f"Added 'To' headers to {updated} letters")

    # Verify
    cur.execute("""
        SELECT letter_number, modern_english FROM letters
        WHERE collection = 'libanius' AND letter_number IN (168, 200, 250, 300, 328)
        ORDER BY letter_number
    """)
    print("\nSample after fix:")
    for r in cur.fetchall():
        print(f"  Letter {r[0]}: {(r[1] or '')[:100]!r}")

    conn.close()


if __name__ == '__main__':
    main()

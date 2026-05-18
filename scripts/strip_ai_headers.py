#!/usr/bin/env python3
"""Strip AI metadata headers (From:/To:/Date:/Context:) from modern_english translations.

These headers were added by the translation pipeline per the voice guide instruction
but are redundant with page metadata and identify translations as AI-generated.

Run: python scripts/strip_ai_headers.py [--dry-run]
"""

import re
import sqlite3
import sys

DB_PATH = "data/roman_letters.db"

# Pattern: From: line, To: line, Date: line, Context: line(s), then blank line
# The Context line can span multiple lines until a double newline
HEADER_PATTERN = re.compile(
    r'^From:.*?\n'
    r'To:.*?\n'
    r'Date:.*?\n'
    r'Context:.*?\n'
    r'\n',
    re.DOTALL
)

# Some letters have a shorter header (just From/To without Date/Context)
SHORT_HEADER = re.compile(
    r'^From:.*?\n'
    r'To:.*?\n'
    r'\n',
    re.DOTALL
)

# Some letters skip To: line (From/Date/Context)
NO_TO_HEADER = re.compile(
    r'^From:.*?\n'
    r'Date:.*?\n'
    r'Context:.*?\n'
    r'\n',
    re.DOTALL
)


def strip_header(text: str) -> str:
    """Remove AI metadata header from the start of a translation."""
    # Try full header first
    stripped = HEADER_PATTERN.sub('', text, count=1)
    if stripped != text:
        return stripped.lstrip('\n')

    # Try short header
    stripped = SHORT_HEADER.sub('', text, count=1)
    if stripped != text:
        return stripped.lstrip('\n')

    # Try no-To header
    stripped = NO_TO_HEADER.sub('', text, count=1)
    if stripped != text:
        return stripped.lstrip('\n')

    return text


def main():
    dry_run = '--dry-run' in sys.argv

    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, collection, letter_number, modern_english
        FROM letters
        WHERE modern_english LIKE 'From:%'
    """)

    rows = cur.fetchall()
    print(f"Found {len(rows)} letters with From: headers")

    updated = 0
    unchanged = 0

    for row_id, collection, letter_num, text in rows:
        stripped = strip_header(text)
        if stripped != text:
            removed_chars = len(text) - len(stripped)
            if dry_run:
                print(f"  [DRY RUN] {collection}/{letter_num} (id={row_id}): strip {removed_chars} chars header")
            else:
                cur.execute("UPDATE letters SET modern_english = ? WHERE id = ?", (stripped, row_id))
            updated += 1
        else:
            # Header didn't match expected pattern — log for review
            first_line = text.split('\n')[0][:80]
            print(f"  [UNCHANGED] {collection}/{letter_num} (id={row_id}): '{first_line}...'")
            unchanged += 1

    if not dry_run:
        conn.commit()
        print(f"\nStripped headers from {updated} letters")
    else:
        print(f"\nWould strip headers from {updated} letters (dry run)")

    if unchanged:
        print(f"{unchanged} letters had 'From:' but didn't match header pattern (review needed)")

    # Verify
    cur.execute("SELECT COUNT(*) FROM letters WHERE modern_english LIKE 'From:%'")
    remaining = cur.fetchone()[0]
    print(f"Letters still starting with 'From:': {remaining}")

    conn.close()


if __name__ == '__main__':
    main()

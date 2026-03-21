#!/usr/bin/env python3
"""
Generate quick_summary for letters that are missing them.
Extracts the first meaningful sentence from the modern_english field.
"""

import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

HEADER_PREFIXES = (
    'From:', 'To:', 'Date:', 'Subject:', 'Context:', 'Place:',
    'Written', '[Context', '[Note', '[This', 'LETTER', 'Letter',
    'Pope ', 'Bishop ',
)


def generate_summary(modern_english):
    """Generate a <=120 char summary from the first meaningful sentence."""
    if not modern_english:
        return None

    lines = modern_english.strip().split('\n')
    body_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Skip header/metadata lines
        if any(stripped.startswith(prefix) for prefix in HEADER_PREFIXES):
            continue
        # Skip "To X, from Y." greeting lines
        if re.match(r'^To .+, from .+\.?\s*$', stripped):
            continue
        # Skip greeting lines like "Sidonius to his dear Firminus, greetings."
        if re.match(r'^[A-Z][a-z]+ to (his |her |the |their )', stripped):
            continue
        # Skip "To Name." or "To Name (date)" short lines
        if re.match(r'^To [A-Z]', stripped) and len(stripped) < 50:
            continue
        # Skip short standalone lines that look like titles
        if len(stripped) < 40 and stripped.endswith('.') and ' to ' in stripped.lower():
            continue
        # Skip numbered section headers like "1." alone
        if re.match(r'^\d+\.\s*$', stripped):
            continue
        body_lines.append(stripped)

    if not body_lines:
        return None

    text = body_lines[0]

    # Strip leading section numbers like "1. " or "I. "
    text = re.sub(r'^(\d+|[IVXLCDM]+)\.\s+', '', text)

    # Take first sentence (up to first period, question mark, or exclamation)
    summary = text
    for i, ch in enumerate(text):
        if ch in '.?!' and i > 20:
            summary = text[:i+1]
            break

    # Truncate to 120 chars
    if len(summary) > 120:
        # Try to break at a word boundary
        truncated = summary[:117].rsplit(' ', 1)[0]
        summary = truncated + '...'

    return summary if summary else None


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()

    # Ensure WAL checkpoint before we start
    cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    # Count letters needing summaries
    cursor.execute("SELECT COUNT(*) FROM letters WHERE quick_summary IS NULL OR quick_summary = ''")
    need_count = cursor.fetchone()[0]
    print(f"Letters needing summaries: {need_count}")

    if need_count == 0:
        print("All letters already have summaries.")
        conn.close()
        return

    # Fetch letters with modern_english that need summaries
    cursor.execute('''
        SELECT id, modern_english
        FROM letters
        WHERE (quick_summary IS NULL OR quick_summary = '')
          AND modern_english IS NOT NULL AND modern_english != ''
    ''')
    letters = cursor.fetchall()
    print(f"Letters with modern_english to process: {len(letters)}")

    updated = 0
    skipped = 0
    samples = []

    for letter_id, modern_english in letters:
        summary = generate_summary(modern_english)
        if summary:
            cursor.execute(
                "UPDATE letters SET quick_summary = ? WHERE id = ?",
                (summary, letter_id)
            )
            updated += 1
            if len(samples) < 10:
                samples.append((letter_id, summary))
        else:
            skipped += 1

        if updated % 500 == 0 and updated > 0:
            conn.commit()
            print(f"  Updated {updated} so far...")

    conn.commit()

    # Force WAL checkpoint to ensure data is written to main DB file
    cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    # Report
    print(f"\nResults:")
    print(f"  Letters updated: {updated}")
    print(f"  Letters skipped (no extractable summary): {skipped}")

    # Remaining without summaries
    cursor.execute("SELECT COUNT(*) FROM letters WHERE quick_summary IS NULL OR quick_summary = ''")
    remaining = cursor.fetchone()[0]
    print(f"  Remaining without summaries: {remaining}")

    # Show samples
    print(f"\nSample summaries (first 10):")
    for letter_id, summary in samples:
        print(f"  [{letter_id}] {summary}")

    conn.close()


if __name__ == '__main__':
    main()

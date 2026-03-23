#!/usr/bin/env python3
"""Strip New Advent advertising/attribution text from english_text field.

Removes footer text like:
- "About this page" sections
- "$19.99" promotional text
- "Kevin Knight" editor contact info
- New Advent URLs and copyright notices

Run: python scripts/clean_english_text.py [--dry-run]
"""

import re
import sqlite3
import sys

DB_PATH = "data/roman_letters.db"

# Patterns to strip from the END of english_text.
# These appear as footer boilerplate from New Advent scraping.
STRIP_PATTERNS = [
    # "Get this entire Catholic website as an instant digital download..." block (Ambrose-style ads)
    r'\s*Get this entire Catholic website as an instant digital download.*$',
    # "Please help support..." through end (the $19.99 ad)
    r'\s*Please help support the mission of New Advent.*$',
    # "Contact information. The editor of New Advent is Kevin Knight..." through end
    r'\s*Contact information\.\s*The editor of New Advent is Kevin Knight.*$',
    # "About this page" section (sometimes appears as heading)
    r'\s*About this page\s*.*$',
    # Standalone "The editor of New Advent..." without "Contact information" prefix
    r'\s*The editor of New Advent is Kevin Knight.*$',
    # Translated/edited for New Advent by Kevin Knight + URL + contact
    r'\s*Translated by [^.]+\.\s*Revised and edited for New Advent by Kevin Knight\.?\s*<https?://[^>]+>\.?\s*Contact information.*$',
    r'\s*Revised and edited for New Advent by Kevin Knight\.?\s*<https?://[^>]+>\.?\s*Contact information.*$',
    # Just the URL + contact block
    r'\s*<https?://www\.newadvent\.org/[^>]+>\.?\s*Contact information.*$',
    # News headlines that got scraped in (e.g., "Pope Leo XIV's Sunday Angelus...")
    r"\s*Pope Leo XIV's Sunday Angelus.*$",
    # "The Complete List of Popes" block
    r'\s*The Complete List of Popes.*$',
    # "The Secret Sauce" and other news article titles that got scraped
    r'\s*The Secret Sauce That Keeps.*$',
]

# Compile as DOTALL so . matches newlines within the footer block
COMPILED = [re.compile(p, re.DOTALL | re.IGNORECASE) for p in STRIP_PATTERNS]


def clean_text(text: str) -> str:
    """Remove New Advent boilerplate from the end of english_text."""
    cleaned = text
    for pattern in COMPILED:
        cleaned = pattern.sub('', cleaned)
    # Remove any trailing whitespace left behind
    return cleaned.rstrip()


def main():
    dry_run = '--dry-run' in sys.argv

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Find all letters with New Advent boilerplate
    cur.execute("""
        SELECT id, collection, letter_number, english_text
        FROM letters
        WHERE english_text LIKE '%Kevin Knight%'
           OR english_text LIKE '%newadvent.org%'
           OR english_text LIKE '%$19.99%'
           OR english_text LIKE '%Please help support the mission of New Advent%'
           OR english_text LIKE '%About this page%'
           OR english_text LIKE '%Get this entire Catholic website%'
           OR english_text LIKE '%The Complete List of Popes%'
    """)

    rows = cur.fetchall()
    print(f"Found {len(rows)} letters with New Advent boilerplate")

    updated = 0
    for row_id, collection, letter_num, text in rows:
        cleaned = clean_text(text)
        if cleaned != text:
            removed_chars = len(text) - len(cleaned)
            if dry_run:
                print(f"  [DRY RUN] {collection}/{letter_num} (id={row_id}): would remove {removed_chars} chars")
            else:
                cur.execute("UPDATE letters SET english_text = ? WHERE id = ?", (cleaned, row_id))
            updated += 1

    if not dry_run:
        conn.commit()
        print(f"Updated {updated} letters")
    else:
        print(f"Would update {updated} letters (dry run)")

    # Verify no remaining ads
    cur.execute("SELECT COUNT(*) FROM letters WHERE english_text LIKE '%$19.99%'")
    remaining = cur.fetchone()[0]
    if remaining > 0:
        print(f"WARNING: {remaining} letters still contain '$19.99' text")
    else:
        print("Verified: no '$19.99' text remains")

    conn.close()


if __name__ == '__main__':
    main()

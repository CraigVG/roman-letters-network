#!/usr/bin/env python3
"""Scrape Cicero's Letters to Atticus from The Latin Library and insert into DB."""

import re
import sqlite3
import time
import urllib.request

DB_PATH = "/Users/drillerdbmacmini/Documents/GitHub/roman-letters-network/data/roman_letters.db"
BASE_URL = "https://www.thelatinlibrary.com/cicero/att{}.shtml"

CICERO_ID = 2014
ATTICUS_ID = 2015

YEAR_BY_BOOK = {
    1: -66, 2: -60, 3: -58, 4: -56, 5: -51, 6: -50, 7: -49, 8: -49,
    9: -49, 10: -49, 11: -47, 12: -46, 13: -45, 14: -44, 15: -44, 16: -43
}


def fetch_page(book_num):
    """Fetch HTML for a given book number."""
    url = BASE_URL.format(book_num)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("latin-1")


def strip_html(text):
    """Remove HTML tags and clean up text."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    text = text.replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_letters(html, book_num):
    """Parse individual letters from the HTML of one book page."""
    letters = []

    # Match anchors in both formats:
    #   <a name="1">    (quoted, books 1-11)
    #   <a name=1>      (unquoted, books 12-16)
    #   <A name=1>      (uppercase)
    # Anchor values can be: 1, 5a, 13-14, 13a, 13b, etc.
    # We split on these anchors.
    pattern = r'<[aA]\s+name=["\']?([^"\'>\s]+)["\']?\s*>'
    parts = re.split(pattern, html, flags=re.IGNORECASE)

    # parts[0] is before first anchor, then alternating: anchor_id, content
    if len(parts) < 3:
        print(f"  WARNING: No letter anchors found in book {book_num}")
        return letters

    for i in range(1, len(parts), 2):
        anchor_id = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ""

        # Remove the header (everything up to and including </CENTER> or </center>)
        header_match = re.search(r'</[Cc][Ee][Nn][Tt][Ee][Rr]>', content)
        if header_match:
            content = content[header_match.end():]

        # Trim at smallborder separator
        content = re.split(r'<[Pp]\s+class=smallborder>', content)[0]

        # Remove footer content
        content = re.split(r'<[Pp]\s+class=pagehead>', content)[0]
        content = re.split(r'The Latin Library', content)[0]

        # Strip HTML tags
        latin_text = strip_html(content)

        # Skip if empty or too short
        if not latin_text or len(latin_text) < 10:
            continue

        letters.append({
            "anchor_id": anchor_id,
            "latin_text": latin_text,
        })

    return letters


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if any letters already exist for this collection
    cur.execute("SELECT COUNT(*) FROM letters WHERE collection='cicero_atticus'")
    existing = cur.fetchone()[0]
    if existing > 0:
        print(f"Already have {existing} letters for cicero_atticus. Aborting to avoid duplicates.")
        conn.close()
        return

    global_letter_num = 0
    total_by_book = {}

    for book_num in range(1, 17):
        print(f"Fetching Book {book_num}...")
        html = fetch_page(book_num)
        letters = parse_letters(html, book_num)
        total_by_book[book_num] = len(letters)
        print(f"  Found {len(letters)} letters (anchors: {[l['anchor_id'] for l in letters]})")

        year = YEAR_BY_BOOK[book_num]

        for letter in letters:
            global_letter_num += 1
            cur.execute("""
                INSERT INTO letters (collection, book, letter_number, sender_id, recipient_id,
                                     latin_text, translation_source, year_approx, source_url)
                VALUES (?, ?, ?, ?, ?, ?, 'latin_only', ?, ?)
            """, (
                'cicero_atticus',
                book_num,
                global_letter_num,
                CICERO_ID,
                ATTICUS_ID,
                letter['latin_text'],
                year,
                BASE_URL.format(book_num),
            ))

        conn.commit()
        time.sleep(1)  # Be polite to the server

    print(f"\n{'='*50}")
    print(f"IMPORT COMPLETE")
    print(f"{'='*50}")
    print(f"Total letters imported: {global_letter_num}")
    print(f"\nLetters per book:")
    for book, count in sorted(total_by_book.items()):
        print(f"  Book {book:2d}: {count:3d} letters")

    conn.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
scrape_pliny_latin.py

Fetches Latin text for Pliny the Younger's letters from The Latin Library
and updates the roman_letters.db database.

The Latin Library pages: https://www.thelatinlibrary.com/pliny.ep{1-10}.html
DB letter_number convention: book * 1000 + original_number
  e.g., Book 1 Letter 3 -> letter_number = 1003

Book 10 has "A"/"B" letter pairs (e.g., "3 A" / "3 B" are a letter + its response).
The DB merges these into a single letter_number by treating both A and B text
as belonging to the base number (the DB skips 10003 and 10017 which were
originally the "B" entries — we just concatenate A+B text into the base number).
"""

import urllib.request
import re
import sqlite3
import sys
import time

DB_PATH = "/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db"
BASE_URL = "https://www.thelatinlibrary.com/pliny.ep{}.html"
BOOKS = range(1, 11)


def fetch_page(url: str) -> str:
    """Fetch a URL and return decoded text. The Latin Library is UTF-8 per meta tag."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    # Page declares UTF-8 but may have some latin-1 characters; use replace to be safe
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def strip_tags(html: str) -> str:
    """Remove HTML tags and decode common HTML entities."""
    # Remove <span...>...</span> section number markers (e.g. <span ...>1</span>)
    text = re.sub(r"<span[^>]*>\d+</span>", "", html)
    # Remove remaining tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode HTML entities
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    text = text.replace("&#151;", "\u2014").replace("&mdash;", "\u2014")
    text = text.replace("&#160;", " ").replace("&nbsp;", " ")
    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_letters(html: str, book: int) -> dict:
    """
    Parse the page HTML into a dict mapping letter_number -> latin_text.

    Letter headers look like: <p><b>3</b>\n</p> or <p><b>3 A</b>\n</p>
    The text of the letter follows in subsequent <p> blocks until the next
    letter header or the nav footer.

    Returns: {letter_number (int): text (str)}
    """
    # Split on letter-number headers. Pattern: <b> followed by digits and optional A/B suffix.
    # We'll work with the raw HTML and split on letter boundaries.

    # Find all letter header positions and their labels
    header_pattern = re.compile(
        r"<[Pp][^>]*>\s*<[Bb]>(\d+(?:\s*[AB])?)</[Bb]>\s*</[Pp]>",
        re.IGNORECASE,
    )

    matches = list(header_pattern.finditer(html))
    if not matches:
        print(f"  WARNING: No letter headers found for book {book}", file=sys.stderr)
        return {}

    letters = {}
    # Track the last seen base number to detect out-of-sequence labels (typos on the site)
    last_base_num = 0

    for i, match in enumerate(matches):
        raw_label = match.group(1).strip()
        # Determine base number (strip trailing A/B)
        base_match = re.match(r"^(\d+)(?:\s*[AB])?$", raw_label, re.IGNORECASE)
        if not base_match:
            continue
        base_num = int(base_match.group(1))
        is_b_variant = bool(re.search(r"[AB]$", raw_label, re.IGNORECASE))

        # Detect out-of-sequence label (page typo): if the label goes backward
        # (and it's not a B-variant of the previous letter), infer the correct
        # number as last_base_num + 1.
        if not is_b_variant and base_num <= last_base_num - 5:
            inferred = last_base_num + 1
            print(
                f"  TYPO detected in book {book}: label '{raw_label}' at position {i} "
                f"is out of sequence (last={last_base_num}); treating as {inferred}.",
                file=sys.stderr,
            )
            base_num = inferred

        letter_number = book * 1000 + base_num
        if not is_b_variant:
            last_base_num = base_num

        # Extract HTML between this header and the next (or end of content)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        chunk = html[start:end]

        # Strip the navigation footer if it crept in
        nav_pos = chunk.find('<p class=border>')
        if nav_pos == -1:
            nav_pos = chunk.find('<table')
        if nav_pos != -1:
            chunk = chunk[:nav_pos]

        text = strip_tags(chunk).strip()

        if letter_number in letters:
            # A/B pair — append B text to A text (same DB entry)
            if text:
                letters[letter_number] = letters[letter_number] + "\n\n" + text
        else:
            letters[letter_number] = text

    return letters


def update_database(letters_by_book: dict) -> tuple:
    """
    Update the database with Latin text.
    Only updates rows where latin_text IS NULL or length < 50.

    Returns (updated_count, skipped_count, not_found_count).
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    updated = 0
    skipped = 0
    not_found = 0

    for letter_number, text in sorted(letters_by_book.items()):
        if not text or len(text) < 10:
            skipped += 1
            continue

        # Check if the row exists and needs updating
        cur.execute(
            """
            SELECT id, latin_text
            FROM letters
            WHERE collection = 'pliny_younger' AND letter_number = ?
            """,
            (letter_number,),
        )
        row = cur.fetchone()

        if row is None:
            not_found += 1
            print(
                f"  NOT FOUND in DB: letter_number={letter_number}",
                file=sys.stderr,
            )
            continue

        row_id, existing_text = row

        if existing_text and len(existing_text) >= 50:
            skipped += 1
            continue

        cur.execute(
            """
            UPDATE letters
            SET latin_text = ?
            WHERE id = ?
            """,
            (text, row_id),
        )
        updated += 1

    conn.commit()
    conn.close()
    return updated, skipped, not_found


def main():
    all_letters = {}
    total_scraped = 0

    for book in BOOKS:
        url = BASE_URL.format(book)
        print(f"Book {book}: fetching {url} ...", flush=True)
        try:
            html = fetch_page(url)
        except Exception as e:
            print(f"  ERROR fetching book {book}: {e}", file=sys.stderr)
            continue

        letters = parse_letters(html, book)
        nonempty = {k: v for k, v in letters.items() if v and len(v) >= 10}
        print(f"  Parsed {len(nonempty)} letters from HTML.")
        total_scraped += len(nonempty)
        all_letters.update(nonempty)

        # Be polite to the server
        if book < max(BOOKS):
            time.sleep(1)

    print(f"\nTotal letters scraped: {total_scraped}")
    print("Updating database...")

    updated, skipped, not_found = update_database(all_letters)

    print(f"\n--- Results ---")
    print(f"  Letters updated with Latin text: {updated}")
    print(f"  Skipped (already had text or scraped text too short): {skipped}")
    print(f"  Not found in DB: {not_found}")

    # Verification query
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) FROM letters
        WHERE collection = 'pliny_younger'
        AND latin_text IS NOT NULL
        AND length(latin_text) >= 50
        """
    )
    (with_text,) = cur.fetchone()
    cur.execute(
        "SELECT COUNT(*) FROM letters WHERE collection = 'pliny_younger'"
    )
    (total,) = cur.fetchone()
    conn.close()

    print(f"\n  DB verification: {with_text}/{total} pliny_younger letters now have Latin text.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Scrape Seneca's Epistulae Morales ad Lucilium from The Latin Library."""

import re
import sqlite3
import time
import urllib.request
from bs4 import BeautifulSoup

DB_PATH = "/Users/drillerdbmacmini/Documents/GitHub/roman-letters-network/data/roman_letters.db"
BASE_URL = "https://www.thelatinlibrary.com/sen/"

# Book URLs and the letter ranges they contain
BOOK_URLS = [
    ("seneca.ep1.shtml", 1),
    ("seneca.ep2.shtml", 2),
    ("seneca.ep3.shtml", 3),
    ("seneca.ep4.shtml", 4),
    ("seneca.ep5.shtml", 5),
    ("seneca.ep6.shtml", 6),
    ("seneca.ep7.shtml", 7),
    ("seneca.ep8.shtml", 8),
    ("seneca.ep9.shtml", 9),
    ("seneca.ep10.shtml", 10),
    ("seneca.ep11-13.shtml", 11),  # Books 11-13 combined
    ("seneca.ep14-15.shtml", 14),  # Books 14-15 combined
    ("seneca.ep16.shtml", 16),
    ("seneca.ep17-18.shtml", 17),  # Books 17-18 combined
    ("seneca.ep19.shtml", 19),
    ("seneca.ep20.shtml", 20),
]

# Map of letter number -> book number (based on standard assignment)
LETTER_TO_BOOK = {}
book_assignments = [
    (1, range(1, 13)),      # Book I: 1-12
    (2, range(13, 22)),     # Book II: 13-21
    (3, range(22, 30)),     # Book III: 22-29
    (4, range(30, 42)),     # Book IV: 30-41
    (5, range(42, 53)),     # Book V: 42-52
    (6, range(53, 58)),     # Book VI: 53-57
    (7, range(58, 66)),     # Book VII: 58-65
    (8, range(66, 70)),     # Book VIII: 66-69
    (9, range(70, 76)),     # Book IX: 70-75 (sometimes up to 80)
    (10, range(76, 81)),    # Book X: 76-80
    (11, range(81, 84)),    # Book XI: 81-83
    (12, range(84, 87)),    # Book XII: 84-86
    (13, range(87, 92)),    # Book XIII: 87-91
    (14, range(92, 95)),    # Book XIV: 92-94
    (15, range(95, 96)),    # Book XV: 95
    (16, range(96, 101)),   # Book XVI: 96-100
    (17, range(101, 105)),  # Book XVII: 101-104
    (18, range(105, 110)),  # Book XVIII: 105-109
    (19, range(110, 118)),  # Book XIX: 110-117
    (20, range(118, 125)),  # Book XX: 118-124
]
for book, letters in book_assignments:
    for letter in letters:
        LETTER_TO_BOOK[letter] = book


def fetch_page(url):
    """Fetch a page and return its HTML content."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("latin-1")


def parse_letters_from_page(html, url):
    """Parse individual letters from a book page.

    Letters are delimited by bold headers like:
    <b>I. SENECA LUCILIO SUO SALUTEM</b>
    or
    <b>LXVI. SENECA LVCILIO SVO SALVTEM</b>
    """
    soup = BeautifulSoup(html, "html.parser")

    # Find all bold tags that contain letter headers
    letters = {}

    # Get the body text
    body = soup.find("body")
    if not body:
        return letters

    # Strategy: find all <b> tags with SENECA in them, then collect text until next <b> or end
    bold_tags = body.find_all("b")
    letter_starts = []

    for b in bold_tags:
        text = b.get_text().strip()
        # Match patterns like "I. SENECA LUCILIO SUO SALUTEM" or "CXXIV. SENECA LVCILIO SVO SALVTEM"
        # Also handle missing period: "XXI SENECA LUCILIO SUO SALUTEM"
        match = re.match(r'^([IVXLCDM]+)\.?\s+SENECA\s+L[UV]CILIO', text, re.IGNORECASE)
        if match:
            roman = match.group(1)
            num = roman_to_int(roman)
            letter_starts.append((num, b))
        else:
            # Handle split bold tags like <b>LXXVI</b>. <b>SENECA...</b>
            # Check if this is just a roman numeral and next sibling bold has SENECA
            match2 = re.match(r'^([IVXLCDM]+)$', text, re.IGNORECASE)
            if match2:
                # Check if the next text after this bold contains ". SENECA"
                next_sib = b.next_sibling
                if next_sib and isinstance(next_sib, str) and '.' in next_sib:
                    next_b = b.find_next('b')
                    if next_b and re.match(r'SENECA\s+L[UV]CILIO', next_b.get_text().strip(), re.IGNORECASE):
                        roman = match2.group(1)
                        num = roman_to_int(roman)
                        letter_starts.append((num, b))

    # For each letter, collect all <p> tags between this header and the next
    for i, (num, b_tag) in enumerate(letter_starts):
        # Collect text from paragraphs after this bold tag until the next letter header
        text_parts = []

        # Navigate through siblings after the parent <p> of this <b>
        current = b_tag.parent  # The <p> containing the <b>
        if current is None:
            continue

        current = current.find_next_sibling()

        while current:
            # Check if this element contains the next letter header
            if current.name == "p":
                b_in_p = current.find("b")
                if b_in_p:
                    b_text = b_in_p.get_text().strip()
                    if re.match(r'^[IVXLCDM]+\.?\s+SENECA\s+L[UV]CILIO', b_text, re.IGNORECASE):
                        break
                    # Also handle split bold: just a roman numeral
                    if re.match(r'^[IVXLCDM]+$', b_text, re.IGNORECASE):
                        next_b = b_in_p.find_next('b')
                        if next_b and re.match(r'SENECA\s+L[UV]CILIO', next_b.get_text().strip(), re.IGNORECASE):
                            break

                # Get text content, skip separator bars
                classes = current.get("class", [])
                if "border" in classes or "shortborder" in classes or "pagehead" in classes:
                    current = current.find_next_sibling()
                    continue

                p_text = current.get_text().strip()
                if p_text:
                    text_parts.append(p_text)

            current = current.find_next_sibling()

        if text_parts:
            full_text = "\n\n".join(text_parts)
            letters[num] = full_text

    return letters


def roman_to_int(s):
    """Convert Roman numeral string to integer."""
    roman_values = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50,
        'C': 100, 'D': 500, 'M': 1000
    }
    result = 0
    s = s.upper()
    for i in range(len(s)):
        if i + 1 < len(s) and roman_values.get(s[i], 0) < roman_values.get(s[i+1], 0):
            result -= roman_values.get(s[i], 0)
        else:
            result += roman_values.get(s[i], 0)
    return result


def get_year_approx(letter_num):
    """Approximate year for a letter."""
    if letter_num <= 40:
        return 63
    elif letter_num <= 80:
        return 64
    else:
        return 65


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Step 1: Create collection and author entries
    cur.execute("""
        INSERT OR IGNORE INTO collections (slug, author_name, title, letter_count, date_range, latin_source_url, scrape_status)
        VALUES ('seneca', 'Seneca the Younger', 'Epistulae Morales ad Lucilium', 124, '62-65 AD',
                'https://www.thelatinlibrary.com/sen.html', 'in_progress')
    """)

    cur.execute("""
        INSERT OR IGNORE INTO authors (name, name_latin, birth_year, death_year, role, location)
        VALUES ('Lucius Annaeus Seneca', 'L. Annaeus Seneca', -4, 65, 'Philosopher, statesman, tutor to Nero', 'Rome')
    """)
    cur.execute("""
        INSERT OR IGNORE INTO authors (name, name_latin, birth_year, death_year, role, location)
        VALUES ('Lucilius Junior', 'C. Lucilius Iunior', NULL, NULL, 'Procurator of Sicily, philosopher', 'Sicily')
    """)

    # Get author IDs
    cur.execute("SELECT id FROM authors WHERE name = 'Lucius Annaeus Seneca'")
    seneca_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM authors WHERE name = 'Lucilius Junior'")
    lucilius_id = cur.fetchone()[0]

    conn.commit()

    # Step 2: Scrape all books
    all_letters = {}

    for filename, book_start in BOOK_URLS:
        url = BASE_URL + filename
        print(f"Fetching {url}...")
        try:
            html = fetch_page(url)
            letters = parse_letters_from_page(html, url)
            print(f"  Found {len(letters)} letters: {sorted(letters.keys())}")

            for num, text in letters.items():
                all_letters[num] = (text, url)

            time.sleep(1)  # Be polite
        except Exception as e:
            print(f"  ERROR: {e}")

    # Special case: Letter 22 has no bold header on ep3.shtml -- it's the text before letter XXIII
    if 22 not in all_letters:
        print("\nAttempting to extract letter 22 (no header) from ep3.shtml...")
        url = BASE_URL + "seneca.ep3.shtml"
        try:
            html = fetch_page(url)
            soup = BeautifulSoup(html, "html.parser")
            body = soup.find("body")
            if body:
                # Collect all <p> text between the page header and the first letter header (XXIII)
                text_parts = []
                for p in body.find_all("p"):
                    classes = p.get("class", [])
                    if "pagehead" in classes or "border" in classes or "shortborder" in classes:
                        continue
                    b_in_p = p.find("b")
                    if b_in_p:
                        b_text = b_in_p.get_text().strip()
                        if re.match(r'^[IVXLCDM]+\.?\s+SENECA', b_text, re.IGNORECASE):
                            break
                    p_text = p.get_text().strip()
                    if p_text:
                        text_parts.append(p_text)
                if text_parts:
                    all_letters[22] = ("\n\n".join(text_parts), url)
                    print(f"  Extracted letter 22 ({len(text_parts)} paragraphs)")
        except Exception as e:
            print(f"  ERROR extracting letter 22: {e}")

    print(f"\nTotal letters scraped: {len(all_letters)}")

    # Check which letters we're missing
    expected = set(range(1, 125))
    found = set(all_letters.keys())
    missing = expected - found
    if missing:
        print(f"Missing letters: {sorted(missing)}")
    extra = found - expected
    if extra:
        print(f"Extra letters (unexpected): {sorted(extra)}")

    # Step 3: Insert letters
    inserted = 0
    for letter_num in sorted(all_letters.keys()):
        if letter_num < 1 or letter_num > 124:
            continue

        text, source_url = all_letters[letter_num]
        book = LETTER_TO_BOOK.get(letter_num, None)
        ref_id = f"seneca.ep.{letter_num}"
        year = get_year_approx(letter_num)

        try:
            cur.execute("""
                INSERT OR IGNORE INTO letters
                (collection, book, letter_number, ref_id, sender_id, recipient_id,
                 year_approx, year_min, year_max, origin_place, dest_place,
                 latin_text, source_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'seneca', book, letter_num, ref_id,
                seneca_id, lucilius_id,
                year, 62, 65,
                'Rome', 'Sicily',
                text, source_url
            ))
            if cur.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"Error inserting letter {letter_num}: {e}")

    # Update collection status
    cur.execute("""
        UPDATE collections SET scrape_status = 'complete', letter_count = ?
        WHERE slug = 'seneca'
    """, (inserted,))

    conn.commit()
    conn.close()

    print(f"\nInserted {inserted} letters into the database.")


if __name__ == "__main__":
    main()

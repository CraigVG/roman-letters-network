#!/usr/bin/env python3
"""
Scrape letter collections for four minor late antique authors:

1. Ennodius of Pavia (~297 letters, 493-521 AD)
   Source: OpenGreekAndLatin/csel-dev GitHub (CSEL 6, TEI XML)
   URL: https://raw.githubusercontent.com/OpenGreekAndLatin/csel-dev/master/data/stoa0114a/stoa008/stoa0114a.stoa008.opp-lat1.xml

2. Avitus of Vienne (~96 letters, 490-518 AD)
   Source: MGH openMGH TEI-XML (MGH Auct. ant. 6,2)
   Downloaded locally to: /tmp/avitus_mgh/bsb00000795.xml
   Live URL: https://data.mgh.de/openmgh/bsb00000795.zip

3. Ruricius of Limoges (~65 letters, 480-510 AD)
   Source: OpenGreekAndLatin/csel-dev GitHub (CSEL 21, TEI XML)
   URL: https://raw.githubusercontent.com/OpenGreekAndLatin/csel-dev/master/data/stoa0245a/stoa001/stoa0245a.stoa001.opp-lat1.xml

4. Paulinus of Nola (~51 letters, 393-431 AD)
   Source: OpenGreekAndLatin/csel-dev GitHub (CSEL 29, TEI XML)
   URL: https://raw.githubusercontent.com/OpenGreekAndLatin/csel-dev/master/data/stoa0223/stoa002/stoa0223.stoa002.opp-lat1.xml

All TEI XML sources are CC-BY or CC-BY-SA licensed from University of Leipzig.
The MGH XML is CC-BY 4.0 from Monumenta Germaniae Historica / BSB Munich.
"""

import sqlite3
import os
import re
import time
import urllib.request
import urllib.parse
import zipfile
import io

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
DELAY = 0.5  # seconds between requests


def fetch_url(url, retries=3, binary=False):
    """Fetch a URL with retries. Returns text or bytes depending on binary flag."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'RomanLettersResearch/1.0 (academic research)'
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                if binary:
                    return raw
                return raw.decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1 * (attempt + 1))
            else:
                print(f"  Failed: {url} - {e}")
                return None
    return None


def clean_tei_text(xml_fragment):
    """Strip TEI/XML tags from a fragment and clean whitespace.
    Handles word-split <w> elements by reassembling them."""
    # Remove XML processing instructions
    text = re.sub(r'<\?[^?]+\?>', '', xml_fragment)
    # Reassemble hyphenated words split across lines (TEI <w> elements)
    text = re.sub(r'<w[^>]*>([^<]*)</w>', r'\1', text)
    # Remove all other tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n[ \t]+', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def upsert_letter(conn, collection, book_num, letter_num, ref_id,
                  sender_name, recipient_name, latin_text, source_url):
    """Insert or update a letter record."""
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
    existing = cursor.fetchone()
    if existing:
        cursor.execute('''
            UPDATE letters SET latin_text = ?, source_url = ?
            WHERE ref_id = ?
        ''', (latin_text, source_url, ref_id))
        return 'updated'
    else:
        cursor.execute('''
            INSERT OR IGNORE INTO letters
                (collection, book, letter_number, ref_id, latin_text, source_url)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (collection, book_num, letter_num, ref_id, latin_text, source_url))
        return 'inserted'


def ensure_collection(conn, slug, author_name, title, letter_count, date_range,
                       latin_source_url, notes):
    """Ensure the collection metadata row exists."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO collections
            (slug, author_name, title, letter_count, date_range, latin_source_url, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (slug, author_name, title, letter_count, date_range, latin_source_url, notes))
    conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# CSEL-dev TEI XML parser (handles Ennodius, Ruricius, Paulinus)
# ─────────────────────────────────────────────────────────────────────────────

def parse_cseldev_xml(xml_text, collection_slug):
    """
    Parse a CSEL-dev TEI XML file into a list of letter dicts.
    These files use:
      <div n="N" subtype="book" type="textpart">
        <div n="M" subtype="letter" type="textpart">
          <ab><title>HEADER</title></ab>
          <p>...</p>
        </div>
      </div>

    Some (Paulinus) have only letter divs with section sub-divs.
    Returns list of dicts: {book, letter_num, header, text}
    """
    letters = []

    # Detect if there are book-level divs
    has_books = bool(re.search(r'subtype=["\']book["\']', xml_text))

    if has_books:
        # Split by book
        book_parts = re.split(r'<div n="(\d+)" subtype="book" type="textpart">', xml_text)
        # book_parts = [preamble, book_n1, book_content1, book_n2, book_content2, ...]
        for i in range(1, len(book_parts), 2):
            book_num = int(book_parts[i])
            book_content = book_parts[i + 1] if i + 1 < len(book_parts) else ''
            _parse_letters_from_block(book_content, book_num, letters)
    else:
        # No book level — all letters at top level (Paulinus structure)
        _parse_letters_from_block(xml_text, 1, letters)

    return letters


def _parse_letters_from_block(block, book_num, letters):
    """Extract individual letter divs from a block of XML."""
    letter_parts = re.split(r'<div n="(\d+)" subtype="letter" type="textpart">', block)
    for i in range(1, len(letter_parts), 2):
        letter_num = int(letter_parts[i])
        letter_content = letter_parts[i + 1] if i + 1 < len(letter_parts) else ''

        # Extract header from <title> or <ab> containing sender/recipient
        header_match = re.search(r'<title[^>]*>(.*?)</title>', letter_content, re.DOTALL)
        if header_match:
            header = clean_tei_text(header_match.group(1))
        else:
            ab_match = re.search(r'<ab[^>]*>(.*?)</ab>', letter_content, re.DOTALL)
            header = clean_tei_text(ab_match.group(1)) if ab_match else ''

        # Get the text (everything, stripped of XML)
        text = clean_tei_text(letter_content)

        if len(text) > 30:
            letters.append({
                'book': book_num,
                'letter_num': letter_num,
                'header': header.strip(),
                'text': text,
            })


# ─────────────────────────────────────────────────────────────────────────────
# MGH TEI XML parser (Avitus of Vienne)
# ─────────────────────────────────────────────────────────────────────────────

def parse_mgh_avitus_xml(xml_text):
    """
    Parse the MGH Avitus XML (bsb00000795.xml).

    The epistulae section starts with 'EPISTVLARVM AD DIVERSOS LIBRI TRES'
    and contains three books in three consecutive <div type="part"> blocks.
    Within each book, individual letters are separated by 'Avitus episcopus X.'
    or 'X ... Avito.' header lines (for letters received).

    Returns list of dicts: {book, letter_num, header, text}
    """
    # Find the epistulae section
    ep_start = xml_text.find('EPISTVLARVM AD DIVERSOS')
    if ep_start < 0:
        print("  ERROR: Could not find 'EPISTVLARVM AD DIVERSOS' in Avitus XML")
        return []

    # Split the epistulae section into <div type="part"> blocks.
    # Parts 1, 2, 3 are the three books; parts 4+ are homiliae/sermones.
    ep_section = xml_text[ep_start:]
    parts = re.split(r'<div type="part">', ep_section)
    # parts[0] = section header, parts[1..3] = three books, parts[4+] = homiliae

    # Letter header detection pattern for Avitus:
    # 'Avitus episcopus/Viennensis X.' OR 'X ... Avito.'
    # Preceded by a newline (or start of cleaned text)
    HEADER_PAT = re.compile(
        r'(?:^|\n)'
        r'(?:'
        r'\[?Avitus\s+\w+\s+[\w\[\]]+[\w\s\[\],]*\.'  # Avitus episcopus/Viennensis X.
        r'|'
        r'\[?[A-Z][a-z]+(?:\s+[a-zA-Z]+)+\s+Avito[\w]*\.'  # X ... Avito.
        r'|'
        r'[A-Z][a-z]+\s+[A-Z][a-z]+\s+viro\s+illustr[\w]+\.'  # X Y viro illustri.
        r'|'
        r'sede\s+dignissimo[^\n]+Avitus\.'  # Hormisdas → Avitus
        r')'
    )

    letters = []
    for book_num in range(1, 4):
        if book_num >= len(parts):
            break
        book_xml = parts[book_num]

        # Strip XML markup to plain text
        plain = re.sub(r'<w[^>]*>([^<]*)</w>', r'\1', book_xml)
        plain = re.sub(r'<[^>]+>', '', plain)
        plain = re.sub(r'[ \t]+', ' ', plain)
        plain = re.sub(r'\n{3,}', '\n\n', plain)
        plain = plain.strip()

        # Find all letter header positions
        header_matches = list(HEADER_PAT.finditer(plain))

        if not header_matches:
            # Fallback: treat whole book as one letter
            letters.append({'book': book_num, 'letter_num': 1,
                             'header': '', 'text': plain})
            continue

        for i, match in enumerate(header_matches):
            start = match.start()
            end = header_matches[i + 1].start() if i + 1 < len(header_matches) else len(plain)
            letter_text = plain[start:end].strip()

            if len(letter_text) < 50:
                continue

            # Header = first meaningful line
            first_line = letter_text.split('\n')[0].strip()
            second_line = letter_text.split('\n')[1].strip() if len(letter_text.split('\n')) > 1 else ''
            header = (first_line + ' ' + second_line).strip()[:200]

            letters.append({
                'book': book_num,
                'letter_num': i + 1,
                'header': header,
                'text': letter_text,
            })

    return letters


# ─────────────────────────────────────────────────────────────────────────────
# Individual scraper functions
# ─────────────────────────────────────────────────────────────────────────────

def scrape_ennodius(conn):
    """
    Ennodius of Pavia (493-521 AD) — CSEL 6 via OpenGreekAndLatin/csel-dev.
    12 books, ~297 letters total.
    """
    SLUG = 'ennodius_pavia'
    SOURCE_URL = ('https://raw.githubusercontent.com/OpenGreekAndLatin/csel-dev'
                  '/master/data/stoa0114a/stoa008/stoa0114a.stoa008.opp-lat1.xml')

    print(f"\n{'='*60}")
    print(f"Scraping Ennodius of Pavia...")
    print(f"Source: {SOURCE_URL}")

    ensure_collection(conn, SLUG,
                      'Ennodius of Pavia',
                      'Epistulae (XII Libri)',
                      297, '493-521 AD',
                      SOURCE_URL,
                      'CSEL 6 (Hartel 1882). TEI XML via OpenGreekAndLatin/csel-dev (CC-BY-SA 4.0).')

    xml_text = fetch_url(SOURCE_URL)
    if not xml_text:
        print(f"  ERROR: Could not fetch Ennodius XML")
        return 0
    time.sleep(DELAY)

    letters = parse_cseldev_xml(xml_text, SLUG)
    print(f"  Parsed {len(letters)} letters from XML")

    inserted = updated = 0
    for letter in letters:
        ref_id = f"ennodius.ep.{letter['book']}.{letter['letter_num']}"
        result = upsert_letter(
            conn, SLUG,
            letter['book'], letter['letter_num'],
            ref_id,
            'Ennodius of Pavia', '',
            letter['text'], SOURCE_URL
        )
        if result == 'inserted':
            inserted += 1
        else:
            updated += 1

        if (inserted + updated) % 50 == 0:
            conn.commit()
            print(f"  Progress: {inserted + updated} letters processed...")

    conn.commit()
    print(f"  Done: {inserted} inserted, {updated} updated")
    return inserted + updated


def scrape_avitus(conn):
    """
    Avitus of Vienne (490-518 AD) — MGH Auct. ant. 6,2 (Peiper 1883).
    TEI-XML from openMGH (CC-BY 4.0).
    Downloaded ZIP: https://data.mgh.de/openmgh/bsb00000795.zip
    """
    SLUG = 'avitus_vienne'
    ZIP_URL = 'https://data.mgh.de/openmgh/bsb00000795.zip'
    LOCAL_XML = '/tmp/avitus_mgh/bsb00000795.xml'

    print(f"\n{'='*60}")
    print(f"Scraping Avitus of Vienne...")
    print(f"Source: {ZIP_URL}")

    ensure_collection(conn, SLUG,
                      'Avitus of Vienne',
                      'Epistularum ad Diversos Libri Tres',
                      96, '490-518 AD',
                      ZIP_URL,
                      'MGH Auct. ant. 6,2 (Peiper 1883). TEI-XML via openMGH (CC-BY 4.0).')

    # Try local file first (already downloaded), else fetch ZIP
    xml_text = None
    if os.path.exists(LOCAL_XML):
        print(f"  Using local file: {LOCAL_XML}")
        with open(LOCAL_XML, 'r', encoding='utf-8') as f:
            xml_text = f.read()
    else:
        print(f"  Downloading ZIP from {ZIP_URL}...")
        zip_data = fetch_url(ZIP_URL, binary=True)
        time.sleep(DELAY)
        if not zip_data:
            print(f"  ERROR: Could not fetch Avitus ZIP")
            return 0
        try:
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                xml_filename = [n for n in zf.namelist() if n.endswith('.xml')][0]
                xml_text = zf.read(xml_filename).decode('utf-8', errors='replace')
        except Exception as e:
            print(f"  ERROR: Could not unzip Avitus: {e}")
            return 0

    letters = parse_mgh_avitus_xml(xml_text)
    print(f"  Parsed {len(letters)} letters from XML")

    inserted = updated = 0
    for letter in letters:
        ref_id = f"avitus.ep.{letter['book']}.{letter['letter_num']}"
        result = upsert_letter(
            conn, SLUG,
            letter['book'], letter['letter_num'],
            ref_id,
            'Avitus of Vienne', '',
            letter['text'], ZIP_URL
        )
        if result == 'inserted':
            inserted += 1
        else:
            updated += 1

        if (inserted + updated) % 20 == 0:
            conn.commit()
            print(f"  Progress: {inserted + updated} letters processed...")

    conn.commit()
    print(f"  Done: {inserted} inserted, {updated} updated")
    return inserted + updated


def scrape_ruricius(conn):
    """
    Ruricius of Limoges (480-510 AD) — CSEL 21 via OpenGreekAndLatin/csel-dev.
    2 books + letters to Ruricius, ~65 letters total.
    """
    SLUG = 'ruricius_limoges'
    SOURCE_URL = ('https://raw.githubusercontent.com/OpenGreekAndLatin/csel-dev'
                  '/master/data/stoa0245a/stoa001/stoa0245a.stoa001.opp-lat1.xml')

    print(f"\n{'='*60}")
    print(f"Scraping Ruricius of Limoges...")
    print(f"Source: {SOURCE_URL}")

    ensure_collection(conn, SLUG,
                      'Ruricius of Limoges',
                      'Epistularum Libri Duo',
                      65, '480-510 AD',
                      SOURCE_URL,
                      'CSEL 21 (Engelbrecht 1891). TEI XML via OpenGreekAndLatin/csel-dev (CC-BY-SA 4.0). '
                      'Includes "Epistulae ad Ruricium Scriptae" (letters to Ruricius) as Book 3.')

    xml_text = fetch_url(SOURCE_URL)
    if not xml_text:
        print(f"  ERROR: Could not fetch Ruricius XML")
        return 0
    time.sleep(DELAY)

    letters = parse_cseldev_xml(xml_text, SLUG)
    print(f"  Parsed {len(letters)} letters from XML")

    inserted = updated = 0
    for letter in letters:
        ref_id = f"ruricius.ep.{letter['book']}.{letter['letter_num']}"
        result = upsert_letter(
            conn, SLUG,
            letter['book'], letter['letter_num'],
            ref_id,
            'Ruricius of Limoges' if letter['book'] <= 2 else '',
            '',
            letter['text'], SOURCE_URL
        )
        if result == 'inserted':
            inserted += 1
        else:
            updated += 1

        if (inserted + updated) % 20 == 0:
            conn.commit()
            print(f"  Progress: {inserted + updated} letters processed...")

    conn.commit()
    print(f"  Done: {inserted} inserted, {updated} updated")
    return inserted + updated


def scrape_paulinus_nola(conn):
    """
    Paulinus of Nola (393-431 AD) — CSEL 29 via OpenGreekAndLatin/csel-dev.
    51 letters total (some with many sections).
    """
    SLUG = 'paulinus_nola'
    SOURCE_URL = ('https://raw.githubusercontent.com/OpenGreekAndLatin/csel-dev'
                  '/master/data/stoa0223/stoa002/stoa0223.stoa002.opp-lat1.xml')

    print(f"\n{'='*60}")
    print(f"Scraping Paulinus of Nola...")
    print(f"Source: {SOURCE_URL}")

    ensure_collection(conn, SLUG,
                      'Paulinus of Nola',
                      'Epistulae',
                      51, '393-431 AD',
                      SOURCE_URL,
                      'CSEL 29 (Hartel 1894). TEI XML via OpenGreekAndLatin/csel-dev (CC-BY-SA 4.0). '
                      'English translation available: Walsh (1966), Paulinus of Nola: Letters, '
                      'Newman Press (2 vols), Internet Archive: archive.org/details/letters-of-st.-paulinus-of-nola')

    xml_text = fetch_url(SOURCE_URL)
    if not xml_text:
        print(f"  ERROR: Could not fetch Paulinus XML")
        return 0
    time.sleep(DELAY)

    letters = parse_cseldev_xml(xml_text, SLUG)
    print(f"  Parsed {len(letters)} letters from XML")

    inserted = updated = 0
    for letter in letters:
        # Paulinus has no books in CSEL-dev XML — all letters at book=1
        ref_id = f"paulinus.ep.{letter['letter_num']}"
        result = upsert_letter(
            conn, SLUG,
            None, letter['letter_num'],
            ref_id,
            'Paulinus of Nola', '',
            letter['text'], SOURCE_URL
        )
        if result == 'inserted':
            inserted += 1
        else:
            updated += 1

        if (inserted + updated) % 20 == 0:
            conn.commit()
            print(f"  Progress: {inserted + updated} letters processed...")

    conn.commit()
    print(f"  Done: {inserted} inserted, {updated} updated")
    return inserted + updated


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT collection, COUNT(*) as total,
               SUM(CASE WHEN latin_text IS NOT NULL THEN 1 ELSE 0 END) as latin,
               SUM(CASE WHEN english_text IS NOT NULL THEN 1 ELSE 0 END) as english
        FROM letters
        WHERE collection IN ('ennodius_pavia', 'avitus_vienne', 'ruricius_limoges', 'paulinus_nola')
        GROUP BY collection ORDER BY collection
    ''')
    rows = cursor.fetchall()
    print(f"\n{'Collection':<25} {'Total':>6} {'Latin':>6} {'English':>8}")
    print('-' * 50)
    for row in rows:
        print(f"{row[0]:<25} {row[1]:>6} {row[2]:>6} {row[3]:>8}")


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    total = 0

    total += scrape_ennodius(conn)
    time.sleep(DELAY)

    total += scrape_avitus(conn)
    time.sleep(DELAY)

    total += scrape_ruricius(conn)
    time.sleep(DELAY)

    total += scrape_paulinus_nola(conn)

    print(f"\n{'='*60}")
    print(f"Total letters processed across all 4 collections: {total}")
    print_summary(conn)
    conn.close()


if __name__ == '__main__':
    main()

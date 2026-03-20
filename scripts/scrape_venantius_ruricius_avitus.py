#!/usr/bin/env python3
"""
Scrape three collections:

1. Venantius Fortunatus verse epistles (~103 letters, 570-600 AD)
   Source: MGH AA 4.1 (bsb00000790) — openMGH CC-BY 4.0
   Collection slug: venantius_fortunatus

2. Ruricius of Limoges Book 3 — 'Epistulae ad Ruricium Scriptae' (8 letters)
   Source: CSEL 21 (same XML as before, fixes parser to handle n="letters" book)
   Collection slug: ruricius_limoges (update existing)

3. Avitus of Vienne — fix to get 32 letters in Book 3 (was 30, now 72 total)
   Source: MGH AA 6.2 (bsb00000795)
   Collection slug: avitus_vienne (update existing)
"""

import sqlite3
import os
import re
import time
import urllib.request
import io
import zipfile

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
DELAY = 0.5


# ─────────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────────

def fetch_url(url, retries=3, binary=False):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'RomanLettersResearch/1.0 (academic research)'
            })
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
                return raw if binary else raw.decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
            else:
                print(f"  Failed: {url} — {e}")
                return None
    return None


def clean_xml_text(xml_fragment):
    """Strip XML/TEI tags and normalize whitespace."""
    text = re.sub(r'<w[^>]*>([^<]*)</w>', r'\1', xml_fragment)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n[ \t]+', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def upsert_letter(conn, collection, book_num, letter_num, ref_id,
                  latin_text, source_url):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            'UPDATE letters SET latin_text = ?, source_url = ? WHERE ref_id = ?',
            (latin_text, source_url, ref_id)
        )
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
    conn.execute('''
        INSERT OR IGNORE INTO collections
            (slug, author_name, title, letter_count, date_range, latin_source_url, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (slug, author_name, title, letter_count, date_range, latin_source_url, notes))
    conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Venantius Fortunatus — MGH AA 4.1
# ─────────────────────────────────────────────────────────────────────────────

def scrape_venantius_fortunatus(conn):
    """
    Venantius Fortunatus (ca. 530–600 AD), bishop-poet of Poitiers.
    His Carmina (11 books, ~263 poems) include ~100+ verse epistles addressed
    to bishops, kings, and friends. Extracts poems with explicit addressees
    ('Ad X' or 'Domino X' in the poem title).

    Source: MGH Auct. ant. 4,1 (Leo 1881) — openMGH CC-BY 4.0
    ZIP: https://data.mgh.de/openmgh/bsb00000790.zip
    """
    SLUG = 'venantius_fortunatus'
    ZIP_URL = 'https://data.mgh.de/openmgh/bsb00000790.zip'
    LOCAL_XML = '/tmp/fortunatus_mgh.xml'

    print(f"\n{'='*60}")
    print("Scraping Venantius Fortunatus (MGH AA 4.1)...")

    ensure_collection(conn, SLUG,
                      'Venantius Fortunatus',
                      'Carminum Libri XI (verse epistles)',
                      103, '570-600 AD',
                      ZIP_URL,
                      'MGH Auct. ant. 4,1 (Leo 1881). openMGH CC-BY 4.0. '
                      'Verse epistles extracted from Carmina Books I-XI: poems '
                      'with explicit personal addressees ("Ad X" or "Domino X" '
                      'in the poem title). Poet-bishop of Poitiers, correspondent '
                      'of Gregory of Tours, Radegund, and the Merovingian court.')

    # Load XML
    xml_text = None
    if os.path.exists(LOCAL_XML):
        print(f"  Using cached XML: {LOCAL_XML}")
        with open(LOCAL_XML, 'r', encoding='utf-8') as f:
            xml_text = f.read()
    else:
        print(f"  Downloading ZIP from {ZIP_URL}...")
        zip_data = fetch_url(ZIP_URL, binary=True)
        if not zip_data:
            print("  ERROR: Could not fetch ZIP")
            return 0
        try:
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                xml_files = [n for n in zf.namelist() if n.endswith('.xml')]
                xml_text = zf.read(xml_files[0]).decode('utf-8', errors='replace')
        except Exception as e:
            print(f"  ERROR unzipping: {e}")
            return 0
        with open(LOCAL_XML, 'w', encoding='utf-8') as f:
            f.write(xml_text)

    # Parse verse epistles
    poems = _parse_fortunatus_epistles(xml_text)
    print(f"  Found {len(poems)} verse epistles")

    inserted = updated = 0
    for poem in poems:
        ref_id = f"fortunatus.carm.{poem['book']}.{poem['poem_num']}"
        result = upsert_letter(
            conn, SLUG,
            poem['book'], poem['poem_num'],
            ref_id,
            poem['text'], ZIP_URL
        )
        if result == 'inserted':
            inserted += 1
        else:
            updated += 1

        if (inserted + updated) % 20 == 0:
            conn.commit()

    conn.commit()
    print(f"  Done: {inserted} inserted, {updated} updated")
    return inserted + updated


def _parse_fortunatus_epistles(xml_text):
    """
    Extract verse epistles from Fortunatus Carmina.
    Returns list of dicts: {book, poem_num, header, text}

    The MGH XML structure:
      <div type="work" n="Ven. Fort. carm.">
        <div type="part">  ← preamble (skip)
        <div type="part">  ← preamble (skip)
        <div type="part">  ← Book I
          <div type="section">  ← individual poem
            <ab>Title of poem</ab>
            <lb/> text lines...
          </div>
        </div>
        <div type="part">  ← Book II
        ...
        <div type="part">  ← Book XI (index 12)
        <div type="part">  ← Appendix carminum (skip)
        ...

    We extract Books I–XI (part indices 2–12) and filter for epistles.
    """
    part_matches = list(re.finditer(r'<div type="part">', xml_text))
    poems = []

    for book_idx, pm in enumerate(part_matches):
        # Books I–XI are at part indices 2–12 (0-indexed)
        if book_idx < 2:
            continue
        if book_idx > 12:
            break

        book_num = book_idx - 1  # 1-indexed

        next_start = part_matches[book_idx + 1].start() if book_idx + 1 < len(part_matches) else len(xml_text)
        book_xml = xml_text[pm.start():next_start]

        sections = list(re.finditer(r'<div type="section">', book_xml))

        for sec_idx, sm in enumerate(sections):
            next_sec = sections[sec_idx + 1].start() if sec_idx + 1 < len(sections) else len(book_xml)
            sec_xml = book_xml[sm.start():next_sec]

            # Get the <ab> header (poem title)
            ab_match = re.search(r'<ab[^>]*>(.*?)</ab>', sec_xml, re.DOTALL)
            header = ''
            if ab_match:
                header = clean_xml_text(ab_match.group(1))

            # Filter: only keep poems explicitly addressed to a person
            # Patterns: "I Ad Vitalem episcopum..." or "DOMINO SANCTO..." or
            # "Ad eundem" (same recipient) or "Item ad eundem"
            is_epistle = bool(
                re.match(r'^[IVXLC]+\.?\s+[Aa]d\s+', header) or
                re.match(r'^[IVXLC]+\.?\s+[Ii]tem\s+[Aa]d\s+', header) or
                re.match(r'^[IVXLC]+\.?\s+[Dd]omino\s+', header) or
                re.search(r'^DOMINO\s+SANCTO', header) or
                re.match(r'^[IVXLC]+\.?\s+[Cc]arissimo', header)
            )

            if not is_epistle:
                continue

            # Get full text
            text = clean_xml_text(sec_xml)
            if len(text) < 30:
                continue

            # Poem number within book = section index + 1
            poem_num = sec_idx + 1

            poems.append({
                'book': book_num,
                'poem_num': poem_num,
                'header': header,
                'text': text,
            })

    return poems


# ─────────────────────────────────────────────────────────────────────────────
# 2. Ruricius Book 3 — Epistulae ad Ruricium Scriptae
# ─────────────────────────────────────────────────────────────────────────────

def scrape_ruricius_book3(conn):
    """
    Add the 'Epistulae ad Ruricium Scriptae' (letters TO Ruricius) from CSEL 21.
    These are stored in the XML as <div n="letters" subtype="book" type="textpart">
    which the original parser missed (it only handled numeric book IDs).
    Adds them as book=3 with ref_ids ruricius.ep.3.N.
    """
    SLUG = 'ruricius_limoges'
    SOURCE_URL = ('https://raw.githubusercontent.com/OpenGreekAndLatin/csel-dev'
                  '/master/data/stoa0245a/stoa001/stoa0245a.stoa001.opp-lat1.xml')

    print(f"\n{'='*60}")
    print("Scraping Ruricius Book 3 (Epistulae ad Ruricium Scriptae)...")

    xml_text = fetch_url(SOURCE_URL)
    if not xml_text:
        print("  ERROR: Could not fetch Ruricius XML")
        return 0
    time.sleep(DELAY)

    # Find the "letters" book: <div n="letters" subtype="book" type="textpart">
    letters_book_match = re.search(
        r'<div n="letters" subtype="book" type="textpart">(.*?)(?=</body>|$)',
        xml_text, re.DOTALL
    )
    if not letters_book_match:
        print("  ERROR: Could not find 'letters' book in XML")
        return 0

    letters_content = letters_book_match.group(1)

    # Extract individual letters from this book
    letter_parts = re.split(r'<div n="(\d+)" subtype="letter" type="textpart">', letters_content)
    # Deduplicate by letter number (some appear twice due to XML nesting)
    seen_nums = set()
    inserted = updated = 0

    for i in range(1, len(letter_parts), 2):
        letter_num = int(letter_parts[i])
        if letter_num in seen_nums:
            continue
        seen_nums.add(letter_num)

        letter_content = letter_parts[i + 1] if i + 1 < len(letter_parts) else ''
        text = clean_xml_text(letter_content)

        if len(text) < 30:
            continue

        ref_id = f"ruricius.ep.3.{letter_num}"
        result = upsert_letter(
            conn, SLUG,
            3, letter_num,
            ref_id,
            text, SOURCE_URL
        )
        if result == 'inserted':
            inserted += 1
            print(f"  Inserted: {ref_id} ({len(text)} chars)")
        else:
            updated += 1

    conn.commit()
    print(f"  Done: {inserted} inserted, {updated} updated (Book 3 'Epistulae ad Ruricium')")
    return inserted + updated


# ─────────────────────────────────────────────────────────────────────────────
# 3. Avitus of Vienne — fix Book 3 to get all 32 letters
# ─────────────────────────────────────────────────────────────────────────────

def fix_avitus_book3(conn):
    """
    Re-scrape Avitus Book 3 to capture all 32 letters (was 30).
    The original header detection missed bracketed headers like [Avitus episcopus X].
    Updates existing letters (upsert) and inserts any missing ones.
    """
    SLUG = 'avitus_vienne'
    ZIP_URL = 'https://data.mgh.de/openmgh/bsb00000795.zip'
    LOCAL_XML = '/tmp/avitus_mgh.xml'

    print(f"\n{'='*60}")
    print("Fixing Avitus of Vienne Book 3 (adding 2 missing letters)...")

    # Load XML
    xml_text = None
    if os.path.exists(LOCAL_XML):
        with open(LOCAL_XML, 'r', encoding='utf-8') as f:
            xml_text = f.read()
    else:
        print(f"  Downloading from {ZIP_URL}...")
        zip_data = fetch_url(ZIP_URL, binary=True)
        if not zip_data:
            print("  ERROR: Could not fetch ZIP")
            return 0
        try:
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                xml_text = zf.read('bsb00000795.xml').decode('utf-8', errors='replace')
        except Exception as e:
            print(f"  ERROR: {e}")
            return 0
        with open(LOCAL_XML, 'w', encoding='utf-8') as f:
            f.write(xml_text)

    # Find epistulae section
    ep_start = xml_text.find('EPISTVLARVM AD DIVERSOS')
    if ep_start < 0:
        print("  ERROR: Could not find epistulae section")
        return 0

    ep_section = xml_text[ep_start:]
    parts = re.split(r'<div type="part">', ep_section)

    # Enhanced header pattern that includes bracketed headers
    HEADER_PAT = re.compile(
        r'(?:^|\n)'
        r'(?:'
        r'\[?Avitus\s+\w+\s+[\w\[\]]+[\w\s\[\],]*\.'  # Avitus episcopus X.
        r'|'
        r'\[?[A-Z][a-z]+(?:\s+[a-zA-Z]+)+\s+Avito[\w]*\.'  # X ... Avito.
        r'|'
        r'[A-Z][a-z]+\s+[A-Z][a-z]+\s+viro\s+illustr[\w]+'  # X Y viro illustri.
        r'|'
        r'sede\s+dignissimo[^\n]+Avitus\.'  # Hormisdas → Avitus
        r'|'
        r'\[[A-Z][a-z]+\s+\w+\s+\w+\],'  # [Avitus episcopus X],
        r')'
    )

    total_inserted = 0
    total_updated = 0

    for book_num in range(1, 4):  # Books 1-3
        if book_num >= len(parts):
            break

        book_xml = parts[book_num]
        plain = re.sub(r'<w[^>]*>([^<]*)</w>', r'\1', book_xml)
        plain = re.sub(r'<[^>]+>', '', plain)
        plain = re.sub(r'[ \t]+', ' ', plain)
        plain = re.sub(r'\n{3,}', '\n\n', plain)
        plain = plain.strip()

        header_matches = list(HEADER_PAT.finditer(plain))
        print(f"  Book {book_num}: {len(header_matches)} letters found")

        if not header_matches:
            continue

        for i, match in enumerate(header_matches):
            start = match.start()
            end = header_matches[i + 1].start() if i + 1 < len(header_matches) else len(plain)
            letter_text = plain[start:end].strip()

            if len(letter_text) < 50:
                continue

            first_line = letter_text.split('\n')[0].strip()
            second_line = (letter_text.split('\n')[1].strip()
                           if len(letter_text.split('\n')) > 1 else '')
            header = (first_line + ' ' + second_line).strip()[:200]

            ref_id = f"avitus.ep.{book_num}.{i + 1}"
            result = upsert_letter(
                conn, SLUG,
                book_num, i + 1,
                ref_id,
                letter_text, ZIP_URL
            )
            if result == 'inserted':
                total_inserted += 1
            else:
                total_updated += 1

        conn.commit()

    print(f"  Done: {total_inserted} inserted, {total_updated} updated")
    return total_inserted + total_updated


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(conn):
    cursor = conn.cursor()
    collections = ['venantius_fortunatus', 'ruricius_limoges', 'avitus_vienne']
    cursor.execute(f'''
        SELECT collection, COUNT(*) as total,
               SUM(CASE WHEN latin_text IS NOT NULL AND latin_text != "" THEN 1 ELSE 0 END) as has_latin,
               SUM(CASE WHEN modern_english IS NOT NULL THEN 1 ELSE 0 END) as has_modern
        FROM letters
        WHERE collection IN ({",".join("?"*len(collections))})
        GROUP BY collection ORDER BY collection
    ''', collections)
    rows = cursor.fetchall()
    print(f"\n{'Collection':<30} {'Total':>6} {'Latin':>6} {'ModEng':>7}")
    print('-' * 55)
    for row in rows:
        print(f"{row[0]:<30} {row[1]:>6} {row[2]:>6} {row[3]:>7}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)

    n1 = scrape_venantius_fortunatus(conn)
    time.sleep(DELAY)

    n2 = scrape_ruricius_book3(conn)
    time.sleep(DELAY)

    n3 = fix_avitus_book3(conn)

    print(f"\n{'='*60}")
    print(f"Total letters processed: {n1 + n2 + n3}")
    print(f"  Venantius Fortunatus: {n1}")
    print(f"  Ruricius Book 3:      {n2}")
    print(f"  Avitus fix:           {n3}")
    print_summary(conn)
    conn.close()


if __name__ == '__main__':
    main()

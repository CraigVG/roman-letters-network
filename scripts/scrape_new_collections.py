#!/usr/bin/env python3
"""
Scrape new letter collections to push DB from ~2,300 to 3,000+.

New collections:
1. Cyprian of Carthage (248-258 AD) - 82 letters from New Advent
   https://www.newadvent.org/fathers/050601.htm ... 050682.htm

2. Theodoret of Cyrrhus (5th century) - 181 letters from New Advent
   https://www.newadvent.org/fathers/2707001.htm ... 2707181.htm

3. Sidonius Apollinaris (455-480 AD) - complete 9 books from Latin Library
   http://thelatinlibrary.com/sidonius1.html ... sidonius9.html

Also complete existing partial collections from New Advent:
4. Augustine (have 161/308)
5. Ambrose (have 28/91)
6. Jerome (have 131/154)
7. Leo the Great (have 73/173)
"""

import sqlite3
import os
import re
import time
import urllib.request

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
DELAY = 0.5  # seconds between requests


# ─────────────────────────────────────────────────────────────────────────────
# Utility functions
# ─────────────────────────────────────────────────────────────────────────────

def fetch_url(url, retries=3):
    """Fetch URL content with retries."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'RomanLettersResearch/1.0 (academic research project)'
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1.0 * (attempt + 1))
            else:
                print(f"  Failed: {url} - {e}")
                return None
    return None


def extract_newadvent_text(html):
    """
    Extract the letter text from a New Advent fathers page.
    The main content is inside <div id="springfield2">
    Strip all HTML tags and clean up whitespace.
    """
    # Find the main content div
    match = re.search(r'<div id="springfield2">(.*?)(?:<div class="pub">|<div id="ogdenville">)',
                      html, re.DOTALL)
    if match:
        content = match.group(1)
    else:
        # Fallback: use body content after navigation
        body_match = re.search(r'<div id="mi5">.*?</div>(.*?)(?:<div class="pub">|<div id="ogdenville">)',
                               html, re.DOTALL)
        content = body_match.group(1) if body_match else html

    # Remove script/style blocks
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)

    # Convert paragraph breaks to newlines
    content = re.sub(r'</p>', '\n\n', content)
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'<h[1-6][^>]*>', '\n\n', content)
    content = re.sub(r'</h[1-6]>', '\n', content)

    # Remove all remaining tags
    content = re.sub(r'<[^>]+>', '', content)

    # Decode HTML entities
    content = content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    content = content.replace('&nbsp;', ' ').replace('&#151;', '—').replace('&#146;', "'")
    content = content.replace('&mdash;', '—').replace('&ldquo;', '"').replace('&rdquo;', '"')
    content = content.replace('&lsquo;', "'").replace('&rsquo;', "'").replace('&aelig;', 'æ')
    content = content.replace('&#230;', 'æ').replace('&oelig;', 'œ').replace('&eacute;', 'é')

    # Clean whitespace
    content = re.sub(r'[ \t]+', ' ', content)
    content = re.sub(r'\n[ \t]+', '\n', content)
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content.strip()


def parse_newadvent_header(text):
    """Extract sender/recipient/subject from letter text."""
    info = {'recipient': None, 'subject': None}

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    for line in lines[:10]:
        # "To NAME." or "To NAME," pattern
        to_match = re.match(r'^To\s+([A-Z][^\.]+?)[\.,]?\s*$', line, re.IGNORECASE)
        if to_match:
            info['recipient'] = to_match.group(1).strip()
            break

        # "To NAME the TITLE" or "To the Bishop of NAME"
        to_match2 = re.match(r'^To\s+(.{3,60}?)\.\s*$', line)
        if to_match2:
            info['recipient'] = to_match2.group(1).strip()
            break

    # Build subject from first substantive paragraph
    for line in lines[3:20]:
        if len(line) > 60 and not line.startswith('To ') and not re.match(r'^Letter\s+\w+', line):
            info['subject'] = line[:200]
            break

    return info


def ensure_author(conn, name, role=None, notes=None):
    """Ensure an author exists in the authors table, return their id."""
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM authors WHERE name = ?', (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(
        'INSERT INTO authors (name, role, notes) VALUES (?, ?, ?)',
        (name, role, notes)
    )
    conn.commit()
    return cursor.lastrowid


def ensure_collection(conn, slug, author_name, title, letter_count, date_range,
                      english_source_url, notes):
    """Ensure the collection metadata row exists."""
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM collections WHERE slug = ?', (slug,))
    if cursor.fetchone():
        return
    cursor.execute('''
        INSERT INTO collections
            (slug, author_name, title, letter_count, date_range, english_source_url, notes, scrape_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'in_progress')
    ''', (slug, author_name, title, letter_count, date_range, english_source_url, notes))
    conn.commit()


def mark_collection_complete(conn, slug):
    cursor = conn.cursor()
    cursor.execute("UPDATE collections SET scrape_status = 'complete' WHERE slug = ?", (slug,))
    conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Cyprian of Carthage (New Advent)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_cyprian(conn):
    """
    82 letters from New Advent.
    URL pattern: https://www.newadvent.org/fathers/050601.htm ... 050682.htm
    """
    SLUG = 'cyprian_carthage'
    BASE_URL = 'https://www.newadvent.org/fathers/0506'
    INDEX_URL = 'https://www.newadvent.org/fathers/0506.htm'
    MAX_LETTERS = 82

    print(f"\n{'='*60}")
    print(f"Scraping Cyprian of Carthage (Letters)...")

    ensure_collection(conn, SLUG,
                      'Cyprian of Carthage',
                      'The Epistles of Cyprian',
                      MAX_LETTERS, '248-258 AD',
                      INDEX_URL,
                      'Translated by Robert Ernest Wallis. From Ante-Nicene Fathers, Vol. 5. '
                      'Public domain via New Advent.')

    sender_id = ensure_author(conn, 'Cyprian of Carthage', 'bishop',
                              'Bishop of Carthage, martyred 258 AD')

    cursor = conn.cursor()

    # Find all letter links from the index
    print(f"  Fetching index from {INDEX_URL}...")
    index_html = fetch_url(INDEX_URL)
    if not index_html:
        print("  ERROR: Could not fetch Cyprian index")
        return 0

    # Find letter numbers from index
    nums = sorted(set(int(m) for m in re.findall(r'0506(\d{2})\.htm', index_html)))
    if not nums:
        nums = list(range(1, MAX_LETTERS + 1))
    print(f"  Found {len(nums)} letter links in index")

    inserted = 0
    skipped = 0
    failed = 0

    for num in nums:
        ref_id = f"cyprian.ep.{num}"

        # Skip if already have it with English text
        cursor.execute('SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL', (ref_id,))
        if cursor.fetchone():
            skipped += 1
            continue

        url = f"{BASE_URL}{num:02d}.htm"
        time.sleep(DELAY)

        html = fetch_url(url)
        if not html:
            failed += 1
            continue

        # Verify it's actually a Cyprian letter
        if 'Cyprian' not in html and 'cyprian' not in html.lower():
            failed += 1
            continue

        text = extract_newadvent_text(html)
        if len(text) < 50:
            failed += 1
            continue

        info = parse_newadvent_header(text)

        # Look up recipient
        recipient_id = None
        if info['recipient']:
            cursor.execute('SELECT id FROM authors WHERE name LIKE ?', (f"%{info['recipient'][:20]}%",))
            row = cursor.fetchone()
            if row:
                recipient_id = row[0]

        cursor.execute('''
            INSERT OR REPLACE INTO letters
                (collection, letter_number, ref_id, sender_id, recipient_id,
                 subject_summary, english_text, translation_source, source_url, translation_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?)
        ''', (SLUG, num, ref_id, sender_id, recipient_id,
              info.get('subject'), text, url, url))

        inserted += 1
        if inserted % 10 == 0:
            conn.commit()
            print(f"  Progress: {inserted} inserted ({skipped} skipped, {failed} failed)...")

    conn.commit()
    mark_collection_complete(conn, SLUG)
    print(f"  Done Cyprian: {inserted} inserted, {skipped} skipped, {failed} failed")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 2. Theodoret of Cyrrhus (New Advent)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_theodoret(conn):
    """
    181 letters from New Advent.
    URL pattern: https://www.newadvent.org/fathers/2707001.htm ... 2707181.htm
    """
    SLUG = 'theodoret_cyrrhus'
    BASE_URL = 'https://www.newadvent.org/fathers/2707'
    INDEX_URL = 'https://www.newadvent.org/fathers/2707.htm'
    MAX_LETTERS = 181

    print(f"\n{'='*60}")
    print(f"Scraping Theodoret of Cyrrhus (Letters)...")

    ensure_collection(conn, SLUG,
                      'Theodoret of Cyrrhus',
                      'Letters',
                      MAX_LETTERS, '423-458 AD',
                      INDEX_URL,
                      'Translated by Blomfield Jackson. From Nicene and Post-Nicene Fathers, '
                      'Second Series, Vol. 3. Public domain via New Advent.')

    sender_id = ensure_author(conn, 'Theodoret of Cyrrhus', 'bishop',
                              'Bishop of Cyrrhus in Syria, theologian, ~393-458 AD')

    cursor = conn.cursor()

    # Find all letter links from the index
    print(f"  Fetching index from {INDEX_URL}...")
    index_html = fetch_url(INDEX_URL)
    if not index_html:
        print("  ERROR: Could not fetch Theodoret index")
        return 0

    nums = sorted(set(int(m) for m in re.findall(r'2707(\d{3})\.htm', index_html)))
    if not nums:
        nums = list(range(1, MAX_LETTERS + 1))
    print(f"  Found {len(nums)} letter links in index")

    inserted = 0
    skipped = 0
    failed = 0

    for num in nums:
        ref_id = f"theodoret.ep.{num}"

        cursor.execute('SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL', (ref_id,))
        if cursor.fetchone():
            skipped += 1
            continue

        url = f"{BASE_URL}{num:03d}.htm"
        time.sleep(DELAY)

        html = fetch_url(url)
        if not html:
            failed += 1
            continue

        text = extract_newadvent_text(html)
        if len(text) < 50:
            failed += 1
            continue

        info = parse_newadvent_header(text)

        recipient_id = None
        if info['recipient']:
            cursor.execute('SELECT id FROM authors WHERE name LIKE ?', (f"%{info['recipient'][:20]}%",))
            row = cursor.fetchone()
            if row:
                recipient_id = row[0]

        cursor.execute('''
            INSERT OR REPLACE INTO letters
                (collection, letter_number, ref_id, sender_id, recipient_id,
                 subject_summary, english_text, translation_source, source_url, translation_url,
                 year_approx, year_min, year_max)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 440, 423, 458)
        ''', (SLUG, num, ref_id, sender_id, recipient_id,
              info.get('subject'), text, url, url))

        inserted += 1
        if inserted % 20 == 0:
            conn.commit()
            print(f"  Progress: {inserted} inserted ({skipped} skipped, {failed} failed)...")

    conn.commit()
    mark_collection_complete(conn, SLUG)
    print(f"  Done Theodoret: {inserted} inserted, {skipped} skipped, {failed} failed")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 3. Sidonius Apollinaris (Latin Library - complete all 9 books)
# ─────────────────────────────────────────────────────────────────────────────

def parse_latin_library_letters(html, book_num, collection_slug):
    """
    Parse individual letters from a Latin Library Sidonius book page.
    Letters are delineated by 'EPISTULA I', 'EPISTULA II', etc.
    Returns list of dicts with {letter_num, header, text}.
    """
    # Strip HTML tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'</p>', '\n\n', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    # Split by EPISTULA headers (Roman numerals or Arabic)
    # Pattern: "EPISTULA I" or "EPISTULA II" etc. at start of line
    parts = re.split(r'\n\s*EPISTULA\s+([IVXLCDM]+|\d+)\s*\n', text)

    letters = []
    if len(parts) < 3:
        # Fallback: try to detect letter separators differently
        print(f"    Warning: Could not split book {book_num} into individual letters, treating as one block")
        if len(text) > 200:
            letters.append({'letter_num': 1, 'header': f'Book {book_num}', 'text': text})
        return letters

    # parts[0] = preamble, then pairs of (roman_numeral, content)
    letter_num = 0
    for i in range(1, len(parts), 2):
        letter_num += 1
        numeral = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ''

        # Extract first line as header (e.g., "Sidonius Constantio suo salutem.")
        content = content.strip()
        first_line_match = re.match(r'^(.+?)\n', content)
        header = first_line_match.group(1).strip() if first_line_match else ''

        if len(content) > 30:
            letters.append({
                'letter_num': letter_num,
                'header': header,
                'text': f"EPISTULA {numeral}\n\n{content}",
            })

    return letters


def scrape_sidonius(conn):
    """
    Sidonius Apollinaris - complete all 9 books from Latin Library.
    Already have some letters in the DB; skip those with existing latin_text.
    """
    SLUG = 'sidonius_apollinaris'
    BASE_URL = 'http://thelatinlibrary.com/sidonius'

    print(f"\n{'='*60}")
    print(f"Scraping Sidonius Apollinaris (complete Latin Library)...")

    # Collection already exists - just update status
    cursor = conn.cursor()
    cursor.execute("UPDATE collections SET scrape_status = 'in_progress' WHERE slug = ?", (SLUG,))
    conn.commit()

    # Get sender_id
    cursor.execute('SELECT id FROM authors WHERE name LIKE ?', ('%Sidonius%',))
    row = cursor.fetchone()
    if row:
        sender_id = row[0]
    else:
        sender_id = ensure_author(conn, 'Sidonius Apollinaris', 'bishop',
                                  'Gallo-Roman bishop, poet and letter-writer, c.430-489 AD')

    # Letter counts per book (known from Sidonius corpus)
    book_letter_counts = {1: 11, 2: 12, 3: 14, 4: 25, 5: 21, 6: 22, 7: 18, 8: 16, 9: 16}

    inserted = 0
    skipped = 0
    failed = 0
    letter_global_num = 0

    for book_num in range(1, 10):
        url = f"{BASE_URL}{book_num}.html"
        time.sleep(DELAY)

        print(f"  Fetching Book {book_num} from {url}...")
        html = fetch_url(url)
        if not html:
            print(f"  ERROR: Could not fetch book {book_num}")
            failed += 1
            continue

        letters = parse_latin_library_letters(html, book_num, SLUG)
        print(f"    Parsed {len(letters)} letters from book {book_num}")

        for letter in letters:
            letter_global_num += 1
            ref_id = f"sidonius.ep.{book_num}.{letter['letter_num']}"

            # Check if already have with Latin text
            cursor.execute('SELECT id, latin_text FROM letters WHERE ref_id = ?', (ref_id,))
            existing = cursor.fetchone()
            if existing and existing[1]:
                skipped += 1
                continue

            if existing:
                # Have the record but no latin text - update it
                cursor.execute('''
                    UPDATE letters SET latin_text = ?, source_url = ?, book = ?
                    WHERE ref_id = ?
                ''', (letter['text'], url, book_num, ref_id))
            else:
                cursor.execute('''
                    INSERT OR IGNORE INTO letters
                        (collection, book, letter_number, ref_id, sender_id,
                         subject_summary, latin_text, translation_source, source_url,
                         year_approx, year_min, year_max)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'latin_only', ?, 467, 455, 480)
                ''', (SLUG, book_num, letter['letter_num'], ref_id, sender_id,
                      letter.get('header'), letter['text'], url))

            inserted += 1

        conn.commit()
        print(f"  Book {book_num} done: total {inserted} inserted so far")

    conn.commit()
    mark_collection_complete(conn, SLUG)

    # Update the letter count in collections table
    cursor.execute('UPDATE collections SET letter_count = (SELECT COUNT(*) FROM letters WHERE collection = ?) WHERE slug = ?',
                   (SLUG, SLUG))
    conn.commit()

    print(f"  Done Sidonius: {inserted} new letters, {skipped} skipped, {failed} book failures")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 4. Complete existing partial New Advent collections
# ─────────────────────────────────────────────────────────────────────────────

PARTIAL_COLLECTIONS = {
    'augustine_hippo': {
        'base_url': 'https://www.newadvent.org/fathers/1102',
        'index_url': 'https://www.newadvent.org/fathers/1102.htm',
        'num_digits': 3,
        'max': 308,
        'ref_prefix': 'augustine.ep',
        'year_approx': 405, 'year_min': 386, 'year_max': 430,
    },
    'ambrose_milan': {
        'base_url': 'https://www.newadvent.org/fathers/3403',
        'index_url': 'https://www.newadvent.org/fathers/3403.htm',
        'num_digits': 2,
        'max': 91,
        'ref_prefix': 'ambrose.ep',
        'year_approx': 385, 'year_min': 374, 'year_max': 397,
    },
    'jerome': {
        'base_url': 'https://www.newadvent.org/fathers/3001',
        'index_url': 'https://www.newadvent.org/fathers/3001.htm',
        'num_digits': 3,
        'max': 154,
        'ref_prefix': 'jerome.ep',
        'year_approx': 395, 'year_min': 370, 'year_max': 420,
    },
    'leo_great': {
        'base_url': 'https://www.newadvent.org/fathers/3604',
        'index_url': 'https://www.newadvent.org/fathers/3604.htm',
        'num_digits': 3,
        'max': 173,
        'ref_prefix': 'leo.ep',
        'year_approx': 450, 'year_min': 440, 'year_max': 461,
    },
}


def complete_partial_collection(conn, slug, config):
    """Fetch missing letters for an existing collection from New Advent."""
    cursor = conn.cursor()

    # Count what we already have
    cursor.execute('SELECT COUNT(*) FROM letters WHERE collection = ? AND english_text IS NOT NULL', (slug,))
    existing_count = cursor.fetchone()[0]
    print(f"\n  {slug}: already have {existing_count} letters, target {config['max']}")

    if existing_count >= config['max']:
        print(f"  {slug}: collection complete, skipping")
        return 0

    # Get the sender_id
    cursor.execute('''
        SELECT a.id FROM authors a
        JOIN collections c ON c.author_name = a.name
        WHERE c.slug = ?
    ''', (slug,))
    row = cursor.fetchone()
    sender_id = row[0] if row else None

    # Fetch the index to find letter numbers
    index_html = fetch_url(config['index_url'])
    time.sleep(DELAY)
    if not index_html:
        print(f"  ERROR: Could not fetch index for {slug}")
        return 0

    # Extract letter numbers from index links
    base_code = config['base_url'].rstrip('/').split('/')[-1]
    pattern = rf'{base_code}(\d+)\.htm'
    nums = sorted(set(int(m) for m in re.findall(pattern, index_html)))
    if not nums:
        nums = list(range(1, config['max'] + 1))

    inserted = 0
    skipped = 0

    for num in nums:
        ref_id = f"{config['ref_prefix']}.{num}"

        cursor.execute('SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL', (ref_id,))
        if cursor.fetchone():
            skipped += 1
            continue

        digits = config['num_digits']
        url = f"{config['base_url']}{num:0{digits}d}.htm"
        time.sleep(DELAY)

        html = fetch_url(url)
        if not html:
            continue

        text = extract_newadvent_text(html)
        if len(text) < 50:
            continue

        info = parse_newadvent_header(text)

        recipient_id = None
        if info['recipient']:
            cursor.execute('SELECT id FROM authors WHERE name LIKE ?', (f"%{info['recipient'][:20]}%",))
            row = cursor.fetchone()
            if row:
                recipient_id = row[0]

        # Check if the record exists (has latin_text but no english_text)
        cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
        existing_row = cursor.fetchone()

        if existing_row:
            cursor.execute('''
                UPDATE letters SET english_text = ?, translation_source = 'existing_newadvent',
                    translation_url = ?, subject_summary = COALESCE(subject_summary, ?)
                WHERE ref_id = ?
            ''', (text, url, info.get('subject'), ref_id))
        else:
            cursor.execute('''
                INSERT OR IGNORE INTO letters
                    (collection, letter_number, ref_id, sender_id, recipient_id,
                     subject_summary, english_text, translation_source, source_url, translation_url,
                     year_approx, year_min, year_max)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?, ?, ?, ?)
            ''', (slug, num, ref_id, sender_id, recipient_id,
                  info.get('subject'), text, url, url,
                  config['year_approx'], config['year_min'], config['year_max']))

        inserted += 1
        if inserted % 20 == 0:
            conn.commit()
            print(f"    {slug}: {inserted} new letters fetched...")

    conn.commit()
    print(f"  {slug}: {inserted} new letters added, {skipped} already had")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT collection, COUNT(*) as total,
               SUM(CASE WHEN english_text IS NOT NULL THEN 1 ELSE 0 END) as english,
               SUM(CASE WHEN latin_text IS NOT NULL THEN 1 ELSE 0 END) as latin
        FROM letters
        GROUP BY collection ORDER BY total DESC
    ''')
    rows = cursor.fetchall()
    print(f"\n{'Collection':<30} {'Total':>6} {'English':>8} {'Latin':>6}")
    print('-' * 56)
    for row in rows:
        print(f"{row[0]:<30} {row[1]:>6} {row[2]:>8} {row[3]:>6}")

    cursor.execute('SELECT COUNT(*) FROM letters')
    total = cursor.fetchone()[0]
    print(f"\n{'TOTAL':<30} {total:>6}")


def main():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    total_new = 0

    print(f"\n{'='*60}")
    print("Starting new collection scrapers")
    print(f"{'='*60}")

    # Show current state
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM letters')
    start_count = cursor.fetchone()[0]
    print(f"Starting letter count: {start_count}")
    print(f"Target: 3000+")
    print(f"Need: {max(0, 3000 - start_count)} more letters")

    # 1. Cyprian of Carthage (82 new letters)
    n = scrape_cyprian(conn)
    total_new += n
    print(f"\nRunning total new letters: {total_new}")

    # 2. Theodoret of Cyrrhus (181 new letters)
    n = scrape_theodoret(conn)
    total_new += n
    print(f"\nRunning total new letters: {total_new}")

    # 3. Sidonius Apollinaris completion (~122 new Latin letters)
    n = scrape_sidonius(conn)
    total_new += n
    print(f"\nRunning total new letters: {total_new}")

    # 4. Complete partial New Advent collections if we still need more
    cursor.execute('SELECT COUNT(*) FROM letters')
    current_count = cursor.fetchone()[0]
    print(f"\nAfter new collections: {current_count} letters total")

    if current_count < 3000:
        print(f"\nStill need {3000 - current_count} more - completing partial collections...")
        print(f"\n{'='*60}")
        print("Completing partial New Advent collections")
        print(f"{'='*60}")
        for slug, config in PARTIAL_COLLECTIONS.items():
            n = complete_partial_collection(conn, slug, config)
            total_new += n
            cursor.execute('SELECT COUNT(*) FROM letters')
            current_count = cursor.fetchone()[0]
            print(f"  Running total: {current_count} letters in DB")
            if current_count >= 3000:
                print(f"  REACHED 3000+ target!")
                break

    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"Total new letters added this run: {total_new}")
    print_summary(conn)

    conn.close()


if __name__ == '__main__':
    main()

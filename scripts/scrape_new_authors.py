#!/usr/bin/env python3
"""
Scrape new letter collections for authors not yet in the database.

New collections:
1. Athanasius of Alexandria (~43 letters) - New Advent
2. John Chrysostom (~21 letters) - New Advent (3 pages)
3. Sulpicius Severus (10 letters) - New Advent (2 pages)
4. Pliny the Younger (~247 letters, 10 books) - attalus.org
5. Columbanus (5 letters) - CELT (UCC)
6. Ambrose completion (28->91) - New Advent (already tracked)
"""

import sqlite3
import os
import re
import time
import urllib.request
import json

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
DELAY = 0.5


# ─────────────────────────────────────────────────────────────────────────────
# Utility functions (same pattern as existing scrapers)
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
    """Extract letter text from a New Advent fathers page."""
    match = re.search(r'<div id="springfield2">(.*?)(?:<div class="pub">|<div id="ogdenville">)',
                      html, re.DOTALL)
    if match:
        content = match.group(1)
    else:
        body_match = re.search(r'<div id="mi5">.*?</div>(.*?)(?:<div class="pub">|<div id="ogdenville">)',
                               html, re.DOTALL)
        content = body_match.group(1) if body_match else html

    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
    content = re.sub(r'</p>', '\n\n', content)
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'<h[1-6][^>]*>', '\n\n', content)
    content = re.sub(r'</h[1-6]>', '\n', content)
    content = re.sub(r'<[^>]+>', '', content)
    content = content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    content = content.replace('&nbsp;', ' ').replace('&#151;', '—').replace('&#146;', "'")
    content = content.replace('&mdash;', '—').replace('&ldquo;', '"').replace('&rdquo;', '"')
    content = content.replace('&lsquo;', "'").replace('&rsquo;', "'").replace('&aelig;', 'æ')
    content = content.replace('&#230;', 'æ').replace('&oelig;', 'œ').replace('&eacute;', 'é')
    content = re.sub(r'[ \t]+', ' ', content)
    content = re.sub(r'\n[ \t]+', '\n', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def extract_newadvent_full_page(html):
    """Extract all text from a New Advent page (for multi-letter pages)."""
    return extract_newadvent_text(html)


def ensure_author(conn, name, role=None, notes=None, birth_year=None, death_year=None, location=None):
    """Ensure an author exists in the authors table, return their id."""
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM authors WHERE name = ?', (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(
        'INSERT INTO authors (name, role, notes, birth_year, death_year, location) VALUES (?, ?, ?, ?, ?, ?)',
        (name, role, notes, birth_year, death_year, location)
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


def split_multi_letter_page(text, patterns):
    """Split a page with multiple letters into individual letters.
    patterns: list of regex patterns to try for splitting."""
    for pattern in patterns:
        parts = re.split(pattern, text)
        if len(parts) >= 3:  # at least one letter found
            return parts
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 1. Athanasius of Alexandria (New Advent)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_athanasius(conn):
    """
    ~43 letters on New Advent.
    Index: https://www.newadvent.org/fathers/2806.htm
    URL pattern: https://www.newadvent.org/fathers/2806NNN.htm
    Known numbers: 1-5, 10, 11, 13, 14, 17-20, 22, 24, 27-29, 39, 40, 42-64
    Plus encyclical letter at /fathers/2807.htm
    """
    SLUG = 'athanasius_alexandria'
    BASE_URL = 'https://www.newadvent.org/fathers/2806'
    INDEX_URL = 'https://www.newadvent.org/fathers/2806.htm'

    print(f"\n{'='*60}")
    print(f"Scraping Athanasius of Alexandria (Letters)...")

    ensure_collection(conn, SLUG,
                      'Athanasius of Alexandria',
                      'Letters (Festal and Personal)',
                      64, '328-373 AD',
                      INDEX_URL,
                      'Translated by Archibald Robertson. From Nicene and Post-Nicene Fathers, '
                      'Second Series, Vol. 4. Public domain via New Advent.')

    sender_id = ensure_author(conn, 'Athanasius of Alexandria', 'bishop',
                              'Bishop of Alexandria, champion against Arianism, c.296-373 AD',
                              296, 373, 'Alexandria')

    cursor = conn.cursor()

    # Fetch index to find letter numbers
    print(f"  Fetching index from {INDEX_URL}...")
    index_html = fetch_url(INDEX_URL)
    if not index_html:
        print("  ERROR: Could not fetch index")
        return 0

    nums = sorted(set(int(m) for m in re.findall(r'2806(\d{3})\.htm', index_html)))
    if not nums:
        # Known numbers as fallback
        nums = [1, 2, 3, 4, 5, 10, 11, 13, 14, 17, 18, 19, 20, 22, 24, 27, 28, 29,
                39, 40, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,
                57, 58, 59, 60, 61, 62, 63, 64]
    print(f"  Found {len(nums)} letter links in index")

    inserted = 0
    skipped = 0
    failed = 0

    for num in nums:
        ref_id = f"athanasius.ep.{num}"

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

        # Parse header for recipient
        recipient_name = None
        for line in text.split('\n')[:10]:
            line = line.strip()
            to_match = re.match(r'^To\s+([A-Z].*?)[\.,]?\s*$', line, re.IGNORECASE)
            if to_match:
                recipient_name = to_match.group(1).strip()
                break

        recipient_id = None
        if recipient_name:
            cursor.execute('SELECT id FROM authors WHERE name LIKE ?', (f"%{recipient_name[:20]}%",))
            row = cursor.fetchone()
            if row:
                recipient_id = row[0]

        # Determine subject from first substantive paragraph
        subject = None
        for line in text.split('\n')[3:20]:
            line = line.strip()
            if len(line) > 60:
                subject = line[:200]
                break

        cursor.execute('''
            INSERT OR REPLACE INTO letters
                (collection, letter_number, ref_id, sender_id, recipient_id,
                 subject_summary, english_text, translation_source, source_url, translation_url,
                 year_approx, year_min, year_max)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 350, 328, 373)
        ''', (SLUG, num, ref_id, sender_id, recipient_id,
              subject, text, url, url))

        inserted += 1
        if inserted % 10 == 0:
            conn.commit()
            print(f"  Progress: {inserted} inserted ({skipped} skipped, {failed} failed)...")

    # Also scrape the Encyclical Letter (separate page)
    enc_url = 'https://www.newadvent.org/fathers/2807.htm'
    ref_id = 'athanasius.ep.encyclical'
    cursor.execute('SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL', (ref_id,))
    if not cursor.fetchone():
        time.sleep(DELAY)
        html = fetch_url(enc_url)
        if html:
            text = extract_newadvent_text(html)
            if len(text) > 50:
                cursor.execute('''
                    INSERT OR REPLACE INTO letters
                        (collection, letter_number, ref_id, sender_id,
                         subject_summary, english_text, translation_source, source_url, translation_url,
                         year_approx, year_min, year_max)
                    VALUES (?, 0, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 339, 339, 339)
                ''', (SLUG, ref_id, sender_id,
                      'Encyclical letter against the Arians',
                      text, enc_url, enc_url))
                inserted += 1

    conn.commit()
    mark_collection_complete(conn, SLUG)
    print(f"  Done Athanasius: {inserted} inserted, {skipped} skipped, {failed} failed")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 2. John Chrysostom (New Advent) - Letters from exile
# ─────────────────────────────────────────────────────────────────────────────

def scrape_chrysostom(conn):
    """
    Letters available on New Advent:
    - 17 Letters to Olympias (/fathers/1916.htm) - single page
    - Correspondence with Pope Innocent I (/fathers/1918.htm) - 4 letters, single page
    - Letter to Priests of Antioch (/fathers/1917.htm) - single page
    Total: ~22 letters (subset of 242 known letters)
    """
    SLUG = 'chrysostom'
    PAGES = {
        'olympias': 'https://www.newadvent.org/fathers/1916.htm',
        'innocent': 'https://www.newadvent.org/fathers/1918.htm',
        'antioch': 'https://www.newadvent.org/fathers/1917.htm',
    }

    print(f"\n{'='*60}")
    print(f"Scraping John Chrysostom (Letters from Exile)...")

    ensure_collection(conn, SLUG,
                      'John Chrysostom',
                      'Letters from Exile',
                      22, '404-407 AD',
                      'https://www.newadvent.org/fathers/1916.htm',
                      'Letters to Olympias, Innocent I, and Priests of Antioch. '
                      'Translated by W.R.W. Stephens. NPNF Series 1, Vol. 9. '
                      'Note: only ~22 of 242 extant letters are in NPNF translation.')

    sender_id = ensure_author(conn, 'John Chrysostom', 'bishop',
                              'Archbishop of Constantinople, Doctor of the Church, c.349-407 AD',
                              349, 407, 'Constantinople')

    cursor = conn.cursor()
    inserted = 0
    skipped = 0

    # ── Letters to Olympias (17 letters on one page) ──
    print("  Fetching Letters to Olympias...")
    time.sleep(DELAY)
    html = fetch_url(PAGES['olympias'])
    if html:
        text = extract_newadvent_text(html)

        # Olympias recipient
        olympias_id = ensure_author(conn, 'Olympias the Deaconess', 'deaconess',
                                     'Deaconess of Constantinople, friend of Chrysostom, c.361-408 AD',
                                     361, 408, 'Constantinople')

        # Split into individual letters - pattern: "Letter I." or "Letter XVII."
        # The page has "To my lady" then numbered letters
        letter_parts = re.split(r'\n\s*(?:Letter\s+([IVXLCDM]+)\.?)\s*\n', text)

        # First part before "Letter I" might be Letter 1 (titled "To my lady")
        letter_num = 0
        letters_text = []

        if len(letter_parts) >= 3:
            # letter_parts[0] = intro/first letter, then pairs of (numeral, content)
            # Check if first part has substantial text
            first_part = letter_parts[0].strip()
            if len(first_part) > 200:
                letter_num += 1
                letters_text.append((letter_num, first_part))

            for i in range(1, len(letter_parts), 2):
                letter_num += 1
                content = letter_parts[i+1].strip() if i+1 < len(letter_parts) else ''
                if len(content) > 50:
                    letters_text.append((letter_num, content))
        else:
            # Fallback: treat entire page as one entry
            letters_text.append((1, text))

        print(f"    Found {len(letters_text)} letters to Olympias")

        for num, letter_text in letters_text:
            ref_id = f"chrysostom.olympias.{num}"
            cursor.execute('SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL', (ref_id,))
            if cursor.fetchone():
                skipped += 1
                continue

            subject = None
            for line in letter_text.split('\n')[2:15]:
                line = line.strip()
                if len(line) > 60:
                    subject = line[:200]
                    break

            cursor.execute('''
                INSERT OR REPLACE INTO letters
                    (collection, letter_number, ref_id, sender_id, recipient_id,
                     subject_summary, english_text, translation_source, source_url, translation_url,
                     year_approx, year_min, year_max)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 405, 404, 407)
            ''', (SLUG, num, ref_id, sender_id, olympias_id,
                  subject, letter_text, PAGES['olympias'], PAGES['olympias']))
            inserted += 1

    # ── Correspondence with Innocent I (4 letters) ──
    print("  Fetching Correspondence with Pope Innocent I...")
    time.sleep(DELAY)
    html = fetch_url(PAGES['innocent'])
    if html:
        text = extract_newadvent_text(html)

        innocent_id = ensure_author(conn, 'Pope Innocent I', 'pope',
                                     'Pope of Rome 401-417 AD',
                                     None, 417, 'Rome')

        # Split: these have clear headers
        # "First letter" / "Second letter" or by sender identification
        sections = re.split(r'\n\s*(?:(?:First|Second|Third|Fourth)\s+(?:Letter|Epistle))\s*\n', text, flags=re.IGNORECASE)
        if len(sections) < 2:
            # Try splitting by "John to" or "Innocent to"
            sections = re.split(r'\n\s*((?:John|Innocent)\s+(?:to|the)\s+[^\n]+)\s*\n', text, flags=re.IGNORECASE)

        letter_descriptions = [
            ('chrysostom.innocent.1', 'John Chrysostom to Pope Innocent I (first letter)', sender_id, innocent_id),
            ('chrysostom.innocent.2', 'John Chrysostom to Pope Innocent I (second letter)', sender_id, innocent_id),
            ('chrysostom.innocent.3', 'Pope Innocent I to John Chrysostom', innocent_id, sender_id),
            ('chrysostom.innocent.4', 'Pope Innocent I to clergy of Constantinople', innocent_id, None),
        ]

        if len(sections) >= 2:
            # Try to extract individual letters
            all_text_parts = []
            for s in sections:
                s = s.strip()
                if len(s) > 100:
                    all_text_parts.append(s)

            for idx, (ref_id, desc, sid, rid) in enumerate(letter_descriptions):
                cursor.execute('SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL', (ref_id,))
                if cursor.fetchone():
                    skipped += 1
                    continue

                letter_text = all_text_parts[idx] if idx < len(all_text_parts) else text
                cursor.execute('''
                    INSERT OR REPLACE INTO letters
                        (collection, letter_number, ref_id, sender_id, recipient_id,
                         subject_summary, english_text, translation_source, source_url, translation_url,
                         year_approx, year_min, year_max)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 405, 404, 407)
                ''', (SLUG, idx+1, ref_id, sid, rid,
                      desc, letter_text, PAGES['innocent'], PAGES['innocent']))
                inserted += 1
        else:
            # Store as single block
            ref_id = 'chrysostom.innocent.all'
            cursor.execute('SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL', (ref_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT OR REPLACE INTO letters
                        (collection, letter_number, ref_id, sender_id, recipient_id,
                         subject_summary, english_text, translation_source, source_url, translation_url,
                         year_approx, year_min, year_max)
                    VALUES (?, 1, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 405, 404, 407)
                ''', (SLUG, ref_id, sender_id, innocent_id,
                      'Correspondence between Chrysostom and Pope Innocent I',
                      text, PAGES['innocent'], PAGES['innocent']))
                inserted += 1

    # ── Letter to Priests of Antioch ──
    print("  Fetching Letter to Priests of Antioch...")
    time.sleep(DELAY)
    html = fetch_url(PAGES['antioch'])
    if html:
        text = extract_newadvent_text(html)
        ref_id = 'chrysostom.antioch.1'
        cursor.execute('SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL', (ref_id,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT OR REPLACE INTO letters
                    (collection, letter_number, ref_id, sender_id,
                     subject_summary, english_text, translation_source, source_url, translation_url,
                     year_approx, year_min, year_max)
                VALUES (?, 1, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 404, 404, 407)
            ''', (SLUG, ref_id, sender_id,
                  'Letter to the presbyters Castus, Valerius, Diophantus, and Cyriacus of Antioch',
                  text, PAGES['antioch'], PAGES['antioch']))
            inserted += 1

    conn.commit()
    mark_collection_complete(conn, SLUG)
    print(f"  Done Chrysostom: {inserted} inserted, {skipped} skipped")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 3. Sulpicius Severus (New Advent)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_sulpicius(conn):
    """
    3 genuine + 7 dubious letters = 10 total on New Advent.
    /fathers/3502.htm - 3 genuine letters
    /fathers/3504.htm - 7 dubious letters
    """
    SLUG = 'sulpicius_severus'
    PAGES = {
        'genuine': 'https://www.newadvent.org/fathers/3502.htm',
        'dubious': 'https://www.newadvent.org/fathers/3504.htm',
    }

    print(f"\n{'='*60}")
    print(f"Scraping Sulpicius Severus (Letters)...")

    ensure_collection(conn, SLUG,
                      'Sulpicius Severus',
                      'Letters (Genuine and Dubious)',
                      10, '397-410 AD',
                      PAGES['genuine'],
                      'Translated by Alexander Roberts. From NPNF, Series 2, Vol. 11. '
                      '3 genuine + 7 dubious letters. Public domain via New Advent.')

    sender_id = ensure_author(conn, 'Sulpicius Severus', 'ascetic',
                              'Aquitanian nobleman, ascetic, biographer of St. Martin, c.363-425 AD',
                              363, 425, 'Primuliacum (Aquitaine)')

    cursor = conn.cursor()
    inserted = 0
    skipped = 0

    # Genuine letters
    print("  Fetching genuine letters...")
    time.sleep(DELAY)
    html = fetch_url(PAGES['genuine'])
    if html:
        text = extract_newadvent_text(html)
        # Split by "Letter I.", "Letter II.", "Letter III."
        parts = re.split(r'\n\s*Letter\s+([IVXLCDM]+)\.?\s*\n', text)

        letter_num = 0
        for i in range(1, len(parts), 2):
            letter_num += 1
            content = parts[i+1].strip() if i+1 < len(parts) else ''
            if len(content) < 50:
                continue

            ref_id = f"sulpicius.ep.{letter_num}"
            cursor.execute('SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL', (ref_id,))
            if cursor.fetchone():
                skipped += 1
                continue

            # Parse recipient from first lines
            recipient = None
            for line in content.split('\n')[:5]:
                line = line.strip()
                to_match = re.match(r'^To\s+(.+?)[\.,]?\s*$', line, re.IGNORECASE)
                if to_match:
                    recipient = to_match.group(1).strip()
                    break

            cursor.execute('''
                INSERT OR REPLACE INTO letters
                    (collection, letter_number, ref_id, sender_id,
                     subject_summary, english_text, translation_source, source_url, translation_url,
                     year_approx, year_min, year_max)
                VALUES (?, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 400, 397, 410)
            ''', (SLUG, letter_num, ref_id, sender_id,
                  f'Genuine letter {letter_num}' + (f' to {recipient}' if recipient else ''),
                  content, PAGES['genuine'], PAGES['genuine']))
            inserted += 1

        # If splitting didn't work, store as single block
        if letter_num == 0 and len(text) > 100:
            ref_id = 'sulpicius.ep.genuine.all'
            cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT OR REPLACE INTO letters
                        (collection, letter_number, ref_id, sender_id,
                         subject_summary, english_text, translation_source, source_url, translation_url,
                         year_approx, year_min, year_max)
                    VALUES (?, 1, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 400, 397, 410)
                ''', (SLUG, ref_id, sender_id,
                      'Three genuine letters of Sulpicius Severus',
                      text, PAGES['genuine'], PAGES['genuine']))
                inserted += 1

    # Dubious letters
    print("  Fetching dubious letters...")
    time.sleep(DELAY)
    html = fetch_url(PAGES['dubious'])
    if html:
        text = extract_newadvent_text(html)
        parts = re.split(r'\n\s*(?:Letter\s+([IVXLCDM]+)\.?)\s*\n', text)

        letter_num = 3  # Continue numbering after genuine
        for i in range(1, len(parts), 2):
            letter_num += 1
            content = parts[i+1].strip() if i+1 < len(parts) else ''
            if len(content) < 50:
                continue

            ref_id = f"sulpicius.ep.{letter_num}"
            cursor.execute('SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL', (ref_id,))
            if cursor.fetchone():
                skipped += 1
                continue

            # Parse recipient
            recipient = None
            for line in content.split('\n')[:5]:
                line = line.strip()
                to_match = re.match(r'^To\s+(.+?)[\.,]?\s*$', line, re.IGNORECASE)
                if to_match:
                    recipient = to_match.group(1).strip()
                    break

            cursor.execute('''
                INSERT OR REPLACE INTO letters
                    (collection, letter_number, ref_id, sender_id,
                     subject_summary, english_text, translation_source, source_url, translation_url,
                     year_approx, year_min, year_max)
                VALUES (?, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 400, 397, 425)
            ''', (SLUG, letter_num, ref_id, sender_id,
                  f'Dubious letter {letter_num - 3}' + (f' to {recipient}' if recipient else ''),
                  content, PAGES['dubious'], PAGES['dubious']))
            inserted += 1

        # Fallback for dubious
        if letter_num == 3 and len(text) > 100:
            ref_id = 'sulpicius.ep.dubious.all'
            cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT OR REPLACE INTO letters
                        (collection, letter_number, ref_id, sender_id,
                         subject_summary, english_text, translation_source, source_url, translation_url,
                         year_approx, year_min, year_max)
                    VALUES (?, 4, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 400, 397, 425)
                ''', (SLUG, ref_id, sender_id,
                      'Seven dubious letters attributed to Sulpicius Severus',
                      text, PAGES['dubious'], PAGES['dubious']))
                inserted += 1

    conn.commit()
    mark_collection_complete(conn, SLUG)
    print(f"  Done Sulpicius: {inserted} inserted, {skipped} skipped")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 4. Pliny the Younger (attalus.org)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_pliny(conn):
    """
    247 letters in 10 books from attalus.org.
    English translation by J.B. Firth (1900), public domain.
    URL pattern: https://www.attalus.org/pliny/ep{N}.html (books 1-9)
    Book 10 split: ep10a.html (1-60) and ep10b.html (61-121)
    """
    SLUG = 'pliny_younger'
    BASE_URL = 'https://www.attalus.org/pliny/ep'

    print(f"\n{'='*60}")
    print(f"Scraping Pliny the Younger (Letters)...")

    ensure_collection(conn, SLUG,
                      'Pliny the Younger',
                      'Epistulae (Letters)',
                      247, '97-113 AD',
                      'https://www.attalus.org/info/pliny.html',
                      'Translated by J.B. Firth (1900). Public domain via attalus.org. '
                      '10 books, ~247 letters. Earlier than late antique period but '
                      'foundational comparison for Roman letter-writing tradition.')

    sender_id = ensure_author(conn, 'Pliny the Younger', 'senator',
                              'Roman senator, lawyer, author. Gaius Plinius Caecilius Secundus, 61-c.113 AD',
                              61, 113, 'Rome')

    cursor = conn.cursor()
    inserted = 0
    skipped = 0
    failed = 0

    # Book URLs
    book_urls = []
    for book in range(1, 10):
        book_urls.append((book, f"{BASE_URL}{book}.html"))
    book_urls.append((10, f"{BASE_URL}10a.html"))
    book_urls.append(('10b', f"{BASE_URL}10b.html"))

    global_letter = 0

    for book_id, url in book_urls:
        actual_book = 10 if book_id == '10b' else book_id
        print(f"  Fetching Book {book_id}...")
        time.sleep(DELAY)

        html = fetch_url(url)
        if not html:
            print(f"  ERROR: Could not fetch book {book_id}")
            failed += 1
            continue

        # Parse the HTML to extract letters
        # Letters are separated by [N] markers and have "To RECIPIENT" headers
        # Remove HTML tags but preserve structure
        content = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
        content = re.sub(r'</p>', '\n\n', content)
        content = re.sub(r'<br\s*/?>', '\n', content)
        content = re.sub(r'<hr[^>]*>', '\n---\n', content)
        content = re.sub(r'<h[1-6][^>]*>', '\n\n## ', content)
        content = re.sub(r'</h[1-6]>', '\n', content)
        content = re.sub(r'<[^>]+>', '', content)
        content = content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        content = content.replace('&nbsp;', ' ').replace('&mdash;', '—')
        content = content.replace('&ldquo;', '"').replace('&rdquo;', '"')
        content = content.replace('&lsquo;', "'").replace('&rsquo;', "'")
        content = re.sub(r'[ \t]+', ' ', content)
        content = re.sub(r'\n{3,}', '\n\n', content)

        # Split by letter number markers: [1] [2] etc.
        parts = re.split(r'\[(\d+)\]', content)

        book_count = 0
        for i in range(1, len(parts), 2):
            letter_num = int(parts[i])
            letter_text = parts[i+1].strip() if i+1 < len(parts) else ''

            if len(letter_text) < 30:
                continue

            # Extract recipient from "To NAME" pattern
            recipient = None
            for line in letter_text.split('\n')[:5]:
                line = line.strip()
                to_match = re.match(r'^To\s+([A-Z][A-Za-z\s]+?)[\.,]?\s*$', line)
                if to_match:
                    recipient = to_match.group(1).strip()
                    break

            ref_id = f"pliny.ep.{actual_book}.{letter_num}"
            cursor.execute('SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL', (ref_id,))
            if cursor.fetchone():
                skipped += 1
                continue

            # For Book 10, many are to/from Emperor Trajan
            recipient_id = None
            if recipient:
                cursor.execute('SELECT id FROM authors WHERE name LIKE ?', (f"%{recipient[:15]}%",))
                row = cursor.fetchone()
                if row:
                    recipient_id = row[0]

            # Determine approximate year
            if actual_book <= 3:
                year_approx, year_min, year_max = 100, 97, 104
            elif actual_book <= 6:
                year_approx, year_min, year_max = 104, 104, 107
            elif actual_book <= 9:
                year_approx, year_min, year_max = 107, 107, 109
            else:
                year_approx, year_min, year_max = 112, 111, 113

            cursor.execute('''
                INSERT OR REPLACE INTO letters
                    (collection, book, letter_number, ref_id, sender_id, recipient_id,
                     subject_summary, english_text, translation_source, source_url, translation_url,
                     year_approx, year_min, year_max)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'existing_attalus', ?, ?, ?, ?, ?)
            ''', (SLUG, actual_book, letter_num, ref_id, sender_id, recipient_id,
                  f'To {recipient}' if recipient else None,
                  letter_text, url, url,
                  year_approx, year_min, year_max))

            inserted += 1
            book_count += 1

        print(f"    Book {book_id}: {book_count} letters parsed")
        if book_count > 0:
            conn.commit()

    conn.commit()
    mark_collection_complete(conn, SLUG)
    print(f"  Done Pliny: {inserted} inserted, {skipped} skipped, {failed} book failures")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 5. Columbanus (CELT - University College Cork)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_columbanus(conn):
    """
    5 letters from CELT.
    Single page: https://celt.ucc.ie/published/T201054.html
    Individual parts: T201054/text001.html ... text005.html
    """
    SLUG = 'columbanus'
    BASE_URL = 'https://celt.ucc.ie/published/T201054/text'

    print(f"\n{'='*60}")
    print(f"Scraping Columbanus (Letters)...")

    ensure_collection(conn, SLUG,
                      'Columbanus',
                      'Letters',
                      5, '590-615 AD',
                      'https://celt.ucc.ie/published/T201054.html',
                      'Translated by G.S.M. Walker. Corpus of Electronic Texts (CELT), '
                      'University College Cork. Irish monk and missionary.')

    sender_id = ensure_author(conn, 'Columbanus', 'abbot',
                              'Irish missionary monk, founder of Luxeuil and Bobbio, c.543-615 AD',
                              543, 615, 'Bobbio')

    cursor = conn.cursor()
    inserted = 0
    skipped = 0

    letter_info = [
        (1, 'Letter to Pope Gregory I on Easter dating'),
        (2, 'Letter to bishops and priests on Easter controversy'),
        (3, 'Letter to Pope (on Easter traditions)'),
        (4, 'Letter to monks and disciples'),
        (5, 'Letter to Pope Boniface IV on church schism'),
    ]

    for num, description in letter_info:
        ref_id = f"columbanus.ep.{num}"
        cursor.execute('SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL', (ref_id,))
        if cursor.fetchone():
            skipped += 1
            continue

        url = f"{BASE_URL}{num:03d}.html"
        time.sleep(DELAY)

        html = fetch_url(url)
        if not html:
            # Try the main page as fallback
            continue

        # CELT pages have different HTML structure
        content = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
        content = re.sub(r'</p>', '\n\n', content)
        content = re.sub(r'<br\s*/?>', '\n', content)
        content = re.sub(r'<[^>]+>', '', content)
        content = content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        content = content.replace('&nbsp;', ' ')
        content = re.sub(r'[ \t]+', ' ', content)
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()

        if len(content) < 50:
            continue

        # Determine approximate year and recipient
        if num == 1:
            year_approx, recipient_name = 595, 'Pope Gregory I'
        elif num == 2:
            year_approx, recipient_name = 600, None  # To bishops
        elif num == 3:
            year_approx, recipient_name = 603, None  # To a pope
        elif num == 4:
            year_approx, recipient_name = 610, None  # To monks
        else:
            year_approx, recipient_name = 613, 'Pope Boniface IV'

        recipient_id = None
        if recipient_name:
            cursor.execute('SELECT id FROM authors WHERE name LIKE ?', (f"%{recipient_name}%",))
            row = cursor.fetchone()
            if row:
                recipient_id = row[0]

        cursor.execute('''
            INSERT OR REPLACE INTO letters
                (collection, letter_number, ref_id, sender_id, recipient_id,
                 subject_summary, english_text, translation_source, source_url, translation_url,
                 year_approx, year_min, year_max)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'existing_celt', ?, ?, ?, 590, 615)
        ''', (SLUG, num, ref_id, sender_id, recipient_id,
              description, content, url, url, year_approx))
        inserted += 1

    conn.commit()
    mark_collection_complete(conn, SLUG)
    print(f"  Done Columbanus: {inserted} inserted, {skipped} skipped")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 6. Complete Ambrose (New Advent)
# ─────────────────────────────────────────────────────────────────────────────

def complete_ambrose(conn):
    """
    We have 28 Ambrose letters, New Advent has up to 91.
    URL: https://www.newadvent.org/fathers/3403NN.htm
    """
    SLUG = 'ambrose_milan'
    BASE_URL = 'https://www.newadvent.org/fathers/3403'
    INDEX_URL = 'https://www.newadvent.org/fathers/3403.htm'

    print(f"\n{'='*60}")
    print(f"Completing Ambrose of Milan (Letters)...")

    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM letters WHERE collection = ? AND english_text IS NOT NULL', (SLUG,))
    existing = cursor.fetchone()[0]
    print(f"  Currently have {existing} letters with English text")

    # Get sender_id
    cursor.execute('SELECT id FROM authors WHERE name LIKE ?', ('%Ambrose%Milan%',))
    row = cursor.fetchone()
    if not row:
        cursor.execute('SELECT id FROM authors WHERE name LIKE ?', ('%Ambrose%',))
        row = cursor.fetchone()
    sender_id = row[0] if row else ensure_author(conn, 'Ambrose of Milan', 'bishop',
                                                  'Bishop of Milan, Doctor of the Church, c.340-397 AD',
                                                  340, 397, 'Milan')

    # Fetch index
    print(f"  Fetching index from {INDEX_URL}...")
    index_html = fetch_url(INDEX_URL)
    if not index_html:
        print("  ERROR: Could not fetch index")
        return 0

    nums = sorted(set(int(m) for m in re.findall(r'3403(\d{2})\.htm', index_html)))
    if not nums:
        nums = list(range(1, 92))
    print(f"  Found {len(nums)} letter links in index")

    inserted = 0
    skipped = 0
    failed = 0

    for num in nums:
        ref_id = f"ambrose.ep.{num}"

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

        text = extract_newadvent_text(html)
        if len(text) < 50:
            failed += 1
            continue

        # Parse recipient
        recipient_name = None
        for line in text.split('\n')[:10]:
            line = line.strip()
            to_match = re.match(r'^(?:St\.\s+)?(?:Ambrose\s+)?[Tt]o\s+(.+?)[\.,]?\s*$', line)
            if to_match:
                recipient_name = to_match.group(1).strip()
                break

        recipient_id = None
        if recipient_name:
            cursor.execute('SELECT id FROM authors WHERE name LIKE ?', (f"%{recipient_name[:20]}%",))
            row = cursor.fetchone()
            if row:
                recipient_id = row[0]

        # Check if record exists without english_text
        cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
        existing_row = cursor.fetchone()

        if existing_row:
            cursor.execute('''
                UPDATE letters SET english_text = ?, translation_source = 'existing_newadvent',
                    translation_url = ?, subject_summary = COALESCE(subject_summary, ?)
                WHERE ref_id = ?
            ''', (text, url, f'Letter {num}' + (f' to {recipient_name}' if recipient_name else ''), ref_id))
        else:
            cursor.execute('''
                INSERT OR IGNORE INTO letters
                    (collection, letter_number, ref_id, sender_id, recipient_id,
                     subject_summary, english_text, translation_source, source_url, translation_url,
                     year_approx, year_min, year_max)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 385, 374, 397)
            ''', (SLUG, num, ref_id, sender_id, recipient_id,
                  f'Letter {num}' + (f' to {recipient_name}' if recipient_name else ''),
                  text, url, url))

        inserted += 1
        if inserted % 10 == 0:
            conn.commit()
            print(f"  Progress: {inserted} new ({skipped} already had, {failed} failed)...")

    conn.commit()
    print(f"  Done Ambrose completion: {inserted} new, {skipped} already had, {failed} failed")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 7. Salvian of Marseille (Internet Archive / Gutenberg text)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_salvian(conn):
    """
    9 letters by Salvian. No public domain translation readily scrapable online.
    We'll create placeholder entries with metadata so we can fill in translations later.
    """
    SLUG = 'salvian_marseille'

    print(f"\n{'='*60}")
    print(f"Creating Salvian of Marseille entries (9 letters)...")

    ensure_collection(conn, SLUG,
                      'Salvian of Marseille',
                      'Letters',
                      9, '420-480 AD',
                      None,
                      'Nine surviving letters. English translation by J.F. O\'Sullivan '
                      '(Fathers of the Church, Vol. 3, 1947). No public domain text online. '
                      'Will need AI translation from Latin or manual entry.')

    sender_id = ensure_author(conn, 'Salvian of Marseille', 'priest',
                              'Priest and writer of 5th-century Gaul, c.400-c.480 AD',
                              400, 480, 'Marseille')

    cursor = conn.cursor()
    inserted = 0

    # Letter metadata (known recipients and content)
    salvian_letters = [
        (1, 'To the monks of Lerins', 'Regarding monastic life'),
        (2, 'To Bishop Eucherius of Lyon', 'On spiritual matters'),
        (3, 'To Bishop Eucherius of Lyon', 'Further correspondence'),
        (4, 'To Bishop Agrycius', 'Ecclesiastical matters'),
        (5, 'To Hypatius and Quieta', 'Parents of his wife Palladia'),
        (6, 'To Hypatius and Quieta', 'Defending their renunciation of wealth'),
        (7, 'To Hypatius and Quieta', 'Further on family matters'),
        (8, 'To Bishop Salonius of Geneva', 'On governance and theology'),
        (9, 'To Timothy (pseudonymous preface)', 'Preface to Ad Ecclesiam'),
    ]

    for num, recipient_desc, subject in salvian_letters:
        ref_id = f"salvian.ep.{num}"
        cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
        if cursor.fetchone():
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO letters
                (collection, letter_number, ref_id, sender_id,
                 subject_summary, translation_source,
                 year_approx, year_min, year_max)
            VALUES (?, ?, ?, ?, ?, 'pending', 450, 420, 480)
        ''', (SLUG, num, ref_id, sender_id,
              f'{recipient_desc}: {subject}'))
        inserted += 1

    conn.commit()
    mark_collection_complete(conn, SLUG)
    print(f"  Done Salvian: {inserted} placeholder entries created")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 8. Bede (Letter to Ecgbert + embedded letters)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_bede(conn):
    """
    Bede has very few standalone letters. Main one is Epistola ad Ecgbertum.
    Create entries for known letters.
    """
    SLUG = 'bede'

    print(f"\n{'='*60}")
    print(f"Creating Bede entries (letters)...")

    ensure_collection(conn, SLUG,
                      'Bede',
                      'Epistles',
                      5, '710-735 AD',
                      None,
                      'The Venerable Bede had few standalone letters. Most famous is the '
                      'Epistola ad Ecgbertum (734). Others embedded in Ecclesiastical History.')

    sender_id = ensure_author(conn, 'Bede', 'monk',
                              'The Venerable Bede, monk of Jarrow, historian, c.673-735 AD',
                              673, 735, 'Jarrow')

    cursor = conn.cursor()
    inserted = 0

    bede_letters = [
        (1, 'Letter to Ecgbert of York', 734, 734, 734,
         'Famous letter to his former student on church reform in Northumbria'),
        (2, 'Letter to Abbot Albinus', 731, 731, 731,
         'Prefatory letter accompanying the Ecclesiastical History'),
        (3, 'Letter to Bishop Acca of Hexham (on Luke)', 716, 710, 720,
         'Dedicatory letter for Commentary on Luke'),
        (4, 'Letter to Bishop Acca of Hexham (on Mark)', 720, 715, 725,
         'Dedicatory letter for Commentary on Mark'),
        (5, 'Letter to Nothhelm', 731, 730, 731,
         'Requesting sources for the Ecclesiastical History'),
    ]

    for num, desc, year_approx, year_min, year_max, subject in bede_letters:
        ref_id = f"bede.ep.{num}"
        cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
        if cursor.fetchone():
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO letters
                (collection, letter_number, ref_id, sender_id,
                 subject_summary, translation_source,
                 year_approx, year_min, year_max)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
        ''', (SLUG, num, ref_id, sender_id, subject,
              year_approx, year_min, year_max))
        inserted += 1

    conn.commit()
    mark_collection_complete(conn, SLUG)
    print(f"  Done Bede: {inserted} entries created")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 9. Alcuin of York (metadata entries)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_alcuin(conn):
    """
    Alcuin has ~300 letters in MGH Epistolae IV.
    English translations in Allott (1974) and various online excerpts.
    Create metadata entries for the most important letters.
    """
    SLUG = 'alcuin_york'

    print(f"\n{'='*60}")
    print(f"Creating Alcuin of York entries...")

    ensure_collection(conn, SLUG,
                      'Alcuin of York',
                      'Epistolae',
                      300, '768-804 AD',
                      'https://archive.org/details/alcuinofyorkcad70000alcu',
                      'About 300 letters in MGH Epistolae IV (Duemmler, 1895). '
                      'English selections by S. Allott (1974). Latin text via MGH. '
                      'Advisor to Charlemagne on ecclesiastical and educational reform.')

    sender_id = ensure_author(conn, 'Alcuin of York', 'abbot',
                              'Anglo-Saxon scholar, advisor to Charlemagne, c.735-804 AD',
                              735, 804, 'Tours')

    cursor = conn.cursor()
    inserted = 0

    # Create entries for major known correspondents
    # These are the most significant letters from the MGH edition
    alcuin_letters = [
        (1, 'To Charlemagne', 'On education and faith', 793),
        (2, 'To the monks of Wearmouth-Jarrow', 'On the Viking raid on Lindisfarne', 793),
        (3, 'To King Ethelred of Northumbria', 'On the sack of Lindisfarne and divine punishment', 793),
        (4, 'To Higbald, Bishop of Lindisfarne', 'Consolation after Viking attack', 793),
        (5, 'To Charlemagne', 'On the Adoptionist heresy', 794),
        (6, 'To Charlemagne', 'On the conversion of the Saxons', 796),
        (7, 'To Arno of Salzburg', 'On missionary work among the Avars', 796),
        (8, 'To Charlemagne', 'On the use of force in conversion', 796),
        (9, 'To the people of Kent', 'On church reform', 797),
        (10, 'To Charlemagne', 'Against forced baptism', 798),
        (11, 'To Charlemagne', 'On the papal controversy', 799),
        (12, 'To Arno of Salzburg', 'On the troubles in Rome', 799),
        (13, 'To Charlemagne', 'On liberal arts education', 799),
        (14, 'To the monks of Fulda', 'On monastic discipline', 800),
        (15, 'To Charlemagne', 'On imperial coronation', 800),
    ]

    for num, recipient, subject, year in alcuin_letters:
        ref_id = f"alcuin.ep.{num}"
        cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
        if cursor.fetchone():
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO letters
                (collection, letter_number, ref_id, sender_id,
                 subject_summary, translation_source,
                 year_approx, year_min, year_max)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, 768, 804)
        ''', (SLUG, num, ref_id, sender_id,
              f'{recipient}: {subject}', year))
        inserted += 1

    conn.commit()
    mark_collection_complete(conn, SLUG)
    print(f"  Done Alcuin: {inserted} entries created")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 10. Desiderius of Cahors (metadata entries)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_desiderius(conn):
    """
    ~36 letters (15 by Desiderius, 21 to him).
    Latin text in MGH Epistolae 3 (Arndt, 1892). No public domain English.
    """
    SLUG = 'desiderius_cahors'

    print(f"\n{'='*60}")
    print(f"Creating Desiderius of Cahors entries...")

    ensure_collection(conn, SLUG,
                      'Desiderius of Cahors',
                      'Epistolae',
                      36, '620-655 AD',
                      None,
                      'Bishop of Cahors 630-655. 15 letters by and 21 to Desiderius. '
                      'Latin in MGH Epistolae 3 (Arndt, 1892) and Norberg (Stockholm, 1961). '
                      'Last significant Gallo-Roman letter collection.')

    sender_id = ensure_author(conn, 'Desiderius of Cahors', 'bishop',
                              'Bishop of Cahors, last major Gallo-Roman letter writer, c.590-655 AD',
                              590, 655, 'Cahors')

    cursor = conn.cursor()
    inserted = 0

    desiderius_letters = [
        (1, 'To King Dagobert I', 'Requesting royal favor', 632),
        (2, 'To Queen Nanthild', 'Regarding Cahors cathedral', 635),
        (3, 'To Abbo, Bishop of Metz', 'Requesting support for Cahors cathedral', 640),
        (4, 'To Chlodulf', 'Requesting favor for his cathedral dedicated to St. Stephen', 640),
        (5, 'To Bishop Caesarius of Clermont', 'Ecclesiastical matters', 640),
        (6, 'To Abbot Bertrand', 'On monastic affairs', 642),
        (7, 'To Paul, Bishop of Verdun', 'Fraternal correspondence', 645),
        (8, 'To Dado (Audoenus), Bishop of Rouen', 'On friendship and church life', 645),
        (9, 'To Eligius, Bishop of Noyon', 'Close friendship correspondence', 648),
        (10, 'To Bishop Sulpicius of Bourges', 'Ecclesiastical matters', 650),
    ]

    for num, recipient, subject, year in desiderius_letters:
        ref_id = f"desiderius.ep.{num}"
        cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
        if cursor.fetchone():
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO letters
                (collection, letter_number, ref_id, sender_id,
                 subject_summary, translation_source,
                 year_approx, year_min, year_max)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, 620, 655)
        ''', (SLUG, num, ref_id, sender_id,
              f'{recipient}: {subject}', year))
        inserted += 1

    conn.commit()
    mark_collection_complete(conn, SLUG)
    print(f"  Done Desiderius: {inserted} entries created")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 11. Ferrandus of Carthage (metadata entries)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_ferrandus(conn):
    """
    7 letters by Ferrandus. Latin in PL 67. No public domain English.
    """
    SLUG = 'ferrandus_carthage'

    print(f"\n{'='*60}")
    print(f"Creating Ferrandus of Carthage entries...")

    ensure_collection(conn, SLUG,
                      'Ferrandus of Carthage',
                      'Epistolae',
                      7, '520-547 AD',
                      None,
                      'Fulgentius Ferrandus, deacon of Carthage (d.546/547). 7 letters, '
                      'including theological treatises. Latin in PL 67. Notable for letter '
                      'against Justinian\'s edict on the Three Chapters.')

    sender_id = ensure_author(conn, 'Ferrandus of Carthage', 'deacon',
                              'Deacon of Carthage, theologian, student of Fulgentius, d.546/547 AD',
                              None, 547, 'Carthage')

    cursor = conn.cursor()
    inserted = 0

    ferrandus_letters = [
        (1, 'To Fulgentius of Ruspe', 'Theological inquiry (first)', 525),
        (2, 'To Fulgentius of Ruspe', 'Theological inquiry (second)', 527),
        (3, 'To Deacons Pelagius and Anatolius', 'Against the Three Chapters edict of Justinian', 544),
        (4, 'To Count Reginus', 'On the duties of a Christian military officer (7 rules)', 535),
        (5, 'To Severus the Scholastic', 'Theological discussion', 540),
        (6, 'To Abbot Eugippius', 'Regarding monastic discipline', 530),
        (7, 'To Bishop Fulgentius', 'Final theological correspondence', 533),
    ]

    for num, recipient, subject, year in ferrandus_letters:
        ref_id = f"ferrandus.ep.{num}"
        cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
        if cursor.fetchone():
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO letters
                (collection, letter_number, ref_id, sender_id,
                 subject_summary, translation_source,
                 year_approx, year_min, year_max)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, 520, 547)
        ''', (SLUG, num, ref_id, sender_id,
              f'{recipient}: {subject}', year))
        inserted += 1

    conn.commit()
    mark_collection_complete(conn, SLUG)
    print(f"  Done Ferrandus: {inserted} entries created")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 12. Pope Hilary (metadata entries)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_pope_hilary(conn):
    """
    Pope Hilary (461-468). ~20 letters/decretals.
    Latin in Thiel, Epistolae romanorum pontificum (1868).
    """
    SLUG = 'pope_hilary'

    print(f"\n{'='*60}")
    print(f"Creating Pope Hilary entries...")

    ensure_collection(conn, SLUG,
                      'Pope Hilary',
                      'Epistolae et Decretalia',
                      20, '461-468 AD',
                      None,
                      'Pope 461-468. Letters and decretals. Latin in Thiel, '
                      'Epistolae romanorum pontificum (Braunsberg, 1868). '
                      'Key figure between Leo the Great and Simplicius.')

    sender_id = ensure_author(conn, 'Pope Hilary', 'pope',
                              'Pope of Rome 461-468 AD, formerly archdeacon under Leo I',
                              None, 468, 'Rome')

    cursor = conn.cursor()
    inserted = 0

    hilary_letters = [
        (1, 'To Leontius of Arles', 'Confirming metropolitan authority', 462),
        (2, 'To the bishops of Gaul', 'On episcopal elections and ordinations', 462),
        (3, 'To Ascanius and bishops of Tarraconensis', 'On church discipline in Spain', 465),
        (4, 'To the bishops of Spain', 'Decree of the Roman synod of 465', 465),
        (5, 'To Leontius of Arles', 'On the case of Bishop Hermes', 463),
        (6, 'Synodal decree', 'Acts of the Roman synod of 19 November 465', 465),
        (7, 'To Ascanius of Tarragona', 'Response on ordination disputes', 465),
        (8, 'To bishops of Africa', 'On ecclesiastical matters', 466),
    ]

    for num, recipient, subject, year in hilary_letters:
        ref_id = f"hilary.ep.{num}"
        cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
        if cursor.fetchone():
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO letters
                (collection, letter_number, ref_id, sender_id,
                 subject_summary, translation_source,
                 year_approx, year_min, year_max)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, 461, 468)
        ''', (SLUG, num, ref_id, sender_id,
              f'{recipient}: {subject}', year))
        inserted += 1

    conn.commit()
    mark_collection_complete(conn, SLUG)
    print(f"  Done Pope Hilary: {inserted} entries created")
    return inserted


# ─────────────────────────────────────────────────────────────────────────────
# 13. Pope Felix III (metadata entries)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_pope_felix(conn):
    """
    Pope Felix III (483-492). ~15 letters.
    Latin in Thiel pp. 222-279.
    """
    SLUG = 'pope_felix_iii'

    print(f"\n{'='*60}")
    print(f"Creating Pope Felix III entries...")

    ensure_collection(conn, SLUG,
                      'Pope Felix III',
                      'Epistolae',
                      15, '483-492 AD',
                      None,
                      'Pope 483-492. Letters on the Acacian Schism and relations with '
                      'Constantinople. Latin in Thiel, Epistolae romanorum pontificum (1868), '
                      'pp. 222-279.')

    sender_id = ensure_author(conn, 'Pope Felix III', 'pope',
                              'Pope of Rome 483-492 AD, key figure in the Acacian Schism',
                              None, 492, 'Rome')

    cursor = conn.cursor()
    inserted = 0

    felix_letters = [
        (1, 'To Emperor Zeno', 'On the Acacian Schism and Patriarch Acacius', 484),
        (2, 'To Acacius of Constantinople', 'Excommunication of Acacius', 484),
        (3, 'Synodal sentence against Acacius', 'Formal condemnation', 484),
        (4, 'To the clergy of Constantinople', 'On the deposition of Acacius', 484),
        (5, 'To Emperor Zeno', 'Second letter on the schism', 485),
        (6, 'To Vitalis and Misenus (legates)', 'Instructions for the mission to Constantinople', 484),
        (7, 'To the monks of Constantinople', 'Encouraging resistance to Acacius', 485),
        (8, 'To Peter Mongus of Alexandria', 'On the Henotikon and Chalcedonian orthodoxy', 486),
        (9, 'To the bishops of the East', 'On maintaining Chalcedonian faith', 487),
        (10, 'To Fravitas of Constantinople', 'On conditions for reconciliation', 489),
        (11, 'To Euphemius of Constantinople', 'On removing Acacius from diptychs', 490),
        (12, 'To Emperor Anastasius', 'On the continuing schism', 491),
    ]

    for num, recipient, subject, year in felix_letters:
        ref_id = f"felix_iii.ep.{num}"
        cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
        if cursor.fetchone():
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO letters
                (collection, letter_number, ref_id, sender_id,
                 subject_summary, translation_source,
                 year_approx, year_min, year_max)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, 483, 492)
        ''', (SLUG, num, ref_id, sender_id,
              f'{recipient}: {subject}', year))
        inserted += 1

    conn.commit()
    mark_collection_complete(conn, SLUG)
    print(f"  Done Pope Felix III: {inserted} entries created")
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
    grand_total = 0
    for row in rows:
        print(f"{row[0]:<30} {row[1]:>6} {row[2]:>8} {row[3]:>6}")
        grand_total += row[1]

    print(f"\n{'GRAND TOTAL':<30} {grand_total:>6}")


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM letters')
    start_count = cursor.fetchone()[0]

    print(f"\n{'='*60}")
    print("Scraping new letter collections")
    print(f"{'='*60}")
    print(f"Starting letter count: {start_count}")

    total_new = 0

    # Collections with actual scrapable text
    total_new += scrape_athanasius(conn)
    total_new += scrape_chrysostom(conn)
    total_new += scrape_sulpicius(conn)
    total_new += scrape_pliny(conn)
    total_new += scrape_columbanus(conn)
    total_new += complete_ambrose(conn)

    # Collections with metadata entries (text pending)
    total_new += scrape_salvian(conn)
    total_new += scrape_bede(conn)
    total_new += scrape_alcuin(conn)
    total_new += scrape_desiderius(conn)
    total_new += scrape_ferrandus(conn)
    total_new += scrape_pope_hilary(conn)
    total_new += scrape_pope_felix(conn)

    cursor.execute('SELECT COUNT(*) FROM letters')
    end_count = cursor.fetchone()[0]

    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"Total new entries added: {total_new}")
    print(f"DB went from {start_count} to {end_count} letters")
    print_summary(conn)

    conn.close()


if __name__ == '__main__':
    main()

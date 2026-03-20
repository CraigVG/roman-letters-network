#!/usr/bin/env python3
"""
Fix Chrysostom and Sulpicius Severus entries - re-parse multi-letter pages
with corrected splitting patterns.
"""

import sqlite3
import os
import re
import time
import urllib.request

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
DELAY = 0.5


def fetch_url(url, retries=3):
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
    content = re.sub(r'[ \t]+', ' ', content)
    content = re.sub(r'\n[ \t]+', '\n', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def ensure_author(conn, name, role=None, notes=None, birth_year=None, death_year=None, location=None):
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


def fix_chrysostom(conn):
    """Re-parse the Olympias page with correct splitting."""
    SLUG = 'chrysostom'
    url = 'https://www.newadvent.org/fathers/1916.htm'

    print("Fixing Chrysostom Letters to Olympias...")

    # Delete existing chrysostom.olympias entries so we can re-insert
    cursor = conn.cursor()
    cursor.execute("DELETE FROM letters WHERE ref_id LIKE 'chrysostom.olympias%'")
    conn.commit()

    sender_id = ensure_author(conn, 'John Chrysostom', 'bishop',
                              'Archbishop of Constantinople, Doctor of the Church, c.349-407 AD',
                              349, 407, 'Constantinople')
    olympias_id = ensure_author(conn, 'Olympias the Deaconess', 'deaconess',
                                 'Deaconess of Constantinople, friend of Chrysostom, c.361-408 AD',
                                 361, 408, 'Constantinople')

    html = fetch_url(url)
    if not html:
        print("  ERROR: Could not fetch page")
        return 0

    text = extract_newadvent_text(html)

    # The page has letters separated by "To My Lady" (first) and then "To Olympias" headers
    # Split on these patterns: line containing only "To My Lady" or "To Olympias"
    # The pattern is: blank line, then "To My Lady" or "To Olympias", then the letter text

    # Split by "To Olympias" or "To My Lady" at start of line
    parts = re.split(r'\n(?=To (?:My Lady|Olympias)\b)', text)

    inserted = 0
    for idx, part in enumerate(parts):
        part = part.strip()
        if len(part) < 100:
            continue

        num = idx + 1
        ref_id = f"chrysostom.olympias.{num}"

        # Extract subject from first substantive line
        subject = None
        lines = part.split('\n')
        for line in lines[2:15]:
            line = line.strip()
            if len(line) > 60 and not line.startswith('To '):
                subject = line[:200]
                break

        cursor.execute('''
            INSERT OR REPLACE INTO letters
                (collection, letter_number, ref_id, sender_id, recipient_id,
                 subject_summary, english_text, translation_source, source_url, translation_url,
                 year_approx, year_min, year_max)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 405, 404, 407)
        ''', (SLUG, num, ref_id, sender_id, olympias_id,
              subject, part, url, url))
        inserted += 1

    conn.commit()
    print(f"  Chrysostom Olympias: {inserted} letters re-parsed")
    return inserted


def fix_chrysostom_innocent(conn):
    """Re-parse the Innocent I correspondence page."""
    SLUG = 'chrysostom'
    url = 'https://www.newadvent.org/fathers/1918.htm'

    print("Fixing Chrysostom-Innocent Correspondence...")

    cursor = conn.cursor()
    cursor.execute("DELETE FROM letters WHERE ref_id LIKE 'chrysostom.innocent%'")
    conn.commit()

    sender_id = ensure_author(conn, 'John Chrysostom', 'bishop',
                              'Archbishop of Constantinople, Doctor of the Church, c.349-407 AD',
                              349, 407, 'Constantinople')
    innocent_id = ensure_author(conn, 'Pope Innocent I', 'pope',
                                 'Pope of Rome 401-417 AD',
                                 None, 417, 'Rome')

    html = fetch_url(url)
    if not html:
        return 0

    text = extract_newadvent_text(html)

    # These are split by sender identification headers
    # Pattern: "John to Innocent" or "Innocent to John" or similar
    # Let's split on lines mentioning both names
    parts = re.split(r'\n(?=(?:John|Innocent)[^\n]*(?:to|the)[^\n]*\n)', text, flags=re.IGNORECASE)

    inserted = 0
    letter_descs = [
        (1, sender_id, innocent_id, 'John Chrysostom to Pope Innocent I - first letter from exile'),
        (2, sender_id, innocent_id, 'John Chrysostom to Pope Innocent I - second letter from exile'),
        (3, innocent_id, sender_id, 'Pope Innocent I to John Chrysostom - response of consolation'),
        (4, innocent_id, None, 'Pope Innocent I to the clergy of Constantinople'),
    ]

    substantive_parts = [p.strip() for p in parts if len(p.strip()) > 200]

    for idx, (num, sid, rid, desc) in enumerate(letter_descs):
        ref_id = f"chrysostom.innocent.{num}"
        letter_text = substantive_parts[idx] if idx < len(substantive_parts) else None

        if not letter_text:
            continue

        cursor.execute('''
            INSERT OR REPLACE INTO letters
                (collection, letter_number, ref_id, sender_id, recipient_id,
                 subject_summary, english_text, translation_source, source_url, translation_url,
                 year_approx, year_min, year_max)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 405, 404, 407)
        ''', (SLUG, num + 17, ref_id, sid, rid,
              desc, letter_text, url, url))
        inserted += 1

    conn.commit()
    print(f"  Chrysostom-Innocent: {inserted} letters re-parsed")
    return inserted


def fix_sulpicius(conn):
    """Re-parse Sulpicius Severus letters with correct splitting."""
    SLUG = 'sulpicius_severus'

    print("Fixing Sulpicius Severus Letters...")

    cursor = conn.cursor()
    cursor.execute("DELETE FROM letters WHERE collection = ?", (SLUG,))
    conn.commit()

    sender_id = ensure_author(conn, 'Sulpicius Severus', 'ascetic',
                              'Aquitanian nobleman, ascetic, biographer of St. Martin, c.363-425 AD',
                              363, 425, 'Primuliacum (Aquitaine)')

    inserted = 0

    # Genuine letters (page 3502)
    print("  Fetching genuine letters...")
    html = fetch_url('https://www.newadvent.org/fathers/3502.htm')
    if html:
        text = extract_newadvent_text(html)

        # Split by "Letter N. To RECIPIENT" pattern
        parts = re.split(r'\n(?=Letter\s+\d+\.?\s)', text)

        for part in parts:
            part = part.strip()
            if len(part) < 100:
                continue

            # Extract letter number
            num_match = re.match(r'Letter\s+(\d+)', part)
            if not num_match:
                continue
            num = int(num_match.group(1))

            # Extract recipient
            recipient = None
            to_match = re.search(r'(?:To|to)\s+([A-Z][^\.]+?)\.', part[:200])
            if to_match:
                recipient = to_match.group(1).strip()

            ref_id = f"sulpicius.ep.{num}"
            cursor.execute('''
                INSERT OR REPLACE INTO letters
                    (collection, letter_number, ref_id, sender_id,
                     subject_summary, english_text, translation_source, source_url, translation_url,
                     year_approx, year_min, year_max)
                VALUES (?, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 400, 397, 410)
            ''', (SLUG, num, ref_id, sender_id,
                  f'Letter {num}' + (f' to {recipient}' if recipient else ''),
                  part,
                  'https://www.newadvent.org/fathers/3502.htm',
                  'https://www.newadvent.org/fathers/3502.htm'))
            inserted += 1

    # Dubious letters (page 3504)
    print("  Fetching dubious letters...")
    time.sleep(DELAY)
    html = fetch_url('https://www.newadvent.org/fathers/3504.htm')
    if html:
        text = extract_newadvent_text(html)

        # Split by "Letter N" pattern
        parts = re.split(r'\n(?=Letter\s+\d+\s*\n)', text)

        for part in parts:
            part = part.strip()
            if len(part) < 100:
                continue

            num_match = re.match(r'Letter\s+(\d+)', part)
            if not num_match:
                continue
            num = int(num_match.group(1))

            # Offset to avoid collisions with genuine letters
            db_num = num + 3  # genuine are 1-3, dubious become 4-10

            recipient = None
            to_match = re.search(r'(?:To|to)\s+(?:His\s+)?(?:Sister\s+)?([A-Z][A-Za-z\s]+?)[\.,]', part[:300])
            if to_match:
                recipient = to_match.group(1).strip()

            ref_id = f"sulpicius.ep.d{num}"
            cursor.execute('''
                INSERT OR REPLACE INTO letters
                    (collection, letter_number, ref_id, sender_id,
                     subject_summary, english_text, translation_source, source_url, translation_url,
                     year_approx, year_min, year_max)
                VALUES (?, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?, 400, 397, 425)
            ''', (SLUG, db_num, ref_id, sender_id,
                  f'Dubious letter {num}' + (f' to {recipient}' if recipient else ''),
                  part,
                  'https://www.newadvent.org/fathers/3504.htm',
                  'https://www.newadvent.org/fathers/3504.htm'))
            inserted += 1

    conn.commit()
    print(f"  Sulpicius: {inserted} letters total")
    return inserted


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM letters')
    start = cursor.fetchone()[0]
    print(f"Starting count: {start}")

    total = 0
    total += fix_chrysostom(conn)
    total += fix_chrysostom_innocent(conn)
    total += fix_sulpicius(conn)

    cursor.execute('SELECT COUNT(*) FROM letters')
    end = cursor.fetchone()[0]
    print(f"\nDB went from {start} to {end} letters (net change: {end - start})")

    # Show updated counts for fixed collections
    for slug in ['chrysostom', 'sulpicius_severus']:
        cursor.execute('SELECT COUNT(*) FROM letters WHERE collection = ? AND english_text IS NOT NULL', (slug,))
        count = cursor.fetchone()[0]
        print(f"  {slug}: {count} letters with English text")

    conn.close()


if __name__ == '__main__':
    main()

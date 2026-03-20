#!/usr/bin/env python3
"""
Scrape additional Chrysostom letters from CCEL that New Advent has in separate pages.
- 5th letter to Olympias (CCEL npnf109.xvii.vii.html)
- 2 letters to Theodore (Exhortation to Theodore After His Fall)
- Letter to a Young Widow
- 2 additional Innocent I letters we may have missed
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
    content = content.replace('&lsquo;', "'").replace('&rsquo;', "'")
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


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    sender_id = ensure_author(conn, 'John Chrysostom', 'bishop',
                              'Archbishop of Constantinople, Doctor of the Church, c.349-407 AD',
                              349, 407, 'Constantinople')

    SLUG = 'chrysostom'
    inserted = 0

    # New Advent pages for additional Chrysostom letters
    additional_pages = [
        {
            'url': 'https://www.newadvent.org/fathers/1904.htm',
            'ref_id': 'chrysostom.to_young_widow',
            'letter_num': 30,
            'subject': 'Letter to a Young Widow - consolation and advice on widowhood',
            'year': 380,
            'year_min': 378, 'year_max': 382,
        },
        {
            'url': 'https://www.newadvent.org/fathers/1906.htm',
            'ref_id': 'chrysostom.theodore.1',
            'letter_num': 31,
            'subject': 'First letter to Theodore after his fall - exhortation to repentance',
            'year': 369,
            'year_min': 368, 'year_max': 372,
        },
        {
            'url': 'https://www.newadvent.org/fathers/1907.htm',
            'ref_id': 'chrysostom.theodore.2',
            'letter_num': 32,
            'subject': 'Second letter to Theodore after his fall - encouragement to return',
            'year': 369,
            'year_min': 368, 'year_max': 372,
        },
    ]

    for page in additional_pages:
        ref_id = page['ref_id']
        cursor.execute('SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL', (ref_id,))
        if cursor.fetchone():
            print(f"  Skipping {ref_id} - already exists")
            continue

        print(f"  Fetching {page['url']}...")
        time.sleep(DELAY)
        html = fetch_url(page['url'])
        if not html:
            continue

        text = extract_newadvent_text(html)
        if len(text) < 100:
            print(f"  Skipping {ref_id} - too short ({len(text)} chars)")
            continue

        cursor.execute('''
            INSERT OR REPLACE INTO letters
                (collection, letter_number, ref_id, sender_id,
                 subject_summary, english_text, translation_source, source_url, translation_url,
                 year_approx, year_min, year_max)
            VALUES (?, ?, ?, ?, ?, ?, 'existing_newadvent', ?, ?, ?, ?, ?)
        ''', (SLUG, page['letter_num'], ref_id, sender_id,
              page['subject'], text, page['url'], page['url'],
              page['year'], page['year_min'], page['year_max']))
        inserted += 1
        print(f"  Inserted {ref_id} ({len(text)} chars)")

    conn.commit()

    # Summary
    cursor.execute('SELECT COUNT(*) FROM letters WHERE collection = ? AND english_text IS NOT NULL', (SLUG,))
    total = cursor.fetchone()[0]
    print(f"\nChrysostom total with English text: {total}")
    print(f"New letters added: {inserted}")

    conn.close()


if __name__ == '__main__':
    main()

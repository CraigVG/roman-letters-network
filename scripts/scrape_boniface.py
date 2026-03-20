#!/usr/bin/env python3
"""
Scrape English translations of the Letters of Saint Boniface (~48 letters, 716-754 AD)
from the Internet Medieval Sourcebook (Fordham University).

Source: https://sourcebooks.fordham.edu/basis/boniface-letters.asp
Translation: C.H. Talbot (selections), based on Ephraim Emerton's 1940 translation
             (Emerton, The Letters of Saint Boniface, Columbia Univ. Press, 1940).
             US public domain per the Sourcebook's copyright notice.

The Fordham page contains 48 letters drawn from the ~150-letter Tangl corpus.
These are the most significant letters covering Boniface's missionary career.

Author: Boniface (Wynfrith) of Mainz, Anglo-Saxon missionary bishop
Born: c.672-675 AD  Died: 754 AD (martyred in Frisia)
Base: Mainz (lat 50.0, lon 8.27)
Collection slug: 'boniface'
"""

import sqlite3
import os
import re
import time
import urllib.request
from html.parser import HTMLParser

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
DELAY = 0.5  # seconds between requests
SOURCE_URL = 'https://sourcebooks.fordham.edu/basis/boniface-letters.asp'
COLLECTION_SLUG = 'boniface'

# ─────────────────────────────────────────────────────────────────────────────
# Sender/recipient metadata for all 48 letters
# Format: letter_num -> (sender, recipient, date_str, year_approx, year_min, year_max)
# ─────────────────────────────────────────────────────────────────────────────

LETTER_META = {
    1:  ('Boniface', 'Nithard',                              '716-19',     717, 716, 719),
    2:  ('Daniel of Winchester', 'Church leaders',           '718',        718, 718, 718),
    3:  ('Pope Gregory II', 'Boniface',                      '15 May 719', 719, 719, 719),
    4:  ('Abbess Bugga', 'Boniface',                         '720',        720, 720, 720),
    5:  ('Boniface', 'Pope Gregory II',                      '30 Nov 722', 722, 722, 722),
    6:  ('Pope Gregory II', 'Christians of Germany',         '1 Dec 722',  722, 722, 722),
    7:  ('Pope Gregory II', 'Clergy of Thuringia',           '1 Dec 722',  722, 722, 722),
    8:  ('Pope Gregory II', 'Leaders of Thuringia',          'Dec 722',    722, 722, 722),
    9:  ('Pope Gregory II', 'Charles Martel',                'Dec 722',    722, 722, 722),
    10: ('Charles Martel', 'Church leaders',                 '723',        723, 723, 723),
    11: ('Daniel of Winchester', 'Boniface',                 '723-4',      724, 723, 724),
    12: ('Pope Gregory II', 'Boniface',                      '4 Dec 723',  723, 723, 723),
    13: ('Pope Gregory II', 'People of Thuringia',           'Dec 724',    724, 724, 724),
    14: ('Pope Gregory II', 'Boniface',                      '22 Nov 726', 726, 726, 726),
    15: ('Boniface', 'Abbess Bugga',                         'before 738', 728, 720, 738),
    16: ('Pope Gregory II', 'Boniface',                      '732',        732, 732, 732),
    17: ('Leoba', 'Boniface',                                'soon after 732', 733, 732, 735),
    18: ('Boniface', 'Abbess Eadburga',                      '735-6',      735, 735, 736),
    19: ('Boniface', 'Archbishop Nothelm of Canterbury',     '735',        735, 735, 735),
    20: ('Boniface', 'Abbot Duddo',                          '735',        735, 735, 735),
    21: ('Boniface', 'Abbess Eadburga',                      '735',        735, 735, 735),
    22: ('Boniface', 'Monks of Fritzlar',                    '737-8',      738, 737, 738),
    23: ('Boniface', 'His disciples',                        '738',        738, 738, 738),
    24: ('Pope Gregory III', 'Boniface',                     '29 Oct 739', 739, 739, 739),
    25: ('Boniface', 'English clergy and faithful',          '738',        738, 738, 738),
    26: ('Boniface', 'Grifo, Mayor of the Palace',           '741',        741, 741, 741),
    27: ('Boniface', 'Pope Zacharias',                       '742',        742, 742, 742),
    28: ('Pope Zacharias', 'Boniface',                       'April 743',  743, 743, 743),
    29: ('Synod of 745', 'Pope Zacharias',                   '25 Oct 745', 745, 745, 745),
    30: ('Boniface', 'Bishop Daniel of Winchester',          '742-6',      744, 742, 746),
    31: ('Pope Zacharias', 'Boniface',                       'July 746',   746, 746, 746),
    32: ('Boniface', 'King Aethelbald of Mercia',            '746-7',      746, 746, 747),
    33: ('Boniface', 'Archbishop Egbert of York',            '747',        747, 747, 747),
    34: ('Boniface', 'Abbot Huetbert of Wearmouth',          '746-7',      747, 746, 747),
    35: ('Boniface', 'Archbishop Cuthbert of Canterbury',    '747',        747, 747, 747),
    36: ('Boniface', 'Pope Zacharias',                       '751',        751, 751, 751),
    37: ('Pope Zacharias', 'Fulda monastery',                'Nov 751',    751, 751, 751),
    38: ('Boniface', 'Archbishop Egbert of York',            '747-51',     749, 747, 751),
    39: ('Boniface', 'His associates',                       '752',        752, 751, 753),
    40: ('Boniface', 'Count Reginbert',                      '732-54',     743, 732, 754),
    41: ('Boniface', 'Leoba, Abbess of Bischofsheim',        '735-54',     743, 735, 754),
    42: ('Boniface', 'Unknown (serf commendation)',          '732-54',     743, 732, 754),
    43: ('Priest Wigbert', 'Monks of Glastonbury',           '732-54',     743, 732, 754),
    44: ('King Ethelbert of Kent', 'Boniface',               '748-54',     750, 748, 754),
    45: ('Boniface', 'King Pippin',                          '753',        753, 753, 753),
    46: ('Boniface', 'Pope Stephen II',                      '752',        752, 752, 752),
    47: ('Boniface', 'Pope Stephen II',                      '753',        753, 753, 753),
    48: ('Bishop Milret of Worcester', 'Lull',               '754-5',      754, 754, 755),
}


# ─────────────────────────────────────────────────────────────────────────────
# HTTP fetch
# ─────────────────────────────────────────────────────────────────────────────

def fetch_url(url, retries=3):
    """Fetch URL with retries."""
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
                print(f"  Failed to fetch {url}: {e}")
                return None
    return None


# ─────────────────────────────────────────────────────────────────────────────
# HTML parsing
# ─────────────────────────────────────────────────────────────────────────────

def clean_html_text(s):
    """Strip HTML tags and normalize whitespace from a fragment."""
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'&amp;', '&', s)
    s = re.sub(r'&lt;', '<', s)
    s = re.sub(r'&gt;', '>', s)
    s = re.sub(r'&quot;', '"', s)
    s = re.sub(r'&#160;|\xa0', ' ', s)
    s = re.sub(r'[ \t]+', ' ', s)
    s = s.replace('\n', ' ')
    return s.strip()


def parse_letters_from_html(html):
    """
    Parse all 48 letters from the Fordham Sourcebook page.

    Returns a dict: { letter_num: {'title': str, 'text': str} }

    Strategy:
      1. Locate the start of letter content (after the [65] page number marker,
         which marks the end of the introduction and TOC).
      2. Extract all <p> elements from that point.
      3. Each letter starts with a paragraph matching '^NN[. ] Title' where NN is 1-48.
      4. Collect all subsequent paragraphs until the next letter heading.
      5. Skip page-number markers like [67], [68], etc.
      6. Skip editorial/intro notes that appear in separate <p> elements between
         the heading and the letter text (identifiable as italicised bios).
    """
    # Find content start (after the [65] page number / end of intro)
    idx_start = html.find('[65]')
    if idx_start < 0:
        # Fallback: look for the first letter heading
        idx_start = 0
    content_html = html[idx_start:]

    # Extract all paragraph/heading elements
    elements = re.findall(
        r'(?:<p[^>]*>|<h[1-6][^>]*>)(.*?)(?:</p>|</h[1-6]>)',
        content_html,
        re.DOTALL
    )

    letters = {}
    current_num = None
    current_parts = []

    # Regex: letter heading: optional spaces, 1-2 digits, period or space, capital title
    heading_re = re.compile(r'^(\d{1,2})\s*[.]?\s+([A-Z].{10,})$')

    for raw in elements:
        text = clean_html_text(raw)
        if not text:
            continue

        # Skip bare page number markers like [65], [72], etc.
        if re.match(r'^\[\d+\]$', text):
            continue

        # Check if this is a letter heading
        m = heading_re.match(text)
        if m:
            num = int(m.group(1))
            if 1 <= num <= 48:
                # Save previous letter
                if current_num is not None:
                    body = '\n\n'.join(p for p in current_parts if p)
                    letters[current_num] = {
                        'title': letters[current_num]['title'],
                        'text': body.strip()
                    }
                current_num = num
                current_parts = []
                letters[num] = {'title': m.group(2).strip(), 'text': ''}
                continue

        # Accumulate body paragraphs for current letter
        if current_num is not None:
            # Skip Tangl citation markers like '(Tangl, 17)'
            if re.match(r'^\(Tangl,?\s*\d+\)$', text):
                continue
            # Skip the bare page numbers that sometimes appear inline
            text2 = re.sub(r'\[\d+\]', '', text).strip()
            if text2:
                current_parts.append(text2)

    # Don't forget the last letter
    if current_num is not None:
        body = '\n\n'.join(p for p in current_parts if p)
        letters[current_num]['text'] = body.strip()

    return letters


# ─────────────────────────────────────────────────────────────────────────────
# Database helpers
# ─────────────────────────────────────────────────────────────────────────────

def ensure_author(conn, name, name_latin, birth_year, death_year, role,
                  location, lat, lon, notes):
    """Insert author if not present; return id."""
    cur = conn.cursor()
    cur.execute('SELECT id FROM authors WHERE name = ?', (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute('''
        INSERT INTO authors
            (name, name_latin, birth_year, death_year, role, location, lat, lon, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, name_latin, birth_year, death_year, role, location, lat, lon, notes))
    conn.commit()
    return cur.lastrowid


def ensure_recipient(conn, name):
    """Return author id for recipient by name, or None if not found."""
    if not name:
        return None
    cur = conn.cursor()
    # Try exact match first
    cur.execute('SELECT id FROM authors WHERE name = ?', (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    # Try partial match on first word (e.g. 'Boniface' matches 'Boniface of Mainz')
    first = name.split()[0]
    cur.execute('SELECT id FROM authors WHERE name LIKE ?', (f'%{first}%',))
    row = cur.fetchone()
    if row:
        return row[0]
    return None


def ensure_collection(conn, slug, author_name, title, letter_count,
                       date_range, english_source_url, notes):
    """Insert collection metadata if not present."""
    cur = conn.cursor()
    cur.execute('SELECT id FROM collections WHERE slug = ?', (slug,))
    if cur.fetchone():
        conn.execute(
            "UPDATE collections SET scrape_status = 'in_progress' WHERE slug = ?",
            (slug,)
        )
        conn.commit()
        return
    cur.execute('''
        INSERT OR IGNORE INTO collections
            (slug, author_name, title, letter_count, date_range,
             english_source_url, scrape_status, notes)
        VALUES (?, ?, ?, ?, ?, ?, 'in_progress', ?)
    ''', (slug, author_name, title, letter_count, date_range,
          english_source_url, notes))
    conn.commit()


def upsert_letter(conn, slug, letter_num, ref_id, sender_id, recipient_id,
                  year_approx, year_min, year_max, subject, text, url):
    """Insert or update a letter."""
    cur = conn.cursor()
    cur.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
    existing = cur.fetchone()

    if existing:
        cur.execute('''
            UPDATE letters
            SET english_text = ?,
                translation_source = 'existing_fordham',
                translation_url = ?,
                subject_summary = ?,
                year_approx = ?,
                year_min = ?,
                year_max = ?,
                sender_id = ?,
                recipient_id = ?
            WHERE ref_id = ?
        ''', (text, url, subject, year_approx, year_min, year_max,
              sender_id, recipient_id, ref_id))
        conn.commit()
        return 'updated'
    else:
        cur.execute('''
            INSERT INTO letters
                (collection, letter_number, ref_id, sender_id, recipient_id,
                 year_approx, year_min, year_max,
                 subject_summary, english_text,
                 translation_source, translation_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'existing_fordham', ?)
        ''', (slug, letter_num, ref_id, sender_id, recipient_id,
              year_approx, year_min, year_max, subject, text, url))
        conn.commit()
        return 'inserted'


# ─────────────────────────────────────────────────────────────────────────────
# Main scraper
# ─────────────────────────────────────────────────────────────────────────────

def scrape_boniface(conn):
    print(f"\n{'='*60}")
    print("Scraping Letters of Saint Boniface (48 letters, 716-754 AD)")
    print(f"Source: {SOURCE_URL}")

    # Ensure collection metadata
    ensure_collection(
        conn, COLLECTION_SLUG,
        'Boniface',
        'Letters of Saint Boniface',
        48,
        '716-754 AD',
        SOURCE_URL,
        ('48 selected letters from the ~150-letter Tangl corpus, translated '
         'by C.H. Talbot (Emerton 1940 as base). Source: Internet Medieval '
         'Sourcebook, Fordham University. US public domain. Covers Boniface\'s '
         'missionary career in Germany, Frankish church reform, and his '
         'correspondence with English abbesses, popes, and secular rulers.')
    )

    # Ensure Boniface as primary author
    sender_id = ensure_author(
        conn,
        'Boniface',
        'Bonifacius (Wynfrith)',
        672, 754,
        'missionary-bishop',
        'Mainz, Germany',
        50.0, 8.27,
        ('Anglo-Saxon missionary bishop (born Wynfrith in Wessex, c.672-675). '
         'Known as the "Apostle of the Germans." Organized the Frankish church '
         'under papal authority; established monasteries including Fulda. '
         'Martyred in Frisia 754. ~150 letters survive (Tangl edition, 1919).')
    )
    print(f"  Boniface author id: {sender_id}")

    # Fetch the page
    print(f"\n  Fetching {SOURCE_URL} ...")
    time.sleep(DELAY)
    html = fetch_url(SOURCE_URL)
    if not html:
        print("  ERROR: Could not fetch source page.")
        return 0

    print(f"  Fetched {len(html):,} bytes")

    # Parse letters
    letters = parse_letters_from_html(html)
    print(f"  Parsed {len(letters)} letters from HTML")

    inserted = updated = skipped = 0

    for letter_num in range(1, 49):
        ref_id = f'boniface.ep.{letter_num}'
        meta = LETTER_META.get(letter_num)
        if not meta:
            print(f"  Letter {letter_num}: no metadata, skipping")
            skipped += 1
            continue

        sender_name, recipient_name, date_str, year_approx, year_min, year_max = meta

        # Resolve sender id: if not Boniface himself, look up or leave as None
        if sender_name == 'Boniface':
            this_sender_id = sender_id
        else:
            this_sender_id = ensure_recipient(conn, sender_name)

        # Resolve recipient id
        recipient_id = ensure_recipient(conn, recipient_name)

        parsed = letters.get(letter_num)
        if not parsed or not parsed.get('text') or len(parsed['text'].strip()) < 30:
            print(f"  Letter {letter_num}: no text found in parsed output, skipping")
            skipped += 1
            continue

        title = parsed['title']
        text = parsed['text']
        # Trim title to subject summary (strip date from end if present)
        subject = re.sub(r'\s*\([^)]+\)\s*$', '', title).strip()[:250]

        result = upsert_letter(
            conn, COLLECTION_SLUG, letter_num, ref_id,
            this_sender_id, recipient_id,
            year_approx, year_min, year_max,
            subject, text, SOURCE_URL
        )

        if result == 'inserted':
            inserted += 1
        else:
            updated += 1

        # Progress
        if (inserted + updated) % 10 == 0 and (inserted + updated) > 0:
            print(f"  Progress: {inserted + updated} letters stored ...")

    conn.commit()

    # Mark collection complete
    conn.execute(
        "UPDATE collections SET scrape_status = 'complete', letter_count = ? WHERE slug = ?",
        (inserted + updated, COLLECTION_SLUG)
    )
    conn.commit()

    print(f"\n  Done: {inserted} inserted, {updated} updated, {skipped} skipped")
    return inserted + updated + skipped


def print_summary(conn):
    cur = conn.cursor()
    cur.execute('''
        SELECT COUNT(*),
               SUM(CASE WHEN english_text IS NOT NULL THEN 1 ELSE 0 END)
        FROM letters WHERE collection = ?
    ''', (COLLECTION_SLUG,))
    total, with_text = cur.fetchone()
    print(f"\nBoniface summary: {total} letters total, {with_text} with English text")

    cur.execute('''
        SELECT MIN(year_approx), MAX(year_approx)
        FROM letters WHERE collection = ? AND year_approx IS NOT NULL
    ''', (COLLECTION_SLUG,))
    row = cur.fetchone()
    if row and row[0]:
        print(f"  Date range: {row[0]} – {row[1]} AD")

    # Sample letter
    cur.execute('''
        SELECT letter_number, subject_summary,
               SUBSTR(english_text, 1, 120)
        FROM letters WHERE collection = ?
        ORDER BY letter_number LIMIT 3
    ''', (COLLECTION_SLUG,))
    print("\n  Sample letters:")
    for row in cur.fetchall():
        print(f"    Letter {row[0]}: {row[1]}")
        print(f"      \"{row[2]}...\"")


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    scrape_boniface(conn)
    print_summary(conn)
    conn.close()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Scrape English translations of Emperor Julian ("the Apostate")'s letters
(~83 letters total, c.355-363 AD) from Tertullian.org.

Source — W. C. Wright translation (1923), Loeb Classical Library Vol. 3:
  Letters 1-73  (authentic): https://www.tertullian.org/fathers/julian_apostate_letters_1_trans.htm
  Letters 74-83 (apocryphal): https://www.tertullian.org/fathers/julian_apostate_letters_2_spurious.htm

Both sources are single-page HTML files with each letter delimited by
an <h3> heading: "N. To RECIPIENT [DATE Location]"

Author: Flavius Claudius Julianus Augustus (331-363 AD)
Role: Roman Emperor (361-363), pagan philosopher-emperor
Period: Letters c.355-363 AD
"""

import sqlite3
import os
import re
import time
import urllib.request
from html.parser import HTMLParser

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
DELAY = 0.5  # seconds between requests

SOURCES = [
    {
        'url': 'https://www.tertullian.org/fathers/julian_apostate_letters_1_trans.htm',
        'label': 'authentic (1-73)',
        'spurious': False,
    },
    {
        'url': 'https://www.tertullian.org/fathers/julian_apostate_letters_2_spurious.htm',
        'label': 'apocryphal (74-83)',
        'spurious': True,
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# HTML parser — extract all text from page body, preserving block structure
# ─────────────────────────────────────────────────────────────────────────────

class BodyTextExtractor(HTMLParser):
    """Extract all text from HTML body, skip script/style/nav."""

    def __init__(self):
        super().__init__()
        self.parts = []
        self.in_body = False
        self.skip_depth = 0
        self.skip_tags = {'script', 'style', 'nav', 'header', 'footer'}

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.in_body = True
        if tag in self.skip_tags:
            self.skip_depth += 1
        if self.in_body and self.skip_depth == 0:
            if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'li', 'br', 'blockquote'):
                self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.skip_depth = max(0, self.skip_depth - 1)
        if self.in_body and self.skip_depth == 0:
            if tag in ('p', 'h3', 'h4', 'li', 'blockquote'):
                self.parts.append('\n')

    def handle_data(self, data):
        if self.in_body and self.skip_depth == 0:
            self.parts.append(data)

    def get_text(self):
        text = ''.join(self.parts)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


def extract_letters_from_page(html):
    """
    Parse a Tertullian.org Julian letters page.
    Each letter starts with an <h3> like:
        "N.&nbsp;To Priscus 1&nbsp;[359 AD From Gaul]"
    Returns list of dicts:
        {number, recipient, date_str, year_approx, origin_place, text, spurious}
    """
    parser = BodyTextExtractor()
    parser.feed(html)
    full_text = parser.get_text()

    # Split on lines that look like letter headers: number followed by period and recipient
    # Pattern: line starting with integer, period/dot, whitespace, then content
    # We re-split based on h3 pattern markers in the raw text
    # After parsing, h3 content becomes a newline-preceded line like "\n7. To Someone [date]\n"
    letter_sections = re.split(
        r'\n(\d{1,3})\.\s+',
        full_text
    )

    # letter_sections = [preamble, num1, content1, num2, content2, ...]
    letters = []
    for i in range(1, len(letter_sections), 2):
        num_str = letter_sections[i].strip()
        content = letter_sections[i + 1] if i + 1 < len(letter_sections) else ''

        try:
            letter_num = int(num_str)
        except ValueError:
            continue

        # First line of content is the recipient + date header
        lines = content.strip().split('\n')
        header_line = lines[0].strip() if lines else ''

        # Parse recipient and date from header:
        # "To Priscus 1 [359 AD From Gaul]"  or
        # "The Emperor Julian Caesar...to the People of Alexandria [362, Jan. ...]"
        recipient = None
        date_str = None
        year_approx = None
        origin_place = None

        # Extract bracketed date string
        date_match = re.search(r'\[([^\]]+)\]', header_line)
        if date_match:
            date_str = date_match.group(1).strip()
            # Extract year from date string
            year_match = re.search(r'\b(3[0-6]\d)\b', date_str)
            if year_match:
                year_approx = int(year_match.group(1))
            # Extract place (last significant word/phrase after year)
            place_match = re.search(
                r'(?:from\s+|at\s+|[Ff]rom\s+)?([A-Z][a-zA-Z]+(?:\s+[a-zA-Z]+)?)\s*\]',
                date_str
            )
            if place_match:
                origin_place = place_match.group(1).strip()

        # Extract recipient from header line (before the bracket)
        header_no_date = re.sub(r'\[.*?\]', '', header_line).strip()
        # Strip leading footnote numbers
        header_no_date = re.sub(r'\s*\d+\s*$', '', header_no_date).strip()

        # "To NAME" pattern
        to_match = re.match(r'^To\s+(.+?)(?:\s*\d+\s*)?$', header_no_date, re.IGNORECASE)
        if to_match:
            recipient = to_match.group(1).strip()
            # Remove trailing footnote digit(s)
            recipient = re.sub(r'\s*\d+\s*$', '', recipient).strip()
        elif header_no_date:
            # Use full header as recipient label (edicts, open letters, etc.)
            recipient = header_no_date[:100]

        # Body text = everything after the header line
        body_lines = lines[1:] if len(lines) > 1 else []
        body_text = '\n'.join(body_lines).strip()

        # Skip footnote-only entries (very short)
        if len(body_text) < 30:
            continue

        letters.append({
            'number': letter_num,
            'recipient': recipient,
            'date_str': date_str,
            'year_approx': year_approx,
            'origin_place': origin_place,
            'header': header_line[:200],
            'text': (header_line + '\n\n' + body_text).strip(),
        })

    return letters


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
# Database helpers
# ─────────────────────────────────────────────────────────────────────────────

def ensure_author(conn, name, name_latin, birth_year, death_year, role, location, notes):
    cur = conn.cursor()
    cur.execute('SELECT id FROM authors WHERE name = ?', (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute('''
        INSERT INTO authors (name, name_latin, birth_year, death_year, role, location, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, name_latin, birth_year, death_year, role, location, notes))
    conn.commit()
    return cur.lastrowid


def ensure_collection(conn, slug, author_name, title, letter_count, date_range,
                       english_source_url, notes):
    cur = conn.cursor()
    cur.execute('SELECT id FROM collections WHERE slug = ?', (slug,))
    if cur.fetchone():
        return
    cur.execute('''
        INSERT OR IGNORE INTO collections
            (slug, author_name, title, letter_count, date_range,
             english_source_url, scrape_status, notes)
        VALUES (?, ?, ?, ?, ?, ?, 'in_progress', ?)
    ''', (slug, author_name, title, letter_count, date_range, english_source_url, notes))
    conn.commit()


def upsert_letter(conn, slug, letter_num, ref_id, sender_id,
                  recipient_name, year_approx, origin_place,
                  subject, text, url, notes_extra=None):
    cur = conn.cursor()

    # Try to resolve recipient
    recipient_id = None
    if recipient_name:
        clean_recip = re.sub(r'\s*\d+\s*$', '', recipient_name).strip()
        cur.execute('SELECT id FROM authors WHERE name LIKE ?', (f'%{clean_recip[:20]}%',))
        row = cur.fetchone()
        if row:
            recipient_id = row[0]

    cur.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
    existing = cur.fetchone()

    if existing:
        cur.execute('''
            UPDATE letters SET english_text = ?, translation_source = 'existing_tertullian',
                translation_url = ?, subject_summary = ?, year_approx = ?,
                origin_place = ?
            WHERE ref_id = ?
        ''', (text, url, subject, year_approx, origin_place, ref_id))
        return 'updated'
    else:
        cur.execute('''
            INSERT INTO letters
                (collection, letter_number, ref_id, sender_id, recipient_id,
                 year_approx, origin_place, subject_summary,
                 english_text, translation_source, translation_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'existing_tertullian', ?)
        ''', (slug, letter_num, ref_id, sender_id, recipient_id,
              year_approx, origin_place, subject, text, url))
        return 'inserted'


# ─────────────────────────────────────────────────────────────────────────────
# Main scraper
# ─────────────────────────────────────────────────────────────────────────────

def scrape_julian(conn):
    SLUG = 'julian_emperor'

    print(f"\n{'='*60}")
    print("Scraping Emperor Julian ('the Apostate') letters (~83, c.355-363 AD)")
    print(f"Source: Tertullian.org — W.C. Wright translation (1923, Loeb)")

    ensure_collection(
        conn, SLUG,
        'Julian the Apostate',
        'Epistulae',
        83,
        'c.355-363 AD',
        SOURCES[0]['url'],
        ('W. C. Wright translation (1923), Loeb Classical Library Vol. 3. '
         'Letters 1-73 authentic; 74-83 apocryphal/spurious. '
         'Letters document Julian\'s attempt to restore Graeco-Roman paganism '
         'and his campaigns against Persia. Key correspondents: Libanius, '
         'Maximus of Ephesus, Priscus, Oribasius, Basil of Caesarea.')
    )

    sender_id = ensure_author(
        conn,
        'Julian the Apostate',
        'Flavius Claudius Iulianus Augustus',
        331, 363,
        'emperor',
        'Constantinople / Antioch / Persia',
        ('Last pagan Roman emperor (r.361-363 AD). Philosopher-emperor trained '
         'in Neoplatonism; attempted to reverse Christianization of the empire. '
         'Killed in battle against Persia near Samarra, June 26, 363. '
         '~83 letters survive, translated by W.C. Wright (1923).')
    )

    print(f"  Author id: {sender_id}")

    total_inserted = total_updated = total_skipped = 0

    for source in SOURCES:
        url = source['url']
        label = source['label']
        print(f"\n  Fetching {label} from {url}...")
        time.sleep(DELAY)

        html = fetch_url(url)
        if not html:
            print(f"  ERROR: Could not fetch {url}")
            continue

        letters = extract_letters_from_page(html)
        print(f"  Parsed {len(letters)} letters from page")

        inserted = updated = skipped = 0

        for letter in letters:
            letter_num = letter['number']
            ref_id = f'julian.ep.{letter_num}'

            # Skip if already has English text
            cur = conn.cursor()
            cur.execute(
                'SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL',
                (ref_id,)
            )
            if cur.fetchone():
                skipped += 1
                continue

            # Subject = first meaningful text line after header
            text_lines = letter['text'].split('\n')
            subject = None
            for line in text_lines[2:]:
                line = line.strip()
                if len(line) > 30:
                    subject = line[:200]
                    break
            if not subject and letter['header']:
                subject = letter['header'][:200]

            result = upsert_letter(
                conn, SLUG, letter_num, ref_id,
                sender_id,
                letter['recipient'],
                letter['year_approx'],
                letter['origin_place'],
                subject,
                letter['text'],
                url
            )

            if result == 'inserted':
                inserted += 1
            else:
                updated += 1

            if (inserted + updated) % 25 == 0 and (inserted + updated) > 0:
                conn.commit()
                print(f"  Progress: {inserted + updated} stored...")

        conn.commit()
        print(f"  {label}: {inserted} inserted, {updated} updated, {skipped} already present")
        total_inserted += inserted
        total_updated += updated
        total_skipped += skipped

    # Mark collection complete
    conn.execute("UPDATE collections SET scrape_status = 'complete' WHERE slug = ?", (SLUG,))
    conn.commit()

    print(f"\n  Done Julian: {total_inserted} inserted, {total_updated} updated, "
          f"{total_skipped} already present")
    return total_inserted + total_updated + total_skipped


def print_summary(conn):
    cur = conn.cursor()
    cur.execute('''
        SELECT COUNT(*), SUM(CASE WHEN english_text IS NOT NULL THEN 1 ELSE 0 END)
        FROM letters WHERE collection = 'julian_emperor'
    ''')
    total, with_text = cur.fetchone()
    print(f"\nJulian summary: {total} letters total, {with_text} with English text")

    cur.execute('''
        SELECT MIN(year_approx), MAX(year_approx)
        FROM letters WHERE collection = 'julian_emperor' AND year_approx IS NOT NULL
    ''')
    row = cur.fetchone()
    if row and row[0]:
        print(f"  Date range: {row[0]} – {row[1]} AD")

    cur.execute('''
        SELECT letter_number, subject_summary, year_approx
        FROM letters WHERE collection = 'julian_emperor'
        ORDER BY letter_number LIMIT 5
    ''')
    print("  First 5 letters:")
    for row in cur.fetchall():
        print(f"    #{row[0]} ({row[2]}) — {str(row[1])[:80]}")


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    scrape_julian(conn)
    print_summary(conn)
    conn.close()


if __name__ == '__main__':
    main()

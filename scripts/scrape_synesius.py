#!/usr/bin/env python3
"""
Scrape English translations of Synesius of Cyrene's letters (~159 letters, c.400 AD)
from Livius.org (Jona Lendering's translations, scholarly English).

Source index: https://www.livius.org/sources/content/synesius/
Individual letters: https://www.livius.org/sources/content/synesius/synesius-letter-NNN/
Letter 057 position: https://www.livius.org/sources/content/synesius/synesius-against-andronicus-letter-057/

Letters are stored in a single sequence (no books), numbered 1-159.
Note: Letter 57 is titled "Against Andronicus" but is counted as letter 57 in sequence.

Author: Synesius of Cyrene (c.370-c.413 AD)
Role: Neo-Platonic philosopher, bishop of Ptolemais (Cyrenaica/Libya)
Period: ~395-413 AD (letters span roughly this range)
"""

import sqlite3
import os
import re
import time
import urllib.request
from html.parser import HTMLParser

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
DELAY = 0.5  # seconds between requests

BASE_URL = 'https://www.livius.org/sources/content/synesius/'
LETTER_URL_TEMPLATE = 'https://www.livius.org/sources/content/synesius/synesius-letter-{:03d}/'
LETTER_057_URL = 'https://www.livius.org/sources/content/synesius/synesius-against-andronicus-letter-057/'

TOTAL_LETTERS = 159  # letters 1-159, with 57 having a special URL


# ─────────────────────────────────────────────────────────────────────────────
# HTML parser for Livius.org article pages
# ─────────────────────────────────────────────────────────────────────────────

class LiviusArticleParser(HTMLParser):
    """
    Extract the main article text from a Livius.org letter page.
    The content lives in <article> or in the main <div class="entry-content">.
    We skip nav, header, footer, sidebar, and script/style tags.
    """

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.depth = 0          # depth inside article/entry-content
        self.in_article = False
        self.skip_depth = 0     # skip nav/header/footer/script/style
        self.skip_tags = {'script', 'style', 'nav', 'header', 'footer', 'aside'}
        self.block_tags = {'p', 'h1', 'h2', 'h3', 'h4', 'li', 'blockquote', 'div'}
        self.recipient = None
        self.date_approx = None
        self._last_h3 = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get('class', '')

        # Detect article / entry-content container
        if tag == 'article' or (tag == 'div' and 'entry-content' in cls):
            self.in_article = True
            self.depth += 1
            return
        if self.in_article and tag not in self.skip_tags:
            self.depth += 1  # crude — we track being inside article

        if tag in self.skip_tags:
            self.skip_depth += 1

        if self.in_article and self.skip_depth == 0:
            if tag in ('p', 'h2', 'h3', 'h4', 'li'):
                self.text_parts.append('\n')
            if tag == 'br':
                self.text_parts.append('\n')

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.skip_depth = max(0, self.skip_depth - 1)
        if self.in_article:
            if tag in ('p', 'h2', 'h3', 'h4', 'li', 'blockquote'):
                self.text_parts.append('\n')

    def handle_data(self, data):
        if self.in_article and self.skip_depth == 0:
            self.text_parts.append(data)

    def get_text(self):
        text = ''.join(self.text_parts)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


def parse_livius_letter(html, letter_num):
    """
    Parse a Livius.org Synesius letter page.

    Page structure (inside <article>):
      1. Shared bio paragraph ("Synesius of Cyrene (c.370-c.413)...")
      2. Context paragraph specific to this letter (date, addressee, translator credit)
         — ends with "offered here in the translation by A. Fitzgerald."
      3. "Letter N: TITLE" heading
      4. Numbered sections "[1] To RECIPIENT\n  letter body..."
      5. Footer ("This page was created in...")

    We extract from the "Letter N:" marker onward, dropping the shared intro.
    Returns dict with: text, recipient, date_approx, subject.
    """
    # Extract article content
    art_match = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
    if art_match:
        raw = art_match.group(1)
    else:
        raw = html

    # Strip all HTML tags to plain text
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&[a-z]+;', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    # Find "Letter N:" marker — the actual letter starts here
    # Matches: "Letter 10: Losing contact..." or "Letter 001: ..."
    letter_marker = re.search(
        rf'(Letter\s+{letter_num}\s*[:\-]\s*[^\n]{{2,100}})',
        text, re.IGNORECASE
    )
    if letter_marker:
        text = text[letter_marker.start():]
    else:
        # Fallback: drop everything before "[1]" (first section marker)
        section1 = re.search(r'\[1\]', text)
        if section1:
            text = text[max(0, section1.start() - 50):]

    # Drop footer ("This page was created in...")
    footer_match = re.search(r'This page was created in', text)
    if footer_match:
        text = text[:footer_match.start()].strip()

    text = re.sub(r'\n{3,}', '\n\n', text).strip()

    # ── Extract metadata ──
    recipient = None
    date_approx = None
    subject = None

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    for line in lines[:10]:
        # "Letter N: TITLE" — subject
        m = re.match(r'^Letter\s+\d+\s*[:\-]\s*(.+)$', line, re.IGNORECASE)
        if m and not subject:
            subject = m.group(1).strip()[:200]

        # "[1]  To NAME" or "To NAME" recipient line
        m = re.match(r'^(?:\[1\]\s*)?To\s+([A-Z][a-zA-Z\s\-]+?)(?:\s+note|\s*\[|\,|$)', line)
        if m and not recipient:
            recipient = m.group(1).strip()

    # Date from intro paragraph (context-specific paragraph before the letter starts)
    # Look for "was written in NNN" or "written in NNN" patterns only
    date_match = re.search(
        r'(?:was written in|written in|written around|dates? (?:from|to))\s*(3\d\d|4[01]\d)',
        html, re.IGNORECASE
    )
    if date_match:
        try:
            date_approx = int(date_match.group(1))
        except Exception:
            pass

    # Fallback subject
    if not subject:
        for line in lines[:5]:
            if len(line) > 20:
                subject = line[:200]
                break

    return {
        'text': text,
        'recipient': recipient,
        'date_approx': date_approx,
        'subject': subject,
    }


# ─────────────────────────────────────────────────────────────────────────────
# HTTP fetch
# ─────────────────────────────────────────────────────────────────────────────

def fetch_url(url, retries=3):
    """Fetch URL with retries and polite delay."""
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
    """Insert author if not present; return id."""
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
    """Insert collection metadata if not present."""
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
                  recipient_name, date_approx, subject, text, url):
    """Insert or update a letter, looking up recipient author id."""
    cur = conn.cursor()

    # Try to resolve recipient to an authors row
    recipient_id = None
    if recipient_name:
        cur.execute('SELECT id FROM authors WHERE name LIKE ?', (f'%{recipient_name}%',))
        row = cur.fetchone()
        if row:
            recipient_id = row[0]

    cur.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
    existing = cur.fetchone()

    if existing:
        cur.execute('''
            UPDATE letters SET english_text = ?, translation_source = 'existing_livius',
                translation_url = ?, subject_summary = ?, year_approx = ?
            WHERE ref_id = ?
        ''', (text, url, subject, date_approx, ref_id))
        return 'updated'
    else:
        cur.execute('''
            INSERT INTO letters
                (collection, letter_number, ref_id, sender_id, recipient_id,
                 year_approx, subject_summary, english_text,
                 translation_source, translation_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'existing_livius', ?)
        ''', (slug, letter_num, ref_id, sender_id, recipient_id,
              date_approx, subject, text, url))
        return 'inserted'


# ─────────────────────────────────────────────────────────────────────────────
# Main scraper
# ─────────────────────────────────────────────────────────────────────────────

def scrape_synesius(conn):
    SLUG = 'synesius_cyrene'

    print(f"\n{'='*60}")
    print("Scraping Synesius of Cyrene (~159 letters, c.395-413 AD)")
    print(f"Source: {BASE_URL}")

    # Ensure collection metadata
    ensure_collection(
        conn, SLUG,
        'Synesius of Cyrene',
        'Epistulae',
        159,
        'c.395-413 AD',
        BASE_URL,
        ('English translations by Jona Lendering via Livius.org. '
         'Letters cover the collapse of Roman Africa, Barbarian invasions, '
         'Neoplatonic philosophy, and episcopal governance in Ptolemais (Cyrenaica).')
    )

    # Ensure author
    sender_id = ensure_author(
        conn,
        'Synesius of Cyrene',
        'Synesius Cyrenensis',
        370, 413,
        'philosopher-bishop',
        'Ptolemais, Cyrenaica (Libya)',
        ('Neo-Platonic philosopher and bishop of Ptolemais. '
         'Pupil of Hypatia in Alexandria. His ~159 letters are a vivid '
         'window into the collapse of Roman Africa c.395-413 AD.')
    )

    print(f"  Author id: {sender_id}")

    inserted = updated = skipped = 0

    for letter_num in range(1, TOTAL_LETTERS + 1):
        # Build ref_id and URL
        ref_id = f'synesius.ep.{letter_num}'
        if letter_num == 57:
            url = LETTER_057_URL
        else:
            url = LETTER_URL_TEMPLATE.format(letter_num)

        # Re-fetch all letters to get corrected dates and text
        # (skip only if year_approx is already set to a valid letter date, not the birth year)
        cur = conn.cursor()
        cur.execute(
            'SELECT id, year_approx, english_text FROM letters WHERE ref_id = ?',
            (ref_id,)
        )
        row = cur.fetchone()
        # 370 is Synesius's birth year — indicates date parsing failed on prior run
        already_good = (
            row and row[2]
            and not row[2].startswith('Synesius of Cyrene (c.370')
            and row[1] is not None
            and row[1] != 370
        )
        if already_good:
            skipped += 1
            continue

        time.sleep(DELAY)

        html = fetch_url(url)
        if not html:
            print(f"  Letter {letter_num}: fetch failed, skipping")
            continue

        parsed = parse_livius_letter(html, letter_num)

        if not parsed['text'] or len(parsed['text']) < 50:
            print(f"  Letter {letter_num}: text too short, skipping")
            continue

        result = upsert_letter(
            conn, SLUG, letter_num, ref_id,
            sender_id,
            parsed['recipient'],
            parsed['date_approx'],
            parsed['subject'],
            parsed['text'],
            url
        )

        if result == 'inserted':
            inserted += 1
        else:
            updated += 1

        if (inserted + updated) % 20 == 0:
            conn.commit()
            print(f"  Progress: {inserted + updated} letters stored (skipped existing: {skipped})...")

    conn.commit()

    # Mark collection complete
    conn.execute("UPDATE collections SET scrape_status = 'complete' WHERE slug = ?", (SLUG,))
    conn.commit()

    print(f"\n  Done Synesius: {inserted} inserted, {updated} updated, {skipped} already present")
    return inserted + updated + skipped


def print_summary(conn):
    cur = conn.cursor()
    cur.execute('''
        SELECT COUNT(*), SUM(CASE WHEN english_text IS NOT NULL THEN 1 ELSE 0 END)
        FROM letters WHERE collection = 'synesius_cyrene'
    ''')
    total, with_text = cur.fetchone()
    print(f"\nSynesius summary: {total} letters total, {with_text} with English text")

    cur.execute('''
        SELECT MIN(year_approx), MAX(year_approx)
        FROM letters WHERE collection = 'synesius_cyrene' AND year_approx IS NOT NULL
    ''')
    row = cur.fetchone()
    if row and row[0]:
        print(f"  Date range: {row[0]} – {row[1]} AD")


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    scrape_synesius(conn)
    print_summary(conn)
    conn.close()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Scrape Latin original texts for Augustine, Jerome, and other collections.

Sources discovered:
- Augustine (260 missing): augustinus.it — individual letter pages with clean Latin HTML.
  URL pattern: https://www.augustinus.it/latino/lettere/lettera_NNN_testo.htm
  Contains 270 letters (1-270); the site uses sequential file numbers but the actual
  Epistola number is in the HTML title. We match by Epistola number to DB letter_number.

- Jerome (131 missing): Latin Library jerome/epistulae.html has only letters 1–10.
  URL: https://www.thelatinlibrary.com/jerome/epistulae.html
  Letters identified by anchor tags (#EP1 ... #EP10).

- Cyprian (82 missing), Gregory Great (421 missing), Leo Great (73 missing):
  No clean HTML source located. Migne PL PDFs exist on Documenta Catholica Omnia
  but have severe OCR artifacts in a two-column scholarly layout — not suitable.
  These collections are skipped in this pass.

Strategy:
  1. For each source, fetch pages with 1-second polite delay.
  2. Extract the actual letter number from the HTML.
  3. Match to DB records by collection + letter_number.
  4. Update latin_text where currently NULL or very short (< 100 chars).
  5. Report totals by collection at the end.

Run with: python3 scripts/scrape_latin_originals.py
"""

import sqlite3
import os
import re
import time
import urllib.request
from html.parser import HTMLParser

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
POLITE_DELAY = 1.0  # seconds between requests — be gentle to small sites


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

class BodyTextExtractor(HTMLParser):
    """Extract visible text from HTML, skipping script/style/head elements."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self._in_body = False
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self._in_body = True
        if tag in ('script', 'style', 'head'):
            self._skip_depth += 1
        if tag in ('p', 'h3', 'h4', 'h5', 'br', 'div'):
            self.text_parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'head'):
            self._skip_depth -= 1
        if tag in ('p', 'div'):
            self.text_parts.append('\n')

    def handle_data(self, data):
        if self._in_body and self._skip_depth <= 0:
            self.text_parts.append(data)

    def get_text(self):
        raw = ''.join(self.text_parts)
        # Collapse excessive blank lines
        return re.sub(r'\n{3,}', '\n\n', raw).strip()


def fetch_url(url, encoding='utf-8', retries=3):
    """Fetch a URL and return decoded HTML text, or None on failure."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'RomanLettersResearch/1.0 (academic research; github.com/CraigVG/roman-letters-network)'
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                # Use Content-Type charset if provided, else fall back to given encoding
                ct = resp.headers.get('Content-Type', '')
                if 'charset=' in ct:
                    enc = ct.split('charset=')[-1].strip().split(';')[0].strip()
                else:
                    enc = encoding
                return resp.read().decode(enc, errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
            else:
                print(f"    [WARN] Failed to fetch {url}: {e}")
                return None
    return None


def clean_latin_text(text):
    """Basic cleanup of extracted Latin text."""
    # Remove JS/analytics snippets that may have leaked through
    text = re.sub(r'_gaq\s*=.*?trackPageview.*?\n', '', text, flags=re.DOTALL)
    text = re.sub(r'var\s+_gaq.*', '', text, flags=re.DOTALL)
    # Strip excessive whitespace / blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def needs_latin(row_latin_text):
    """Return True if this record needs Latin text (NULL or very short)."""
    if row_latin_text is None:
        return True
    return len(row_latin_text) < 100


# ---------------------------------------------------------------------------
# Augustine — augustinus.it
# ---------------------------------------------------------------------------
# The site hosts 270 individual Latin letter pages, each with a clear
# <H3>EPISTOLA N</H3> header identifying the actual epistola number.
# The file number (NNN in the URL) does NOT always equal the epistola number
# because the site includes some letters that skipped numbers (like starred
# variants), so we always read the epistola number from the HTML.
#
# DB collections involved:
#   collection='augustine_hippo'  — letter_number = Epistola number (1..269)
#   AND letter_number = Epistola number + 50000 for the duplicate batch
#     (ref_id = 'augustine.ep.N'), so Ep.1 = letter_number 50001, etc.

AUGUSTINE_BASE_URL = 'https://www.augustinus.it/latino/lettere/'
# The site has files lettera_001 through lettera_278 (covering Epistolae 1-270).
# Files 280+ begin a second pass of the same letters (different edition/text).
# We scan up to 278 to get the first unique occurrence of each epistola.
AUGUSTINE_FILE_COUNT = 278


def scrape_augustine(conn):
    """Scrape Augustine letters from augustinus.it and update the DB."""
    print("\n=== AUGUSTINE (augustinus.it) ===")
    cursor = conn.cursor()

    # Build a lookup: ep_number -> list of row ids that need Latin
    # For letter_number < 1000: ep_number = letter_number
    # For letter_number >= 50000: ep_number = letter_number - 50000
    cursor.execute("""
        SELECT id, letter_number, latin_text
        FROM letters
        WHERE collection = 'augustine_hippo'
        ORDER BY letter_number
    """)
    rows = cursor.fetchall()

    # ep_number -> [(id, latin_text), ...]
    ep_to_ids = {}
    for row_id, letter_num, lat in rows:
        if letter_num < 1000:
            ep_num = letter_num
        elif letter_num >= 50000:
            ep_num = letter_num - 50000
        else:
            continue  # unexpected
        ep_to_ids.setdefault(ep_num, []).append((row_id, lat))

    updated = 0
    skipped_already_has = 0
    skipped_no_match = 0
    fetch_errors = 0

    for file_num in range(1, AUGUSTINE_FILE_COUNT + 1):
        url = f"{AUGUSTINE_BASE_URL}lettera_{file_num:03d}_testo.htm"
        html = fetch_url(url, encoding='windows-1252')
        time.sleep(POLITE_DELAY)

        if html is None:
            fetch_errors += 1
            continue

        # Extract actual Epistola number from HTML
        # <TITLE>Augustinus Hipponensis - Epistola N</TITLE>
        # or <H3 ...>EPISTOLA N</H3>
        ep_match = re.search(
            r'EPISTOLA\s+(\d+)',
            html,
            re.IGNORECASE
        )
        if not ep_match:
            # Try the title tag
            ep_match = re.search(r'Epistola\s+(\d+)', html[:500], re.IGNORECASE)
        if not ep_match:
            print(f"  [SKIP] file {file_num:03d}: could not find Epistola number")
            skipped_no_match += 1
            continue

        ep_num = int(ep_match.group(1))

        if ep_num not in ep_to_ids:
            skipped_no_match += 1
            continue

        # Check if any record for this ep_num needs Latin text
        target_rows = [(rid, lat) for rid, lat in ep_to_ids[ep_num] if needs_latin(lat)]
        if not target_rows:
            skipped_already_has += 1
            continue

        # Extract clean body text
        extractor = BodyTextExtractor()
        extractor.feed(html)
        raw_text = extractor.get_text()
        latin_text = clean_latin_text(raw_text)

        if len(latin_text) < 50:
            print(f"  [SKIP] Ep.{ep_num} (file {file_num:03d}): text too short ({len(latin_text)} chars)")
            skipped_no_match += 1
            continue

        # Update all matching records
        for row_id, _ in target_rows:
            cursor.execute("""
                UPDATE letters
                SET latin_text = ?, source_url = ?
                WHERE id = ?
            """, (latin_text, url, row_id))
            updated += 1

        if updated % 25 == 0:
            conn.commit()
            print(f"  ... {updated} Augustine letters updated so far")

    conn.commit()
    print(f"  Augustine result: {updated} updated, {skipped_already_has} already had Latin, "
          f"{skipped_no_match} no DB match, {fetch_errors} fetch errors")
    return updated


# ---------------------------------------------------------------------------
# Jerome — Latin Library (jerome/epistulae.html)
# ---------------------------------------------------------------------------
# The Latin Library has a single page with Jerome letters 1–10, each marked
# with an anchor <a name="EP1">, <a name="EP2">, etc., followed by the
# letter text until the next EP anchor.
#
# DB collection: collection='jerome', letter_number = 1..150

JEROME_URL = 'https://www.thelatinlibrary.com/jerome/epistulae.html'


def scrape_jerome(conn):
    """Scrape Jerome letters 1-10 from Latin Library."""
    print("\n=== JEROME (Latin Library) ===")
    cursor = conn.cursor()

    html = fetch_url(JEROME_URL, encoding='latin-1')
    if html is None:
        print("  Could not fetch Jerome page")
        return 0

    # Extract text between EP anchors.
    # The anchors look like <a name="EP1">, <a name="EP2">, etc.
    # Split on the full anchor tag — this produces:
    #   blocks[0] = preamble HTML
    #   blocks[1] = 'EP1', blocks[2] = content until next anchor
    #   blocks[3] = 'EP2', blocks[4] = content ...
    ep_blocks = re.split(r'<a\s+name=["\']?(EP\d+)["\']?\s*>', html, flags=re.IGNORECASE)

    updated = 0
    skipped_already_has = 0
    skipped_no_match = 0

    i = 1
    while i + 1 < len(ep_blocks):
        ep_tag = ep_blocks[i].strip()   # e.g. 'EP1'
        block_html = ep_blocks[i + 1]
        i += 2

        num_match = re.search(r'(\d+)', ep_tag)
        if not num_match:
            continue
        try:
            ep_num = int(num_match.group(1))
        except ValueError:
            continue

        # Extract text from this block's HTML
        # The block ends at the next EP anchor (already split) or page end
        extractor = BodyTextExtractor()
        # Wrap in a minimal HTML so the parser works correctly
        extractor.feed(f'<body>{block_html}</body>')
        raw_text = extractor.get_text()
        latin_text = clean_latin_text(raw_text)

        if len(latin_text) < 30:
            continue

        # Find matching DB record
        cursor.execute("""
            SELECT id, latin_text
            FROM letters
            WHERE collection = 'jerome' AND letter_number = ?
        """, (ep_num,))
        row = cursor.fetchone()

        if row is None:
            skipped_no_match += 1
            continue

        row_id, existing_latin = row
        if not needs_latin(existing_latin):
            skipped_already_has += 1
            continue

        cursor.execute("""
            UPDATE letters
            SET latin_text = ?, source_url = ?
            WHERE id = ?
        """, (latin_text, JEROME_URL, row_id))
        updated += 1

    conn.commit()
    print(f"  Jerome result: {updated} updated, {skipped_already_has} already had Latin, "
          f"{skipped_no_match} no DB match")
    return updated


# ---------------------------------------------------------------------------
# Cyprian — CSEL text via Latin Library (if available)
# ---------------------------------------------------------------------------
# Research found no clean HTML source for Cyprian's 65 epistulae.
# The Migne PL PDF on Documenta Catholica Omnia has severe OCR artifacts
# (two-column scholarly layout with apparatus mixed in) and is not suitable
# for automated extraction without significant post-processing.
#
# The Latin Library does NOT have a Cyprian epistulae page.
# CCEL only has the English translation.
#
# This function is a placeholder for future work.

def scrape_cyprian(conn):
    """Placeholder — no suitable HTML Latin source found for Cyprian."""
    print("\n=== CYPRIAN (skipped — no clean HTML source found) ===")
    print("  The Migne PL PDF on Documenta Catholica Omnia has severe OCR artifacts.")
    print("  Recommend using CSEL 3 (University press scan) or a clean digital edition.")
    return 0


# ---------------------------------------------------------------------------
# Gregory the Great — placeholder
# ---------------------------------------------------------------------------
# Research findings:
# - Latin Library: Only one letter (gregory7.html = Gregory VII, not Gregory I)
#   greg.html = one letter fragment (ep. IV.30 to Empress Constantina)
# - Documenta Catholica Omnia: Registri Epistolarum PDF exists in 04z/ directory
#   but is not publicly downloadable (only HTML stub page served).
# - MGH Registrum Epistularum: available at dmgh.de but not as scrape-friendly HTML.
# - The existing DB already has 435 Gregory letters with Latin from Archive.org.

def scrape_gregory(conn):
    """Placeholder — best sources require institutional access or PDF OCR."""
    print("\n=== GREGORY THE GREAT (skipped — 435 letters already have Latin) ===")
    print("  Remaining 421 gaps require MGH Registrum or PL 77 PDF extraction.")
    print("  The single public letter (greg.html) is letter IV.30 to Constantina.")
    # Could add the single greg.html letter here if desired
    return 0


# ---------------------------------------------------------------------------
# Leo the Great — placeholder
# ---------------------------------------------------------------------------
# Research findings:
# - Latin Library: leo.html = Leo of Naples (10th century, wrong person).
# - Documenta Catholica Omnia: Epistolae__MLT.pdf in 04z/ is not publicly
#   downloadable. Migne PL 54 PDF would need same two-column OCR parsing.

def scrape_leo(conn):
    """Placeholder — no clean HTML source found for Leo the Great."""
    print("\n=== LEO THE GREAT (skipped — no accessible clean HTML source) ===")
    print("  Migne PL 54 PDF requires OCR post-processing.")
    return 0


# ---------------------------------------------------------------------------
# Final report
# ---------------------------------------------------------------------------

def print_summary(conn):
    """Print updated Latin text coverage for target collections."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT collection,
               COUNT(*) as total,
               SUM(CASE WHEN latin_text IS NOT NULL AND length(latin_text) >= 100 THEN 1 ELSE 0 END) as has_latin,
               SUM(CASE WHEN latin_text IS NULL OR length(latin_text) < 100 THEN 1 ELSE 0 END) as missing_latin
        FROM letters
        WHERE collection IN ('augustine_hippo', 'jerome', 'gregory_great', 'leo_great', 'cyprian_carthage')
        GROUP BY collection
        ORDER BY collection
    """)
    print(f"\n{'Collection':<20} {'Total':>7} {'Has Latin':>10} {'Missing':>8}")
    print('-' * 48)
    for row in cursor.fetchall():
        pct = 100 * row[2] / row[1] if row[1] > 0 else 0
        print(f"{row[0]:<20} {row[1]:>7} {row[2]:>9} ({pct:.0f}%) {row[3]:>7}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Latin Original Text Scraper")
    print("=" * 60)
    print(f"Database: {os.path.abspath(DB_PATH)}")

    conn = sqlite3.connect(DB_PATH)

    # Initial state
    print("\n--- Initial Latin coverage (target collections) ---")
    print_summary(conn)

    totals = {}

    # 1. Augustine — best source, highest yield
    totals['augustine_hippo'] = scrape_augustine(conn)

    # 2. Jerome — Latin Library, 10 letters
    totals['jerome'] = scrape_jerome(conn)

    # 3. Cyprian — no suitable source
    totals['cyprian_carthage'] = scrape_cyprian(conn)

    # 4. Gregory the Great — mostly done from Archive.org
    totals['gregory_great'] = scrape_gregory(conn)

    # 5. Leo the Great — no suitable source
    totals['leo_great'] = scrape_leo(conn)

    # Final state
    print("\n--- Final Latin coverage ---")
    print_summary(conn)

    print("\n--- Summary of letters updated ---")
    grand_total = 0
    for collection, count in totals.items():
        if count > 0:
            print(f"  {collection}: {count} letters updated")
        grand_total += count
    print(f"\n  TOTAL updated: {grand_total} letters")

    conn.close()
    print("\nDone.")


if __name__ == '__main__':
    main()

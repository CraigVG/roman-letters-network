#!/usr/bin/env python3
"""
Scrape English translations of late antique letters from New Advent (Church Fathers).
New Advent hosts public domain translations from the Nicene and Post-Nicene Fathers series.

Collections available:
- Augustine: https://www.newadvent.org/fathers/1102.htm (letters index)
- Jerome: https://www.newadvent.org/fathers/3001.htm
- Ambrose: https://www.newadvent.org/fathers/3403.htm
- Gregory the Great: https://www.newadvent.org/fathers/3602.htm (Register)
- Leo the Great: https://www.newadvent.org/fathers/3604.htm
- Basil of Caesarea: https://www.newadvent.org/fathers/3202.htm
"""

import sqlite3
import os
import re
import time
import urllib.request
from html.parser import HTMLParser

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

# Map collection slug -> New Advent base URLs for individual letters
# New Advent typically uses sequential numbering: base + NN.htm
COLLECTIONS = {
    'augustine_hippo': {
        'index_url': 'https://www.newadvent.org/fathers/1102.htm',
        'base_url': 'https://www.newadvent.org/fathers/1102',
        'max_letters': 308,
    },
    'jerome': {
        'index_url': 'https://www.newadvent.org/fathers/3001.htm',
        'base_url': 'https://www.newadvent.org/fathers/3001',
        'max_letters': 154,
    },
    'ambrose_milan': {
        'index_url': 'https://www.newadvent.org/fathers/3403.htm',
        'base_url': 'https://www.newadvent.org/fathers/3403',
        'max_letters': 91,
    },
    'gregory_great': {
        'index_url': 'https://www.newadvent.org/fathers/3602.htm',
        'base_url': 'https://www.newadvent.org/fathers/3602',
        'max_letters': 854,
    },
    'leo_great': {
        'index_url': 'https://www.newadvent.org/fathers/3604.htm',
        'base_url': 'https://www.newadvent.org/fathers/3604',
        'max_letters': 173,
    },
    'basil_caesarea': {
        'index_url': 'https://www.newadvent.org/fathers/3202.htm',
        'base_url': 'https://www.newadvent.org/fathers/3202',
        'max_letters': 368,
    },
}


class SimpleHTMLTextExtractor(HTMLParser):
    """Extract text content from HTML, skipping navigation/footer."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_body = False
        self.skip_tags = {'script', 'style', 'nav', 'header', 'footer'}
        self.current_skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.current_skip += 1
        if tag == 'body':
            self.in_body = True
        if tag == 'p' or tag == 'br':
            self.text_parts.append('\n')

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.current_skip -= 1
        if tag == 'p':
            self.text_parts.append('\n')

    def handle_data(self, data):
        if self.in_body and self.current_skip <= 0:
            self.text_parts.append(data)

    def get_text(self):
        return ''.join(self.text_parts).strip()


def fetch_url(url, retries=3, delay=1.0):
    """Fetch URL content with retries and polite delay."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'RomanLettersResearch/1.0 (academic research project)'
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                print(f"  Failed to fetch {url}: {e}")
                return None
    return None


def extract_text_from_html(html):
    """Extract readable text from HTML."""
    parser = SimpleHTMLTextExtractor()
    parser.feed(html)
    text = parser.get_text()
    # Clean up excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def find_letter_links(index_html, base_url):
    """Parse an index page to find individual letter URLs."""
    # New Advent index pages have links like 1102001.htm, 1102002.htm etc.
    # Extract the numeric part of base_url
    base_num = base_url.rstrip('/').split('/')[-1]
    pattern = rf'{base_num}(\d+)\.htm'
    matches = re.findall(pattern, index_html)
    urls = []
    seen = set()
    for m in matches:
        if m not in seen:
            seen.add(m)
            urls.append((int(m), f"{base_url}{m}.htm"))
    urls.sort(key=lambda x: x[0])
    return urls


def parse_letter_header(text):
    """Try to extract sender/recipient info from letter text."""
    info = {'sender': None, 'recipient': None, 'subject': None}

    # Common patterns in New Advent translations:
    # "Letter I." or "Letter XLII."
    # "To Marcellinus" or "Augustine to Marcellinus"
    lines = text.split('\n')
    for line in lines[:15]:  # Check first 15 lines
        line = line.strip()
        if not line:
            continue

        # "To NAME" pattern
        to_match = re.match(r'^To\s+(.+?)[\.,\s]*$', line, re.IGNORECASE)
        if to_match:
            info['recipient'] = to_match.group(1).strip()

        # "FROM to TO" pattern
        from_to = re.match(r'^(\w[\w\s]*?)\s+to\s+(\w[\w\s]*?)[\.,\s]*$', line, re.IGNORECASE)
        if from_to:
            info['sender'] = from_to.group(1).strip()
            info['recipient'] = from_to.group(2).strip()

    # Build a subject from first substantive paragraph
    for line in lines[5:25]:
        line = line.strip()
        if len(line) > 50 and not line.startswith('Letter') and not line.startswith('To '):
            info['subject'] = line[:200]
            break

    return info


def scrape_collection(slug, config, conn):
    """Scrape all letters from a single New Advent collection."""
    cursor = conn.cursor()

    # Check what we already have
    cursor.execute('SELECT COUNT(*) FROM letters WHERE collection = ? AND english_text IS NOT NULL', (slug,))
    existing = cursor.fetchone()[0]
    if existing > 0:
        print(f"  Already have {existing} letters for {slug}, skipping existing...")

    print(f"\nScraping {slug} from {config['index_url']}...")

    # First, fetch the index to find all letter links
    index_html = fetch_url(config['index_url'])
    if not index_html:
        print(f"  Could not fetch index for {slug}")
        return 0

    letter_links = find_letter_links(index_html, config['base_url'])

    if not letter_links:
        # Try sequential numbering as fallback
        print(f"  No links found in index, trying sequential numbering...")
        letter_links = [(i, f"{config['base_url']}{i:03d}.htm") for i in range(1, min(config['max_letters'] + 1, 50))]

    print(f"  Found {len(letter_links)} letter links")

    count = 0
    for letter_num, url in letter_links:
        ref_id = f"{slug}.{letter_num}"

        # Skip if already scraped
        cursor.execute('SELECT id FROM letters WHERE ref_id = ? AND english_text IS NOT NULL', (ref_id,))
        if cursor.fetchone():
            count += 1
            continue

        # Polite delay
        time.sleep(0.5)

        html = fetch_url(url)
        if not html:
            continue

        text = extract_text_from_html(html)
        if len(text) < 50:
            continue

        info = parse_letter_header(text)

        # Look up or create sender
        sender_id = None
        cursor.execute('SELECT id FROM authors WHERE name = (SELECT author_name FROM collections WHERE slug = ?)', (slug,))
        row = cursor.fetchone()
        if row:
            sender_id = row[0]

        # Look up recipient if identified
        recipient_id = None
        if info['recipient']:
            cursor.execute('SELECT id FROM authors WHERE name LIKE ?', (f"%{info['recipient']}%",))
            row = cursor.fetchone()
            if row:
                recipient_id = row[0]

        cursor.execute('''
            INSERT OR REPLACE INTO letters
                (collection, letter_number, ref_id, sender_id, recipient_id,
                 subject_summary, english_text, translation_source, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'existing_newadvent', ?)
        ''', (slug, letter_num, ref_id, sender_id, recipient_id,
              info.get('subject'), text, url))

        count += 1
        if count % 25 == 0:
            conn.commit()
            print(f"  Scraped {count} letters...")

    conn.commit()

    # Update collection status
    cursor.execute("UPDATE collections SET scrape_status = 'complete' WHERE slug = ?", (slug,))
    conn.commit()

    print(f"  Done: {count} letters for {slug}")
    return count


def main():
    conn = sqlite3.connect(DB_PATH)
    total = 0

    for slug, config in COLLECTIONS.items():
        count = scrape_collection(slug, config, conn)
        total += count

    print(f"\n{'='*50}")
    print(f"Total letters scraped: {total}")

    # Show DB stats
    cursor = conn.cursor()
    cursor.execute('SELECT collection, COUNT(*) FROM letters GROUP BY collection')
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    conn.close()


if __name__ == '__main__':
    main()

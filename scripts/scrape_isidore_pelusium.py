#!/usr/bin/env python3
"""
Scrape English translations of Isidore of Pelusium's letters from Roger Pearse's blog.

Isidore of Pelusium (~360-435 AD): Egyptian monk and theologian at Pelusium on the Nile delta.
The largest letter collection from any Church Father (~2,000 letters survive).
He was a contemporary and critic of Cyril of Alexandria, correspondent with emperors,
bishops, monks, and officials across the Eastern Empire.

Available free English sources:
- Roger Pearse's blog (roger-pearse.com): ~70+ letters scattered across multiple posts
  These are commissioned draft translations, some by named translators
- Letters 1-14: first batch translated for Pearse
- Letters 27, 35-36: individual letters
- Letter 78: Letter to a soldier
- Letters 97-101: batch
- Letters 102-116: Clive Sweeting translation (2010, never formally published)
- Letters 212, 221, 310-311, 322, 448: scattered
- Letter 1106: to Cyril
- Letters 1214-1229, 1241, 1243-1246, 1285, 1382, 1582: large/later batch

Greek text: Migne Patrologia Graeca vol.78 (public domain scan on archive.org)
Critical edition: Pierre Evieux, Sources Chrétiennes 422 & 454 (1997) — letters 1-800+
"""

import sqlite3
import os
import re
import time
import urllib.request
from html.parser import HTMLParser

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
DELAY = 0.5

# All known Roger Pearse blog posts containing Isidore letter translations
# Format: (url, description)
SOURCES = [
    (
        'https://www.roger-pearse.com/weblog/2010/11/11/14-letters-of-isidore-of-pelusium/',
        'Letters 1-14'
    ),
    (
        'https://www.roger-pearse.com/weblog/2009/01/22/isidore-of-pelusium-some-newly-translated-letters/',
        'Letters 35, 310, 1106, 1582'
    ),
    (
        'https://www.roger-pearse.com/weblog/2009/02/07/isidore-of-pelusium-some-more-letters/',
        'Letters 311, 322'
    ),
    (
        'https://www.roger-pearse.com/weblog/2009/03/07/a-few-more-letters-of-isidore-of-pelusium/',
        'Letters 1214-1218'
    ),
    (
        'https://www.roger-pearse.com/weblog/2011/02/19/letters-97-101-of-isidore-of-pelusium/',
        'Letters 97-101'
    ),
    (
        'https://www.roger-pearse.com/weblog/2013/04/23/isidore-of-pelusium-letter-78/',
        'Letter 78'
    ),
    (
        'https://www.roger-pearse.com/weblog/2020/09/05/a-few-more-letters-of-isidore-of-pelusium-102-116/',
        'Letters 102-116 (Sweeting)'
    ),
    (
        'https://www.roger-pearse.com/weblog/2020/08/25/an-email-about-the-letters-of-isidore-of-pelusium/',
        'Letters inventory/some texts 1219-1229 etc.'
    ),
]

# Additional letters that may appear in comments or other posts
ADDITIONAL_SOURCES = [
    (
        'https://www.roger-pearse.com/weblog/2009/03/27/some-1843-translations-of-ancient-letters-including-isidore-of-pelusium/',
        '1843 Roberts translations'
    ),
    (
        'https://www.roger-pearse.com/weblog/2009/08/20/a-couple-more-letters-by-isidore-of-pelusium/',
        'Letters 1243-1246'
    ),
    (
        'https://www.roger-pearse.com/weblog/2009/08/19/a-bit-more-on-the-zosimus-affair/',
        'Letter 1285'
    ),
    (
        'https://www.roger-pearse.com/weblog/2010/02/19/styles-of-translation-an-example-from-isidore-of-pelusium/',
        'Letter 212'
    ),
    (
        'https://www.roger-pearse.com/weblog/2009/09/16/isidore-of-pelusium-on-romans-128-29/',
        'Letters 1245-1246'
    ),
    (
        'https://www.roger-pearse.com/weblog/2009/08/19/another-letter-to-zosimus-from-isidore-of-pelusium/',
        'Letter 1241'
    ),
]


class BlogTextParser(HTMLParser):
    """
    Extract the main article/post content from a WordPress blog post,
    separating it from navigation, sidebars, and comments.
    """

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_article = False
        self.article_depth = 0
        self.skip_tags = {'script', 'style', 'nav', 'header', 'footer'}
        self.skip_depth = 0
        self.tag_stack = []
        self.in_skip = False
        # Track div/section depth for article content
        self.article_class_patterns = [
            'entry-content', 'post-content', 'entry', 'post-entry',
            'article', 'hentry'
        ]
        self.capturing = False
        self.capture_depth = 0

    def handle_starttag(self, tag, attrs):
        self.tag_stack.append(tag)
        attr_dict = dict(attrs)

        if tag in self.skip_tags:
            self.skip_depth += 1
            return

        if self.skip_depth > 0:
            return

        # Check if this is the main article content div
        classes = attr_dict.get('class', '').lower()
        if not self.capturing:
            for pattern in self.article_class_patterns:
                if pattern in classes:
                    self.capturing = True
                    self.capture_depth = len(self.tag_stack)
                    break

        if self.capturing:
            if tag in ('p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'li'):
                self.text_parts.append('\n')

    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1] == tag:
            depth = len(self.tag_stack)
            self.tag_stack.pop()

            if tag in self.skip_tags:
                self.skip_depth = max(0, self.skip_depth - 1)
                return

            if self.capturing and depth <= self.capture_depth:
                self.capturing = False
                self.capture_depth = 0

            if self.capturing and tag in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'li'):
                self.text_parts.append('\n')

    def handle_data(self, data):
        if self.capturing and self.skip_depth == 0:
            self.text_parts.append(data)

    def get_text(self):
        text = ''.join(self.text_parts)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


def fetch_url(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'RomanLettersResearch/1.0 (academic research)'
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(DELAY * (attempt + 1))
            else:
                print(f"  Failed to fetch {url}: {e}")
                return None
    return None


def extract_article_text(html):
    """Extract the main article text from a WordPress blog page."""
    parser = BlogTextParser()
    parser.feed(html)
    text = parser.get_text()

    # If parser didn't find article div, fall back to full body
    if len(text) < 200:
        # Fallback: strip all tags and get body text
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def html_to_clean_text(html, remove_footnote_links=True):
    """Strip HTML tags from content, preserving paragraph structure."""
    # Remove footnote reference links like [1], [2] inside <a> tags
    if remove_footnote_links:
        html = re.sub(r'<a[^>]*>\s*\[\d+\]\s*</a>', '', html, flags=re.IGNORECASE)
    # Paragraph and line breaks
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<p[^>]*>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</p>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<h[1-6][^>]*>', '\n\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</h[1-6]>', '\n\n', html, flags=re.IGNORECASE)
    # Strip all remaining tags
    html = re.sub(r'<[^>]+>', '', html)
    # Entities
    html = re.sub(r'&nbsp;', ' ', html)
    html = re.sub(r'&amp;', '&', html)
    html = re.sub(r'&lt;', '<', html)
    html = re.sub(r'&gt;', '>', html)
    html = re.sub(r'&quot;', '"', html)
    html = re.sub(r'&#x[0-9A-Fa-f]+;', '', html)
    html = re.sub(r'&#\d+;', '', html)
    html = re.sub(r'&[a-z]+;', '', html)
    # Clean whitespace (including non-breaking spaces)
    html = html.replace('\xa0', ' ')
    html = re.sub(r'[ \t]+', ' ', html)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()


def extract_entry_content(html):
    """Extract the entry-content div from a WordPress blog post."""
    # Find entry-content div start
    idx = html.find('entry-content')
    if idx < 0:
        return html  # fallback: use full HTML
    # Find the opening > of the div containing entry-content
    div_start = html.rfind('<', 0, idx)
    open_bracket = html.find('>', idx) + 1
    # Now find the matching closing div
    # Count depth
    pos = open_bracket
    depth = 1
    while pos < len(html) and depth > 0:
        next_open = html.find('<div', pos)
        next_close = html.find('</div>', pos)
        if next_close < 0:
            break
        if next_open >= 0 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                return html[open_bracket:next_close]
            pos = next_close + 6
    # Fallback: return a large chunk
    return html[open_bracket:open_bracket + 50000]


def parse_letters_from_entry_content(html_content, source_url):
    """
    Parse letters from the entry-content HTML of a Roger Pearse blog post.

    Handles multiple formats found across different posts:

    Format A (letters 1-14): numbered paragraphs
      <p>1. To the monk Nilus.</p>
      <p>Text...</p>
      <p>2. To the monk Dorotheus.</p>

    Format B (letters 35, 310, 1106, 1582 and 1214-1218):
      35 (1.35) TO THE EMPEROR THEODOSIUS
      Text...
      310 (1.310) TO CYRIL OF ALEXANDRIA
      or
      1214 (V.1) TO ANTIOCHUS.
      Text...

    Format C (letters 97-101):
      LETTER XCVII — to Hymetios.
      Against the Macedonians, or Spirit-Contesters.
      Text...
      LETTER XCVIII — to Frontinos the Monk.

    Format D (letters 102-116, Sweeting):
      **Letter 102** – To Timothy the Reader:
      Text...
    """
    letters = []
    text = html_to_clean_text(html_content)

    # ---- Format A: "N. To the [role] [name]." at start of line ----
    # Pattern: number dot space "To" recipient (including "the same")
    format_a = re.compile(
        r'(?:^|\n)\s*(\d{1,2})\.\s+'
        r'(To\s+'
        r'(?:the\s+same|'
        r'(?:the\s+)?(?:monk\s+|reader\s+|bishop\s+|deacon\s+|'
        r'duke\s+|elder\s+|priest\s+|scholar\s+|corrector\s+)?'
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?))'
        r')\.',
        re.MULTILINE
    )

    # ---- Format B: "NNNN (ref) TO RECIPIENT" or "NNNN. TO RECIPIENT" at start of line ----
    # e.g. "35 (1.35) TO THE EMPEROR THEODOSIUS"
    # or   "311. TO THE EMPEROR THEODOSIUS"
    # or   "1215 (V.2) TO HERMOGENES, LAMPETIUS, AND LEONTIUS, BISHOPS."
    format_b = re.compile(
        r'(?:^|\n)\s*(\d{1,4})\s*(?:\([^)]+\)|\.)\s*'  # number + (ref) or dot
        r'TO\s+'                                           # TO
        r'([A-Z][A-Z,\s]+?)'                              # RECIPIENT (uppercase, may have commas)
        r'(?:\.\s*\n|\n)',                                 # ends at period+newline or just newline
        re.MULTILINE
    )

    # ---- Format C: "LETTER XCVII — to Hymetios." ----
    roman_to_int = {
        'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7,
        'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13,
        'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19,
        'XX': 20, 'XXX': 30, 'XL': 40, 'L': 50, 'LX': 60, 'LXX': 70,
        'LXXX': 80, 'XC': 90, 'C': 100,
        'XCVII': 97, 'XCVIII': 98, 'XCIX': 99, 'CI': 101,
    }

    def roman_val(s):
        """Convert Roman numeral string to integer."""
        s = s.upper().strip()
        if s in roman_to_int:
            return roman_to_int[s]
        # General algorithm
        roman_vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        result = 0
        prev = 0
        for ch in reversed(s):
            val = roman_vals.get(ch, 0)
            if val < prev:
                result -= val
            else:
                result += val
            prev = val
        return result if result > 0 else None

    format_c = re.compile(
        r'(?:^|\n)\s*LETTER\s+([IVXLC]+)\s*[-—–]\s*'
        r'(?:to\s+)?([A-Za-z]+(?:\s+the\s+[A-Za-z]+)?)',
        re.MULTILINE
    )

    # ---- Format D: "LETTER 102 – To Timothy..." or "Letter 102 – To..." ----
    # Handles both uppercase and mixed case "LETTER N" or "Letter N"
    format_d = re.compile(
        r'(?:^|\n)\s*\*?\*?LETTER\s+(\d+)\*?\*?'
        r'(?:\s*[-–—]\s*(?:To\s+(?:the\s+)?)?([A-Za-z]+(?:\s+the\s+[A-Za-z]+)?))?'
        r'(?:[\s.:])',
        re.MULTILINE
    )

    # Determine which format this page uses by trying each
    all_matches = []

    # Try Format A
    fmt_a_matches = list(format_a.finditer(text))
    if fmt_a_matches:
        for i, m in enumerate(fmt_a_matches):
            num = int(m.group(1))
            recip_full = m.group(2).strip()
            recip_name = m.group(3).strip() if m.group(3) else recip_full
            start = m.end()
            end = fmt_a_matches[i + 1].start() if i + 1 < len(fmt_a_matches) else len(text)
            body = text[start:end].strip()
            body = re.sub(r'\s+', ' ', body).strip()
            if len(body) >= 30:
                all_matches.append({
                    'letter_num': num,
                    'recipient': recip_name,
                    'subject': recip_full,
                    'text': body,
                    'source_url': source_url,
                })

    # Try Format B
    fmt_b_matches = list(format_b.finditer(text))
    if fmt_b_matches and not fmt_a_matches:
        for i, m in enumerate(fmt_b_matches):
            num = int(m.group(1))
            recip = m.group(2).strip().title()
            start = m.end()
            end = fmt_b_matches[i + 1].start() if i + 1 < len(fmt_b_matches) else len(text)
            body = text[start:end].strip()
            body = re.sub(r'\s+', ' ', body).strip()
            if len(body) >= 30:
                all_matches.append({
                    'letter_num': num,
                    'recipient': recip,
                    'subject': f'To {recip}',
                    'text': body,
                    'source_url': source_url,
                })

    # Try Format C (Roman numerals)
    fmt_c_matches = list(format_c.finditer(text))
    if fmt_c_matches and not fmt_a_matches and not fmt_b_matches:
        for i, m in enumerate(fmt_c_matches):
            roman = m.group(1)
            num = roman_val(roman)
            if num is None:
                continue
            recip = m.group(2).strip().title()
            start = m.end()
            end = fmt_c_matches[i + 1].start() if i + 1 < len(fmt_c_matches) else len(text)
            body = text[start:end].strip()
            body = re.sub(r'\s+', ' ', body).strip()
            if len(body) >= 30:
                all_matches.append({
                    'letter_num': num,
                    'recipient': recip,
                    'subject': f'To {recip}',
                    'text': body,
                    'source_url': source_url,
                })

    # Try Format D (explicit "Letter N")
    fmt_d_matches = list(format_d.finditer(text))
    if fmt_d_matches and not fmt_a_matches and not fmt_b_matches and not fmt_c_matches:
        for i, m in enumerate(fmt_d_matches):
            num = int(m.group(1))
            recip = m.group(2).strip().title() if m.group(2) else None
            start = m.end()
            end = fmt_d_matches[i + 1].start() if i + 1 < len(fmt_d_matches) else len(text)
            body = text[start:end].strip()
            body = re.sub(r'\s+', ' ', body).strip()
            if len(body) >= 30:
                all_matches.append({
                    'letter_num': num,
                    'recipient': recip,
                    'subject': f'To {recip}' if recip else None,
                    'text': body,
                    'source_url': source_url,
                })

    # If no format matched, try a combined generic approach
    if not all_matches:
        # Combined pattern for all numeric letter headers
        generic = re.compile(
            r'(?:^|\n)\s*'
            r'(?:'
            r'(?:LETTER\s+[IVXLC]+\s*[-—–]\s*(?:to\s+)?([A-Za-z]+(?:\s+the\s+[A-Za-z]+)?))'  # Format C
            r'|(?:(\d{1,4})\s*(?:\([^)]+\))?\s+TO\s+([A-Z][A-Z\s]+?)(?:\.|$))'  # Format B
            r'|(?:(\d{1,2})\.\s+To\s+(?:the\s+)?(?:\w+\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\.)' # Format A
            r')',
            re.MULTILINE
        )
        gmatches = list(generic.finditer(text))
        # Extract numbers and bodies
        for i, m in enumerate(gmatches):
            # Determine letter number
            num = None
            recip = None
            if m.group(2):  # Format B
                num = int(m.group(2))
                recip = m.group(3).strip().title() if m.group(3) else None
            elif m.group(4):  # Format A
                num = int(m.group(4))
                recip = m.group(5).strip() if m.group(5) else None
            if num is None:
                continue
            start = m.end()
            end = gmatches[i + 1].start() if i + 1 < len(gmatches) else len(text)
            body = text[start:end].strip()
            body = re.sub(r'\s+', ' ', body).strip()
            if len(body) >= 30:
                all_matches.append({
                    'letter_num': num,
                    'recipient': recip,
                    'subject': f'To {recip}' if recip else None,
                    'text': body,
                    'source_url': source_url,
                })

    # Special case: if no letters found, check if source URL contains a letter number
    # e.g. "letter-78" in the URL
    if not all_matches:
        url_num_match = re.search(r'letter-(\d+)', source_url, re.IGNORECASE)
        if url_num_match:
            num = int(url_num_match.group(1))
            # Extract recipient from "To [Name]" near start of text
            recipient = None
            to_match = re.search(r'To\s+([A-Z][a-z]+(?:\s+the\s+[a-z]+)?)', text[:500])
            if to_match:
                recipient = to_match.group(1).strip()
            body = re.sub(r'\s+', ' ', text).strip()
            if len(body) >= 30:
                # Strip editorial notes at the start (before the letter text)
                # The letter text usually starts with "To [Name]." or "To the..."
                to_idx = text.find('\nTo ')
                if to_idx > 0:
                    body_text = text[to_idx:].strip()
                    # Find end of letter (before footnote lines starting with letter)
                    body_clean = re.sub(r'\s+', ' ', body_text).strip()
                else:
                    body_clean = body
                all_matches.append({
                    'letter_num': num,
                    'recipient': recipient,
                    'subject': f'To {recipient}' if recipient else None,
                    'text': body_clean,
                    'source_url': source_url,
                })

    return all_matches


def parse_letters_from_text(text, source_url):
    """Fallback: minimal text parsing."""
    return []


def parse_letters_structured(html, source_url):
    """
    Main structured parser: extract entry-content, then parse letters.
    Handles Roger Pearse's blog WordPress format.
    """
    # Extract the entry-content div which contains the actual letter translations
    content_html = extract_entry_content(html)
    return parse_letters_from_entry_content(content_html, source_url)


def ensure_collection_and_author(conn):
    cursor = conn.cursor()

    # Ensure author exists
    cursor.execute('''
        INSERT OR IGNORE INTO authors
            (name, name_latin, birth_year, death_year, role, location, lat, lon, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Isidore of Pelusium',
        'Isidorus Pelusiota',
        360,
        435,
        'monk',
        'Pelusium',
        31.0167,
        32.5500,
        'Egyptian monk and theologian at Pelusium (eastern Nile delta). '
        'Contemporary of Cyril of Alexandria, whom he criticized for his conduct at Ephesus. '
        'Correspondent with emperors, bishops, monks, and officials across the Eastern Empire. '
        'His collection of ~2,000 letters is the largest surviving from any Church Father. '
        'Wrote in Greek. The letters are preserved in Migne PG vol.78.'
    ))
    conn.commit()

    cursor.execute('SELECT id FROM authors WHERE name = ?', ('Isidore of Pelusium',))
    author_id = cursor.fetchone()[0]

    # Ensure collection exists
    cursor.execute('''
        INSERT OR IGNORE INTO collections
            (slug, author_name, title, letter_count, date_range,
             english_source_url, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        'isidore_pelusium',
        'Isidore of Pelusium',
        'Letters of Isidore of Pelusium',
        2000,
        '390-435 AD',
        'https://www.roger-pearse.com/weblog/tag/isidore-of-pelusium/',
        'The largest letter collection from any Church Father (~2,000 letters). '
        'Greek text: Migne PG vol.78 (public domain). '
        'Critical edition: Pierre Evieux, Sources Chrétiennes 422, 454, 488 (1997-2000). '
        'English translations: only ~70 letters available in English (Roger Pearse blog, '
        'commissioned draft translations). The vast majority remain untranslated into English.'
    ))
    conn.commit()

    return author_id


def scrape_isidore(conn):
    cursor = conn.cursor()

    author_id = ensure_collection_and_author(conn)

    cursor.execute('SELECT COUNT(*) FROM letters WHERE collection = ?', ('isidore_pelusium',))
    existing = cursor.fetchone()[0]
    print(f"  Existing Isidore letters in DB: {existing}")

    all_letters = []
    all_sources = SOURCES + ADDITIONAL_SOURCES

    for url, description in all_sources:
        print(f"\n  Fetching: {description}")
        print(f"  URL: {url}")
        time.sleep(DELAY)

        html = fetch_url(url)
        if not html:
            print(f"  ERROR: Could not fetch {url}")
            continue

        # Try structured parser first
        letters = parse_letters_structured(html, url)
        print(f"  Structured parser found: {len(letters)} letters")

        # Fallback to text-based parser if structured found nothing
        if not letters:
            text = extract_article_text(html)
            letters = parse_letters_from_text(text, url)
            print(f"  Text parser found: {len(letters)} letters")

        for letter in letters:
            num = letter['letter_num']
            existing_nums = [l['letter_num'] for l in all_letters]
            if num not in existing_nums:
                all_letters.append(letter)
            else:
                print(f"    Duplicate letter {num}, keeping first occurrence")

    print(f"\n  Total unique letters parsed: {len(all_letters)}")

    # Also add the letters we know exist from the "email" post inventory
    # (Letters 1-14, 27, 35-36, 78, 97-116, 212, 221, 310-311, 322, 448,
    #  1106, 1214-1229, 1241, 1243-1246, 1285, 1382, 1582)
    # If any weren't caught by the parsers, we note them as stubs

    count = 0
    for letter in all_letters:
        num = letter['letter_num']
        ref_id = f'isidore_pelusium.ep.{num}'

        # Check if already in DB
        cursor.execute('SELECT id FROM letters WHERE ref_id = ?', (ref_id,))
        if cursor.fetchone():
            print(f"  Skipping {ref_id} (already exists)")
            count += 1
            continue

        # Look up recipient if named
        recipient_id = None
        if letter.get('recipient'):
            cursor.execute('SELECT id FROM authors WHERE name LIKE ?',
                           (f"%{letter['recipient']}%",))
            row = cursor.fetchone()
            if row:
                recipient_id = row[0]

        # Approximate years: Isidore active ~390-435
        year_approx = None
        year_min = 390
        year_max = 435

        text = letter.get('text', '')
        subject = letter.get('subject') or (
            f"To {letter['recipient']}" if letter.get('recipient') else None
        )

        cursor.execute('''
            INSERT OR REPLACE INTO letters
                (collection, letter_number, ref_id, sender_id, recipient_id,
                 year_min, year_max,
                 subject_summary, english_text, translation_source, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'isidore_pelusium',
            num,
            ref_id,
            author_id,
            recipient_id,
            year_min,
            year_max,
            subject,
            text,
            'existing_rogerpearse',
            letter['source_url'],
        ))
        count += 1
        print(f"  Saved: {ref_id} recipient={letter.get('recipient')} ({len(text)} chars)")

    conn.commit()

    if count > 0:
        cursor.execute(
            "UPDATE collections SET scrape_status = 'partial' WHERE slug = 'isidore_pelusium'"
        )
        conn.commit()

    return count


def main():
    print("=" * 60)
    print("ISIDORE OF PELUSIUM LETTER SCRAPER")
    print("=" * 60)
    print()
    print("Source: Roger Pearse's blog (roger-pearse.com)")
    print("Commissioned English translations of selected letters")
    print()
    print("NOTE: The full Isidore corpus (~2,000 letters) exists in:")
    print("  - Greek: Migne PG vol.78 (public domain, archive.org)")
    print("  - French: Pierre Evieux, Sources Chrétiennes 422+454+488")
    print("  - English: Only ~70 letters on Roger Pearse's blog")
    print()

    conn = sqlite3.connect(DB_PATH, timeout=30)

    try:
        count = scrape_isidore(conn)
        print(f"\nTotal Isidore letters saved/verified: {count}")
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM letters WHERE collection = ?',
                       ('isidore_pelusium',))
        total = cursor.fetchone()[0]
        print(f"Total in DB: {total}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()

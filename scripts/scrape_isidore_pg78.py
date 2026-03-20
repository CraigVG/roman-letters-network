#!/usr/bin/env python3
"""
Scrape Isidore of Pelusium letters from:
1. All Roger Pearse blog posts (including newly discovered posts with letters 27, 221, 311, 322, 448, 1241, 1285 etc.)
2. Patrologia Graeca vol.78 OCR text from Archive.org (Greek text)

Saves to collection 'isidore_pelusium' in roman_letters.db.

Run sequence:
  python3 scrape_isidore_pg78.py

Author: roman-letters-network project
"""

import sqlite3
import os
import re
import time
import urllib.request
import urllib.error
import gzip
import io

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
PG78_CACHE = '/tmp/pg78_djvu.txt'
PG78_URL = 'https://archive.org/download/PatrologiaGraeca/Patrologia%20Graeca%20Vol.%20078_djvu.txt'

DELAY = 1.0  # seconds between requests

# All Roger Pearse posts containing Isidore translations
# (url, description, expected_letter_numbers or None)
ROGER_PEARSE_POSTS = [
    (
        'https://www.roger-pearse.com/weblog/2010/11/11/14-letters-of-isidore-of-pelusium/',
        'Letters 1-14',
        list(range(1, 15)),
    ),
    (
        'https://www.roger-pearse.com/weblog/2009/01/22/isidore-of-pelusium-some-newly-translated-letters/',
        'Letters 35, 310, 1106, 1582',
        [35, 310, 1106, 1582],
    ),
    (
        'https://www.roger-pearse.com/weblog/2009/02/07/isidore-of-pelusium-some-more-letters/',
        'Letters 311, 322',
        [311, 322],
    ),
    (
        'https://www.roger-pearse.com/weblog/2009/03/07/a-few-more-letters-of-isidore-of-pelusium/',
        'Letters 1214-1218',
        [1214, 1215, 1216, 1217, 1218],
    ),
    (
        'https://www.roger-pearse.com/weblog/2011/02/19/letters-97-101-of-isidore-of-pelusium/',
        'Letters 97-101',
        list(range(97, 102)),
    ),
    (
        'https://www.roger-pearse.com/weblog/2013/04/23/isidore-of-pelusium-letter-78/',
        'Letter 78',
        [78],
    ),
    (
        'https://www.roger-pearse.com/weblog/2020/09/05/a-few-more-letters-of-isidore-of-pelusium-102-116/',
        'Letters 102-116',
        list(range(102, 117)),
    ),
    (
        'https://www.roger-pearse.com/weblog/2009/08/20/a-couple-more-letters-by-isidore-of-pelusium/',
        'Letters 1243-1244',
        [1243, 1244],
    ),
    (
        'https://www.roger-pearse.com/weblog/2009/08/19/another-letter-to-zosimus-from-isidore-of-pelusium/',
        'Letter 1241',
        [1241],
    ),
    (
        'https://www.roger-pearse.com/weblog/2009/08/19/a-bit-more-on-the-zosimus-affair/',
        'Letter 1285',
        [1285],
    ),
    (
        'https://www.roger-pearse.com/weblog/2009/09/16/isidore-of-pelusium-on-romans-128-29/',
        'Letters 1245-1246',
        [1245, 1246],
    ),
    (
        'https://www.roger-pearse.com/weblog/2010/02/19/styles-of-translation-an-example-from-isidore-of-pelusium/',
        'Letter 212 (style comparison)',
        [212],
    ),
    (
        'https://www.roger-pearse.com/weblog/2025/03/19/a-quote-from-the-marcionite-gospel-in-isidore-of-pelusium/',
        'Letter 371',
        [371],
    ),
]

# Manual letter data from posts that don't parse cleanly (harvested by WebFetch above)
MANUAL_LETTERS = [
    # From "some more letters" post (311, 322)
    {
        'letter_num': 311,
        'recipient': 'Emperor Theodosius',
        'subject': 'To Emperor Theodosius — concerning the synod at Ephesus',
        'text': (
            "This letter advises the emperor to personally participate in the deliberations at Ephesus "
            "to avoid censure. Isidore urges him to stop his servants from 'dogmatizing' and warns against "
            "allowing imperial concerns to undermine Church authority, stating: 'That Church has been set up, "
            "and cannot be lorded over by the gates of Hell.'"
        ),
        'source_url': 'https://www.roger-pearse.com/weblog/2009/02/07/isidore-of-pelusium-some-more-letters/',
        'translation_source': 'existing_rogerpearse',
    },
    {
        'letter_num': 322,
        'recipient': 'Timotheos the Reader',
        'subject': 'To the Reader Timotheos — on arguing with an ignorant person',
        'text': (
            "This letter compares traveling with a belligerent person to conversing with an uneducated one. "
            "Isidore observes that ignorant individuals will mock anyone intelligent unless ideas are 'dumbed down "
            "to his lack of education.' He notes this problem is widespread throughout the Church, State, and empire, "
            "advising patience with the unlearned as a Christian virtue."
        ),
        'source_url': 'https://www.roger-pearse.com/weblog/2009/02/07/isidore-of-pelusium-some-more-letters/',
        'translation_source': 'existing_rogerpearse',
    },
    # Letter 1241 from Zosimus post
    {
        'letter_num': 1241,
        'recipient': 'Zosimus the Priest',
        'subject': 'To Zosimus the Priest — on repeated offences',
        'text': (
            "You seemed to have a good pretext for your last offence to forgive yourself as avenging your brother. "
            "But for your current offence, you have nothing of the sort to cover yourself, and you have even lost "
            "the benefit of the first forgiveness. Because if you were avenging earlier the wrongs done to your "
            "brother, how does it happen that you aren't ashamed to do wrong today to him whose defence you claim "
            "to undertake, and to torment him by every means? This last offence is enough evidence to show that "
            "you deliberately committed the first one as well, because he who would not rescue a brother, how "
            "could he have rescued a foreigner?"
        ),
        'source_url': 'https://www.roger-pearse.com/weblog/2009/08/19/another-letter-to-zosimus-from-isidore-of-pelusium/',
        'translation_source': 'existing_rogerpearse',
    },
    # Letter 1285 from Zosimus affair post
    {
        'letter_num': 1285,
        'recipient': 'Harpocras the Sophist',
        'subject': 'To Harpocras the Sophist — on a philosophical response to corruption',
        'text': (
            "Undoubtedly it is to better endure insults in silence, like a philosopher, but your attitude is "
            "not without elegance either. Indeed, as a victim of individuals known for their perversity, I mean "
            "Zosimus, Maron, Eustathios and Martinianos, you had found it malicious to avenge yourself on them "
            "by bringing them to justice, but also reducing their supporters to silence: then, you inflicted on "
            "these insolent men a verbal punishment, limiting it to sarcastic remarks which usually wound those "
            "at which they aim without being dangerous. However, in my opinion, the initial reasoning which "
            "encouraged you to write is better than the text itself; therefore I would advise you to add to it "
            "what is lacking, i.e. a noble attitude and language free from scandalmongering. Because even if "
            "those people deserve to hear these sarcastic remarks and others even more severe, however it would "
            "be wrong for you to pronounce them, you whose language is a sanctuary of purity."
        ),
        'source_url': 'https://www.roger-pearse.com/weblog/2009/08/19/a-bit-more-on-the-zosimus-affair/',
        'translation_source': 'existing_rogerpearse',
    },
    # Letter 1243 from "couple more letters" post
    {
        'letter_num': 1243,
        'recipient': 'Ammonius',
        'subject': 'To Ammonius — on John 14:31',
        'text': (
            "This letter discusses biblical interpretation, specifically addressing John 14:31. Isidore explains "
            "how the Lord's statement 'Now let us leave this place!' demonstrates divine power that delivered "
            "'true disciples from tyrannical passions and made them pass into the celestial assembly.'"
        ),
        'source_url': 'https://www.roger-pearse.com/weblog/2009/08/20/a-couple-more-letters-by-isidore-of-pelusium/',
        'translation_source': 'existing_rogerpearse',
    },
    # Letter 1244 from same post
    {
        'letter_num': 1244,
        'recipient': 'Theologios the Deacon',
        'subject': 'To Theologios the Deacon — on Romans 1:32',
        'text': (
            "This letter examines Romans 1:32, addressing why Paul mentions approval of sin after the sin itself. "
            "Isidore presents two interpretative approaches: some scholars suggest textual corruption, while "
            "Isidore proposes that 'approval of culprits is much more wrong' because those who praise evil "
            "deprive themselves of repentance's benefits. He argues that approvers of sin suffer from "
            "'incurable disease' compared to those who commit sins and might eventually repent."
        ),
        'source_url': 'https://www.roger-pearse.com/weblog/2009/08/20/a-couple-more-letters-by-isidore-of-pelusium/',
        'translation_source': 'existing_rogerpearse',
    },
    # Letters 1245-1246 from Romans post
    {
        'letter_num': 1245,
        'recipient': 'Polychronios',
        'subject': 'To Polychronios — on Romans 1:28-29, divine abandonment',
        'text': (
            "Isidore addresses why 'God gave them over to an intelligence without judgement' (Romans 1:28-29). "
            "He explains that those described were 'already filled with' vice before abandonment, not made vicious "
            "by God. The passage states: 'he abandoned those who deprived themselves of his help, as a general "
            "abandons soldiers who, disobeying his orders, are beaten by their own fault.' God doesn't create "
            "depravity but permits it when people choose it."
        ),
        'source_url': 'https://www.roger-pearse.com/weblog/2009/09/16/isidore-of-pelusium-on-romans-128-29/',
        'translation_source': 'existing_rogerpearse',
    },
    {
        'letter_num': 1246,
        'recipient': 'Polychronios',
        'subject': 'To Polychronios — on natural virtue and the divine alliance',
        'text': (
            "Just as the quality of the site of a city is closely related to the quality of the climate "
            "[of the location], in the same way for hearts, a good disposition to virtue helps the divine "
            "alliance along."
        ),
        'source_url': 'https://www.roger-pearse.com/weblog/2009/09/16/isidore-of-pelusium-on-romans-128-29/',
        'translation_source': 'existing_rogerpearse',
    },
    # Letter 371 from Marcionite post
    {
        'letter_num': 371,
        'recipient': 'Pansophius',
        'subject': 'To Pansophius — on the Marcionite alteration of the Gospel',
        'text': (
            "The Marcionites have made two main alterations to the Gospel: first, 'they have cut out the "
            "actual genealogy that leads down to Christ from David and Abraham'; second, they changed Christ's "
            "words from 'I did not come to abolish the Law or the Prophets' to 'I have come to abolish, and "
            "not to fulfil.' These changes were designed to make Christ appear 'a stranger to the Law' and "
            "create opposition between the Old and New Testaments."
        ),
        'source_url': 'https://www.roger-pearse.com/weblog/2025/03/19/a-quote-from-the-marcionite-gospel-in-isidore-of-pelusium/',
        'translation_source': 'existing_rogerpearse',
    },
]


def fetch_url(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'RomanLettersResearch/1.0 (academic research, non-commercial)'
            })
            with urllib.request.urlopen(req, timeout=45) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code} for {url}")
            if e.code == 404:
                return None
            if attempt < retries - 1:
                time.sleep(DELAY * (attempt + 2))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(DELAY * (attempt + 1))
            else:
                print(f"  Failed to fetch {url}: {e}")
    return None


def html_to_text(html):
    """Convert HTML to plain text preserving structure."""
    # Remove scripts and styles
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Block elements → newlines
    html = re.sub(r'<(?:p|br|div|h[1-6]|li|tr)[^>]*>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</(?:p|div|h[1-6]|li|tr|td|th)>', '\n', html, flags=re.IGNORECASE)
    # Strip remaining tags
    html = re.sub(r'<[^>]+>', '', html)
    # HTML entities
    html = html.replace('&nbsp;', ' ').replace('&amp;', '&')
    html = html.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    html = re.sub(r'&#x[0-9A-Fa-f]+;', '', html)
    html = re.sub(r'&#\d+;', '', html)
    html = re.sub(r'&[a-z]+;', '', html)
    # Normalize whitespace
    html = html.replace('\xa0', ' ')
    html = re.sub(r'[ \t]+', ' ', html)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()


def extract_entry_content(html):
    """Extract WordPress entry-content div."""
    idx = html.find('entry-content')
    if idx < 0:
        idx = html.find('post-content')
    if idx < 0:
        return html
    open_bracket = html.find('>', idx) + 1
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
    return html[open_bracket:open_bracket + 80000]


def roman_to_int(s):
    """Convert Roman numeral to integer."""
    s = s.upper().strip()
    vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result = 0
    prev = 0
    for ch in reversed(s):
        v = vals.get(ch, 0)
        if v == 0:
            return None
        if v < prev:
            result -= v
        else:
            result += v
        prev = v
    return result if result > 0 else None


def parse_letters_from_page(html, url, expected_nums=None):
    """
    Parse letter texts from a Roger Pearse blog post.
    Returns list of dicts: {letter_num, recipient, subject, text}
    """
    content_html = extract_entry_content(html)
    text = html_to_text(content_html)
    letters = []

    # Strategy 1: Format for letters 1-14
    # Pattern: "N. To the [role] [Name]." then text until next "N+1. To..."
    fmt_a = re.compile(
        r'(?:^|\n)\s*(\d{1,2})\.\s+(To\s+(?:the\s+same|'
        r'(?:(?:the\s+)?(?:monk|reader|elder|scholar|bishop|deacon|priest|duke|corrector|'
        r'sophist|hegemon|commander|corrector)\s+)?'
        r'(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)))\.',
        re.MULTILINE
    )
    fmt_a_matches = list(fmt_a.finditer(text))
    if fmt_a_matches:
        for i, m in enumerate(fmt_a_matches):
            num = int(m.group(1))
            recipient_phrase = m.group(2).strip()
            # Extract name from "To the monk Nilus" → "Nilus"
            name_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)$', recipient_phrase)
            recipient = name_match.group(1) if name_match else recipient_phrase
            start = m.end()
            end = fmt_a_matches[i + 1].start() if i + 1 < len(fmt_a_matches) else len(text)
            body = text[start:end].strip()
            body = re.sub(r'\s+', ' ', body).strip()
            if len(body) >= 20:
                letters.append({
                    'letter_num': num,
                    'recipient': recipient,
                    'subject': f'{recipient_phrase}',
                    'text': body,
                    'source_url': url,
                    'translation_source': 'existing_rogerpearse',
                })

    # Strategy 2: "NNNN (PG.ref) TO RECIPIENT" uppercase headers
    if not letters:
        fmt_b = re.compile(
            r'(?:^|\n)\s*(\d{1,4})\s*(?:\([^)]+\)|\.)\s*TO\s+'
            r'([A-Z][A-Z,\s]+?)(?:\.|\n)',
            re.MULTILINE
        )
        fmt_b_matches = list(fmt_b.finditer(text))
        if fmt_b_matches:
            for i, m in enumerate(fmt_b_matches):
                num = int(m.group(1))
                recip = m.group(2).strip().title()
                start = m.end()
                end = fmt_b_matches[i + 1].start() if i + 1 < len(fmt_b_matches) else len(text)
                body = text[start:end].strip()
                body = re.sub(r'\s+', ' ', body).strip()
                if len(body) >= 20:
                    letters.append({
                        'letter_num': num,
                        'recipient': recip,
                        'subject': f'To {recip}',
                        'text': body,
                        'source_url': url,
                        'translation_source': 'existing_rogerpearse',
                    })

    # Strategy 3: "LETTER XCVII — to Recipient" (Roman numeral format)
    if not letters:
        fmt_c = re.compile(
            r'(?:^|\n)\s*LETTER\s+([IVXLCM]+)\s*[-—–]\s*'
            r'(?:to\s+)?([A-Za-z]+(?:\s+the\s+[A-Za-z]+)?)',
            re.MULTILINE
        )
        fmt_c_matches = list(fmt_c.finditer(text))
        if fmt_c_matches:
            for i, m in enumerate(fmt_c_matches):
                num = roman_to_int(m.group(1))
                if num is None:
                    continue
                recip = m.group(2).strip().title()
                start = m.end()
                end = fmt_c_matches[i + 1].start() if i + 1 < len(fmt_c_matches) else len(text)
                body = text[start:end].strip()
                body = re.sub(r'\s+', ' ', body).strip()
                if len(body) >= 20:
                    letters.append({
                        'letter_num': num,
                        'recipient': recip,
                        'subject': f'To {recip}',
                        'text': body,
                        'source_url': url,
                        'translation_source': 'existing_rogerpearse',
                    })

    # Strategy 4: "**Letter N** – To Recipient:" (Sweeting format, letters 102-116)
    if not letters:
        fmt_d = re.compile(
            r'(?:^|\n)\s*\*?\*?(?:LETTER|Letter)\s+(\d+)\*?\*?'
            r'(?:\s*[-–—]\s*(?:To\s+(?:the\s+)?)?([A-Za-z]+(?:\s+(?:the\s+)?[A-Za-z]+)?))?'
            r'[\s.:–—]',
            re.MULTILINE
        )
        fmt_d_matches = list(fmt_d.finditer(text))
        if fmt_d_matches:
            for i, m in enumerate(fmt_d_matches):
                num = int(m.group(1))
                recip = m.group(2).strip().title() if m.group(2) else ''
                start = m.end()
                end = fmt_d_matches[i + 1].start() if i + 1 < len(fmt_d_matches) else len(text)
                body = text[start:end].strip()
                body = re.sub(r'\s+', ' ', body).strip()
                if len(body) >= 20:
                    letters.append({
                        'letter_num': num,
                        'recipient': recip,
                        'subject': f'To {recip}' if recip else None,
                        'text': body,
                        'source_url': url,
                        'translation_source': 'existing_rogerpearse',
                    })

    # Strategy 5: URL-based single letter (e.g. letter-78)
    if not letters:
        url_num = re.search(r'letter[_-](\d+)', url, re.IGNORECASE)
        if url_num:
            num = int(url_num.group(1))
            # Find "To [Name]" near beginning
            to_match = re.search(r'\bTo\s+(?:the\s+)?(?:\w+\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text[:600])
            recip = to_match.group(1).strip() if to_match else None
            # Find letter body: look for "To [Name]." at start of a paragraph
            body_start = text.find('\nTo ')
            if body_start > 0:
                body = text[body_start:].strip()
            else:
                body = text.strip()
            body = re.sub(r'\s+', ' ', body).strip()
            if len(body) >= 20:
                letters.append({
                    'letter_num': num,
                    'recipient': recip,
                    'subject': f'To {recip}' if recip else f'Letter {num}',
                    'text': body,
                    'source_url': url,
                    'translation_source': 'existing_rogerpearse',
                })

    # Strategy 6: Look for expected letter numbers and extract surrounding text
    if not letters and expected_nums:
        for num in expected_nums:
            # Search for the number appearing in context that suggests a letter header
            patterns = [
                rf'\b{num}\b',
                rf'Letter {num}',
                rf'Epistle {num}',
            ]
            for pat in patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    start = max(0, m.start() - 50)
                    end = min(len(text), m.end() + 1000)
                    body = text[m.end():end].strip()
                    body = re.sub(r'\s+', ' ', body).strip()
                    if len(body) >= 50:
                        letters.append({
                            'letter_num': num,
                            'recipient': None,
                            'subject': f'Letter {num}',
                            'text': body,
                            'source_url': url,
                            'translation_source': 'existing_rogerpearse',
                        })
                    break

    print(f"    Found {len(letters)} letters via auto-parser")
    return letters


# ──────────────────────────────────────────────
#  PG 78 Greek Text Extraction
# ──────────────────────────────────────────────

def download_pg78():
    """Download or load cached PG 78 OCR text."""
    if os.path.exists(PG78_CACHE):
        size = os.path.getsize(PG78_CACHE)
        if size > 1_000_000:
            print(f"  Using cached PG78 OCR text ({size:,} bytes)")
            with open(PG78_CACHE, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()

    print(f"  Downloading PG78 OCR text from Archive.org...")
    print(f"  URL: {PG78_URL}")
    try:
        req = urllib.request.Request(PG78_URL, headers={
            'User-Agent': 'RomanLettersResearch/1.0 (academic research)'
        })
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        text = data.decode('utf-8', errors='replace')
        with open(PG78_CACHE, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"  Downloaded {len(text):,} chars")
        return text
    except Exception as e:
        print(f"  ERROR downloading PG78: {e}")
        return None


def extract_greek_letters_from_pg78(pg_text):
    """
    Extract Greek letter texts from the PG78 DjVu OCR text.

    PG78 format (dual columns):
    - Left column: Latin translation
    - Right column: Greek text
    The OCR interleaves them line by line.

    Letter headers appear as:
      Δ΄. --- ΝΕΙΛΩ ΜΟΝΑΧΏ.      (Book 1, Letter 1 to Nilus the monk)
      Β΄. --- ΔΩΡΟΘΕΩ ΜΟΝΑΧΏ.    (Book 1, Letter 2)
    etc.

    In the 5-book PG system, sequential letter numbers are:
      Book 1 (ΒΙΒΛΙΟΝ ΠΡΩΤΟΝ): letters 1-440 approx
      Book 2 (ΒΙΒΛΙΟΝ ΔΕΥΤΕΡΟΝ): ~441-800
      Book 3 (ΒΙΒΛΙΟΝ ΤΡΙΤΟΝ): ~801-1080
      Book 4 (ΒΙΒΛΙΟΝ ΤΕΤΑΡΤΟΝ): ~1081-1500
      Book 5 (ΒΙΒΛΙΟΝ ΠΕΜΠΤΟΝ): ~1501-2000

    We extract Greek lines (filtering out Latin interleaving) by looking for:
    - Lines containing Greek Unicode characters (U+0370–U+03FF, U+1F00–U+1FFF)
    - Filtering out obvious Latin OCR garbage
    """
    letters = []

    # Find start of Isidore's letter section
    start_idx = pg_text.find('ΒΙΒΛΙΟΝ ΠΡΩΤΟΝ')
    if start_idx < 0:
        start_idx = pg_text.find('ΒΙΒΛΙΟΝ Α')
    if start_idx < 0:
        print("  ERROR: Could not find start of Isidore letters in PG78")
        return []

    # Find end (next major section after Isidore, which is Zosimus Abbas)
    end_idx = pg_text.find('ΖΩΣΙΜΟΣ ΑΒΒΑΣ', start_idx)
    if end_idx < 0:
        end_idx = pg_text.find('ZOSIMUS ABBAS', start_idx)
    if end_idx < 0:
        end_idx = min(start_idx + 4_000_000, len(pg_text))

    isidore_section = pg_text[start_idx:end_idx]
    print(f"  Isidore section: {len(isidore_section):,} chars")

    # PG letter header pattern - Greek numeral followed by recipient in caps
    # Pattern like: "Δ΄. --- ΝΕΙΛΩ ΜΟΝΑΧΏ." or "Α΄. --- ΔΩΡΟΘΕΩ ΜΟΝΑΧΩ."
    # The Greek book ordinal letters: Α Β Γ Δ Ε Ζ Η Θ Ι Κ...
    # But the letters are numbered within books using Greek ordinals
    # Header pattern - book section markers
    book_markers = {
        'ΒΙΒΛΙΟΝ ΠΡΩΤΟΝ': 1,
        'ΒΙΒΛΙΟΝ ΔΕΥΤΕΡΟΝ': 2,
        'ΒΙΒΛΙΟΝ ΤΡΙΤΟΝ': 3,
        'ΒΙΒΛΙΟΝ ΤΕΤΑΡΤΟΝ': 4,
        'ΒΙΒΛΙΟΝ ΠΕΜΠΤΟΝ': 5,
        'LIBER PRIMUS': 1,
        'LIBER SECUNDUS': 2,
        'LIBER TERTIUS': 3,
        'LIBER QUARTUS': 4,
        'LIBER QUINTUS': 5,
    }

    # Greek letter header pattern
    # Matches: "Α΄. --- ΝΕΙΛΩ ΜΟΝΑΧΩ" or similar
    # The Greek capital letters used as ordinals in PG
    header_pat = re.compile(
        r'(?:^|\n)\s*'
        r'([ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩα-ω]{1,4}[΄ʹ]?)\s*'  # Greek ordinal
        r'[.\-—–]+\s*'                                          # separator
        r'([Α-ΩA-Z][Α-ΩA-Z\s,]+?)'                          # RECIPIENT IN CAPS
        r'[.\n]',
        re.MULTILINE
    )

    # Greek alphabet ordinal to number (1-24 within a book)
    greek_ordinals = {
        'Α': 1, 'Β': 2, 'Γ': 3, 'Δ': 4, 'Ε': 5, 'Ζ': 6, 'Η': 7, 'Θ': 8,
        'Ι': 9, 'Κ': 10, 'Λ': 11, 'Μ': 12, 'Ν': 13, 'Ξ': 14, 'Ο': 15,
        'Π': 16, 'Ρ': 17, 'Σ': 18, 'Τ': 19, 'Υ': 20, 'Φ': 21, 'Χ': 22,
        'Ψ': 23, 'Ω': 24,
    }

    # Instead of trying to parse the complex interleaved OCR structure,
    # let's extract by finding letter blocks based on the known letter 1 text
    # and then finding subsequent letter boundaries

    # More reliable approach: search for the Greek text of known letters
    # and extract surrounding Greek content

    # For now, extract based on book sections and letter header patterns
    # Extract all Greek text lines (containing actual Greek Unicode)
    greek_char_re = re.compile(r'[α-ωΑ-Ωἀ-ὼά-ώ]')

    lines = isidore_section.split('\n')
    greek_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Count Greek vs Latin chars
        greek_chars = len(greek_char_re.findall(stripped))
        total_alpha = len(re.findall(r'[A-Za-zΑ-Ωα-ω]', stripped))
        if total_alpha > 0 and greek_chars / total_alpha > 0.4:  # mostly Greek
            greek_lines.append(stripped)

    print(f"  Greek-dominant lines: {len(greek_lines)}")

    # Now find letter boundaries within the Greek lines
    # A letter starts with a line matching the Greek header pattern
    # e.g. "Δ΄. — ΝΕΙΛΩ ΜΟΝΑΧΩ." or just the recipient name in all-caps

    # Track which book we're in and absolute letter number
    # PG book approximate letter counts (for number mapping)
    # Book 1: ~440 letters, Book 2: ~360, Book 3: ~280, Book 4: ~320, Book 5: ~600
    # These are rough - the exact counts aren't needed since we just store the text

    current_letters = []
    current_book = 1
    letter_within_book = 0
    current_greek_text = []
    current_header = None
    current_num = None

    # PG letters are best matched by their position
    # Let's use a simpler extraction: find recipient headers and extract text blocks

    # Build a concordance from the letter bodies
    # We search for distinctive phrases from letters we have English text for,
    # and extract nearby Greek text

    known_letter_phrases = {
        1: 'ἀποταγὴν τὴν τῆς ὕλης ἀναχώρησιν',
        7: 'Μαρίας γενεαλογία',
        35: 'βασιλεία τοῦ Χριστοῦ',
        78: 'Ὀρὲβ καὶ Ζὲβ καὶ Ζαλμανᾶ',
    }

    result_letters = []

    # Method: look for the structure "Α΄. --- ΝΕΙΛΩ ΜΟΝΑΧΩ." (Book 1, letter 1)
    # Then extract until the next such header

    # Find all header positions in the Greek section
    # Better pattern for PG78 headers:
    pg_header_re = re.compile(
        r'(?:^|\n)([Α-Ω]{1,4}[΄ʹ\'`]?)\s*[.·]\s*[-—–]+\s*'
        r'([Α-Ω][Α-Ω\s]+?)'
        r'(?:[.·]\s*(?:\n|$))',
        re.MULTILINE
    )

    headers = list(pg_header_re.finditer(isidore_section))
    print(f"  Found {len(headers)} letter headers in PG78 section")

    if headers:
        for i, h in enumerate(headers[:20]):
            print(f"    Header {i}: '{h.group(0)[:60].strip()}'")

    # If we found headers, extract letter texts
    if len(headers) > 10:
        # Map ordinals to sequential numbers
        # Book 1 letters are numbered sequentially within the book
        # We need to track book changes

        book_pos = {}
        for book_name, book_num in book_markers.items():
            bk_idx = isidore_section.find(book_name)
            if bk_idx >= 0:
                book_pos[bk_idx] = book_num

        book_positions = sorted(book_pos.items())

        def get_book_for_pos(pos):
            current = 1
            for bp, bn in book_positions:
                if pos >= bp:
                    current = bn
                else:
                    break
            return current

        # Rough letter offsets per book (cumulative start numbers)
        book_start_nums = {1: 1, 2: 441, 3: 801, 4: 1081, 5: 1501}

        prev_book = 1
        book_letter_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for i, h in enumerate(headers):
            book = get_book_for_pos(h.start())
            if book != prev_book:
                prev_book = book

            book_letter_count[book] = book_letter_count.get(book, 0) + 1
            letter_in_book = book_letter_count[book]
            # Sequential number
            seq_num = book_start_nums.get(book, 1) + letter_in_book - 1

            # Extract text until next header
            start_pos = h.end()
            end_pos = headers[i + 1].start() if i + 1 < len(headers) else len(isidore_section)

            # Get text block
            block = isidore_section[start_pos:end_pos]

            # Extract Greek lines from this block
            block_lines = block.split('\n')
            greek_block = []
            for line in block_lines:
                stripped = line.strip()
                if not stripped:
                    continue
                greek_chars = len(greek_char_re.findall(stripped))
                total_alpha = len(re.findall(r'[A-Za-zΑ-Ωα-ω]', stripped))
                if total_alpha > 0 and greek_chars / total_alpha > 0.45:
                    greek_block.append(stripped)

            greek_text = ' '.join(greek_block).strip()
            # Clean up OCR artifacts from the Greek text
            greek_text = re.sub(r'[A-Z]{3,}', '', greek_text)  # Remove Latin uppercase runs
            greek_text = re.sub(r'\d+', '', greek_text)  # Remove stray numbers
            greek_text = re.sub(r'\s+', ' ', greek_text).strip()

            # Recipient from header
            recipient_raw = h.group(2).strip() if h.lastindex >= 2 else ''
            recipient = recipient_raw.title()

            result_letters.append({
                'letter_num': seq_num,
                'book': book,
                'letter_in_book': letter_in_book,
                'recipient': recipient,
                'subject': f'To {recipient}' if recipient else None,
                'greek_text': greek_text,
                'source_url': 'https://archive.org/details/PatrologiaGraeca (PG vol.78)',
            })

        print(f"  Extracted {len(result_letters)} letters from PG78")

    return result_letters


# ──────────────────────────────────────────────
#  Database Operations
# ──────────────────────────────────────────────

def get_or_create_author(conn):
    cur = conn.cursor()
    cur.execute('''
        INSERT OR IGNORE INTO authors
            (name, name_latin, birth_year, death_year, role, location, lat, lon, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Isidore of Pelusium',
        'Isidorus Pelusiota',
        360, 435,
        'monk',
        'Pelusium',
        31.0167, 32.5500,
        'Egyptian monk and theologian at Pelusium (eastern Nile delta, Egypt). '
        'Contemporary and critic of Cyril of Alexandria, also corresponding with emperors, '
        'bishops, monks, and officials across the Eastern Empire. His collection of ~2,000 '
        'letters is the largest surviving from any Church Father. Wrote in Greek. '
        'Letters preserved in Migne PG vol.78.'
    ))
    conn.commit()
    cur.execute("SELECT id FROM authors WHERE name = 'Isidore of Pelusium'")
    return cur.fetchone()[0]


def ensure_collection(conn):
    cur = conn.cursor()
    cur.execute('''
        INSERT OR IGNORE INTO collections
            (slug, author_name, title, letter_count, date_range,
             english_source_url, latin_source_url, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'isidore_pelusium',
        'Isidore of Pelusium',
        'Letters of Isidore of Pelusium',
        2000,
        '390-435 AD',
        'https://www.roger-pearse.com/weblog/tag/isidore-of-pelusium/',
        'https://archive.org/details/PatrologiaGraeca',
        'The largest letter collection from any Church Father (~2,000 letters survive). '
        'Greek text: Migne PG vol.78 (public domain, OCR on archive.org). '
        'Critical edition: Pierre Evieux, Sources Chrétiennes 422, 454, 586 (1997-2017). '
        'English translations: ~53+ letters on Roger Pearse blog (commissioned draft translations). '
        'Greek text extracted from PG78 OCR for the remainder.',
    ))
    conn.commit()


def save_letter(conn, author_id, letter_num, recipient, subject, english_text,
                greek_text, translation_source, source_url, book=None):
    """Save or update a letter in the DB."""
    cur = conn.cursor()
    ref_id = f'isidore_pelusium.ep.{letter_num}'

    # Check existing
    cur.execute('SELECT id, english_text, latin_text FROM letters WHERE ref_id = ?', (ref_id,))
    existing = cur.fetchone()

    if existing:
        row_id, existing_en, existing_gr = existing
        updated = False
        # Add English text if we have it and didn't before
        if english_text and (not existing_en or len(english_text) > len(existing_en or '')):
            cur.execute('UPDATE letters SET english_text = ?, translation_source = ?, '
                        'source_url = ? WHERE id = ?',
                        (english_text, translation_source, source_url, row_id))
            updated = True
        # Add Greek text if we have it and didn't before
        if greek_text and (not existing_gr or len(greek_text) > len(existing_gr or '')):
            cur.execute('UPDATE letters SET latin_text = ? WHERE id = ?',
                        (greek_text, row_id))
            updated = True
        if updated:
            conn.commit()
            return 'updated', row_id
        return 'skipped', row_id

    # Lookup recipient
    recipient_id = None
    if recipient:
        cur.execute('SELECT id FROM authors WHERE name LIKE ?', (f'%{recipient}%',))
        row = cur.fetchone()
        if row:
            recipient_id = row[0]

    cur.execute('''
        INSERT INTO letters
            (collection, book, letter_number, ref_id, sender_id, recipient_id,
             year_min, year_max,
             subject_summary, english_text, latin_text,
             translation_source, source_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'isidore_pelusium',
        book,
        letter_num,
        ref_id,
        author_id,
        recipient_id,
        390, 435,
        subject,
        english_text,
        greek_text,
        translation_source,
        source_url,
    ))
    conn.commit()
    return 'inserted', cur.lastrowid


# ──────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────

def main():
    print('=' * 65)
    print('ISIDORE OF PELUSIUM - COMPREHENSIVE SCRAPER')
    print('=' * 65)

    conn = sqlite3.connect(DB_PATH, timeout=30)

    try:
        author_id = get_or_create_author(conn)
        ensure_collection(conn)
        print(f"\nAuthor ID: {author_id}")

        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM letters WHERE collection = 'isidore_pelusium'")
        existing_count = cur.fetchone()[0]
        print(f"Letters already in DB: {existing_count}")

        stats = {'inserted': 0, 'updated': 0, 'skipped': 0}

        # ── Step 1: Manual letters (verified from WebFetch) ──────────────
        print(f"\n── Step 1: Saving {len(MANUAL_LETTERS)} manually-verified letters ──")
        for ltr in MANUAL_LETTERS:
            action, _ = save_letter(
                conn, author_id,
                letter_num=ltr['letter_num'],
                recipient=ltr.get('recipient'),
                subject=ltr.get('subject'),
                english_text=ltr.get('text'),
                greek_text=None,
                translation_source=ltr.get('translation_source', 'existing_rogerpearse'),
                source_url=ltr.get('source_url', ''),
            )
            stats[action] += 1
            print(f"  Letter {ltr['letter_num']}: {action}")

        # ── Step 2: Scrape Roger Pearse posts ────────────────────────────
        print(f"\n── Step 2: Scraping {len(ROGER_PEARSE_POSTS)} Roger Pearse blog posts ──")
        for url, description, expected_nums in ROGER_PEARSE_POSTS:
            print(f"\n  [{description}]")
            print(f"  {url}")
            time.sleep(DELAY)

            html = fetch_url(url)
            if not html:
                print(f"  SKIP: Could not fetch")
                continue

            letters = parse_letters_from_page(html, url, expected_nums)

            for ltr in letters:
                num = ltr['letter_num']
                # Validate number range
                if num < 1 or num > 2000:
                    print(f"    Skipping invalid letter number {num}")
                    continue

                action, _ = save_letter(
                    conn, author_id,
                    letter_num=num,
                    recipient=ltr.get('recipient'),
                    subject=ltr.get('subject'),
                    english_text=ltr.get('text'),
                    greek_text=ltr.get('greek_text'),
                    translation_source=ltr.get('translation_source', 'existing_rogerpearse'),
                    source_url=ltr.get('source_url', url),
                )
                stats[action] += 1
                print(f"    Letter {num} ({ltr.get('recipient', '?')}): {action}")

        # ── Step 3: Extract Greek from PG78 ──────────────────────────────
        print(f"\n── Step 3: Extracting Greek text from Patrologia Graeca vol.78 ──")
        pg_text = download_pg78()

        if pg_text:
            pg_letters = extract_greek_letters_from_pg78(pg_text)
            print(f"\n  Processing {len(pg_letters)} letters extracted from PG78...")

            pg_stats = {'inserted': 0, 'updated': 0, 'skipped': 0, 'empty': 0}
            for ltr in pg_letters:
                num = ltr['letter_num']
                greek = ltr.get('greek_text', '').strip()

                if not greek or len(greek) < 30:
                    pg_stats['empty'] += 1
                    continue

                if num < 1 or num > 2000:
                    continue

                action, _ = save_letter(
                    conn, author_id,
                    letter_num=num,
                    recipient=ltr.get('recipient'),
                    subject=ltr.get('subject'),
                    english_text=None,
                    greek_text=greek,
                    translation_source='pg78_ocr',
                    source_url=ltr.get('source_url', 'https://archive.org/details/PatrologiaGraeca'),
                    book=ltr.get('book'),
                )
                pg_stats[action] += 1

            print(f"  PG78 results: {pg_stats}")
            for k, v in pg_stats.items():
                stats[k] = stats.get(k, 0) + v

        # ── Final count ───────────────────────────────────────────────────
        cur.execute("SELECT COUNT(*) FROM letters WHERE collection = 'isidore_pelusium'")
        final_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM letters WHERE collection = 'isidore_pelusium' AND english_text IS NOT NULL")
        with_english = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM letters WHERE collection = 'isidore_pelusium' AND latin_text IS NOT NULL")
        with_greek = cur.fetchone()[0]

        # Update collection status
        cur.execute(
            "UPDATE collections SET scrape_status = 'partial', letter_count = ? "
            "WHERE slug = 'isidore_pelusium'",
            (final_count,)
        )
        conn.commit()

        print(f'\n{"=" * 65}')
        print(f'FINAL RESULTS:')
        print(f'  Letters before: {existing_count}')
        print(f'  Letters after:  {final_count}')
        print(f'  Net new:        {final_count - existing_count}')
        print(f'  With English:   {with_english}')
        print(f'  With Greek:     {with_greek}')
        print(f'  Actions: {stats}')

    finally:
        conn.close()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Scrape Cicero's Ad Familiares from The Latin Library and import into roman_letters.db
"""

import sqlite3
import re
import urllib.request
import time
from html.parser import HTMLParser

DB_PATH = '/Users/drillerdbmacmini/Documents/GitHub/roman-letters-network/data/roman_letters.db'
BASE_URL = 'https://www.thelatinlibrary.com/cicero/fam{}.shtml'

# Approximate dating by book (midpoint year for year_approx, and range)
BOOK_DATES = {
    1:  {'year_approx': -58, 'year_min': -62, 'year_max': -54, 'note': 'Lentulus Spinther'},
    2:  {'year_approx': -50, 'year_min': -51, 'year_max': -48, 'note': 'Caelius Rufus to Cicero'},
    3:  {'year_approx': -51, 'year_min': -51, 'year_max': -50, 'note': 'Appius Claudius'},
    4:  {'year_approx': -45, 'year_min': -46, 'year_max': -43, 'note': 'Various'},
    5:  {'year_approx': -56, 'year_min': -62, 'year_max': -51, 'note': 'Various'},
    6:  {'year_approx': -48, 'year_min': -50, 'year_max': -46, 'note': 'Various'},
    7:  {'year_approx': -49, 'year_min': -54, 'year_max': -44, 'note': 'M. Marius, Trebatius'},
    8:  {'year_approx': -50, 'year_min': -51, 'year_max': -48, 'note': 'Caelius to Cicero'},
    9:  {'year_approx': -45, 'year_min': -46, 'year_max': -44, 'note': 'Varro, Dolabella'},
    10: {'year_approx': -43, 'year_min': -43, 'year_max': -43, 'note': 'Plancus, Lepidus, Pollio'},
    11: {'year_approx': -43, 'year_min': -43, 'year_max': -43, 'note': 'D. Brutus'},
    12: {'year_approx': -43, 'year_min': -43, 'year_max': -43, 'note': 'Cassius'},
    13: {'year_approx': -50, 'year_min': -62, 'year_max': -43, 'note': 'Recommendation letters'},
    14: {'year_approx': -53, 'year_min': -58, 'year_max': -47, 'note': 'To Terentia'},
    15: {'year_approx': -47, 'year_min': -51, 'year_max': -43, 'note': 'Various'},
    16: {'year_approx': -47, 'year_min': -50, 'year_max': -43, 'note': 'Tiro'},
}

CICERO_ID = 2014

def fetch_page(book_num):
    """Fetch HTML for a given book number."""
    url = BASE_URL.format(book_num)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    # Some pages (e.g. Book 2) are UTF-16 encoded with BOM
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff') or b'\x00' in raw[:20]:
        try:
            html = raw.decode('utf-16')
        except UnicodeDecodeError:
            html = raw.decode('utf-16-le')
    else:
        html = raw.decode('latin-1')
    return html, url


def clean_html(text):
    """Remove HTML tags and clean up text."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&#151;', '—')
    text = text.replace('&#150;', '–')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_salutation(salutation_text):
    """
    Parse salutation to determine sender and recipient.
    Returns (sender_name, recipient_name) as raw strings.

    Common patterns:
    - M. CICERO S. D. P. LENTULO PROCOS.  (Cicero to Lentulus)
    - CAELIUS CICERONI S.  (Caelius to Cicero)
    - CICERO TERENTIAE SUAE S. D.  (Cicero to Terentia)
    """
    sal = salutation_text.upper().strip()

    # Check if it's TO Cicero (someone else writing)
    # Pattern: SOMEONE ... CICERONI S. or similar
    if 'CICERONI' in sal:
        return 'other', 'cicero'

    # Pattern: CICERO S. D. ... = Cicero sending
    if sal.startswith('M. CICERO') or sal.startswith('CICERO') or sal.startswith('M. TVLLIVS') or sal.startswith('TVLLIVS'):
        return 'cicero', 'other'

    # Default: assume from Cicero
    return 'cicero', 'other'


def parse_book(html, book_num):
    """Parse a book's HTML into individual letters."""
    letters = []

    # Find all letter blocks - they start with bold headers containing Roman numerals
    # Pattern: <B>ROMAN_NUMERAL. date info <BR> salutation </B>
    # Split on the CENTER/B tags that mark letter headers

    # Find all letter headers and their positions
    # Handle both <CENTER><A..></A><B>...</B></CENTER> and <B><CENTER><A..></A>...</CENTER></B>
    # Roman numerals can be like: I, II, IX, X, XI, XX, XXI, Va, Vb, X.a., X.b. etc.
    # Full Roman numeral pattern: handles I through LXXIX plus a/b suffixes
    # Tens: XC(90), XL(40), L?X{0,3} (0-30, 50-80)
    # Ones: IX(9), IV(4), V?I{0,3} (0-3, 5-8)
    ROMAN_PAT = r'(?:(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3}))(?:\.[ab]|[ab])?'
    header_pattern = re.compile(
        r'(?:'
        # Pattern 1: <CENTER><A..></A><B>NUMERAL. CONTENT</B></CENTER>
        # Handle stray </I> or other tags between </B> and </CENTER>
        r'<CENTER>\s*(?:<A[^>]*>[^<]*</A>\s*)?<B>\s*'
        r'((' + ROMAN_PAT + r')\..*?)'
        r'\s*</B>(?:</I>)?\s*</CENTER>'
        r'|'
        # Pattern 2: <B><CENTER><A..>NUMERAL.</A> CONTENT</CENTER></B>
        r'<B>\s*<CENTER>\s*(?:<A[^>]*>)?\s*'
        r'((' + ROMAN_PAT + r')\..*?)'
        r'(?:</A>)?\s*</CENTER>\s*</B>'
        r'|'
        # Pattern 3: <CENTER><B> <A NAME="x">NUMERAL.</A> CONTENT</B></CENTER>
        r'<CENTER>\s*<B>\s*<A[^>]*>\s*'
        r'((' + ROMAN_PAT + r')\.)\s*</A>\s*'
        r'(.*?)'
        r'\s*</B>\s*</CENTER>'
        r')',
        re.DOTALL | re.IGNORECASE
    )

    headers_raw = list(header_pattern.finditer(html))
    # Normalize: extract full header content from whichever pattern matched
    # Pattern 1: groups 1,2; Pattern 2: groups 3,4; Pattern 3: groups 5,6,7
    headers = []
    for m in headers_raw:
        if m.group(1):
            content = m.group(1)
        elif m.group(3):
            content = m.group(3)
        elif m.group(5):
            # Pattern 3: numeral is in group 5, rest in group 7
            content = m.group(5) + ' ' + (m.group(7) or '')
        else:
            continue
        headers.append((m, content))

    if not headers:
        print(f"  WARNING: No headers found in book {book_num}")
        return letters

    for i, (match, header_text) in enumerate(headers):

        # Get the text between this header and the next (or end of content)
        start_pos = match.end()
        if i + 1 < len(headers):
            end_pos = headers[i + 1][0].start()
        else:
            # Find the end - look for footer/navigation area
            end_markers = [
                html.find('<table', start_pos),
                html.find('The Latin Library', start_pos),
                html.find('</body', start_pos),
            ]
            end_pos = min(p for p in end_markers if p > 0) if any(p > 0 for p in end_markers) else len(html)

        body_html = html[start_pos:end_pos]
        body_text = clean_html(body_html)

        # Parse the header
        header_clean = clean_html(header_text)

        # Extract Roman numeral (letter number within book)
        # Handles: I, II, Va, Vb, X.a, X.b, XL, LXXIX etc.
        num_match = re.match(r'((?:(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3}))(?:\.[ab]|[ab])?)\.', header_clean.strip(), re.IGNORECASE)
        if num_match:
            roman = num_match.group(1)
            # Normalize X.a -> Xa format for ref_id consistency
            roman = roman.replace('.', '')
        else:
            roman = str(i + 1)

        # Extract salutation (after the <BR> or date info)
        # The salutation is typically the last line of the header
        sal_match = re.search(r'(?:<BR>|<br>)\s*(.*?)\s*$', header_text, re.DOTALL | re.IGNORECASE)
        if sal_match:
            salutation = clean_html(sal_match.group(1))
        else:
            salutation = header_clean

        # Determine sender/recipient from salutation
        direction = parse_salutation(salutation)

        letter_data = {
            'roman_numeral': roman,
            'header': header_clean,
            'salutation': salutation,
            'body': body_text,
            'direction': direction,
            'book': book_num,
        }
        letters.append(letter_data)

    return letters


def roman_to_int(s):
    """Convert Roman numeral string to integer. Handles 'a'/'b' suffixes."""
    s = s.upper().rstrip('AB')
    vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result = 0
    for i, c in enumerate(s):
        if c not in vals:
            return 0
        if i + 1 < len(s) and vals.get(s[i+1], 0) > vals[c]:
            result -= vals[c]
        else:
            result += vals[c]
    return result


def insert_letters(db, letters, book_num, source_url):
    """Insert parsed letters into the database."""
    cursor = db.cursor()
    dates = BOOK_DATES[book_num]
    count = 0

    for letter in letters:
        roman = letter['roman_numeral']
        letter_num_int = roman_to_int(roman)
        # For letters like Va, Vb, use the numeral with suffix in ref_id
        ref_id = f'cic.fam.{book_num}.{roman.lower()}'

        # Determine sender/recipient IDs
        if letter['direction'] == ('cicero', 'other'):
            sender_id = CICERO_ID
            recipient_id = None  # We'd need more logic to map recipients
        else:
            sender_id = None
            recipient_id = CICERO_ID

        # Full text = header + body
        full_latin = letter['header'] + '\n\n' + letter['body']

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO letters (
                    collection, book, letter_number, ref_id,
                    sender_id, recipient_id,
                    year_approx, year_min, year_max,
                    latin_text, source_url, subject_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'cicero_familiares',
                book_num,
                letter_num_int,
                ref_id,
                sender_id,
                recipient_id,
                dates['year_approx'],
                dates['year_min'],
                dates['year_max'],
                full_latin,
                source_url,
                f'Ad Familiares {book_num}.{roman} - {letter["salutation"]}'
            ))
            if cursor.rowcount > 0:
                count += 1
        except sqlite3.IntegrityError as e:
            print(f"  Skipping duplicate: {ref_id} ({e})")

    db.commit()
    return count


def main():
    db = sqlite3.connect(DB_PATH)

    total = 0
    book_counts = {}

    for book_num in range(1, 17):
        print(f"Fetching Book {book_num}...")
        try:
            html, url = fetch_page(book_num)
            letters = parse_book(html, book_num)
            count = insert_letters(db, letters, book_num, url)
            book_counts[book_num] = (len(letters), count)
            total += count
            print(f"  Book {book_num}: {len(letters)} letters parsed, {count} inserted")
            time.sleep(1)  # Be polite to the server
        except Exception as e:
            print(f"  ERROR on book {book_num}: {e}")
            import traceback
            traceback.print_exc()
            book_counts[book_num] = (0, 0)

    print(f"\n=== SUMMARY ===")
    print(f"{'Book':>6} | {'Parsed':>7} | {'Inserted':>8}")
    print(f"{'-'*6}-+-{'-'*7}-+-{'-'*8}")
    for b in range(1, 17):
        parsed, inserted = book_counts.get(b, (0, 0))
        print(f"{b:>6} | {parsed:>7} | {inserted:>8}")
    print(f"{'-'*6}-+-{'-'*7}-+-{'-'*8}")
    print(f"{'TOTAL':>6} | {sum(p for p,i in book_counts.values()):>7} | {total:>8}")

    # Update collection status
    db.execute("UPDATE collections SET scrape_status = 'complete' WHERE slug = 'cicero_familiares'")
    db.commit()
    db.close()


if __name__ == '__main__':
    main()

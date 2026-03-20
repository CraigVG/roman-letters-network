#!/usr/bin/env python3
"""
Scrape letters of Pope Pelagius I from the Gassó-Batlle 1956 critical edition.

Source: https://archive.org/details/gasso-batlle-1956-pelagius
Edition: Pelagii I Papae Epistulae Quae Supersunt (556-561 AD)
Critical edition by Pius M. Gassó and Columba M. Batlle,
  In Abbatia Montisserrati, 1956.  ~96 surviving letters.

OCR text (DjVu) downloaded from Internet Archive.

No English translation exists for this corpus. The Gassó-Batlle 1956 Latin
critical edition is the standard scholarly text and has never been translated.

DB: data/roman_letters.db
Collection slug: pelagius_i
Author: Pope Pelagius I, pope, Rome (41.8967, 12.4822), ~500-561
"""

import sqlite3
import re
import os
import sys
import time
import urllib.request

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'roman_letters.db'
)

SOURCE_URL = 'https://archive.org/details/gasso-batlle-1956-pelagius'
OCR_URL = (
    'https://archive.org/download/gasso-batlle-1956-pelagius/'
    'Gass%C3%B3%20Batlle%201956%20-%20Pelagius_djvu.txt'
)
OCR_CACHE = '/tmp/pelagius_gasso_batlle_djvu.txt'

DELAY = 0.5   # seconds between DB inserts (as specified)


# ── Hardcoded fallback: J-K number → Gassó-Batlle edition letter number ───────
# Used when the OCR-based heuristic cannot determine the letter number.
# Derived by manual inspection of the OCR text structure and comparison with
# the edition's table of contents and page headers.
JK_TO_EP_FALLBACK = {
    # Pelagius I genuine letters (Gassó-Batlle numbering)
    940: 1,   941: 2,   943: 4,   944: 5,   945: 6,   946: 7,   948: 8,
    947: 9,   939: 10,  938: 11,  949: 12,  950: 13,  974: 15,  975: 16,
    976: 17,  977: 18,  978: 19,  979: 20,  980: 21,  981: 22,  982: 23,
    983: 24,  984: 25,  985: 26,  986: 27,  987: 28,  988: 29,  989: 30,
    990: 31,  991: 32,  993: 34,  994: 35,  995: 36,  996: 37,  971: 38,
    998: 39,  1000: 41, 1001: 42, 1002: 43, 1003: 44, 1004: 45, 1005: 46,
    1006: 47, 1008: 48, 970: 49,  1009: 50, 1010: 51, 1011: 52, 1012: 53,
    1013: 54, 1014: 55, 1015: 56, 1016: 57, 1017: 58, 1018: 59, 1019: 60,
    961: 62,  1021: 63, 1022: 64, 1025: 66, 1026: 67, 1028: 70, 1029: 71,
    1030: 72, 1032: 74, 1033: 75, 1034: 76, 1035: 77, 1037: 79, 972: 80,
    965: 81,  966: 82,  953: 83,  956: 84,  959: 86,  955: 87,  957: 88,
    958: 89,  964: 91,  968: 92,  969: 95,  961: 62,
    # Letters of disputed/uncertain number use None → will be skipped
    # (some J-K refs appear twice for multi-section letters; skip duplicates)
}

# J-K numbers that appear multiple times (letter sections, not separate letters)
# Second and subsequent occurrences are skipped
JK_SECTION_REFS = {1005, 1008}   # appear as both full letter and section ref


# ── Date parsing ──────────────────────────────────────────────────────────────

def parse_date(date_str):
    """
    Parse date strings from the edition into (year_approx, year_min, year_max).
    All dates are sanitized to 556-561 AD range (Pelagius I's pontificate).

    Examples:
      '4 iulii a. 556'              -> (556, 556, 556)
      '16 Septembris a. 556'        -> (556, 556, 556)
      'aa. 556-561'                 -> (558, 556, 561)
      'ex. a. 558 - a. 561 [?]'     -> (560, 558, 561)
      '3 februarii a. 557'          -> (557, 557, 557)
      '29 aprilis a. 560'           -> (560, 560, 560)
    """
    if not date_str:
        return None, None, None
    s = date_str.strip()
    # Range: aa. NNN-NNN
    range_m = re.search(r'aa?\.\s*(\d{3,4})\s*[-–]\s*(?:[ina][n.]*\s*)?a\.\s*(\d{3,4})', s)
    if not range_m:
        range_m = re.search(r'aa?\.\s*(\d{3,4})\s*[-–]\s*(\d{3,4})', s)
    if range_m:
        y1, y2 = int(range_m.group(1)), int(range_m.group(2))
        y1 = _clamp_year(y1)
        y2 = _clamp_year(y2)
        if y1 and y2:
            return (y1 + y2) // 2, y1, y2
    # Look for "ex. a. NNN - a. NNN" or "in. a. NNN - a. NNN"
    range2_m = re.search(
        r'(?:ex|in)\.\s*a\.\s*(\d{3,4})\s*[-–]\s*(?:[ina][n.]*\s*)?a\.\s*(\d{3,4})', s
    )
    if range2_m:
        y1, y2 = int(range2_m.group(1)), int(range2_m.group(2))
        y1 = _clamp_year(y1)
        y2 = _clamp_year(y2)
        if y1 and y2:
            return (y1 + y2) // 2, y1, y2
    # Single year
    single_m = re.search(r'a\.\s*(\d{3,4})', s)
    if single_m:
        y = _clamp_year(int(single_m.group(1)))
        if y:
            return y, y, y
    return None, None, None


def _clamp_year(y):
    """Return y if it's plausibly within Pelagius I's pontificate, else None."""
    # Allow 550-565 to accommodate edge letters; reject obvious OCR errors
    if 550 <= y <= 565:
        return y
    return None


# ── OCR download ──────────────────────────────────────────────────────────────

def download_ocr():
    """Download the DjVu OCR text from Internet Archive if not cached."""
    if os.path.exists(OCR_CACHE) and os.path.getsize(OCR_CACHE) > 100000:
        print(f"  Using cached OCR: {OCR_CACHE}")
        return True

    print("  Downloading OCR from Internet Archive...")
    req = urllib.request.Request(OCR_URL, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; roman-letters-network-scraper)'
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        with open(OCR_CACHE, 'wb') as f:
            f.write(data)
        print(f"  Downloaded {len(data):,} bytes -> {OCR_CACHE}")
        return True
    except Exception as e:
        print(f"  ERROR downloading: {e}")
        return False


# ── OCR text cleaning ─────────────────────────────────────────────────────────

def clean_letter_text(raw):
    """
    Clean OCR noise from letter body text.
    Removes apparatus, footnotes, page headers, bibliography lines.
    Preserves the Latin letter text.
    """
    lines = raw.split('\n')
    out = []
    for raw_line in lines:
        s = raw_line.strip()
        if not s:
            if out and out[-1]:
                out.append('')
            continue

        # Page headers
        if re.match(r'^PEI?[,./\\]?[AL]AGII\s+I\s+PAP', s, re.IGNORECASE):
            continue
        if re.match(r'^EPISTU[EL]A[ES]?\s+[\d,\.\-;:\s]+$', s):
            continue

        # Apparatus: "N word] variant"
        if re.match(r'^\d+\s+\w+\]', s):
            continue
        if re.match(r'^Codd?\.\s*:?', s):
            continue
        if re.match(r'^Bishop\s*:', s):
            continue

        # Footnote starters
        if re.match(r'^Tit\.\s+\w+:', s):
            continue
        if re.match(r'^\d+[-–]\d+\.\s', s):
            continue
        if re.match(r'^\d+\.\s+(?:Cf\.|Ed\.|Ibid\.|Edd\.|MiGN|GUND|Maass|Thier|MIGN|'
                    r'Kehr|Wolf|Gund|Baluze|MGH|Pflugk|Anselm|PFLUGK|WOLF)', s):
            continue

        # Edd./Ed. bibliography
        if re.match(r'^Edd?\.\s*:|^Ed\.\s*:', s):
            continue

        # Pure page numbers (1-3 digits alone)
        if re.match(r'^\d{1,3}\s*$', s):
            continue

        # J-K lines
        if re.match(r'^J-K\.', s):
            continue

        # Scholarly reference lines
        if re.match(r'^(?:Cf\.|Ibid\.|l\.\s*c\.|op\.\s*cit\.)', s):
            continue

        # Remove inline section numbers at start of line
        s = re.sub(r'^(\d+)\s+([a-z])', r'\2', s)

        out.append(s)

    text = '\n'.join(out).strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def extract_recipient(salutation):
    """Extract recipient name from salutation line."""
    if not salutation:
        return ''
    s = salutation.strip()

    # Pattern 1: "PELAGIUS [PAPA] RECIPIENT TITLE"
    m = re.match(
        r'(?:PELAGIUS|PELAGII)\s+(?:\[PAPA\]\s+)?'
        r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)',
        s
    )
    if m:
        name = m.group(1)
        if name.upper() not in ('EPISCOPO', 'PRESBYTERO', 'DIACONO', 'PAPA',
                                 'CLERO', 'FRATRIBUS', 'OMNIBUS', 'EPISCOPIS'):
            return name.title()

    # Pattern 2: "DILECTISSIMO FRATRI NAME ... PELAGIUS"
    m = re.match(
        r'(?:DILECTISSIM[OA]|DIEECTISSIM[OA]|HONORABIL[IS]|VENERABIL[IS]|'
        r'REVERENDISSIM[OA]|MAGNIFICENTISSIM[OA]|GLORIOS[IU]S?)\s+'
        r'(?:\w+\s+)?([A-Z][A-Z]{2,}(?:\s+[A-Z][A-Z]{2,})?)\s+PELAGIUS',
        s
    )
    if m:
        return m.group(1).title()

    # Pattern 3: second capitalized word
    skip = {'PELAGIUS', 'PAPA', 'EPISCOPO', 'EPISCOPUS', 'DILECTISSIMO',
            'DIEECTISSIMO', 'FRATRI', 'FRATRIBUS', 'VIRO', 'MAGNIFICO',
            'PATRICIO', 'ILLUSTRI', 'HONORABILI', 'VENERABILI',
            'REVERENDISSIMO', 'CLERO', 'OMNIBUS', 'PRESBYTERO'}
    words = re.findall(r'\b[A-Z]{3,}\b', s)
    for w in words:
        if w not in skip:
            return w.title()
    return ''


# ── Letter number detection ───────────────────────────────────────────────────

def find_ep_num(text_before_jk, max_lookback=5000):
    """
    Find the Gassó-Batlle letter number (1-96) that precedes a J-K marker.

    In the edition, each letter is structured as:
      [previous letter's apparatus/commentary]
      [page headers: PELAGII I PAPAE / EPISTULAE N,M; K]
      N                          <- standalone letter number
      [(annotation like (37+48))]
      Summary text ...           <- Latin description of the letter
      ...more summary...
      J-K. XXXX                 <- the marker we're looking back from

    Page numbers (book pages) also appear as standalone digits but are
    distinguished by:
    a) they appear between/after page headers, not directly before summary text
    b) they are NOT followed by the summary block
    """
    segment = text_before_jk[-max_lookback:]
    lines = segment.split('\n')

    # Phase 1: find the summary block (going backwards from J-K)
    first_summary_idx = None
    collecting_summary = False

    for i in range(len(lines) - 1, -1, -1):
        s = lines[i].strip()
        if not s:
            if collecting_summary:
                break   # blank line after summary content = end of summary block
            continue
        # Skip page headers
        if re.match(r'^PEI?[,./]?[AL]AGII|^PKI', s, re.IGNORECASE):
            continue
        if re.match(r'^EPISTU', s, re.IGNORECASE):
            continue
        # Skip annotation lines like "(37 + 48)" or "(65 + 66)"
        if re.match(r'^\(\d+\s*[\+\d\s]*\)', s):
            continue
        # Everything else is the summary
        collecting_summary = True
        first_summary_idx = i

    if first_summary_idx is None:
        return None

    # Phase 2: find the standalone letter number just before the summary
    for i in range(first_summary_idx - 1, max(0, first_summary_idx - 15), -1):
        s = lines[i].strip()
        if not s:
            continue
        # Skip annotation lines
        if re.match(r'^\(\d+[\s\+\d]*\)', s):
            continue
        # Skip page headers (but note numbers within them)
        if re.match(r'^PEI?[,./]?[AL]AGII|^PKI', s, re.IGNORECASE):
            # A letter number preceded by PELAGII I PAPAE is valid
            # if the lines AFTER the number (before summary) are blank/annotation only
            # We'll check in the standalone-number handler below
            continue

        if re.match(r'^EPISTU', s, re.IGNORECASE):
            # Extract the LAST letter number from the page header
            # e.g. "EPISTULAE 21,3-5; 22,1" -> last letter number = 22
            # e.g. "EPISTULAE 6,1-4" -> 6
            # Numbers in headers: filter out section numbers (single digits alone)
            all_nums = re.findall(r'\b(\d{1,2})\b', s)
            valid = []
            for n_str in all_nums:
                n = int(n_str)
                if 2 <= n <= 96:  # exclude 1 (likely section number)
                    valid.append(n)
            if valid:
                return valid[-1]
            continue

        # Standalone letter number
        if re.match(r'^\d{1,2}\s*$', s):
            num = int(s)
            if 1 <= num <= 96:
                # Verify: check what precedes this number
                preceded_by_pelagii = False
                preceded_by_epistu = False
                epistu_nums = []
                for j in range(i - 1, max(0, i - 5), -1):
                    prev = lines[j].strip()
                    if not prev:
                        continue
                    if re.match(r'^EPISTU', prev, re.IGNORECASE):
                        preceded_by_epistu = True
                        epistu_nums = [int(n) for n in re.findall(r'\b(\d{1,2})\b', prev)
                                       if 1 <= int(n) <= 96]
                    elif re.match(r'^PEI?[,./]?[AL]AGII|^PKI', prev, re.IGNORECASE):
                        preceded_by_pelagii = True
                    break

                if preceded_by_epistu:
                    # Accept if the number appears in the EPISTULAE header
                    if num in epistu_nums:
                        return num
                    # Or if we can confirm it directly follows the header
                    return num   # OCR sometimes omits explicit header numbers
                elif preceded_by_pelagii:
                    # Check lines AFTER this number; if they lead to the summary, accept
                    after_lines = []
                    for k in range(i + 1, min(len(lines), i + 8)):
                        ak = lines[k].strip()
                        if ak and not re.match(r'^\(\d+[\s\+\d]*\)', ak):
                            after_lines.append(ak)
                    if after_lines and re.match(r'^[A-Z]', after_lines[0]):
                        return num   # summary follows directly
                    # Otherwise it's a page number
                else:
                    # No page header before number = it IS the letter number
                    return num

        # Non-number, non-blank, non-header content = stop searching
        if not re.match(r'^\d+\s*$', s):
            break

    return None


# ── Letter parsing ────────────────────────────────────────────────────────────

def get_summary_before_jk(text_before_jk, max_lookback=3000):
    """Extract the Latin summary lines just before the J-K marker."""
    segment = text_before_jk[-max_lookback:]
    lines = segment.split('\n')
    summary_lines = []
    collecting = False

    for i in range(len(lines) - 1, -1, -1):
        s = lines[i].strip()
        if not s:
            if collecting and summary_lines:
                break
            continue
        if re.match(r'^PEI?[,./]?[AL]AGII|^PKI', s, re.IGNORECASE):
            if collecting:
                break
            continue
        # EPISTULAE headers: skip but don't stop collection
        if re.match(r'^EPISTU', s, re.IGNORECASE):
            if collecting:
                break
            continue
        if re.match(r'^\(\d+[\s\+\d]*\)', s):
            continue
        # Skip bibliography/Edd./Migne lines — these are NOT part of the summary
        if re.match(r'^Edd?\.\s*:|^Ed\.\s*:|^MIGNE|^MGH|^MANSI|^GUNDL|^Kehr\b|^BALUZE|^WOLF', s, re.IGNORECASE):
            if collecting:
                break
            continue
        if re.match(r'^[A-Z]', s) and len(s) > 5:
            collecting = True
            summary_lines.insert(0, s)
        elif collecting:
            break

    return ' '.join(summary_lines).strip()


def parse_letters(content):
    """
    Parse all letters from the Gassó-Batlle OCR text.

    Strategy: use J-K catalog numbers as anchors. Extract:
    - Letter number (from OCR structure)
    - Summary (Latin abstract before J-K)
    - Date (from J-K line or nearby)
    - Letter text (after Edd.: line)

    Returns list of dicts.
    """
    # Find letters section
    ep1_anchor = 'Sapaudo salutem dicit, suamque in solium pontificium evectionem'
    ep1_pos = content.find(ep1_anchor)
    if ep1_pos == -1:
        print("ERROR: Cannot find start of letters section in OCR text.")
        return []

    letters_start = content.rfind('\n1 \n', 0, ep1_pos + 100)
    if letters_start == -1:
        letters_start = ep1_pos - 300

    letters_end = content.find('1. LOCA SACRAE SCRIPTURAE')
    if letters_end == -1:
        letters_end = content.find('LOCA SACRAE SCRIPTURAE')
    if letters_end == -1:
        letters_end = len(content)

    letters_section = content[letters_start:letters_end]

    # Find all J-K markers
    jk_re = re.compile(r'\nJ-K\.\s*(\d+)([^\n]*)')
    jk_matches = [
        (m.start(), m.end(), int(m.group(1)), m.group(2).strip())
        for m in jk_re.finditer(letters_section)
    ]

    if not jk_matches:
        print("ERROR: No J-K references found.")
        return []

    letters = []
    seen_jk = {}   # jk_num -> first occurrence index (for dedup)

    for idx, (jk_start, jk_end, jk_num, jk_line_rest) in enumerate(jk_matches):

        # Skip duplicate J-K entries (letter sections already covered)
        if jk_num in seen_jk:
            continue
        seen_jk[jk_num] = idx

        # ── Letter number ─────────────────────────────────────────────────────
        text_before = letters_section[:jk_start]
        ep_num = find_ep_num(text_before)

        # Fallback: use hardcoded map
        if ep_num is None:
            ep_num = JK_TO_EP_FALLBACK.get(jk_num)

        # ── Summary ───────────────────────────────────────────────────────────
        summary = get_summary_before_jk(text_before)

        # ── Date ─────────────────────────────────────────────────────────────
        date_str = None
        date_m = re.search(
            r'(\d+\s+\w+\s+a\.\s+\d{3,4}|aa?\.\s*\d{3,4}[-–][\s\d.a]+|'
            r'ex\.\s*[ma]\.\s*\w+\s*[-–].*?a\.\s*\d{3,4}|'
            r'in\.\s*[ma]\.\s*\w+\s*[-–].*?a\.\s*\d{3,4}|'
            r'[a-z]+\s+m\.\s*\w+\s*a\.\s*\d{3,4}|'
            r'ex\.\s*a\.\s*\d{3,4}|in\.\s*a\.\s*\d{3,4}|'
            r'a\.\s*\d{3,4})',
            jk_line_rest, re.IGNORECASE
        )
        if date_m:
            date_str = date_m.group(1)
        else:
            after_jk = letters_section[jk_end:jk_end + 400]
            for line in after_jk.split('\n')[:8]:
                s = line.strip()
                if not s:
                    continue
                if re.match(r'^Edd?\.', s) or re.match(r'^Kehr\b', s):
                    break
                dm = re.search(
                    r'(\d+\s+\w+\s+a\.\s+\d{3,4}|aa?\.\s*\d{3,4}[-–][\s\d.a]+|'
                    r'a\.\s*\d{3,4})',
                    s, re.IGNORECASE
                )
                if dm:
                    date_str = dm.group(1)
                    break

        year, year_min, year_max = parse_date(date_str)

        # ── Letter text ───────────────────────────────────────────────────────
        if idx + 1 < len(jk_matches):
            next_jk_start = jk_matches[idx + 1][0]
        else:
            next_jk_start = len(letters_section)

        segment = letters_section[jk_end:next_jk_start]

        # Find where letter text begins (after Edd.: or Ed.:)
        text_start_pos = 0
        edd_seen = False
        pos = 0
        for line in segment.split('\n'):
            if re.match(r'^Edd?\.\s*:|^Ed\.\s*:', line.strip()):
                edd_seen = True
                pos += len(line) + 1
                continue
            if edd_seen or pos > 400:
                s = line.strip()
                if (s and re.match(r'^[A-Z][A-Za-z]{2,}', s) and
                        not re.match(r'^J-K\.|^PEI?[,./]?[AL]AGII|^EPISTU', s, re.IGNORECASE)):
                    text_start_pos = pos
                    break
            pos += len(line) + 1

        raw_text = segment[text_start_pos:]
        body = clean_letter_text(raw_text)

        # ── Salutation ────────────────────────────────────────────────────────
        first_nonempty = ''
        for line in body.split('\n'):
            s = line.strip()
            if s:
                first_nonempty = s
                break
        salutation = first_nonempty[:200]
        recipient_raw = extract_recipient(salutation)

        letters.append({
            'number': ep_num,
            'jk': jk_num,
            'date_str': date_str,
            'year': year,
            'year_min': year_min,
            'year_max': year_max,
            'summary': summary[:400],
            'body': body,
            'salutation': salutation,
            'recipient_raw': recipient_raw,
        })

    return letters


# ── Database operations ───────────────────────────────────────────────────────

def ensure_author(conn):
    """Get or create Pope Pelagius I author record."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM authors WHERE name = 'Pope Pelagius I'")
    row = cur.fetchone()
    if row:
        print(f"  Author already exists (id={row[0]})")
        return row[0]

    cur.execute("""
        INSERT INTO authors
            (name, name_latin, role, location, lat, lon, birth_year, death_year, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'Pope Pelagius I',
        'Pelagius I Papa',
        'pope',
        'Rome',
        41.8967,
        12.4822,
        500,
        561,
        'Pope 556-561 AD. Born c.500 in Rome, son of a vicar. '
        'Served as apocrisiarius in Constantinople 536-543. '
        'Involved in the Three Chapters controversy. '
        'Consecrated pope 16 April 556; died 3/4 March 561. '
        '~96 letters survive; edited by Gassó & Batlle, Montserrat 1956. '
        'No English translation exists.',
    ))
    conn.commit()
    return cur.lastrowid


def ensure_collection(conn):
    """Ensure the pelagius_i collection record exists."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM collections WHERE slug = 'pelagius_i'")
    if cur.fetchone():
        print("  Collection record already exists.")
        return

    cur.execute("""
        INSERT OR IGNORE INTO collections
            (slug, author_name, title, letter_count, date_range,
             latin_source_url, english_source_url, scrape_status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'pelagius_i',
        'Pope Pelagius I',
        'Pelagii I Papae Epistulae Quae Supersunt',
        96,
        '556-561',
        SOURCE_URL,
        None,
        'complete',
        'Critical edition: Pius M. Gassó & Columba M. Batlle, '
        'In Abbatia Montisserrati, 1956. '
        'Scripta et Documenta 8. '
        'OCR from Internet Archive DjVu text. '
        'No English translation available.',
    ))
    conn.commit()
    print("  Collection 'pelagius_i' created.")


def insert_letters(conn, letters, author_id):
    """Insert parsed letters into DB with 0.5s delay between each."""
    cur = conn.cursor()
    inserted = 0
    skipped = 0
    no_num = 0

    for letter in letters:
        if letter['number'] is None:
            no_num += 1
            continue

        ref_id = f"pelagius_i.ep.{letter['number']}"

        cur.execute("SELECT id FROM letters WHERE ref_id = ?", (ref_id,))
        if cur.fetchone():
            skipped += 1
            continue

        # Build subject summary
        parts = []
        if letter['jk']:
            parts.append(f"J-K. {letter['jk']}")
        if letter['summary']:
            parts.append(letter['summary'][:300])
        elif letter['salutation']:
            parts.append(letter['salutation'][:200])
        subject = ' | '.join(parts)[:500]

        cur.execute("""
            INSERT INTO letters (
                collection, letter_number, ref_id,
                sender_id,
                year_approx, year_min, year_max,
                origin_place, origin_lat, origin_lon,
                latin_text, english_text,
                subject_summary, source_url,
                translation_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'pelagius_i',
            letter['number'],
            ref_id,
            author_id,
            letter['year'],
            letter['year_min'],
            letter['year_max'],
            'Rome',
            41.8967,
            12.4822,
            letter['body'] if letter['body'] else None,
            None,
            subject if subject else None,
            SOURCE_URL,
            'none',
        ))
        inserted += 1
        time.sleep(DELAY)

    conn.commit()
    return inserted, skipped, no_num


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== Pelagius I Letter Scraper (Gassó-Batlle 1956) ===\n")

    # Step 1: Download OCR text
    print("Step 1: Fetching OCR text from Internet Archive...")
    if not download_ocr():
        print("FATAL: Could not obtain OCR text. Aborting.")
        sys.exit(1)
    time.sleep(DELAY)

    # Step 2: Load
    print("\nStep 2: Loading OCR text...")
    with open(OCR_CACHE, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    print(f"  Loaded {len(content):,} characters")

    # Step 3: Parse letters
    print("\nStep 3: Parsing letters from OCR...")
    letters = parse_letters(content)
    print(f"  Letter blocks found: {len(letters)}")

    if not letters:
        print("ERROR: No letters parsed.")
        sys.exit(1)

    with_num  = sum(1 for l in letters if l['number'])
    with_body = sum(1 for l in letters if l['body'] and len(l['body']) > 50)
    with_jk   = sum(1 for l in letters if l['jk'])
    with_date = sum(1 for l in letters if l['year'])
    no_num    = sum(1 for l in letters if not l['number'])

    print(f"  With letter number:   {with_num}")
    print(f"  Without num (no map): {no_num}")
    print(f"  With J-K number:      {with_jk}")
    print(f"  With parsed date:     {with_date}")
    print(f"  With body text:       {with_body}")
    print(f"  Letter numbers found: {sorted(l['number'] for l in letters if l['number'])}")

    # Sample ep.1
    ep1 = next((l for l in letters if l['number'] == 1), None)
    if ep1:
        print(f"\n  Sample ep.1:")
        print(f"    J-K: {ep1['jk']}, date: {ep1['date_str']!r}, year: {ep1['year']}")
        print(f"    Summary: {ep1['summary'][:100]!r}")
        print(f"    Salutation: {ep1['salutation'][:80]!r}")
        print(f"    Body ({len(ep1['body'])} chars): {ep1['body'][:120]!r}")

    # Step 4: Connect to DB
    print(f"\nStep 4: Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH, timeout=30)

    # Step 5: Author
    print("\nStep 5: Ensuring author record...")
    author_id = ensure_author(conn)
    print(f"  Author ID: {author_id} (Pope Pelagius I)")

    # Step 6: Collection
    print("\nStep 6: Ensuring collection record...")
    ensure_collection(conn)

    # Step 7: Insert letters
    print(f"\nStep 7: Inserting letters (0.5s delay each, ~{len(letters)*0.5:.0f}s total)...")
    inserted, skipped, no_num_db = insert_letters(conn, letters, author_id)
    print(f"  Inserted: {inserted}")
    print(f"  Skipped (already in DB): {skipped}")
    print(f"  Skipped (no letter number): {no_num_db}")

    # Step 8: Verify
    print("\n=== Database verification ===")
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM letters WHERE collection='pelagius_i'")
    total = cur.fetchone()[0]
    print(f"  Total letters in pelagius_i: {total}")

    cur.execute("""
        SELECT COUNT(*) FROM letters
        WHERE collection='pelagius_i' AND latin_text IS NOT NULL AND LENGTH(latin_text) > 50
    """)
    with_text = cur.fetchone()[0]
    print(f"  With substantial Latin text: {with_text}")

    cur.execute("""
        SELECT MIN(year_approx), MAX(year_approx)
        FROM letters WHERE collection='pelagius_i' AND year_approx IS NOT NULL
    """)
    yr = cur.fetchone()
    print(f"  Year range: {yr[0]} – {yr[1]}")

    cur.execute("""
        SELECT letter_number, year_approx, subject_summary
        FROM letters WHERE collection='pelagius_i'
        ORDER BY letter_number LIMIT 6
    """)
    print("\n  First 6 letters:")
    for row in cur.fetchall():
        print(f"    ep.{row[0]}: year={row[1]} | {str(row[2])[:80]}")

    # Author
    cur.execute("""
        SELECT id, name, name_latin, role, location, lat, lon, birth_year, death_year
        FROM authors WHERE name='Pope Pelagius I'
    """)
    row = cur.fetchone()
    if row:
        print(f"\n  Author: id={row[0]}, name={row[1]!r}, "
              f"role={row[3]!r}, location={row[4]!r}, "
              f"lat={row[5]}, lon={row[6]}, "
              f"born={row[7]}, died={row[8]}")

    conn.close()
    print("\nDone!")


if __name__ == '__main__':
    main()

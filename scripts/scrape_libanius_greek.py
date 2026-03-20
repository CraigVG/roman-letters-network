#!/usr/bin/env python3
"""
Scraper for Libanius Greek letters from OpenGreekAndLatin/First1KGreek.
Source: volume_xml/libanius_10.xml — Epistulae 1-839 in Greek (Foerster 1963 edition).

Downloads the XML, parses all Greek letters, inserts into roman_letters.db,
then generates modern English translations using the Anthropic API.
"""

import re
import sqlite3
import sys
import os
import urllib.request
import urllib.error
import json
import time

DB_PATH = "/Users/drillerdbmacmini/Documents/GitHub/roman-letters-network/data/roman_letters.db"
XML_URL = "https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/master/volume_xml/libanius_10.xml"
XML_CACHE = "/tmp/libanius_10.xml"
SOURCE_URL = "https://github.com/OpenGreekAndLatin/First1KGreek/blob/master/volume_xml/libanius_10.xml"
LIBANIUS_AUTHOR_ID = 366  # confirmed from DB


# ---------------------------------------------------------------------------
# 1. Fetch XML
# ---------------------------------------------------------------------------

def fetch_xml():
    if os.path.exists(XML_CACHE) and os.path.getsize(XML_CACHE) > 1_000_000:
        print(f"Using cached XML at {XML_CACHE}")
        with open(XML_CACHE, encoding="utf-8") as f:
            return f.read()
    print(f"Downloading {XML_URL} ...")
    req = urllib.request.Request(XML_URL, headers={"User-Agent": "roman-letters-network/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        content = resp.read().decode("utf-8")
    with open(XML_CACHE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved to {XML_CACHE} ({len(content):,} bytes)")
    return content


# ---------------------------------------------------------------------------
# 2. Parse XML into letter records
# ---------------------------------------------------------------------------

def strip_xml_tags(text):
    """Remove all XML tags from text."""
    # Remove footnotes entirely
    text = re.sub(r'<note type="footnote"[^>]*>.*?</note>', ' ', text, flags=re.DOTALL)
    # Remove marginal notes
    text = re.sub(r'<note type="marginal"[^>]*>.*?</note>', ' ', text, flags=re.DOTALL)
    # Remove page breaks
    text = re.sub(r'<pb[^>]*/>', ' ', text)
    # Remove line breaks
    text = re.sub(r'<lb[^/]*/>', ' ', text)
    # Remove remaining tags
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


def parse_recipient_and_date(header_text):
    """Parse recipient name and approximate date from the header paragraph.

    Header looks like: 'Κλεάρχῳ. (372/73 vel 382/84?)' or 'τῷ αὐτῷ. (383)'
    """
    header_text = header_text.strip()

    # Extract date if present
    date_match = re.search(r'\(([^)]+)\)', header_text)
    date_str = date_match.group(1) if date_match else None

    # Extract year from date string
    year_approx = None
    if date_str:
        # Try to find a 3-4 digit year
        year_match = re.search(r'\b(3[0-9]{2}|4[0-9]{2}|36[0-9]|39[0-9]|40[0-9])\b', date_str)
        if year_match:
            year_approx = int(year_match.group(1))

    # Recipient is text before the parenthetical and trailing period
    recipient = re.sub(r'\s*\([^)]+\)', '', header_text).strip().rstrip('.')

    return recipient, year_approx


def extract_letter_text_from_div(div_content):
    """Extract the Greek body text from a letter div, stripping all footnotes/notes."""
    # Remove footnote divs
    text = re.sub(r'<note type="footnote"[^>]*>.*?</note>', '', div_content, flags=re.DOTALL)
    # Remove marginal notes
    text = re.sub(r'<note type="marginal"[^>]*>.*?</note>', '', text, flags=re.DOTALL)
    # Remove page breaks and line breaks
    text = re.sub(r'<pb[^>]*/>', '', text)
    text = re.sub(r'<lb[^/]*/>', '', text)
    # Extract text from p elements
    paras = re.findall(r'<p>(.*?)</p>', text, flags=re.DOTALL)
    # Remove remaining tags
    paras_clean = [re.sub(r'<[^>]+>', '', p).strip() for p in paras]
    # Filter out very short paragraphs that are just letter numbers (α', β', etc.)
    paras_clean = [p for p in paras_clean if len(p) > 5 and not re.match(r'^[α-ω΄\']+\.$', p)]
    return '\n\n'.join(paras_clean).strip()


def parse_letters(xml_content):
    """Parse all letters from the XML. Returns list of dicts."""
    letters = []

    # The edition section starts here
    edition_start = xml_content.find('<div type="edition"')
    if edition_start == -1:
        print("ERROR: Could not find edition div")
        return letters

    edition_content = xml_content[edition_start:]

    # Find all outer letter divs
    # Pattern: <div type="textpart" subtype="letter" n="N">
    outer_pattern = re.compile(
        r'<div type="textpart" subtype="letter" n="(\d+)">(.*?)(?=<div type="textpart" subtype="letter" n="\d+">|$)',
        re.DOTALL
    )

    matches = list(outer_pattern.finditer(edition_content))
    print(f"Found {len(matches)} outer letter divs")

    # But each outer div may contain a NESTED inner div with the same numbering.
    # The outer div structure is:
    #   outer div n=X  -> header (pb, alpha numeral, recipient+date)
    #     inner div type=textpart subtype=letter n=X -> first chapter of text
    #     inner div type=textpart subtype=chapter n=2 -> second chapter etc.
    # Some letters have the outer div wrapping the recipient line + inner div

    for i, m in enumerate(matches):
        letter_n = int(m.group(1))
        outer_content = m.group(2)

        # Skip if this is the very first match (n=1 appears twice due to nesting)
        # We want the OUTER n=X, not the inner n=X
        # Detect if this div starts with a header paragraph or immediately with body text
        # Header divs have a <p> with Greek letter numeral before any inner div

        # Get content before first inner div
        first_inner_pos = outer_content.find('<div type="textpart"')
        pre_div = outer_content[:first_inner_pos] if first_inner_pos != -1 else outer_content

        # Check if pre_div has a recipient-style paragraph (Greek dative ending in ῳ or τῷ αὐτῷ)
        pre_paras = re.findall(r'<p>(.*?)</p>', pre_div, flags=re.DOTALL)
        pre_paras_text = [strip_xml_tags(p).strip() for p in pre_paras]

        # Find recipient paragraph: the one with a date or a Greek dative name
        # It's typically the second <p> (first is the alpha numeral)
        recipient_text = ''
        for p in pre_paras_text:
            p_clean = p.strip()
            if len(p_clean) > 3 and not re.match(r'^[α-ωΑ-Ω΄\'\s]+$', p_clean):
                # Has a real name (not just a Greek letter numeral)
                recipient_text = p_clean
                break
            elif re.search(r'ῳ|αὐτῷ|αὐτοῖς', p_clean):
                recipient_text = p_clean
                break

        # If no header content before inner div, this might be a nested copy — skip it
        if not recipient_text and first_inner_pos == 0:
            continue

        # Extract body text from all inner divs
        body_parts = []
        # Get all <p> content that's Greek text (not just numerals or footnotes)
        all_text = extract_letter_text_from_div(outer_content)

        if not all_text:
            continue

        recipient, year_approx = parse_recipient_and_date(recipient_text)

        letters.append({
            'letter_number': letter_n,
            'recipient_raw': recipient,
            'year_approx': year_approx,
            'greek_text': all_text,
        })

    return letters


# ---------------------------------------------------------------------------
# 3. Deduplicate — some outer divs wrap an identically-numbered inner div
# ---------------------------------------------------------------------------

def deduplicate_letters(raw_letters):
    """
    The XML nesting means letter n=X appears as both an outer and inner div.
    We want the version with a recipient header. Deduplicate by letter_number,
    preferring entries that have a non-empty recipient.
    """
    seen = {}
    for letter in raw_letters:
        n = letter['letter_number']
        if n not in seen:
            seen[n] = letter
        else:
            # Prefer the one with a recipient
            if letter['recipient_raw'] and not seen[n]['recipient_raw']:
                seen[n] = letter
            # Also prefer longer text (outer div has more content)
            elif len(letter['greek_text']) > len(seen[n]['greek_text']):
                seen[n] = letter

    result = sorted(seen.values(), key=lambda x: x['letter_number'])
    print(f"After deduplication: {len(result)} unique letters")
    return result


# ---------------------------------------------------------------------------
# 4. Database insertion
# ---------------------------------------------------------------------------

def get_existing_letter_numbers(conn):
    cur = conn.execute("SELECT letter_number FROM letters WHERE collection='libanius'")
    return {row[0] for row in cur.fetchall()}


def insert_letters(conn, letters):
    existing = get_existing_letter_numbers(conn)
    print(f"Existing Libanius letters in DB: {len(existing)}")

    inserted = 0
    skipped = 0

    for letter in letters:
        n = letter['letter_number']
        if n in existing:
            skipped += 1
            continue

        ref_id = f"libanius.ep.{n}"

        conn.execute("""
            INSERT OR IGNORE INTO letters
                (collection, letter_number, ref_id, sender_id,
                 year_approx, subject_summary, latin_text,
                 translation_source, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'libanius',
            n,
            ref_id,
            LIBANIUS_AUTHOR_ID,
            letter['year_approx'],
            f"Letter to {letter['recipient_raw']}" if letter['recipient_raw'] else None,
            letter['greek_text'],   # greek stored in latin_text column
            'ai_translated',        # will be translated below
            SOURCE_URL,
        ))
        inserted += 1

    conn.commit()
    print(f"Inserted {inserted} new letters, skipped {skipped} already present")
    return inserted


# ---------------------------------------------------------------------------
# 5. Translation via Anthropic API
# ---------------------------------------------------------------------------

def translate_letter(greek_text, letter_number, recipient):
    """Translate a Greek letter to modern English using Anthropic API."""
    import anthropic

    client = anthropic.Anthropic()

    context = f"Letter {letter_number}"
    if recipient:
        context += f" to {recipient}"

    prompt = f"""You are translating a Greek letter by Libanius of Antioch (314–394 AD), the famous late antique rhetorician and sophist. This is {context} from his collection of ~1,544 surviving letters.

Translate this Greek text into clear, fluent modern English. Preserve the rhetorical sophistication and personal tone. Keep proper names (recipients, third parties) as they appear. If there are textual difficulties or unclear passages, translate your best reading.

Greek text:
{greek_text}

Provide only the English translation, no commentary."""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text.strip()


def translate_batch(conn, batch_size=50):
    """Translate letters that have Greek text but no English translation yet."""
    try:
        import anthropic
    except ImportError:
        print("anthropic package not installed. Skipping translation.")
        print("Install with: pip install anthropic")
        return 0

    # Get letters needing translation
    cur = conn.execute("""
        SELECT id, letter_number, latin_text, subject_summary
        FROM letters
        WHERE collection='libanius'
          AND latin_text IS NOT NULL
          AND (english_text IS NULL OR english_text = '')
        ORDER BY letter_number
        LIMIT ?
    """, (batch_size,))

    rows = cur.fetchall()
    print(f"\nTranslating {len(rows)} letters (batch_size={batch_size})...")

    translated = 0
    errors = 0

    for row in rows:
        letter_id, letter_number, greek_text, subject_summary = row

        # Extract recipient from subject_summary
        recipient = ''
        if subject_summary and subject_summary.startswith('Letter to '):
            recipient = subject_summary[len('Letter to '):]

        try:
            english = translate_letter(greek_text, letter_number, recipient)
            conn.execute("""
                UPDATE letters
                SET english_text = ?,
                    translation_source = 'ai_translated'
                WHERE id = ?
            """, (english, letter_id))
            conn.commit()
            translated += 1

            if translated % 10 == 0:
                print(f"  Translated {translated}/{len(rows)} letters...")

            # Small pause to avoid rate limits
            time.sleep(0.3)

        except Exception as e:
            print(f"  ERROR translating letter {letter_number}: {e}")
            errors += 1
            if errors > 5:
                print("  Too many errors, stopping translation batch")
                break
            time.sleep(2)

    print(f"Translation complete: {translated} translated, {errors} errors")
    return translated


# ---------------------------------------------------------------------------
# 6. Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Libanius Greek Letters Scraper")
    print("Source: OpenGreekAndLatin/First1KGreek — Epistulae 1-839")
    print("=" * 60)

    # Step 1: Fetch XML
    xml_content = fetch_xml()

    # Step 2: Parse letters
    print("\nParsing letters from XML...")
    raw_letters = parse_letters(xml_content)
    print(f"Parsed {len(raw_letters)} raw letter entries")

    # Step 3: Deduplicate
    letters = deduplicate_letters(raw_letters)

    # Show sample
    if letters:
        print(f"\nSample letters:")
        for l in letters[:3]:
            print(f"  Letter {l['letter_number']}: to '{l['recipient_raw']}' (~{l['year_approx']}) "
                  f"— {len(l['greek_text'])} chars")

    # Step 4: Insert into DB
    print(f"\nConnecting to DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH, timeout=30)

    n_inserted = insert_letters(conn, letters)

    # Step 5: Translate
    if n_inserted > 0 or '--translate' in sys.argv:
        batch = int(sys.argv[sys.argv.index('--batch') + 1]) if '--batch' in sys.argv else 100
        translate_batch(conn, batch_size=batch)
    else:
        print("\nNo new letters to translate (all already in DB).")
        print("Use --translate flag to re-run translation on untranslated letters.")

    # Final stats
    cur = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN latin_text IS NOT NULL THEN 1 ELSE 0 END) as has_greek,
            SUM(CASE WHEN english_text IS NOT NULL THEN 1 ELSE 0 END) as has_english
        FROM letters WHERE collection='libanius'
    """)
    row = cur.fetchone()
    print(f"\nFinal Libanius stats in DB:")
    print(f"  Total letters: {row[0]}")
    print(f"  With Greek text: {row[1]}")
    print(f"  With English translation: {row[2]}")

    conn.close()
    print("\nDone.")


if __name__ == '__main__':
    main()

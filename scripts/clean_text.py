#!/usr/bin/env python3
"""
Clean the stored letter texts by stripping New Advent navigation boilerplate.
Also regenerate summaries after cleaning.
"""

import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')


def clean_newadvent_text(text):
    """Remove New Advent website navigation and boilerplate from letter text."""
    if not text:
        return text

    # Remove the navigation header block
    # Pattern: everything up to "Home > Fathers of the Church > ... > Letter N"
    patterns = [
        r'^.*?(?:Home\s*>\s*Fathers of the Church\s*>\s*[^>]+>\s*(?:Letter|Epistle|Book)\s*[^\n]*\n)',
        r'^.*?(?:Home\s*>\s*Fathers of the Church\s*>\s*[^>]+>\s*[^\n]*\n)',
    ]

    for pattern in patterns:
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if m:
            text = text[m.end():]
            break

    # Remove "Search: Submit Search" header
    text = re.sub(r'^Search:\s*Submit Search\s*', '', text, flags=re.MULTILINE)

    # Remove alphabet navigation "A B C D E F G H ..."
    text = re.sub(r'^\s*A\s+B\s+C\s+D\s+E\s+F\s+G\s+H\s+I\s+J\s+K\s+L\s+M\s+N\s+O\s+P\s+Q\s+R\s+S\s+T\s+U\s+V\s+W\s+X\s+Y\s+Z\s*$', '', text, flags=re.MULTILINE)

    # Remove "Please help support..." fundraising text
    text = re.sub(r'Please help support the mission of New Advent.*?(?:\$\d+\.\d+\.\.\.|\n\n)', '', text, flags=re.DOTALL)

    # Remove the "Letter N" header line if it's at the very start
    text = re.sub(r'^\s*(Letter|Epistle)\s+[IVXLCDM\d]+\.?\s*\n', '', text, flags=re.IGNORECASE)

    # Remove footer boilerplate
    footer_patterns = [
        r'\n\s*Taken from.*$',
        r'\n\s*This document has been generated.*$',
        r'\n\s*Copyright.*New Advent.*$',
        r'\n\s*Dedicated to the Immaculate.*$',
        r'\n\s*Kevin Knight\.?\s*\d{4}\.?\s*$',
        r'\n\s*Translated by.*?(?:Schaff|Wace|Fremantle).*$',
        r'\n\s*HOME\s*$',
    ]
    for pattern in footer_patterns:
        text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

    # Clean up excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    return text


def generate_summary(text, collection, letter_number):
    """Generate a 1-2 sentence summary from cleaned text."""
    if not text or len(text) < 50:
        return None, None

    lines = text.strip().split('\n')
    clean_lines = [l.strip() for l in lines if l.strip() and len(l.strip()) > 10]

    # Skip remaining header lines (To X, dates, etc.)
    content_start = 0
    for i, line in enumerate(clean_lines):
        if re.match(r'^(To |From |Written |A\.?D\.?\s*\d|Circa |About |\d{3,4}\s)', line, re.IGNORECASE):
            content_start = i + 1
            continue
        if re.match(r'^[IVXLCDM]+\.\s', line):
            content_start = i + 1
            continue
        if len(line) > 40:
            content_start = i
            break

    content_lines = clean_lines[content_start:]
    if not content_lines:
        content_lines = clean_lines

    full_content = ' '.join(content_lines)

    # Get first 2-3 sentences
    sentences = re.split(r'(?<=[.!?])\s+', full_content)
    summary = ' '.join(sentences[:3])
    if len(summary) > 350:
        summary = summary[:347] + '...'
    if len(summary) < 20:
        return None, None

    # Identify what makes it interesting
    interesting = identify_interest(full_content, collection)

    return summary, interesting


def identify_interest(text, collection):
    """Identify what makes a letter historically interesting."""
    text_lower = text.lower()
    interests = []

    tags = [
        (['barbarian', 'goth', 'vandal', 'hun', 'frank', 'burgundian', 'lombard'], 'Barbarian peoples/invasions'),
        (['heresy', 'heretic', 'arian', 'donatist', 'pelagian', 'nestorian', 'manichee'], 'Theological controversy'),
        (['emperor', 'imperial', 'augustus', 'palace', 'court'], 'Imperial politics'),
        (['council', 'synod', 'ecumenical'], 'Church council'),
        (['persecution', 'martyr', 'prison', 'exile', 'banish'], 'Persecution or exile'),
        (['journey', 'travel', 'voyage', 'road', 'ship', 'sailing', 'courier'], 'Travel & mobility'),
        (['famine', 'plague', 'earthquake', 'flood', 'disaster', 'pestilence'], 'Natural disaster/crisis'),
        (['slave', 'captive', 'ransom', 'prisoner'], 'Slavery or captivity'),
        (['war', 'siege', 'battle', 'army', 'soldier', 'invasion'], 'Military conflict'),
        (['friendship', 'longing', 'absence', 'miss you', 'desire to see'], 'Personal friendship'),
        (['book', 'library', 'copy', 'manuscript', 'codex'], 'Literary culture'),
        (['property', 'estate', 'land', 'villa', 'farm', 'rent'], 'Economic matters'),
        (['death', 'funeral', 'mourning', 'tomb', 'burial', 'obituary'], 'Death & mourning'),
        (['marriage', 'wedding', 'bride', 'dowry'], 'Marriage customs'),
        (['baptism', 'catechumen', 'conversion', 'pagan'], 'Conversion/baptism'),
        (['jew', 'jewish', 'synagogue'], 'Jewish-Christian relations'),
        (['trade', 'merchant', 'commerce', 'market', 'goods', 'money'], 'Trade & commerce'),
        (['miracle', 'relic', 'saint', 'vision', 'dream'], 'Miracles & relics'),
    ]

    for keywords, label in tags:
        if any(w in text_lower for w in keywords):
            interests.append(label)
        if len(interests) >= 3:
            break

    return '; '.join(interests) if interests else None


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()

    # Add columns if needed
    for col in ['quick_summary', 'interesting_note']:
        try:
            cursor.execute(f'ALTER TABLE letters ADD COLUMN {col} TEXT')
        except sqlite3.OperationalError:
            pass
    conn.commit()

    # Clean all English texts
    cursor.execute('SELECT id, english_text FROM letters WHERE english_text IS NOT NULL')
    letters = cursor.fetchall()
    print(f"Cleaning {len(letters)} letter texts...")

    cleaned_count = 0
    summary_count = 0

    for letter_id, text in letters:
        cleaned = clean_newadvent_text(text)
        if cleaned != text:
            cursor.execute('UPDATE letters SET english_text = ? WHERE id = ?', (cleaned, letter_id))
            cleaned_count += 1

        # Regenerate summary
        cursor.execute('SELECT collection, letter_number FROM letters WHERE id = ?', (letter_id,))
        coll, num = cursor.fetchone()
        summary, interesting = generate_summary(cleaned, coll, num)
        if summary:
            cursor.execute('UPDATE letters SET quick_summary = ?, interesting_note = ? WHERE id = ?',
                           (summary, interesting, letter_id))
            summary_count += 1

    conn.commit()

    print(f"Cleaned: {cleaned_count} texts")
    print(f"Summaries generated: {summary_count}")

    # Show examples
    cursor.execute('''
        SELECT l.collection, l.letter_number, l.quick_summary, l.interesting_note,
               s.name as sender, r.name as recipient
        FROM letters l
        LEFT JOIN authors s ON l.sender_id = s.id
        LEFT JOIN authors r ON l.recipient_id = r.id
        WHERE l.quick_summary IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 5
    ''')
    print(f"\nSample summaries:")
    for row in cursor.fetchall():
        print(f"\n  [{row[0]} #{row[1]}] {row[4] or '?'} -> {row[5] or '?'}")
        print(f"  Summary: {row[2][:200]}")
        if row[3]:
            print(f"  Tags: {row[3]}")

    conn.close()


if __name__ == '__main__':
    main()

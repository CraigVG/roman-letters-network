#!/usr/bin/env python3
"""
Generate concise, interesting summaries for each letter.
Extracts what the letter is about and what makes it historically interesting.

This script works on the English translations already in the database.
For letters without English text, it creates summaries from the Latin text headers.
"""

import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

# Add summary columns if they don't exist
ALTER_SQL = [
    "ALTER TABLE letters ADD COLUMN quick_summary TEXT;",
    "ALTER TABLE letters ADD COLUMN interesting_note TEXT;",
]


def generate_summary_from_english(text, collection, letter_number):
    """Generate a 1-2 sentence summary from the English translation text."""
    if not text or len(text) < 100:
        return None, None

    lines = text.strip().split('\n')
    clean_lines = [l.strip() for l in lines if l.strip() and len(l.strip()) > 10]

    # Skip header lines (letter numbers, "To X", dates, etc.)
    content_lines = []
    header_ended = False
    for line in clean_lines:
        if header_ended:
            content_lines.append(line)
            continue
        # Skip typical header patterns
        if re.match(r'^(Letter|Epistle|Book|Chapter|To |From |\d+\.|[IVXLCDM]+\.)', line, re.IGNORECASE):
            continue
        if re.match(r'^\(A\.?D\.?\s*\d+', line):
            continue
        if len(line) < 30:
            continue
        header_ended = True
        content_lines.append(line)

    if not content_lines:
        content_lines = clean_lines[3:] if len(clean_lines) > 3 else clean_lines

    # Build summary from first substantive content
    full_content = ' '.join(content_lines)

    # Extract first 2-3 sentences as summary
    sentences = re.split(r'(?<=[.!?])\s+', full_content)
    summary_sentences = []
    char_count = 0
    for s in sentences:
        if char_count > 300:
            break
        summary_sentences.append(s)
        char_count += len(s)

    summary = ' '.join(summary_sentences[:3])
    if len(summary) > 400:
        summary = summary[:397] + '...'

    # Try to identify what makes this letter interesting
    interesting = identify_interest(full_content, collection)

    return summary, interesting


def identify_interest(text, collection):
    """Identify what makes a letter historically interesting based on keywords."""
    text_lower = text.lower()
    interests = []

    # Historical events and themes
    if any(w in text_lower for w in ['barbarian', 'goth', 'vandal', 'hun', 'frank', 'burgundian']):
        interests.append('References barbarian peoples/invasions')
    if any(w in text_lower for w in ['heresy', 'heretic', 'arian', 'donatist', 'pelagian', 'nestorian']):
        interests.append('Addresses theological controversy')
    if any(w in text_lower for w in ['emperor', 'imperial', 'augustus', 'palace']):
        interests.append('Involves imperial politics')
    if any(w in text_lower for w in ['council', 'synod', 'ecumenical']):
        interests.append('References a church council')
    if any(w in text_lower for w in ['persecution', 'martyr', 'prison', 'exile']):
        interests.append('Describes persecution or hardship')
    if any(w in text_lower for w in ['journey', 'travel', 'voyage', 'road', 'ship', 'sailing']):
        interests.append('Describes travel/mobility')
    if any(w in text_lower for w in ['famine', 'plague', 'earthquake', 'flood', 'disaster']):
        interests.append('Reports natural disaster or crisis')
    if any(w in text_lower for w in ['slave', 'captive', 'ransom', 'prisoner']):
        interests.append('Addresses slavery or captivity')
    if any(w in text_lower for w in ['widow', 'orphan', 'poor', 'charity']):
        interests.append('Discusses care for the vulnerable')
    if any(w in text_lower for w in ['scripture', 'bible', 'gospel', 'psalm', 'prophet']):
        interests.append('Contains scriptural commentary')
    if any(w in text_lower for w in ['marriage', 'wedding', 'virgin', 'celibacy', 'chastity']):
        interests.append('Discusses marriage/celibacy')
    if any(w in text_lower for w in ['death', 'funeral', 'mourning', 'tomb', 'burial']):
        interests.append('Contains an obituary or mourning')
    if any(w in text_lower for w in ['friendship', 'longing', 'absence', 'miss you', 'desire to see']):
        interests.append('Expresses personal friendship/longing')
    if any(w in text_lower for w in ['book', 'library', 'copy', 'manuscript', 'writing']):
        interests.append('References books/literary culture')
    if any(w in text_lower for w in ['property', 'estate', 'land', 'villa', 'farm']):
        interests.append('Discusses property/economic matters')
    if any(w in text_lower for w in ['ordination', 'bishop', 'deacon', 'priest', 'clergy']):
        interests.append('Addresses church administration')
    if any(w in text_lower for w in ['rome', 'roman', 'senate', 'consul']):
        interests.append('References Roman institutions')
    if any(w in text_lower for w in ['baptism', 'catechumen', 'conversion']):
        interests.append('Discusses baptism/conversion')

    if interests:
        return '; '.join(interests[:3])  # Max 3 tags
    return None


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()

    # Add columns
    for sql in ALTER_SQL:
        try:
            cursor.execute(sql)
        except sqlite3.OperationalError:
            pass
    conn.commit()

    # Process letters with English text that don't have summaries yet
    cursor.execute('''
        SELECT id, collection, letter_number, english_text
        FROM letters
        WHERE english_text IS NOT NULL AND quick_summary IS NULL
    ''')
    letters = cursor.fetchall()
    print(f"Generating summaries for {len(letters)} letters...")

    count = 0
    for letter_id, collection, letter_num, text in letters:
        summary, interesting = generate_summary_from_english(text, collection, letter_num)
        if summary:
            cursor.execute('''
                UPDATE letters SET quick_summary = ?, interesting_note = ?
                WHERE id = ?
            ''', (summary, interesting, letter_id))
            count += 1

        if count % 100 == 0 and count > 0:
            conn.commit()
            print(f"  Processed {count} letters...")

    conn.commit()

    # Report
    cursor.execute('SELECT COUNT(*) FROM letters WHERE quick_summary IS NOT NULL')
    print(f"\nLetters with summaries: {cursor.fetchone()[0]}")

    cursor.execute('SELECT COUNT(*) FROM letters WHERE interesting_note IS NOT NULL')
    print(f"Letters with interest tags: {cursor.fetchone()[0]}")

    # Show some examples
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
        print(f"  Summary: {row[2][:200]}...")
        if row[3]:
            print(f"  Tags: {row[3]}")

    conn.close()


if __name__ == '__main__':
    main()

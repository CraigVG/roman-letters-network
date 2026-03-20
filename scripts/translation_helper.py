#!/usr/bin/env python3
"""
Helper functions for reading/writing letter translations to the database.
Used by translation agents.

Usage:
  # Read letters needing translation for a collection
  python3 scripts/translation_helper.py read augustine_hippo 0 10

  # Write a modern translation for a specific letter ID
  python3 scripts/translation_helper.py write <letter_id> "<modern_text>"

  # Check progress
  python3 scripts/translation_helper.py status
"""

import sqlite3
import os
import sys
import json

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')


def get_db():
    return sqlite3.connect(DB_PATH, timeout=30)


def read_letters(collection, offset=0, limit=10):
    """Read letters needing modern translation."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT l.id, l.collection, l.letter_number, l.year_approx,
               l.english_text, l.latin_text,
               s.name as sender_name, r.name as recipient_name,
               l.quick_summary, l.interesting_note
        FROM letters l
        LEFT JOIN authors s ON l.sender_id = s.id
        LEFT JOIN authors r ON l.recipient_id = r.id
        WHERE l.collection = ? AND l.modern_english IS NULL
            AND (l.english_text IS NOT NULL OR l.latin_text IS NOT NULL)
        ORDER BY l.letter_number
        LIMIT ? OFFSET ?
    ''', (collection, limit, offset))

    letters = []
    for row in c.fetchall():
        letters.append({
            'id': row[0],
            'collection': row[1],
            'letter_number': row[2],
            'year_approx': row[3],
            'english_text': row[4],
            'latin_text': row[5],
            'sender_name': row[6],
            'recipient_name': row[7],
            'quick_summary': row[8],
            'interesting_note': row[9],
        })
    conn.close()
    return letters


def write_translation(letter_id, modern_text):
    """Write a modern translation for a letter."""
    conn = get_db()
    conn.execute('UPDATE letters SET modern_english = ? WHERE id = ?',
                 (modern_text, letter_id))
    conn.commit()
    conn.close()


def write_translations_batch(translations):
    """Write multiple translations at once. translations = [(id, text), ...]"""
    conn = get_db()
    c = conn.cursor()
    for letter_id, text in translations:
        c.execute('UPDATE letters SET modern_english = ? WHERE id = ?', (text, letter_id))
    conn.commit()
    conn.close()
    return len(translations)


def status():
    """Show translation progress."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT collection, COUNT(*) as total,
            SUM(CASE WHEN modern_english IS NOT NULL THEN 1 ELSE 0 END) as modern
        FROM letters GROUP BY collection ORDER BY total DESC
    ''')
    print(f"{'Collection':<25} {'Total':>6} {'Modern':>7} {'%':>5}")
    print('-' * 48)
    for row in c.fetchall():
        pct = f"{row[2]*100//row[1]}%" if row[1] > 0 else "0%"
        print(f"{row[0]:<25} {row[1]:>6} {row[2]:>7} {pct:>5}")
    conn.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: translation_helper.py [read|write|status] ...")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'read':
        collection = sys.argv[2]
        offset = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10
        letters = read_letters(collection, offset, limit)
        for l in letters:
            print(f"\n{'='*60}")
            print(f"ID: {l['id']} | {l['collection']} #{l['letter_number']} | ~{l['year_approx']} AD")
            print(f"From: {l['sender_name']} -> To: {l['recipient_name']}")
            if l['english_text']:
                print(f"\n--- English ({len(l['english_text'])} chars) ---")
                print(l['english_text'][:2000])
            if l['latin_text']:
                print(f"\n--- Latin ({len(l['latin_text'])} chars) ---")
                print(l['latin_text'][:1000])
            print()

    elif cmd == 'write':
        letter_id = int(sys.argv[2])
        text = sys.argv[3]
        write_translation(letter_id, text)
        print(f"Written translation for letter {letter_id}")

    elif cmd == 'status':
        status()

    else:
        print(f"Unknown command: {cmd}")

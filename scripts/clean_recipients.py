#!/usr/bin/env python3
"""Clean up recipient names that captured too much text from letter headers."""

import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')


def clean_name(name):
    """Clean up an author name that may have captured extra text."""
    if not name:
        return name

    # Truncate at common sentence-start words
    for pattern in [
        r'\s+(?:sends?|send)\s+(?:greeting|salutation)',
        r'\s+(?:Catholic|Clergy|Following|District)',
        r',\s+(?:my|his|her|our|your)\s+',
        r'\s+(?:my|his)\s+(?:holy|noble|beloved|brother)',
        r'\s+(?:Augustine|Jerome|Gregory|Ambrose)\s+sends',
    ]:
        m = re.search(pattern, name, re.IGNORECASE)
        if m:
            name = name[:m.start()]

    # Clean trailing punctuation and whitespace
    name = name.rstrip(' ,;:.')

    # If the name is still very long, truncate at first comma or parenthetical
    if len(name) > 50:
        m = re.match(r'^([^,]+)', name)
        if m:
            name = m.group(1).strip()

    return name.strip()


def merge_duplicate_authors(cursor):
    """Find and merge authors that look like duplicates."""
    cursor.execute('SELECT id, name FROM authors ORDER BY name')
    authors = cursor.fetchall()

    # Build a map of first-name to list of (id, name)
    first_names = {}
    for aid, aname in authors:
        first = aname.split(',')[0].split(' of ')[0].strip()
        if first not in first_names:
            first_names[first] = []
        first_names[first].append((aid, aname))

    merged = 0
    for first, entries in first_names.items():
        if len(entries) <= 1:
            continue

        # Keep the shortest/cleanest name as the primary
        entries.sort(key=lambda x: len(x[1]))
        primary_id, primary_name = entries[0]

        for dup_id, dup_name in entries[1:]:
            if dup_id == primary_id:
                continue
            # Only merge if the names are actually similar (not just share first word)
            if len(first) < 4:
                continue  # Skip very short first names to avoid false merges

            # Merge: update all letter references
            cursor.execute('UPDATE letters SET sender_id = ? WHERE sender_id = ?', (primary_id, dup_id))
            cursor.execute('UPDATE letters SET recipient_id = ? WHERE recipient_id = ?', (primary_id, dup_id))
            cursor.execute('UPDATE people_mentioned SET person_id = ? WHERE person_id = ?', (primary_id, dup_id))
            cursor.execute('DELETE FROM authors WHERE id = ?', (dup_id,))
            merged += 1

    return merged


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()

    # Clean up author names
    cursor.execute('SELECT id, name FROM authors')
    updated = 0
    for aid, name in cursor.fetchall():
        cleaned = clean_name(name)
        if cleaned != name and cleaned:
            # Check if cleaned name already exists
            cursor.execute('SELECT id FROM authors WHERE name = ? AND id != ?', (cleaned, aid))
            existing = cursor.fetchone()
            if existing:
                # Merge into existing author
                eid = existing[0]
                cursor.execute('UPDATE letters SET sender_id = ? WHERE sender_id = ?', (eid, aid))
                cursor.execute('UPDATE letters SET recipient_id = ? WHERE recipient_id = ?', (eid, aid))
                cursor.execute('UPDATE people_mentioned SET person_id = ? WHERE person_id = ?', (eid, aid))
                cursor.execute('DELETE FROM authors WHERE id = ?', (aid,))
                updated += 1
                if updated <= 20:
                    print(f"  Merged: '{name}' -> existing '{cleaned}'")
            else:
                cursor.execute('UPDATE authors SET name = ? WHERE id = ?', (cleaned, aid))
                updated += 1
                if updated <= 20:
                    print(f"  Cleaned: '{name}' -> '{cleaned}'")

    print(f"\nCleaned {updated} author names")

    # Merge duplicates
    merged = merge_duplicate_authors(cursor)
    print(f"Merged {merged} duplicate authors")

    conn.commit()

    # Show final stats
    cursor.execute('SELECT COUNT(*) FROM authors')
    print(f"\nTotal authors: {cursor.fetchone()[0]}")

    cursor.execute('''
        SELECT COUNT(DISTINCT sender_id || '-' || recipient_id)
        FROM letters WHERE sender_id IS NOT NULL AND recipient_id IS NOT NULL
    ''')
    print(f"Unique connections: {cursor.fetchone()[0]}")

    # Top connections after cleanup
    cursor.execute('''
        SELECT s.name, r.name, COUNT(*) as cnt
        FROM letters l
        JOIN authors s ON l.sender_id = s.id
        JOIN authors r ON l.recipient_id = r.id
        GROUP BY l.sender_id, l.recipient_id
        ORDER BY cnt DESC
        LIMIT 15
    ''')
    print(f"\nTop letter connections:")
    for row in cursor.fetchall():
        print(f"  {row[0]} -> {row[1]}: {row[2]} letters")

    conn.close()


if __name__ == '__main__':
    main()

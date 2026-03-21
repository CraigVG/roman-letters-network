#!/usr/bin/env python3
"""
Fix missing sender_id in the Roman Letters database.

For collections where the sender is the collection author, sets sender_id
for all letters where it is NULL.

Also scans small papal collections for extractable recipient information.
"""

import sqlite3
import re
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

# Mapping of collection name -> author name in the authors table
# These are collections where ALL letters (or all NULL-sender letters) are from the named author
COLLECTION_AUTHOR_MAP = {
    # Primary targets (100% missing or nearly so)
    'ennodius_pavia': 'Ennodius of Pavia',
    'venantius_fortunatus': 'Venantius Fortunatus',
    'paulinus_nola': 'Paulinus of Nola',
    # Partially missing - the NULL entries are from the collection author
    'ruricius_limoges': 'Ruricius of Limoges',
    'avitus_vienne': 'Avitus of Vienne',
    'sidonius_apollinaris': 'Sidonius Apollinaris',
    'ambrose_milan': 'Ambrose of Milan',
    # Single orphan .lat. entries
    'cassiodorus': 'Cassiodorus',
    'gregory_great': 'Pope Gregory the Great',
}


def fix_senders(conn):
    """Fix missing sender_id for known collection authors."""
    cursor = conn.cursor()
    total_fixed = 0

    for collection, author_name in COLLECTION_AUTHOR_MAP.items():
        # Look up the author
        cursor.execute("SELECT id FROM authors WHERE name = ?", (author_name,))
        row = cursor.fetchone()
        if not row:
            print(f"  WARNING: Author '{author_name}' not found in authors table!")
            continue
        author_id = row[0]

        # Count how many need fixing
        cursor.execute(
            "SELECT COUNT(*) FROM letters WHERE collection = ? AND sender_id IS NULL",
            (collection,)
        )
        null_count = cursor.fetchone()[0]

        if null_count == 0:
            print(f"  {collection}: no missing senders (already fixed)")
            continue

        # Update
        cursor.execute(
            "UPDATE letters SET sender_id = ? WHERE collection = ? AND sender_id IS NULL",
            (author_id, collection)
        )
        updated = cursor.rowcount
        total_fixed += updated
        print(f"  {collection}: set sender_id={author_id} ({author_name}) for {updated} letters")

    conn.commit()
    print(f"\nTotal sender_id fixes: {total_fixed}")
    return total_fixed


def verify_senders(conn):
    """Check which collections still have missing sender_id."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT collection, COUNT(*) as total,
            SUM(CASE WHEN sender_id IS NULL THEN 1 ELSE 0 END) as missing_sender
        FROM letters
        GROUP BY collection
        HAVING missing_sender > 0
        ORDER BY missing_sender DESC
    """)
    rows = cursor.fetchall()
    if rows:
        print("\nCollections still missing sender_id:")
        print(f"  {'Collection':<30} {'Total':>6} {'Missing':>8}")
        print(f"  {'-'*30} {'-'*6} {'-'*8}")
        for collection, total, missing in rows:
            print(f"  {collection:<30} {total:>6} {missing:>8}")
    else:
        print("\nNo collections have missing sender_id!")
    return rows


def scan_papal_recipients(conn):
    """Scan small papal collections for extractable recipient information."""
    cursor = conn.cursor()

    # Collections with 0% recipient coverage and small size
    papal_collections = [
        'benedict_i', 'pelagius_ii', 'pope_agapetus_i',
        'pope_john_ii', 'pope_john_iii', 'pope_vigilius',
    ]

    print("\n--- Scanning papal collections for recipient information ---\n")

    for collection in papal_collections:
        cursor.execute("""
            SELECT id, ref_id, recipient_id,
                   SUBSTR(COALESCE(modern_english, english_text, ''), 1, 500)
            FROM letters
            WHERE collection = ?
            ORDER BY id
        """, (collection,))
        rows = cursor.fetchall()
        if not rows:
            continue

        print(f"  {collection} ({len(rows)} letters):")
        for letter_id, ref_id, recipient_id, text_start in rows:
            if recipient_id:
                print(f"    {ref_id}: already has recipient_id={recipient_id}")
                continue

            # Try to extract recipient from text
            recipient = None
            # Pattern: "To: <name>" or "To <name>"
            m = re.search(r'(?:^|\n)\s*(?:To[:\s]+)(.+?)(?:\n|$)', text_start)
            if m:
                recipient = m.group(1).strip().rstrip('.')
            # Pattern: "to the Patriarch of X" / "to Bishop X" etc in first line
            if not recipient:
                m = re.search(r'to (?:the )?((?:Patriarch|Bishop|Emperor|King|Deacon|Archbishop|Abbot|Presbyter)\w*\s+(?:of\s+)?[\w\s,]+?)(?:[.;:\n]|greeting)', text_start, re.IGNORECASE)
                if m:
                    recipient = m.group(1).strip().rstrip(',')
            # Pattern: "To our most reverend brother Bishop X"
            if not recipient:
                m = re.search(r'[Tt]o (?:our |the )?(?:most )?(?:reverend |beloved |dear )?(?:brother |lord |father )?(?:Bishop |Archbishop |Patriarch |Deacon |Abbot )?(\w[\w\s]*?)(?:[,.]|\s+(?:from|greeting|send))', text_start)
                if m:
                    recipient = m.group(1).strip()

            if recipient:
                # Truncate long matches
                if len(recipient) > 80:
                    recipient = recipient[:80] + '...'
                print(f"    {ref_id}: FOUND recipient -> \"{recipient}\"")
            else:
                # Show first 150 chars for manual inspection
                preview = text_start[:150].replace('\n', ' | ')
                print(f"    {ref_id}: no clear recipient pattern. Preview: {preview}")


def main():
    conn = sqlite3.connect(DB_PATH)

    print("=== Fixing missing sender_id ===\n")
    fix_senders(conn)

    print("\n=== Verification ===")
    verify_senders(conn)

    scan_papal_recipients(conn)

    conn.close()
    print("\nDone.")


if __name__ == '__main__':
    main()

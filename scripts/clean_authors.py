#!/usr/bin/env python3
"""
Data cleaning pass on the Roman Letters database.

Fixes:
1. Fake/unknown recipient entries → set recipient_id = NULL, delete fake authors
2. Generic group names → set recipient_id = NULL (keep courts as they are real entities)
3. Name annotations → clean brackets and parenthetical metadata
4. Metadata-as-names → nullify and delete
5. "An inquirer" → nullify (not a person)

Does NOT touch:
- Austrasian Court, Visigothic Court (real political entities that sent/received letters)
- Frankish Clergy (sent 12 letters — real collective sender in this context)
- Entries used as senders (checked before deletion)
"""

import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
BACKUP_PATH = DB_PATH + f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'


def get_counts(conn):
    """Get baseline stats."""
    cur = conn.cursor()
    stats = {}
    stats['total_authors'] = cur.execute("SELECT COUNT(*) FROM authors").fetchone()[0]
    stats['total_letters'] = cur.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
    stats['letters_with_recipient'] = cur.execute(
        "SELECT COUNT(*) FROM letters WHERE recipient_id IS NOT NULL").fetchone()[0]
    stats['letters_null_recipient'] = cur.execute(
        "SELECT COUNT(*) FROM letters WHERE recipient_id IS NULL").fetchone()[0]
    stats['people_mentioned_count'] = cur.execute(
        "SELECT COUNT(*) FROM people_mentioned").fetchone()[0]
    return stats


def nullify_recipient_and_delete(conn, author_ids, reason):
    """Set recipient_id = NULL for letters pointing to these authors, then delete the authors.
    Only deletes if the author is not used as a sender."""
    cur = conn.cursor()
    deleted = []
    nullified_total = 0

    for aid in author_ids:
        name = cur.execute("SELECT name FROM authors WHERE id = ?", (aid,)).fetchone()
        if not name:
            print(f"  WARNING: Author ID {aid} not found, skipping")
            continue
        name = name[0]

        # Check if used as sender
        sent = cur.execute("SELECT COUNT(*) FROM letters WHERE sender_id = ?", (aid,)).fetchone()[0]
        received = cur.execute("SELECT COUNT(*) FROM letters WHERE recipient_id = ?", (aid,)).fetchone()[0]

        # Nullify recipient references
        cur.execute("UPDATE letters SET recipient_id = NULL WHERE recipient_id = ?", (aid,))
        nullified_total += received

        # Clean people_mentioned references
        mentioned = cur.execute("SELECT COUNT(*) FROM people_mentioned WHERE person_id = ?", (aid,)).fetchone()[0]
        if mentioned > 0:
            cur.execute("DELETE FROM people_mentioned WHERE person_id = ?", (aid,))

        if sent == 0:
            cur.execute("DELETE FROM authors WHERE id = ?", (aid,))
            deleted.append((aid, name))
            print(f"  DELETED author {aid}: '{name}' ({received} letters nullified, {reason})")
        else:
            print(f"  KEPT author {aid}: '{name}' (used as sender for {sent} letters, {received} recipient refs nullified)")

    return nullified_total, deleted


def rename_author(conn, author_id, new_name):
    """Rename an author, handling potential conflicts."""
    cur = conn.cursor()
    old_name = cur.execute("SELECT name FROM authors WHERE id = ?", (author_id,)).fetchone()
    if not old_name:
        print(f"  WARNING: Author ID {author_id} not found for rename")
        return False
    old_name = old_name[0]

    # Check if new_name already exists
    existing = cur.execute("SELECT id FROM authors WHERE name = ? AND id != ?", (new_name, author_id)).fetchone()
    if existing:
        # Merge: reassign all references from author_id to existing[0], then delete author_id
        existing_id = existing[0]
        cur.execute("UPDATE letters SET sender_id = ? WHERE sender_id = ?", (existing_id, author_id))
        cur.execute("UPDATE letters SET recipient_id = ? WHERE recipient_id = ?", (existing_id, author_id))
        cur.execute("UPDATE people_mentioned SET person_id = ? WHERE person_id = ?", (existing_id, author_id))
        cur.execute("DELETE FROM authors WHERE id = ?", (author_id,))
        print(f"  MERGED author {author_id}: '{old_name}' → existing '{new_name}' (id={existing_id})")
        return True

    cur.execute("UPDATE authors SET name = ? WHERE id = ?", (new_name, author_id))
    print(f"  RENAMED author {author_id}: '{old_name}' → '{new_name}'")
    return True


def main():
    # Backup first
    print(f"Creating backup: {BACKUP_PATH}")
    shutil.copy2(DB_PATH, BACKUP_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    before = get_counts(conn)
    print("\n=== BEFORE CLEANING ===")
    for k, v in before.items():
        print(f"  {k}: {v}")

    # ──────────────────────────────────────────────
    # 1. FAKE/UNKNOWN RECIPIENTS → NULL + DELETE
    # ──────────────────────────────────────────────
    print("\n--- Step 1: Remove fake/unknown recipient entries ---")
    fake_recipient_ids = [
        93,    # Unnamed Mother and Daughter (478 letters)
        31,    # Unknown Father (168 letters)
        803,   # Unknown recipient (unknown) (89 letters)
        1281,  # A friend (name lost) (32 letters)
        1520,  # A friend (unidentified) (16 letters)
        35,    # Unknown Noble (11 letters)
        46,    # Unknown Son (5 letters)
        275,   # Anonymous Young Person (4 letters)
    ]
    n1, d1 = nullify_recipient_and_delete(conn, fake_recipient_ids, "fake/unknown person")

    # ──────────────────────────────────────────────
    # 2. GENERIC GROUP NAMES → NULL + DELETE
    # ──────────────────────────────────────────────
    print("\n--- Step 2: Remove generic group/metadata entries ---")
    group_ids = [
        842,   # An inquirer (43 letters) — not a person
        347,   # same, in answer to another question (16 letters) — section header
        380,   # Clergy, Concerning Prayer to God (12 letters) — topic, not person
        386,   # Carthaginian Clergy, About Letters Sent to Rome... (9 letters) — group + topic
        339,   # clergy of Neocæsarea (3 letters) — group
        709,   # Bishops [Gothic clergy in Constantinople] (2 letters) — group
        710,   # Provinces [published edict] (1 letter) — not a person
        696,   # Clergy of Roman Church (1 letter) — group
        471,   # Januarius, Catholic Clergy of District of Hippo... (1 letter) — group
        1495,  # The clergy, people, and orthodox monks of Constantinople (1 letter)
        1551,  # Clergy and faithful (1 letter)
        1497,  # my lord, son, and most beloved fellow-minister Diodorus... (1 letter) — full salutation
        1317,  # Governor and Scholasticus [local officials] (1 letter) — titles, not names
        642,   # Dromonarii [River Patrol Boatmen] (1 letter) — group
    ]
    n2, d2 = nullify_recipient_and_delete(conn, group_ids, "generic group/metadata")

    # Handle pairs: nullify recipient but keep note of real people
    # These are two-person entries that should not be single author entries
    print("\n--- Step 2b: Handle paired-name entries ---")
    pair_ids = [
        615,   # Albinus And Avienus (26 letters)
        113,   # Bacauda and Agnellus, Bishops (20 letters as recipient, 1 as sender)
        164,   # Victor and Columbus, Bishops (13 letters)
        167,   # Eulogius and Anastasius, Bishops (7 letters)
        807,   # Celer and Patricius [senior imperial officials] (3 letters)
    ]
    n2b, d2b = nullify_recipient_and_delete(conn, pair_ids, "paired names (not single person)")

    # NOTE: Keeping Austrasian Court (522), Visigothic Court (526), Frankish Clergy (1568),
    # Merovingian Correspondent (531) — these are real collective entities that sent letters

    # ──────────────────────────────────────────────
    # 3. CLEAN NAME ANNOTATIONS
    # ──────────────────────────────────────────────
    print("\n--- Step 3: Clean name annotations ---")

    # Specific renames from the task
    rename_author(conn, 591, "Apollinaris (son of Sidonius)")
    rename_author(conn, 759, "Faustus Junior")
    rename_author(conn, 802, "Avitus of Vienne")

    # Clean all names with [square brackets] — remove the bracketed part
    cur = conn.cursor()
    bracketed = cur.execute("SELECT id, name FROM authors WHERE name LIKE '%[%'").fetchall()
    for aid, name in bracketed:
        import re
        # Remove bracketed annotations but keep the core name
        cleaned = re.sub(r'\s*\[.*?\]', '', name).strip()
        # Remove trailing comma if any
        cleaned = cleaned.rstrip(',').strip()
        if cleaned != name and cleaned:
            rename_author(conn, aid, cleaned)

    # Clean specific parenthetical annotations that are metadata, not identity
    # But preserve disambiguation like "(son of Sidonius)" — only clean obvious metadata
    metadata_parens = cur.execute(
        "SELECT id, name FROM authors WHERE name LIKE '%(unknown)%'"
    ).fetchall()
    for aid, name in metadata_parens:
        import re
        cleaned = re.sub(r'\s*\(unknown\)', '', name).strip()
        if cleaned != name and cleaned:
            rename_author(conn, aid, cleaned)

    # Clean "Basil. ( Praises of Quiet.)" — this is a title not a name modifier
    basil = cur.execute("SELECT id, name FROM authors WHERE name = 'Basil. ( Praises of Quiet.)'").fetchone()
    if basil:
        rename_author(conn, basil[0], "Basil")

    # Clean "Senator [Cassiodorus], Praetorian" → "Cassiodorus"
    # Actually this is already a reference to Cassiodorus. Check if Cassiodorus exists.
    senator = cur.execute("SELECT id FROM authors WHERE id = 705").fetchone()
    if senator:
        rename_author(conn, 705, "Senator, Praetorian Prefect")

    # Clean names with weird parentheticals like "Aeonius, ( patron)"
    paren_names = cur.execute(
        "SELECT id, name FROM authors WHERE name LIKE '%( %' AND name NOT LIKE '%(son%' AND name NOT LIKE '%(brother%'"
    ).fetchall()
    for aid, name in paren_names:
        import re
        # Remove parenthetical metadata like "( patron)", "( baptismal )"
        cleaned = re.sub(r'\s*\(\s*\w+[\s\w]*\?\s*\)', '', name)  # handles "( son?)"
        cleaned = re.sub(r'\s*\(\s*[a-z][\s\w]*\)', '', cleaned)  # handles "( patron)"
        cleaned = cleaned.rstrip(',').strip()
        if cleaned != name and cleaned and len(cleaned) > 2:
            rename_author(conn, aid, cleaned)

    # ──────────────────────────────────────────────
    # 4. COMMIT AND REPORT
    # ──────────────────────────────────────────────
    conn.commit()

    after = get_counts(conn)
    print("\n=== AFTER CLEANING ===")
    for k, v in after.items():
        print(f"  {k}: {v}")

    print("\n=== SUMMARY ===")
    print(f"  Authors removed: {before['total_authors'] - after['total_authors']}")
    print(f"  Letters now with NULL recipient: {after['letters_null_recipient']} (was {before['letters_null_recipient']})")
    print(f"  Letters newly nullified: {after['letters_null_recipient'] - before['letters_null_recipient']}")
    print(f"  Total letters unchanged: {after['total_letters']} (was {before['total_letters']})")

    # Show remaining real authors count
    real_authors = conn.execute("""
        SELECT COUNT(*) FROM authors a
        WHERE EXISTS (SELECT 1 FROM letters WHERE sender_id = a.id)
           OR EXISTS (SELECT 1 FROM letters WHERE recipient_id = a.id)
    """).fetchone()[0]
    print(f"  Real authors (with letter connections): {real_authors}")

    orphan_authors = conn.execute("""
        SELECT COUNT(*) FROM authors a
        WHERE NOT EXISTS (SELECT 1 FROM letters WHERE sender_id = a.id)
          AND NOT EXISTS (SELECT 1 FROM letters WHERE recipient_id = a.id)
          AND NOT EXISTS (SELECT 1 FROM people_mentioned WHERE person_id = a.id)
    """).fetchone()[0]
    print(f"  Orphan authors (no letter connections at all): {orphan_authors}")

    conn.close()
    print(f"\nBackup saved at: {BACKUP_PATH}")
    print("Done!")


if __name__ == '__main__':
    main()

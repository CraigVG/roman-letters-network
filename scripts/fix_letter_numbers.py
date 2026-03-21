#!/usr/bin/env python3
"""
Fix duplicate letter_number values across collections.

Problem: Many collections have letters numbered within books (Book 1 Letter 1,
Book 2 Letter 1, etc.) but stored with flat letter_number. This causes duplicate
URLs and hidden letters on the website.

Strategy:
1. For collections WITH a populated book column:
   new letter_number = book * 1000 + original_letter_number
   (e.g., Book 3, Letter 5 -> 3005)

2. For collections WITHOUT book data but with duplicate letter_numbers:
   Use ref_id to extract a unique number, or use row ordering to disambiguate.

3. Special cases handled individually (ambrose_milan, augustine_hippo, etc.)
"""

import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

def analyze_duplicates(cur):
    """Show current duplicate situation."""
    cur.execute("""
        SELECT collection, COUNT(*) as dup_letter_numbers
        FROM (
            SELECT collection, letter_number
            FROM letters
            GROUP BY collection, letter_number
            HAVING COUNT(*) > 1
        )
        GROUP BY collection
        ORDER BY dup_letter_numbers DESC
    """)
    rows = cur.fetchall()
    if rows:
        print("\n=== Collections with duplicate letter_numbers ===")
        for collection, count in rows:
            print(f"  {collection}: {count} duplicate letter_numbers")
    else:
        print("\n=== No duplicate letter_numbers found! ===")
    return rows


def fix_collections_with_books(cur):
    """
    For collections where book column is populated,
    set letter_number = book * 1000 + letter_number.
    """
    # Find collections that have book data AND duplicates
    cur.execute("""
        SELECT DISTINCT l.collection
        FROM letters l
        WHERE l.book IS NOT NULL
        AND l.collection IN (
            SELECT collection FROM (
                SELECT collection, letter_number
                FROM letters
                GROUP BY collection, letter_number
                HAVING COUNT(*) > 1
            )
        )
    """)
    collections_with_books = [r[0] for r in cur.fetchall()]

    for collection in collections_with_books:
        # Check how many have book data
        cur.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN book IS NOT NULL THEN 1 ELSE 0 END) as has_book
            FROM letters WHERE collection = ?
        """, (collection,))
        total, has_book = cur.fetchone()

        print(f"\n--- Fixing {collection} ({total} letters, {has_book} with book data) ---")

        # First, handle letters WITH book data
        if has_book > 0:
            # Check max letter_number per book to ensure no overflow
            cur.execute("""
                SELECT book, MAX(letter_number) FROM letters
                WHERE collection = ? AND book IS NOT NULL
                GROUP BY book ORDER BY book
            """, (collection,))
            book_info = cur.fetchall()
            for book, max_ln in book_info:
                if max_ln >= 1000:
                    print(f"  WARNING: Book {book} has letter_number {max_ln} >= 1000!")

            # Update: new letter_number = book * 1000 + letter_number
            cur.execute("""
                UPDATE letters
                SET letter_number = book * 1000 + letter_number
                WHERE collection = ? AND book IS NOT NULL
            """, (collection,))
            updated = cur.rowcount
            print(f"  Updated {updated} letters with book data (letter_number = book*1000 + letter_number)")

        # Now handle letters WITHOUT book data in this collection (orphans)
        cur.execute("""
            SELECT id, ref_id, letter_number FROM letters
            WHERE collection = ? AND book IS NULL
            ORDER BY id
        """, (collection,))
        orphans = cur.fetchall()
        if orphans:
            print(f"  {len(orphans)} letters without book data - disambiguating...")
            for row_id, ref_id, ln in orphans:
                # Check if this letter_number now conflicts
                cur.execute("""
                    SELECT COUNT(*) FROM letters
                    WHERE collection = ? AND letter_number = ? AND id != ?
                """, (collection, ln, row_id))
                conflict = cur.fetchone()[0]
                if conflict > 0:
                    # Try to extract info from ref_id
                    # Common patterns: collection.lat.N, collection.N
                    # For these orphans, put them in "book 0" (prefix 0)
                    # Actually, just find the next available number
                    new_ln = ln
                    while True:
                        cur.execute("""
                            SELECT COUNT(*) FROM letters
                            WHERE collection = ? AND letter_number = ? AND id != ?
                        """, (collection, new_ln, row_id))
                        if cur.fetchone()[0] == 0:
                            break
                        new_ln += 10000  # Put in a high range
                    if new_ln != ln:
                        cur.execute("UPDATE letters SET letter_number = ? WHERE id = ?", (new_ln, row_id))
                        print(f"    Moved orphan id={row_id} ref_id={ref_id}: {ln} -> {new_ln}")


def fix_no_book_collections(cur):
    """
    For collections without book data, disambiguate using ref_id or row order.
    """
    # Collections with duplicates but NO book data
    cur.execute("""
        SELECT collection FROM (
            SELECT collection, letter_number
            FROM letters
            GROUP BY collection, letter_number
            HAVING COUNT(*) > 1
        )
        GROUP BY collection
    """)
    dup_collections = [r[0] for r in cur.fetchall()]

    # Filter to those without book data
    no_book_collections = []
    for coll in dup_collections:
        cur.execute("""
            SELECT SUM(CASE WHEN book IS NOT NULL THEN 1 ELSE 0 END)
            FROM letters WHERE collection = ?
        """, (coll,))
        has_book = cur.fetchone()[0] or 0
        if has_book == 0:
            no_book_collections.append(coll)

    for collection in no_book_collections:
        print(f"\n--- Fixing {collection} (no book data) ---")

        # Get all duplicate letter_numbers
        cur.execute("""
            SELECT letter_number, COUNT(*) as cnt
            FROM letters
            WHERE collection = ?
            GROUP BY letter_number
            HAVING COUNT(*) > 1
            ORDER BY letter_number
        """, (collection,))
        dup_lns = cur.fetchall()

        for ln, cnt in dup_lns:
            # Get all rows with this letter_number
            cur.execute("""
                SELECT id, ref_id, letter_number
                FROM letters
                WHERE collection = ? AND letter_number = ?
                ORDER BY id
            """, (collection, ln))
            rows = cur.fetchall()

            # Keep the first one, renumber the rest
            # Try to extract unique numbers from ref_id
            for i, (row_id, ref_id, letter_num) in enumerate(rows):
                if i == 0:
                    continue  # Keep the first one as-is

                # Try to extract a unique number from ref_id
                # Patterns: augustine_hippo.N, augustine.ep.N, ambrose_milan.lat.N, etc.
                new_ln = None
                if ref_id:
                    parts = ref_id.split('.')
                    # Try to use the last numeric part
                    for part in reversed(parts):
                        try:
                            num = int(part)
                            # Check if this would be unique
                            new_ln = num + 50000  # High offset to avoid conflicts
                            break
                        except ValueError:
                            continue

                if new_ln is None:
                    new_ln = ln + (i * 10000)

                # Ensure uniqueness
                while True:
                    cur.execute("""
                        SELECT COUNT(*) FROM letters
                        WHERE collection = ? AND letter_number = ? AND id != ?
                    """, (collection, new_ln, row_id))
                    if cur.fetchone()[0] == 0:
                        break
                    new_ln += 1

                cur.execute("UPDATE letters SET letter_number = ? WHERE id = ?", (new_ln, row_id))
                print(f"  {ref_id}: letter_number {letter_num} -> {new_ln}")


def fix_ambrose_special(cur):
    """
    Ambrose has three numbering systems in ref_ids:
    - ambrose_milan.lat.N (Latin library numbering)
    - ambrose_milan.N (Faller/Zelzer numbering)
    - ambrose.ep.N (traditional numbering)

    These are DIFFERENT editions of the same letters, but some are genuinely
    different letters. We need to keep them all with unique letter_numbers.
    """
    # Check if ambrose still has duplicates (may have been handled)
    cur.execute("""
        SELECT letter_number, COUNT(*) FROM letters
        WHERE collection = 'ambrose_milan'
        GROUP BY letter_number HAVING COUNT(*) > 1
    """)
    if not cur.fetchall():
        print("\n--- ambrose_milan: no duplicates remaining ---")
        return
    # Will be handled by fix_no_book_collections since book is NULL


def fix_chrysostom_libanius(cur):
    """Handle the 1-2 duplicates in chrysostom and libanius."""
    for collection in ('chrysostom', 'libanius'):
        cur.execute("""
            SELECT letter_number, COUNT(*) FROM letters
            WHERE collection = ?
            GROUP BY letter_number HAVING COUNT(*) > 1
        """, (collection,))
        dups = cur.fetchall()
        if not dups:
            continue

        print(f"\n--- Fixing {collection} ---")
        for ln, cnt in dups:
            cur.execute("""
                SELECT id, ref_id, letter_number FROM letters
                WHERE collection = ? AND letter_number = ?
                ORDER BY id
            """, (collection, ln))
            rows = cur.fetchall()
            for i, (row_id, ref_id, letter_num) in enumerate(rows):
                if i == 0:
                    continue
                # Find next available number
                new_ln = letter_num + 10000
                while True:
                    cur.execute("""
                        SELECT COUNT(*) FROM letters
                        WHERE collection = ? AND letter_number = ?
                    """, (collection, new_ln))
                    if cur.fetchone()[0] == 0:
                        break
                    new_ln += 1
                cur.execute("UPDATE letters SET letter_number = ? WHERE id = ?", (new_ln, row_id))
                print(f"  {ref_id}: letter_number {letter_num} -> {new_ln}")


def fix_null_letter_numbers(cur):
    """Fix any rows with NULL letter_number by extracting from ref_id."""
    cur.execute("""
        SELECT id, collection, ref_id FROM letters WHERE letter_number IS NULL
    """)
    nulls = cur.fetchall()
    if not nulls:
        print("\nNo NULL letter_numbers found.")
        return

    print(f"\nFixing {len(nulls)} rows with NULL letter_number...")
    for row_id, collection, ref_id in nulls:
        # Try to extract a number from ref_id
        new_ln = None
        if ref_id:
            parts = ref_id.split('.')
            # Build a unique number from numeric parts
            nums = []
            for part in parts:
                try:
                    nums.append(int(part))
                except ValueError:
                    pass
            if nums:
                # Use last number + high offset
                new_ln = 60000 + nums[-1]
                if len(nums) > 1:
                    new_ln = 60000 + nums[-2] * 100 + nums[-1]

        if new_ln is None:
            new_ln = 60000 + row_id  # Fallback: use row id

        # Ensure uniqueness
        while True:
            cur.execute("""
                SELECT COUNT(*) FROM letters
                WHERE collection = ? AND letter_number = ? AND id != ?
            """, (collection, new_ln, row_id))
            if cur.fetchone()[0] == 0:
                break
            new_ln += 1

        cur.execute("UPDATE letters SET letter_number = ? WHERE id = ?", (new_ln, row_id))
        print(f"  {collection} id={row_id} ref_id={ref_id}: NULL -> {new_ln}")


def verify(cur):
    """Verify no duplicates remain."""
    cur.execute("""
        SELECT collection, letter_number, COUNT(*) as cnt
        FROM letters
        GROUP BY collection, letter_number
        HAVING COUNT(*) > 1
    """)
    remaining = cur.fetchall()
    if remaining:
        print(f"\n!!! WARNING: {len(remaining)} duplicate (collection, letter_number) pairs remain !!!")
        for coll, ln, cnt in remaining[:20]:
            print(f"  {coll} letter_number={ln}: {cnt} rows")
        return False
    else:
        print("\n=== VERIFIED: Zero duplicate (collection, letter_number) pairs! ===")
        return True


def show_sample(cur):
    """Show sample results for key collections."""
    for coll in ('pliny_younger', 'cassiodorus', 'symmachus', 'sidonius_apollinaris'):
        cur.execute("""
            SELECT ref_id, book, letter_number FROM letters
            WHERE collection = ?
            ORDER BY letter_number
            LIMIT 5
        """, (coll,))
        rows = cur.fetchall()
        print(f"\n  Sample {coll}:")
        for ref_id, book, ln in rows:
            print(f"    {ref_id} book={book} letter_number={ln}")

        cur.execute("SELECT COUNT(*) FROM letters WHERE collection = ?", (coll,))
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT letter_number) FROM letters WHERE collection = ?", (coll,))
        distinct = cur.fetchone()[0]
        print(f"    Total: {total}, Distinct letter_numbers: {distinct}")


def main():
    print(f"Database: {os.path.abspath(DB_PATH)}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Show initial state
    print("\n" + "="*60)
    print("BEFORE FIX")
    print("="*60)
    analyze_duplicates(cur)

    # Count total letters
    cur.execute("SELECT COUNT(*) FROM letters")
    total = cur.fetchone()[0]
    print(f"\nTotal letters in database: {total}")

    # Step 0: Fix NULL letter_numbers
    print("\n" + "="*60)
    print("STEP 0: Fix NULL letter_numbers")
    print("="*60)
    fix_null_letter_numbers(cur)

    # Step 1: Fix collections with book data
    print("\n" + "="*60)
    print("STEP 1: Fix collections WITH book data")
    print("="*60)
    fix_collections_with_books(cur)

    # Step 2: Fix collections without book data
    print("\n" + "="*60)
    print("STEP 2: Fix collections WITHOUT book data")
    print("="*60)
    fix_no_book_collections(cur)

    # Step 3: Fix chrysostom and libanius
    print("\n" + "="*60)
    print("STEP 3: Fix remaining edge cases")
    print("="*60)
    fix_chrysostom_libanius(cur)

    # Verify
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    success = verify(cur)

    if success:
        analyze_duplicates(cur)
        show_sample(cur)
        conn.commit()
        print("\n=== Changes committed to database ===")
    else:
        print("\n!!! Rolling back - duplicates still exist !!!")
        conn.rollback()
        sys.exit(1)

    conn.close()
    print("\nDone!")


if __name__ == '__main__':
    main()

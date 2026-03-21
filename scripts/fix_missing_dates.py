#!/usr/bin/env python3
"""
Fix missing year_approx dates in the Roman Letters database.

Only updates letters where year_approx IS NULL.
Distributes letters evenly across each author's known active period.
For collections with some existing dates, uses book data if available
to infer chronological position.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

def distribute_evenly(start_year, end_year, count):
    """Generate evenly distributed years across a range."""
    years = []
    for i in range(count):
        year = start_year + round((end_year - start_year) * i / max(count - 1, 1))
        years.append(year)
    return years


def fix_all_null_collection(cur, collection, start_year, end_year):
    """Fix a collection where ALL letters lack dates."""
    cur.execute(
        "SELECT id FROM letters WHERE collection = ? AND year_approx IS NULL ORDER BY id",
        (collection,)
    )
    rows = cur.fetchall()
    if not rows:
        return 0

    years = distribute_evenly(start_year, end_year, len(rows))
    for (letter_id,), year in zip(rows, years):
        cur.execute(
            "UPDATE letters SET year_approx = ? WHERE id = ? AND year_approx IS NULL",
            (year, letter_id)
        )
    return len(rows)


def fix_partial_collection_with_books(cur, collection, start_year, end_year):
    """
    Fix a collection where SOME letters have dates.
    Uses book numbers to infer chronological position if available.
    """
    # Get undated letters
    cur.execute(
        "SELECT id, book FROM letters WHERE collection = ? AND year_approx IS NULL ORDER BY id",
        (collection,)
    )
    undated = cur.fetchall()
    if not undated:
        return 0

    # Check if book data exists for undated letters
    has_books = any(book is not None for _, book in undated)

    if has_books:
        # Get date ranges per book from existing dated letters
        cur.execute(
            """SELECT book, MIN(year_approx), MAX(year_approx), COUNT(*)
               FROM letters WHERE collection = ? AND year_approx IS NOT NULL AND book IS NOT NULL
               GROUP BY book ORDER BY book""",
            (collection,)
        )
        book_ranges = {row[0]: (row[1], row[2]) for row in cur.fetchall()}

        # For undated letters with a known book, use that book's date range
        # For undated letters without a book, use the full author range
        updated = 0
        # Group undated by book
        by_book = {}
        no_book = []
        for letter_id, book in undated:
            if book is not None:
                by_book.setdefault(book, []).append(letter_id)
            else:
                no_book.append(letter_id)

        # Assign dates for letters with book numbers
        for book in sorted(by_book.keys()):
            ids = by_book[book]
            if book in book_ranges:
                b_start, b_end = book_ranges[book]
            else:
                # Book exists but no dated letters in it; interpolate from surrounding books
                known_books = sorted(book_ranges.keys())
                if known_books:
                    # Find surrounding books
                    lower = [b for b in known_books if b < book]
                    upper = [b for b in known_books if b > book]
                    if lower and upper:
                        b_start = book_ranges[lower[-1]][1]  # max of previous book
                        b_end = book_ranges[upper[0]][0]      # min of next book
                    elif lower:
                        b_start = book_ranges[lower[-1]][0]
                        b_end = end_year
                    elif upper:
                        b_start = start_year
                        b_end = book_ranges[upper[0]][1]
                    else:
                        b_start, b_end = start_year, end_year
                else:
                    b_start, b_end = start_year, end_year

            years = distribute_evenly(b_start, b_end, len(ids))
            for lid, year in zip(ids, years):
                cur.execute(
                    "UPDATE letters SET year_approx = ? WHERE id = ? AND year_approx IS NULL",
                    (year, lid)
                )
            updated += len(ids)

        # Assign dates for letters without book numbers
        if no_book:
            years = distribute_evenly(start_year, end_year, len(no_book))
            for lid, year in zip(no_book, years):
                cur.execute(
                    "UPDATE letters SET year_approx = ? WHERE id = ? AND year_approx IS NULL",
                    (year, lid)
                )
            updated += len(no_book)

        return updated
    else:
        # No book data, distribute evenly
        ids = [r[0] for r in undated]
        years = distribute_evenly(start_year, end_year, len(ids))
        for lid, year in zip(ids, years):
            cur.execute(
                "UPDATE letters SET year_approx = ? WHERE id = ? AND year_approx IS NULL",
                (year, lid)
            )
        return len(ids)


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    total_updated = 0

    # ── 1. Collections where ALL letters lack dates ──
    all_null_collections = {
        'isidore_pelusium':     (390, 435),
        'hormisdas':            (514, 523),
        'venantius_fortunatus':  (566, 600),
        'gregory_nazianzus':    (362, 390),
        'paulinus_nola':        (393, 431),
        # Small papal collections (all NULL)
        'gelasius_i':           (492, 496),
        'innocent_i':           (401, 417),
        'simplicius_pope':      (468, 483),
        'pope_symmachus':       (498, 514),
        'pope_anastasius_ii':   (496, 498),
        'pope_john_ii':         (533, 535),
        'pope_agapetus_i':      (535, 536),
        'pope_vigilius':        (537, 555),
        'benedict_i':           (574, 579),
        'pope_john_iii':        (561, 574),
        'pelagius_ii':          (579, 590),
    }

    for collection, (start, end) in all_null_collections.items():
        count = fix_all_null_collection(cur, collection, start, end)
        if count > 0:
            print(f"  {collection}: updated {count} letters ({start}-{end} AD)")
            total_updated += count

    # ── 2. Collections where SOME letters have dates ──
    partial_collections = {
        'libanius':       (314, 393),
        'gregory_great':  (590, 604),
        # Additional partial collections found in the data
        'julian_emperor': (355, 363),
        'synesius_cyrene': (394, 413),
        'pope_felix_iii': (483, 492),
        'pope_hilary':    (461, 468),
        'pelagius_i':     (556, 561),
    }

    for collection, (start, end) in partial_collections.items():
        count = fix_partial_collection_with_books(cur, collection, start, end)
        if count > 0:
            print(f"  {collection}: updated {count} letters ({start}-{end} AD)")
            total_updated += count

    conn.commit()

    # ── 3. Verify ──
    print(f"\nTotal letters updated: {total_updated}")
    print("\nVerification — collections still missing dates:")
    cur.execute("""
        SELECT collection, COUNT(*) as total,
               SUM(CASE WHEN year_approx IS NULL THEN 1 ELSE 0 END) as missing
        FROM letters
        GROUP BY collection
        HAVING missing > 0
        ORDER BY missing DESC
    """)
    remaining = cur.fetchall()
    if remaining:
        for row in remaining:
            print(f"  {row[0]}: {row[2]}/{row[1]} missing")
    else:
        print("  None! All letters have dates.")

    conn.close()


if __name__ == '__main__':
    main()

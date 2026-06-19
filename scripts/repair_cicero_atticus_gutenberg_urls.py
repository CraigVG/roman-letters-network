#!/usr/bin/env python3
"""Repair Cicero Atticus Project Gutenberg translation URLs by book."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"
COLLECTION = "cicero_atticus"

VOLUME_URLS = {
    1: "https://www.gutenberg.org/ebooks/58418",
    2: "https://www.gutenberg.org/ebooks/50692",
    3: "https://www.gutenberg.org/ebooks/51403",
}

BOOK_TO_VOLUME = {
    **{book: 1 for book in range(1, 7)},
    **{book: 2 for book in range(7, 12)},
    **{book: 3 for book in range(12, 17)},
}


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def expected_url(book: int) -> str:
    if book not in BOOK_TO_VOLUME:
        raise ValueError(f"Unexpected Cicero Atticus book outside 1-16: {book}")
    return VOLUME_URLS[BOOK_TO_VOLUME[book]]


def repair_urls(db_path: str | Path = DEFAULT_DB, dry_run: bool = False) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, book, letter_number, translation_url
            FROM letters
            WHERE collection = ?
            ORDER BY book, letter_number, id
            """,
            (COLLECTION,),
        ).fetchall()
        if not rows:
            raise ValueError("No Cicero Atticus rows found")

        unexpected_books = sorted({row["book"] for row in rows if row["book"] not in BOOK_TO_VOLUME})
        if unexpected_books:
            raise ValueError(f"Unexpected Cicero Atticus books: {unexpected_books}")

        updates: list[tuple[int, int, int, str | None, str]] = []
        by_volume = {1: 0, 2: 0, 3: 0}
        for row in rows:
            book = int(row["book"])
            target_url = expected_url(book)
            by_volume[BOOK_TO_VOLUME[book]] += 1
            current_url = row["translation_url"]
            if current_url != target_url:
                updates.append(
                    (
                        int(row["id"]),
                        book,
                        int(row["letter_number"]),
                        current_url,
                        target_url,
                    )
                )

        result = {
            "matched": len(rows),
            "updated": len(updates),
            "dry_run": dry_run,
            "by_volume": by_volume,
            "updates": updates,
        }

        if dry_run:
            return result

        for row_id, _book, _letter_number, _current_url, target_url in updates:
            conn.execute(
                """
                UPDATE letters
                SET translation_url = ?
                WHERE id = ?
                  AND collection = ?
                """,
                (target_url, row_id, COLLECTION),
            )
        conn.commit()
        return result
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=DEFAULT_DB, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = repair_urls(args.db, dry_run=args.dry_run)
    mode = "DRY RUN" if args.dry_run else "UPDATED"
    print(f"{mode}: Cicero Atticus Gutenberg translation URLs")
    print(f"Rows matched: {result['matched']}")
    print(f"Rows needing update: {result['updated']}")
    for volume, count in sorted(result["by_volume"].items()):
        print(f"Volume {volume}: {count} rows -> {VOLUME_URLS[volume]}")
    if result["updates"]:
        preview = result["updates"][:10]
        print("Update preview:")
        for _row_id, book, letter_number, current_url, target_url in preview:
            print(f"  book {book}, letter {letter_number}: {current_url or '[blank]'} -> {target_url}")
        if len(result["updates"]) > len(preview):
            print(f"  ... and {len(result['updates']) - len(preview)} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

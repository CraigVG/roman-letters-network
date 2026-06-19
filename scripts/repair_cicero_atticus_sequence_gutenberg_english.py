#!/usr/bin/env python3
"""Repair sequence-matched Cicero Atticus Gutenberg English scaffolding."""

from __future__ import annotations

import argparse
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import repair_cicero_atticus_gutenberg_english as gutenberg


DEFAULT_DB = gutenberg.DEFAULT_DB
COLLECTION = gutenberg.COLLECTION
TRANSLATION_SOURCE = "gutenberg_winstedt_sequence_repair_v1"
TARGET_BOOKS = (3, 6, 9, 10, 11, 14, 15)
EXPECTED_REPAIR_COUNT = 114
TARGET_LETTERS = (
    65,
    67,
    121,
    165,
    166,
    167,
    168,
    169,
    170,
    171,
    172,
    173,
    174,
    175,
    176,
    177,
    178,
    179,
    180,
    181,
    182,
    183,
    184,
    185,
    186,
    187,
    188,
    189,
    193,
    194,
    195,
    196,
    197,
    198,
    199,
    200,
    201,
    202,
    203,
    204,
    205,
    206,
    207,
    208,
    209,
    210,
    211,
    212,
    217,
    218,
    219,
    220,
    221,
    222,
    223,
    224,
    225,
    226,
    227,
    228,
    229,
    230,
    231,
    232,
    233,
    234,
    235,
    236,
    237,
    238,
    239,
    365,
    366,
    367,
    368,
    369,
    370,
    371,
    372,
    373,
    374,
    375,
    376,
    378,
    379,
    380,
    381,
    382,
    383,
    384,
    385,
    386,
    387,
    388,
    389,
    390,
    391,
    392,
    393,
    394,
    395,
    396,
    397,
    398,
    399,
    400,
    401,
    402,
    403,
    404,
    405,
    406,
    407,
    408,
)


@dataclass(frozen=True)
class SequenceRepairCandidate:
    row_id: int
    letter_number: int
    book: int
    sequence: int
    old_text: str
    new_text: str
    old_translation_url: str | None
    new_translation_url: str
    old_translation_source: str | None
    parsed_heading: str

    @property
    def pending(self) -> bool:
        return (
            gutenberg.comparable_text(self.old_text) != gutenberg.comparable_text(self.new_text)
            or (self.old_translation_url or "") != self.new_translation_url
            or (self.old_translation_source or "") != TRANSLATION_SOURCE
        )


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def required_columns_present(conn: sqlite3.Connection) -> None:
    columns = gutenberg.table_columns(conn, "letters")
    required = {
        "id",
        "collection",
        "book",
        "letter_number",
        "english_text",
        "modern_english",
        "translation_source",
        "translation_url",
    }
    missing = required - columns
    if missing:
        raise ValueError(f"letters table is missing required columns: {sorted(missing)}")


def group_parsed_by_book(
    parsed_letters: Iterable[gutenberg.ParsedLetter],
) -> dict[int, list[gutenberg.ParsedLetter]]:
    grouped: dict[int, list[gutenberg.ParsedLetter]] = defaultdict(list)
    for parsed in parsed_letters:
        grouped[parsed.book].append(parsed)
    for book, items in grouped.items():
        items.sort(key=lambda item: item.sequence)
        for expected_sequence, parsed in enumerate(items, 1):
            if parsed.sequence != expected_sequence:
                raise ValueError(
                    f"Parsed Gutenberg book {book} has non-contiguous sequence at "
                    f"{parsed.heading!r}: expected {expected_sequence}, got {parsed.sequence}"
                )
    return dict(grouped)


def fetch_db_book_rows(conn: sqlite3.Connection, book: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT id, book, letter_number, english_text, modern_english,
               translation_source, translation_url
        FROM letters
        WHERE collection = ? AND book = ?
        ORDER BY CAST(letter_number AS INTEGER), id
        """,
        (COLLECTION, book),
    ).fetchall()


def plan_sequence_repairs(
    conn: sqlite3.Connection,
    parsed_letters: Sequence[gutenberg.ParsedLetter],
    target_letters: Sequence[int] = TARGET_LETTERS,
    target_books: Sequence[int] = TARGET_BOOKS,
    expected_count: int = EXPECTED_REPAIR_COUNT,
) -> list[SequenceRepairCandidate]:
    required_columns_present(conn)

    target_letter_set = {int(letter) for letter in target_letters}
    target_book_set = {int(book) for book in target_books}
    if len(target_letter_set) != len(target_letters):
        raise ValueError("Target letters must be unique")
    if len(target_letter_set) != expected_count:
        raise ValueError(
            f"Expected {expected_count} target letters, found {len(target_letter_set)}"
        )

    parsed_by_book = group_parsed_by_book(parsed_letters)
    candidates: list[SequenceRepairCandidate] = []
    seen_letters: set[int] = set()

    for book in sorted(target_book_set):
        parsed_rows = parsed_by_book.get(book)
        if not parsed_rows:
            raise ValueError(f"No parsed Gutenberg rows found for target book {book}")

        db_rows = fetch_db_book_rows(conn, book)
        if len(db_rows) != len(parsed_rows):
            raise ValueError(
                f"Book {book} DB/source count mismatch: "
                f"{len(db_rows)} DB rows vs {len(parsed_rows)} parsed rows"
            )

        for sequence, (row, parsed) in enumerate(zip(db_rows, parsed_rows), 1):
            if parsed.book != book or parsed.sequence != sequence:
                raise ValueError(
                    f"Book {book} sequence mismatch at DB sequence {sequence}: "
                    f"parsed book={parsed.book} sequence={parsed.sequence}"
                )

            letter_number = int(row["letter_number"])
            if letter_number not in target_letter_set:
                continue

            seen_letters.add(letter_number)
            if book not in target_book_set:
                raise ValueError(f"Target letter {letter_number} is outside target books")
            if (row["modern_english"] or "").strip():
                raise ValueError(
                    f"Target letter {letter_number} already has modern_english; stop"
                )

            gutenberg.validate_parsed_text(parsed.text, parsed.heading)
            candidates.append(
                SequenceRepairCandidate(
                    row_id=int(row["id"]),
                    letter_number=letter_number,
                    book=book,
                    sequence=sequence,
                    old_text=row["english_text"] or "",
                    new_text=parsed.text,
                    old_translation_url=row["translation_url"],
                    new_translation_url=parsed.translation_url,
                    old_translation_source=row["translation_source"],
                    parsed_heading=parsed.heading,
                )
            )

    missing_targets = sorted(target_letter_set - seen_letters)
    if missing_targets:
        sample = ", ".join(str(item) for item in missing_targets[:20])
        raise ValueError(f"Missing target letters in count-matched books: {sample}")

    if len(candidates) != expected_count:
        raise ValueError(f"Expected {expected_count} candidates, found {len(candidates)}")

    return sorted(candidates, key=lambda item: item.letter_number)


def pending_repairs(
    candidates: Iterable[SequenceRepairCandidate],
) -> list[SequenceRepairCandidate]:
    return [candidate for candidate in candidates if candidate.pending]


def summarize_by_book(candidates: Iterable[SequenceRepairCandidate]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for candidate in candidates:
        counts[candidate.book] = counts.get(candidate.book, 0) + 1
    return dict(sorted(counts.items()))


def apply_sequence_repairs(
    db_path: str | Path = DEFAULT_DB,
    parsed_letters: Sequence[gutenberg.ParsedLetter] | None = None,
    dry_run: bool = False,
    target_letters: Sequence[int] = TARGET_LETTERS,
    target_books: Sequence[int] = TARGET_BOOKS,
    expected_count: int = EXPECTED_REPAIR_COUNT,
) -> dict[str, Any]:
    parsed_letters = parsed_letters if parsed_letters is not None else gutenberg.fetch_and_parse_gutenberg()
    conn = connect(db_path)
    try:
        candidates = plan_sequence_repairs(
            conn,
            parsed_letters,
            target_letters=target_letters,
            target_books=target_books,
            expected_count=expected_count,
        )
        pending = pending_repairs(candidates)

        result: dict[str, Any] = {
            "dry_run": dry_run,
            "parsed_letters": len(parsed_letters),
            "targeted": len(candidates),
            "updated": len(pending),
            "target_books": list(target_books),
            "target_counts_by_book": summarize_by_book(candidates),
            "updated_letters": [candidate.letter_number for candidate in pending],
            "translation_source": TRANSLATION_SOURCE,
        }
        if dry_run:
            return result

        for candidate in pending:
            conn.execute(
                """
                UPDATE letters
                SET english_text = ?,
                    translation_url = ?,
                    translation_source = ?
                WHERE id = ?
                """,
                (
                    candidate.new_text,
                    candidate.new_translation_url,
                    TRANSLATION_SOURCE,
                    candidate.row_id,
                ),
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

    result = apply_sequence_repairs(args.db, dry_run=args.dry_run)
    mode = "DRY RUN" if args.dry_run else "UPDATED"
    print(f"{mode}: Cicero Atticus sequence-based Gutenberg English repair")
    print(f"Parsed Gutenberg letter sections: {result['parsed_letters']}")
    print(f"Targeted repair rows: {result['targeted']}")
    print(f"Rows pending update: {result['updated']}")
    print(f"Target books: {result['target_books']}")
    print(f"Target counts by book: {result['target_counts_by_book']}")
    print(f"Translation source: {result['translation_source']}")
    if result["updated_letters"]:
        updated = ", ".join(str(item) for item in result["updated_letters"][:120])
        print(f"Pending letter numbers: {updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

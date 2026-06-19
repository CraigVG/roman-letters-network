#!/usr/bin/env python3
"""Backfill Gregory the Great original Latin from public-domain PL77 OCR.

This script updates existing ``gregory_great`` rows only. It does not insert new
letters and it never overwrites a non-empty ``latin_text`` value.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sqlite3
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "roman_letters.db"
LEGACY_PARSER_PATH = ROOT / "scripts" / "scrape_gregory_pl77.py"

PL77_DJVU_TEXT_URL = (
    "https://archive.org/download/bim_early-english-books-1641-1700_1849_77/"
    "bim_early-english-books-1641-1700_1849_77_djvu.txt"
)
PL77_ARCHIVE_PAGE = "https://archive.org/details/bim_early-english-books-1641-1700_1849_77"
PL77_CACHE = Path("/tmp/pl77_gregory.txt")
DEFAULT_MIN_TEXT_CHARS = 300


@dataclass(frozen=True)
class ParsedLetter:
    db_number: int
    book: int
    pl_letter_num: int
    latin_text: str
    recipient_name: str = ""
    salutation: str = ""


@dataclass(frozen=True)
class PlannedUpdate:
    id: int
    letter_number: int
    latin_text: str


def load_legacy_parser() -> Any:
    spec = importlib.util.spec_from_file_location("scrape_gregory_pl77", LEGACY_PARSER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load parser at {LEGACY_PARSER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_source_text(source_text: Path | None = None) -> str:
    path = source_text or PL77_CACHE
    if path.exists() and path.stat().st_size > 1_000_000:
        return path.read_text(encoding="utf-8", errors="replace")

    req = urllib.request.Request(
        PL77_DJVU_TEXT_URL,
        headers={"User-Agent": "RomanLettersResearch/1.0 (academic research)"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    path.write_text(text, encoding="utf-8")
    return text


def looks_like_latin_letter(text: str, min_chars: int = DEFAULT_MIN_TEXT_CHARS) -> bool:
    body = re.sub(r"\s+", " ", text).strip()
    if len(body) < min_chars:
        return False
    lower = body.lower()
    if "home encyclopedia summa fathers bible" in lower:
        return False
    if "bookreader requires javascript" in lower:
        return False

    alpha = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]", body)
    if len(alpha) < min_chars // 2:
        return False

    latin_signals = (
        "gregorius",
        "domino",
        "fraternitas",
        "vestra",
        "quoniam",
        "sanct",
        "episcop",
        "presbyter",
        "eccles",
        "praecip",
    )
    if not any(signal in lower for signal in latin_signals):
        return False

    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]{2,}", lower)
    if not words:
        return False
    short_common = {"et", "in", "ut", "ad", "de", "non", "si", "qui", "est", "cum"}
    return sum(1 for word in words if word in short_common or len(word) > 3) >= 25


def parse_pl77_letters(source_text: str, min_chars: int = DEFAULT_MIN_TEXT_CHARS) -> dict[int, ParsedLetter]:
    parser = load_legacy_parser()
    parsed: dict[int, ParsedLetter] = {}

    for index, (book, start) in enumerate(parser.BOOK_POSITIONS):
        end = parser.BOOK_POSITIONS[index + 1][1] if index + 1 < len(parser.BOOK_POSITIONS) else parser.TEXT_END
        book_text = source_text[start:end]
        for item in parser.parse_book(book, book_text):
            db_number = book * 1000 + int(item["pl_letter_num"])
            latin_text = item["latin_text"].strip()
            if not looks_like_latin_letter(latin_text, min_chars=min_chars):
                continue
            candidate = ParsedLetter(
                db_number=db_number,
                book=book,
                pl_letter_num=int(item["pl_letter_num"]),
                latin_text=latin_text,
                recipient_name=item.get("recipient_name", ""),
                salutation=item.get("salutation", ""),
            )
            existing = parsed.get(db_number)
            if existing is None or len(candidate.latin_text) > len(existing.latin_text):
                parsed[db_number] = candidate

    return parsed


def missing_gregory_original_rows(conn: sqlite3.Connection) -> list[tuple[int, int]]:
    return conn.execute(
        """
        SELECT id, letter_number
        FROM letters
        WHERE collection = 'gregory_great'
          AND (latin_text IS NULL OR trim(latin_text) = '')
        ORDER BY letter_number
        """
    ).fetchall()


def build_update_plan(
    conn: sqlite3.Connection,
    parsed: dict[int, ParsedLetter],
    *,
    limit: int | None = None,
) -> list[PlannedUpdate]:
    updates: list[PlannedUpdate] = []
    for row_id, letter_number in missing_gregory_original_rows(conn):
        parsed_letter = parsed.get(letter_number)
        if not parsed_letter:
            continue
        updates.append(
            PlannedUpdate(
                id=int(row_id),
                letter_number=int(letter_number),
                latin_text=parsed_letter.latin_text,
            )
        )
        if limit is not None and len(updates) >= limit:
            break
    return updates


def collection_source_needs_update(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT latin_source_url FROM collections WHERE slug = 'gregory_great'"
    ).fetchone()
    return row is not None and (row[0] or "") != PL77_DJVU_TEXT_URL


def apply_updates(conn: sqlite3.Connection, updates: list[PlannedUpdate]) -> int:
    applied = 0
    for update in updates:
        cur = conn.execute(
            """
            UPDATE letters
            SET latin_text = ?,
                scan_url = ?
            WHERE id = ?
              AND collection = 'gregory_great'
              AND (latin_text IS NULL OR trim(latin_text) = '')
            """,
            (update.latin_text, PL77_ARCHIVE_PAGE, update.id),
        )
        applied += cur.rowcount

    conn.execute(
        """
        UPDATE collections
        SET latin_source_url = ?
        WHERE slug = 'gregory_great'
        """,
        (PL77_DJVU_TEXT_URL,),
    )
    conn.commit()
    return applied


def summarize(
    conn: sqlite3.Connection,
    parsed: dict[int, ParsedLetter],
    updates: list[PlannedUpdate],
    *,
    dry_run: bool,
    applied: int = 0,
) -> dict[str, Any]:
    missing_before_or_after = len(missing_gregory_original_rows(conn))
    return {
        "collection": "gregory_great",
        "dry_run": dry_run,
        "source_url": PL77_DJVU_TEXT_URL,
        "scan_url": PL77_ARCHIVE_PAGE,
        "parsed_unique_letters": len(parsed),
        "planned_update_count": len(updates),
        "applied_update_count": applied,
        "missing_original_count_current": missing_before_or_after,
        "collection_source_needs_update": collection_source_needs_update(conn),
        "sample_updates": [
            {
                "id": update.id,
                "letter_number": update.letter_number,
                "latin_length": len(update.latin_text),
            }
            for update in updates[:12]
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, default=DB_PATH)
    parser.add_argument("--source-text", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--min-updates", type=int, default=150)
    parser.add_argument("--min-text-chars", type=int, default=DEFAULT_MIN_TEXT_CHARS)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)

    source_text = load_source_text(args.source_text)
    parsed = parse_pl77_letters(source_text, min_chars=args.min_text_chars)

    conn = sqlite3.connect(args.db_path)
    try:
        updates = build_update_plan(conn, parsed, limit=args.limit)
        if len(updates) < args.min_updates:
            summary = summarize(conn, parsed, updates, dry_run=True)
            summary["error"] = (
                f"Planned updates {len(updates)} below required minimum {args.min_updates}"
            )
            if args.as_json:
                print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(summary["error"], file=sys.stderr)
            return 2

        applied = 0
        if not args.dry_run:
            applied = apply_updates(conn, updates)

        summary = summarize(conn, parsed, updates, dry_run=args.dry_run, applied=applied)
        if args.as_json:
            print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            action = "Would update" if args.dry_run else "Updated"
            print(f"{action} {len(updates) if args.dry_run else applied} Gregory rows")
            print(f"Parsed unique PL77 letters: {len(parsed)}")
            print(f"Current missing Gregory originals: {summary['missing_original_count_current']}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

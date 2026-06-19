#!/usr/bin/env python3
"""Repair Cicero Ad Familiares English scaffolds from ToposText."""

from __future__ import annotations

import argparse
import html
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"
COLLECTION = "cicero_familiares"

TOPOSTEXT_URL = "https://topostext.org/work/136"
TRANSLATION_SOURCE = "topostext_shuckburgh_repair_v1"
USER_AGENT = "roman-letters-network/1.0 (cicero familiares scaffold repair)"
MIN_SECTIONS = 350
MIN_UPDATES = 300

SUSPICIOUS_PATTERNS = (
    "APPENDIX ",
    "LETTERS IN VOLUMES",
    "Number Number",
    "PROJECT GUTENBERG",
    "START OF THE PROJECT",
    "END OF THE PROJECT",
    "TABLE OF CONTENTS",
)


@dataclass(frozen=True)
class FamiliaresSection:
    book: int
    letter_number: int
    text: str

    @property
    def translation_url(self) -> str:
        return f"{TOPOSTEXT_URL}#Fam.{self.book}.{self.letter_number}"


@dataclass(frozen=True)
class FamiliaresRow:
    id: int
    book: int
    letter_number: int
    english_text: str
    translation_source: str | None
    translation_url: str | None


@dataclass(frozen=True)
class PlannedUpdate:
    row: FamiliaresRow
    section: FamiliaresSection


@dataclass(frozen=True)
class SkippedRow:
    row_id: int
    book: int
    letter_number: int
    reason: str


def fetch_topostext_html(url: str = TOPOSTEXT_URL) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=45) as response:
        return response.read().decode("utf-8", "replace")


def _plain_text(fragment: str) -> str:
    fragment = re.sub(r"<sup[^>]*>.*?</sup>", "", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"</(?:p|div|h[1-6])>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    text = html.unescape(fragment)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_topostext_sections(document: str) -> dict[tuple[int, int], FamiliaresSection]:
    starts = list(
        re.finditer(
            r'<div\s+class="pSelector"\s+id=Fam\.(\d+)\.(\d+)>\s*<p[^>]*>',
            document,
            flags=re.S | re.I,
        )
    )
    sections: dict[tuple[int, int], FamiliaresSection] = {}

    for index, match in enumerate(starts):
        book = int(match.group(1))
        letter_number = int(match.group(2))
        end = starts[index + 1].start() if index + 1 < len(starts) else len(document)
        fragment = document[match.end() : end]
        event_date = re.search(r"Event Date:", fragment, flags=re.I)
        if event_date:
            fragment = fragment[: event_date.start()]
        text = _plain_text(fragment)
        text = re.sub(r"^\s*(?:§\s*)?Fam\.\d+\.\d+\s+", "", text)
        if text:
            sections[(book, letter_number)] = FamiliaresSection(
                book=book,
                letter_number=letter_number,
                text=text,
            )

    return sections


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def load_familiares_rows(conn: sqlite3.Connection) -> list[FamiliaresRow]:
    rows = conn.execute(
        """
        SELECT id, book, letter_number, english_text, translation_source, translation_url
        FROM letters
        WHERE collection = ?
        ORDER BY book, letter_number, id
        """,
        (COLLECTION,),
    ).fetchall()
    return [
        FamiliaresRow(
            id=int(row["id"]),
            book=int(row["book"]),
            letter_number=int(row["letter_number"]),
            english_text=(row["english_text"] or ""),
            translation_source=row["translation_source"],
            translation_url=row["translation_url"],
        )
        for row in rows
    ]


def is_suspicious_section(text: str) -> str | None:
    stripped = text.strip()
    if not stripped:
        return "empty parsed text"
    if len(stripped) < 80:
        return "parsed text too short"
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern.lower() in stripped.lower():
            return f"suspicious parsed text: {pattern}"
    return None


def build_plan(
    rows: list[FamiliaresRow],
    sections: dict[tuple[int, int], FamiliaresSection],
) -> tuple[list[PlannedUpdate], list[SkippedRow]]:
    ids_by_key: dict[tuple[int, int], list[int]] = {}
    for row in rows:
        ids_by_key.setdefault((row.book, row.letter_number), []).append(row.id)

    planned: list[PlannedUpdate] = []
    skipped: list[SkippedRow] = []

    for row in rows:
        key = (row.book, row.letter_number)
        duplicate_ids = ids_by_key[key]
        if len(duplicate_ids) != 1:
            skipped.append(
                SkippedRow(
                    row_id=row.id,
                    book=row.book,
                    letter_number=row.letter_number,
                    reason=f"duplicate DB key with ids {duplicate_ids}",
                )
            )
            continue

        section = sections.get(key)
        if section is None:
            skipped.append(
                SkippedRow(
                    row_id=row.id,
                    book=row.book,
                    letter_number=row.letter_number,
                    reason="no matching ToposText section",
                )
            )
            continue

        suspicious = is_suspicious_section(section.text)
        if suspicious:
            skipped.append(
                SkippedRow(
                    row_id=row.id,
                    book=row.book,
                    letter_number=row.letter_number,
                    reason=suspicious,
                )
            )
            continue

        planned.append(PlannedUpdate(row=row, section=section))

    return planned, skipped


def _needs_update(update: PlannedUpdate) -> bool:
    row = update.row
    section = update.section
    return (
        row.english_text.strip() != section.text.strip()
        or row.translation_source != TRANSLATION_SOURCE
        or row.translation_url != section.translation_url
    )


def repair_database(
    db_path: str | Path = DEFAULT_DB,
    *,
    source_html: str | None = None,
    dry_run: bool = False,
    min_sections: int = MIN_SECTIONS,
    min_updates: int = MIN_UPDATES,
) -> dict[str, Any]:
    document = source_html if source_html is not None else fetch_topostext_html()
    sections = parse_topostext_sections(document)
    if len(sections) < min_sections:
        raise ValueError(
            f"Refusing repair: parsed {len(sections)} sections, expected at least {min_sections}"
        )

    conn = connect(db_path)
    try:
        rows = load_familiares_rows(conn)
        planned, skipped = build_plan(rows, sections)
        pending = [update for update in planned if _needs_update(update)]
        if pending and len(pending) < min_updates:
            raise ValueError(
                f"Refusing repair: only {len(pending)} pending updates, expected at least {min_updates}"
            )

        result: dict[str, Any] = {
            "dry_run": dry_run,
            "parsed_sections": len(sections),
            "familiares_rows": len(rows),
            "planned_rows": len(planned),
            "skipped_rows": len(skipped),
            "pending_updates": len(pending),
            "translation_source": TRANSLATION_SOURCE,
            "skipped_by_reason": {},
        }
        for skipped_row in skipped:
            result["skipped_by_reason"][skipped_row.reason] = (
                result["skipped_by_reason"].get(skipped_row.reason, 0) + 1
            )

        if dry_run or not pending:
            return result

        with conn:
            for update in pending:
                conn.execute(
                    """
                    UPDATE letters
                    SET english_text = ?,
                        translation_source = ?,
                        translation_url = ?
                    WHERE id = ?
                      AND collection = ?
                    """,
                    (
                        update.section.text.strip(),
                        TRANSLATION_SOURCE,
                        update.section.translation_url,
                        update.row.id,
                        COLLECTION,
                    ),
                )

        result["updated_rows"] = len(pending)
        return result
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--source-html")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--min-sections", type=int, default=MIN_SECTIONS)
    parser.add_argument("--min-updates", type=int, default=MIN_UPDATES)
    args = parser.parse_args()

    source_html = Path(args.source_html).read_text(encoding="utf-8") if args.source_html else None
    result = repair_database(
        args.db,
        source_html=source_html,
        dry_run=args.dry_run,
        min_sections=args.min_sections,
        min_updates=args.min_updates,
    )

    mode = "DRY RUN" if args.dry_run else "UPDATED"
    print(f"{mode}: Cicero Familiares ToposText/Shuckburgh scaffold repair")
    print(f"Parsed ToposText sections: {result['parsed_sections']}")
    print(f"Familiares DB rows: {result['familiares_rows']}")
    print(f"Planned high-confidence rows: {result['planned_rows']}")
    print(f"Skipped rows: {result['skipped_rows']}")
    print(f"Pending updates: {result['pending_updates']}")
    if not args.dry_run:
        print(f"Updated rows: {result.get('updated_rows', 0)}")
    print(f"Translation source: {result['translation_source']}")
    if result["skipped_by_reason"]:
        print("Skipped by reason:")
        for reason, count in sorted(result["skipped_by_reason"].items()):
            print(f"- {reason}: {count}")


if __name__ == "__main__":
    main()

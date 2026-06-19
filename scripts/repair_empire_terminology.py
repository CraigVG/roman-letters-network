#!/usr/bin/env python3
"""Repair legacy empire terminology in persisted corpus text."""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"

LEGACY_ROOT = "Byz" + "ant"
LEGACY_LABEL = LEGACY_ROOT + "ine"
LEGACY_PEOPLE = LEGACY_LABEL + "s"
LEGACY_CITY = LEGACY_ROOT + "ium"

CONTENT_TABLES = ("letters", "authors", "collections")
ORIGINAL_TEXT_COLUMNS = {"latin_text", "greek_text", "original_text"}


@dataclass(frozen=True)
class CellUpdate:
    table: str
    row_id: int
    column: str
    before: str
    after: str


def repair_text(value: str) -> str:
    """Return text with legacy empire terminology replaced by approved wording."""
    replacements = [
        (LEGACY_CITY, "Constantinople"),
        (LEGACY_CITY.lower(), "Constantinople"),
        (f"{LEGACY_LABEL} Empire", "Roman Empire in the East"),
        (f"{LEGACY_LABEL} empire", "Roman Empire in the East"),
        (f"{LEGACY_LABEL} province", "Roman province"),
        (f"{LEGACY_LABEL} provinces", "Roman provinces"),
        (f"{LEGACY_LABEL} territory", "Eastern Roman territory"),
        (f"{LEGACY_LABEL} territories", "Eastern Roman territories"),
        (f"{LEGACY_LABEL}-held", "Eastern Roman-held"),
        (LEGACY_PEOPLE, "Eastern Romans"),
        (LEGACY_LABEL, "Eastern Roman"),
    ]

    repaired = value
    for old, new in replacements:
        repaired = repaired.replace(old, new)
    return repaired


def is_repairable_column(column: str) -> bool:
    """Avoid changing preserved original-language source text."""
    return column not in ORIGINAL_TEXT_COLUMNS


def text_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    columns: list[str] = []
    for row in conn.execute(f"PRAGMA table_info({table})"):
        column_name = row[1]
        column_type = (row[2] or "").upper()
        if column_type in {"TEXT", "VARCHAR"} or column_type == "":
            columns.append(column_name)
    return columns


def collect_updates(conn: sqlite3.Connection) -> list[CellUpdate]:
    conn.row_factory = sqlite3.Row
    updates: list[CellUpdate] = []
    needle = f"%{LEGACY_ROOT}%"

    for table in CONTENT_TABLES:
        for column in text_columns(conn, table):
            if not is_repairable_column(column):
                continue
            rows = conn.execute(
                f"SELECT id, {column} AS value FROM {table} WHERE lower({column}) LIKE ?",
                (needle,),
            ).fetchall()
            for row in rows:
                before = row["value"]
                if not isinstance(before, str):
                    continue
                after = repair_text(before)
                if before != after:
                    updates.append(
                        CellUpdate(
                            table=table,
                            row_id=int(row["id"]),
                            column=column,
                            before=before,
                            after=after,
                        )
                    )

    return updates


def apply_updates(conn: sqlite3.Connection, updates: list[CellUpdate]) -> None:
    for update in updates:
        conn.execute(
            f"UPDATE {update.table} SET {update.column} = ? WHERE id = ?",
            (update.after, update.row_id),
        )
    conn.commit()


def remaining_hits(conn: sqlite3.Connection) -> dict[str, dict[str, int]]:
    hits: dict[str, dict[str, int]] = {}
    needle = f"%{LEGACY_ROOT}%"
    for table in CONTENT_TABLES:
        table_hits: dict[str, int] = {}
        for column in text_columns(conn, table):
            if not is_repairable_column(column):
                continue
            count = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE lower({column}) LIKE ?",
                (needle,),
            ).fetchone()[0]
            if count:
                table_hits[column] = int(count)
        if table_hits:
            hits[table] = table_hits
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Repair legacy empire terminology in Roman Letters corpus text."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    updates = collect_updates(conn)

    print(f"Database: {args.db}")
    print(f"Cells to update: {len(updates)}")
    for update in updates:
        preview_before = update.before.replace("\n", " ")[:90]
        preview_after = update.after.replace("\n", " ")[:90]
        print(
            f"- {update.table}.{update.column} id={update.row_id}: "
            f"{preview_before!r} -> {preview_after!r}"
        )

    if args.dry_run:
        print("Dry run only; no changes written.")
        return 0

    if updates:
        apply_updates(conn, updates)

    hits = remaining_hits(conn)
    if hits:
        print(f"Remaining repairable legacy-term hits: {hits}")
        return 1

    print("Remaining repairable legacy-term hits: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

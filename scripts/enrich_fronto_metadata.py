#!/usr/bin/env python3
"""Source-backed metadata enrichment for Fronto's correspondence."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"

ROME = (41.8967, 12.4822)
ROME_LABEL = "Rome (career hub)"
CONFIDENCE = "career_hub"

SOURCE_NOTE = (
    "Sources: Attalus Fronto letter index; Britannica biographies for "
    "Marcus Cornelius Fronto, Marcus Aurelius, Antoninus Pius, and Lucius Verus."
)

AUTHOR_BIOS: dict[str, str] = {
    "Marcus Cornelius Fronto": (
        "Marcus Cornelius Fronto (c. AD 95-c. 166) was a Roman orator, "
        "rhetorician, advocate, and suffect consul from Cirta in Numidia. "
        "Educated and active in Rome, he became the Latin rhetoric tutor of "
        "Marcus Aurelius and Lucius Verus under Antoninus Pius. His surviving "
        "correspondence with the Antonine court preserves a rare personal view "
        "of imperial education, literary taste, illness, friendship, and Roman "
        "elite family life in the second century."
    ),
    "Marcus Aurelius": (
        "Marcus Aurelius (AD 121-180) was Roman emperor from 161 to 180 and "
        "a Stoic philosopher. His letters with Fronto belong chiefly to his "
        "long apprenticeship before and around his accession, showing the "
        "future emperor as a student, friend, family man, and ruler formed in "
        "the literary culture of the Antonine court."
    ),
    "Antoninus Pius": (
        "Antoninus Pius (AD 86-161) was Roman emperor from 138 to 161. He "
        "adopted Marcus Aurelius and Lucius Verus as his heirs and placed "
        "Fronto in their circle as a teacher of Latin rhetoric. His presence "
        "in the Fronto correspondence anchors the collection in the courtly "
        "world of the Antonine succession."
    ),
    "Lucius Verus": (
        "Lucius Verus (AD 130-169) was Roman emperor jointly with Marcus "
        "Aurelius from 161 to 169. Adopted into the Antonine succession, he "
        "was one of Fronto's pupils and correspondents; his letters preserve "
        "part of the same teacher-student and imperial-family network as "
        "Marcus Aurelius's exchanges with Fronto."
    ),
}


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _author_ids(conn: sqlite3.Connection) -> dict[str, int]:
    placeholders = ",".join("?" for _ in AUTHOR_BIOS)
    rows = conn.execute(
        f"SELECT id, name FROM authors WHERE name IN ({placeholders})",
        tuple(AUTHOR_BIOS),
    ).fetchall()
    found = {str(row["name"]): int(row["id"]) for row in rows}
    missing = sorted(set(AUTHOR_BIOS) - set(found))
    if missing:
        raise ValueError(f"Missing Fronto correspondent author rows: {', '.join(missing)}")
    return found


def _protected_geodata_count(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM letters
        WHERE collection = 'fronto'
          AND (
            (
              (origin_lat IS NOT NULL OR origin_lon IS NOT NULL)
              AND COALESCE(origin_confidence, 'unknown') NOT IN ('unknown', 'career_hub')
            )
            OR (
              (dest_lat IS NOT NULL OR dest_lon IS NOT NULL)
              AND COALESCE(dest_confidence, 'unknown') NOT IN ('unknown', 'career_hub')
            )
          )
        """
    ).fetchone()
    return int(row["count"])


def enrich_database(db_path: str | Path = DEFAULT_DB, dry_run: bool = False) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        author_ids = _author_ids(conn)
        protected = _protected_geodata_count(conn)
        if protected:
            raise ValueError(
                "Refusing to overwrite existing non-career-hub Fronto geodata "
                f"on {protected} letter(s)."
            )

        ids = tuple(author_ids.values())
        placeholders = ",".join("?" for _ in ids)
        fronto_letters = int(
            conn.execute("SELECT COUNT(*) FROM letters WHERE collection = 'fronto'").fetchone()[0]
        )
        origin_updates = int(
            conn.execute(
                f"""
                SELECT COUNT(*)
                FROM letters
                WHERE collection = 'fronto'
                  AND sender_id IN ({placeholders})
                """,
                ids,
            ).fetchone()[0]
        )
        dest_updates = int(
            conn.execute(
                f"""
                SELECT COUNT(*)
                FROM letters
                WHERE collection = 'fronto'
                  AND recipient_id IN ({placeholders})
                """,
                ids,
            ).fetchone()[0]
        )
        missing_recipient = int(
            conn.execute(
                "SELECT COUNT(*) FROM letters WHERE collection = 'fronto' AND recipient_id IS NULL"
            ).fetchone()[0]
        )
        result = {
            "authors_updated": len(author_ids),
            "fronto_letters": fronto_letters,
            "origin_updates": origin_updates,
            "destination_updates": dest_updates,
            "distance_updates": dest_updates,
            "missing_recipient_left_ungeocoded": missing_recipient,
            "dry_run": dry_run,
        }
        if dry_run:
            return result

        for name, bio in AUTHOR_BIOS.items():
            conn.execute(
                """
                UPDATE authors
                SET
                  location = ?,
                  lat = ?,
                  lon = ?,
                  bio = ?,
                  notes = ?,
                  location_confidence = ?
                WHERE id = ?
                """,
                (
                    "Rome",
                    ROME[0],
                    ROME[1],
                    bio,
                    SOURCE_NOTE,
                    CONFIDENCE,
                    author_ids[name],
                ),
            )

        conn.execute(
            f"""
            UPDATE letters
            SET
              origin_place = ?,
              origin_lat = ?,
              origin_lon = ?,
              origin_confidence = ?
            WHERE collection = 'fronto'
              AND sender_id IN ({placeholders})
            """,
            (ROME_LABEL, ROME[0], ROME[1], CONFIDENCE, *ids),
        )
        conn.execute(
            f"""
            UPDATE letters
            SET
              dest_place = ?,
              dest_lat = ?,
              dest_lon = ?,
              distance_km = ?,
              dest_confidence = ?
            WHERE collection = 'fronto'
              AND recipient_id IN ({placeholders})
            """,
            (ROME_LABEL, ROME[0], ROME[1], 0.0, CONFIDENCE, *ids),
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

    result = enrich_database(args.db, dry_run=args.dry_run)
    mode = "DRY RUN" if args.dry_run else "UPDATED"
    print(f"{mode}: Fronto metadata enrichment")
    print(f"Authors updated: {result['authors_updated']}")
    print(f"Fronto letters: {result['fronto_letters']}")
    print(f"Origin geocodes updated: {result['origin_updates']}")
    print(f"Destination geocodes updated: {result['destination_updates']}")
    print(f"Distance rows updated: {result['distance_updates']}")
    print(f"Recipient gaps left ungeocoded: {result['missing_recipient_left_ungeocoded']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

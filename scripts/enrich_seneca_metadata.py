#!/usr/bin/env python3
"""Source-backed metadata enrichment for Seneca's letters to Lucilius."""

from __future__ import annotations

import argparse
import math
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"

SENECA_NAME = "Lucius Annaeus Seneca"
LUCILIUS_NAME = "Lucilius Junior"

# Author/location coordinates. Letter endpoints below are deliberately regional:
# the collection-level evidence supports southern Italy and Sicily, not exact
# per-letter send and receive addresses.
ROME = (41.8967, 12.4822)
SOUTHERN_ITALY = (40.8518, 14.2681)
SICILY = (37.59999, 14.01536)

SOURCE_NOTE = (
    "Sources: Stanford Encyclopedia of Philosophy, Seneca; "
    "Wikisource/Gummere introduction to Moral Letters to Lucilius; "
    "Cambridge University Press sample from Inwood, Reading Seneca."
)

SENECA_BIO = (
    "Lucius Annaeus Seneca (c. 4 BC-AD 65) was a Roman Stoic philosopher, "
    "statesman, dramatist, and adviser to Nero. The Moral Letters to Lucilius "
    "belong to his final years in retirement and use the form of letters to "
    "teach practical Stoic ethics."
)

LUCILIUS_BIO = (
    "Lucilius Junior was a Roman equestrian, writer, philosopher, and Seneca's "
    "friend and correspondent. He was procurator in Sicily when the Moral "
    "Letters were written; what is known about him comes chiefly through "
    "Seneca's writings."
)


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _author_id(conn: sqlite3.Connection, name: str) -> int:
    row = conn.execute("SELECT id FROM authors WHERE name = ?", (name,)).fetchone()
    if not row:
        raise ValueError(f"Author not found: {name}")
    return int(row["id"])


def enrich_database(db_path: str | Path = DEFAULT_DB, dry_run: bool = False) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        seneca_id = _author_id(conn, SENECA_NAME)
        lucilius_id = _author_id(conn, LUCILIUS_NAME)
        letter_rows = conn.execute(
            """
            SELECT id
            FROM letters
            WHERE collection = 'seneca'
              AND sender_id = ?
              AND recipient_id = ?
            ORDER BY letter_number
            """,
            (seneca_id, lucilius_id),
        ).fetchall()

        distance = round(
            haversine_km(
                SOUTHERN_ITALY[0],
                SOUTHERN_ITALY[1],
                SICILY[0],
                SICILY[1],
            ),
            1,
        )

        result = {
            "authors_updated": 2,
            "seneca_author_id": seneca_id,
            "lucilius_author_id": lucilius_id,
            "seneca_letters": len(letter_rows),
            "letters_updated": len(letter_rows),
            "distance_km": distance,
            "dry_run": dry_run,
        }

        if dry_run:
            return result

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
                SENECA_BIO,
                SOURCE_NOTE,
                "career_hub",
                seneca_id,
            ),
        )
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
                "Sicily",
                SICILY[0],
                SICILY[1],
                LUCILIUS_BIO,
                SOURCE_NOTE,
                "regional",
                lucilius_id,
            ),
        )
        conn.execute(
            """
            UPDATE letters
            SET
              origin_place = ?,
              origin_lat = ?,
              origin_lon = ?,
              dest_place = ?,
              dest_lat = ?,
              dest_lon = ?,
              distance_km = ?,
              origin_confidence = ?,
              dest_confidence = ?
            WHERE collection = 'seneca'
              AND sender_id = ?
              AND recipient_id = ?
            """,
            (
                "Southern Italy (regional)",
                SOUTHERN_ITALY[0],
                SOUTHERN_ITALY[1],
                "Sicily (regional)",
                SICILY[0],
                SICILY[1],
                distance,
                "regional",
                "regional",
                seneca_id,
                lucilius_id,
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

    result = enrich_database(args.db, dry_run=args.dry_run)
    mode = "DRY RUN" if args.dry_run else "UPDATED"
    print(f"{mode}: Seneca metadata enrichment")
    print(f"Authors updated: {result['authors_updated']}")
    print(f"Seneca letters matched: {result['seneca_letters']}")
    print(f"Letters updated: {result['letters_updated']}")
    print(f"Regional distance km: {result['distance_km']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

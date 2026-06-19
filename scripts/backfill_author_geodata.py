#!/usr/bin/env python3
"""Backfill missing letter geodata from curated author coordinates."""

from __future__ import annotations

import argparse
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"


@dataclass(frozen=True)
class EndpointUpdate:
    letter_id: int
    collection: str
    letter_number: int | None
    endpoint: str
    place: str
    lat: float
    lon: float
    confidence: str


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(delta_lon / 2) ** 2
    )
    return round(radius_km * 2 * math.asin(math.sqrt(a)), 2)


def author_place(author: sqlite3.Row, role: str) -> str:
    location = (author["location"] or "").strip()
    if location:
        return location
    return f"{author['name']} ({role})"


def author_confidence(author: sqlite3.Row) -> str:
    confidence = (author["location_confidence"] or "unknown").strip() or "unknown"
    return f"author_location:{confidence}"


def _collection_filter_sql(collections: list[str]) -> tuple[str, list[str]]:
    if not collections:
        return "", []
    placeholders = ",".join("?" for _ in collections)
    return f" AND l.collection IN ({placeholders})", collections


def collect_endpoint_updates(
    conn: sqlite3.Connection, collections: list[str] | None = None
) -> list[EndpointUpdate]:
    collections = collections or []
    collection_sql, params = _collection_filter_sql(collections)

    origin_rows = conn.execute(
        f"""
        SELECT l.id, l.collection, l.letter_number,
               a.name, a.location, a.lat, a.lon, a.location_confidence
        FROM letters l
        JOIN authors a ON a.id = l.sender_id
        WHERE l.origin_lat IS NULL
          AND l.origin_lon IS NULL
          AND a.lat IS NOT NULL
          AND a.lon IS NOT NULL
          {collection_sql}
        """,
        params,
    ).fetchall()
    dest_rows = conn.execute(
        f"""
        SELECT l.id, l.collection, l.letter_number,
               a.name, a.location, a.lat, a.lon, a.location_confidence
        FROM letters l
        JOIN authors a ON a.id = l.recipient_id
        WHERE l.dest_lat IS NULL
          AND l.dest_lon IS NULL
          AND a.lat IS NOT NULL
          AND a.lon IS NOT NULL
          {collection_sql}
        """,
        params,
    ).fetchall()

    updates: list[EndpointUpdate] = []
    for row in origin_rows:
        updates.append(
            EndpointUpdate(
                letter_id=int(row["id"]),
                collection=str(row["collection"]),
                letter_number=row["letter_number"],
                endpoint="origin",
                place=author_place(row, "sender"),
                lat=float(row["lat"]),
                lon=float(row["lon"]),
                confidence=author_confidence(row),
            )
        )
    for row in dest_rows:
        updates.append(
            EndpointUpdate(
                letter_id=int(row["id"]),
                collection=str(row["collection"]),
                letter_number=row["letter_number"],
                endpoint="destination",
                place=author_place(row, "recipient"),
                lat=float(row["lat"]),
                lon=float(row["lon"]),
                confidence=author_confidence(row),
            )
        )
    return updates


def partial_coordinate_rows(
    conn: sqlite3.Connection, collections: list[str] | None = None
) -> list[sqlite3.Row]:
    collections = collections or []
    collection_sql, params = _collection_filter_sql(collections)
    return conn.execute(
        f"""
        SELECT id, collection, letter_number,
               origin_lat, origin_lon, dest_lat, dest_lon
        FROM letters l
        WHERE (
            (origin_lat IS NULL AND origin_lon IS NOT NULL)
            OR (origin_lat IS NOT NULL AND origin_lon IS NULL)
            OR (dest_lat IS NULL AND dest_lon IS NOT NULL)
            OR (dest_lat IS NOT NULL AND dest_lon IS NULL)
        )
        {collection_sql}
        """,
        params,
    ).fetchall()


def apply_endpoint_updates(
    conn: sqlite3.Connection, updates: list[EndpointUpdate]
) -> set[int]:
    changed_letter_ids: set[int] = set()
    for update in updates:
        if update.endpoint == "origin":
            cursor = conn.execute(
                """
                UPDATE letters
                SET origin_place = COALESCE(NULLIF(origin_place, ''), ?),
                    origin_lat = ?,
                    origin_lon = ?,
                    origin_confidence = ?
                WHERE id = ?
                  AND origin_lat IS NULL
                  AND origin_lon IS NULL
                """,
                (
                    update.place,
                    update.lat,
                    update.lon,
                    update.confidence,
                    update.letter_id,
                ),
            )
        else:
            cursor = conn.execute(
                """
                UPDATE letters
                SET dest_place = COALESCE(NULLIF(dest_place, ''), ?),
                    dest_lat = ?,
                    dest_lon = ?,
                    dest_confidence = ?
                WHERE id = ?
                  AND dest_lat IS NULL
                  AND dest_lon IS NULL
                """,
                (
                    update.place,
                    update.lat,
                    update.lon,
                    update.confidence,
                    update.letter_id,
                ),
            )
        if cursor.rowcount:
            changed_letter_ids.add(update.letter_id)
    return changed_letter_ids


def update_distances(conn: sqlite3.Connection, letter_ids: set[int]) -> int:
    if not letter_ids:
        return 0
    updated = 0
    for letter_id in sorted(letter_ids):
        row = conn.execute(
            """
            SELECT origin_lat, origin_lon, dest_lat, dest_lon, distance_km
            FROM letters
            WHERE id = ?
            """,
            (letter_id,),
        ).fetchone()
        if not row or row["distance_km"] is not None:
            continue
        if (
            row["origin_lat"] is None
            or row["origin_lon"] is None
            or row["dest_lat"] is None
            or row["dest_lon"] is None
        ):
            continue
        distance = haversine_km(
            float(row["origin_lat"]),
            float(row["origin_lon"]),
            float(row["dest_lat"]),
            float(row["dest_lon"]),
        )
        conn.execute("UPDATE letters SET distance_km = ? WHERE id = ?", (distance, letter_id))
        updated += 1
    return updated


def summarize_updates(updates: list[EndpointUpdate]) -> dict[str, Any]:
    by_collection: dict[str, dict[str, int]] = {}
    for update in updates:
        bucket = by_collection.setdefault(update.collection, {"origin": 0, "destination": 0})
        bucket[update.endpoint] += 1
    return {
        "origin_updates": sum(1 for update in updates if update.endpoint == "origin"),
        "destination_updates": sum(
            1 for update in updates if update.endpoint == "destination"
        ),
        "by_collection": dict(sorted(by_collection.items())),
    }


def backfill(
    db_path: str | Path = DEFAULT_DB,
    dry_run: bool = False,
    collections: list[str] | None = None,
) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        partials = partial_coordinate_rows(conn, collections)
        if partials:
            examples = ", ".join(
                f"{row['collection']}/{row['letter_number']}#{row['id']}"
                for row in partials[:5]
            )
            raise ValueError(
                "Refusing to run with partial coordinate pairs present: " + examples
            )

        updates = collect_endpoint_updates(conn, collections)
        summary = summarize_updates(updates)
        summary["dry_run"] = dry_run
        summary["distance_updates"] = 0

        if dry_run:
            return summary

        changed_letter_ids = apply_endpoint_updates(conn, updates)
        summary["distance_updates"] = update_distances(conn, changed_letter_ids)
        conn.commit()
        return summary
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=DEFAULT_DB, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--collection",
        action="append",
        default=[],
        help="Limit updates to a collection; may be repeated.",
    )
    args = parser.parse_args()

    result = backfill(args.db, dry_run=args.dry_run, collections=args.collection)
    mode = "DRY RUN" if args.dry_run else "UPDATED"
    print(f"{mode}: author-location geodata backfill")
    print(f"Origin geocodes: {result['origin_updates']}")
    print(f"Destination geocodes: {result['destination_updates']}")
    print(f"Distances computed: {result['distance_updates']}")
    print("Collections:")
    for collection, counts in result["by_collection"].items():
        print(
            f"  {collection}: origin={counts['origin']} "
            f"destination={counts['destination']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

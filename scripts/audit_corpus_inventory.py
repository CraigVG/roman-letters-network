#!/usr/bin/env python3
"""Audit corpus inventory targets against the Roman Letters database."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"
DEFAULT_INVENTORY = ROOT / "data" / "corpus_inventory.yaml"


def load_inventory(path: str | Path = DEFAULT_INVENTORY) -> dict[str, Any]:
    inventory_path = Path(path)
    with inventory_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Inventory must be a mapping: {inventory_path}")
    if not isinstance(data.get("targets"), list):
        raise ValueError(f"Inventory must contain a targets list: {inventory_path}")

    slugs: set[str] = set()
    for index, target in enumerate(data["targets"], start=1):
        if not isinstance(target, dict):
            raise ValueError(f"Target #{index} must be a mapping")
        slug = target.get("slug")
        if not slug:
            raise ValueError(f"Target #{index} is missing slug")
        if slug in slugs:
            raise ValueError(f"Duplicate target slug: {slug}")
        slugs.add(slug)

    return data


def _bool_sum(expr: str) -> str:
    return f"SUM(CASE WHEN {expr} THEN 1 ELSE 0 END)"


def load_db_snapshot(path: str | Path = DEFAULT_DB) -> dict[str, Any]:
    db_path = Path(path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        letter_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(letters)").fetchall()
        }
        has_existing_modern_source = {"translation_source", "english_text"}.issubset(letter_columns)
        modern_english_expr = "modern_english IS NOT NULL AND TRIM(modern_english) != ''"
        if has_existing_modern_source:
            modern_english_expr = (
                f"{modern_english_expr} OR ("
                "translation_source = 'existing_kalvesmaki_evagrius_2014' "
                "AND english_text IS NOT NULL "
                "AND TRIM(english_text) != '')"
            )
        collection_rows = conn.execute(
            f"""
            SELECT
                collection,
                COUNT(*) AS letters,
                SUM(CASE WHEN {modern_english_expr} THEN 1 ELSE 0 END) AS modern_english,
                SUM(CASE WHEN latin_text IS NOT NULL AND TRIM(latin_text) != '' THEN 1 ELSE 0 END) AS original_text,
                SUM(CASE WHEN source_url IS NOT NULL AND TRIM(source_url) != '' THEN 1 ELSE 0 END) AS source_url,
                SUM(CASE WHEN sender_id IS NOT NULL THEN 1 ELSE 0 END) AS sender_linked,
                SUM(CASE WHEN recipient_id IS NOT NULL THEN 1 ELSE 0 END) AS recipient_linked,
                SUM(CASE WHEN origin_lat IS NOT NULL AND origin_lon IS NOT NULL THEN 1 ELSE 0 END) AS origin_geocode,
                SUM(CASE WHEN dest_lat IS NOT NULL AND dest_lon IS NOT NULL THEN 1 ELSE 0 END) AS destination_geocode
            FROM letters
            GROUP BY collection
            ORDER BY collection
            """
        ).fetchall()

        bio_rows = conn.execute(
            """
            WITH collection_people AS (
                SELECT collection, sender_id AS author_id
                FROM letters
                WHERE sender_id IS NOT NULL
                UNION
                SELECT collection, recipient_id AS author_id
                FROM letters
                WHERE recipient_id IS NOT NULL
            )
            SELECT
                cp.collection,
                COUNT(DISTINCT cp.author_id) AS people,
                SUM(CASE WHEN a.bio IS NULL OR TRIM(a.bio) = '' THEN 1 ELSE 0 END) AS people_missing_bios
            FROM collection_people cp
            LEFT JOIN authors a ON a.id = cp.author_id
            GROUP BY cp.collection
            """
        ).fetchall()

        collection_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(collections)").fetchall()
        }
        scrape_status_expr = (
            "scrape_status"
            if "scrape_status" in collection_columns
            else "NULL AS scrape_status"
        )
        declared_rows = conn.execute(
            f"""
            SELECT slug, author_name, title, letter_count, {scrape_status_expr}
            FROM collections
            ORDER BY slug
            """
        ).fetchall()

        if "year_approx" in letter_columns:
            min_year_expr = "MIN(year_approx)"
            max_year_expr = "MAX(year_approx)"
            post_800_expr = _bool_sum("year_approx BETWEEN 801 AND 1453")
        else:
            min_year_expr = "NULL"
            max_year_expr = "NULL"
            post_800_expr = "0"

        range_row = conn.execute(
            f"""
            SELECT
                COUNT(*) AS letters,
                COUNT(DISTINCT collection) AS collections,
                {min_year_expr} AS min_year,
                {max_year_expr} AS max_year,
                {post_800_expr} AS post_800_letters
            FROM letters
            """
        ).fetchone()
    finally:
        conn.close()

    bios_by_collection = {row["collection"]: dict(row) for row in bio_rows}
    collections: dict[str, dict[str, Any]] = {}
    for row in collection_rows:
        item = dict(row)
        bio = bios_by_collection.get(row["collection"], {})
        item["people"] = bio.get("people", 0) or 0
        item["people_missing_bios"] = bio.get("people_missing_bios", 0) or 0
        collections[row["collection"]] = item

    declared = {row["slug"]: dict(row) for row in declared_rows}

    return {
        "db_path": str(db_path),
        "summary": dict(range_row) if range_row else {},
        "collections": collections,
        "declared_collections": declared,
    }


def _required(target: dict[str, Any], field: str) -> bool:
    requirements = target.get("requirements") or {}
    return requirements.get(field, "required") == "required"


def _missing_count(stats: dict[str, Any], present_key: str) -> int:
    letters = int(stats.get("letters") or 0)
    present = int(stats.get(present_key) or 0)
    return max(letters - present, 0)


def audit_inventory(inventory: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    db_collections = snapshot["collections"]
    targets: dict[str, dict[str, Any]] = {}
    missing_targets: list[str] = []
    present_in_db = 0
    expected_shortfall = 0
    metadata_gap_total = 0

    for target in inventory["targets"]:
        slug = target["slug"]
        stats = db_collections.get(slug)
        expected = target.get("expected_letters")
        target_report: dict[str, Any] = {
            "status": target.get("status", "unknown"),
            "priority": target.get("priority"),
            "expected_letters": expected,
            "db_letters": 0,
            "letter_shortfall": expected if isinstance(expected, int) else None,
            "missing_modern_english": None,
            "missing_original_text": None,
            "missing_source_url": None,
            "missing_sender": None,
            "missing_recipient": None,
            "missing_origin_geocode": None,
            "missing_destination_geocode": None,
            "people_missing_bios": None,
        }

        if stats is None:
            missing_targets.append(slug)
            targets[slug] = target_report
            if isinstance(expected, int):
                expected_shortfall += expected
            continue

        present_in_db += 1
        db_letters = int(stats["letters"] or 0)
        shortfall = max((expected or db_letters) - db_letters, 0) if isinstance(expected, int) else 0
        target_report["db_letters"] = db_letters
        target_report["letter_shortfall"] = shortfall
        expected_shortfall += shortfall

        if _required(target, "modern_english"):
            target_report["missing_modern_english"] = _missing_count(stats, "modern_english")
        if _required(target, "original_text"):
            target_report["missing_original_text"] = _missing_count(stats, "original_text")
        if _required(target, "source_url"):
            target_report["missing_source_url"] = _missing_count(stats, "source_url")
        if _required(target, "sender_recipient"):
            target_report["missing_sender"] = _missing_count(stats, "sender_linked")
            target_report["missing_recipient"] = _missing_count(stats, "recipient_linked")
        if _required(target, "geolocation"):
            target_report["missing_origin_geocode"] = _missing_count(stats, "origin_geocode")
            target_report["missing_destination_geocode"] = _missing_count(stats, "destination_geocode")
        if _required(target, "bios"):
            target_report["people_missing_bios"] = int(stats.get("people_missing_bios") or 0)

        metadata_gap_total += sum(
            int(value)
            for key, value in target_report.items()
            if key.startswith("missing_") and isinstance(value, int)
        )
        if isinstance(target_report["people_missing_bios"], int):
            metadata_gap_total += target_report["people_missing_bios"]

        targets[slug] = target_report

    inventory_slugs = {target["slug"] for target in inventory["targets"]}
    untracked_db_collections = sorted(set(db_collections) - inventory_slugs)

    return {
        "summary": {
            "targets": len(inventory["targets"]),
            "present_in_db": present_in_db,
            "missing_from_db": len(missing_targets),
            "untracked_db_collections": len(untracked_db_collections),
            "expected_letter_shortfall": expected_shortfall,
            "metadata_gap_total": metadata_gap_total,
            "db_letters": snapshot["summary"].get("letters", 0),
            "db_collections": snapshot["summary"].get("collections", 0),
            "db_min_year": snapshot["summary"].get("min_year"),
            "db_max_year": snapshot["summary"].get("max_year"),
            "db_post_800_letters": snapshot["summary"].get("post_800_letters", 0),
        },
        "targets": targets,
        "missing_targets": missing_targets,
        "untracked_db_collections": untracked_db_collections,
    }


def render_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "Roman Letters Corpus Inventory Audit",
        "=" * 38,
        f"Inventory targets: {summary['targets']}",
        f"Present in DB: {summary['present_in_db']}",
        f"Missing from DB: {summary['missing_from_db']}",
        f"Untracked DB collections: {summary['untracked_db_collections']}",
        f"Expected letter shortfall: {summary['expected_letter_shortfall']}",
        f"Metadata gap total: {summary['metadata_gap_total']}",
        f"DB coverage window: {summary['db_min_year']} to {summary['db_max_year']}",
        f"DB post-800 letters: {summary['db_post_800_letters']}",
        "",
        "Highest-priority action targets:",
    ]

    ranked = sorted(
        report["targets"].items(),
        key=lambda item: (
            item[1].get("priority") if item[1].get("priority") is not None else 999,
            item[0],
        ),
    )
    for slug, target in ranked[:15]:
        gaps = []
        shortfall = target.get("letter_shortfall")
        if shortfall:
            gaps.append(f"{shortfall} letters")
        for key in (
            "missing_modern_english",
            "missing_original_text",
            "missing_destination_geocode",
            "people_missing_bios",
        ):
            value = target.get(key)
            if value:
                gaps.append(f"{value} {key.replace('_', ' ')}")
        gap_text = ", ".join(gaps) if gaps else "tracked"
        lines.append(f"- {slug}: {gap_text}")

    if report["missing_targets"]:
        lines.extend(["", "Missing inventory targets:"])
        lines.extend(f"- {slug}" for slug in report["missing_targets"][:25])

    if report["untracked_db_collections"]:
        lines.extend(["", "DB collections not yet represented as inventory targets:"])
        lines.extend(f"- {slug}" for slug in report["untracked_db_collections"][:25])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", default=DEFAULT_INVENTORY, type=Path)
    parser.add_argument("--db", default=DEFAULT_DB, type=Path)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero when tracked gaps or untracked DB collections remain",
    )
    args = parser.parse_args()

    inventory = load_inventory(args.inventory)
    snapshot = load_db_snapshot(args.db)
    report = audit_inventory(inventory, snapshot)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_report(report))

    if args.strict and (
        report["summary"]["missing_from_db"]
        or report["summary"]["untracked_db_collections"]
        or report["summary"]["expected_letter_shortfall"]
        or report["summary"]["metadata_gap_total"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

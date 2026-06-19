#!/usr/bin/env python3
"""Repair Libanius Foerster volume 11 around printed letters 890-900.

The T254 source-boundary review found that Foerster printed letter 890,
addressed to the envoys, was skipped in the previous batch. The rows currently
stored as 890-899 are printed 891-900. This script shifts those rows forward
and inserts the missing printed 890.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

import import_libanius_volume11_pilot as base


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"
DEFAULT_SOURCE_MAP = ROOT / "data" / "source_maps" / "libanius_foerster_volume11.json"

COLLECTION_SLUG = base.COLLECTION_SLUG
ARCHIVE_ITEM_URL = base.ARCHIVE_ITEM_URL
VOLUME11_DJVU_XML_URL = base.VOLUME11_DJVU_XML_URL
VOLUME11_PDF_URL = base.VOLUME11_PDF_URL
OGL_VOLUME10_RAW_URL = base.OGL_VOLUME10_RAW_URL
GEMINI_OCR_MODEL = base.GEMINI_OCR_MODEL
EXPECTED_VOLUME11_RANGE = base.EXPECTED_VOLUME11_RANGE
ANTIOCH = base.ANTIOCH

REPAIR_SOURCE = "modern_libanius_foerster_vol11_t254_repair_gemini_flash_v1"
SHIFT_RANGE = tuple(range(890, 900))

COLLECTION_NOTES = (
    "The single largest surviving letter collection from antiquity (~1,544 letters "
    "in Foerster ed.). Greek text: Foerster Opera vols.10-11 (1921-22, Leipzig: "
    "Teubner), available at archive.org. English translations: A.F. Norman Loeb "
    "vols.478-479 (1993, 193 selected letters); Bradbury TTH vol.41 (2004, 183 "
    "letters from 355-365); Bradbury & Moncur TTH vol.82 (2023, letters 388-393). "
    "Only 16 Julian letters (1784 translation) are freely available online at "
    "tertullian.org. This collection now includes OCR-checked Foerster volume 11 "
    "packets through printed letter 900, including the T254 repair that restored "
    "the skipped printed letter 890 and shifted the former 890-899 rows to 891-900."
)

MISSING_890 = {
    "number": 890,
    "recipient": "Envoys, correspondents of Libanius",
    "recipient_latin": "Envoys",
    "recipient_greek": "Τοῖς πρέσβεσιν",
    "year": 388,
    "leaf_start": 53,
    "leaf_end": 54,
    "heading": "ωϟ΄. Τοῖς πρέσβεσιν. (388)",
    "greek": (
        "1. Τοὺς περὶ Ῥωμύλου λόγους οἶμαί γε ἐν ὑμῖν κεῖσθαι καὶ "
        "τοὔργον ὑμᾶς ἐπιθυμεῖν προσθεῖναι, βλάβη δὲ οὐδεμία καὶ "
        "πρὸς μεμνημένους ἐλθεῖν τοιαύτην ἐπιστολήν. 2. δέχεσθε "
        "τοίνυν τὴν ἐπιστολὴν καὶ οἷς πράττετε τιμᾶτε καὶ Ῥωμύλον "
        "καὶ ὑμᾶς αὐτοὺς καὶ ἐμὲ καὶ τὴν πόλιν."
    ),
    "modern_english": (
        "I believe the arguments about Romulus are already in your hands, and that "
        "you are eager to add action to them. There is no harm in such a letter "
        "reaching people who remember the matter. So receive this letter, and by "
        "what you do honor Romulus, yourselves, me, and the city."
    ),
    "quick_summary": (
        "Libanius urges the envoys to act on Romulus' case and honor Romulus, "
        "themselves, Libanius, and Antioch."
    ),
    "subject_summary": "A brief appeal to envoys to act on Romulus' behalf.",
    "interesting_note": (
        "This printed letter 890 was missed in the earlier 870-899 packet because "
        "Foerster's heading begins at the foot of leaf n53 and continues on n54."
    ),
    "topics": "Romulus,envoys,patronage,petition,Antioch,civic honor",
}

SHIFTED_HEADINGS = {
    891: "ωϟα΄. Φωτίῳ. (388)",
    892: "ωϟβ΄. Γεσσίῳ. (388)",
    893: "ωϟγ΄. Εὐσεβίῳ. (388)",
    894: "ωϟδ΄. Ἡσυχίῳ. (388)",
    895: "ωϟε΄. Λεοντίῳ. (388)",
    896: "ωϟϛ΄. Ἀρισταινέτῳ. (388)",
    897: "ωϟζ΄. Σατορνίνῳ. (388)",
    898: "ωϟη΄. Ἐλεβίκῳ. (388)",
    899: "ωϟθ΄. Τατιανῷ. (388)",
    900: "ϡ΄. Ἡρακλείτῳ. (388)",
}


def scan_url(leaf: int) -> str:
    return base.scan_url(leaf)


def connect(db_path: str | Path) -> sqlite3.Connection:
    return base.connect(db_path)


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return base.table_columns(conn, table)


def author_data() -> list[dict[str, Any]]:
    return [
        {
            "name": "Libanius",
            "name_latin": "Libanius Antiochenus",
            "birth_year": 314,
            "death_year": 393,
            "role": "Greek rhetorician and letter writer",
            "location": ANTIOCH[0],
            "lat": ANTIOCH[1],
            "lon": ANTIOCH[2],
            "location_confidence": "author_base",
            "notes": "Major fourth-century Roman rhetorician based in Antioch.",
            "bio": (
                "Libanius of Antioch was a fourth-century Greek rhetorician whose "
                "large surviving correspondence preserves civic, educational, and "
                "administrative networks across the Roman Empire."
            ),
            "update_existing": True,
        },
        {
            "name": MISSING_890["recipient"],
            "name_latin": MISSING_890["recipient_latin"],
            "role": "envoys addressed by Libanius",
            "location": None,
            "lat": None,
            "lon": None,
            "location_confidence": "unknown",
            "notes": "Recipient scaffold from Libanius, Foerster Epistle 890.",
            "bio": (
                "These envoys are addressed collectively by Libanius in Foerster "
                "Epistle 890, dated 388, in a short appeal concerning Romulus."
            ),
            "update_existing": True,
        },
    ]


def ensure_collection(conn: sqlite3.Connection, dry_run: bool) -> bool:
    row = conn.execute("SELECT id FROM collections WHERE slug = ?", (COLLECTION_SLUG,)).fetchone()
    if row:
        return False
    if dry_run:
        return True
    conn.execute(
        """
        INSERT INTO collections (
            slug, author_name, title, letter_count, date_range, latin_source_url,
            english_source_url, scrape_status, notes, scan_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            COLLECTION_SLUG,
            "Libanius",
            "Letters of Libanius",
            0,
            "314-393 AD",
            ARCHIVE_ITEM_URL,
            "https://www.tertullian.org/fathers/libanius_02_16_letters_to_julian.htm",
            "partial",
            COLLECTION_NOTES,
            ARCHIVE_ITEM_URL,
        ),
    )
    return True


def collection_needs_update(
    conn: sqlite3.Connection,
    projected_insertions: int,
    collection_created: bool,
) -> bool:
    if collection_created:
        return True
    row = conn.execute(
        "SELECT letter_count, latin_source_url, scrape_status, notes, scan_url FROM collections WHERE slug = ?",
        (COLLECTION_SLUG,),
    ).fetchone()
    if not row:
        return True
    current_count = conn.execute(
        "SELECT COUNT(*) FROM letters WHERE collection = ?",
        (COLLECTION_SLUG,),
    ).fetchone()[0]
    projected_count = int(current_count) + projected_insertions
    return (
        int(row["letter_count"] or 0) != projected_count
        or (row["latin_source_url"] or "") != ARCHIVE_ITEM_URL
        or row["scrape_status"] != "partial"
        or (row["notes"] or "") != COLLECTION_NOTES
        or (row["scan_url"] or "") != ARCHIVE_ITEM_URL
    )


def update_collection(conn: sqlite3.Connection) -> None:
    current_count = conn.execute(
        "SELECT COUNT(*) FROM letters WHERE collection = ?",
        (COLLECTION_SLUG,),
    ).fetchone()[0]
    data = {
        "letter_count": int(current_count),
        "date_range": "314-393 AD",
        "latin_source_url": ARCHIVE_ITEM_URL,
        "scrape_status": "partial",
        "notes": COLLECTION_NOTES,
        "scan_url": ARCHIVE_ITEM_URL,
    }
    columns = table_columns(conn, "collections")
    data = {key: value for key, value in data.items() if key in columns}
    assignments = ", ".join(f"{key} = ?" for key in data)
    conn.execute(
        f"UPDATE collections SET {assignments} WHERE slug = ?",
        [data[key] for key in data] + [COLLECTION_SLUG],
    )


def get_or_create_author(
    conn: sqlite3.Connection,
    data: dict[str, Any],
    dry_run: bool,
) -> tuple[int | None, bool, bool]:
    return base.get_or_create_author(conn, data, dry_run)


def build_missing_890_letter() -> dict[str, Any]:
    return {
        "collection": COLLECTION_SLUG,
        "book": None,
        "letter_number": MISSING_890["number"],
        "ref_id": "libanius.ep.890",
        "sender": "Libanius",
        "recipient": MISSING_890["recipient"],
        "year_approx": MISSING_890["year"],
        "year_min": MISSING_890["year"],
        "year_max": MISSING_890["year"],
        "origin_place": ANTIOCH[0],
        "origin_lat": ANTIOCH[1],
        "origin_lon": ANTIOCH[2],
        "dest_place": None,
        "dest_lat": None,
        "dest_lon": None,
        "dest_confidence": "unknown",
        "subject_summary": MISSING_890["subject_summary"],
        "latin_text": MISSING_890["greek"],
        "english_text": None,
        "modern_english": MISSING_890["modern_english"],
        "translation_source": REPAIR_SOURCE,
        "source_url": VOLUME11_DJVU_XML_URL,
        "translation_url": None,
        "scan_url": scan_url(MISSING_890["leaf_start"]),
        "quick_summary": MISSING_890["quick_summary"],
        "interesting_note": MISSING_890["interesting_note"],
        "topics": MISSING_890["topics"],
        "distance_km": None,
        "origin_confidence": "author_base",
        "carrier_name": None,
        "carrier_role": None,
        "carrier_mentioned": 0,
    }


def validate_packet() -> None:
    letter = build_missing_890_letter()
    if len(letter["latin_text"]) < 120:
        raise ValueError("Missing 890 Greek source is too short")
    if len(letter["modern_english"]) < 120:
        raise ValueError("Missing 890 modern English is too short")
    if re.search(r"^(to|from|letter)\b", letter["modern_english"].strip(), flags=re.I):
        raise ValueError("Missing 890 translation contains a metadata header")
    lowered = letter["modern_english"].lower()
    for forbidden in ("thou", "thee", "wherefore", "hast", "machine translation"):
        if re.search(rf"\b{forbidden}\b", lowered):
            raise ValueError(f"Missing 890 translation contains archaic or boilerplate word {forbidden!r}")
    if "Byz" + "ant" in letter["modern_english"]:
        raise ValueError("Forbidden terminology present in missing 890 translation")


def repair_state(conn: sqlite3.Connection) -> str:
    row_890 = conn.execute(
        """
        SELECT l.ref_id, r.name AS recipient_name
        FROM letters l
        LEFT JOIN authors r ON r.id = l.recipient_id
        WHERE l.collection = ? AND l.letter_number = 890
        """,
        (COLLECTION_SLUG,),
    ).fetchone()
    row_900 = conn.execute(
        "SELECT ref_id FROM letters WHERE collection = ? AND letter_number = 900",
        (COLLECTION_SLUG,),
    ).fetchone()
    if row_890 and row_890["ref_id"] == "libanius.ep.890" and row_890["recipient_name"] == MISSING_890["recipient"]:
        if row_900 and row_900["ref_id"] == "libanius.ep.900":
            return "already_repaired"
        raise ValueError("Printed 890 is present but printed 900 is missing; repair is partially applied")
    if row_900:
        raise ValueError("Printed 900 already exists before the 890 repair")
    return "needs_repair"


def validate_shiftable_rows(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT letter_number, ref_id
        FROM letters
        WHERE collection = ? AND letter_number BETWEEN 890 AND 899
        ORDER BY letter_number
        """,
        (COLLECTION_SLUG,),
    ).fetchall()
    found = {int(row["letter_number"]): row["ref_id"] for row in rows}
    expected = {number: f"libanius.ep.{number}" for number in SHIFT_RANGE}
    if found != expected:
        raise ValueError(f"Cannot shift Libanius 890-899; expected {expected}, found {found}")


def shift_existing_rows(conn: sqlite3.Connection, dry_run: bool) -> int:
    validate_shiftable_rows(conn)
    if dry_run:
        return len(SHIFT_RANGE)
    for number in reversed(SHIFT_RANGE):
        conn.execute(
            """
            UPDATE letters
            SET letter_number = ?, ref_id = ?
            WHERE collection = ? AND ref_id = ?
            """,
            (number + 1, f"libanius.ep.{number + 1}", COLLECTION_SLUG, f"libanius.ep.{number}"),
        )
    return len(SHIFT_RANGE)


def check_existing_missing_890(row: sqlite3.Row, letter: dict[str, Any]) -> None:
    checks = {
        "latin_text": letter["latin_text"],
        "english_text": None,
        "modern_english": letter["modern_english"],
        "translation_source": REPAIR_SOURCE,
        "source_url": VOLUME11_DJVU_XML_URL,
        "translation_url": None,
        "scan_url": letter["scan_url"],
    }
    for key, expected in checks.items():
        existing = row[key] if key in row.keys() else None
        if (existing or None) != (expected or None):
            raise ValueError(f"{letter['ref_id']} already exists with different {key}")


def insert_missing_890(
    conn: sqlite3.Connection,
    author_ids: dict[str, int | None],
    dry_run: bool,
) -> tuple[int, int]:
    letter = build_missing_890_letter()
    existing = conn.execute(
        """
        SELECT ref_id, latin_text, english_text, modern_english, translation_source,
               source_url, translation_url, scan_url
        FROM letters
        WHERE ref_id = ?
        """,
        (letter["ref_id"],),
    ).fetchone()
    if existing:
        check_existing_missing_890(existing, letter)
        return 0, 1
    if dry_run:
        return 1, 0

    sender_id = author_ids[letter["sender"]]
    recipient_id = author_ids[letter["recipient"]]
    if sender_id is None or recipient_id is None:
        raise ValueError("Dry-run author placeholder leaked into apply")

    conn.execute(
        """
        INSERT INTO letters (
            collection, book, letter_number, ref_id, sender_id, recipient_id,
            year_approx, year_min, year_max,
            origin_place, origin_lat, origin_lon,
            dest_place, dest_lat, dest_lon,
            subject_summary, latin_text, english_text, modern_english,
            translation_source, source_url, translation_url, scan_url,
            quick_summary, interesting_note, topics, distance_km,
            origin_confidence, dest_confidence,
            carrier_name, carrier_role, carrier_mentioned
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            COLLECTION_SLUG,
            None,
            letter["letter_number"],
            letter["ref_id"],
            sender_id,
            recipient_id,
            letter["year_approx"],
            letter["year_min"],
            letter["year_max"],
            letter["origin_place"],
            letter["origin_lat"],
            letter["origin_lon"],
            letter["dest_place"],
            letter["dest_lat"],
            letter["dest_lon"],
            letter["subject_summary"],
            letter["latin_text"],
            None,
            letter["modern_english"],
            REPAIR_SOURCE,
            letter["source_url"],
            None,
            letter["scan_url"],
            letter["quick_summary"],
            letter["interesting_note"],
            letter["topics"],
            letter["distance_km"],
            letter["origin_confidence"],
            letter["dest_confidence"],
            None,
            None,
            0,
        ),
    )
    return 1, 0


def source_map_entry_for_890() -> dict[str, Any]:
    return {
        "number": 890,
        "ref_id": "libanius.ep.890",
        "recipient": MISSING_890["recipient"],
        "recipient_greek": MISSING_890["recipient_greek"],
        "year": MISSING_890["year"],
        "heading": MISSING_890["heading"],
        "leaf_start": MISSING_890["leaf_start"],
        "leaf_end": MISSING_890["leaf_end"],
        "scan_url": scan_url(MISSING_890["leaf_start"]),
        "greek_chars": len(MISSING_890["greek"]),
        "modern_english_chars": len(MISSING_890["modern_english"]),
        "translation_source": REPAIR_SOURCE,
    }


def write_source_map(path: str | Path) -> None:
    path = Path(path)
    if path.exists():
        source_map = json.loads(path.read_text(encoding="utf-8"))
    else:
        source_map = {
            "collection": COLLECTION_SLUG,
            "source_family": "Libanius Foerster Opera volume 11",
            "archive_item_url": ARCHIVE_ITEM_URL,
            "source_url": VOLUME11_DJVU_XML_URL,
            "pdf_url": VOLUME11_PDF_URL,
            "ogl_volume10_raw_url": OGL_VOLUME10_RAW_URL,
            "volume11_range": list(EXPECTED_VOLUME11_RANGE),
            "blocked_gap_before_volume11": list(range(832, 840)),
            "letters": [],
        }

    source_map.update(
        {
            "collection": COLLECTION_SLUG,
            "source_family": "Libanius Foerster Opera volume 11",
            "archive_item_url": ARCHIVE_ITEM_URL,
            "source_url": VOLUME11_DJVU_XML_URL,
            "pdf_url": VOLUME11_PDF_URL,
            "ogl_volume10_raw_url": OGL_VOLUME10_RAW_URL,
            "volume11_range": list(EXPECTED_VOLUME11_RANGE),
            "ocr_model": GEMINI_OCR_MODEL,
            "ocr_note": (
                "Archive DjVu XML proved broad boundaries but had noisy headings and "
                "apparatus bleed. T254 restored printed letter 890 from page-image "
                "review and shifted the former 890-899 rows to printed 891-900."
            ),
            "t254_repair_numbers": list(range(890, 901)),
            "t254_repair_note": (
                "Printed 890, addressed to the envoys, begins at the foot of leaf n53 "
                "and continues on n54; printed 901 begins with Entrechius on n61."
            ),
        }
    )

    entries = {int(item["number"]): dict(item) for item in source_map.get("letters", [])}
    if 900 not in entries or entries.get(890, {}).get("recipient") != MISSING_890["recipient"]:
        old_entries = dict(entries)
        for number in reversed(SHIFT_RANGE):
            if number not in old_entries:
                continue
            shifted = dict(old_entries[number])
            new_number = number + 1
            shifted["number"] = new_number
            shifted["ref_id"] = f"libanius.ep.{new_number}"
            shifted["heading"] = SHIFTED_HEADINGS[new_number]
            entries[new_number] = shifted
        entries[890] = source_map_entry_for_890()
    else:
        entries[890] = source_map_entry_for_890()
        for number, heading in SHIFTED_HEADINGS.items():
            if number in entries:
                entries[number]["number"] = number
                entries[number]["ref_id"] = f"libanius.ep.{number}"
                entries[number]["heading"] = heading

    source_map["letters"] = [entries[number] for number in sorted(entries)]
    source_map["completed_numbers"] = [item["number"] for item in source_map["letters"]]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(source_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def repair_batch(
    db_path: str | Path = DEFAULT_DB,
    dry_run: bool = False,
    source_map_path: str | Path = DEFAULT_SOURCE_MAP,
) -> dict[str, Any]:
    validate_packet()
    conn = connect(db_path)
    try:
        state = repair_state(conn)
        author_ids: dict[str, int | None] = {}
        authors_created = 0
        authors_updated = 0
        for author in author_data():
            author_id, created, updated = get_or_create_author(conn, author, dry_run=dry_run)
            author_ids[author["name"]] = author_id
            authors_created += int(created)
            authors_updated += int(updated)

        collection_created = ensure_collection(conn, dry_run=dry_run)
        rows_shifted = 0
        if state == "needs_repair":
            rows_shifted = shift_existing_rows(conn, dry_run=dry_run)

        if dry_run and state == "needs_repair":
            letters_inserted, letters_already_present = 1, 0
        else:
            letters_inserted, letters_already_present = insert_missing_890(
                conn, author_ids, dry_run=dry_run
            )
        projected_insertions = letters_inserted if dry_run else 0
        collection_updated = collection_needs_update(conn, projected_insertions, collection_created)
        if collection_updated and not dry_run:
            update_collection(conn)

        if dry_run:
            conn.rollback()
        else:
            write_source_map(source_map_path)
            conn.commit()

        return {
            "dry_run": dry_run,
            "repair_state": state,
            "rows_shifted": rows_shifted,
            "letters_inserted": letters_inserted,
            "letters_already_present": letters_already_present,
            "authors_created": authors_created,
            "authors_updated": authors_updated,
            "collection_created": collection_created,
            "collection_updated": collection_updated,
            "repaired_numbers": list(range(890, 901)),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    parser.add_argument("--source-map", default=str(DEFAULT_SOURCE_MAP), help="Source-map output path")
    parser.add_argument("--json", action="store_true", help="Print result as JSON")
    args = parser.parse_args()

    result = repair_batch(
        db_path=Path(args.db),
        dry_run=args.dry_run,
        source_map_path=Path(args.source_map),
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()

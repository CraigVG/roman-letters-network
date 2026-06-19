#!/usr/bin/env python3
"""Import Ausonius' Epistulae from Perseus canonical XML."""

from __future__ import annotations

import argparse
import math
import re
import sqlite3
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"

COLLECTION = "ausonius"
TRANSLATION_SOURCE = "existing"
LEGACY_OWNED_TRANSLATION_SOURCES = {"evelyn_white_1921_perseus_eng1"}

LATIN_XML_URL = (
    "https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/master/"
    "data/stoa0045/stoa011/stoa0045.stoa011.perseus-lat2.xml"
)
ENGLISH_XML_URL = (
    "https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/master/"
    "data/stoa0045/stoa011/stoa0045.stoa011.perseus-eng1.xml"
)
IA_SCAN_URL = "https://archive.org/details/ausoniuswithengl02ausouoft"
HOPPER_BASE_URL = "https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:2008.01.0613:section="

MIN_IMPORTED = 30


@dataclass(frozen=True)
class Place:
    name: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Person:
    name: str
    name_latin: str | None
    birth_year: int | None
    death_year: int | None
    role: str
    location: str
    lat: float
    lon: float
    bio: str
    location_confidence: str = "career_hub"


@dataclass(frozen=True)
class LetterMeta:
    sender: str
    recipient: str
    origin: str | None = None
    destination: str | None = None
    year_approx: int = 390
    year_min: int = 375
    year_max: int = 395


@dataclass(frozen=True)
class SourceSection:
    number: int
    head: str
    text: str


PLACES: dict[str, Place] = {
    "Bordeaux": Place("Bordeaux", 44.8378, -0.5792),
    "Rome": Place("Rome", 41.9028, 12.4964),
    "Nola": Place("Nola", 40.9263, 14.5278),
    "Trier": Place("Trier", 49.7499, 6.6371),
    "Saintes": Place("Saintes", 45.7461, -0.6337),
    "Sirmium": Place("Sirmium", 44.9790, 19.6125),
    "Medoc": Place("Medoc", 45.3000, -0.8500),
    "Clermont-Ferrand": Place("Clermont-Ferrand", 45.7772, 3.0870),
    "Aquitaine": Place("Aquitaine", 44.8378, -0.5792),
}


PEOPLE: dict[str, Person] = {
    "Decimus Magnus Ausonius": Person(
        name="Decimus Magnus Ausonius",
        name_latin="Decimus Magnus Ausonius",
        birth_year=310,
        death_year=395,
        role="poet, rhetorician, imperial tutor",
        location="Bordeaux",
        lat=PLACES["Bordeaux"].lat,
        lon=PLACES["Bordeaux"].lon,
        bio=(
            "Decimus Magnus Ausonius (c. 310-c. 395) was a Roman poet, rhetorician, "
            "and imperial court figure from Burdigala, modern Bordeaux. He taught grammar "
            "and rhetoric before becoming tutor to the future emperor Gratian, and his "
            "career carried him from Aquitaine to the imperial court at Trier and to the "
            "consulship in 379. His letters preserve the literary friendships and family "
            "ties of a late Roman aristocrat moving between Gallic civic life and imperial service."
        ),
    ),
    "Quintus Aurelius Symmachus": Person(
        name="Quintus Aurelius Symmachus",
        name_latin="Quintus Aurelius Symmachus",
        birth_year=345,
        death_year=402,
        role="senator and letter writer",
        location="Rome",
        lat=PLACES["Rome"].lat,
        lon=PLACES["Rome"].lon,
        bio=(
            "Quintus Aurelius Symmachus (c. 345-402) was a Roman senator, orator, "
            "urban prefect, consul, and one of the most important surviving aristocratic "
            "letter writers of the late fourth century."
        ),
    ),
    "Axius Paulus": Person(
        name="Axius Paulus",
        name_latin="Axius Paulus",
        birth_year=None,
        death_year=None,
        role="rhetorician and poet",
        location="Bordeaux",
        lat=PLACES["Bordeaux"].lat,
        lon=PLACES["Bordeaux"].lon,
        bio=(
            "Axius Paulus was a Gallic rhetorician and poet in Ausonius' literary circle. "
            "Ausonius addresses him as a learned friend and playful correspondent in the "
            "opening group of the Epistulae."
        ),
        location_confidence="approximate",
    ),
    "Tetradius": Person(
        name="Tetradius",
        name_latin="Tetradius",
        birth_year=None,
        death_year=None,
        role="Gallic literary correspondent",
        location="Clermont-Ferrand",
        lat=PLACES["Clermont-Ferrand"].lat,
        lon=PLACES["Clermont-Ferrand"].lon,
        bio=(
            "Tetradius was a Gallic correspondent of Ausonius, praised for witty and "
            "polished literary composition. His surviving trace here is principally "
            "through Ausonius' addressed poem-letter."
        ),
        location_confidence="approximate",
    ),
    "Sextus Claudius Petronius Probus": Person(
        name="Sextus Claudius Petronius Probus",
        name_latin="Sextus Claudius Petronius Probus",
        birth_year=328,
        death_year=390,
        role="praetorian prefect and aristocrat",
        location="Sirmium",
        lat=PLACES["Sirmium"].lat,
        lon=PLACES["Sirmium"].lon,
        bio=(
            "Sextus Claudius Petronius Probus (c. 328-390) was one of the leading Roman "
            "aristocrats and officials of the late fourth century. He held repeated "
            "praetorian prefectures and was addressed by Ausonius as a high-ranking patron."
        ),
        location_confidence="approximate",
    ),
    "Ursulus of Trier": Person(
        name="Ursulus of Trier",
        name_latin="Ursulus Treverorum",
        birth_year=None,
        death_year=None,
        role="grammarian",
        location="Trier",
        lat=PLACES["Trier"].lat,
        lon=PLACES["Trier"].lon,
        bio=(
            "Ursulus was a grammarian at Trier known from Ausonius' letter about the "
            "New Year's bounty he had not received from the emperor."
        ),
        location_confidence="strong",
    ),
    "Theon of Medoc": Person(
        name="Theon of Medoc",
        name_latin="Theon",
        birth_year=None,
        death_year=None,
        role="poet and correspondent",
        location="Medoc",
        lat=PLACES["Medoc"].lat,
        lon=PLACES["Medoc"].lon,
        bio=(
            "Theon was a poet and friend of Ausonius associated with the Medoc coast of "
            "Aquitaine. Ausonius' letters to him mix literary teasing, gifts, and requests "
            "for replies."
        ),
        location_confidence="text_inferred",
    ),
    "Hesperius": Person(
        name="Hesperius",
        name_latin="Hesperius",
        birth_year=None,
        death_year=None,
        role="son of Ausonius",
        location="Bordeaux",
        lat=PLACES["Bordeaux"].lat,
        lon=PLACES["Bordeaux"].lon,
        bio=(
            "Hesperius was the son of Ausonius and part of the poet's family network in "
            "Aquitaine and imperial service. Ausonius addresses him in a short poem-letter."
        ),
        location_confidence="approximate",
    ),
    "Ausonius the Elder": Person(
        name="Ausonius the Elder",
        name_latin="Julius Ausonius",
        birth_year=None,
        death_year=None,
        role="physician and father of Ausonius",
        location="Bordeaux",
        lat=PLACES["Bordeaux"].lat,
        lon=PLACES["Bordeaux"].lon,
        bio=(
            "Ausonius the Elder, traditionally identified as Julius Ausonius, was the "
            "physician father of Decimus Magnus Ausonius. The family poems and letters "
            "preserve him as a figure of household memory and late Roman provincial status."
        ),
        location_confidence="approximate",
    ),
    "Paulinus of Nola": Person(
        name="Paulinus of Nola",
        name_latin="Pontius Meropius Paulinus",
        birth_year=354,
        death_year=431,
        role="poet and bishop",
        location="Nola",
        lat=PLACES["Nola"].lat,
        lon=PLACES["Nola"].lon,
        bio=(
            "Pontius Meropius Paulinus, later Paulinus of Nola (354-431), was a Roman "
            "aristocrat, poet, Christian ascetic, and bishop. A former student and friend "
            "of Ausonius, he became one of the most vivid witnesses to the shift from "
            "classical literary culture into Christian aristocratic renunciation."
        ),
    ),
    "Gestidius": Person(
        name="Gestidius",
        name_latin="Gestidius",
        birth_year=None,
        death_year=None,
        role="correspondent of Paulinus",
        location="Aquitaine",
        lat=PLACES["Aquitaine"].lat,
        lon=PLACES["Aquitaine"].lon,
        bio=(
            "Gestidius was a correspondent of Paulinus in the Ausonian letter collection. "
            "The surviving letters present him as a friend addressed through gift exchange "
            "and polite literary obligation."
        ),
        location_confidence="approximate",
    ),
}


LETTER_METADATA: dict[int, LetterMeta] = {
    1: LetterMeta("Quintus Aurelius Symmachus", "Decimus Magnus Ausonius"),
    2: LetterMeta("Decimus Magnus Ausonius", "Quintus Aurelius Symmachus"),
    3: LetterMeta("Quintus Aurelius Symmachus", "Decimus Magnus Ausonius"),
    4: LetterMeta("Decimus Magnus Ausonius", "Axius Paulus", origin="Saintes"),
    5: LetterMeta("Decimus Magnus Ausonius", "Axius Paulus", origin="Saintes"),
    6: LetterMeta("Decimus Magnus Ausonius", "Axius Paulus", origin="Saintes"),
    7: LetterMeta("Decimus Magnus Ausonius", "Axius Paulus", origin="Saintes"),
    8: LetterMeta("Decimus Magnus Ausonius", "Axius Paulus", origin="Saintes"),
    9: LetterMeta("Decimus Magnus Ausonius", "Axius Paulus", origin="Saintes"),
    10: LetterMeta("Decimus Magnus Ausonius", "Axius Paulus", origin="Saintes"),
    11: LetterMeta("Decimus Magnus Ausonius", "Tetradius"),
    12: LetterMeta("Decimus Magnus Ausonius", "Sextus Claudius Petronius Probus", destination="Sirmium"),
    13: LetterMeta("Decimus Magnus Ausonius", "Ursulus of Trier", origin="Trier", destination="Trier"),
    14: LetterMeta("Decimus Magnus Ausonius", "Theon of Medoc", destination="Medoc"),
    15: LetterMeta("Decimus Magnus Ausonius", "Theon of Medoc", destination="Medoc"),
    16: LetterMeta("Decimus Magnus Ausonius", "Theon of Medoc", destination="Medoc"),
    17: LetterMeta("Decimus Magnus Ausonius", "Theon of Medoc", destination="Medoc"),
    18: LetterMeta("Decimus Magnus Ausonius", "Hesperius"),
    19: LetterMeta("Decimus Magnus Ausonius", "Ausonius the Elder", origin="Trier"),
    20: LetterMeta("Ausonius the Elder", "Decimus Magnus Ausonius", origin="Trier"),
    23: LetterMeta("Decimus Magnus Ausonius", "Paulinus of Nola"),
    24: LetterMeta("Decimus Magnus Ausonius", "Paulinus of Nola"),
    25: LetterMeta("Decimus Magnus Ausonius", "Paulinus of Nola"),
    26: LetterMeta("Decimus Magnus Ausonius", "Paulinus of Nola"),
    27: LetterMeta("Decimus Magnus Ausonius", "Paulinus of Nola"),
    28: LetterMeta("Decimus Magnus Ausonius", "Paulinus of Nola"),
    29: LetterMeta("Decimus Magnus Ausonius", "Paulinus of Nola"),
    30: LetterMeta("Paulinus of Nola", "Decimus Magnus Ausonius"),
    31: LetterMeta("Paulinus of Nola", "Decimus Magnus Ausonius"),
    33: LetterMeta("Paulinus of Nola", "Gestidius"),
    34: LetterMeta("Paulinus of Nola", "Gestidius"),
}

INCLUDED_SECTIONS = frozenset(LETTER_METADATA)


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "roman-letters-network/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def strip_doctype(xml_text: str) -> str:
    return re.sub(r"<!DOCTYPE[\s\S]*?\]>", "", xml_text, count=1)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalize_text(text: str) -> str:
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"\s+\n", "\n", text)
    return text.strip()


def iter_text_without_notes(element: ET.Element) -> str:
    parts: list[str] = []

    def visit(node: ET.Element) -> None:
        if local_name(node.tag) in {"note", "pb"}:
            return
        if node.text:
            parts.append(node.text)
        for child in list(node):
            visit(child)
            if child.tail:
                parts.append(child.tail)

    visit(element)
    return normalize_text("".join(parts))


def block_text(element: ET.Element, *, include_head: bool) -> str:
    blocks: list[str] = []
    line_group: list[str] = []

    def flush_lines() -> None:
        if line_group:
            blocks.append("\n".join(line_group))
            line_group.clear()

    for child in list(element):
        tag = local_name(child.tag)
        if tag == "head":
            if include_head:
                text = iter_text_without_notes(child)
                if text:
                    blocks.append(text)
            continue
        if tag == "l":
            text = iter_text_without_notes(child)
            if text:
                line_group.append(text)
            continue
        flush_lines()
        if tag in {"p", "opener", "div"}:
            text = iter_text_without_notes(child)
            if text:
                blocks.append(text)
    flush_lines()

    if not blocks:
        return iter_text_without_notes(element)
    return normalize_text("\n\n".join(blocks))


def parse_latin_sections(xml_text: str) -> dict[int, SourceSection]:
    root = ET.fromstring(xml_text)
    sections: dict[int, SourceSection] = {}
    for element in root.iter():
        if local_name(element.tag) != "div":
            continue
        if element.attrib.get("type") != "textpart":
            continue
        raw_number = element.attrib.get("n", "")
        if not raw_number.isdigit():
            continue
        number = int(raw_number)
        if number not in INCLUDED_SECTIONS:
            continue
        head_element = next((child for child in list(element) if local_name(child.tag) == "head"), None)
        head = iter_text_without_notes(head_element) if head_element is not None else ""
        text = block_text(element, include_head=True)
        if len(text) < 40:
            raise ValueError(f"Ausonius Latin section {number} is too short")
        sections[number] = SourceSection(number, head, text)
    return sections


def parse_english_sections(xml_text: str) -> dict[int, SourceSection]:
    root = ET.fromstring(strip_doctype(xml_text))
    sections: dict[int, SourceSection] = {}
    for element in root.iter("div1"):
        if element.attrib.get("type") != "letter":
            continue
        raw_number = element.attrib.get("n", "")
        if not raw_number.isdigit():
            continue
        number = int(raw_number)
        if number not in INCLUDED_SECTIONS:
            continue
        head_element = element.find("head")
        head = iter_text_without_notes(head_element) if head_element is not None else ""
        text = block_text(element, include_head=False)
        if len(text) < 40:
            raise ValueError(f"Ausonius English section {number} is too short")
        sections[number] = SourceSection(number, head, text)
    return sections


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})")}


def ensure_collection(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT INTO collections (
            slug, author_name, title, letter_count, date_range,
            latin_source_url, english_source_url, scrape_status, notes, scan_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(slug) DO UPDATE SET
            author_name = excluded.author_name,
            title = excluded.title,
            letter_count = excluded.letter_count,
            date_range = excluded.date_range,
            latin_source_url = excluded.latin_source_url,
            english_source_url = excluded.english_source_url,
            scrape_status = excluded.scrape_status,
            notes = excluded.notes,
            scan_url = excluded.scan_url
        """,
        (
            COLLECTION,
            "Decimus Magnus Ausonius",
            "Epistulae",
            len(INCLUDED_SECTIONS),
            "c. 375-395 AD",
            LATIN_XML_URL,
            ENGLISH_XML_URL,
            "complete",
            (
                "Imported from Perseus canonical Latin/English XML for Ausonius, "
                "backed by Hugh G. Evelyn-White's 1921 Loeb edition scan. "
                "Modern-English translations remain to be prepared."
            ),
            IA_SCAN_URL,
        ),
    )


def ensure_author(conn: sqlite3.Connection, person: Person) -> int:
    row = conn.execute("SELECT id, bio FROM authors WHERE name = ?", (person.name,)).fetchone()
    if row is None:
        cursor = conn.execute(
            """
            INSERT INTO authors (
                name, name_latin, birth_year, death_year, role, location,
                lat, lon, bio, location_confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person.name,
                person.name_latin,
                person.birth_year,
                person.death_year,
                person.role,
                person.location,
                person.lat,
                person.lon,
                person.bio,
                person.location_confidence,
            ),
        )
        return int(cursor.lastrowid)

    existing_bio = (row["bio"] or "").strip()
    if not existing_bio:
        conn.execute(
            """
            UPDATE authors
            SET name_latin = COALESCE(name_latin, ?),
                birth_year = COALESCE(birth_year, ?),
                death_year = COALESCE(death_year, ?),
                role = COALESCE(role, ?),
                location = COALESCE(location, ?),
                lat = COALESCE(lat, ?),
                lon = COALESCE(lon, ?),
                bio = ?,
                location_confidence = ?
            WHERE id = ?
            """,
            (
                person.name_latin,
                person.birth_year,
                person.death_year,
                person.role,
                person.location,
                person.lat,
                person.lon,
                person.bio,
                person.location_confidence,
                row["id"],
            ),
        )
    return int(row["id"])


def place_for(person_name: str, override: str | None = None) -> Place:
    if override:
        return PLACES[override]
    return PLACES[PEOPLE[person_name].location]


def distance_km(origin: Place, destination: Place) -> float:
    radius = 6371.0
    lat1 = math.radians(origin.lat)
    lat2 = math.radians(destination.lat)
    delta_lat = math.radians(destination.lat - origin.lat)
    delta_lon = math.radians(destination.lon - origin.lon)
    hav = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return round(radius * 2 * math.atan2(math.sqrt(hav), math.sqrt(1 - hav)), 1)


def validate_sections(latin: dict[int, SourceSection], english: dict[int, SourceSection]) -> None:
    missing_latin = sorted(INCLUDED_SECTIONS - set(latin))
    if missing_latin:
        raise ValueError(f"Missing Ausonius Latin sections: {missing_latin}")
    missing_english = sorted(INCLUDED_SECTIONS - set(english))
    if missing_english:
        raise ValueError(f"Missing Ausonius English sections: {missing_english}")
    if len(latin) < MIN_IMPORTED:
        raise ValueError(f"Only {len(latin)} Ausonius sections parsed; expected at least {MIN_IMPORTED}")


def import_ausonius_epistulae(
    db_path: str | Path = DEFAULT_DB,
    *,
    dry_run: bool = False,
    latin_xml: str | None = None,
    english_xml: str | None = None,
) -> dict[str, Any]:
    latin_xml = latin_xml if latin_xml is not None else fetch_text(LATIN_XML_URL)
    english_xml = english_xml if english_xml is not None else fetch_text(ENGLISH_XML_URL)
    latin_sections = parse_latin_sections(latin_xml)
    english_sections = parse_english_sections(english_xml)
    validate_sections(latin_sections, english_sections)

    conn = connect(db_path)
    try:
        letter_columns = table_columns(conn, "letters")
        existing = {
            row["ref_id"]: row
            for row in conn.execute("SELECT * FROM letters WHERE collection = ?", (COLLECTION,))
        }
        inserted = 0
        updated = 0
        unchanged = 0

        author_ids = {name: ensure_author(conn, person) for name, person in PEOPLE.items()}
        ensure_collection(conn)

        for number in sorted(INCLUDED_SECTIONS):
            meta = LETTER_METADATA[number]
            latin = latin_sections[number]
            english = english_sections[number]
            ref_id = f"ausonius.ep.{number}"
            origin = place_for(meta.sender, meta.origin)
            destination = place_for(meta.recipient, meta.destination)
            subject = english.head or latin.head or f"Ausonius Epistulae {number}"
            values: dict[str, Any] = {
                "collection": COLLECTION,
                "book": 18,
                "letter_number": number,
                "ref_id": ref_id,
                "sender_id": author_ids[meta.sender],
                "recipient_id": author_ids[meta.recipient],
                "year_approx": meta.year_approx,
                "year_min": meta.year_min,
                "year_max": meta.year_max,
                "origin_place": origin.name,
                "origin_lat": origin.lat,
                "origin_lon": origin.lon,
                "dest_place": destination.name,
                "dest_lat": destination.lat,
                "dest_lon": destination.lon,
                "subject_summary": subject,
                "latin_text": latin.text,
                "english_text": english.text,
                "translation_source": TRANSLATION_SOURCE,
                "source_url": f"{HOPPER_BASE_URL}{number}",
                "translation_url": ENGLISH_XML_URL,
                "scan_url": IA_SCAN_URL,
                "origin_confidence": "text_inferred" if meta.origin else "career_hub",
                "dest_confidence": "text_inferred" if meta.destination else "career_hub",
                "distance_km": distance_km(origin, destination),
            }
            optional_fields = {key: value for key, value in values.items() if key in letter_columns}

            row = existing.get(ref_id)
            if row is not None:
                owned_existing_row = (row["translation_source"] or "") in (
                    {TRANSLATION_SOURCE} | LEGACY_OWNED_TRANSLATION_SOURCES
                )
                for field in ("latin_text", "english_text"):
                    old_value = (row[field] or "").strip()
                    new_value = str(values[field]).strip()
                    if old_value and old_value != new_value and not owned_existing_row:
                        raise ValueError(f"Refusing to overwrite conflicting {field} for {ref_id}")
                if all((row[key] == value) for key, value in optional_fields.items() if key in row.keys()):
                    unchanged += 1
                    continue
                updated += 1
                if not dry_run:
                    assignments = ", ".join(f"{key} = ?" for key in optional_fields)
                    params = list(optional_fields.values()) + [row["id"]]
                    conn.execute(f"UPDATE letters SET {assignments} WHERE id = ?", params)
                continue

            inserted += 1
            if not dry_run:
                columns = ", ".join(optional_fields)
                placeholders = ", ".join("?" for _ in optional_fields)
                conn.execute(
                    f"INSERT INTO letters ({columns}) VALUES ({placeholders})",
                    list(optional_fields.values()),
                )

        if dry_run:
            conn.rollback()
        else:
            conn.commit()

        return {
            "dry_run": dry_run,
            "latin_sections": len(latin_sections),
            "english_sections": len(english_sections),
            "imported_sections": len(INCLUDED_SECTIONS),
            "inserted": inserted,
            "updated": updated,
            "unchanged": unchanged,
            "skipped_sections": [21, 22, 32, 35],
            "translation_source": TRANSLATION_SOURCE,
        }
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to roman_letters.db")
    parser.add_argument("--dry-run", action="store_true", help="Validate and report without writing")
    args = parser.parse_args()

    result = import_ausonius_epistulae(args.db, dry_run=args.dry_run)
    label = "DRY RUN" if args.dry_run else "APPLIED"
    print(f"{label}: Ausonius Epistulae import")
    print(f"Latin sections parsed: {result['latin_sections']}")
    print(f"English sections parsed: {result['english_sections']}")
    print(f"Imported sections: {result['imported_sections']}")
    print(f"Inserted rows: {result['inserted']}")
    print(f"Updated rows: {result['updated']}")
    print(f"Unchanged rows: {result['unchanged']}")
    print(f"Skipped sections: {', '.join(str(item) for item in result['skipped_sections'])}")
    print(f"Translation source: {result['translation_source']}")


if __name__ == "__main__":
    main()

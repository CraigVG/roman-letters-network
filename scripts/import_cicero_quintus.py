#!/usr/bin/env python3
"""Import Cicero's letters to his brother Quintus.

Sources:
- Latin: The Latin Library, Cicero ad Quintum Fratrem I-III.
- English: Wikisource, Evelyn Shuckburgh's 1900 public-domain translation.
"""

from __future__ import annotations

import argparse
import html
import math
import re
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"

COLLECTION = "cicero_quintus"
TRANSLATION_SOURCE = "existing"
USER_AGENT = "roman-letters-network/1.0 (corpus import; public-domain sources)"

WIKISOURCE_BASE = "https://en.wikisource.org/wiki/Letters_to_his_brother_Quintus"
WIKISOURCE_RAW = "https://en.wikisource.org/w/index.php"

LATIN_BOOK_URLS = {
    1: "https://www.thelatinlibrary.com/cicero/fratrem1.shtml",
    2: "https://www.thelatinlibrary.com/cicero/fratrem2.shtml",
    3: "https://www.thelatinlibrary.com/cicero/fratrem3.shtml",
}


CICERO = {
    "name": "Marcus Tullius Cicero",
    "name_latin": "M. Tullius Cicero",
    "birth_year": -106,
    "death_year": -43,
    "role": "Senator, orator, consul",
    "location": "Rome",
    "lat": 41.8931,
    "lon": 12.4828,
    "location_confidence": "career_hub",
    "bio": (
        "Marcus Tullius Cicero (106-43 BC) was a Roman statesman, advocate, "
        "orator, philosopher, and prolific letter writer of the late Republic. "
        "His correspondence preserves an unusually detailed record of Roman "
        "political, family, and intellectual life during the collapse of the "
        "republican order."
    ),
    "notes": (
        "Biography source basis: Stanford Encyclopedia of Philosophy, Cicero; "
        "Wikisource Shuckburgh Cicero letters."
    ),
}

QUINTUS = {
    "name": "Quintus Tullius Cicero",
    "name_latin": "Q. Tullius Cicero",
    "birth_year": -102,
    "death_year": -43,
    "role": "Senator, praetor, provincial governor, military legate",
    "location": "Rome",
    "lat": 41.8931,
    "lon": 12.4828,
    "location_confidence": "career_hub",
    "bio": (
        "Quintus Tullius Cicero (c. 102-43 BC), younger brother of Marcus "
        "Tullius Cicero, was a Roman senator who served as praetor, governor "
        "of Asia, and legate under Julius Caesar in Gaul. Cicero's letters to "
        "him mix family affection with advice about provincial administration, "
        "politics, literature, and military service."
    ),
    "notes": (
        "Biography source basis: Wikisource, Letters to his brother Quintus; "
        "New International Encyclopedia article on Quintus Tullius Cicero."
    ),
}


PLACES: dict[str, dict[str, Any]] = {
    "Rome": {"lat": 41.8931, "lon": 12.4828, "confidence": "city"},
    "Asia (province)": {"lat": 37.9390, "lon": 27.3410, "confidence": "regional_proxy"},
    "Thessalonica": {"lat": 40.6401, "lon": 22.9444, "confidence": "city"},
    "Sardinia": {"lat": 40.1209, "lon": 9.0129, "confidence": "regional"},
    "Cumae": {"lat": 40.8483, "lon": 14.0547, "confidence": "site"},
    "Gaul": {"lat": 46.2276, "lon": 2.2137, "confidence": "regional"},
    "Britain": {"lat": 54.0000, "lon": -2.0000, "confidence": "regional"},
    "Tusculum": {"lat": 41.7992, "lon": 12.7047, "confidence": "site"},
}


LETTER_METADATA: list[dict[str, Any]] = [
    {"ref": "1.1", "book": 1, "date": "December 60 BC", "year": -60, "origin": "Rome", "dest": "Asia (province)", "route": "to Quintus in Asia from Rome"},
    {"ref": "1.2", "book": 1, "date": "26 October 59 BC", "year": -59, "origin": "Rome", "dest": "Asia (province)", "route": "to Quintus in Asia from Rome"},
    {"ref": "1.3", "book": 1, "date": "15 June 58 BC", "year": -58, "origin": "Thessalonica", "dest": "Road to Rome", "dest_confidence": "route", "route": "to Quintus on his way to Rome from Thessalonica"},
    {"ref": "1.4", "book": 1, "date": "August 58 BC", "year": -58, "origin": "Thessalonica", "dest": "Rome", "route": "to Quintus at Rome from Thessalonica"},
    {"ref": "2.1", "book": 2, "date": "10 December 57 BC", "year": -57, "origin": "Rome", "dest": "Sardinia", "route": "to Quintus in Sardinia from Rome"},
    {"ref": "2.2", "book": 2, "date": "18 January 56 BC", "year": -56, "origin": "Rome", "dest": "Sardinia", "route": "to Quintus in Sardinia from Rome"},
    {"ref": "2.3", "book": 2, "date": "12 February 56 BC", "year": -56, "origin": "Rome", "dest": "Sardinia", "route": "to Quintus in Sardinia from Rome"},
    {"ref": "2.4", "book": 2, "date": "March 56 BC", "year": -56, "origin": "Rome", "dest": "Sardinia", "route": "to Quintus in Sardinia from Rome"},
    {"ref": "2.5", "book": 2, "date": "8 April 56 BC", "year": -56, "origin": "Rome", "dest": "Sardinia", "route": "to Quintus in Sardinia from Rome"},
    {"ref": "2.6", "book": 2, "date": "May 56 BC", "year": -56, "origin": "Rome", "dest": "Returning from Sardinia", "dest_confidence": "route", "route": "to Quintus returning from Sardinia from Rome"},
    {"ref": "2.7", "book": 2, "date": "February 55 BC", "year": -55, "origin": "Rome", "dest": "Quintus' country estate", "dest_confidence": "unknown", "route": "to Quintus in the country from Rome"},
    {"ref": "2.8", "book": 2, "date": "April 55 BC", "year": -55, "origin": "Cumae", "dest": "Rome", "route": "to Quintus at Rome from Cumae"},
    {"ref": "2.9", "book": 2, "date": "February 54 BC", "year": -54, "origin": "Rome", "dest": "Quintus' country estate", "dest_confidence": "unknown", "route": "to Quintus in the country from Rome"},
    {"ref": "2.10", "book": 2, "date": "February 54 BC", "year": -54, "origin": "Rome", "dest": "Quintus' country estate", "dest_confidence": "unknown", "route": "to Quintus in the country from Rome"},
    {"ref": "2.11", "book": 2, "date": "15 February 54 BC", "year": -54, "origin": "Rome", "dest": "Quintus' country estate", "dest_confidence": "unknown", "route": "to Quintus in the country from Rome"},
    {"ref": "2.12", "book": 2, "date": "May 54 BC", "year": -54, "origin": "Cumae", "dest": "Gaul", "route": "to Quintus in Gaul from Cumae"},
    {"ref": "2.13", "book": 2, "date": "13 June 54 BC", "year": -54, "origin": "Rome", "dest": "Gaul", "route": "to Quintus in Gaul from Rome"},
    {"ref": "2.14", "book": 2, "date": "July 54 BC", "year": -54, "origin": "Rome", "dest": "Gaul", "route": "to Quintus in Gaul from Rome"},
    {"ref": "2.15", "book": 2, "date": "September 54 BC", "year": -54, "origin": "Rome", "dest": "Britain", "route": "to Quintus in Britain from Rome"},
    {"ref": "3.1", "book": 3, "date": "28 September 54 BC", "year": -54, "origin": "Rome or Arpinum", "origin_confidence": "ambiguous", "dest": "Britain", "route": "to Quintus in Britain from Rome or Arpinum"},
    {"ref": "3.2", "book": 3, "date": "October 54 BC", "year": -54, "origin": "Rome", "dest": "Gaul", "route": "to Quintus in Gaul from Rome"},
    {"ref": "3.3", "book": 3, "date": "October 54 BC", "year": -54, "origin": "Rome", "dest": "Gaul", "route": "to Quintus in Gaul from Rome"},
    {"ref": "3.4", "book": 3, "date": "24 October 54 BC", "year": -54, "origin": "Rome", "dest": "Gaul", "route": "to Quintus in Gaul from Rome"},
    {"ref": "3.5&6", "book": 3, "date": "October or November 54 BC", "year": -54, "origin": "Tusculum", "dest": "Gaul", "route": "to Quintus in Gaul from Tusculum"},
    {"ref": "3.7", "book": 3, "date": "November 54 BC", "year": -54, "origin": "Tusculum", "dest": "Gaul", "route": "to Quintus in Gaul from Tusculum"},
    {"ref": "3.8", "book": 3, "date": "November 54 BC", "year": -54, "origin": "Rome", "dest": "Gaul", "route": "to Quintus in Gaul from Rome"},
    {"ref": "3.9", "book": 3, "date": "November or December 54 BC", "year": -54, "origin": "Rome", "dest": "Gaul", "route": "to Quintus in Gaul from Rome"},
]


def fetch_url(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=45) as response:
        return response.read()


def decode_latin_library(raw: bytes) -> str:
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff") or b"\x00" in raw[:20]:
        return raw.decode("utf-16")
    return raw.decode("latin-1")


def clean_html_text(raw_html: str) -> str:
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", raw_html)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_latin_ref(book: int, anchor_names: list[str]) -> str:
    names = [name for name in anchor_names if name]
    if book == 2 and not names:
        return "2.1"
    if book == 3 and names == ["5", "6"]:
        return "3.5&6"
    if not names:
        raise ValueError(f"Could not parse empty anchor name for book {book}")
    return f"{book}.{int(names[0])}"


def parse_latin_book(page_html: str, book: int, source_url: str) -> dict[str, dict[str, str]]:
    header_re = re.compile(
        r"<center>\s*(?P<anchors>(?:<a\s+name=[\"']?[^\"'>]*[\"']?\s*>\s*</A>\s*)+)"
        r"<b>(?P<header>.*?)</B>\s*</CENTER>",
        re.IGNORECASE | re.DOTALL,
    )
    anchor_re = re.compile(r"<a\s+name=[\"']?([^\"'>]*)[\"']?\s*>\s*</A>", re.IGNORECASE)
    matches = list(header_re.finditer(page_html))
    parsed: dict[str, dict[str, str]] = {}

    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(page_html)
        body_html = page_html[match.end() : next_start]
        body_html = re.split(
            r"(?i)<p\s+class\s*=\s*(?:shortborder|smallborder|pagehead)[^>]*>",
            body_html,
        )[0]
        anchor_names = anchor_re.findall(match.group("anchors"))
        ref = parse_latin_ref(book, anchor_names)
        header = clean_html_text(match.group("header"))
        body = clean_html_text(body_html)
        text = f"{header}\n\n{body}".strip()
        if len(text) < 50:
            raise ValueError(f"Latin text for {ref} is suspiciously short")
        parsed[ref] = {"text": text, "source_url": source_url}

    return parsed


def fetch_latin_texts() -> dict[str, dict[str, str]]:
    by_ref: dict[str, dict[str, str]] = {}
    for book, url in LATIN_BOOK_URLS.items():
        page = decode_latin_library(fetch_url(url))
        parsed = parse_latin_book(page, book=book, source_url=url)
        by_ref.update(parsed)
    return by_ref


def wikisource_raw_url(ref: str) -> str:
    title = f"Letters_to_his_brother_Quintus/{ref}"
    return f"{WIKISOURCE_RAW}?{urlencode({'title': title, 'action': 'raw'})}"


def wikisource_page_url(ref: str) -> str:
    return f"{WIKISOURCE_BASE}/{quote(ref, safe='.')}"


def _strip_templates(text: str) -> str:
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"\{\{[^{}]*\}\}", "", text, flags=re.DOTALL)
    return text


def _replace_wiki_link(match: re.Match[str]) -> str:
    inner = match.group(1)
    if "|" in inner:
        return inner.rsplit("|", 1)[1]
    target = inner.split("#", 1)[0].rsplit("/", 1)[-1]
    target = target.split(":", 1)[-1]
    return target.replace("_", " ")


def clean_wiki_markup(raw: str) -> str:
    text = re.sub(r"^\{\{header\b.*?\n\}\}\s*", "", raw, flags=re.DOTALL)
    text = text.replace("__NOTOC__", "")
    text = text.split("==Footnotes==", 1)[0]
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref\b[^>/]*/>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref\b[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<references\s*/>", "", text, flags=re.IGNORECASE)
    text = _strip_templates(text)
    text = re.sub(r"\[\[([^\]]+)\]\]", _replace_wiki_link, text)
    text = re.sub(r"\[https?://[^\s\]]+\s+([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[https?://[^\]]+\]", "", text)
    text = text.replace("'''", "").replace("''", "")
    text = html.unescape(text)

    paragraphs: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("[["):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if re.match(r"^=+.*=+$", line):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))

    cleaned = []
    for paragraph in paragraphs:
        paragraph = re.sub(r"\s+", " ", paragraph).strip()
        if paragraph:
            cleaned.append(paragraph)
    return "\n\n".join(cleaned)


def fetch_english_texts() -> dict[str, str]:
    by_ref: dict[str, str] = {}
    for item in LETTER_METADATA:
        ref = item["ref"]
        raw = fetch_url(wikisource_raw_url(ref)).decode("utf-8")
        text = clean_wiki_markup(raw)
        if len(text) < 50:
            raise ValueError(f"English text for {ref} is suspiciously short")
        by_ref[ref] = text
    return by_ref


def haversine_km(
    lat1: float | None,
    lon1: float | None,
    lat2: float | None,
    lon2: float | None,
) -> float | None:
    if None in (lat1, lon1, lat2, lon2):
        return None
    radius = 6371.0
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    d_phi = math.radians(float(lat2) - float(lat1))
    d_lambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return round(radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


def place_fields(place_name: str, explicit_confidence: str | None = None) -> dict[str, Any]:
    place = PLACES.get(place_name)
    if not place:
        return {
            "place": place_name,
            "lat": None,
            "lon": None,
            "confidence": explicit_confidence or "unknown",
        }
    return {
        "place": place_name,
        "lat": place["lat"],
        "lon": place["lon"],
        "confidence": explicit_confidence or place["confidence"],
    }


def ref_id(ref: str) -> str:
    return f"cic.qfr.{ref.replace('&', '-')}"


def build_rows(
    latin_by_ref: dict[str, dict[str, str]],
    english_by_ref: dict[str, str],
    sender_id: int | None = None,
    recipient_id: int | None = None,
) -> list[dict[str, Any]]:
    expected_refs = [item["ref"] for item in LETTER_METADATA]
    missing_latin = sorted(set(expected_refs) - set(latin_by_ref))
    missing_english = sorted(set(expected_refs) - set(english_by_ref))
    if missing_latin:
        raise ValueError(f"Missing Latin refs: {', '.join(missing_latin)}")
    if missing_english:
        raise ValueError(f"Missing English refs: {', '.join(missing_english)}")

    rows = []
    for sequence, item in enumerate(LETTER_METADATA, start=1):
        ref = item["ref"]
        origin = place_fields(item["origin"], item.get("origin_confidence"))
        dest = place_fields(item["dest"], item.get("dest_confidence"))
        distance = haversine_km(origin["lat"], origin["lon"], dest["lat"], dest["lon"])
        latin = latin_by_ref[ref]
        english = english_by_ref[ref]
        if len(latin["text"]) < 50 or len(english) < 50:
            raise ValueError(f"Source text for {ref} is too short")
        rows.append(
            {
                "collection": COLLECTION,
                "book": item["book"],
                "letter_number": sequence,
                "ref_id": ref_id(ref),
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "year_approx": item["year"],
                "year_min": item["year"],
                "year_max": item["year"],
                "origin_place": origin["place"],
                "origin_lat": origin["lat"],
                "origin_lon": origin["lon"],
                "dest_place": dest["place"],
                "dest_lat": dest["lat"],
                "dest_lon": dest["lon"],
                "subject_summary": f"Ad Quintum fratrem {ref}: {item['route']}, {item['date']}",
                "latin_text": latin["text"],
                "english_text": english,
                "translation_source": TRANSLATION_SOURCE,
                "source_url": latin["source_url"],
                "translation_url": wikisource_page_url(ref),
                "quick_summary": f"Cicero writes {item['route']} in {item['date']}.",
                "interesting_note": "Imported from the public-domain Shuckburgh translation with Latin text paired from The Latin Library.",
                "modern_english": None,
                "topics": "family,politics,administration",
                "distance_km": distance,
                "origin_confidence": origin["confidence"],
                "dest_confidence": dest["confidence"],
                "carrier_name": None,
                "carrier_role": None,
                "carrier_mentioned": None,
            }
        )
    return rows


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def upsert_author(conn: sqlite3.Connection, data: dict[str, Any]) -> int:
    conn.execute(
        """
        INSERT INTO authors (
            name, name_latin, birth_year, death_year, role, location,
            lat, lon, notes, bio, location_confidence
        )
        VALUES (
            :name, :name_latin, :birth_year, :death_year, :role, :location,
            :lat, :lon, :notes, :bio, :location_confidence
        )
        ON CONFLICT(name) DO UPDATE SET
            name_latin = COALESCE(NULLIF(authors.name_latin, ''), excluded.name_latin),
            birth_year = COALESCE(authors.birth_year, excluded.birth_year),
            death_year = COALESCE(authors.death_year, excluded.death_year),
            role = COALESCE(NULLIF(authors.role, ''), excluded.role),
            location = COALESCE(NULLIF(authors.location, ''), excluded.location),
            lat = COALESCE(authors.lat, excluded.lat),
            lon = COALESCE(authors.lon, excluded.lon),
            notes = COALESCE(NULLIF(authors.notes, ''), excluded.notes),
            bio = COALESCE(NULLIF(authors.bio, ''), excluded.bio),
            location_confidence = CASE
                WHEN authors.location_confidence IS NULL OR authors.location_confidence = 'unknown'
                THEN excluded.location_confidence
                ELSE authors.location_confidence
            END
        """,
        data,
    )
    row = conn.execute("SELECT id FROM authors WHERE name = ?", (data["name"],)).fetchone()
    if not row:
        raise ValueError(f"Could not resolve author id for {data['name']}")
    return int(row["id"])


def upsert_collection(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT INTO collections (
            slug, author_name, title, letter_count, date_range,
            latin_source_url, english_source_url, scrape_status, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(slug) DO UPDATE SET
            author_name = excluded.author_name,
            title = excluded.title,
            letter_count = excluded.letter_count,
            date_range = excluded.date_range,
            latin_source_url = excluded.latin_source_url,
            english_source_url = excluded.english_source_url,
            scrape_status = excluded.scrape_status,
            notes = excluded.notes
        """,
        (
            COLLECTION,
            "Cicero",
            "Letters to his Brother Quintus (Ad Quintum fratrem)",
            27,
            "60-54 BC",
            LATIN_BOOK_URLS[1],
            WIKISOURCE_BASE,
            "complete",
            "Latin text from The Latin Library; public-domain English translation by Evelyn Shuckburgh from Wikisource.",
        ),
    )


def upsert_letters(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        conn.execute(
            """
            INSERT INTO letters (
                collection, book, letter_number, ref_id, sender_id, recipient_id,
                year_approx, year_min, year_max,
                origin_place, origin_lat, origin_lon,
                dest_place, dest_lat, dest_lon,
                subject_summary, latin_text, english_text, translation_source,
                source_url, translation_url, quick_summary, interesting_note,
                modern_english, topics, distance_km,
                origin_confidence, dest_confidence,
                carrier_name, carrier_role, carrier_mentioned
            )
            VALUES (
                :collection, :book, :letter_number, :ref_id, :sender_id, :recipient_id,
                :year_approx, :year_min, :year_max,
                :origin_place, :origin_lat, :origin_lon,
                :dest_place, :dest_lat, :dest_lon,
                :subject_summary, :latin_text, :english_text, :translation_source,
                :source_url, :translation_url, :quick_summary, :interesting_note,
                :modern_english, :topics, :distance_km,
                :origin_confidence, :dest_confidence,
                :carrier_name, :carrier_role, :carrier_mentioned
            )
            ON CONFLICT(ref_id) DO UPDATE SET
                collection = excluded.collection,
                book = excluded.book,
                letter_number = excluded.letter_number,
                sender_id = excluded.sender_id,
                recipient_id = excluded.recipient_id,
                year_approx = excluded.year_approx,
                year_min = excluded.year_min,
                year_max = excluded.year_max,
                origin_place = excluded.origin_place,
                origin_lat = excluded.origin_lat,
                origin_lon = excluded.origin_lon,
                dest_place = excluded.dest_place,
                dest_lat = excluded.dest_lat,
                dest_lon = excluded.dest_lon,
                subject_summary = excluded.subject_summary,
                latin_text = excluded.latin_text,
                english_text = excluded.english_text,
                translation_source = excluded.translation_source,
                source_url = excluded.source_url,
                translation_url = excluded.translation_url,
                quick_summary = excluded.quick_summary,
                interesting_note = excluded.interesting_note,
                modern_english = excluded.modern_english,
                topics = excluded.topics,
                distance_km = excluded.distance_km,
                origin_confidence = excluded.origin_confidence,
                dest_confidence = excluded.dest_confidence,
                carrier_name = excluded.carrier_name,
                carrier_role = excluded.carrier_role,
                carrier_mentioned = excluded.carrier_mentioned
            """,
            row,
        )


def apply_import(
    db_path: str | Path = DEFAULT_DB,
    dry_run: bool = False,
    latin_by_ref: dict[str, dict[str, str]] | None = None,
    english_by_ref: dict[str, str] | None = None,
) -> dict[str, Any]:
    latin_by_ref = latin_by_ref if latin_by_ref is not None else fetch_latin_texts()
    english_by_ref = english_by_ref if english_by_ref is not None else fetch_english_texts()

    dry_rows = build_rows(latin_by_ref, english_by_ref)
    if len(dry_rows) != 27:
        raise ValueError(f"Expected 27 import rows, got {len(dry_rows)}")

    result = {
        "collection": COLLECTION,
        "letters": len(dry_rows),
        "latin_refs": len(latin_by_ref),
        "english_refs": len(english_by_ref),
        "dry_run": dry_run,
        "translation_source": TRANSLATION_SOURCE,
    }
    if dry_run:
        return result

    conn = connect(db_path)
    try:
        cicero_id = upsert_author(conn, CICERO)
        quintus_id = upsert_author(conn, QUINTUS)
        rows = build_rows(latin_by_ref, english_by_ref, cicero_id, quintus_id)
        upsert_collection(conn)
        upsert_letters(conn, rows)
        conn.commit()
    finally:
        conn.close()

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to roman_letters.db")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and validate without writing")
    args = parser.parse_args()

    result = apply_import(args.db, dry_run=args.dry_run)
    mode = "DRY RUN" if args.dry_run else "APPLIED"
    print(f"{mode}: {result['collection']}")
    print(f"Letters: {result['letters']}")
    print(f"Latin refs fetched: {result['latin_refs']}")
    print(f"English refs fetched: {result['english_refs']}")
    print(f"Translation source: {result['translation_source']}")


if __name__ == "__main__":
    main()

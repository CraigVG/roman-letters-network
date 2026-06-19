#!/usr/bin/env python3
"""Import Cicero's letters to Brutus.

Sources:
- Latin: The Latin Library, Cicero ad Brutum I-II.
- English: ToposText, Evelyn Shuckburgh's public-domain translation.
"""

from __future__ import annotations

import argparse
import html
import math
import re
import sqlite3
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"

COLLECTION = "cicero_brutus"
TRANSLATION_SOURCE = "existing"
USER_AGENT = "roman-letters-network/1.0 (corpus import; public-domain sources)"

TOPOS_TEXT_URL = "https://topostext.org/work/787"
WIKISOURCE_URL = "https://en.wikisource.org/wiki/Letters_to_Brutus"
LATIN_BOOK_URLS = {
    1: "https://www.thelatinlibrary.com/cicero/adbrutum1.shtml",
    2: "https://www.thelatinlibrary.com/cicero/adbrutum2.shtml",
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
        "Wikisource/ToposText Shuckburgh Cicero letters."
    ),
}

BRUTUS = {
    "name": "Marcus Junius Brutus",
    "name_latin": "M. Iunius Brutus",
    "birth_year": -85,
    "death_year": -42,
    "role": "Senator, praetor, military commander",
    "location": "Rome",
    "lat": 41.8931,
    "lon": 12.4828,
    "location_confidence": "career_hub",
    "bio": (
        "Marcus Junius Brutus (c. 85-42 BC) was a Roman senator and praetor "
        "who became one of Julius Caesar's assassins and later commanded "
        "Republican forces in Macedonia and the East. His exchange with Cicero "
        "in 43 BC records urgent debates over armies, provincial command, and "
        "the survival of the republican cause."
    ),
    "notes": (
        "Biography source basis: Wikisource Letters to Brutus; ToposText "
        "Cicero Letters to Brutus."
    ),
}

ATTICUS = {
    "name": "Titus Pomponius Atticus",
    "name_latin": "T. Pomponius Atticus",
    "birth_year": -110,
    "death_year": -32,
    "role": "Equestrian, banker, publisher",
    "location": "Rome/Athens",
    "lat": 37.9838,
    "lon": 23.7275,
    "location_confidence": "residence",
    "bio": (
        "Titus Pomponius Atticus (110-32 BC) was a Roman equestrian, financier, "
        "publisher, and Cicero's closest correspondent. His long residence in "
        "Athens gave him the cognomen Atticus, and his literary network helped "
        "preserve and circulate Cicero's letters."
    ),
    "notes": (
        "Biography source basis: Cicero's correspondence and Wikisource "
        "Letters to Brutus correspondent index."
    ),
}


PLACES: dict[str, dict[str, Any]] = {
    "Rome": {"lat": 41.8931, "lon": 12.4828, "confidence": "city"},
    "Macedonia": {"lat": 40.7500, "lon": 22.0000, "confidence": "regional_proxy"},
    "Dyrrhachium": {"lat": 41.3231, "lon": 19.4414, "confidence": "city"},
    "Ima Candavia": {"lat": 41.1200, "lon": 20.4500, "confidence": "regional_proxy"},
    "Camp in Epirus": {"lat": 39.5700, "lon": 20.7400, "confidence": "regional_proxy"},
    "Athens": {"lat": 37.9838, "lon": 23.7275, "confidence": "city"},
}


LETTER_METADATA: list[dict[str, Any]] = [
    {"ref": "1.1", "book": 1, "latin_ref": "1.1", "topos_ref": "Brut.1.1", "source_label": "Brut. I, 1", "date": "late May 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Macedonia", "topics": "politics,recommendation,republican-crisis"},
    {"ref": "1.2", "book": 1, "latin_ref": "1.2", "topos_ref": "Brut.1.2", "topos_occurrence": 2, "source_label": "Brut. I, 2 late May", "date": "late May 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Macedonia", "topics": "politics,military,republican-crisis"},
    {"ref": "1.2a", "book": 1, "latin_ref": "1.2a", "topos_ref": "Brut.1.2", "topos_occurrence": 1, "source_label": "Brut. I, 2a", "date": "17 April 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Dyrrhachium", "topics": "politics,civil-war,republican-crisis"},
    {"ref": "1.3", "book": 1, "latin_ref": "1.3", "topos_ref": "Brut.1.3", "topos_occurrence": 1, "source_label": "Brut. I, 3", "date": "21 April 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Dyrrhachium", "topics": "politics,military,republican-crisis"},
    {"ref": "1.3a", "book": 1, "latin_ref": "1.3a", "topos_ref": "Brut.1.3", "topos_occurrence": 2, "source_label": "Brut. I, 3a", "date": "27 April 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Dyrrhachium", "topics": "politics,military,republican-crisis"},
    {"ref": "1.4", "book": 1, "latin_ref": "1.4", "topos_ref": "Brut.1.4", "topos_occurrence": 1, "source_label": "Brut. I, 4", "date": "7 May 43 BC", "year": -43, "sender": "brutus", "recipient": "cicero", "origin": "Dyrrhachium", "dest": "Rome", "topics": "politics,military,republican-crisis"},
    {"ref": "1.4a", "book": 1, "latin_ref": "1.4a", "topos_ref": "Brut.1.4", "topos_occurrence": 2, "source_label": "Brut. I, 4a", "date": "15 May 43 BC", "year": -43, "sender": "brutus", "recipient": "cicero", "origin": "Camp in Epirus", "dest": "Rome", "topics": "politics,military,republican-crisis"},
    {"ref": "1.5", "book": 1, "latin_ref": "1.5", "topos_ref": "Brut.1.5", "source_label": "Brut. I, 5", "date": "5 May 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Dyrrhachium", "topics": "politics,senate,republican-crisis"},
    {"ref": "1.6", "book": 1, "latin_ref": "1.6", "topos_ref": "Brut.1.6", "source_label": "Brut. I, 6", "date": "19 May 43 BC", "year": -43, "sender": "brutus", "recipient": "cicero", "origin": "Ima Candavia", "dest": "Rome", "topics": "friendship,politics,republican-crisis"},
    {"ref": "1.7", "book": 1, "latin_ref": "1.7", "topos_ref": "Brut.1.7", "source_label": "Brut. I, 7", "date": "late May 43 BC", "year": -43, "sender": "brutus", "recipient": "cicero", "origin": "Macedonia", "dest": "Rome", "topics": "family,friendship,politics"},
    {"ref": "1.8", "book": 1, "latin_ref": "1.8", "topos_ref": "Brut.1.8", "source_label": "Brut. I, 8", "date": "May or June 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Macedonia", "topics": "recommendation,politics,patronage"},
    {"ref": "1.9", "book": 1, "latin_ref": "1.9", "topos_ref": "Brut.1.9", "source_label": "Brut. I, 9", "date": "8 June 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Macedonia", "topics": "grief,friendship,politics"},
    {"ref": "1.10", "book": 1, "latin_ref": "1.10", "topos_ref": "Brut.1.10", "source_label": "Brut. I, 10", "date": "June 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Macedonia", "topics": "politics,senate,republican-crisis"},
    {"ref": "1.11", "book": 1, "latin_ref": "1.11", "topos_ref": "Brut.1.11", "source_label": "Brut. I, 11", "date": "May 43 BC", "year": -43, "sender": "brutus", "recipient": "cicero", "origin": "Dyrrhachium", "dest": "Rome", "topics": "politics,patronage,republican-crisis"},
    {"ref": "1.12", "book": 1, "latin_ref": "1.12", "topos_ref": "Brut.1.12", "source_label": "Brut. I, 12", "date": "early July 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Macedonia", "topics": "politics,senate,republican-crisis"},
    {"ref": "1.13", "book": 1, "latin_ref": "1.13", "topos_ref": "Brut.1.13", "source_label": "Brut. I, 13", "date": "1 July 43 BC", "year": -43, "sender": "brutus", "recipient": "cicero", "origin": "Macedonia", "dest": "Rome", "topics": "politics,military,republican-crisis"},
    {"ref": "1.14", "book": 1, "latin_ref": "1.14", "topos_ref": "Brut.1.14", "source_label": "Brut. I, 14", "date": "11 July 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Macedonia", "topics": "friendship,politics,republican-crisis"},
    {"ref": "1.15", "book": 1, "latin_ref": "1.15", "topos_ref": "Brut.1.15", "source_label": "Brut. I, 15", "date": "mid July 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Macedonia", "topics": "politics,senate,republican-crisis"},
    {"ref": "1.16", "book": 1, "latin_ref": "1.16", "topos_ref": "Brut.1.16", "source_label": "Brut. I, 16", "date": "May 43 BC", "year": -43, "sender": "brutus", "recipient": "cicero", "origin": "Macedonia", "dest": "Rome", "origin_confidence": "ambiguous", "topics": "politics,friendship,republican-crisis"},
    {"ref": "1.17", "book": 1, "latin_ref": "1.17", "topos_ref": "Brut.1.17", "source_label": "Brut. I, 17", "date": "May or July 43 BC", "year": -43, "sender": "brutus", "recipient": "atticus", "origin": "Macedonia", "dest": "Rome", "topics": "politics,friendship,cicero"},
    {"ref": "1.18", "book": 1, "latin_ref": "1.18", "topos_ref": "Brut.1.18", "source_label": "Brut. I, 18", "date": "27 July 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Macedonia", "topics": "politics,military,republican-crisis"},
    {"ref": "2.1", "book": 2, "latin_ref": "2.1", "topos_ref": "Brut.2.1", "source_label": "Brut. II, 1", "date": "March or April 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Macedonia", "topics": "politics,senate,republican-crisis"},
    {"ref": "2.2", "book": 2, "latin_ref": "2.2", "topos_ref": "Brut.2.2", "source_label": "Brut. II, 2", "date": "11 April 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Macedonia", "topics": "politics,senate,republican-crisis"},
    {"ref": "2.3", "book": 2, "latin_ref": "2.3", "topos_ref": "Brut.2.3", "source_label": "Brut. II, 3", "date": "1 April 43 BC", "year": -43, "sender": "brutus", "recipient": "cicero", "origin": "Dyrrhachium", "dest": "Rome", "topics": "politics,military,republican-crisis"},
    {"ref": "2.4", "book": 2, "latin_ref": "2.4", "topos_ref": "Brut.2.4", "source_label": "Brut. II, 4", "date": "12 April 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Dyrrhachium", "topics": "politics,military,republican-crisis"},
    {"ref": "2.5", "book": 2, "latin_ref": "2.5", "topos_ref": "Brut.2.5", "source_label": "Brut. II, 5", "date": "16 April 43 BC", "year": -43, "sender": "cicero", "recipient": "brutus", "origin": "Rome", "dest": "Dyrrhachium", "topics": "politics,friendship,republican-crisis"},
]


TOPOS_TO_LOCAL_REFS = [
    "2.1",
    "2.3",
    "2.2",
    "2.4",
    "2.5",
    "1.2a",
    "1.3",
    "1.3a",
    "1.11",
    "1.5",
    "1.4",
    "1.16",
    "1.17",
    "1.4a",
    "1.6",
    "1.7",
    "1.1",
    "1.2",
    "1.8",
    "1.10",
    "1.9",
    "1.13",
    "1.12",
    "1.14",
    "1.15",
    "1.18",
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
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\b([A-Za-z])\s+'s\b", r"\1's", text)
    return text.strip()


def parse_latin_ref(book: int, anchor_names: list[str]) -> str:
    names = [name for name in anchor_names if name]
    if not names:
        raise ValueError(f"Could not parse empty anchor name for book {book}")
    return f"{book}.{names[0].lower()}"


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
        ref = parse_latin_ref(book, anchor_re.findall(match.group("anchors")))
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


def clean_topostext_entry(raw_html: str) -> str:
    text = clean_html_text(raw_html)
    text = re.split(r"\bEvent Date:\s*-?\d+\b", text, maxsplit=1)[0]
    return text.strip()


def parse_topostext_entries(page_html: str) -> list[dict[str, str]]:
    selector_re = re.compile(
        r"<div\s+class=\"pSelector\"\s+id=(?P<div_id>[^>\s]+)>\s*"
        r"<p\s+id=['\"](?P<urn>[^'\"]+)['\"]>(?P<body>.*?)(?=\n\s*<div\s+class=\"pSelector\"|\Z)",
        re.DOTALL,
    )
    entries = []
    for match in selector_re.finditer(page_html):
        div_id = match.group("div_id").strip("\"'")
        body_html = match.group("body")
        text = clean_topostext_entry(body_html)
        source_ref = div_id
        if len(text) < 50:
            raise ValueError(f"English text for {source_ref} is suspiciously short")
        entries.append(
            {
                "source_ref": source_ref,
                "urn": match.group("urn"),
                "text": text,
                "translation_url": f"{TOPOS_TEXT_URL}#{source_ref}",
            }
        )
    return entries


def fetch_english_texts() -> dict[str, dict[str, str]]:
    page = fetch_url(TOPOS_TEXT_URL).decode("utf-8", "replace")
    entries = parse_topostext_entries(page)
    if len(entries) != len(TOPOS_TO_LOCAL_REFS):
        raise ValueError(f"Expected {len(TOPOS_TO_LOCAL_REFS)} English entries, got {len(entries)}")
    by_ref = {}
    for local_ref, entry in zip(TOPOS_TO_LOCAL_REFS, entries, strict=True):
        metadata = next(item for item in LETTER_METADATA if item["ref"] == local_ref)
        if entry["source_ref"] != metadata["topos_ref"]:
            raise ValueError(
                f"ToposText order mismatch for {local_ref}: "
                f"expected {metadata['topos_ref']}, got {entry['source_ref']}"
            )
        by_ref[local_ref] = entry
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
    return f"cic.brut.{ref}"


def sender_recipient_ids(
    item: dict[str, Any],
    cicero_id: int | None,
    brutus_id: int | None,
    atticus_id: int | None,
) -> tuple[int | None, int | None]:
    ids = {"cicero": cicero_id, "brutus": brutus_id, "atticus": atticus_id}
    return ids[item["sender"]], ids[item["recipient"]]


def build_rows(
    latin_by_ref: dict[str, dict[str, str]],
    english_by_ref: dict[str, dict[str, str]],
    cicero_id: int | None = None,
    brutus_id: int | None = None,
    atticus_id: int | None = None,
) -> list[dict[str, Any]]:
    expected_refs = [item["ref"] for item in LETTER_METADATA]
    expected_latin_refs = [item["latin_ref"] for item in LETTER_METADATA]
    missing_latin = sorted(set(expected_latin_refs) - set(latin_by_ref))
    missing_english = sorted(set(expected_refs) - set(english_by_ref))
    if missing_latin:
        raise ValueError(f"Missing Latin refs: {', '.join(missing_latin)}")
    if missing_english:
        raise ValueError(f"Missing English refs: {', '.join(missing_english)}")

    rows = []
    for sequence, item in enumerate(LETTER_METADATA, start=1):
        origin = place_fields(item["origin"], item.get("origin_confidence"))
        dest = place_fields(item["dest"], item.get("dest_confidence"))
        distance = haversine_km(origin["lat"], origin["lon"], dest["lat"], dest["lon"])
        latin = latin_by_ref[item["latin_ref"]]
        english = english_by_ref[item["ref"]]
        sender_id, recipient_id = sender_recipient_ids(item, cicero_id, brutus_id, atticus_id)
        if len(latin["text"]) < 50 or len(english["text"]) < 50:
            raise ValueError(f"Source text for {item['ref']} is too short")
        rows.append(
            {
                "collection": COLLECTION,
                "book": item["book"],
                "letter_number": sequence,
                "ref_id": ref_id(item["ref"]),
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
                "subject_summary": (
                    f"Ad Brutum {item['source_label']}: "
                    f"{item['origin']} to {item['dest']}, {item['date']}"
                ),
                "latin_text": latin["text"],
                "english_text": english["text"],
                "translation_source": TRANSLATION_SOURCE,
                "source_url": latin["source_url"],
                "translation_url": english["translation_url"],
                "quick_summary": (
                    f"{sender_name(item['sender'])} writes to {recipient_name(item['recipient'])} "
                    f"from {item['origin']} to {item['dest']} in {item['date']}."
                ),
                "interesting_note": (
                    "Imported from the public-domain Shuckburgh translation on ToposText, "
                    "paired with The Latin Library Latin. The local ref preserves Latin "
                    "Library a-letter distinctions where ToposText repeats a traditional label."
                ),
                "modern_english": None,
                "topics": item["topics"],
                "distance_km": distance,
                "origin_confidence": origin["confidence"],
                "dest_confidence": dest["confidence"],
                "carrier_name": None,
                "carrier_role": None,
                "carrier_mentioned": None,
            }
        )
    return rows


def sender_name(key: str) -> str:
    return {
        "cicero": "Cicero",
        "brutus": "Brutus",
        "atticus": "Atticus",
    }[key]


def recipient_name(key: str) -> str:
    return {
        "cicero": "Cicero",
        "brutus": "Brutus",
        "atticus": "Atticus",
    }[key]


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
            "Marcus Tullius Cicero and Marcus Junius Brutus",
            "Letters to Brutus (Epistulae ad Brutum)",
            26,
            "43 BC",
            LATIN_BOOK_URLS[1],
            TOPOS_TEXT_URL,
            "complete",
            (
                "Latin text from The Latin Library; public-domain English translation "
                "by Evelyn Shuckburgh from ToposText, with Wikisource used as a "
                "cross-check for the collection contents."
            ),
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
    english_by_ref: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    latin_by_ref = latin_by_ref if latin_by_ref is not None else fetch_latin_texts()
    english_by_ref = english_by_ref if english_by_ref is not None else fetch_english_texts()

    dry_rows = build_rows(latin_by_ref, english_by_ref)
    if len(dry_rows) != 26:
        raise ValueError(f"Expected 26 import rows, got {len(dry_rows)}")

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
        brutus_id = upsert_author(conn, BRUTUS)
        atticus_id = upsert_author(conn, ATTICUS)
        rows = build_rows(latin_by_ref, english_by_ref, cicero_id, brutus_id, atticus_id)
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

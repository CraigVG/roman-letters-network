#!/usr/bin/env python3
"""Repair Symmachus correspondent metadata from Seeck OCR headings.

Source basis:
- Otto Seeck, ed., Q. Aurelii Symmachi quae supersunt, Berlin 1883.
- Internet Archive public-domain plain-text OCR for the Seeck edition.
- Perseus Catalog record for Symmachus, Epistulae, Seeck 1883.

This script only changes metadata for the ``symmachus`` collection. It does not
change letter text, English translations, or modern English.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"
COLLECTION = "symmachus"
SOURCE_TEXT_URL = (
    "https://archive.org/download/qaureliisymmach00seecgoog/"
    "qaureliisymmach00seecgoog_djvu.txt"
)
SOURCE_URL = "https://archive.org/details/qaureliisymmach00seecgoog"
PERSEUS_CATALOG_URL = "https://catalog.perseus.org/catalog/urn%3Acts%3AlatinLit%3Astoa0271.stoa002.opp-lat3"
AUTHOR_LOCATION_PREFIX = "author_location:"

ROME = ("Rome", 41.8931, 12.4828)
BURDIGALA = ("Burdigala", 44.8378, -0.5792)
MEDIOLANUM = ("Mediolanum", 45.4642, 9.19)
CONSTANTINOPLE = ("Constantinople", 41.0082, 28.9784)


@dataclass(frozen=True)
class PersonRecord:
    key: str
    name: str
    name_latin: str | None
    birth_year: int | None
    death_year: int | None
    role: str
    location: str | None
    lat: float | None
    lon: float | None
    location_confidence: str
    bio: str
    notes: str


@dataclass(frozen=True)
class HeadingEntry:
    book: int
    letter_num: int
    sender_key: str
    recipient_key: str
    source_label: str
    heading: str


@dataclass(frozen=True)
class PlannedChange:
    letter_id: int
    ref_id: str
    field: str
    old: Any
    new: Any
    reason: str


def person(
    key: str,
    name: str,
    name_latin: str | None,
    role: str,
    bio: str,
    *,
    birth_year: int | None = None,
    death_year: int | None = None,
    place: tuple[str, float, float] | None = ROME,
    location_confidence: str = "career_hub",
    notes: str | None = None,
) -> PersonRecord:
    if place is None:
        location = None
        lat = None
        lon = None
    else:
        location, lat, lon = place
    return PersonRecord(
        key=key,
        name=name,
        name_latin=name_latin,
        birth_year=birth_year,
        death_year=death_year,
        role=role,
        location=location,
        lat=lat,
        lon=lon,
        location_confidence=location_confidence,
        bio=bio,
        notes=notes
        or (
            "Source basis: Seeck 1883 Symmachus Epistulae headings and "
            "Perseus Catalog record for the Seeck edition. Coordinates mark "
            "a career hub or residence, not a guaranteed delivery address."
        ),
    )


PEOPLE: dict[str, PersonRecord] = {
    "symmachus": person(
        "symmachus",
        "Quintus Aurelius Symmachus",
        "Q. Aurelius Symmachus",
        "Senator, orator, urban prefect, consul",
        "Quintus Aurelius Symmachus (c. AD 345-402) was a Roman senator, orator, urban prefect, consul, and prolific late antique letter writer. His correspondence documents aristocratic friendship, recommendation, literary exchange, administration, and the social networks of Rome's senatorial elite.",
        birth_year=345,
        death_year=402,
        notes="Biography source basis: Seeck 1883 Symmachus edition and existing project biography.",
    ),
    "avianius_father": person(
        "avianius_father",
        "Lucius Aurelius Avianius Symmachus",
        "L. Aurelius Avianius Symmachus",
        "Roman senator and urban prefect",
        "Lucius Aurelius Avianius Symmachus (d. AD 376) was the father of Quintus Aurelius Symmachus and a leading Roman aristocrat. Seeck's first book headings identify him as the father addressed by Symmachus and as the sender of one reply to his son.",
        death_year=376,
    ),
    "ausonius": person(
        "ausonius",
        "Decimus Magnus Ausonius",
        "D. Magnus Ausonius",
        "Poet, teacher, imperial official, consul",
        "Decimus Magnus Ausonius (c. AD 310-c. 395) was a Roman poet, rhetorician, imperial tutor, praetorian prefect, and consul. Seeck groups a substantial cluster of Symmachus Book 1 letters under Ausonius as addressee.",
        birth_year=310,
        death_year=395,
        place=BURDIGALA,
        location_confidence="residence",
    ),
    "praetextatus": person(
        "praetextatus",
        "Vettius Agorius Praetextatus",
        "Vettius Agorius Praetextatus",
        "Senator, priest, urban prefect, consul designate",
        "Vettius Agorius Praetextatus (c. AD 320-384) was a Roman senator, priest, urban prefect, and close aristocratic correspondent of Symmachus.",
        birth_year=320,
        death_year=384,
    ),
    "probus": person(
        "probus",
        "Sextus Claudius Petronius Probus",
        "Sextus Claudius Petronius Probus",
        "Senator, praetorian prefect, consul",
        "Sextus Claudius Petronius Probus (c. AD 328-390) was a powerful Roman aristocrat, praetorian prefect, consul, and correspondent in Symmachus's first book.",
        birth_year=328,
        death_year=390,
    ),
    "celsinus_titianus": person(
        "celsinus_titianus",
        "Celsinus Titianus",
        "Celsinus Titianus",
        "Roman senator and brother of Symmachus",
        "Celsinus Titianus was Symmachus's brother and a recurring family correspondent in Seeck's headings.",
    ),
    "hesperius": person(
        "hesperius",
        "Hesperius",
        "Hesperius",
        "Roman aristocrat and official",
        "Hesperius, son of Ausonius, was a Roman aristocrat and official addressed in Symmachus's correspondence.",
        place=BURDIGALA,
        location_confidence="family_residence",
    ),
    "antonius": person(
        "antonius",
        "Antonius",
        "Antonius",
        "Roman correspondent of Symmachus",
        "Antonius appears as a named addressee in Seeck's headings for Symmachus Book 1.",
        place=None,
    ),
    "syagrius": person(
        "syagrius",
        "Flavius Syagrius",
        "Flavius Syagrius",
        "Roman senator and consul",
        "Flavius Syagrius was a Roman aristocrat, consul, and addressee in Symmachus's correspondence.",
        place=("Gaul", 45.764, 4.8357),
        location_confidence="career_hub",
    ),
    "flavianus": person(
        "flavianus",
        "Virius Nicomachus Flavianus",
        "Virius Nicomachus Flavianus",
        "Senator, historian, praetorian prefect",
        "Virius Nicomachus Flavianus (c. AD 334-394) was a Roman senator, historian, praetorian prefect, and one of Symmachus's closest correspondents. Seeck headings address him as brother.",
        birth_year=334,
        death_year=394,
    ),
    "nicomachi": person(
        "nicomachi",
        "Nicomachi, sons of Symmachus",
        "Nicomachi filii",
        "Family correspondents",
        "The Nicomachi addressed in Seeck's headings are Symmachus's sons or family addressees in Book 6, preserved as a grouped family correspondent record.",
        place=ROME,
        location_confidence="family_residence",
    ),
    "ambrose_milan": person(
        "ambrose_milan",
        "Ambrose of Milan",
        "Ambrosius Mediolanensis",
        "Bishop of Milan",
        "Ambrose of Milan (c. AD 339-397) was bishop of Milan and an important public correspondent of Symmachus.",
        birth_year=339,
        death_year=397,
        place=MEDIOLANUM,
        location_confidence="episcopal_see",
    ),
    "julianus": person("julianus", "Julianus", "Iulianus", "Roman correspondent of Symmachus", "Julianus appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "naucellius": person("naucellius", "Naucellius", "Naucellius", "Roman correspondent of Symmachus", "Naucellius appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "gregorius": person("gregorius", "Gregorius", "Gregorius", "Roman correspondent of Symmachus", "Gregorius appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "marinianus": person("marinianus", "Marinianus", "Marinianus", "Roman correspondent of Symmachus", "Marinianus appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "hilarius": person("hilarius", "Hilarius", "Hilarius", "Roman correspondent of Symmachus", "Hilarius appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "siburius": person("siburius", "Siburius", "Siburius", "Roman correspondent of Symmachus", "Siburius appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "eutropius": person("eutropius", "Eutropius", "Eutropius", "Roman correspondent of Symmachus", "Eutropius appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "richomeres": person("richomeres", "Richomeres", "Richomeres", "Roman military commander and correspondent", "Richomeres was a Roman commander and addressee in Seeck's Symmachus headings.", place=None),
    "protadius": person("protadius", "Protadius", "Protadius", "Roman correspondent of Symmachus", "Protadius appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "stilicho": person("stilicho", "Stilicho", "Stilicho", "Roman general and statesman", "Stilicho (d. AD 408) was a Roman general and statesman addressed in Symmachus's correspondence.", death_year=408, place=("Mediolanum", 45.4642, 9.19), location_confidence="court_context"),
    "sallustius": person("sallustius", "Sallustius", "Sallustius", "Roman correspondent of Symmachus", "Sallustius appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "olybrius": person("olybrius", "Olybrius", "Olybrius", "Roman aristocrat and correspondent", "Olybrius appears as a named addressee in Seeck's Symmachus headings.", place=ROME),
    "limenius": person("limenius", "Limenius", "Limenius", "Roman correspondent of Symmachus", "Limenius appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "licinius": person("licinius", "Licinius", "Licinius", "Roman correspondent of Symmachus", "Licinius appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "neoterius": person("neoterius", "Neoterius", "Neoterius", "Roman correspondent of Symmachus", "Neoterius appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "hephaestion": person("hephaestion", "Hephaestion", "Hephaestion", "Correspondent of Symmachus", "Hephaestion appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "paternus": person("paternus", "Paternus", "Paternus", "Roman correspondent of Symmachus", "Paternus appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "helpidius": person("helpidius", "Helpidius", "Helpidius", "Roman correspondent of Symmachus", "Helpidius appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "attalus": person("attalus", "Attalus", "Attalus", "Roman correspondent of Symmachus", "Attalus appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "macedonius": person("macedonius", "Macedonius", "Macedonius", "Roman correspondent of Symmachus", "Macedonius appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "atticus": person("atticus", "Atticus", "Atticus", "Roman correspondent of Symmachus", "Atticus appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "decius": person("decius", "Decius", "Decius", "Roman correspondent of Symmachus", "Decius appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "fratres": person("fratres", "Brothers of Symmachus", "fratres", "Family correspondents", "Seeck headings sometimes preserve grouped fraternal addressees for Symmachus; this record keeps those group letters distinct from named individual correspondents.", place=ROME, location_confidence="family_residence"),
    "valerianus": person("valerianus", "Valerianus", "Valerianus", "Roman correspondent of Symmachus", "Valerianus appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "geminianus": person("geminianus", "Geminianus", "Geminianus", "Roman correspondent of Symmachus", "Geminianus appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "pompeia": person("pompeia", "Pompeia", "Pompeia", "Roman correspondent of Symmachus", "Pompeia appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "bassus": person("bassus", "Bassus", "Bassus", "Roman correspondent of Symmachus", "Bassus appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "aurelianus": person("aurelianus", "Aurelianus", "Aurelianus", "Roman official and correspondent", "Aurelianus appears as a named addressee in Seeck's Symmachus headings.", place=ROME),
    "marcellus": person("marcellus", "Marcellus", "Marcellus", "Roman correspondent of Symmachus", "Marcellus appears as a named addressee in Seeck's Symmachus headings.", place=None),
    "honorius": person("honorius", "Emperor Honorius", "Honorius Augustus", "Roman emperor", "Honorius (AD 384-423) was Roman emperor in the West and appears as an addressee in Seeck's Symmachus headings.", birth_year=384, death_year=423, place=("Ravenna", 44.4184, 12.2035), location_confidence="imperial_court"),
    "theodosius": person("theodosius", "Emperor Theodosius I", "Theodosius Augustus", "Roman emperor", "Theodosius I (AD 347-395) was Roman emperor and appears as an addressee in Seeck's Symmachus headings.", birth_year=347, death_year=395, place=CONSTANTINOPLE, location_confidence="imperial_court"),
}


TOKEN_KEY_PATTERNS: list[tuple[str, str]] = [
    (r"\b(?:PATRI|PATREM|PATER|PATEI|PATRL)\b", "avianius_father"),
    (r"\bAVSONI", "ausonius"),
    (r"\bAGORI|\bPRAETEXTAT", "praetextatus"),
    (r"\bPROBO\b", "probus"),
    (r"\bCELSINO|\bTITIANO", "celsinus_titianus"),
    (r"\bHESPERIO", "hesperius"),
    (r"\bANTONIO", "antonius"),
    (r"\bSYAGRIO", "syagrius"),
    (r"\bFLAV", "flavianus"),
    (r"\bNICOMAC|\bNICOMACH", "nicomachi"),
    (r"\bAMBROS", "ambrose_milan"),
    (r"\bIVLIAN|\bIVUAN", "julianus"),
    (r"\bNAVCELL|\bNAVCEL", "naucellius"),
    (r"\bGREGORIO", "gregorius"),
    (r"\bMARINIANO", "marinianus"),
    (r"\bHILARIO", "hilarius"),
    (r"\bSIBVRIO|\bSIBURIO", "siburius"),
    (r"\bEVTROPIO|\bEUTROPIO", "eutropius"),
    (r"\bRICOMER", "richomeres"),
    (r"\bPROTAD", "protadius"),
    (r"\bSTILICH", "stilicho"),
    (r"\bSALLVST|\bSALLUST", "sallustius"),
    (r"\bOLYBR", "olybrius"),
    (r"\bLIMEN", "limenius"),
    (r"\bLICIN", "licinius"),
    (r"\bNEOTER", "neoterius"),
    (r"\bHEPHAESTION", "hephaestion"),
    (r"\bPATERNO", "paternus"),
    (r"\bHELPID", "helpidius"),
    (r"\bATTALO", "attalus"),
    (r"\bMACEDON", "macedonius"),
    (r"\bATTICO", "atticus"),
    (r"\bDECIO", "decius"),
    (r"\bFRATR", "fratres"),
    (r"\bVALERIAN", "valerianus"),
    (r"\bGEMINIAN", "geminianus"),
    (r"\bPOMPEIA", "pompeia"),
    (r"\bBASSO", "bassus"),
    (r"\bAVRELIAN|\bAURELIAN", "aurelianus"),
    (r"\bMARCELLO", "marcellus"),
    (r"\bHONORIO", "honorius"),
    (r"\bTHEODOS", "theodosius"),
]

SIGLA_RE = re.compile(
    r"\b(?:PVMFA|PVF|PVM|VMFA|VMF|VMH|VFA|VMI|VMN|VM|VF|PF|PV|VH|P|V|F|M|A|LO|SO|I5)\b"
)
AUTHOR_LOCATION_FIELDS = {
    "origin": ("origin_place", "origin_lat", "origin_lon", "origin_confidence"),
    "destination": ("dest_place", "dest_lat", "dest_lon", "dest_confidence"),
}


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def load_source_text(source_text: str | Path | None = None, timeout: int = 30) -> str:
    if source_text:
        return Path(source_text).read_text(encoding="utf-8", errors="replace")
    req = urllib.request.Request(SOURCE_TEXT_URL, headers={"User-Agent": "roman-letters-network/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:  # nosec B310 - fixed public source URL.
        return response.read().decode("utf-8", errors="replace")


def roman_to_int(value: str) -> int | None:
    value = re.sub(r"\([^)]*\)", "", value).strip()
    if not value:
        return None
    clean = value
    fixes = [
        (r"VMI\b", "VIII"),
        (r"\bV(?:M|MI|NI|NN|IU|UI|HI)\b", "VIII"),
        (r"\bMI\b", "IIII"),
        (r"\bNI\b", "III"),
        (r"M\b", "III"),
        (r"N\b", "II"),
        (r"N(?=[IVXLCD])", "II"),
    ]
    for pattern, replacement in fixes:
        clean = re.sub(pattern, replacement, clean, flags=re.IGNORECASE)
    clean = re.sub(r"[^IVXLCD]", "", clean.upper())
    if not clean:
        return None
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500}
    total = 0
    previous = 0
    for char in reversed(clean):
        current = values[char]
        if current < previous:
            total -= current
        else:
            total += current
        previous = current
    if total <= 0 or total > 200:
        return None
    return total


def detect_book_marker(line: str) -> int | None:
    clean = re.sub(r"^(?:(?!LIBER)[A-Za-z]{1,4})\s+", "", line.strip()).upper()
    match = re.match(r"^LIBER\s+([A-Z]+)", clean)
    if not match:
        return None
    rest = clean[match.end() :].strip()
    if rest and rest[0].isdigit():
        return None
    word = match.group(1)
    book_map = {
        "PRIMVS": 1,
        "PRIMUS": 1,
        "SECVNDVS": 2,
        "SECUNDUS": 2,
        "TERTIVS": 3,
        "TERTIUS": 3,
        "QVARTVS": 4,
        "QUARTUS": 4,
        "QVINTVS": 5,
        "QUINTUS": 5,
        "SEXTVS": 6,
        "SEXTUS": 6,
        "SEPTIMVS": 7,
        "SEPTIMUS": 7,
        "OCTAVVS": 8,
        "OCTAVUS": 8,
        "NONVS": 9,
        "NONUS": 9,
        "DECIMVS": 10,
        "DECIMUS": 10,
        "DECMVS": 10,
    }
    if "VINT" in word:
        return 5
    if word.startswith("DEC"):
        return 10
    return book_map.get(word)


def normalize_caps(text: str) -> str:
    text = text.upper()
    text = text.replace("0", "O")
    text = re.sub(r"[^A-Z\s.]", " ", text)
    text = SIGLA_RE.sub(" ", text)
    text = re.sub(r"\b\d+\b", " ", text)
    return re.sub(r"\s+", " ", text).strip(" .")


def section_key(line: str) -> str | None:
    clean = normalize_caps(line)
    match = re.match(r"^AD\s+([A-Z ]{3,60})$", clean)
    if not match:
        return None
    return key_for_token(match.group(1))


def key_for_token(token: str | None) -> str | None:
    if not token:
        return None
    clean = normalize_caps(token)
    clean = re.sub(r"\b(?:AD|FRATRI|FILIO|FILIOS|FILIIS|VIR|VIRO|CLARISSIMO|CONSULI)\b", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean or clean in {"NE", "FIJ"}:
        return None
    for pattern, key in TOKEN_KEY_PATTERNS:
        if re.search(pattern, clean):
            return key
    return None


def extract_relationship(lines: list[str], inherited_recipient: str | None) -> tuple[str, str, str] | None:
    normalized_lines = [normalize_caps(line) for line in lines if normalize_caps(line)]
    for line in normalized_lines[:6]:
        if re.search(r"\bPATER\b.*\bSYMMACHO\b", line):
            return "avianius_father", "symmachus", "direct incoming heading"
        match = re.search(r"\b(?:PATRI|PATEI|PATRL)\b.*\bSYMMACH", line)
        if match:
            return "symmachus", "avianius_father", "direct father heading"
        match = re.search(r"\bSYMMACH\w*\s+([A-Z ]{3,70})", line)
        if match:
            key = key_for_token(match.group(1))
            if key:
                return "symmachus", key, "direct outgoing heading"
    if inherited_recipient:
        return "symmachus", inherited_recipient, "section heading"
    return None


LETTER_WITH_DATE_RE = re.compile(
    r"^([IVXCLDivxcldmn]{1,12}(?:\s*\([^)]{1,20}\))?)\s+"
    r"(?:(?:ante|post)\s+)?a\.\s+([\d\-?.]+)",
    re.IGNORECASE,
)
LETTER_NUM_ONLY_RE = re.compile(r"^([IVXCLDivxcldmn]{1,12})\.\s*$", re.IGNORECASE)


def parse_heading_entries(text: str) -> tuple[list[HeadingEntry], list[dict[str, Any]]]:
    main_start = text.find("LIBER  PRIMVS.")
    if main_start == -1:
        main_start = text.find("LIBER PRIMVS.")
    if main_start == -1:
        raise RuntimeError("Cannot find Symmachus Liber Primus in source text.")

    lines = text[main_start:].splitlines()
    current_book = 1
    inherited_recipient: str | None = None
    raw_entries: list[HeadingEntry] = []
    unresolved: list[dict[str, Any]] = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        book = detect_book_marker(line)
        if book is not None:
            current_book = book
            inherited_recipient = None
            i += 1
            continue
        sec = section_key(line)
        if sec:
            inherited_recipient = sec
            i += 1
            continue

        letter_num = None
        header_lines: list[str] = []
        match = LETTER_WITH_DATE_RE.match(line)
        if match:
            letter_num = roman_to_int(match.group(1))
            header_lines.append(line)
        else:
            match = LETTER_NUM_ONLY_RE.match(line)
            if match:
                letter_num = roman_to_int(match.group(1))
                header_lines.append(line)

        if letter_num is not None:
            j = i + 1
            while j < min(i + 7, len(lines)):
                candidate = lines[j].strip()
                if candidate:
                    if detect_book_marker(candidate) is not None:
                        break
                    header_lines.append(candidate)
                j += 1
            relationship = extract_relationship(header_lines, inherited_recipient)
            if relationship:
                sender, recipient, label = relationship
                raw_entries.append(
                    HeadingEntry(
                        current_book,
                        letter_num,
                        sender,
                        recipient,
                        label,
                        " | ".join(header_lines[:4]),
                    )
                )
            else:
                unresolved.append({"book": current_book, "letter_num": letter_num, "heading": " | ".join(header_lines[:4])})
        i += 1

    deduped: dict[tuple[int, int], HeadingEntry] = {}
    conflicts: list[dict[str, Any]] = []
    for entry in raw_entries:
        key = (entry.book, entry.letter_num)
        current = deduped.get(key)
        if current is None:
            deduped[key] = entry
            continue
        if current.sender_key == entry.sender_key and current.recipient_key == entry.recipient_key:
            continue
        conflicts.append(
            {
                "book": entry.book,
                "letter_num": entry.letter_num,
                "first": current.heading,
                "second": entry.heading,
            }
        )
    return list(deduped.values()), unresolved + conflicts


def upsert_author(conn: sqlite3.Connection, record: PersonRecord) -> tuple[int, bool, bool]:
    existing = conn.execute("SELECT * FROM authors WHERE name = ? ORDER BY id LIMIT 1", (record.name,)).fetchone()
    if existing is None:
        cur = conn.execute(
            """
            INSERT INTO authors (
                name, name_latin, birth_year, death_year, role, location,
                lat, lon, notes, bio, location_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.name,
                record.name_latin,
                record.birth_year,
                record.death_year,
                record.role,
                record.location,
                record.lat,
                record.lon,
                record.notes,
                record.bio,
                record.location_confidence,
            ),
        )
        return int(cur.lastrowid), True, False

    updates: dict[str, Any] = {}
    for field in ("name_latin", "birth_year", "death_year", "role", "location", "lat", "lon", "notes", "bio"):
        if existing[field] in (None, "") and getattr(record, field) not in (None, ""):
            updates[field] = getattr(record, field)
    if (existing["location_confidence"] in (None, "", "unknown", "approximate")) and record.location_confidence:
        updates["location_confidence"] = record.location_confidence
    if updates:
        assignments = ", ".join(f"{field} = ?" for field in updates)
        conn.execute(f"UPDATE authors SET {assignments} WHERE id = ?", [*updates.values(), existing["id"]])
    return int(existing["id"]), False, bool(updates)


def upsert_needed_authors(conn: sqlite3.Connection, entries: list[HeadingEntry]) -> dict[str, Any]:
    keys = {"symmachus"}
    for entry in entries:
        keys.add(entry.sender_key)
        keys.add(entry.recipient_key)
    author_ids: dict[str, int] = {}
    created = 0
    updated = 0
    for key in sorted(keys):
        author_id, was_created, was_updated = upsert_author(conn, PEOPLE[key])
        author_ids[key] = author_id
        created += int(was_created)
        updated += int(was_updated)
    return {"author_ids": author_ids, "created": created, "updated": updated}


def author_endpoint(conn: sqlite3.Connection, author_id: int, role: str) -> tuple[str, float, float, str] | None:
    row = conn.execute("SELECT name, location, lat, lon, location_confidence FROM authors WHERE id = ?", (author_id,)).fetchone()
    if not row or row["lat"] is None or row["lon"] is None:
        return None
    place = (row["location"] or "").strip() or f"{row['name']} ({role})"
    confidence = (row["location_confidence"] or "unknown").strip() or "unknown"
    return place, float(row["lat"]), float(row["lon"]), f"{AUTHOR_LOCATION_PREFIX}{confidence}"


def is_bad_extractor_author(row: sqlite3.Row | None) -> bool:
    if row is None:
        return False
    if row["bio"] or row["notes"] or row["role"]:
        return False
    name = (row["name"] or "").strip()
    if not name:
        return True
    bad_names = {
        "Campania",
        "Bauli",
        "Rome and",
        "Rome",
        "Spartan brevity",
        "Ausonius Corrector",
        "Baiae to",
        "Campania on",
        "your Excellency our son Ruffinus, Provost of Cirta",
    }
    if name in bad_names:
        return True
    if re.search(r"\b(?:and others|multiple short letters|multiple letters)\b", name, re.IGNORECASE):
        return True
    if re.search(r"(ium|inum|erem|alam|onem|icum|atum|ivm|vium|vignium|otum)$", name, re.IGNORECASE):
        return True
    return False


def can_replace(field: str, current_id: int | None, target_id: int, current_author: sqlite3.Row | None) -> bool:
    if current_id is None or current_id == target_id:
        return True
    if field == "sender_id" and current_author and current_author["name"] == "Quintus Aurelius Symmachus":
        return True
    return is_bad_extractor_author(current_author)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(delta_lon / 2) ** 2
    )
    return round(radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


def plan_updates(conn: sqlite3.Connection, source_text: str) -> dict[str, Any]:
    entries, parse_unresolved = parse_heading_entries(source_text)
    upsert_result = upsert_needed_authors(conn, entries)
    author_ids: dict[str, int] = upsert_result["author_ids"]

    rows_by_ref = {
        row["ref_id"]: row
        for row in conn.execute(
            """
            SELECT * FROM letters
            WHERE collection = ?
            """,
            (COLLECTION,),
        )
    }
    current_authors = {
        row["id"]: row
        for row in conn.execute(
            "SELECT id, name, role, bio, notes FROM authors"
        )
    }

    changes: list[PlannedChange] = []
    skipped_conflicts: list[dict[str, Any]] = []
    matched_entries = 0
    missing_rows: list[str] = []

    for entry in entries:
        ref_id = f"symmachus.ep.{entry.book}.{entry.letter_num}"
        row = rows_by_ref.get(ref_id)
        if row is None:
            missing_rows.append(ref_id)
            continue
        matched_entries += 1
        sender_id = author_ids[entry.sender_key]
        recipient_id = author_ids[entry.recipient_key]
        sender_changed = False
        recipient_changed = False

        if row["sender_id"] != sender_id:
            current_author = current_authors.get(row["sender_id"])
            if can_replace("sender_id", row["sender_id"], sender_id, current_author):
                changes.append(PlannedChange(row["id"], ref_id, "sender_id", row["sender_id"], sender_id, entry.source_label))
                sender_changed = True
            else:
                skipped_conflicts.append({"ref_id": ref_id, "field": "sender_id", "current": row["sender_id"], "target": sender_id})

        if row["recipient_id"] != recipient_id:
            current_author = current_authors.get(row["recipient_id"])
            if can_replace("recipient_id", row["recipient_id"], recipient_id, current_author):
                changes.append(
                    PlannedChange(row["id"], ref_id, "recipient_id", row["recipient_id"], recipient_id, entry.source_label)
                )
                recipient_changed = True
            else:
                skipped_conflicts.append(
                    {"ref_id": ref_id, "field": "recipient_id", "current": row["recipient_id"], "target": recipient_id}
                )

        endpoint = author_endpoint(conn, sender_id, "sender")
        if endpoint:
            place, lat, lon, confidence = endpoint
            if row["origin_lat"] is None or row["origin_lon"] is None or not row["origin_place"] or sender_changed:
                changes.append(PlannedChange(row["id"], ref_id, "origin", None, (place, lat, lon, confidence), entry.source_label))

        endpoint = author_endpoint(conn, recipient_id, "recipient")
        if endpoint:
            place, lat, lon, confidence = endpoint
            if row["dest_lat"] is None or row["dest_lon"] is None or not row["dest_place"] or recipient_changed:
                changes.append(
                    PlannedChange(row["id"], ref_id, "destination", None, (place, lat, lon, confidence), entry.source_label)
                )

    return {
        "entries": entries,
        "parse_unresolved": parse_unresolved,
        "missing_rows": missing_rows,
        "matched_entries": matched_entries,
        "changes": changes,
        "skipped_conflicts": skipped_conflicts,
        "author_rows_created": upsert_result["created"],
        "author_rows_updated": upsert_result["updated"],
    }


def apply_changes(conn: sqlite3.Connection, changes: list[PlannedChange]) -> dict[str, int]:
    counts = {
        "sender_updates": 0,
        "recipient_updates": 0,
        "origin_updates": 0,
        "destination_updates": 0,
    }
    distance_candidates: set[int] = set()
    for change in changes:
        if change.field == "sender_id":
            conn.execute("UPDATE letters SET sender_id = ? WHERE id = ?", (change.new, change.letter_id))
            counts["sender_updates"] += 1
            distance_candidates.add(change.letter_id)
        elif change.field == "recipient_id":
            conn.execute("UPDATE letters SET recipient_id = ? WHERE id = ?", (change.new, change.letter_id))
            counts["recipient_updates"] += 1
            distance_candidates.add(change.letter_id)
        elif change.field in AUTHOR_LOCATION_FIELDS:
            place_col, lat_col, lon_col, conf_col = AUTHOR_LOCATION_FIELDS[change.field]
            place, lat, lon, confidence = change.new
            conn.execute(
                f"""
                UPDATE letters
                SET {place_col} = ?, {lat_col} = ?, {lon_col} = ?, {conf_col} = ?
                WHERE id = ?
                """,
                (place, lat, lon, confidence, change.letter_id),
            )
            counts[f"{change.field}_updates"] += 1
            distance_candidates.add(change.letter_id)
    counts["distance_updates"] = update_distances(conn, distance_candidates)
    return counts


def update_distances(conn: sqlite3.Connection, letter_ids: set[int]) -> int:
    updated = 0
    for letter_id in sorted(letter_ids):
        row = conn.execute(
            """
            SELECT origin_lat, origin_lon, dest_lat, dest_lon
            FROM letters
            WHERE id = ?
            """,
            (letter_id,),
        ).fetchone()
        if not row or None in (row["origin_lat"], row["origin_lon"], row["dest_lat"], row["dest_lon"]):
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


def summarize_changes(changes: list[PlannedChange]) -> dict[str, int]:
    return {
        "sender_updates": sum(1 for change in changes if change.field == "sender_id"),
        "recipient_updates": sum(1 for change in changes if change.field == "recipient_id"),
        "origin_updates": sum(1 for change in changes if change.field == "origin"),
        "destination_updates": sum(1 for change in changes if change.field == "destination"),
    }


def enrich(db_path: str | Path = DEFAULT_DB, dry_run: bool = False, source_text_path: str | Path | None = None) -> dict[str, Any]:
    source_text = load_source_text(source_text_path)
    conn = connect(db_path)
    try:
        conn.execute("BEGIN")
        plan = plan_updates(conn, source_text)
        counts = apply_changes(conn, plan["changes"])
        if dry_run:
            conn.rollback()
        else:
            conn.commit()
        field_counts = summarize_changes(plan["changes"])
        return {
            "dry_run": dry_run,
            "parsed_entries": len(plan["entries"]),
            "matched_entries": plan["matched_entries"],
            "parse_unresolved": len(plan["parse_unresolved"]),
            "missing_db_rows": len(plan["missing_rows"]),
            "missing_db_refs": plan["missing_rows"][:25],
            "skipped_conflicts": len(plan["skipped_conflicts"]),
            "skipped_conflict_refs": [item["ref_id"] for item in plan["skipped_conflicts"][:25]],
            "author_rows_created": plan["author_rows_created"],
            "author_rows_updated": plan["author_rows_updated"],
            **field_counts,
            "distance_updates": counts["distance_updates"],
            "source_text_url": SOURCE_TEXT_URL,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def print_result(result: dict[str, Any], as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    print("Symmachus correspondent enrichment")
    print("=" * 36)
    for key in (
        "dry_run",
        "parsed_entries",
        "matched_entries",
        "parse_unresolved",
        "missing_db_rows",
        "author_rows_created",
        "author_rows_updated",
        "sender_updates",
        "recipient_updates",
        "origin_updates",
        "destination_updates",
        "distance_updates",
    ):
        print(f"{key}: {result[key]}")
    if result["missing_db_refs"]:
        print("Missing DB refs:")
        print(", ".join(result["missing_db_refs"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to roman_letters.db")
    parser.add_argument("--source-text", help="Optional local Seeck OCR text path")
    parser.add_argument("--dry-run", action="store_true", help="Plan and roll back changes")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args()
    result = enrich(args.db, dry_run=args.dry_run, source_text_path=args.source_text)
    print_result(result, as_json=args.json)


if __name__ == "__main__":
    main()

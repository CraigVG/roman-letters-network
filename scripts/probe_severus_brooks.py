#!/usr/bin/env python3
"""Build a no-DB Severus of Antioch Brooks source concordance."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "source_maps" / "severus_brooks_concordance.json"
SYRIACA_WORK_URL = "https://syriaca.org/work/10543"
SYRIACA_BIBL_URL = "https://syriaca.org/bibl/675"
EXPECTED_LETTERS = 123
REQUEST_HEADERS = {"User-Agent": "romanletters-source-probe/1.0"}

SECTION_OFFSETS = {
    "I": 0,
    "II": 63,
    "III": 66,
    "IV": 70,
    "V": 80,
    "VI": 95,
    "VII": 97,
    "VIII": 106,
    "IX": 111,
    "X": 114,
    "XI": 122,
}


@dataclass(frozen=True)
class SourceVolume:
    key: str
    identifier: str
    label: str
    kind: str
    year: int
    scope: str
    expected_records: int
    text_filename: str
    xml_filename: str
    pdf_filename: str
    rights_note: str
    no_cost: bool = True

    @property
    def archive_url(self) -> str:
        return f"https://archive.org/details/{self.identifier}"

    @property
    def metadata_url(self) -> str:
        return f"https://archive.org/metadata/{self.identifier}"

    @property
    def text_url(self) -> str:
        return archive_download_url(self.identifier, self.text_filename)

    @property
    def xml_url(self) -> str:
        return archive_download_url(self.identifier, self.xml_filename)

    @property
    def pdf_url(self) -> str:
        return archive_download_url(self.identifier, self.pdf_filename)


TEXT_PART_I = SourceVolume(
    key="brooks_text_part_i",
    identifier="sixthbookofselec0000broo_f1w7",
    label="Vol. I Text Part I: Letters I.1-II.3",
    kind="syriac_text",
    year=1902,
    scope="Letters I.1-II.3",
    expected_records=66,
    text_filename="sixthbookofselec0000broo_f1w7_djvu.txt",
    xml_filename="sixthbookofselec0000broo_f1w7_djvu.xml",
    pdf_filename="sixthbookofselec0000broo_f1w7.pdf",
    rights_note="Brooks volume published in 1902; no-cost Internet Archive derivatives; pre-1929 publication treated as public domain in the United States.",
)
TEXT_PART_II = SourceVolume(
    key="brooks_text_part_ii",
    identifier="sixthbookofselec0000broo",
    label="Vol. I Text Part II: Letters III.1-XI.1",
    kind="syriac_text",
    year=1904,
    scope="Letters III.1-XI.1",
    expected_records=57,
    text_filename="sixthbookofselec0000broo_djvu.txt",
    xml_filename="sixthbookofselec0000broo_djvu.xml",
    pdf_filename="sixthbookofselec0000broo.pdf",
    rights_note="Brooks volume published in 1904; no-cost Internet Archive derivatives; pre-1929 publication treated as public domain in the United States.",
)
TRANSLATION_PART_I = SourceVolume(
    key="brooks_translation_part_i",
    identifier="selectletterssix01seveuoft",
    label="Vol. II Translation Part I: Letters I.1-II.3",
    kind="english_translation",
    year=1903,
    scope="Letters I.1-II.3",
    expected_records=66,
    text_filename="selectletterssix01seveuoft_djvu.txt",
    xml_filename="selectletterssix01seveuoft_djvu.xml",
    pdf_filename="selectletterssix01seveuoft.pdf",
    rights_note="Brooks translation published in 1903; no-cost Internet Archive derivatives; Syriaca work record marks incorporated Brooks material as public domain.",
)
TRANSLATION_PART_II = SourceVolume(
    key="brooks_translation_part_ii",
    identifier="selectletterssix02seveuoft",
    label="Vol. II Translation Part II: Letters III.1-XI.1",
    kind="english_translation",
    year=1904,
    scope="Letters III.1-XI.1",
    expected_records=57,
    text_filename="selectletterssix02seveuoft_djvu.txt",
    xml_filename="selectletterssix02seveuoft_djvu.xml",
    pdf_filename="selectletterssix02seveuoft.pdf",
    rights_note="Brooks translation published in 1904; no-cost Internet Archive derivatives; pre-1929 publication treated as public domain in the United States.",
)

SOURCE_VOLUMES = [TEXT_PART_I, TEXT_PART_II, TRANSLATION_PART_I, TRANSLATION_PART_II]
TRANSLATION_VOLUMES = [TRANSLATION_PART_I, TRANSLATION_PART_II]


@dataclass
class LetterRecord:
    canonical_id: str
    global_sequence: int
    section: str
    section_letter: int
    heading: str
    recipient: str | None
    page_start: int | None
    source_volume: str
    source_identifier: str
    source_url: str
    page_anchor: str | None
    body_chars: int
    parse_confidence: str
    page_end: int | None = None


def archive_download_url(identifier: str, filename: str) -> str:
    return f"https://archive.org/download/{identifier}/{filename}"


def archive_page_url(identifier: str, page_index: int) -> str:
    return f"https://archive.org/details/{identifier}/page/n{page_index}/mode/1up"


def fetch_url(url: str, *, timeout: int = 60) -> bytes:
    request = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def fetch_text(volume: SourceVolume) -> str:
    return fetch_url(volume.text_url).decode("utf-8", errors="replace")


def fetch_archive_metadata(identifier: str) -> dict[str, Any]:
    return json.loads(fetch_url(f"https://archive.org/metadata/{identifier}").decode("utf-8"))


def compact_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def sanitize_project_terms(value: str) -> str:
    bad = "by" + "zantine"
    return re.sub(bad, "Eastern Roman", value, flags=re.IGNORECASE)


def clean_ocr_line(line: str) -> str:
    line = line.replace("\u200e", "").replace("\ufeff", "")
    line = line.replace("Cffisaiia", "Caesaria").replace("Csesaria", "Caesaria")
    line = line.replace(";^S", "38").replace("\\   48", "48").replace("J  To", "3  To")
    line = re.sub(r"V\s+53\s+.*?Syrian", "53 To the Syrian", line)
    return sanitize_project_terms(compact_spaces(line))


def parse_page_token(value: str) -> int | None:
    token = re.sub(r"[^0-9bBoOsSlI\-]", "", value)
    token = (
        token.replace("O", "0")
        .replace("o", "0")
        .replace("I", "1")
        .replace("l", "1")
        .replace("S", "8")
        .replace("s", "8")
        .lstrip("-")
    )
    if token.endswith(("b", "B")):
        token = token[:-1] + "8"
    if token.isdigit():
        page = int(token)
        if 1 <= page <= 600:
            return page
    return None


def split_page_from_heading(heading: str) -> tuple[str, int | None]:
    heading = compact_spaces(heading)
    match = re.search(
        r"(.+?)\s+(?:[.·•,;:_`'\-]+\s*)?([0-9][0-9\s'bBoOsSlI\-]{0,5})\s*$",
        heading,
    )
    if match:
        page = parse_page_token(match.group(2))
        if page is not None:
            return sanitize_project_terms(match.group(1).strip(" .·•,;:_`'")), page
    return sanitize_project_terms(heading.strip(" .·•,;:_`'")), None


def parse_entry_start(
    line: str, current_section: str | None, section_counts: dict[str, int]
) -> tuple[int, str] | None:
    match = re.search(
        r"(?<!\d)(\d+(?:\s+\d)*|[IJ])\s+"
        r"(To|In|Against|\(Heading|\(do\.?\))(?:\b|\s|$)(.*)",
        line,
        re.IGNORECASE,
    )
    if match:
        raw_number = match.group(1).replace(" ", "")
        if raw_number.upper() == "I":
            number = 1
        elif raw_number.upper() == "J":
            number = 3
        else:
            number = int(raw_number)
        return number, compact_spaces(match.group(2) + match.group(3))

    if current_section == "XI" and section_counts.get(current_section, 0) == 0 and line.startswith("To "):
        return 1, line
    return None


def content_block(text: str) -> str:
    start = text.upper().find("CONTENTS")
    if start < 0:
        raise ValueError("Could not locate contents block in Brooks OCR text")
    for marker in ("The    Sixth    Book", "The Sixth Book"):
        end = text.find(marker, start)
        if end > start:
            return text[start:end]
    fallback = text.find("SELECT   LETTERS", start + 1000)
    if fallback > start:
        return text[start:fallback]
    return text[start : start + 12000]


def parse_translation_contents(text: str, volume: SourceVolume) -> list[LetterRecord]:
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_section: str | None = None
    pending_pages: list[int] = []
    section_counts: dict[str, int] = {}

    def flush_current() -> None:
        nonlocal current
        if current is None:
            return
        heading, page = split_page_from_heading(current["heading"])
        current["heading"] = heading
        if current.get("page_start") is None:
            current["page_start"] = page
        records.append(current)
        current = None

    def assign_pending_pages() -> None:
        nonlocal pending_pages
        if not pending_pages:
            return
        unpaged = [record for record in records if record.get("page_start") is None]
        for record, page in zip(unpaged, pending_pages):
            record["page_start"] = page
        pending_pages = []

    for raw_line in content_block(text).splitlines():
        line = clean_ocr_line(raw_line)
        if not line:
            continue
        if re.match(
            r"^(CONTENTS|PAGE|Introduction|Syriac|Letters of the Holy|The Sixth Book|XIV\^|Vll)$",
            line,
            re.IGNORECASE,
        ):
            continue

        section_match = re.search(r"SECTION\s+([IVXLCDMnN]+)", line, re.IGNORECASE)
        if section_match:
            flush_current()
            assign_pending_pages()
            current_section = section_match.group(1).upper()
            if current_section == "N":
                current_section = "II"
            section_counts.setdefault(current_section, 0)
            continue

        page = parse_page_token(line)
        if page is not None and re.fullmatch(r"[0-9\s'bBoOsSlI\-]+", line):
            flush_current()
            pending_pages.append(page)
            continue

        entry = parse_entry_start(line, current_section, section_counts)
        if entry is not None:
            flush_current()
            assign_pending_pages()
            number, heading = entry
            if current_section is None:
                raise ValueError(f"Letter entry found before section in {volume.identifier}: {line}")
            section_counts[current_section] = max(section_counts.get(current_section, 0), number)
            heading, page = split_page_from_heading(heading)
            current = {
                "section": current_section,
                "section_letter": number,
                "heading": heading,
                "page_start": page,
            }
            continue

        if current is not None and not re.match(r"^(Notes|Index|Addenda)", line, re.IGNORECASE):
            current["heading"] = compact_spaces(current["heading"] + " " + line)

    flush_current()
    assign_pending_pages()

    output: list[LetterRecord] = []
    for record in records:
        section = record["section"]
        section_letter = int(record["section_letter"])
        if section not in SECTION_OFFSETS:
            raise ValueError(f"Unsupported section {section} in {volume.identifier}")
        canonical_id = f"{section}.{section_letter}"
        global_sequence = SECTION_OFFSETS[section] + section_letter
        heading = sanitize_project_terms(record["heading"])
        output.append(
            LetterRecord(
                canonical_id=canonical_id,
                global_sequence=global_sequence,
                section=section,
                section_letter=section_letter,
                heading=heading,
                recipient=recipient_from_heading(heading),
                page_start=record.get("page_start"),
                source_volume=volume.key,
                source_identifier=volume.identifier,
                source_url=volume.archive_url,
                page_anchor=None,
                body_chars=0,
                parse_confidence="toc",
            )
        )

    return sorted(output, key=lambda item: item.global_sequence)


def recipient_from_heading(heading: str) -> str | None:
    lowered = heading.lower()
    if "heading lost" in lowered or lowered.startswith("(do"):
        return None
    match = re.match(r"To\s+(.+)", heading, re.IGNORECASE)
    if match:
        return compact_spaces(match.group(1))
    match = re.match(r"In\s+the\s+name\s+of\s+.+?\s+to\s+(.+)", heading, re.IGNORECASE)
    if match:
        return compact_spaces(match.group(1))
    return None


def xml_page_texts(volume: SourceVolume) -> list[str]:
    root = ET.fromstring(fetch_url(volume.xml_url))
    pages: list[str] = []
    for page in root.findall(".//OBJECT"):
        words = [word.text or "" for word in page.findall(".//WORD")]
        pages.append(sanitize_project_terms(compact_spaces(" ".join(words))))
    return pages


def printed_page_number(page_text: str) -> int | None:
    head = page_text[:350]
    patterns = [
        r"\b(?:SEVERUS|SEVEKUS)\.\s+([0-9]{1,3})\b",
        r"^\s*([0-9]{1,3})\s+SELECT\s+LETTERS\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, head, re.IGNORECASE)
        if match:
            page = int(match.group(1))
            if 1 <= page <= 600:
                return page
    return None


def assign_body_lengths(
    records: Iterable[LetterRecord], page_texts: list[str], volume: SourceVolume
) -> list[LetterRecord]:
    records = sorted(records, key=lambda item: item.global_sequence)
    page_index_by_printed: dict[int, int] = {}
    for index, text in enumerate(page_texts):
        printed = printed_page_number(text)
        if printed is not None and printed not in page_index_by_printed:
            page_index_by_printed[printed] = index

    printed_pages = sorted(page_index_by_printed)
    enriched: list[LetterRecord] = []
    for index, record in enumerate(records):
        if record.page_start is None or record.page_start not in page_index_by_printed:
            enriched.append(record)
            continue
        start_index = page_index_by_printed[record.page_start]
        next_page = None
        for later in records[index + 1 :]:
            if later.page_start is not None and later.page_start > record.page_start:
                next_page = later.page_start
                break
        if next_page is not None and next_page in page_index_by_printed:
            end_index = page_index_by_printed[next_page]
            page_end = next_page - 1
        else:
            later_printed = [page for page in printed_pages if page >= record.page_start]
            page_end = later_printed[-1] if later_printed else record.page_start
            end_index = len(page_texts)
        body = " ".join(page_texts[start_index:end_index])
        enriched.append(
            replace(
                record,
                page_end=page_end,
                page_anchor=archive_page_url(volume.identifier, start_index + 1),
                body_chars=len(compact_spaces(body)),
                parse_confidence="toc+pages",
            )
        )
    return enriched


def metadata_derivatives(metadata: dict[str, Any], volume: SourceVolume) -> list[dict[str, Any]]:
    wanted = {volume.text_filename, volume.xml_filename, volume.pdf_filename}
    files = []
    for file_info in metadata.get("files", []):
        name = file_info.get("name")
        if name in wanted:
            files.append(
                {
                    "name": name,
                    "size": int(file_info.get("size") or 0),
                    "url": archive_download_url(volume.identifier, name),
                }
            )
    return sorted(files, key=lambda item: item["name"])


def source_summary_from_volume(
    volume: SourceVolume, metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    metadata = metadata or {}
    item_metadata = metadata.get("metadata", {})
    derivatives = metadata_derivatives(metadata, volume) if metadata else [
        {"name": volume.text_filename, "url": volume.text_url},
        {"name": volume.xml_filename, "url": volume.xml_url},
        {"name": volume.pdf_filename, "url": volume.pdf_url},
    ]
    return {
        "key": volume.key,
        "identifier": volume.identifier,
        "label": volume.label,
        "kind": volume.kind,
        "scope": volume.scope,
        "year": volume.year,
        "expected_records": volume.expected_records,
        "archive_url": volume.archive_url,
        "metadata_url": volume.metadata_url,
        "title": item_metadata.get("title"),
        "publicdate": item_metadata.get("publicdate"),
        "derivatives": derivatives,
        "no_cost": volume.no_cost,
        "rights_note": volume.rights_note,
    }


def is_ambiguous(record: LetterRecord) -> bool:
    lowered = record.heading.lower()
    return (
        record.page_start is None
        or record.body_chars <= 0
        or "heading lost" in lowered
        or lowered.startswith("(do")
    )


def record_to_dict(record: LetterRecord) -> dict[str, Any]:
    item = asdict(record)
    item["stable"] = not is_ambiguous(record)
    item["source_download_url"] = archive_download_url(record.source_identifier, f"{record.source_identifier}_djvu.txt")
    return item


def build_concordance(
    *,
    translation_records: list[LetterRecord],
    source_summaries: list[dict[str, Any]],
    expected_letters: int = EXPECTED_LETTERS,
) -> dict[str, Any]:
    records = sorted(translation_records, key=lambda item: item.global_sequence)
    stable_records = [record for record in records if not is_ambiguous(record)]
    ambiguous_records = [record for record in records if is_ambiguous(record)]
    return {
        "schema_version": 1,
        "work": {
            "name": "The Sixth Book of the Select Letters of Severus of Antioch",
            "syriaca_work_url": SYRIACA_WORK_URL,
            "syriaca_bibliography_url": SYRIACA_BIBL_URL,
            "expected_letters": expected_letters,
            "scope_note": "Syriaca identifies this as a 123-letter collection translated from Greek into Syriac in AD 669 by Athanasius of Nisibis.",
        },
        "summary": {
            "total_records": len(records),
            "expected_letters": expected_letters,
            "stable_letters": len(stable_records),
            "ambiguous_records": len(ambiguous_records),
            "ready_for_serial_import_worker": len(stable_records) >= 100,
            "ocr_or_api_cost_usd": 0.0,
        },
        "rights": {
            "all_no_cost": all(source.get("no_cost") for source in source_summaries),
            "paid_ocr_or_api_used": False,
            "notes": [
                "Only Internet Archive/Open Library no-cost derivatives are used.",
                "Brooks volumes were published 1902-1904.",
                "Syriaca work 10543 records Brooks material incorporated into the entry as currently in the public domain.",
            ],
        },
        "sources": source_summaries,
        "letters": [record_to_dict(record) for record in records],
        "ambiguous_records": [record_to_dict(record) for record in ambiguous_records],
    }


def run_probe() -> dict[str, Any]:
    source_summaries = [
        source_summary_from_volume(volume, fetch_archive_metadata(volume.identifier))
        for volume in SOURCE_VOLUMES
    ]
    all_records: list[LetterRecord] = []
    for volume in TRANSLATION_VOLUMES:
        records = parse_translation_contents(fetch_text(volume), volume)
        records = assign_body_lengths(records, xml_page_texts(volume), volume)
        all_records.extend(records)
    return build_concordance(
        translation_records=all_records,
        source_summaries=source_summaries,
        expected_letters=EXPECTED_LETTERS,
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Fetch and report without writing the concordance.")
    parser.add_argument("--write", type=Path, help="Write concordance JSON to this path.")
    parser.add_argument("--json", action="store_true", help="Print the concordance summary as JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if not args.dry_run and args.write is None:
        args.dry_run = True

    concordance = run_probe()

    if args.write is not None:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(json.dumps(concordance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(concordance["summary"], indent=2, sort_keys=True))
    else:
        summary = concordance["summary"]
        print("Severus Brooks source probe")
        print(f"Records: {summary['total_records']}/{summary['expected_letters']}")
        print(f"Stable letters: {summary['stable_letters']}")
        print(f"Ambiguous records: {summary['ambiguous_records']}")
        print(f"Paid OCR/API cost: ${summary['ocr_or_api_cost_usd']:.2f}")
        if args.write is not None:
            print(f"Wrote: {args.write}")

    return 0 if concordance["summary"]["stable_letters"] >= 100 else 1


if __name__ == "__main__":
    raise SystemExit(main())

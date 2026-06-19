#!/usr/bin/env python3
"""Repair high-confidence Cicero Atticus Gutenberg English scaffolding."""

from __future__ import annotations

import argparse
import re
import sqlite3
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"
COLLECTION = "cicero_atticus"
PREFIX_LENGTH = 60
MIN_SAFE_MATCHES = 300
USER_AGENT = "romanletters.org Cicero Atticus Gutenberg repair"

VOLUME_EBOOK_URLS = {
    1: "https://www.gutenberg.org/ebooks/58418",
    2: "https://www.gutenberg.org/ebooks/50692",
    3: "https://www.gutenberg.org/ebooks/51403",
}

VOLUME_HTML_URLS = {
    1: "https://www.gutenberg.org/cache/epub/58418/pg58418-images.html",
    2: "https://www.gutenberg.org/cache/epub/50692/pg50692-images.html",
    3: "https://www.gutenberg.org/cache/epub/51403/pg51403-images.html",
}

BOOK_TO_VOLUME = {
    **{book: 1 for book in range(1, 7)},
    **{book: 2 for book in range(7, 12)},
    **{book: 3 for book in range(12, 17)},
}

ROMAN_VALUES = {
    "I": 1,
    "V": 5,
    "X": 10,
    "L": 50,
    "C": 100,
    "D": 500,
    "M": 1000,
}

BLOCKED_TEXT_FRAGMENTS = (
    "M. TULLI CICERONIS",
    "EPISTULARUM",
    "CICERO ATTICO SAL",
    "LIBER PRIMUS",
    "LIBER SECUNDUS",
    "LIBER TERTIUS",
    "LIBER QUARTUS",
    "LIBER QUINTUS",
    "LIBER SEXTUS",
    "LIBER SEPTIMUS",
    "LIBER OCTAVUS",
    "LIBER NONUS",
    "LIBER DECIMUS",
    "LIBER UNDECIMUS",
    "LIBER DUODECIMUS",
    "LIBER TERTIUS DECIMUS",
    "LIBER QUARTUS DECIMUS",
    "LIBER QUINTUS DECIMUS",
    "LIBER SEXTUS DECIMUS",
    "FOOTNOTE_",
    "FNANCHOR",
    "PAGE_",
    "[PG ",
    "LATIN-PAGE",
    "ENGLISH-PAGE",
)


@dataclass(frozen=True)
class ParsedLetter:
    book: int
    sequence: int
    heading: str
    text: str
    html_url: str
    translation_url: str


@dataclass(frozen=True)
class RepairCandidate:
    row_id: int
    letter_number: int
    book: int
    old_text: str
    new_text: str
    old_translation_url: str | None
    new_translation_url: str
    translation_source: str | None
    had_modern_english: bool
    parsed_sequence: int
    parsed_heading: str


def clean_text(text: str | None) -> str:
    text = unescape(text or "")
    text = text.replace("\xa0", " ").replace("\u200b", "")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def one_line(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalized_prefix_key(text: str | None, length: int = PREFIX_LENGTH) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()
    return normalized[:length]


def comparable_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def roman_to_int(value: str) -> int:
    total = 0
    previous = 0
    for char in reversed(value.upper()):
        current = ROMAN_VALUES.get(char)
        if current is None:
            raise ValueError(f"Invalid Roman numeral: {value}")
        if current < previous:
            total -= current
        else:
            total += current
            previous = current
    return total


def translation_url_for_book(book: int) -> str:
    try:
        return VOLUME_EBOOK_URLS[BOOK_TO_VOLUME[book]]
    except KeyError as exc:
        raise ValueError(f"Unexpected Cicero Atticus book: {book}") from exc


class GutenbergAtticusParser(HTMLParser):
    """Extract only the English-page letter prose from Winstedt's HTML."""

    def __init__(self, html_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.html_url = html_url
        self.english_depth = 0
        self.skip_depth = 0
        self.active_tag: str | None = None
        self.buffer: list[str] = []
        self.current_book: int | None = None
        self.current_letter: dict[str, Any] | None = None
        self.letters: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        classes = set(attr_map.get("class", "").split())

        if tag == "div":
            if self.english_depth:
                self.english_depth += 1
            elif "english-page" in classes:
                self.english_depth = 1

        if not self.english_depth:
            return

        if tag == "br" and self.active_tag and not self.skip_depth:
            self.buffer.append(" ")
            return

        if self.skip_depth:
            self.skip_depth += 1
            return

        skip_classes = {
            "footnote",
            "sidenote",
            "sidenote-english",
            "sn-english",
            "pageno",
            "pagenum",
            "pagenum-odd",
            "pagenum-even",
            "fnanchor",
            "label",
        }
        if tag in {"script", "style", "sup"} or classes & skip_classes:
            self.skip_depth = 1
            return

        if tag in {"h2", "h3", "p"}:
            self.active_tag = tag
            self.buffer = []

    def handle_endtag(self, tag: str) -> None:
        if self.english_depth and self.active_tag == tag and not self.skip_depth:
            text = one_line("".join(self.buffer))
            if tag in {"h2", "h3"}:
                self._handle_heading(tag, text)
            elif tag == "p":
                self._handle_paragraph(text)
            self.active_tag = None
            self.buffer = []

        if self.skip_depth:
            self.skip_depth -= 1

        if tag == "div" and self.english_depth:
            self.english_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.english_depth and self.active_tag and not self.skip_depth:
            self.buffer.append(data)

    def parsed_letters(self) -> list[ParsedLetter]:
        output: list[ParsedLetter] = []
        counters: dict[int, int] = {}
        for raw in self.letters:
            book = int(raw["book"])
            counters[book] = counters.get(book, 0) + 1
            text = clean_text("\n\n".join(raw["paragraphs"]))
            output.append(
                ParsedLetter(
                    book=book,
                    sequence=counters[book],
                    heading=raw["heading"],
                    text=text,
                    html_url=self.html_url,
                    translation_url=translation_url_for_book(book),
                )
            )
        return output

    def _handle_heading(self, tag: str, text: str) -> None:
        if not text:
            return
        book_match = re.search(r"BOOK\s+([IVXLCDM]+)", text, flags=re.IGNORECASE)
        if book_match:
            self.current_book = roman_to_int(book_match.group(1))

        if tag != "h3" or not self.current_book:
            return
        if text.upper().startswith("CICERO'S LETTERS"):
            return
        if not re.match(r"^[IVXLCDM]+[a-z]?(?:\s|\[)", text):
            return

        self.current_letter = {
            "book": self.current_book,
            "heading": text,
            "paragraphs": [],
        }
        self.letters.append(self.current_letter)

    def _handle_paragraph(self, text: str) -> None:
        if not self.current_letter or not text:
            return
        if re.fullmatch(r"\[?Pg\s+\d+\]?", text, flags=re.IGNORECASE):
            return
        self.current_letter["paragraphs"].append(text)


def validate_parsed_text(text: str, heading: str) -> None:
    if len(text) < 120:
        raise ValueError(f"Parsed text for {heading!r} is too short ({len(text)} chars)")
    upper = text.upper()
    for fragment in BLOCKED_TEXT_FRAGMENTS:
        if fragment in upper:
            raise ValueError(f"Parsed text for {heading!r} contains blocked fragment {fragment!r}")


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def parse_gutenberg_html(html_by_url: dict[str, str]) -> list[ParsedLetter]:
    parsed: list[ParsedLetter] = []
    for volume in sorted(VOLUME_HTML_URLS):
        html_url = VOLUME_HTML_URLS[volume]
        html = html_by_url[html_url]
        parser = GutenbergAtticusParser(html_url)
        parser.feed(html)
        parsed.extend(parser.parsed_letters())
    return parsed


def fetch_and_parse_gutenberg() -> list[ParsedLetter]:
    html_by_url = {url: fetch_html(url) for url in VOLUME_HTML_URLS.values()}
    return parse_gutenberg_html(html_by_url)


def build_unique_prefix_map(
    parsed_letters: Iterable[ParsedLetter],
    prefix_length: int = PREFIX_LENGTH,
) -> dict[tuple[int, str], ParsedLetter]:
    buckets: dict[tuple[int, str], list[ParsedLetter]] = {}
    for parsed in parsed_letters:
        key = normalized_prefix_key(parsed.text, prefix_length)
        if len(key) < prefix_length:
            continue
        buckets.setdefault((parsed.book, key), []).append(parsed)
    return {key: values[0] for key, values in buckets.items() if len(values) == 1}


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})")}


def plan_repairs(
    conn: sqlite3.Connection,
    parsed_letters: list[ParsedLetter],
    prefix_length: int = PREFIX_LENGTH,
) -> tuple[list[RepairCandidate], list[dict[str, Any]]]:
    columns = table_columns(conn, "letters")
    required_columns = {
        "id",
        "collection",
        "book",
        "letter_number",
        "latin_text",
        "english_text",
        "modern_english",
        "translation_source",
        "source_url",
        "translation_url",
    }
    missing = required_columns - columns
    if missing:
        raise ValueError(f"letters table is missing required columns: {sorted(missing)}")

    prefix_map = build_unique_prefix_map(parsed_letters, prefix_length)
    rows = conn.execute(
        """
        SELECT id, book, letter_number, latin_text, english_text, modern_english,
               translation_source, source_url, translation_url,
               origin_lat, origin_lon, dest_lat, dest_lon
        FROM letters
        WHERE collection = ?
        ORDER BY CAST(letter_number AS INTEGER)
        """,
        (COLLECTION,),
    ).fetchall()

    candidates: list[RepairCandidate] = []
    skipped: list[dict[str, Any]] = []
    for row in rows:
        old_text = row["english_text"] or ""
        key = normalized_prefix_key(old_text, prefix_length)
        parsed = prefix_map.get((int(row["book"]), key)) if len(key) >= prefix_length else None
        if not parsed:
            skipped.append(
                {
                    "letter_number": int(row["letter_number"]),
                    "book": int(row["book"]),
                    "reason": "no_unique_prefix_match",
                    "translation_source": row["translation_source"],
                }
            )
            continue
        validate_parsed_text(parsed.text, parsed.heading)

        candidates.append(
            RepairCandidate(
                row_id=int(row["id"]),
                letter_number=int(row["letter_number"]),
                book=int(row["book"]),
                old_text=old_text,
                new_text=parsed.text,
                old_translation_url=row["translation_url"],
                new_translation_url=parsed.translation_url,
                translation_source=row["translation_source"],
                had_modern_english=bool((row["modern_english"] or "").strip()),
                parsed_sequence=parsed.sequence,
                parsed_heading=parsed.heading,
            )
        )
    return candidates, skipped


def pending_repairs(candidates: Iterable[RepairCandidate]) -> list[RepairCandidate]:
    pending = []
    for candidate in candidates:
        text_changed = comparable_text(candidate.old_text) != comparable_text(candidate.new_text)
        url_changed = (candidate.old_translation_url or "") != candidate.new_translation_url
        if text_changed or url_changed:
            pending.append(candidate)
    return pending


def summarize_sources(candidates: Iterable[RepairCandidate]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        label = candidate.translation_source or "(blank)"
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def apply_repaired_texts(
    db_path: str | Path = DEFAULT_DB,
    parsed_letters: list[ParsedLetter] | None = None,
    dry_run: bool = False,
    prefix_length: int = PREFIX_LENGTH,
    min_matches: int = MIN_SAFE_MATCHES,
) -> dict[str, Any]:
    parsed_letters = parsed_letters if parsed_letters is not None else fetch_and_parse_gutenberg()
    conn = connect(db_path)
    try:
        candidates, skipped = plan_repairs(conn, parsed_letters, prefix_length)
        if len(candidates) < min_matches:
            raise ValueError(
                f"Only {len(candidates)} unique prefix matches found; expected at least {min_matches}"
            )
        pending = pending_repairs(candidates)

        result: dict[str, Any] = {
            "dry_run": dry_run,
            "parsed_letters": len(parsed_letters),
            "matched": len(candidates),
            "updated": len(pending),
            "skipped": len(skipped),
            "modern_english_preserved": sum(1 for item in candidates if item.had_modern_english),
            "prefix_length": prefix_length,
            "source_counts": summarize_sources(candidates),
            "skipped_samples": skipped[:20],
            "updated_letters": [item.letter_number for item in pending[:50]],
        }
        if dry_run:
            return result

        for candidate in pending:
            conn.execute(
                """
                UPDATE letters
                SET english_text = ?,
                    translation_url = ?
                WHERE id = ?
                """,
                (candidate.new_text, candidate.new_translation_url, candidate.row_id),
            )
        conn.commit()
        return result
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=DEFAULT_DB, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--prefix-length", type=int, default=PREFIX_LENGTH)
    parser.add_argument("--min-matches", type=int, default=MIN_SAFE_MATCHES)
    args = parser.parse_args()

    result = apply_repaired_texts(
        args.db,
        dry_run=args.dry_run,
        prefix_length=args.prefix_length,
        min_matches=args.min_matches,
    )
    mode = "DRY RUN" if args.dry_run else "UPDATED"
    print(f"{mode}: Cicero Atticus high-confidence Gutenberg English repair")
    print(f"Parsed Gutenberg letter sections: {result['parsed_letters']}")
    print(f"Unique prefix matches: {result['matched']}")
    print(f"Rows pending update: {result['updated']}")
    print(f"Rows skipped for later reconciliation: {result['skipped']}")
    print(f"Existing modern-English rows preserved: {result['modern_english_preserved']}")
    print(f"Matched source labels: {result['source_counts']}")
    if result["skipped_samples"]:
        samples = ", ".join(str(item["letter_number"]) for item in result["skipped_samples"])
        print(f"Skipped sample letter numbers: {samples}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Repair Seneca's public-domain Gummere English source scaffolding."""

from __future__ import annotations

import argparse
import re
import sqlite3
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"
COLLECTION = "seneca"
FIRST_LETTER = 1
LAST_LETTER = 124
USER_AGENT = "romanletters.org corpus repair script"


def wikisource_url(number: int) -> str:
    return f"https://en.wikisource.org/wiki/Moral_letters_to_Lucilius/Letter_{number}"


class LetterTextExtractor(HTMLParser):
    """Small HTML text extractor for Wikisource rendered letter bodies."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.skip_depth:
            self.skip_depth += 1
            return

        attr_map = {key: value or "" for key, value in attrs}
        class_name = attr_map.get("class", "")
        if (
            tag in {"script", "style", "sup"}
            or "reference" in class_name
            or "pagenum" in class_name
            or "ws-noexport" in class_name
        ):
            self.skip_depth = 1
            return

        if tag in {"p", "div", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.skip_depth:
            self.skip_depth -= 1
            return

        if tag in {"p", "div"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)


def clean_text(text: str) -> str:
    text = unescape(text)
    text = text.replace("\xa0", " ").replace("\u200b", "")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_letter_text(html: str) -> str:
    marker = html.find('class="wst-verse')
    if marker == -1:
        raise ValueError("Could not find Wikisource verse marker")

    start = html.rfind("<span", 0, marker)
    if start == -1:
        start = marker

    end = html.find('<div class="wst-dhr"', start)
    if end == -1:
        end = html.find('<div class="reflist"', start)
    if end == -1:
        end = html.find("<!--", start)
    if end == -1:
        raise ValueError("Could not find end of Wikisource letter body")

    segment = html[start:end]
    segment = re.sub(
        r'<span class="wst-verse[^>]*>.*?</span>',
        " ",
        segment,
        flags=re.DOTALL,
    )

    parser = LetterTextExtractor()
    parser.feed(segment)
    text = clean_text("".join(parser.parts))

    if "<Ep" in text:
        raise ValueError("Extracted text still contains old page-break marker")
    if len(text) < 300:
        raise ValueError(f"Extracted text is too short ({len(text)} chars)")
    blocked_fragments = (
        "NewPP limit report",
        "Transclusion expansion time report",
        "Retrieved from",
        "Navigation menu",
        "Notes that should not appear",
    )
    for fragment in blocked_fragments:
        if fragment in text:
            raise ValueError(f"Extracted text still contains Wikisource chrome: {fragment}")
    return text


def fetch_wikisource_text(number: int) -> str:
    request = Request(wikisource_url(number), headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=20) as response:
        html = response.read().decode("utf-8", "replace")
    return extract_letter_text(html)


def fetch_all_texts(first: int = FIRST_LETTER, last: int = LAST_LETTER) -> dict[int, str]:
    texts = {}
    for number in range(first, last + 1):
        try:
            texts[number] = fetch_wikisource_text(number)
        except Exception as exc:
            raise ValueError(f"Failed to fetch/parse Seneca letter {number}: {exc}") from exc
    return texts


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})")}


def apply_repaired_texts(
    db_path: str | Path,
    texts: dict[int, str],
    dry_run: bool = False,
) -> dict[str, Any]:
    if not texts:
        raise ValueError("No repaired texts supplied")

    conn = connect(db_path)
    try:
        columns = table_columns(conn, "letters")
        rows: dict[int, sqlite3.Row] = {}
        for number in sorted(texts):
            text = texts[number]
            if "<Ep" in text:
                raise ValueError(f"Letter {number} text still contains page-break marker")
            if len(text.strip()) < 300:
                raise ValueError(f"Letter {number} text is too short")

            row = conn.execute(
                """
                SELECT id, modern_english
                FROM letters
                WHERE collection = ?
                  AND CAST(letter_number AS INTEGER) = ?
                """,
                (COLLECTION, number),
            ).fetchone()
            if not row:
                raise ValueError(f"Seneca letter {number} not found")
            rows[number] = row

        result = {
            "matched": len(rows),
            "updated": len(rows),
            "dry_run": dry_run,
            "modern_english_preserved": sum(
                1 for row in rows.values() if row["modern_english"]
            ),
        }
        if dry_run:
            return result

        for number, row in rows.items():
            update_cols = ["english_text = ?"]
            params: list[Any] = [texts[number]]
            if "translation_url" in columns:
                update_cols.append("translation_url = ?")
                params.append(wikisource_url(number))
            params.append(row["id"])
            conn.execute(
                f"UPDATE letters SET {', '.join(update_cols)} WHERE id = ?",
                params,
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

    texts = fetch_all_texts()
    result = apply_repaired_texts(args.db, texts, dry_run=args.dry_run)
    mode = "DRY RUN" if args.dry_run else "UPDATED"
    print(f"{mode}: Seneca Gummere source repair")
    print(f"Fetched Wikisource texts: {len(texts)}")
    print(f"Letters matched: {result['matched']}")
    print(f"Letters updated: {result['updated']}")
    print(f"Existing modern-English rows preserved: {result['modern_english_preserved']}")
    print("Old <Ep...> page-break markers removed from repaired source text.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

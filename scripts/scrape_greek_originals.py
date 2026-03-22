#!/usr/bin/env python3
"""
scrape_greek_originals.py
=========================
Fetch original Greek text for major Greek letter collections in roman_letters.db.

Sources investigated and availability summary:
─────────────────────────────────────────────
COLLECTION          TLG#     SOURCE               STATUS
Basil of Caesarea   tlg2040  PerseusDL grc2.xml   ✓ AVAILABLE  (letters 1-368)
Julian the Apostate tlg2003  PerseusDL grc2.xml   ✓ AVAILABLE  (letters 1-83 + frag_89b)
Theodoret           tlg4089  First1KGreek         ✗ Letters NOT in repo (only HE & HR)
Synesius            tlg2006  First1KGreek         ✗ Not in repo
Gregory Nazianzus   tlg2022  First1KGreek         ✗ Only orations (tlg007-011), not letters
Athanasius          tlg2035  First1KGreek         ✗ Only anti-Arian orations, not letters
Chrysostom          tlg2062  First1KGreek         ✗ Not in repo

Perseids/Scaife CTS API: confirms the same gaps — none of the five missing collections
have digitised letter corpora available in open TEI XML.

Patrologia Graeca djvu.txt (Internet Archive / PatrologiaGraeca collection):
All relevant volumes are present (PG 25-28, 32, 37, 52, 66, 83), but the djvu OCR
output is severely corrupted for Greek — mixed Greek/Latin character errors throughout —
and is unsuitable as a source for Greek originals.

Action taken:
  • Download Basil letters 1-368 from PerseusDL → update latin_text for letters 1-325
    (our DB only holds 325; extras 326-368 noted in report).
  • Download Julian letters 1-83 + frag_89b from PerseusDL → update latin_text for
    letters 1-83 (frag_89b mapped to letter 55 which corresponds to the famous
    rescript on Christian teachers, Wright no. 36 / Bidez-Cumont 89b).
  • Mark each updated row with source_url pointing to the raw GitHub XML.

Usage:
  python3 scrape_greek_originals.py [--dry-run]

Author: roman-letters-network project
"""

import argparse
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "roman_letters.db")

BASIL_XML_URL = (
    "https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/"
    "data/tlg2040/tlg004/tlg2040.tlg004.perseus-grc2.xml"
)
BASIL_CACHE = "/tmp/basil_epistulae_grc2.xml"
BASIL_SOURCE_URL = (
    "https://github.com/PerseusDL/canonical-greekLit/blob/master/"
    "data/tlg2040/tlg004/tlg2040.tlg004.perseus-grc2.xml"
)

JULIAN_XML_URL = (
    "https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/"
    "data/tlg2003/tlg013/tlg2003.tlg013.perseus-grc2.xml"
)
JULIAN_CACHE = "/tmp/julian_epistolae_grc2.xml"
JULIAN_SOURCE_URL = (
    "https://github.com/PerseusDL/canonical-greekLit/blob/master/"
    "data/tlg2003/tlg013/tlg2003.tlg013.perseus-grc2.xml"
)

HEADERS = {"User-Agent": "roman-letters-network/1.0 (research project; greek text import)"}


# ─────────────────────────────────────────────────────────────────────────────
# Download helpers
# ─────────────────────────────────────────────────────────────────────────────

def fetch_xml(url: str, cache_path: str, min_size: int = 500_000) -> str:
    """Download XML (or use cache if already present and large enough)."""
    if os.path.exists(cache_path) and os.path.getsize(cache_path) >= min_size:
        print(f"  Using cached file: {cache_path}")
        with open(cache_path, encoding="utf-8") as fh:
            return fh.read()

    print(f"  Downloading: {url}")
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            content = resp.read().decode("utf-8")
    except urllib.error.URLError as exc:
        sys.exit(f"Download failed: {exc}")

    with open(cache_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"  Cached to: {cache_path}  ({len(content):,} bytes)")
    return content


# ─────────────────────────────────────────────────────────────────────────────
# TEI XML text extraction
# ─────────────────────────────────────────────────────────────────────────────

def clean_tei(raw: str) -> str:
    """Strip TEI markup from a letter div and return clean Greek text."""
    # Remove footnote / apparatus notes entirely (keep no content — apparatus is Latin)
    raw = re.sub(r"<note[^>]*>.*?</note>", "", raw, flags=re.DOTALL)
    # Remove page break and milestone markers
    raw = re.sub(r"<pb[^>]*/>", "", raw)
    raw = re.sub(r"<milestone[^>]*/?>", "", raw)
    # Remove gap elements
    raw = re.sub(r"<gap[^>]*>.*?</gap>", "[…]", raw, flags=re.DOTALL)
    raw = re.sub(r"<gap[^>]*/?>", "[…]", raw)
    # Keep text inside <foreign> and <q> tags
    raw = re.sub(r"<foreign[^>]*>(.*?)</foreign>", r"\1", raw, flags=re.DOTALL)
    raw = re.sub(r"<q(?:\s[^>]*)?>", "\"", raw)
    raw = re.sub(r"</q>", "\"", raw)
    # Extract head as [Recipient: …] prefix
    def head_replace(m: re.Match) -> str:
        inner = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        return f"[Πρός: {inner}]\n\n" if inner else ""
    raw = re.sub(r"<head[^>]*>(.*?)</head>", head_replace, raw, flags=re.DOTALL)
    # Strip all remaining XML tags
    raw = re.sub(r"<[^>]+>", "", raw)
    # Normalise whitespace
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def parse_letters(xml: str) -> dict[str, str]:
    """
    Return {letter_n_value: cleaned_greek_text} for every letter div in *xml*.

    Handles both simple 'n="1"' keys and special keys like 'frag_89b'.
    Each letter div is bounded by the next sibling letter div (or end of body).
    """
    # Split on every letter-level div opener to find boundaries
    # Pattern: <div type="textpart" subtype="letter" ... n="...">
    split_pattern = re.compile(
        r'<div\s+type="textpart"\s+subtype="letter"(?:[^>]|\n)*?n="([^"]+)"[^>]*>',
        re.DOTALL,
    )

    positions: list[tuple[int, int, str]] = []  # (start, n_end, n_value)
    for m in split_pattern.finditer(xml):
        positions.append((m.start(), m.end(), m.group(1)))

    results: dict[str, str] = {}
    for idx, (start, content_start, n_val) in enumerate(positions):
        # Content runs from end-of-opener to start of next opener (or end of file)
        content_end = positions[idx + 1][0] if idx + 1 < len(positions) else len(xml)
        raw_block = xml[content_start:content_end]
        text = clean_tei(raw_block)
        if text:
            results[n_val] = text

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Database helpers
# ─────────────────────────────────────────────────────────────────────────────

def db_connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def update_latin_text(
    conn: sqlite3.Connection,
    collection: str,
    letter_number: int,
    greek_text: str,
    source_url: str,
    dry_run: bool,
) -> bool:
    """
    Update latin_text for the matching row.
    Returns True if a row was found and updated (or would be in dry-run).
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT id, latin_text FROM letters WHERE collection = ? AND letter_number = ?",
        (collection, letter_number),
    )
    row = cur.fetchone()
    if row is None:
        return False

    if dry_run:
        return True  # would update

    cur.execute(
        "UPDATE letters SET latin_text = ?, source_url = ? WHERE id = ?",
        (greek_text, source_url, row["id"]),
    )
    conn.commit()
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Per-collection import logic
# ─────────────────────────────────────────────────────────────────────────────

def import_basil(conn: sqlite3.Connection, dry_run: bool) -> dict:
    """Import Basil of Caesarea Greek letters from PerseusDL TEI XML."""
    print("\n[Basil of Caesarea]")
    print(f"  Source: {BASIL_XML_URL}")
    xml = fetch_xml(BASIL_XML_URL, BASIL_CACHE, min_size=1_000_000)
    letters = parse_letters(xml)
    print(f"  Letters parsed from XML: {len(letters)}")

    updated = 0
    skipped_no_db_row = []
    for n_val, text in sorted(letters.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 9999):
        if not n_val.isdigit():
            continue
        letter_num = int(n_val)
        ok = update_latin_text(
            conn, "basil_caesarea", letter_num, text, BASIL_SOURCE_URL, dry_run
        )
        if ok:
            updated += 1
        else:
            skipped_no_db_row.append(letter_num)

    return {
        "collection": "basil_caesarea",
        "xml_letters": len(letters),
        "updated": updated,
        "no_db_row": len(skipped_no_db_row),
        "no_db_row_examples": skipped_no_db_row[:10],
    }


def import_julian(conn: sqlite3.Connection, dry_run: bool) -> dict:
    """
    Import Julian the Apostate Greek letters from PerseusDL TEI XML.

    The XML contains letters n="1"..n="83" (with n="55" absent; instead there is
    n="frag_89b" which is the rescript on Christian teachers, conventionally
    numbered as letter 55 in many editions).  Our DB uses letter_number=55 for
    this fragment, so we map frag_89b → letter_number 55.
    """
    print("\n[Julian the Apostate]")
    print(f"  Source: {JULIAN_XML_URL}")
    xml = fetch_xml(JULIAN_XML_URL, JULIAN_CACHE, min_size=100_000)
    letters = parse_letters(xml)
    print(f"  Letters parsed from XML: {len(letters)}")

    updated = 0
    skipped_no_db_row = []

    # Resolve frag_89b → letter_number 55
    mapping: dict[int, str] = {}
    for n_val, text in letters.items():
        if n_val.isdigit():
            mapping[int(n_val)] = text
        elif n_val == "frag_89b":
            mapping[55] = text  # conventional numbering

    for letter_num, text in sorted(mapping.items()):
        ok = update_latin_text(
            conn, "julian_emperor", letter_num, text, JULIAN_SOURCE_URL, dry_run
        )
        if ok:
            updated += 1
        else:
            skipped_no_db_row.append(letter_num)

    return {
        "collection": "julian_emperor",
        "xml_letters": len(letters),
        "updated": updated,
        "no_db_row": len(skipped_no_db_row),
        "no_db_row_examples": skipped_no_db_row[:10],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Availability report for unavailable collections
# ─────────────────────────────────────────────────────────────────────────────

UNAVAILABLE = {
    "theodoret_cyrrhus": {
        "tlg": "tlg4089",
        "pg": "PG 83",
        "reason": (
            "OpenGreekAndLatin/First1KGreek contains tlg4089 but only has "
            "Historia Ecclesiastica (tlg003) and Historia Religiosa (tlg004) — "
            "not the Epistulae (tlg006).  "
            "PerseusDL canonical-greekLit does not include tlg4089 at all.  "
            "Patrologia Graeca vol. 83 is on Archive.org but the djvu OCR "
            "is too corrupted for Greek originals."
        ),
    },
    "synesius_cyrene": {
        "tlg": "tlg2006",
        "pg": "PG 66",
        "reason": (
            "tlg2006 is absent from First1KGreek, PerseusDL canonical-greekLit, "
            "and Perseids/Scaife CTS.  "
            "Patrologia Graeca vol. 66 is on Archive.org but djvu OCR is unusable.  "
            "The standard critical edition (Garzya 1979) has no open digital Greek text."
        ),
    },
    "gregory_nazianzus": {
        "tlg": "tlg2022",
        "pg": "PG 37",
        "reason": (
            "First1KGreek has tlg2022 but only the five Theological Orations "
            "(tlg007-011) and Christus Patiens (tlg003) — not the Epistulae (tlg001).  "
            "Perseids/Scaife confirms the same set.  "
            "PG vol. 37 is on Archive.org but djvu OCR is unusable."
        ),
    },
    "athanasius_alexandria": {
        "tlg": "tlg2035",
        "pg": "PG 25-28",
        "reason": (
            "First1KGreek has tlg2035 but only the anti-Arian orations "
            "(tlg117/130/131/132), De Incarnatione (tlg002), and De decretis (tlg003) — "
            "not the letters.  "
            "PG vols. 25-28 are on Archive.org but djvu OCR is unusable."
        ),
    },
    "chrysostom": {
        "tlg": "tlg2062",
        "pg": "PG 52",
        "reason": (
            "tlg2062 is absent from First1KGreek, PerseusDL canonical-greekLit, "
            "and all CTS endpoints checked.  "
            "PG vol. 52 is on Archive.org but djvu OCR is unusable."
        ),
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Import original Greek text for major letter collections")
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing to DB")
    args = parser.parse_args()

    dry_run: bool = args.dry_run
    if dry_run:
        print("DRY-RUN MODE — no changes will be written to the database.\n")

    db_path = os.path.abspath(DB_PATH)
    if not os.path.exists(db_path):
        sys.exit(f"Database not found: {db_path}")
    print(f"Database: {db_path}\n")

    conn = db_connect(db_path)

    results = []

    # ── Basil ──────────────────────────────────────────────────────────────
    try:
        r = import_basil(conn, dry_run)
        results.append(r)
    except Exception as exc:
        print(f"  ERROR importing Basil: {exc}")
        results.append({"collection": "basil_caesarea", "updated": 0, "error": str(exc)})

    # ── Julian ─────────────────────────────────────────────────────────────
    try:
        r = import_julian(conn, dry_run)
        results.append(r)
    except Exception as exc:
        print(f"  ERROR importing Julian: {exc}")
        results.append({"collection": "julian_emperor", "updated": 0, "error": str(exc)})

    conn.close()

    # ── Final report ───────────────────────────────────────────────────────
    print("\n" + "=" * 66)
    print("IMPORT REPORT")
    print("=" * 66)

    total_updated = 0
    for r in results:
        col = r["collection"]
        upd = r.get("updated", 0)
        total_updated += upd
        xml_n = r.get("xml_letters", "?")
        no_row = r.get("no_db_row", 0)
        err = r.get("error")
        status = "DRY-RUN" if dry_run else "UPDATED"
        if err:
            print(f"  {col:30s}  ERROR: {err}")
        else:
            print(f"  {col:30s}  {status}: {upd:4d}  (xml had {xml_n}, no DB row for {no_row})")
            if r.get("no_db_row_examples"):
                print(f"    Letters in XML but not in DB: {r['no_db_row_examples']}")

    print(f"\n  Total letters updated: {total_updated}")

    print("\n" + "─" * 66)
    print("COLLECTIONS WITH NO USABLE OPEN-ACCESS GREEK SOURCE:")
    print("─" * 66)
    for coll, info in UNAVAILABLE.items():
        db_count_row = sqlite3.connect(db_path).execute(
            "SELECT COUNT(*) FROM letters WHERE collection = ?", (coll,)
        ).fetchone()
        db_count = db_count_row[0] if db_count_row else "?"
        print(f"\n  {coll}  (TLG: {info['tlg']}, {info['pg']}, DB rows: {db_count})")
        # Word-wrap reason at 70 chars
        words = info["reason"].split()
        line = "    "
        for w in words:
            if len(line) + len(w) + 1 > 74:
                print(line)
                line = "    " + w
            else:
                line += (" " if line != "    " else "") + w
        print(line)

    print("\n" + "=" * 66)
    print("RECOMMENDED NEXT STEPS FOR MISSING COLLECTIONS:")
    print(
        "  • Theodoret / Gregory Naz / Athanasius / Chrysostom / Synesius:")
    print(
        "    The Thesaurus Linguae Graecae (TLG, tlg.uci.edu) holds all these")
    print(
        "    texts but requires a subscription.  If access is available, export")
    print(
        "    the letter corpora as UTF-8 and adapt parse_letters() for the TLG")
    print(
        "    plain-text format (paragraph numbers rather than TEI XML).")
    print(
        "  • Alternatively, the Sources Chrétiennes series has modern critical")
    print(
        "    editions; some volumes are being digitised by BVMM/CAEL projects.")
    print("=" * 66)


if __name__ == "__main__":
    main()

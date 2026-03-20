#!/usr/bin/env python3
"""
Translate newly added papal letters to modern English.
Collections: pelagius_ii (7 untranslated), benedict_i (2), pope_john_iii (1)
Also handles gregory_great MGH Latin letters.

Uses Anthropic API.
"""

import sqlite3
import os
import time
import sys
import subprocess

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
CLAUDE_CLI = '/opt/homebrew/bin/claude'

DELAY = 1.5  # seconds between API calls


PAPAL_SYSTEM = """You are an expert translator of late antique Latin letters. Translate the following papal letter into clear, modern English.

The text is from the Patrologia Latina (Migne's 19th-century edition), OCR'd from a two-column format. The Latin may have some OCR artifacts (e.g., 's' rendered as '$', 'sub' as '8ub', ligatures).

TRANSLATION RULES:
1. Translate the FULL content of the letter — theological arguments, canonical decisions, historical context
2. Convert to natural, accessible modern English (not archaic Victorian style)
3. PRESERVE all proper names (people, places, church offices, councils)
4. ADD brief [context] notes in brackets where helpful for modern readers, e.g.:
   - [the Three Chapters controversy: a 6th-century dispute over whether to condemn three theologians posthumously]
   - [Istrian schism: bishops of Istria who rejected the Second Council of Constantinople (553)]
   - [chorepiscopos: auxiliary bishops serving rural areas]
5. Maintain the letter's formal register (these are official papal communications)
6. Keep paragraph structure
7. The salutation usually identifies sender and recipient — preserve it naturally
8. IGNORE obvious OCR artifacts and footnote markers (sequences like "^", "a)", numbers in brackets)

OUTPUT FORMAT: Just the translated letter text. No preamble like "Here is the translation:"."""


GREGORY_MGH_SYSTEM = """You are an expert translator of late antique Latin letters. Translate the following letter by Pope Gregory the Great (590-604 AD) into clear, modern English.

The Latin text is from the MGH (Monumenta Germaniae Historica) critical edition, OCR'd from a 19th-century scholarly edition. The text contains critical apparatus (footnote markers like letters+parentheses, variant readings, manuscript sigla) mixed with the letter text itself. IGNORE all apparatus: skip lines with "codd.", variant readings like "word] variant", superscript markers, and manuscript abbreviations.

GREGORY'S VOICE: Practical, warm but authoritative — the great administrative pope who reorganized the Western Church during the Lombard invasions. He cared deeply about pastoral work, the poor, liturgy, and the spiritual lives of clergy. His letters deal with church administration, property management, theological disputes, missionary work, and pastoral care across Italy, Spain, Gaul, North Africa, and the East.

TRANSLATION RULES:
1. Translate the FULL letter content — ignore critical apparatus but preserve all actual letter text
2. Convert to clear, accessible modern English
3. PRESERVE all proper names and places (add [context] notes when helpful)
4. ADD brief [context] notes for: named people not widely known, obscure place names, specialized church terminology
5. Maintain Gregory's direct, practical administrative tone
6. The letter summary (in the subject_summary field) describes the letter — use it to understand what the letter is about
7. If the OCR is very poor and large portions are illegible, translate what you can clearly read and summarize the rest based on the summary

OUTPUT FORMAT: Just the translated letter text. No preamble."""


def translate_letter(system_prompt, user_content, ref_id):
    """Call Claude CLI and return translation text."""
    full_prompt = f"{system_prompt}\n\n{user_content}"
    try:
        result = subprocess.run(
            [CLAUDE_CLI, '--print', '-p', full_prompt],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            err = result.stderr.strip()[:200] if result.stderr else '(no stderr)'
            print(f"  ERROR translating {ref_id}: CLI code {result.returncode}: {err}")
            return None
    except subprocess.TimeoutExpired:
        print(f"  ERROR translating {ref_id}: timeout")
        return None
    except Exception as e:
        print(f"  ERROR translating {ref_id}: {e}")
        return None


def translate_collection(conn, collection, system_prompt, limit=None):
    """Translate all untranslated letters in a collection."""
    query = """
        SELECT l.id, l.ref_id, l.subject_summary, l.latin_text, l.english_text,
               s.name as sender_name, r.name as recipient_name, l.year_approx
        FROM letters l
        LEFT JOIN authors s ON l.sender_id = s.id
        LEFT JOIN authors r ON l.recipient_id = r.id
        WHERE l.collection = ? AND (l.modern_english IS NULL OR l.modern_english = '')
        ORDER BY l.letter_number
    """
    if limit:
        query += f" LIMIT {limit}"

    rows = conn.execute(query, (collection,)).fetchall()

    if not rows:
        print(f"  No untranslated letters in {collection}")
        return 0

    print(f"  Translating {len(rows)} letters in {collection}...")
    translated = 0

    for row in rows:
        letter_id, ref_id, summary, latin, english, sender, recipient, year = row

        # Build the user message
        parts = []
        if summary:
            parts.append(f"SUMMARY: {summary}")
        if sender:
            parts.append(f"FROM: {sender}")
        if recipient:
            parts.append(f"TO: {recipient}")
        if year:
            parts.append(f"DATE: approximately {year} AD")
        parts.append("")

        source_text = latin or english or ""
        if not source_text.strip():
            print(f"    Skipping {ref_id}: no text")
            continue

        parts.append(f"LATIN TEXT:\n{source_text[:6000]}")
        user_content = "\n".join(parts)

        text = translate_letter(system_prompt, user_content, ref_id)
        if text and len(text) > 50:
            conn.execute('UPDATE letters SET modern_english = ? WHERE id = ?', (text, letter_id))
            conn.commit()
            translated += 1
            print(f"    ✓ {ref_id} ({len(text)} chars)")
        else:
            print(f"    ✗ {ref_id}: translation failed or too short")

        time.sleep(DELAY)

    return translated


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)

    total = 0

    # 1. Small new papal collections
    for coll in ['pelagius_ii', 'benedict_i', 'pope_john_iii']:
        print(f"\n=== {coll} ===")
        n = translate_collection(conn, coll, PAPAL_SYSTEM)
        total += n
        print(f"  Done: {n} translated")

    # 2. Gregory MGH letters (392 untranslated)
    # Do them in batches of 50 at a time via the limit parameter
    limit_per_run = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    print(f"\n=== gregory_great MGH letters (limit={limit_per_run}) ===")
    n = translate_collection(conn, 'gregory_great', GREGORY_MGH_SYSTEM, limit=limit_per_run)
    total += n
    print(f"  Done: {n} translated")

    # 3. Remaining Venantius Fortunatus (if any)
    print(f"\n=== venantius_fortunatus ===")

    FORTUNATUS_SYSTEM = """You are an expert translator of late antique Latin verse epistles. Translate the following verse letter by Venantius Fortunatus (c.530–600 AD) into clear, modern English prose.

VENANTIUS FORTUNATUS'S VOICE: Charming, warm, and witty — a professional poet who used verse letters as social currency in Merovingian Gaul. His letters are effusive with flattery but genuine in affection, full of wordplay and classical allusions.

TRANSLATION RULES:
1. Translate the FULL content of the poem into English prose
2. Capture all imagery, compliments, requests, and specific details
3. Convert Latin verse to natural modern English prose paragraphs
4. PRESERVE all proper names (people, places, churches, saints)
5. ADD brief [context] notes in brackets for named people, places, and obscure references
6. Keep Fortunatus's warmth and wit

OUTPUT FORMAT: Just the translated letter. No preamble."""

    n = translate_collection(conn, 'venantius_fortunatus', FORTUNATUS_SYSTEM, limit=50)
    total += n
    print(f"  Done: {n} translated")

    print(f"\nTotal translated: {total}")

    # Print status
    print("\nStatus:")
    for coll in ['pelagius_ii', 'benedict_i', 'pope_john_iii', 'gregory_great', 'venantius_fortunatus']:
        row = conn.execute(
            "SELECT COUNT(*), SUM(CASE WHEN modern_english IS NOT NULL THEN 1 ELSE 0 END) FROM letters WHERE collection=?",
            (coll,)
        ).fetchone()
        pct = f"{row[1]*100//row[0]}%" if row[0] and row[1] else "0%"
        print(f"  {coll}: {row[1]}/{row[0]} ({pct})")

    conn.close()


if __name__ == '__main__':
    main()

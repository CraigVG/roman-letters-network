#!/usr/bin/env python3
"""
Translate Libanius Greek letters to modern English using the Claude CLI.

Uses `claude -p` (print mode) to translate batches of Greek letters from the DB.
Greek text is stored in the latin_text column.

Usage:
  python3 translate_libanius.py              # Translate 50 letters (default)
  python3 translate_libanius.py --batch 100  # Translate 100 letters
  python3 translate_libanius.py --offset 50  # Skip first 50 untranslated letters
  python3 translate_libanius.py --stats      # Show progress only
"""

import sqlite3
import subprocess
import sys
import time
import re
import os

DB_PATH = "/Users/drillerdbmacmini/Documents/GitHub/roman-letters-network/data/roman_letters.db"
CLAUDE_CLI = "/opt/homebrew/bin/claude"


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def get_stats():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM letters WHERE collection='libanius'").fetchone()[0]
    has_greek = conn.execute("SELECT COUNT(*) FROM letters WHERE collection='libanius' AND latin_text IS NOT NULL AND latin_text != ''").fetchone()[0]
    has_english = conn.execute("SELECT COUNT(*) FROM letters WHERE collection='libanius' AND english_text IS NOT NULL AND english_text != ''").fetchone()[0]
    conn.close()
    return total, has_greek, has_english


def get_letters_needing_translation(batch_size=50, offset=0):
    conn = get_connection()
    cur = conn.execute("""
        SELECT id, letter_number, latin_text, subject_summary
        FROM letters
        WHERE collection='libanius'
          AND latin_text IS NOT NULL
          AND latin_text != ''
          AND (english_text IS NULL OR english_text = '')
        ORDER BY letter_number
        LIMIT ? OFFSET ?
    """, (batch_size, offset))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def translate_via_claude_cli(greek_text, letter_number, recipient):
    """Translate using the claude CLI in print (-p) mode."""
    context = f"Letter {letter_number}"
    if recipient:
        context += f" to {recipient}"

    prompt = f"""You are translating a Greek letter by Libanius of Antioch (314-394 AD), the famous late antique rhetorician and sophist. This is {context} from his collection of surviving letters. He wrote from Antioch on the Orontes in Roman Syria.

Translate this Greek text into clear, fluent modern English. Preserve his rhetorical sophistication and the personal, epistolary tone. Render proper names in their conventional English or Latinized forms where known (e.g., Κλέαρχος = Clearchus, Θεμίστιος = Themistius, Ἰουλιανός = Julian). If a passage is corrupt or unclear, translate your best reading.

Greek text:
{greek_text}

Provide only the English translation, no preamble or commentary."""

    try:
        result = subprocess.run(
            [CLAUDE_CLI, "-p", prompt],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            print(f"    CLI error: {result.stderr[:200]}")
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"    Timeout for letter {letter_number}")
        return None
    except Exception as e:
        print(f"    Exception: {e}")
        return None


def save_translation(letter_id, english_text):
    conn = get_connection()
    conn.execute("""
        UPDATE letters
        SET english_text = ?,
            translation_source = 'ai_translated'
        WHERE id = ?
    """, (english_text, letter_id))
    conn.commit()
    conn.close()


def main():
    args = sys.argv[1:]

    if '--stats' in args:
        total, has_greek, has_english = get_stats()
        print(f"Libanius letters in DB: {total}")
        print(f"  With Greek text: {has_greek}")
        print(f"  With English translation: {has_english}")
        print(f"  Still needing translation: {has_greek - has_english}")
        return

    batch_size = 50
    offset = 0

    if '--batch' in args:
        idx = args.index('--batch')
        batch_size = int(args[idx + 1])

    if '--offset' in args:
        idx = args.index('--offset')
        offset = int(args[idx + 1])

    total, has_greek, has_english = get_stats()
    remaining = has_greek - has_english
    print(f"Libanius translation status: {has_english}/{has_greek} translated, {remaining} remaining")
    print(f"Translating batch of {batch_size} (offset={offset})...\n")

    letters = get_letters_needing_translation(batch_size, offset)
    if not letters:
        print("No untranslated letters found.")
        return

    translated = 0
    errors = 0

    for i, letter in enumerate(letters):
        letter_id = letter['id']
        letter_number = letter['letter_number']
        greek_text = letter['latin_text']  # Greek stored in latin_text column
        subject = letter['subject_summary'] or ''

        # Extract recipient from subject_summary
        recipient = ''
        if subject.startswith('Letter to '):
            recipient = subject[len('Letter to '):]

        print(f"[{i+1}/{len(letters)}] Letter {letter_number} ({recipient[:30] if recipient else 'unknown recipient'})...", end=' ', flush=True)

        english = translate_via_claude_cli(greek_text, letter_number, recipient)

        if english:
            save_translation(letter_id, english)
            translated += 1
            print(f"OK ({len(english)} chars)")
        else:
            errors += 1
            print(f"FAILED")
            if errors >= 3:
                print("\nToo many consecutive errors. Stopping.")
                break

        # Small pause between calls to be polite
        if i < len(letters) - 1:
            time.sleep(0.5)

    print(f"\nDone: {translated} translated, {errors} errors")

    total, has_greek, has_english = get_stats()
    print(f"New total: {has_english}/{has_greek} Libanius letters translated")


if __name__ == '__main__':
    main()

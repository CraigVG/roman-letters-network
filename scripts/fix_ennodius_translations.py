#!/usr/bin/env python3
"""
Re-translate 57 Ennodius letters that have summary/placeholder translations
instead of full modern English translations.

These letters have a Latin/modern-english length ratio > 3.0, meaning
the current 'translation' is a paraphrase summary, not an actual translation.

Ennodius's style: ornate, literary, elaborate rhetorical flourishes.
"""

import sqlite3
import subprocess
import time
import sys
import os

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

DB_PATH = "data/roman_letters.db"

LETTER_IDS = [
    3059, 3306, 3092, 3307, 3233, 3230, 3216, 3040, 3268, 3068,
    3187, 3299, 3305, 3224, 3231, 3221, 3287, 3135, 3270, 3083,
    3308, 3158, 3303, 3304, 3309, 3019, 3261, 3164, 3232, 3202,
    3311, 3096, 3125, 3136, 3196, 3036, 3055, 3121, 3134, 3161,
    3190, 3223, 3053, 3088, 3100, 3257, 3262, 3078, 3102, 3157,
    3047, 3162, 3249, 3250, 3302, 3218, 3263,
]

SYSTEM_PROMPT = """You are translating letters by Ennodius of Pavia (c. 473–521 AD),
a deacon and later bishop of Pavia in Ostrogothic Italy.

Ennodius is famous for his ornate, highly rhetorical Latin style — elaborate metaphors,
extended flourishes, self-conscious literary display. His letters are never brief or
simple in their expression, even when the underlying message is short.

TRANSLATION RULES:
1. Translate the FULL Latin text — do not summarize or abridge.
2. Capture Ennodius's elaborate rhetorical style in natural modern English.
3. Keep honorifics: "Your Greatness", "Your Magnificence", "Your Holiness", etc.
4. Include a header block:
   From: [Name, role in city]
   To: [Name, role/title]
   Date: ~[year] AD
   Context: [One sentence on what makes this letter notable]
5. Follow the header with the full translation.
6. Do NOT add "Farewell." unless it appears in the Latin as "Vale" or similar.
7. Voice: well-written literary nonfiction — clear but not dumbed down.
   Think Mary Beard or Tom Holland writing about late antiquity.
8. Bracketed notes [like this] for things a modern reader needs explained.
9. Do NOT start translation with "Ennodius to X." unless the Latin opens that way.

IMPORTANT: The current translation in the database is just a placeholder summary.
Translate the full Latin text completely."""


def translate_with_sdk(client, full_prompt: str) -> str:
    """Translate using the Anthropic SDK."""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": full_prompt}],
    )
    return response.content[0].text.strip()


def translate_with_cli(full_prompt: str) -> str:
    """Translate using the claude CLI tool."""
    result = subprocess.run(
        ['claude', '--print', '--model', 'claude-sonnet-4-6'],
        input=SYSTEM_PROMPT + "\n\n" + full_prompt,
        capture_output=True, text=True, timeout=180
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    raise RuntimeError(f"CLI failed (rc={result.returncode}): {result.stderr[:300]}")


def translate_letter(client, latin_text: str, existing_modern: str, ref_id: str) -> str:
    """Translate a single letter using Claude (SDK or CLI fallback)."""

    prompt = f"""Translate this letter by Ennodius of Pavia from Latin to modern English.

Reference: {ref_id}

LATIN TEXT:
{latin_text}

EXISTING (POOR) TRANSLATION (this is just a placeholder summary — IGNORE IT and translate the Latin fully):
{existing_modern[:300]}...

Please provide a complete, full translation of the Latin text above."""

    if client is not None:
        return translate_with_sdk(client, prompt)
    else:
        return translate_with_cli(prompt)


def main():
    client = None
    if HAS_ANTHROPIC and os.environ.get('ANTHROPIC_API_KEY'):
        client = anthropic.Anthropic()
        print("Using Anthropic SDK")
    else:
        print("ANTHROPIC_API_KEY not set — using claude CLI fallback")
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    # Get letters needing re-translation
    placeholders = ",".join("?" * len(LETTER_IDS))
    cur.execute(f"""
        SELECT id, ref_id, latin_text, modern_english
        FROM letters
        WHERE id IN ({placeholders})
        ORDER BY id
    """, LETTER_IDS)

    letters = cur.fetchall()
    print(f"Found {len(letters)} Ennodius letters to re-translate")

    success = 0
    errors = 0

    for i, (letter_id, ref_id, latin_text, modern_english) in enumerate(letters):
        print(f"\n[{i+1}/{len(letters)}] Translating {ref_id} (ID={letter_id})...")
        print(f"  Latin: {len(latin_text)} chars → Current modern: {len(modern_english)} chars")

        if not latin_text or len(latin_text.strip()) < 50:
            print(f"  SKIP: no Latin text")
            continue

        try:
            new_translation = translate_letter(client, latin_text, modern_english, ref_id)

            cur.execute("""
                UPDATE letters SET modern_english = ? WHERE id = ?
            """, (new_translation, letter_id))
            conn.commit()

            print(f"  OK: new translation = {len(new_translation)} chars")
            success += 1

            # Rate limiting
            time.sleep(1)

        except Exception as e:
            print(f"  ERROR: {e}")
            errors += 1
            time.sleep(5)
            continue

    conn.close()
    print(f"\n{'='*50}")
    print(f"Done: {success} translated, {errors} errors")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()

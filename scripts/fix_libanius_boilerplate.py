#!/usr/bin/env python3
"""
Fix Libanius letters 329-831 that received generic boilerplate translations.

These letters were bulk-generated with template phrases like:
  - "I write to you not because I have any pressing news..."
  - "I bring to your attention a matter that demands your intervention..."
  - "Your latest letter was a welcome arrival..."
  etc.

This script re-translates them from the original Greek (stored in latin_text)
using the same style as letters 1-167: direct, literate, no header block.

Libanius (314-393 AD): urbane pagan rhetorician of Antioch, teacher of Julian,
friend of emperors and governors. His letters: witty, literary, often very brief,
full of classical allusion. His Greek is polished Atticizing prose.

Run: python3 scripts/fix_libanius_boilerplate.py [--start N] [--count N] [--dry-run]
"""

import sqlite3
import os
import sys
import json
import time
import argparse
import subprocess

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

# Boilerplate openers that indicate a letter needs re-translation
BOILERPLATE_OPENERS = [
    'Your latest letter was a welcome arrival',
    'I bring to your attention a matter that demands your intervention',
    'I write to you not because I have any pressing news',
    'The management of public affairs is both the noblest',
    'Family is the bedrock upon which everything else is built',
    'Your letter brought me news that I received with mixed emotions',
    'The state of education in our cities is a matter',
    'I write to commend someone to your good graces',
]

SYSTEM_PROMPT = """Translate these Libanius letters from Greek to modern English. Libanius (314-393 AD) was an urbane pagan rhetorician of Antioch — witty, self-conscious, brief.

RULES:
- Translate faithfully from the Greek; do not summarize or fabricate
- Modern literate English; no archaisms; preserve his brevity
- Greek names as given; [bracketed notes] only where essential (1-2 per letter max)
- The Greek may have OCR noise (embedded line numbers, HTML entities like &#x003C;) — read through it
- Format: "To [Name]. ([date])\n\n[letter text]" — no From:/To:/Context: header block

OUTPUT: Return ONLY a JSON array: [{"id": <id>, "translation": "<text>"}, ...]"""


def is_boilerplate(modern_english):
    """Check if a modern_english translation is boilerplate."""
    if not modern_english:
        return True
    text = modern_english
    # Strip header if present
    if text.startswith('From:'):
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if line.strip() == '' and i >= 3:
                text = '\n'.join(lines[i + 1:]).strip()
                break
    return any(text.startswith(opener) for opener in BOILERPLATE_OPENERS)


def get_boilerplate_letters(conn, limit=None, offset=0):
    """Fetch all Libanius letters 168+ with boilerplate translations."""
    cur = conn.cursor()
    cur.execute('''
        SELECT l.id, l.letter_number, l.year_approx, l.latin_text,
               l.modern_english,
               s.name AS sender_name, r.name AS recipient_name
        FROM letters l
        LEFT JOIN authors s ON l.sender_id = s.id
        LEFT JOIN authors r ON l.recipient_id = r.id
        WHERE l.collection = 'libanius'
          AND l.letter_number >= 168
        ORDER BY l.letter_number
    ''')
    rows = cur.fetchall()

    boilerplate = [
        {
            'id': row[0],
            'letter_number': row[1],
            'year_approx': row[2],
            'greek': row[3] or '',
            'modern_english': row[4] or '',
            'sender': row[5],
            'recipient': row[6],
        }
        for row in rows
        if is_boilerplate(row[4])
    ]

    # Apply offset/limit
    boilerplate = boilerplate[offset:]
    if limit:
        boilerplate = boilerplate[:limit]
    return boilerplate


def build_batch_prompt(letters):
    """Build a prompt for translating a batch of letters."""
    lines = []
    lines.append("Translate the following Libanius letters from Greek into modern English.")
    lines.append("Return a JSON array: [{\"id\": <id>, \"translation\": \"<text>\"}, ...]")
    lines.append("")

    for letter in letters:
        greek = (letter['greek'] or '')[:3000]  # Libanius letters are short
        year = letter['year_approx'] or 'unknown'
        recipient = letter['recipient'] or 'unknown'
        lines.append(f"--- Letter {letter['letter_number']} (ID: {letter['id']}) ---")
        lines.append(f"Recipient: {recipient} | Date: ~{year} AD")
        lines.append(f"Greek text:")
        lines.append(greek)
        lines.append("")

    return '\n'.join(lines)


def translate_batch_cli(letters, dry_run=False):
    """Translate a batch of letters using the Claude CLI."""
    prompt = build_batch_prompt(letters)
    full_prompt = SYSTEM_PROMPT + "\n\n" + prompt

    if dry_run:
        print(f"  [DRY RUN] Would translate {len(letters)} letters via CLI")
        print(f"  Prompt length: {len(full_prompt)} chars")
        return []

    print(f"  Calling Claude CLI for {len(letters)} letters...")
    result = subprocess.run(
        ['claude', '--print'],
        input=full_prompt,
        capture_output=True,
        text=True,
        timeout=600
    )

    if result.returncode != 0:
        raise RuntimeError(f"CLI failed (rc={result.returncode}): {result.stderr[:500]}")

    output = result.stdout.strip()

    # Extract JSON from output
    # Sometimes claude wraps JSON in markdown code blocks
    if '```json' in output:
        start = output.index('```json') + 7
        end = output.index('```', start)
        output = output[start:end].strip()
    elif '```' in output:
        start = output.index('```') + 3
        end = output.index('```', start)
        output = output[start:end].strip()

    # Find JSON array
    bracket_start = output.find('[')
    bracket_end = output.rfind(']')
    if bracket_start != -1 and bracket_end != -1:
        output = output[bracket_start:bracket_end + 1]

    try:
        translations = json.loads(output)
        return translations
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        print(f"  Output (first 500): {output[:500]}")
        return []


def save_translations(conn, translations):
    """Save translations to the database."""
    cur = conn.cursor()
    saved = 0
    for t in translations:
        letter_id = t.get('id')
        text = t.get('translation', '').strip()
        if letter_id and text and len(text) > 30:
            cur.execute(
                'UPDATE letters SET modern_english = ? WHERE id = ?',
                (text, letter_id)
            )
            saved += 1
    conn.commit()
    return saved


def main():
    parser = argparse.ArgumentParser(description='Fix Libanius boilerplate translations')
    parser.add_argument('--start', type=int, default=0,
                        help='Start from this offset into the boilerplate list')
    parser.add_argument('--count', type=int, default=None,
                        help='Max letters to process (default: all)')
    parser.add_argument('--batch-size', type=int, default=5,
                        help='Letters per API call (default: 20)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without calling API or saving')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")

    letters = get_boilerplate_letters(conn, limit=args.count, offset=args.start)
    print(f"Found {len(letters)} boilerplate letters to re-translate")

    if not letters:
        print("Nothing to do.")
        conn.close()
        return

    # Show a sample
    print(f"First: letter {letters[0]['letter_number']} (ID {letters[0]['id']})")
    print(f"Last:  letter {letters[-1]['letter_number']} (ID {letters[-1]['id']})")
    print()

    total_saved = 0
    batch_size = args.batch_size

    for i in range(0, len(letters), batch_size):
        batch = letters[i:i + batch_size]
        batch_nums = [str(b['letter_number']) for b in batch]
        print(f"Batch {i // batch_size + 1}: letters {batch_nums[0]}-{batch_nums[-1]} ({len(batch)} letters)")

        try:
            translations = translate_batch_cli(batch, dry_run=args.dry_run)

            if dry_run := args.dry_run:
                print(f"  [DRY RUN] Skipping save")
                continue

            if not translations:
                print(f"  WARNING: No translations returned for this batch")
                continue

            saved = save_translations(conn, translations)
            total_saved += saved
            print(f"  Saved {saved}/{len(batch)} translations")

            # Brief pause between batches
            if i + batch_size < len(letters):
                time.sleep(2)

        except Exception as e:
            print(f"  ERROR in batch: {e}")
            print(f"  Continuing with next batch...")
            time.sleep(5)

    print(f"\nDone. Total saved: {total_saved}")
    conn.close()


if __name__ == '__main__':
    main()

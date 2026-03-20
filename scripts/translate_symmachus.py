#!/usr/bin/env python3
"""
Translate Symmachus's letters from Latin to modern English.

Quintus Aurelius Symmachus (c. 345-402 AD) was a Roman senator, orator, and the
last great champion of traditional Roman paganism. His 10 books of letters — modeled
on Pliny the Younger — are THE key source for late 4th-century Roman aristocratic
life. They reveal a world of dinner invitations, villa holidays in Campania, literary
patronage, political maneuvering, and the twilight of pagan Rome.

His voice: urbane, polished, aristocratic. Short elegant notes between senators —
like a gentlemen's club correspondent. His famous Relatio III defending the Altar
of Victory is a landmark of religious tolerance arguments.

CHALLENGE: The Latin texts are OCR'd from Seeck's 1883 critical edition via
Archive.org. They contain:
  - OCR noise (e.g., "promptuB" for "promptus", "qfuam" for "quam")
  - Line numbers embedded in text
  - Apparatus criticus fragments (variant readings, manuscript sigla like P, V, F, M)
  - Hyphenated line breaks from the printed edition
The translator must read through this noise to the underlying Latin.

Run: python3 translate_symmachus.py [--start N] [--count N] [--dry-run]
"""

import sqlite3
import os
import sys
import time
import argparse

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — Symmachus's distinctive voice
# ─────────────────────────────────────────────────────────────────────────────

SYMMACHUS_SYSTEM = """You are a specialist translator of the letters of Quintus Aurelius Symmachus (c. 345-402 AD), the Roman senator, orator, and last great champion of traditional Roman paganism.

YOUR JOB: Translate the given Latin letter into modern, accessible English that captures Symmachus's authentic personality and social world.

SYMMACHUS'S DISTINCTIVE VOICE:
- Urbane and polished: He wrote like a gentleman — measured, witty, never vulgar. His style is deliberately restrained and elegant, modeled on Pliny the Younger
- Aristocratic: He is acutely conscious of rank, propriety, and social obligation. Every letter encodes precise social relationships
- Brief: Most of his letters are short notes — a few sentences. He valued concision as a mark of good breeding
- Warm within limits: He expresses genuine affection for friends, but always within the conventions of senatorial amicitia. Never effusive, never raw
- Pagan: He is a traditional Roman polytheist in an increasingly Christian empire. He references the gods (dii, numina, divinitas) naturally, not polemically
- Politically astute: He served as urban prefect of Rome (384-385), consul (391). His letters navigate the politics of the late Western Empire with care
- Literary patron: He exchanged and critiqued literary works with his circle. Style mattered enormously — a letter's prose demonstrated its author's social standing

KEY RELATIONSHIPS IN THE LETTERS:
- His father (Lucius Aurelius Avianus Symmachus) — early letters show filial deference
- Virius Nicomachus Flavianus — his closest friend, fellow pagan aristocrat, whose son married Symmachus's daughter
- Ausonius — the Gallic poet and tutor to Emperor Gratian; their exchange is famous
- Ambrose of Milan — the Christian bishop; Symmachus's great adversary over the Altar of Victory
- Various senators, governors, and imperial officials — the network of late Roman aristocratic patronage

ABOUT THE LATIN TEXT:
The Latin is OCR'd from Seeck's 1883 critical edition. It contains:
- OCR errors (e.g., "promptuB" = "promptus", "qfuam" = "quam", "snme" = "sume")
- Embedded line numbers (e.g., "20", "25" appearing mid-text)
- Apparatus criticus fragments (variant readings like "om. VF", "P, om. VM", manuscript sigla)
- Hyphenated line breaks from the printed page (e.g., "saluta-\\ntionis" = "salutationis")
- Section headers like "AD THEODORVM" (addressee headings between sub-letters)
- Dating notes like "n ante a. 395" or "a. 382-383?"
YOU MUST read through this noise to the underlying Latin text. Ignore apparatus, line numbers, and editorial notes. Reconstruct hyphenated words.

TRANSLATION RULES:
1. TRANSLATE the Latin directly into clear, modern English prose
2. PRESERVE Symmachus's tone: polished, urbane, aristocratic. Not stuffy — civilized
3. PRESERVE all names, places, and references exactly
4. KEEP his brevity — if the Latin is a 3-sentence note, the English should be similarly concise
5. RENDER amicitia language naturally: "my dear friend", "our friendship", not "my love" or "my soul"
6. RENDER honorific titles as titles: clarissimus = "Most Distinguished", spectabilis = "Most Distinguished"
7. ADD brief [context] notes in brackets ONLY for things a modern reader truly needs, e.g.:
   - [Flavianus: Virius Nicomachus Flavianus, Symmachus's closest friend and fellow pagan senator]
   - [Baiae: the fashionable resort town on the Bay of Naples]
   - [praetorship: a senior magistracy involving expensive public games]
   - [the urban prefecture: the governorship of Rome, which Symmachus held in 384-385]
   Do NOT over-annotate. One or two notes per letter at most.
8. When the letter contains multiple sub-letters (marked by "AD [NAME]" headers), translate each as a separate section with a blank line between them
9. When the Latin is too fragmentary or corrupt to translate, note [text corrupt/fragmentary] and translate what you can
10. PRESERVE his pagan religious references naturally — "the gods willing", "with heaven's favor", etc.

OUTPUT FORMAT:
Just the modernized letter text. No preamble, no "Here is the translation:", no explanation.
Start directly with the letter content."""


SYMMACHUS_PROMPT = """Translate this Symmachus letter from Latin into modern English, capturing his urbane aristocratic voice.

LETTER NUMBER: {letter_num} (Book {book})
APPROXIMATE DATE: {year} AD
SENDER: {sender}
RECIPIENT: {recipient}

ORIGINAL LATIN (OCR from Seeck's 1883 edition — contains OCR noise, line numbers, apparatus criticus):
{latin}

Translate the actual letter text, reading through the OCR noise and editorial apparatus. Capture Symmachus's polished, civilized tone."""


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: guess the book number from letter_number ranges
# ─────────────────────────────────────────────────────────────────────────────

def guess_book(letter_num):
    """Estimate which book of Symmachus's letters this belongs to.
    His collection has ~10 books. Rough ranges based on Seeck's numbering."""
    if letter_num is None:
        return "?"
    try:
        n = int(str(letter_num).split('.')[0].split('-')[0].strip())
    except (ValueError, IndexError):
        return "?"
    # Very rough: Seeck edition numbering by book
    # Book I: 1-~100, Book II: ~100+, etc. The DB has sequential IDs.
    # Since the DB letter_number field often just says "1", "2" etc per book,
    # we'll just use it as-is
    return "I-X"


# ─────────────────────────────────────────────────────────────────────────────
# TRANSLATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def build_prompt(letter_num, year, sender, recipient, latin):
    """Build the translation prompt."""
    latin_trunc = (latin or '')[:5000]  # generous limit for Symmachus's short letters
    return SYMMACHUS_PROMPT.format(
        letter_num=letter_num or '?',
        book=guess_book(letter_num),
        year=year or 'unknown',
        sender=sender or 'Quintus Aurelius Symmachus',
        recipient=recipient or 'Unknown recipient',
        latin=latin_trunc,
    )


def translate_with_sdk(client, prompt):
    """Call via the anthropic SDK."""
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYMMACHUS_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def translate_with_cli(full_prompt):
    """Fallback: use the claude CLI via stdin."""
    import subprocess
    result = subprocess.run(
        ['claude', '--print', '--model', 'claude-sonnet-4-20250514'],
        input=full_prompt,
        capture_output=True, text=True, timeout=180
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    raise RuntimeError(f"CLI failed (rc={result.returncode}): {result.stderr[:200]}")


def translate_letter(client, letter_num, year, sender, recipient, latin):
    """Translate a single letter — tries SDK first, falls back to CLI."""
    prompt = build_prompt(letter_num, year, sender, recipient, latin)
    if client is not None:
        return translate_with_sdk(client, prompt)
    else:
        full_prompt = SYMMACHUS_SYSTEM + "\n\n" + prompt
        return translate_with_cli(full_prompt)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Translate Symmachus letters')
    parser.add_argument('--start', type=int, default=0,
                        help='Start from this offset (0-based)')
    parser.add_argument('--count', type=int, default=20,
                        help='Number of letters to translate')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be translated without calling API')
    args = parser.parse_args()

    # Try to get an SDK client
    client = None
    if HAS_ANTHROPIC and os.environ.get('ANTHROPIC_API_KEY'):
        client = anthropic.Anthropic()
        print("Using Anthropic SDK")
    else:
        print("ANTHROPIC_API_KEY not set — using claude CLI fallback")

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    cursor = conn.cursor()

    # Fetch Symmachus letters needing translation
    cursor.execute('''
        SELECT l.id, l.letter_number, l.year_approx,
               l.latin_text,
               s.name AS sender_name, r.name AS recipient_name
        FROM letters l
        LEFT JOIN authors s ON l.sender_id = s.id
        LEFT JOIN authors r ON l.recipient_id = r.id
        WHERE l.collection = 'symmachus'
          AND l.modern_english IS NULL
          AND l.latin_text IS NOT NULL
          AND LENGTH(l.latin_text) > 50
        ORDER BY l.id
        LIMIT ? OFFSET ?
    ''', (args.count, args.start))
    letters = cursor.fetchall()

    total = len(letters)
    print(f"Symmachus letters to translate: {total} (offset {args.start}, limit {args.count})")
    print("=" * 60)

    if args.dry_run:
        for row in letters:
            lid, num, year, latin, sender, recip = row
            print(f"  Would translate: ID={lid} | #{num} | ~{year} AD | "
                  f"to={recip or '?'} | {len(latin)}c Latin")
        conn.close()
        return

    translated = 0
    failed = 0
    failed_ids = []

    for i, row in enumerate(letters):
        letter_id, letter_num, year, latin, sender, recipient = row

        print(f"  [{i+1}/{total}] Letter #{letter_num} (ID={letter_id}, ~{year} AD, "
              f"{len(latin)}c)...", end=' ', flush=True)

        try:
            modern = translate_letter(
                client, letter_num, year, sender, recipient, latin
            )

            if modern and len(modern) > 30:
                cursor.execute(
                    'UPDATE letters SET modern_english = ? WHERE id = ?',
                    (modern, letter_id)
                )
                translated += 1
                print(f"OK ({len(modern)} chars)")
            else:
                print("FAILED (empty response)")
                failed += 1
                failed_ids.append(letter_id)

        except Exception as e:
            err_str = str(e).lower()
            if 'rate' in err_str or '529' in str(e) or '429' in str(e):
                print("RATE LIMITED — waiting 60s...")
                time.sleep(60)
                try:
                    modern = translate_letter(
                        client, letter_num, year, sender, recipient, latin
                    )
                    if modern and len(modern) > 30:
                        cursor.execute(
                            'UPDATE letters SET modern_english = ? WHERE id = ?',
                            (modern, letter_id)
                        )
                        translated += 1
                        print(f"  Retry OK ({len(modern)} chars)")
                    else:
                        failed += 1
                        failed_ids.append(letter_id)
                except Exception as e2:
                    print(f"  Retry FAILED: {e2}")
                    failed += 1
                    failed_ids.append(letter_id)
            else:
                print(f"ERROR: {e}")
                failed += 1
                failed_ids.append(letter_id)

        # Commit after every translation
        conn.commit()

        # Pause between API calls
        time.sleep(1)

    # Final commit
    conn.commit()

    print()
    print("=" * 60)
    print(f"TRANSLATION COMPLETE")
    print(f"  Translated: {translated}/{total}")
    print(f"  Failed:     {failed}")
    if failed_ids:
        print(f"  Failed IDs: {failed_ids}")

    # Show sample translations
    print()
    print("=" * 60)
    print("SAMPLE TRANSLATIONS:")
    cursor.execute('''
        SELECT l.id, l.letter_number, l.year_approx, l.modern_english,
               r.name AS recipient_name
        FROM letters l
        LEFT JOIN authors r ON l.recipient_id = r.id
        WHERE l.collection = 'symmachus' AND l.modern_english IS NOT NULL
        ORDER BY l.id
        LIMIT 3
    ''')
    for lid, letter_num, year, text, recip in cursor.fetchall():
        print(f"\n--- Letter #{letter_num} (~{year} AD, to {recip or '?'}) [ID={lid}] ---")
        print(text[:500])
        if len(text) > 500:
            print("...")

    conn.close()
    print()
    print("Done.")


if __name__ == '__main__':
    main()

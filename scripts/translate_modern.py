#!/usr/bin/env python3
"""
Translate late antique letters into modern, accessible English.

Late antique letters have distinctive features that need translation:

EPISTOLARY CONVENTIONS:
- Elaborate greetings: "Augustine sends greeting in the Lord" → just context
- Formulaic closings: "May God keep you safe" → natural endings
- Honorifics: "Your Holiness", "Your Excellency", "my venerable lord" → use names
- Self-deprecation: "my humble self" → "I"
- Third-person self-reference: "your servant Augustine" → "I"

RHETORICAL STYLE:
- Heavy biblical allusion and quotation — needs context notes
- Elaborate metaphors drawn from classical education
- Periodic sentences (very long, nested clauses) → break into shorter sentences
- Formal register throughout → mix of conversational and clear prose

CULTURAL CONTEXT THAT NEEDS EXPLANATION:
- Church hierarchy (bishop, metropolitan, exarch, subdeacon)
- Roman administrative terms (patrician, prefect, comes)
- Theological controversies (Arianism, Donatism, Pelagianism)
- Geographic references to provinces and dioceses

The goal: Make these read like a modern person would write an email about the same
topics. Keep the substance, lose the Victorian translation style and ancient formality.
"""

import sqlite3
import os
import re
import json
import subprocess
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

# System prompt for the translation agent
TRANSLATION_SYSTEM = """You are a specialist in translating late antique Roman letters into modern, accessible English.

You are given a letter from the late Roman Empire (300-600 AD), either in a Victorian-era English translation or in Latin. Your job is to rewrite it in clear, natural modern English that any educated person today could understand.

RULES:
1. PRESERVE all factual content, names, places, and specific details
2. CONVERT formal/archaic language to natural modern English
3. BREAK long periodic sentences into shorter, clearer ones
4. REPLACE Victorian translation artifacts ("thou", "hath", "wherefore") with modern equivalents
5. SIMPLIFY elaborate greetings/closings but keep the sender-recipient relationship clear
6. ADD brief [context] notes in brackets for terms a modern reader wouldn't know, e.g.:
   - "[Arianism was a theological movement that denied Christ's divinity]"
   - "[The Exarch governed Italy on behalf of the Byzantine Emperor]"
   - "[Hippo Regius was a city in modern-day Algeria]"
7. Keep it CONCISE — if the original is 500 words of rhetoric making a simple point, 200 clear words is fine
8. TONE: Imagine the letter writer sending this as a thoughtful email today. Maintain their personality and emotion, but drop the performative formality.

OUTPUT FORMAT: Just the modernized text. No preamble or explanation."""

TRANSLATION_PROMPT_BOTH = """Translate this late antique letter into modern, accessible English.
You have BOTH the original Latin and a 19th-century English translation. Use both to produce the best modern version — the Latin for accuracy, the English for meaning.

SENDER: {sender}
RECIPIENT: {recipient}
COLLECTION: {collection}
APPROXIMATE DATE: {year} AD

ORIGINAL LATIN:
{latin}

19TH-CENTURY ENGLISH TRANSLATION:
{english}

Rewrite this in clear, modern English. Add brief [context] notes where needed for modern readers."""

TRANSLATION_PROMPT_SINGLE = """Translate this late antique letter into modern, accessible English:

SENDER: {sender}
RECIPIENT: {recipient}
COLLECTION: {collection}
APPROXIMATE DATE: {year} AD

{source_label}:
{text}

Rewrite this in clear, modern English. Add brief [context] notes where needed for modern readers."""


def translate_with_claude(english, latin, sender, recipient, collection, year):
    """Call Claude API to translate a letter to modern English.
    Uses both Latin original and English translation when available."""
    if english and latin:
        prompt = TRANSLATION_PROMPT_BOTH.format(
            sender=sender or "Unknown",
            recipient=recipient or "Unknown",
            collection=collection.replace('_', ' ').title(),
            year=year or "Unknown",
            latin=latin[:3000],
            english=english[:3000],
        )
    elif english:
        prompt = TRANSLATION_PROMPT_SINGLE.format(
            sender=sender or "Unknown",
            recipient=recipient or "Unknown",
            collection=collection.replace('_', ' ').title(),
            year=year or "Unknown",
            source_label="19TH-CENTURY ENGLISH TRANSLATION",
            text=english[:4000],
        )
    else:
        prompt = TRANSLATION_PROMPT_SINGLE.format(
            sender=sender or "Unknown",
            recipient=recipient or "Unknown",
            collection=collection.replace('_', ' ').title(),
            year=year or "Unknown",
            source_label="ORIGINAL LATIN",
            text=latin[:4000],
        )

    # Use the Anthropic API via python
    try:
        import anthropic
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=TRANSLATION_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except ImportError:
        # Fall back to CLI
        return translate_with_cli(prompt)
    except Exception as e:
        print(f"  API error: {e}")
        return None


def translate_with_cli(prompt):
    """Fallback: use claude CLI if anthropic package not available."""
    try:
        full_prompt = TRANSLATION_SYSTEM + "\n\n" + prompt
        result = subprocess.run(
            ['claude', '--print', '-p', full_prompt],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"  CLI error: {e}")
    return None


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()

    # Get letters that need modern translation (have english_text but no modern_english)
    cursor.execute('''
        SELECT l.id, l.collection, l.letter_number, l.year_approx,
               l.english_text, l.latin_text,
               s.name as sender_name, r.name as recipient_name
        FROM letters l
        LEFT JOIN authors s ON l.sender_id = s.id
        LEFT JOIN authors r ON l.recipient_id = r.id
        WHERE l.modern_english IS NULL
            AND (l.english_text IS NOT NULL OR l.latin_text IS NOT NULL)
        ORDER BY l.collection, l.letter_number
    ''')
    letters = cursor.fetchall()
    print(f"Letters needing modern translation: {len(letters)}")

    # Process in batches
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    letters = letters[:batch_size]
    print(f"Processing batch of {len(letters)}...")

    translated = 0
    failed = 0

    for letter_id, collection, letter_num, year, english, latin, sender, recipient in letters:
        if not (english or latin) or (len(english or '') + len(latin or '')) < 50:
            continue

        print(f"  Translating {collection} #{letter_num}...", end=' ', flush=True)

        modern = translate_with_claude(english, latin, sender, recipient, collection, year)

        if modern and len(modern) > 30:
            cursor.execute('UPDATE letters SET modern_english = ? WHERE id = ?',
                           (modern, letter_id))
            translated += 1
            print(f"OK ({len(modern)} chars)")
        else:
            failed += 1
            print("FAILED")

        # Commit every 10
        if translated % 10 == 0:
            conn.commit()

    conn.commit()

    print(f"\nResults: {translated} translated, {failed} failed")

    # Show a sample
    cursor.execute('''
        SELECT collection, letter_number, modern_english
        FROM letters WHERE modern_english IS NOT NULL
        ORDER BY RANDOM() LIMIT 2
    ''')
    for row in cursor.fetchall():
        print(f"\n--- {row[0]} #{row[1]} ---")
        print(row[2][:500])

    conn.close()


if __name__ == '__main__':
    main()

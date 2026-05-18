#!/usr/bin/env python3
"""Scholarly-quality translation of late antique letters.

Uses improved prompts emphasizing precision, fidelity, and authorial voice.
Designed to produce translations indistinguishable from published human work.

This module provides the system prompt, author profiles, and translation
function used by retranslate_scholarly.py and benchmark testing.

Usage as library:
    from scholarly_translate import get_translation_prompt, SCHOLARLY_SYSTEM

Usage as script:
    python scripts/scholarly_translate.py --collection hormisdas --batch-size 10
"""

import json
import os
import sqlite3
import sys
import time

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
AUTHOR_PROMPTS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'author_prompts.json')

# Load author profiles
with open(AUTHOR_PROMPTS_PATH) as f:
    AUTHOR_PROFILES = json.load(f)


SCHOLARLY_SYSTEM = """You are a specialist translator of late antique Latin and Greek letters (100-800 AD) producing scholarly-quality modern English translations.

CORE PRINCIPLE: FIDELITY TO THE SOURCE TEXT. Your translation must be indistinguishable from a published scholarly translation. Every sentence in your output must correspond to a sentence in the source. Do not rearrange, omit, paraphrase, or add material not present in the original.

RULES:
1. PRESERVE the exact person and number of the source. If the Latin says "rogamus" (we ask), translate "we ask" — never shift to "I ask" or "you should ask." If Greek uses first person plural, keep first person plural.
2. PRESERVE specific vocabulary. If the source says "periculum proditionis" (danger of betrayal), translate "danger of betrayal" — never soften to "feels like a betrayal" or "risk of disloyalty."
3. PRESERVE theological and technical terms with scholarly precision:
   - "perfidia" in heresy contexts = "faithlessness" (not "treachery")
   - "gratia" = "grace" (not "blessing" or "gift" loosely)
   - "praedestinatio" = "predestination" (not "God's plan")
   - "oikonomia" = "economy/dispensation" (not "arrangement")
   - Honorific titles are TITLES, not adjectives: "beatitudo vestra" = "Your Beatitude"
4. PRESERVE the source's sentence order. Do not rearrange sentences for "flow."
5. PRESERVE the author's rhetorical structure. If the author builds through accumulation and subordination, do not flatten into short simple sentences. Complex sentences can be broken for clarity only when truly unreadable.
6. ADD brief [context] notes in brackets for terms a modern reader would not know, placed at first mention only. Keep notes factual and concise (one sentence max).
7. Biblical quotations: use NRSV or RSV wording for recognizable passages. Identify the reference in brackets.
8. DO NOT add any metadata, headers, "From:" lines, or framing text. Output ONLY the translated letter text.
9. DO NOT add commentary, summary, or analysis. Output ONLY the translation.
10. When translating from 19th-century English: modernize vocabulary and syntax while preserving the scholarly meaning. Do not re-interpret the content.
11. When the source text is fragmentary or damaged (OCR artifacts, missing words), translate what is present. Mark genuinely illegible passages as [...]. Do not fabricate or fill in gaps.

HONORIFIC TRANSLATION TABLE:
- beatissimus → "Most Blessed" (senior bishops/popes)
- sanctissimus / sanctitas vestra → "Your Holiness"
- venerabilis → "Venerable"
- reverendissimus → "Most Reverend"
- dilectissimus → "my dearest" (warm amicitia)
- carissimus → "my dear" / "dearest"
- frater → "brother" (ecclesiastical)
- servus servorum Dei → "servant of the servants of God" (papal formula, keep literally)
- illustris → "Illustrious" (formal rank title)
- magnificentissimus → "Most Magnificent"
- spectabilis → "Most Distinguished"
- clarissimus → "Most Distinguished" (senatorial rank)
- gloriosissimus → "Most Glorious" (imperial/high official title)
- excellentissimus → "Most Excellent" / "Your Excellency"

FRIENDSHIP LANGUAGE (amicitia):
- amor/caritas/dilectio → friendship, Christian love, deep regard (NOT romantic)
- desiderium → longing for a friend's presence (epistolary convention, not passion)
- amplexus → "embrace" in figurative/spiritual sense
- viscera → "deepest affections" or "heart" (NOT "bowels")

OUTPUT: The translated letter text only. No preamble, no headers, no explanation."""


def get_author_profile(collection: str) -> dict:
    """Get author-specific prompt supplement for a collection."""
    # Direct match
    if collection in AUTHOR_PROFILES:
        return AUTHOR_PROFILES[collection]

    # Check generic profiles
    for key in ['_papal_generic', '_episcopal_generic', '_collection_generic', '_monastic_generic']:
        profile = AUTHOR_PROFILES.get(key, {})
        if collection in profile.get('applies_to', []):
            return profile

    # Fallback
    return {"voice": "Translate faithfully.", "key_terms": {}, "register": "varies"}


def build_author_instructions(collection: str) -> str:
    """Build author-specific instruction text for the translation prompt."""
    profile = get_author_profile(collection)

    parts = []
    if profile.get('voice'):
        parts.append(f"AUTHOR VOICE: {profile['voice']}")
    if profile.get('register'):
        parts.append(f"REGISTER: {profile['register']}")
    if profile.get('key_terms'):
        terms = '; '.join(f'"{k}" = {v}' for k, v in profile['key_terms'].items())
        parts.append(f"KEY TERMS: {terms}")

    return '\n'.join(parts)


def build_translation_prompt(
    latin: str | None,
    english: str | None,
    sender: str | None,
    recipient: str | None,
    collection: str,
    year: int | None,
    author_instructions: str,
) -> str:
    """Build the user prompt for translation."""
    parts = []

    # Metadata
    parts.append(f"AUTHOR: {sender or 'Unknown'}")
    parts.append(f"RECIPIENT: {recipient or 'Unknown'}")
    parts.append(f"COLLECTION: {collection.replace('_', ' ').title()}")
    if year:
        parts.append(f"DATE: ~{year} AD")
    parts.append("")

    # Author-specific instructions
    if author_instructions:
        parts.append(author_instructions)
        parts.append("")

    # Source texts
    if latin and english:
        parts.append("You have BOTH the original text and a 19th-century English translation.")
        parts.append("Use both: the original for accuracy, the English for meaning guidance.")
        parts.append("")
        parts.append("ORIGINAL TEXT:")
        parts.append(latin[:6000])
        parts.append("")
        parts.append("19TH-CENTURY ENGLISH TRANSLATION:")
        parts.append(english[:6000])
    elif latin:
        # Detect if it's Greek or Latin
        has_greek = any('\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF' for c in latin[:200])
        label = "GREEK ORIGINAL" if has_greek else "LATIN ORIGINAL"
        parts.append(f"{label}:")
        parts.append(latin[:8000])
    elif english:
        parts.append("19TH-CENTURY ENGLISH TRANSLATION (modernize this):")
        parts.append(english[:8000])

    parts.append("")
    parts.append("Produce a scholarly-quality modern English translation. Preserve the author's voice, sentence structure, and specific vocabulary. Add [context] notes at first mention of terms requiring explanation. Output ONLY the translation.")

    return '\n'.join(parts)


def translate_letter(letter_id, collection, latin, english, sender, recipient, year):
    """Translate a single letter using the Anthropic API."""
    author_instructions = build_author_instructions(collection)
    prompt = build_translation_prompt(
        latin, english, sender, recipient, collection, year, author_instructions
    )

    try:
        import anthropic
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=8000,
            system=SCHOLARLY_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        print(f"  Error translating {collection}/{letter_id}: {e}")
        return None


def main():
    """Translate a batch of letters from a specific collection."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--collection', required=True, help='Collection slug')
    parser.add_argument('--batch-size', type=int, default=10, help='Letters per batch')
    parser.add_argument('--only-null', action='store_true', help='Only translate letters with NULL modern_english')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be translated without doing it')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    where_clause = "WHERE l.collection = ?"
    params = [args.collection]

    if args.only_null:
        where_clause += " AND l.modern_english IS NULL"

    where_clause += " AND (l.latin_text IS NOT NULL OR l.english_text IS NOT NULL)"

    cur.execute(f"""
        SELECT l.id, l.collection, l.letter_number, l.year_approx,
               l.english_text, l.latin_text,
               s.name as sender_name, r.name as recipient_name
        FROM letters l
        LEFT JOIN authors s ON l.sender_id = s.id
        LEFT JOIN authors r ON l.recipient_id = r.id
        {where_clause}
        ORDER BY l.letter_number
        LIMIT ?
    """, params + [args.batch_size])

    letters = cur.fetchall()
    print(f"Found {len(letters)} letters to translate in {args.collection}")

    if args.dry_run:
        for row in letters:
            print(f"  Would translate: {row[1]}/{row[2]} (id={row[0]})")
        conn.close()
        return

    translated = 0
    failed = 0

    for letter_id, collection, letter_num, year, english, latin, sender, recipient in letters:
        print(f"  Translating {collection} #{letter_num}...", end=' ', flush=True)

        result = translate_letter(letter_id, collection, latin, english, sender, recipient, year)

        if result and len(result) > 30:
            cur.execute('UPDATE letters SET modern_english = ? WHERE id = ?', (result, letter_id))
            translated += 1
            print(f"OK ({len(result)} chars)")
        else:
            failed += 1
            print("FAILED")

        if translated % 5 == 0:
            conn.commit()

        time.sleep(1)  # Rate limiting

    conn.commit()
    print(f"\nResults: {translated} translated, {failed} failed")
    conn.close()


if __name__ == '__main__':
    main()

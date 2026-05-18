#!/usr/bin/env python3
"""Automated post-translation quality validation.

Runs quick checks on translations without needing an LLM call.
Designed to catch obvious issues before the LLM reviewer sees them.

Run: python scripts/scholarly_validate.py [--collection NAME] [--fix]
"""

import re
import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

# AI hedging patterns that human translators don't use
HEDGING_PATTERNS = [
    r'\bessentially\b',
    r'\bin a sense\b',
    r'\bsort of\b',
    r'\bkind of\b',
    r'\bit seems?\b',
    r'\bfeels? like\b',
    r'\bbasically\b',
    r'\bmore or less\b',
    r'\bat its core\b',
    r'\bin essence\b',
]
HEDGING_RE = [re.compile(p, re.IGNORECASE) for p in HEDGING_PATTERNS]

# Header pattern
HEADER_RE = re.compile(r'^From:.*?\n', re.MULTILINE)


def validate_translation(modern_english, latin_text, english_text, sender_name, recipient_name):
    """Validate a single translation. Returns list of (severity, issue) tuples."""
    issues = []
    if not modern_english:
        return [('ERROR', 'No translation')]

    text = modern_english

    # 1. Header detection
    if text.startswith('From:') or text.startswith('To:'):
        issues.append(('ERROR', 'Contains AI metadata header'))

    # 2. Length ratio check
    source_len = len(latin_text or '') or len(english_text or '')
    if source_len > 0:
        ratio = len(text) / source_len
        if ratio < 0.3:
            issues.append(('WARNING', f'Suspiciously short (ratio={ratio:.2f}, {len(text)} chars vs {source_len} source)'))
        elif ratio > 3.0:
            issues.append(('WARNING', f'Suspiciously long (ratio={ratio:.2f}, {len(text)} chars vs {source_len} source)'))

    # 3. Hedging pattern detection
    hedges_found = []
    for pattern in HEDGING_RE:
        matches = pattern.findall(text)
        if matches:
            hedges_found.extend(matches)
    if len(hedges_found) >= 3:
        issues.append(('WARNING', f'AI hedging language ({len(hedges_found)} instances: {", ".join(hedges_found[:5])})'))

    # 4. Boilerplate detection — no proper nouns from metadata
    if sender_name and recipient_name:
        sender_first = sender_name.split()[0] if sender_name else ''
        recipient_first = recipient_name.split()[0] if recipient_name else ''
        has_sender = sender_first.lower() in text.lower() if sender_first else True
        has_recipient = recipient_first.lower() in text.lower() if recipient_first else True
        if not has_sender and not has_recipient and len(text) > 200:
            issues.append(('WARNING', 'No sender/recipient names found in translation'))

    # 5. Placeholder detection
    placeholders = ['translation pending', 'not yet translated', '[translation]',
                     'lorem ipsum', 'to be translated']
    for ph in placeholders:
        if ph in text.lower():
            issues.append(('ERROR', f'Contains placeholder: "{ph}"'))

    # 6. Untranslated Greek detection
    greek_pattern = re.compile(r'[\u0370-\u03FF\u1F00-\u1FFF]{3,}')
    greek_matches = greek_pattern.findall(text)
    if len(greek_matches) >= 2:
        issues.append(('ERROR', f'Contains untranslated Greek ({len(greek_matches)} passages)'))

    return issues


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--collection', help='Only validate this collection')
    parser.add_argument('--fix', action='store_true', help='Set ERROR translations to NULL')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    where = "WHERE l.modern_english IS NOT NULL"
    params = []
    if args.collection:
        where += " AND l.collection = ?"
        params.append(args.collection)

    cur.execute(f"""
        SELECT l.id, l.collection, l.letter_number,
               l.modern_english, l.latin_text, l.english_text,
               s.name, r.name
        FROM letters l
        LEFT JOIN authors s ON l.sender_id = s.id
        LEFT JOIN authors r ON l.recipient_id = r.id
        {where}
        ORDER BY l.collection, l.letter_number
    """, params)

    rows = cur.fetchall()
    print(f"Validating {len(rows)} translations...")

    errors = []
    warnings = []

    for row_id, coll, lnum, modern, latin, english, sender, recipient in rows:
        issues = validate_translation(modern, latin, english, sender, recipient)
        for severity, issue in issues:
            entry = (row_id, coll, lnum, severity, issue)
            if severity == 'ERROR':
                errors.append(entry)
            else:
                warnings.append(entry)

    # Print results
    print(f"\nERRORS: {len(errors)}")
    for row_id, coll, lnum, sev, issue in errors[:30]:
        print(f"  [{coll}/{lnum}] (id={row_id}): {issue}")
    if len(errors) > 30:
        print(f"  ... and {len(errors) - 30} more")

    print(f"\nWARNINGS: {len(warnings)}")
    for row_id, coll, lnum, sev, issue in warnings[:30]:
        print(f"  [{coll}/{lnum}] (id={row_id}): {issue}")
    if len(warnings) > 30:
        print(f"  ... and {len(warnings) - 30} more")

    if args.fix and errors:
        print(f"\nRemoving {len(errors)} ERROR translations...")
        for row_id, coll, lnum, sev, issue in errors:
            cur.execute("UPDATE letters SET modern_english = NULL WHERE id = ?", (row_id,))
        conn.commit()
        print("Done.")

    conn.close()


if __name__ == '__main__':
    main()

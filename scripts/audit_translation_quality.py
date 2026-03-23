#!/usr/bin/env python3
"""Audit AI-generated translations for quality issues.

Flags letters where modern_english:
- Contains untranslated Latin/Greek words
- Is suspiciously short (<100 chars)
- Contains OCR artifacts
- Contains placeholder text
- Is near-identical to english_text (just copied)

Run: python scripts/audit_translation_quality.py [--fix]

With --fix: sets modern_english = NULL for unacceptable translations
Without --fix: report only (default)
"""

import re
import sqlite3
import sys
from difflib import SequenceMatcher

DB_PATH = "data/roman_letters.db"

# Common Latin words that should NOT appear in a proper English translation
# (excluding proper nouns and widely-known terms like "via")
LATIN_INDICATORS = [
    r'\best\b', r'\bsunt\b', r'\benim\b', r'\bautem\b', r'\bquod\b',
    r'\bquia\b', r'\bsed\b', r'\betiam\b', r'\bquae\b', r'\bqui\b',
    r'\bhaec\b', r'\bhoc\b', r'\bideo\b', r'\bergo\b', r'\bnon\b',
    r'\bcum\b', r'\btamen\b', r'\bquoque\b', r'\binter\b',
]
# Only flag if 5+ Latin words appear (to avoid false positives on proper nouns)
LATIN_THRESHOLD = 5

# OCR artifact patterns
OCR_ARTIFACTS = re.compile(r'[■□▪▫◆◇●○▶▷◀◁★☆※†‡§¶]+')
BRACKET_REFS = re.compile(r'\[\d+[a-z]?\]')  # [1], [2a], etc — manuscript refs from OCR

# Greek character ranges (indicates untranslated Greek)
GREEK_PATTERN = re.compile(r'[\u0370-\u03FF\u1F00-\u1FFF]{3,}')  # 3+ consecutive Greek chars


def check_latin_contamination(text: str) -> int:
    """Count how many common Latin words appear in the text."""
    count = 0
    text_lower = text.lower()
    for pattern in LATIN_INDICATORS:
        count += len(re.findall(pattern, text_lower))
    return count


def check_similarity(text_a: str, text_b: str) -> float:
    """Return similarity ratio between two texts (0.0 to 1.0)."""
    if not text_a or not text_b:
        return 0.0
    # Compare first 500 chars to avoid slow comparisons on long texts
    return SequenceMatcher(None, text_a[:500], text_b[:500]).ratio()


def audit_letter(modern_english: str, english_text: str | None) -> list[str]:
    """Return list of quality issues found."""
    issues = []

    if not modern_english:
        return issues

    # 1. Suspiciously short
    if len(modern_english.strip()) < 100:
        issues.append(f"SHORT ({len(modern_english.strip())} chars)")

    # 2. Placeholder text
    placeholders = ['translation pending', 'needs translation', 'to be translated',
                     'not yet translated', '[translation]', 'lorem ipsum']
    lower = modern_english.lower()
    for ph in placeholders:
        if ph in lower:
            issues.append(f"PLACEHOLDER: '{ph}'")

    # 3. Latin contamination
    latin_count = check_latin_contamination(modern_english)
    if latin_count >= LATIN_THRESHOLD:
        issues.append(f"LATIN_WORDS ({latin_count} common Latin words)")

    # 4. Untranslated Greek
    greek_matches = GREEK_PATTERN.findall(modern_english)
    if len(greek_matches) >= 2:
        issues.append(f"GREEK_TEXT ({len(greek_matches)} Greek passages)")

    # 5. OCR artifacts
    artifact_matches = OCR_ARTIFACTS.findall(modern_english)
    if artifact_matches:
        issues.append(f"OCR_ARTIFACTS: {''.join(artifact_matches[:5])}")

    # 6. Excessive bracket references (suggests un-cleaned OCR)
    bracket_count = len(BRACKET_REFS.findall(modern_english))
    if bracket_count >= 5:
        issues.append(f"BRACKET_REFS ({bracket_count} manuscript references)")

    # 7. Near-identical to english_text (just copied, not modernized)
    if english_text:
        sim = check_similarity(modern_english, english_text)
        if sim > 0.95:
            issues.append(f"DUPLICATE (similarity={sim:.2f})")

    return issues


# Severity: issues that warrant removal vs just a warning
REMOVAL_ISSUES = {'PLACEHOLDER', 'OCR_ARTIFACTS', 'GREEK_TEXT'}
WARNING_ISSUES = {'SHORT', 'LATIN_WORDS', 'BRACKET_REFS', 'DUPLICATE'}


def should_remove(issues: list[str]) -> bool:
    """Determine if a translation is bad enough to remove."""
    for issue in issues:
        issue_type = issue.split('(')[0].split(':')[0].strip()
        if issue_type in REMOVAL_ISSUES:
            return True
    return False


def main():
    fix_mode = '--fix' in sys.argv

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Only audit non-scholarly translations
    cur.execute("""
        SELECT id, collection, letter_number, modern_english, english_text, translation_source
        FROM letters
        WHERE modern_english IS NOT NULL
          AND modern_english != ''
          AND (translation_source IS NULL
               OR translation_source NOT IN (
                   'existing_newadvent', 'existing_tertullian', 'existing_fordham',
                   'existing_celt', 'existing_attalus', 'existing_livius', 'existing_rogerpearse'
               ))
    """)

    rows = cur.fetchall()
    print(f"Auditing {len(rows)} non-scholarly translations...\n")

    flagged = []
    removal_candidates = []
    warning_candidates = []

    for row_id, collection, letter_num, modern, english, source in rows:
        issues = audit_letter(modern, english)
        if issues:
            entry = {
                'id': row_id,
                'collection': collection,
                'letter_number': letter_num,
                'source': source,
                'issues': issues,
            }
            flagged.append(entry)
            if should_remove(issues):
                removal_candidates.append(entry)
            else:
                warning_candidates.append(entry)

    # Print summary by collection
    print("=" * 70)
    print("SUMMARY BY COLLECTION")
    print("=" * 70)
    from collections import Counter
    coll_counts = Counter(e['collection'] for e in flagged)
    for coll, count in coll_counts.most_common():
        removals = sum(1 for e in removal_candidates if e['collection'] == coll)
        warnings = sum(1 for e in warning_candidates if e['collection'] == coll)
        print(f"  {coll}: {count} flagged ({removals} remove, {warnings} warn)")

    # Print removal candidates
    print(f"\n{'=' * 70}")
    print(f"REMOVAL CANDIDATES ({len(removal_candidates)} letters)")
    print("=" * 70)
    for entry in removal_candidates[:50]:  # Show first 50
        print(f"  [{entry['collection']}/{entry['letter_number']}] (id={entry['id']}, src={entry['source']})")
        for issue in entry['issues']:
            print(f"    - {issue}")

    if len(removal_candidates) > 50:
        print(f"  ... and {len(removal_candidates) - 50} more")

    # Print warning candidates
    print(f"\n{'=' * 70}")
    print(f"WARNING CANDIDATES ({len(warning_candidates)} letters)")
    print("=" * 70)
    for entry in warning_candidates[:30]:
        print(f"  [{entry['collection']}/{entry['letter_number']}] (id={entry['id']}, src={entry['source']})")
        for issue in entry['issues']:
            print(f"    - {issue}")

    if len(warning_candidates) > 30:
        print(f"  ... and {len(warning_candidates) - 30} more")

    # Apply fixes if requested
    if fix_mode:
        print(f"\n{'=' * 70}")
        print("APPLYING FIXES")
        print("=" * 70)
        removed = 0
        for entry in removal_candidates:
            cur.execute("UPDATE letters SET modern_english = NULL WHERE id = ?", (entry['id'],))
            removed += 1
            print(f"  Removed translation: {entry['collection']}/{entry['letter_number']}")

        conn.commit()
        print(f"\nRemoved {removed} bad translations")
    else:
        print(f"\nTotal flagged: {len(flagged)}")
        print(f"  Would remove: {len(removal_candidates)}")
        print(f"  Would warn: {len(warning_candidates)}")
        print("\nRun with --fix to remove bad translations")

    conn.close()


if __name__ == '__main__':
    main()

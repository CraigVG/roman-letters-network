#!/usr/bin/env python3
"""
Transliterate Greek-character author names in the roman_letters.db to Latin/English equivalents.
Updates the `name` field with transliterated version and saves original Greek in `name_latin`.
"""

import sqlite3
import unicodedata
import re

DB_PATH = "/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db"

# ── Special-case entries by ID (most reliable) ──────────────────────────────
SPECIAL_BY_ID = {
    952: "To the same person",       # Τῷ αὐτῶ
    961: "To the same person (2)",    # Τῷ αὐτῷ
    1110: "Julian, Emperor",          # Ιουλιανῷ αὐτοκράτορι
    1484: "Julian, Emperor (2)",      # 'Ιουλιανῷ αὐτοκράτορι
    1088: "Sopatros (letter incipit)",  # Παλαιᾶς τινος εὐεργεσίας...
    1112: "Amphitera (letter incipit)", # Ἀμφότερα εὑ ᾔδειν...
    1047: "Agroikios and Eusebios",   # Ἀγροικίῳ καὶ Εὐσεβίῳ
    1036: "Dorotheos, bishop",        # Δωροθέῳ ἐπισκόπῳ
    1060: "Bassianos (2)",            # Βασσιαωῷ (likely typo for Βασσιανῷ)
    1105: "Hierax",                   # Ἱέρακι (irregular dative of Hierax)
    1045: "Eudaimon",                 # Εὐδαίμονι (dative of Eudaimon)
}

# Words to strip and note as roles
ROLE_WORDS = {
    "ἐπισκόπῳ": "bishop",
    "αὐτοκράτορι": "emperor",
}

# ── Greek-to-Latin character mapping ─────────────────────────────────────────

# Diphthongs (order matters - check longer sequences first)
DIPHTHONGS = [
    ("αι", "ai"), ("ει", "ei"), ("οι", "oi"), ("ου", "ou"),
    ("αυ", "au"), ("ευ", "eu"), ("ηυ", "eu"),
    ("γγ", "ng"), ("γκ", "nk"), ("γξ", "nx"), ("γχ", "nch"),
    ("μπ", "mp"), ("ντ", "nt"),
]

# Single character mapping (lowercase)
GREEK_TO_LATIN = {
    'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e',
    'ζ': 'z', 'η': 'e', 'θ': 'th', 'ι': 'i', 'κ': 'k',
    'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o',
    'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't',
    'υ': 'u', 'φ': 'ph', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o',
    # Uppercase
    'Α': 'A', 'Β': 'B', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E',
    'Ζ': 'Z', 'Η': 'E', 'Θ': 'Th', 'Ι': 'I', 'Κ': 'K',
    'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X', 'Ο': 'O',
    'Π': 'P', 'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'U',
    'Φ': 'Ph', 'Χ': 'Ch', 'Ψ': 'Ps', 'Ω': 'O',
}


def strip_accents_and_breathing(text):
    """
    Decompose Greek characters into base + combining marks, then strip
    combining marks (accents, breathing, iota subscript, diaeresis).
    """
    # Handle iota subscript characters first
    iota_sub = {
        'ᾳ': 'αι', 'ᾴ': 'αι', 'ᾲ': 'αι', 'ᾷ': 'αι', 'ᾶ': 'α',
        'ῃ': 'ηι', 'ῄ': 'ηι', 'ῂ': 'ηι', 'ῇ': 'ηι',
        'ῳ': 'ωι', 'ῴ': 'ωι', 'ῲ': 'ωι', 'ῷ': 'ωι',
        'ᾀ': 'αι', 'ᾁ': 'αι', 'ᾂ': 'αι', 'ᾃ': 'αι',
        'ᾄ': 'αι', 'ᾅ': 'αι', 'ᾆ': 'αι', 'ᾇ': 'αι',
        'ᾐ': 'ηι', 'ᾑ': 'ηι', 'ᾒ': 'ηι', 'ᾓ': 'ηι',
        'ᾔ': 'ηι', 'ᾕ': 'ηι', 'ᾖ': 'ηι', 'ᾗ': 'ηι',
        'ᾠ': 'ωι', 'ᾡ': 'ωι', 'ᾢ': 'ωι', 'ᾣ': 'ωι',
        'ᾤ': 'ωι', 'ᾥ': 'ωι', 'ᾦ': 'ωι', 'ᾧ': 'ωι',
        'ᾼ': 'Αι', 'ῌ': 'Ηι', 'ῼ': 'Ωι',
    }
    result = []
    for ch in text:
        if ch in iota_sub:
            result.append(iota_sub[ch])
        else:
            result.append(ch)
    text = ''.join(result)

    # NFD decomposition to strip combining marks
    decomposed = unicodedata.normalize('NFD', text)
    stripped = ''.join(c for c in decomposed if unicodedata.category(c)[0] != 'M')
    return stripped


def transliterate_word(word):
    """Transliterate a single Greek word to Latin characters."""
    if not word:
        return word

    has_greek = any('GREEK' in unicodedata.name(ch, '') for ch in word)
    if not has_greek:
        return word

    base = strip_accents_and_breathing(word)
    first_upper = base[0].isupper() if base else False
    lower = base.lower()

    # Apply diphthongs first
    result = lower
    for greek_di, latin_di in DIPHTHONGS:
        result = result.replace(greek_di, latin_di)

    # Apply single character mapping
    mapped = []
    for ch in result:
        if ch in GREEK_TO_LATIN:
            mapped.append(GREEK_TO_LATIN[ch].lower())
        else:
            mapped.append(ch)
    result = ''.join(mapped)

    if first_upper and result:
        result = result[0].upper() + result[1:]

    return result


def convert_dative_to_nominative(name):
    """
    Convert Greek dative endings to nominative for standard English transliteration.
    """
    # -oii (from -ῳ with iota subscript) → -os
    if name.endswith('oii'):
        return name[:-3] + 'os'
    # -oi at end (from -ω without subscript or -οι) → -os for names
    if name.endswith('oi') and len(name) > 3:
        return name[:-2] + 'os'

    # -eii (from -ῃ with iota subscript) → -es
    if name.endswith('eii'):
        return name[:-3] + 'es'
    # -ei at end (dative of -ης) → -es
    if name.endswith('ei') and len(name) > 3:
        return name[:-2] + 'es'

    # -aii (from -ᾳ with iota subscript) → -a
    if name.endswith('aii'):
        return name[:-3] + 'a'
    # -ai at end → -a
    if name.endswith('ai') and len(name) > 3:
        return name[:-2] + 'a'

    # -oni (dative of -ων names like Ἀπελλίωνι, Βαρβατίωνι) → -on
    if name.endswith('oni'):
        return name[:-1]

    # -o at end (from -ω without iota subscript) → -os
    if name.endswith('o') and len(name) > 2:
        return name + 's'

    # -i at end (dative of consonant stems) - leave as-is for now
    return name


def has_greek(text):
    """Check if text contains any Greek characters."""
    for ch in text:
        if 'GREEK' in unicodedata.name(ch, ''):
            return True
    return False


def transliterate_greek_name(name):
    """
    Full pipeline: strip roles, transliterate, fix endings.
    Returns (transliterated_name, role_or_none).
    """
    name = name.strip()

    # Check for and strip role words
    detected_role = None
    for greek_role, english_role in ROLE_WORDS.items():
        if greek_role in name:
            name = name.replace(greek_role, '').strip()
            detected_role = english_role

    # Strip leading quotes/marks
    name = name.lstrip("'ʽʼ᾿")

    # Split into words and transliterate each
    words = name.split()
    transliterated_words = []
    for w in words:
        t = transliterate_word(w)
        transliterated_words.append(t)

    result = ' '.join(transliterated_words)

    # Convert dative endings to nominative for each word
    parts = result.split()
    converted = []
    for p in parts:
        converted.append(convert_dative_to_nominative(p))
    result = ' '.join(converted)

    # Capitalize first letter
    if result:
        result = result[0].upper() + result[1:]

    return result, detected_role


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get all existing author names to check for conflicts
    cur.execute("SELECT id, name FROM authors")
    existing_names = {}
    for row in cur.fetchall():
        existing_names[row[1]] = row[0]

    # Find all authors with Greek characters
    cur.execute("SELECT id, name, name_latin, role FROM authors")
    all_authors = cur.fetchall()

    greek_authors = []
    for row in all_authors:
        aid, name, name_latin, role = row
        if name and has_greek(name):
            greek_authors.append(row)

    print(f"Found {len(greek_authors)} authors with Greek characters\n")
    print(f"{'ID':>5} | {'Original Greek':<55} | {'Transliterated':<40} | {'Role'}")
    print("-" * 145)

    # First pass: compute all transliterations, detect duplicates
    raw_updates = []
    for aid, name, name_latin, existing_role in greek_authors:
        if aid in SPECIAL_BY_ID:
            transliterated = SPECIAL_BY_ID[aid]
            detected_role = None
            # Extract role from special name if applicable
            if "bishop" in transliterated.lower():
                detected_role = "bishop"
            elif "emperor" in transliterated.lower():
                detected_role = "emperor"
        else:
            transliterated, detected_role = transliterate_greek_name(name)
        raw_updates.append((aid, name, name_latin, transliterated, detected_role, existing_role))

    # Detect duplicate transliterated names (among Greek authors AND existing non-Greek authors)
    name_counts = {}
    for _, _, _, transliterated, _, _ in raw_updates:
        name_counts[transliterated] = name_counts.get(transliterated, 0) + 1

    # For duplicates, append " (N)" suffix
    name_seen = {}
    updates = []
    for aid, orig_name, name_latin, transliterated, detected_role, existing_role in raw_updates:
        final_name = transliterated

        # Check if this name already exists in the db (non-Greek author)
        if transliterated in existing_names and existing_names[transliterated] != aid:
            # Conflict with existing non-Greek author
            if transliterated not in name_seen:
                name_seen[transliterated] = 1
            name_seen[transliterated] += 1
            final_name = f"{transliterated} ({name_seen[transliterated]})"
        elif name_counts[transliterated] > 1:
            # Duplicate among Greek authors
            if transliterated not in name_seen:
                name_seen[transliterated] = 0
            name_seen[transliterated] += 1
            if name_seen[transliterated] > 1:
                final_name = f"{transliterated} ({name_seen[transliterated]})"

        updates.append((aid, orig_name, name_latin, final_name, detected_role, existing_role))
        role_str = detected_role or ''
        print(f"{aid:>5} | {orig_name:<55} | {final_name:<40} | {role_str}")

    # Perform the updates
    print(f"\nUpdating {len(updates)} authors...")
    for aid, original_greek, old_name_latin, transliterated, detected_role, existing_role in updates:
        cur.execute(
            "UPDATE authors SET name = ?, name_latin = ? WHERE id = ?",
            (transliterated, original_greek, aid)
        )
        if detected_role and not existing_role:
            cur.execute(
                "UPDATE authors SET role = ? WHERE id = ?",
                (detected_role, aid)
            )

    conn.commit()
    print("Done! All updates committed.")

    # Verify
    cur.execute("SELECT id, name, name_latin FROM authors WHERE id IN ({})".format(
        ','.join(str(u[0]) for u in updates)
    ))
    verified = cur.fetchall()
    remaining_greek = sum(1 for _, n, _ in verified if has_greek(n))
    print(f"\nVerification: {remaining_greek} authors still have Greek in name field")
    if remaining_greek > 0:
        for aid, n, _ in verified:
            if has_greek(n):
                print(f"  Still Greek: {aid} -> {n}")

    conn.close()


if __name__ == "__main__":
    main()

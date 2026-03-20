#!/usr/bin/env python3
"""
Extract letter-carrier information from Roman letters database.

Scans modern_english and english_text for mentions of letter bearers/carriers,
extracting carrier names, roles, and whether a carrier is mentioned at all.

Based on patterns from Wyman's Chapter 4 on who physically carried letters
in late antiquity.
"""

import sqlite3
import re
from collections import Counter

DB_PATH = "/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db"

# Role classification mapping
ROLE_KEYWORDS = {
    'deacon': ['deacon', 'diacono'],
    'subdeacon': ['subdeacon', 'sub-deacon', 'subdiaconus'],
    'priest': ['priest', 'presbyter', 'presbytero'],
    'bishop': ['bishop', 'episcopo', 'archbishop', 'metropolitan'],
    'monk': ['monk', 'monastic', 'religious', 'abbot', 'abbess'],
    'notary': ['notary', 'notarius', 'secretary'],
    'defensor': ['defensor', 'defensorem', 'church legal advocate', 'legal advocate'],
    'merchant': ['merchant', 'trader', 'businessman'],
    'soldier': ['soldier', 'military', 'tribune', 'comes', 'dux'],
    'official': ['official', 'praetor', 'prefect', 'governor', 'consul', 'magistrate', 'proconsul', 'exarch'],
    'envoy': ['envoy', 'legate', 'legatus', 'ambassador', 'emissary', 'nuncio', 'delegate', 'representative'],
}

# Common late-antique name pattern: capitalized word(s)
NAME_PAT = r"([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)"

# ---- CARRIER DETECTION PATTERNS ----
# These return (full_match_text) for carrier_mentioned detection.
# Name extraction is done separately.

CARRIER_PATTERNS_SIMPLE = [
    # "the bearer of this letter" / "the bearer"
    r'\bthe\s+bearer(?:\s+of\s+(?:this|the|my|our)\s+(?:letter|epistle|communication|note|writing|present)s?)?\b',
    r'\bpresent\s+bearer\b',
    # "carried by [name]"
    r'\bcarried\s+by\b',
    # "sent by the hand of"
    r'\bsent\s+by\s+the\s+hand(?:s)?\s+of\b',
    r'\bby\s+the\s+hand(?:s)?\s+of\b',
    # "through [name]" as carrier context
    r'\bthrough\s+whom\s+(?:I|we)\s+(?:am\s+)?send(?:ing)?\b',
    # "your/my/our/the messenger"
    r'\b(?:your|my|our|the|this)\s+messenger\b',
    # "the courier" / "the envoy" / "the legate"
    r'\bthe\s+courier\b',
    r'\bthe\s+envoy\b',
    r'\bthe\s+legate\b',
    # "entrusted this letter to"
    r'\bentrusted\s+(?:this|the|my|our)\s+(?:letter|epistle|note|writing)s?\s+to\b',
    # "deliver this letter"
    r'\bdeliver(?:ing|ed|s)?\s+(?:this|the|my|our)\s+(?:letter|epistle|note|writing)\b',
    # "bring(?:s|ing) this letter"
    r'\bbring(?:s|ing)\s+(?:this|the|my|our)\s+(?:letter|epistle|note|writing)\b',
    # "who carries this"
    r'\bwho\s+(?:carries|is\s+carrying|will\s+carry|brought|brings)\s+(?:this|the|my|our)\b',
    # "dispatched [name] to"
    r'\bdispatched\b.*?\bto\s+(?:you|your)\b',
]

# Patterns that extract a name - group 1 should be the name
CARRIER_NAME_PATTERNS = [
    # "I am sending / I have sent [Name]"
    (r'\bI\s+(?:am\s+)?send(?:ing|t)\s+' + NAME_PAT + r'\s+to\s+(?:you|your)', 1),
    (r'\bwe\s+(?:are\s+)?send(?:ing|t)\s+' + NAME_PAT + r'\s+to\s+(?:you|your)', 1),
    (r"\bI(?:'ve|'ve| have)\s+sent\s+" + NAME_PAT + r'\s+to\s+(?:you|your)', 1),
    # "carried by [Name]"
    (r'\bcarried\s+by\s+' + NAME_PAT, 1),
    # "by the hand(s) of [Name]"
    (r'\bby\s+the\s+hand(?:s)?\s+of\s+' + NAME_PAT, 1),
    # "sent by the hand of [Name]"
    (r'\bsent\s+by\s+the\s+hand(?:s)?\s+of\s+' + NAME_PAT, 1),
    # "[Name], the bearer"
    (NAME_PAT + r',?\s+the\s+bearer', 1),
    # "the bearer, [Name]"
    (r'\bthe\s+bearer,?\s+' + NAME_PAT, 1),
    # "by our/my/your brother/son/deacon/servant [Name]"
    (r'\bby\s+(?:our|my|your|the)\s+(?:brother|son|daughter|deacon|servant|friend|subdeacon|sub-deacon|priest|presbyter|notary|defensor|monk|bishop|legate|envoy|messenger)\s+' + NAME_PAT, 1),
    # "through [Name], who is a [role]"
    (r'\bthrough\s+' + NAME_PAT + r',?\s+who\s+is\s+(?:a|an|our|my|the)\s+', 1),
    # "entrusted this letter to [Name]"
    (r'\bentrusted\s+(?:this|the|my|our)\s+(?:letter|epistle|note|writing)s?\s+to\s+' + NAME_PAT, 1),
    # "I'm sending [Name] the [role]"
    (r"I(?:'m| am)\s+send(?:ing)\s+" + NAME_PAT + r'\s+the\s+(?:deacon|subdeacon|sub-deacon|defensor|priest|presbyter|notary|monk|bishop|legate|envoy|messenger)', 1),
    # "sending [Name] the defensor" (Gregory pattern)
    (r'\bsending\s+' + NAME_PAT + r'\s+the\s+(?:deacon|subdeacon|sub-deacon|defensor|priest|presbyter|notary|monk|bishop)', 1),
    # "dispatched [Name]"
    (r'\bdispatched\s+' + NAME_PAT, 1),
    # "we've appointed [Name] ... as our delegate"
    (r"(?:we(?:'ve|'ve| have)\s+appointed|appointing)\s+" + NAME_PAT, 1),
]

# Patterns for role extraction from context around a carrier mention
ROLE_CONTEXT_PATTERNS = [
    # "[Name] the [role]" or "[Name], [role]"
    (r'the\s+(deacon|subdeacon|sub-deacon|priest|presbyter|notary|defensor|monk|bishop|archbishop|legate|envoy|courier|messenger|soldier|tribune|official|abbot|ambassador|representative|delegate|nuncio)', 1),
    (r'(?:a|an|our|my|the|your)\s+(deacon|subdeacon|sub-deacon|priest|presbyter|notary|defensor|monk|bishop|archbishop|legate|envoy|courier|messenger|soldier|tribune|official|abbot|ambassador|representative|delegate|nuncio)', 1),
]

# Words that should NOT be carrier names (common false positives)
NAME_BLACKLIST = {
    'God', 'Lord', 'Christ', 'Jesus', 'Holy', 'Spirit', 'Scripture',
    'Almighty', 'Father', 'Son', 'Church', 'Rome', 'Constantinople',
    'Jerusalem', 'Alexandria', 'Antioch', 'Africa', 'Italy', 'Sicily',
    'Gaul', 'Spain', 'Egypt', 'Greece', 'Palestine', 'Syria',
    'Your', 'His', 'Her', 'Our', 'The', 'This', 'That', 'These',
    'But', 'For', 'And', 'Not', 'Yet', 'Now', 'Then', 'When', 'Where',
    'What', 'Who', 'How', 'May', 'Let', 'See', 'Take', 'Give',
    'Letter', 'Book', 'Chapter', 'Council', 'Epistle',
    'Bishop', 'Deacon', 'Priest', 'Pope', 'Emperor',
    'Christian', 'Catholic', 'Orthodox', 'Arian',
    'Easter', 'Lent', 'Christmas', 'Pentecost',
    'January', 'February', 'March', 'April', 'June', 'July',
    'August', 'September', 'October', 'November', 'December',
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
    'Indeed', 'However', 'Therefore', 'Moreover', 'Furthermore',
    'Meanwhile', 'Nevertheless', 'Accordingly', 'Consequently',
    'Clearly', 'Certainly', 'Perhaps', 'Whether', 'Because',
    'Since', 'Although', 'Unless', 'Before', 'After',
    'Above', 'Below', 'Between', 'Beyond', 'Through',
    'Otherwise', 'Already', 'Likewise', 'Instead', 'Still',
    'Jew', 'Jews', 'Pagan', 'Pagans', 'Heretic', 'Heretics',
    'God', 'Dear', 'Most', 'Here', 'There', 'Some', 'Any',
    'Each', 'Every', 'Such', 'Much', 'Very', 'Just', 'Only',
}


def classify_role(text_window):
    """Classify the carrier's role based on surrounding text."""
    text_lower = text_window.lower()

    # Check role-specific keywords in order of specificity
    for role, keywords in [
        ('subdeacon', ROLE_KEYWORDS['subdeacon']),
        ('defensor', ROLE_KEYWORDS['defensor']),
        ('notary', ROLE_KEYWORDS['notary']),
        ('deacon', ROLE_KEYWORDS['deacon']),
        ('priest', ROLE_KEYWORDS['priest']),
        ('bishop', ROLE_KEYWORDS['bishop']),
        ('monk', ROLE_KEYWORDS['monk']),
        ('envoy', ROLE_KEYWORDS['envoy']),
        ('soldier', ROLE_KEYWORDS['soldier']),
        ('official', ROLE_KEYWORDS['official']),
        ('merchant', ROLE_KEYWORDS['merchant']),
    ]:
        for kw in keywords:
            if kw in text_lower:
                return role

    return 'unknown'


def extract_carrier_info(text):
    """
    Extract carrier name, role, and whether a carrier is mentioned.
    Returns (carrier_mentioned, carrier_name, carrier_role).
    """
    if not text:
        return False, None, None

    carrier_mentioned = False
    carrier_name = None
    carrier_role = None

    # Check simple carrier-mention patterns
    for pattern in CARRIER_PATTERNS_SIMPLE:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            carrier_mentioned = True
            # Get context window for role classification
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]
            if not carrier_role or carrier_role == 'unknown':
                carrier_role = classify_role(context)
            break

    # Try to extract named carriers
    for pattern, group_idx in CARRIER_NAME_PATTERNS:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(group_idx).strip()
            # Validate the name
            # Check each word against blacklist
            words = candidate.split()
            if (candidate and len(candidate) > 2
                and candidate not in NAME_BLACKLIST
                and all(w not in NAME_BLACKLIST for w in words)
                and len(words) <= 3):
                # Additional validation: should look like a proper name
                if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', candidate):
                    carrier_mentioned = True
                    carrier_name = candidate
                    # Get context for role
                    start = max(0, match.start() - 150)
                    end = min(len(text), match.end() + 150)
                    context = text[start:end]
                    carrier_role = classify_role(context)
                    break

    # If carrier mentioned but no role found, set unknown
    if carrier_mentioned and not carrier_role:
        carrier_role = 'unknown'

    return carrier_mentioned, carrier_name, carrier_role


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Add columns if they don't exist
    existing_cols = [row[1] for row in cur.execute("PRAGMA table_info(letters)").fetchall()]

    for col, coltype in [
        ('carrier_name', 'TEXT'),
        ('carrier_role', 'TEXT'),
        ('carrier_mentioned', 'BOOLEAN'),
    ]:
        if col not in existing_cols:
            cur.execute(f"ALTER TABLE letters ADD COLUMN {col} {coltype}")
            print(f"  Added column: {col} {coltype}")

    conn.commit()

    # 2. Scan all letters
    rows = cur.execute("""
        SELECT id, collection, ref_id, modern_english, english_text
        FROM letters
    """).fetchall()

    print(f"\nScanning {len(rows)} letters for carrier mentions...\n")

    updated = 0
    carrier_count = 0
    role_counter = Counter()
    name_counter = Counter()
    collection_counter = Counter()

    for row in rows:
        letter_id = row['id']
        collection = row['collection']

        # Combine both text fields for scanning
        texts = []
        if row['modern_english']:
            texts.append(row['modern_english'])
        if row['english_text']:
            texts.append(row['english_text'])

        if not texts:
            continue

        combined_text = '\n'.join(texts)

        mentioned, name, role = extract_carrier_info(combined_text)

        if mentioned:
            carrier_count += 1
            role_counter[role] += 1
            collection_counter[collection] += 1
            if name:
                name_counter[name] += 1

        # Update the row
        cur.execute("""
            UPDATE letters
            SET carrier_mentioned = ?,
                carrier_name = ?,
                carrier_role = ?
            WHERE id = ?
        """, (1 if mentioned else 0, name, role, letter_id))
        updated += 1

    conn.commit()

    # 3. Print summary statistics
    total_letters = len(rows)
    print("=" * 65)
    print("LETTER-CARRIER EXTRACTION SUMMARY")
    print("=" * 65)
    print(f"\nTotal letters scanned:        {total_letters}")
    print(f"Letters with carrier mentions: {carrier_count} ({100*carrier_count/total_letters:.1f}%)")
    print(f"Letters with named carriers:   {sum(name_counter.values())}")

    print(f"\n{'CARRIER ROLE BREAKDOWN':}")
    print("-" * 40)
    for role, count in sorted(role_counter.items(), key=lambda x: -x[1]):
        print(f"  {role:<20} {count:>5}  ({100*count/carrier_count:.1f}%)")

    print(f"\nTOP 25 NAMED CARRIERS:")
    print("-" * 40)
    for name, count in name_counter.most_common(25):
        print(f"  {name:<25} {count:>3} mentions")

    print(f"\nCARRIER MENTIONS BY COLLECTION:")
    print("-" * 55)
    # Get total letters per collection for percentage
    collection_totals = {}
    for row in rows:
        c = row['collection']
        collection_totals[c] = collection_totals.get(c, 0) + 1

    for coll, count in sorted(collection_counter.items(), key=lambda x: -x[1]):
        total = collection_totals[coll]
        print(f"  {coll:<35} {count:>4} / {total:<5} ({100*count/total:.1f}%)")

    conn.close()
    print(f"\nDone. Updated {updated} rows in the database.")


if __name__ == "__main__":
    main()

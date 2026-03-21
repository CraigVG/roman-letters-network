#!/usr/bin/env python3
"""
fix_missing_recipients.py

Extracts recipient names from letter text (modern_english) and assigns
recipient_id values in the letters table. Creates new author entries
when a name appears in 2+ letters and doesn't already exist.

Patterns handled:
- "To [Name], Bishop of [Place]" (venantius_fortunatus, gregory_great, etc.)
- "Gregory to [Name], Bishop of [Place]" (gregory_great)
- "Augustine to [Name], greetings" (augustine)
- "From: ...\nTo: [Name]" (isidore_pelusium, hormisdas, cassiodorus)
- "KING THEODERIC TO [NAME]" (cassiodorus)
- "King Theodoric to [Name]" (cassiodorus)
- "Pope Pelagius I to [Name]" (pelagius_i)
"""

import sqlite3
import re
from collections import Counter, defaultdict
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "roman_letters.db")


def clean_name(name):
    """Clean up an extracted name, removing titles, brackets, trailing punctuation."""
    if not name:
        return None

    name = name.strip()

    # Remove leading/trailing quotes
    name = name.strip('"\'')

    # Remove trailing punctuation
    name = re.sub(r'[.,;:!?]+$', '', name)

    # Remove bracketed annotations like [bishop of Tours, c.556-573...]
    name = re.sub(r'\s*\[.*?\]', '', name)

    # Remove parenthetical annotations
    name = re.sub(r'\s*\(.*?\)', '', name)

    # Remove trailing "greetings", "greeting", "sends greetings"
    name = re.sub(r',?\s*(sends?\s+)?greetings?\s*$', '', name, flags=re.IGNORECASE)

    # Remove trailing "sends greeting in the Lord" etc.
    name = re.sub(r',?\s*sends?\s+.*$', '', name, flags=re.IGNORECASE)

    name = name.strip(' ,;:—-')

    # Skip if too short or too long
    if len(name) < 2 or len(name) > 100:
        return None

    return name


def normalize_for_matching(name):
    """Normalize a name for fuzzy matching against the authors table."""
    n = name.lower().strip()
    # Remove common titles
    for title in ['bishop ', 'pope ', 'emperor ', 'king ', 'deacon ', 'presbyter ',
                  'monk ', 'count ', 'tribune ', 'senator ', 'consul ', 'prefect ',
                  'saint ', 'st. ', 'blessed ', 'the most illustrious ',
                  'the illustrious ', 'vir illustris ']:
        if n.startswith(title):
            n = n[len(title):]
    # Remove trailing titles
    for suffix in [' the presbyter', ' the deacon', ' the monk', ' the tribune',
                   ' the count', ' the bishop', ' the most illustrious',
                   ' vir illustris']:
        if n.endswith(suffix):
            n = n[:-len(suffix)]
    return n.strip()


# Words/phrases that indicate we DON'T have a real recipient name
SKIP_PATTERNS = [
    'unnamed', 'unknown', 'an inquirer', 'a bishop', 'a monk', 'a person',
    'all bishops', 'all the bishops', 'the clergy', 'the people',
    'various', 'several', 'certain', 'the same', 'the senate',
    'all', 'everyone', 'his', 'her', 'my', 'our', 'their',
    'an unnamed', 'a friend', 'some friends', 'a correspondent',
    'formula', 'not 4', 'migne', 'codd',
]

# Group designations that are valid recipients but not individual authors
GROUP_SKIP = [
    'all the bishops', 'all bishops', 'the clergy', 'the people',
    'the senate', 'the roman senate', 'the dromonarii',
    'the community', 'various bishops',
]


def should_skip_name(name):
    """Return True if this extracted name should be skipped."""
    if not name:
        return True
    lower = name.lower()

    # Skip very generic / unnamed references
    for pat in SKIP_PATTERNS:
        if pat in lower:
            return True

    # Skip if it's just a title with no name
    title_only = re.match(r'^(a |the |an )?(bishop|pope|emperor|king|deacon|presbyter|monk|count|tribune)s?\.?$',
                          lower)
    if title_only:
        return True

    # Skip if starts with number or special chars
    if re.match(r'^[\d\[\(]', name):
        return True

    # Skip if it looks like Latin apparatus
    if re.match(r'^[A-Z]{3,}\s', name) and name == name.upper():
        # All caps like "MIGNE PL 69" - skip
        return True

    return False


def extract_recipient_from_text(text, collection):
    """
    Extract recipient name from the first few lines of modern_english text.
    Returns a cleaned name string or None.
    """
    if not text:
        return None

    lines = text.strip().split('\n')
    first_lines = '\n'.join(lines[:10])  # Check first 10 lines

    # === Pattern 1: "From: ...\nTo: [Name]" header format ===
    # Used by isidore_pelusium, hormisdas, cassiodorus
    to_match = re.search(r'^To:\s*(.+?)(?:\n|$)', first_lines, re.MULTILINE)
    if to_match:
        name = to_match.group(1).strip()
        # Remove "Date:" if it got captured
        name = re.sub(r'\s*Date:.*$', '', name)
        name = clean_name(name)
        if name and not should_skip_name(name):
            return name

    # === Pattern 2: "Gregory to [Name], Bishop of [Place]." ===
    # Also: "Augustine to [Name], greetings."
    # Also: "Pope Pelagius I to [Name]."
    sender_to = re.match(
        r'^(?:(?:Pope\s+)?(?:Gregory|Augustine|Pelagius\s+I|Hormisdas|Gelasius|Felix|Hilary|Simplicius|Innocent|Leo)\s+to\s+)(.+?)(?:\.\s*$|\.\s*\n)',
        lines[0], re.IGNORECASE
    )
    if sender_to:
        name = sender_to.group(1).strip()
        name = clean_name(name)
        if name and not should_skip_name(name):
            return name

    # === Pattern 3: "To [Name], Bishop of [Place]" as first line or after Latin header ===
    # venantius_fortunatus format: "To Vitalis, Bishop of Ravenna"
    for i, line in enumerate(lines[:5]):
        to_line = re.match(r'^To\s+(.+?)(?:\s*$)', line.strip())
        if to_line:
            name = to_line.group(1).strip()
            name = clean_name(name)
            if name and not should_skip_name(name):
                return name

    # === Pattern 4: "KING THEODERIC TO [NAME]" (cassiodorus, all caps) ===
    caps_match = re.match(r'^(?:KING\s+)?THEODER[IO]C\s+TO\s+(.+?)(?:\.\s*$|,)', lines[0])
    if caps_match:
        name = caps_match.group(1).strip()
        # Convert from ALL CAPS to Title Case
        name = name.title()
        name = clean_name(name)
        if name and not should_skip_name(name):
            return name

    # === Pattern 5: "King Theodoric to [Name]" (mixed case) ===
    king_match = re.match(r'^King\s+Theoder[io]c\s+to\s+(.+?)(?:\.\s*$|\.\s*\n|$)', lines[0])
    if king_match:
        name = king_match.group(1).strip()
        name = clean_name(name)
        if name and not should_skip_name(name):
            return name

    # === Pattern 6: Latin header "Ad [Name]" followed by "To [Name]" ===
    # venantius_fortunatus: "I. Ad Vitalem episcopum Ravennensem\nTo Vitalis, Bishop of Ravenna"
    for i, line in enumerate(lines[:5]):
        if line.strip().startswith('Ad ') or re.match(r'^[IVXLCDM]+\.\s+Ad\s+', line.strip()):
            # Look at next lines for "To [Name]"
            for j in range(i+1, min(i+3, len(lines))):
                to_line = re.match(r'^To\s+(.+?)(?:\s*$)', lines[j].strip())
                if to_line:
                    name = to_line.group(1).strip()
                    name = clean_name(name)
                    if name and not should_skip_name(name):
                        return name

    # === Pattern 7: "Book X, Letter Y\n\nTo [Name]" (gregory_great) ===
    for i, line in enumerate(lines[:8]):
        if re.match(r'^To\s+', line.strip()) and not re.match(r'^To\s+(the|my|a|an)\s', line.strip(), re.IGNORECASE):
            name = re.sub(r'^To\s+', '', line.strip())
            name = clean_name(name)
            if name and not should_skip_name(name):
                return name

    # === Pattern 8: Venantius subtitle patterns ===
    # "On the Dedication of Felix's Church" -> Felix
    # "Easter Letter to Felix, Bishop of Nantes" -> Felix, Bishop of Nantes
    # "More Praise of Felix, Bishop of Nantes" -> Felix, Bishop of Nantes
    # "More to Felix, Bishop of Nantes" -> Felix, Bishop of Nantes
    # "Greeting to Gregory" -> Gregory
    # "On His Literary Work — to Hilarius" -> Hilarius
    for i, line in enumerate(lines[:5]):
        # "Easter Letter to [Name]", "More to [Name]", "Greeting to [Name]"
        subtitle_to = re.match(r'^(?:Easter Letter|More|Greeting|On .*?)\s+(?:—\s+)?to\s+(.+?)(?:\s*$)', line.strip())
        if subtitle_to:
            name = subtitle_to.group(1).strip()
            name = clean_name(name)
            if name and not should_skip_name(name):
                return name
        # "More Praise of Felix, Bishop of Nantes"
        praise_of = re.match(r'^More\s+Praise\s+of\s+(.+?)(?:\s*$)', line.strip())
        if praise_of:
            name = praise_of.group(1).strip()
            name = clean_name(name)
            if name and not should_skip_name(name):
                return name
        # "On the Dedication of Felix's Church" -> extract "Felix"
        possessive = re.search(r"(\w+)'s\s+(?:Church|Cathedral|Basilica|Tower|Villa|Estate)", line.strip())
        if possessive:
            # This gives just first name; too ambiguous without more context. Skip.
            pass
        # "To the Citizens of Tours, on Bishop Gregory" -> Gregory
        on_bishop = re.match(r'^To .+?,\s+on\s+Bishop\s+(\w+)', line.strip())
        if on_bishop:
            name = on_bishop.group(1).strip()
            name = clean_name(name)
            if name and not should_skip_name(name):
                return name
        # "To Gregory, on Jews Converted by..." -> Gregory
        to_name_comma = re.match(r'^To\s+(\w+),\s+(?:on|for|About|after|Recommending)', line.strip())
        if to_name_comma:
            name = to_name_comma.group(1).strip()
            name = clean_name(name)
            if name and not should_skip_name(name):
                return name

    # === Pattern 9: "Nectarius to Augustine" (letters TO the collection author) ===
    incoming = re.match(r'^(\w[\w\s]+?)\s+to\s+(Augustine|Gregory|Basil|Jerome)', lines[0])
    if incoming:
        # Skip - recipient should be the collection author, handled differently
        pass

    # === Pattern 10: Venantius "To my holy lord..." with name in 3rd line ===
    # Some letters have "To my holy lord..." but the actual name is on the Ad line
    # "XXI. To my holy lord... Father Avitus [bishop of Clermont]"
    if collection == 'venantius_fortunatus':
        for i, line in enumerate(lines[:3]):
            avitus_match = re.search(r'Father\s+(\w+)\s*\[', line)
            if avitus_match:
                name = avitus_match.group(1).strip()
                name = clean_name(name)
                if name and not should_skip_name(name):
                    return name

    return None


def extract_recipient_name_parts(name):
    """
    Split a complex recipient string into individual names for group letters.
    E.g., "Bacauda and Agnellus, Bishops" -> ["Bacauda", "Agnellus"]
    Returns list of individual name strings, or [name] if not a group.
    """
    # Check for "and" joining names (but not "Bishop of X and Y")
    # "Victor and Columbus, Bishops of Africa" -> ["Victor", "Columbus"]
    # "Eulogius, Bishop of Alexandria, and Anastasius, Bishop of Antioch" -> ["Eulogius", "Anastasius"]

    # For now, return the full name as-is for matching. We'll handle the primary recipient.
    # Complex group extraction would be fragile.
    return [name]


def find_author_match(name, authors_dict, authors_normalized):
    """
    Try to find an existing author that matches the given name.
    Returns author id or None.
    """
    if not name:
        return None

    name_lower = name.lower()
    norm = normalize_for_matching(name)

    # 1. Exact match on name
    if name_lower in authors_dict:
        return authors_dict[name_lower]

    # 2. Exact match on normalized name
    if norm in authors_normalized:
        return authors_normalized[norm]

    # 3. Try matching just the first word (personal name) against authors
    first_word = norm.split(',')[0].split(' of ')[0].strip()
    if len(first_word) >= 3:
        # Look for author whose name contains this first word
        matches = []
        for auth_norm, auth_id in authors_normalized.items():
            if first_word == auth_norm or auth_norm.startswith(first_word + ' ') or auth_norm.startswith(first_word + ','):
                matches.append((auth_norm, auth_id))

        if len(matches) == 1:
            return matches[0][1]

    # 4. Try "Name of Place" pattern
    of_match = re.match(r'^(.+?)\s+of\s+(.+)$', name, re.IGNORECASE)
    if of_match:
        person = of_match.group(1).strip().lower()
        place = of_match.group(2).strip().lower()
        # Search for "Person of Place" in authors
        search_key = f"{person} of {place}"
        if search_key in authors_normalized:
            return authors_normalized[search_key]

    # 5. Try "Bishop Name" -> just "Name"
    title_stripped = re.sub(r'^(bishop|pope|emperor|king|deacon|presbyter|saint|st\.?)\s+',
                            '', name, flags=re.IGNORECASE).strip()
    if title_stripped.lower() != name.lower() and title_stripped.lower() in authors_normalized:
        return authors_normalized[title_stripped.lower()]

    return None


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Backup check
    print(f"Database: {DB_PATH}")
    cur.execute("SELECT COUNT(*) FROM letters WHERE recipient_id IS NULL")
    total_missing = cur.fetchone()[0]
    print(f"Total letters missing recipient_id: {total_missing}")

    # Load all authors for matching
    cur.execute("SELECT id, name FROM authors")
    authors_rows = cur.fetchall()
    # name (lowercase) -> id
    authors_dict = {}
    # normalized name -> id
    authors_normalized = {}
    for row in authors_rows:
        authors_dict[row['name'].lower()] = row['id']
        norm = normalize_for_matching(row['name'])
        authors_normalized[norm] = row['id']

    print(f"Loaded {len(authors_rows)} existing authors")

    # Load letters missing recipients
    cur.execute("""
        SELECT id, collection, modern_english, book, letter_number
        FROM letters
        WHERE recipient_id IS NULL AND modern_english IS NOT NULL
        ORDER BY collection, book, letter_number
    """)
    letters = cur.fetchall()
    print(f"Letters to process (have modern_english): {len(letters)}")

    # Phase 1: Extract all recipient names
    extracted = {}  # letter_id -> extracted name
    name_counts = Counter()  # name -> count of letters
    name_to_letters = defaultdict(list)  # name -> [letter_ids]
    skipped_reasons = Counter()

    for letter in letters:
        lid = letter['id']
        text = letter['modern_english']
        collection = letter['collection']

        name = extract_recipient_from_text(text, collection)
        if name:
            extracted[lid] = name
            name_counts[name] += 1
            name_to_letters[name].append(lid)
        else:
            skipped_reasons['no_pattern_match'] += 1

    print(f"\nPhase 1 - Extraction:")
    print(f"  Extracted recipient names from {len(extracted)} letters")
    print(f"  Unique names found: {len(name_counts)}")
    print(f"  No pattern match: {skipped_reasons['no_pattern_match']}")

    # Show top extracted names
    print(f"\n  Top 30 extracted names:")
    for name, count in name_counts.most_common(30):
        print(f"    {name}: {count} letters")

    # Phase 2: Match names to existing authors or create new ones
    assigned = 0
    new_authors_created = 0
    skipped_single = 0
    skipped_no_match = 0

    # First pass: match against existing authors
    name_to_author_id = {}
    names_needing_creation = []

    # High-confidence single-mention names: those with a title/role indicator
    high_conf_pattern = re.compile(
        r'\b(Bishop|Deacon|Presbyter|Subdeacon|Pope|Emperor|King|Queen|Count|Tribune|Abbot|Abbess|Patrician|Defender|Governor|Consul|Prefect)\b',
        re.IGNORECASE
    )

    for name in name_counts:
        author_id = find_author_match(name, authors_dict, authors_normalized)
        if author_id:
            name_to_author_id[name] = author_id
        elif name_counts[name] >= 2:
            names_needing_creation.append(name)
        elif high_conf_pattern.search(name):
            # Single-mention but has a title -> high confidence, create author
            names_needing_creation.append(name)
        else:
            skipped_single += 1

    print(f"\nPhase 2 - Matching:")
    print(f"  Matched to existing authors: {len(name_to_author_id)}")
    print(f"  Need new author entries (2+ letters): {len(names_needing_creation)}")
    print(f"  Skipped (single mention): {skipped_single}")

    # Create new authors for names appearing in 2+ letters
    for name in names_needing_creation:
        # Extract role from name if present
        role = None
        clean = name
        role_match = re.search(r'\b(Bishop|Pope|Emperor|King|Deacon|Presbyter|Monk|Count|Tribune|Senator|Consul|Prefect)\b',
                               name, re.IGNORECASE)
        if role_match:
            role = role_match.group(1).lower()

        # Clean up the name for the author entry
        # Remove trailing title descriptions like ", Bishop of Tours"
        author_name = re.sub(r',\s*(Bishop|Pope|Emperor|King|Deacon|Presbyter|Monk|Count|Tribune|Senator)\s+.*$',
                             '', name, flags=re.IGNORECASE)
        # But keep "of Place" if it's part of the name like "Felix of Nantes"
        # Remove "the Presbyter", "the Deacon" etc for cleaner name
        author_name = re.sub(r'\s+the\s+(Presbyter|Deacon|Monk|Tribune|Count|Most Illustrious)$',
                             '', author_name, flags=re.IGNORECASE)
        author_name = author_name.strip(' ,;')

        # Check this cleaned name doesn't already exist
        if author_name.lower() in authors_dict:
            name_to_author_id[name] = authors_dict[author_name.lower()]
            continue

        # Also check normalized
        norm_check = normalize_for_matching(author_name)
        if norm_check in authors_normalized:
            name_to_author_id[name] = authors_normalized[norm_check]
            continue

        try:
            cur.execute("INSERT INTO authors (name, role) VALUES (?, ?)",
                        (author_name, role))
            new_id = cur.lastrowid
            name_to_author_id[name] = new_id
            authors_dict[author_name.lower()] = new_id
            authors_normalized[normalize_for_matching(author_name)] = new_id
            new_authors_created += 1
            if new_authors_created <= 30:
                print(f"    Created author: '{author_name}' (role={role}, id={new_id}, {name_counts[name]} letters)")
        except sqlite3.IntegrityError:
            # Name already exists (race condition or variant)
            cur.execute("SELECT id FROM authors WHERE name = ?", (author_name,))
            row = cur.fetchone()
            if row:
                name_to_author_id[name] = row['id']

    if new_authors_created > 30:
        print(f"    ... and {new_authors_created - 30} more")

    # Phase 3: Assign recipient_ids
    for lid, name in extracted.items():
        if name in name_to_author_id:
            cur.execute("UPDATE letters SET recipient_id = ? WHERE id = ?",
                        (name_to_author_id[name], lid))
            assigned += 1

    conn.commit()

    # Report results
    cur.execute("SELECT COUNT(*) FROM letters WHERE recipient_id IS NULL")
    still_missing = cur.fetchone()[0]

    print(f"\n{'='*60}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"Recipients assigned:      {assigned}")
    print(f"New authors created:      {new_authors_created}")
    print(f"Still missing recipient:  {still_missing} (was {total_missing})")
    print(f"Improvement:              {total_missing - still_missing} letters fixed")

    # Per-collection breakdown
    print(f"\nPer-collection breakdown:")
    cur.execute("""
        SELECT collection,
               COUNT(*) as total,
               SUM(CASE WHEN recipient_id IS NULL THEN 1 ELSE 0 END) as missing
        FROM letters
        GROUP BY collection
        ORDER BY missing DESC
    """)
    for row in cur.fetchall():
        total = row['total']
        missing = row['missing']
        pct = ((total - missing) / total * 100) if total > 0 else 0
        print(f"  {row['collection']:30s}: {total:4d} total, {missing:4d} missing, {pct:5.1f}% coverage")

    # Show unmatched names (appeared 2+ times but no author found/created)
    unmatched_multi = [(n, c) for n, c in name_counts.items()
                       if n not in name_to_author_id and c >= 2]
    if unmatched_multi:
        print(f"\nUnmatched names (2+ occurrences, not assigned):")
        for name, count in sorted(unmatched_multi, key=lambda x: -x[1])[:20]:
            print(f"    {name}: {count} letters")

    conn.close()
    print("\nDone.")


if __name__ == '__main__':
    main()

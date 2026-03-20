#!/usr/bin/env python3
"""
enrich_relationships.py — Scan letter texts for people mentions and fix null recipients.

1. For letters WITH modern_english (or english_text), scan for names of known authors.
   When a known person is mentioned but isn't the sender or recipient, add to people_mentioned.
2. For letters where recipient_id IS NULL, try to match "To [Name]" patterns to known authors.
3. Print progress and summary stats.
"""

import sqlite3
import re
from collections import defaultdict

DB_PATH = "/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db"

# Common English words that appear as first words in group/institutional "author" names.
# These must never be used as name-search tokens.
COMMON_WORD_BLOCKLIST = {
    "people", "church", "another", "various", "certain", "synod",
    "comes", "learned", "brethren", "citizens", "clergy", "martyrs",
    "confessors", "monks", "nobles", "soldiers", "presbyters",
    "neapolitans", "virgins", "bishops", "unknown", "concerning",
    "enclosed", "council", "inhabitants", "congregation", "about",
    "against", "before", "letter", "letters", "those", "their",
    "which", "whose", "there", "these", "other", "every", "after",
    "would", "could", "should", "being", "where", "while", "since",
    "under", "above", "below", "along", "among", "between", "within",
    "without", "through", "during", "until", "might", "never",
    "always", "often", "still", "again", "already", "perhaps",
    "rather", "indeed", "truly", "first", "second", "third",
    "great", "greater", "whole", "right", "order", "place", "point",
    "things", "times", "world", "power", "state", "hands", "words",
    "works", "honor", "peace", "grace", "glory", "faith", "truth",
    "spirit", "master", "father", "brother", "sister", "mother",
    "friend", "bishop", "priest", "deacon", "saint", "emperor",
    "count", "judge", "prefect", "consul", "tribune", "primate",
    "envoy", "legate", "abbot", "general",
    "governor", "senator", "senate", "patriarch", "archdeacon",
    "deacons", "patriarch", "matron", "widow", "writer",
    "censitor", "soldier", "accountant", "assessor",
    "patrician", "exarch", "guardian", "archimandrite",
    "presbyter", "metropolitan", "subdeacon", "oeconomus",
    # Latin common words that appear in names
    "sanctus", "beatus", "frater", "pater",
    "dominus", "domini", "comes",
    # Descriptive terms used as author name prefixes
    "heretic", "heresy", "apostate", "sophist",
}

# Author IDs that are groups/institutions, not individual people.
# These should only match on their full name, never on partial tokens.
GROUP_AUTHOR_IDS = set()


def is_individual_person(name):
    """Heuristic: return False if the 'author' name looks like a group or institution."""
    lower = name.lower()
    group_markers = [
        "people of", "church of", "citizens of", "monks",
        "brethren", "synod of", "council of", "clergy",
        "confessors", "martyrs", "presbyters", "soldiers",
        "congregation", "inhabitants", "nobles and",
        "bishops of", "virgins of", "various ", "certain ",
        "another ", "learned ", "enclosed ",
        "concerning ", "faction of",
    ]
    return not any(marker in lower for marker in group_markers)


def build_name_index(authors):
    """
    Build a lookup from name variants -> author_id.
    Only generates short-name tokens for actual individual people.
    """
    name_to_id = {}
    short_name_counts = defaultdict(list)

    for author_id, name, name_latin, role in authors:
        name_lower = name.lower().strip()

        # Full name always maps (for groups too — but they require exact full match)
        name_to_id[name_lower] = author_id

        if not is_individual_person(name):
            GROUP_AUTHOR_IDS.add(author_id)
            continue

        # Latin full name
        if name_latin and name_latin.strip():
            name_to_id[name_latin.lower().strip()] = author_id
            # Individual parts of latin name (>= 6 chars for safety)
            for part in name_latin.strip().split():
                cleaned = part.strip("(),")
                if len(cleaned) >= 6 and cleaned.lower() not in COMMON_WORD_BLOCKLIST:
                    short_name_counts[cleaned.lower()].append(author_id)

        # Handle "Pope X", "Emperor X" — add the rest as a variant
        titles = ["pope", "emperor", "saint", "st."]
        for title in titles:
            if name_lower.startswith(title + " "):
                rest = name[len(title) + 1:].strip()
                if len(rest) >= 6:
                    name_to_id[rest.lower()] = author_id

        # First name from English name (>= 6 chars to avoid "Peter", "James", etc.)
        parts = name.split()
        if len(parts) >= 1:
            first = parts[0].strip("(),")
            if len(first) >= 6 and first.lower() not in COMMON_WORD_BLOCKLIST:
                short_name_counts[first.lower()].append(author_id)

        # "Name of Place" — add full form
        if " of " in name and len(name) >= 8:
            name_to_id[name_lower] = author_id

    # Only add short names that uniquely map to one author
    for short_name, ids in short_name_counts.items():
        unique_ids = list(set(ids))
        if len(unique_ids) == 1:
            name_to_id[short_name] = unique_ids[0]

    # Remove any key that is a common English word or too short
    for k in list(name_to_id.keys()):
        if len(k) < 5:
            del name_to_id[k]
            continue
        # Check if the key itself is a blocked word
        if k in COMMON_WORD_BLOCKLIST:
            del name_to_id[k]
            continue
        # Check if key is a single word that is blocked
        if " " not in k and k.split(",")[0].strip() in COMMON_WORD_BLOCKLIST:
            del name_to_id[k]

    return name_to_id


def find_mentions_in_text(text, name_to_id, sender_id, recipient_id):
    """Find all known people mentioned in text, excluding sender and recipient."""
    if not text:
        return set()

    text_lower = text.lower()
    found = set()

    for name, author_id in name_to_id.items():
        if author_id == sender_id or author_id == recipient_id:
            continue
        # Skip group authors for text scanning — too many false positives
        if author_id in GROUP_AUTHOR_IDS:
            continue
        # Require name to be at least 6 chars for text scanning
        if len(name) < 6:
            continue

        idx = text_lower.find(name)
        while idx != -1:
            # Check word boundaries
            before_ok = (idx == 0) or not text_lower[idx - 1].isalpha()
            after_pos = idx + len(name)
            after_ok = (after_pos >= len(text_lower)) or not text_lower[after_pos].isalpha()
            if before_ok and after_ok:
                found.add(author_id)
                break
            idx = text_lower.find(name, idx + 1)

    return found


def try_match_recipient(text, name_to_id, all_authors_by_id):
    """
    Try to extract recipient from letter text.
    Patterns:
      - "To: Name" in structured header
      - "To Name —" at start
      - "SenderName to RecipientName, greetings"
      - "To my [adjectives] Name, ..."
    """
    if not text:
        return None

    header = text[:500]

    # Pattern 1: "To: Name" structured header
    m = re.search(r'(?:^|\n)\s*To:\s*(.+?)(?:\n|$)', header)
    if m:
        match = match_name_to_author(m.group(1).strip(), name_to_id, all_authors_by_id)
        if match:
            return match

    # Pattern 2: "To Name —" or "To Name," at start (after optional "Letter N..." header)
    m = re.match(r'^(?:Letter \d+.*?\n\n)?To\s+(.+?)(?:\s*[—–\-,])', header)
    if m:
        match = match_name_to_author(m.group(1).strip(), name_to_id, all_authors_by_id)
        if match:
            return match

    # Pattern 3: "SenderName to RecipientName, greetings/my/sends"
    m = re.match(
        r'^(?:Letter \d+.*?\n\n)?(\w+)\s+to\s+(.+?)(?:\s*,\s*(?:my|greetings|greeting|sends|bishop))',
        header, re.IGNORECASE
    )
    if m:
        match = match_name_to_author(m.group(2).strip(), name_to_id, all_authors_by_id)
        if match:
            return match

    # Pattern 3b: "Name to Name." (period-terminated, no "greetings")
    m = re.match(
        r'^(?:Letter \d+.*?\n\n)?([\w\s]+?)\s+to\s+([\w\s]+?)\.\s*\n',
        header, re.IGNORECASE
    )
    if m:
        match = match_name_to_author(m.group(2).strip(), name_to_id, all_authors_by_id)
        if match:
            return match

    # Pattern 3c: "Name to Name, greetings" with "sends greeting" variant
    m = re.match(
        r'^(?:Letter \d+.*?\n\n)?[\w\s,]+?\s+to\s+(.+?)(?:\s*[—–\-]\s*|\s*,\s*)(?:greetings?|sends?\s+greeting)',
        header, re.IGNORECASE
    )
    if m:
        match = match_name_to_author(m.group(1).strip(), name_to_id, all_authors_by_id)
        if match:
            return match

    # Pattern 4: "To my [lord/noble/...] Name, ..." or "To ... Name sends greeting"
    m = re.search(
        r'(?:^|\n)To\s+(?:my\s+)?'
        r'(?:lord|noble|honourable|venerable|beloved|esteemed|dearest|excellent|'
        r'holy|blessed|brother|father|son|friend|colleague|reverend|[\w,\s]{1,40}?)\s+'
        r'(\w[\w\s]{2,30}?)(?:\s*[,;—–\-]|\s+sends?\s+greeting)',
        header, re.IGNORECASE
    )
    if m:
        match = match_name_to_author(m.group(1).strip(), name_to_id, all_authors_by_id)
        if match:
            return match

    return None


def match_name_to_author(text, name_to_id, all_authors_by_id=None):
    """Try to match a recipient text to a known author."""
    text_clean = text.strip().rstrip(',.;:').strip()
    text_lower = text_clean.lower()

    # Direct match
    if text_lower in name_to_id:
        return name_to_id[text_lower]

    # Check if any known name appears at the start, prefer longest match
    for name, author_id in sorted(name_to_id.items(), key=lambda x: -len(x[0])):
        if text_lower.startswith(name):
            return author_id

    # Check if text contains a known name (>= 6 chars)
    for name, author_id in sorted(name_to_id.items(), key=lambda x: -len(x[0])):
        if len(name) >= 6 and name in text_lower:
            if author_id not in GROUP_AUTHOR_IDS:
                return author_id

    # Try matching first word from the text against author names
    # This catches "Augustine, Bishop of Hippo" -> first word "augustine"
    words = text_lower.split()
    if words:
        first_word = words[0].strip("(),")
        if len(first_word) >= 6:
            if first_word in name_to_id:
                return name_to_id[first_word]
            # Even if first_word was ambiguous (excluded from name_to_id),
            # try to find it as the first word of a real person's name
            if all_authors_by_id:
                candidates = []
                for aid, aname in all_authors_by_id.items():
                    if aid in GROUP_AUTHOR_IDS:
                        continue
                    aname_lower = aname.lower()
                    # Match "augustine" -> "Augustine of Hippo" (first word match)
                    aname_first = aname_lower.split()[0].strip("(),")
                    if aname_first == first_word:
                        # Prefer authors whose name pattern is "Name of Place"
                        if " of " in aname_lower:
                            candidates.insert(0, aid)
                        else:
                            candidates.append(aid)
                if len(candidates) == 1:
                    return candidates[0]
                elif candidates:
                    # If there's one with "of" pattern, prefer it
                    return candidates[0]

    return None


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    # Load all authors
    cur.execute("SELECT id, name, name_latin, role FROM authors ORDER BY id")
    authors = cur.fetchall()
    all_authors_by_id = {a[0]: a[1] for a in authors}
    print(f"Loaded {len(authors)} authors from database")

    # Build name index
    name_to_id = build_name_index(authors)
    print(f"Built name index with {len(name_to_id)} searchable name variants")
    print(f"Identified {len(GROUP_AUTHOR_IDS)} group/institutional 'authors' (excluded from text scan)")

    # Show sample entries
    sample_items = sorted(name_to_id.items(), key=lambda x: x[0])[:15]
    for name, aid in sample_items:
        tag = " [GROUP]" if aid in GROUP_AUTHOR_IDS else ""
        print(f"  '{name}' -> #{aid} ({all_authors_by_id.get(aid, '?')}){tag}")
    print(f"  ... and {len(name_to_id) - 15} more\n")

    # =========================================================================
    # PHASE 0: Clear previous run data (idempotent re-runs)
    # =========================================================================
    cur.execute("SELECT COUNT(*) FROM people_mentioned")
    old_count = cur.fetchone()[0]
    if old_count > 0:
        print(f"Clearing {old_count} existing people_mentioned rows from previous run...")
        cur.execute("DELETE FROM people_mentioned")
        conn.commit()

    # Also reset recipient_id values we may have set in a previous run.
    # We only reset ones that were NULL before our first run — tracked by
    # the fact that we don't have a "before" snapshot. So we skip this
    # to avoid data loss. Phase 2 will only fill NULLs.

    # =========================================================================
    # PHASE 1: Scan texts for people mentions
    # =========================================================================
    print("=" * 70)
    print("PHASE 1: Scanning letter texts for people mentions")
    print("=" * 70)

    existing_mentions = set()

    cur.execute("""
        SELECT id, sender_id, recipient_id, modern_english, english_text
        FROM letters
        WHERE modern_english IS NOT NULL AND modern_english != ''
           OR english_text IS NOT NULL AND english_text != ''
    """)
    letters = cur.fetchall()
    print(f"Letters with text to scan: {len(letters)}\n")

    mentions_added = 0
    letters_with_mentions = 0
    mention_counts = defaultdict(int)

    for i, (letter_id, sender_id, recipient_id, modern_english, english_text) in enumerate(letters):
        text = modern_english if modern_english else english_text
        if not text:
            continue

        found = find_mentions_in_text(text, name_to_id, sender_id, recipient_id)

        if found:
            letters_with_mentions += 1

        for person_id in found:
            if (letter_id, person_id) not in existing_mentions:
                cur.execute(
                    "INSERT INTO people_mentioned (letter_id, person_id, role_in_letter) VALUES (?, ?, 'mentioned')",
                    (letter_id, person_id)
                )
                existing_mentions.add((letter_id, person_id))
                mentions_added += 1
                mention_counts[person_id] += 1

        if (i + 1) % 200 == 0:
            print(f"  Scanned {i + 1}/{len(letters)} letters... ({mentions_added} mentions added so far)")

    conn.commit()

    print(f"\n  Total mentions added: {mentions_added}")
    print(f"  Letters with at least one mention: {letters_with_mentions}")
    if mention_counts:
        print(f"\n  Top 25 most-mentioned people:")
        for person_id, count in sorted(mention_counts.items(), key=lambda x: -x[1])[:25]:
            print(f"    {all_authors_by_id.get(person_id, '?')} (#{person_id}): mentioned in {count} letters")

    # =========================================================================
    # PHASE 2: Fix null recipients
    # =========================================================================
    print("\n" + "=" * 70)
    print("PHASE 2: Matching null recipients from letter text")
    print("=" * 70)

    cur.execute("""
        SELECT id, sender_id, modern_english, english_text
        FROM letters
        WHERE recipient_id IS NULL
          AND (modern_english IS NOT NULL AND modern_english != ''
               OR english_text IS NOT NULL AND english_text != '')
    """)
    null_recip_letters = cur.fetchall()
    print(f"Letters with NULL recipient_id and text: {len(null_recip_letters)}\n")

    recipients_fixed = 0
    fixes = []

    for letter_id, sender_id, modern_english, english_text in null_recip_letters:
        text = modern_english if modern_english else english_text
        matched_id = try_match_recipient(text, name_to_id, all_authors_by_id)
        if matched_id and matched_id != sender_id:
            cur.execute("UPDATE letters SET recipient_id = ? WHERE id = ?", (matched_id, letter_id))
            recipients_fixed += 1
            fixes.append((letter_id, all_authors_by_id.get(matched_id, '?')))

    conn.commit()

    print(f"  Recipients matched and set: {recipients_fixed}")
    if fixes:
        print(f"\n  All recipient fixes:")
        for letter_id, name in fixes:
            print(f"    Letter #{letter_id} -> {name}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    cur.execute("SELECT COUNT(*) FROM people_mentioned")
    total_mentions = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT person_id) FROM people_mentioned")
    unique_people = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT letter_id) FROM people_mentioned")
    letters_with = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM letters WHERE recipient_id IS NULL")
    still_null = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM letters WHERE recipient_id IS NOT NULL")
    has_recip = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM letters")
    total_letters = cur.fetchone()[0]

    print(f"  Total letters in database:       {total_letters}")
    print(f"  people_mentioned rows total:     {total_mentions}")
    print(f"  Unique people mentioned:         {unique_people}")
    print(f"  Letters with mentions:           {letters_with}")
    print(f"  New mentions added (this run):   {mentions_added}")
    print(f"  Recipients fixed (this run):     {recipients_fixed}")
    print(f"  Letters with recipient_id set:   {has_recip}")
    print(f"  Letters still missing recipient:  {still_null}")
    print(f"  Recipient coverage:              {has_recip}/{total_letters} ({100*has_recip/total_letters:.1f}%)")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

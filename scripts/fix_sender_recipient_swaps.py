#!/usr/bin/env python3
"""
Audit and fix sender/recipient mislabeling in the Roman Letters database.

Many letter collections include replies from correspondents, but all letters
in a collection are often labeled as FROM the collection author. This script
detects and fixes these by analyzing text headers in english_text and modern_english.

Conservative approach: only swaps when the text clearly indicates a different sender.
"""

import sqlite3
import re
import sys
from collections import defaultdict

DB_PATH = '/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db'

# Whether to actually apply fixes or just report
DRY_RUN = '--dry-run' in sys.argv

# Words that should never be treated as sender names
SKIP_NAMES = {
    'the', 'your', 'his', 'her', 'my', 'our', 'their', 'from', 'letter',
    'epistle', 'argument', 'chapter', 'about', 'please', 'source',
    'translated', 'revised', 'edited', 'king', 'lord', 'most', 'holy',
    'blessed', 'beloved', 'reverend', 'venerable', 'dearest',
}


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_author_name_variants(name):
    """Generate common short-form variants for matching in text headers."""
    variants = set()
    variants.add(name)

    parts = name.split()
    if parts:
        variants.add(parts[0])

    if parts[0] == 'Pope' and len(parts) > 1:
        variants.add(parts[1])

    if len(parts) >= 3:
        variants.add(parts[-1])

    if len(parts) == 2:
        variants.add(parts[0])
        variants.add(parts[1])

    if 'the' in parts:
        idx = parts.index('the')
        if idx > 0:
            variants.add(parts[idx - 1])

    if 'of' in parts:
        idx = parts.index('of')
        if idx > 0:
            variants.add(parts[idx - 1])

    KNOWN_SHORT = {
        'Augustine of Hippo': ['Augustine'],
        'Jerome': ['Jerome'],
        'Basil of Caesarea': ['Basil'],
        'Gregory of Nazianzus': ['Gregory Nazianzus', 'Gregory'],
        'Pope Gregory the Great': ['Gregory'],
        'Pope Leo the Great': ['Leo'],
        'Cyprian of Carthage': ['Cyprian'],
        'Sidonius Apollinaris': ['Sidonius'],
        'Quintus Aurelius Symmachus': ['Symmachus'],
        'John Chrysostom': ['Chrysostom', 'John'],
        'Paulinus of Nola': ['Paulinus'],
        'Pliny the Younger': ['Pliny'],
        'Ambrose of Milan': ['Ambrose'],
        'Theodoret of Cyrrhus': ['Theodoret'],
        'Alcuin of York': ['Alcuin'],
        'Avitus of Vienne': ['Avitus'],
        'Ruricius of Limoges': ['Ruricius'],
        'Ennodius of Pavia': ['Ennodius'],
        'Faustus of Riez': ['Faustus'],
        'Athanasius of Alexandria': ['Athanasius'],
        'Isidore of Pelusium': ['Isidore'],
        'Synesius of Cyrene': ['Synesius'],
        'Julian the Apostate': ['Julian'],
        'Desiderius of Cahors': ['Desiderius'],
        'Braulio of Zaragoza': ['Braulio'],
        'Salvian of Marseille': ['Salvian'],
        'Sulpicius Severus': ['Sulpicius'],
        'Venantius Fortunatus': ['Venantius', 'Fortunatus'],
        'Ferrandus of Carthage': ['Ferrandus'],
        'Caesarius of Arles': ['Caesarius'],
        'Columbanus': ['Columbanus'],
        'Boniface': ['Boniface'],
        'Bede': ['Bede'],
        'Cassiodorus': ['Cassiodorus'],
        'Libanius': ['Libanius'],
        'Gelasius I': ['Gelasius'],
        'Hormisdas': ['Hormisdas'],
        'Innocent I': ['Innocent'],
        'Simplicius': ['Simplicius'],
        'Symmachus (Pope)': ['Symmachus'],
        'Pope Benedict I': ['Benedict'],
        'Pope Pelagius II': ['Pelagius'],
        'Pope Pelagius I': ['Pelagius'],
        'Agapetus I': ['Agapetus'],
        'Anastasius II': ['Anastasius'],
        'Pope Felix III': ['Felix'],
        'Pope Hilary': ['Hilary'],
        'John II (Pope)': ['John'],
        'Pope John III': ['John'],
        'Vigilius (Pope)': ['Vigilius'],
    }

    if name in KNOWN_SHORT:
        for v in KNOWN_SHORT[name]:
            variants.add(v)

    return variants


def find_author_by_name(cursor, name_fragment):
    """
    Try to find an author in the DB by a name fragment.
    Prefers exact matches, then name-starts-with, then contains.
    Among multiple matches, prefers shorter names (more likely the actual person).
    """
    # Skip bogus names
    if name_fragment.lower() in SKIP_NAMES:
        return None, None
    if len(name_fragment) < 3:
        return None, None

    # Clean up the fragment
    name_fragment = name_fragment.strip()
    # Remove trailing punctuation
    name_fragment = re.sub(r'[.,;:]+$', '', name_fragment)

    # Exact match first
    row = cursor.execute(
        "SELECT id, name FROM authors WHERE name = ?", (name_fragment,)
    ).fetchone()
    if row:
        return row['id'], row['name']

    # Name starts with fragment followed by non-alpha (e.g., "Cornelius," or "Cornelius ")
    # This indicates the fragment IS the person's primary name
    rows = cursor.execute(
        "SELECT id, name FROM authors WHERE name LIKE ? ORDER BY LENGTH(name) ASC",
        (f'{name_fragment}%',)
    ).fetchall()

    if rows:
        # Prefer: exact name match with a qualifier (comma, "of", "the")
        # e.g., "Cornelius" should match "Cornelius, on Refusal..." over "Cornelius Ursus"
        # because "Cornelius Ursus" means Cornelius is a praenomen, not the person's identifier
        for row in rows:
            rname = row['name']
            rest = rname[len(name_fragment):]
            # Fragment IS the full name, or followed by qualifier
            if not rest or rest[0] in (',', ' ') and (
                rest.startswith(', ') or rest.startswith(' of ') or
                rest.startswith(' the ') or rest.startswith(' I') or
                rest.startswith(' (') or not rest.strip()
            ):
                return row['id'], row['name']
        # Fall back to shortest match
        return rows[0]['id'], rows[0]['name']

    # "X of Y" pattern: "Theophilus" -> "Theophilus of Alexandria"
    rows = cursor.execute(
        "SELECT id, name FROM authors WHERE name LIKE ? ORDER BY LENGTH(name) ASC",
        (f'{name_fragment} of %',)
    ).fetchall()
    if rows:
        return rows[0]['id'], rows[0]['name']

    # "Pope X" pattern
    rows = cursor.execute(
        "SELECT id, name FROM authors WHERE name LIKE ? ORDER BY LENGTH(name) ASC",
        (f'Pope {name_fragment}%',)
    ).fetchall()
    if rows:
        return rows[0]['id'], rows[0]['name']

    # General contains (less reliable, require the fragment to be a significant part)
    rows = cursor.execute(
        "SELECT id, name FROM authors WHERE name LIKE ? ORDER BY LENGTH(name) ASC",
        (f'%{name_fragment}%',)
    ).fetchall()
    for row in rows:
        if len(name_fragment) >= len(row['name']) * 0.4:
            return row['id'], row['name']

    return None, None


def is_valid_sender_name(name):
    """Check if a potential sender name looks legitimate."""
    if not name:
        return False
    name_lower = name.lower().strip()
    if name_lower in SKIP_NAMES:
        return False
    if len(name_lower) < 3:
        return False
    # Must start with uppercase
    if not name[0].isupper():
        return False
    # Must not be just a title
    titles = {'bishop', 'pope', 'patriarch', 'archbishop', 'presbyter',
              'deacon', 'emperor', 'king', 'prince', 'senator'}
    if name_lower in titles:
        return False
    return True


def extract_sender_from_header(text, author_variants, collection_author_id, cursor):
    """
    Analyze the first ~500 chars of a letter's text to determine actual sender.

    Returns (actual_sender_id, actual_sender_name, evidence) or (None, None, None)
    if no swap is needed.
    """
    if not text:
        return None, None, None

    header = text[:500]

    # Build regex-safe author variants
    author_re_parts = sorted(author_variants, key=len, reverse=True)
    author_pattern = '|'.join(re.escape(v) for v in author_re_parts)

    def check_sender(sender_text, evidence_template):
        """Helper: validate a sender candidate and return result or None."""
        if not is_valid_sender_name(sender_text):
            return None
        # Check it's not the collection author
        is_author = any(v.lower() == sender_text.lower() for v in author_variants)
        if is_author:
            return None
        # Don't match "Pope [Author]" as a different person
        cleaned = re.sub(r'^(?:Pope|Saint|St\.?)\s+', '', sender_text)
        is_author_cleaned = any(v.lower() == cleaned.lower() for v in author_variants)
        if is_author_cleaned:
            return None
        sid, sname = find_author_by_name(cursor, sender_text)
        if sid and sid != collection_author_id:
            return sid, sname, evidence_template.format(sender=sender_text)
        return None

    # PATTERN 1: "From [SomeName] to [AuthorVariant]" or "From [SomeName]" on its own line
    # e.g. "From Pope Damasus", "From Theophilus to Jerome"
    m = re.search(
        r'^(?:Letter\s+\d+[^.\n]*\n+)?From\s+(.+?)(?:\s+to\s+(?:' + author_pattern + r'))?\.?\s*$',
        header, re.MULTILINE | re.IGNORECASE
    )
    if m:
        sender_text = m.group(1).strip()
        # Remove "Pope" prefix for lookup but keep for display
        result = check_sender(sender_text, 'Header: "From {sender}"')
        if result:
            return result
        # Try without "Pope" prefix
        if sender_text.startswith('Pope '):
            result = check_sender(sender_text[5:], 'Header: "From {sender}"')
            if result:
                return result

    # PATTERN 2: "To [AuthorVariant] [SomeName] Sends Greeting"
    # e.g. "To Augustine Nebridius Sends Greeting"
    m = re.search(
        r'To\s+(?:(?:My\s+)?(?:Most\s+)?(?:Beloved\s+|Venerable\s+|Holy\s+|Reverend\s+)?'
        r'(?:Lord\s+(?:and\s+\w+\s+)*)?(?:Brother\s+(?:and\s+\w+\s+)*)?(?:Father\s+(?:and\s+\w+\s+)*)?)?'
        r'(?:' + author_pattern + r')'
        r'[,\s]+(?:(?:Our\s+|My\s+)?(?:Lord\s+(?:and\s+\w+\s+)*)?(?:Brother\s+(?:and\s+\w+\s+)*)?)?'
        r'([A-Z][a-z]+(?:\s+(?:and\s+)?[A-Z][a-z]+)*)\s+Sends?\s+Greeting',
        header, re.IGNORECASE
    )
    if m:
        sender_text = m.group(1).strip()
        sender_text = re.sub(r'\s+(?:in\s+(?:the\s+)?(?:Lord|Christ)).*', '', sender_text)
        result = check_sender(sender_text, 'Greeting: "{sender} Sends Greeting" to author')
        if result:
            return result

    # PATTERN 3: "[SomeName] to [AuthorVariant]" at start of a line
    # e.g. "Caldonius to Cyprian", "Libanius to Basil"
    for line in header.split('\n')[:12]:
        line = line.strip()
        if not line:
            continue
        # Skip obvious non-header lines
        if line.startswith('Please help') or line.startswith('About this'):
            continue

        m = re.match(
            r'^(?:(?:The\s+)?(?:Confessors|Presbyters|Deacons|Roman Clergy|Clergy|Bishops|'
            r'Council|Synod)\s+(?:(?:and\s+)?(?:Confessors|Presbyters|Deacons|Clergy|Bishops)\s+)*'
            r'(?:Abiding\s+)?(?:at\s+\w+\s*,?\s*)?)?'
            r'([A-Z][A-Za-z]+(?:(?:\s+(?:of|the|and|I|II|III|IV))*\s+[A-Z][A-Za-z]+)*)'
            r'\s+to\s+(?:' + author_pattern + r')(?:\b)',
            line, re.IGNORECASE
        )
        if m:
            sender_text = m.group(1).strip()
            if sender_text.lower() in ('letter', 'epistle', 'from', 'argument', 'a'):
                continue
            result = check_sender(sender_text, 'Header line: "{sender} to [author]"')
            if result:
                return result

    # PATTERN 4: "[Letter N:] From [Author2] to [Author1] (date)"
    # e.g. "From Jerome to Augustine (A.D. 397)"
    m = re.search(
        r'From\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+to\s+(?:' + author_pattern + r')',
        header, re.IGNORECASE
    )
    if m:
        sender_text = m.group(1).strip()
        result = check_sender(sender_text, 'Header: "From {sender} to [author]"')
        if result:
            return result

    # PATTERN 5: "To his ... [AuthorVariant] — [SomeName] sends greeting"
    m = re.search(
        r'To\s+(?:his\s+)?(?:[\w\s,]+?\s+)?(?:' + author_pattern + r')'
        r'\s*[—\-,]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+sends?\s+greeting',
        header, re.IGNORECASE
    )
    if m:
        sender_text = m.group(1).strip()
        result = check_sender(sender_text, 'Greeting: "{sender} sends greeting" to author')
        if result:
            return result

    # PATTERN 6: "[Someone], Bishop/Pope of [Place], to [AuthorVariant]"
    m = re.search(
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+'
        r'(?:Bishop|Pope|Patriarch|Archbishop|Presbyter|Deacon|bishop|pope)'
        r'(?:\s+of\s+\w+)?,?\s+to\s+(?:the\s+)?(?:most\s+)?(?:holy\s+)?(?:' + author_pattern + r')',
        header, re.IGNORECASE
    )
    if m:
        sender_text = m.group(1).strip()
        result = check_sender(sender_text, 'Header: "{sender}, [title] to [author]"')
        if result:
            return result

    # PATTERN 7: "L Trajan to Pliny" (Pliny Book 10 pattern, with "L" = Latin praenomen initial)
    m = re.search(
        r'^(?:L\s+)?([A-Z][a-z]+)\s+to\s+(?:' + author_pattern + r')\.',
        header, re.MULTILINE | re.IGNORECASE
    )
    if m:
        sender_text = m.group(1).strip()
        result = check_sender(sender_text, 'Header: "{sender} to [author]"')
        if result:
            return result

    # PATTERN 8: "[From SomeName to AuthorVariant]" in brackets (modern_english pattern)
    m = re.search(
        r'\[From\s+([A-Z][A-Za-z]+(?:\s+[A-Za-z]+)*)\s+to\s+(?:' + author_pattern + r')\]',
        header, re.IGNORECASE
    )
    if m:
        sender_text = m.group(1).strip()
        result = check_sender(sender_text, 'Bracket header: "[From {sender} to author]"')
        if result:
            return result

    # PATTERN 9: "From: [Name]\nTo: [AuthorVariant]" (structured modern_english headers)
    m = re.search(
        r'From:\s*([A-Z][A-Za-z]+(?:[\s,]+[A-Za-z]+)*)\s*\n\s*To:\s*(?:' + author_pattern + r')',
        header, re.IGNORECASE
    )
    if m:
        sender_text = m.group(1).strip()
        # Clean trailing title info
        sender_text = re.sub(r',?\s+(?:Bishop|Pope|Patriarch|of\s+\w+).*', '', sender_text)
        result = check_sender(sender_text, 'Structured header: "From: {sender} / To: [author]"')
        if result:
            return result

    return None, None, None


def audit_and_fix():
    conn = get_connection()
    c = conn.cursor()

    # Get all collections and their primary author
    collections = c.execute('''
        SELECT c.slug, c.author_name, a.id as author_id
        FROM collections c
        LEFT JOIN authors a ON a.name = c.author_name
        WHERE c.letter_count > 0
        ORDER BY c.slug
    ''').fetchall()

    all_fixes = []

    for coll in collections:
        slug = coll['slug']
        author_name = coll['author_name']
        author_id = coll['author_id']

        if not author_id:
            continue

        author_variants = get_author_name_variants(author_name)

        # Get all letters where the collection author is the sender
        letters = c.execute('''
            SELECT id, letter_number, book, sender_id, recipient_id,
                substr(COALESCE(english_text, ''), 1, 500) as eng_text,
                substr(COALESCE(modern_english, ''), 1, 500) as mod_text
            FROM letters
            WHERE collection = ? AND sender_id = ?
        ''', (slug, author_id)).fetchall()

        for letter in letters:
            lid = letter['id']
            lnum = letter['letter_number']
            book = letter['book']
            current_sender = letter['sender_id']
            current_recipient = letter['recipient_id']

            for text_field, text in [('english_text', letter['eng_text']),
                                      ('modern_english', letter['mod_text'])]:
                if not text or not text.strip():
                    continue

                result = extract_sender_from_header(text, author_variants, author_id, c)
                if result and result[0] is not None:
                    actual_sender_id, actual_sender_name, evidence = result
                    all_fixes.append({
                        'letter_id': lid,
                        'collection': slug,
                        'letter_number': lnum,
                        'book': book,
                        'current_sender_id': current_sender,
                        'current_recipient_id': current_recipient,
                        'actual_sender_id': actual_sender_id,
                        'actual_sender_name': actual_sender_name,
                        'collection_author_id': author_id,
                        'collection_author_name': author_name,
                        'evidence': evidence,
                        'text_field': text_field,
                        'is_self_addressed': current_sender == current_recipient,
                    })
                    break

    # Also check self-addressed letters that might not have the collection author as sender
    # (edge case: sender_id == recipient_id but neither is the collection author)
    self_letters = c.execute('''
        SELECT l.id, l.collection, l.letter_number, l.book, l.sender_id, l.recipient_id,
            substr(COALESCE(l.english_text, ''), 1, 500) as eng_text,
            substr(COALESCE(l.modern_english, ''), 1, 500) as mod_text,
            c.author_name
        FROM letters l
        JOIN collections c ON l.collection = c.slug
        WHERE l.sender_id = l.recipient_id AND l.sender_id IS NOT NULL
    ''').fetchall()

    already_fixed_ids = {f['letter_id'] for f in all_fixes}

    for letter in self_letters:
        lid = letter['id']
        if lid in already_fixed_ids:
            continue

        author_name_coll = letter['author_name']
        author_id_self = letter['sender_id']
        author_variants = get_author_name_variants(author_name_coll)

        for text_field, text in [('english_text', letter['eng_text']),
                                  ('modern_english', letter['mod_text'])]:
            if not text or not text.strip():
                continue

            result = extract_sender_from_header(text, author_variants, author_id_self, c)
            if result and result[0] is not None:
                actual_sender_id, actual_sender_name, evidence = result
                all_fixes.append({
                    'letter_id': lid,
                    'collection': letter['collection'],
                    'letter_number': letter['letter_number'],
                    'book': letter['book'],
                    'current_sender_id': letter['sender_id'],
                    'current_recipient_id': letter['recipient_id'],
                    'actual_sender_id': actual_sender_id,
                    'actual_sender_name': actual_sender_name,
                    'collection_author_id': author_id_self,
                    'collection_author_name': author_name_coll,
                    'evidence': evidence,
                    'text_field': text_field,
                    'is_self_addressed': True,
                })
                break

    # Print report
    print("=" * 80)
    print("SENDER/RECIPIENT SWAP AUDIT REPORT")
    print("=" * 80)

    by_collection = defaultdict(list)
    for fix in all_fixes:
        by_collection[fix['collection']].append(fix)

    total_swaps = 0
    for slug in sorted(by_collection.keys()):
        fixes = by_collection[slug]
        author_name = fixes[0]['collection_author_name']
        print(f"\n--- {slug} (author: {author_name}) ---")
        for fix in sorted(fixes, key=lambda x: (x.get('book') or 0, x['letter_number'] or 0)):
            label = "SELF-ADDR" if fix['is_self_addressed'] else "SWAP"
            book_str = f"bk{fix['book']}." if fix['book'] else ""
            print(f"  [{label}] Letter {book_str}{fix['letter_number']} (id={fix['letter_id']}): "
                  f"sender should be {fix['actual_sender_name']} (id={fix['actual_sender_id']}), "
                  f"recipient should be {author_name} (id={fix['collection_author_id']})")
            print(f"         Evidence: {fix['evidence']} [{fix['text_field']}]")
            total_swaps += 1

    self_count = sum(1 for f in all_fixes if f['is_self_addressed'])
    swap_count = total_swaps - self_count

    print(f"\n{'=' * 80}")
    print(f"TOTAL SWAPS TO APPLY: {total_swaps}")
    print(f"  From sender==author mislabeling: {swap_count}")
    print(f"  From self-addressed fixes: {self_count}")
    print(f"{'=' * 80}")

    if DRY_RUN:
        print("\n*** DRY RUN — no changes made. Run without --dry-run to apply fixes. ***")
        conn.close()
        return

    if total_swaps == 0:
        print("\nNo swaps needed.")
        conn.close()
        return

    # Apply fixes
    print(f"\nApplying {total_swaps} fixes...")
    applied = 0
    skipped = 0
    for fix in all_fixes:
        new_sender = fix['actual_sender_id']
        new_recipient = fix['collection_author_id']

        if new_sender == new_recipient:
            print(f"  SKIP id={fix['letter_id']}: would create self-addressed letter")
            skipped += 1
            continue

        c.execute('''
            UPDATE letters SET sender_id = ?, recipient_id = ?
            WHERE id = ?
        ''', (new_sender, new_recipient, fix['letter_id']))
        applied += 1

    conn.commit()
    print(f"Applied {applied} fixes. Skipped {skipped}.")

    # Verify: check remaining self-addressed letters
    remaining_self = c.execute('''
        SELECT COUNT(*) as cnt FROM letters
        WHERE sender_id = recipient_id AND sender_id IS NOT NULL
    ''').fetchone()['cnt']
    print(f"\nRemaining self-addressed letters: {remaining_self} (was 159)")

    # Verify a sample
    print("\nVerification sample (first 15 fixed letters):")
    sample_ids = [f['letter_id'] for f in all_fixes[:15]]
    if sample_ids:
        placeholders = ','.join('?' * len(sample_ids))
        rows = c.execute(f'''
            SELECT l.id, l.collection, l.letter_number,
                   s.name as sender_name, r.name as recipient_name
            FROM letters l
            LEFT JOIN authors s ON l.sender_id = s.id
            LEFT JOIN authors r ON l.recipient_id = r.id
            WHERE l.id IN ({placeholders})
        ''', sample_ids).fetchall()
        for row in rows:
            print(f"  id={row['id']} {row['collection']} #{row['letter_number']}: "
                  f"{row['sender_name']} -> {row['recipient_name']}")

    conn.close()
    print("\nDone.")


if __name__ == '__main__':
    audit_and_fix()

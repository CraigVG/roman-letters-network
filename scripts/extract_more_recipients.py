#!/usr/bin/env python3
"""
extract_more_recipients.py

Scans all letters where recipient_id IS NULL and attempts to extract recipient names
from modern_english or english_text using a variety of text patterns.

Patterns handled:
  1. Structured "From: ... / To: ..." header blocks (modern_english from Claude translations)
  2. "To [Name]." salutation at start of text  (Pliny, Ennodius, Cassiodorus, etc.)
  3. "SENDER to RECIPIENT" first-line pattern
  4. "Gregory/Ambrose/[Author] to [Name], [Title] of [City]"
  5. "Cassiodorus-style": "ROMAN_NUMERAL. SENDER TO RECIPIENT_NAME." headings
  6. "Dear [Name]" salutation
  7. "Addressed to [Name]" / "Addressed without formal salutation to [Name]"
  8. subject_summary "To [Name]" patterns
  9. "[Name], from [Sender]" (Ennodius reversed style)

For new authors created:
  - If name contains "of [City]" → use city coords, confidence='strong'
  - If collection is Gregory correspondent → use Rome or regional default, confidence='approximate'
  - If papal correspondent → Rome, confidence='approximate'
  - Otherwise → sender's location, confidence='approximate'
"""

import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

# ---------------------------------------------------------------------------
# Known city coordinates for "of [City]" disambiguation
# ---------------------------------------------------------------------------
CITY_COORDS = {
    'rome': (41.8967, 12.4822),
    'milan': (45.4642, 9.19),
    'carthage': (36.8065, 10.1815),
    'hippo': (36.8833, 7.75),
    'alexandria': (31.2001, 29.9187),
    'antioch': (36.2021, 36.1601),
    'constantinople': (41.0082, 28.9784),
    'jerusalem': (31.7054, 35.2195),
    'bethlehem': (31.7054, 35.2024),
    'caesarea': (38.7312, 35.4787),
    'nazianzus': (38.2167, 34.5),
    'ravenna': (44.4184, 12.2035),
    'pavia': (45.1847, 9.1582),
    'vienne': (45.5242, 4.8783),
    'limoges': (45.8336, 1.2611),
    'clermont': (45.7772, 3.087),
    'nola': (40.9263, 14.5278),
    'ancona': (43.6158, 13.5189),
    'aquileia': (45.7705, 13.3672),
    'lyon': (45.764, 4.8357),
    'arles': (43.6767, 4.6278),
    'toulouse': (43.6047, 1.4442),
    'bordeaux': (44.8378, -0.5792),
    'narbonne': (43.1841, 3.0039),
    'marseille': (43.2965, 5.3698),
    'tours': (47.3941, 0.6848),
    'york': (53.9599, -1.0873),
    'london': (51.5074, -0.1278),
    'carthago': (36.8065, 10.1815),
    'pelusium': (31.0167, 32.55),
    'cyrene': (32.82, 21.86),
    'ptolemais': (32.82, 21.86),
    'cyrrhus': (36.8833, 36.8667),
    'thessalonica': (40.6401, 22.9444),
    'corinth': (37.9383, 22.9319),
    'ephesus': (37.9395, 27.3417),
    'athens': (37.9838, 23.7275),
    'nicaea': (40.4247, 29.719),
    'capua': (41.1067, 14.2078),
    'palermo': (38.1157, 13.3615),
    'naples': (40.8518, 14.2681),
    'brindisi': (40.638, 17.9463),
    'spoleto': (42.7342, 12.7381),
    'perugia': (43.1122, 12.3888),
    'florence': (43.7696, 11.2558),
    'genoa': (44.4056, 8.9463),
    'verona': (45.4384, 10.9916),
    'brescia': (45.5416, 10.2118),
    'cremona': (45.1327, 10.0227),
    'como': (45.8080, 9.0852),
    'mainz': (49.9929, 8.2473),
    'trier': (49.7499, 6.6371),
    'cologne': (50.938, 6.9603),
    'metz': (49.1194, 6.1764),
    'besancon': (47.2378, 6.0241),
    'orange': (44.1367, 4.8092),
    'riez': (43.8167, 6.0833),
    'sisteron': (44.1961, 5.9447),
    'catania': (37.5023, 15.0873),
    'syracuse': (37.0755, 15.2866),
    'calama': (36.4652, 7.1269),
    'thagaste': (36.0333, 8.5167),
    'madaura': (36.4667, 8.1167),
    'cirta': (36.365, 6.6147),
    'numidia': (36.0, 7.0),
    'africa': (36.0, 10.0),
    'egypt': (27.0, 30.0),
    'gaul': (46.0, 2.0),
    'spain': (40.4168, -3.7038),
    'sicily': (37.6, 14.0154),
    'sardinia': (40.1209, 9.0129),
    'dalmatia': (43.9159, 17.6791),
    'pannonia': (47.0, 17.0),
    'thrace': (42.0, 27.0),
    'syria': (35.0, 38.0),
    'palestine': (31.5, 35.0),
    'pontus': (41.0, 36.5),
    'cappadocia': (38.5, 34.5),
}

# Collection-level fallback coordinates for new recipients
COLLECTION_DEFAULTS = {
    'gregory_great': (41.8967, 12.4822),   # Rome
    'leo_great': (41.8967, 12.4822),
    'gelasius_i': (41.8967, 12.4822),
    'innocent_i': (41.8967, 12.4822),
    'hormisdas': (41.8967, 12.4822),
    'pelagius_i': (41.8967, 12.4822),
    'simplicius_pope': (41.8967, 12.4822),
    'celestine_i': (41.8967, 12.4822),
    'augustine_hippo': (36.8833, 7.75),
    'cyprian_carthage': (36.8065, 10.1815),
    'ambrose_milan': (45.4642, 9.19),
    'jerome': (31.7054, 35.2024),
    'basil_caesarea': (38.7312, 35.4787),
    'gregory_nazianzus': (38.2167, 34.5),
    'chrysostom': (41.0082, 28.9784),
    'isidore_pelusium': (31.0167, 32.55),
    'synesius_cyrene': (32.82, 21.86),
    'theodoret_cyrrhus': (36.8833, 36.8667),
    'libanius': (36.2021, 36.1601),
    'cassiodorus': (44.4184, 12.2035),
    'symmachus': (41.8967, 12.4822),
    'sidonius_apollinaris': (45.7772, 3.087),
    'avitus_vienne': (45.5242, 4.8783),
    'ruricius_limoges': (45.8336, 1.2611),
    'ennodius_pavia': (45.1847, 9.1582),
    'paulinus_nola': (40.9263, 14.5278),
    'pliny_younger': (41.8967, 12.4822),
    'julian_emperor': (41.0082, 28.9784),
    'athanasius_alexandria': (31.2001, 29.9187),
    'boniface': (50.0, 8.27),
    'sulpicius_severus': (44.0, 2.0),
    'paulinus_milan': (45.4642, 9.19),
    'columbanus': (44.7167, 9.4167),
}

# Words that should not appear in recipient names
NOISE_WORDS = {
    'which', 'that', 'this', 'what', 'where', 'when', 'although', 'because',
    'however', 'therefore', 'moreover', 'concerning', 'regarding', 'about',
    'will', 'would', 'could', 'should', 'have', 'been', 'were', 'being',
    'request', 'letter', 'epistle', 'write', 'written', 'send', 'sent',
}


def normalize_name(name: str) -> str:
    """Clean up a recipient name for matching."""
    if not name:
        return ''
    name = name.strip()
    # Remove surrounding quotes
    name = name.strip('"\'')
    # Remove titles
    for prefix in [
        'St\\.', 'Saint', 'Bp\\.', 'Bishop', 'Pope', 'Emperor', 'Empress',
        'Patriarch', 'Archbishop', 'Abbot', 'Abbess', 'Presbyter', 'Deacon',
        'Priest', 'Prefect', 'Consul', 'Tribune', 'Count', 'Duke', 'King',
        'Queen', 'Lord', 'Lady', 'Rev\\.', 'Reverend', 'Father', 'Mother',
        'the', 'The', 'his', 'her', 'our', 'your', 'my', 'most', 'holy',
        'blessed', 'venerable', 'illustrious', 'distinguished', 'exalted',
        'all', 'entire',
    ]:
        name = re.sub(rf'\b{prefix}\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+', ' ', name).strip()
    name = name.rstrip('.,;:!')
    name = name.strip()
    return name


def looks_like_name(name: str) -> bool:
    """Sanity check: does this string look like a personal name?"""
    if not name or len(name) < 2 or len(name) > 80:
        return False
    lower = name.lower()
    # Reject if it contains noise/sentence words
    for w in NOISE_WORDS:
        if f' {w} ' in f' {lower} ':
            return False
    # Must start with uppercase or digit (for roman numerals)
    if not (name[0].isupper() or name[0].isdigit()):
        return False
    # Reject pure lowercase words
    if name == name.lower():
        return False
    return True


def extract_city_from_name(name: str):
    """Try to parse 'of [City]' from a name string."""
    m = re.search(r'\bof\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', name)
    if m:
        city = m.group(1).lower()
        if city in CITY_COORDS:
            return CITY_COORDS[city], city
        # Try first word only
        city_first = city.split()[0]
        if city_first in CITY_COORDS:
            return CITY_COORDS[city_first], city_first
    return None, None


def extract_recipient_from_text(text: str, collection: str, subject: str) -> str | None:
    """Extract recipient name from letter text using various patterns."""
    if not text:
        text = ''

    lines = text.split('\n')

    # --- Pattern 1: Structured "To: [Name]" header (Claude translation style) ---
    for i, line in enumerate(lines[:20]):
        line_s = line.strip()
        m = re.match(r'^To:\s*(.+?)$', line_s, re.IGNORECASE)
        if m:
            cand = m.group(1).strip().rstrip('.,;:')
            norm = normalize_name(cand)
            if looks_like_name(norm):
                return norm

    # --- Pattern 2: "To [Name]." at the very start of first non-blank line ---
    for line in lines[:10]:
        line_s = line.strip()
        if not line_s:
            continue
        # "To Acilius." or "To my lord Paulinus." or "To the people of..."
        m = re.match(
            r'^To\s+(?:my\s+)?(?:the\s+)?(?:most\s+)?(?:holy\s+)?(?:blessed\s+)?(?:lord\s+)?(?:dear\s+)?([A-Z][^\.\,\n]{1,60})[\.,]?$',
            line_s
        )
        if m:
            norm = normalize_name(m.group(1))
            if looks_like_name(norm):
                return norm
        # Without trailing punct
        m = re.match(
            r'^To\s+(?:my\s+)?(?:the\s+)?([A-Z][^\.\,\n]{1,60})$',
            line_s
        )
        if m:
            norm = normalize_name(m.group(1))
            if looks_like_name(norm):
                return norm
        break  # Only check the very first non-blank line for this pattern

    # --- Pattern 3: Ennodius-style "NAME, from Ennodius." reversed header ---
    first_lines = [l.strip() for l in lines[:5] if l.strip()]
    if first_lines:
        fl = first_lines[0]
        # "Faustus, from Ennodius." or "Johannes, from Ennodius."
        m = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s+from\s+\w+[\.\s]', fl)
        if m:
            norm = normalize_name(m.group(1))
            if looks_like_name(norm):
                return norm
        # "Ennodius to Florianus." direct style
        m = re.match(r'^(?:\w+\s+){1,3}to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)[\.\,\s]*$', fl)
        if m:
            norm = normalize_name(m.group(1))
            if looks_like_name(norm) and norm.split()[0].lower() not in {'the', 'all', 'his', 'her', 'my', 'our'}:
                return norm

    # --- Pattern 4: Cassiodorus "ROMAN_NUM. SENDER TO RECIPIENT_NAME." ---
    for line in lines[:5]:
        line_s = line.strip()
        # "IX. KING THEODERIC TO EUSTORGIUS, THE VENERABLE BISHOP OF MILAN."
        m = re.match(
            r'^(?:[IVXLCDM]+|[0-9]+)\.?\s+[A-Z\s]+\s+TO\s+([A-Z][A-Z\s\,]+?)(?:,\s+[A-Z]|\.$|\s*$)',
            line_s
        )
        if m:
            raw = m.group(1).strip().rstrip('.,')
            # Title-case it
            norm = normalize_name(raw.title())
            if looks_like_name(norm):
                return norm
        # "KING THEODERIC TO THE SENATE OF THE CITY OF ROME." (no roman numeral)
        m = re.match(r'^[A-Z\s]+\s+TO\s+([A-Z][A-Z\s]+?)(?:,\s+[A-Z]|\.$|\s*$)', line_s)
        if m:
            raw = m.group(1).strip().rstrip('.,')
            norm = normalize_name(raw.title())
            if looks_like_name(norm):
                return norm

    # --- Pattern 5: Pliny-style "To [Name]." as its own paragraph ---
    for line in lines[:15]:
        line_s = line.strip()
        m = re.match(r'^To\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)[\.\,]?\s*$', line_s)
        if m:
            norm = normalize_name(m.group(1))
            if looks_like_name(norm):
                return norm

    # --- Pattern 6: "Gregory to [Name], Bishop of [City]" style ---
    for line in lines[:10]:
        line_s = line.strip()
        m = re.match(
            r'^(?:Gregory|Ambrose|Jerome|Augustine|Basil|Leo|Hormisdas|Pelagius|Gelasius|Innocent|Cassiodorus|Avitus|Sidonius|Ruricius|Ennodius|Paulinus|Cyprian|Athanasius|Synesius|Theodoret|Isidore|Libanius|Chrysostom|Symmachus|Pliny)\s+to\s+([A-Z][^\.,\n]{1,60})',
            line_s, re.IGNORECASE
        )
        if m:
            norm = normalize_name(m.group(1))
            if looks_like_name(norm):
                return norm

    # --- Pattern 7: "Dear [Name]" salutation ---
    for line in lines[:15]:
        line_s = line.strip()
        m = re.match(r'^Dear\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,\.]', line_s)
        if m:
            norm = normalize_name(m.group(1))
            if looks_like_name(norm):
                return norm

    # --- Pattern 8: "Addressed to [Name]" or "Addressed without formal salutation to [Name]" ---
    for line in lines[:15]:
        line_s = line.strip()
        m = re.match(r'^Addressed\s+(?:without\s+\w+\s+\w+\s+)?to\s+([A-Z][^\.,\n]{1,60})', line_s, re.IGNORECASE)
        if m:
            norm = normalize_name(m.group(1))
            if looks_like_name(norm):
                return norm

    # --- Pattern 9: subject_summary "To [Name]" prefix ---
    if subject:
        m = re.match(r'^To\s+([A-Z][^\.,\n]{1,60})', subject.strip())
        if m:
            norm = normalize_name(m.group(1))
            if looks_like_name(norm):
                return norm

    # --- Pattern 10: Isidore of Pelusium "To the [title] [Name]" in subject ---
    if subject and collection == 'isidore_pelusium':
        m = re.match(
            r'^To\s+(?:the\s+)?(?:monk|scholar|priest|deacon|bishop|presbyter|reader|subdeacon|lector|hermit|philosopher|soldier|official|governor|count|prefect|magistrate|senator|nobleman|nobleman|woman|lady|widow|virgin|man|physician|lawyer|rhetor|sophist|teacher|student|young|old|holy|blessed|reverend|venerable)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            subject.strip(), re.IGNORECASE
        )
        if m:
            norm = normalize_name(m.group(1))
            if looks_like_name(norm):
                return norm

    # --- Pattern 11: "[Name] sends greetings" or "SENDER to RECIPIENT, greetings" in first paragraph ---
    for line in lines[:20]:
        line_s = line.strip()
        # "Augustine to Generosus, greetings."
        m = re.match(
            r'^(?:\w+\s+){1,3}to\s+([A-Z][a-z]+(?:\s+(?:and\s+)?[A-Z][a-z]+)?),?\s+(?:greetings|greeting|health|blessing)',
            line_s, re.IGNORECASE
        )
        if m:
            norm = normalize_name(m.group(1))
            if looks_like_name(norm):
                return norm
        # "To my lord Praesidius ... — Augustine sends greeting"
        m = re.match(
            r'^To\s+(?:my\s+)?(?:lord\s+|lady\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,—]',
            line_s
        )
        if m:
            norm = normalize_name(m.group(1))
            if looks_like_name(norm):
                return norm

    # --- Pattern 12: "Against [Name]" subject (Synesius formal decrees, skip these) ---
    # Pattern 13: "Letter [N] — To [Name]" or "Epistle [N]. To [Name]"
    for line in lines[:15]:
        line_s = line.strip()
        m = re.match(
            r'^(?:Letter|Epistle|Ep\.?)\s+(?:[IVXLCDM]+|\d+)\.?\s*(?:\([^)]*\)\s*)?(?:—\s*)?To\s+(.+?)[\.,]?\s*$',
            line_s, re.IGNORECASE
        )
        if m:
            norm = normalize_name(m.group(1))
            if looks_like_name(norm):
                return norm

    return None


def fuzzy_find_author(cursor, name: str) -> int | None:
    """Look up an author by fuzzy matching. Returns author id or None."""
    if not name:
        return None

    # Exact match (case-insensitive)
    cursor.execute('SELECT id FROM authors WHERE name = ? COLLATE NOCASE', (name,))
    row = cursor.fetchone()
    if row:
        return row[0]

    # Partial: name is contained within existing author name
    cursor.execute('SELECT id, name FROM authors WHERE name LIKE ?', (f'%{name}%',))
    row = cursor.fetchone()
    if row:
        return row[0]

    # Single-word match on first significant token (skip short words)
    tokens = [t for t in name.split() if len(t) > 3]
    if tokens:
        first = tokens[0]
        cursor.execute('SELECT id, name FROM authors WHERE name LIKE ?', (f'%{first}%',))
        rows = cursor.fetchall()
        if len(rows) == 1:
            return rows[0][0]
        # If multiple matches, try to narrow by second token
        if len(rows) > 1 and len(tokens) > 1:
            second = tokens[1]
            for row in rows:
                if second.lower() in row[1].lower():
                    return row[0]

    return None


def get_coords_for_new_author(name: str, collection: str, sender_lat, sender_lon) -> tuple:
    """
    Return (lat, lon, confidence) for a newly created author.

    Priority:
      1. "of [City]" in name → city coords, 'strong'
      2. Collection default → collection coords, 'approximate'
      3. Sender's location → sender coords, 'approximate'
    """
    coords, city = extract_city_from_name(name)
    if coords:
        return coords[0], coords[1], 'strong'

    if collection in COLLECTION_DEFAULTS:
        lat, lon = COLLECTION_DEFAULTS[collection]
        return lat, lon, 'approximate'

    if sender_lat and sender_lon:
        return sender_lat, sender_lon, 'approximate'

    return None, None, 'unknown'


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # --- Baseline stats ---
    cursor.execute('SELECT COUNT(*) FROM letters')
    total_letters = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM letters WHERE recipient_id IS NOT NULL')
    baseline_recipients = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM letters WHERE distance_km IS NOT NULL')
    baseline_distances = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM authors')
    baseline_authors = cursor.fetchone()[0]

    print(f"Baseline:")
    print(f"  Total letters:           {total_letters}")
    print(f"  Letters with recipient:  {baseline_recipients} ({100*baseline_recipients//total_letters}%)")
    print(f"  Letters with distance:   {baseline_distances} ({100*baseline_distances//total_letters}%)")
    print(f"  Total authors:           {baseline_authors}")
    print()

    # --- Fetch all letters needing recipients ---
    cursor.execute('''
        SELECT l.id, l.collection, l.modern_english, l.english_text, l.subject_summary,
               l.sender_id, a.lat as sender_lat, a.lon as sender_lon, a.name as sender_name
        FROM letters l
        LEFT JOIN authors a ON l.sender_id = a.id
        WHERE l.recipient_id IS NULL
          AND (l.modern_english IS NOT NULL OR l.english_text IS NOT NULL)
        ORDER BY l.collection, l.id
    ''')
    letters = cursor.fetchall()
    print(f"Processing {len(letters)} letters without recipient_id ...\n")

    matched_existing = 0
    created_new = 0
    failed = 0
    new_authors_created = []

    for row in letters:
        letter_id = row['id']
        collection = row['collection']
        text = row['modern_english'] or row['english_text'] or ''
        subject = row['subject_summary'] or ''
        sender_lat = row['sender_lat']
        sender_lon = row['sender_lon']

        recipient_name = extract_recipient_from_text(text, collection, subject)
        if not recipient_name:
            failed += 1
            continue

        # Try to find existing author
        existing_id = fuzzy_find_author(cursor, recipient_name)
        if existing_id:
            cursor.execute('UPDATE letters SET recipient_id = ? WHERE id = ?', (existing_id, letter_id))
            matched_existing += 1
        else:
            # Create new author
            lat, lon, confidence = get_coords_for_new_author(recipient_name, collection, sender_lat, sender_lon)
            try:
                if lat is not None:
                    cursor.execute(
                        'INSERT INTO authors (name, lat, lon, location_confidence) VALUES (?, ?, ?, ?)',
                        (recipient_name, lat, lon, confidence)
                    )
                else:
                    cursor.execute(
                        'INSERT INTO authors (name, location_confidence) VALUES (?, ?)',
                        (recipient_name, confidence)
                    )
                new_id = cursor.lastrowid
                cursor.execute('UPDATE letters SET recipient_id = ? WHERE id = ?', (new_id, letter_id))
                new_authors_created.append((recipient_name, collection, lat, lon, confidence))
                created_new += 1
            except sqlite3.IntegrityError:
                # Name uniqueness violation — author was just inserted in this run
                cursor.execute('SELECT id FROM authors WHERE name = ?', (recipient_name,))
                r = cursor.fetchone()
                if r:
                    cursor.execute('UPDATE letters SET recipient_id = ? WHERE id = ?', (r[0], letter_id))
                    matched_existing += 1
                else:
                    failed += 1

    conn.commit()

    # --- Task 3: Refine locations for newly created authors ---
    # (Already handled above in get_coords_for_new_author, but do a cleanup pass for
    #  any that got coordinates=NULL due to missing sender location)
    location_fixed = 0
    for name, collection, lat, lon, confidence in new_authors_created:
        if lat is None and collection in COLLECTION_DEFAULTS:
            dlat, dlon = COLLECTION_DEFAULTS[collection]
            cursor.execute(
                'UPDATE authors SET lat=?, lon=?, location_confidence=? WHERE name=? AND lat IS NULL',
                (dlat, dlon, 'approximate', name)
            )
            if cursor.rowcount > 0:
                location_fixed += 1

    conn.commit()

    # --- Stats ---
    cursor.execute('SELECT COUNT(*) FROM letters WHERE recipient_id IS NOT NULL')
    new_recipients = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM authors')
    new_author_count = cursor.fetchone()[0]

    print("=" * 60)
    print("TASK 1 RESULTS: Recipient Extraction")
    print("=" * 60)
    print(f"  Matched to existing authors:  {matched_existing}")
    print(f"  New authors created:          {created_new}")
    print(f"  Could not extract recipient:  {failed}")
    print(f"  Location fixes (post-pass):   {location_fixed}")
    print()
    print(f"  Recipient coverage: {baseline_recipients} → {new_recipients} letters")
    print(f"  ({100*new_recipients//total_letters}% of {total_letters} total, was {100*baseline_recipients//total_letters}%)")
    print(f"  Authors: {baseline_authors} → {new_author_count}")
    print()

    if new_authors_created[:20]:
        print("Sample of new authors created:")
        for name, coll, lat, lon, conf in new_authors_created[:20]:
            coords = f"({lat:.2f}, {lon:.2f})" if lat else "(no coords)"
            print(f"  [{coll[:20]:<20}] {name:<40} {coords} [{conf}]")
        if len(new_authors_created) > 20:
            print(f"  ... and {len(new_authors_created)-20} more")

    # --- Task 2: Recompute distances ---
    print()
    print("=" * 60)
    print("TASK 2: Recomputing distances ...")
    print("=" * 60)

    cursor.execute("""
        SELECT l.id, a1.lat, a1.lon, a2.lat, a2.lon
        FROM letters l
        JOIN authors a1 ON l.sender_id = a1.id
        JOIN authors a2 ON l.recipient_id = a2.id
        WHERE a1.lat IS NOT NULL AND a1.lon IS NOT NULL
          AND a2.lat IS NOT NULL AND a2.lon IS NOT NULL
    """)
    coord_rows = cursor.fetchall()
    print(f"  Letters with sender + recipient coordinates: {len(coord_rows)}")

    import math

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.asin(math.sqrt(a))

    dist_updated = 0
    for letter_id, s_lat, s_lon, r_lat, r_lon in coord_rows:
        dist = haversine(s_lat, s_lon, r_lat, r_lon)
        cursor.execute("UPDATE letters SET distance_km = ? WHERE id = ?", (round(dist, 1), letter_id))
        dist_updated += 1

    conn.commit()

    cursor.execute('SELECT COUNT(*) FROM letters WHERE distance_km IS NOT NULL')
    new_distances = cursor.fetchone()[0]

    print(f"  Distance computations written: {dist_updated}")
    print(f"  Distance coverage: {baseline_distances} → {new_distances} letters")
    print(f"  ({100*new_distances//total_letters}% of {total_letters} total, was {100*baseline_distances//total_letters}%)")

    # --- Final summary ---
    print()
    print("=" * 60)
    print("OVERALL COVERAGE IMPROVEMENT")
    print("=" * 60)
    cursor.execute('SELECT COUNT(DISTINCT sender_id || \'-\' || recipient_id) FROM letters WHERE sender_id IS NOT NULL AND recipient_id IS NOT NULL')
    unique_pairs = cursor.fetchone()[0]
    print(f"  Recipient coverage:  {baseline_recipients}/{total_letters} → {new_recipients}/{total_letters}")
    pct_before = 100 * baseline_recipients / total_letters
    pct_after = 100 * new_recipients / total_letters
    print(f"                       {pct_before:.1f}% → {pct_after:.1f}% (+{pct_after - pct_before:.1f}pp)")
    print(f"  Distance coverage:   {baseline_distances}/{total_letters} → {new_distances}/{total_letters}")
    pct_d_before = 100 * baseline_distances / total_letters
    pct_d_after = 100 * new_distances / total_letters
    print(f"                       {pct_d_before:.1f}% → {pct_d_after:.1f}% (+{pct_d_after - pct_d_before:.1f}pp)")
    print(f"  Unique sender→recipient pairs: {unique_pairs}")
    print(f"  Total authors: {new_author_count}")

    conn.close()


if __name__ == '__main__':
    main()

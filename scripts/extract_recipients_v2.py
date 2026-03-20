#!/usr/bin/env python3
"""
extract_recipients_v2.py

Enhanced recipient extraction targeting patterns missed by extract_more_recipients.py.

Key patterns added:
  A. Enhanced "To:" header — extract proper name even when preceded by titles/roles
  B. Libanius "To Name. (year)" format
  C. "AUTHOR, title, to [adj+nouns] NAME" — comma between author and "to"
  D. "AUTHOR to [adj+nouns] NAME" — no comma
  E. "King/Emperor SENDER to NAME" — Cassiodorus royal sender
  F. "To [title] NAME [bracket annotation]" — inverted format or annotated
  G. "AUTHOR to his lord NAME" / "Sidonius to his lord, Bishop Lupus"
"""

import sqlite3
import os
import re
import math

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

CITY_COORDS = {
    'rome': (41.8967, 12.4822), 'milan': (45.4642, 9.19),
    'carthage': (36.8065, 10.1815), 'hippo': (36.8833, 7.75),
    'alexandria': (31.2001, 29.9187), 'antioch': (36.2021, 36.1601),
    'constantinople': (41.0082, 28.9784), 'jerusalem': (31.7054, 35.2195),
    'bethlehem': (31.7054, 35.2024), 'caesarea': (38.7312, 35.4787),
    'nazianzus': (38.2167, 34.5), 'ravenna': (44.4184, 12.2035),
    'pavia': (45.1847, 9.1582), 'vienne': (45.5242, 4.8783),
    'limoges': (45.8336, 1.2611), 'clermont': (45.7772, 3.087),
    'nola': (40.9263, 14.5278), 'ancona': (43.6158, 13.5189),
    'aquileia': (45.7705, 13.3672), 'lyon': (45.764, 4.8357),
    'arles': (43.6767, 4.6278), 'toulouse': (43.6047, 1.4442),
    'bordeaux': (44.8378, -0.5792), 'narbonne': (43.1841, 3.0039),
    'marseille': (43.2965, 5.3698), 'tours': (47.3941, 0.6848),
    'york': (53.9599, -1.0873), 'london': (51.5074, -0.1278),
    'carthago': (36.8065, 10.1815), 'pelusium': (31.0167, 32.55),
    'cyrene': (32.82, 21.86), 'ptolemais': (32.82, 21.86),
    'cyrrhus': (36.8833, 36.8667), 'thessalonica': (40.6401, 22.9444),
    'corinth': (37.9383, 22.9319), 'ephesus': (37.9395, 27.3417),
    'athens': (37.9838, 23.7275), 'nicaea': (40.4247, 29.719),
    'capua': (41.1067, 14.2078), 'palermo': (38.1157, 13.3615),
    'naples': (40.8518, 14.2681), 'brindisi': (40.638, 17.9463),
    'spoleto': (42.7342, 12.7381), 'perugia': (43.1122, 12.3888),
    'florence': (43.7696, 11.2558), 'genoa': (44.4056, 8.9463),
    'verona': (45.4384, 10.9916), 'brescia': (45.5416, 10.2118),
    'cremona': (45.1327, 10.0227), 'como': (45.8080, 9.0852),
    'mainz': (49.9929, 8.2473), 'trier': (49.7499, 6.6371),
    'cologne': (50.938, 6.9603), 'metz': (49.1194, 6.1764),
    'besancon': (47.2378, 6.0241), 'orange': (44.1367, 4.8092),
    'riez': (43.8167, 6.0833), 'sisteron': (44.1961, 5.9447),
    'catania': (37.5023, 15.0873), 'syracuse': (37.0755, 15.2866),
    'calama': (36.4652, 7.1269), 'thagaste': (36.0333, 8.5167),
    'madaura': (36.4667, 8.1167), 'cirta': (36.365, 6.6147),
    'beneventum': (41.1308, 14.7794), 'poitiers': (46.5802, 0.3404),
    'reims': (49.2577, 4.0317), 'antibes': (43.5808, 7.1239),
    'numidia': (36.0, 7.0), 'africa': (36.0, 10.0),
    'egypt': (27.0, 30.0), 'gaul': (46.0, 2.0),
    'spain': (40.4168, -3.7038), 'sicily': (37.6, 14.0154),
    'sardinia': (40.1209, 9.0129), 'dalmatia': (43.9159, 17.6791),
    'pannonia': (47.0, 17.0), 'thrace': (42.0, 27.0),
    'syria': (35.0, 38.0), 'palestine': (31.5, 35.0),
    'pontus': (41.0, 36.5), 'cappadocia': (38.5, 34.5),
    'campania': (41.0, 14.5), 'picenum': (43.0, 13.5),
    'etruria': (43.0, 11.5), 'troyes': (48.2973, 4.0744),
    'auxerre': (47.7979, 3.5714), 'chalon': (46.7803, 4.8522),
}

COLLECTION_DEFAULTS = {
    'gregory_great': (41.8967, 12.4822), 'leo_great': (41.8967, 12.4822),
    'gelasius_i': (41.8967, 12.4822), 'innocent_i': (41.8967, 12.4822),
    'hormisdas': (41.8967, 12.4822), 'pelagius_i': (41.8967, 12.4822),
    'simplicius_pope': (41.8967, 12.4822), 'celestine_i': (41.8967, 12.4822),
    'augustine_hippo': (36.8833, 7.75), 'cyprian_carthage': (36.8065, 10.1815),
    'ambrose_milan': (45.4642, 9.19), 'jerome': (31.7054, 35.2024),
    'basil_caesarea': (38.7312, 35.4787), 'gregory_nazianzus': (38.2167, 34.5),
    'chrysostom': (41.0082, 28.9784), 'isidore_pelusium': (31.0167, 32.55),
    'synesius_cyrene': (32.82, 21.86), 'theodoret_cyrrhus': (36.8833, 36.8667),
    'libanius': (36.2021, 36.1601), 'cassiodorus': (44.4184, 12.2035),
    'symmachus': (41.8967, 12.4822), 'sidonius_apollinaris': (45.7772, 3.087),
    'avitus_vienne': (45.5242, 4.8783), 'ruricius_limoges': (45.8336, 1.2611),
    'ennodius_pavia': (45.1847, 9.1582), 'paulinus_nola': (40.9263, 14.5278),
    'pliny_younger': (41.8967, 12.4822), 'julian_emperor': (41.0082, 28.9784),
    'athanasius_alexandria': (31.2001, 29.9187), 'boniface': (50.0, 8.27),
    'sulpicius_severus': (44.0, 2.0), 'paulinus_milan': (45.4642, 9.19),
    'columbanus': (44.7167, 9.4167),
}

NOISE_WORDS = {
    'which', 'that', 'this', 'what', 'where', 'when', 'although', 'because',
    'however', 'therefore', 'moreover', 'concerning', 'regarding', 'about',
    'will', 'would', 'could', 'should', 'have', 'been', 'were', 'being',
    'request', 'letter', 'epistle', 'write', 'written', 'send', 'sent',
    'formula', 'senate', 'people', 'brethren', 'congregation', 'faithful',
}

# These "To:" values indicate anonymous/group letters — skip
SKIP_PATTERNS = [
    r'^\[',              # [Unnamed...] [Appointee...]
    r'^a friend',
    r'^an unknown',
    r'^the same',
    r'^unknown',
    r'^all ',
    r'^the faithful',
    r'^the brethren',
    r'^the church',
    r'^the clergy',
    r'^the people',
    r'^the bishops',
    r'^the monks',
    r'^the nuns',
    r'^the senators',
    r'^the senate',
    r'^the newly',
    r'^caecilianus and others',
]

# Words that are NOT personal names (titles, roles, common nouns, religious terms, groups)
TITLE_WORDS = {
    'the', 'a', 'an', 'his', 'her', 'my', 'our', 'your', 'or',
    'most', 'very', 'right', 'truly', 'holy', 'blessed', 'venerable',
    'illustrious', 'distinguished', 'exalted', 'eminent', 'dear', 'beloved',
    'dearly', 'sincerely', 'reverend', 'worthy', 'well', 'esteemed',
    'saint', 'st', 'bishop', 'pope', 'emperor', 'empress', 'patriarch',
    'archbishop', 'abbot', 'abbess', 'presbyter', 'deacon', 'priest',
    'prefect', 'consul', 'tribune', 'count', 'duke', 'king', 'queen',
    'lord', 'lady', 'rev', 'father', 'mother', 'brother', 'sister',
    'son', 'daughter', 'sons', 'daughters', 'brothers', 'sisters',
    'usurper', 'noble', 'senator', 'praetor', 'magistrate', 'official',
    'general', 'commander', 'legate', 'vicar', 'exarch', 'governor',
    'proconsul', 'procurator', 'quaestor', 'metropolitan', 'suffragan',
    'chorepiscopus', 'chorepiskopos', 'comes', 'dux', 'corrector',
    'colleague', 'friend', 'servant', 'devout', 'pious', 'faithful',
    'new', 'old', 'great', 'little', 'young', 'beloved', 'blessed',
    # Religious/group terms that appear in salutations
    'christ', 'jesus', 'god', 'spirit', 'trinity', 'apostle',
    'disciples', 'brethren', 'fathers', 'monks', 'nuns', 'virgins',
    'lords', 'ladies', 'saints', 'martyrs', 'confessors',
    'ornament', 'flower', 'philosopher', 'sophist', 'scholar',
    # Geographic areas often used as recipients in Cassiodorus/Julian
    'jews', 'pagans', 'gentiles', 'senate', 'synod', 'council',
    'palestine', 'byzacium', 'bostra', 'cappadocia', 'cyprus',
    'complaint', 'petition', 'decree', 'formula', 'preface',
}

# Known author first names (for Pattern C/D disambiguation)
KNOWN_AUTHORS_RE = re.compile(
    r'^(?:Leo|Augustine|Ambrose|Gregory|Jerome|Basil|Chrysostom|Sidonius|'
    r'Paulinus|Cyprian|Athanasius|Hormisdas|Gelasius|Celestine|Innocent|'
    r'Boniface|Columbanus|Columba|Ruricius|Avitus|Ennodius|Cassiodorus|Symmachus|'
    r'Isidore|Synesius|Theodoret|Libanius|Julian|Pelagius|Simplicius|'
    r'Hilarius|Hilary|Vigilius|Silverius|John|Peter|Claudianus|Claudian|'
    r'Faustus|Remigius|Severus|Sulpicius|Braulio|Venantius|Alcuin|'
    r'Felix|Fulgentius|Salvian|Ennodius|Nicetas)\b',
    re.IGNORECASE
)

# Optional adjective+noun words between "to" and the actual name
# Handles: "his beloved son, Eutyches", "his dear brother Dorus", "his lord, Bishop Lupus"
# NOTE: use [,\s]+ after nouns to handle "son, Name" (comma before name)
ADJ_NOUN_PREFIX = (
    r'(?:(?:his|her|my|our|your)\s+)?'          # possessive
    r'(?:(?:most|very|right|truly|dearly|deeply)\s+)?'  # intensifier
    r'(?:(?:dear|beloved|well-beloved|sincerely\s+beloved|reverend|'
    r'holy|blessed|venerable|illustrious|distinguished|esteemed|'
    r'devout|pious|faithful)\s+)?'              # adjective
    r'(?:(?:son|daughter|sons|daughters|brother|brothers|sister|sisters|'
    r'father|mother|friend|colleague|lord|servant|partner|co-bishop|'
    r'fellow|fellow-bishop|fellow-servant|co-worker|presbyter|deacon|'
    r'bishop|pope|abbot|priest|monk|nun|count|duke|prefect|senator|'
    r'metropolitan|vicar|legate|patrician|exarch|governor|emperor|'
    r'general|consul|tribune|official|noble|nobleman)[,\s]+)?'   # noun/title
)


def should_skip_to_value(raw: str) -> bool:
    lower = raw.strip().lower()
    for pat in SKIP_PATTERNS:
        if re.match(pat, lower):
            return True
    return False


def extract_proper_name_from_phrase(phrase: str) -> str | None:
    """
    Given "The usurper Eugenius" or "his beloved brother Dorus [annotation]",
    find the most likely personal name (capitalized, non-title word).
    Returns only the first proper name token (not two) to avoid "Name Title" pairs.
    """
    if not phrase:
        return None
    if should_skip_to_value(phrase):
        return None
    # Remove bracket annotations like "[Theodosius II]"
    phrase = re.sub(r'\[.*?\]', '', phrase).strip()
    # Remove em-dash and everything after it (often SENDER signature in inverted format)
    phrase = re.sub(r'\s*[—–].*$', '', phrase).strip()
    words = phrase.replace(',', ' ').replace('.', ' ').split()
    for w in words:
        w_clean = w.rstrip('.,;:!?)')
        if not w_clean:
            continue
        if w_clean[0].isupper() and w_clean.lower() not in TITLE_WORDS and len(w_clean) > 2:
            # Return the first valid proper name token only
            result = w_clean.strip('[]')
            if result and result[0].isupper():
                return result
    return None


def strip_leading_title(name: str) -> str:
    """Strip a leading title word like 'Bishop Lupus' → 'Lupus'."""
    words = name.split()
    if len(words) >= 2 and words[0].lower() in TITLE_WORDS:
        return ' '.join(words[1:])
    return name


def looks_like_name(name: str) -> bool:
    if not name or len(name) < 2 or len(name) > 80:
        return False
    lower = name.lower()
    for w in NOISE_WORDS:
        if f' {w} ' in f' {lower} ':
            return False
    if not (name[0].isupper() or name[0].isdigit()):
        return False
    if name == name.lower():
        return False
    # Reject if it looks like a whole sentence
    if len(name.split()) > 4:
        return False
    return True


def extract_city_from_name(name: str):
    m = re.search(r'\bof\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', name)
    if m:
        city = m.group(1).lower()
        if city in CITY_COORDS:
            return CITY_COORDS[city], city
        city_first = city.split()[0]
        if city_first in CITY_COORDS:
            return CITY_COORDS[city_first], city_first
    return None, None


def extract_recipient_v2(text: str, collection: str, subject: str) -> str | None:
    if not text:
        return None

    lines = text.split('\n')

    # --- Pattern A: Enhanced "To:" header ---
    for line in lines[:25]:
        line_s = line.strip()
        m = re.match(r'^To:\s*(.+?)$', line_s, re.IGNORECASE)
        if m:
            raw = m.group(1).strip().rstrip('.,;:')
            if should_skip_to_value(raw):
                return None  # Confirmed anonymous — stop
            name = extract_proper_name_from_phrase(raw)
            if name and looks_like_name(name):
                return name

    # --- Pattern B: Libanius "To Name. (year)" ---
    for line in lines[:10]:
        line_s = line.strip()
        # "To Auxentius. (358)" or "To Meterius and Alcimus. (359)"
        m = re.match(r'^To\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:\s+and\s+[A-Z][a-z]+)?[.,]\s*\(\d', line_s)
        if m:
            name = m.group(1).strip()
            if looks_like_name(name) and name.lower() not in {'the', 'same', 'another'}:
                return name

    # --- Pattern C: "AUTHOR, [title], to [adj+nouns] NAME" ---
    # e.g. "Leo, the bishop, to his dearly beloved son, Eutyches [...]"
    #      "Leo, Bishop of Rome, to his beloved brother Dorus, Bishop of Beneventum."
    for line in lines[:20]:
        line_s = line.strip()
        m = re.match(
            KNOWN_AUTHORS_RE.pattern +
            r'(?:,\s*[^,\n]+)*,\s*to\s+' +
            ADJ_NOUN_PREFIX +
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
            r'(?=\s*[\[,.\n]|$)',
            line_s, re.IGNORECASE
        )
        if m:
            # re.IGNORECASE means [A-Z] matches lowercase too — must check isupper() explicitly
            groups = [g for g in m.groups() if g and g[0].isupper() and g.lower() not in TITLE_WORDS]
            if groups:
                name = strip_leading_title(groups[-1].strip())
                if name[0].isupper() and name.lower() not in TITLE_WORDS and looks_like_name(name):
                    return name

    # --- Pattern D: "AUTHOR to [adj+nouns] NAME" (no comma between author and "to") ---
    # e.g. "Sidonius to his dear Firminus, greetings."
    #      "Sidonius to his sons Simplicius and Apollinaris."
    #      "Sidonius to his lord, Bishop Lupus [of Troyes]."
    for line in lines[:20]:
        line_s = line.strip()
        m = re.match(
            KNOWN_AUTHORS_RE.pattern +
            r'\s+to\s+' +
            ADJ_NOUN_PREFIX +
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
            r'(?=\s*[\[,.\n]|$|\s+and\b)',
            line_s, re.IGNORECASE
        )
        if m:
            groups = [g for g in m.groups() if g and g[0].isupper() and g.lower() not in TITLE_WORDS]
            if groups:
                name = strip_leading_title(groups[-1].strip())
                if name[0].isupper() and name.lower() not in TITLE_WORDS and looks_like_name(name):
                    return name

    # --- Pattern E: "King/Emperor SENDER to NAME" (Cassiodorus royal sender) ---
    for line in lines[:10]:
        line_s = line.strip()
        m = re.match(
            r'^(?:King|Emperor|Empress|Pope)\s+\w+(?:\s+\w+)?\s+to\s+' +
            ADJ_NOUN_PREFIX +
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
            r'(?=\s*[\[,.\n]|$)',
            line_s
        )
        if m:
            groups = [g for g in m.groups() if g and g[0].isupper() and g.lower() not in TITLE_WORDS]
            if groups:
                name = groups[-1].strip()
                if name[0].isupper() and name.lower() not in TITLE_WORDS and looks_like_name(name):
                    return name
        # ALL-CAPS variant: "KING THEODERIC TO AGAPITUS, VIR ILLUSTRIS"
        m = re.match(
            r'^(?:KING|EMPEROR|EMPRESS|POPE)\s+[A-Z]+(?:\s+[A-Z]+)?\s+TO\s+'
            r'([A-Z][A-Z]+(?:\s+[A-Z]+)?)'
            r'(?:,|\.|$|\s*$)',
            line_s
        )
        if m:
            raw = m.group(1).strip()
            name = raw.title()
            if name.lower() not in TITLE_WORDS and looks_like_name(name):
                return name

    # --- Pattern F: "To [title/adj] NAME [annotation]." ---
    # Handles: "To the Lord Bishop Lupus [Lupus of Troyes...]."
    #          "To Emperor Theodosius [Theodosius II], the devout Augustus — Leo..."
    #          "To Simplicius and Apollinaris [annotation]."
    for line in lines[:15]:
        line_s = line.strip()
        # Match "To PHRASE [optional bracket] PUNCT" and extract name from phrase
        m = re.match(r'^To\s+(.+?)(?:\s*\[.*?\])?\s*[,.\n]', line_s)
        if m:
            phrase = m.group(1).strip()
            if not should_skip_to_value(phrase):
                name = extract_proper_name_from_phrase(phrase)
                if name and looks_like_name(name):
                    return name

    # --- Pattern G: greetings pattern with adj+nouns ---
    # e.g. "Augustine to the clergy and elders of Hippo, greetings." → group, skip
    # "Augustine to Generosus, greetings." → "Generosus"
    for line in lines[:20]:
        line_s = line.strip()
        m = re.match(
            KNOWN_AUTHORS_RE.pattern +
            r'(?:,\s*[^,\n]+)*[,\s]+to\s+' +
            ADJ_NOUN_PREFIX +
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),'
            r'?\s+(?:greetings|greeting|health|salvation|peace)',
            line_s, re.IGNORECASE
        )
        if m:
            groups = [g for g in m.groups() if g and g[0].isupper() and g.lower() not in TITLE_WORDS]
            if groups:
                name = groups[-1].strip()
                if name.lower() not in TITLE_WORDS and looks_like_name(name):
                    return name

    # --- Pattern H: subject_summary direct match ---
    if subject:
        # "Leo, the bishop, to his dearly beloved son, Eutyches, presbyter."
        m = re.match(
            KNOWN_AUTHORS_RE.pattern +
            r'(?:,\s*[^,\n]+)*[,\s]+to\s+' +
            ADJ_NOUN_PREFIX +
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            subject.strip(), re.IGNORECASE
        )
        if m:
            groups = [g for g in m.groups() if g and g[0].isupper() and g.lower() not in TITLE_WORDS]
            if groups:
                name = groups[-1].strip()
                if name.lower() not in TITLE_WORDS and looks_like_name(name):
                    return name

    return None


def fuzzy_find_author(cursor, name: str) -> int | None:
    if not name:
        return None
    cursor.execute('SELECT id FROM authors WHERE name = ? COLLATE NOCASE', (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute('SELECT id, name FROM authors WHERE name LIKE ?', (f'%{name}%',))
    row = cursor.fetchone()
    if row:
        return row[0]
    tokens = [t for t in name.split() if len(t) > 3]
    if tokens:
        first = tokens[0]
        cursor.execute('SELECT id, name FROM authors WHERE name LIKE ?', (f'%{first}%',))
        rows = cursor.fetchall()
        if len(rows) == 1:
            return rows[0][0]
        if len(rows) > 1 and len(tokens) > 1:
            second = tokens[1]
            for row in rows:
                if second.lower() in row[1].lower():
                    return row[0]
    return None


def get_coords_for_new_author(name: str, collection: str, sender_lat, sender_lon) -> tuple:
    coords, city = extract_city_from_name(name)
    if coords:
        return coords[0], coords[1], 'strong'
    if collection in COLLECTION_DEFAULTS:
        lat, lon = COLLECTION_DEFAULTS[collection]
        return lat, lon, 'approximate'
    if sender_lat and sender_lon:
        return sender_lat, sender_lon, 'approximate'
    return None, None, 'unknown'


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM letters')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM letters WHERE recipient_id IS NOT NULL')
    baseline_recip = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM letters WHERE distance_km IS NOT NULL')
    baseline_dist = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM authors')
    baseline_authors = cursor.fetchone()[0]

    print(f"Baseline: {baseline_recip}/{total} ({100*baseline_recip//total}%) letters with recipient")
    print(f"          {baseline_dist}/{total} ({100*baseline_dist//total}%) with distance")
    print(f"          {baseline_authors} authors\n")

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
    collection_stats = {}

    # Debug: track what we extract
    debug_extractions = []

    for row in letters:
        letter_id = row['id']
        collection = row['collection']
        text = row['modern_english'] or row['english_text'] or ''
        subject = row['subject_summary'] or ''
        sender_lat = row['sender_lat']
        sender_lon = row['sender_lon']

        recipient_name = extract_recipient_v2(text, collection, subject)
        if not recipient_name:
            failed += 1
            continue

        debug_extractions.append((letter_id, collection, recipient_name))

        existing_id = fuzzy_find_author(cursor, recipient_name)
        if existing_id:
            cursor.execute('UPDATE letters SET recipient_id = ? WHERE id = ?', (existing_id, letter_id))
            matched_existing += 1
            collection_stats[collection] = collection_stats.get(collection, 0) + 1
        else:
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
                collection_stats[collection] = collection_stats.get(collection, 0) + 1
            except sqlite3.IntegrityError:
                cursor.execute('SELECT id FROM authors WHERE name = ?', (recipient_name,))
                r = cursor.fetchone()
                if r:
                    cursor.execute('UPDATE letters SET recipient_id = ? WHERE id = ?', (r[0], letter_id))
                    matched_existing += 1
                    collection_stats[collection] = collection_stats.get(collection, 0) + 1
                else:
                    failed += 1

    conn.commit()

    # Recompute all distances
    cursor.execute("""
        SELECT l.id, a1.lat, a1.lon, a2.lat, a2.lon
        FROM letters l
        JOIN authors a1 ON l.sender_id = a1.id
        JOIN authors a2 ON l.recipient_id = a2.id
        WHERE a1.lat IS NOT NULL AND a1.lon IS NOT NULL
          AND a2.lat IS NOT NULL AND a2.lon IS NOT NULL
    """)
    coord_rows = cursor.fetchall()
    dist_updated = 0
    for lid, s_lat, s_lon, r_lat, r_lon in coord_rows:
        dist = haversine(s_lat, s_lon, r_lat, r_lon)
        cursor.execute("UPDATE letters SET distance_km = ? WHERE id = ?", (round(dist, 1), lid))
        dist_updated += 1
    conn.commit()

    cursor.execute('SELECT COUNT(*) FROM letters WHERE recipient_id IS NOT NULL')
    new_recip = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM letters WHERE distance_km IS NOT NULL')
    new_dist = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM authors')
    new_authors = cursor.fetchone()[0]

    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"  Matched existing:  {matched_existing}")
    print(f"  Created new:       {created_new}")
    print(f"  Failed:            {failed}")
    print()
    pct_b = 100 * baseline_recip / total
    pct_a = 100 * new_recip / total
    print(f"  Recipient coverage: {baseline_recip} → {new_recip} (+{new_recip - baseline_recip})")
    print(f"  {pct_b:.1f}% → {pct_a:.1f}% (+{pct_a - pct_b:.1f}pp)")
    pct_db = 100 * baseline_dist / total
    pct_da = 100 * new_dist / total
    print(f"  Distance coverage:  {baseline_dist} → {new_dist} (+{new_dist - baseline_dist})")
    print(f"  {pct_db:.1f}% → {pct_da:.1f}% (+{pct_da - pct_db:.1f}pp)")
    print(f"  Authors: {baseline_authors} → {new_authors}")
    print()

    if collection_stats:
        print("Matches per collection:")
        for coll, cnt in sorted(collection_stats.items(), key=lambda x: -x[1]):
            print(f"  {coll:<30} +{cnt}")
    print()

    if debug_extractions[:30]:
        print("Sample extractions:")
        for lid, coll, name in debug_extractions[:30]:
            print(f"  [{coll[:22]:<22}] id={lid:<5} → '{name}'")

    if new_authors_created[:15]:
        print("\nSample new authors created:")
        for name, coll, lat, lon, conf in new_authors_created[:15]:
            coords = f"({lat:.2f}, {lon:.2f})" if lat else "(no coords)"
            print(f"  [{coll[:20]:<20}] {name:<35} {coords} [{conf}]")

    conn.close()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
ai_extract_recipients.py

Pure text-based recipient extraction for the three largest collections missing
recipient_id: symmachus (648), isidore_pelusium (381), gregory_great (148).

NO external API calls — works entirely from text in the database.

Strategies per collection:
  - gregory_great: "Gregory to NAME" / "To all the Bishops of REGION" / group patterns
  - isidore_pelusium: subject_summary has Greek names ("To Αθανασιω") → transliterate;
                      modern_english has "To: NAME" headers
  - symmachus: no salutation lines — use subject_summary + partial-match on known
               correspondents; look for "To [Name]" in latin_text header lines
"""

import sqlite3
import re
import math
import unicodedata
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

# ─────────────────────────────────────────────────────────────────────────────
# Greek transliteration (reused from transliterate_greek_names.py)
# ─────────────────────────────────────────────────────────────────────────────

DIPHTHONGS = [
    ("αι", "ai"), ("ει", "ei"), ("οι", "oi"), ("ου", "ou"),
    ("αυ", "au"), ("ευ", "eu"), ("ηυ", "eu"),
    ("γγ", "ng"), ("γκ", "nk"), ("γξ", "nx"), ("γχ", "nch"),
    ("μπ", "mp"), ("ντ", "nt"),
]

GREEK_TO_LATIN = {
    'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e',
    'ζ': 'z', 'η': 'e', 'θ': 'th', 'ι': 'i', 'κ': 'k',
    'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o',
    'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't',
    'υ': 'u', 'φ': 'ph', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o',
    'Α': 'A', 'Β': 'B', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E',
    'Ζ': 'Z', 'Η': 'E', 'Θ': 'Th', 'Ι': 'I', 'Κ': 'K',
    'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X', 'Ο': 'O',
    'Π': 'P', 'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'U',
    'Φ': 'Ph', 'Χ': 'Ch', 'Ψ': 'Ps', 'Ω': 'O',
}

# Greek role words to strip (dative forms)
GREEK_ROLE_STRIP = {
    'Πρεσβυτερω': 'presbyter',
    'Επισκοπω': 'bishop',
    'Κομητι': 'comes',
    'Μοναχω': 'monk',
    'Μοναζοντι': 'monk',
    'Μοναοθπο': 'monk',
    'Σχολαστικω': 'scholasticus',
    'Σχολαστικο': 'scholasticus',
    'Γραμματικω': 'grammatikos',
    'Αναγνωστη': 'reader',
    'Μαγιστριανω': 'magistrianos',
    'Αρχιμανδριτη': 'archimandrite',
    'Πολιτευομενω': 'decurion',
    'Διακονω': 'deacon',
    'Στρατηλατη': 'military commander',
    'Ηγεμονι': 'governor',
    'Κτητορι': 'landlord',
    'Ιατρω': 'physician',
    'Λαμπροτατω': 'vir clarissimus',
    'Ριαθονο': '',   # OCR noise
    'Μοναθπο': '',  # OCR noise
    'Οομιπ': '',    # OCR noise
}


def has_greek(text):
    if not text:
        return False
    for ch in text:
        if 'GREEK' in unicodedata.name(ch, ''):
            return True
    return False


def strip_accents(text):
    iota_sub = {
        'ᾳ': 'αι', 'ᾴ': 'αι', 'ᾲ': 'αι', 'ᾷ': 'αι', 'ᾶ': 'α',
        'ῃ': 'ηι', 'ῄ': 'ηι', 'ῂ': 'ηι', 'ῇ': 'ηι',
        'ῳ': 'ωι', 'ῴ': 'ωι', 'ῲ': 'ωι', 'ῷ': 'ωι',
    }
    result = []
    for ch in text:
        result.append(iota_sub.get(ch, ch))
    text = ''.join(result)
    decomposed = unicodedata.normalize('NFD', text)
    return ''.join(c for c in decomposed if unicodedata.category(c)[0] != 'M')


def transliterate_word(word):
    if not word or not has_greek(word):
        return word
    base = strip_accents(word)
    first_upper = base[0].isupper() if base else False
    lower = base.lower()
    result = lower
    for greek_di, latin_di in DIPHTHONGS:
        result = result.replace(greek_di, latin_di)
    mapped = []
    for ch in result:
        mapped.append(GREEK_TO_LATIN.get(ch, ch).lower() if ch in GREEK_TO_LATIN else ch)
    result = ''.join(mapped)
    if first_upper and result:
        result = result[0].upper() + result[1:]
    return result


def dative_to_nominative(name):
    """Convert common Greek dative endings to nominative form."""
    if name.endswith('oni'):
        return name[:-1]          # -ωνι → -ον  (Ωριωνι → Orion)
    if name.endswith('oi') and len(name) > 3:
        return name[:-2] + 'os'   # -ωι → -ος
    if name.endswith('ei') and len(name) > 3:
        return name[:-2] + 'es'   # -ηι → -ης
    if name.endswith('ai') and len(name) > 3:
        return name[:-2] + 'a'
    if name.endswith('o') and len(name) > 2 and not name.endswith('ao'):
        return name + 's'         # -ω → -ος
    if name.endswith('i') and len(name) > 3:
        return name[:-1]          # dative -ι consonant stem → strip
    return name


def transliterate_greek_name_field(raw):
    """
    Given a raw subject_summary like "To Αθανασιω Πρεσβυτερω",
    strip the "To " prefix, strip role words, transliterate, convert dative.
    Returns (name_str, role_str) or (None, None) on failure.
    """
    if not raw:
        return None, None

    text = raw.strip()
    # Strip "To " / "To:" prefix
    text = re.sub(r'^To\s*:?\s*', '', text, flags=re.IGNORECASE).strip()

    # Detect role words (Greek)
    role = None
    for greek_role, english_role in GREEK_ROLE_STRIP.items():
        if greek_role in text:
            text = text.replace(greek_role, '').strip()
            if english_role:
                role = english_role
            break

    if not text or not has_greek(text):
        return None, None

    words = text.split()
    transliterated = [transliterate_word(w) for w in words]
    converted = [dative_to_nominative(w) for w in transliterated]
    name = ' '.join(converted).strip()

    # Clean up any remaining non-ASCII garbage (OCR noise)
    name = re.sub(r'[^\x00-\x7F]+', '', name).strip()

    if len(name) < 2 or not name[0].isupper():
        return None, None

    return name, role


# ─────────────────────────────────────────────────────────────────────────────
# Noise / skip patterns
# ─────────────────────────────────────────────────────────────────────────────

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
    'colleague', 'friend', 'servant', 'devout', 'pious', 'faithful',
    'new', 'old', 'great', 'little', 'young',
    'christ', 'jesus', 'god', 'spirit', 'trinity',
    'lords', 'ladies', 'saints', 'martyrs', 'confessors',
    'senate', 'synod', 'council', 'formula',
}

NOISE_WORDS = {
    'which', 'that', 'this', 'what', 'where', 'when', 'although', 'because',
    'however', 'therefore', 'moreover', 'concerning', 'regarding', 'about',
    'will', 'would', 'could', 'should', 'have', 'been', 'were', 'being',
    'request', 'letter', 'epistle', 'write', 'written', 'send', 'sent',
}

# Values to skip entirely — generic or ambiguous
SKIP_RE = re.compile(
    r'^(?:an?\s+(?:unknown|unnamed|unnamed|unidentified)|'
    r'the\s+same|same|to\s+same|to\s+the\s+same|'
    r'unknown|a\s+friend|uncertain|'
    r'all\s+|the\s+faithful|the\s+brethren|the\s+church|'
    r'the\s+clergy|the\s+senate|the\s+bishops|letter\s+\d|'
    r'the\s+newly|an?\s+(?:bishop|monk|presbyter|deacon|priest|'
    r'inquirer|correspondent|recipient|cleric|abbot)\b)',
    re.IGNORECASE
)


def should_skip(text):
    if not text:
        return True
    return bool(SKIP_RE.match(text.strip()))


def looks_like_name(name):
    if not name or len(name) < 2 or len(name) > 60:
        return False
    lower = name.lower()
    for w in NOISE_WORDS:
        if f' {w} ' in f' {lower} ':
            return False
    if not name[0].isupper():
        return False
    if name == name.lower():
        return False
    if len(name.split()) > 5:
        return False
    return True


def extract_proper_name(phrase):
    """From a phrase like 'all bishops of Sicily' or 'Natalis, Bishop of Salona',
    find the first likely personal name."""
    if not phrase:
        return None
    phrase = re.sub(r'\[.*?\]', '', phrase).strip()
    phrase = re.sub(r'\s*[—–].*$', '', phrase).strip()
    words = phrase.replace(',', ' ').replace('.', ' ').split()
    for w in words:
        wc = w.rstrip('.,;:!?)')
        if not wc:
            continue
        if wc[0].isupper() and wc.lower() not in TITLE_WORDS and len(wc) > 2:
            return wc.strip('[]')
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Per-collection extraction functions
# ─────────────────────────────────────────────────────────────────────────────

# Known Symmachus correspondents (from existing letters that DO have recipient_id)
# We'll load these dynamically at runtime.
SYMMACHUS_KNOWN_RECIPIENTS = {}  # name.lower() -> author_id, populated at runtime


def extract_gregory(modern_english, subject_summary):
    """
    Gregory letters almost always start with a salutation line like:
      "Gregory to Victor and Columbus, Bishops of Africa."
      "Gregory to all the Bishops of Sicily."
      "To all the Bishops of Italy."
      "Book I, Letter 1\n\nTo all the Bishops of Sicily.\n\nGregory..."
    Returns (name, is_group) where name is the recipient name/label.
    """
    if not modern_english:
        return None, False

    lines = modern_english.split('\n')

    # Strip boilerplate first lines (navigation menus from newadvent)
    cleaned = []
    for line in lines:
        ls = line.strip()
        # Skip newadvent nav boilerplate
        if re.match(r'^Home\s+Encyclopedia', ls):
            continue
        if ls:
            cleaned.append(ls)

    text_block = '\n'.join(cleaned[:30])

    # Pattern 1: "Gregory to NAME, [title]." — named individual
    # e.g. "Gregory to Victor and Columbus, Bishops of Africa."
    # e.g. "Gregory to Theodorus, Demetrius, Philip..."
    m = re.search(
        r'Gregory\s+to\s+'
        r'(?:(?:his|the|all|our)\s+)?'
        r'([A-Z][a-z]+(?:(?:\s+and\s+|\s*,\s*)[A-Z][a-z]+)*)'
        r'(?:,\s*[Bb]ishop|,\s*[Aa]bishop|\s+[Bb]ishop|\s+[Aa]bishop|,\s+|\.|\s*$)',
        text_block
    )
    if m:
        raw = m.group(1).strip()
        # Check if it's a group description, not a name
        if not should_skip(raw):
            # Multiple names: "Victor and Columbus" → take first as primary
            # or use as-is if it's a meaningful group
            first_name = re.split(r'\s+and\s+|,\s*', raw)[0].strip()
            if first_name.lower() not in TITLE_WORDS and looks_like_name(first_name):
                return first_name, False

    # Pattern 2: "To all the Bishops of REGION" — group letter
    # e.g. "To all the Bishops of Sicily."
    m = re.search(
        r'To\s+(?:all\s+(?:the\s+)?)?[Bb]ishops?\s+(?:of|throughout|in)\s+'
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        text_block
    )
    if m:
        region = m.group(1).strip()
        return f"Bishops of {region}", True

    # Pattern 3: "Gregory to all [clergy/bishops] of REGION"
    m = re.search(
        r'Gregory\s+to\s+all\s+(?:the\s+)?(?:bishops?|clergy|priests?|clerics?)\s+'
        r'(?:of|throughout|in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        text_block
    )
    if m:
        region = m.group(1).strip()
        return f"Bishops of {region}", True

    # Pattern 4: "Gregory to all." — generic group
    m = re.search(r'Gregory\s+to\s+all\s*\.', text_block)
    if m:
        return "All Bishops (general)", True

    # Pattern 5: "To NAME, [title]" line at the start
    for line in cleaned[:8]:
        m = re.match(r'^To\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,.]', line)
        if m:
            name = m.group(1).strip()
            if name.lower() not in TITLE_WORDS and not should_skip(name) and looks_like_name(name):
                return name, False

    # Pattern 6: "To all [Bishops/clergy/priests] of REGION" without "Gregory" prefix
    m = re.search(
        r'To\s+all\s+(?:the\s+)?(?:bishops?|clergy|priests?|clerics?)\s+'
        r'(?:of|throughout|in|under)\s+([A-Z][a-z]+(?:(?:\s+[A-Z][a-z]+){0,2}))',
        text_block
    )
    if m:
        region = m.group(1).strip()
        # Strip bracket annotation
        region = re.sub(r'\s*\[.*?\]', '', region).strip()
        return f"Bishops of {region}", True

    # Pattern 7: Look for "To [title] NAME" line
    for line in cleaned[:10]:
        m = re.match(
            r'^To\s+(?:the\s+)?(?:most\s+)?(?:reverend\s+|holy\s+|blessed\s+)?'
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
            r'(?:,|\s+[Bb]ishop|\s+[Pp]riest|\s+[Aa]bbot|\s*\.|\s*$)',
            line
        )
        if m:
            name = m.group(1).strip()
            if name.lower() not in TITLE_WORDS and not should_skip(name) and looks_like_name(name):
                return name, False

    # Pattern 8: Subject summary
    if subject_summary:
        m = re.search(
            r'Gregory\s+to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            subject_summary
        )
        if m:
            name = m.group(1).strip()
            if name.lower() not in TITLE_WORDS and looks_like_name(name):
                return name, False

    return None, False


def extract_isidore(modern_english, subject_summary, english_text):
    """
    Isidore Pelusium letters have Greek names in subject_summary.
    Modern_english often has "From: ... / To: ..." structured headers.
    Falls back to reading body text for "To: NAME" patterns.
    """

    # Strategy 1: subject_summary with Greek names — most reliable
    if subject_summary and has_greek(subject_summary):
        ss = subject_summary.strip()
        if should_skip(ss):
            return None, None
        name, role = transliterate_greek_name_field(ss)
        if name and looks_like_name(name):
            return name, role

    # Strategy 2: "To: NAME" / "To: A [title]" in modern_english structured header
    if modern_english:
        lines = modern_english.split('\n')
        for line in lines[:15]:
            ls = line.strip()
            m = re.match(r'^To\s*:\s*(.+)$', ls, re.IGNORECASE)
            if m:
                raw = m.group(1).strip().rstrip('.,;:')
                if should_skip(raw):
                    return None, None
                # Check if it's a named person vs generic role
                # "An unnamed recipient" → skip; "Athanasius" → keep
                m2 = re.match(
                    r'^(?:An?\s+(?:unnamed|unknown|inquirer|correspondent|recipient|cleric|monk|bishop|deacon|priest|presbyter|abbots?|friend)\b)',
                    raw, re.IGNORECASE
                )
                if m2:
                    return None, None
                # Try to extract a proper name
                name = extract_proper_name(raw)
                if name and looks_like_name(name) and name.lower() not in TITLE_WORDS:
                    # Determine role if title present
                    role = None
                    if 'bishop' in raw.lower():
                        role = 'bishop'
                    elif 'priest' in raw.lower() or 'presbyter' in raw.lower():
                        role = 'presbyter'
                    elif 'monk' in raw.lower():
                        role = 'monk'
                    return name, role

    # Strategy 3: subject_summary with English text "To NAME" (non-Greek)
    if subject_summary and not has_greek(subject_summary):
        ss = subject_summary.strip()
        m = re.match(r'^To\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', ss)
        if m:
            raw = m.group(1).strip()
            if not should_skip(raw) and raw.lower() not in TITLE_WORDS:
                if looks_like_name(raw):
                    return raw, None

    return None, None


# Symmachus known correspondents — will be populated from the DB at runtime
_SYMMACHUS_CORR_LOADED = False
SYMMACHUS_CORR = []  # list of (name, author_id, lower_name)


def load_symmachus_correspondents(cursor):
    """Load all known Symmachus correspondents from letters that have recipient_id."""
    global _SYMMACHUS_CORR_LOADED, SYMMACHUS_CORR
    if _SYMMACHUS_CORR_LOADED:
        return
    cursor.execute('''
        SELECT DISTINCT a.id, a.name
        FROM letters l
        JOIN authors a ON l.recipient_id = a.id
        WHERE l.collection = 'symmachus'
    ''')
    rows = cursor.fetchall()
    SYMMACHUS_CORR = [(r[1], r[0], r[1].lower()) for r in rows]
    _SYMMACHUS_CORR_LOADED = True


def extract_symmachus(modern_english, subject_summary, latin_text, cursor):
    """
    Symmachus letters rarely have explicit English salutations.
    Strategies:
    1. Look for "SYMMAQUE À [NAME]" or Latin header "SYMMACHI AD [NAME]"
    2. Check first line of latin_text for addressee
    3. Check subject_summary for any name reference
    4. Pattern match the modern_english opening for "you" context cues
       and compare against known Symmachus correspondents
    """
    load_symmachus_correspondents(cursor)

    # Strategy 1: Latin header patterns
    # Symmachus Latin headers often are: "AD AVIENVM" / "SYMMACHI AD AVIENVM"
    if latin_text:
        # Look for "AD [NAME]" in first few lines (all caps possible from OCR)
        for line in latin_text.split('\n')[:10]:
            ls = line.strip()
            # "AD AVIENVM" or "ad Aviemum" at start of line
            m = re.match(r'^(?:SYMMACHUS?|SYMMACHI?|Q\.\s*AUR\.\s*SYMMACHI?)?\s*AD\s+([A-Z][A-Z]+)(?:\s*$|\.|\s+)', ls)
            if m:
                raw = m.group(1)
                # Title-case it
                name = raw.title()
                # Fix common Latin endings: AVIENVM → Avienum, NICOMACHVM → Nicomachus
                # Strip trailing -VM/-M accusative/dative ending
                name = re.sub(r'vm$', 'um', name, flags=re.IGNORECASE)
                if looks_like_name(name) and name.lower() not in TITLE_WORDS:
                    return name
            # Mixed case "ad Avienum"
            m2 = re.match(r'^[Aa][Dd]\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', ls)
            if m2:
                name = m2.group(1).strip()
                if looks_like_name(name) and name.lower() not in TITLE_WORDS:
                    return name

    # Strategy 2: Check subject_summary
    if subject_summary:
        ss = subject_summary.strip()
        # "To NAME" directly
        m = re.match(r'^To\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,.]?$', ss)
        if m:
            name = m.group(1).strip()
            if not should_skip(name) and name.lower() not in TITLE_WORDS and looks_like_name(name):
                return name

    # Strategy 3: scan modern_english opening for "To [Name]" salutation
    if modern_english:
        lines = modern_english.split('\n')
        for line in lines[:10]:
            ls = line.strip()
            # Direct "To NAME," salutation
            m = re.match(r'^To\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,.]', ls)
            if m:
                name = m.group(1).strip()
                if not should_skip(name) and name.lower() not in TITLE_WORDS and looks_like_name(name):
                    return name
            # "Symmachus to NAME" (rare but possible in some translations)
            m2 = re.match(r'^Symmachus\s+to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', ls)
            if m2:
                name = m2.group(1).strip()
                if not should_skip(name) and name.lower() not in TITLE_WORDS and looks_like_name(name):
                    return name

    # Strategy 4: Check if known correspondents appear prominently in the opening
    # This helps when no salutation exists — a name mentioned in the first sentence
    # that matches a known Symmachus correspondent is likely the recipient
    if modern_english and SYMMACHUS_CORR:
        opening = modern_english[:600]
        # Sort by name length descending to prefer longer/more specific names
        sorted_corr = sorted(SYMMACHUS_CORR, key=lambda x: len(x[0]), reverse=True)
        for name, author_id, lower_name in sorted_corr:
            # Only check names > 4 chars to avoid false positives with short names
            if len(lower_name) < 5:
                continue
            # Must appear as a word boundary match in opening
            if re.search(r'\b' + re.escape(name) + r'\b', opening, re.IGNORECASE):
                return name

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Author lookup and creation
# ─────────────────────────────────────────────────────────────────────────────

CITY_COORDS = {
    'rome': (41.8967, 12.4822), 'milan': (45.4642, 9.19),
    'carthage': (36.8065, 10.1815), 'hippo': (36.8833, 7.75),
    'alexandria': (31.2001, 29.9187), 'antioch': (36.2021, 36.1601),
    'constantinople': (41.0082, 28.9784), 'jerusalem': (31.7054, 35.2195),
    'pelusium': (31.0167, 32.55), 'ravenna': (44.4184, 12.2035),
    'sicily': (37.6, 14.0154), 'numidia': (36.0, 7.0),
    'africa': (36.0, 10.0), 'gaul': (46.0, 2.0),
    'spain': (40.4168, -3.7038), 'dalmatia': (43.9159, 17.6791),
    'pannonia': (47.0, 17.0), 'thrace': (42.0, 27.0),
    'illyricum': (42.5, 20.0), 'epirus': (39.5, 20.5),
    'sardinia': (40.1209, 9.0129), 'corsica': (42.0, 9.0),
    'campania': (41.0, 14.5), 'hellas': (38.5, 22.5),
    'greece': (38.5, 22.5), 'egypt': (27.0, 30.0),
    'italy': (43.0, 12.0), 'sicilia': (37.6, 14.0154),
    'calabria': (38.5, 16.0), 'apulia': (41.0, 16.0),
    'lombardy': (45.5, 10.0), 'aquitaine': (44.0, 1.0),
}

COLLECTION_COORDS = {
    'gregory_great': (41.8967, 12.4822),  # Rome
    'isidore_pelusium': (31.0167, 32.55),  # Pelusium
    'symmachus': (41.8967, 12.4822),       # Rome
}


def fuzzy_find_author(cursor, name):
    """Find an author by exact match, then partial match, then token match."""
    if not name:
        return None
    # Exact match (case-insensitive)
    cursor.execute('SELECT id FROM authors WHERE name = ? COLLATE NOCASE', (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    # Partial match — name is contained in author name
    cursor.execute('SELECT id, name FROM authors WHERE name LIKE ?', (f'%{name}%',))
    rows = cursor.fetchall()
    if len(rows) == 1:
        return rows[0][0]
    if len(rows) > 1:
        # Try to find exact word match
        name_lower = name.lower()
        for r in rows:
            if name_lower == r[1].lower().split(',')[0].strip():
                return r[0]
        # Prefer shorter names (more specific match)
        return min(rows, key=lambda r: len(r[1]))[0]
    # Token match
    tokens = [t for t in name.split() if len(t) > 4]
    if tokens:
        cursor.execute('SELECT id, name FROM authors WHERE name LIKE ?',
                       (f'%{tokens[0]}%',))
        rows = cursor.fetchall()
        if len(rows) == 1:
            return rows[0][0]
        if len(rows) > 1 and len(tokens) > 1:
            for r in rows:
                if tokens[1].lower() in r[1].lower():
                    return r[0]
    return None


def get_coords(name, collection, sender_lat, sender_lon):
    """Get coordinates for a new author entry."""
    # Check if name contains a city reference
    m = re.search(r'\bof\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', name)
    if m:
        city = m.group(1).lower()
        if city in CITY_COORDS:
            return CITY_COORDS[city][0], CITY_COORDS[city][1], 'strong'
        # Try first word of city
        city0 = city.split()[0]
        if city0 in CITY_COORDS:
            return CITY_COORDS[city0][0], CITY_COORDS[city0][1], 'approximate'
    # For group names like "Bishops of Sicily", extract region
    m2 = re.search(r'(?:Bishops?|Clergy|Priests?)\s+of\s+([A-Z][a-z]+)', name)
    if m2:
        region = m2.group(1).lower()
        if region in CITY_COORDS:
            return CITY_COORDS[region][0], CITY_COORDS[region][1], 'approximate'
    if collection in COLLECTION_COORDS:
        lat, lon = COLLECTION_COORDS[collection]
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


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

TARGET_COLLECTIONS = ('symmachus', 'isidore_pelusium', 'gregory_great')


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # ── Baseline stats ──
    cursor.execute('SELECT COUNT(*) FROM letters')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM letters WHERE recipient_id IS NOT NULL')
    baseline_recip = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM authors')
    baseline_authors = cursor.fetchone()[0]

    print(f"=== ai_extract_recipients.py ===")
    print(f"Total letters: {total}")
    print(f"Baseline recipients assigned: {baseline_recip} ({100*baseline_recip/total:.1f}%)")
    print(f"Baseline authors: {baseline_authors}")
    print()

    # ── Load target letters ──
    placeholders = ','.join('?' for _ in TARGET_COLLECTIONS)
    cursor.execute(f'''
        SELECT l.id, l.collection, l.modern_english, l.english_text, l.latin_text,
               l.subject_summary, l.sender_id,
               a.lat AS sender_lat, a.lon AS sender_lon, a.name AS sender_name
        FROM letters l
        LEFT JOIN authors a ON l.sender_id = a.id
        WHERE l.recipient_id IS NULL
          AND l.collection IN ({placeholders})
        ORDER BY l.collection, l.id
    ''', TARGET_COLLECTIONS)
    letters = cursor.fetchall()

    print(f"Letters to process: {len(letters)}")
    per_coll = {}
    for row in letters:
        per_coll[row['collection']] = per_coll.get(row['collection'], 0) + 1
    for coll, cnt in sorted(per_coll.items(), key=lambda x: -x[1]):
        print(f"  {coll:<30} {cnt}")
    print()

    # ── Pre-load Symmachus correspondents ──
    load_symmachus_correspondents(cursor)
    print(f"Symmachus known correspondents loaded: {len(SYMMACHUS_CORR)}")

    # ── Process ──
    matched_existing = 0
    created_new = 0
    skipped = 0
    failed_extract = 0
    collection_stats = {}
    new_authors_list = []
    sample_extractions = []  # (letter_id, collection, name, matched_existing)

    for row in letters:
        letter_id = row['id']
        coll = row['collection']
        modern = row['modern_english'] or ''
        english = row['english_text'] or ''
        latin = row['latin_text'] or ''
        subject = row['subject_summary'] or ''
        sender_lat = row['sender_lat']
        sender_lon = row['sender_lon']

        # ── Extract recipient name ──
        recipient_name = None
        is_group = False
        role = None

        if coll == 'gregory_great':
            recipient_name, is_group = extract_gregory(modern, subject)
        elif coll == 'isidore_pelusium':
            recipient_name, role = extract_isidore(modern, subject, english)
        elif coll == 'symmachus':
            recipient_name = extract_symmachus(modern, subject, latin, cursor)

        if not recipient_name:
            failed_extract += 1
            continue

        # ── Look up or create author ──
        existing_id = fuzzy_find_author(cursor, recipient_name)

        if existing_id:
            cursor.execute('UPDATE letters SET recipient_id = ? WHERE id = ?',
                           (existing_id, letter_id))
            matched_existing += 1
            collection_stats[coll] = collection_stats.get(coll, 0) + 1
            if len(sample_extractions) < 60:
                sample_extractions.append((letter_id, coll, recipient_name, True))
        else:
            # Create new author
            lat, lon, conf = get_coords(recipient_name, coll, sender_lat, sender_lon)
            notes_parts = []
            if is_group:
                notes_parts.append('group recipient')
            if role:
                notes_parts.append(f'role: {role}')
            notes_str = '; '.join(notes_parts) if notes_parts else None

            try:
                if lat is not None:
                    cursor.execute(
                        'INSERT INTO authors (name, lat, lon, location_confidence, notes, role) VALUES (?,?,?,?,?,?)',
                        (recipient_name, lat, lon, conf, notes_str, role)
                    )
                else:
                    cursor.execute(
                        'INSERT INTO authors (name, location_confidence, notes, role) VALUES (?,?,?,?)',
                        (recipient_name, conf, notes_str, role)
                    )
                new_id = cursor.lastrowid
                cursor.execute('UPDATE letters SET recipient_id = ? WHERE id = ?',
                               (new_id, letter_id))
                created_new += 1
                collection_stats[coll] = collection_stats.get(coll, 0) + 1
                new_authors_list.append((recipient_name, coll, lat, lon, conf))
                if len(sample_extractions) < 60:
                    sample_extractions.append((letter_id, coll, recipient_name, False))
            except sqlite3.IntegrityError:
                # Name conflict — retry lookup
                cursor.execute('SELECT id FROM authors WHERE name = ? COLLATE NOCASE',
                               (recipient_name,))
                r = cursor.fetchone()
                if r:
                    cursor.execute('UPDATE letters SET recipient_id = ? WHERE id = ?',
                                   (r[0], letter_id))
                    matched_existing += 1
                    collection_stats[coll] = collection_stats.get(coll, 0) + 1
                else:
                    failed_extract += 1

    conn.commit()

    # ── Recompute distances for newly assigned letters ──
    cursor.execute('''
        SELECT l.id, a1.lat, a1.lon, a2.lat, a2.lon
        FROM letters l
        JOIN authors a1 ON l.sender_id = a1.id
        JOIN authors a2 ON l.recipient_id = a2.id
        WHERE a1.lat IS NOT NULL AND a1.lon IS NOT NULL
          AND a2.lat IS NOT NULL AND a2.lon IS NOT NULL
    ''')
    dist_rows = cursor.fetchall()
    for lid, s_lat, s_lon, r_lat, r_lon in dist_rows:
        dist = haversine(s_lat, s_lon, r_lat, r_lon)
        cursor.execute('UPDATE letters SET distance_km = ? WHERE id = ?',
                       (round(dist, 1), lid))
    conn.commit()

    # ── Final stats ──
    cursor.execute('SELECT COUNT(*) FROM letters WHERE recipient_id IS NOT NULL')
    new_recip = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM authors')
    new_authors = cursor.fetchone()[0]

    total_assigned = matched_existing + created_new
    print("=" * 65)
    print("RESULTS")
    print("=" * 65)
    print(f"  Total assigned:       {total_assigned}")
    print(f"    Matched existing:   {matched_existing}")
    print(f"    Created new:        {created_new}")
    print(f"  Failed to extract:    {failed_extract}")
    print()
    pct_b = 100 * baseline_recip / total
    pct_a = 100 * new_recip / total
    print(f"  Recipient coverage:   {baseline_recip} → {new_recip}  (+{new_recip - baseline_recip})")
    print(f"                        {pct_b:.1f}% → {pct_a:.1f}%  (+{pct_a - pct_b:.1f}pp)")
    print(f"  Authors:              {baseline_authors} → {new_authors}  (+{new_authors - baseline_authors})")
    print()

    print("Per-collection breakdown:")
    for coll in TARGET_COLLECTIONS:
        total_missing = per_coll.get(coll, 0)
        assigned = collection_stats.get(coll, 0)
        pct = 100 * assigned / total_missing if total_missing else 0
        print(f"  {coll:<30}  {assigned:>4} / {total_missing:<4}  ({pct:.0f}%)")
    print()

    if sample_extractions:
        print("Sample extractions (first 40):")
        print(f"  {'collection':<25} {'id':<6} {'name':<35} {'status'}")
        print("  " + "-" * 80)
        for lid, coll, name, matched in sample_extractions[:40]:
            status = 'existing' if matched else 'NEW'
            print(f"  {coll:<25} {lid:<6} {name:<35} {status}")

    if new_authors_list:
        print(f"\nNew authors created (first 25 of {len(new_authors_list)}):")
        print(f"  {'name':<35} {'collection':<22} {'coords':<22} confidence")
        print("  " + "-" * 90)
        for name, coll, lat, lon, conf in new_authors_list[:25]:
            coords = f"({lat:.2f},{lon:.2f})" if lat else "(none)"
            print(f"  {name:<35} {coll:<22} {coords:<22} {conf}")

    # ── Verification: show remaining missing by collection ──
    print("\nRemaining missing recipients by collection (top 10):")
    cursor.execute('''
        SELECT collection, COUNT(*) as cnt
        FROM letters WHERE recipient_id IS NULL
        GROUP BY collection ORDER BY cnt DESC LIMIT 10
    ''')
    for row in cursor.fetchall():
        print(f"  {row[0]:<30} {row[1]}")

    conn.close()
    print("\nDone.")


if __name__ == '__main__':
    main()

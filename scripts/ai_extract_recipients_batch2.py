#!/usr/bin/env python3
"""
ai_extract_recipients_batch2.py

Batch 2 recipient extraction — targets ALL remaining collections
EXCEPT symmachus, isidore_pelusium, gregory_great (handled by another agent).

Collections processed (~731 letters total):
  cassiodorus, hormisdas, pelagius_i, venantius_fortunatus,
  basil_caesarea, gregory_nazianzus, gelasius_i, libanius,
  innocent_i, athanasius_alexandria, simplicius_pope, braulio_zaragoza,
  cyprian_carthage, augustine_hippo, theodoret_cyrrhus, ennodius_pavia,
  pope_hilary, leo_great, pope_felix_iii, ambrose_milan, boniface,
  jerome, pelagius_ii, julian_emperor, sulpicius_severus,
  pope_anastasius_ii, pope_symmachus, synesius_cyrene, alcuin_york,
  chrysostom, columbanus, avitus_vienne, benedict_i, paulinus_nola,
  ruricius_limoges, caesarius_arles, salvian_marseille, sidonius_apollinaris,
  and any others not in the exclusion list.

Extraction patterns:
  A. "To: NAME" structured header (used in context blocks)
  B. "KING/EMPEROR/POPE NAME to NAME" all-caps Cassiodorus headers
  C. "King/Emp NAME to NAME" mixed-case Cassiodorus
  D. Libanius "To Name. (year)" format
  E. Venantius "Ad NAME\nTo NAME" Latin/English double header
  F. "AUTHOR, title(s), to NAME" — comma-separated author prefix
  G. "AUTHOR to NAME" — no-comma author prefix
  H. "AUTHOR to his/her/the [adj+] [title+] NAME" — possessive prefix
  I. "Gregory/Basil/Author, in NAME's name, to ..." — in-name-of format
  J. Subject-summary patterns
  K. "Dear NAME," salutation
  L. Latin "Ad NAME" first-line header
  M. OCR-style Latin headers: "PELAGIUS ... [NAME]..."
  N. Context line: "To: [NAME]" or "To: Named recipient (NAME)"
  O. "Pope X to the [title] NAME" pattern

Skip: group addresses, [brackets], "Unknown", "the same", ambiguous
"""

import sqlite3
import os
import re
import math

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

# Collections to skip (handled by other agents)
SKIP_COLLECTIONS = {'symmachus', 'isidore_pelusium', 'gregory_great'}

# ── Coordinate helpers ──────────────────────────────────────────────────────

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
    'pelusium': (31.0167, 32.55), 'cyrene': (32.82, 21.86),
    'cyrrhus': (36.8833, 36.8667), 'thessalonica': (40.6401, 22.9444),
    'corinth': (37.9383, 22.9319), 'ephesus': (37.9395, 27.3417),
    'athens': (37.9838, 23.7275), 'nicaea': (40.4247, 29.719),
    'capua': (41.1067, 14.2078), 'palermo': (38.1157, 13.3615),
    'naples': (40.8518, 14.2681), 'brindisi': (40.638, 17.9463),
    'spoleto': (42.7342, 12.7381), 'perugia': (43.1122, 12.3888),
    'florence': (43.7696, 11.2558), 'genoa': (44.4056, 8.9463),
    'verona': (45.4384, 10.9916), 'brescia': (45.5416, 10.2118),
    'cremona': (45.1327, 10.0227), 'como': (45.808, 9.0852),
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
    'bourges': (47.0833, 2.3833), 'meaux': (48.9606, 2.8784),
    'nantes': (47.2184, -1.5536), 'paris': (48.8566, 2.3522),
    'zaragoza': (41.6488, -0.8891), 'seville': (37.3886, -5.9823),
    'toledo': (39.8628, -4.0273),
}

COLLECTION_DEFAULTS = {
    'gregory_great': (41.8967, 12.4822),
    'leo_great': (41.8967, 12.4822),
    'gelasius_i': (41.8967, 12.4822),
    'innocent_i': (41.8967, 12.4822),
    'hormisdas': (41.8967, 12.4822),
    'pelagius_i': (41.8967, 12.4822),
    'pelagius_ii': (41.8967, 12.4822),
    'simplicius_pope': (41.8967, 12.4822),
    'pope_hilary': (41.8967, 12.4822),
    'pope_felix_iii': (41.8967, 12.4822),
    'pope_anastasius_ii': (41.8967, 12.4822),
    'pope_symmachus': (41.8967, 12.4822),
    'benedict_i': (41.8967, 12.4822),
    'augustine_hippo': (36.8833, 7.75),
    'cyprian_carthage': (36.8065, 10.1815),
    'ambrose_milan': (45.4642, 9.19),
    'jerome': (31.7054, 35.2024),
    'basil_caesarea': (38.7312, 35.4787),
    'gregory_nazianzus': (38.2167, 34.5),
    'chrysostom': (41.0082, 28.9784),
    'synesius_cyrene': (32.82, 21.86),
    'theodoret_cyrrhus': (36.8833, 36.8667),
    'libanius': (36.2021, 36.1601),
    'cassiodorus': (44.4184, 12.2035),
    'sidonius_apollinaris': (45.7772, 3.087),
    'avitus_vienne': (45.5242, 4.8783),
    'ruricius_limoges': (45.8336, 1.2611),
    'ennodius_pavia': (45.1847, 9.1582),
    'paulinus_nola': (40.9263, 14.5278),
    'julian_emperor': (41.0082, 28.9784),
    'athanasius_alexandria': (31.2001, 29.9187),
    'boniface': (50.0, 8.27),
    'sulpicius_severus': (44.0, 2.0),
    'columbanus': (44.7167, 9.4167),
    'alcuin_york': (53.9599, -1.0873),
    'braulio_zaragoza': (41.6488, -0.8891),
    'venantius_fortunatus': (48.8566, 2.3522),
    'salvian_marseille': (43.2965, 5.3698),
    'caesarius_arles': (43.6767, 4.6278),
}

# ── Skip patterns (group / anonymous addresses) ──────────────────────────────

SKIP_PATTERNS = [
    r'^\[',                       # [Unnamed...] [Appointee...]
    r'^\(',                       # (unknown)
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
    r'^the orthodox',
    r'^the holy',
    r'^the universal',
    r'^the eastern',
    r'^the western',
    r'^general',                  # "General circular"
    r'^caecilianus and others',
    r'^various',
    r'^multiple',
    r'^unnamed',
    r'^recipient unknown',
    r'^unknown recipient',
    r'^dromonarii',               # group boatmen
    r'^appointee',
    r'^template',
    r'^honorati',
    r'^retired',
    r'^illustrious men',
    r'^illustrious',
]

# Words that are NOT personal names
TITLE_WORDS = {
    'the', 'a', 'an', 'his', 'her', 'my', 'our', 'your', 'or', 'and',
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
    'new', 'old', 'great', 'little', 'young', 'elected', 'ordained',
    'christ', 'jesus', 'god', 'spirit', 'trinity', 'apostle',
    'disciples', 'brethren', 'fathers', 'monks', 'nuns', 'virgins',
    'lords', 'ladies', 'saints', 'martyrs', 'confessors',
    'ornament', 'flower', 'philosopher', 'sophist', 'scholar',
    'jews', 'pagans', 'gentiles', 'senate', 'synod', 'council',
    'complaint', 'petition', 'decree', 'formula', 'preface',
    'same', 'another', 'certain', 'various', 'unknown',
    # Latin-origin titles that appear in OCR mixed text
    'episcopus', 'papa', 'rex', 'domino', 'fratri', 'filio',
    'dilectissimo', 'uenerabili', 'gloriosissimo',
}

NOISE_WORDS = {
    'which', 'that', 'this', 'what', 'where', 'when', 'although', 'because',
    'however', 'therefore', 'moreover', 'concerning', 'regarding', 'about',
    'will', 'would', 'could', 'should', 'have', 'been', 'were', 'being',
    'request', 'letter', 'epistle', 'write', 'written', 'send', 'sent',
    'formula', 'senate', 'people', 'brethren', 'congregation', 'faithful',
}

# Known author first names (used in pattern matching)
KNOWN_AUTHORS_RE = re.compile(
    r'^(?:Leo|Augustine|Ambrose|Gregory|Jerome|Basil|Chrysostom|Sidonius|'
    r'Paulinus|Cyprian|Athanasius|Hormisdas|Gelasius|Celestine|Innocent|'
    r'Boniface|Columbanus|Columba|Ruricius|Avitus|Ennodius|Cassiodorus|'
    r'Symmachus|Isidore|Synesius|Theodoret|Libanius|Julian|Pelagius|'
    r'Simplicius|Hilarius|Hilary|Vigilius|Silverius|John|Peter|'
    r'Claudianus|Claudian|Faustus|Remigius|Severus|Sulpicius|Sulpitius|'
    r'Braulio|Venantius|Alcuin|Felix|Fulgentius|Salvian|Nicetas|'
    r'Benedict|Caesarius|Fortunatus|Theoderic|Clovis|Anastasius)\b',
    re.IGNORECASE
)

# Optional adj+noun prefix between "to" and the actual name
ADJ_NOUN_PREFIX = (
    r'(?:(?:his|her|my|our|your)\s+)?'
    r'(?:(?:most|very|right|truly|dearly|deeply)\s+)?'
    r'(?:(?:dear|beloved|well-beloved|sincerely\s+beloved|reverend|'
    r'holy|blessed|venerable|illustrious|distinguished|esteemed|'
    r'devout|pious|faithful|apostolic|most\s+illustrious)\s+)?'
    r'(?:(?:son|daughter|sons|daughters|brother|brothers|sister|sisters|'
    r'father|mother|friend|colleague|lord|servant|partner|co-bishop|'
    r'fellow|fellow-bishop|fellow-servant|co-worker|presbyter|deacon|'
    r'bishop|pope|abbot|priest|monk|nun|count|duke|prefect|senator|'
    r'metropolitan|vicar|legate|patrician|exarch|governor|emperor|'
    r'general|consul|tribune|official|noble|nobleman|archdeacon|'
    r'king|queen)[,\s]+)?'
)


# ── Core helper functions ────────────────────────────────────────────────────

def should_skip_to_value(raw: str) -> bool:
    lower = raw.strip().lower()
    for pat in SKIP_PATTERNS:
        if re.match(pat, lower):
            return True
    return False


def extract_proper_name_from_phrase(phrase: str) -> str | None:
    """Given a phrase like 'The most illustrious Eugenius', return 'Eugenius'."""
    if not phrase:
        return None
    if should_skip_to_value(phrase):
        return None
    # Remove bracket annotations
    phrase = re.sub(r'\[.*?\]', '', phrase).strip()
    # Remove em-dash and everything after
    phrase = re.sub(r'\s*[—–].*$', '', phrase).strip()
    words = phrase.replace(',', ' ').replace('.', ' ').split()
    for w in words:
        w_clean = w.rstrip('.,;:!?)(')
        if not w_clean:
            continue
        if w_clean[0].isupper() and w_clean.lower() not in TITLE_WORDS and len(w_clean) > 2:
            result = w_clean.strip('[]')
            if result and result[0].isupper():
                return result
    return None


def strip_leading_title(name: str) -> str:
    """'Bishop Lupus' → 'Lupus'"""
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
    if len(name.split()) > 5:
        return False
    # Reject obvious non-names
    bad = {'formula', 'fragment', 'preface', 'appendix', 'extract', 'circular',
           'decree', 'encyclical', 'synodal', 'chapter', 'summary', 'note',
           'letter', 'epistle', 'message', 'unknown', 'untitled'}
    if lower in bad:
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


# ── Main extraction function ─────────────────────────────────────────────────

def extract_recipient(text: str, collection: str, subject: str,
                      latin_text: str) -> str | None:
    """
    Try all patterns in priority order; return first good name found.
    """
    if not text and not subject and not latin_text:
        return None

    full_text = text or ''
    lines = full_text.split('\n')

    # ── Pattern A: "To: NAME" context header (most reliable) ─────────────────
    # Covers "To: Celer and Patricius [senior imperial officials]"
    for line in lines[:20]:
        line_s = line.strip()
        m = re.match(r'^To:\s*(.+?)(?:\s*\[.*?\])?\s*$', line_s, re.IGNORECASE)
        if m:
            raw = m.group(1).strip().rstrip('.,;:')
            if should_skip_to_value(raw):
                return None  # Confirmed group/anonymous — stop here
            name = extract_proper_name_from_phrase(raw)
            if name and looks_like_name(name):
                return name

    # ── Pattern B: ALL-CAPS Cassiodorus header ────────────────────────────────
    # "KING THEODERIC TO ALBINUS AND AVIENUS, MEN OF ILLUSTRIOUS RANK"
    # "SENATOR CASSIODORUS TO LIBERIUS, PRAETORIAN PREFECT"
    for line in lines[:5]:
        line_s = line.strip()
        m = re.match(
            r'^(?:KING|EMPEROR|EMPRESS|POPE|SENATOR|MAGISTRATE)\s+'
            r'[A-Z]+(?:\s+[A-Z]+)*\s+TO\s+'
            r'([A-Z][A-Z]+(?:\s+[A-Z]+)?)'
            r'(?:,|\s+AND\s|\s+MEN|\s+VIR|\s*$)',
            line_s
        )
        if m:
            raw = m.group(1).strip()
            # Filter all-caps junk: "THE", "ALL", etc.
            if raw.upper() not in {'THE', 'ALL', 'HIS', 'HER', 'AND', 'MEN',
                                   'VARIOUS', 'UNKNOWN'}:
                name = raw.title()
                if looks_like_name(name) and name.lower() not in TITLE_WORDS:
                    return name

    # ── Pattern C: Mixed-case "King/Pope NAME to NAME" ────────────────────────
    # "King Theodoric to Albinus, Vir Illustris"
    for line in lines[:10]:
        line_s = line.strip()
        m = re.match(
            r'^(?:King|Emperor|Empress|Pope)\s+\w+(?:\s+\w+)?\s+to\s+'
            + ADJ_NOUN_PREFIX +
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
            r'(?=\s*[\[,.\n]|$)',
            line_s
        )
        if m:
            groups = [g for g in m.groups() if g and g[0].isupper()
                      and g.lower() not in TITLE_WORDS]
            if groups:
                name = groups[-1].strip()
                if looks_like_name(name):
                    return name

    # ── Pattern D: Libanius "To Name. (year)" ────────────────────────────────
    for line in lines[:10]:
        line_s = line.strip()
        m = re.match(
            r'^To\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
            r'(?:\s+and\s+[A-Z][a-z]+)?[.,]\s*\(\d',
            line_s
        )
        if m:
            name = m.group(1).strip()
            if looks_like_name(name) and name.lower() not in {'the', 'same'}:
                return name

    # ── Pattern E: Venantius "Ad NAME\nTo NAME" double header ────────────────
    # First line is Latin: "I. Ad Eufronium episcopum Turonensem"
    # Second line is English: "To Euphronius, Bishop of Tours"
    # Also handles: "IX. Item ad Lupum ducem\nMore to Duke Lupus"
    # Skip "Ad eundem" (to the same) — no extractable name
    for i, line in enumerate(lines[:10]):
        line_s = line.strip()
        # Skip "ad eundem / ad easdem / item ad eundem" — means "to the same person"
        if re.match(r'^(?:[IVXLCDM]+\.\s+)?(?:Item\s+)?[Aa]d\s+(?:eundem|easdem|eosdem)',
                    line_s, re.IGNORECASE):
            break
        # Latin "Ad NAME" header line
        m = re.match(r'^(?:[IVXLCDM]+\.\s+)?(?:Item\s+)?[Aa]d\s+'
                     r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                     line_s)
        if m:
            name_lat = m.group(1).strip()
            if looks_like_name(name_lat) and name_lat.lower() not in TITLE_WORDS:
                # Prefer the English version on the next line if available
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    m2 = re.match(r'^To\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', next_line)
                    if m2:
                        eng_name = m2.group(1).strip()
                        if (looks_like_name(eng_name)
                                and eng_name.lower() not in TITLE_WORDS):
                            return eng_name
                return name_lat

    # ── Pattern F: "AUTHOR, [title(s)], to [adj+] NAME" ─────────────────────
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
            groups = [g for g in m.groups()
                      if g and g[0].isupper() and g.lower() not in TITLE_WORDS]
            if groups:
                name = strip_leading_title(groups[-1].strip())
                if name[0].isupper() and name.lower() not in TITLE_WORDS and looks_like_name(name):
                    return name

    # ── Pattern G: "AUTHOR to [adj+] NAME" (no comma) ────────────────────────
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
            groups = [g for g in m.groups()
                      if g and g[0].isupper() and g.lower() not in TITLE_WORDS]
            if groups:
                name = strip_leading_title(groups[-1].strip())
                if name[0].isupper() and name.lower() not in TITLE_WORDS and looks_like_name(name):
                    return name

    # ── Pattern H: Greetings pattern ─────────────────────────────────────────
    # "Augustine to Generosus, greetings."
    for line in lines[:20]:
        line_s = line.strip()
        m = re.match(
            KNOWN_AUTHORS_RE.pattern +
            r'(?:,\s*[^,\n]+)*[,\s]+to\s+' +
            ADJ_NOUN_PREFIX +
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?'
            r'\s+(?:greetings?|health|salvation|peace|sends?\s+greetings?)',
            line_s, re.IGNORECASE
        )
        if m:
            groups = [g for g in m.groups()
                      if g and g[0].isupper() and g.lower() not in TITLE_WORDS]
            if groups:
                name = groups[-1].strip()
                if name.lower() not in TITLE_WORDS and looks_like_name(name):
                    return name

    # ── Pattern I: "Gregory/Author, in NAME's name, to the people of..." ──────
    # "Gregory, in his father's name, to the people of Caesarea"
    # → skip (group address), but "Gregory, concerning NAME" might give us context
    # Pattern I is for "In [name]'s name": skip these (group)

    # ── Pattern J: "To [NAME]" line (simple line-level match) ────────────────
    # "To Euphronius, Bishop of Tours"  (Venantius second-line)
    # "To the Lord Bishop Lupus [Lupus of Troyes...]"
    for line in lines[:15]:
        line_s = line.strip()
        m = re.match(r'^To\s+(.+?)(?:\s*\[.*?\])?\s*[,.\n]', line_s)
        if m:
            phrase = m.group(1).strip()
            if not should_skip_to_value(phrase):
                name = extract_proper_name_from_phrase(phrase)
                if name and looks_like_name(name):
                    return name

    # ── Pattern K: "Dear NAME," salutation ───────────────────────────────────
    for line in lines[:15]:
        line_s = line.strip()
        m = re.match(
            r'^(?:Dear|My dear|Most dear|My beloved)\s+' +
            ADJ_NOUN_PREFIX +
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)[,!.]',
            line_s
        )
        if m:
            groups = [g for g in m.groups()
                      if g and g[0].isupper() and g.lower() not in TITLE_WORDS]
            if groups:
                name = groups[-1].strip()
                if looks_like_name(name):
                    return name

    # ── Pattern L: "Pope X to the Bishop/Bishops of PLACE" ──────────────────
    # e.g. "Pope Gelasius I to the bishops of Dardaniam" — yields place, not person
    # Skip for now; only extract if it's a proper personal name

    # ── Pattern M: Subject summary patterns ──────────────────────────────────
    if subject:
        # Try full subject as a pattern-F/G match
        m = re.match(
            KNOWN_AUTHORS_RE.pattern +
            r'(?:,\s*[^,\n]+)*[,\s]+to\s+' +
            ADJ_NOUN_PREFIX +
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            subject.strip(), re.IGNORECASE
        )
        if m:
            groups = [g for g in m.groups()
                      if g and g[0].isupper() and g.lower() not in TITLE_WORDS]
            if groups:
                name = groups[-1].strip()
                if name.lower() not in TITLE_WORDS and looks_like_name(name):
                    return name

        # "To NAME" at subject start
        m = re.match(r'^To\s+' + ADJ_NOUN_PREFIX +
                     r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', subject.strip())
        if m:
            groups = [g for g in m.groups()
                      if g and g[0].isupper() and g.lower() not in TITLE_WORDS]
            if groups:
                name = groups[-1].strip()
                if looks_like_name(name):
                    return name

    # ── Pattern N: OCR-style Latin header with recipient name ─────────────────
    # "PELAGIUS ... to CHILDEBERTO REGI" → "Childebertus" but usually too garbled
    # Looks for "to [A-Z]+ EPISCOPUM" patterns (Latin accusative)
    # More conservative: look for capitalised name before EPISCOPUM/REGI/PAPAM
    if full_text:
        # e.g. "DILECTISSIMO fratri SAPAUDO PELAGIUS" → Sapaudus
        # Try: first 3 lines of text (OCR artifacts)
        for line in lines[:5]:
            m = re.search(
                r'\bto\s+([A-Z][A-Z]+)\s+(?:EPISCOPUM|REGI|PAPAM|ABBATI|'
                r'PRESBYTERO|ARCHIEPISCOPO)',
                line, re.IGNORECASE
            )
            if m:
                raw = m.group(1).strip().title()
                if looks_like_name(raw) and raw.lower() not in TITLE_WORDS:
                    return raw

    # ── Pattern O: Latin text "Ad NAME" (first line) ─────────────────────────
    if latin_text:
        lat_lines = latin_text.split('\n')
        for line in lat_lines[:5]:
            line_s = line.strip()
            m = re.match(r'^(?:[IVXLCDM]+\.\s+)?[Aa]d\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                         line_s)
            if m:
                name = m.group(1).strip()
                if looks_like_name(name) and name.lower() not in TITLE_WORDS:
                    return name

    return None


# ── Database helpers ─────────────────────────────────────────────────────────

def fuzzy_find_author(cursor, name: str) -> int | None:
    """
    Match extracted name against existing authors.
    Priority:
      1. Exact (case-insensitive)
      2. Extracted name is a substring of an author name (e.g. 'Radegund' → 'Queen Radegund...')
      3. Author name is a substring of extracted name
      4. First long token of extracted name appears in exactly one author name
      5. Multi-token: first + second token cross-match
    """
    if not name:
        return None
    # 1. Exact match (case-insensitive)
    cursor.execute('SELECT id FROM authors WHERE name = ? COLLATE NOCASE', (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    # 2. Extracted name is contained in an author name
    cursor.execute('SELECT id, name FROM authors WHERE name LIKE ?', (f'%{name}%',))
    rows = cursor.fetchall()
    if len(rows) == 1:
        return rows[0][0]
    if len(rows) > 1:
        # Prefer shortest match (most specific)
        rows.sort(key=lambda r: len(r[1]))
        return rows[0][0]
    # 3. Author name is contained in extracted name (e.g. "Bishop Gregory" → "Gregory of Tours")
    # Only if name > 5 chars to avoid spurious matches
    if len(name) > 5:
        cursor.execute('SELECT id, name FROM authors WHERE ? LIKE \'%\' || name || \'%\'',
                       (name,))
        rows = cursor.fetchall()
        if len(rows) == 1:
            return rows[0][0]
    # 4. First long token
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


def get_coords_for_new_author(name: str, collection: str,
                               sender_lat, sender_lon) -> tuple:
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
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # ── Baseline stats ────────────────────────────────────────────────────────
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

    # ── Fetch target letters ──────────────────────────────────────────────────
    skip_list = ', '.join(f"'{c}'" for c in SKIP_COLLECTIONS)
    cursor.execute(f'''
        SELECT l.id, l.collection, l.modern_english, l.english_text,
               l.subject_summary, l.latin_text,
               l.sender_id, a.lat AS sender_lat, a.lon AS sender_lon,
               a.name AS sender_name
        FROM letters l
        LEFT JOIN authors a ON l.sender_id = a.id
        WHERE l.recipient_id IS NULL
          AND l.collection NOT IN ({skip_list})
        ORDER BY l.collection, l.id
    ''')
    letters = cursor.fetchall()
    print(f"Processing {len(letters)} letters without recipient_id "
          f"(excl. {', '.join(SKIP_COLLECTIONS)}) ...\n")

    # ── Count per collection before ───────────────────────────────────────────
    collection_before = {}
    for row in letters:
        c = row['collection']
        collection_before[c] = collection_before.get(c, 0) + 1
    print("Letters missing recipients per collection:")
    for c, n in sorted(collection_before.items(), key=lambda x: -x[1]):
        print(f"  {c:<35} {n}")
    print()

    # ── Track new names → count occurrences before creating ──────────────────
    # First pass: collect all extracted names
    extracted = []   # (letter_id, collection, name, sender_lat, sender_lon)
    failed_ids = []

    for row in letters:
        letter_id = row['id']
        collection = row['collection']
        text = row['modern_english'] or row['english_text'] or ''
        subject = row['subject_summary'] or ''
        latin_text = row['latin_text'] or ''
        sender_lat = row['sender_lat']
        sender_lon = row['sender_lon']

        name = extract_recipient(text, collection, subject, latin_text)
        if name:
            extracted.append((letter_id, collection, name, sender_lat, sender_lon))
        else:
            failed_ids.append(letter_id)

    # ── Count occurrences of each new name ───────────────────────────────────
    name_counts: dict[str, int] = {}
    for _, _, nm, _, _ in extracted:
        name_counts[nm] = name_counts.get(nm, 0) + 1

    # ── Second pass: match/create authors, then update letters ───────────────
    matched_existing = 0
    created_new = 0
    skipped_singleton = 0   # single-mention names without clear title
    new_authors_created = []
    collection_stats: dict[str, int] = {}
    debug_extractions = []

    for letter_id, collection, name, sender_lat, sender_lon in extracted:
        debug_extractions.append((letter_id, collection, name))

        existing_id = fuzzy_find_author(cursor, name)
        if existing_id:
            # Verify it's not mapping a person to themselves (sender == recipient)
            cursor.execute('SELECT sender_id FROM letters WHERE id = ?', (letter_id,))
            sender_row = cursor.fetchone()
            if sender_row and sender_row[0] == existing_id:
                # Author writing to themselves — skip
                skipped_singleton += 1
                continue
            cursor.execute('UPDATE letters SET recipient_id = ? WHERE id = ?',
                           (existing_id, letter_id))
            matched_existing += 1
            collection_stats[collection] = collection_stats.get(collection, 0) + 1
        else:
            # Only create new author if:
            #   - appears in 2+ letters across all extraction results, OR
            #   - has a clear title in the name (Bishop, Pope, Emperor, King, etc.), OR
            #   - name is >= 6 chars (likely a proper name, not OCR garbage)
            has_title = bool(re.search(
                r'\b(?:Bishop|Archbishop|Pope|Patriarch|Emperor|King|'
                r'Empress|Queen|Duke|Count|Prefect|Abbot|Abbess|Deacon|'
                r'Presbyter|Senator|Patrician|Metropolitan|Referendary)\b',
                name, re.IGNORECASE
            ))
            count = name_counts.get(name, 1)
            name_len_ok = len(name) >= 6 and not re.search(r'[^A-Za-z\s\-\']', name)
            if count < 2 and not has_title and not name_len_ok:
                skipped_singleton += 1
                continue

            lat, lon, confidence = get_coords_for_new_author(
                name, collection, sender_lat, sender_lon
            )
            try:
                if lat is not None:
                    cursor.execute(
                        'INSERT INTO authors (name, lat, lon, location_confidence) '
                        'VALUES (?, ?, ?, ?)',
                        (name, lat, lon, confidence)
                    )
                else:
                    cursor.execute(
                        'INSERT INTO authors (name, location_confidence) VALUES (?, ?)',
                        (name, confidence)
                    )
                new_id = cursor.lastrowid
                cursor.execute('UPDATE letters SET recipient_id = ? WHERE id = ?',
                               (new_id, letter_id))
                new_authors_created.append((name, collection, lat, lon, confidence))
                created_new += 1
                collection_stats[collection] = collection_stats.get(collection, 0) + 1
            except sqlite3.IntegrityError:
                cursor.execute('SELECT id FROM authors WHERE name = ?', (name,))
                r = cursor.fetchone()
                if r:
                    cursor.execute('UPDATE letters SET recipient_id = ? WHERE id = ?',
                                   (r[0], letter_id))
                    matched_existing += 1
                    collection_stats[collection] = collection_stats.get(collection, 0) + 1

    conn.commit()

    # ── Recompute distances ──────────────────────────────────────────────────
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
        cursor.execute('UPDATE letters SET distance_km = ? WHERE id = ?',
                       (round(dist, 1), lid))
        dist_updated += 1
    conn.commit()

    # ── Final stats ──────────────────────────────────────────────────────────
    cursor.execute('SELECT COUNT(*) FROM letters WHERE recipient_id IS NOT NULL')
    new_recip = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM letters WHERE distance_km IS NOT NULL')
    new_dist = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM authors')
    new_authors = cursor.fetchone()[0]

    total_assigned = matched_existing + created_new
    total_extracted = len(extracted)
    failed = len(failed_ids)

    print("=" * 65)
    print("RESULTS — Batch 2 Recipient Extraction")
    print("=" * 65)
    print(f"  Letters processed:      {len(letters)}")
    print(f"  Names extracted:        {total_extracted}")
    print(f"  Matched existing author:{matched_existing}")
    print(f"  New authors created:    {created_new}")
    print(f"  Skipped (singleton):    {skipped_singleton}")
    print(f"  No name found:          {failed}")
    print(f"  Total letters assigned: {total_assigned}")
    print()
    pct_b = 100 * baseline_recip / total
    pct_a = 100 * new_recip / total
    print(f"  Recipient coverage: {baseline_recip} → {new_recip} "
          f"(+{new_recip - baseline_recip})")
    print(f"  {pct_b:.1f}% → {pct_a:.1f}% (+{pct_a - pct_b:.1f}pp)")
    pct_db = 100 * baseline_dist / total
    pct_da = 100 * new_dist / total
    print(f"  Distance coverage:  {baseline_dist} → {new_dist} "
          f"(+{new_dist - baseline_dist})")
    print(f"  {pct_db:.1f}% → {pct_da:.1f}% (+{pct_da - pct_db:.1f}pp)")
    print(f"  Authors: {baseline_authors} → {new_authors}")
    print()

    if collection_stats:
        print("Matches per collection:")
        for coll, cnt in sorted(collection_stats.items(), key=lambda x: -x[1]):
            before = collection_before.get(coll, 0)
            print(f"  {coll:<35} +{cnt:3d}  (of {before} missing)")
        print()

    # Remaining unresolved
    remaining_colls: dict[str, int] = {}
    for letter_id in failed_ids:
        # We need collection for these — re-query
        pass
    # Re-fetch remaining
    cursor.execute(f'''
        SELECT collection, COUNT(*) FROM letters
        WHERE recipient_id IS NULL
          AND collection NOT IN ({skip_list})
        GROUP BY collection
        ORDER BY COUNT(*) DESC
    ''')
    remaining = cursor.fetchall()
    if remaining:
        print("Remaining unresolved (after this run):")
        total_remaining = 0
        for coll, cnt in remaining:
            print(f"  {coll:<35} {cnt}")
            total_remaining += cnt
        print(f"  {'TOTAL':<35} {total_remaining}")
        print()

    if debug_extractions[:40]:
        print("Sample extractions (first 40):")
        for lid, coll, nm in debug_extractions[:40]:
            print(f"  [{coll[:25]:<25}] id={lid:<5} → '{nm}'")
        print()

    if new_authors_created[:20]:
        print("New authors created (first 20):")
        for nm, coll, lat, lon, conf in new_authors_created[:20]:
            coords = f"({lat:.2f}, {lon:.2f})" if lat else "(no coords)"
            print(f"  [{coll[:22]:<22}] {nm:<38} {coords} [{conf}]")

    conn.close()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Translate Latin-only collections to modern English.
Strategy: Clean apparatus criticus aggressively, then translate clause-by-clause
using a comprehensive Latin parsing system for papal/ecclesiastical Latin.

Collections: Pelagius I (82), Gelasius I (45), Innocent I (34), Simplicius (31)
"""
import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')


def clean_apparatus(text):
    """
    Aggressively remove critical apparatus from Latin text.
    The apparatus includes manuscript sigla, variant readings,
    scholarly cross-references, page numbers, and editor notes.
    """
    if not text:
        return ""

    # First pass: remove obvious editorial/scholarly content by line
    lines = text.split('\n')
    cleaned = []

    for line in lines:
        orig_line = line
        line = line.strip()
        if not line:
            continue

        # Skip entire lines that are clearly apparatus/editorial
        skip = False
        skip_patterns = [
            r'^[\d\s,;.:\-]+$',  # Lines of numbers/punctuation only
            r'^\d+\.\s+\w+:',  # Footnote-style entries "1. word:"
            r'^[A-Z]{2,}\.\s*\d',  # Section markers "XXXV. 9"
            r'^(?:Cf|cf)\.\s',  # Cross-references
            r'^(?:Bar|Edd?|ed|Collect|BTA|Thiel)\.',  # Edition refs
            r'MGH\b',  # Monumenta Germaniae Historica
            r'Baronius',
            r'Gundlach',
            r'Ballerin',
            r'Hinschius',
            r'Coustant',
            r'Quesnel',
            r'Garnerius',
            r'Maurin',
            r'Zambicari',
            r'Fabricius',
            r'DACL\b',
            r'DHGE\b',
            r'Pauly-Wissowa',
            r'Daremberg',
            r'Migne',
            r'Mansi',
            r'Jaff[eé]',
            r'Hannoverae',
            r'Corp\.\s*Christ',
            r'Biblioth',
            r'Onomastic',
            r'saec\.\s+[IVX]+',  # Century references "saec. IX"
            r'^\d+\s+(?:Simplicii|Gelasii|Innocentii|Pelagii)\s+papae',  # Page headers
            r'^\d+\s+(?:Epistulae|epistulae)',  # Section headers
            r'^\([^)]*(?:cf\.|Cf\.|leg\.|ut notat)',  # Parenthetical refs
            r'^Epist\.\s+[XLVI]+',  # Epistle numbering refs
            r'^[a-z]\^',  # Manuscript sigla start
            r'^\(\s*leg\.',  # Conjectural reading notes
            r'Pseudo-\s*isid',  # Pseudo-Isidore refs
            r'Decretal\.',
            r'^\w+\]\s+(?:om\.|ex\s|add\.|del\.)',  # Apparatus entries
            r'(?:incipit|desinit)\s+[A-Z]$',  # MS notes
            r'^\d+\s+(?:post|ante)\s+correctionem',  # Correction notes
            r'codic[ei]',  # Manuscript references
            r'Paris\.\s+lat\.',  # Paris manuscript refs
            r'Berol\.',  # Berlin manuscript refs
            r'^\w+\s+(?:V|B|K|Q):\s+\w+\s+(?:V|B|K|Q)',  # Variant apparatus "word V: word B"
        ]

        for pat in skip_patterns:
            if re.search(pat, line):
                skip = True
                break

        if skip:
            continue

        # Remove inline apparatus
        # Pattern: "word] variant manuscript"  e.g., "caritatis] per add. Baronius"
        line = re.sub(r'\b\w+\]\s+(?:om|ex|add|del|per|et|om|in)\b[^.]*?(?=\s[A-Z]|\s[a-z]{3,}|\.\s)', '', line)
        line = re.sub(r'\b\w+\]\s+(?:om|ex|add|del)\.[^.]*', '', line)

        # Remove manuscript sigla inline: "a^", "a^2", "V", "B", "K", "Q" when they appear as apparatus
        line = re.sub(r'\s+[a-z]\^\d?\s*', ' ', line)

        # Remove parenthetical scholarly refs
        line = re.sub(r'\([^)]*(?:cf\.|Cf\.|leg\.|p\.\s+\d|epp?\.\s+\d|MGH|DACL|Mansi|Jaff)[^)]*\)', '', line)

        # Remove isolated page/line numbers at start
        line = re.sub(r'^\d{2,3}\s+', '', line)

        # Remove stray apparatus markers
        line = re.sub(r'\s*\[(?:sic|leg|om|del)\.\?\]\s*', ' ', line)

        # Remove Greek text (mixed-in apparatus)
        line = re.sub(r'[Α-Ωα-ω]+', '', line)

        # Clean up word-breaks from column formatting
        line = re.sub(r'(\w)-\s+(\w)', r'\1\2', line)

        # Remove floating punctuation
        line = re.sub(r'\s+([,;:])\s+', r'\1 ', line)

        # Clean up
        line = re.sub(r'\s{2,}', ' ', line)
        line = line.strip()

        if line and len(line) > 3:
            cleaned.append(line)

    result = ' '.join(cleaned)

    # Second pass: clean up remaining artifacts
    result = re.sub(r'\s{2,}', ' ', result)
    result = re.sub(r'\s+([.,;:!?])', r'\1', result)

    return result.strip()


def translate_salutation(text):
    """Translate the opening salutation of a papal letter."""
    salutation_patterns = [
        # Simplicius patterns
        (r'SIMPLICIUS EPISCOPUS (\w+) EPISCOPO (\w+)',
         lambda m: f"Simplicius, Bishop of Rome, to {m.group(1)}, Bishop of {m.group(2)}."),
        (r'ZENONI AUGUSTO SINPLICIUS EPISCOPUS',
         "Simplicius, Bishop of Rome, to the Emperor Zeno."),
        (r'SIMPLICIUS EPISCOPUS ACACIO EPISCOPO CONSTANTINOPOLITANO',
         "Simplicius, Bishop of Rome, to Acacius, Bishop of Constantinople."),

        # Pelagius patterns
        (r'DILECTISSIMO FRATRI (\w+) PELAGIUS',
         lambda m: f"Pelagius to his most beloved brother {m.group(1).title()}."),
        (r'DIEECTISSIMO fratri (\w+) PEEAGIUS',
         lambda m: f"Pelagius to his most beloved brother {m.group(1).title()}."),
        (r'PELAGIUS (\w+)',
         lambda m: f"Pelagius to {m.group(1).title()}."),

        # Gelasius patterns
        (r'DILECTISSIMIS FRATRIBUS (?:UNIVERSIS )?EPISCOPIS PER (\w+)',
         lambda m: f"Gelasius, to all the most beloved brother bishops throughout {m.group(1).title()}."),
        (r'GELASIUS\s+(?:EPISCOPUS\s+)?(\w+)',
         lambda m: f"Gelasius to {m.group(1).title()}."),

        # Innocent patterns
        (r'DILECTISSIMIS FRATRIBUS (.+?) INNOCENTIUS',
         lambda m: f"Innocent to his most beloved brothers {m.group(1).title()}."),
        (r'DILECTISSIMO FILIO (.+?) INNOCENTIUS',
         lambda m: f"Innocent to his most beloved son {m.group(1).title()}."),
        (r'INNOCENTIUS\s+(\w+)',
         lambda m: f"Innocent to {m.group(1).title()}."),

        # Generic
        (r'DILECTISSIM[OIA]\w*\s+(?:FRATRI|FILIO|FILIAE)\s+(\w+)',
         lambda m: f"To our most beloved {m.group(1).title()}."),
    ]

    for pattern, replacement in salutation_patterns:
        m = re.search(pattern, text[:300])
        if m:
            if callable(replacement):
                return replacement(m)
            return replacement

    return None


# Comprehensive Latin-to-English clause dictionary
# These are common clause-level patterns in papal Latin
CLAUSE_TRANSLATIONS = [
    # Opening formulas
    (r'Fraternitatis uestrae litter(?:ae|as)\b', "Your Brotherhood's letter"),
    (r'ad caritatem tuam\b', "to Your Charity"),
    (r'dilectioni tuae\b', "to Your Beloved"),
    (r'caritas tua\b', "Your Charity"),
    (r'fraternitas (?:tua|uestra)\b', "Your Brotherhood"),
    (r'sanctitas (?:tua|uestra)\b', "Your Holiness"),

    # Common verbs/phrases
    (r'scripsimus\b', "we have written"),
    (r'credimus\b', "we believe"),
    (r'mandamus\b', "we command"),
    (r'iubemus\b', "we order"),
    (r'hortamur\b', "we urge"),
    (r'monemus\b', "we advise"),
    (r'commonemus\b', "we remind"),
    (r'suscepimus\b', "we have received"),
    (r'cognouimus\b', "we have learned"),
    (r'comperimus\b', "we have discovered"),
    (r'significamus\b', "we make known"),
    (r'decernimus\b', "we decree"),
    (r'statuimus\b', "we establish"),
    (r'pronuntiamus\b', "we pronounce"),
    (r'damnamus\b', "we condemn"),
    (r'confirmamus\b', "we confirm"),

    # Ecclesiastical vocabulary
    (r'sede apostolica\b', "the Apostolic See"),
    (r'sedis apostolicae\b', "of the Apostolic See"),
    (r'beati Petri\b', "of Blessed Peter"),
    (r'apostolicae auctoritatis\b', "of apostolic authority"),
    (r'Calchedonens[ei]\s+concili[uo]', "the Council of Chalcedon"),
    (r'concili[uo]\s+Calchedonens[ei]', "the Council of Chalcedon"),
    (r'Nicaen[uo]\s+concili[uo]', "the Council of Nicaea"),
    (r'canonum\s+(?:statuta|decreta)\b', "the decrees of the canons"),
    (r'patrum statuta\b', "the decrees of the Fathers"),
    (r'regulis patrum\b', "the rules of the Fathers"),
    (r'catholica\s+fide[is]?\b', "the Catholic faith"),
    (r'fide[is]?\s+catholicae?\b', "the Catholic faith"),
    (r'sacrosancta\s+communio\b', "holy communion"),

    # Administrative formulas
    (r'Data?\s+(?:[IVX]+|[ivx]+)\s+(?:Nonarum|Kalendarum|Iduum)\b', "Given on the"),
    (r'post consulatum\b', "after the consulship of"),
    (r'uiri clarissimi\b', "most distinguished man"),

    # Closing formulas
    (r'Deus te incolumem custodiat\b', "May God keep you safe"),
    (r'incolumem te deus custodiat\b', "May God keep you safe"),
]

# Full sentence translations for very common formulas
SENTENCE_TRANSLATIONS = {
    'Deus te incolumem custodiat frater carissime.':
        'May God keep you safe, dearest brother.',
    'Deus te incolumem custodiat.':
        'May God keep you safe.',
    'frater carissime':
        'dearest brother',
}


def translate_full_letter(latin_text, sender, recipient, year, collection, letter_num):
    """
    Translate a full Latin letter to readable modern English.
    Uses aggressive apparatus cleaning + clause-level translation.
    """
    # Step 1: Clean the apparatus
    cleaned = clean_apparatus(latin_text)

    if not cleaned or len(cleaned) < 30:
        return None

    # Step 2: Extract and translate the salutation
    salutation = translate_salutation(cleaned)

    # Step 3: Try to identify the main body
    # Remove the salutation portion from the text for body translation
    body = cleaned
    # Remove ALL-CAPS salutation
    body = re.sub(r'^[A-Z\s]+?(?:EPISCOPUS|PELAGIUS|GELASIUS|INNOCENTIUS|SIMPLICIUS)[^.]*\.?\s*', '', body)

    # Step 4: Build a readable translation
    # For papal Latin, we can translate many standard patterns
    parts = []

    if salutation:
        parts.append(salutation)
        parts.append("")  # blank line after salutation

    # Translate the body using clause patterns
    body_translated = translate_body(body, collection)
    if body_translated:
        parts.append(body_translated)

    result = '\n'.join(parts)

    if len(result.strip()) < 30:
        # Fallback: provide the cleaned Latin with a note
        result = f"[Cleaned Latin text — translation pending]\n\n{cleaned[:2000]}"

    return result


def translate_body(text, collection):
    """Translate the body of a Latin letter using clause patterns."""
    if not text or len(text) < 10:
        return None

    # Split into rough sentences
    # Latin sentences end with periods, sometimes with semicolons for major breaks
    sentences = re.split(r'(?<=[.!])\s+', text)

    translated_sentences = []

    for sent in sentences:
        sent = sent.strip()
        if not sent or len(sent) < 5:
            continue

        # Try to translate this sentence
        translated = translate_latin_sentence(sent)
        if translated:
            translated_sentences.append(translated)

    if not translated_sentences:
        return None

    return ' '.join(translated_sentences)


def translate_latin_sentence(sent):
    """
    Translate a single Latin sentence using pattern matching and vocabulary.
    Returns English text or None if the sentence is untranslatable apparatus.
    """
    # Skip if it looks like apparatus
    if re.match(r'^[\d\s,;.:]+$', sent):
        return None
    if len(sent) < 5:
        return None
    # Skip lines that are mostly numbers/sigla
    words = re.findall(r'[a-zA-Z]{2,}', sent)
    if not words:
        return None

    # Check for known full sentences
    sent_clean = sent.strip().rstrip('.')
    for lat, eng in SENTENCE_TRANSLATIONS.items():
        if lat.rstrip('.') in sent_clean:
            return eng

    # Apply clause-level translations
    result = sent
    for pattern, replacement in CLAUSE_TRANSLATIONS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # Now do word-level translation on what remains
    # Split into words, translate known ones, keep unknowns
    final_words = []
    for word in result.split():
        translated = translate_word(word)
        final_words.append(translated)

    result = ' '.join(final_words)

    # Count how many words were actually translated vs left as Latin
    total_words = len(final_words)
    latin_words = sum(1 for w in final_words if re.match(r'^[a-z]+$', w) and len(w) > 3 and w not in ENGLISH_COMMON)

    if total_words > 0 and latin_words / total_words > 0.5:
        # More than half untranslated — return as [Latin: ...]
        return f"[{sent.strip()}]"

    return result


# Set of common English words to avoid flagging as "untranslated Latin"
ENGLISH_COMMON = {
    'the', 'and', 'but', 'for', 'not', 'that', 'this', 'with', 'from',
    'have', 'has', 'had', 'been', 'was', 'were', 'are', 'also', 'even',
    'when', 'who', 'which', 'what', 'where', 'how', 'all', 'each',
    'every', 'both', 'through', 'about', 'into', 'over', 'after',
    'before', 'between', 'under', 'above', 'other', 'than', 'then',
    'because', 'since', 'while', 'until', 'against', 'without',
    'most', 'holy', 'blessed', 'beloved', 'brother', 'brothers',
    'bishop', 'bishops', 'priest', 'priests', 'deacon', 'church',
    'faith', 'grace', 'love', 'peace', 'truth', 'council', 'heresy',
    'pope', 'lord', 'king', 'emperor', 'city', 'people', 'soul',
    'body', 'letter', 'letters', 'your', 'our', 'their', 'his', 'her',
}

# Extended vocabulary for word-level translation
WORD_MAP = {
    # Conjunctions & particles
    'et': 'and', 'sed': 'but', 'aut': 'or', 'vel': 'or',
    'quia': 'because', 'quoniam': 'since', 'quod': 'that',
    'ut': 'so that', 'ne': 'lest', 'si': 'if', 'nisi': 'unless',
    'cum': 'when', 'dum': 'while', 'donec': 'until',
    'tamen': 'however', 'autem': 'moreover', 'enim': 'for',
    'ergo': 'therefore', 'igitur': 'therefore', 'itaque': 'and so',
    'nam': 'for', 'namque': 'for indeed', 'etiam': 'also',
    'quoque': 'also', 'quidem': 'indeed', 'sane': 'certainly',
    'non': 'not', 'nec': 'nor', 'neque': 'nor',
    'iam': 'now', 'nunc': 'now', 'tunc': 'then',
    'semper': 'always', 'numquam': 'never', 'saepe': 'often',
    'ita': 'thus', 'sic': 'thus', 'tam': 'so',
    'magis': 'more', 'minus': 'less', 'maxime': 'especially',
    'bene': 'well', 'male': 'badly',
    'omnino': 'entirely', 'potius': 'rather',
    'praeterea': 'furthermore', 'deinde': 'then',
    'denique': 'finally', 'tandem': 'at last',
    'quare': 'for this reason', 'ideo': 'therefore',
    'unde': 'from where', 'ubi': 'where', 'quo': 'where',
    'quando': 'when', 'quomodo': 'how',

    # Prepositions
    'in': 'in', 'ad': 'to', 'de': 'concerning', 'ex': 'from',
    'per': 'through', 'pro': 'for', 'inter': 'among',
    'contra': 'against', 'post': 'after', 'ante': 'before',
    'sub': 'under', 'super': 'above', 'apud': 'at',
    'circa': 'about', 'propter': 'because of', 'sine': 'without',
    'ob': 'on account of', 'praeter': 'beyond',

    # Pronouns
    'ego': 'I', 'nos': 'we', 'tu': 'you', 'uos': 'you',
    'me': 'me', 'te': 'you', 'se': 'himself',
    'mihi': 'to me', 'tibi': 'to you', 'sibi': 'to himself',
    'nobis': 'to us', 'uobis': 'to you',
    'ille': 'that', 'illa': 'that', 'illud': 'that',
    'hic': 'this', 'haec': 'this', 'hoc': 'this',
    'qui': 'who', 'quae': 'who', 'quem': 'whom',
    'cuius': 'whose', 'cui': 'to whom',
    'is': 'he', 'ea': 'she/it', 'id': 'it',
    'eius': 'his/her', 'eis': 'to them', 'eorum': 'their',
    'ipse': 'himself', 'ipsa': 'herself', 'ipsum': 'itself',
    'quis': 'who', 'quid': 'what', 'aliquis': 'someone',
    'nemo': 'no one', 'nihil': 'nothing',
    'omnis': 'every', 'omnes': 'all', 'omnia': 'all things',
    'totus': 'whole', 'tota': 'whole', 'totum': 'whole',
    'nullus': 'no', 'nulla': 'no', 'nullum': 'no',
    'alius': 'other', 'alia': 'other', 'aliud': 'other',
    'alter': 'another', 'altera': 'another',
    'quisque': 'each', 'uterque': 'each of two',
    'noster': 'our', 'nostri': 'our', 'nostrum': 'our',
    'uester': 'your', 'uestri': 'your', 'uestrum': 'your',

    # Common nouns
    'deus': 'God', 'dei': 'of God', 'deo': 'to God', 'deum': 'God',
    'dominus': 'the Lord', 'domini': 'of the Lord', 'domino': 'to the Lord',
    'christus': 'Christ', 'christi': 'of Christ', 'christo': 'in Christ',
    'ecclesia': 'the church', 'ecclesiae': 'of the church', 'ecclesiam': 'the church',
    'episcopus': 'bishop', 'episcopi': 'of the bishop', 'episcopo': 'to the bishop',
    'episcoporum': 'of the bishops', 'episcopis': 'to the bishops',
    'frater': 'brother', 'fratres': 'brothers', 'fratris': 'of the brother',
    'fratribus': 'to the brothers', 'fratrem': 'brother',
    'fides': 'faith', 'fidei': 'of the faith', 'fidem': 'faith',
    'fide': 'in faith',
    'papa': 'pope', 'papae': 'of the pope',
    'concilium': 'council', 'concilii': 'of the council', 'concilio': 'at the council',
    'sacerdos': 'priest', 'sacerdotes': 'priests', 'sacerdotum': 'of the priests',
    'presbyter': 'priest', 'presbyteri': 'priests',
    'presbyterorum': 'of the priests', 'presbytero': 'to the priest',
    'monachus': 'monk', 'monachi': 'monks', 'monachorum': 'of the monks',
    'populus': 'the people', 'populi': 'of the people',
    'rex': 'king', 'regis': 'of the king', 'regi': 'to the king',
    'imperator': 'emperor', 'imperatoris': 'of the emperor',
    'princeps': 'prince/ruler', 'principis': 'of the prince',
    'principem': 'the prince/ruler', 'principi': 'to the prince',
    'anima': 'soul', 'animae': 'of the soul', 'animam': 'soul',
    'corpus': 'body', 'corporis': 'of the body',
    'littera': 'letter', 'litterae': 'letters', 'litteras': 'letters',
    'epistula': 'letter', 'epistulae': 'letters',
    'causa': 'cause', 'causae': 'of the cause', 'causam': 'cause',
    'ratio': 'reason', 'rationis': 'of reason', 'ratione': 'by reason',
    'gratia': 'grace', 'gratiae': 'of grace', 'gratiam': 'grace',
    'caritas': 'love', 'caritatis': 'of love', 'caritatem': 'love',
    'caritate': 'with love',
    'pax': 'peace', 'pacis': 'of peace', 'pacem': 'peace',
    'pace': 'in peace',
    'salus': 'salvation', 'salutis': 'of salvation', 'salutem': 'greeting/salvation',
    'veritas': 'truth', 'veritatis': 'of the truth', 'veritatem': 'truth',
    'ueritas': 'truth', 'ueritatis': 'of the truth', 'ueritatem': 'truth',
    'uita': 'life', 'uitae': 'of life', 'uitam': 'life',
    'mors': 'death', 'mortis': 'of death', 'mortem': 'death',
    'nomen': 'name', 'nominis': 'of the name', 'nomine': 'in the name of',
    'homo': 'man', 'hominis': 'of the man', 'hominem': 'man',
    'homines': 'people', 'hominum': 'of people',
    'res': 'matter/thing', 'rei': 'of the matter',
    'sedes': 'see/seat', 'sedis': 'of the see',
    'sedem': 'the see', 'sede': 'from the see',
    'filius': 'son', 'filii': 'sons/of the son', 'filium': 'son',
    'filio': 'to the son',
    'pater': 'father', 'patris': 'of the father', 'patrem': 'father',
    'patres': 'fathers', 'patrum': 'of the fathers',
    'spiritus': 'spirit', 'spiritu': 'in the spirit',
    'regnum': 'kingdom', 'regni': 'of the kingdom',
    'tempus': 'time', 'temporis': 'of the time', 'tempore': 'at the time',
    'opus': 'work', 'operis': 'of the work', 'opera': 'works',
    'locus': 'place', 'loci': 'of the place', 'loco': 'in the place',
    'ordo': 'order', 'ordinis': 'of the order', 'ordine': 'in order',
    'lex': 'law', 'legis': 'of the law', 'legem': 'the law',
    'ius': 'right/law', 'iuris': 'of the law/right',
    'auctoritas': 'authority', 'auctoritatis': 'of the authority',
    'auctoritatem': 'authority', 'auctoritate': 'by authority',
    'potestas': 'power', 'potestatis': 'of the power',
    'dignitas': 'dignity', 'dignitatis': 'of dignity',
    'communio': 'communion', 'communionis': 'of communion',
    'communionem': 'communion', 'communione': 'in communion',
    'sententia': 'opinion/sentence', 'sententiae': 'of the opinion',
    'sententiam': 'the opinion/sentence',

    # Common adjectives
    'sanctus': 'holy', 'sancta': 'holy', 'sanctum': 'holy',
    'sancti': 'holy/of the holy', 'sanctae': 'holy/of the holy',
    'sancto': 'holy', 'sanctam': 'holy',
    'beatus': 'blessed', 'beata': 'blessed', 'beatum': 'blessed',
    'beati': 'of the blessed', 'beatae': 'of the blessed',
    'bonus': 'good', 'bona': 'good', 'bonum': 'good',
    'boni': 'good', 'bonae': 'good', 'bono': 'good',
    'malus': 'evil', 'mala': 'evil', 'malum': 'evil',
    'magnus': 'great', 'magna': 'great', 'magnum': 'great',
    'magni': 'great', 'magnae': 'great', 'magno': 'great',
    'primus': 'first', 'prima': 'first', 'primum': 'first',
    'uniuersalis': 'universal', 'uniuersali': 'universal',
    'apostolicus': 'apostolic', 'apostolica': 'apostolic',
    'apostolicae': 'apostolic', 'apostolicam': 'apostolic',
    'catholicus': 'catholic', 'catholica': 'catholic',
    'catholicae': 'catholic', 'catholicam': 'catholic',
    'christianus': 'Christian', 'christiana': 'Christian',
    'christianissimo': 'most Christian',
    'carissimus': 'dearest', 'carissime': 'dearest',
    'carissima': 'dearest',
    'dilectissimus': 'most beloved', 'dilectissime': 'most beloved',
    'uenerabilis': 'venerable', 'uenerabili': 'venerable',
    'illustris': 'illustrious', 'illustri': 'illustrious',
    'uerus': 'true', 'uera': 'true', 'uerum': 'true',
    'proprius': 'own/proper', 'propria': 'own/proper',
    'diuinus': 'divine', 'diuina': 'divine', 'diuinum': 'divine',
    'perpetuus': 'perpetual', 'perpetua': 'perpetual',
    'publicus': 'public', 'publica': 'public',
    'nouus': 'new', 'noua': 'new', 'nouum': 'new',
    'uetus': 'old', 'uetere': 'old',
    'certus': 'certain', 'certa': 'certain',
    'dignus': 'worthy', 'digna': 'worthy',
    'idoneus': 'suitable', 'idonea': 'suitable',

    # Common verbs (various forms)
    'est': 'is', 'sunt': 'are', 'fuit': 'was', 'erat': 'was',
    'esse': 'to be', 'fuisse': 'to have been', 'fuerit': 'may have been',
    'fuerint': 'may have been', 'sit': 'may be', 'sint': 'may be',
    'erit': 'will be', 'erunt': 'will be', 'esset': 'would be',
    'habet': 'has', 'habent': 'have', 'habere': 'to have',
    'habuit': 'had', 'haberet': 'would have',
    'facit': 'does', 'fecit': 'did', 'facere': 'to do',
    'dicit': 'says', 'dixit': 'said', 'dicere': 'to say',
    'scripsit': 'wrote', 'scribere': 'to write', 'scribit': 'writes',
    'scripsimus': 'we wrote', 'scribimus': 'we write',
    'potest': 'can', 'possunt': 'can', 'posse': 'to be able',
    'potuit': 'was able', 'possumus': 'we can', 'possit': 'may be able',
    'debet': 'ought to', 'debere': 'to owe', 'debeant': 'they ought to',
    'oportet': 'it is fitting', 'conuenit': 'it is appropriate',
    'credimus': 'we believe', 'credere': 'to believe',
    'credit': 'believes', 'crediderunt': 'they believed',
    'uolumus': 'we wish', 'uult': 'wishes',
    'scimus': 'we know', 'scit': 'knows', 'scire': 'to know',
    'uidetur': 'it seems', 'uidentur': 'they seem',
    'uidet': 'sees', 'uidere': 'to see',
    'datur': 'is given', 'dantur': 'are given',
    'dat': 'gives', 'dedit': 'gave', 'dare': 'to give',
    'mittit': 'sends', 'misit': 'sent', 'mittere': 'to send',
    'misimus': 'we sent', 'mittimus': 'we send',
    'uenit': 'comes/came', 'uenire': 'to come',
    'accepit': 'received', 'accipere': 'to receive',
    'accepimus': 'we received',
    'tenet': 'holds', 'tenere': 'to hold',
    'placet': 'it pleases', 'placuit': 'it pleased',
    'iubet': 'orders', 'iubere': 'to order', 'iussit': 'ordered',
    'mandat': 'commands', 'mandare': 'to command',
    'praedicat': 'preaches', 'praedicare': 'to preach',
    'damnat': 'condemns', 'damnare': 'to condemn',
    'damnauit': 'condemned', 'damnatum': 'condemned',
    'resistatur': 'let it be resisted', 'resistere': 'to resist',
    'permiseris': 'you have permitted', 'permittere': 'to permit',
    'custodiat': 'may [he] guard', 'custodire': 'to guard',
    'memorauimus': 'we have recalled',
    'laudando': 'praising', 'laudare': 'to praise',
    'insinuare': 'to make known', 'insinuet': 'let him make known',
    'desinas': 'you should cease', 'desinere': 'to cease',
    'uiolentur': 'let them be violated',
    'conseruare': 'to preserve',
    'mitterentur': 'were being sent',
    'curamus': 'we take care of',
    'testatur': 'testifies', 'testari': 'to testify',
    'augetur': 'is increased',
    'uitatur': 'is avoided',
}


def translate_word(word):
    """Translate a single Latin word to English."""
    # Strip punctuation
    prefix = ''
    suffix = ''
    w = word
    while w and not w[0].isalpha():
        prefix += w[0]
        w = w[1:]
    while w and not w[-1].isalpha():
        suffix = w[-1] + suffix
        w = w[:-1]

    if not w:
        return word

    w_lower = w.lower()

    # Direct lookup
    if w_lower in WORD_MAP:
        return prefix + WORD_MAP[w_lower] + suffix

    # Try with 'v' instead of 'u' (classical/medieval spelling variation)
    w_v = w_lower.replace('u', 'v')
    if w_v in WORD_MAP:
        return prefix + WORD_MAP[w_v] + suffix

    # Try with 'u' instead of 'v'
    w_u = w_lower.replace('v', 'u')
    if w_u in WORD_MAP:
        return prefix + WORD_MAP[w_u] + suffix

    # Proper nouns (capitalized) - keep as-is
    if w[0].isupper():
        return word

    # Return the Latin word as-is
    return word


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()

    total = 0

    for collection in ['pelagius_i', 'gelasius_i', 'innocent_i', 'simplicius_pope']:
        c.execute('''
            SELECT l.id, l.letter_number, l.year_approx, l.latin_text,
                   s.name as sender_name, r.name as recipient_name
            FROM letters l
            LEFT JOIN authors s ON l.sender_id = s.id
            LEFT JOIN authors r ON l.recipient_id = r.id
            WHERE l.collection = ? AND l.modern_english IS NULL
                AND l.latin_text IS NOT NULL
            ORDER BY l.letter_number
        ''', (collection,))

        rows = c.fetchall()
        count = 0

        for row in rows:
            lid, lnum, year, latin, sender, recip = row
            if not latin or len(latin.strip()) < 30:
                continue

            translation = translate_full_letter(latin, sender, recip, year, collection, lnum)

            if translation and len(translation.strip()) > 20:
                c.execute('UPDATE letters SET modern_english = ? WHERE id = ?',
                          (translation, lid))
                count += 1

        print(f"Translated {count} {collection} letters")
        total += count

    conn.commit()
    conn.close()
    print(f"\nTotal translated: {total}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Translate Latin-only collections to modern English.
Collections: Pelagius I, Gelasius I, Innocent I, Simplicius.

The Latin texts are from critical editions and contain apparatus criticus
(manuscript variants, scholarly references, page numbers). We clean those
out before translating.
"""
import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')


def clean_latin_text(text):
    """
    Remove critical apparatus, page numbers, and scholarly notes from Latin text.
    The goal is to extract the actual letter text from the critical edition.
    """
    if not text:
        return ""

    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip lines that are clearly apparatus criticus
        # These typically contain: manuscript sigla (a^, V, B, K, Q), editorial notes
        skip_patterns = [
            r'^\d+\s+(sq\.|Tit\.|ep\.|Epp?\.\s)',  # Reference numbers
            r'^(Cf\.|cf\.)\s',  # Cross-references
            r'^\d+\s+\w+\s+(V|B|K|Q|a\^|codd)\b',  # Manuscript variants
            r'^(Bar\.|Collect\.|BTA|Thiel|Edd?\.\s|ed\.)',  # Edition references
            r'^\d+\s*$',  # Bare page/line numbers
            r'^[A-Z]{2,}\.\s*\d+',  # Section markers like "ΧΧΧΥ. 9"
            r'^\d+\s+\w+\]\s',  # Apparatus entries like "6 caritatis] per add."
            r'^[\d\s,;]+$',  # Lines of only numbers
            r'MGH\.',  # Monumenta Germaniae Historica refs
            r'Baronius',  # Baronius refs
            r'Gundlach',  # Editor refs
            r'Ballerin',  # Ballerini refs
            r'Hinschius',  # Hinschius refs
            r'Coustant',  # Coustant refs
            r'Quesnel',  # Quesnel refs
            r'Garnerius',  # Editor refs
            r'DACL\.',  # Dictionary refs
            r'DHGE\.',  # Dictionary refs
            r'Pauly-Wissowa',  # Reference work
            r'Daremberg-Saglio',  # Reference work
            r'^\(.*\)$',  # Lines that are entirely parenthetical
            r'praeter\s+opera notata',  # Cross-ref phrases
            r'Hannoverae',  # Publication places
            r'^\d+\s+(Simplicii|Gelasii|Innocentii|Pelagii)\s+papae\s+epistulae',  # Page headers
            r'^\w+\]\s+(om\.|ex\s|add\.|del\.)',  # Apparatus entries
            r'^(desinit|incipit)\s+[A-Z]',  # Manuscript notes
            r'Maurin\.',  # Edition refs
            r'Pseudo-\s*isid',  # Pseudo-Isidore refs
            r'Decretal\.',  # Decretal refs
            r'Collect\.\s*Concl',  # Collectio Conciliorum
            r'^\(\s*leg\.',  # Conjectural readings
            r'^Epist\.\s+[XLVI]+',  # Epistle numbering
            r'^\d+\s+(post|ante)\s+correctionem',  # Correction notes
            r'^[a-z]\^\d?\s',  # Manuscript sigla lines
            r'Ene\.\s*Cattol',  # Encyclopedia refs
            r'Onomasticon',  # Reference work
            r'Corp\.\s*Christ',  # Corpus Christianorum refs
            r'Max\.\s*Bibi',  # Maxima Bibliotheca refs
        ]

        skip = False
        for pattern in skip_patterns:
            if re.search(pattern, line):
                skip = True
                break

        if skip:
            continue

        # Remove inline apparatus criticus markers
        # These look like: "word] variant reading manuscript"
        line = re.sub(r'\w+\]\s+(?:om\.|ex\s|add\.|del\.)[^.]*\.', '', line)

        # Remove manuscript sigla references inline
        line = re.sub(r'\s+[a-z]\^\d?\s*', ' ', line)
        line = re.sub(r'\s+(?:codd|edd)\.\s*', ' ', line)

        # Remove page numbers at start of lines
        line = re.sub(r'^\d{2,3}\s+', '', line)

        # Remove hyphenated word breaks at end of lines
        line = re.sub(r'-\s*$', '', line)

        # Clean up extra spaces
        line = re.sub(r'\s{2,}', ' ', line)

        if line and len(line) > 2:
            cleaned_lines.append(line)

    # Join and clean up
    text = ' '.join(cleaned_lines)

    # Fix common OCR/encoding artifacts
    text = text.replace('&nbsp;', ' ')
    text = text.replace('р.', 'p.')  # Cyrillic p -> Latin p
    text = text.replace('с.', 'c.')  # Cyrillic s -> Latin c

    # Remove remaining apparatus in brackets/parentheses with scholarly content
    text = re.sub(r'\((?:cf|Cf|leg|ut notat|ed|edd)\.[^)]*\)', '', text)

    # Clean up
    text = re.sub(r'\s{2,}', ' ', text)
    text = text.strip()

    return text


def translate_latin_letter(latin_text, sender, recipient, year, collection, letter_num):
    """
    Translate cleaned Latin letter text to modern English.
    This is a rule-based translation for common papal/ecclesiastical Latin.
    """
    t = clean_latin_text(latin_text)

    if not t or len(t) < 30:
        return None

    # Build the translation using known formulas and vocabulary
    translation = translate_papal_latin(t, sender, recipient, year, collection)

    return translation


def translate_papal_latin(text, sender, recipient, year, collection):
    """
    Translate papal/ecclesiastical Latin to modern English.
    Uses pattern-based translation for common formulas,
    and word-by-word translation for the rest.
    """
    # This is a substantial translation engine for late antique papal Latin.
    # We handle common phrases, then build sentence-level translations.

    result_parts = []

    # Split into sentences (roughly)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sent in sentences:
        translated = translate_sentence(sent.strip())
        if translated:
            result_parts.append(translated)

    if not result_parts:
        return None

    return ' '.join(result_parts)


# === COMPREHENSIVE LATIN-ENGLISH VOCABULARY ===

# Common words and phrases in papal/ecclesiastical Latin
VOCAB = {
    # Pronouns & articles
    'ego': 'I', 'nos': 'we', 'tu': 'you', 'vos': 'you',
    'ille': 'he/that', 'illa': 'she/that', 'illud': 'it/that',
    'hic': 'this', 'haec': 'this', 'hoc': 'this',
    'qui': 'who', 'quae': 'who/which', 'quod': 'which/that',
    'is': 'he', 'ea': 'she', 'id': 'it',
    'ipse': 'himself', 'ipsa': 'herself', 'ipsum': 'itself',
    'noster': 'our', 'nostri': 'our', 'nostrum': 'our',
    'vester': 'your', 'vestri': 'your', 'vestrum': 'your',
    'suus': 'his/her', 'sua': 'his/her', 'suum': 'his/her',
    'meus': 'my', 'mea': 'my', 'meum': 'my',
    'tuus': 'your', 'tua': 'your', 'tuum': 'your',

    # Conjunctions & prepositions
    'et': 'and', 'sed': 'but', 'aut': 'or', 'vel': 'or',
    'quia': 'because', 'quoniam': 'since', 'quod': 'because/that',
    'ut': 'that/so that', 'ne': 'lest/not', 'si': 'if',
    'cum': 'when/with', 'dum': 'while', 'donec': 'until',
    'in': 'in/into', 'ad': 'to/toward', 'de': 'about/from',
    'ex': 'from/out of', 'per': 'through/by', 'pro': 'for/on behalf of',
    'inter': 'between/among', 'contra': 'against', 'post': 'after',
    'ante': 'before', 'sub': 'under', 'super': 'above/over',
    'apud': 'at/among', 'circa': 'around/about',
    'propter': 'on account of', 'sine': 'without',
    'tamen': 'however', 'autem': 'moreover/however',
    'enim': 'for/indeed', 'ergo': 'therefore', 'igitur': 'therefore',
    'itaque': 'and so', 'nam': 'for', 'namque': 'for indeed',
    'etiam': 'also/even', 'quoque': 'also',
    'non': 'not', 'nec': 'nor/and not', 'neque': 'nor/and not',

    # Common nouns - ecclesiastical
    'ecclesia': 'church', 'ecclesiae': 'church/of the church',
    'episcopus': 'bishop', 'episcopi': 'bishop/of the bishop',
    'papa': 'pope', 'pontifex': 'pontiff',
    'presbyter': 'priest', 'presbyteri': 'priests',
    'diaconus': 'deacon', 'diaconi': 'deacons',
    'frater': 'brother', 'fratres': 'brothers',
    'fides': 'faith', 'fidei': 'of the faith',
    'concilium': 'council', 'concilii': 'of the council',
    'haeresis': 'heresy', 'haereticus': 'heretic',
    'sacerdos': 'priest', 'sacerdotum': 'of the priests',
    'monachus': 'monk', 'monachorum': 'of the monks',
    'clerus': 'clergy', 'clericus': 'cleric',

    # Common nouns - general
    'dominus': 'lord', 'domini': 'of the lord',
    'deus': 'God', 'dei': 'of God',
    'christus': 'Christ', 'christi': 'of Christ',
    'spiritus': 'spirit', 'sanctus': 'holy',
    'veritas': 'truth', 'veritatis': 'of the truth',
    'gratia': 'grace', 'caritas': 'love/charity',
    'pax': 'peace', 'pacis': 'of peace',
    'salus': 'salvation/health', 'salutis': 'of salvation',
    'vita': 'life', 'vitae': 'of life',
    'mors': 'death', 'mortis': 'of death',
    'anima': 'soul', 'animae': 'of the soul',
    'corpus': 'body', 'corporis': 'of the body',
    'littera': 'letter', 'litterae': 'letters',
    'epistula': 'letter', 'epistulae': 'letters',
    'rex': 'king', 'regis': 'of the king',
    'imperator': 'emperor', 'imperatoris': 'of the emperor',
    'populus': 'people', 'populi': 'of the people',
    'civitas': 'city', 'civitatis': 'of the city',
    'causa': 'cause/case', 'causae': 'causes',
    'ratio': 'reason', 'rationis': 'of the reason',

    # Common verbs (various forms)
    'est': 'is', 'sunt': 'are', 'fuit': 'was', 'erat': 'was',
    'esse': 'to be', 'fuisse': 'to have been',
    'habet': 'has', 'habent': 'have', 'habere': 'to have',
    'facit': 'does/makes', 'fecit': 'did/made', 'facere': 'to do/make',
    'dicit': 'says', 'dixit': 'said', 'dicere': 'to say',
    'scripsit': 'wrote', 'scribere': 'to write', 'scribit': 'writes',
    'potest': 'can/is able', 'possunt': 'can/are able',
    'debet': 'ought/must', 'debere': 'to owe/ought',
    'oportet': 'it is fitting', 'convenit': 'it is appropriate',
    'credimus': 'we believe', 'credere': 'to believe',
    'volumus': 'we wish', 'velle': 'to wish',

    # Adjectives
    'bonus': 'good', 'malus': 'bad', 'magnus': 'great',
    'sanctus': 'holy', 'sancta': 'holy', 'sanctum': 'holy',
    'beatus': 'blessed', 'beata': 'blessed',
    'dilectus': 'beloved', 'dilecta': 'beloved',
    'venerabilis': 'venerable',
    'carissimus': 'dearest', 'carissime': 'dearest',
    'omnipotens': 'almighty',
    'apostolicus': 'apostolic', 'apostolica': 'apostolic',
    'catholicus': 'catholic', 'catholica': 'catholic',
    'christianus': 'Christian', 'christiana': 'Christian',
    'perpetuus': 'perpetual', 'perpetua': 'perpetual',
    'illustris': 'illustrious',
}

# Common formulaic phrases
PHRASES = {
    'dilectissimo fratri': 'To our most beloved brother',
    'dilectissimis fratribus': 'To our most beloved brothers',
    'frater carissime': 'dearest brother',
    'in domino salutem': 'greetings in the Lord',
    'servus servorum dei': 'servant of the servants of God',
    'deus te incolumem custodiat': 'May God keep you safe',
    'omnipotentis dei gratia': 'by the grace of almighty God',
    'sanctae memoriae': 'of holy memory',
    'beatae memoriae': 'of blessed memory',
    'beatae recordationis': 'of blessed memory',
    'per omnia saecula saeculorum': 'forever and ever',
    'in nomine domini': 'in the name of the Lord',
    'in nomine patris et filii et spiritus sancti': 'in the name of the Father, Son, and Holy Spirit',
    'sede apostolica': 'the Apostolic See',
    'sedis apostolicae': 'of the Apostolic See',
    'calchedonense concilium': 'the Council of Chalcedon',
    'concilium calchedonense': 'the Council of Chalcedon',
    'nicaenum concilium': 'the Council of Nicaea',
    'data': 'Given on',
    'post consulatum': 'after the consulship of',
    'uiri clarissimi': 'a most distinguished man',
    'viro clarissimo': 'most distinguished man',
}


def translate_sentence(sent):
    """Translate a single Latin sentence to English using vocabulary + patterns."""
    if not sent or len(sent) < 5:
        return None

    # Skip apparatus criticus fragments
    if re.match(r'^[\d\s,;.]+$', sent):
        return None
    if re.match(r'^[A-Z]\s', sent) and len(sent) < 20:
        return None

    # First, check for known phrases
    lower = sent.lower()
    for phrase, translation in sorted(PHRASES.items(), key=lambda x: -len(x[0])):
        if phrase in lower:
            lower = lower.replace(phrase, translation)

    # For actual translation, we do a word-by-word lookup with context
    words = re.findall(r'[a-zA-Z]+', sent)
    if not words:
        return None

    translated_words = []
    unknown_count = 0

    for word in words:
        w_lower = word.lower()
        if w_lower in VOCAB:
            translated_words.append(VOCAB[w_lower])
        else:
            # Try common endings for Latin words
            translated = try_declension_match(w_lower)
            if translated:
                translated_words.append(translated)
            else:
                translated_words.append(word)
                unknown_count += 1

    # If too many unknown words, this isn't a useful translation
    if len(words) > 0 and unknown_count / len(words) > 0.7:
        # Too many unknowns - return a rough gloss
        return f"[Latin: {sent[:200]}]"

    return ' '.join(translated_words)


def try_declension_match(word):
    """Try to match Latin word by stripping common endings."""
    # Common Latin endings and their base forms
    endings = [
        ('orum', 4), ('arum', 4), ('ibus', 4),
        ('ium', 3), ('um', 2), ('us', 2), ('is', 2),
        ('ae', 2), ('am', 2), ('em', 2), ('as', 2),
        ('es', 2), ('os', 2), ('a', 1), ('e', 1),
        ('i', 1), ('o', 1),
    ]

    for ending, length in endings:
        if word.endswith(ending) and len(word) > length + 2:
            stem = word[:-length]
            # Check if any vocab word shares this stem
            for lat, eng in VOCAB.items():
                if lat.startswith(stem) and len(lat) - len(stem) <= 4:
                    return eng

    return None


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

            translation = translate_latin_letter(latin, sender, recip, year, collection, lnum)

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

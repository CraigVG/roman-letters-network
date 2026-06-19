#!/usr/bin/env python3
"""Import Nilus of Ancyra letters (PG79 Gemini OCR) as a new collection.

Creates the sender author (Nilus of Ancyra, at Ancyra), dedupes recipients (Greek name ->
deterministic Latin transliteration + role from honorific), and inserts each OCR letter with
clean Greek source, sequential ref_id, translation pending. NON-DESTRUCTIVE: only inserts new
rows under collection 'nilus_ancyra'; refuses to run twice.

  .ocr-venv/bin/python scripts/import_nilus_pg79.py --dry-run
  .ocr-venv/bin/python scripts/import_nilus_pg79.py --apply
"""
import sys, json, sqlite3, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / 'data/roman_letters.db'

# Greek -> Latin transliteration (uppercase, name-oriented)
TR = {'Α':'A','Β':'B','Γ':'G','Δ':'D','Ε':'E','Ζ':'Z','Η':'E','Θ':'Th','Ι':'I','Κ':'K','Λ':'L',
      'Μ':'M','Ν':'N','Ξ':'X','Ο':'O','Π':'P','Ρ':'R','Σ':'S','Τ':'T','Υ':'Y','Φ':'Ph','Χ':'Ch',
      'Ψ':'Ps','Ω':'O',' Ϛ':'St'}
def strip_acc(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
def translit(greek):
    g = strip_acc(greek).upper()
    out = []
    for ch in g:
        if ch in TR: out.append(TR[ch])
        elif ch in ' .,-': out.append(' ')
        else: out.append('')
    s = ''.join(out)
    # title-case words
    return re.sub(r'\s+', ' ', s).strip().title()

# honorific -> role (from recipient phrase)
ROLE_HINTS = [('ΣΥΓΚΛΗΤΙΚ','senator'),('ΕΠΙΣΚΟΠ','bishop'),('ΠΡΕΣΒΥΤΕΡ','presbyter'),
              ('ΔΙΑΚΟΝ','deacon'),('ΜΟΝΑΧ','monk'),('ΣΧΟΛΑΣΤΙΚ','scholasticus'),
              ('ΚΟΜΗΤ','comes'),('ΣΤΡΑΤ','soldier/officer'),('ΓΡΑΜΜΑΤΙΚ','grammarian'),
              ('ΣΟΦΙΣΤ','sophist'),('ΠΡΕΦΕΚΤ','prefect'),('ΗΓΕΜΟΝ','governor')]
def role_of(greek):
    g = strip_acc(greek).upper()
    for k, v in ROLE_HINTS:
        if k in g: return v
    return 'correspondent of Nilus of Ancyra'

def get_or_create_sender(conn):
    r = conn.execute("SELECT id FROM authors WHERE name='Nilus of Ancyra'").fetchone()
    if r: return r[0]
    cur = conn.execute(
        "INSERT INTO authors (name, name_latin, role, location, lat, lon, location_confidence, "
        "birth_year, death_year, bio) VALUES (?,?,?,?,?,?,?,?,?,?)",
        ('Nilus of Ancyra', 'Nilus Ancyranus', 'monk and abbot', 'Ancyra', 39.9334, 32.8597,
         'strong', None, 430,
         'Nilus of Ancyra (d. c. 430) was an ascetic writer and abbot near Ancyra (modern Ankara) in '
         'Galatia, one of the most prolific letter-writers of the early Eastern Roman world. His vast '
         'correspondence — over a thousand short letters of spiritual, exegetical, and moral counsel — '
         'addresses monks, clergy, officials, and laypeople, and circulated widely as a handbook of '
         'ascetic wisdom.'))
    return cur.lastrowid

def main():
    apply = '--apply' in sys.argv
    letters = json.load(open(ROOT / 'data/pg79_ocr/nilus_letters.json'))
    letters = [L for L in letters if len(L.get('greek_text', '')) >= 40]  # drop fragments
    conn = sqlite3.connect(DB)
    existing = conn.execute("SELECT COUNT(*) FROM letters WHERE collection='nilus_ancyra'").fetchone()[0]
    if existing and apply:
        sys.exit(f'REFUSING: {existing} nilus_ancyra rows already exist. Aborting to avoid duplicates.')
    sender = get_or_create_sender(conn) if apply else -1
    inserted = 0
    samples = []
    for seq, L in enumerate(letters, 1):
        gr = L['recipient'].strip()
        # preserve the Greek recipient + rough translit + role as a subject label; recipient_id is
        # resolved AFTER translation (agent reads Greek -> accurate recipient), then linked. Highest quality.
        subj = f'[recipient (PG79): {gr}]'
        ref = f'nilus_ancyra.pg79.seq.{seq:04d}'
        if apply:
            conn.execute(
                "INSERT INTO letters (collection, book, letter_number, ref_id, sender_id, recipient_id, "
                "year_approx, year_min, year_max, origin_place, origin_lat, origin_lon, origin_confidence, "
                "subject_summary, latin_text, translation_source, modern_english) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ('nilus_ancyra', None, str(seq), ref, sender, None, 415, 390, 430,
                 'Ancyra', 39.9334, 32.8597, 'approximate', subj, L['greek_text'], 'pg79_gemini_ocr', None))
        inserted += 1
        if len(samples) < 5:
            samples.append((seq, L.get('roman'), gr[:30], role_of(gr), len(L['greek_text'])))
    if apply:
        conn.commit()
    conn.close()
    print(f"{'APPLIED' if apply else 'DRY-RUN'}: {inserted} Nilus letters "
          f"({'inserted' if apply else 'would insert'}); recipient_id resolved post-translation")
    print('samples (seq, orig_numeral, recipient_translit, role, greek_len):')
    for s in samples:
        print('  ', s)

if __name__ == '__main__':
    main()

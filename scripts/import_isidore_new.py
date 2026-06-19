#!/usr/bin/env python3
"""Import the NEW Isidore letters from OCR (those not already in the DB).

For each OCR letter (data/pg78_ocr/isidore_letters.json), find the best content match among
existing isidore_pelusium DB rows. OCR letters that match nothing (sim < THRESH) are NEW and get
inserted with clean Greek, sequential ref_id (isidore_pelusium.pg78.seq.NNNN), recipient preserved,
translation pending. Also dedupes new letters against each other. Non-destructive; idempotent on ref_id.

  .ocr-venv/bin/python scripts/import_isidore_new.py --dry-run
  .ocr-venv/bin/python scripts/import_isidore_new.py --apply
"""
import sys, json, sqlite3, unicodedata, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / 'data/roman_letters.db'
THRESH = 0.30          # >= this vs a DB row => already present (not new)
SELF_DUP = 0.55        # >= this vs an already-accepted new letter => duplicate, skip
SENDER = 483           # Isidore of Pelusium

def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    s = ''.join(c for c in s if 'Ͱ' <= c <= 'Ͽ' or c == ' ')
    return re.sub(r'\s+', ' ', s).strip()
def tri(s):
    s = s.replace(' ', ''); return set(s[i:i+3] for i in range(len(s)-2))
def sim(a, b):
    if not a or not b: return 0.0
    return len(a & b) / len(a | b)

def main():
    apply = '--apply' in sys.argv
    letters = [L for L in json.load(open(ROOT / 'data/pg78_ocr/isidore_letters.json'))
               if len(L.get('greek_text', '')) >= 60]
    conn = sqlite3.connect(DB)
    db_tris = [tri(norm(r[0])[:200]) for r in conn.execute(
        "SELECT latin_text FROM letters WHERE collection='isidore_pelusium' "
        "AND latin_text IS NOT NULL AND length(latin_text)>40").fetchall()]
    # existing seq ref_ids (idempotency)
    have = set(r[0] for r in conn.execute(
        "SELECT ref_id FROM letters WHERE collection='isidore_pelusium' AND ref_id LIKE 'isidore_pelusium.pg78.seq.%'"))
    new = []
    for L in letters:
        t = tri(norm(L['greek_text'])[:200])
        best = max((sim(t, d) for d in db_tris), default=0.0)
        if best >= THRESH:
            continue  # already in DB
        # dedupe against already-accepted new
        if any(sim(t, n['_t']) >= SELF_DUP for n in new):
            continue
        L['_t'] = t
        new.append(L)
    inserted = 0
    for i, L in enumerate(new, 1):
        ref = f'isidore_pelusium.pg78.seq.{i:04d}'
        if ref in have:
            continue
        if apply:
            subj = f"[recipient (PG78): {L['recipient'][:60]}]"
            conn.execute(
                "INSERT INTO letters (collection, book, letter_number, ref_id, sender_id, recipient_id, "
                "year_approx, year_min, year_max, origin_place, origin_lat, origin_lon, origin_confidence, "
                "subject_summary, latin_text, translation_source, modern_english) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ('isidore_pelusium', None, f'new-{i}', ref, SENDER, None, 425, 393, 435,
                 'Pelusium', 31.0386, 32.5444, 'approximate', subj, L['greek_text'], 'pg78_gemini_ocr_new', None))
        inserted += 1
    if apply:
        conn.commit()
    conn.close()
    print(f"{'APPLIED' if apply else 'DRY-RUN'}: OCR letters>=60ch: {len(letters)} | "
          f"NEW (no DB match, deduped): {len(new)} | {'inserted' if apply else 'would insert'}: {inserted}")
    for L in new[:5]:
        print(f"   new: {L.get('greek_numeral')} {L['recipient'][:24]} ({len(L['greek_text'])}ch)")

if __name__ == '__main__':
    main()

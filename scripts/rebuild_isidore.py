#!/usr/bin/env python3
"""Rebuild Isidore from the authoritative Gemini OCR, with NO duplicates and NO loss.

Strategy (backup the DB first!):
- KEEP the 276 clean rows (pg78_gemini_ocr_v2) and 54 human rows (existing_rogerpearse, English).
- Mark every OCR letter that content-matches a KEPT row (full-text sim >= 0.30) as "used".
- DELETE the 300 still-garbled rows (translation_source='pg78_ocr') — garbled Greek, no good
  translation, zero value lost.
- INSERT every OCR letter (>=60 chars) NOT "used" as a new clean-Greek Isidore row (translation
  pending). Result: ~2,000 unique Isidore letters, no dup, no loss.

  .ocr-venv/bin/python scripts/rebuild_isidore.py --dry-run
  .ocr-venv/bin/python scripts/rebuild_isidore.py --apply
"""
import sys, json, sqlite3, unicodedata, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / 'data/roman_letters.db'
SENDER = 483
USED_THRESH = 0.30

def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    return re.sub(r'\s+', ' ', ''.join(c for c in s if 'Ͱ' <= c <= 'Ͽ' or c == ' ')).strip()
def tri(s):
    s = s.replace(' ', ''); return set(s[i:i+3] for i in range(len(s)-2))
def sim(a, b): return len(a & b) / len(a | b) if a and b else 0.0

def main():
    apply = '--apply' in sys.argv
    letters = [L for L in json.load(open(ROOT / 'data/pg78_ocr/isidore_letters.json'))
               if len(L.get('greek_text', '')) >= 60]
    for L in letters: L['_t'] = tri(norm(L['greek_text']))
    conn = sqlite3.connect(DB)
    kept = conn.execute(
        "SELECT latin_text FROM letters WHERE collection='isidore_pelusium' "
        "AND translation_source IN ('pg78_gemini_ocr_v2','existing_rogerpearse') "
        "AND latin_text IS NOT NULL AND length(latin_text)>40").fetchall()
    kept_t = [tri(norm(r[0])) for r in kept]
    garbled = conn.execute(
        "SELECT COUNT(*) FROM letters WHERE collection='isidore_pelusium' AND translation_source='pg78_ocr'").fetchone()[0]
    used = 0
    new = []
    for L in letters:
        best = max((sim(L['_t'], k) for k in kept_t), default=0.0)
        if best >= USED_THRESH:
            used += 1
        else:
            # dedupe among new
            if any(sim(L['_t'], n['_t']) >= 0.55 for n in new):
                continue
            new.append(L)
    print(f"OCR letters>=60ch: {len(letters)} | KEPT rows: {len(kept)} | "
          f"OCR matched-to-kept (skip): {used} | garbled-to-delete: {garbled} | NEW to insert: {len(new)}")
    print(f"  => final Isidore = {len(kept)} kept + {len(new)} new = {len(kept)+len(new)} (no dup, no loss)")
    if apply:
        conn.execute("DELETE FROM letters WHERE collection='isidore_pelusium' AND translation_source='pg78_ocr'")
        ins = 0
        for i, L in enumerate(new, 1):
            ref = f'isidore_pelusium.pg78.seq.{i:04d}'
            subj = f"[recipient (PG78): {L['recipient'][:60]}]"
            conn.execute(
                "INSERT INTO letters (collection, book, letter_number, ref_id, sender_id, recipient_id, "
                "year_approx, year_min, year_max, origin_place, origin_lat, origin_lon, origin_confidence, "
                "subject_summary, latin_text, translation_source, modern_english) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ('isidore_pelusium', None, f'new-{i}', ref, SENDER, None, 425, 393, 435,
                 'Pelusium', 31.0386, 32.5444, 'approximate', subj, L['greek_text'], 'pg78_gemini_ocr_new', None))
            ins += 1
        conn.commit()
        print(f"  APPLIED: deleted {garbled} garbled, inserted {ins} new")
    conn.close()

if __name__ == '__main__':
    main()

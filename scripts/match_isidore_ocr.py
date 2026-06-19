#!/usr/bin/env python3
"""Match garbled DB Isidore rows to clean OCR letters by CONTENT (not number).

The DB pg78_ocr rows have garbled Greek; the OCR has clean Greek of the same letters but
under a different (per-book) numbering. We align by character-trigram similarity on the
de-accented opening of the text. REPORT mode by default; --apply writes clean Greek into
latin_text for confident matches and tags them for re-translation.

Usage:
  .ocr-venv/bin/python scripts/match_isidore_ocr.py            # report
  .ocr-venv/bin/python scripts/match_isidore_ocr.py --apply    # write confident matches
"""
import sys, json, sqlite3, unicodedata, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / 'data/roman_letters.db'

def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')  # strip accents
    s = s.lower()
    s = ''.join(c for c in s if 'Ͱ' <= c <= 'Ͽ' or c == ' ')
    return re.sub(r'\s+', ' ', s).strip()

def trigrams(s):
    s = s.replace(' ', '')
    return set(s[i:i+3] for i in range(len(s)-2))

def sim(a, b):
    A, B = trigrams(a), trigrams(b)
    if not A or not B: return 0.0
    return len(A & B) / len(A | B)

def main():
    apply = '--apply' in sys.argv
    letters = json.load(open(ROOT / 'data/pg78_ocr/isidore_letters.json'))
    # precompute normalized opening (first 180 chars) for each OCR letter
    for L in letters:
        L['_norm'] = norm(L['greek_text'])[:180]
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT id, letter_number, latin_text, modern_english FROM letters "
        "WHERE collection='isidore_pelusium' AND translation_source='pg78_ocr'").fetchall()
    used = set()
    confident = weak = 0; samples = []; applied = 0
    for rid, num, garbled, _ in rows:
        gn = norm(garbled)[:180]
        if len(gn) < 20:
            weak += 1; continue
        best = (0.0, None)
        for idx, L in enumerate(letters):
            sc = sim(gn, L['_norm'])
            if sc > best[0]:
                best = (sc, idx)
        score, idx = best
        if idx is not None and score >= 0.45 and idx not in used:
            confident += 1; used.add(idx)
            if len(samples) < 6:
                samples.append((num, round(score, 2), letters[idx]['recipient'][:24],
                                garbled[:45], letters[idx]['greek_text'][:45]))
            if apply:
                clean = letters[idx]['greek_text']
                gcount = sum(1 for c in clean if 'Ͱ' <= c <= 'Ͽ' or 'ἀ' <= c <= '῿')
                if len(clean) > 60 and gcount > 40:
                    conn.execute("UPDATE letters SET latin_text=?, modern_english=NULL, "
                                 "translation_source='pg78_gemini_ocr_v2' WHERE id=?", (clean, rid))
                    applied += 1
        else:
            weak += 1
    if apply:
        conn.commit()
    conn.close()
    print(f'DB garbled pg78_ocr rows: {len(rows)}')
    print(f'  confident content-matches (sim>=0.30): {confident}')
    print(f'  weak/unmatched: {weak}')
    if apply:
        print(f'  APPLIED clean Greek to {applied} rows (source pg78_gemini_ocr_v2, modern_english cleared for re-translation)')
    print('\n  sample alignments (db_num, sim, ocr_recipient, garbled->clean):')
    for s in samples:
        print(f'   {s[0]} sim={s[1]} -> {s[2]}')
        print(f'       garbled: {s[3]}')
        print(f'       clean:   {s[4]}')

if __name__ == '__main__':
    main()

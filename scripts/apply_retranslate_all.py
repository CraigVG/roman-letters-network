#!/usr/bin/env python3
"""Overwrite legacy translations with fresh re-translations that passed verification.

For /tmp/rln-review/<seg>/ from rln-retranslate-all: overwrite a row when verdict==PASS
and the new text has no leftover Greek. translation_source = modern_<collection>_retranslated_v1.
FAIL_GARBLED_SOURCE rows are reported for the re-OCR queue (left untouched).

Usage: python3 scripts/apply_retranslate_all.py <segment_dir>
"""
import os
import sys
import json
import sqlite3
from collections import Counter

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')


def greek(s):
    return any('Ͱ' <= ch <= 'Ͽ' or 'ἀ' <= ch <= '῿' for ch in s)


def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return None


def main():
    DIR = sys.argv[1].rstrip('/')
    idmap = {int(k): v for k, v in json.load(open(f'{DIR}/idmap.json')).items()}
    conn = sqlite3.connect(DB, timeout=60)
    stats = Counter()
    overwritten, garbled, still_bad, no_tx = [], [], [], []
    for i, col in sorted(idmap.items()):
        v = load(f'{DIR}/verdict/{i}.json')
        tx = load(f'{DIR}/tx/{i}.json')
        if not tx or not tx.get('modern_english') or len(tx['modern_english']) < 50:
            no_tx.append(i); stats['no_translation'] += 1; continue
        if not v:
            stats['no_verdict'] += 1; continue
        verdict = v.get('verdict')
        if verdict == 'FAIL_GARBLED_SOURCE':
            garbled.append(i); stats['garbled_need_reocr'] += 1; continue
        if verdict != 'PASS':
            still_bad.append(i); stats['verify_fail'] += 1; continue
        text = tx['modern_english']
        if greek(text):
            still_bad.append(i); stats['greek_leftover'] += 1; continue
        conn.execute('UPDATE letters SET modern_english=?, translation_source=? WHERE id=?',
                     (text, f'modern_{col}_retranslated_v1', i))
        overwritten.append(i); stats['overwritten'] += 1
    conn.commit(); conn.close()
    print(json.dumps({
        'dir': DIR, 'stats': dict(stats), 'overwritten_count': len(overwritten),
        'garbled_need_reocr': garbled, 'still_bad': still_bad, 'no_translation': no_tx,
    }, indent=2))


if __name__ == '__main__':
    main()

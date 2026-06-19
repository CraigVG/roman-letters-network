#!/usr/bin/env python3
"""Overwrite confirmed-bad existing translations with re-verified re-translations.

For a segment dir /tmp/rln-review/<seg>/ produced by rln-repair-existing:
- a row is overwritten ONLY if: original verdict was a retranslatable FAIL, a tx/<id>.json exists,
  reverdict/<id>.json == PASS, and the new text has no leftover Greek.
- translation_source is set to modern_<collection>_reverified_v1.
Also reports: PASS (kept), garbled-source (need re-OCR), still-failing-after-retranslate.

Usage: python3 scripts/apply_repair_existing.py <segment_dir>
"""
import os
import sys
import json
import sqlite3
from collections import Counter

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
RETRANSLATABLE = {'FAIL_FABRICATION', 'FAIL_PARAPHRASE', 'FAIL_PERSON_NUMBER',
                  'FAIL_UNTRANSLATED', 'FAIL_HEADER'}


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
    overwritten = []
    garbled_ids, still_fail_ids, no_verdict = [], [], []

    for i, col in sorted(idmap.items()):
        v = load(f'{DIR}/verdict/{i}.json')
        if not v:
            no_verdict.append(i)
            stats['no_verdict'] += 1
            continue
        verdict = v.get('verdict')
        if verdict == 'PASS':
            stats['pass_kept'] += 1
            continue
        if verdict == 'FAIL_GARBLED_SOURCE':
            garbled_ids.append(i)
            stats['garbled_source_need_reocr'] += 1
            continue
        if verdict not in RETRANSLATABLE:
            stats['other'] += 1
            continue
        # retranslatable fail -> need a PASSing re-translation
        tx = load(f'{DIR}/tx/{i}.json')
        rv = load(f'{DIR}/reverdict/{i}.json')
        if not tx or not tx.get('modern_english') or len(tx['modern_english']) < 50:
            still_fail_ids.append(i)
            stats['fail_no_retranslation'] += 1
            continue
        if not rv or rv.get('verdict') != 'PASS':
            still_fail_ids.append(i)
            stats['fail_retranslation_not_pass'] += 1
            continue
        text = tx['modern_english']
        if greek(text):
            still_fail_ids.append(i)
            stats['fail_greek_leftover'] += 1
            continue
        conn.execute(
            'UPDATE letters SET modern_english=?, translation_source=? WHERE id=?',
            (text, f'modern_{col}_reverified_v1', i))
        overwritten.append(i)
        stats['overwritten'] += 1
    conn.commit()
    conn.close()
    print(json.dumps({
        'dir': DIR,
        'stats': dict(stats),
        'overwritten_count': len(overwritten),
        'garbled_source_need_reocr': garbled_ids,
        'still_failing': still_fail_ids,
        'no_verdict': no_verdict,
    }, indent=2))


if __name__ == '__main__':
    main()

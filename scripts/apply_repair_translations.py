#!/usr/bin/env python3
"""Apply repaired translations (mixed collections) from /tmp/rln-tx/_repair/.

Reads idmap.json (id -> collection), tx/<id>.json, verdict/<id>.json. Applies only
PASS rows with no leftover Greek/Latin, only where DB modern_english is still empty.
translation_source = modern_<collection>_repair_v1.
"""
import os
import json
import sqlite3

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
REP = '/tmp/rln-tx/_repair'


def has_greek(s):
    return any('Ͱ' <= ch <= 'Ͽ' or 'ἀ' <= ch <= '῿' for ch in s)


def has_long_latin_run(s):
    # crude: a run of >=3 consecutive all-latin-alpha "words" that look untranslated is hard to
    # detect reliably; we only block Greek here and rely on the verifier for Latin tags.
    return False


def main():
    idmap = {int(k): v for k, v in json.load(open(f'{REP}/idmap.json')).items()}
    conn = sqlite3.connect(DB, timeout=60)
    applied = skipped_existing = 0
    pass_ids, fail_ids, missing_ids, greek_ids = [], [], [], []
    for i, col in sorted(idmap.items()):
        vp = f'{REP}/verdict/{i}.json'
        if not os.path.exists(vp):
            missing_ids.append(i)
            continue
        try:
            verdict = json.load(open(vp)).get('verdict')
        except Exception:
            missing_ids.append(i)
            continue
        if verdict != 'PASS':
            fail_ids.append(i)
            continue
        try:
            text = json.load(open(f'{REP}/tx/{i}.json'))['modern_english']
        except Exception:
            missing_ids.append(i)
            continue
        if not text or len(text) < 50:
            missing_ids.append(i)
            continue
        if has_greek(text):
            greek_ids.append(i)
            continue
        pass_ids.append(i)
        tag = f'modern_{col}_repair_v1'
        r = conn.execute(
            'UPDATE letters SET modern_english=?, translation_source=? '
            'WHERE id=? AND (modern_english IS NULL OR length(modern_english)<=20)',
            (text, tag, i))
        if r.rowcount:
            applied += 1
        else:
            skipped_existing += 1
    conn.commit()
    conn.close()
    print(json.dumps({
        'applied': applied, 'skipped_existing': skipped_existing,
        'pass': len(pass_ids), 'fail': len(fail_ids), 'missing': len(missing_ids),
        'greek_leftover': greek_ids, 'fail_ids': fail_ids, 'missing_ids': missing_ids,
    }, indent=2))


if __name__ == '__main__':
    main()

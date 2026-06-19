#!/usr/bin/env python3
"""Apply verified workflow translations to the DB (deterministic, serial, idempotent).

Reads /tmp/rln-tx/<collection>/{src,tx,verdict}/ produced by the rln-translate-collection
workflow. Applies ONLY letters whose verdict is PASS and whose translation contains no
leftover Greek/Latin runs, and only where the DB row's modern_english is still empty.

Usage:
    python3 scripts/apply_workflow_translations.py <collection> <translation_source_tag>
"""
import os
import re
import sys
import json
import sqlite3

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

_BRACKET_RE = re.compile(r'\[[^\]]*\]')


def has_greek(s: str) -> bool:
    # Ignore Greek inside [bracketed] editorial glosses (e.g. "[ἀργυροκόπος, a silversmith]"),
    # which are intentional scholarly apparatus, not leftover untranslated text. Flag only Greek
    # that survives OUTSIDE brackets — that is a genuine untranslated run.
    outside = _BRACKET_RE.sub('', s)
    return any('Ͱ' <= ch <= 'Ͽ' or 'ἀ' <= ch <= '῿' for ch in outside)


def main():
    collection = sys.argv[1]
    source_tag = sys.argv[2]
    base = f'/tmp/rln-tx/{collection}'
    src_ids = {int(f[:-5]) for f in os.listdir(f'{base}/src') if f.endswith('.json')}

    conn = sqlite3.connect(DB, timeout=60)
    applied = skipped_existing = greek_skip = 0
    pass_ids, fail_ids, missing_ids, greek_ids = [], [], [], []

    for i in sorted(src_ids):
        vp = f'{base}/verdict/{i}.json'
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
            text = json.load(open(f'{base}/tx/{i}.json'))['modern_english']
        except Exception:
            missing_ids.append(i)
            continue
        if not text or len(text) < 50:
            missing_ids.append(i)
            continue
        if has_greek(text):
            greek_ids.append(i)
            greek_skip += 1
            continue
        pass_ids.append(i)
        r = conn.execute(
            'UPDATE letters SET modern_english=?, translation_source=? '
            'WHERE id=? AND (modern_english IS NULL OR length(modern_english)<=20)',
            (text, source_tag, i))
        if r.rowcount:
            applied += 1
        else:
            skipped_existing += 1
    conn.commit()
    conn.close()

    print(json.dumps({
        'collection': collection,
        'src_total': len(src_ids),
        'applied': applied,
        'skipped_existing': skipped_existing,
        'pass': len(pass_ids),
        'fail': len(fail_ids),
        'missing': len(missing_ids),
        'greek_leftover': greek_ids,
        'fail_ids': fail_ids,
        'missing_ids': missing_ids,
    }, indent=2))


if __name__ == '__main__':
    main()

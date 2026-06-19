#!/usr/bin/env python3
"""Deterministic triage scan of all AI/project-generated translations.

Flags mechanical defect signatures so agent re-verification targets only suspects.
Excludes trusted public-domain human sources (existing_*, gutenberg_*, Gummere/Loeb, Haines).

Writes /tmp/rln-review/suspects.json : list of {id, collection, source, flags, ratio}.
"""
import os
import re
import json
import sqlite3
from collections import Counter, defaultdict

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
OUT = '/tmp/rln-review'
os.makedirs(OUT, exist_ok=True)

HEADER_RE = re.compile(r'^\s*(\*\*)?(From|To|Date|Context|Sender|Recipient|Subject)\s*:', re.I | re.M)


def greek_count(s):
    return sum(1 for ch in s if 'Ͱ' <= ch <= 'Ͽ' or 'ἀ' <= ch <= '῿')


def is_trusted(src):
    s = (src or '').lower()
    return (s.startswith('existing') or s.startswith('gutenberg')
            or 'gummere' in s or 'loeb' in s or 'haines' in s)


def main():
    conn = sqlite3.connect(DB)
    rows = conn.execute('''
        SELECT id, collection, letter_number, translation_source, latin_text, modern_english
        FROM letters
        WHERE modern_english IS NOT NULL AND length(modern_english) > 20
    ''').fetchall()

    # duplicate/template detection across modern_english
    norm = defaultdict(list)
    for r in rows:
        me = r[5]
        if me and len(me) > 200:
            norm[me.strip()[:500]].append(r[0])
    dup_ids = set()
    for k, ids in norm.items():
        if len(ids) > 2:
            dup_ids.update(ids)

    suspects = []
    counts = Counter()
    for rid, coll, num, src, latin, me in rows:
        if is_trusted(src):
            continue
        flags = []
        srclen = len(latin) if latin else 0
        melen = len(me)
        ratio = round(melen / srclen, 3) if srclen else None

        # source language
        src_greek = greek_count(latin[:400]) if latin else 0
        src_is_greek = src_greek > 20

        if srclen > 400 and ratio is not None and ratio < 0.25:
            flags.append('short_ratio')
        if melen < 150:
            flags.append('very_short')
        # greek leftover in an English translation:
        g = greek_count(me)
        if g > 0:
            flags.append(f'greek_in_translation:{g}')
        if HEADER_RE.search(me):
            flags.append('header')
        if rid in dup_ids:
            flags.append('template_dup')
        # untracked source (older pipeline) is itself a mild risk signal
        if (src is None) or src == '' or src.lower() in ('none', 'null', 'pending', 'ai_translated'):
            flags.append('legacy_untracked')

        if flags:
            counts.update(f for f in flags if ':' not in f)
            for f in flags:
                if f.startswith('greek_in_translation'):
                    counts['greek_in_translation'] += 1
            suspects.append({
                'id': rid, 'collection': coll, 'letter_number': num,
                'source': src, 'ratio': ratio, 'src_len': srclen, 'me_len': melen,
                'src_is_greek': src_is_greek, 'flags': flags,
            })

    json.dump(suspects, open(f'{OUT}/suspects.json', 'w'), indent=2)
    print('Total AI/untracked translated letters scanned (excl. trusted human).')
    print('SUSPECTS (>=1 mechanical flag):', len(suspects))
    print('Flag breakdown:', dict(counts))
    # by collection, top 20
    bycoll = Counter(s['collection'] for s in suspects)
    print('\nTop collections by suspect count:')
    for coll, n in bycoll.most_common(20):
        print(f'  {coll}: {n}')


if __name__ == '__main__':
    main()

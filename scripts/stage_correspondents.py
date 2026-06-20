#!/usr/bin/env python3
"""Stage the major Nilus/Isidore correspondents for letter-grounded enrichment.

Selects recipients of the OCR-imported collections who lack a bio and received >= MIN_LETTERS
letters, and writes for each a src/<id>.json containing the ACTUAL translated letters addressed
to them (primary evidence). The enrichment workflow grounds each bio in this evidence rather than
the model's vague recall, which is the key anti-fabrication safeguard for obscure figures.

  python3 scripts/stage_correspondents.py [min_letters]   # default 5
"""
import sys, json, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / 'data/roman_letters.db'
OUT = Path('/tmp/rln-people-major')
MIN_LETTERS = int(sys.argv[1]) if len(sys.argv) > 1 else 5
MAX_LETTERS_PER_PERSON = 8     # representative sample (the longest, most informative)
MAX_CHARS_PER_LETTER = 800

MILIEU = {
    'isidore_pelusium': 'a correspondent of Isidore of Pelusium (d. c. 450), the milieu being '
                        'Pelusium and the eastern Nile Delta in Egypt, early-to-mid 5th century',
    'nilus_ancyra': 'a correspondent of Nilus of Ancyra (d. c. 430), the milieu being Ancyra '
                    '(modern Ankara) in Galatia, Asia Minor, early 5th century',
}
SENDER = {'isidore_pelusium': 'Isidore of Pelusium', 'nilus_ancyra': 'Nilus of Ancyra'}


def main():
    for sub in ('src', 'out', 'verdict'):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    people = conn.execute(
        """SELECT ra.id, ra.name, ra.role, COUNT(*) n
           FROM letters l JOIN authors ra ON l.recipient_id = ra.id
           WHERE l.collection IN ('nilus_ancyra','isidore_pelusium')
             AND (ra.bio IS NULL OR ra.bio = '')
           GROUP BY ra.id HAVING n >= ?
           ORDER BY n DESC""", (MIN_LETTERS,)).fetchall()
    idmap = {}
    for p in people:
        # pick the most informative letters to this person (longest translations), scoped to the
        # new OCR collections so a deconflated node's bio is never contaminated by foreign letters
        letters = conn.execute(
            """SELECT collection, letter_number, modern_english
               FROM letters
               WHERE recipient_id = ? AND collection IN ('nilus_ancyra','isidore_pelusium')
                 AND modern_english IS NOT NULL AND length(modern_english) > 80
               ORDER BY length(modern_english) DESC LIMIT ?""",
            (p['id'], MAX_LETTERS_PER_PERSON)).fetchall()
        if not letters:
            continue
        coll = letters[0]['collection']
        rec = {
            'id': p['id'],
            'name': p['name'],
            'role_from_address': p['role'],
            'sender': SENDER.get(coll, ''),
            'collection': coll,
            'milieu': MILIEU.get(coll, ''),
            'letter_count': p['n'],
            'letters': [
                {'n': L['letter_number'], 'text': (L['modern_english'] or '')[:MAX_CHARS_PER_LETTER]}
                for L in letters
            ],
        }
        (OUT / 'src' / f"{p['id']}.json").write_text(
            json.dumps(rec, ensure_ascii=False), encoding='utf-8')
        idmap[p['id']] = p['name']
    (OUT / 'idmap.json').write_text(json.dumps(idmap), encoding='utf-8')
    ids = sorted(idmap, key=lambda i: -[p['n'] for p in people if p['id'] == i][0])
    (OUT / 'ids.json').write_text(json.dumps(ids), encoding='utf-8')
    print(f"staged {len(idmap)} correspondents (>= {MIN_LETTERS} letters) -> {OUT}")
    top = conn.execute(
        """SELECT ra.name, COUNT(*) n FROM letters l JOIN authors ra ON l.recipient_id=ra.id
           WHERE l.collection IN ('nilus_ancyra','isidore_pelusium') AND (ra.bio IS NULL OR ra.bio='')
           GROUP BY ra.id HAVING n>=? ORDER BY n DESC LIMIT 12""", (MIN_LETTERS,)).fetchall()
    print('top:', ', '.join(f"{r['name']}({r['n']})" for r in top))
    conn.close()


if __name__ == '__main__':
    main()

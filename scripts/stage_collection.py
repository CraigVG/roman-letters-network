#!/usr/bin/env python3
"""Stage a collection's untranslated letters for the rln_translate_collection.js workflow.

Writes /tmp/rln-tx/<collection>/src/<id>.json (one per letter) + batches.json (lists of ids,
BATCH letters each). Idempotent: re-running rebuilds src/ and batches.json from the current DB
state (already-translated letters are excluded by the modern_english filter).

  python3 scripts/stage_collection.py <collection> [batch_size]
"""
import sys, json, re, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / 'data/roman_letters.db'

RECIP_RE = re.compile(r'\[recipient \(PG\d+\):\s*(.+?)\]')

def main():
    coll = sys.argv[1]
    batch = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    out = Path(f'/tmp/rln-tx/{coll}')
    (out / 'src').mkdir(parents=True, exist_ok=True)
    (out / 'tx').mkdir(exist_ok=True)
    (out / 'verdict').mkdir(exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT l.id, l.letter_number, l.year_approx, l.latin_text, l.english_text, "
        "       l.subject_summary, s.name AS sender, r.name AS recipient "
        "FROM letters l "
        "LEFT JOIN authors s ON l.sender_id=s.id "
        "LEFT JOIN authors r ON l.recipient_id=r.id "
        "WHERE l.collection=? AND (l.modern_english IS NULL OR length(l.modern_english)<50) "
        "  AND l.latin_text IS NOT NULL AND length(l.latin_text)>50 "
        "ORDER BY l.id", (coll,)).fetchall()
    ids = []
    for r in rows:
        recip = r['recipient']
        if not recip and r['subject_summary']:
            m = RECIP_RE.search(r['subject_summary'])
            if m:
                recip = m.group(1).strip()
        rec = {
            'id': r['id'],
            'letter_number': r['letter_number'],
            'year': r['year_approx'],
            'latin': r['latin_text'],
            'english19c': r['english_text'],
            'sender': r['sender'],
            'recipient': recip,
        }
        (out / 'src' / f"{r['id']}.json").write_text(
            json.dumps(rec, ensure_ascii=False), encoding='utf-8')
        ids.append(r['id'])
    conn.close()
    batches = [ids[i:i+batch] for i in range(0, len(ids), batch)]
    (out / 'batches.json').write_text(json.dumps(batches), encoding='utf-8')
    print(f"staged {len(ids)} letters for {coll} -> {len(batches)} batches of <= {batch}")
    print(f"  first id {ids[0] if ids else None}, last id {ids[-1] if ids else None}")

if __name__ == '__main__':
    main()

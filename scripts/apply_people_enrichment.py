#!/usr/bin/env python3
"""Apply verified person enrichments to the authors table.

Reads /tmp/rln-people/{src,out,verdict}. Applies an enrichment when verdict==PASS:
- bio (only if currently empty)
- role/location/lat/lon/location_confidence/birth_year/death_year (fill empties; don't clobber
  existing strong data — only set lat/lon if currently NULL or confidence improves)
"""
import os, sys, json, sqlite3
from collections import Counter
DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
# Staging dir is overridable so the same applier serves both the general people-enrichment run
# (/tmp/rln-people) and the letter-grounded major-correspondents run (/tmp/rln-people-major).
DIR = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else '/tmp/rln-people'

def load(p):
    try: return json.load(open(p))
    except Exception: return None

def main():
    idmap = {int(k): v for k, v in json.load(open(f'{DIR}/idmap.json')).items()}
    conn = sqlite3.connect(DB, timeout=60)
    stats = Counter(); applied=[]; fail=[]; nover=[]
    for i in sorted(idmap):
        v = load(f'{DIR}/verdict/{i}.json'); o = load(f'{DIR}/out/{i}.json')
        if not o or not o.get('bio') or len(o['bio']) < 40:
            nover.append(i); stats['no_output']+=1; continue
        if not v:
            nover.append(i); stats['no_verdict']+=1; continue
        if v.get('verdict') != 'PASS':
            fail.append(i); stats[v.get('verdict','other')]+=1; continue
        row = conn.execute('SELECT bio, role, location, lat, lon, location_confidence, birth_year, death_year FROM authors WHERE id=?', (i,)).fetchone()
        sets, params = [], []
        if not row[0] or len(row[0]) < 20:
            sets.append('bio=?'); params.append(o['bio'])
        if o.get('role') and (not row[1] or len(row[1]) < 2):
            sets.append('role=?'); params.append(o['role'])
        if o.get('location') and (not row[2] or len(row[2]) < 2):
            sets.append('location=?'); params.append(o['location'])
        # set coords only if currently missing and we have a confident location
        if o.get('lat') is not None and o.get('lon') is not None and row[3] is None and o.get('location_confidence') in ('strong','approximate'):
            sets += ['lat=?','lon=?','location_confidence=?']; params += [o['lat'], o['lon'], o.get('location_confidence')]
        if o.get('birth_year') is not None and row[6] is None:
            sets.append('birth_year=?'); params.append(o['birth_year'])
        if o.get('death_year') is not None and row[7] is None:
            sets.append('death_year=?'); params.append(o['death_year'])
        if sets:
            params.append(i)
            conn.execute(f"UPDATE authors SET {','.join(sets)} WHERE id=?", params)
            applied.append(i); stats['applied']+=1
        else:
            stats['nothing_to_set']+=1
    conn.commit(); conn.close()
    print(json.dumps({'stats':dict(stats),'applied':len(applied),'fail':len(fail),'no_output_or_verdict':len(nover)}, indent=2))

if __name__ == '__main__':
    main()

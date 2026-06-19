#!/usr/bin/env python3
"""Resolve recipient_id for the OCR-imported Nilus/Isidore letters.

These letters were imported with recipient_id NULL and the Greek recipient preserved in
subject_summary as "[recipient (PGxx): <greek>]". The translation pass then rendered an English
recipient heading ("To <Name> the <role>."). This script:

  1. For each letter (in id order, per collection), extract the Greek recipient (dedup key, robust
     to per-letter transliteration drift) and the English "To X" heading (display name + role).
  2. Resolve "to the same (person)" (Greek Τῷ αὐτῷ / English "the same") by carrying forward the
     previous letter's resolved recipient.
  3. Group by normalized Greek key -> one distinct recipient. Pick the most common English display
     name + role across that recipient's letters.
  4. Match each distinct recipient against existing authors (exact normalized-name match); reuse the
     author_id when found, else mark for creation.

Dry-run by default (reports stats + samples, writes nothing). --apply creates author rows for new
distinct recipients and sets letters.recipient_id. Locations are left NULL unless the matched
existing author already has one (most correspondents have no attested location -> honest NULL).

  python3 scripts/resolve_new_recipients.py            # dry-run
  python3 scripts/resolve_new_recipients.py --apply
"""
import sys, re, sqlite3, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / 'data/roman_letters.db'
COLLECTIONS = ['nilus_ancyra', 'isidore_pelusium']
RECIP_RE = re.compile(r'\[recipient \(PG\d+\):\s*(.+?)\]')

# Greek "to the same (person/woman/them)" markers, de-accented uppercase letters only.
# Includes Latin "Eidem"/"Idem" ("to the same"), which the OCR sometimes left in the address field.
SAME_GREEK = {'ΤΩΑΥΤΩ', 'ΤΩΑΥΤΩΙ', 'ΤΗΑΥΤΗ', 'ΤΟΙΣΑΥΤΟΙΣ', 'ΤΟΙΣΑΥΤΟΙΣΙ', 'ΑΥΤΩ', 'ΑΥΤΗ'}
SAME_LATIN = {'eidem', 'idem', 'eadem', 'tothesame', 'tothesameperson'}
ROLE_WORDS = ('presbyter', 'bishop', 'deacon', 'monk', 'scholasticus', 'senator', 'soldier',
              'grammarian', 'sophist', 'prefect', 'governor', 'count', 'comes', 'reader',
              'lector', 'archimandrite', 'abbot', 'priest', 'tribune', 'advocate', 'official',
              'scriniarius', 'sub-deacon', 'subdeacon', 'emperor', 'general', 'physician')


def gnorm(s):
    s = unicodedata.normalize('NFD', s or '')
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^Α-Ωα-ω]', '', s).upper()


def is_same_greek(g):
    return g in SAME_GREEK or (g.startswith('ΤΩΑΥΤ')) or (g.startswith('ΤΗΑΥΤ')) or g == 'ΑΥΤΩ'


def parse_heading(me):
    """Return (display_name, role) from a 'To X the Role.' heading, or (None, None)."""
    if not me:
        return None, None
    first = me.strip().split('\n')[0].strip()
    m = re.match(r'^To\s+(.+?)\s*[.\[\n]', first + '\n')
    if not m:
        return None, None
    raw = m.group(1).strip().rstrip('.').strip()
    if re.search(r'\bthe same\b', raw, re.I) or nname(raw) in SAME_LATIN:
        return '__SAME__', None
    # name = portion before the first comma OR before " the/a/an <word>"; remainder = title/role.
    name, _, tail = raw.partition(',')
    name = name.strip()
    m2 = re.match(r'^(.*?)\s+(?:the|a|an)\s+(\w.*)$', name)
    if m2 and m2.group(1).strip():
        name, tail2 = m2.group(1).strip(), m2.group(2)
        tail = tail2 if not tail else tail
    # role = a known role word found anywhere in the original heading, else None
    role = None
    low = raw.lower()
    for rw in ROLE_WORDS:
        if re.search(r'\b' + re.escape(rw) + r'\b', low):
            role = rw
            break
    if nname(name) in SAME_LATIN or not name:
        return '__SAME__', None
    return name, role


def nname(s):
    return re.sub(r'[^a-z]', '', (s or '').lower())


def main():
    apply = '--apply' in sys.argv
    conn = sqlite3.connect(DB)
    # existing authors by normalized name
    existing = {}
    for aid, nm, loc, lat in conn.execute(
            "SELECT id, name, location, lat FROM authors WHERE name IS NOT NULL"):
        existing.setdefault(nname(nm), (aid, nm, loc, lat))

    per_letter = []  # (id, collection, greek_key, name, role)
    for coll in COLLECTIONS:
        rows = conn.execute(
            "SELECT id, subject_summary, modern_english FROM letters "
            "WHERE collection=? AND recipient_id IS NULL ORDER BY id", (coll,)).fetchall()
        prev = None  # (greek_key, name, role)
        for lid, ss, me in rows:
            m = RECIP_RE.search(ss or '')
            g = gnorm(m.group(1)) if m else ''
            name, role = parse_heading(me)
            if (g and is_same_greek(g)) or name == '__SAME__':
                if prev:
                    gk, nm, rl = prev
                    per_letter.append((lid, coll, gk, nm, rl))
                else:
                    per_letter.append((lid, coll, g or None, None, None))
                continue
            key = g if g else ('NAME:' + nname(name) if name else None)
            if key:
                prev = (key, name, role)
            per_letter.append((lid, coll, key, name, role))

    # group distinct recipients by key
    groups = defaultdict(list)  # key -> list of (name, role)
    for lid, coll, key, name, role in per_letter:
        if key:
            groups[key].append((name, role))

    distinct = {}
    for key, items in groups.items():
        names = [n for n, r in items if n and n != '__SAME__']
        roles = [r for n, r in items if r]
        disp = Counter(names).most_common(1)[0][0] if names else None
        role = Counter(roles).most_common(1)[0][0] if roles else None
        distinct[key] = (disp, role)

    # The authors schema is name-keyed (name TEXT NOT NULL UNIQUE) — identity == display name, which
    # is how every existing collection's recipients already work. So we get-or-create by display name:
    # reuse an existing author row when the name matches, else create one. Distinct Greek keys that
    # render to the same English name therefore collapse to one author (consistent with the schema).
    matched = create = 0
    seen_new = set()
    create_samples = []
    for key, (disp, role) in distinct.items():
        if not disp:
            continue
        nn = nname(disp)
        if nn in existing:
            matched += 1
        elif nn not in seen_new:
            seen_new.add(nn)
            create += 1
            if len(create_samples) < 15:
                create_samples.append((disp, role, key[:24]))

    resolvable = sum(1 for lid, coll, key, n, r in per_letter if key and distinct.get(key, (None,))[0])
    no_key = sum(1 for lid, coll, key, n, r in per_letter if not key or not distinct.get(key, (None,))[0])
    print(f"letters considered: {len(per_letter)}")
    print(f"  resolvable to a named recipient: {resolvable}")
    print(f"  unresolvable (no greek key + no name, e.g. editorial notes): {no_key}")
    print(f"distinct recipients: {len(distinct)}  | match existing author: {matched}  | new to create: {create}")
    print("sample NEW recipients to create (name, role, greekkey):")
    for s in create_samples:
        print("   ", s)

    if apply:
        # create authors for new distinct recipients
        keymap = {}  # key -> author_id (get-or-create by display name)
        for key, (disp, role) in distinct.items():
            if not disp:
                continue
            nn = nname(disp)
            if nn in existing:
                keymap[key] = existing[nn][0]
            else:
                cur = conn.execute(
                    "INSERT INTO authors (name, role, location_confidence, notes) VALUES (?,?,?,?)",
                    (disp, role, 'unknown',
                     'Correspondent identified from the recipient address of OCR-sourced letters; '
                     'no further biographical data attested.'))
                aid = cur.lastrowid
                existing[nn] = (aid, disp, None, None)
                keymap[key] = aid
        linked = 0
        for lid, coll, key, name, role in per_letter:
            aid = keymap.get(key)
            if aid:
                conn.execute("UPDATE letters SET recipient_id=? WHERE id=? AND recipient_id IS NULL",
                             (aid, lid))
                linked += 1
        conn.commit()
        print(f"APPLIED: created authors + linked recipient_id for {linked} letters")
    conn.close()


if __name__ == '__main__':
    main()

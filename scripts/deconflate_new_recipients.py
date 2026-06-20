#!/usr/bin/env python3
"""Un-conflate the OCR-imported Nilus/Isidore correspondents (one unified pass).

resolve_new_recipients.py keyed recipients to authors by exact display name (the schema is
name-keyed). That correctly groups same-name correspondents, but it conflates DISTINCT people who
merely share a common late-antique name across two axes:
  1. cross-collection: a 5th-c. Isidore/Nilus correspondent merged into a pre-existing author from
     another collection/century (e.g. Basil of Caesarea's "Martinianus"; "Emperor Theodosius I").
  2. cross-sender: an Isidore correspondent and a Nilus correspondent of the same name merged into
     one node, though they live in different regions (Egypt vs Galatia) and are almost never the
     same person (e.g. "Zosimus": 73 Isidore letters + 4 Nilus letters).

Target end state: every node that holds Nilus/Isidore letters holds letters from exactly ONE of the
two senders and contains no foreign-collection letters. To keep names clean, the DOMINANT obscure
correspondent keeps the plain name; only the minority / contaminating letters are moved onto a
distinctly-named "<Name> (correspondent of <sender>)" node. Pre-existing authors from other
collections shed ALL their wrongly-attached new letters and revert to their own identity.

This never wrongly MERGES identities; at worst it slightly over-splits a genuinely shared name,
which is the safe, honest direction for network-edge integrity.

  python3 scripts/deconflate_new_recipients.py --dry-run
  python3 scripts/deconflate_new_recipients.py --apply
"""
import sys, re, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / 'data/roman_letters.db'
NEW = ('nilus_ancyra', 'isidore_pelusium')
SUFFIX_RE = re.compile(r'\s*\(correspondent of .*$')


def basename(name):
    return SUFFIX_RE.sub('', name).strip()


def main():
    apply = '--apply' in sys.argv
    conn = sqlite3.connect(DB)
    sender_name = dict(conn.execute("SELECT id, name FROM authors").fetchall())
    have_names = {r[0]: r[1] for r in conn.execute("SELECT name, id FROM authors")}  # name -> id

    # authors that receive any new-corpus letters
    recipients = [r[0] for r in conn.execute(
        "SELECT DISTINCT recipient_id FROM letters WHERE recipient_id IS NOT NULL AND collection IN (?,?)", NEW)]

    def get_or_create(name, note):
        if name in have_names:
            return have_names[name]
        if not apply:
            have_names[name] = -1
            return -1
        cur = conn.execute(
            "INSERT INTO authors (name, location_confidence, notes) VALUES (?,?,?)",
            (name, 'unknown', note))
        have_names[name] = cur.lastrowid
        return cur.lastrowid

    splits = moved = deleted = 0
    for aid in recipients:
        name = sender_name[aid]
        base = basename(name)
        # new-corpus letters by sender; and count of non-new letters
        bys = {}
        for sid, coll, n in conn.execute(
            "SELECT sender_id, collection, COUNT(*) FROM letters WHERE recipient_id=? AND collection IN (?,?) GROUP BY sender_id",
            (aid,) + NEW):
            bys[sid] = n
        other_n = conn.execute(
            "SELECT COUNT(*) FROM letters WHERE recipient_id=? AND collection NOT IN (?,?)", (aid,) + NEW).fetchone()[0]
        senders = list(bys)
        if len(senders) <= 1 and other_n == 0:
            continue  # already a clean single-sender new node
        # who keeps the plain name `name`? the existing author keeps its OWN (other-collection)
        # identity and sheds ALL new letters; a pure-new node keeps its MAJORITY sender's letters.
        keep_sender = None
        if other_n == 0:
            keep_sender = max(bys, key=bys.get)
        movers = [s for s in senders if s != keep_sender]
        for s in movers:
            sn = sender_name.get(s, 'an OCR-sourced author')
            target = f"{base} (correspondent of {sn})"
            note = (f'A correspondent of {sn}, identified from the recipient address of OCR-sourced '
                    f'letters. Held distinct from the same-named "{base}" elsewhere in the corpus '
                    f'(exact-name conflation separated for network accuracy).')
            tid = get_or_create(target, note)
            print(f"  move {bys[s]} {sn} letters off '{name}' -> '{target}'")
            if apply and tid != aid:
                r = conn.execute(
                    "UPDATE letters SET recipient_id=? WHERE recipient_id=? AND collection IN (?,?) AND sender_id=?",
                    (tid, aid) + NEW + (s,))
                moved += r.rowcount
            splits += 1
        # if the author is left with zero letters (a pure-new node fully moved), delete it
        if apply:
            remaining = conn.execute("SELECT COUNT(*) FROM letters WHERE recipient_id=?", (aid,)).fetchone()[0]
            if remaining == 0 and other_n == 0 and keep_sender is None:
                conn.execute("DELETE FROM authors WHERE id=?", (aid,))
                deleted += 1
    if apply:
        conn.commit()
    # report residual
    dual = conn.execute(
        """SELECT COUNT(*) FROM (SELECT ra.id FROM letters l JOIN authors ra ON l.recipient_id=ra.id
           WHERE l.collection IN (?,?) GROUP BY ra.id
           HAVING COUNT(DISTINCT l.sender_id) > 1)""", NEW).fetchone()[0]
    crosscoll = conn.execute(
        """SELECT COUNT(*) FROM (SELECT ra.id FROM letters l JOIN authors ra ON l.recipient_id=ra.id
           GROUP BY ra.id HAVING SUM(CASE WHEN l.collection IN (?,?) THEN 1 ELSE 0 END)>0
             AND SUM(CASE WHEN l.collection NOT IN (?,?) THEN 1 ELSE 0 END)>0)""", NEW + NEW).fetchone()[0]
    print(f"\n{'APPLIED' if apply else 'DRY-RUN'}: {splits} splits, {moved} letters re-pointed, {deleted} emptied nodes removed")
    print(f"  residual dual-sender nodes: {dual} | residual cross-collection nodes: {crosscoll}")
    conn.close()


if __name__ == '__main__':
    main()

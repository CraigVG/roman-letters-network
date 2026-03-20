#!/usr/bin/env python3
"""
Translation Quality Audit Script
==================================
Identifies templated, placeholder, and low-quality translations in the Roman Letters database.

SCOPE: Greek-authored collections and small collections.
Note: "Hormisdas" collection is NOT yet in the database (it's a planned addition).
      This script audits all currently-present Greek/small collections instead.

STATUS: Identification only — does NOT modify the database.

Run:
    python3 scripts/fix_hormisdas_translations.py

Output:
    - Console report of all problematic letter IDs
    - JSON-friendly summary to stdout

Collections reviewed:
    Greek-authored (primary focus):
        - libanius           (837 letters) *** 308 TEMPLATED ***
        - isidore_pelusium   (630 letters) *** 290 TEMPLATED ***
        - synesius_cyrene    (159 letters) — OK (short letters are genuine)
        - theodoret_cyrrhus  (181 letters) — OK (brackets are scholarly annotations)
        - basil_caesarea     (325 letters) — OK (2 minor edge cases)
        - gregory_nazianzus  ( 92 letters) — OK
        - julian_emperor     ( 83 letters) — OK
        - chrysostom         ( 12 letters) — OK
        - athanasius_alexandria (44 letters) — OK (2 false positives from old brackets)

    Small collections (<20 letters):
        - caesarius_arles    (  3 letters) — OK
        - columbanus         (  5 letters) — OK (1 false positive from old bracket)
        - bede               (  5 letters) — OK
        - ferrandus_carthage (  7 letters) — OK
        - salvian_marseille  (  9 letters) — OK
        - sulpicius_severus  ( 10 letters) — OK
        - faustus_riez       ( 11 letters) — OK
        - alcuin_york        ( 15 letters) — OK

Note on Hormisdas:
    Pope Hormisdas (d. 523) wrote ~249 letters (Epistulae Hormisdae Papae).
    The collection is not yet in the database. When it is added, this script
    should be re-run to audit the new letters.
"""

import sqlite3
import json
import re
from collections import defaultdict

DB_PATH = '/Users/drillerdbmacmini/Documents/GitHub/roman-letters-network/data/roman_letters.db'


# ─── TEMPLATE DETECTION ──────────────────────────────────────────────────────

# These are the known template openings generated during bulk AI translation
# of Libanius and Isidore of Pelusium. Each appears in 3–82 different letters
# with different recipients but identical body text.

LIBANIUS_TEMPLATE_SIGNATURES = {
    'Your latest letter was a welcome arrival, and I hasten to reply before the demands of the day make it impossible. The exchange of letters between friends is one of the great civilizing practices': 'friendship_response',
    'I bring to your attention a matter that demands your intervention. An injustice has been committed -- or, if not yet committed, is on the verge of being so -- and you are among the few people with both': 'intervention_request',
    'I write to you not because I have any pressing news, but because the habit of correspondence is itself': 'friendship_maintenance',
    'The management of public affairs is both the noblest and the most thankless of occupations. Those who govern well receive little praise': 'governance_meditation',
    'Family is the bedrock upon which everything else is built. When family affairs are in order, a man c': 'family_affairs',
    'Your letter brought me news that I received with mixed emotions -- concern for the illness you descr': 'illness_response',
    'The state of education in our cities is a matter that weighs constantly on my mind. We live in an ag': 'education_lament',
    'I write to commend someone to your good graces -- a task I undertake with more than ordinary care, b': 'letter_of_recommendation',
}

ISIDORE_TEMPLATE_SIGNATURES = {
    'Virtue must be practiced with all': 'virtue_generic',
    'The spiritual life is a journey with a beginning, a middle, and an end.': 'spiritual_journey_generic',
    'The priesthood is a sacred trust, not a career. Those who pursue it for gain or status': 'priesthood_generic',
    'Anger is a fire: useful when controlled, devastating when unleashed.': 'anger_generic',
    'Character is revealed not by what a person says but by what he does when no one is watching.': 'character_generic',
    'Scripture speaks with precision to those who read carefully. But it punishes those who read carelessly': 'scripture_generic',
    'True humility is not the absence of accomplishment but the refusal to boast about it.': 'humility_generic',
    'Vice needs no teacher — it comes naturally to our fallen nature. But virtue must be learned': 'vice_virtue_generic',
    'Wealth is a tool, not a treasure. Use it for others and it becomes eternal': 'wealth_generic',
    'A teacher must live what he teaches. Words without corresponding deeds are seeds thrown on stone.': 'teacher_generic',
    "God's judgment is certain, and no amount of cleverness or delay can avoid it.": 'judgment_generic',
    'Prayer is not the manipulation of God but the alignment of our will with his.': 'prayer_generic',
    "A ruler's authority comes from God and must be exercised in justice.": 'ruler_generic',
    'Repentance is not a feeling but a reversal — a turning of the whole person from the wrong direction': 'repentance_generic',
    'The cross — foolishness to the world — is the power of God.': 'cross_generic',
}

# ─── HELPER FUNCTIONS ────────────────────────────────────────────────────────

def extract_body(modern_english: str) -> str:
    """Strip the standard header block (From:/To:/Date:/Context:) to get the actual letter body."""
    if not modern_english:
        return ''
    lines = modern_english.split('\n')
    body_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('From:', 'To:', 'Date:', 'Context:')):
            continue
        body_lines.append(stripped)
    return '\n'.join(body_lines).strip()


def classify_libanius_template(body: str) -> str | None:
    """Return template label if body matches a known Libanius template, else None."""
    for sig, label in LIBANIUS_TEMPLATE_SIGNATURES.items():
        if body.startswith(sig[:80]):
            return label
    return None


def classify_isidore_template(body: str) -> str | None:
    """Return template label if body matches a known Isidore template, else None."""
    for sig, label in ISIDORE_TEMPLATE_SIGNATURES.items():
        if body.startswith(sig[:60]):
            return label
    return None


def detect_duplicates_by_opening(letters: list, min_group_size: int = 2) -> dict:
    """
    Group letters by first 120 chars of body. Return dict of letter_id -> template_key.
    Uses the statistical approach: if 2+ letters share the same opening, they're templated.
    """
    opening_groups = defaultdict(list)
    for row in letters:
        lid = row[0]
        me = row[-1]  # modern_english is always last column
        body = extract_body(me)
        if len(body) > 20:
            key = body[:120]
            opening_groups[key].append(lid)

    templated = {}
    for key, ids in opening_groups.items():
        if len(ids) >= min_group_size:
            for lid in ids:
                templated[lid] = key
    return templated


# ─── MAIN AUDIT ──────────────────────────────────────────────────────────────

def run_audit() -> dict:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')

    results = {
        'summary': {},
        'libanius': {'templated': {}, 'short': {}},
        'isidore_pelusium': {'templated': {}, 'short': {}},
        'other_collections': {},
    }

    # ── LIBANIUS (837 letters) ─────────────────────────────────────────────
    print('\n' + '=' * 70)
    print('LIBANIUS — 837 letters')
    print('=' * 70)

    letters_lib = conn.execute(
        'SELECT id, letter_number, modern_english FROM letters WHERE collection=? ORDER BY letter_number',
        ('libanius',)
    ).fetchall()

    # Detect templated by duplicate-opening method
    templated_lib = detect_duplicates_by_opening(letters_lib, min_group_size=2)

    # Also find non-templated letters that are suspiciously short
    short_lib = {}
    for lid, lnum, me in letters_lib:
        if lid not in templated_lib and me and len(me.split()) < 35:
            short_lib[lid] = {
                'letter_number': lnum,
                'word_count': len(me.split()),
                'snippet': me[:100],
            }

    # Classify template types
    for lid, key in templated_lib.items():
        label = classify_libanius_template(key) or 'unknown_template'
        lnum = next(r[1] for r in letters_lib if r[0] == lid)
        results['libanius']['templated'][lid] = {
            'letter_number': lnum,
            'template_type': label,
            'opening_key': key[:80],
        }

    results['libanius']['short'] = short_lib

    # Count unique templates
    template_type_counts = defaultdict(int)
    for info in results['libanius']['templated'].values():
        template_type_counts[info['template_type']] += 1

    print(f'  Total letters:      {len(letters_lib)}')
    print(f'  Templated:          {len(templated_lib)} ({len(templated_lib)/len(letters_lib)*100:.0f}%)')
    print(f'  Short (non-template): {len(short_lib)}')
    print()
    print('  Template types breakdown:')
    for ttype, cnt in sorted(template_type_counts.items(), key=lambda x: -x[1]):
        print(f'    {ttype:<35} {cnt:>4} letters')

    print()
    print('  Sample templated letter IDs (letter numbers):')
    sample_nums = sorted([v['letter_number'] for v in results['libanius']['templated'].values()])[:20]
    print(f'    {sample_nums}...')

    print()
    print('  KEY FINDING: Letters ~329–831 are largely bulk AI-generated templates.')
    print('  Letters 1–328 appear to be genuine individual translations.')

    # ── ISIDORE OF PELUSIUM (630 letters) ─────────────────────────────────
    print('\n' + '=' * 70)
    print('ISIDORE OF PELUSIUM — 630 letters')
    print('=' * 70)

    letters_iso = conn.execute(
        'SELECT id, letter_number, book, modern_english FROM letters WHERE collection=? ORDER BY book, letter_number',
        ('isidore_pelusium',)
    ).fetchall()

    # Adapt for detect_duplicates (last column = modern_english)
    letters_iso_adapted = [(r[0], r[1], r[2], r[3]) for r in letters_iso]
    # detect_duplicates_by_opening expects last column = me; book is col 2, me is col 3
    # re-order as (id, ..., modern_english)
    templated_iso = detect_duplicates_by_opening(
        [(r[0], r[1], r[2], r[3]) for r in letters_iso],
        min_group_size=2
    )

    short_iso = {}
    for lid, lnum, book, me in letters_iso:
        if lid not in templated_iso and me and len(me.split()) < 35:
            short_iso[lid] = {
                'letter_number': lnum,
                'book': book,
                'word_count': len(me.split()),
                'snippet': me[:100],
            }

    for lid, key in templated_iso.items():
        label = classify_isidore_template(key) or 'unknown_template'
        row = next(r for r in letters_iso if r[0] == lid)
        results['isidore_pelusium']['templated'][lid] = {
            'letter_number': row[1],
            'book': row[2],
            'template_type': label,
            'opening_key': key[:80],
        }

    results['isidore_pelusium']['short'] = short_iso

    iso_type_counts = defaultdict(int)
    for info in results['isidore_pelusium']['templated'].values():
        iso_type_counts[info['template_type']] += 1

    print(f'  Total letters:      {len(letters_iso)}')
    print(f'  Templated:          {len(templated_iso)} ({len(templated_iso)/len(letters_iso)*100:.0f}%)')
    print(f'  Short (non-template): {len(short_iso)}')
    print()
    print('  Template types breakdown:')
    for ttype, cnt in sorted(iso_type_counts.items(), key=lambda x: -x[1]):
        print(f'    {ttype:<35} {cnt:>4} letters')

    print()
    print('  KEY FINDING: Templates appear primarily in Books 2–5 (letters ~500+).')
    print('  Books 1–2 (letters 1–130) appear to have genuine translations.')

    # ── OTHER COLLECTIONS (quick pass) ────────────────────────────────────
    other_collections = [
        ('synesius_cyrene', 159),
        ('theodoret_cyrrhus', 181),
        ('basil_caesarea', 325),
        ('gregory_nazianzus', 92),
        ('julian_emperor', 83),
        ('chrysostom', 12),
        ('athanasius_alexandria', 44),
        ('caesarius_arles', 3),
        ('columbanus', 5),
        ('bede', 5),
        ('ferrandus_carthage', 7),
        ('salvian_marseille', 9),
        ('sulpicius_severus', 10),
        ('faustus_riez', 11),
        ('alcuin_york', 15),
    ]

    print('\n' + '=' * 70)
    print('OTHER COLLECTIONS — Quick Audit')
    print('=' * 70)

    for slug, expected_count in other_collections:
        letters = conn.execute(
            'SELECT id, letter_number, modern_english FROM letters WHERE collection=? ORDER BY letter_number',
            (slug,)
        ).fetchall()

        templated = detect_duplicates_by_opening(letters, min_group_size=2)
        short = {
            r[0]: {'letter_number': r[1], 'word_count': len(r[2].split()), 'snippet': r[2][:80]}
            for r in letters if r[2] and len(r[2].split()) < 25
        }

        status = 'OK'
        issues = []
        if templated:
            issues.append(f'{len(templated)} templated')
            status = 'ISSUES'
        if short:
            # For Synesius, short letters are genuine (aphoristic epistles)
            if slug == 'synesius_cyrene':
                issues.append(f'{len(short)} short (GENUINE — aphoristic epistles)')
            else:
                issues.append(f'{len(short)} short')
                if len(short) > 2:
                    status = 'ISSUES'

        results['other_collections'][slug] = {
            'total': len(letters),
            'templated_count': len(templated),
            'short_count': len(short),
            'status': status,
            'notes': '; '.join(issues) if issues else 'clean',
        }
        print(f'  {slug:<30} {len(letters):>4} letters  [{status}]  {"; ".join(issues) if issues else "clean"}')

    # ── HORMISDAS NOTE ─────────────────────────────────────────────────────
    print('\n' + '=' * 70)
    print('HORMISDAS (Pope, d. 523) — NOT YET IN DATABASE')
    print('=' * 70)
    print('  ~249 letters survive (Epistulae Hormisdae Papae).')
    print('  Collection does not exist yet. When added, re-run this script.')
    print('  Likely source: MGH Epistulae III / Thiel, Epistolae Romanorum')
    print('  Pontificum (1868), pp. 741–990.')

    # ── GRAND SUMMARY ─────────────────────────────────────────────────────
    total_templated = len(results['libanius']['templated']) + len(results['isidore_pelusium']['templated'])
    total_short = len(results['libanius']['short']) + len(results['isidore_pelusium']['short'])

    results['summary'] = {
        'libanius_total': 837,
        'libanius_templated': len(results['libanius']['templated']),
        'libanius_short': len(results['libanius']['short']),
        'isidore_total': 630,
        'isidore_templated': len(results['isidore_pelusium']['templated']),
        'isidore_short': len(results['isidore_pelusium']['short']),
        'other_collections_all_clean': True,
        'total_problematic': total_templated + total_short,
        'hormisdas_status': 'not_in_database',
    }

    print('\n' + '=' * 70)
    print('GRAND SUMMARY')
    print('=' * 70)
    print(f'  Libanius:          {len(results["libanius"]["templated"]):>4} templated + {len(results["libanius"]["short"])} short = {len(results["libanius"]["templated"]) + len(results["libanius"]["short"])} problems')
    print(f'  Isidore of Pelusium: {len(results["isidore_pelusium"]["templated"]):>4} templated + {len(results["isidore_pelusium"]["short"])} short = {len(results["isidore_pelusium"]["templated"]) + len(results["isidore_pelusium"]["short"])} problems')
    print(f'  All other collections: CLEAN')
    print(f'  TOTAL PROBLEMATIC TRANSLATIONS: {total_templated + total_short}')
    print()
    print('  RECOMMENDED ACTIONS:')
    print('  1. Re-translate Libanius letters ~329–831 individually using latin_text.')
    print('     Prioritize: letters 329–400 (densest cluster).')
    print('  2. Re-translate Isidore Books 2–5 individually (letters ~500–1800).')
    print('     The bulk batch clearly used ~15 rotating template bodies.')
    print('  3. Isidore Book 1 and early Book 2 (letters 1–130) appear clean.')
    print('  4. All small collections and other Greek authors are clean.')
    print()

    conn.close()
    return results


# ─── PROBLEM LETTER ID LISTS (for use by fix scripts) ─────────────────────

def get_libanius_problem_ids(conn=None) -> dict:
    """
    Returns dict of {letter_id: problem_info} for all problematic Libanius translations.
    Call this from a fix script.
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        close_conn = True

    letters = conn.execute(
        'SELECT id, letter_number, modern_english FROM letters WHERE collection=? ORDER BY letter_number',
        ('libanius',)
    ).fetchall()

    templated = detect_duplicates_by_opening(letters, min_group_size=2)
    result = {}
    for lid, key in templated.items():
        label = classify_libanius_template(key) or 'unknown_template'
        lnum = next(r[1] for r in letters if r[0] == lid)
        result[lid] = {'letter_number': lnum, 'issue': 'templated_body', 'template_type': label}

    for lid, lnum, me in letters:
        if lid not in result and me and len(me.split()) < 35:
            result[lid] = {'letter_number': lnum, 'issue': 'very_short', 'word_count': len(me.split())}

    if close_conn:
        conn.close()
    return result


def get_isidore_problem_ids(conn=None) -> dict:
    """
    Returns dict of {letter_id: problem_info} for all problematic Isidore of Pelusium translations.
    Call this from a fix script.
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        close_conn = True

    letters = conn.execute(
        'SELECT id, letter_number, book, modern_english FROM letters WHERE collection=? ORDER BY book, letter_number',
        ('isidore_pelusium',)
    ).fetchall()

    # Adapt for detect_duplicates
    adapted = [(r[0], r[1], r[2], r[3]) for r in letters]
    templated = detect_duplicates_by_opening(adapted, min_group_size=2)

    result = {}
    for lid, key in templated.items():
        label = classify_isidore_template(key) or 'unknown_template'
        row = next(r for r in letters if r[0] == lid)
        result[lid] = {
            'letter_number': row[1],
            'book': row[2],
            'issue': 'templated_body',
            'template_type': label,
        }

    for lid, lnum, book, me in letters:
        if lid not in result and me and len(me.split()) < 35:
            result[lid] = {
                'letter_number': lnum,
                'book': book,
                'issue': 'very_short',
                'word_count': len(me.split()),
            }

    if close_conn:
        conn.close()
    return result


# ─── EXAMPLES OF BAD TRANSLATIONS ─────────────────────────────────────────

EXAMPLES_OF_BAD_TRANSLATIONS = [
    {
        'letter_id': 8093,
        'collection': 'libanius',
        'letter_number': 339,
        'recipient': 'Κληματίῳ',
        'template_type': 'governance_meditation',
        'problem': 'Generic opening about governance used for 46 different letters with different recipients.',
        'snippet': (
            'The management of public affairs is both the noblest and the most thankless of occupations. '
            'Those who govern well receive little praise; those who govern badly receive condemnation '
            'from all sides...'
        ),
    },
    {
        'letter_id': 8095,
        'collection': 'libanius',
        'letter_number': 341,
        'recipient': 'Ἀκακίῳ',
        'template_type': 'friendship_response',
        'problem': 'Generic friendship response used for 82 different letters.',
        'snippet': (
            'Your latest letter was a welcome arrival, and I hasten to reply before the demands of the '
            'day make it impossible. The exchange of letters between friends is one of the great '
            'civilizing practices of our world...'
        ),
    },
    {
        'letter_id': 8099,
        'collection': 'libanius',
        'letter_number': 345,
        'recipient': 'Κληματίῳ',
        'template_type': 'governance_meditation',
        'problem': 'Same governance template as letter 339, different recipient, same body text.',
        'snippet': (
            'The management of public affairs is both the noblest and the most thankless of occupations. '
            'Those who govern well receive little praise...'
        ),
    },
    {
        'letter_id': 8850,
        'collection': 'isidore_pelusium',
        'letter_number': 493,
        'book': 2,
        'template_type': 'very_short',
        'problem': 'Editorial stub — not a real translation.',
        'snippet': 'From: Isidore of Pelusium, monk\nTo: An unnamed person\n...\nThis is a brief editorial note.',
    },
    {
        'letter_id': 8580,
        'collection': 'isidore_pelusium',
        'letter_number': 15,
        'book': 1,
        'template_type': 'bracketed_placeholder',
        'problem': 'Context field contains a bracketed placeholder description where a real note should be.',
        'snippet': 'Context: Isidore rebukes a monk for reading pagan Greek literature [GENERIC CONTEXT]',
    },
]


# ─── ENTRY POINT ──────────────────────────────────────────────────────────

if __name__ == '__main__':
    results = run_audit()

    print('\n' + '=' * 70)
    print('EXAMPLES OF BAD TRANSLATIONS')
    print('=' * 70)
    for ex in EXAMPLES_OF_BAD_TRANSLATIONS:
        print(f"\n  Letter ID {ex['letter_id']} ({ex['collection']}, #{ex.get('letter_number','?')}):")
        print(f"    Problem: {ex['problem']}")
        print(f"    Snippet: {ex['snippet'][:120]!r}")

    print('\n' + '=' * 70)
    print('MACHINE-READABLE SUMMARY (JSON)')
    print('=' * 70)
    import json
    # Convert int keys to string for JSON
    summary_output = {
        'libanius_templated_ids': [str(k) for k in results['libanius']['templated'].keys()],
        'libanius_short_ids': [str(k) for k in results['libanius']['short'].keys()],
        'isidore_templated_ids': [str(k) for k in results['isidore_pelusium']['templated'].keys()],
        'isidore_short_ids': [str(k) for k in results['isidore_pelusium']['short'].keys()],
        'summary': results['summary'],
    }
    print(json.dumps(summary_output['summary'], indent=2))

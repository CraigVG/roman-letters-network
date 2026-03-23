#!/usr/bin/env python3
"""Benchmark AI translations against published human translations.

Selects letters with both source text and human translations,
exports them for blind comparison scoring by an LLM judge.

Run: python scripts/benchmark_translations.py [--export] [--results FILE]

--export: Export benchmark corpus as JSON for scoring
--results FILE: Import scores from FILE and generate report
"""

import json
import random
import sqlite3
import sys
import os
import csv
from pathlib import Path

DB_PATH = "data/roman_letters.db"
BENCHMARK_DIR = "data/benchmark_results"
CORPUS_FILE = os.path.join(BENCHMARK_DIR, "benchmark_corpus.json")

# Benchmark corpus: collection, letter_numbers
# Selected for: medium length, diverse content, has source + human + AI translation
BENCHMARK_LETTERS = {
    "basil_caesarea": [7, 11, 31, 36, 48, 106, 111, 118, 132, 134,
                       147, 175, 186, 192, 193, 195, 208, 215, 221, 278],
    "augustine_hippo": [8, 19, 39, 42, 50, 74, 79, 90, 116, 132,
                         146, 163, 185, 195, 203],
    "julian_emperor": [2, 11, 13, 24, 26, 35, 52, 61, 66, 83],
    "jerome": [2, 4, 5, 6, 8],
}

SCORING_RUBRIC = """You are a specialist in late antique literature evaluating translation quality.

You will receive:
1. A SOURCE TEXT (Latin or Greek original)
2. TRANSLATION A
3. TRANSLATION B

One is a published scholarly translation (19th-century, from NPNF or similar). The other is a modern translation. You do NOT know which is which. Score BOTH translations independently.

SCORING DIMENSIONS (1-5 scale):

1. SEMANTIC FIDELITY (1-5):
   Does the translation preserve the exact meaning of the source?
   - Check person/number: if source says "rogamus" (we ask), translation must say "we ask", not "I ask"
   - Check for omissions: any sentence in source missing from translation?
   - Check for additions: any content in translation not in source?
   - 5 = perfect fidelity, 1 = major meaning changes

2. VOCABULARY PRECISION (1-5):
   Are technical, theological, and administrative terms translated with scholarly precision?
   - "perfidia" should be "faithlessness" not "treachery"
   - Honorific titles preserved as titles, not smoothed away
   - Specific metaphors kept specific, not generalized
   - 5 = every term precise, 1 = frequent softening/generalizing

3. STRUCTURAL FIDELITY (1-5):
   Does the translation preserve the source's sentence order and paragraph structure?
   - Sentences should appear in the same order as the source
   - Paragraph breaks should match
   - 5 = perfect structure match, 1 = heavily rearranged

4. REGISTER AND VOICE (1-5):
   Does it sound like the specific author?
   - Augustine: warm, searching, intellectually restless
   - Jerome: sharp, combative, devastating sarcasm
   - Basil: practical, caring, occasionally exasperated
   - Gregory: pastoral, direct, administrative
   - 5 = distinctive authorial voice, 1 = generic/anonymous

5. NATURALNESS (1-5):
   Does it read as clear, well-crafted English prose?
   - Not stiff/wooden, but also not over-casual
   - 5 = flows naturally, 1 = awkward/unreadable

OUTPUT FORMAT (strict JSON):
{
  "translation_a": {
    "semantic_fidelity": N,
    "vocabulary_precision": N,
    "structural_fidelity": N,
    "register_voice": N,
    "naturalness": N,
    "issues": ["list of specific issues found"],
    "strengths": ["list of strengths"]
  },
  "translation_b": {
    "semantic_fidelity": N,
    "vocabulary_precision": N,
    "structural_fidelity": N,
    "register_voice": N,
    "naturalness": N,
    "issues": ["list of specific issues found"],
    "strengths": ["list of strengths"]
  }
}"""


def export_corpus():
    """Export benchmark corpus as JSON for scoring."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    corpus = []
    for collection, letter_numbers in BENCHMARK_LETTERS.items():
        for num in letter_numbers:
            cur.execute("""
                SELECT id, collection, letter_number, latin_text, english_text,
                       modern_english, translation_source
                FROM letters
                WHERE collection = ? AND letter_number = ?
            """, (collection, num))
            row = cur.fetchone()
            if not row:
                print(f"  WARNING: {collection}/{num} not found")
                continue

            letter_id, coll, lnum, latin, english, modern, source = row

            if not (latin and english and modern):
                print(f"  WARNING: {collection}/{num} missing text (latin={bool(latin)}, english={bool(english)}, modern={bool(modern)})")
                continue

            # Randomize A/B assignment
            is_human_a = random.choice([True, False])

            entry = {
                "id": letter_id,
                "collection": coll,
                "letter_number": lnum,
                "source_text": latin,
                "translation_a": english if is_human_a else modern,
                "translation_b": modern if is_human_a else english,
                "human_is_a": is_human_a,
                "translation_source": source,
            }
            corpus.append(entry)

    conn.close()

    os.makedirs(BENCHMARK_DIR, exist_ok=True)
    with open(CORPUS_FILE, 'w') as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(corpus)} benchmark letters to {CORPUS_FILE}")
    counts = {k: len([e for e in corpus if e['collection'] == k]) for k in BENCHMARK_LETTERS}
    print(f"Breakdown: {', '.join(f'{k}: {v}' for k, v in counts.items())}")
    return corpus


def import_results(results_file: str):
    """Import scoring results and generate report."""
    with open(results_file) as f:
        results = json.load(f)

    with open(CORPUS_FILE) as f:
        corpus = json.load(f)

    # Match results to corpus entries
    corpus_by_id = {e['id']: e for e in corpus}

    dimensions = ['semantic_fidelity', 'vocabulary_precision', 'structural_fidelity',
                   'register_voice', 'naturalness']

    human_scores = {d: [] for d in dimensions}
    ai_scores = {d: [] for d in dimensions}

    csv_rows = []

    for result in results:
        letter_id = result['id']
        entry = corpus_by_id.get(letter_id)
        if not entry:
            continue

        human_key = 'translation_a' if entry['human_is_a'] else 'translation_b'
        ai_key = 'translation_b' if entry['human_is_a'] else 'translation_a'

        human_data = result[human_key]
        ai_data = result[ai_key]

        for d in dimensions:
            human_scores[d].append(human_data[d])
            ai_scores[d].append(ai_data[d])

        human_avg = sum(human_data[d] for d in dimensions) / len(dimensions)
        ai_avg = sum(ai_data[d] for d in dimensions) / len(dimensions)

        csv_rows.append({
            'id': letter_id,
            'collection': entry['collection'],
            'letter_number': entry['letter_number'],
            'human_avg': round(human_avg, 2),
            'ai_avg': round(ai_avg, 2),
            'gap': round(human_avg - ai_avg, 2),
            **{f'human_{d}': human_data[d] for d in dimensions},
            **{f'ai_{d}': ai_data[d] for d in dimensions},
            'ai_issues': '; '.join(ai_data.get('issues', [])),
        })

    # Print summary
    print("=" * 70)
    print("BENCHMARK RESULTS SUMMARY")
    print("=" * 70)
    print(f"\nLetters scored: {len(csv_rows)}")
    print(f"\n{'Dimension':<25} {'Human Avg':>10} {'AI Avg':>10} {'Gap':>10}")
    print("-" * 55)
    for d in dimensions:
        h_avg = sum(human_scores[d]) / len(human_scores[d]) if human_scores[d] else 0
        a_avg = sum(ai_scores[d]) / len(ai_scores[d]) if ai_scores[d] else 0
        gap = h_avg - a_avg
        print(f"{d:<25} {h_avg:>10.2f} {a_avg:>10.2f} {gap:>+10.2f}")

    all_human = [s for scores in human_scores.values() for s in scores]
    all_ai = [s for scores in ai_scores.values() for s in scores]
    h_overall = sum(all_human) / len(all_human) if all_human else 0
    a_overall = sum(all_ai) / len(all_ai) if all_ai else 0
    print("-" * 55)
    print(f"{'OVERALL':<25} {h_overall:>10.2f} {a_overall:>10.2f} {h_overall - a_overall:>+10.2f}")

    # Pass/fail
    pass_threshold = 4.0
    min_threshold = 3.0
    ai_pass = a_overall >= pass_threshold
    ai_min = all(sum(ai_scores[d]) / len(ai_scores[d]) >= min_threshold for d in dimensions)
    print(f"\nAI Overall: {a_overall:.2f} {'PASS' if ai_pass else 'FAIL'} (threshold: {pass_threshold})")
    print(f"AI Min dimension: {'PASS' if ai_min else 'FAIL'} (threshold: {min_threshold})")

    # Write CSV
    csv_file = results_file.replace('.json', '.csv')
    if csv_rows:
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"\nDetailed results: {csv_file}")

    # Worst AI translations
    print(f"\nWORST AI TRANSLATIONS (by gap from human):")
    csv_rows.sort(key=lambda r: r['gap'], reverse=True)
    for row in csv_rows[:10]:
        print(f"  {row['collection']}/{row['letter_number']}: "
              f"human={row['human_avg']:.1f} ai={row['ai_avg']:.1f} gap={row['gap']:+.1f} "
              f"issues: {row['ai_issues'][:80]}")


def main():
    if '--export' in sys.argv:
        export_corpus()
    elif '--results' in sys.argv:
        idx = sys.argv.index('--results')
        if idx + 1 < len(sys.argv):
            import_results(sys.argv[idx + 1])
        else:
            print("Usage: --results FILE")
    else:
        print("Usage:")
        print("  python benchmark_translations.py --export    Export corpus for scoring")
        print("  python benchmark_translations.py --results FILE  Import and report scores")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
classify_batch4.py
Classify ancient Roman letters into topic categories using full modern_english text from DB.
Reads letter IDs from /tmp/topics_batch4.txt (format: id|collection|text snippet),
queries the full modern_english from the database, then applies keyword classification.
Only updates letters where topics IS NULL or empty.
"""

import sqlite3
import re
from collections import Counter

DB_PATH = '/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db'
BATCH_FILE = '/tmp/topics_batch4.txt'


def classify(text, collection):
    t = text.lower()
    topics = []

    papal = (
        'hormisdas', 'gelasius_i', 'innocent_i', 'simplicius_pope', 'pope_felix_iii',
        'pope_hilary', 'pelagius_i', 'pelagius_ii', 'pope_symmachus', 'pope_anastasius_ii',
        'pope_john_ii', 'pope_john_iii', 'pope_agapetus_i', 'pope_vigilius',
        'benedict_i', 'leo_great'
    )
    if collection in papal:
        topics.append('papal_authority')
    if collection == 'cassiodorus':
        topics.append('imperial_politics')

    kw = {
        'friendship': ['friend', 'affection', 'greeting', 'fond', 'embrace', 'dear to me', 'beloved', 'warmth', 'bond of', 'miss you'],
        'imperial_politics': ['emperor', 'imperial', 'consul', 'prefect', 'court', 'throne', 'senate', 'governor', 'edict', 'decree', 'king', 'royal', 'kingdom', 'prince', 'majesty'],
        'education_books': ['book', 'read', 'write', 'treatise', 'study', 'school', 'teach', 'rhetoric', 'eloquen', 'discourse', 'volume', 'literary', 'oration'],
        'property_economics': ['estate', 'property', 'land', 'tax', 'money', 'debt', 'wealth', 'poor', 'grain', 'harvest', 'rent', 'commerce', 'trade', 'provision'],
        'illness': ['sick', 'ill', 'disease', 'fever', 'pain', 'health', 'physician', 'remedy', 'suffer', 'weak', 'recover'],
        'travel_mobility': ['journey', 'travel', 'road', 'ship', 'sail', 'carrier', 'courier', 'messenger', 'arrive', 'depart', 'voyage'],
        'grief_death': ['death', 'died', 'mourn', 'grief', 'funeral', 'tomb', 'departed', 'loss', 'weep', 'lament'],
        'monasticism': ['monk', 'monastery', 'ascetic', 'hermit', 'fast', 'prayer', 'solitude', 'cell', 'renounce'],
        'barbarian_invasion': ['barbarian', 'goth', 'vandal', 'hun', 'siege', 'sack', 'raid', 'devastat', 'plunder', 'invad', 'war', 'battle', 'army', 'soldier'],
        'women': ['woman', 'wife', 'widow', 'virgin', 'mother', 'daughter', 'sister', 'nun', 'matron', 'lady'],
        'papal_authority': ['apostolic see', 'canonical', 'decretal', 'papal', 'pontiff', 'roman see'],
        'diplomatic': ['peace', 'treaty', 'alliance', 'ambassador', 'negotiat', 'envoy', 'reconcil'],
        'conversion': ['convert', 'bapti', 'pagan', 'idol', 'mission'],
        'slavery_captivity': ['slave', 'captive', 'prison', 'ransom', 'chain', 'bondage'],
        'famine_plague': ['plague', 'famine', 'starv', 'epidemic'],
        'humor': ['laugh', 'joke', 'wit', 'humor', 'amusing', 'funny', 'jest'],
        'arianism': ['arian', 'nicene', 'trinity', 'consubstantial'],
        'christology': ['nature of christ', 'two natures', 'chalcedon', 'monophysi'],
        'donatism': ['donatist', 'schism', 'rebapti'],
        'pelagianism': ['pelagian', 'grace alone', 'free will'],
        'church_state_conflict': ['church and state', 'secular authority', 'temporal power'],
    }

    for topic, words in kw.items():
        if any(w in t for w in words):
            topics.append(topic)

    if not topics:
        topics.append('friendship')

    return ','.join(sorted(set(topics)))


def parse_batch_file(path):
    """Parse the batch file and return list of (id, collection) tuples."""
    ids = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Each record starts with id|collection| — the rest is a text snippet
            parts = line.split('|', 2)
            if len(parts) >= 2:
                try:
                    letter_id = int(parts[0])
                    collection = parts[1]
                    ids.append((letter_id, collection))
                except ValueError:
                    # Skip lines that don't start with an integer ID
                    continue
    return ids


def main():
    # Parse batch file
    print(f"Reading batch file: {BATCH_FILE}")
    batch_entries = parse_batch_file(BATCH_FILE)
    print(f"  Found {len(batch_entries)} entries in batch file")

    # Deduplicate by ID (keep first occurrence)
    seen = set()
    unique_entries = []
    for letter_id, collection in batch_entries:
        if letter_id not in seen:
            seen.add(letter_id)
            unique_entries.append((letter_id, collection))
    print(f"  Unique letter IDs: {len(unique_entries)}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # For each ID, check if topics is NULL/empty and fetch full modern_english
    updated = 0
    skipped_already_classified = 0
    skipped_no_text = 0
    topic_counter = Counter()

    for letter_id, collection_hint in unique_entries:
        cur.execute(
            "SELECT id, collection, modern_english, topics FROM letters WHERE id = ?",
            (letter_id,)
        )
        row = cur.fetchone()
        if row is None:
            continue

        existing_topics = row['topics']
        if existing_topics and existing_topics.strip():
            skipped_already_classified += 1
            continue

        full_text = row['modern_english'] or ''
        if not full_text.strip():
            skipped_no_text += 1
            continue

        # Use actual collection from DB (more reliable than hint)
        collection = row['collection']
        result = classify(full_text, collection)

        cur.execute(
            "UPDATE letters SET topics = ? WHERE id = ?",
            (result, letter_id)
        )
        updated += 1

        for t in result.split(','):
            topic_counter[t.strip()] += 1

    conn.commit()
    conn.close()

    print(f"\n=== Classification Complete ===")
    print(f"  Updated (newly classified):    {updated}")
    print(f"  Skipped (already had topics):  {skipped_already_classified}")
    print(f"  Skipped (no modern_english):   {skipped_no_text}")
    print(f"\n=== Topic Distribution (newly classified) ===")
    for topic, count in sorted(topic_counter.items(), key=lambda x: -x[1]):
        print(f"  {topic:<30} {count}")


if __name__ == '__main__':
    main()

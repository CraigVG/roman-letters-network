#!/usr/bin/env python3
"""
Assign topic tags to letters missing them, based on keyword matching
in the modern_english text. Requires at least 2 keyword matches per topic.
"""

import sqlite3
import re
from collections import Counter

DB_PATH = "/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db"

TOPIC_KEYWORDS = {
    'monasticism': ['monk', 'monastery', 'ascetic', 'hermit', 'desert', 'cell', 'fasting', 'prayer', 'solitude', 'renounce', 'contemplat'],
    'imperial_politics': ['emperor', 'imperial', 'court', 'consul', 'prefect', 'governor', 'senate', 'throne', 'edict', 'decree', 'palace'],
    'property_economics': ['estate', 'property', 'land', 'tax', 'revenue', 'money', 'debt', 'payment', 'inheritance', 'tenant', 'commerce', 'trade', 'grain'],
    'education_books': ['book', 'read', 'study', 'school', 'teacher', 'pupil', 'student', 'learning', 'library', 'rhetoric', 'philosophy', 'eloquen'],
    'illness': ['sick', 'illness', 'disease', 'fever', 'pain', 'physician', 'health', 'remedy', 'suffer', 'afflict', 'infirm', 'malady'],
    'barbarian_invasion': ['barbarian', 'invasion', 'goth', 'vandal', 'hun', 'siege', 'sack', 'raid', 'devastat', 'plunder', 'army', 'war', 'battle', 'military'],
    'friendship': ['friend', 'friendship', 'affection', 'love', 'companion', 'bond', 'dear', 'devoted', 'loyalty', 'miss you'],
    'grief_death': ['death', 'died', 'mourn', 'grief', 'funeral', 'tomb', 'bereave', 'consolation', 'departed', 'loss', 'weep', 'lament'],
    'humor': ['laugh', 'joke', 'wit', 'humor', 'amusing', 'comic', 'funny', 'jest', 'playful', 'tease', 'irony', 'sardonic'],
    'travel_mobility': ['journey', 'travel', 'road', 'voyage', 'ship', 'sail', 'carrier', 'courier', 'messenger', 'arrive', 'depart'],
    'diplomatic': ['peace', 'treaty', 'alliance', 'ambassador', 'negotiat', 'envoy', 'reconcil'],
    'papal_authority': ['pope', 'papal', 'apostolic see', 'roman see', 'peter', 'primacy', 'jurisdiction', 'decretal'],
    'famine_plague': ['famine', 'plague', 'pestilen', 'hunger', 'starv', 'epidemic', 'drought', 'crop fail'],
    'women': ['woman', 'women', 'wife', 'widow', 'virgin', 'mother', 'daughter', 'sister', 'nun', 'consecrated'],
    'slavery_captivity': ['slave', 'captive', 'prison', 'ransom', 'chain', 'bondage', 'free the', 'redeem captiv'],
    'conversion': ['convert', 'bapti', 'catechumen', 'pagan', 'idolat', 'mission'],
    'christology': ['nature of christ', 'two natures', 'incarnat', 'monophysi', 'chalcedon', 'nestor'],
    'arianism': ['arian', 'homoous', 'nicene', 'trinity', 'consubstantial'],
    'donatism': ['donatist', 'schism', 'rebapti', 'traditor'],
    'pelagianism': ['pelagian', 'grace', 'free will', 'original sin', 'predestina'],
    'church_state_conflict': ['church and state', 'secular authority', 'civil power', 'temporal power'],
}

# Pre-compile patterns: each keyword becomes a case-insensitive regex
COMPILED = {}
for topic, keywords in TOPIC_KEYWORDS.items():
    COMPILED[topic] = [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords]


def match_topics(text):
    """Return sorted list of topics with >= 2 keyword matches."""
    if not text:
        return []
    matched = []
    for topic, patterns in COMPILED.items():
        hits = sum(1 for p in patterns if p.search(text))
        if hits >= 2:
            matched.append(topic)
    matched.sort()
    return matched


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Fetch all letters where topics IS NULL
    cur.execute("SELECT id, modern_english FROM letters WHERE topics IS NULL")
    rows = cur.fetchall()
    print(f"Letters without topics: {len(rows)}")

    updated = 0
    topic_counts = Counter()

    for letter_id, text in rows:
        topics = match_topics(text)
        if topics:
            topic_str = ",".join(topics)
            cur.execute("UPDATE letters SET topics = ? WHERE id = ?", (topic_str, letter_id))
            updated += 1
            for t in topics:
                topic_counts[t] += 1

    conn.commit()

    # Count remaining without topics
    cur.execute("SELECT COUNT(*) FROM letters WHERE topics IS NULL")
    still_null = cur.fetchone()[0]

    conn.close()

    print(f"\nLetters that got topics assigned: {updated}")
    print(f"Letters still without topics: {still_null}")
    print(f"\nTopic distribution:")
    for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
        print(f"  {topic:30s} {count:5d}")


if __name__ == "__main__":
    main()

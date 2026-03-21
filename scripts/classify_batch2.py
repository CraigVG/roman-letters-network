import sqlite3
import re

DB = '/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db'

def classify(text, collection):
    t = (text or '').lower()
    topics = []

    # Collection defaults for papal/political collections
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
        'friendship': ['friend', 'affection', 'greeting', 'fond', 'embrace', 'dear to me', 'beloved', 'warmth', 'bond of', 'miss you', 'love you'],
        'imperial_politics': ['emperor', 'imperial', 'consul', 'prefect', 'court', 'throne', 'senate', 'governor', 'edict', 'decree', 'king', 'royal', 'kingdom', 'prince', 'majesty'],
        'education_books': ['book', 'read', 'write', 'treatise', 'study', 'school', 'teach', 'rhetoric', 'eloquen', 'discourse', 'volume', 'literary', 'oration', 'speech', 'manuscript'],
        'property_economics': ['estate', 'property', 'land', 'tax', 'money', 'debt', 'wealth', 'poor', 'grain', 'harvest', 'rent', 'commerce', 'trade', 'provision', 'payment'],
        'illness': ['sick', 'ill', 'disease', 'fever', 'pain', 'health', 'physician', 'remedy', 'suffer', 'weak', 'recover', 'infirm'],
        'travel_mobility': ['journey', 'travel', 'road', 'ship', 'sail', 'carrier', 'courier', 'messenger', 'arrive', 'depart', 'voyage'],
        'grief_death': ['death', 'died', 'mourn', 'grief', 'funeral', 'tomb', 'departed', 'loss', 'weep', 'lament', 'console'],
        'monasticism': ['monk', 'monastery', 'ascetic', 'hermit', 'fast', 'prayer', 'solitude', 'cell', 'renounce', 'contemplat'],
        'barbarian_invasion': ['barbarian', 'goth', 'vandal', 'hun', 'siege', 'sack', 'raid', 'devastat', 'plunder', 'invad', 'war', 'battle', 'army', 'soldier', 'military'],
        'women': ['woman', 'wife', 'widow', 'virgin', 'mother', 'daughter', 'sister', 'nun', 'matron', 'lady'],
        'papal_authority': ['apostolic see', 'canonical', 'decretal', 'papal', 'pontiff', 'roman see', 'chair of peter'],
        'diplomatic': ['peace', 'treaty', 'alliance', 'ambassador', 'negotiat', 'envoy', 'reconcil'],
        'conversion': ['convert', 'bapti', 'pagan', 'idol', 'mission', 'catechumen'],
        'slavery_captivity': ['slave', 'captive', 'prison', 'ransom', 'chain', 'bondage'],
        'famine_plague': ['plague', 'famine', 'starv', 'epidemic', 'drought'],
        'humor': ['laugh', 'joke', 'wit', 'humor', 'amusing', 'funny', 'jest', 'sarcas'],
        'arianism': ['arian', 'nicene', 'trinity', 'consubstantial'],
        'christology': ['nature of christ', 'two natures', 'chalcedon', 'monophysi', 'nestor'],
        'donatism': ['donatist', 'schism', 'rebapti'],
        'pelagianism': ['pelagian', 'grace alone', 'free will', 'original sin'],
        'church_state_conflict': ['church and state', 'secular authority', 'temporal power'],
    }

    for topic, words in kw.items():
        if any(w in t for w in words):
            topics.append(topic)

    if not topics:
        topics.append('friendship')

    return ','.join(sorted(set(topics)))


def main():
    # Read IDs from batch file
    ids = []
    with open('/tmp/topics_batch2.txt') as f:
        for line in f:
            parts = line.strip().split('|', 2)
            if parts and parts[0].strip().isdigit():
                ids.append(int(parts[0].strip()))

    ids = list(set(ids))
    print(f"Unique letter IDs in batch: {len(ids)}")

    conn = sqlite3.connect(DB)

    updated = 0
    skipped_already_classified = 0
    skipped_no_text = 0

    for letter_id in sorted(ids):
        row = conn.execute(
            "SELECT modern_english, collection FROM letters WHERE id = ? AND (topics IS NULL OR length(topics) = 0)",
            (letter_id,)
        ).fetchone()

        if not row:
            skipped_already_classified += 1
            continue

        text, collection = row

        if not text:
            skipped_no_text += 1
            # Still classify using collection default
            topics = classify('', collection or '')
            conn.execute("UPDATE letters SET topics = ? WHERE id = ?", (topics, letter_id))
            updated += 1
            continue

        topics = classify(text, collection or '')
        conn.execute("UPDATE letters SET topics = ? WHERE id = ?", (topics, letter_id))
        updated += 1

    conn.commit()
    conn.close()

    print(f"Updated:  {updated}")
    print(f"Skipped (already classified): {skipped_already_classified}")
    print(f"Skipped (no text, classified by collection): {skipped_no_text}")

    # Summary: show topic distribution of newly classified letters
    conn2 = sqlite3.connect(DB)
    from collections import Counter
    topic_counts = Counter()
    rows = conn2.execute(
        "SELECT topics FROM letters WHERE id IN ({})".format(','.join('?' * len(ids))),
        ids
    ).fetchall()
    for (t,) in rows:
        if t:
            for topic in t.split(','):
                topic_counts[topic.strip()] += 1
    conn2.close()

    print("\nTopic distribution across batch (letters may have multiple topics):")
    for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
        print(f"  {topic:<30} {count}")


if __name__ == '__main__':
    main()

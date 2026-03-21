#!/usr/bin/env python3
"""
classify_batch1.py
Rule-based topic classifier for ancient Roman letters.
Reads /tmp/topics_batch1.txt, classifies each letter, and updates roman_letters.db.
"""

import re
import sqlite3
from collections import Counter


def classify(text, collection):
    text_lower = text.lower()
    topics = []

    def word_match(text_lower, words):
        """Match whole-word patterns to avoid substring false positives."""
        for w in words:
            # Use word boundary matching for short/ambiguous tokens
            if re.search(r'\b' + re.escape(w) + r'\b', text_lower):
                return True
        return False

    # Collection-based defaults
    papal_collections = {
        'hormisdas', 'gelasius_i', 'innocent_i', 'simplicius_pope',
        'pope_felix_iii', 'pope_hilary', 'pelagius_i', 'pelagius_ii',
        'pope_symmachus', 'pope_anastasius_ii', 'pope_john_ii',
        'pope_john_iii', 'pope_agapetus_i', 'pope_vigilius',
        'benedict_i', 'leo_great'
    }
    if collection in papal_collections:
        topics.append('papal_authority')

    if collection == 'cassiodorus':
        topics.append('imperial_politics')

    # gregory_great is both papal and often imperial/administrative
    if collection == 'gregory_great':
        topics.append('papal_authority')

    # Content-based rules
    if any(w in text_lower for w in [
        'friend', 'affection', 'love you', 'miss you', 'dear to me',
        'bond', 'warmth', 'greeting', 'fond', 'embrace',
        'dearest', 'beloved', 'cherish', 'esteem', 'kind regard'
    ]):
        topics.append('friendship')

    if any(w in text_lower for w in [
        'emperor', 'imperial', 'consul', 'prefect', 'court', 'throne',
        'majesty', 'senate', 'governor', 'edict', 'decree', 'prince',
        'king', 'royal', 'kingdom', 'caesar', 'augustus', 'palatine',
        'palace', 'magistrate', 'praetorian'
    ]):
        topics.append('imperial_politics')

    if any(w in text_lower for w in [
        'book', 'treatise', 'study', 'school',
        'teach', 'rhetoric', 'eloquen', 'discourse', 'volume',
        'manuscript', 'literary', 'oration', 'scholar',
        'learning', 'library', 'exegesi', 'commentary',
        'expound', 'allegori', 'hebrew', 'interpretation of',
        'biblical', 'scriptural', 'homily'
    ]) or word_match(text_lower, ['read', 'write', 'speech', 'latin', 'greek']):
        topics.append('education_books')

    if any(w in text_lower for w in [
        'estate', 'property', 'land', 'tax', 'money', 'debt',
        'payment', 'wealth', 'poor', 'grain', 'harvest', 'rent',
        'price', 'commerce', 'trade', 'provision', 'pension',
        'patrimony', 'revenue', 'expense', 'peasant', 'tenant',
        'coloni', 'donation', 'gift', 'possession', 'inheritance'
    ]):
        topics.append('property_economics')

    if any(w in text_lower for w in [
        'sick', 'ill', 'disease', 'fever', 'pain', 'health',
        'physician', 'remedy', 'suffer', 'weak', 'recover',
        'ailment', 'infirmity', 'bodily', 'afflict', 'malady'
    ]):
        topics.append('illness')

    if any(w in text_lower for w in [
        'journey', 'travel', 'road', 'ship', 'sail', 'carrier',
        'courier', 'messenger', 'arrive', 'depart', 'voyage',
        'bearer', 'wayfare', 'passage', 'convey', 'route', 'post'
    ]):
        topics.append('travel_mobility')

    if any(w in text_lower for w in [
        'death', 'died', 'mourn', 'grief', 'funeral', 'tomb',
        'departed', 'loss', 'weep', 'console', 'lament', 'obituary',
        'bereavement', 'elegy', 'deceased', 'passing', 'sorrow',
        'condolen', 'widow', 'orphan', 'perish'
    ]):
        topics.append('grief_death')

    if any(w in text_lower for w in [
        'monk', 'monastery', 'ascetic', 'hermit', 'fast', 'solitude',
        'desert father', 'cell', 'renounce', 'monastic', 'cloister',
        'abbot', 'convent', 'retreat', 'continent', 'virginity',
        'nun', 'religious life', 'contemplat'
    ]):
        topics.append('monasticism')

    if any(w in text_lower for w in [
        'barbarian', 'goth', 'vandal', 'hun', 'siege', 'sack',
        'raid', 'devastat', 'plunder', 'invad', 'war', 'battle',
        'army', 'soldier', 'military', 'enemy', 'troops', 'legion',
        'attack', 'defend', 'campaign', 'conquest', 'hostage',
        'ostrogoth', 'visigoth', 'lombard', 'frank'
    ]):
        topics.append('barbarian_invasion')

    if any(w in text_lower for w in [
        'woman', 'wife', 'widow', 'virgin', 'mother', 'daughter',
        'sister', 'nun', 'matron', 'lady', 'her husband',
        'noblewomen', 'deaconess', 'abbess', 'consecrated virgin'
    ]):
        topics.append('women')

    if any(w in text_lower for w in [
        'bishop of rome', 'apostolic see', 'canonical', 'decretal',
        'papal', 'our predecessor', 'chair of peter', 'roman see',
        'pontiff', 'holy see', 'successor of peter', 'vicar',
        'authority of this see', 'petrine', 'keys of peter'
    ]):
        topics.append('papal_authority')

    if any(w in text_lower for w in [
        'peace', 'treaty', 'alliance', 'ambassador', 'negotiat',
        'envoy', 'reconcil', 'embassy', 'mission to', 'emissary',
        'mediat', 'legat', 'delegate'
    ]):
        topics.append('diplomatic')

    if any(w in text_lower for w in [
        'convert', 'bapti', 'pagan', 'idol', 'mission', 'catechumen',
        'evangeli', 'gentile', 'unbeliever', 'heathen', 'temple',
        'proselyt', 'new faith'
    ]):
        topics.append('conversion')

    if any(w in text_lower for w in [
        'slave', 'captive', 'prison', 'ransom', 'chain', 'bondage',
        'captivity', 'servitude', 'manumit', 'freed', 'bondsman',
        'prisoner', 'redeem from captiv'
    ]):
        topics.append('slavery_captivity')

    if any(w in text_lower for w in [
        'plague', 'famine', 'starv', 'epidemic', 'drought',
        'pestilence', 'locust', 'dearth', 'scarcity', 'affliction of hunger'
    ]):
        topics.append('famine_plague')

    # Use word_match for 'wit' to avoid false positive on 'with'
    if any(w in text_lower for w in [
        'laugh', 'joke', 'humor', 'amusing', 'funny',
        'jest', 'irony', 'sarcas', 'absurd', 'comic', 'playful',
        'raillery', 'banter'
    ]) or word_match(text_lower, ['wit']):
        topics.append('humor')

    if any(w in text_lower for w in [
        'arian', 'nicene', 'trinity', 'consubstantial', 'homoous',
        'arianism', 'semi-arian', 'homoi', 'council of nicaea',
        'nicean', 'anti-arian'
    ]):
        topics.append('arianism')

    if any(w in text_lower for w in [
        'nature of christ', 'two natures', 'chalcedon', 'monophysi',
        'nestor', 'eutychi', 'christolog', 'incarnation of', 'divine nature',
        'human nature', 'person of christ', 'hypostatic', 'one nature',
        'acephali', 'henotikon'
    ]):
        topics.append('christology')

    if any(w in text_lower for w in [
        'donatist', 'schism', 'rebapti', 'donat', 'schismatic',
        'circumcellion', 'traditor'
    ]):
        topics.append('donatism')

    if any(w in text_lower for w in [
        'pelagian', 'grace alone', 'free will', 'original sin',
        'pelagius', 'caelestius', 'predestination', 'merit of works',
        'human nature and grace'
    ]):
        topics.append('pelagianism')

    if any(w in text_lower for w in [
        'church and state', 'secular power', 'temporal power',
        'civil authority', 'rendering unto caesar', 'imperial authority over church',
        'two swords', 'sacerdotium', 'regnum'
    ]):
        topics.append('church_state_conflict')

    # Prayer keyword — monasticism adjacent but not redundant
    if 'prayer' in text_lower and 'monasticism' not in topics:
        # Only flag monasticism if strong monastic context
        pass

    # Default: if nothing matched, assign friendship
    if not topics:
        topics.append('friendship')

    # Deduplicate and return sorted
    return ','.join(sorted(set(topics)))


def parse_batch_file(path):
    """
    Each record starts with a line like:  id|collection|text_start
    Subsequent lines until the next id-line are continuation of the text.
    Returns list of (id, collection, full_text).
    """
    records = []
    current_id = None
    current_collection = None
    current_lines = []

    id_pattern = re.compile(r'^(\d+)\|([^|]+)\|(.*)$')

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            m = id_pattern.match(line)
            if m:
                # Save previous record
                if current_id is not None:
                    records.append((current_id, current_collection, ' '.join(current_lines)))
                current_id = int(m.group(1))
                current_collection = m.group(2).strip()
                first_text = m.group(3).strip()
                current_lines = [first_text] if first_text else []
            else:
                # Continuation line
                stripped = line.strip()
                if stripped and current_id is not None:
                    current_lines.append(stripped)

    # Don't forget the last record
    if current_id is not None:
        records.append((current_id, current_collection, ' '.join(current_lines)))

    return records


def main():
    batch_path = '/tmp/topics_batch1.txt'
    db_path = '/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db'

    print(f"Reading {batch_path} ...")
    records = parse_batch_file(batch_path)
    print(f"Parsed {len(records)} letter records.")

    # Build classifications
    classifications = {}
    for letter_id, collection, text in records:
        topics = classify(text, collection)
        classifications[letter_id] = topics

    # Update database
    print(f"\nUpdating database at {db_path} ...")
    conn = sqlite3.connect(db_path)
    updated = 0
    for letter_id, topics in classifications.items():
        cursor = conn.execute(
            "UPDATE letters SET topics = ? WHERE id = ? AND (topics IS NULL OR length(topics) = 0)",
            (topics, letter_id)
        )
        updated += cursor.rowcount
    conn.commit()
    conn.close()

    print(f"Updated {updated} rows (skipped already-classified letters).")

    # Topic distribution
    all_topics = []
    for topics_str in classifications.values():
        all_topics.extend(topics_str.split(','))

    topic_counts = Counter(all_topics)
    print(f"\nTopic distribution across {len(classifications)} classified letters:")
    for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
        print(f"  {topic:<25} {count:>4}")

    # Sample output
    print("\nSample classifications (first 10):")
    for letter_id, collection, text in records[:10]:
        print(f"  id={letter_id:4d}  [{collection:<20}]  -> {classifications[letter_id]}")
        print(f"           text: {text[:80]}...")


if __name__ == '__main__':
    main()

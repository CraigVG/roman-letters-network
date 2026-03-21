#!/usr/bin/env python3
"""
AI-style topic classification for the 2,162 letters still missing topic tags.

Uses an extended keyword list with longer, more specific phrases.
Requires only 1 match (vs. the old 2-match threshold) but the phrases
are intentionally more precise to reduce false positives.

Only updates letters where topics IS NULL — never overwrites existing tags.
"""

import sqlite3
import re
from collections import Counter

DB_PATH = "/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db"

# Extended keyword phrases — longer and more specific to work with a threshold of 1.
# Each entry is a list of literal phrase strings (lowercased for matching).
TOPIC_KEYWORDS_EXTENDED = {
    'friendship': [
        'my dear friend', 'our friendship', 'bond of affection', 'i miss you',
        'longing to see you', 'your companionship', 'beloved friend', 'dearest friend',
        'warmest regards', 'fond memories', 'cherished friend', 'faithful friend',
        'truest friend', 'deepest affection', 'your company is missed',
        'how i long', 'we have been parted', 'your absence pains',
        'write to me often', 'i think of you often',
    ],
    'imperial_politics': [
        'the emperor', 'his majesty', 'the imperial court', 'imperial decree',
        'by order of the emperor', 'augustus', 'caesar', 'the praefect',
        'the prefecture', 'the consulship', 'the magistrate', 'ascended the throne',
        'the prince', 'imperial sovereignty', 'at the palace', 'the court at ravenna',
        'the court at constantinople', 'his imperial majesty', 'the imperial will',
        'imperial rescript', 'the praetorian prefect', 'master of soldiers',
    ],
    'education_books': [
        'your writings', 'the treatise', 'i have read', 'send me the book',
        'manuscript', 'copy of your', 'your commentary', 'scholarly work',
        'the lecture', 'the discourse', 'literary composition', 'the oration',
        'the volume you', 'a copy of the', 'reading your', 'your learned',
        'the books you', 'send me a copy', 'i am studying', 'i have been reading',
        'your philosophical', 'rhetorical skill', 'your eloquence',
        'the library', 'borrowed from', 'lend me',
    ],
    'property_economics': [
        'the estate', 'your lands', 'the rent', 'the purchase', 'has been sold',
        'the market', 'great wealth', 'in poverty', 'the provisions',
        'the harvest', 'the vineyard', 'the farm', 'the wages', 'the price',
        'the cost of', 'the patrimony', 'church property', 'the revenues',
        'the taxes', 'the tenant', 'the steward', 'the debtors', 'the creditors',
        'money is owed', 'payment of', 'financial affairs', 'economic hardship',
    ],
    'travel_mobility': [
        'your journey', 'safe travels', 'along the road', 'by ship',
        'set sail', 'arrived safely', 'has departed', 'the bearer of this letter',
        'our messenger', 'sent by hand', 'delivered by', 'through the messenger',
        'the roads are', 'the journey is', 'crossing the sea', 'at sea',
        'the traveller', 'by way of', 'has arrived', 'on the road',
        'the letter carrier', 'who brings this letter', 'who carries this',
        'delayed on the road', 'difficulty of travel',
    ],
    'grief_death': [
        'has passed away', 'has died', 'passed from this life', 'in mourning',
        'the loss of', 'rest in peace', 'his soul', 'her soul',
        'the deceased', 'the burial', 'in memory of', 'words of condolence',
        'comfort in your grief', 'grieve with you', 'your bereavement',
        'the death of', 'mourn the passing', 'taken from us',
        'called home', 'gone to god', 'departed this life', 'untimely death',
        'premature death', 'sudden death', 'i weep', 'words of comfort',
    ],
    'illness': [
        'fallen ill', 'recovering from', 'in poor health', 'the doctors',
        'your recovery', 'has taken to bed', 'suffering from illness',
        'bodily weakness', 'medical treatment', 'a cure for', 'the fever',
        'my illness', 'your illness', 'his illness', 'her illness',
        'been unwell', 'been sick', 'has been ailing', 'physical suffering',
        'afflicted by', 'the infirmity', 'the ailment', 'my health',
        'your health', 'weakness of body', 'pain in my',
    ],
    'monasticism': [
        'the brothers', 'the brethren', 'your monastery', 'religious life',
        'spiritual discipline', 'withdrawal from the world', 'the solitary life',
        'the rule of', 'community of monks', 'your convent', 'the monastery',
        'monastic life', 'the monks', 'the nuns', 'the abbot', 'the abbess',
        'life in the desert', 'desert fathers', 'the hermit', 'the cloister',
        'renounce the world', 'ascetic life', 'the cell', 'holy brethren',
    ],
    'barbarian_invasion': [
        'the enemy has', 'the enemy attacked', 'has been pillaged',
        'ravaged the', 'destroyed by the', 'the invaders', 'hostile forces',
        'under siege', 'forced to flee', 'refugees from', 'displaced by',
        'the barbarians', 'the goths', 'the vandals', 'the huns',
        'the lombards', 'the franks', 'the enemy forces', 'barbarian attack',
        'sack of rome', 'fall of the city', 'invaded by', 'ravaged by',
        'war has devastated', 'the province has been',
    ],
    'humor': [
        'i cannot help but smile', 'you amuse me', 'a witty remark',
        'tongue in cheek', 'you rascal', 'with a laugh', 'amusing story',
        'delightfully absurd', 'you jest', 'in jest', 'a playful spirit',
        'i jest', 'said in fun', 'the joke', 'comic',
    ],
    'women': [
        'your daughter', 'your wife', 'the lady', 'virgin consecrated to god',
        'the widow', 'her dowry', 'the matron', 'the abbess',
        'holy woman', 'devout woman', 'consecrated virgin', 'the blessed woman',
        'noble lady', 'the empress', 'the queen', 'women in the church',
        'the holy virgin', 'your mother', 'the sister', 'dedicated to god',
        'female ascetic', 'the deaconess',
    ],
    'papal_authority': [
        'the apostolic see', 'by authority of the', 'canonical authority',
        'the bishop of rome', 'papal authority', 'papal decree',
        'our predecessor', 'the chair of peter', 'primacy of rome',
        'roman primacy', 'successor of peter', 'vicar of christ',
        'apostolic succession', 'the roman see', 'appeal to rome',
        'universal bishop', 'the supreme pontiff', 'decretal letter',
        'the pope has decreed',
    ],
    'diplomatic': [
        'peace between', 'the treaty', 'good relations between', 'the alliance',
        'mutual agreement', 'terms of peace', 'reconciliation between',
        'the embassy', 'our ambassador', 'the envoy', 'the legate',
        'diplomatic mission', 'peace negotiations', 'the truce',
        'brokering peace', 'terms of agreement', 'a peaceful settlement',
        'to negotiate', 'sent as ambassador', 'dispatched as envoy',
    ],
    'conversion': [
        'brought to the faith', 'accepted baptism', 'turned from paganism',
        'newly converted', 'embraced christianity', 'the catechumens',
        'converted from paganism', 'baptised into', 'turned to christ',
        'abandoned the old gods', 'the newly baptized', 'instruction in the faith',
        'preparing for baptism', 'the pagan temples', 'demolishing the idols',
        'missionary work', 'preaching to the pagans',
    ],
    'slavery_captivity': [
        'held captive', 'ransom the prisoners', 'set them free',
        'in chains', 'the enslaved', 'liberate the captives',
        'the slaves', 'in captivity', 'taken as slaves', 'sold into slavery',
        'the prisoners', 'redeem the captives', 'free the prisoners',
        'ransomed from', 'captive christians',
    ],
    'famine_plague': [
        'the plague has', 'people are starving', 'food shortage',
        'the epidemic', 'many have died', 'widespread disease',
        'the pestilence', 'famine has struck', 'great mortality',
        'died of plague', 'ravaged by disease', 'the hunger',
        'starvation', 'dearth of food', 'the drought',
        'the locusts', 'catastrophic flood',
    ],
    'christology': [
        'the nature of christ', 'divine and human natures', 'eutychian heresy',
        'the council of chalcedon', 'one nature', 'two natures of christ',
        'nestorian heresy', 'nestorius', 'the theotokos', 'mother of god',
        'chalcedonian definition', 'hypostatic union', 'tome of leo',
        'the council of ephesus', 'monophysite', 'miaphysite',
        'the person of christ', 'divine nature of christ',
    ],
    'arianism': [
        'the arian heresy', 'homoousios', 'the nicene faith', 'against the arians',
        'consubstantial with the father', 'arian doctrine', 'arian bishop',
        'council of nicaea', 'the nicene creed', 'homoiousian',
        'arian controversy', 'arian persecution', 'semi-arian',
        'the arians deny', 'opposed to arianism',
    ],
    'donatism': [
        'the donatists', 'donatist schism', 'rebaptism of the', 'the unity of the church',
        'schismatic party', 'against the donatists', 'donatist bishop',
        'caecilian', 'circumcellions', 'the donatist controversy',
        'donatist clergy', 'schismatics who rebaptize',
    ],
    'pelagianism': [
        'pelagian error', 'human will alone', 'divine grace is necessary',
        'without grace', 'pelagius', 'caelestius', 'julian of eclanum',
        'the pelagian heresy', 'against pelagius', 'grace and free will',
        'pelagian doctrine', 'original sin denied', 'semi-pelagian',
    ],
    'church_state_conflict': [
        'the church must be free', 'secular interference', 'the state has no right',
        'spiritual jurisdiction', 'ecclesiastical independence',
        'the emperor interferes', 'the bishop refuses', 'exiled by the emperor',
        'the secular power', 'the civil authorities', 'against the church',
        'the clergy are exempt', 'temporal power over the church',
        'the church is not subject', 'resist the emperor',
    ],
}


def build_patterns(keywords_dict):
    """Compile lowercase patterns for fast matching."""
    compiled = {}
    for topic, phrases in keywords_dict.items():
        # Escape each phrase for literal matching, join with |
        patterns = [re.escape(phrase.lower()) for phrase in phrases]
        compiled[topic] = re.compile('|'.join(patterns))
    return compiled


def classify_letter(text, compiled_patterns):
    """Return list of matching topics for the given text."""
    if not text or not text.strip():
        return []
    text_lower = text.lower()
    tags = []
    for topic, pattern in compiled_patterns.items():
        if pattern.search(text_lower):
            tags.append(topic)
    return sorted(tags)


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Sanity check: how many are missing topics?
    total_missing = cur.execute("SELECT COUNT(*) FROM letters WHERE topics IS NULL").fetchone()[0]
    print(f"Letters with topics IS NULL: {total_missing}")

    # Fetch only letters missing topics
    rows = cur.execute(
        "SELECT id, modern_english, english_text, subject_summary, quick_summary "
        "FROM letters WHERE topics IS NULL"
    ).fetchall()
    print(f"Processing {len(rows)} letters...\n")

    compiled_patterns = build_patterns(TOPIC_KEYWORDS_EXTENDED)

    tag_counter = Counter()
    tagged_count = 0
    no_text_count = 0
    updates = []

    for row in rows:
        # Combine all available text fields — full text, no truncation
        parts = []
        for field in ('modern_english', 'english_text', 'subject_summary', 'quick_summary'):
            val = row[field]
            if val and val.strip():
                parts.append(val)
        combined_text = "\n".join(parts)

        if not combined_text.strip():
            no_text_count += 1
            # Leave as NULL — no text to classify
            continue

        tags = classify_letter(combined_text, compiled_patterns)

        if tags:
            tagged_count += 1
            for t in tags:
                tag_counter[t] += 1
            updates.append((','.join(tags), row['id']))
        # If no tags found, leave topics as NULL (don't update)

    # Batch UPDATE — only rows that got tags
    if updates:
        cur.executemany(
            "UPDATE letters SET topics = ? WHERE id = ? AND topics IS NULL",
            updates
        )
        conn.commit()
        print(f"Committed {len(updates)} updates.\n")

    # Final count
    remaining_null = cur.execute("SELECT COUNT(*) FROM letters WHERE topics IS NULL").fetchone()[0]
    total_letters = cur.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
    tagged_total = cur.execute("SELECT COUNT(*) FROM letters WHERE topics IS NOT NULL").fetchone()[0]

    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total letters in DB:         {total_letters}")
    print(f"Letters now with topics:     {tagged_total}")
    print(f"Letters still missing topics:{remaining_null}")
    print(f"  Of which: no text at all:  {no_text_count}")
    print(f"  Of which: text but no match:{remaining_null - no_text_count}")
    print(f"\nNewly tagged this run:       {tagged_count}")

    print(f"\n{'=' * 60}")
    print("TOPIC DISTRIBUTION (newly tagged letters this run)")
    print("=" * 60)
    for topic in sorted(TOPIC_KEYWORDS_EXTENDED.keys()):
        count = tag_counter.get(topic, 0)
        bar = '#' * (count // 5)
        print(f"  {topic:<25} {count:>5}  {bar}")

    # Also show overall distribution across ALL letters
    print(f"\n{'=' * 60}")
    print("OVERALL TOPIC DISTRIBUTION (all letters with topics)")
    print("=" * 60)
    all_tagged = cur.execute("SELECT topics FROM letters WHERE topics IS NOT NULL").fetchall()
    overall_counter = Counter()
    for row in all_tagged:
        for tag in row['topics'].split(','):
            overall_counter[tag.strip()] += 1
    for topic, count in sorted(overall_counter.items(), key=lambda x: -x[1]):
        bar = '#' * (count // 20)
        print(f"  {topic:<25} {count:>5}  {bar}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

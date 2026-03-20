#!/usr/bin/env python3
"""
Tag letters with specific historical topics based on text content analysis.

Scans modern_english, english_text, subject_summary, and quick_summary fields
for keyword patterns and assigns granular topic tags to a new 'topics' column.
"""

import sqlite3
import re
from collections import Counter

DB_PATH = "/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db"

# Each topic: (tag_name, category, compiled_regex)
# Patterns are case-insensitive and use word boundaries where appropriate
TOPIC_RULES = []

def rule(tag, category, pattern):
    TOPIC_RULES.append((tag, category, re.compile(pattern, re.IGNORECASE)))

# ── POLITICAL ──────────────────────────────────────────────────────────────
rule("barbarian_invasion", "POLITICAL",
     r"\b(?:goth|goths|gothic|ostrogoth|visigoth|vandal|vandals|hun|huns|hunnic|"
     r"lombard|lombards|frank|franks|frankish|burgund|burgundian|alan|alans|"
     r"heruli|herulian|suev|suevi|suebi|gepid|gepids|"
     r"barbarian\w*\s+(?:invasion|attack|raid|incursion|horde|army|armies|threat|menace)|"
     r"(?:invasion|incursion|raid|sack|plunder|ravag|devastat)\w*\s+(?:by|of)\s+(?:the\s+)?(?:barbarian|goth|vandal|hun|lombard|frank)|"
     r"attila|alaric|gaiseric|genseric|odoacer|theoderic|theodoric|totila|clovis|stilicho|radagaisus|"
     r"(?:sack|fall|siege)\s+(?:of\s+)?rome|"
     r"barbarian\s+(?:nation|people|tribe|race|king|chief))")

rule("imperial_politics", "POLITICAL",
     r"\b(?:emperor\b|empress\b|imperial\s+(?:court|decree|edict|command|order|law|power|majesty|authority)|"
     r"augustus\b|augusta\b|caesar\b|"
     r"(?:the\s+)?(?:court|palace)\s+(?:at|of|in)\s+(?:constantinople|ravenna|milan)|"
     r"prefect\b|praetorian|consul\b|patrician\b|"
     r"theodosius|valentinian|honorius|arcadius|justinian|theodora|marcian|"
     r"leo\s+(?:the\s+)?emperor|zeno\s+(?:the\s+)?emperor|anastasius\s+(?:the\s+)?emperor|"
     r"constantius|constans|julian\s+(?:the\s+)?(?:emperor|apostate)|"
     r"imperial\s+rescript|edict\b|"
     r"comes\b|magister\s+militum|master\s+of\s+(?:soldiers|offices|the\s+horse))")

rule("church_state_conflict", "POLITICAL",
     r"\b(?:(?:bishop|church|clergy|priest|pope|pontiff)\w*\s+(?:against|versus|conflict|dispute|clash|resist|oppos|defy|defi)\w*\s+(?:emperor|state|secular|civil|king|prince|magistrat|prefect|governor)|"
     r"(?:emperor|state|secular|civil|king|prince|magistrat|prefect|governor)\w*\s+(?:against|versus|interfer|meddle|encroach|persecute|exile|banish|depos)\w*\s+(?:bishop|church|clergy|priest|pope|pontiff)|"
     r"secular\s+(?:power|authority|interference|jurisdiction)\s+(?:over|in|into)\s+(?:the\s+)?(?:church|ecclesiastical|spiritual)|"
     r"ecclesiastical\s+(?:independence|freedom|liberty|immunity|privilege)\s+(?:from|against)\s+(?:the\s+)?(?:state|secular|civil)|"
     r"(?:banish|exile|depos|remov)\w+\s+(?:the\s+)?(?:bishop|patriarch|pope)|"
     r"(?:bishop|patriarch|pope)\w*\s+(?:banish|exile|depos|remov)|"
     r"ambrose\s+(?:and|against|versus)\s+(?:theodosius|emperor)|"
     r"investiture|caesaropapism|two\s+swords)")

rule("diplomatic", "POLITICAL",
     r"\b(?:(?:peace\s+)?treat(?:y|ies)|embassy|embass(?:y|ies)|ambassador|envoy|legate\b|"
     r"negotiat\w+|peace\s+(?:terms|agreement|accord|proposal)|"
     r"truce\b|armistice|alliance\b|"
     r"(?:send|sent|dispatch)\w*\s+(?:an?\s+)?(?:embassy|envoy|legate|ambassador|delegation|mission)|"
     r"(?:diplomatic|peace)\s+(?:mission|overture|initiative|effort|relation)|"
     r"intercede\w*\s+(?:with|before|on\s+behalf)|"
     r"(?:beg|plead|petition|appeal)\w*\s+(?:for\s+)?(?:peace|mercy|clemency)|"
     r"ransom\w*\s+(?:captive|prisoner|hostage))")

# ── RELIGIOUS ──────────────────────────────────────────────────────────────
rule("arianism", "RELIGIOUS",
     r"\b(?:arian\w*|arius\b|homoousio|homoiousio|anomoean|eunomi\w+|"
     r"nicene\s+(?:creed|faith|formula|definition|council)|"
     r"consubstantial|council\s+of\s+nicaea|"
     r"(?:semi[- ]?arian|neo[- ]?arian|macedonian\s+heresy)|"
     r"eudoxi\w+|valens\s+(?:the\s+)?(?:arian|bishop)|"
     r"(?:arian|homoian)\s+(?:heresy|doctrine|bishop|clergy|church|party|controversy|persecution))")

rule("donatism", "RELIGIOUS",
     r"\b(?:donatist\w*|donatus\b|donatism|"
     r"circumcellion\w*|caecilian\w*|"
     r"(?:traditor|traditores)\b|"
     r"(?:donatist|schismatic)\s+(?:bishop|clergy|church|party|controversy|schism|rebaptis))")

rule("pelagianism", "RELIGIOUS",
     r"\b(?:pelagian\w*|pelagius\b|pelagianism|"
     r"caelestius\b|celestius\b|julian\s+of\s+eclanum|"
     r"(?:semi[- ]?pelagian)|"
     r"(?:original\s+sin|free\s+will|grace\s+(?:alone|of\s+god))\s+(?:controversy|debate|dispute|heresy|doctrine)|"
     r"(?:pelagian)\s+(?:heresy|doctrine|controversy|error))")

rule("christology", "RELIGIOUS",
     r"\b(?:nestorian\w*|nestorius\b|nestorianism|"
     r"monophysit\w*|miaphysit\w*|eutychi\w*|eutyches\b|"
     r"chalcedon(?:ian)?\b|council\s+of\s+chalcedon|"
     r"council\s+of\s+ephesus|"
     r"theotokos|christotokos|"
     r"(?:two|one|dual)\s+(?:nature|natures)\s+(?:of\s+)?christ|"
     r"(?:hypostatic\s+union|communicatio\s+idiomatum)|"
     r"tome\s+of\s+leo|"
     r"apollinari\w+|"
     r"(?:dioscorus|dioscurus|flavian|cyril\s+of\s+alexandria)\b)")

rule("conversion", "RELIGIOUS",
     r"\b(?:(?:convert|conversion|converting|converted)\s+(?:the\s+)?(?:pagan|heathen|heretic|jew|barbarian|gentile|infidel|nation|people|tribe)|"
     r"(?:pagan|heathen|heretic|jew|barbarian|gentile)\w*\s+(?:convert|conversion|bapti[sz])|"
     r"bapti[sz]\w+\s+(?:the\s+)?(?:pagan|heathen|heretic|barbarian|king|nation|convert|catechumen|infant|child)|"
     r"(?:catechumen|neophyte|newly\s+bapti[sz])|"
     r"(?:pagan|idol)\w*\s+(?:worship|temple|shrine|sacrifice|rite|custom)\w*\s+(?:destroy|abolish|suppress|eradicat|overthrow|demolish)|"
     r"(?:mission|missionary|evangeli[sz])\w*\s+(?:to|among|work)|"
     r"(?:instruction|instruct)\w*\s+(?:in\s+(?:the\s+)?faith|catechumen|convert))")

rule("monasticism", "RELIGIOUS",
     r"\b(?:monast\w+|monk|monks|nun|nuns|abbot\b|abbess\b|"
     r"(?:monastic|religious)\s+(?:life|rule|discipline|community|order|vow|habit)|"
     r"(?:rule\s+of\s+(?:st\.?\s+)?(?:benedict|basil|augustine|pachomius))|"
     r"(?:cenobite|cenobitic|anchorite|anchoretic|hermit|eremit\w+|ascetic\w*)|"
     r"(?:cell|cloister|monastery|convent|desert\s+father|desert\s+mother)|"
     r"(?:renounce|renunciation|renouncing)\s+(?:the\s+)?(?:world|flesh|secular))")

rule("papal_authority", "RELIGIOUS",
     r"\b(?:(?:primacy|supremacy|authority|jurisdiction|prerogative)\s+(?:of\s+)?(?:the\s+)?(?:roman\s+(?:see|church|bishop|pontiff)|apostolic\s+see|pope|peter|"
     r"see\s+of\s+(?:peter|rome))|"
     r"(?:vicar\s+of\s+(?:christ|peter|god))|"
     r"(?:successor\s+of\s+(?:peter|the\s+apostle))|"
     r"(?:apostolic\s+(?:see|authority|tradition|succession|primacy))|"
     r"(?:(?:roman|papal)\s+(?:primacy|supremacy|jurisdiction|prerogative|authority))|"
     r"(?:tu\s+es\s+petrus|upon\s+this\s+rock)|"
     r"(?:appeal\w*\s+to\s+(?:the\s+)?(?:pope|rome|apostolic\s+see))|"
     r"(?:canonical\s+jurisdiction|metropolitan\s+authority))")

# ── SOCIAL ─────────────────────────────────────────────────────────────────
rule("famine_plague", "SOCIAL",
     r"\b(?:famine\b|plague\b|pestilence\b|epidemic\b|pandemic\b|"
     r"(?:great\s+)?(?:hunger|starvation|dearth|scarcity)\b|"
     r"(?:earthquake|flood|drought|locust|volcano|eruption|disaster)\b|"
     r"(?:plague|pestilence|disease|sickness|contagion|mortality)\s+(?:ravag|devastat|spread|struck|swept|killed|carried\s+off|claimed)|"
     r"(?:many|countless|innumerable|great\s+numbers?)\s+(?:died|perished|were\s+(?:killed|carried\s+off|struck\s+down)))")

rule("slavery_captivity", "SOCIAL",
     r"\b(?:slave\w*|slavery\b|enslav\w+|servitude\b|bondage\b|"
     r"captiv\w+|prisoner\w*|hostage\w*|"
     r"(?:ransom|redeem|free|liberat)\w*\s+(?:the\s+)?(?:captive|prisoner|slave|hostage)|"
     r"(?:taken|held|sold)\s+(?:as\s+)?(?:captive|prisoner|slave|hostage)|"
     r"(?:chain|shackle|fetter|manacle)\w*|"
     r"(?:human\s+traffick|slave\s+(?:trade|market|dealer)))")

rule("women", "SOCIAL",
     r"\b(?:(?:to|dear|beloved|holy|blessed|noble|illustrious)\s+(?:lady|sister|mother|daughter|widow|virgin|woman|matron|empress|queen|abbess)|"
     r"(?:lady|sister|mother|daughter|widow|virgin|matron|abbess)\s+(?:\w+\s+)?(?:writes?|send|greet|asks?|request|beseech|implore)|"
     r"(?:consecrated|dedicated|devoted)\s+virgin|"
     r"(?:women|female|widow|virgin)\s+(?:in\s+the\s+church|religious|consecrated|role|place|status)|"
     r"(?:marriage|dowry|conjugal|bridal|nuptial|wife|wive|husband\s+and\s+wife)\b)")

rule("education_books", "SOCIAL",
     r"\b(?:(?:send|sent|lending|lend|borrow|copy|copies|copying|transcrib)\w*\s+(?:the\s+)?(?:book|volume|work|manuscript|codex|text|treatise|scroll|letter)|"
     r"(?:book|volume|work|manuscript|codex|library|libraries)\s+(?:you\s+)?(?:sent|send|request|ask|lend|borrow|copy)|"
     r"(?:liberal\s+arts|rhetoric|grammar|dialectic|philosophy|eloquen\w+|education|school|teacher|pupil|student|tutor)\b|"
     r"(?:literary|learned|scholarly|intellectual)\s+(?:culture|circle|pursuits|friendship|exchange|life)|"
     r"(?:study|studies|studying|read|reading)\s+(?:of\s+)?(?:scripture|classics|philosophy|rhetoric|law|literature)|"
     r"(?:cicero|virgil|vergil|horace|plato|aristotle|homer|sallust|livy|tacitus)\b)")

rule("property_economics", "SOCIAL",
     r"\b(?:(?:estate|property|properties|land|lands|farm|villa|rent|revenue|tax|taxes|tithe|patrimony)\b|"
     r"(?:buy|sell|purchase|sale|trade|merchant|market|commerce|commercial|economic)\b|"
     r"(?:debt|creditor|debtor|loan|interest|payment|money|wealth|income|profit|loss)\b|"
     r"(?:tenant|lease|steward|procurator|administration)\s+(?:of\s+)?(?:the\s+)?(?:estate|property|land|patrimony|church)|"
     r"(?:patrimony\s+of\s+(?:st\.?\s+)?peter|church\s+(?:property|estate|land|revenue|patrimony)))")

rule("travel_mobility", "SOCIAL",
     r"\b(?:(?:journey|travel|voyage|trip|passage|crossing)\w*\s+(?:to|from|through|across|by\s+(?:sea|land|road))|"
     r"(?:road|roads|highway|route|path)\s+(?:(?:is|are|were|was)\s+)?(?:dangerous|unsafe|blocked|impassable|difficult)|"
     r"(?:winter|storm|weather|sea|mountain|bandit|robber|pirate)\w*\s+(?:prevent|delay|hinder|block|endanger|threaten)\w*\s+(?:the\s+)?(?:journey|travel|voyage|passage|letter|messenger)|"
     r"(?:messenger|carrier|courier|letter[- ]?bearer|travell?er)\w*\s+(?:arriv|deliver|bring|carry|sent|dispatch)|"
     r"(?:delay|late|slow|difficult)\w*\s+(?:in\s+)?(?:deliver|arrival|communication|correspondence|mail|letter)|"
     r"(?:sail|sailed|sailing|embarked|set\s+out|set\s+forth|departed|arrived)\s+(?:for|from|at|in)\b)")

# ── PERSONAL ──────────────────────────────────────────────────────────────
rule("friendship", "PERSONAL",
     r"\b(?:(?:dear|dearest|beloved|cherished|closest)\s+friend|"
     r"(?:our|your|my|mutual|old|true|faithful|loyal|enduring|close|deep)\s+friendship|"
     r"amicitia\b|"
     r"(?:bond|bonds|tie|ties)\s+of\s+(?:friendship|affection|love|devotion)|"
     r"(?:miss|long\s+for|yearn\s+for|pine\s+for)\s+(?:you|your\s+(?:company|presence|conversation))|"
     r"(?:absence|separation|apart)\s+(?:from\s+)?(?:you|each\s+other|one\s+another)\s+(?:grieves?|pains?|saddens?|hurts?))")

rule("grief_death", "PERSONAL",
     r"\b(?:(?:death|passing|loss|decease)\s+of\s+(?:your|his|her|our|the|my)|"
     r"(?:mourn|grieve|lament|bewail|weep\s+for|sorrow\s+(?:for|over|at))\w*|"
     r"(?:console|consolation|comfort)\w*\s+(?:you|him|her|them|us|the\s+(?:bereaved|grieving|mourning))|"
     r"(?:funeral|burial|tomb|grave|epitaph|obituary|eulogy|elegy)\b|"
     r"(?:departed|deceased|fallen\s+asleep|gone\s+to\s+(?:god|the\s+lord|rest|heaven)|called\s+(?:home|to\s+god))|"
     r"(?:premature|untimely|sudden|unexpected)\s+(?:death|end|passing))")

rule("illness", "PERSONAL",
     r"\b(?:(?:my|your|his|her|our)\s+(?:illness|sickness|disease|ailment|malady|infirmity|health|fever|pain|gout|blindness|weakness)|"
     r"(?:sick|ill|unwell|ailing|infirm|bedridden|feeble|frail)\b|"
     r"(?:recover|recovery|recuperat|convalesc|heal)\w*\s+(?:from\s+)?(?:(?:my|your|his|her|the)\s+)?(?:illness|sickness|disease|fever)|"
     r"(?:doctor|physician|medicine|remedy|treatment|cure)\b|"
     r"(?:bodily|physical)\s+(?:weakness|suffering|pain|affliction|distress))")

rule("humor", "PERSONAL",
     r"\b(?:(?:joke|jest|wit|witty|humor|humour|humorous|funny|amusing|comic|comical|playful|merry|lighthearted|tongue[- ]in[- ]cheek)\b|"
     r"(?:laugh|laughing|laughter|chuckle|smile|grin)\w*\s+(?:at|about|over|when)|"
     r"(?:tease|teasing|mock|mocking|banter|irony|ironic|satiric|sarcas)\w*|"
     r"(?:in\s+(?:jest|fun|sport|play))\b)")


def get_text(row):
    """Combine available text fields for scanning."""
    parts = []
    for field in (row["modern_english"], row["english_text"], row["subject_summary"], row["quick_summary"]):
        if field:
            parts.append(field)
    return "\n".join(parts)


def tag_letter(row):
    """Return sorted list of topic tags for a letter."""
    text = get_text(row)
    if not text.strip():
        return []
    tags = []
    for tag, category, pattern in TOPIC_RULES:
        if pattern.search(text):
            tags.append(tag)
    return sorted(tags)


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Add topics column if not exists
    columns = [r[1] for r in cur.execute("PRAGMA table_info(letters)").fetchall()]
    if "topics" not in columns:
        cur.execute("ALTER TABLE letters ADD COLUMN topics TEXT")
        conn.commit()
        print("Added 'topics' column to letters table.")
    else:
        print("'topics' column already exists.")

    # 2. Fetch all letters
    rows = cur.execute(
        "SELECT id, modern_english, english_text, subject_summary, quick_summary FROM letters"
    ).fetchall()
    print(f"\nScanning {len(rows)} letters for topic tags...\n")

    # 3. Tag each letter
    tag_counter = Counter()
    category_counter = Counter()
    tagged_count = 0
    no_text_count = 0
    updates = []

    for row in rows:
        text = get_text(row)
        if not text.strip():
            no_text_count += 1
            updates.append((None, row["id"]))
            continue

        tags = tag_letter(row)
        if tags:
            tagged_count += 1
            for t in tags:
                tag_counter[t] += 1
                # Find category
                for tag, cat, _ in TOPIC_RULES:
                    if tag == t:
                        category_counter[cat] += 1
                        break
            updates.append((",".join(tags), row["id"]))
        else:
            updates.append((None, row["id"]))

    # 4. Batch update
    cur.executemany("UPDATE letters SET topics = ? WHERE id = ?", updates)
    conn.commit()

    # 5. Print stats
    total = len(rows)
    with_text = total - no_text_count
    print(f"Total letters:       {total}")
    print(f"Letters with text:   {with_text}")
    print(f"Letters tagged:      {tagged_count} ({tagged_count*100//with_text}% of those with text)")
    print(f"Letters untagged:    {with_text - tagged_count}")
    print(f"Letters without text:{no_text_count}")

    print(f"\n{'='*60}")
    print(f"TAG DISTRIBUTION (by category)")
    print(f"{'='*60}")

    # Group by category
    tag_by_cat = {}
    for tag, cat, _ in TOPIC_RULES:
        tag_by_cat.setdefault(cat, []).append(tag)

    for cat in ["POLITICAL", "RELIGIOUS", "SOCIAL", "PERSONAL"]:
        print(f"\n  {cat}:")
        for tag in tag_by_cat.get(cat, []):
            count = tag_counter.get(tag, 0)
            bar = "#" * (count // 20)
            print(f"    {tag:<25} {count:>5}  {bar}")

    print(f"\n{'='*60}")
    print(f"CATEGORY TOTALS (tag assignments, not unique letters)")
    print(f"{'='*60}")
    for cat in ["POLITICAL", "RELIGIOUS", "SOCIAL", "PERSONAL"]:
        print(f"  {cat:<15} {category_counter.get(cat, 0):>5}")

    # Average tags per tagged letter
    total_tags = sum(tag_counter.values())
    if tagged_count:
        print(f"\nAverage tags per tagged letter: {total_tags/tagged_count:.1f}")

    # Top 10 most common tag combinations
    print(f"\n{'='*60}")
    print(f"TOP 15 TAG COMBINATIONS")
    print(f"{'='*60}")
    combo_counter = Counter()
    for topics_str, _ in updates:
        if topics_str:
            combo_counter[topics_str] += 1
    for combo, count in combo_counter.most_common(15):
        print(f"  {count:>4}x  {combo}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

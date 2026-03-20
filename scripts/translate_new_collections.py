#!/usr/bin/env python3
"""
Translate newly scraped collections to modern English.

Collections with Latin text (translate from Latin):
  - venantius_fortunatus (100 verse epistles)
  - caesarius_arles (3 letters)

Collections with metadata only (generate scholarly summaries):
  - epistulae_langobardorum (25 letters)
  - epistulae_merowingici (20 letters)
  - faustus_riez (11 letters)
  - epistulae_wisigothicae (remaining 12)
  - ruricius_limoges book 3 (8 letters to Ruricius, have Latin text)
  - avitus_vienne new letters (have Latin text)

Uses Claude claude-sonnet-4-6 via Anthropic API.
"""

import sqlite3
import os
import time
import anthropic

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
client = anthropic.Anthropic()

DELAY = 1.2  # seconds between API calls


# ─────────────────────────────────────────────────────────────────────────────
# System prompts
# ─────────────────────────────────────────────────────────────────────────────

FORTUNATUS_SYSTEM = """You are an expert translator of late antique Latin verse. Translate the following verse epistle by Venantius Fortunatus (c.530–600 AD) into clear, modern English prose.

VENANTIUS FORTUNATUS'S VOICE: Charming, warm, and witty — a professional poet who used verse letters as a social currency in Merovingian Gaul. Born in northern Italy, he settled at Poitiers as companion to Queen Radegund and her abbess Agnes. His letters are effusive with flattery but genuine in affection, full of wordplay and classical allusions, and historically invaluable for their picture of post-Roman Gaul. Think of him as the most well-connected dinner guest at every episcopal table in 6th-century France.

TRANSLATION RULES:
1. Translate the FULL content of the poem into English prose — capture all the imagery, compliments, requests, and specific details
2. The poem is a VERSE LETTER: translate it to sound like an eloquent, warmly flattering personal letter, not a poem
3. Convert the Latin verse to natural modern English prose paragraphs
4. PRESERVE all proper names (people, places, churches, saints)
5. ADD brief [context] notes in brackets for: named people (e.g., [Gregory of Tours — bishop of Tours, 573-594, historian of the Franks]), places, and any obscure classical/biblical references
6. KEEP Fortunatus's warmth and wit — he's never boring, often charming, occasionally obsequious
7. If the poem is very short (a few couplets), it's fine to have a brief translation
8. The opening title line (e.g., "I. Ad Vitalem episcopum Ravennensem") is a heading — include it as-is

OUTPUT FORMAT: Just the translated letter. Start with the heading if present, then the prose translation. No "Here is the translation:" preamble."""

LATIN_LETTER_SYSTEM = """You are an expert translator of late antique Latin letters. Translate the following letter into clear, modern English.

TRANSLATION RULES:
1. Translate the FULL content — capture all theological arguments, historical references, and specific details
2. Convert to natural modern English prose (not archaic Victorian style)
3. PRESERVE all proper names (people, places, church offices)
4. ADD brief [context] notes in brackets where helpful for modern readers
5. Maintain the letter's formal/informal register appropriately
6. Keep paragraph structure
7. No preamble — just the translation

OUTPUT FORMAT: Just the translated letter text."""

SUMMARY_SYSTEM = """You are an expert in late antique and early medieval history. Create a brief but informative modern English description of the following letter, based on the metadata provided.

Write 2-4 sentences that:
1. Identify the sender and recipient clearly (with brief context on who they are)
2. Summarize the main content/purpose of the letter
3. Note its historical significance if relevant

Write in the style of a museum label or encyclopedia entry — factual, clear, accessible.
The output will be displayed as the "modern English" content for this letter on a website about late Roman correspondence.

Do NOT write "This letter..." as the opening. Start with the content directly.
OUTPUT FORMAT: Just the 2-4 sentence description. No preamble."""


# ─────────────────────────────────────────────────────────────────────────────
# Core translation function
# ─────────────────────────────────────────────────────────────────────────────

def translate_letter(system_prompt, user_content, letter_id, ref_id):
    """Call Claude API and return translation text, or None on failure."""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"  ERROR translating {ref_id}: {e}")
        return None


def save_translation(conn, letter_id, text):
    conn.execute('UPDATE letters SET modern_english = ? WHERE id = ?', (text, letter_id))
    conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Venantius Fortunatus — translate from Latin verse
# ─────────────────────────────────────────────────────────────────────────────

def translate_fortunatus(conn):
    print(f"\n{'='*60}")
    print("Translating Venantius Fortunatus (100 verse epistles)...")

    rows = conn.execute('''
        SELECT id, ref_id, book, letter_number, latin_text
        FROM letters
        WHERE collection = 'venantius_fortunatus'
          AND latin_text IS NOT NULL
          AND (modern_english IS NULL OR length(modern_english) = 0)
        ORDER BY book, letter_number
    ''').fetchall()

    print(f"  Found {len(rows)} letters to translate")
    done = 0

    for letter_id, ref_id, book, letter_num, latin_text in rows:
        user_msg = f"Translate this verse epistle by Venantius Fortunatus (Book {book}, Poem {letter_num}):\n\n{latin_text[:8000]}"
        translation = translate_letter(FORTUNATUS_SYSTEM, user_msg, letter_id, ref_id)

        if translation:
            save_translation(conn, letter_id, translation)
            done += 1
            if done % 10 == 0:
                print(f"  Progress: {done}/{len(rows)} translated")

        time.sleep(DELAY)

    print(f"  Done: {done} Fortunatus verse epistles translated")
    return done


# ─────────────────────────────────────────────────────────────────────────────
# 2. Caesarius of Arles — translate from Latin
# ─────────────────────────────────────────────────────────────────────────────

def translate_caesarius(conn):
    print(f"\n{'='*60}")
    print("Translating Caesarius of Arles (3 letters)...")

    rows = conn.execute('''
        SELECT id, ref_id, latin_text, subject_summary
        FROM letters
        WHERE collection = 'caesarius_arles'
          AND latin_text IS NOT NULL
          AND (modern_english IS NULL OR length(modern_english) = 0)
        ORDER BY letter_number
    ''').fetchall()

    CAESARIUS_SYSTEM = """You are an expert translator of late antique Latin. Translate the following letter by Caesarius of Arles (470–542 AD) into clear, modern English.

CAESARIUS'S VOICE: Practical, warm, and pastorally urgent — a bishop focused on the daily spiritual life of his congregation. He wrote primarily for monastic communities and lay Christians, not theologians. His Latin is clear and direct, aimed at being understood. Think of him as a thoughtful parish priest who also had significant theological and political standing.

TRANSLATION RULES:
1. Translate the FULL content into natural modern English
2. Keep his pastoral, warm-but-authoritative tone
3. ADD [context] notes for historical/theological references
4. Preserve the epistolary structure (opening, body, closing)

OUTPUT FORMAT: Just the translated letter. No preamble."""

    done = 0
    for letter_id, ref_id, latin_text, summary in rows:
        user_msg = f"Translate this letter by Caesarius of Arles:\n\n{latin_text[:8000]}"
        translation = translate_letter(CAESARIUS_SYSTEM, user_msg, letter_id, ref_id)
        if translation:
            save_translation(conn, letter_id, translation)
            done += 1
            print(f"  Translated {ref_id}")
        time.sleep(DELAY)

    print(f"  Done: {done} letters translated")
    return done


# ─────────────────────────────────────────────────────────────────────────────
# 3. Ruricius Book 3 and new Avitus — translate from Latin
# ─────────────────────────────────────────────────────────────────────────────

def translate_latin_collections(conn, collections_info):
    """
    Generic Latin→English translator for multiple collections.
    collections_info: list of (collection_slug, author_description) tuples
    """
    total = 0
    for slug, author_desc in collections_info:
        rows = conn.execute('''
            SELECT id, ref_id, latin_text, subject_summary
            FROM letters
            WHERE collection = ?
              AND latin_text IS NOT NULL
              AND length(latin_text) > 50
              AND (modern_english IS NULL OR length(modern_english) = 0)
            ORDER BY book, letter_number
        ''', (slug,)).fetchall()

        if not rows:
            continue

        print(f"\n  Translating {slug}: {len(rows)} letters...")
        system = LATIN_LETTER_SYSTEM + f"\n\nAUTHOR CONTEXT: {author_desc}"

        for letter_id, ref_id, latin_text, summary in rows:
            user_msg = f"Translate this Latin letter:\n\n{latin_text[:8000]}"
            translation = translate_letter(system, user_msg, letter_id, ref_id)
            if translation:
                save_translation(conn, letter_id, translation)
                total += 1
                print(f"    Translated {ref_id}")
            time.sleep(DELAY)

    return total


# ─────────────────────────────────────────────────────────────────────────────
# 4. Metadata-only collections — generate scholarly summaries
# ─────────────────────────────────────────────────────────────────────────────

def generate_summaries_for_collection(conn, slug, collection_context):
    """
    For letters with only subject_summary (no Latin text),
    generate informative modern_english descriptions using Claude.
    """
    rows = conn.execute('''
        SELECT id, ref_id, subject_summary, year_approx,
               (SELECT name FROM authors WHERE id = sender_id) as sender_name,
               (SELECT name FROM authors WHERE id = recipient_id) as recipient_name
        FROM letters
        WHERE collection = ?
          AND (latin_text IS NULL OR length(latin_text) = 0)
          AND (modern_english IS NULL OR length(modern_english) = 0)
          AND subject_summary IS NOT NULL
        ORDER BY letter_number
    ''', (slug,)).fetchall()

    if not rows:
        return 0

    print(f"\n  Generating summaries for {slug}: {len(rows)} entries...")
    done = 0

    for letter_id, ref_id, summary, year, sender, recipient in rows:
        sender_str = sender or 'Unknown sender'
        recipient_str = recipient or 'Unknown recipient'
        year_str = f"~{year} AD" if year else "date uncertain"

        user_msg = (
            f"Collection: {collection_context}\n"
            f"Letter: {ref_id}\n"
            f"From: {sender_str}\n"
            f"To: {recipient_str}\n"
            f"Date: {year_str}\n"
            f"Summary: {summary}\n\n"
            f"Write a 2-4 sentence modern English description for this letter."
        )

        text = translate_letter(SUMMARY_SYSTEM, user_msg, letter_id, ref_id)
        if text:
            save_translation(conn, letter_id, text)
            done += 1

        time.sleep(DELAY)

    print(f"    Generated {done} summaries for {slug}")
    return done


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def print_progress(conn):
    collections = [
        'venantius_fortunatus', 'caesarius_arles', 'epistulae_langobardorum',
        'epistulae_merowingici', 'faustus_riez', 'epistulae_wisigothicae',
        'ruricius_limoges', 'avitus_vienne',
    ]
    placeholders = ','.join(['?'] * len(collections))
    rows = conn.execute(f'''
        SELECT collection,
               COUNT(*) as total,
               SUM(CASE WHEN modern_english IS NOT NULL THEN 1 ELSE 0 END) as translated
        FROM letters WHERE collection IN ({placeholders})
        GROUP BY collection ORDER BY collection
    ''', collections).fetchall()

    print(f"\n{'Collection':<30} {'Total':>6} {'Trans':>6}")
    print('-' * 45)
    for row in rows:
        print(f"{row[0]:<30} {row[1]:>6} {row[2]:>6}")


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)

    # --- Step 1: Translate collections with actual Latin text ---
    n1 = translate_fortunatus(conn)

    n2 = translate_caesarius(conn)

    # Ruricius book 3 (letters TO Ruricius — have Latin text)
    # Avitus new letters
    n3 = translate_latin_collections(conn, [
        ('ruricius_limoges',
         'Ruricius of Limoges (c.440-510), bishop in late Roman Gaul. '
         'These are letters received by Ruricius from other bishops and laymen.'),
        ('avitus_vienne',
         'Avitus of Vienne (c.470-518), bishop of Vienne in Burgundy. '
         'Letters to Visigothic and Burgundian royalty, fellow bishops, '
         'and Roman aristocrats during the fall of the Western Roman Empire.'),
    ])

    # --- Step 2: Generate summaries for metadata-only collections ---
    n4 = 0

    n4 += generate_summaries_for_collection(
        conn, 'epistulae_langobardorum',
        'Lombard correspondence (590-660 AD): letters between Lombard royalty '
        '(Theudelinda, Agilulf, Arioald, Rothari), Pope Gregory the Great, '
        'and later popes. Period of Lombard expansion in Italy.'
    )

    n4 += generate_summaries_for_collection(
        conn, 'epistulae_merowingici',
        'Merovingian Frankish royal correspondence (6th-7th century): '
        'letters of Frankish kings, queens, and bishops including '
        'Childebert II, Brunhild, Chlothar II, and their correspondents '
        'in Byzantium and the papacy.'
    )

    n4 += generate_summaries_for_collection(
        conn, 'faustus_riez',
        'Faustus of Riez (c.408-490), bishop of Riez in Provence. '
        'Semi-Pelagian theologian and correspondent of Sidonius Apollinaris. '
        'His letters deal with theological controversies (grace, free will) '
        'and literary friendship in late Roman Gaul.'
    )

    n4 += generate_summaries_for_collection(
        conn, 'epistulae_wisigothicae',
        'Visigothic Spain correspondence (6th-7th century): letters of '
        'Visigothic kings (Reccared, Sisebut, Chindaswinth), bishops '
        '(Isidore of Seville, Braulio of Zaragoza), and councils. '
        'Period of the Visigothic kingdom in Iberia.'
    )

    print(f"\n{'='*60}")
    print(f"TRANSLATION COMPLETE")
    print(f"  Latin translations: {n1 + n2 + n3}")
    print(f"  Scholarly summaries: {n4}")
    print(f"  Total: {n1 + n2 + n3 + n4}")
    print_progress(conn)
    conn.close()


if __name__ == '__main__':
    main()

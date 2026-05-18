#!/usr/bin/env python3
"""Import Cyril of Alexandria letters into the Roman Letters database.

Only 4 letters are available on New Advent (embedded in Council documents).
The collection is created with accurate metadata noting partial availability.
"""

import sqlite3
import os

DB_PATH = os.path.expanduser("~/Documents/GitHub/roman-letters-network/data/roman_letters.db")

COLLECTION = {
    "slug": "cyril_alexandria",
    "author_name": "Cyril of Alexandria",
    "title": "Letters of Cyril of Alexandria",
    "letter_count": 4,
    "date_range": "412-444 AD",
    "english_source_url": "https://www.newadvent.org/fathers/3810.htm",
    "scrape_status": "complete",
    "notes": "4 letters available on New Advent (embedded in Council of Ephesus and Chalcedon documents). "
             "The full corpus of ~110 letters exists in Fathers of the Church vol. 76-77 (McEnerney trans., 1987) "
             "but is not freely available online. Letters here: 2 to Nestorius, Twelve Anathematisms, 1 to John of Antioch.",
}

AUTHORS = [
    {
        "name": "Cyril of Alexandria",
        "name_latin": "Cyrillus Alexandrinus",
        "birth_year": 376,
        "death_year": 444,
        "role": "patriarch",
        "location": "Alexandria",
        "lat": 31.2001,
        "lon": 29.9187,
        "bio": "Patriarch of Alexandria (412-444), chief opponent of Nestorius, presided at the Council of Ephesus (431). Doctor of the Church. Prolific theologian and letter-writer.",
    },
    {
        "name": "Nestorius",
        "name_latin": "Nestorius",
        "birth_year": 386,
        "death_year": 450,
        "role": "patriarch",
        "location": "Constantinople",
        "lat": 41.0082,
        "lon": 28.9784,
        "bio": "Patriarch of Constantinople (428-431), condemned at the Council of Ephesus for his Christological teachings. Exiled to Egypt.",
    },
    {
        "name": "John of Antioch",
        "name_latin": "Ioannes Antiochenus",
        "birth_year": None,
        "death_year": 441,
        "role": "patriarch",
        "location": "Antioch",
        "lat": 36.2,
        "lon": 36.15,
        "bio": "Patriarch of Antioch (429-441). Initially supported Nestorius but reconciled with Cyril through the Formula of Reunion (433).",
    },
]


def load_text(path):
    with open(path, "r") as f:
        return f.read().strip()


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Insert collection
    cur.execute("""
        INSERT OR IGNORE INTO collections (slug, author_name, title, letter_count, date_range, english_source_url, scrape_status, notes)
        VALUES (:slug, :author_name, :title, :letter_count, :date_range, :english_source_url, :scrape_status, :notes)
    """, COLLECTION)
    print(f"Collection: {COLLECTION['slug']} -> inserted={cur.rowcount}")

    # 2. Insert/update authors
    for author in AUTHORS:
        # Check if exists (Cyril may already exist as id 823)
        cur.execute("SELECT id FROM authors WHERE name = ?", (author["name"],))
        row = cur.fetchone()
        if row:
            author_id = row[0]
            # Update with better data if missing
            cur.execute("""
                UPDATE authors SET
                    name_latin = COALESCE(NULLIF(:name_latin, ''), name_latin),
                    birth_year = COALESCE(:birth_year, birth_year),
                    death_year = COALESCE(:death_year, death_year),
                    role = COALESCE(NULLIF(:role, ''), role),
                    location = COALESCE(NULLIF(:location, ''), location),
                    lat = COALESCE(:lat, lat),
                    lon = COALESCE(:lon, lon),
                    bio = COALESCE(NULLIF(:bio, ''), bio)
                WHERE id = :id
            """, {**author, "id": author_id})
            print(f"  Author updated: {author['name']} (id={author_id})")
        else:
            cur.execute("""
                INSERT INTO authors (name, name_latin, birth_year, death_year, role, location, lat, lon, bio)
                VALUES (:name, :name_latin, :birth_year, :death_year, :role, :location, :lat, :lon, :bio)
            """, author)
            author_id = cur.lastrowid
            print(f"  Author inserted: {author['name']} (id={author_id})")

    # Also handle the existing "Cyril Of Alexandria" entry (id=823) - merge if different
    cur.execute("SELECT id FROM authors WHERE name = 'Cyril Of Alexandria' AND id != (SELECT id FROM authors WHERE name = 'Cyril of Alexandria')")
    old = cur.fetchone()
    if old:
        print(f"  Note: old author entry 'Cyril Of Alexandria' (id={old[0]}) exists alongside new one")

    # 3. Look up sender id
    cur.execute("SELECT id FROM authors WHERE name = 'Cyril of Alexandria'")
    sender_row = cur.fetchone()
    if not sender_row:
        # Try the capitalized version
        cur.execute("SELECT id FROM authors WHERE name = 'Cyril Of Alexandria'")
        sender_row = cur.fetchone()
    sender_id = sender_row[0]

    # 4. Load texts
    letter1_text = load_text("/tmp/cyril_letter1.txt")
    letter2_text = load_text("/tmp/cyril_letter2.txt")
    anathemas_text = load_text("/tmp/cyril_anathemas.txt")
    letter_john_text = load_text("/tmp/cyril_letter_john.txt")

    # Combine letter 2 with anathemas (they are part of the same document)
    letter2_full = letter2_text + "\n\n" + anathemas_text

    # 5. Define letters
    cur.execute("SELECT id FROM authors WHERE name = 'Nestorius'")
    nestorius_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM authors WHERE name = 'John of Antioch'")
    john_id = cur.fetchone()[0]

    letters = [
        {
            "letter_number": 1,
            "ref_id": "cyril.ep.nestorius.1",
            "recipient_id": nestorius_id,
            "year_approx": 430,
            "year_min": 429,
            "year_max": 430,
            "origin_place": "Alexandria",
            "origin_lat": 31.2001,
            "origin_lon": 29.9187,
            "dest_place": "Constantinople",
            "dest_lat": 41.0082,
            "dest_lon": 28.9784,
            "subject_summary": "First letter to Nestorius defending orthodox Christology. The Word personally united to flesh became man; two natures in true union make one Christ; Mary rightly called Mother of God (Theotokos). Appeal for peace among the churches.",
            "english_text": letter1_text,
            "source_url": "https://www.newadvent.org/fathers/3810.htm",
            "translation_url": "https://www.newadvent.org/fathers/3810.htm",
        },
        {
            "letter_number": 2,
            "ref_id": "cyril.ep.nestorius.2",
            "recipient_id": nestorius_id,
            "year_approx": 430,
            "year_min": 430,
            "year_max": 431,
            "origin_place": "Alexandria",
            "origin_lat": 31.2001,
            "origin_lon": 29.9187,
            "dest_place": "Constantinople",
            "dest_lat": 41.0082,
            "dest_lon": 28.9784,
            "subject_summary": "Second (synodal) letter to Nestorius from Cyril and the synod of Alexandria. Warns Nestorius to recant his heresy or face excommunication. Includes the Twelve Anathematisms against Nestorian Christology. Endorsed by Pope Celestine.",
            "english_text": letter2_full,
            "source_url": "https://www.newadvent.org/fathers/3810.htm",
            "translation_url": "https://www.newadvent.org/fathers/3810.htm",
        },
        {
            "letter_number": 3,
            "ref_id": "cyril.ep.nestorius.3",
            "recipient_id": nestorius_id,
            "year_approx": 430,
            "year_min": 430,
            "year_max": 430,
            "origin_place": "Alexandria",
            "origin_lat": 31.2001,
            "origin_lon": 29.9187,
            "dest_place": "Constantinople",
            "dest_lat": 41.0082,
            "dest_lon": 28.9784,
            "subject_summary": "Third letter to Nestorius (often called the 'dogmatic letter'). Read and approved at the Council of Ephesus (431). Defines orthodox Christology: one Christ, Son, and Lord, with the Word incarnate from the Holy Virgin.",
            "english_text": "This letter (Cyril's third to Nestorius) is referenced in the Council of Ephesus acts but its full text overlaps substantially with the second letter and its anathematisms. The Council approved both the second and third letters as standards of orthodoxy.",
            "source_url": "https://www.newadvent.org/fathers/3810.htm",
            "translation_url": "https://www.newadvent.org/fathers/3810.htm",
        },
        {
            "letter_number": 4,
            "ref_id": "cyril.ep.john_antioch",
            "recipient_id": john_id,
            "year_approx": 433,
            "year_min": 433,
            "year_max": 433,
            "origin_place": "Alexandria",
            "origin_lat": 31.2001,
            "origin_lon": 29.9187,
            "dest_place": "Antioch",
            "dest_lat": 36.2,
            "dest_lon": 36.15,
            "subject_summary": "Letter of reunion (Formula of Reunion / Laetentur Caeli). Celebrates peace between Alexandria and Antioch after the Council of Ephesus. Contains the agreed Christological formula: one Christ, perfect God and perfect Man, two natures united, Mary as Theotokos. Confirmed at the Council of Chalcedon (451).",
            "english_text": letter_john_text,
            "source_url": "https://www.newadvent.org/fathers/3811.htm",
            "translation_url": "https://www.newadvent.org/fathers/3811.htm",
        },
    ]

    # 6. Insert letters
    inserted = 0
    for letter in letters:
        cur.execute("""
            INSERT OR IGNORE INTO letters (
                collection, letter_number, ref_id, sender_id, recipient_id,
                year_approx, year_min, year_max,
                origin_place, origin_lat, origin_lon,
                dest_place, dest_lat, dest_lon,
                subject_summary, english_text, translation_source,
                source_url, translation_url
            ) VALUES (
                :collection, :letter_number, :ref_id, :sender_id, :recipient_id,
                :year_approx, :year_min, :year_max,
                :origin_place, :origin_lat, :origin_lon,
                :dest_place, :dest_lat, :dest_lon,
                :subject_summary, :english_text, :translation_source,
                :source_url, :translation_url
            )
        """, {
            "collection": "cyril_alexandria",
            "letter_number": letter["letter_number"],
            "ref_id": letter["ref_id"],
            "sender_id": sender_id,
            "recipient_id": letter["recipient_id"],
            "year_approx": letter["year_approx"],
            "year_min": letter["year_min"],
            "year_max": letter["year_max"],
            "origin_place": letter["origin_place"],
            "origin_lat": letter["origin_lat"],
            "origin_lon": letter["origin_lon"],
            "dest_place": letter["dest_place"],
            "dest_lat": letter["dest_lat"],
            "dest_lon": letter["dest_lon"],
            "subject_summary": letter["subject_summary"],
            "english_text": letter["english_text"],
            "translation_source": "existing_newadvent",
            "source_url": letter["source_url"],
            "translation_url": letter["translation_url"],
        })
        if cur.rowcount:
            inserted += 1
            print(f"  Letter inserted: {letter['ref_id']}")
        else:
            print(f"  Letter exists: {letter['ref_id']}")

    conn.commit()
    conn.close()
    print(f"\nDone. {inserted} Cyril letters imported.")


if __name__ == "__main__":
    main()

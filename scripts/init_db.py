#!/usr/bin/env python3
"""Initialize the SQLite database and seed it with known collections and authors."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')

# Major late antique letter collections (300-600 AD)
# These are the core collections Wyman would have studied
COLLECTIONS = [
    {
        'slug': 'ambrose_milan',
        'author_name': 'Ambrose of Milan',
        'title': 'Epistulae',
        'letter_count': 91,
        'date_range': '374-397',
        'latin_source_url': 'https://www.thelatinlibrary.com/ambrose.html',
        'english_source_url': 'https://www.newadvent.org/fathers/3403.htm',
    },
    {
        'slug': 'augustine_hippo',
        'author_name': 'Augustine of Hippo',
        'title': 'Epistulae',
        'letter_count': 308,
        'date_range': '386-430',
        'latin_source_url': 'https://www.thelatinlibrary.com/augustine.html',
        'english_source_url': 'https://www.newadvent.org/fathers/1102.htm',
    },
    {
        'slug': 'jerome',
        'author_name': 'Jerome',
        'title': 'Epistulae',
        'letter_count': 154,
        'date_range': '370-420',
        'latin_source_url': 'https://www.thelatinlibrary.com/jerome.html',
        'english_source_url': 'https://www.newadvent.org/fathers/3001.htm',
    },
    {
        'slug': 'paulinus_nola',
        'author_name': 'Paulinus of Nola',
        'title': 'Epistulae',
        'letter_count': 51,
        'date_range': '393-431',
        'latin_source_url': 'https://www.thelatinlibrary.com/paulinus.html',
        'english_source_url': None,
    },
    {
        'slug': 'sidonius_apollinaris',
        'author_name': 'Sidonius Apollinaris',
        'title': 'Epistulae (9 books)',
        'letter_count': 147,
        'date_range': '455-480',
        'latin_source_url': 'https://www.thelatinlibrary.com/sidonius.html',
        'english_source_url': None,
    },
    {
        'slug': 'symmachus',
        'author_name': 'Quintus Aurelius Symmachus',
        'title': 'Epistulae (10 books)',
        'letter_count': 900,
        'date_range': '365-402',
        'latin_source_url': 'https://www.thelatinlibrary.com/symmachus.html',
        'english_source_url': None,
    },
    {
        'slug': 'cassiodorus',
        'author_name': 'Cassiodorus',
        'title': 'Variae (12 books)',
        'letter_count': 468,
        'date_range': '506-538',
        'latin_source_url': 'https://www.thelatinlibrary.com/cassiodorus.html',
        'english_source_url': None,
    },
    {
        'slug': 'ennodius',
        'author_name': 'Ennodius of Pavia',
        'title': 'Epistulae',
        'letter_count': 297,
        'date_range': '493-521',
        'latin_source_url': None,
        'english_source_url': None,
    },
    {
        'slug': 'avitus_vienne',
        'author_name': 'Avitus of Vienne',
        'title': 'Epistulae',
        'letter_count': 96,
        'date_range': '490-518',
        'latin_source_url': None,
        'english_source_url': None,
    },
    {
        'slug': 'ruricius_limoges',
        'author_name': 'Ruricius of Limoges',
        'title': 'Epistulae (2 books)',
        'letter_count': 65,
        'date_range': '480-510',
        'latin_source_url': None,
        'english_source_url': None,
    },
    {
        'slug': 'gregory_great',
        'author_name': 'Pope Gregory the Great',
        'title': 'Registrum Epistularum (14 books)',
        'letter_count': 854,
        'date_range': '590-604',
        'latin_source_url': 'https://www.thelatinlibrary.com/gregory.html',
        'english_source_url': 'https://www.newadvent.org/fathers/3602.htm',
    },
    {
        'slug': 'leo_great',
        'author_name': 'Pope Leo the Great',
        'title': 'Epistulae',
        'letter_count': 173,
        'date_range': '440-461',
        'latin_source_url': None,
        'english_source_url': 'https://www.newadvent.org/fathers/3604.htm',
    },
    {
        'slug': 'basil_caesarea',
        'author_name': 'Basil of Caesarea',
        'title': 'Epistulae',
        'letter_count': 368,
        'date_range': '357-378',
        'latin_source_url': None,
        'english_source_url': 'https://www.newadvent.org/fathers/3202.htm',
    },
    {
        'slug': 'gregory_nazianzus',
        'author_name': 'Gregory of Nazianzus',
        'title': 'Epistulae',
        'letter_count': 249,
        'date_range': '362-390',
        'latin_source_url': None,
        'english_source_url': None,
    },
]

# Key known people from these letters (seed data)
AUTHORS_SEED = [
    ('Ambrose of Milan', 'Ambrosius Mediolanensis', 340, 397, 'bishop', 'Milan', 45.4642, 9.1900),
    ('Augustine of Hippo', 'Aurelius Augustinus', 354, 430, 'bishop', 'Hippo Regius', 36.8833, 7.7500),
    ('Jerome', 'Eusebius Hieronymus', 347, 420, 'priest/scholar', 'Bethlehem', 31.7054, 35.2024),
    ('Paulinus of Nola', 'Pontius Meropius Paulinus', 354, 431, 'bishop', 'Nola', 40.9263, 14.5278),
    ('Sidonius Apollinaris', 'Gaius Sollius Modestus Sidonius Apollinaris', 430, 489, 'bishop', 'Clermont', 45.7772, 3.0870),
    ('Quintus Aurelius Symmachus', 'Quintus Aurelius Symmachus', 345, 402, 'senator', 'Rome', 41.8967, 12.4822),
    ('Cassiodorus', 'Flavius Magnus Aurelius Cassiodorus', 485, 585, 'senator/monk', 'Ravenna', 44.4184, 12.2035),
    ('Ennodius of Pavia', 'Magnus Felix Ennodius', 473, 521, 'bishop', 'Pavia', 45.1847, 9.1582),
    ('Avitus of Vienne', 'Alcimus Ecdicius Avitus', 450, 518, 'bishop', 'Vienne', 45.5242, 4.8783),
    ('Ruricius of Limoges', 'Ruricius', 440, 510, 'bishop', 'Limoges', 45.8336, 1.2611),
    ('Pope Gregory the Great', 'Gregorius Magnus', 540, 604, 'pope', 'Rome', 41.8967, 12.4822),
    ('Pope Leo the Great', 'Leo Magnus', 400, 461, 'pope', 'Rome', 41.8967, 12.4822),
    ('Basil of Caesarea', 'Basilius Caesariensis', 330, 379, 'bishop', 'Caesarea', 38.7312, 35.4787),
    ('Gregory of Nazianzus', 'Gregorius Nazianzenus', 329, 390, 'bishop', 'Nazianzus', 38.4500, 34.2833),
    ('Emperor Valentinian', 'Valentinianus', 321, 375, 'emperor', 'Milan', 45.4642, 9.1900),
    ('Emperor Theodosius I', 'Theodosius', 347, 395, 'emperor', 'Constantinople', 41.0082, 28.9784),
    ('Lupicinus', None, None, None, 'bishop', 'Lyon', 45.7640, 4.8357),
    ('Faustus of Riez', 'Faustus Reiensis', 405, 495, 'bishop', 'Riez', 43.8167, 6.0833),
]


def init_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Run schema
    with open(SCHEMA_PATH) as f:
        cursor.executescript(f.read())

    # Seed collections
    for c in COLLECTIONS:
        cursor.execute('''
            INSERT OR IGNORE INTO collections (slug, author_name, title, letter_count, date_range,
                latin_source_url, english_source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (c['slug'], c['author_name'], c['title'], c['letter_count'],
              c['date_range'], c['latin_source_url'], c['english_source_url']))

    # Seed known authors/people
    for a in AUTHORS_SEED:
        cursor.execute('''
            INSERT OR IGNORE INTO authors (name, name_latin, birth_year, death_year, role, location, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', a)

    conn.commit()

    # Report
    cursor.execute('SELECT COUNT(*) FROM collections')
    nc = cursor.fetchone()[0]
    cursor.execute('SELECT SUM(letter_count) FROM collections')
    nl = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM authors')
    na = cursor.fetchone()[0]

    print(f"Database initialized at: {os.path.abspath(DB_PATH)}")
    print(f"  Collections: {nc}")
    print(f"  Estimated total letters: {nl}")
    print(f"  Known people: {na}")

    conn.close()


if __name__ == '__main__':
    init_database()

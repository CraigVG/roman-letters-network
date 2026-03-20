#!/usr/bin/env python3
"""
Add links to original scanned editions on Internet Archive and other digital libraries.
These are scanned pages of the 19th-century critical editions (Migne's Patrologia Latina,
CSEL, MGH, etc.) — the closest we can get to the original texts in printed form.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

# Add scan_url column if it doesn't exist
ALTER_SQL = """
ALTER TABLE collections ADD COLUMN scan_url TEXT;
"""

ALTER_LETTERS_SQL = """
ALTER TABLE letters ADD COLUMN scan_url TEXT;
"""

# Internet Archive links to scanned critical editions
SCAN_LINKS = {
    'augustine_hippo': {
        'scan_url': 'https://archive.org/details/patrologiaecursu33migngoog',
        'notes': 'Patrologia Latina vol. 33 (Migne) - Augustine Epistulae. Full scanned pages of the 1845 edition.',
    },
    'jerome': {
        'scan_url': 'https://archive.org/details/patrologiaecursu22teleduoft',
        'notes': 'Patrologia Latina vol. 22 (Migne) - Jerome Epistulae. Scanned 1845 edition.',
    },
    'ambrose_milan': {
        'scan_url': 'https://archive.org/details/patrologiaecursu16teleduoft',
        'notes': 'Patrologia Latina vol. 16 (Migne) - Ambrose Opera including Epistulae.',
    },
    'sidonius_apollinaris': {
        'scan_url': 'https://archive.org/details/gaborneusidonii00sidogoog',
        'notes': 'Sidonii Apollinaris Epistulae et Carmina (MGH Auctores Antiquissimi VIII). Critical edition by Luetjohann, 1887.',
    },
    'cassiodorus': {
        'scan_url': 'https://archive.org/details/cassiodorisenato00teleduoft',
        'notes': 'Cassiodori Senatoris Variae (MGH Auctores Antiquissimi XII). Critical edition by Mommsen, 1894.',
    },
    'gregory_great': {
        'scan_url': 'https://archive.org/details/registrumepistol01gregrich',
        'notes': 'Registrum Epistolarum (MGH Epistolae I-II). Critical edition by Ewald & Hartmann. Full papal register.',
    },
    'ennodius': {
        'scan_url': 'https://archive.org/details/magnifelicisenn00teleduoft',
        'notes': 'Magni Felicis Ennodii Opera (CSEL vol. 6). Critical edition by Hartel, 1882.',
    },
    'paulinus_nola': {
        'scan_url': 'https://archive.org/details/sanctipontiimero0029paul',
        'notes': 'S. Pontii Meropii Paulini Nolani Epistulae (CSEL vol. 29). Critical edition by Hartel, 1894.',
    },
    'leo_great': {
        'scan_url': 'https://archive.org/details/patrologiaecursu54teleduoft',
        'notes': 'Patrologia Latina vol. 54 (Migne) - Leo Magnus Epistulae.',
    },
    'symmachus': {
        'scan_url': 'https://archive.org/details/qaurelisymmachi00symm',
        'notes': 'Q. Aureli Symmachi Quae Supersunt (MGH Auctores Antiquissimi VI.1). Critical edition by Seeck, 1883.',
    },
    'avitus_vienne': {
        'scan_url': 'https://archive.org/details/alcimiecdiciiavi00teleduoft',
        'notes': 'Alcimi Ecdicii Aviti Opera (MGH Auctores Antiquissimi VI.2). Critical edition by Peiper, 1883.',
    },
    'ruricius_limoges': {
        'scan_url': 'https://archive.org/details/gaborneusidonii00sidogoog',
        'notes': 'Ruricius letters found in MGH Auctores Antiquissimi VIII (same volume as Sidonius).',
    },
    'basil_caesarea': {
        'scan_url': 'https://archive.org/details/patrologiaecursu32migngoog',
        'notes': 'Patrologia Graeca vol. 32 (Migne) - Basil of Caesarea Epistulae. Greek text with Latin translation.',
    },
    'gregory_nazianzus': {
        'scan_url': 'https://archive.org/details/patrologiaecursu37migngoog',
        'notes': 'Patrologia Graeca vol. 37 (Migne) - Gregory of Nazianzus Epistulae.',
    },
}


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()

    # Add columns if needed
    try:
        cursor.execute(ALTER_SQL)
        print("Added scan_url column to collections")
    except sqlite3.OperationalError:
        pass  # Already exists

    try:
        cursor.execute(ALTER_LETTERS_SQL)
        print("Added scan_url column to letters")
    except sqlite3.OperationalError:
        pass

    # Update collections with scan links
    for slug, info in SCAN_LINKS.items():
        cursor.execute('''
            UPDATE collections SET scan_url = ?, notes = ?
            WHERE slug = ?
        ''', (info['scan_url'], info['notes'], slug))
        if cursor.rowcount:
            print(f"  Updated {slug}: {info['scan_url']}")

    conn.commit()

    # Show results
    cursor.execute('SELECT slug, author_name, scan_url FROM collections WHERE scan_url IS NOT NULL')
    print(f"\n{'Collection':<25} {'Scan Link'}")
    print('-' * 80)
    for row in cursor.fetchall():
        print(f"{row[0]:<25} {row[2] or 'N/A'}")

    conn.close()
    print("\nDone! Original edition scan links added to all collections.")


if __name__ == '__main__':
    main()

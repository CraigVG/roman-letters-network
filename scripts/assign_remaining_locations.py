#!/usr/bin/env python3
"""
Assign lat/lon coordinates to authors who currently lack them.

Logic:
- Anonymous figures in basil_caesarea collection -> Caesarea Mazaca (Cappadocia)
- Chilo, disciple (basil_caesarea) -> Caesarea
- Gregory of Nazianzus (bishop, location=Nazianzus) -> Nazianzus / near Caesarea
- Truly unknowable -> left NULL
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

# ── City coordinate lookup ──────────────────────────────────────────────────

CITIES = {
    # Italian
    'Rome':          (41.8967, 12.4822),
    'Ravenna':       (44.4184, 12.2035),
    'Milan':         (45.4642,  9.1900),
    'Naples':        (40.8518, 14.2681),
    'Syracuse':      (37.0755, 15.2866),
    'Terracina':     (41.2928, 13.2483),
    'Pavia':         (45.1847,  9.1582),
    'Cagliari':      (39.2238,  9.1217),
    # North African
    'Carthage':      (36.8065, 10.1815),
    'Hippo Regius':  (36.8833,  7.7500),
    'Calama':        (36.4530,  7.4413),
    'Thagaste':      (36.2661,  8.0017),
    'Madauros':      (36.3833,  7.6500),
    # Gallic
    'Arles':         (43.6767,  4.6278),
    'Marseilles':    (43.2965,  5.3698),
    'Vienne':        (45.5242,  4.8783),
    'Lyon':          (45.7640,  4.8357),
    'Clermont':      (45.7772,  3.0870),
    'Tours':         (47.3941,  0.6848),
    'Bordeaux':      (44.8378, -0.5792),
    # Eastern
    'Constantinople': (41.0082, 28.9784),
    'Antioch':       (36.2028, 36.1606),
    'Alexandria':    (31.2001, 29.9187),
    'Jerusalem':     (31.7683, 35.2137),
    'Bethlehem':     (31.7054, 35.2024),
    'Caesarea':      (38.7312, 35.4787),   # Caesarea Mazaca / Kayseri
    'Thessalonica':  (40.6401, 22.9444),
    'Ephesus':       (37.9414, 27.3417),
    # Extra: Nazianzus is ~100 km SW of Caesarea Mazaca
    'Nazianzus':     (38.2167, 34.5000),
}

# ── Inference rules ─────────────────────────────────────────────────────────

def infer_location(name: str, role: str | None, location: str | None,
                   notes: str | None, collections: str | None):
    """
    Return (lat, lon, city_label) or (None, None, None) if truly unknown.
    """
    name_l      = (name      or '').lower()
    role_l      = (role      or '').lower()
    location_l  = (location  or '').lower()
    notes_l     = (notes     or '').lower()
    colls       = (collections or '').lower()

    # ── Named-location hints in the author's location field OR name ──
    # Check both, so "Ambrose, of Milan" and "Ascholius, of Thessalonica" etc. resolve correctly
    for city, coords in CITIES.items():
        city_l = city.lower()
        if city_l in location_l or city_l in name_l:
            return coords[0], coords[1], city

    # ── Gregory of Nazianzus ──
    if 'nazianzus' in name_l or 'nazianzus' in location_l:
        c = CITIES['Nazianzus']
        return c[0], c[1], 'Nazianzus'

    # ── Anonymous / unnamed figures in Basil of Caesarea's correspondence ──
    if 'basil_caesarea' in colls and 'anonymous' in name_l:
        c = CITIES['Caesarea']
        return c[0], c[1], 'Caesarea (default for Basil correspondents)'

    # ── Disciples / associates in Basil's circle ──
    if 'basil_caesarea' in colls and ('disciple' in name_l or 'disciple' in role_l):
        c = CITIES['Caesarea']
        return c[0], c[1], 'Caesarea (Basil disciple)'

    # ── Generic Basil of Caesarea correspondents (any remaining) ──
    if 'basil_caesarea' in colls and not any(
            key in colls for key in ('gregory_great', 'augustine', 'jerome')):
        c = CITIES['Caesarea']
        return c[0], c[1], 'Caesarea (Basil correspondent default)'

    # ── Gregory the Great correspondents ──
    if 'gregory_great' in colls:
        if 'exarch' in name_l or 'exarch' in role_l:
            c = CITIES['Ravenna']
            return c[0], c[1], 'Ravenna (Exarch)'
        if 'patrician' in name_l or 'patrician' in role_l:
            c = CITIES['Rome']
            return c[0], c[1], 'Rome (Patrician)'
        if 'subdeacon' in role_l or 'subdeacon' in name_l:
            c = CITIES['Rome']
            return c[0], c[1], 'Rome (Subdeacon, Gregory correspondent)'
        # Default for Gregory recipients
        c = CITIES['Rome']
        return c[0], c[1], 'Rome (Gregory correspondent default)'

    # ── Augustine correspondents in Africa ──
    if 'augustine' in colls:
        c = CITIES['Hippo Regius']
        return c[0], c[1], 'Hippo Regius (Augustine correspondent default)'

    # ── Jerome correspondents ──
    if 'jerome' in colls:
        if 'bethlehem' in location_l or 'bethlehem' in notes_l:
            c = CITIES['Bethlehem']
            return c[0], c[1], 'Bethlehem'
        c = CITIES['Rome']
        return c[0], c[1], 'Rome (Jerome correspondent default)'

    # ── Truly unknown ──
    return None, None, None


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch all authors without lat, along with the collections they appear in
    cursor.execute('''
        SELECT
            a.id,
            a.name,
            a.role,
            a.location,
            a.notes,
            GROUP_CONCAT(DISTINCT l.collection) AS collections
        FROM authors a
        LEFT JOIN letters l ON (l.sender_id = a.id OR l.recipient_id = a.id)
        WHERE a.lat IS NULL
        GROUP BY a.id
        ORDER BY a.name
    ''')
    rows = cursor.fetchall()

    print(f"Found {len(rows)} author(s) without lat/lon.\n")

    assigned = 0
    skipped  = 0

    updates = []
    for row in rows:
        author_id  = row['id']
        name       = row['name']
        role       = row['role']
        location   = row['location']
        notes      = row['notes']
        collections = row['collections']

        lat, lon, label = infer_location(name, role, location, notes, collections)

        if lat is not None:
            updates.append((lat, lon, author_id))
            print(f"  ASSIGN  [{author_id:3d}] {name!r:40s} -> {label}  ({lat:.4f}, {lon:.4f})")
            assigned += 1
        else:
            print(f"  SKIP    [{author_id:3d}] {name!r:40s}  (collections={collections})")
            skipped += 1

    # Apply all updates in one transaction
    if updates:
        cursor.executemany(
            'UPDATE authors SET lat = ?, lon = ? WHERE id = ?',
            updates
        )
        conn.commit()
        print(f"\nCommitted {len(updates)} update(s).")
    else:
        print("\nNo updates to commit.")

    conn.close()

    print(f"\nSummary: {assigned} assigned, {skipped} left NULL (truly unknown).")
    return assigned, skipped


if __name__ == '__main__':
    main()

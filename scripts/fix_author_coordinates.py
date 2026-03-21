#!/usr/bin/env python3
"""
Fix missing coordinates for 20 authors and recompute letter distances.
"""

import sqlite3
import math
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

# (id, location, lat, lon)
AUTHOR_UPDATES = [
    (497, "Rome", 41.9028, 12.4964),
    (492, "Alexandria", 31.2001, 29.9187),
    (502, "Cahors", 44.4475, 1.4402),
    (1491, "Rome", 41.9028, 12.4964),
    (496, "Toulouse", 43.6047, 1.4442),
    (1488, "Rome", 41.9028, 12.4964),
    (1489, "Rome", 41.9028, 12.4964),
    (501, "Aachen", 50.7753, 6.0839),
    (493, "Constantinople", 41.0082, 28.9784),
    (505, "Rome", 41.9028, 12.4964),
    (504, "Rome", 41.9028, 12.4964),
    (499, "Marseille", 43.2965, 5.3698),
    (503, "Carthage", 36.8528, 10.3234),
    (494, "Constantinople", 41.0082, 28.9784),
    (1490, "Rome", 41.9028, 12.4964),
    (498, "Bobbio", 44.7667, 9.3833),
    (500, "Jarrow", 54.9783, -1.4728),
    (513, "Valencia", 39.4699, -0.3763),
    (495, "Rome", 41.9028, 12.4964),
    (510, "Toledo", 39.8628, -4.0273),
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Update author coordinates and location
    authors_updated = 0
    for author_id, location, lat, lon in AUTHOR_UPDATES:
        cur.execute(
            "UPDATE authors SET lat = ?, lon = ?, location = ? WHERE id = ? AND (lat IS NULL OR lon IS NULL)",
            (lat, lon, location, author_id)
        )
        if cur.rowcount > 0:
            authors_updated += 1

    print(f"Authors updated with coordinates: {authors_updated}")

    # 2. Update origin_lat/lon on letters where sender now has coordinates but letter doesn't
    cur.execute("""
        UPDATE letters
        SET origin_lat = a.lat, origin_lon = a.lon
        FROM authors a
        WHERE letters.sender_id = a.id
          AND a.lat IS NOT NULL AND a.lon IS NOT NULL
          AND (letters.origin_lat IS NULL OR letters.origin_lon IS NULL)
    """)
    origins_updated = cur.rowcount
    print(f"Letters with origin coordinates filled: {origins_updated}")

    # 3. Update dest_lat/lon on letters where recipient now has coordinates but letter doesn't
    cur.execute("""
        UPDATE letters
        SET dest_lat = a.lat, dest_lon = a.lon
        FROM authors a
        WHERE letters.recipient_id = a.id
          AND a.lat IS NOT NULL AND a.lon IS NOT NULL
          AND (letters.dest_lat IS NULL OR letters.dest_lon IS NULL)
    """)
    dests_updated = cur.rowcount
    print(f"Letters with destination coordinates filled: {dests_updated}")

    # 4. Compute distance_km for letters that now have both origin and dest coords but no distance
    cur.execute("""
        SELECT id, origin_lat, origin_lon, dest_lat, dest_lon
        FROM letters
        WHERE distance_km IS NULL
          AND origin_lat IS NOT NULL AND origin_lon IS NOT NULL
          AND dest_lat IS NOT NULL AND dest_lon IS NOT NULL
    """)
    rows = cur.fetchall()
    distances_computed = 0
    for letter_id, olat, olon, dlat, dlon in rows:
        dist = haversine(olat, olon, dlat, dlon)
        cur.execute("UPDATE letters SET distance_km = ? WHERE id = ?", (round(dist, 2), letter_id))
        distances_computed += 1

    print(f"Distances computed: {distances_computed}")

    # 5. Report totals
    cur.execute("SELECT COUNT(*) FROM letters WHERE distance_km IS NOT NULL")
    total_with_distance = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM letters")
    total_letters = cur.fetchone()[0]
    print(f"\nTotal letters with distance data: {total_with_distance} / {total_letters}")

    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()

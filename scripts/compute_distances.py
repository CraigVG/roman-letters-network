#!/usr/bin/env python3
"""
compute_distances.py

For every letter with sender + recipient coordinates (via authors table),
calculate haversine great-circle distance in km. Adds a `distance_km` column
to the letters table and prints summary stats by decade.
"""

import sqlite3
import math
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')


def haversine(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance between two points in km."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    # 1. Add distance_km column if it doesn't exist
    cur.execute("PRAGMA table_info(letters)")
    columns = [row[1] for row in cur.fetchall()]
    if 'distance_km' not in columns:
        cur.execute("ALTER TABLE letters ADD COLUMN distance_km REAL")
        print("Added distance_km column to letters table.")
    else:
        print("distance_km column already exists.")

    # 2. Fetch all letters with sender + recipient coordinates via authors
    cur.execute("""
        SELECT l.id, a1.lat, a1.lon, a2.lat, a2.lon
        FROM letters l
        JOIN authors a1 ON l.sender_id = a1.id
        JOIN authors a2 ON l.recipient_id = a2.id
        WHERE a1.lat IS NOT NULL AND a1.lon IS NOT NULL
          AND a2.lat IS NOT NULL AND a2.lon IS NOT NULL
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} letters with sender + recipient coordinates.")

    # 3. Compute and store distances
    updated = 0
    for letter_id, s_lat, s_lon, r_lat, r_lon in rows:
        dist = haversine(s_lat, s_lon, r_lat, r_lon)
        cur.execute("UPDATE letters SET distance_km = ? WHERE id = ?", (round(dist, 1), letter_id))
        updated += 1

    conn.commit()
    print(f"Updated {updated} letters with distance values.")

    # 4. Print summary stats by decade
    print("\n" + "=" * 72)
    print(f"{'Decade':<10} {'Letters':>8} {'Avg km':>10} {'Max km':>10} {'Pairs':>8} {'>500km':>8}")
    print("=" * 72)

    cur.execute("""
        SELECT
            (year_approx / 10) * 10 as decade,
            COUNT(*) as letter_count,
            ROUND(AVG(distance_km), 0) as avg_dist,
            ROUND(MAX(distance_km), 0) as max_dist,
            COUNT(DISTINCT sender_id || '-' || recipient_id) as unique_pairs,
            SUM(CASE WHEN distance_km > 500 THEN 1 ELSE 0 END) as long_distance
        FROM letters
        WHERE distance_km IS NOT NULL AND year_approx IS NOT NULL
        GROUP BY decade
        ORDER BY decade
    """)

    for row in cur.fetchall():
        decade, count, avg_d, max_d, pairs, long_d = row
        pct_long = round(100 * long_d / count, 1) if count > 0 else 0
        print(f"{decade:<10} {count:>8} {avg_d:>10.0f} {max_d:>10.0f} {pairs:>8} {pct_long:>7.1f}%")

    # Overall stats
    cur.execute("""
        SELECT COUNT(*), ROUND(AVG(distance_km),0), ROUND(MAX(distance_km),0),
               ROUND(MIN(distance_km),0)
        FROM letters WHERE distance_km IS NOT NULL
    """)
    total, avg_all, max_all, min_all = cur.fetchone()
    print("=" * 72)
    print(f"Total: {total} letters | Avg: {avg_all:.0f} km | Max: {max_all:.0f} km | Min: {min_all:.0f} km")

    conn.close()


if __name__ == '__main__':
    main()

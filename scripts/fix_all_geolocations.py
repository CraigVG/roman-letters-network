#!/usr/bin/env python3
"""
fix_all_geolocations.py
Assign geographic coordinates to all authors in roman_letters.db who lack them.

Strategy (in priority order):
1. Name contains "of <City>" → map to that city
2. Explicit known-person mapping by name keywords
3. Role hints (pope, emperor, etc.)
4. Collection-based defaults
5. Generic "Mediterranean" fallback for truly unknown people
"""

import sqlite3
import re

DB_PATH = "/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db"

# ── Key cities ──────────────────────────────────────────────────────────────
CITIES = {
    "rome":           (41.8967, 12.4822),
    "constantinople": (41.0082, 28.9784),
    "carthage":       (36.8065, 10.1815),
    "alexandria":     (31.2001, 29.9187),
    "antioch":        (36.2028, 36.1606),
    "jerusalem":      (31.7683, 35.2137),
    "milan":          (45.4642,  9.1900),
    "ravenna":        (44.4184, 12.2035),
    "hippo":          (36.8833,  7.7500),
    "arles":          (43.6767,  4.6278),
    "mainz":          (50.0000,  8.2700),
    "cyrene":         (32.8200, 21.8600),
    "ptolemais":      (32.8200, 21.8600),
    "tours":          (47.3941,  0.6848),
    "vienne":         (45.5242,  4.8783),
    "limoges":        (45.8336,  1.2611),
    "caesarea":       (38.7312, 35.4787),
    "thessalonica":   (40.6401, 22.9444),
    "trier":          (49.7499,  6.6371),
    "marseilles":     (43.2965,  5.3698),
    "lyon":           (45.7640,  4.8357),
    "pavia":          (45.1847,  9.1582),
    "nola":           (40.9263, 14.5278),
    # additional cities that appear in theodoret names
    "samosata":       (37.5500, 38.5000),
    "edessa":         (37.1580, 38.7950),
    "emesa":          (34.7324, 36.7137),
    "apamea":         (35.4167, 36.4000),
    "sidon":          (33.5600, 35.3700),
    "berœa":          (36.2000, 37.1500),  # Beroea = Aleppo area, Syria
    "beroea":         (36.2000, 37.1500),
    "germanicia":     (37.3833, 36.9167),  # Kahramanmaraş, Turkey
    "doliche":        (37.5167, 37.6500),
    "constantina":    (36.3167, 36.4000),  # Constantina in Syria
    "colonia":        (37.8000, 36.5000),  # Colonia/Comana Cappadociae
    "cyprus":         (35.1264, 33.4299),
    "ephesus":        (37.9395, 27.3408),
    "corinth":        (37.9400, 22.9350),
    "athens":         (37.9838, 23.7275),
    "smyrna":         (38.4237, 27.1428),
    "nicaea":         (40.4267, 29.7183),
    "chalcedon":      (40.9900, 29.0300),
    "persian armenia": (39.9197, 41.2750),
    "armenia":        (40.0691, 45.0382),
}

# City aliases / alternate spellings → canonical key
CITY_ALIASES = {
    "marseille":   "marseilles",
    "lyons":       "lyon",
    "lugdunum":    "lyon",
    "mediolanum":  "milan",
    "ravenna":     "ravenna",
    "nicomedia":   (40.7667, 29.9333),  # direct coords
    "pergamum":    (39.1200, 27.1800),
    "pergamon":    (39.1200, 27.1800),
}

# ── Name-keyword → coordinates (for specific well-known people) ─────────────
NAMED_PERSON_MAP = [
    # theodoret_cyrrhus correspondents with "of <place>" in name
    ("of samosata",        CITIES["samosata"]),
    ("of edessa",          CITIES["edessa"]),
    ("of emesa",           CITIES["emesa"]),
    ("of apamea",          CITIES["apamea"]),
    ("of sidon",           CITIES["sidon"]),
    ("of berœa",           CITIES["berœa"]),
    ("of beroea",          CITIES["beroea"]),
    ("of germanicia",      CITIES["germanicia"]),
    ("of doliche",         CITIES["doliche"]),
    ("of constantina",     CITIES["constantina"]),
    ("of colonia",         CITIES["colonia"]),
    ("of antioch",         CITIES["antioch"]),
    ("of alexandria",      CITIES["alexandria"]),
    ("of rome",            CITIES["rome"]),
    ("of carthage",        CITIES["carthage"]),
    ("of constantinople",  CITIES["constantinople"]),
    ("of jerusalem",       CITIES["jerusalem"]),
    ("of milan",           CITIES["milan"]),
    ("of ravenna",         CITIES["ravenna"]),
    ("of hippo",           CITIES["hippo"]),
    ("of arles",           CITIES["arles"]),
    ("of caesarea",        CITIES["caesarea"]),
    ("of thessalonica",    CITIES["thessalonica"]),
    ("of trier",           CITIES["trier"]),
    ("of tours",           CITIES["tours"]),
    ("of vienne",          CITIES["vienne"]),
    ("of ephesus",         CITIES["ephesus"]),
    ("of cyprus",          CITIES["cyprus"]),
    ("of corinth",         CITIES["corinth"]),
    ("of persian armenia", CITIES["persian armenia"]),
    ("of armenia",         CITIES["armenia"]),
    ("monk of constantinople", CITIES["constantinople"]),
    ("archbishop of antioch",  CITIES["antioch"]),
    # Specific well-known people identifiable by name fragment
    ("synesius",           CITIES["ptolemais"]),
    ("julian the apostate", CITIES["constantinople"]),
    ("julian",             CITIES["constantinople"]),   # emperor Julian
    ("flavianus of constantinople", CITIES["constantinople"]),
    ("flavianus, of constantinople", CITIES["constantinople"]),
    ("proclus, of constantinople",   CITIES["constantinople"]),
    ("dioscorus",          CITIES["alexandria"]),   # Dioscorus of Alexandria
    ("nestorius",          CITIES["constantinople"]),
    ("ibas",               CITIES["edessa"]),
    ("domnus of antioch",  CITIES["antioch"]),
    ("domnus, of apamea",  CITIES["apamea"]),
    ("damianus, of sidon", CITIES["sidon"]),
    ("theoctistus, of berœa", CITIES["berœa"]),
    ("john, of germanicia", CITIES["germanicia"]),
    ("longinus, archimandrite of doliche", CITIES["doliche"]),
    ("sophronius, of constantina", CITIES["constantina"]),
    # Cyprian correspondents – all Carthage-area
    ("caldonius",          CITIES["carthage"]),
    ("celerinus",          CITIES["carthage"]),
    ("lucian",             CITIES["carthage"]),
    ("rogatianus",         CITIES["carthage"]),
    ("successus",          CITIES["carthage"]),
    ("fidus",              CITIES["carthage"]),
    ("pomponius",          CITIES["carthage"]),
    ("pompey",             CITIES["carthage"]),
    ("quintus",            CITIES["carthage"]),
    ("jubaianus",          CITIES["carthage"]),
    ("magnus",             CITIES["carthage"]),
    ("nemesianus",         CITIES["carthage"]),
    ("sergius",            CITIES["carthage"]),
    ("cornelius",          CITIES["rome"]),
    ("lucius of rome",     CITIES["rome"]),
    ("novatian",           CITIES["rome"]),
    # Gregory Nazianzus correspondents
    ("bosporius",          CITIES["caesarea"]),  # Colonia = region of Cappadocia
    # Role-based specific names
    ("archdeacon of rome", CITIES["rome"]),
]

# ── Collection-level defaults ────────────────────────────────────────────────
COLLECTION_DEFAULTS = {
    "ambrose_milan":        CITIES["milan"],
    "augustine_hippo":      CITIES["hippo"],
    "jerome":               CITIES["rome"],      # Jerome moved around but Rome is hub
    "paulinus_nola":        CITIES["nola"],
    "sidonius_apollinaris": CITIES["lyon"],       # Sidonius was bishop of Clermont; Lyon is close proxy
    "symmachus":            CITIES["rome"],
    "cyprian_carthage":     CITIES["carthage"],
    "gregory_nazianzus":    CITIES["caesarea"],
    "basil_caesarea":       CITIES["caesarea"],
    "theodoret_cyrrhus":    (36.8333, 36.8333),  # Cyrrhus, Syria (near Aleppo)
    "gregory_nyssa":        (40.3500, 36.0000),  # Nyssa, Cappadocia
    "john_chrysostom":      CITIES["constantinople"],
    "innocent_i":           CITIES["rome"],
    "leo_great":            CITIES["rome"],
    "gelasius_i":           CITIES["rome"],
    "hormisdas":            CITIES["rome"],
    "boniface":             CITIES["rome"],
    "isidore_pelusium":     (30.9700, 32.5500),  # Pelusium, Egypt (NE Nile Delta)
    "ennodius_pavia":       CITIES["pavia"],
    "julian_emperor":       CITIES["constantinople"],
    "synesius_cyrene":      CITIES["ptolemais"],
    "cassiodorus":          CITIES["ravenna"],
}

# ── Role-based defaults ──────────────────────────────────────────────────────
ROLE_DEFAULTS = {
    "pope":      CITIES["rome"],
    "emperor":   CITIES["constantinople"],
    "bishop":    None,   # too ambiguous without location
    "presbyter": None,
}

# ── Fallback for letters-based location inference ────────────────────────────
MEDITERRANEAN_CENTER = (38.0, 20.0)


def normalize(s):
    """Lowercase, strip extra spaces."""
    if not s:
        return ""
    return re.sub(r"\s+", " ", s.strip().lower())


def match_city_in_text(text):
    """Return (lat, lon) if a known city appears in text."""
    t = normalize(text)
    # Try aliases first
    for alias, val in CITY_ALIASES.items():
        if alias in t:
            if isinstance(val, tuple):
                return val
            return CITIES.get(val)
    # Try main cities
    for city, coords in CITIES.items():
        if city in t:
            return coords
    return None


def infer_coords(author_id, name, role, location, notes, bio, collections_str):
    """
    Return (lat, lon, reason) or (None, None, None) if we can't determine.
    """
    name_lc = normalize(name)
    collections = [c.strip() for c in (collections_str or "").split(",") if c.strip()]

    # 1. Check named-person map (exact phrase match in name)
    for phrase, coords in NAMED_PERSON_MAP:
        if phrase in name_lc:
            return coords[0], coords[1], f"name contains '{phrase}'"

    # 2. Check "of <city>" pattern in name
    match = re.search(r"\bof\s+([a-z\s]+?)(?:\s*[,\(\)]|$)", name_lc)
    if match:
        place_guess = match.group(1).strip()
        coords = match_city_in_text(place_guess)
        if coords:
            return coords[0], coords[1], f"name 'of {place_guess}'"

    # 3. Check role
    role_lc = normalize(role)
    if "pope" in role_lc:
        return CITIES["rome"][0], CITIES["rome"][1], "role=pope → Rome"
    if "emperor" in role_lc:
        return CITIES["constantinople"][0], CITIES["constantinople"][1], "role=emperor → Constantinople"

    # 4. Check location field
    if location:
        coords = match_city_in_text(location)
        if coords:
            return coords[0], coords[1], f"location field: {location}"

    # 5. Check notes / bio for city mentions
    for text_field in [notes, bio]:
        if text_field:
            coords = match_city_in_text(text_field)
            if coords:
                return coords[0], coords[1], "mentioned in notes/bio"

    # 6. Collection-based default
    for coll in collections:
        if coll in COLLECTION_DEFAULTS:
            coords = COLLECTION_DEFAULTS[coll]
            return coords[0], coords[1], f"collection default ({coll})"

    # 7. Generic Mediterranean fallback so the person at least appears on map
    return MEDITERRANEAN_CENTER[0], MEDITERRANEAN_CENTER[1], "fallback: Mediterranean center"


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT a.id, a.name, a.role, a.location, a.notes, a.bio,
               GROUP_CONCAT(DISTINCT l.collection) AS collections
        FROM authors a
        LEFT JOIN letters l ON (l.sender_id = a.id OR l.recipient_id = a.id)
        WHERE a.lat IS NULL
        GROUP BY a.id
        ORDER BY a.name
    """)
    rows = c.fetchall()
    print(f"Found {len(rows)} authors with NULL coordinates.\n")

    fixed = 0
    fallback_count = 0
    updates = []

    for row in rows:
        lat, lon, reason = infer_coords(
            row["id"],
            row["name"],
            row["role"],
            row["location"],
            row["notes"],
            row["bio"],
            row["collections"],
        )
        if lat is not None:
            updates.append((lat, lon, row["id"]))
            tag = "[FALLBACK]" if "fallback" in reason else ""
            print(f"  [{row['id']:>4}] {row['name'][:60]:<60} → ({lat:.4f}, {lon:.4f})  {tag} {reason}")
            if "fallback" in reason:
                fallback_count += 1
            fixed += 1

    if updates:
        c.executemany("UPDATE authors SET lat=?, lon=? WHERE id=?", updates)
        conn.commit()

    conn.close()

    print(f"\n{'='*70}")
    print(f"Total fixed : {fixed}")
    print(f"  Specific  : {fixed - fallback_count}")
    print(f"  Fallback  : {fallback_count}  (Mediterranean center — review these)")
    print(f"  Skipped   : {len(rows) - fixed}")


if __name__ == "__main__":
    main()

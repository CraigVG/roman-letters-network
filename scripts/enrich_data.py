#!/usr/bin/env python3
"""
enrich_data.py — Enrich the roman_letters.db database with:
1. Cleaned author/recipient names
2. lat/lon coordinates for people
3. Approximate dates for letters
4. Merged duplicate people

Safe to run multiple times (idempotent).
"""

import sqlite3
import re
import math

DB_PATH = "data/roman_letters.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ---------------------------------------------------------------------------
# Step 1: Clean author/recipient names
# ---------------------------------------------------------------------------

# Patterns to strip (applied in order, case-insensitive)
NAME_STRIP_PATTERNS = [
    # "X Augustine" where Augustine is the sender context
    r'\s+Augustine\s*$',
    r'\s+Augustine,\s*Presbyter\s*$',
    # "from Augustine", "by Augustine"
    r'\s+from\s+Augustine\s*$',
    r',?\s+Augustine\s*$',
    # honorifics prefix
    r'^My\s+Beloved\s+and\s+Venerable\s+Father\s+',
    r'^My\s+Noble\s+and\s+Most\s+Excellent\s+and\s+Loving\s+Son\s*',
    r'^My\s+Noble\s+and\s+Justly\s+Honoured\s+Brother\s+',
    r'^My\s+Noble\s+and\s+Brother\s*',
    r'^My\s+Noble\s+',
    r'^Holy\s+and\s+Venerable\s+Handmaid\s+of\s+God\s+',
    r'^Eminently\s+Religious\s+and\s+Holy\s+Daughter\s+',
    r'^well-?Beloved\s+and\s+honourable\s+Brother\s+',
    r'^Aged\s+',
    r'^Brother\s+',
    # trailing date annotations like "(A.D. 419)"
    r'\s*\(A\.D\.\s*\d+\)\s*$',
    # trailing role context
    r',?\s+Colleague\s+in\s+Episcopal\s+Office\s*$',
    # "sends greeting" / "Sends Greeting" patterns
    r'\s+Sends\s+Greeting.*$',
    r'\s+sends\s+greeting.*$',
    # trailing whitespace
]

# Specific overrides for known messy names: old_name -> clean_name
NAME_OVERRIDES = {
    "Hermogenianus Augustine": "Hermogenianus",
    "Zenobius Augustine": "Zenobius",
    "Nebridius Augustine": "Nebridius",
    "Romanianus Augustine": "Romanianus",
    "Cœlestinus Augustine": "Cœlestinus",
    "Gaius Augustine": "Gaius",
    "Antoninus Augustine": "Antoninus",
    "Aurelius, Augustine, Presbyter": "Aurelius",
    "Licentius from Augustine": "Licentius",
    "Brother Profuturus Augustine": "Profuturus",
    "My Beloved and Venerable Father Augustine": "Unknown Father",
    "Boniface, Colleague in Episcopal Office, Augustine": "Boniface",
    "Alypius and Augustine (A.D. 419)": "Alypius",
    "Aged Alypius, Augustine": "Alypius",
    "Lampadius, Augustine": "Lampadius",
    "My Noble and Brother": "Unknown Noble",
    "My Noble and Justly Honoured Brother Nectarius": "Nectarius",
    "My Noble and Most Excellent and Loving Son": "Unknown Son",
    "Holy and Venerable Handmaid of God Albina": "Albina",
    "Eminently Religious and Holy Daughter Sapida": "Sapida",
    "well-Beloved and honourable Brother Theodorus": "Theodorus",
    "Julian, a of Antioch": "Julian of Antioch",
    "Niceas, Sub- of Aquileia": "Niceas of Aquileia",
    "Chrysogonus, a Monk of Aquileia": "Chrysogonus of Aquileia",
    "Paul, an Old Man of Concordia": "Paul of Concordia",
    "dearly-beloved brother Ravennius of Arles, Leo": "Ravennius of Arles",
    "Eudocia Augusta , about Monks of Palestine": "Eudocia Augusta",
    "John, of Jerusalem": "John of Jerusalem",
    "Arsicinus Duke": "Arsicinus",
    "Abbot Eusebius": "Eusebius",
    "Cyprian Presbyter": "Cyprian",
    "Peter Subdeacon": "Peter",
    "Anthemius, Subdeacon": "Anthemius",
    "Savinus, Subdeacon": "Savinus",
    "Antoninus, Subdeacon": "Antoninus",
    "Rufinus Monk": "Rufinus",
    "Antony, Monk": "Antony",
    "Heliodorus, Monk": "Heliodorus",
    "Magnus an Orator of Rome": "Magnus of Rome",
    "Theoctista, Sister of": "Theoctista",
    "Presbyters and": "Presbyters",
    "Quiricus, , etc": "Quiricus",
    "Virgilius": "Virgil",
    "Gulfaris, Magister Militum": "Gulfaris",
    "Velox, Magister Militium": "Velox",
    "Arsicinus Duke": "Arsicinus",
    "Leontius, Ex-": "Leontius",
    "Marcellus, Pro- of Dalmatia": "Marcellus of Dalmatia",
    "Aristobulus, Ex- and Antigraphus": "Aristobulus",
    "Venantius, Ex-Monk, Patrician of Syracuse": "Venantius of Syracuse",
    "Castorina, Maternal Aunt": "Castorina",
    "a Mother and Daughter Living in Gaul": "Unnamed Mother and Daughter",
    "a widow": "Anonymous Widow",
    "a lapsed Monk": "Anonymous Lapsed Monk",
    "a fallen virgin": "Anonymous Fallen Virgin",
    "a Solitary": "Anonymous Solitary",
    "a Magistrate": "Anonymous Magistrate",
    "President": "Anonymous President",
    "Young": "Anonymous Young Person",
    "Governor of Neocæsarea": "Governor of Neocaesarea",
    "Church of Neocæsarea. Consolatory": "Church of Neocaesarea",
    "Cæsareans. A defense of withdrawal": "Caesareans",
    "Canonicæ": "Canonicae",
    "Chorepiscopi": "Chorepiscopi (Rural Bishops)",
}


def clean_name(name):
    """Apply overrides first, then pattern-based cleaning."""
    if name in NAME_OVERRIDES:
        return NAME_OVERRIDES[name]
    cleaned = name
    for pattern in NAME_STRIP_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE).strip()
    # Remove trailing comma or whitespace
    cleaned = cleaned.strip(' ,')
    return cleaned if cleaned else name


def step1_fix_names(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM authors")
    rows = cur.fetchall()

    updated = 0
    skipped_dup = 0
    for row in rows:
        old_name = row['name']
        new_name = clean_name(old_name)
        if new_name != old_name:
            # Check if new_name already exists
            cur.execute("SELECT id FROM authors WHERE name=? AND id!=?", (new_name, row['id']))
            existing = cur.fetchone()
            if existing:
                # Will be handled by dedup step; skip rename for now
                skipped_dup += 1
                continue
            cur.execute("UPDATE authors SET name=? WHERE id=?", (new_name, row['id']))
            updated += 1

    conn.commit()
    print(f"[Step 1] Name cleaning: {updated} names updated, {skipped_dup} skipped (will be merged in Step 4)")


# ---------------------------------------------------------------------------
# Step 2: Assign locations (lat/lon) to people
# ---------------------------------------------------------------------------

# Known coordinates
CITY_COORDS = {
    "Rome": (41.8967, 12.4822),
    "Constantinople": (41.0082, 28.9784),
    "Hippo Regius": (36.8833, 7.7500),
    "Milan": (45.4642, 9.1900),
    "Ravenna": (44.4184, 12.2035),
    "Carthage": (36.8065, 10.1815),
    "Alexandria": (31.2001, 29.9187),
    "Antioch": (36.2028, 36.1606),
    "Bethlehem": (31.7054, 35.2024),
    "Clermont": (45.7772, 3.0870),
    "Vienne": (45.5242, 4.8783),
    "Limoges": (45.8336, 1.2611),
    "Pavia": (45.1847, 9.1582),
    "Nola": (40.9263, 14.5278),
    "Arles": (43.6767, 4.6278),
    "Marseilles": (43.2965, 5.3698),
    "Lyon": (45.7640, 4.8357),
    "Caesarea": (38.7312, 35.4787),
    "Nazianzus": (38.4500, 34.2833),
    "Tours": (47.3941, 0.6848),
    "Trier": (49.7499, 6.6371),
    "Toledo": (39.8628, -4.0273),
    "Jerusalem": (31.7683, 35.2137),
    "Thessalonica": (40.6401, 22.9444),
    "Terracina": (41.2928, 13.2483),
    "Riez": (43.8167, 6.0833),
    "Aquileia": (45.7695, 13.3685),
    "Salona": (43.5389, 16.4847),  # Split/Spalato, Croatia
    "Seville": (37.3882, -5.9823),
    "Naples": (40.8518, 14.2681),
    "Syracuse": (37.0755, 15.2866),
    "Sardinia": (39.2238, 9.1217),
    "Corsica": (42.0396, 9.0129),
    "Dalmatia": (43.5089, 16.4500),
    "Ephesus": (37.9515, 27.3630),
    "Cyrus": (36.7436, 36.9631),
    "Neocaesarea": (40.6167, 37.3833),
    "Ariminum": (44.0594, 12.5683),  # Rimini
    "Tyana": (37.8330, 34.5800),
    "Madaura": (36.4667, 8.1167),   # North Africa
    "Hippo": (36.8833, 7.7500),
    "Concordia": (45.7533, 12.8377),  # Concordia Sagittaria
    "Rhisinum": (42.4486, 18.4847),
    "Vapincum": (44.5638, 6.0842),   # Gap, France
    "Messana": (38.1938, 15.5500),   # Messina
    "Corcyra": (39.6243, 19.9217),   # Corfu
    "Illyricum": (42.5, 17.0),
    "Lugdunum": (45.7640, 4.8357),   # Lyon
    "Lerins": (43.5142, 7.0458),
    "Hispalis": (37.3882, -5.9823),  # Seville
    "Neapolis": (40.8518, 14.2681),  # Naples
    "Aemona": (46.0511, 14.5051),    # Ljubljana
}

# Per-person location assignments based on historical knowledge
PERSON_LOCATIONS = {
    # Augustine's circle - North Africa
    "Hermogenianus": ("Carthage", 36.8065, 10.1815),
    "Zenobius": ("Hippo Regius", 36.8833, 7.7500),
    "Nebridius": ("Carthage", 36.8065, 10.1815),
    "Romanianus": ("Thagaste", 36.0333, 8.5167),
    "Cœlestinus": ("Hippo Regius", 36.8833, 7.7500),
    "Gaius": ("Hippo Regius", 36.8833, 7.7500),
    "Antoninus": ("Hippo Regius", 36.8833, 7.7500),
    "Aurelius": ("Carthage", 36.8065, 10.1815),
    "Licentius": ("Rome", 41.8967, 12.4822),
    "Profuturus": ("Hippo Regius", 36.8833, 7.7500),
    "Nectarius": ("Calama", 36.5000, 6.9667),
    "Lampadius": ("Carthage", 36.8065, 10.1815),
    "Proculeianus": ("Hippo Regius", 36.8833, 7.7500),
    "Crispinus": ("Hippo Regius", 36.8833, 7.7500),
    "Januarius": ("Hippo Regius", 36.8833, 7.7500),
    "Vincentius": ("Cartennae", 36.1167, 0.3667),
    "Boniface": ("Carthage", 36.8065, 10.1815),
    "Dioscorus": ("Alexandria", 31.2001, 29.9187),
    "Albina": ("Rome", 41.8967, 12.4822),
    "Sapida": ("Carthage", 36.8065, 10.1815),
    "Anastasius": ("Rome", 41.8967, 12.4822),
    "Marcellinus": ("Carthage", 36.8065, 10.1815),
    "Evodius": ("Uzalis", 37.0500, 10.0333),
    "Alypius": ("Thagaste", 36.0333, 8.5167),
    "Innocent": ("Rome", 41.8967, 12.4822),
    "Florentius": ("Hippo Regius", 36.8833, 7.7500),
    "Maximus of Madaura": ("Madaura", 36.4667, 8.1167),
    "Proculeianus": ("Hippo Regius", 36.8833, 7.7500),

    # Jerome's circle - Bethlehem / Rome
    "Julian of Antioch": ("Antioch", 36.2028, 36.1606),
    "Chromatius": ("Aquileia", 45.7695, 13.3685),
    "Niceas of Aquileia": ("Aquileia", 45.7695, 13.3685),
    "Chrysogonus of Aquileia": ("Aquileia", 45.7695, 13.3685),
    "Paul of Concordia": ("Concordia", 45.7533, 12.8377),
    "Heliodorus": ("Aquileia", 45.7695, 13.3685),
    "Damasus": ("Rome", 41.8967, 12.4822),
    "Eustochium": ("Bethlehem", 31.7054, 35.2024),
    "Marcella": ("Rome", 41.8967, 12.4822),
    "Paula": ("Bethlehem", 31.7054, 35.2024),
    "Asella": ("Rome", 41.8967, 12.4822),
    "Desiderius": ("Rome", 41.8967, 12.4822),
    "Pammachius": ("Rome", 41.8967, 12.4822),
    "Domnio": ("Rome", 41.8967, 12.4822),
    "Nepotian": ("Aquileia", 45.7695, 13.3685),
    "Furia": ("Rome", 41.8967, 12.4822),
    "Amandus": ("Rome", 41.8967, 12.4822),
    "Vigilantius": ("Gaul", 44.0, 2.0),
    "Tranquillinus": ("Rome", 41.8967, 12.4822),
    "Theophilus": ("Alexandria", 31.2001, 29.9187),
    "Fabiola": ("Rome", 41.8967, 12.4822),
    "Principia": ("Rome", 41.8967, 12.4822),
    "Castrutius": ("Rome", 41.8967, 12.4822),
    "Oceanus": ("Rome", 41.8967, 12.4822),
    "Magnus of Rome": ("Rome", 41.8967, 12.4822),
    "Lucinius": ("Baetica", 37.5, -4.5),
    "Vitalis": ("Antioch", 36.2028, 36.1606),
    "Evangelus": ("Rome", 41.8967, 12.4822),
    "Theodora": ("Rome", 41.8967, 12.4822),
    "Abigaus": ("Rome", 41.8967, 12.4822),
    "Salvina": ("Constantinople", 41.0082, 28.9784),
    "Macarius": ("Rome", 41.8967, 12.4822),
    "Epiphanius": ("Salamis", 35.1833, 33.9000),
    "Simplicianus": ("Milan", 45.4642, 9.1900),
    "Sunnias and Fretela": ("Gothic lands", 45.0, 28.0),
    "Laeta": ("Rome", 41.8967, 12.4822),
    "Riparius": ("Gaul", 44.0, 2.0),
    "Minervius and Alexander": ("Gaul", 44.0, 2.0),
    "Hedibia": ("Gaul", 44.0, 2.0),
    "Algasia": ("Gaul", 44.0, 2.0),
    "Rusticus": ("Marseilles", 43.2965, 5.3698),
    "Ageruchia": ("Gaul", 44.0, 2.0),
    "Gaudentius": ("Brescia", 45.5416, 10.2118),
    "Dardanus": ("Gaul", 44.0, 2.0),
    "Demetrias": ("Rome", 41.8967, 12.4822),
    "Ctesiphon": ("Bethlehem", 31.7054, 35.2024),
    "Apronius": ("Rome", 41.8967, 12.4822),
    "Castorina": ("Bethlehem", 31.7054, 35.2024),
    "Antony": ("Egypt", 28.0, 30.0),
    "Virgins of Æmona": ("Aemona", 46.0511, 14.5051),

    # Gregory the Great's circle - mostly Rome/Italy
    "Justinus": ("Sicily", 37.6000, 14.0154),
    "Theoctista": ("Constantinople", 41.0082, 28.9784),
    "Narses": ("Rome", 41.8967, 12.4822),
    "Peter Subdeacon": ("Rome", 41.8967, 12.4822),
    "Bacauda and Agnellus": ("Spain", 40.4168, -3.7038),
    "Clementina": ("Rome", 41.8967, 12.4822),
    "Severus of Aquileia": ("Aquileia", 45.7695, 13.3685),
    "Natalis of Salona": ("Salona", 43.5389, 16.4847),
    "Honoratus of Salona": ("Salona", 43.5389, 16.4847),
    "Sebastian of Rhisinum": ("Rhisinum", 42.4486, 18.4847),
    "Aristobulus": ("Rome", 41.8967, 12.4822),
    "Romanus": ("Ravenna", 44.4184, 12.2035),
    "Venantius of Syracuse": ("Syracuse", 37.0755, 15.2866),
    "Peter of Terracina": ("Terracina", 41.2928, 13.2483),
    "Anthemius": ("Rome", 41.8967, 12.4822),
    "Leander of Hispalis (Seville)": ("Seville", 37.3882, -5.9823),
    "Arsicinus": ("Italy", 42.0, 12.5),
    "Gennadius": ("Carthage", 36.8065, 10.1815),
    "Felix of Messana": ("Messina", 38.1938, 15.5500),
    "Leo in Corsica": ("Corsica", 42.0396, 9.0129),
    "Martinus in Corsica": ("Corsica", 42.0396, 9.0129),
    "Maximianus of Syracuse": ("Syracuse", 37.0755, 15.2866),
    "Paulus of Naples": ("Naples", 40.8518, 14.2681),
    "Castorius of Ariminum": ("Rimini", 44.0594, 12.5683),
    "Rusticiana": ("Rome", 41.8967, 12.4822),
    "Italica": ("Rome", 41.8967, 12.4822),
    "Mauricius Augustus": ("Constantinople", 41.0082, 28.9784),
    "Domitian": ("Melitene", 38.3552, 38.3095),
    "Constantius": ("Milan", 45.4642, 9.1900),
    "Theodelinda": ("Milan", 45.4642, 9.1900),
    "Maurus": ("Rome", 41.8967, 12.4822),
    "Hospito": ("Sardinia", 39.2238, 9.1217),
    "Zabardas": ("Sardinia", 39.2238, 9.1217),
    "Constantina Augusta": ("Constantinople", 41.0082, 28.9784),
    "Pantaleo": ("Rome", 41.8967, 12.4822),
    "Eulogius and Anastasius": ("Rome", 41.8967, 12.4822),
    "Childebert": ("Paris", 48.8566, 2.3522),
    "Marinianus": ("Ravenna", 44.4184, 12.2035),
    "Brunichild": ("Metz", 49.1193, 6.1757),
    "Candidus": ("Gaul", 44.0, 2.0),
    "Donus": ("Rome", 41.8967, 12.4822),
    "Montana and Thomas": ("Africa", 33.0, 9.0),
    "Mauricius": ("Constantinople", 41.0082, 28.9784),
    "Theotistus": ("Constantinople", 41.0082, 28.9784),
    "Secundus": ("Rome", 41.8967, 12.4822),
    "Fortunatus": ("Naples", 40.8518, 14.2681),
    "Urbicus": ("Rome", 41.8967, 12.4822),
    "Palladius": ("Gaul", 44.0, 2.0),
    "Pelagius and Serenus": ("Rome", 41.8967, 12.4822),
    "Protasius": ("Rome", 41.8967, 12.4822),
    "Arigius": ("Gaul", 44.0, 2.0),
    "Theodoric and Theodebert": ("Frankish lands", 49.0, 7.0),
    "Athanasius": ("Naples", 40.8518, 14.2681),
    "Cyriacus": ("Constantinople", 41.0082, 28.9784),
    "Rufinus of Ephesus": ("Ephesus", 37.9515, 27.3630),
    "Respecta": ("Africa", 33.0, 9.0),
    "George": ("Constantinople", 41.0082, 28.9784),
    "Gregoria": ("Constantinople", 41.0082, 28.9784),
    "Theodore": ("Constantinople", 41.0082, 28.9784),
    "Eulogius of Alexandria": ("Alexandria", 31.2001, 29.9187),
    "Leontius": ("Rome", 41.8967, 12.4822),
    "Marcellus of Dalmatia": ("Salona", 43.5389, 16.4847),
    "Callinicus": ("Ravenna", 44.4184, 12.2035),
    "Julianus": ("Rome", 41.8967, 12.4822),
    "Agilulph": ("Milan", 45.4642, 9.1900),
    "Anatolius": ("Constantinople", 41.0082, 28.9784),
    "Gulfaris": ("Italy", 42.0, 12.5),
    "Syagrius": ("Autun", 46.9494, 4.2985),
    "Aregius of Vapincum": ("Gap", 44.5638, 6.0842),
    "Theoderic and Theodebert, Kings of Franks": ("Frankish lands", 49.0, 7.0),
    "Claudius in Spain": ("Spain", 40.4168, -3.7038),
    "Rechared": ("Toledo", 39.8628, -4.0273),
    "Adrian": ("Sicily", 37.6000, 14.0154),
    "Eusebius, Archbishop of Thessalonica": ("Thessalonica", 40.6401, 22.9444),
    "Conon of Lirinus": ("Lerins", 43.5142, 7.0458),
    "Bertha": ("Canterbury", 51.2802, 1.0789),
    "Mellitus": ("Canterbury", 51.2802, 1.0789),
    "Etherius of Lugdunum (Lyons)": ("Lyon", 45.7640, 4.8357),
    "Paschasius of Neapolis (Naples)": ("Naples", 40.8518, 14.2681),
    "Phocas": ("Constantinople", 41.0082, 28.9784),
    "Leontia": ("Constantinople", 41.0082, 28.9784),
    "Alcyson of Corcyra": ("Corfu", 39.6243, 19.9217),
    "Turribius": ("Spain", 40.4168, -3.7038),
    "Flavian of Constantinople": ("Constantinople", 41.0082, 28.9784),
    "Pulcheria Augusta": ("Constantinople", 41.0082, 28.9784),
    "Ravennius of Arles": ("Arles", 43.6767, 4.6278),
    "Marcian Augustus": ("Constantinople", 41.0082, 28.9784),
    "Synod of Chalcedon": ("Chalcedon", 40.9881, 29.0340),
    "Theodoret of Cyrus": ("Cyrus", 36.7436, 36.9631),
    "Proterius of Alexandria": ("Alexandria", 31.2001, 29.9187),
    "Juvenal of Jerusalem": ("Jerusalem", 31.7683, 35.2137),
    "Isacius of Jerusalem": ("Jerusalem", 31.7683, 35.2137),
    "Amos, Patriarch of Jerusalem": ("Jerusalem", 31.7683, 35.2137),

    # Leo the Great's circle
    "Ravennius": ("Arles", 43.6767, 4.6278),
    "Flavian": ("Constantinople", 41.0082, 28.9784),
    "Pulcheria": ("Constantinople", 41.0082, 28.9784),

    # Basil of Caesarea's circle
    "Eustathius Philosopher": ("Caesarea", 38.7312, 35.4787),
    "Candidianus": ("Caesarea", 38.7312, 35.4787),
    "Olympius": ("Caesarea", 38.7312, 35.4787),
    "Arcadius": ("Constantinople", 41.0082, 28.9784),
    "Origenes": ("Caesarea", 38.7312, 35.4787),
    "Cæsarius, brother of Gregory": ("Constantinople", 41.0082, 28.9784),
    "Church of Neocaesarea": ("Neocaesarea", 40.6167, 37.3833),
    "Sophronius Master": ("Caesarea", 38.7312, 35.4787),
    "Aburgius": ("Caesarea", 38.7312, 35.4787),
    "Chilo": ("Caesarea", 38.7312, 35.4787),
    "Bosporius": ("Caesarea", 38.7312, 35.4787),
    "Paregorius": ("Caesarea", 38.7312, 35.4787),
    "Pergamius": ("Caesarea", 38.7312, 35.4787),
    "Meletius of Antioch": ("Antioch", 36.2028, 36.1606),
    "Gregory, uncle": ("Nazianzus", 38.4500, 34.2833),
    "Hesychius": ("Caesarea", 38.7312, 35.4787),
    "Atarbius": ("Neocaesarea", 40.6167, 37.3833),
    "Callisthenes": ("Caesarea", 38.7312, 35.4787),
    "Martinianus": ("Caesarea", 38.7312, 35.4787),
    "Valerianus": ("Illyricum", 42.5, 17.0),
    "Elias": ("Caesarea", 38.7312, 35.4787),
    "Sophronius, master": ("Caesarea", 38.7312, 35.4787),
    "Senate of Tyana": ("Tyana", 37.8330, 34.5800),
    "Terentius": ("Caesarea", 38.7312, 35.4787),
    "Innocentius": ("Caesarea", 38.7312, 35.4787),
    "Worthiness": ("Caesarea", 38.7312, 35.4787),
    "Eustathius": ("Sebaste", 38.3552, 37.0218),
    "wife of Nectarius": ("Caesarea", 38.7312, 35.4787),

    # Ambrose circle
    "Emperor Valentinian": ("Milan", 45.4642, 9.1900),
    "Emperor Theodosius I": ("Constantinople", 41.0082, 28.9784),

    # Sidonius circle
    "Lupicinus": ("Lyon", 45.7640, 4.8357),
    "Syagrius": ("Autun", 46.9494, 4.2985),

    # General Gregory recipients
    "Sabinianus": ("Constantinople", 41.0082, 28.9784),
    "Matron Celantia": ("Rome", 41.8967, 12.4822),
    "Justinus, Prætor of Sicily": ("Sicily", 37.6000, 14.0154),
    "Exuperantius": ("Gaul", 44.0, 2.0),
    "Cyprian": ("Carthage", 36.8065, 10.1815),

    # Collections
    "Neapolitans": ("Naples", 40.8518, 14.2681),
    "people of Ravenna": ("Ravenna", 44.4184, 12.2035),
    "Salonitans": ("Salona", 43.5389, 16.4847),
    "various Metropolitans and Bishops": ("Rome", 41.8967, 12.4822),
    "Divers Bishops of Gaul": ("Gaul", 44.0, 2.0),
    "certain Bishops of Sicily": ("Sicily", 37.6000, 14.0154),
    "Italians and Gauls": ("Italy", 42.0, 12.5),
    "Nobles and Proprietors in Sardinia": ("Sardinia", 39.2238, 9.1217),
    "Brethren going to England (Angliam)": ("Rome", 41.8967, 12.4822),
    "Husbandmen (Colonos) of Syracusan Patrimony": ("Syracuse", 37.0755, 15.2866),
    "Theodoric and Theodebert": ("Frankish lands", 49.0, 7.0),
    "Maurilius and Vitalianus": ("Italy", 42.0, 12.5),
    "Bacauda and Agnellus, Bishops": ("Spain", 40.4168, -3.7038),
    "Victor and Columbus, Bishops": ("Africa", 33.0, 9.0),
    "Eulogius and Anastasius, Bishops": ("Rome", 41.8967, 12.4822),
    "Pelagius and Serenus, Bishops": ("Rome", 41.8967, 12.4822),
    "Demetrian and Valerian": ("Africa", 33.0, 9.0),
    "Marcellinus and Anapsychia (A.D. 410)": ("Carthage", 36.8065, 10.1815),
    "Chromatius, Jovinus, and Eusebius": ("Aquileia", 45.7695, 13.3685),
    "Minervius and Alexander": ("Gaul", 44.0, 2.0),
    "Maurentius": ("Rome", 41.8967, 12.4822),
    "Fantinus": ("Rome", 41.8967, 12.4822),
    "Luminosus": ("Rome", 41.8967, 12.4822),
    "Dominicus": ("Rome", 41.8967, 12.4822),
    "Columbus": ("Africa", 33.0, 9.0),
    "Scholasticus": ("Rome", 41.8967, 12.4822),
    "Dynamius": ("Gaul", 44.0, 2.0),
    "Sabinus": ("Rome", 41.8967, 12.4822),
    "Libertinus": ("Sicily", 37.6000, 14.0154),
    "Andrew": ("Rome", 41.8967, 12.4822),
    "Adeodatus": ("Rome", 41.8967, 12.4822),
    "Secundinus": ("Rome", 41.8967, 12.4822),
    "Vincomalus": ("Rome", 41.8967, 12.4822),
    "Conon, Abbot of Lirinus (Lerins)": ("Lerins", 43.5142, 7.0458),
    "Barbara and Antonina": ("Rome", 41.8967, 12.4822),
    "Vitus": ("Rome", 41.8967, 12.4822),
    "Senator": ("Rome", 41.8967, 12.4822),
    "Thalassia": ("Rome", 41.8967, 12.4822),
    "Lupo": ("Gaul", 44.0, 2.0),
    "Respecta, Abbess": ("Africa", 33.0, 9.0),
    "Edilbert": ("Canterbury", 51.2802, 1.0789),
    "Clotaire": ("Frankish lands", 49.0, 7.0),
    "Theoderic, of Franks": ("Frankish lands", 49.0, 7.0),
    "Theoderic and Theodebert, Kings of Franks": ("Frankish lands", 49.0, 7.0),
    "Etherius": ("Lyon", 45.7640, 4.8357),
    "Abbot Eusebius": ("Rome", 41.8967, 12.4822),
    "Eusebius": ("Rome", 41.8967, 12.4822),
    "Stephen, Abbot": ("Rome", 41.8967, 12.4822),
    "Maurus, Abbot": ("Rome", 41.8967, 12.4822),
    "Urbicus, Abbot": ("Rome", 41.8967, 12.4822),
    "Senator, Abbot": ("Rome", 41.8967, 12.4822),
    "Luminosus, Abbot": ("Rome", 41.8967, 12.4822),
    "Abbot Eusebius": ("Rome", 41.8967, 12.4822),
    "Abbot of Lirinus (Lerins)": ("Lerins", 43.5142, 7.0458),
    "Presbyters and": ("Rome", 41.8967, 12.4822),
    "Presbyters": ("Rome", 41.8967, 12.4822),
    "Lupo, Abbot": ("Gaul", 44.0, 2.0),
    "Thalassia, Abbess": ("Rome", 41.8967, 12.4822),
    "Respecta, Abbess": ("Africa", 33.0, 9.0),

    # Eustathius - depends on collection; in Basil -> Sebaste
    "Hedibia": ("Gaul", 44.0, 2.0),
    "Castorina": ("Bethlehem", 31.7054, 35.2024),

    # Key major authors with explicit coords
    "Ambrose of Milan": ("Milan", 45.4642, 9.1900),
    "Augustine of Hippo": ("Hippo Regius", 36.8833, 7.7500),
    "Jerome": ("Bethlehem", 31.7054, 35.2024),
    "Paulinus of Nola": ("Nola", 40.9263, 14.5278),
    "Sidonius Apollinaris": ("Clermont", 45.7772, 3.0870),
    "Quintus Aurelius Symmachus": ("Rome", 41.8967, 12.4822),
    "Cassiodorus": ("Ravenna", 44.4184, 12.2035),
    "Ennodius of Pavia": ("Pavia", 45.1847, 9.1582),
    "Avitus of Vienne": ("Vienne", 45.5242, 4.8783),
    "Ruricius of Limoges": ("Limoges", 45.8336, 1.2611),
    "Pope Gregory the Great": ("Rome", 41.8967, 12.4822),
    "Pope Leo the Great": ("Rome", 41.8967, 12.4822),
    "Basil of Caesarea": ("Caesarea", 38.7312, 35.4787),
    "Faustus of Riez": ("Riez", 43.8167, 6.0833),
    "Leander of Hispalis (Seville)": ("Seville", 37.3882, -5.9823),
    "John of Jerusalem": ("Jerusalem", 31.7683, 35.2137),

    # Gregory recipients with known titles/locations
    "Narses, Patrician": ("Rome", 41.8967, 12.4822),
    "Peter": ("Rome", 41.8967, 12.4822),
    "Clementina, Patrician": ("Rome", 41.8967, 12.4822),
    "Romanus, Patrician, and Exarch of Italy": ("Ravenna", 44.4184, 12.2035),
    "Gennadius, Patrician and Exarch of Africa": ("Carthage", 36.8065, 10.1815),
    "Velox": ("Italy", 42.0, 12.5),
    "Antoninus, Subdeacon": ("Rome", 41.8967, 12.4822),
    "Rusticiana, Patrician": ("Rome", 41.8967, 12.4822),
    "Savinus": ("Rome", 41.8967, 12.4822),
    "Savinus, Subdeacon": ("Rome", 41.8967, 12.4822),
    "Scholasticus, Judge": ("Rome", 41.8967, 12.4822),
    "Dynamius, Patrician": ("Gaul", 44.0, 2.0),
    "Sabinus, Guardian (Defensorem)": ("Rome", 41.8967, 12.4822),
    "Libertinus, Præfect": ("Sicily", 37.6000, 14.0154),
    "Italica, Patrician": ("Rome", 41.8967, 12.4822),
    "Domitian, Metropolitan": ("Melitene", 38.3552, 38.3095),
    "Hospito, Duke of Barbaricini": ("Sardinia", 39.2238, 9.1217),
    "Pantaleo, Præfect": ("Rome", 41.8967, 12.4822),
    "Vincomalus, Guardian (Defensorem)": ("Rome", 41.8967, 12.4822),
    "Candidus, Presbyter": ("Gaul", 44.0, 2.0),
    "Arigius, Patrician": ("Gaul", 44.0, 2.0),
    "Athanasius, Presbyter": ("Naples", 40.8518, 14.2681),
    "George, Presbyter": ("Constantinople", 41.0082, 28.9784),
    "Theodore, Physician": ("Constantinople", 41.0082, 28.9784),
    "Fantinus, Guardian (Defensorem)": ("Rome", 41.8967, 12.4822),
    "Callinicus, Exarch of Italy": ("Ravenna", 44.4184, 12.2035),
    "Julianus, Scribo": ("Rome", 41.8967, 12.4822),
    "Agilulph, of Lombards": ("Milan", 45.4642, 9.1900),
    "Martin, Scholasticus": ("Rome", 41.8967, 12.4822),
    "Anatolius, Constantinopolitan": ("Constantinople", 41.0082, 28.9784),
    "Rechared, of Visigoths": ("Toledo", 39.8628, -4.0273),
    "Bertha, of Angli": ("Canterbury", 51.2802, 1.0789),
    "Vitus, Guardian (Defensorem )": ("Rome", 41.8967, 12.4822),
    "Clotaire, of Franks": ("Paris", 48.8566, 2.3522),
    "Edilbert, of Angli": ("Canterbury", 51.2802, 1.0789),
    "Quiricus": ("Toledo", 39.8628, -4.0273),
    "Mellitus, Abbot": ("Canterbury", 51.2802, 1.0789),
    "Leontia, Empress": ("Constantinople", 41.0082, 28.9784),
    "Eudocia Augusta": ("Constantinople", 41.0082, 28.9784),
    "Arcadius, Imperial Treasurer": ("Constantinople", 41.0082, 28.9784),
    "Canonicae": ("Rome", 41.8967, 12.4822),
    "Chorepiscopi (Rural Bishops)": ("Caesarea", 38.7312, 35.4787),
    "Paregorius, presbyter": ("Caesarea", 38.7312, 35.4787),
    "Anonymous Magistrate": ("Caesarea", 38.7312, 35.4787),
    "Anonymous President": ("Caesarea", 38.7312, 35.4787),
    "Valerianus, of Illyricum": ("Illyricum", 42.5, 17.0),
    "Elias, Governor of Province": ("Caesarea", 38.7312, 35.4787),

    # Augustine circle extras
    "Rufinus": ("Aquileia", 45.7695, 13.3685),
    "Marcellinus and Anapsychia": ("Carthage", 36.8065, 10.1815),
    "Alypius and Augustine (A.D. 419)": ("Thagaste", 36.0333, 8.5167),
    "Theodorus": ("Rome", 41.8967, 12.4822),

    # Virgil (Virgilius)
    "Virgil": ("Arles", 43.6767, 4.6278),

    # Generics for truly anonymous/unknown
    "Unknown Father": ("North Africa", 33.0, 9.0),
    "Unknown Noble": ("North Africa", 33.0, 9.0),
    "Unknown Son": ("Hippo Regius", 36.8833, 7.7500),
    "Unnamed Mother and Daughter": ("Gaul", 44.0, 2.0),
}

# Also apply fuzzy "of X" location inference
PLACE_KEYWORDS = {
    "antioch": (36.2028, 36.1606),
    "alexandria": (31.2001, 29.9187),
    "jerusalem": (31.7683, 35.2137),
    "arles": (43.6767, 4.6278),
    "constantinople": (41.0082, 28.9784),
    "aquileia": (45.7695, 13.3685),
    "salona": (43.5389, 16.4847),
    "thessalonica": (40.6401, 22.9444),
    "ephesus": (37.9515, 27.3630),
    "lyons": (45.7640, 4.8357),
    "lyon": (45.7640, 4.8357),
    "lugdunum": (45.7640, 4.8357),
    "milan": (45.4642, 9.1900),
    "ravenna": (44.4184, 12.2035),
    "naples": (40.8518, 14.2681),
    "neapolis": (40.8518, 14.2681),
    "syracuse": (37.0755, 15.2866),
    "sardinia": (39.2238, 9.1217),
    "corsica": (42.0396, 9.0129),
    "sicily": (37.6000, 14.0154),
    "carthage": (36.8065, 10.1815),
    "hippo": (36.8833, 7.7500),
    "gaul": (44.0, 2.0),
    "spain": (40.4168, -3.7038),
    "rome": (41.8967, 12.4822),
    "seville": (37.3882, -5.9823),
    "hispalis": (37.3882, -5.9823),
    "terracina": (41.2928, 13.2483),
    "dalmatia": (43.5089, 16.4500),
    "ariminum": (44.0594, 12.5683),
    "neocaesarea": (40.6167, 37.3833),
    "caesarea": (38.7312, 35.4787),
    "corcyra": (39.6243, 19.9217),
    "corfu": (39.6243, 19.9217),
    "tyana": (37.8330, 34.5800),
    "lerins": (43.5142, 7.0458),
    "lirinus": (43.5142, 7.0458),
    "vapincum": (44.5638, 6.0842),
    "messana": (38.1938, 15.5500),
    "messene": (38.1938, 15.5500),
    "cyrus": (36.7436, 36.9631),
}


def infer_location_from_name(name):
    """Try to infer lat/lon from place keywords in the name."""
    name_lower = name.lower()
    for keyword, coords in PLACE_KEYWORDS.items():
        if keyword in name_lower:
            return coords
    return None


def step2_assign_locations(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, name, lat, lon FROM authors")
    rows = cur.fetchall()

    updated = 0
    for row in rows:
        # Skip if already has coords
        if row['lat'] is not None and row['lon'] is not None:
            continue

        name = row['name']
        coords = None

        # Exact match in PERSON_LOCATIONS
        if name in PERSON_LOCATIONS:
            loc, lat, lon = PERSON_LOCATIONS[name]
            coords = (lat, lon)

        # Try keyword inference from name
        if coords is None:
            coords = infer_location_from_name(name)

        if coords:
            cur.execute(
                "UPDATE authors SET lat=?, lon=? WHERE id=?",
                (coords[0], coords[1], row['id'])
            )
            updated += 1

    conn.commit()
    print(f"[Step 2] Locations: {updated} authors assigned coordinates")


# ---------------------------------------------------------------------------
# Step 3: Assign approximate dates to letters
# ---------------------------------------------------------------------------

COLLECTION_DATE_RANGES = {
    "augustine_hippo": (386, 430),
    "jerome": (370, 420),
    "gregory_great": (590, 604),
    "leo_great": (440, 461),
    "basil_caesarea": (357, 378),
    "ambrose_milan": (374, 397),
    "sidonius_apollinaris": (455, 480),
    "cassiodorus": (506, 538),
}


def interpolate_year(letter_number, max_letter_number, year_start, year_end):
    """Linearly interpolate year based on letter position."""
    if max_letter_number <= 1:
        return year_start
    fraction = (letter_number - 1) / (max_letter_number - 1)
    return round(year_start + fraction * (year_end - year_start))


def step3_assign_dates(conn):
    cur = conn.cursor()
    updated = 0

    for collection, (year_start, year_end) in COLLECTION_DATE_RANGES.items():
        if collection == "gregory_great":
            # Gregory uses BBNNN encoding: book = letter_number // 1000
            # Book 1 -> 590, Book 14 -> 604
            # Get all Gregory letters with no year
            cur.execute("""
                SELECT id, letter_number FROM letters
                WHERE collection=? AND year_approx IS NULL AND letter_number IS NOT NULL
            """, (collection,))
            letters = cur.fetchall()
            for letter in letters:
                ln = letter['letter_number']
                if ln < 100:
                    # Edge case: the single Latin letter numbered 1
                    book = 1
                else:
                    book = ln // 1000
                    if book == 0:
                        book = 1
                if book < 1:
                    book = 1
                if book > 14:
                    book = 14
                year = round(590 + (book - 1) * (14 / 13))
                cur.execute(
                    "UPDATE letters SET year_approx=? WHERE id=?",
                    (year, letter['id'])
                )
                updated += 1
        else:
            # Get max letter number for this collection
            cur.execute(
                "SELECT MAX(letter_number) as mx FROM letters WHERE collection=?",
                (collection,)
            )
            max_row = cur.fetchone()
            max_ln = max_row['mx'] if max_row and max_row['mx'] else 1

            cur.execute("""
                SELECT id, letter_number FROM letters
                WHERE collection=? AND year_approx IS NULL AND letter_number IS NOT NULL
            """, (collection,))
            letters = cur.fetchall()
            for letter in letters:
                year = interpolate_year(letter['letter_number'], max_ln, year_start, year_end)
                cur.execute(
                    "UPDATE letters SET year_approx=? WHERE id=?",
                    (year, letter['id'])
                )
                updated += 1

    conn.commit()
    print(f"[Step 3] Dates: {updated} letters assigned year_approx")


# ---------------------------------------------------------------------------
# Step 4: Merge duplicate people
# ---------------------------------------------------------------------------

def normalize_for_compare(name):
    """Normalize a name for duplicate comparison."""
    name = name.lower()
    name = re.sub(r'[^a-z0-9 ]', '', name)  # Remove punctuation/accents
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def step4_merge_duplicates(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM authors ORDER BY id")
    rows = cur.fetchall()

    # Build normalized name map
    norm_map = {}  # normalized_name -> (primary_id, primary_name)
    duplicates = []  # (dup_id, primary_id)

    for row in rows:
        norm = normalize_for_compare(row['name'])
        if norm in norm_map:
            # This is a duplicate
            duplicates.append((row['id'], norm_map[norm][0]))
        else:
            norm_map[norm] = (row['id'], row['name'])

    merged = 0
    for dup_id, primary_id in duplicates:
        # Update all letter references
        cur.execute("UPDATE letters SET sender_id=? WHERE sender_id=?", (primary_id, dup_id))
        cur.execute("UPDATE letters SET recipient_id=? WHERE recipient_id=?", (primary_id, dup_id))
        cur.execute("UPDATE people_mentioned SET person_id=? WHERE person_id=?", (primary_id, dup_id))
        # Delete the duplicate
        cur.execute("DELETE FROM authors WHERE id=?", (dup_id,))
        merged += 1

    conn.commit()
    print(f"[Step 4] Duplicates: merged {merged} duplicate author entries")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def print_summary(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM authors")
    author_count = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) as cnt FROM authors WHERE lat IS NOT NULL")
    with_coords = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) as cnt FROM letters WHERE year_approx IS NOT NULL")
    with_dates = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) as cnt FROM letters")
    total_letters = cur.fetchone()['cnt']

    print("\n=== Final Summary ===")
    print(f"Authors:          {author_count}")
    print(f"With coordinates: {with_coords} / {author_count} ({100*with_coords//author_count}%)")
    print(f"Letters with year: {with_dates} / {total_letters} ({100*with_dates//total_letters}%)")

    # Show a few still-missing coords
    cur.execute("SELECT id, name FROM authors WHERE lat IS NULL LIMIT 20")
    missing = cur.fetchall()
    if missing:
        print(f"\nAuthors still missing coordinates ({len(missing)} shown):")
        for r in missing:
            print(f"  [{r['id']}] {r['name']}")


def main():
    print("Connecting to database...")
    conn = get_conn()

    print("\n--- Step 1: Cleaning author names ---")
    step1_fix_names(conn)

    print("\n--- Step 2: Assigning coordinates ---")
    step2_assign_locations(conn)

    print("\n--- Step 3: Assigning approximate dates ---")
    step3_assign_dates(conn)

    print("\n--- Step 4: Merging duplicates ---")
    step4_merge_duplicates(conn)

    print_summary(conn)
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

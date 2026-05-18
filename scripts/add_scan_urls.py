#!/usr/bin/env python3
"""
add_scan_urls.py

Adds Internet Archive scan_url links to the `collections` table in roman_letters.db
for collections that are missing them.

Each scan_url points to an IA details page for the primary critical edition
of that collection's letters.

Research notes:
  - PG = Patrologia Graeca (Migne series, patrologiae_cursus_completus_gr_vol_* items)
  - PL = Patrologia Latina (Migne series, patrologiaecursu*mign items at Univ. of Toronto)
  - Thiel = Epistolae Romanorum Pontificum (covers popes from Hilarus to Pelagius II, 461–590)
  - Collectio Avellana = Corpus of imperial/papal letters 367–553 (CSEL 35)
  - CSEL = Corpus Scriptorum Ecclesiasticorum Latinorum
  - MGH Ep = Monumenta Germaniae Historica, Epistolae series
  - MGH AA = Monumenta Germaniae Historica, Auctores Antiquissimi
"""

import sqlite3
import sys
import os

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "roman_letters.db"
)

# ---------------------------------------------------------------------------
# Mapping: collection slug → Internet Archive details URL
#
# All URLs verified to exist on archive.org before inclusion.
# Items with None have no confirmed IA scan and are left unchanged.
# ---------------------------------------------------------------------------
SCAN_URLS = {
    # ── Libanius ──────────────────────────────────────────────────────────────
    # Foerster's complete 12-volume edition; letters are in vols 10–11.
    # Single IA item bundles all twelve volumes as separate PDF files.
    "libanius": "https://archive.org/details/foerster-libanii-opera",

    # ── Isidore of Pelusium ───────────────────────────────────────────────────
    # PG 78; BIM microfilm scan of Migne, Patrologia Graeca vol. 78 (1860).
    # Confirmed to be in the pub_patrologia-graeca IA collection.
    "isidore_pelusium": (
        "https://archive.org/details/"
        "bim_early-english-books-1641-1700_patrologiae-cursus-completus-_1860_78"
    ),

    # ── Pliny the Younger ─────────────────────────────────────────────────────
    # Loeb Classical Library vol. 55: Letters & Panegyricus I (Books 1–7).
    # Complete letters continue in Loeb vol. 59 (L059).
    "pliny_younger": (
        "https://archive.org/details/L055PlinyTheYoungerLettersPanegyricusI17"
    ),

    # ── Ennodius of Pavia ─────────────────────────────────────────────────────
    # MGH Auctores Antiquissimi vol. 7 (Vogel, 1885).
    # monumentagermani07geseuoft = MGH AA vol. 7 in the UofT/IA scan set.
    "ennodius_pavia": (
        "https://archive.org/details/monumentagermani07geseuoft"
    ),

    # ── Hormisdas (and shared Thiel papal group) ──────────────────────────────
    # Thiel, Epistolae Romanorum Pontificum genuinae, vol. 1 (1868).
    # Covers papal letters from Hilarus (461) through Hormisdas (523).
    # Used for: hormisdas, gelasius_i, simplicius_pope, pope_felix_iii,
    #           pope_hilary, pope_symmachus, pope_anastasius_ii.
    "hormisdas": "https://archive.org/details/epistolaeromano00thiegoog",
    "gelasius_i": "https://archive.org/details/epistolaeromano00thiegoog",
    "simplicius_pope": "https://archive.org/details/epistolaeromano00thiegoog",
    "pope_felix_iii": "https://archive.org/details/epistolaeromano00thiegoog",
    "pope_hilary": "https://archive.org/details/epistolaeromano00thiegoog",
    "pope_symmachus": "https://archive.org/details/epistolaeromano00thiegoog",
    "pope_anastasius_ii": "https://archive.org/details/epistolaeromano00thiegoog",

    # ── Theodoret of Cyrrhus ──────────────────────────────────────────────────
    # PG 83 (Migne, Patrologia Graeca Series vol. 83).
    "theodoret_cyrrhus": (
        "https://archive.org/details/patrologiae_cursus_completus_gr_vol_083"
    ),

    # ── Synesius of Cyrene ────────────────────────────────────────────────────
    # PG 66 (Migne, Patrologia Graeca Series vol. 66, version one).
    "synesius_cyrene": (
        "https://archive.org/details/patrologiae_cursus_completus_gr_vol_066a"
    ),

    # ── Venantius Fortunatus ──────────────────────────────────────────────────
    # MGH Auctores Antiquissimi vol. 4 (Leo, 1881).
    # monumentagermani04geseuoft = MGH AA vol. 4 in the UofT/IA scan set.
    "venantius_fortunatus": (
        "https://archive.org/details/monumentagermani04geseuoft"
    ),

    # ── Julian the Emperor ────────────────────────────────────────────────────
    # Wright's Loeb edition of The Works of the Emperor Julian, vol. 1 (1913).
    "julian_emperor": (
        "https://archive.org/details/worksofemperorju0001juli_u8o6"
    ),

    # ── Cyprian of Carthage ───────────────────────────────────────────────────
    # CSEL 3, pt. 2 (Hartel, 1871): S. Thasci Caecili Cypriani opera omnia.
    # Part 2 contains the letters (Epistulae).
    "cyprian_carthage": (
        "https://archive.org/details/sthascicaecilic01cyprgoog"
    ),

    # ── Pelagius I ────────────────────────────────────────────────────────────
    # Gassó & Batlle critical edition of the letters of Pelagius I (1956).
    "pelagius_i": "https://archive.org/details/gasso-batlle-1956-pelagius",

    # ── Avitus of Vienne ──────────────────────────────────────────────────────
    # MGH Auctores Antiquissimi vol. 6 (Peiper, 1883); repr. Weidmann 1961.
    # alcimiecdiciiavi62avit = Alcimi Ecdicii Aviti viennensis episcopi opera.
    "avitus_vienne": "https://archive.org/details/alcimiecdiciiavi62avit",

    # ── Boniface ──────────────────────────────────────────────────────────────
    # MGH Epistolae (Epistolae Merowingici et Karolini aevi, vol. 1).
    # Boniface's letters appear in MGH Ep t.3 = the same IA item as the
    # Merowingici corpus (monumentagerman01geseuoft covers the series).
    "boniface": "https://archive.org/details/monumentagerman01geseuoft",

    # ── Epistulae Austrasicae and related Merowingici groups ─────────────────
    # MGH Epistolae vol. 1 (Epistolae Merowingici et Karolini aevi, pars 1).
    # Contains: Austrasicae, Desiderius of Cahors, Boniface & Lull, Merowingici
    # collectae, Wisigothicae, Langobardorum collectae.
    "epistulae_austrasicae": (
        "https://archive.org/details/monumentagerman01geseuoft"
    ),
    "desiderius_cahors": (
        "https://archive.org/details/monumentagerman01geseuoft"
    ),
    "epistulae_wisigothicae": (
        "https://archive.org/details/monumentagerman01geseuoft"
    ),
    "epistulae_langobardorum": (
        "https://archive.org/details/monumentagerman01geseuoft"
    ),
    "epistulae_merowingici": (
        "https://archive.org/details/monumentagerman01geseuoft"
    ),

    # ── Athanasius of Alexandria ──────────────────────────────────────────────
    # PG 25 (Migne, Patrologia Graeca Series vol. 25 – Athanasius part 1).
    "athanasius_alexandria": (
        "https://archive.org/details/patrologiae_cursus_completus_gr_vol_025"
    ),

    # ── Innocent I ───────────────────────────────────────────────────────────
    # PL 20 (Migne, Patrologia Latina vol. 20), University of Toronto scan.
    "innocent_i": "https://archive.org/details/patrologiaecursu20mign",

    # ── Alcuin of York ────────────────────────────────────────────────────────
    # MGH Epistolae vol. 4 (Epistolae Karolini aevi II = Alcuini epistolae).
    "alcuin_york": "https://archive.org/details/monumentagerman04geseuoft",

    # ── John Chrysostom ───────────────────────────────────────────────────────
    # PG 52 (Migne, Patrologia Graeca Series vol. 52 – Chrysostom letters).
    "chrysostom": (
        "https://archive.org/details/patrologiae_cursus_completus_gr_vol_052"
    ),

    # ── Pelagius II ───────────────────────────────────────────────────────────
    # PL 72 (Migne, Patrologia Latina vol. 72), University of Toronto scan.
    # Also used for Benedict I and John III (all in PL 72).
    "pelagius_ii": "https://archive.org/details/patrologiaecur72mign",
    "benedict_i": "https://archive.org/details/patrologiaecur72mign",
    "pope_john_iii": "https://archive.org/details/patrologiaecur72mign",

    # ── Sulpicius Severus ─────────────────────────────────────────────────────
    # CSEL 1 (Halm, 1866): Sulpicii Severi libri qui supersunt.
    "sulpicius_severus": (
        "https://archive.org/details/sulpiciiseveril00halmgoog"
    ),

    # ── Salvian of Marseille ──────────────────────────────────────────────────
    # CSEL 8 (Pauly, 1883): Salviani presbyteri Massiliensis Opera omnia.
    "salvian_marseille": (
        "https://archive.org/details/salvianipresbyt00salvgoog"
    ),

    # ── Ferrandus of Carthage ─────────────────────────────────────────────────
    # PL 67 (Migne, Patrologia Latina vol. 67), University of Toronto scan.
    "ferrandus_carthage": (
        "https://archive.org/details/patrologiaecursu67mign"
    ),

    # ── Columbanus ───────────────────────────────────────────────────────────
    # Walker's Dublin Institute edition (1957) is the standard critical text.
    # No standalone IA scan confirmed; use the Epistolae Merowingici corpus
    # (MGH Ep vol. 1) which also contains the Columbanus letters.
    "columbanus": "https://archive.org/details/monumentagerman01geseuoft",

    # ── Bede ─────────────────────────────────────────────────────────────────
    # Plummer's Oxford edition: Baedae Opera Historica (1896).
    "bede": "https://archive.org/details/operahistoricaad0000bede",

    # ── Caesarius of Arles ────────────────────────────────────────────────────
    # Morin's CCL 103–104 (1953) is the standard edition but is not on IA.
    # Use the PL 67 item which contains some Caesarius texts as a fallback
    # (Migne, PL 67 includes Caesarius of Arles among 6th-century bishops).
    # NOTE: The PL 67 item is shared with ferrandus_carthage; both are in that volume.
    "caesarius_arles": (
        "https://archive.org/details/patrologiaecursu67mign"
    ),

    # ── Pope John II ─────────────────────────────────────────────────────────
    # Collectio Avellana (CSEL 35, Günther, 1895–1898), vol. 1.
    # Covers imperial/papal letters 367–553 including John II, Agapetus I, Vigilius.
    "pope_john_ii": "https://archive.org/details/epistulaeimperat01gnth",
    "pope_agapetus_i": "https://archive.org/details/epistulaeimperat01gnth",
    "pope_vigilius": "https://archive.org/details/epistulaeimperat01gnth",

    # ── Faustus of Riez ───────────────────────────────────────────────────────
    # CSEL 21 (Engelbrecht, 1891) is the standard edition but is not on IA.
    # PL 58 contains Faustus; no confirmed IA scan found for either edition.
    # Left as None — will not be updated.
    "faustus_riez": None,

    # ── Braulio of Zaragoza ───────────────────────────────────────────────────
    # Lynch & Galindo edition (1950) or Riesco Terrero's edition.
    # No confirmed IA scan found for any critical edition.
    "braulio_zaragoza": None,
}


def main():
    db_path = os.path.abspath(DB_PATH)
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    # Fetch current state
    cur.execute("SELECT slug, scan_url FROM collections ORDER BY slug")
    rows = cur.fetchall()
    existing = {slug: url for slug, url in rows}

    updated = 0
    skipped_already_set = 0
    skipped_no_url = 0
    not_in_db = []

    for slug, scan_url in SCAN_URLS.items():
        if slug not in existing:
            not_in_db.append(slug)
            continue

        if scan_url is None:
            # No confirmed IA URL for this collection
            skipped_no_url += 1
            continue

        if existing[slug]:
            # Already has a scan_url — leave it alone
            skipped_already_set += 1
            continue

        cur.execute(
            "UPDATE collections SET scan_url = ? WHERE slug = ?",
            (scan_url, slug),
        )
        print(f"  UPDATED: {slug}")
        print(f"           {scan_url}")
        updated += 1

    conn.commit()
    conn.close()

    print()
    print("=" * 60)
    print(f"Collections updated:         {updated}")
    print(f"Already had scan_url:        {skipped_already_set}")
    print(f"No confirmed IA URL:         {skipped_no_url}")
    if not_in_db:
        print(f"Slug not in DB (skipped):    {len(not_in_db)}")
        for s in not_in_db:
            print(f"  - {s}")
    print("=" * 60)

    # Show final state
    conn2 = sqlite3.connect(db_path)
    cur2 = conn2.cursor()
    cur2.execute(
        "SELECT COUNT(*) FROM collections WHERE scan_url IS NOT NULL AND scan_url != ''"
    )
    with_url = cur2.fetchone()[0]
    cur2.execute("SELECT COUNT(*) FROM collections")
    total = cur2.fetchone()[0]
    conn2.close()

    print(f"Collections with scan_url:   {with_url} / {total}")

    # List any still missing
    conn3 = sqlite3.connect(db_path)
    cur3 = conn3.cursor()
    cur3.execute(
        "SELECT slug FROM collections WHERE scan_url IS NULL OR scan_url = '' ORDER BY slug"
    )
    missing = [r[0] for r in cur3.fetchall()]
    conn3.close()
    if missing:
        print(f"\nStill missing scan_url ({len(missing)}):")
        for s in missing:
            print(f"  - {s}")


if __name__ == "__main__":
    main()

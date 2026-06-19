#!/usr/bin/env python3
"""Enrich Cicero Ad Familiares correspondents from Latin salutations.

Source basis:
- Existing cicero_familiares Latin headers in data/roman_letters.db, imported
  from The Latin Library.
- Perseus CTS catalog for Cicero, Epistulae ad Familiares.
- Attalus name/reference index for selected classical prosopography checks.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"

COLLECTION = "cicero_familiares"
CICERO_NAME = "Marcus Tullius Cicero"
AUTHOR_LOCATION_PREFIX = "author_location:"


@dataclass(frozen=True)
class PersonRecord:
    key: str
    name: str
    name_latin: str | None
    birth_year: int | None
    death_year: int | None
    role: str
    location: str | None
    lat: float | None
    lon: float | None
    location_confidence: str
    bio: str
    notes: str
    force_location: bool = False


@dataclass(frozen=True)
class Rule:
    pattern: str
    sender: str | None
    recipient: str | None
    label: str
    allow_default_sender_override: bool = True
    allow_cicero_recipient_override: bool = False


@dataclass
class PlannedChange:
    letter_id: int
    ref_id: str
    field: str
    old: Any
    new: Any
    reason: str


ROME_LAT = 41.8931
ROME_LON = 12.4828


def person(
    key: str,
    name: str,
    name_latin: str | None,
    role: str,
    bio: str,
    *,
    birth_year: int | None = None,
    death_year: int | None = None,
    location: str | None = "Rome",
    lat: float | None = ROME_LAT,
    lon: float | None = ROME_LON,
    location_confidence: str = "career_hub",
    notes: str | None = None,
    force_location: bool = False,
) -> PersonRecord:
    return PersonRecord(
        key=key,
        name=name,
        name_latin=name_latin,
        birth_year=birth_year,
        death_year=death_year,
        role=role,
        location=location,
        lat=lat,
        lon=lon,
        location_confidence=location_confidence,
        bio=bio,
        notes=notes
        or (
            "Source basis: Cicero, Epistulae ad Familiares salutation; "
            "The Latin Library and Perseus text catalog; Attalus classical "
            "reference index where applicable."
        ),
        force_location=force_location,
    )


PEOPLE: dict[str, PersonRecord] = {
    "cicero": person(
        "cicero",
        CICERO_NAME,
        "M. Tullius Cicero",
        "Senator, orator, consul",
        "Marcus Tullius Cicero (106-43 BC) was a Roman statesman, advocate, orator, philosopher, and prolific letter writer of the late Republic. His correspondence preserves an unusually detailed record of Roman political, family, and intellectual life during the collapse of the republican order.",
        birth_year=-106,
        death_year=-43,
        notes="Biography source basis: Stanford Encyclopedia of Philosophy, Cicero; Cicero correspondence source texts.",
    ),
    "quintus_cicero": person(
        "quintus_cicero",
        "Quintus Tullius Cicero",
        "Q. Tullius Cicero",
        "Senator, praetor, provincial governor, military legate",
        "Quintus Tullius Cicero (c. 102-43 BC), younger brother of Marcus Tullius Cicero, was a Roman senator who served as praetor, governor of Asia, and legate under Julius Caesar in Gaul. The Cicero family letters preserve him both as correspondent and as a member of Cicero's household network.",
        birth_year=-102,
        death_year=-43,
    ),
    "cicero_minor": person(
        "cicero_minor",
        "Marcus Tullius Cicero Minor",
        "M. Tullius Cicero filius",
        "Student, later consul",
        "Marcus Tullius Cicero Minor (65-after 30 BC) was Cicero's son. In the Ad Familiares tradition he appears in family salutations and in letters from Athens to Tiro; later he served in public life under Augustus.",
        birth_year=-65,
        death_year=None,
        location="Athens",
        lat=37.9838,
        lon=23.7275,
        location_confidence="correspondence_context",
    ),
    "terentia": person(
        "terentia",
        "Terentia",
        "Terentia",
        "Cicero's wife and family correspondent",
        "Terentia (c. 98 BC-after 40 BC) was Cicero's wife for much of his public career and a central recipient in his family correspondence during exile, civil war, and separation.",
        birth_year=-98,
        death_year=None,
        location_confidence="residence",
    ),
    "tiro": person(
        "tiro",
        "Marcus Tullius Tiro",
        "M. Tullius Tiro",
        "Freedman, secretary, editor",
        "Marcus Tullius Tiro (c. 103-4 BC), Cicero's freedman, secretary, and literary assistant, was a trusted member of Cicero's household and later helped preserve Cicero's writings.",
        birth_year=-103,
        death_year=-4,
        location="Patrae",
        lat=38.2466,
        lon=21.7346,
        location_confidence="correspondence_context",
    ),
    "senate": person(
        "senate",
        "Roman Senate",
        "Senatus Romanus",
        "Roman governing body",
        "The Roman Senate was the central deliberative body of the Roman Republic. Cicero's official dispatches in Ad Familiares address the senate and magistrates as public recipients.",
        birth_year=None,
        death_year=None,
        force_location=True,
    ),
    "lucius_valerius_jurist": person(
        "lucius_valerius_jurist",
        "Lucius Valerius, jurist",
        "L. Valerius iurisconsultus",
        "Jurist and Cicero correspondent",
        "Lucius Valerius was a jurist addressed by Cicero in Ad Familiares 1.10. The salutation identifies him by praenomen, nomen, and professional role.",
    ),
    "lentulus_spinther": person(
        "lentulus_spinther",
        "Publius Cornelius Lentulus Spinther",
        "P. Cornelius Lentulus Spinther",
        "Senator, consul, proconsul",
        "Publius Cornelius Lentulus Spinther (c. 100-c. 47 BC) was a Roman senator, consul in 57 BC, and proconsular correspondent of Cicero. Cicero's first book of Ad Familiares is addressed chiefly to him.",
        birth_year=-100,
        death_year=-47,
        location="Cilicia",
        lat=36.8121,
        lon=34.6415,
        location_confidence="correspondence_context",
    ),
    "curio": person(
        "curio",
        "Gaius Scribonius Curio",
        "C. Scribonius Curio",
        "Tribune of the plebs, politician",
        "Gaius Scribonius Curio (d. 49 BC) was a Roman politician and tribune of the plebs. Cicero's letters to Curio track political friendship and patronage in the years before civil war.",
        death_year=-49,
    ),
    "caelius": person(
        "caelius",
        "Marcus Caelius Rufus",
        "M. Caelius Rufus",
        "Senator, aedile, correspondent",
        "Marcus Caelius Rufus (82-48 BC) was a Roman senator, orator, and political ally of Cicero. His letters to Cicero in Ad Familiares book 8 are a vivid source for Roman politics while Cicero was away from the city.",
        birth_year=-82,
        death_year=-48,
    ),
    "coelius_caldus": person(
        "coelius_caldus",
        "Gaius Coelius Caldus",
        "C. Coelius Caldus",
        "Quaestor under Cicero in Cilicia",
        "Gaius Coelius Caldus was Cicero's quaestor in Cilicia in 50 BC. Ad Familiares 2.19 addresses him in that administrative setting.",
        location="Cilicia",
        lat=36.8121,
        lon=34.6415,
        location_confidence="correspondence_context",
    ),
    "curius": person(
        "curius",
        "Manius Curius",
        "M. Curius",
        "Businessman and Cicero correspondent",
        "Manius Curius was a Roman businessman and friend of Cicero, known from Cicero's correspondence as part of the wider Italian and Greek commercial network.",
        location="Patrae",
        lat=38.2466,
        lon=21.7346,
        location_confidence="correspondence_context",
    ),
    "caninius_sallustius": person(
        "caninius_sallustius",
        "Caninius Sallustius",
        "Caninius Sallustius",
        "Proquaestor and Cicero correspondent",
        "Caninius Sallustius was a Roman office-holder connected with Cicero's Cilician command. Ad Familiares 2.17 addresses him as proquaestor.",
        location="Cilicia",
        lat=36.8121,
        lon=34.6415,
        location_confidence="correspondence_context",
    ),
    "appius_pulcher": person(
        "appius_pulcher",
        "Appius Claudius Pulcher",
        "Ap. Claudius Pulcher",
        "Senator, consul, proconsul",
        "Appius Claudius Pulcher (c. 97-48 BC), consul in 54 BC, preceded Cicero as governor of Cilicia and was the main correspondent in Ad Familiares book 3.",
        birth_year=-97,
        death_year=-48,
        location="Cilicia",
        lat=36.8121,
        lon=34.6415,
        location_confidence="correspondence_context",
    ),
    "servius_sulpicius": person(
        "servius_sulpicius",
        "Servius Sulpicius Rufus",
        "Ser. Sulpicius Rufus",
        "Jurist, consul, governor",
        "Servius Sulpicius Rufus (c. 106-43 BC) was a Roman jurist, consul, and close correspondent of Cicero. His exchange with Cicero includes consolation, public affairs, and recommendation letters.",
        birth_year=-106,
        death_year=-43,
        location="Achaea",
        lat=37.9838,
        lon=23.7275,
        location_confidence="correspondence_context",
    ),
    "marcus_marcellus": person(
        "marcus_marcellus",
        "Marcus Claudius Marcellus",
        "M. Claudius Marcellus",
        "Senator, consul, exile",
        "Marcus Claudius Marcellus (c. 95-45 BC), consul in 51 BC, was a republican senator whose exile and recall under Caesar are reflected in Cicero's correspondence.",
        birth_year=-95,
        death_year=-45,
        location="Mytilene",
        lat=39.1070,
        lon=26.5550,
        location_confidence="correspondence_context",
    ),
    "gaius_marcellus": person(
        "gaius_marcellus",
        "Gaius Claudius Marcellus",
        "C. Claudius Marcellus",
        "Senator, consul",
        "Gaius Claudius Marcellus was consul in 50 BC and a recipient of Cicero's official letters from Cilicia in Ad Familiares book 15.",
    ),
    "figulus": person(
        "figulus",
        "Publius Nigidius Figulus",
        "P. Nigidius Figulus",
        "Senator, scholar, exile",
        "Publius Nigidius Figulus (c. 98-45 BC) was a Roman senator, scholar, and republican figure addressed by Cicero in exile-related correspondence.",
        birth_year=-98,
        death_year=-45,
    ),
    "plancius": person(
        "plancius",
        "Gnaeus Plancius",
        "Cn. Plancius",
        "Senator and Cicero ally",
        "Gnaeus Plancius was a Roman public figure and ally of Cicero, remembered especially for his support during Cicero's exile and as a recipient in Ad Familiares.",
    ),
    "metellus_celer": person(
        "metellus_celer",
        "Quintus Caecilius Metellus Celer",
        "Q. Caecilius Metellus Celer",
        "Senator, consul, proconsul",
        "Quintus Caecilius Metellus Celer (d. 59 BC), consul in 60 BC, appears in Cicero's correspondence as a high-ranking aristocratic correspondent in the late Republic.",
        death_year=-59,
    ),
    "metellus_nepos": person(
        "metellus_nepos",
        "Quintus Caecilius Metellus Nepos",
        "Q. Caecilius Metellus Nepos",
        "Senator, tribune, consul",
        "Quintus Caecilius Metellus Nepos (c. 100-55 BC) was a Roman senator and political opponent turned correspondent of Cicero.",
        birth_year=-100,
        death_year=-55,
    ),
    "antonius_hybrida": person(
        "antonius_hybrida",
        "Gaius Antonius Hybrida",
        "C. Antonius Hybrida",
        "Senator, consul, governor",
        "Gaius Antonius Hybrida was Cicero's consular colleague in 63 BC and later a provincial commander addressed in Cicero's correspondence.",
        death_year=-42,
    ),
    "sestius": person(
        "sestius",
        "Publius Sestius",
        "P. Sestius",
        "Tribune of the plebs, Cicero supporter",
        "Publius Sestius was a Roman politician and supporter of Cicero, known from Cicero's defense speech for him and from the correspondence.",
    ),
    "pompey": person(
        "pompey",
        "Gnaeus Pompeius Magnus",
        "Cn. Pompeius Magnus",
        "General, statesman",
        "Gnaeus Pompeius Magnus (106-48 BC), known as Pompey, was one of the dominant Roman commanders and politicians of the late Republic and a major figure in Cicero's political world.",
        birth_year=-106,
        death_year=-48,
    ),
    "crassus": person(
        "crassus",
        "Marcus Licinius Crassus",
        "M. Licinius Crassus",
        "General, statesman",
        "Marcus Licinius Crassus (c. 115-53 BC) was a Roman aristocrat, commander, and member of the first triumvirate, addressed by Cicero in Ad Familiares.",
        birth_year=-115,
        death_year=-53,
    ),
    "vatinius": person(
        "vatinius",
        "Publius Vatinius",
        "P. Vatinius",
        "Senator, commander",
        "Publius Vatinius was a Roman politician, ally of Caesar, and correspondent of Cicero. Ad Familiares preserves letters both to and from him.",
    ),
    "lucceius": person(
        "lucceius",
        "Lucius Lucceius",
        "L. Lucceius",
        "Historian, public figure",
        "Lucius Lucceius was a Roman historian and political figure whom Cicero famously asked to write an account of his consulship and exile.",
    ),
    "titius": person(
        "titius",
        "Titus Titius",
        "T. Titius",
        "Roman magistrate and correspondent",
        "Titus Titius appears in Cicero's recommendation correspondence as a Roman office-holder and recipient.",
    ),
    "sittius": person(
        "sittius",
        "Publius Sittius",
        "P. Sittius",
        "Financier and military adventurer",
        "Publius Sittius was a Roman financier and military adventurer connected with Cicero's network and recommendation correspondence.",
    ),
    "fadius_gallus": person(
        "fadius_gallus",
        "Marcus Fadius Gallus",
        "M. Fadius Gallus",
        "Friend and correspondent of Cicero",
        "Marcus Fadius Gallus was a friend and correspondent of Cicero, appearing in the informal social and literary network of Ad Familiares.",
    ),
    "mescinius": person(
        "mescinius",
        "Lucius Mescinius Rufus",
        "L. Mescinius Rufus",
        "Quaestor and Cicero associate",
        "Lucius Mescinius Rufus served with Cicero in Cilicia and appears in Cicero's correspondence after that governorship.",
        location="Cilicia",
        lat=36.8121,
        lon=34.6415,
        location_confidence="correspondence_context",
    ),
    "torquatus": person(
        "torquatus",
        "Aulus Manlius Torquatus",
        "A. Manlius Torquatus",
        "Senator and Cicero correspondent",
        "Aulus Manlius Torquatus was a Roman senator and correspondent addressed by Cicero during the aftermath of civil war.",
    ),
    "caecina": person(
        "caecina",
        "Aulus Caecina",
        "A. Caecina",
        "Writer and Cicero correspondent",
        "Aulus Caecina was a Roman writer and political exile associated with Cicero's correspondence and advocacy after Caesar's victory.",
    ),
    "furfanius": person(
        "furfanius",
        "Titus Furfanius Postumus",
        "T. Furfanius Postumus",
        "Proconsul and Cicero correspondent",
        "Titus Furfanius Postumus was a Roman proconsular recipient in Cicero's correspondence, addressed in connection with Aulus Caecina.",
        location="Sicily",
        lat=37.59999,
        lon=14.01536,
        location_confidence="correspondence_context",
    ),
    "trebianus": person(
        "trebianus",
        "Gaius Trebianus",
        "C. Trebianus",
        "Roman correspondent of Cicero",
        "Gaius Trebianus was a Roman correspondent addressed by Cicero in Ad Familiares book 6.",
    ),
    "ampius": person(
        "ampius",
        "Titus Ampius Balbus",
        "T. Ampius Balbus",
        "Politician and Pompeian supporter",
        "Titus Ampius Balbus was a Roman politician and Pompeian supporter addressed by Cicero during the civil-war period.",
    ),
    "ligarius": person(
        "ligarius",
        "Quintus Ligarius",
        "Q. Ligarius",
        "Senator and Pompeian",
        "Quintus Ligarius was a Roman senator and Pompeian whose fate after the civil war prompted Cicero's advocacy and correspondence.",
    ),
    "basilus": person(
        "basilus",
        "Lucius Minucius Basilus",
        "L. Minucius Basilus",
        "Praetor and Caesar assassin",
        "Lucius Minucius Basilus was a Roman politician associated with the conspiracy against Caesar and addressed by Cicero shortly after the Ides of March.",
    ),
    "bithynicus": person(
        "bithynicus",
        "Pompeius Bithynicus",
        "Pompeius Bithynicus",
        "Roman correspondent of Cicero",
        "Pompeius Bithynicus was a Roman public figure and correspondent in Cicero's Ad Familiares book 6.",
    ),
    "lepta": person(
        "lepta",
        "Quintus Lepta",
        "Q. Lepta",
        "Cicero associate and officer",
        "Quintus Lepta was a close associate of Cicero and served with him during the Cilician command; Cicero's letters to him preserve household and political concerns.",
        location="Cilicia",
        lat=36.8121,
        lon=34.6415,
        location_confidence="correspondence_context",
    ),
    "toranius": person(
        "toranius",
        "Gaius Toranius",
        "C. Toranius",
        "Roman correspondent of Cicero",
        "Gaius Toranius was a Roman correspondent addressed by Cicero in the civil-war-era letters of Ad Familiares.",
    ),
    "domitius": person(
        "domitius",
        "Lucius Domitius Ahenobarbus",
        "L. Domitius Ahenobarbus",
        "Senator, consul, Pompeian commander",
        "Lucius Domitius Ahenobarbus (d. 48 BC) was a Roman senator, consul, and Pompeian commander addressed in Cicero's correspondence.",
        death_year=-48,
    ),
    "marius": person(
        "marius",
        "Marcus Marius",
        "M. Marius",
        "Friend and correspondent of Cicero",
        "Marcus Marius was a friend and correspondent of Cicero, best known from Cicero's letters about spectacle, illness, and cultivated retirement.",
    ),
    "caesar": person(
        "caesar",
        "Gaius Julius Caesar",
        "C. Iulius Caesar",
        "Dictator, general, statesman",
        "Gaius Julius Caesar (100-44 BC) was a Roman commander, politician, and dictator whose rise and assassination dominate the final phase of Cicero's correspondence.",
        birth_year=-100,
        death_year=-44,
        location="Rome/Gaul",
        lat=46.2276,
        lon=2.2137,
        location_confidence="correspondence_context",
    ),
    "trebatius": person(
        "trebatius",
        "Gaius Trebatius Testa",
        "C. Trebatius Testa",
        "Jurist and Cicero correspondent",
        "Gaius Trebatius Testa (c. 84 BC-AD 4) was a Roman jurist and friend of Cicero, recommended to Caesar's staff and frequently teased by Cicero in the letters.",
        birth_year=-84,
        death_year=4,
        location="Gaul",
        lat=46.2276,
        lon=2.2137,
        location_confidence="correspondence_context",
    ),
    "volumnius": person(
        "volumnius",
        "Publius Volumnius Eutrapelus",
        "P. Volumnius Eutrapelus",
        "Equestrian and Cicero correspondent",
        "Publius Volumnius Eutrapelus was a Roman equestrian, wit, and friend in Cicero's social network.",
    ),
    "varro": person(
        "varro",
        "Marcus Terentius Varro",
        "M. Terentius Varro",
        "Scholar, writer, public figure",
        "Marcus Terentius Varro (116-27 BC) was Rome's great antiquarian scholar and a correspondent of Cicero during the civil-war years.",
        birth_year=-116,
        death_year=-27,
    ),
    "dolabella": person(
        "dolabella",
        "Publius Cornelius Dolabella",
        "P. Cornelius Dolabella",
        "Senator, consul, Cicero's son-in-law",
        "Publius Cornelius Dolabella (c. 70-43 BC) was a Roman senator, consul, and Cicero's former son-in-law, a recurring correspondent in the crisis after Caesar's death.",
        birth_year=-70,
        death_year=-43,
    ),
    "paetus": person(
        "paetus",
        "Lucius Papirius Paetus",
        "L. Papirius Paetus",
        "Friend and correspondent of Cicero",
        "Lucius Papirius Paetus was a friend and correspondent of Cicero whose letters preserve a more relaxed, humorous side of Cicero's social world.",
    ),
    "plancus": person(
        "plancus",
        "Lucius Munatius Plancus",
        "L. Munatius Plancus",
        "Senator, commander, consul designate",
        "Lucius Munatius Plancus (c. 87-c. 15 BC) was a Roman senator and commander. In Ad Familiares book 10 he corresponds with Cicero during the military and political crisis of 43 BC.",
        birth_year=-87,
        death_year=-15,
        location="Gaul",
        lat=46.2276,
        lon=2.2137,
        location_confidence="correspondence_context",
    ),
    "furnius": person(
        "furnius",
        "Gaius Furnius",
        "C. Furnius",
        "Tribune and Cicero correspondent",
        "Gaius Furnius was a Roman politician and correspondent of Cicero, active around the military politics of 43 BC.",
        location="Gaul",
        lat=46.2276,
        lon=2.2137,
        location_confidence="correspondence_context",
    ),
    "lepidus": person(
        "lepidus",
        "Marcus Aemilius Lepidus",
        "M. Aemilius Lepidus",
        "Triumvir, commander, pontifex maximus",
        "Marcus Aemilius Lepidus (c. 89-13 BC) was a Roman commander, pontifex maximus, and later triumvir. His letters in Ad Familiares belong to the crisis after Caesar's assassination.",
        birth_year=-89,
        death_year=-13,
        location="Gaul",
        lat=43.9493,
        lon=4.8055,
        location_confidence="correspondence_context",
    ),
    "trebonius": person(
        "trebonius",
        "Gaius Trebonius",
        "C. Trebonius",
        "Praetor, governor, Caesar assassin",
        "Gaius Trebonius (d. 43 BC) was a Roman politician and one of Caesar's assassins; Cicero addressed him during the unstable months after the assassination.",
        death_year=-43,
        location="Asia",
        lat=37.9390,
        lon=27.3410,
        location_confidence="correspondence_context",
    ),
    "galba": person(
        "galba",
        "Servius Sulpicius Galba",
        "Ser. Sulpicius Galba",
        "Praetor and commander",
        "Servius Sulpicius Galba was a Roman commander and correspondent of Cicero during the Mutina campaign.",
        location="Mutina",
        lat=44.6471,
        lon=10.9252,
        location_confidence="correspondence_context",
    ),
    "pollio": person(
        "pollio",
        "Gaius Asinius Pollio",
        "C. Asinius Pollio",
        "Commander, consul, historian",
        "Gaius Asinius Pollio (76 BC-AD 4) was a Roman commander, consul, historian, and correspondent of Cicero during the late republican crisis.",
        birth_year=-76,
        death_year=4,
        location="Corduba",
        lat=37.8882,
        lon=-4.7794,
        location_confidence="correspondence_context",
    ),
    "decimus_brutus": person(
        "decimus_brutus",
        "Decimus Junius Brutus Albinus",
        "D. Iunius Brutus Albinus",
        "Senator, commander, consul designate",
        "Decimus Junius Brutus Albinus (c. 81-43 BC) was a Roman commander and one of Caesar's assassins. Cicero's letters to and from him in 43 BC center on the Mutina campaign and the defense of the republican cause.",
        birth_year=-81,
        death_year=-43,
        location="Mutina",
        lat=44.6471,
        lon=10.9252,
        location_confidence="correspondence_context",
    ),
    "matius": person(
        "matius",
        "Gaius Matius",
        "C. Matius",
        "Friend of Caesar and Cicero correspondent",
        "Gaius Matius was a Roman equestrian and friend of Caesar whose exchange with Cicero after Caesar's death reflects conflicting loyalties in elite Roman society.",
    ),
    "oppius": person(
        "oppius",
        "Gaius Oppius",
        "C. Oppius",
        "Friend of Caesar and correspondent",
        "Gaius Oppius was a Roman equestrian, friend of Caesar, and correspondent in Cicero's late republican network.",
    ),
    "cassius": person(
        "cassius",
        "Gaius Cassius Longinus",
        "C. Cassius Longinus",
        "Senator, praetor, commander",
        "Gaius Cassius Longinus (c. 86-42 BC) was a Roman senator, one of Caesar's assassins, and a major republican commander in the years after 44 BC.",
        birth_year=-86,
        death_year=-42,
        location="Syria",
        lat=34.8021,
        lon=38.9968,
        location_confidence="correspondence_context",
    ),
    "cornificius": person(
        "cornificius",
        "Quintus Cornificius",
        "Q. Cornificius",
        "Praetor, governor, poet",
        "Quintus Cornificius (d. 42 BC) was a Roman praetor, governor, and literary figure addressed by Cicero in the final years of the Republic.",
        death_year=-42,
        location="Africa",
        lat=36.8065,
        lon=10.1815,
        location_confidence="correspondence_context",
    ),
    "memmius": person(
        "memmius",
        "Gaius Memmius",
        "C. Memmius",
        "Praetor and literary patron",
        "Gaius Memmius was a Roman politician, praetor, and literary patron, known from Cicero's correspondence and as the dedicatee of Lucretius' poem.",
        location="Athens",
        lat=37.9838,
        lon=23.7275,
        location_confidence="correspondence_context",
    ),
    "valerius_orca": person(
        "valerius_orca",
        "Quintus Valerius Orca",
        "Q. Valerius Orca",
        "Legate and proconsular official",
        "Quintus Valerius Orca was a Roman magistrate and provincial official addressed in Cicero's recommendation letters.",
    ),
    "cluvius": person(
        "cluvius",
        "Marcus Cluvius",
        "M. Cluvius",
        "Roman banker and Cicero correspondent",
        "Marcus Cluvius was a Roman businessman and correspondent in Cicero's recommendation network.",
    ),
    "rutilius": person(
        "rutilius",
        "Marcus Rutilius",
        "M. Rutilius",
        "Roman correspondent of Cicero",
        "Marcus Rutilius appears in Cicero's recommendation correspondence as a named recipient.",
    ),
    "crassipes": person(
        "crassipes",
        "Furius Crassipes",
        "Furius Crassipes",
        "Roman senator and Cicero connection",
        "Furius Crassipes was a Roman aristocrat connected with Cicero's family and correspondence.",
    ),
    "brutus": person(
        "brutus",
        "Marcus Junius Brutus",
        "M. Iunius Brutus",
        "Senator, praetor, commander",
        "Marcus Junius Brutus (c. 85-42 BC) was a Roman senator and praetor who became one of Caesar's assassins and later commanded republican forces in Macedonia and the East.",
        birth_year=-85,
        death_year=-42,
        location="Rome",
        location_confidence="career_hub",
    ),
    "cato": person(
        "cato",
        "Marcus Porcius Cato",
        "M. Porcius Cato Uticensis",
        "Senator, praetor, republican leader",
        "Marcus Porcius Cato (95-46 BC), known as Cato the Younger, was a Roman senator and republican leader. Cicero addressed him in official letters from Cilicia.",
        birth_year=-95,
        death_year=-46,
    ),
    "acilius": person(
        "acilius",
        "Acilius, proconsul of Sicily",
        "Acilius proconsul",
        "Proconsul of Sicily",
        "Acilius was the proconsul of Sicily addressed by Cicero in a cluster of recommendation letters in Ad Familiares book 13.",
        location="Sicily",
        lat=37.59999,
        lon=14.01536,
        location_confidence="correspondence_context",
    ),
    "ancharius": person(
        "ancharius",
        "Quintus Ancharius",
        "Q. Ancharius",
        "Proconsul and Cicero correspondent",
        "Quintus Ancharius was a Roman proconsular recipient in Cicero's recommendation correspondence.",
    ),
    "culleolus": person(
        "culleolus",
        "Lucius Culleolus",
        "L. Culleolus",
        "Proconsul and Cicero correspondent",
        "Lucius Culleolus was a proconsular recipient of Cicero's recommendation letters.",
    ),
    "gallius": person(
        "gallius",
        "Rufus Gallius",
        "R. Gallius",
        "Roman correspondent of Cicero",
        "Rufus Gallius appears as a recipient in Cicero's recommendation correspondence.",
    ),
    "appuleius": person(
        "appuleius",
        "Appuleius, proquaestor",
        "Appuleius proquaestor",
        "Proquaestor and Cicero correspondent",
        "Appuleius was a proquaestorian recipient in Cicero's recommendation letters.",
    ),
    "silius": person(
        "silius",
        "Publius Silius",
        "P. Silius",
        "Propraetor and Cicero correspondent",
        "Publius Silius was a Roman propraetor and recipient of Cicero's recommendation letters.",
        location="Bithynia",
        lat=40.7000,
        lon=29.9000,
        location_confidence="correspondence_context",
    ),
    "sextilius_rufus": person(
        "sextilius_rufus",
        "Gaius Sextilius Rufus",
        "C. Sextilius Rufus",
        "Quaestor and Cicero correspondent",
        "Gaius Sextilius Rufus was a quaestorian recipient in Cicero's recommendation correspondence.",
    ),
    "caesius": person(
        "caesius",
        "Publius Caesius",
        "P. Caesius",
        "Roman correspondent of Cicero",
        "Publius Caesius appears as a recipient in Cicero's recommendation correspondence.",
    ),
    "deiotarus": person(
        "deiotarus",
        "Deiotarus",
        "Deiotarus rex",
        "King of Galatia",
        "Deiotarus was king of Galatia and a Roman ally, addressed in Cicero's recommendation correspondence.",
        birth_year=-105,
        death_year=-40,
        location="Galatia",
        lat=39.9208,
        lon=32.8541,
        location_confidence="regional",
    ),
    "thermus": person(
        "thermus",
        "Quintus Minucius Thermus",
        "Q. Minucius Thermus",
        "Propraetor and Cicero correspondent",
        "Quintus Minucius Thermus was a Roman propraetor in Asia and recipient of Cicero's recommendation letters.",
        location="Asia",
        lat=37.9390,
        lon=27.3410,
        location_confidence="correspondence_context",
    ),
    "curtius_peducaeanus": person(
        "curtius_peducaeanus",
        "Gaius Curtius Peducaeanus",
        "C. Curtius Peducaeanus",
        "Praetor and Cicero correspondent",
        "Gaius Curtius Peducaeanus was a Roman praetor and recipient in Cicero's recommendation correspondence.",
    ),
    "munatius": person(
        "munatius",
        "Gaius Munatius",
        "C. Munatius",
        "Roman correspondent of Cicero",
        "Gaius Munatius appears as a named recipient in Cicero's recommendation correspondence.",
    ),
    "servilius": person(
        "servilius",
        "Publius Servilius Isauricus",
        "P. Servilius Isauricus",
        "Senator, consul, proconsul",
        "Publius Servilius Isauricus was a Roman senator, consul, and proconsular recipient of Cicero's recommendation letters.",
    ),
    "philippus": person(
        "philippus",
        "Quintus Marcius Philippus",
        "Q. Marcius Philippus",
        "Proconsul and Cicero correspondent",
        "Quintus Marcius Philippus was a Roman proconsular recipient in Cicero's recommendation correspondence.",
    ),
    "paullus": person(
        "paullus",
        "Lucius Aemilius Paullus",
        "L. Aemilius Paullus",
        "Senator and consul",
        "Lucius Aemilius Paullus was a Roman senator and consul addressed by Cicero in official correspondence from Cilicia.",
    ),
    "sulpicius_imperator": person(
        "sulpicius_imperator",
        "Publius Sulpicius Rufus",
        "P. Sulpicius Rufus",
        "Imperator and Cicero correspondent",
        "Publius Sulpicius Rufus appears as an imperator addressed by Cicero in Ad Familiares book 13.",
    ),
    "allienus": person(
        "allienus",
        "Aulus Allienus",
        "A. Allienus",
        "Proconsul and Cicero correspondent",
        "Aulus Allienus was a Roman proconsul and recipient in Cicero's recommendation correspondence.",
    ),
}


def out(pattern: str, recipient: str, label: str, *, allow_cicero_recipient_override: bool = False) -> Rule:
    return Rule(
        pattern=pattern,
        sender="cicero",
        recipient=recipient,
        label=label,
        allow_cicero_recipient_override=allow_cicero_recipient_override,
    )


def incoming(pattern: str, sender: str, label: str) -> Rule:
    return Rule(pattern=pattern, sender=sender, recipient="cicero", label=label)


RULES: list[Rule] = [
    Rule(r"\bPLANCUS\b.*\bSENATUI\b", "plancus", "senate", "Plancus official letter to senate"),
    Rule(r"\bM LEPIDUS\b.*\bSENATUI\b", "lepidus", "senate", "Lepidus official letter to senate"),
    Rule(r"\bP LENTULUS\b.*\bSENATUI\b", "lentulus_spinther", "senate", "Lentulus official letter to senate"),
    Rule(r"\bM TULLIUS\b.*\bSENATUI\b", "cicero", "senate", "Cicero official letter to senate"),
    Rule(r"\bQ M FRATRI\b", "quintus_cicero", "cicero", "Quintus Cicero to Marcus Cicero"),
    Rule(r"\bQ CICERO\b.*\bTIRONI\b", "quintus_cicero", "tiro", "Quintus Cicero to Tiro"),
    Rule(r"\bCICERO F\b.*\bTIRONI\b", "cicero_minor", "tiro", "Cicero Minor to Tiro"),
    Rule(
        r"\bTULLIUS\b.*\bTERENTIAE\b",
        "cicero",
        "terentia",
        "Cicero family letter to Terentia",
        allow_cicero_recipient_override=True,
    ),
    incoming(r"\bCAELIUS\b.*\bCICERONI\b", "caelius", "Caelius to Cicero"),
    incoming(r"\bSERVIUS\b.*\bCICERONI\b", "servius_sulpicius", "Servius Sulpicius to Cicero"),
    incoming(r"\bMARCELLUS\b.*\bCICERONI\b", "marcus_marcellus", "Marcellus to Cicero"),
    incoming(r"\bMETELLUS Q F CELER\b.*\bCICERONI\b", "metellus_celer", "Metellus Celer to Cicero"),
    incoming(r"\bMETELLUS NEPOS\b.*\bCICERONI\b", "metellus_nepos", "Metellus Nepos to Cicero"),
    incoming(r"\bVATINIUS\b.*\bCICERONI\b", "vatinius", "Vatinius to Cicero"),
    incoming(r"\bCAECINA\b.*\bCICERONI\b", "caecina", "Caecina to Cicero"),
    incoming(r"\bBITHYNICUS\b.*\bCICERONI\b", "bithynicus", "Bithynicus to Cicero"),
    incoming(r"\bCURIUS\b.*\bCICERONI\b", "curius", "Curius to Cicero"),
    incoming(r"\bDOLABELLA\b.*\bCICERONI\b", "dolabella", "Dolabella to Cicero"),
    incoming(r"\bPLANCUS\b.*\bCICERONI\b", "plancus", "Plancus to Cicero"),
    incoming(r"\bGALBA\b.*\bCICERONI\b", "galba", "Galba to Cicero"),
    incoming(r"\bC ASINIUS POLLIO\b.*\bCICERONI\b|\bPOLLIO\b.*\bCICERONI\b", "pollio", "Pollio to Cicero"),
    incoming(r"\bM LEPIDUS\b.*\bCICERONI\b", "lepidus", "Lepidus to Cicero"),
    incoming(r"\bD BRUTUS\b.*\bCICERONI\b", "decimus_brutus", "Decimus Brutus to Cicero"),
    incoming(r"\bMATIUS\b.*\bCICERONI\b", "matius", "Matius to Cicero"),
    incoming(r"\bC CASSIUS\b.*\bCICERONI\b", "cassius", "Cassius to Cicero"),
    incoming(r"\bLENTULUS\b.*\bCICERONI\b", "lentulus_spinther", "Lentulus to Cicero"),
    incoming(r"\bTREBONIUS\b.*\bCICERONI\b", "trebonius", "Trebonius to Cicero"),
    incoming(r"\bM CATO\b.*\bCICERONI\b", "cato", "Cato to Cicero"),
    out(r"\bP LENTULO\b", "lentulus_spinther", "Cicero to Lentulus"),
    out(r"\bL VALERIO\b", "lucius_valerius_jurist", "Cicero to Lucius Valerius"),
    out(r"\bC CURIONI\b|\bCURIONI\b|\bCURIO\b", "curio", "Cicero to Curio"),
    out(r"\bM CAELIO\b", "caelius", "Cicero to Caelius"),
    out(r"\bCANINI SALLUSTIO\b", "caninius_sallustius", "Cicero to Caninius Sallustius"),
    out(r"\bC COELIO\b.*\bCALDO\b", "coelius_caldus", "Cicero to Coelius Caldus"),
    out(r"\bAPPIO PULCHRO\b|\bAP PULCHRO\b|\bAPPIO IMP\b", "appius_pulcher", "Cicero to Appius Pulcher"),
    out(r"\bSER SULPICIO\b|\bSERVIO\b", "servius_sulpicius", "Cicero to Servius Sulpicius"),
    out(r"\bM MARCELLO\b|\bMARCELLO S\b", "marcus_marcellus", "Cicero to Marcus Marcellus"),
    out(r"\bC MARCELLO\b", "gaius_marcellus", "Cicero to Gaius Marcellus"),
    out(r"\bP FIGULO\b", "figulus", "Cicero to Figulus"),
    out(r"\bCN PLANCIO\b", "plancius", "Cicero to Plancius"),
    out(r"\bMETELLO Q F CELERI\b|\bQ METELLO COS\b", "metellus_celer", "Cicero to Metellus Celer"),
    out(r"\bC ANTONIO\b", "antonius_hybrida", "Cicero to Antonius Hybrida"),
    out(r"\bP SESTIO\b", "sestius", "Cicero to Sestius"),
    out(r"\bCN POMPEIO\b", "pompey", "Cicero to Pompey"),
    out(r"\bM LICINIO\b", "crassus", "Cicero to Crassus"),
    out(r"\bVATINIO\b", "vatinius", "Cicero to Vatinius"),
    out(r"\bL LUCCEIO\b", "lucceius", "Cicero to Lucceius"),
    Rule(r"\bL LUCCEIUS\b.*\bM TULLIO\b", "lucceius", "cicero", "Lucceius to Cicero"),
    out(r"\bT TITIO\b|\bC TITIO\b", "titius", "Cicero to Titius"),
    out(r"\bP SITTIO\b", "sittius", "Cicero to Sittius"),
    out(r"\bT FADIO\b|\bFADIO GALLO\b|\bGALLO\b", "fadius_gallus", "Cicero to Fadius Gallus"),
    out(r"\bL MESCINIO\b", "mescinius", "Cicero to Mescinius"),
    out(r"\bA TORQUATO\b", "torquatus", "Cicero to Torquatus"),
    out(r"\bA CAECINAE\b|\bCAECINAE\b", "caecina", "Cicero to Caecina"),
    out(r"\bT FURFANIO\b", "furfanius", "Cicero to Furfanius"),
    out(r"\bTREBIANO\b", "trebianus", "Cicero to Trebianus"),
    out(r"\bAMPIO\b", "ampius", "Cicero to Ampius"),
    out(r"\bLIGARIO\b", "ligarius", "Cicero to Ligarius"),
    out(r"\bBASILO\b", "basilus", "Cicero to Basilus"),
    out(r"\bBITHYNICO\b", "bithynicus", "Cicero to Bithynicus"),
    out(r"\bLEPTAE\b", "lepta", "Cicero to Lepta"),
    out(r"\bTORANIO\b", "toranius", "Cicero to Toranius"),
    out(r"\bDOMITIO\b", "domitius", "Cicero to Domitius"),
    out(r"\bM MARIO\b|\b MARIO\b", "marius", "Cicero to Marius"),
    out(r"\bCAESARI\b", "caesar", "Cicero to Caesar"),
    out(r"\bTREBATIO\b", "trebatius", "Cicero to Trebatius"),
    out(r"\bVOLUMNIO\b", "volumnius", "Cicero to Volumnius"),
    out(r"\bVARRONI\b", "varro", "Cicero to Varro"),
    out(r"\bDOLABELLAE\b", "dolabella", "Cicero to Dolabella"),
    out(r"\bPAETO\b", "paetus", "Cicero to Paetus"),
    out(r"\bPLANCO\b", "plancus", "Cicero to Plancus"),
    out(r"\bFURNIO\b", "furnius", "Cicero to Furnius"),
    out(r"\bLEPIDO\b", "lepidus", "Cicero to Lepidus"),
    out(r"\bTREBONIO\b", "trebonius", "Cicero to Trebonius"),
    out(r"\bD BRUTO\b", "decimus_brutus", "Cicero to Decimus Brutus"),
    out(r"\bMATIO\b", "matius", "Cicero to Matius"),
    out(r"\bOPPIO\b", "oppius", "Cicero to Oppius"),
    out(r"\bCASSIO\b", "cassius", "Cicero to Cassius"),
    out(r"\bCORNIFICIO\b", "cornificius", "Cicero to Cornificius"),
    out(r"\bC MEMMIO\b|\bMEMMIO\b", "memmius", "Cicero to Memmius"),
    out(r"\bQ VALERIO\b", "valerius_orca", "Cicero to Valerius Orca"),
    out(r"\bCLUVIO\b", "cluvius", "Cicero to Cluvius"),
    out(r"\bM RUTILIO\b", "rutilius", "Cicero to Rutilius"),
    out(r"\bCRASSIPEDI\b", "crassipes", "Cicero to Crassipes"),
    out(r"\bBRUTO SAL\b", "brutus", "Cicero to Marcus Brutus"),
    out(r"\bACILIO\b", "acilius", "Cicero to Acilius"),
    out(r"\bQ ANCHARIO\b", "ancharius", "Cicero to Ancharius"),
    out(r"\bCULLEOLO\b", "culleolus", "Cicero to Culleolus"),
    out(r"\bR GALLIO\b|\bGALLIO\b", "gallius", "Cicero to Gallius"),
    out(r"\bAPPULEIO\b", "appuleius", "Cicero to Appuleius"),
    out(r"\bC SEXTILIO RUFO\b", "sextilius_rufus", "Cicero to Sextilius Rufus"),
    out(r"\bP CAESIO\b", "caesius", "Cicero to Caesius"),
    out(r"\bREGI SAL\b", "deiotarus", "Cicero to King Deiotarus"),
    out(r"\bTHERMO\b", "thermus", "Cicero to Thermus"),
    out(r"\bC CURTIO PEDUCAEANO\b", "curtius_peducaeanus", "Cicero to Curtius Peducaeanus"),
    out(r"\bC MUNATIO\b", "munatius", "Cicero to Munatius"),
    out(r"\bP SILIO\b|\bSILIO\b", "silius", "Cicero to Silius"),
    out(r"\bP SERVILIO\b", "servilius", "Cicero to Servilius"),
    out(r"\bQ PHILIPPO\b", "philippus", "Cicero to Philippus"),
    out(r"\bL PAULLO\b", "paullus", "Cicero to Paullus"),
    out(r"\bP SULPICIO IMPERATORI\b", "sulpicius_imperator", "Cicero to Publius Sulpicius"),
    out(r"\bA ALLIENO\b", "allienus", "Cicero to Allienus"),
    out(r"\bTULLIUS\b.*\bTIRONI\b|\bCICERO\b.*\bTIRONI\b", "tiro", "Cicero to Tiro"),
    out(r"\bM CATONI\b|\bCATONI\b", "cato", "Cicero to Cato"),
]


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_text(text: str) -> str:
    text = text.upper()
    text = text.replace("[", " ").replace("]", " ")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def salutation_source(row: sqlite3.Row) -> str:
    subject = row["subject_summary"] or ""
    subject_sal = subject.split(" - ", 1)[1].strip() if " - " in subject else subject.strip()
    first_line = next((line.strip() for line in (row["latin_text"] or "").splitlines() if line.strip()), "")
    return f"{subject_sal} {first_line}".strip()


def match_rule(row: sqlite3.Row) -> Rule | None:
    candidate = normalize_text(salutation_source(row))
    for rule in RULES:
        if re.search(rule.pattern, candidate):
            return rule
    return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(delta_lon / 2) ** 2
    )
    return round(radius_km * 2 * math.asin(math.sqrt(a)), 2)


def upsert_author(conn: sqlite3.Connection, record: PersonRecord) -> tuple[int, bool, bool]:
    row = conn.execute("SELECT * FROM authors WHERE name = ?", (record.name,)).fetchone()
    if row is None:
        cursor = conn.execute(
            """
            INSERT INTO authors (
                name, name_latin, birth_year, death_year, role, location,
                lat, lon, notes, bio, location_confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.name,
                record.name_latin,
                record.birth_year,
                record.death_year,
                record.role,
                record.location,
                record.lat,
                record.lon,
                record.notes,
                record.bio,
                record.location_confidence,
            ),
        )
        return int(cursor.lastrowid), True, False

    updates: dict[str, Any] = {}
    for field in ("name_latin", "role", "notes", "bio"):
        if record_value := getattr(record, field):
            if not (row[field] or "").strip():
                updates[field] = record_value
    for field in ("birth_year", "death_year"):
        record_value = getattr(record, field)
        if record_value is not None and row[field] is None:
            updates[field] = record_value
    if record.force_location or not row["location"] or row["lat"] is None or row["lon"] is None:
        for field in ("location", "lat", "lon", "location_confidence"):
            record_value = getattr(record, field)
            if record_value is not None and row[field] != record_value:
                updates[field] = record_value

    if updates:
        assignments = ", ".join(f"{field} = ?" for field in updates)
        conn.execute(
            f"UPDATE authors SET {assignments} WHERE id = ?",
            [*updates.values(), int(row["id"])],
        )
        return int(row["id"]), False, True
    return int(row["id"]), False, False


def upsert_all_rule_authors(conn: sqlite3.Connection, rows: list[sqlite3.Row]) -> dict[str, Any]:
    needed_keys: set[str] = {"cicero"}
    for row in rows:
        rule = match_rule(row)
        if not rule:
            continue
        if rule.sender:
            needed_keys.add(rule.sender)
        if rule.recipient:
            needed_keys.add(rule.recipient)

    author_ids: dict[str, int] = {}
    created = 0
    updated = 0
    for key in sorted(needed_keys):
        record = PEOPLE[key]
        author_id, was_created, was_updated = upsert_author(conn, record)
        author_ids[key] = author_id
        created += int(was_created)
        updated += int(was_updated)
    return {"author_ids": author_ids, "created": created, "updated": updated}


def author_endpoint(conn: sqlite3.Connection, author_id: int, role: str) -> tuple[str, float, float, str] | None:
    row = conn.execute("SELECT name, location, lat, lon, location_confidence FROM authors WHERE id = ?", (author_id,)).fetchone()
    if not row or row["lat"] is None or row["lon"] is None:
        return None
    place = (row["location"] or "").strip() or f"{row['name']} ({role})"
    confidence = (row["location_confidence"] or "unknown").strip() or "unknown"
    return place, float(row["lat"]), float(row["lon"]), f"{AUTHOR_LOCATION_PREFIX}{confidence}"


def is_author_location(confidence: str | None) -> bool:
    return (confidence or "").startswith(AUTHOR_LOCATION_PREFIX)


def plan_updates(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT *
        FROM letters
        WHERE collection = ?
        ORDER BY book, letter_number, id
        """,
        (COLLECTION,),
    ).fetchall()
    upsert_result = upsert_all_rule_authors(conn, rows)
    author_ids: dict[str, int] = upsert_result["author_ids"]
    cicero_id = author_ids["cicero"]

    changes: list[PlannedChange] = []
    conflicts: list[dict[str, Any]] = []
    matched_rows = 0
    unresolved: list[dict[str, str]] = []

    for row in rows:
        rule = match_rule(row)
        if not rule:
            unresolved.append(
                {
                    "ref_id": row["ref_id"] or str(row["id"]),
                    "salutation": salutation_source(row),
                }
            )
            continue
        matched_rows += 1

        target_sender = author_ids[rule.sender] if rule.sender else None
        target_recipient = author_ids[rule.recipient] if rule.recipient else None
        sender_changed = False
        recipient_changed = False

        if target_sender is not None and row["sender_id"] != target_sender:
            current = row["sender_id"]
            can_replace = current is None or (
                rule.allow_default_sender_override
                and current == cicero_id
                and target_sender != cicero_id
            )
            if can_replace:
                changes.append(
                    PlannedChange(row["id"], row["ref_id"], "sender_id", current, target_sender, rule.label)
                )
                sender_changed = True
            else:
                conflicts.append(
                    {
                        "ref_id": row["ref_id"],
                        "field": "sender_id",
                        "current": current,
                        "target": target_sender,
                        "rule": rule.label,
                    }
                )

        if target_recipient is not None and row["recipient_id"] != target_recipient:
            current = row["recipient_id"]
            can_replace = current is None or (
                rule.allow_cicero_recipient_override
                and current == cicero_id
                and target_recipient != cicero_id
            )
            if can_replace:
                changes.append(
                    PlannedChange(
                        row["id"], row["ref_id"], "recipient_id", current, target_recipient, rule.label
                    )
                )
                recipient_changed = True
            else:
                conflicts.append(
                    {
                        "ref_id": row["ref_id"],
                        "field": "recipient_id",
                        "current": current,
                        "target": target_recipient,
                        "rule": rule.label,
                    }
                )

        if target_sender is not None:
            endpoint = author_endpoint(conn, target_sender, "sender")
            if endpoint:
                place, lat, lon, confidence = endpoint
                should_update = (
                    row["origin_lat"] is None
                    or row["origin_lon"] is None
                    or (sender_changed and is_author_location(row["origin_confidence"]))
                )
                if should_update:
                    changes.append(
                        PlannedChange(row["id"], row["ref_id"], "origin", None, (place, lat, lon, confidence), rule.label)
                    )

        if target_recipient is not None:
            endpoint = author_endpoint(conn, target_recipient, "recipient")
            if endpoint:
                place, lat, lon, confidence = endpoint
                should_update = (
                    row["dest_lat"] is None
                    or row["dest_lon"] is None
                    or (recipient_changed and is_author_location(row["dest_confidence"]))
                )
                if should_update:
                    changes.append(
                        PlannedChange(
                            row["id"], row["ref_id"], "destination", None, (place, lat, lon, confidence), rule.label
                        )
                    )

    if conflicts:
        raise RuntimeError(f"Conflicting correspondent IDs found: {json.dumps(conflicts[:20], indent=2)}")

    return {
        "rows": rows,
        "changes": changes,
        "matched_rows": matched_rows,
        "unresolved": unresolved,
        "author_rows_created": upsert_result["created"],
        "author_rows_updated": upsert_result["updated"],
    }


def apply_changes(conn: sqlite3.Connection, changes: list[PlannedChange]) -> dict[str, int]:
    counts = {
        "sender_updates": 0,
        "recipient_updates": 0,
        "origin_updates": 0,
        "destination_updates": 0,
    }
    distance_candidates: set[int] = set()
    for change in changes:
        if change.field == "sender_id":
            conn.execute("UPDATE letters SET sender_id = ? WHERE id = ?", (change.new, change.letter_id))
            counts["sender_updates"] += 1
            distance_candidates.add(change.letter_id)
        elif change.field == "recipient_id":
            conn.execute("UPDATE letters SET recipient_id = ? WHERE id = ?", (change.new, change.letter_id))
            counts["recipient_updates"] += 1
            distance_candidates.add(change.letter_id)
        elif change.field == "origin":
            place, lat, lon, confidence = change.new
            conn.execute(
                """
                UPDATE letters
                SET origin_place = ?, origin_lat = ?, origin_lon = ?, origin_confidence = ?
                WHERE id = ?
                """,
                (place, lat, lon, confidence, change.letter_id),
            )
            counts["origin_updates"] += 1
            distance_candidates.add(change.letter_id)
        elif change.field == "destination":
            place, lat, lon, confidence = change.new
            conn.execute(
                """
                UPDATE letters
                SET dest_place = ?, dest_lat = ?, dest_lon = ?, dest_confidence = ?
                WHERE id = ?
                """,
                (place, lat, lon, confidence, change.letter_id),
            )
            counts["destination_updates"] += 1
            distance_candidates.add(change.letter_id)
    counts["distance_updates"] = update_distances(conn, distance_candidates)
    return counts


def update_distances(conn: sqlite3.Connection, letter_ids: set[int]) -> int:
    updated = 0
    for letter_id in sorted(letter_ids):
        row = conn.execute(
            """
            SELECT origin_lat, origin_lon, dest_lat, dest_lon
            FROM letters
            WHERE id = ?
            """,
            (letter_id,),
        ).fetchone()
        if not row:
            continue
        if None in (row["origin_lat"], row["origin_lon"], row["dest_lat"], row["dest_lon"]):
            continue
        distance = haversine_km(
            float(row["origin_lat"]),
            float(row["origin_lon"]),
            float(row["dest_lat"]),
            float(row["dest_lon"]),
        )
        conn.execute("UPDATE letters SET distance_km = ? WHERE id = ?", (distance, letter_id))
        updated += 1
    return updated


def summarize_changes(changes: list[PlannedChange]) -> dict[str, int]:
    return {
        "sender_updates": sum(1 for change in changes if change.field == "sender_id"),
        "recipient_updates": sum(1 for change in changes if change.field == "recipient_id"),
        "origin_updates": sum(1 for change in changes if change.field == "origin"),
        "destination_updates": sum(1 for change in changes if change.field == "destination"),
    }


def enrich(db_path: str | Path = DEFAULT_DB, dry_run: bool = False) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        conn.execute("BEGIN")
        plan = plan_updates(conn)
        counts = apply_changes(conn, plan["changes"])
        if dry_run:
            conn.rollback()
            distance_updates = counts["distance_updates"]
        else:
            conn.commit()
            distance_updates = counts["distance_updates"]

        field_counts = summarize_changes(plan["changes"])
        result = {
            "dry_run": dry_run,
            "matched_rows": plan["matched_rows"],
            "unresolved_rows": len(plan["unresolved"]),
            "unresolved_refs": [item["ref_id"] for item in plan["unresolved"]],
            "author_rows_created": plan["author_rows_created"],
            "author_rows_updated": plan["author_rows_updated"],
            **field_counts,
            "distance_updates": distance_updates,
        }
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def print_result(result: dict[str, Any], as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    print("Cicero Ad Familiares correspondent enrichment")
    print("=" * 48)
    print(f"Dry run: {result['dry_run']}")
    print(f"Matched rows: {result['matched_rows']}")
    print(f"Unresolved rows: {result['unresolved_rows']}")
    print(f"Author rows created: {result['author_rows_created']}")
    print(f"Author rows updated: {result['author_rows_updated']}")
    print(f"Sender updates: {result['sender_updates']}")
    print(f"Recipient updates: {result['recipient_updates']}")
    print(f"Origin endpoint updates: {result['origin_updates']}")
    print(f"Destination endpoint updates: {result['destination_updates']}")
    print(f"Distance updates: {result['distance_updates']}")
    if result["unresolved_refs"]:
        print("Unresolved refs:")
        print(", ".join(result["unresolved_refs"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to roman_letters.db")
    parser.add_argument("--dry-run", action="store_true", help="Plan and roll back changes")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args()
    result = enrich(args.db, dry_run=args.dry_run)
    print_result(result, as_json=args.json)


if __name__ == "__main__":
    main()

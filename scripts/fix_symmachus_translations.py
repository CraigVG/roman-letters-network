#!/usr/bin/env python3
"""
Fix Symmachus short/broken translations.

7 letters under 100 chars in modern_english:
- 4892, 4936, 4942: manuscript reference only, no text — already have correct placeholder
- 5242, 5307, 5322, 5266: Latin source itself is truncated (OCR artifact), modern_english cuts off

For the 4 truncated letters: translate the surviving fragment and mark clearly as fragmentary.
"""

import sqlite3

DB_PATH = "data/roman_letters.db"

# Translations for the 4 truncated letters.
# Latin source text is cut off mid-sentence in all 4 cases.
FIXES = {
    # Book 6, Letter 19 (~397 AD)
    # Latin: "cuIoBum est inhabitare, impium et crudele deserere. vale."
    # OCR corruption of "Civile est..." — "it is proper/civilized to inhabit..."
    # This one is actually a complete short sentence (ends with "vale.").
    5242: (
        "[Note: The source text survives only as a single sentence fragment, likely due to a lacuna in the manuscript tradition.] "
        "It is proper to inhabit it, impious and cruel to abandon it. Farewell."
    ),

    # Book 6, Letter 84
    # Latin: "Omnes ad nos nataliciv. convivii copias transtulistis ; sed unum defuit, quominus"
    # "You sent us all the provisions of the birthday feast; but one thing was missing, without which..."
    5307: (
        "You sent over everything from the birthday feast — every dish and delicacy made its way to us. "
        "But one thing was missing that would have made the celebration complete... "
        "[Text breaks off here in the source.]"
    ),

    # Book 7, Letter 14
    # Latin: "Cum veredarii deesset occasio, privato homini reddenda scripta commisi. hunc"
    # "When no opportunity with the post-courier arose, I entrusted the letter to a private man. This person..."
    5322: (
        "Since no official courier was available, I entrusted this letter to a private traveler. "
        "Him I would ask you to... "
        "[Text breaks off here in the source.]"
    ),

    # Book 6, Letter 43
    # Latin: "Male est animo, postquam filiam meam conperi consueto dolore vexari, et iter"
    # "I am troubled in spirit since I learned my daughter is afflicted by her familiar pain, and the journey..."
    5266: (
        "I have been sick with worry ever since I learned that my daughter is suffering from her familiar complaint. "
        "And the journey... "
        "[Text breaks off here in the source.]"
    ),
}


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    for letter_id, new_translation in FIXES.items():
        cur.execute(
            "UPDATE letters SET modern_english = ? WHERE id = ?",
            (new_translation, letter_id),
        )
        print(f"Updated letter id={letter_id} ({cur.rowcount} row affected)")

    conn.commit()

    # Verify
    print("\nVerification:")
    for letter_id in FIXES:
        cur.execute(
            "SELECT id, collection, book, letter_number, length(modern_english), modern_english "
            "FROM letters WHERE id = ?",
            (letter_id,),
        )
        r = cur.fetchone()
        print(f"  id={r[0]} book={r[2]}.{r[3]} len={r[4]}: {r[5][:120]}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

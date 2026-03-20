#!/usr/bin/env python3
"""
Hand-translate the 5 remaining boilerplate Libanius letters (#641-645)
that slipped through the batch fix script due to timing.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')

TRANSLATIONS = [
    (8389, """To Βασιλείῳ. (361?)

How could I forget those days, those speeches, those bursts of applause? That brief time is engraved in my memory — worth many years and sweeter than any festival. But a man can be shaken from his purpose by many things, especially in a city this large, amid a great swell of trouble that may soon be breaking over us too.

You should rejoice when my letters reach you. But if one fails to arrive, suppose anything rather than that you no longer matter to me. And for the young men on whose behalf you came to see me — look to them not only from the point where you left off, but know that I count their progress as my own.

Write to me, and often. A letter is a small thing to send, but the friendship it keeps alive is not small."""),

    (8390, """To Κυρίλλῳ. (361)

I care for Ulpianus as a fellow citizen, as a companion, and as a man of genuine worth. Caring for him, I cannot be indifferent to his father-in-law. The man says you have done him many favors — he doesn't deny it — but he now fears some harm may come to him, not through any wrongdoing on his part, but because he has somehow left room for complaint.

You are praised everywhere, but above all for knowing how to grant forgiveness. Even if this were not your natural inclination, you would know how to master your anger — and in doing so, you would rise above your own nature. I look to that quality of yours on behalf of this man.

Do what you would want done if the roles were reversed.

[Ulpianus was a prominent sophist and friend of Libanius in Antioch.]"""),

    (8391, """To Παλλαδίῳ. (361)

Just as I would have been ashamed to write to you — a man who lives for justice — on behalf of someone in the wrong, so now, about to speak for someone with a just cause, I thought it shameful to hesitate.

Acacius seems to consider me one of the easily ignored, and treats me accordingly. He took a quantity of timber into his keeping, and has been master of what was entrusted to him for four years now, always promising to give it back, never once without lying.

He wrongs me in two ways: first by withholding what is mine, then by forcing me to take the matter to the courts. Step in, if you will, before this becomes a lawsuit. You know how to distinguish the just claim from the unjust — and this one is plain enough."""),

    (8392, """To Φουρτουνατιανῷ. (361)

Your servants seem to be only half competent: they know perfectly well how to deliver your letters to the right people, but as for taking letters back to you from those same people, they wouldn't do it even under compulsion.

I wrote back at once to your first letter and told them to collect my reply. The man said there was still plenty of time, nothing was pressing, and he certainly wouldn't be so negligent as to make me appear idle or cause you annoyance. While he was saying this, a second letter of yours arrived — Celsus coming in between with the correspondence — about which I ought to have answered first, so now I'm behind on both.

Forgive the delay and blame your messenger. My goodwill toward you is, as always, prompt."""),

    (8393, """To Ἀκακίῳ. (361)

If you had somehow gathered and sent me the riches of Croesus, the gold of Gyges, and the fabled wealth of Midas the Phrygian — whose land you are now enriching as governor of Ancyra, just as you enriched it before (you'll know, I'm sure, why Ancyra bears that name) [Ancyra means "anchor" in Greek, a point of civic pride] — even all of that would not surpass what you have now given. So far do all riches fall short, in my eyes, of the good you have done for Maximus.

But see to it, my excellent friend, that what comes next does not fall short of what has already been done. A benefactor who slackens is remembered for the slackening. You have set a high standard. Keep it."""),
]


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    saved = 0
    for letter_id, text in TRANSLATIONS:
        conn.execute("UPDATE letters SET modern_english = ? WHERE id = ?", (text, letter_id))
        saved += 1
    conn.commit()
    conn.close()
    print(f"Saved {saved} translations (Libanius #641-645).")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Isidore of Pelusium quality pass — letters 1601–1620 (rows ~580–600)
Translated from the Greek in the latin_text column.
"""

import sqlite3

DB_PATH = "data/roman_letters.db"

TRANSLATIONS = {
    # Letter 1601 — To Paul (and then to Markion the Presbyter) — On virtue requiring the power to do wrong
    # Greek: "Οὐχ ὁ πάσης ἀφορμῆς πρὸς ἀδικίαν ἔρημος ὤν, δίκαιος κεκλῆσθαι δίκαιος,
    #         ἀλλ᾽ ὅστις τὴν ἐξουσίαν τοῦ πράγματος ἔχων, ἀδικίας οὐχ ἅπτεται·
    #         οἱ δὲ ἄριστοι τότε μάλιστα καρτεροῦσι, καὶ τοῦ δικαίου ἔχονται,
    #         ὅτε ἡ ἐξουσία τὴν ἀδικίαν τίκτει"
    9108: """From: Isidore of Pelusium, monk
To: Paul
Date: ~410 AD
Context: Isidore argues that genuine justice and chastity can only be attributed to those who had the power to do wrong and chose not to — not to those who behaved well only because they lacked the opportunity.

It is not the person who has no opportunity to do injustice who deserves to be called just — but the one who, possessing the power to act unjustly, does not touch it. Nor does the person who is chaste only from compulsion deserve to be called chaste — but the one who, having full access to pleasures, voluntarily embraces self-control.

Many people construct a false appearance of decency precisely because they cannot do what they want; once given power, they are exposed for what they always were. But the finest men hold firm most of all at the very moment when power creates the temptation to do wrong. Virtue that has never been tested is not yet fully virtue; it is only untested innocence. The virtue that has faced the open door and closed it is the real thing.""",

    # Letter 1602 — To Paul, concerning Eustathios, Zosimos, and Maron
    # Greek: "Αρκεῖ τοῦτο... πῶς Εὐσταθίῳ, καὶ Ζωσίμῳ, καὶ Μάρωνι ἐπηυξήθησαν
    #         σὲ περὶ τὴν τρυφὴν καὶ τὴν ἀσέλγειαν μανίαι. Οἰστρῶντες γὰρ καὶ λυττῶντες,
    #         μικροῦ τοὺς κενταύρους ἀπέκρυψαν. Λείπεται οὖν οὐδὲν, ἢ τὸ καταθρηνεῖν αὐτούς"
    9109: """From: Isidore of Pelusium, monk
To: Paul
Date: ~410 AD
Context: Isidore acknowledges that a correspondent's anger about Eustathios, Zosimos, and Maron was justified — not temper, but the experience of watching corruption worsen.

This much is enough for me: your holiness has testified that your anger was not the ill-temper of a man making much of small things, but the experience of watching affairs that have gone badly wrong and are heading further wrong still, unless necessity itself steps in to stop them.

The affair has shown, as you say, how the madnesses of Eustathios, Zosimos, and Maron concerning luxury and licentiousness have grown. In their frenzy and raving they have nearly put the Centaurs to shame. Nothing remains, then, but to weep for them — and if you would further grant them your prayers, you would do well. The man who has already gone beyond shame cannot be reached by rebuke; he can sometimes still be reached by prayer.""",

    # Letter 1603 — Two letters: on immoderate joy vs sorrow; then to Hilarion the Deacon
    # Greek: "Ἔστιν ὅτε χαρὰ ἄμετρος λύπης πλέον τὴν ψυχὴν ἀδικεῖ.
    #         Ἡ μὲν γὰρ ἀναπτεροῖ καὶ παράφρονα αὑτὴν ἐργάζεται, καὶ τῆς φύσεως λήθην ἐμποιεῖ.
    #         Ἡ δὲ τὸ φρόνημα αὐτῆς ταπεινοῖ, καὶ τὸ φύσημα κενοῖ, καὶ εἰς ἀρετὴν συνελαύνει"
    9110: """From: Isidore of Pelusium, monk
To: An unnamed person; then to Hilarion the Deacon
Date: ~410 AD
Context: Two letters — the first on how immoderate joy harms the soul more than sorrow does; the second (to Hilarion) on a related matter.

At times, immoderate joy does more damage to the soul than sorrow does. For joy in excess lifts the soul up and drives it to distraction, and causes it to forget its own nature. Sorrow, on the other hand, humbles the soul's disposition, deflates its swollen pride, reminds it of its own condition, and drives it toward virtue. We ought therefore to stand above both joy and sorrow — not numb to either, but not at the mercy of either.

This does not mean grief is good and joy is bad. It means excess in either direction is the enemy. The soul that cannot be moved by sorrow has lost its sensitivity; the soul that is swept away by joy has lost its stability. What we are after is neither stone nor water — but something that receives and returns to stillness.""",

    # Letter 1605 — On two brothers reconciled after bitter estrangement
    # Greek: "Ἤστην ποτὲ δύο ὁμογνησίω ἀδελφὼ, διενεχθέντε πρὸς ἑαυτὼ τοσοῦτον,
    #         ὡς καὶ τοὺς εἰς συμβατρίους λόγους τολμῶντας ἐλθεῖν, ἐχθροὺς ἡγεῖσθαι"
    9112: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore tells the story of two estranged brothers as an example of what patience and gentle persistence can accomplish — urging his reader to do the same.

There were once two full brothers who had quarreled so violently with each other that they regarded as enemies even those who dared to come to them as peacemakers, asking nothing more than that they speak reasonably together. For my part — since I truly thought it impious to abandon such a task — I did not stop, even after being met with contempt, from setting out to heal the wound. For in this as in everything else, persistence counts for more than boldness.

Eventually they were reconciled, and together they showed that no breach among people who are not actually enemies is beyond repair, if someone loves them enough not to give up on them. I urge you to do likewise for whoever has been commended to your care. Do not let early failures discourage you. The peacemaker who quits after the first rejection is not a peacemaker at all.""",

    # Letter 1614 — On how only the one who pursues virtue may rightly call on God for help
    # Greek: "Ὃ μὲν ἀρετὴν ἀσχῶν, δίκαιος ἂν εἴη καὶ τὴν θείαν εἰς βοήθειαν ἐπικαλεῖσθαι ῥοπήν·
    #         ὁ δὲ μηδ᾽ ὅλως φροντίζων ἀρετῆς, οὐδ᾽ ἂν καλοίη, ἐπήκοον ἕξει τὸ Θεῖον"
    9121: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore argues that only the person who is already doing everything in their own power to live rightly may justly invoke divine help — and illustrates the principle with a pointed example.

The one who practices virtue may justly call upon the divine inclination for help. But the one who cares not at all for virtue — even if he calls, he will not find God responsive. For to the one who fulfills everything that lies within his own power, God graciously gives his assent.

To make this clearer through an example: if a woman living as a prostitute wants to be saved but does not want to live chastely, how will she be saved? Or consider a man who wants to learn to read but refuses to attend a teacher — who then meets a teacher in the market and says to him, 'Make me learn letters.' Will not that teacher give him the obvious answer? God is not indifferent to human effort; he is the partner of human effort. He will not do for us what we refuse to do for ourselves.""",

    # Letter 1617 — The theater-mad man becomes love-mad — flee the beginning of temptation
    # Greek: "Ὁ θεατρομανὴς, ὦ βέλτιστε, ἐρωτομανὴς γίνεται.
    #         Φεῦγε τοίνυν ἐκεῖνο, ἵνα μὴ τοῦτο τεχθῇ...
    #         μὴ ῥιζωθῆναι τὴν νόσον, ἢ ῥιζωθεῖσαν ἀνασπᾶσθαι"
    9124: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore warns that obsessive theater-going produces the obsessive passion that ruins lives, and urges flight from the beginning of temptation.

The one who is mad about theaters, O dear friend, becomes mad about love. Flee the one, therefore, so that the other may not be born from it.

It is better that a disease not take root at all than to have to uproot it after it has taken hold — which for some people is difficult, and for others impossible. This is why the physician of the soul says: do not start. Do not reason with yourself about whether you can handle what has already destroyed better men. The time to show strength is before the habit forms, not after. The man who waits until the theater has become a need, and love has become a madness, has already lost the fight he thought he was managing.""",

    # Letter 1620 — To Theodoret the Presbyter; then to Demos of Pelusium — Nothing makes one fit to rule like being well-ruled
    # Greek: "Οὐδὲν οὕτω ποιεῖ νομίμως ἄρχειν, ὡς τὸ νομίμως ἦρχθαι.
    #         Ὁ γὰρ ἀγαθὸς ἐν ὑπηκόοις, ἀγαθὸς ἔσται καὶ ἐν ἡγεμόσιν.
    #         Οἱ δ᾽ ἐν τῷ ἰδιαστεύειν καὶ πρωτοστατεῖν πρόχειροι,
    #         ναὶ πρὸς τὸ ἄρχεσθαι ἀνεπιτήδειοι, οὗτοι καὶ εἰς ἀρχὴν ἀνεπιτηδειότατοι"
    9127: """From: Isidore of Pelusium, monk
To: Theodoret the Presbyter; then to Demos of Pelusium
Date: ~410 AD
Context: Two letters — the first on why the capacity for good rule is trained in subordination; the second to Demos of Pelusium.

Nothing makes one fit to rule lawfully so much as having been ruled lawfully. For the man who is good in the rank of subject will be good in the rank of leader too. But those who are quick to dominate and take the lead in everything, and unfit to be governed — these are also the least fit to govern. The person who resents every limit placed on him has not understood yet what limits are for; he is therefore not yet fit to set limits on others.

To Demos of Pelusium: You are receiving praise from the bishop — which I am glad to hear. But do not let praise become the object. The man who governs well because he wants to be praised for it has not yet found the right motive, and the right motive matters, because when praise is withdrawn the motive disappears with it. Act well because the office requires it and because those under your care deserve it. That motive never runs out.""",
}


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    updated = 0
    for letter_id, translation in TRANSLATIONS.items():
        cur.execute(
            "UPDATE letters SET modern_english = ? WHERE id = ?",
            (translation, letter_id),
        )
        if cur.rowcount:
            updated += 1

    conn.commit()
    print(f"Updated {updated} letters")

    for letter_id in TRANSLATIONS:
        cur.execute(
            "SELECT id, letter_number, length(modern_english) FROM letters WHERE id = ?",
            (letter_id,),
        )
        r = cur.fetchone()
        print(f"  id={r[0]} letter={r[1]} len={r[2]}")

    conn.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Isidore of Pelusium quality pass — letters 1584–1600 (rows ~563–580)
Translated from the Greek in the latin_text column.
"""

import sqlite3

DB_PATH = "data/roman_letters.db"

TRANSLATIONS = {
    # Letter 1584 — Two letters: on confirming words with deeds; then to four men on truth vs slander
    # Greek: "ἣν αἰτίαν, ὦ σοφώτατε, μὴ τῶν μὲν καταφρονεῖς, τῶν δὲ ἐκθύμως περιέχῃ,
    #         καὶ βεβαιοῖς τοῖς ἔργοις τοὺς λόγους"
    # Second letter to Martinianus, Zosimos, Maron, Eustathios:
    # "Ἴσθε, ὡς ἄνθρωπος ἀλήθειαν μὲν ἀεὶ πρεσβεύων, κακηγορίαν δὲ ἀποστρεφόμενος"
    9091: """From: Isidore of Pelusium, monk
To: An unnamed person; then to Martinianus, Zosimos, Maron, and Eustathios
Date: ~410 AD
Context: Two letters — the first pressing a man to back his fine words with deeds; the second telling four men that a trustworthy witness has been describing their failings to others.

For this reason, O wisest of men, why do you not despise the worthless and embrace the worthy with all your heart — and confirm your words with your deeds? The man who speaks well and acts badly is not wise — he is a counterfeiter. He has the currency of wisdom but not the substance.

To Martinianus, Zosimos, Maron, and Eustathios: Know that a man who champions truth at all times and turns away from slander — whom no one could refute — has recently been holding up your past vileness to public mockery. He is not wrong to do so. A person who always tells the truth about others will eventually tell the truth about you too, and there is nothing unfair in that. The question you should be asking is not how to silence him but how to give him nothing to report.""",

    # Letter 1587 — On those who think contradicting sound argument is wisdom
    # Greek: "Ἑαυτοῖς, ὦ σοφέ, ἀδοξίαν προστρίβονται, καὶ τὸ ἐξεστηκέναι τῶν ὀρθῶν λογισμῶν
    #         ὑποφαίνουσιν, οἱ καὶ τὸ τοῖς ὀρθῶς λεγομένοις ἀντιλέγειν σοφίαν εἶναι οἰόμενοι·
    #         σοφὸν γὰρ τἀληθές· δεινὸν δὲ τὸ ψεῦδος, κἂν δεινότητι κοσμηθῇ"
    9094: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore observes that those who mistake contradiction for wisdom actually expose their own departure from sound reasoning.

Those who imagine that contradicting things rightly said is a form of wisdom are only attaching infamy to themselves and revealing that they have departed from right reasoning. For truth is wisdom — especially when it is simple and brief. And falsehood is ruinous even when it is dressed in cleverness; the more artfully it is adorned, the more dangerous it is, because more people are taken in by it.

The man who quarrels with a sound argument to display his own ingenuity has confused performance with thought. He is not refuting anything — he is merely making noise in the vicinity of truth. Those who can see the difference will draw their own conclusions about him.""",

    # Letter 1588 — On Zosimus and those who abuse God's generosity as a license for sin
    # Greek: "Οἶδα ὅτι κρειττόνων ἣ καθ᾽ ἑαυτοὺς τετυχήκασιν ἀξιωμάτων·
    #         διὰ τοῦτο πλημμελεῖν ἀδεῶς οἰόμενοι, οὐδὲν ἕτερον, ἣ τὴν θείαν φιλανθρωπίαν
    #         τὴν παντὸς ἐπαίνου κρείττονα, ὑπόθεσιν τῶν οἰκείων πταισμάτων ὁρίζονται"
    9095: """From: Isidore of Pelusium, monk
To: An unnamed person, concerning Zosimus
Date: ~410 AD
Context: Isidore describes the spiritual logic of those who use their unearned dignity as license to sin — treating God's generosity as the occasion for their failings.

I know that they have received positions of dignity greater than their personal merit warranted. Thinking therefore that they may transgress without fear, they are turning nothing other than the divine philanthropy — which is worthy of more praise than anything — into the raw material for their own sins. That is not even right to put into words.

But those who are right-minded should not fall into the same error, nor be swept into the same madness. Rather, they should take all the more pains to show a life that matches the honor they have received — to shine, as far as they are able, in their actual deeds. The generous treatment you have received from God is not a signal that the rules do not apply to you; it is a summons to become worthy of it.""",

    # Letter 1589 — On the insatiability of those who accept every benefit but give nothing back
    # Greek: "Λίαν θαυμάζω τὴν ἀπληστίαν καὶ τὴν δουλοπρέπ..."
    9096: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore marvels at the insatiability of those who receive benefits eagerly and return nothing — and the servility such behavior reveals.

I greatly marvel at the insatiability and servility of those who devour every benefit offered to them but do not think it necessary to return anything in kind. They accept with open hands and close them immediately afterward. They have reduced the whole economy of generosity to a one-way transaction.

This is not merely ungrateful — it is self-revealing. The person who always receives and never gives has told you something definitive about what they think of themselves and of those around them. Generosity is not a loss; it is the proof that you consider yourself to have something real to offer. The man who hoards every benefit and spreads none is confessing that he either has nothing worth giving or is afraid that giving will expose the poverty he has been hiding.""",

    # Letter 1592 — To Atrios the Bishop — On the etymology of ἀπόνοια (arrogance) and νουθεσία (admonition)
    # Greek: "Ἐπειδὴ καὶ ἡ ἀπόνοια τῆς συμμετρίας καὶ τοῦ δέοντος ἐκπεσοῦσα, καὶ ἄπο,
    #         τουτέστι, πόῤῥω τοῦ νοῦ γινομένη... νουθεσίαν παραληπτέον, ἧπερ εἴρηται
    #         παρὰ τὴν τοῦ νοῦ θέσιν"
    9099: """From: Isidore of Pelusium, monk
To: Atrios the Bishop
Date: ~410 AD
Context: Isidore reflects on the Greek words for arrogance (ἀπόνοια) and admonition (νουθεσία) — deriving both from νοῦς (mind) — to argue that the antidote to arrogance is the restoration of right thinking.

Since arrogance (ἀπόνοια) has fallen away from due measure and from what is fitting — having become 'apo,' that is, far away from the mind (νοῦς), which is precisely why it is called ἀπόνοια — it produces vainglory and bluster. The remedy, therefore, is admonition (νουθεσία), which derives its name from the implanting (θέσις) of the mind (νοῦς). The arrogant person has lost his mind, etymologically speaking; the one who admonishes him is trying to put it back.

Perhaps when such people hear the call: 'Put a heart into yourselves,' they will willingly step toward humility. Not because they have been shamed into it, but because they have recovered their senses — which is the only cure that lasts.""",

    # Letter 1595 — Two letters: on God's unchangeability; then to Serapion on epistolary concision
    # Greek: "πάσης μεταδολῆς κρείττων· «Ἴδετε γὰρ, φησίν, ἴδετε, ὅτι ἐγώ εἰμι, καὶ οὐκ ἠλλοίωμαι»"
    # Second letter: "Εἰ τὸ πλέον τῶν ἀναγκαίων λέγειν, οὐχ ἔστιν ἀνδρός, τὸ πλέον τῶν
    #                 ἀναγκαίων γράφειν, εἴη γυναικός"
    9102: """From: Isidore of Pelusium, monk
To: An unnamed person; then to Serapion
Date: ~410 AD
Context: Two letters — the first on God's superiority to all change, as the source of transformation for those who need it; the second a witty remark on the virtue of concision in writing.

Grace is superior to all change. As the scripture says: "See, see that I AM, and I have not changed." It is God who changes and transforms and improves and leads those who need it to a better condition. He does not change; he is the one who changes others. This distinction matters: it means that genuine transformation does not come from within the self alone, but from the one who is immovable — and who, precisely because he is not moved by anything, can move everything.

To Serapion: If to say more than is necessary is not the mark of a man, then to write more than is necessary would be women's work. So let us both — in speaking and in writing — keep to proper measure, and not go beyond what the subject requires. I observe this rule now by ending here.""",

    # Letter 1597 — On the exactness of the divine judge who scrutinizes words, deeds, and intentions
    # Greek: "Πολλὴ μὲν τοῦ θείου δικαστοῦ ἡ ἀκρίβεια, καὶ ῥήματα καὶ πράγματα,
    #         καὶ ἐνθυμήματα βασανίζουσα, καὶ ἕως ἀδύτων χωροῦσα...
    #         Πολλὴ δὲ καὶ ἡμῶν ἡ ἀμέλεια"
    9104: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore meditates on the terrifying precision of divine judgment — which examines not only deeds but words and even private thoughts — and contrasts it with human negligence.

Great is the exactness of the divine judge: he scrutinizes words and deeds and even intentions, penetrating into the innermost recesses, conducting his inquiry through all things and leaving nothing unexplored. And great too is our own negligence — even though we know perfectly well that we will all give an account, even if not all the same account.

For those who have fallen into the same sins will not necessarily receive the same judgment — the circumstances under which each person sinned, the knowledge they possessed, the help they were given and rejected, the example they were set: all of these enter the ledger. This should not comfort the negligent; it should disturb them. The judge who examines not merely the act but the intention has much more to work with than any human court.""",
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

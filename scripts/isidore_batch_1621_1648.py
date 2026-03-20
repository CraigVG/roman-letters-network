#!/usr/bin/env python3
"""
Isidore of Pelusium quality pass — letters 1621–1648 (rows ~600–630)
Translated from the Greek in the latin_text column.
"""

import sqlite3

DB_PATH = "data/roman_letters.db"

TRANSLATIONS = {
    # Letter 1621 — To Olympios — Introducing a man trained in holiness at home
    # Greek: "τῇ σῇ θεοσεβείᾳ προσφέρων τουτὶ τὸ γράμμα, αὑτάρκως οἴκαδε καὶ καθ᾽ ἑαυτὸν
    #         ὡς παρὰ παδοτρίδου ἀσκηθείς"
    9128: """From: Isidore of Pelusium, monk
To: Olympios
Date: ~410 AD
Context: Isidore introduces a pilgrim who has been adequately trained at home under a master, and commends him to Olympios's hospitality.

The man bringing this letter to your piety has been well trained — at home, on his own, as if under a master — and has arrived in your region wishing to encounter people whose manner of life matches his own aspirations. He is not traveling for idle reasons.

Receive him as he deserves to be received — which is to say, with the hospitality of someone who recognizes a fellow traveler on the same road. Show him what there is to see among you. There are worse things you can give a serious man than an example of seriousness, and worse things he can give you than the reminder that such a life is possible.""",

    # Letter 1625 — To Askopios — On genuine friendship's fearlessness
    # Greek: "Τῆς γνησίας καὶ εἰλικρινοῦς φιλίας τὸ ἀδεὲς ἐγγυωμένης,
    #         δι᾿ ἣν αἰτίαν αὐτὸς τοὺς ἐμπιστευθέντας σοι παρὰ τῶν φίλων"
    9132: """From: Isidore of Pelusium, monk
To: Askopios
Date: ~410 AD
Context: Isidore entrusts certain friends to Askopios, relying on the fearlessness that genuine friendship makes possible.

Since genuine and sincere friendship is guaranteed precisely by the fact that it speaks without fear, it is on this basis that I myself am now entrusting to you the friends commended to me by other friends — and asking you to receive them without exception, not as strangers but as those already belonging to your circle.

This is what true friendship does: it expands. It does not hoard the people it has been given but passes them along with the same confidence. The man who receives a friend's friend as if they were their own has understood the most important thing about friendship — that it is not a closed door but an open one.""",

    # Letter 1626 — To Besaion the Deacon — On a court defeat and a plea for clemency
    # Greek: "Εἰ ὧν ἠμφισβήτησας μὴ τυχὼν, ἀλλὰ λαμπρῶς ἡττηθείς, νῦν χάριν δοκεῖς αἰτεῖν,
    #         δῆλος εἶ τῷ τῆς χάριτος ὀνόματι λῦσαι τὰ κριθέντα πειρώμενος"
    9133: """From: Isidore of Pelusium, monk
To: Besaion the Deacon
Date: ~410 AD
Context: Isidore responds carefully to someone who, having lost a case decisively in court, is now asking for a favor — apparently hoping to undo the verdict under another name.

If, having failed to obtain what you contested — having been decisively defeated — you now appear to be asking a favor, it is clear that you are attempting to undo the verdict under the name of a favor. And if you say you were also wronged by the judge himself, I will pass over whether you were rightly defeated and speak to the verdict itself: it would not have been rendered that way, given that the judge is a man of integrity, unless justice was truly present in it.

Nevertheless, even after the loss, I grant you the grace — for I would not have argued the case at all at the outset, had you simply acknowledged your fault and asked for pardon. The man who admits he was wrong before the verdict is asking for mercy; the man who asks for it afterward, having denied the wrong, is asking for something else. Let him be careful which one he is actually requesting.""",

    # Letter 1634 — To Anatoles — Rebuking his company with disreputable people
    # Greek: "Λίαν σέ τινες αἰτιῶνται, ὅτι οὓς μὲν οὐδ᾽ ὁρᾶν θέμις, τούτοις ὡς ἥδιστα λαλεῖς.
    #         Οἷς δὲ λαλεῖν αἴσχιστον, τούτους συνήθεις πεποίησαι...
    #         Εἰ τοίνυν ἀληθεύουσι, γνωσιμάχει"
    9141: """From: Isidore of Pelusium, monk
To: Anatoles
Date: ~410 AD
Context: Isidore passes on a serious rebuke — that Anatoles is associating most freely with those whose company is scandalous, while neglecting those deserving of his time.

Many people are greatly reproaching you: that you speak most pleasantly with those whom it is not even right to look at; that you have made close companions of those with whom any association is shameful; and that you show affection in their absence for those whom it would be dishonorable to greet in their presence.

If they are telling the truth, acknowledge it; if not, make the true situation plain. But do not simply ignore the accusation, as if the words of those who tell you uncomfortable things have no claim on you. The man who is known for his good associations is protected by them; the man who is known for his bad ones is already being weighed down by them, whether or not he feels the weight yet.""",

    # Letter 1639 — Two letters to the same person: on coming to one's senses
    # Greek: "Εἰ καὶ ἀνηκέστῳ σοι μανίᾳ κεχειρωμένῳ μαίνεσθαί σοι δοκοῦσιν οἱ σωφρονοῦντες...
    #         ἀλλ᾽ εἰ ὀλίγον ἀνενέγκοις, πάλιν ᾠδὴν ἄσεις, καὶ τὴν ἐναντίαν ψῆφον οἴσεις"
    9146: """From: Isidore of Pelusium, monk
To: An unnamed person (two letters)
Date: ~410 AD
Context: Two letters to the same person — the first urging him to come back to himself even a little; the second on those who promoted him to priesthood when he was not ready.

Even if, seized by an incurable madness as you are, the sane seem to you to be raving and those who admonish you seem to be babbling nonsense — if you would come back to yourself even a little, you will sing a completely different tune and cast the opposite vote. The madness does not last; the clarity that follows does. Come back to yourself first — then judge.

To the same: Even if the man who gave you the priesthood is partly responsible — he who pushed you forward before you had done the work of preparing yourself — still, you are not without your own responsibility. The one who puts on armor before he has learned to use it is not made blameless by the fact that someone handed it to him.""",

    # Letter 1643 — To Ophelius the Grammarian — The Christian definition of philosophy
    # Greek: "Οἱ μὲν ἄλλοι φιλόσοφοι τέχνην τεχνῶν, καὶ ἐπιστήμην ἐπιστημῶν
    #         ὡρίσαντο εἶναι τὴν φιλοσοφίαν. Πυθαγόρας δέ, ζῆλον σοφίας. Πλάτων δέ, κτῆσιν
    #         ἐπιστημῶν. Χρύσιππος δέ, ἐπιτήδευσιν λόγου ὀρθότητος. Καὶ αὐτῶν οὖν τῶν
    #         δοκούντων ἄκρων εἶναι ὁμοίως ὁριζομένων, ἡμεῖς ἀληθῆ φιλοσοφίαν ὁριζόμεθα
    #         τὴν μηδὲν τῶν ἡκόντων εἰς εὐσέβειαν καὶ ἀρετὴν παρορῶσαν"
    9150: """From: Isidore of Pelusium, monk
To: Ophelius the Grammarian
Date: ~410 AD
Context: Isidore surveys the ancient philosophers' definitions of philosophy and offers a Christian definition that supersedes them all.

The other philosophers defined philosophy as the art of arts and the science of sciences. Pythagoras defined it as zeal for wisdom. Plato, as acquisition of the sciences. Chrysippus, as the practice of correctness in speech. Even among those who are thought to be the supreme thinkers, the definitions come out roughly the same.

Our definition is different. We define true philosophy as that which neglects nothing that leads toward piety and virtue. Not art, not science, not verbal precision — though these have their place — but the life that never turns away from what matters most. Any other definition of philosophy is a philosophy about philosophy. Ours is philosophy put to use.""",

    # Letter 1644 — The truest rule of friendship — simple in intention, tongue, and life
    # Greek: "Ἐγὼ κανόνα φιλίας εὐθύτατον ἡγοῦμαι τὸν ἀπροφασίστως μὲν τοῖς ἀδελφοῖς
    #         συμπνέοντα, μήτε δὲ κολακείᾳ τὰς φιλίας προσαγόμενον, μῆτε λάθρα
    #         μεταχειριζόμενον τὰς ἔχθρας· ἁπλοῦν μὲν τυγχάνοντα τὴν γνώμην,
    #         ἁπλοῦν δὲ τὴν γλῶτταν, ἁπλούστερον δὲ ἔτι μᾶλλον τὸν βίον"
    9151: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore lays out what he considers the truest rule of friendship — simplicity of intention, speech, and life.

I consider the truest rule of friendship to be the one who agrees with his brothers without making excuses, who neither gains friendships through flattery nor conducts his enmities in secret — but who keeps his soul naked before everyone: simple in his intention, simple in his speech, and still more simple in his life.

Three kinds of simplicity are required — and each is a little harder than the last. Simple intention means no hidden agenda. Simple speech means saying what you actually think. Simple life means living consistently with both. The man who has all three has nothing to hide, and therefore nothing to manage. This is why such a man's friendships are real: they require no maintenance, because there is no performance to sustain.""",

    # Letter 1646 — To Zosimos the Presbyter — Why are you letting such a comedy be sung about you?
    # Greek: "Ὅτι οὐδὲν ἀκόλαστον, οὐδὲ μειρακιῶδες χρὴ διαπράττεσθαι,
    #         ἀλλὰ σώφρονα καὶ κεκολασμένην ἔχειν ἐν παντὶ τῷ βίῳ τὴν δίαιταν...
    #         Τί τοίνυν τοιαύτην κωμῳδίαν περιορᾷς κατὰ σαυτοῦ ᾀδομένην"
    9153: """From: Isidore of Pelusium, monk
To: Zosimos the Presbyter
Date: ~410 AD
Context: Isidore rebukes Zosimos for living in a way that has given others cause to mock him — neither temperate in youth nor reformed in old age.

That nothing licentious or childish should be practiced — that one should maintain a disciplined and restrained manner of life in all things — this is clear to everyone who has any share of mind and judgment. Why, then, do you allow such a comedy to be sung against you, with the wise observing that neither when you were young did you moderate your desires out of poverty, nor now that you are old do you out of any sense of disgrace?

The life that provides no material for mockery is the only life proof against mockery. You cannot silence the commentary without changing the behavior it describes. The playwright works with what you give him. Give him nothing, and there is no play.""",
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

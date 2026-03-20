#!/usr/bin/env python3
"""
Isidore of Pelusium quality pass — letters 1558–1583 (rows ~538–562)
Translated from the Greek in the latin_text column.
"""

import sqlite3

DB_PATH = "data/roman_letters.db"

TRANSLATIONS = {
    # Letter 1559 — To Theon the Bishop — On avenging personal wrongs while ignoring wrongs to God
    # Greek: "Ἴσθι, ὦ βέλειστε, ὡς χἀν τούτῳ πταίομεν, τὰ μὲν εἰς ἑαυτοὺς δρώμενα ἐκδιχοῦντες,
    #         τὰ δὲ εἰς ὃν Θεὸν παρορῶντες"
    9067: """From: Isidore of Pelusium, monk
To: Theon the Bishop
Date: ~410 AD
Context: Isidore points out a spiritual inconsistency — people rush to avenge wrongs done to themselves but ignore wrongs done to God.

Know this, best of men: we err even in this — avenging wrongs done against ourselves while overlooking wrongs done against God. When we are wronged, we seek justice; but when God is wronged, we look away. Every injury inflicted on us rouses us to action; nothing rouses us when it is He who is dishonored.

This is the reversal that should trouble us most. The injury done to an immortal and all-good God, which might at least be endured with patience by the one offended, causes no disturbance in us. But the wrong done to us — frail and sinful creatures that we are — stirs us to fire. Think about what this reveals about where our true loyalties lie, and correct it accordingly.""",

    # Letter 1563 — Two letters: to Eutonios the Deacon, then to the same again
    # Greek: "Εἰρήνην διώχετε καὶ τὸν ἁγιασμόν, οὗ χωρὶς οὐδεὶς ὄψεται τὸν Κύριον"
    # And: "Μάλιστα μὲν ἃ μὴ δεῖ ποιεῖν"
    9071: """From: Isidore of Pelusium, monk
To: Eutonios the Deacon
Date: ~410 AD
Context: Two letters to the same deacon — the first on pursuing peace and holiness, the second on the proper use of the tongue.

Pursue peace and holiness, without which no one will see the Lord. This is not optional equipment for the spiritual life — it is the road itself. Do not imagine you are progressing because you have avoided the grosser sins. The finer work of purification — the peace that makes you gentle toward others, the holiness that keeps your inner life clean — this is what the vision of God requires.

To the same: Above all, avoid doing what should not be done. But if you cannot achieve that fully, at least do not compound it by seeking to blame someone else or turn suspicion on another. Those who do this may think they are covering their tracks, but they are only deepening the wound. Cease from the wrong itself; do not add hypocrisy to it.""",

    # Letter 1565 — On the astonishment of all at the vanity of human life
    # Greek: "Πάντες χομιδῇ θαυμάζουσι καὶ ἐκπλήττονται, πῶς"
    # + "Ἄνθρωπός ἐστι πνεῦμα καὶ σκιά μόνον"
    9073: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore meditates on the vanity of human greatness and the universally surprising frailty of human life.

Everyone, without exception, is utterly astonished and struck dumb when they see how quickly the great collapse and the powerful are brought low. What seemed immovable — office, wealth, reputation, the whole edifice of human greatness — proves as fragile as a stage set, and the actor exits as suddenly as he entered.

The scriptures have the answer for this astonishment: "Man is but a breath and a shadow." There is nothing solid in what dazzles us. The comedy, as the poets also knew, is set in motion and then cut off — and the man who yesterday seemed like a god is not even a memory tomorrow. Let this thought work in you not as despair but as liberation: if none of these things is real, then losing them is not a loss, and you need not spend your life protecting what cannot be kept.""",

    # Letter 1566 — To Alypius the Scholastic — On virginity, marriage, and fornication
    # Greek: "Ἡ μὲν παρθενία θειοτάτη ἐστὶ καὶ ὑπερφυής, ὁ δὲ νόμιμος γάμος τίμιος,
    #         ἡ δὲ πορνεία παράνομος. Διὸ καὶ ἡ μὲν τῶν οὐρανῶν ἐστιν ἀξία, ὁ δὲ τῆς γῆς"
    9074: """From: Isidore of Pelusium, monk
To: Alypius the Scholastic
Date: ~410 AD
Context: Isidore lays out the Christian hierarchy of the three states of life, ranking them by their closeness to God.

Virginity is the most divine and supernatural of the three states; lawful marriage is honorable; fornication is lawless. Accordingly, virginity belongs to heaven; lawful marriage to the earth; and fornication does not belong anywhere that should be inhabited.

This is the teaching I have heard from those who have gone before us, and I find it persuasive. The man who commits fornication calls "my own" what is not his and never can be. The man who is rightly married honors the order God has placed in creation. The virgin, however, has not merely kept a rule — he or she has died with Christ and now lives a life the flesh cannot explain. That life, as someone has said, is already immortal here — not dying now, and to be vivified even further there.""",

    # Letter 1570 — To Martinianus, Zosimus, and Eustathios — On clinging to God's right hand in trials
    # Greek: "τῆς ἀηττήτου ἔχεσθαι δεξιᾶς· ἧς ὁ ἀντεχόμενος κρείττων δήπου τῶν πειρασμῶν
    #         ἀποφανθήσεται"
    9078: """From: Isidore of Pelusium, monk
To: Martinianus, Zosimus, and Eustathios
Date: ~410 AD
Context: Isidore urges three men — likely facing difficulties together — not to rely on their own strength but to cling to the invincible right hand of God.

Do not entrust the verdict of victory to the weak power of human beings. Instead, cling to the right hand of the One who cannot be defeated. Whoever holds on to that hand will surely prove stronger than all the temptations arrayed against him.

This is not advice to be passive. It is advice to fight with the right weapon. The man who enters a battle trusting in his own strength has already taken his greatest risk. The man who has learned that his strength alone is nothing — and who has therefore learned to rely entirely on Another — that man has found the one resource that does not run out. Do not despair over what you suffer; despair would mean you have forgotten whose right hand is still extended toward you.""",

    # Letter 1573 — On the worthlessness of wealth, rank, and cleverness without virtue
    # Greek: "Οὐδὲν, ὦ θαυμάσιε, ὁ πλοῦτος, κἂν πολὺς ᾖ καὶ πάντοθεν ἐπιῤῥέῃ·
    #         οὐδὲν τὸ ἀξίωμα, κἂν βασιλικόν... οὐδὲν ἡ σύνεσις, κἂν εὐγλωττίᾳ κοσμῆται"
    9081: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore argues that wealth, rank, and cleverness are each worthless in the absence of genuine virtue.

Nothing, O admirable friend, is wealth — not even if it be great and flooding in from every direction. Nothing is rank — not even if it be royal. Nothing is cleverness — not even when it is adorned with eloquence. These are shells. They look like something; they weigh nothing.

Why do I say this? Because each of these things can be taken away in an afternoon by fortune, by death, by time. The man who has nothing but wealth and loses it has lost everything. The man who has virtue and loses his wealth has lost nothing he cannot survive. This is why I press you toward the one acquisition that neither thieves steal, nor floods wash away, nor kings confiscate — the life of virtue, which belongs to the one who has formed it and cannot be stripped from him by anything in this world.""",

    # Letter 1574 — On bold but true criticism
    # Greek: "Τολμηρὸν μὲν ὄντως τὸ παρὰ σοῦ γραφέν, ἀληθὲς"
    9082: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore acknowledges that a correspondent has written something bold but true — and defends him against those who would silence honest speech.

What you have written is truly bold — and true. Those are the two qualities that make a word worth reading. The man who is bold but wrong merely makes noise. The man who is right but too timid to say it is useless. But the man who speaks truth boldly in the service of a genuine cause deserves to be heard.

Those who are trying to silence you are doing one of two things: either they want to shut down genuine frankness, which serves them, or they want to train shamelessness further into vice — which serves neither them nor anyone else. Do not be deterred. What can be said against a word that is both bold and true? Nothing, except that it is uncomfortable. And discomfort is exactly what it was meant to produce.""",

    # Letter 1575 — Two letters: on those who praise virtue in words but not deeds; then to Dioscoros and Timothy
    # Greek: "Οὐδεὶς μὲν ἀξιωθείη τῆς οὐρανίου πανηγύρεως... ἄλλα μὲν διὰ γλώσσης φέροντες,
    #         ἄλλα δὲ διὰ γνώμης ἔχοντες· οὓς οὐ χρὴ ζηλοῦν, ἀλλὰ κομιδῇ καταθρηνεῖν"
    9083: """From: Isidore of Pelusium, monk
To: An unnamed person; then to Dioscoros and Timothy
Date: ~410 AD
Context: Two letters — the first on hypocrisy in the praise of virtue; the second (to Dioscoros and Timothy) an invitation to change.

No one would be found worthy of the heavenly festival unless he were truly adorned with the marks of virtue. Many, as you rightly observe, honor virtue in their words but in their deeds commit acts worthy not of praise but of punishment. These men clearly carry one thing on their tongue and another in their heart. Do not envy them — weep for them. They have chosen the worst of all positions: they know enough to praise what is good, and yet do not do it. A man who does not know what virtue is can at least be pitied for his ignorance. But these men have no such excuse.

To Dioscoros and Timothy: You are invited to change. The invitation stands open. Those who accept it find that even past wretchedness can become useful — as a reminder of where they came from and a goad toward where they are going.""",

    # Letter 1577 — To Boethes the Monk — On why the suffering of the virtuous is not a scandal
    # Greek: "Μὴ θορυβείτω σε τὸ πολλοὺς τῶν φιλαρέτων μυρία ἐνταῦθα πάσχειν δεινά...
    #         καὶ οἱ τῶν ἐπὶ γῆς βασιλέων φίλοι, οὗτοι μάλιστα παρακινδυνεύουσιν ἐν πολέμοις"
    9085: """From: Isidore of Pelusium, monk
To: Boethes the Monk
Date: ~410 AD
Context: Isidore reassures a monk troubled by the fact that many virtuous people suffer greatly in this life.

Do not be shaken by the fact that many who love virtue suffer countless terrible things in this world. Instead, bring to mind the analogy that should settle it: the friends of earthly kings are precisely the ones who take the greatest risks in war, who bear wounds through which the trophies were erected, and who are sent on long journeys far from home. Their suffering is the proof of their closeness to the king, not of his neglect of them.

And if that still does not satisfy you, consider that there are some among the righteous who prosper even here. So if the suffering of the godly scandalized you because it seemed like abandonment — here is the counter-evidence. The fact that some righteous people flourish in this world shows that God is watching and can bless; the fact that others suffer shows that he is training them and will reward. Neither group is forgotten.""",

    # Letter 1578 — To Theodosius the Scholastic — On calling frankness shamelessness and vice versa
    # Greek: "Λίαν θαυμάζω τῶν καὶ τὰ πράγματα καὶ τὰ ὀνόματα συγχεόντων...
    #         τὴν μὲν παῤῥησίαν ἀναισχυντίαν καλεῖν, τὴν δὲ ἀναισχυντίαν παῤῥησίαν"
    9086: """From: Isidore of Pelusium, monk
To: Theodosius the Scholastic
Date: ~410 AD
Context: Isidore condemns the rhetorical maneuver of renaming vices as virtues and virtues as vices.

I am thoroughly astonished at those who confuse not only the things themselves but their very names — who have arrived at such a pinnacle of 'wisdom' that they call frankness shamelessness, and shamelessness frankness, erring in both directions at once. They do this for one of two reasons: either to silence genuine frankness, or to train shamelessness into an even greater vice. Either way, the goal is the suppression of truth.

They may claim not to understand the difference. But the difference is not subtle. Frankness speaks difficult truth for the benefit of the one who hears it; shamelessness speaks whatever serves the speaker, regardless of who is harmed. One is brave; the other is merely brazen. A man of any honesty can tell them apart — which is why those who benefit from the confusion work so hard to maintain it.""",

    # Letter 1579 — On "What God has joined, let no man separate" applied to the soul and its virtues
    # Greek: "Εἰ ἐπ᾽ ἀνδρὸς καὶ γυναικὸς δυοῖν ὄντοιν λέλεκται «Ἃ ὁ Θεὸς συνέζευξεν,
    #         ἄνθρωπος μὴ χωριζέτω»"
    9087: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore extends the saying "what God has joined, let no man separate" beyond marriage to the union of soul and body, and of virtue and the soul.

If, speaking of a man and a woman as two separate persons, it is said: "What God has joined, let no man put asunder" — how much more should we say this of the soul and the virtues which God has implanted in it, or of the soul and the body which God has joined together for the purposes of this life?

The one who seizes wickedness and uses it to violently separate the soul from its natural goodness is doing something more violent than any divorce. He is not merely breaking a bond between two people — he is tearing apart a creature from its own intended nature. Vice does not merely corrupt; it dismembers. What should have remained united under God's design is broken apart by the interference of human choice. This is why virtue is not a decoration added onto the soul — it is what the soul was made to be joined to. Losing it is a kind of death.""",

    # Letter 1580 — On how the advisor should rebuke — with frankness, without shame or fear
    # Greek: "Οἴμαι, ὅτι οὐ τύπτειν, οὐ λοιδορεῖν... ἀλλ᾽ ἐλέγχειν μόνον μετὰ παῤῥησίας,
    #         μήτε αἰδούμενον, μήτε φοβούμενον χρὴ τὸν παραινέτην"
    9088: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore explains how the one who reproves another should do it — with frankness only, not with violence, and without letting either shame or fear dilute the rebuke.

I believe that the one who reproves another should neither strike, nor revile, nor come to physical confrontation — but should rebuke only, with frankness, neither from a sense of embarrassment nor from fear. If you doubt this principle, I will read you what the divine scriptures say.

The man who rebukes from shame — hedging, softening, afraid to give offense — has not really rebuked at all. He has performed a rebuke, and the person he was speaking to knew it. And the man who rebukes in fury has substituted self-expression for correction, and the one being rebuked will notice. Only the rebuke that comes from genuine concern for the other, delivered plainly and without self-interest, has any chance of being received as the gift it is.""",

    # Letter 1581 — On the inequality of this life as a sign pointing to the equality of the next
    # Greek: "Ὥσπερ ἡ ἀνωμαλία ἡ ἐν τῷδε τῷ βίῳ... τῆς ἰσότητος εἶναι δοχεῖ διαφορά,
    #         οὕτω καὶ ἡ... ἐν τῷ μέλλοντι αἰῶνι ἀνισότης"
    9089: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore addresses someone troubled by the unevenness of this life and the apparent unevenness of the next — and argues that both point toward the same divine justice.

Just as the inequality we see in this present life — the righteous suffering, the wicked prospering — appears to be a deviation from equality, and thus cries out for a future settling of accounts, so too what seems like inequality in the age to come should be understood correctly: it is not arbitrary. The sorting that takes place at the judgment is precisely the restoration of true equality — each receiving exactly what corresponds to his life.

The problem is that we want equality now, on our own terms, before the full evidence is in. But the judge who rules prematurely does not produce justice — he produces the appearance of justice. The patient soul understands that the ledger is being kept, even if it is not yet visible, and waits for the day when both columns are finally shown.""",

    # Letter 1583 — Two letters: on the art of speech for saving souls; then to Symmachios on heavenly vs earthly change
    # Greek: "οὐδὲν γὰρ λαμπρότερον τοῦ ψυχὴν πεπλανημένην ἐπαναγαγεῖν εἰς τὴν τῆς ἀληθείας ὁδόν"
    # And: "Ὡς φής, εἰ τῶν μὲν καθ᾽ ἡμᾶς ἡ μεταβολὴ κυρία... τὰ δὲ οὐράνια μεταβολῆς τυγχάνει κρείττονα"
    9090: """From: Isidore of Pelusium, monk
To: An unnamed person; then to Symmachios
Date: ~410 AD
Context: Two letters — the first on the rhetorical virtues needed to bring a wandering soul back to truth; the second to Symmachios on why earthly things change but heavenly things do not.

Touching on the highest of all subjects — for there is nothing more glorious than leading a wandering soul back to the way of truth — the teacher must learn to speak at length where dwelling is profitable, and to hint only where hinting is the proper approach; to proceed by method where method is needed, and to speak plainly whatever is most fittingly said outright. Only by using all these virtues of speech together might one have any hope of drawing up a soul that has been submerged beneath its passions.

To Symmachios: You say — and you say rightly — that the changes of earthly things are the mark of their weakness, while heavenly things are superior to change. You are correct. The mutability of everything here is not a feature; it is a symptom. What is made of the stuff of time will change with time. What is made of the stuff of eternity does not. Seek therefore not what impresses you by its splendor — splendor that depends on conditions is already halfway to failure — but what cannot be taken away.""",
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

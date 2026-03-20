#!/usr/bin/env python3
"""
Isidore of Pelusium quality pass — letters 1519–1540 (rows ~500–519)
Translated from the Greek in the latin_text column.
Isidore's voice: direct, aphoristic, theologically precise, spiritually urgent.
"""

import sqlite3

DB_PATH = "data/roman_letters.db"

TRANSLATIONS = {
    # Letter 1519 — To Artemidorus
    # Greek: On the man who does everything in his power to persuade and fails
    # Paul: "each will carry his own load" (Gal 6:5)
    9027: """From: Isidore of Pelusium, monk
To: Artemidorus
Date: ~410 AD
Context: Isidore defends a man who tried his best to persuade others but failed.

The man who has done everything within his power to persuade, and yet failed, deserves to be admired as one who accomplished his purpose — he is that far from being worthy of blame. If this seems surprising to you, Paul will settle the question, saying: "Each will carry his own load." The one who makes the effort is not responsible for the one who refuses to listen. Virtue brings its own reward to the one who pursues it — and it does not wait on the stubbornness of those who refuse to receive it.""",

    # Letter 1520 — On bishops' bad example not being grounds for scandal
    # Greek: "If the piety of rulers has exposed the impiety of bishops..."
    9028: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Someone has written upset that rulers' piety exposes the impiety of certain bishops.

If, as you write, the piety of rulers in matters of God has exposed the impiety of bishops — if the extraordinary honor those rulers bestow has actually weakened the honored, and their great ambition has become an occasion for luxury and dissipation — nevertheless, do not let this become a stumbling block for you. Not all have been brought down by these failings. There are those who strive to live by the apostolic pattern. And if you would say that these are few, neither are you yourself your own judge. Be careful not to condemn the whole on account of the part, nor to use others' failures as an excuse for your own.""",

    # Letter 1521 — To a craftsman / To Hierax the Deacon
    # Greek: "Do not be ashamed of your work, but take pride in it"
    9029: """From: Isidore of Pelusium, monk
To: A craftsman, and then to Hierax the Deacon
Date: ~410 AD
Context: First, Isidore encourages a manual laborer; then turns to address Hierax the Deacon on the virtue of moderation.

Do not be ashamed of your work — take pride in it. You have taken up the most necessary and useful craft. It is those who chase pleasure who deserve to blush. Their fires are nearly extinguished by the very pursuit they live for.

To Hierax the Deacon: The man who keeps his soul composed even in the heart of winter is wise. Even at the peak of the cold season, a fire kept burning in a sheltered room preserves its warmth. So too the soul that does not give itself over to distraction will hold its heat even against the worst conditions.""",

    # Letter 1522 — On enduring the end of trials
    # Greek: "The temptation that has passed moves toward forgetfulness"
    9030: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore encourages someone bearing a trial that is nearly over.

Hold on — especially since the greater part has already been endured and its sting has been spent. A temptation that has already passed tends quickly toward forgetfulness. But the one still anticipated distresses as many times as it is anticipated. The one you have almost outlasted already fades; why let the shadow of what remains trouble you more than the thing itself?""",

    # Letter 1523 — To Narcissus the Sophist — On faith in God
    # Greek: "I don't know how unbelievers can make light of faith in God"
    9031: """From: Isidore of Pelusium, monk
To: Narcissus the Sophist
Date: ~410 AD
Context: Isidore commends faith in God as easy to understand, safe to hold, and impossible to defeat.

I cannot understand how unbelievers manage to make light of faith in God, whose knowledge is easy to acquire, whose possession is secure, and whose outcome is invincible. The knowledge: because God has disclosed himself plainly to all who seek him. The possession: because once truly taken hold of, nothing can wrest it away. The outcome: because it ends not in disappointment but in the very life of God.""",

    # Letter 1525 — To Proclus — On emulating the virtuous
    # Greek: "Those strongest in virtue rightly deserve to be called luminaries"
    9033: """From: Isidore of Pelusium, monk
To: Proclus
Date: ~410 AD
Context: On choosing the right models to imitate — the virtuous, not those who darken others.

Those who stand strongest in virtue, who surpass others in piety and sound judgment, and who excel their neighbors as the morning star surpasses the lesser stars — these men rightly deserve to be called luminaries. They have raised themselves to such a height not for their own benefit alone, but to give light to those walking in darkness and to lead them by the hand toward virtue's summit.

These are the men you should emulate. Not those who do everything in their power to darken even the eyes of those who observe them. The choice is plain: follow the ones who shine, not the ones who snuff out the light.""",

    # Letter 1526 — To Apocras the Sophist — On defining the wise and the good
    # Greek: "My definition of the wise: those adorned with rational virtues"
    9034: """From: Isidore of Pelusium, monk
To: Apocras the Sophist
Date: ~410 AD
Context: Isidore distinguishes the 'wise' from the 'good,' drawing on intellectual vs. practical virtue.

My definition of the wise — I am not laying down law, but offering my judgment — is those adorned with the virtues of the intellect: men like the ones who possessed both reason and the wisdom of knowledge. By 'the good' I mean those who pursue what some call the non-rational virtues: men incapable of saying anything philosophically profound, yet who educate those who observe them by the sheer quality of their way of life. Their silence is more useful than words emptied of action.

If anyone should possess both the rational and the so-called non-rational virtues together, I would call that man both good and wise.""",

    # Letter 1527 — To Epiphanius the Deacon — On the word 'pardon'
    # Greek: "Since you asked where the word for pardon gets its meaning..."
    9035: """From: Isidore of Pelusium, monk
To: Epiphanius the Deacon
Date: ~410 AD
Context: Isidore explains the etymology and meaning of the Greek word for 'pardon' (συγγνώμη).

Since you have asked where the word for pardon (συγγνώμη — literally, 'knowing together') gets its meaning when applied to forgiveness and release, here is what I think: because the man who has come to know himself — that is, the one who neither ignores his failures when he has failed, but keeps to the wise saying 'Know yourself,' nor, when he has done something right, becomes puffed up with arrogance if momentarily off his guard — such a man, learning his own nature and weakness and not imagining himself beyond human limits, fights against his own nature.

The man who truly 'knows together' — that is, who takes stock of himself honestly — is the one fitted to receive pardon, because he already holds within himself the beginning of change.""",

    # Letter 1528 — To Theophilus — On giving wealth away rather than leaving it to enemies
    # Greek: "What you will leave to enemies against your will, give willingly"
    9036: """From: Isidore of Pelusium, monk
To: Theophilus
Date: ~410 AD
Context: Isidore urges generosity now rather than having wealth seized by enemies later.

What you will often leave to your enemies against your will — give it willingly now. Turn necessity into generosity, so you will not weep over what cannot be undone. Send your possessions ahead into the ageless world, where they will be of use to you. The man who clutches his wealth here will find it claimed by enemies; the man who releases it in acts of mercy will find it waiting for him where neither moth nor thief can touch it.""",

    # Letter 1529 — On someone who set out on a long journey not for virtue's sake
    # Greek: "A short while ago, while it was still dawn..."
    9037: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore reports that learned friends are disturbed to hear that this person left on a long journey for self-interested rather than spiritual reasons.

A short while ago, when it was still dawn — night and daybreak were just blending — a close friend of mine came to me and reported that some men of learning, hearing that you had set out on a long journey not for virtue's sake, nor to improve yourself or anyone else, were troubled. They had expected better of you.

I write so that you will know this — not to wound you, but to give you a reason to turn around, if not in body then at least in intent. A journey undertaken for the wrong reasons can be redirected. What matters is not the road you started on, but the one you finish.""",

    # Letter 1530 — To Theodosius the Scholasticist — On the right use of a sharp tongue
    # Greek: "If you have a very sharp tongue, first bridle it"
    9038: """From: Isidore of Pelusium, monk
To: Theodosius the Scholasticist
Date: ~410 AD
Context: On the proper use of a gifted and sharp tongue — restraint first, then righteous advocacy.

If you have a very sharp tongue, try above all to bridle it and rein it in. But if you find that you cannot, then at least direct it to worthy ends: for the glory of God, to defend the wronged, to champion what is good, against the greed of those who harm others, against the ignorance of those who attribute the governance of all things to wicked spirits, against the madness of heretics. Use that edge where it cuts in a righteous direction.

A sword does not become blameworthy because it is sharp — only when it is drawn without reason or wielded for a bad cause.""",

    # Letter 1532 — To Apocras the Sophist — On detachment from earthly possessions
    # Greek: "Hold only to those possessions of which you will have need after departing this life"
    9040: """From: Isidore of Pelusium, monk
To: Apocras the Sophist
Date: ~410 AD
Context: Brief exhortation to detach from earthly goods and hold only what lasts.

Let us hold only to those possessions of which we will have need after departing this life. The rest, let us treat with contempt. The man who learns to live without what he cannot take with him has already arrived.""",

    # Letter 1533 — On modesty and acting within one's measure
    # Greek: "Since our nature has nothing inherently noble or extraordinary"
    9041: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore urges his reader to embrace moderation, since human nature carries nothing extraordinary of its own.

Since our nature has nothing inherently noble or extraordinary, let us lead it toward the moderate and the fitting — which are, in fact, its proper goods. Pride in what is not truly ours is the source of most of our destruction. The man who knows that he is neither more nor less than human is the one best equipped to become something more.""",

    # Letter 1534 — To Ophelius the Grammarian — "Do not give what is holy to dogs"
    # Greek: "What you ask about, I could tell you — but I cannot"
    9042: """From: Isidore of Pelusium, monk
To: Ophelius the Grammarian
Date: ~410 AD
Context: Isidore refuses to share spiritual teaching with someone still in a state of sin, citing Christ's command.

What you ask about, I could tell you — but I cannot, obedient as I am to the divine oracle that commands, 'Do not give what is holy to dogs.' But if you should rid yourself of the dogs' madness and attain human nobility — or rather, rise above merely human standards to the angelic — then come and ask again. You will not be turned away. The question is not whether the teaching is available, but whether the one asking is ready to receive it.""",

    # Letter 1535 — On spiritual self-deception and refusing to be healed
    # Greek: "Since we have no perception of our sins due to laziness and self-love"
    9043: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore reflects on how spiritual sickness renders itself invisible — we cannot see what we will not look at.

Since we ourselves have no perception of the terrible things we do, because of laziness and self-love — and since we do not provide that perception to others either, because they are in no better state than we are — we fancy ourselves healthy. And so we neither seek physicians nor want to be healed.

This is the most dangerous kind of disease: the kind that convinces its host that there is nothing wrong. The man who knows he is sick is already partway to a cure. The man who does not know has lost even the beginning.""",

    # Letter 1536 — To Paul — On doing good to friends, strangers, and enemies
    # Greek: "It is good to do good to friends; better to all in need; best of all to enemies"
    9044: """From: Isidore of Pelusium, monk
To: Paul
Date: ~410 AD
Context: Isidore expounds the ascending degrees of charity — good to friends, better to strangers, best to enemies.

It is good to do good to friends. It is better to do good to all who are in need. It is best of all to do good even to enemies. For even tax collectors and pagans accomplish the first — there is nothing distinctively Christian about benefiting those who benefit you. Doing good to all who ask is the mark of those who obey God's law. But loving enemies and praying for those who persecute you — that is the life worthy of heaven, the pattern of the One who makes his sun rise on the evil and the good alike.""",

    # Letter 1537 — To Theodosius the Scholasticist — On appearances and reality
    # Greek: "What seems elegant and just is not necessarily actually just"
    9045: """From: Isidore of Pelusium, monk
To: Theodosius the Scholasticist
Date: ~410 AD
Context: A sharp observation on the gap between appearance and reality in moral judgment.

What appears elegant is not necessarily elegant, and what appears just is not necessarily just. Things that have the look of wisdom without its substance deceive those who judge by the surface. This is why our Lord warned us to judge not by outward appearance but by righteous judgment — because reality and its imitation are only distinguishable to those willing to look beneath the surface.""",

    # Letter 1538 — On the superiority of unsullied victory over recovery after defeat
    # Greek: "Far better, most wise one, is a victory untainted by defeat"
    9046: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore argues that a clean victory is far better than recovering from a fall, however admirable recovery may be.

Far better, most wise one, is a victory untainted by any defeat than to conquer after a fall. Both may end in the same place, but they have very different dignity. The man who was never brought down has never compromised his ground. The man who rises after a fall has done something admirable — but he must first have fallen. Keep your armor on and you will not need to be rescued.""",

    # Letter 1539 — On the resurrection of the soul — extraordinarily clear Greek text
    # Greek: "The resurrection of the soul deadened by sin takes place here"
    9047: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore explains that the soul has its own resurrection in this life — the return from sin to righteousness — and that the body's resurrection awaits the next.

The resurrection of the soul deadened by sin happens here, in this life, when it is reformed into life by acts of righteousness. By 'death' of the soul we should understand wickedness — not annihilation. This is why, of the prodigal son, who was still alive in body, it was said: "He was dead and came back to life." And to the one deadened by sin and buried in it, the word came: "Awake, O sleeper, and rise from the dead, and Christ will give you light."

For to the one who has shaken off the death of sin through repentance, the true light will rise. As for the resurrection of the body — that will take place there, equally for all on account of immortality, though not equally in terms of what that immortality looks like. For the one who has lived rightly, immortality will be light and glory; for the one who has not, it will be something quite different.""",
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

    # Verify
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

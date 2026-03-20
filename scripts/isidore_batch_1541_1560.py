#!/usr/bin/env python3
"""
Isidore of Pelusium quality pass — letters 1541–1558 (rows ~520–537)
Translated from the Greek in the latin_text column.
"""

import sqlite3

DB_PATH = "data/roman_letters.db"

TRANSLATIONS = {
    # Letter 1541 — To Dositheus, Ammonius and Dionysius — On an uneducated Goth
    # Greek: "Gothus the uneducated who received letters of education..."
    9049: """From: Isidore of Pelusium, monk
To: Dositheus, Ammonius, and Dionysius
Date: ~410 AD
Context: Isidore comments on a Goth who received some education but lost it.

Whoever receives the advice and counsel that breathes good and usefulness will profit from it — provided he approaches it as one who is eager to learn and not as one who seeks only flattery. Instruction can only go as far as the disposition of the one receiving it.

The uneducated Goth received letters — that is what we call him, since no better word seems proper — how he fared with them, I do not know exactly. But I suspect he held them for show rather than for use. He who takes up learning only to appear learned has missed the whole point of the exercise.""",

    # Letter 1542 — On Sparta's discipline and the corruption of luxury
    # Greek: "I greatly admire ancient Sparta..."
    9050: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore holds up ancient Sparta as a model of discipline, contrasting it with the corruption of luxury in his own day.

I greatly admire ancient Sparta — a city adorned with honor, whose mothers forbade ornament so that the men they raised would shine by their deeds and not by their dress. They understood that the true beauty of a city is not its gilded columns but the character of its citizens.

What comes from lawless wealth is not honor but its image — a glittering shell over an empty center. True nobility does not look like nobility; it is. And true virtue does not need advertisement; it is recognized by those who have eyes to see it. I am not surprised that a city which prized frugality above all produced men that the whole world could not break.""",

    # Letter 1543 — On the dangerous love of eloquence for its own sake
    # Greek: "A terrible love of words has flooded the souls of people in this time"
    9051: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore laments that people love words that entertain rather than words that form the soul.

A terrible love of words has flooded the souls of people in this time — words, I say, not of the kind that bring wisdom and correction, but of the kind that entertain those who hear them. The result is that the crowd flocks to the performer and ignores the physician.

This is an old danger in a new form. Entertainment is not education. The man who leaves a lecture pleased but unchanged has been flattered, not taught. And the preacher who measures his success by applause has already chosen the wrong measure.""",

    # Letter 1545 — On the road to piety; then on 'rash' vs. 'involuntary'
    # Greek: two letters combined
    9053: """From: Isidore of Pelusium, monk
To: Cassianus and Absonius
Date: ~410 AD
Context: Two short letters — one on the road to piety, one on the distinction between rashness and involuntary action.

The road that seems finest to me is the one that leads toward piety and ends in open, spacious freedom. The path of virtue is not narrow forever — it only appears so at the beginning. Those who persist find that it widens into something they could not have imagined from the entrance.

To Absonius: 'Rash' and 'involuntary' are not the same thing. The first refers to acting without reflection; the second to acting without will. The first has to do with doing; the second with suffering. A rash act is one that lacks deliberation; an involuntary act is one that lacks consent. Let those who confuse the two be careful: to excuse rashness as involuntary is to deny responsibility for what one chose not to think about.""",

    # Letter 1546 — To an unnamed person — Brothers quarreling while their father pretends not to know
    # Greek: "Your eldest and youngest children are at odds..."
    9054: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Two short letters — one urging a father to stop pretending not to notice that his sons are quarreling.

Some say that your eldest and youngest children are at odds, and that you know this but pretend not to. Put down the deliberate ignorance quickly and try to reconcile them before the breach widens. A wound that could have been stitched shut in a day becomes a scar that lasts a lifetime if left unattended.

A father who sees a quarrel between his children and looks away is not keeping the peace — he is merely postponing it. The one who intervenes early, even if they do not thank him immediately, will be thanked in the end.""",

    # Letter 1547 — Congratulating someone on their change of life
    # Greek: "I was extraordinarily glad to hear of your excellent change of heart"
    9055: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore expresses joy at hearing of someone's genuine conversion and change of life.

I was extraordinarily glad to hear of your excellent change of heart. And I believe you will quickly shed the disgrace that previously attached itself to you from your wickedness. You will take up the adornment of virtue and earn undying fame — proclaimed here among all who know you, and in the world to come before the One who sees everything.

This is what true change looks like: not only leaving what was wrong behind, but replacing it with something real. A man who ceases from evil has made a start. A man who takes up virtue has arrived.""",

    # Letter 1549 — On refusing to judge a man who has not yet been tried
    # Greek: "I will neither condemn nor judge a man of whom I was neither a witness nor a judge"
    9057: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore refuses to render a judgment on a man he has not personally observed or heard — he will wait for the formal outcome.

I will neither condemn nor acquit a man of whom I was neither a witness nor a judge. But if he is brought to trial and found guilty, then the verdict against him will be pronounced at that time. It is not my place to pronounce ahead of the process.

This is not indifference — it is justice. The mouth that pronounces guilt before the hearing has closed is not serving truth; it is serving rumor. I would rather be thought slow than be found unjust.""",

    # Letter 1550 — To Zosimus the Presbyter — On wounding the poor further by withholding charity
    # Greek: "If you are unwilling to heal anything, and actually deepen the wounds of the poor"
    9058: """From: Isidore of Pelusium, monk
To: Zosimus the Presbyter
Date: ~410 AD
Context: Isidore rebukes a presbyter who has not only refused to help the poor but made their condition worse.

If you are unwilling to heal anything, and actually deepen the wounds of the poor — what more terrible battle are you creating for those already fighting against the hard-to-cure and hard-to-fight beast of poverty? The alms that the merciful provide for their sustenance, you remove.

I say this plainly: the priest who enriches himself while the poor in his care go hungry has not only failed in his duty — he has actively done harm. The one who can see a wound and does not close it is not neutral; he is complicit. What excuse will you give when asked to account for those you were placed there to tend?""",

    # Letter 1551 — To Theodosius the Presbyter — Recommending a devout man as a guest
    # Greek: "A man devoted above all to holy religion has come there"
    9059: """From: Isidore of Pelusium, monk
To: Theodosius the Presbyter
Date: ~410 AD
Context: Isidore introduces a devout pilgrim and asks Theodosius to serve as his guide to the virtuous people in the area.

A man deeply devoted to the most holy religion, and who places great value on meeting others who share his way of life, has arrived in your area. Be a good guide to him. Let him see you and the other images of virtue among you, so that he may satisfy the longing that drove him to make the journey.

There are men who travel great distances not for trade or politics but for a sight of genuine holiness. Receive him as such a man deserves to be received.""",

    # Letter 1553 — On the prosperity of the wicked as evidence for future judgment
    # Greek: "The vile Zosimus dares to serve as priest — but let this strengthen your faith in judgment"
    9061: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore addresses someone scandalized that a corrupt man named Zosimus dares to serve as priest, arguing that the apparent injustice of the world is actually evidence for the coming judgment.

The vile and God-hated Zosimus dares to serve as priest — as you write with shock. But let this very thing strengthen your faith that judgment certainly awaits. For if everyone in this life received what they deserved — the righteous their rewards and the wicked their punishments — the whole idea of a judgment would be superfluous.

But since many wicked men prosper and many virtuous men are passed over, the very thing that causes distress should be what resolves the distress: precisely because this life does not sort things justly, there must be a settling of accounts. God would not be just if he allowed these things to stand permanently. That they are allowed temporarily is an invitation to faith.""",

    # Letter 1554 — On the limits of the advisor's role
    # Greek: "It is the advisor's task to say what is best; the one advised must be persuaded"
    9062: """From: Isidore of Pelusium, monk
To: An unnamed person
Date: ~410 AD
Context: Isidore defends himself against criticism that his counsel failed, arguing that the advisor's responsibility ends with speaking clearly.

If I claimed to possess words capable of eliminating every kind of wickedness, I would rightly be accused of arrogance. But what I know above all else is this: it belongs to the advisor to say what is best; it belongs to the one being advised to be persuaded. One is master of speaking; the other, of acting.

Why, then, if you are unwilling to accept the advice, do you blame the one who fulfilled his part by speaking well? And if you will not accept even this, you will have to extend your criticism to the inscrutable wisdom of God himself — which could not persuade the apostate Jews, and could not persuade the traitor. So great is the respect God pays to human freedom that he will not compel even those he died for.""",

    # Letter 1557 — To Macarius the Deacon — On the love of money
    # Greek: "It is easier not to be caught than to recover yourself once caught"
    9065: """From: Isidore of Pelusium, monk
To: Macarius the Deacon
Date: ~410 AD
Context: Isidore urges his reader to do everything to avoid falling into the love of money, since recovery is so much harder than prevention.

Since it is difficult — hard, that is — for one who has fallen into the love of money to pull back (for such a person becomes hard to cure, if not incurable), one must do everything to avoid being caught by this terrible thing in the first place. It is far easier not to be caught than to recover yourself once you have been.

The man who has never been enslaved by money does not understand how strong its chains are. The man who has been does. This is why it is wisdom, not timidity, to flee the beginning of temptation rather than to test one's strength against a current that has already swept stronger men away.""",
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

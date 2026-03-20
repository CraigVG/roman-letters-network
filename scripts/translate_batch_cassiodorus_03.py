#!/usr/bin/env python3
"""Batch translate Cassiodorus letters (IDs 2892, 2917, 2601, 2640, 2788, 2813, 2860)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(2892, """From: Cassiodorus, on behalf of King Athalaric
To: Pope John
Date: ~522 AD
Context: A major decree against simony (the buying and selling of church offices), prompted by reports that sacred vessels were being sold during papal elections. Athalaric reinforces earlier Senate legislation on the matter.

If ancient emperors strove to devise laws so that their subjects might enjoy delightful peace, it is far nobler to decree measures that accord with sacred rules. Let the damaging profits of our age be banished. The only thing we can truly call gain is what divine judgment does not punish.

Recently, a defender of the Roman Church came to us with a tearful complaint: when a bishop was being chosen for the apostolic see, certain men exploited the crisis of the moment through wicked scheming, burdening the poor with extorted promises so heavily that -- unspeakable to say -- even sacred vessels appeared to have been put up for public sale. What was so cruel in its commission is equally glorious to cut away with an act of piety.

Therefore, let your holiness know that we have decreed the following by the present ruling -- which we also wish to apply to all patriarchal and metropolitan churches: from the time of the most holy Pope Boniface [Boniface I, pope 418-422], when the conscript fathers of the Senate, mindful of their nobility, passed decrees prohibiting such corrupt payments, anyone who is shown to have promised anything -- whether personally or through any intermediary -- in the obtaining of a bishopric, that abominable contract shall be voided with full force.

If anyone is found to have been involved in this crime, we leave them no legal standing. Indeed, if they believe they can reclaim what was promised or refuse to return what was received, they shall immediately be held guilty of sacrilege and compelled to restore what they took by order of the competent judge. The most just laws open the way for the virtuous just as they close it for the corrupt.

Furthermore, we command that everything decreed in that Senate resolution be enforced in full against those who have entangled themselves -- in any manner or through any intermediary -- in these criminal transactions.

And because all things must be governed with moderation, and nothing excessive can be called just: when a dispute arises over the consecration of the apostolic pontiff and the matter is brought to our palace, we wish the following rules to apply..."""),

(2917, """From: Cassiodorus, on behalf of King Theodahad
To: Emperor Justinian
Date: ~522 AD
Context: A brief diplomatic letter from the Gothic king to the Eastern Roman emperor, commending an envoy traveling on behalf of the church at Ravenna.

Our desire is fulfilled whenever we have the opportunity to send a salutary letter to your piety, because the man who speaks with you in sincere spirit is always filled with joyful happiness. And so, greeting your clemency with fitting honor, I commend to you the bearer of this letter, who comes on business of the church of Ravenna with a request that I trust will be most welcome to you. The cause he brings is one where bestowing a favor seems to earn a reward -- the kind of reward that those who desire your serenity to flourish always hope you will gain. For there is no doubt that those who grant just requests receive better things in return."""),

(2601, """From: Cassiodorus, on behalf of King Theoderic
To: The Roman Senate
Date: ~522 AD
Context: Theoderic announces the promotion of Venantius and delivers an extraordinary tribute to his father, the patrician Liberius -- praising his loyalty to the defeated King Odoacer and his seamless transfer of that loyalty to Theoderic.

It is our policy, conscript fathers, to grant rewards to upright character and to kindle men of good promise toward still better conduct by the fruit of our generosity. The examples set by rewards nourish virtue, and no one fails to strive for the highest standards of character when what conscience approves does not go unrewarded.

This is why we have elevated the distinguished Venantius -- shining by his own merits as well as his father's -- to the dignity of the honorary Count of the Domestics, so that the innate splendor of his birth might be made more brilliant by the bestowal of honors. You remember, conscript fathers, the patrician Liberius [one of the most remarkable figures of the transition from Roman to Gothic rule in Italy] -- how praiseworthy he was even in our adversity. He served Odoacer [the barbarian king who deposed the last Western Roman emperor in 476] with the most scrupulous loyalty, yet afterward proved himself most worthy of our affection -- against whom he had appeared to act as an enemy. He did not cross over to us in the contemptible manner of a deserter, nor did he feign hatred for his own master in order to win another's favor. He awaited the divine judgment with his integrity intact and did not allow himself to seek a new king until his first lord had fallen.

The result was that we gladly gave him a reward, because he had faithfully served our enemy. By an ironic twist of fortune, he became all the more acceptable to us the more he had been recognized as devoted to the other side. Even when his master's cause was nearly lost, no threats could make him waver. He stood immovable through the ruin of his prince. The novelty of the situation could not unsettle a man whom even the ferocity of barbarian peoples had respected. He wisely shared his master's fate, so that by steadfastly enduring the divine judgment, he would find all the more favor with men.

We tested the man's loyalty: he came over to our authority with a heavy heart -- one who, when his side was defeated, changed his allegiance but never engineered the defeat. As soon as we entrusted him with the dignity of the Praetorian Prefecture, he managed everything assigned to him with such integrity that one would marvel at how simply devoted was a man known to have been so shrewdly opposed. With tireless effort -- the rarest kind of virtue -- he managed public affairs under the guise of universal goodwill..."""),

(2640, """From: Cassiodorus, on behalf of King Theoderic
To: Gemellus, Vir Sublimis
Date: ~522 AD
Context: Theoderic appoints Gemellus as vicar of the prefects in Gaul, ordering him to govern the recently conquered Gallic provinces with justice and sensitivity.

A judgment backed by precedent is solid, and there is no room for doubt where proven experience speaks in one's favor. We have tested your effectiveness through various stages of active service, and you have earned equal favor in each, consistently approved in diverse assignments.

This is why our authority now sends you to the provinces of Gaul -- subject to us by God's help -- as vicar of the prefects [the deputy of the Praetorian Prefect, with jurisdiction over the Gallic provinces]. Consider what kind of opinion we must hold of you, since you are being sent to govern the very people we believe were especially won over to our glory. A prince's glory is precious, and he must naturally be more attentive to the lands from which he feels his triumphs have grown.

Carry out your orders, then, if you wish our confidence in you to grow. Do not court disorder; shun greed, so that the war-weary province may receive in you the kind of judge it knows a Roman prince has sent. A people crushed by calamity longs for outstanding men. Make them glad they were conquered. Let them experience nothing like what they suffered when they were seeking Rome's protection. Let all the sadness of their disaster fade; let their clouded faces clear at last. Now is the time for them to rejoice, since they have obtained what they wished for."""),

(2788, """From: Cassiodorus, on behalf of the King
To: A newly appointed Notary (formula)
Date: ~522 AD
Context: A template for appointing a royal notary, describing the essential qualities of discretion and loyalty required of those who handle the king's secrets.

There is no doubt that the prince's inner circle honors those who serve in it, since essential matters are entrusted only to those who are firmly established in loyalty. Everything we do is public in the end, but much of it must not be known until it has been accomplished with God's help. And the more eagerly people desire to learn these things, the more carefully they must be concealed.

A king's counsel should be known only to the most serious men. Notaries should imitate the cabinets that hold official records: they should speak only when information is sought from them, and the rest of the time they should pretend not to know what they know. For under the probing gaze of the curious, even a facial expression can betray what the tongue keeps silent. Let innocence be present -- it commends everything -- because royal words deserve to be deposited in a calm mind.

Since our watchful concern for good character has identified you as a man of proven morals, we appoint you our notary from the current tax year, so that in the regular course of service you may happily rise to the summit of the primiceriatus [the senior rank of the notarial corps]. This is an honor that makes a man a senator -- one to whom the hall of the fathers is justly opened. For the man who labors in our service through constant night watches rightly deserves to enter the Hall of Liberty as well.

There is yet another reward for completed service: if a former primicerius attains the rank of illustris -- whether active or honorary -- he takes precedence over all those who hold the same rank by mere codicil [a letter of appointment without actual office]. From this it is clear that the reward of the primiceriatus is meant to ensure that within the same title, the dignity earned by service outweighs that acquired by other means. You should therefore be encouraged to labor, knowing that such a prize awaits you -- the kind that even the most distinguished men are glad to have found."""),

(2813, """From: Cassiodorus, on behalf of the King
To: The islands of Curitana and Celsina (appointment of a count/judge)
Date: ~522 AD
Context: A formula for appointing a judge over two small Adriatic islands -- likely Veglia (Krk) and Cherso (Cres) off the Dalmatian coast.

It is generally agreed that things go well wherever a person in authority is present. Without a leader, everything falls into confusion, and when each person thinks he can live according to his own will, the rule of discipline is abandoned. Following ancient custom, therefore, our authority grants you jurisdiction over the islands of Curitana and Celsina [two islands in the northern Adriatic, modern Krk and Cres in Croatia] for the current tax year.

It is only right that someone should travel to the settlements of people who are cut off from the rest of human society, to arrange their affairs by sound judgment -- lest their remoteness become an excuse for injustice, with those far away remaining ignorant of public business. You now have, people of those islands, a man who can both hear and settle disputes that arise among you. And if anything is decreed by our authority, carry it out with his guidance, since the opportunity for error is removed when you know clearly whom you must obey. We trust he will devote himself so thoroughly to good deeds that he may earn the increase of our favor. For he must necessarily receive a reward from us if he arranges what is beneficial for you."""),

(2860, """From: Cassiodorus, on behalf of King Athalaric
To: Opilio, Count of the Sacred Largesses
Date: ~522 AD
Context: Athalaric appoints Opilio to one of the highest financial offices in the kingdom, praising his distinguished family's long record of service and recalling how Opilio and his brother served together in a touching display of fraternal devotion.

It is customary for those approaching court offices to be weighed by long examination, lest the royal judgment seem to approve anything doubtful -- since the glory of a reign lies in selecting distinguished judges. But the fortunate record of advancement in your family is so frequent, and the wisdom displayed by so many of its members so well attested, that even if someone chose you on the spur of the moment, the decision would not seem uncertain. A blessed lineage preserves family likeness, and those who cannot find examples of wrongdoing in their own kin feel ashamed to commit it.

This is why it is better recognized as having chosen a nobleman than as having made a lucky pick -- because the nobleman, instructed by the deeds of his forebears, guards his own conduct, while the self-made man has no example except what he himself creates. We therefore entrust to you with confidence what we are glad to have entrusted so often to your family. Your father held these very fasces [the symbols of office]; your brother likewise shone with the same distinction. The office itself has, in a manner of speaking, set up its household shrine in your home, and a public honor has become a family tradition.

You learned the routine of this office under your brother's distinguished tenure: bound to him by mutual affection, you shared his labors as a partner and his deliberations as a brother, judging what he had received to belong more to you than to him. He leaned on this support all the more happily, sometimes deliberately overlooking details in his confidence in you, because he saw that everything was being accomplished through your efforts.

What a sweet bond between brothers -- an ancient harmony in modern times! It is right to entrust judgment to men who are naturally inclined to preserve good character. Even when the pleasures of country retreat and provincial leisure might have tempted you, crowds of litigants and the anxious hopes of the wronged came running to you. You took on the office of a good judge among them, as if by some premonition of the future -- performing through the assumption of merit what you could have received from us by appointment.

We also remember with what devotion you served us at the beginning of our reign, when the loyalty of the faithful was most sorely needed. For after the passing of our grandfather of divine memory, when the anxious hopes of the people trembled and hearts were flooded with uncertainty about the still-undecided heir of so great a kingdom..."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Cassiodorus translations (batch 03)")

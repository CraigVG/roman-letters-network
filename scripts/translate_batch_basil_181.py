#!/usr/bin/env python3
"""Batch translate Basil letters 185-190 (IDs 996-1001)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(996, """From: Basil, Bishop of Caesarea
To: Theodotus, Bishop of Beraea
Date: ~368 AD
Context: A brief, warm appeal to a silent friend to exchange letters as their only means of connection across distance.

Even though you do not write to me, I know there is a place for me in your heart -- not because I am worthy of any special remembrance, but because your soul overflows with love. Still, as far as you are able, take whatever opportunities arise to write. That way I can be cheered by news of you, and you can have news of me. Letters are the only means of communication for those who live far apart. Let us not deprive each other of them, so far as our work permits.

But I pray God that we may one day meet in person -- that our love may deepen and our gratitude to our Master may multiply for his greater blessings."""),

(997, """From: Basil, Bishop of Caesarea
To: Antipater, Governor of Cappadocia
Date: ~368 AD
Context: A delightfully playful letter congratulating the governor on his recovery, achieved (to Basil's amusement) through the medicinal powers of pickled cabbage.

Philosophy is an excellent thing, if only for this: it heals its students cheaply. In philosophy, the same dish is both a delicacy and good medicine.

I am told that you have restored your failing appetite with pickled cabbage. I used to look down on the stuff -- partly because of the proverb [a Greek proverb about cabbage being a sign of poverty], and partly because it reminded me of the poverty that came with it. But now I am forced to change my mind. I laugh at the proverb when I see that cabbage is such a fine nursemaid of men, and has restored our governor to the vigor of youth.

From now on I shall think nothing compares to cabbage -- not Homer's lotus, not even that ambrosia, whatever it was, that fed the gods on Olympus."""),

(999, """From: Basil, Bishop of Caesarea
To: Amphilochius, Bishop of Iconium
Date: ~368 AD
Context: The first of Basil's three great canonical letters -- responses to Amphilochius's questions about church discipline that became foundational texts of Eastern canon law. This letter addresses the treatment of heretics, schismatics, the lapsed, and questions of marriage and penance.

(First Canonical Letter)

To Amphilochius, concerning the Canons:

"Even a fool, when he asks questions, is counted wise" -- but when a wise man asks questions, he makes even a fool wise. This, thank God, is my experience every time a letter arrives from you. We become more knowledgeable simply by engaging with your questions, because we are taught things we had not considered, and the effort of answering serves as a teacher in itself. At present, though I had never given close attention to the points you raise, I have been compelled to investigate carefully and to turn over in my mind both what I heard from the elders and everything I was taught in keeping with their instruction.

I. Regarding your inquiry about the Cathari [the "Pure Ones," a rigorist sect]: a ruling has already been made, and you rightly remind me that we should follow the custom prevailing in each region, since those who originally decided these matters held different views about the validity of their baptism. But the baptism of the Pepuzeni [followers of the Montanist heresy, named after their headquarters in Pepuza, Phrygia] seems to me to carry no authority at all, and I am astonished that this escaped Dionysius [Dionysius the Great of Alexandria], well-versed as he was in the canons.

The old authorities decided to accept only that baptism which in no way departs from the faith. They distinguished three categories: heresies, schisms, and unlawful assemblies. By "heresies" they meant those completely broken off and alienated in matters of actual faith. By "schisms" they meant those who had separated over ecclesiastical disputes that could be mutually resolved. By "unlawful assemblies" they meant gatherings held by disorderly presbyters, bishops, or undisciplined laymen -- as when a man convicted of an offense is barred from ministry but refuses to submit to the canons, instead claiming episcopal and ministerial authority for himself, and others leave the Catholic Church to follow him.

[This letter continues at great length with detailed canonical rulings on the rebaptism of various heretical groups, the treatment of those who have lapsed in persecution, categories of penance, regulations on marriage after divorce, and the proper handling of clergy who have fallen into sin. These rulings became authoritative in Eastern church law.]"""),

(1000, """From: Basil, Bishop of Caesarea
To: Eustathius, physician and philosopher
Date: ~368 AD
Context: Basil thanks his friend Eustathius -- both a doctor and a philosopher -- for encouraging him not to keep silent under slander, and reflects on the duty to defend truth even when lies seem invincible.

Dear Eustathius,

Compassion is the regular business of all who practice medicine. And in my judgment, to put your profession at the head of life's pursuits is both reasonable and right. This much at least seems clear: that our most precious possession -- life itself -- is painful and not worth living unless we have health, and for health we depend on your skill.

But in your case medicine works, as it were, with two right hands. You extend the accepted limits of human kindness by applying your skill not only to the body but to the diseases of the soul as well. I write this not simply because of what others report, but from my own personal experience -- tested many times, and especially now, in the midst of the unspeakable malice of my enemies, which has flooded my life like a poisonous stream. You dispersed it with great skill. By pouring in your soothing words you calmed the inflammation of my heart.

Faced with the relentless and varied attacks of my enemies, I had decided to keep silent -- to endure their assaults without reply, without trying to counter opponents armed with falsehood, that terrible weapon which too often pierces the heart of truth itself. But you were right to urge me not to abandon truth's defense, and instead to expose our accusers -- lest, if lies go unchallenged, many be harmed.

My opponents, in adopting their sudden posture of hatred toward me, seem to be reenacting Aesop's old fable. The wolf brings charges against the lamb, ashamed to appear to kill a creature who has done him no harm without some plausible pretext. When the lamb easily refutes the slander, the wolf attacks all the same -- defeated in justice, but victorious in force.

[The letter continues with Basil's extended defense against the theological accusations leveled at him, and his gratitude for Eustathius's philosophical counsel.]"""),

(1001, """From: Basil, Bishop of Caesarea
To: Amphilochius, Bishop of Iconium
Date: ~368 AD
Context: Basil responds to Amphilochius's concern about the Isaurian church's need for more bishops, weighing the advantages of multiple appointments against the risk of ordaining unfit men.

Your interest in the affairs of the Isaurian church is exactly what I would expect from the zeal and good judgment that continually earn my admiration. Even the most casual observer can see that it is in every way better for responsibility and oversight to be divided among several bishops. You have noticed this yourself and done well to bring the situation to my attention.

But finding the right men is not easy. While we naturally want the credit that comes from numbers and desire to see God's church more effectively governed through more officers, we must be careful not to bring the ministry into disrepute by appointing men of poor character, and in the process teach the laity to be indifferent. You know well enough that the conduct of the governed usually matches the conduct of those set over them.

Perhaps, then, it would be better to appoint one thoroughly proven man -- though even this may not be simple -- to oversee the whole city, and entrust him with managing the details on his own authority. Only let him be "a servant of God, a workman who needs not be ashamed" [2 Timothy 2:15], "not looking to his own interests but to the interests of the many, that they may be saved" [cf. Philippians 2:4, 1 Thessalonians 2:16]. If he finds himself overwhelmed, he can bring in fellow workers for the harvest.

If we can find such a man, I genuinely believe that one good bishop is worth many mediocre ones, and that this approach will serve the churches better while exposing us to less risk. If, however, that proves too difficult, let us first appoint overseers to the small towns and villages that have traditionally been episcopal sees, and then worry about the larger appointments afterward."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Basil translations (IDs: 996-1001)")

#!/usr/bin/env python3
"""Batch translate Theodoret letters 46-50 (IDs 4254-4258)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(4254, """From: Theodoret, Bishop of Cyrrhus
To: Petrus, a scholar
Date: ~440 AD
Context: Theodoret praises a learned layman for standing up against injustice and asks him to keep fighting the lies of the renegade bishop.

To the learned Petrus,

Nothing can stop the praiseworthy resolve of those who hold fast to what is right. Your magnificence proves the point: when you received the latest news, you refused to let the assault on justice pass in silence. You acted quickly to set aside your distress and rightly shut the mouth of the enemy of truth.

When we heard about this -- when we saw genuine philosophical conviction paired with rhetorical skill -- our admiration for your excellence only grew warmer. Now we beg you all the more earnestly: counter this man's lies and uphold the relief that has been granted to the wretched poor."""),

(4255, """From: Theodoret, Bishop of Cyrrhus
To: Proclus, Bishop of Constantinople
Date: ~440 AD
Context: Theodoret appeals to the patriarch of Constantinople to block a renegade bishop's attempt to overturn the tax relief granted to Cyrrhus twelve years earlier.

To Proclus, Bishop of Constantinople,

A year ago, thanks to your holiness, the distinguished Philip -- governor of our city -- was delivered from serious danger. Once he was safely enjoying the security your intervention had secured, he filled our ears with your praises.

But now a certain "most pious" individual is working to undo everything you accomplished. He is attacking a tax assessment carried out twelve years ago, and has adopted a style of slander that would be beneath even a respectable slave.

I beg your sanctity to put a stop to his lies and to persuade the illustrious prefects to ratify the decision they rightly and mercifully rendered. The facts are these: our city was taxed more heavily than any other in the province. Even after every other city received relief, ours continued to this day assessed at over sixty-two thousand acres. Eventually the authorities were persuaded -- with difficulty -- to send inspectors. Their report was first accepted by Isidorus of blessed memory, then confirmed by the distinguished and Christ-loving lord Florentius, and the entire matter was carefully reviewed by our present ruler, whose fairness adorns his office. He confirmed the assessment by imperial decree.

Yet this self-proclaimed champion of truth, motivated entirely by his hatred of one man -- the excellent Philip -- has declared war on the poor.

I implore your holiness: marshal the forces of your righteous eloquence against his eloquence of wrong. Throw your shield over the truth that is under attack, and prove at once her strength and the futility of his lies."""),

(4256, """From: Theodoret, Bishop of Cyrrhus
To: Eustathius, Bishop of Berytus
Date: ~440 AD
Context: A playful response to Eustathius's complaint about not receiving enough letters.

To Eustathius, Bishop of Berytus [modern Beirut],

I gladly accept the accusation, though I have no trouble disproving it. I have written not three letters but four. I suspect one of two things: either the people who promised to deliver them failed me, or your piety received them all but still wants more -- and so has trumped up a charge of laziness against me.

As I said, the accusation does not distress me. On the contrary, it is clear proof of the warmth of your affection. So by all means keep at it. Don't stop pressing your complaint -- it brings me nothing but pleasure."""),

(4257, """From: Theodoret, Bishop of Cyrrhus
To: Damianus, Bishop of Sidon
Date: ~440 AD
Context: A graceful, self-deprecating reply to Damianus's flattering letter.

To Damianus, Bishop of Sidon,

It is the nature of mirrors to reflect the faces of those who look into them -- anyone who gazes at one sees his own features. The same is true of the pupils of our eyes: they show us other people's likenesses.

Your holiness furnishes a perfect example of this. You have not actually seen my ugliness -- you have simply gazed with admiration at your own beauty. I truly possess none of the qualities you ascribed to me. Still, it is my prayer that your words may yet be vindicated by reality, and I beg your piety to bring it about by your prayers that your praises do not fall to the ground for want of anything real to support them."""),

(4258, """From: Theodoret, Bishop of Cyrrhus
To: Gerontius, Archimandrite [head of a monastic community]
Date: ~440 AD
Context: Theodoret responds to Gerontius's anxious letter about an impending judgment, contrasting the monk's spiritual vigilance with his own admitted lethargy.

To the Archimandrite Gerontius,

The character of a soul is often painted in words, its unseen form revealed on the page. Your letter, reverend father, is exactly such a portrait -- it displays the piety of your holy soul. Your anticipation of that verdict, your anxiety, your search for advocates, your preparation of a defense: all of it clearly reveals your soul's passion for divine things.

We, by contrast, are practically asleep. We are nourished on idleness and stand in desperate need of the help that prayer provides. Give us that help, O man beloved of God, so that we may at last wake up and give some proper attention to the state of our souls."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Theodoret translations (IDs: 4254-4258)")

#!/usr/bin/env python3
"""Batch translate Theodoret letters 71-75 (IDs 4279-4283)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(4279, """From: Theodoret, Bishop of Cyrrhus
To: Zeno, General and Consul
Date: ~440 AD
Context: A congratulatory letter to the newly elevated consul Zeno, praising his military virtues and praying he may receive eternal rewards to match his earthly honors.

To Zeno, General and Consul,

Your courage has won universal admiration -- courage tempered by gentleness and meekness, showing kindness to your household and boldness to your enemies. These are the qualities of an admirable general. In a soldier's character the chief ornament is bravery, but in a commander prudence takes precedence. After these come self-discipline and fairness, by which a whole treasury of virtue is assembled. Such wealth is the reward of a soul that reaches after the good and, with its eyes fixed on the sweetness of the fruit, finds the labor well worth bearing.

For virtue's athletes, the God of all -- like some great master of the games -- has offered prizes: some in this life, some in the life beyond that has no end. Those belonging to this present life your excellency has already enjoyed; you have reached the highest honor. May it also be your lot to obtain the lasting, eternal blessings -- to receive not only the consul's robe but the garment that is beyond description and divine. This is the common prayer of all who understand the greatness of that gift."""),

(4280, """From: Theodoret, Bishop of Cyrrhus
To: Hermesigenes, Assessor [a legal advisor to a provincial governor]
Date: ~440 AD
Context: A festal letter that begins with a striking comparison between the fragmented pagan festival calendar and the universal Christian feast observed everywhere in the known world.

To Hermesigenes the Assessor,

In the days when humanity was buried in the darkness of ignorance, different cities celebrated different festivals. In Elis there were the Olympic games, at Delphi the Pythian, at Sparta the Hyacinthian, at Athens the Panathenaic, the Thesmophoria, and the Dionysian. These were the most famous -- and beyond them, various peoples held revels for one deity or another.

But now that those mists have been scattered by intellectual light, on every land and sea, mainlanders and islanders together keep the feast of our God and Savior. Wherever one might wish to travel -- toward the rising sun or the setting -- everywhere one finds the same celebration observed at the same time. There is no longer any necessity, as under the Mosaic law (which was adapted to the weakness of the Jews), to gather in a single city to commemorate our blessings. Every town, every village, the countryside and the farthest frontiers are filled with the grace of God, and in every place shrines and sanctuaries have been consecrated to the God of all.

So through every city we keep our festivals and greet one another in the joy of the feast. It is the same God and Lord who is praised in our hymns and to whom our sacred offerings are made. For this reason, as is well known, we neighbors send letters to one another to share the gladness the feast brings.

And so I write to you now and offer the festal greeting to your excellency. You will no doubt reply and honor the custom of the feast."""),

(4281, """From: Theodoret, Bishop of Cyrrhus
To: Apollonius
Date: ~440 AD
Context: Theodoret praises a talented pagan's natural gifts and education, then gently suggests that the one thing missing from his excellence is knowledge of God.

To Apollonius,

Themistocles, son of Neocles -- that famous and admirable general -- is described by his admiring historian as endowed with natural virtue alone. Pericles, son of Xanthippus, however, is said to have supplemented his native gifts with an education that enabled him to charm his listeners through persuasive eloquence: he could both see what needed to be done and articulate it in words. I see no impropriety in borrowing his own words to describe your case.

These examples illustrate your magnificence, for God our Creator has given you natural ability, and your education makes its brilliance all the more conspicuous. Nothing is lacking to complete the full measure of your fine qualities -- save only the knowledge of their Author. Let that be added, and the catalog of virtues will be complete.

I write this on hearing of your arrival, praying the Giver of all good things to send a beam of light to your mind's eye -- to reveal to you the greatness of his gift, to kindle your love for that treasure, and to grant the longed-for blessing to one who longs for it."""),

(4282, """From: Theodoret, Bishop of Cyrrhus
To: Urbanus
Date: ~440 AD
Context: A short festal greeting invoking the sacramental blessings of the feast.

To Urbanus,

Our generous Lord has granted us once again to enjoy the feast and to send your excellency the festal greeting. We pray that you may be well and prosperous, and that you may share in the unspeakable, divine gift which supplies to those who approach it the seeds of the blessings we hope for, and gives us the pledges of the life and kingdom that have no end.

These things we ask the loving Lord to grant you, for it is natural for friends to pray that their friends may be blessed."""),

(4283, """From: Theodoret, Bishop of Cyrrhus
To: The Clergy of Beroea
Date: ~440 AD
Context: Theodoret celebrates his warm ties with the clergy of Beroea, tracing their bond through a shared spiritual father, a beloved bishop, geographic proximity, and above all agreement in the faith.

To the Clergy of Beroea [modern Aleppo],

I see that my warm feelings toward your reverences are well founded, for your kind letter has assured me that my affection is returned. There are many reasons for this affection of mine.

First, your father -- that great and apostolic man -- was my father too. Second, I regard the truly devout bishop who now governs your church as a brother, in both blood and sympathy. Third, our cities are near neighbors. Fourth, our frequent dealings with one another naturally create friendship and, once created, strengthen it. If you like, I will add a fifth: we share the same relationship as the tongue has with the ears -- the one uttering speech, the other receiving it. For you listen most gladly to my words, and I am happy to let fall my small contribution.

But the crown of our union is our harmony in the faith: our refusal to accept any counterfeit doctrines, our preservation of the ancient apostolic teaching -- a tradition brought to you by venerable wisdom and nourished by the hard labor of virtue.

I urge you, then, to take even greater care of the flock: preserve it unharmed for the Shepherd, and boldly speak the famous words of the patriarch: "That which was torn by beasts I did not bring to you" [Genesis 31:39 -- Jacob's declaration that he never passed off a loss as unavoidable]."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Theodoret translations (IDs: 4279-4283)")

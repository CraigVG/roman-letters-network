#!/usr/bin/env python3
"""Batch translate Theodoret letters 66-70 (IDs 4274-4278)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(4274, """From: Theodoret, Bishop of Cyrrhus
To: Aerius, Sophist [a professional rhetorician and teacher]
Date: ~440 AD
Context: Theodoret invites a rhetorician to the dedication feast of a new church built to house relics of apostles and prophets.

To Aerius the Sophist,

She who bore you and raised you invites you to the long-awaited feast. The holy shrine is crowned with a roof. It is fittingly adorned. It is eager for the inhabitants for whom it was built -- apostles and prophets, the bold-voiced heralds of the old and new covenants.

So grace the feast with your presence. Receive the blessing that flows from it, and make the celebration more joyful for all of us."""),

(4275, """From: Theodoret, Bishop of Cyrrhus
To: Maranas
Date: ~440 AD
Context: Theodoret credits Maranas with building a new church and asks him to invite others to the dedication.

To Maranas,

It was really your task, my good sir, to summon the rest to the feast of the dedication as well. Through your zeal and energy the holy temple was built, and the bold-voiced heralds of truth have come to dwell in it, guarding all who approach in faith.

Still, I write to announce the season of the feast."""),

(4276, """From: Theodoret, Bishop of Cyrrhus
To: Epiphanius
Date: ~440 AD
Context: Theodoret carefully invites a man of different theological opinions to a church dedication, limiting the invitation to their shared civic ties rather than pressing the point of faith.

To Epiphanius,

I wanted to invite you to the feast of the holy apostles and prophets -- not only as a fellow citizen, but as one who shares both my faith and my home. But the state of your opinions prevents me from doing that.

So I set aside every claim except that of our common homeland, and I invite you to share in the precious blessing of the holy apostles and prophets. No difference of belief need stand in the way of that."""),

(4277, """From: Theodoret, Bishop of Cyrrhus
To: Eugraphia
Date: ~440 AD
Context: A letter of consolation to a recently widowed noblewoman, urging her to grieve with the restraint that Christian faith demands.

To Eugraphia,

Had I not been unavoidably detained, the moment I heard that your great and distinguished husband had fallen asleep I would have come straight to your side. I have received many kindnesses at your hands and owe you a great debt of gratitude. When circumstances beyond my control prevented me from paying it, I thought it unwise to send a letter at the very height of your grief -- when no messenger could have reached you, and sorrow would have kept you from reading what I wrote.

But now that your reason has had time to wake from the intoxication of grief, to steady your emotions and discipline the excess of sorrow, I am emboldened to write and to beg your excellency to think on human nature -- to reflect on how common the loss you mourn truly is, and above all to accept what our faith teaches and not let your distress run beyond its bounds.

For your most excellent husband, as the Lord himself said, "is not dead but sleeps" [cf. John 11:11] -- a sleep merely a little longer than he was accustomed to. This is the hope the Lord has given us; this is the promise we have received from Scripture.

I know how painful the separation is -- how deeply painful. Especially so when affection has been strengthened by harmony of character and length of time together. But let your grief be for a journey to a far country, not for a life that has ended. This kind of wisdom is especially fitting for those raised in piety, and it is this wisdom, my honored friend, that I beg you to seek.

I do not offer this advice as one who feels nothing himself. My heart genuinely grieved when I learned of the departure of a man I loved so well."""),

(4278, """From: Theodoret, Bishop of Cyrrhus
To: Eustathius, Bishop of Aegae
Date: ~440 AD
Context: Theodoret asks for help getting a noblewoman safely home -- Mary, the daughter of a Libyan official, who was captured by barbarians, sold into slavery, and rescued by Christian soldiers in Cyrrhus.

To Eustathius, Bishop of Aegae,

The story of the noble Mary belongs in a tragedy. As she herself says, and as several others confirm, she is a daughter of the distinguished Eudaemon. In the catastrophe that has overtaken Libya [likely the Vandal conquest of North Africa], she has fallen from her father's free estate into slavery. Merchants bought her from the barbarians and sold her to people in our region. Sold alongside her was a young woman who had once been her own household servant, so the galling yoke of slavery fell at the same moment on both mistress and maid.

But the servant refused to forget the distinction between them. Even in calamity she preserved her loyalty: after waiting on their common masters, she waited on the woman who was now reckoned her fellow slave -- washing her feet, making her bed, and performing every such service. The purchasers noticed. Soon the whole town heard the story of the mistress's noble birth and the servant's remarkable devotion.

When this reached the ears of the faithful soldiers stationed in our city (I was away at the time), they paid the purchase price and freed the woman from slavery. On my return, when I was told the whole sad story and the admirable generosity of the soldiers, I called down blessings on their heads, placed the noble young woman in the care of a reputable deacon, and arranged sufficient provision for her.

Ten months passed. Then she heard that her father was still alive and holding high office in the West. Naturally, she expressed a desire to return to him. It is reported that many travelers from the West are on their way to the fair being held here, and I ask your holiness to help her find safe passage among them."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Theodoret translations (IDs: 4274-4278)")

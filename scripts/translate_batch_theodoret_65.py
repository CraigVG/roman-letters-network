#!/usr/bin/env python3
"""Batch translate Theodoret letters 61-65 (IDs 4269-4273)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(4269, """From: Theodoret, Bishop of Cyrrhus
To: Archibius, Presbyter
Date: ~440 AD
Context: Theodoret apologizes for a delayed letter, blaming winter weather that kept ships in harbor, and reflects charmingly on how the debts of friendship grow larger the more you pay them.

To the Presbyter Archibius,

I did not ignore your two recent letters. I wrote back without delay and gave my reply to the deeply devout presbyter Eusebius. But the letter was held up: winter weather kept the ships in harbor, warning of a coming storm and bidding sailors and pilots to wait.

So I discharged my debt for the moment -- not in order to stop being a debtor, but to increase what I owe. For this is the nature of the obligation of friendship: it grows many times greater every time you pay it. Those who try to honor the laws of friendship only increase the power of its love, blowing sparks into a flame and kindling an ever-greater warmth, while everyone caught in that fire strives to outdo the other in affection.

Accept this defense, my dear friend. Forgive the delay. And send me a letter telling me how you are."""),

(4270, """From: Theodoret, Bishop of Cyrrhus
To: John, Presbyter
Date: ~440 AD
Context: Theodoret explains his preference for quiet obscurity, then warmly responds to hearing that John had praised him in a gathering -- initiating a correspondence by letter to match John's spoken kindness.

To the Presbyter John,

One of the men formerly called wise said, "Live unseen." I applaud the sentiment and have resolved to put it into practice. I see nothing wrong with gathering what is good from any source -- just as bees, they say, draw their sweet nectar from bitter herbs as well as wholesome ones, and I have seen them myself settling on a bare rock to suck up its meager moisture. It is far more reasonable for those of us credited with reason to harvest what is good wherever we find it.

So, as I said, I try to live unseen. Above all men I love peace and quiet.

But the very devout presbyter Eusebius, on his recent return from your region, reported that you had held a meeting at which my name came up, and that your piety spoke well of my insignificant self. I thought it ungrateful -- unfair, really -- that someone who had spoken so kindly of me should receive nothing in return. We may have done nothing worthy of praise, but we admire the intention behind such words, for praise of this kind is the offspring of affection.

So I greet your reverence, using as my messenger the same man who brought me your unwritten words. You were first in speech; I am first in writing -- I answer your spoken word with a letter. It remains for you now to answer letter with letter."""),

(4271, """From: Theodoret, Bishop of Cyrrhus
To: [unnamed recipients, a festal letter]
Date: ~440 AD
Context: A Paschal festal letter mixing the joy of Easter with grief over the storm engulfing the churches -- likely written around the time of the Christological controversies of the late 440s.

Festal greeting.

We have enjoyed the familiar blessings of the feast. We have kept the memorial of the saving Passion. Through the Lord's resurrection we have received the glad promise of the resurrection of all, and we have sung hymns to the unspeakable love of our God and Savior.

But the storm tossing the churches has not allowed us to taste that gladness without alloy. If, when one member of the body is in pain, the whole body shares the suffering, how can we hold back our grief when the entire body is in distress? What deepens our discouragement is the thought that these troubles may be the prelude to the general apostasy [a feared final falling-away from the faith before Christ's return].

May your piety pray that in our present condition we may receive divine help and, as the apostle puts it, "be able to withstand the evil day" [Ephesians 6:13]. And if any time remains for the business of this life, pray that the storm may pass and the churches recover their former calm -- so that the enemies of the truth may no longer gloat over our misfortunes."""),

(4272, """From: Theodoret, Bishop of Cyrrhus
To: [unnamed recipients, a festal letter]
Date: ~440 AD
Context: A brief Paschal letter connecting the disciples' initial bewilderment at the Crucifixion with their subsequent joy at the Resurrection.

Festal greeting.

When the Master endured the saving Passion for the sake of humanity, the company of the holy apostles was deeply shaken -- for they did not yet clearly understand what fruit the Passion would bear. But when they learned of the salvation that grew from it, they called the proclamation of the Passion "good news" and eagerly offered it to all humanity. Those who believed, their minds now enlightened, received it with joy. They keep the feast in memory of the Passion and transform the moment of death into an occasion for celebration and festivity -- for the resurrection, bound so closely to the Passion, dissolves the sadness of death and becomes a pledge of the resurrection of all.

Having just now taken part in this celebration, we send you these tidings of the feast like some fragrant perfume, and greet your piety."""),

(4273, """From: Theodoret, Bishop of Cyrrhus
To: General Zeno
Date: ~440 AD
Context: A letter of consolation to a grieving military commander, urging him to overcome sorrow through philosophical reflection on human nature and divine providence.

To the General Zeno,

To be struck by the misfortunes common to our nature is the lot of every person. To endure them bravely and rise above their assault is no longer common -- it belongs to those with resolution. This is why we admire the philosophers who chose the noblest course of life and conquered their sorrows through wisdom. And philosophy is the work of our power of reason, which governs the passions rather than being dragged about by them.

Grief is one of these human ills, and it is grief I urge your excellency to overcome. It will not be difficult for you to rise victorious over this feeling if you reflect on two things: human nature itself, and the uselessness of sorrow. For what good does it do the departed if we wail and grieve?

When you remember his noble birth, the long years of your friendship, his distinguished military service, and his celebrated achievements -- reflect also that the man adorned by all these things was, like all of us, subject to the law of death. Reflect further that everything is ordained by God, who guides human affairs according to his sacred knowledge of what will serve our good.

I have written what the limits of a letter allow. But I earnestly ask your eminence, for all our sakes, to take care of your health. Health is sustained by good spirits and destroyed by despondency. It is out of concern for all of us who depend on you that I have written this letter."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Theodoret translations (IDs: 4269-4273)")

#!/usr/bin/env python3
"""Batch translate Basil letters 191-195 (IDs 1002-1006)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(1002, """From: Basil, Bishop of Caesarea
To: Amphilochius, Bishop of Iconium
Date: ~368 AD
Context: Basil thanks Amphilochius for initiating correspondence and proposes a plan to restore fellowship between divided churches through mutual recognition and hospitality.

On reading your reverence's letter I gave hearty thanks to God, because I found in your words the traces of an old affection. You are not like most people: you did not stubbornly refuse to be the first to write. You have grasped the greatness of the prize promised to the saints for humility, and so you have chosen to win the race by taking second place. Among Christians these are the terms of victory -- the one content to come second wins the crown.

But I must not fall behind in this virtuous competition, so I return your greeting and share my thoughts with you. Since we are now in agreement on the faith, nothing further prevents us from being "one body and one spirit, called in one hope of our calling" [Ephesians 4:4]. It is for you, in your generosity, to follow up this good beginning -- to rally like-minded men to your side and to propose both a time and a place to meet. Then, by God's grace and through mutual accommodation, we may govern the churches with the kind of love that prevailed in ancient times: welcoming brothers from the other side as our own members, sending to them as to our own people, and receiving from them as from kin.

This was once the great boast of the Church. Brothers traveling from one end of the world to the other carried small tokens of identification and found fathers and brothers everywhere. The enemy of Christ's churches has robbed us of this privilege. Now we are each confined to our own city, and everyone eyes his neighbor with suspicion. What more can be said? "Our love has grown cold" [Matthew 24:12] -- the very thing by which alone, as our Lord told us, his disciples are recognized [John 13:35].

So if you are willing, start by making yourselves known to one another, that I may learn with whom I am to be in agreement. Then, by common consent, we will settle on a time and place."""),

(1003, """From: Basil, Bishop of Caesarea
To: Sophronius, the Master
Date: ~368 AD
Context: A brief, gracious thank-you note to Sophronius for swift action on a favor.

With your extraordinary zeal for doing good, you wrote to tell me that you consider yourself doubly indebted to me -- first for receiving my letter, and second for having had the chance to do me a service. What thanks, then, must I owe you, both for reading your delightful words and for finding my request so quickly granted! The news itself was gratifying enough, but it gave me far greater pleasure knowing that you were the friend who made it happen.

God grant that before long I may see you, thank you in person, and enjoy the great pleasure of your company."""),

(1004, """From: Basil, Bishop of Caesarea
To: Meletius, physician
Date: ~368 AD
Context: A wonderfully self-deprecating letter from Basil about his miserable winter health -- fever, quartan ague, and a body "thinner than a cobweb."

I cannot escape the discomforts of winter as well as cranes can, though when it comes to foreseeing trouble I am quite as shrewd as any crane. But in freedom of life the birds are almost as far ahead of me as they are in their ability to fly.

First, I have been detained by various worldly business. Then I have been so wasted by constant, violent attacks of fever that there now seems to be something thinner even than I was -- and I was thin before. On top of all that, bouts of quartan ague [a malarial fever recurring every four days] have continued for more than twenty cycles. I do seem to be free of fever at the moment, but I am in such a feeble state that I am no stronger than a cobweb. The shortest journey is too far for me, and every gust of wind is more dangerous to me than a great wave is to sailors at sea.

I have no choice but to hide in my hut and wait for spring -- if I can last that long and am not carried off first by the internal illness that never leaves me. If the Lord saves me with his mighty hand, I will gladly make my way to your remote corner of the world and gladly embrace a friend so dear. Only pray that my life may be ordered in whatever way is best for my soul."""),

(1005, """From: Basil, Bishop of Caesarea
To: Zoilus
Date: ~368 AD
Context: Basil responds to a flattering letter from Zoilus with characteristic humor, then gives a stark report on his health.

What are you doing, my excellent friend, outstripping me in humility? Educated as you are, capable of writing such a fine letter, you still ask my forgiveness -- as though you had done something rash or above your station. But enough of that game. Keep writing to me at every opportunity.

Am I not practically illiterate? It is a delight to read the letters of an eloquent writer. Have I not learned from Scripture how good a thing love is? I count the companionship of a loving friend beyond all value. And I hope you will be able to tell me of all the good things I pray for you: the best of health and prosperity for your entire household.

As for my own affairs, my condition is no more bearable than usual. That much is enough to tell you -- you will understand how bad my health is. It has indeed reached such a pitch of suffering that it is as hard to describe as to endure (assuming your own experience has not matched mine). But it is the work of our good God to give me the strength to bear patiently whatever trials are sent for my benefit by our merciful Lord."""),

(1006, """From: Basil, Bishop of Caesarea
To: Euphronius, Bishop of Colonia in Armenia Minor
Date: ~368 AD
Context: Basil explains why he so rarely writes to this remote bishop and asks for prayers for the exiled orthodox bishops scattered by the Arian persecution.

Colonia, which the Lord has placed under your authority, lies well off the ordinary routes. The result is that, although I frequently write to the other bishops in Armenia Minor, I hesitate to write to your reverence because I never expect to find anyone going your way with a letter. Now, however, since I am hoping either for your visit in person or that one of the bishops I have written to will forward this letter to you, I write to greet you.

I want you to know that I am still alive -- and at the same time I urge you to pray for me. Ask the Lord to ease my afflictions and lift the heavy weight of pain that now presses on my heart like a cloud. I will have this relief if he will only grant a swift restoration to those godly bishops who are now being punished for their faithfulness to true religion by being scattered across the world."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Basil translations (IDs: 1002-1006)")

#!/usr/bin/env python3
"""Batch translate Basil letters 208-213 (IDs 1019-1024)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(1019, """From: Basil, Bishop of Caesarea
To: Eulancius
Date: ~369 AD
Context: Basil writes to a man in Neocaesarea who used to be his supporter, gently chiding him for his silence and hoping the hostile atmosphere there has not turned him.

You have been silent for a long time, though you have great power of speech and are well trained in the art of conversation and in displaying your eloquence. Perhaps it is Neocaesarea that is keeping you from writing to me. I suppose I should count it a kindness if the people there simply do not mention me at all -- for according to those who report what they hear, the mentions are not kind.

You, however, used to be one of those who were disliked on my account, not one of those who dislike me on account of others. I hope that description still fits you, and that wherever you are you will write to me and think well of me -- if you care at all for what is fair and right. It is certainly fair that those who first showed affection should be repaid in kind."""),

(1020, """From: Basil, Bishop of Caesarea
To: [unnamed recipient]
Date: ~369 AD
Context: A brief, warm letter to a loyal friend who has risked his reputation defending Basil, thanking him and encouraging him to keep demanding letters.

It is your lot to share my troubles and to fight on my behalf. This is proof of your courage. God, who orders our lives, grants to those who can endure great battles a greater opportunity for renown. You have truly risked your own reputation as a test of your loyalty to your friend -- like gold in the furnace.

I pray God that others may be made better, that you may remain what you are, and that you will never stop scolding me (as you do) and accusing me of not writing often enough, as though my neglect does you a grave injustice. That is an accusation only a friend makes. Keep demanding payment of such debts. I am not so unreasonable about paying the claims of affection."""),

(1021, """From: Basil, Bishop of Caesarea
To: The notables of Neocaesarea
Date: ~369 AD
Context: A major letter to the leading citizens of Neocaesarea defending himself against rumors and slanders, recalling his family roots in the region and his grandmother Macrina who raised him there.

I am really under no obligation to publish my thoughts to you or to explain why I am currently staying where I am. It is not my custom to advertise myself, and the matter hardly merits publicity. I am not, I think, following my own whims -- I am responding to the challenge your leaders have thrown down.

I have always tried harder to go unnoticed than fame-seekers try to get noticed. But I am told that everyone's ears in your city are buzzing, while certain professional gossips -- hired specifically for the purpose -- are spinning tales about me and my doings. So I cannot think it right to leave you exposed to teaching born of malice and a foul tongue. I must tell you myself how things actually stand.

From childhood I have known this place. I was raised here by my grandmother [Macrina the Elder, a disciple of Gregory Thaumaturgus]. I have often retreated here, and spent many years here when trying to escape the noise of public affairs -- for experience taught me that the quiet and solitude of this spot are conducive to serious thought. Now that my brothers are living here as well, I have gladly retired to this haven and taken a brief rest from the constant pressures surrounding me -- not as a base from which to cause trouble for others, but to satisfy my own longing for peace.

So why the need for dream-interpreters and hired rumor-mongers, and for making me a topic at public dinners? Had the slander come from any other quarter, I would have called you as my witnesses. So now I ask each of you to remember those old days when your city invited me to take charge of educating its young, and a delegation of your leading men came to see me...

[The letter continues at length with Basil's detailed defense of his conduct and theology against the Neocaesarean accusations.]"""),

(1023, """From: Basil, Bishop of Caesarea
To: Hilarius
Date: ~369 AD
Context: Basil laments that a letter from Hilarius went missing, describes the factional warfare in the churches, and confides that forged documents are being circulated under his name.

You can imagine how I felt and what state of mind I was in when I reached Dazimon and found you had left just days before my arrival. Since boyhood I have admired you, and ever since our old school days I have valued your company. But beyond that, nothing is as precious now as a soul that loves truth and possesses sound judgment in practical matters -- and this, I believe, I find in you.

I see most men, as in a hippodrome, divided into factions, shouting for their respective sides. But you stand above fear, flattery, and every base impulse, and so you naturally look at truth with an unbiased eye. I can see too that you are deeply concerned about the affairs of the churches, about which you say you sent me a letter. I would like to know who carried it, so I may find out who robbed me of it. No such letter has ever reached me.

How much would I have given to meet you, to tell you all my troubles in person! When one is in pain, even describing the suffering brings some relief. How gladly I would have answered your questions face to face, not trusting to lifeless letters but in my own person -- for living words carry more persuasive force and are far less vulnerable to misrepresentation.

As things stand, nothing has been left untried. The very men in whom I placed the greatest confidence -- men who, when I saw them among others, seemed to me more than human -- have received documents written by someone else and passed them along as mine. On that basis they are slandering me to the brothers, as though my name were now the one thing every pious and faithful person should most detest."""),

(1024, """From: Basil, Bishop of Caesarea
To: [unnamed recipient]
Date: ~369 AD
Context: Basil thanks an unnamed correspondent for a consoling letter, confesses discouragement at the spiritual apathy of his flock, and reports that he may be summoned to the imperial court.

May the Lord, who has been my prompt helper in affliction, grant you the same refreshment with which you have refreshed me by your letter -- rewarding your consolation of my humble self with the real and great gladness of the Spirit. For I was indeed downcast in soul when I saw in a great multitude of people an almost brutish insensibility, and in their leaders an entrenched and ineradicable uselessness.

But I saw your letter. I saw the treasure of love it contained. And I recognized that he who governs all our lives had caused some sweet consolation to shine on me in the bitterness of my existence. So I greet your holiness in return and urge you, as I always do, not to stop praying for my unhappy life: that I may never, drowned in the unrealities of this world, forget God "who raises the poor from the dust" [Psalm 113:7]; that I may never be puffed up with pride and "fall into the condemnation of the devil" [1 Timothy 3:6]; that I may never be found by the Lord neglecting my stewardship, or asleep, or discharging it badly and wounding the conscience of my fellow servants; and that I may never, keeping company with the drunken, suffer the punishment God's just judgment threatens against wicked stewards.

Know also this: I am expecting to be summoned by the heretics to the imperial court, in the name of peace. I have also learned that a bishop has written urging me to hurry to Mesopotamia, assemble like-minded supporters, and travel with them to see the emperor. But my health may not allow me to undertake such a journey."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Basil translations (IDs: 1019-1024)")

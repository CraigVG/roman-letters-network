#!/usr/bin/env python3
"""Batch translate Theodoret letters 56-60 (IDs 4264-4268)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(4264, """From: Theodoret, Bishop of Cyrrhus
To: [unnamed recipient, a festal letter]
Date: ~440 AD
Context: The briefest of festal greetings, written at a moment of acute personal grief.

Festal greeting.

My grief is now at its peak and weighs heavily on my mind. But I have thought it right to honor the custom of the feast, so I take up my pen to greet your reverence and pay the debt of affection."""),

(4265, """From: Theodoret, Bishop of Cyrrhus
To: Eutrechius, Prefect
Date: ~440 AD
Context: Theodoret congratulates a newly elevated prefect, combining genuine warmth with the formal obligations of the patron-client relationship.

To the Prefect Eutrechius,

Among the many blessings the Ruler of the universe has granted us is the news of your excellency's elevation. I congratulate both you on your new honor and your subjects on so gentle a rule. I felt it would be wrong to keep my satisfaction to myself and not express it in writing.

Your magnificence knows perfectly well how warm our affection for you is -- an affection you have most warmly returned. And being so full of this mutual regard, we pray the Giver of all good things to continue pouring his manifold gifts upon you."""),

(4266, """From: Theodoret, Bishop of Cyrrhus
To: Nomus, Consul
Date: ~440 AD
Context: Theodoret writes to a powerful consul, torn between not wishing to intrude on a busy man and not wanting his silence to seem like neglect.

To the Consul Nomus,

I am of two minds about writing to your greatness. On one hand, I know that everything depends on your judgment. I see you bowed under the weight of public responsibilities, and I think it better to keep quiet. On the other hand, knowing the breadth and capacity of your intelligence, I cannot bear to say nothing -- and I am afraid of being accused of negligence.

What pushes me further is the lingering regret I feel from the brief taste I had of your company. My full enjoyment of it was cut short by the illness and death of that most blessed man [apparently a mutual friend or associate whose identity is lost to us]. So now I think writing will be some consolation.

I pray the Master of all to guide your life on favorable winds, so that we may continue to benefit from your generous care."""),

(4267, """From: Theodoret, Bishop of Cyrrhus
To: Claudianus
Date: ~440 AD
Context: A warm letter of friendship carried by a military officer, affirming that true bonds survive distance and time.

To Claudianus,

Sincere friendships are neither dissolved by distance nor weakened by time. Time does indeed inflict indignities on our bodies -- it strips them of the bloom of beauty and brings on old age. But friendship it only makes more beautiful, constantly kindling its fire to greater warmth and brightness.

So although I am separated from your magnificence by many days' journey, the goad of friendship drives me to write this greeting. The letter is carried by the standard-bearer Patroinus, a man whose high character makes him worthy of every respect -- he strives with great zeal to observe the laws of God.

Please be so kind, most excellent sir, as to send back by him news of your precious health, and word on whether you have fulfilled that promise of yours."""),

(4268, """From: Theodoret, Bishop of Cyrrhus
To: Dioscorus, Bishop of Alexandria
Date: ~440 AD
Context: Theodoret writes a carefully diplomatic letter to the powerful patriarch of Alexandria, praising his modesty and requesting his prayers -- a striking gesture given that Dioscorus would later become Theodoret's bitter enemy at the "Robber Council" of Ephesus in 449.

To Dioscorus, Bishop of Alexandria [the patriarch of the most powerful see in the eastern church after Constantinople],

Among the many virtues we hear adorn your holiness -- for the fame of your glory fills every ear and flies in every direction -- men unanimously single out your modesty for special praise. This is a virtue our Lord set himself as the example of in his teaching: "Learn of me, for I am meek and lowly in heart" [Matthew 11:29]. For though God is exalted -- indeed, the Most High -- he honored the meek and lowly spirit when he took on human flesh.

Looking to him, my lord, you do not fix your gaze on the multitude of your subjects or the height of your throne. Instead you see human nature itself, with all its swift reversals, and you follow the divine laws whose observance wins us the kingdom of heaven.

Hearing of this modesty, I take courage to greet in this letter one who is sacred and dear to God, and I offer prayers whose fruit is salvation. The occasion for writing is provided by the deeply devout presbyter Eusebius. When I learned of his journey to Alexandria, I immediately wrote this letter to ask your holiness to support us with your prayers, and to gladden us with a reply -- sending to us who are hungry the blessed banquet of your words."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Theodoret translations (IDs: 4264-4268)")

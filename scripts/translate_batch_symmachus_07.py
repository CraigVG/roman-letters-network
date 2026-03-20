#!/usr/bin/env python3
"""Batch translate Symmachus letters (IDs 5135, 5434, 5137, 5140, 5141)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(5135, """From: Quintus Aurelius Symmachus, Roman Senator
To: Unknown recipient
Date: ~376 AD
Context: A fragmentary letter surviving only as a partial heading and brief reference in the manuscript.

[This entry preserves only textual apparatus and a brief heading. The main letter text is largely lost.]"""),

(5434, """From: Quintus Aurelius Symmachus, Roman Senator
To: Caecilianus and others (multiple letter fragments)
Date: ~377 AD
Context: Fragments of several short letters including a military recommendation and an intervention on behalf of a debtor.

...has completed his years of military service without incident. I ask that, having been admitted into your clientele, he may be glad both that my patronage has been of use to him and that yours has been added.

---

To Caecilianus: I do not refuse to intercede on behalf of just debts. It would be wrong to reject an opportunity for a favor in such matters..."""),

(5137, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~377 AD
Context: A fragment about horse purchases, urging a friend to show fair generosity in the selection and pricing of chariot horses.

...I pray you, show the just kindness of a fair price and good selection in this long foreign journey, so that the men who followed a flattering reputation may be confirmed in their hope -- a hope grounded in your dedication and my own standing."""),

(5140, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~379 AD
Context: A fragmentary letter in which Symmachus mentions waiting for a friend's literary judgment, asking for it to be confirmed by oath since friendship has come under suspicion of flattery.

...I am still waiting in suspense for your judgment on those pieces belonging to our togaed nation. I want you to send it sworn, because it is fitting to bind one's word with an oath whenever friendship is suspected of mere courtesy."""),

(5141, """From: Quintus Aurelius Symmachus, Roman Senator
To: Eusignius and others (multiple short letters)
Date: ~379-388 AD
Context: Two short letters: one expressing relief at the resumption of correspondence, and one recommending a man named Eusebius.

I had long been waiting for your letters, uncertain in my mind about what so prolonged a silence might mean. But once you restored to me the gift I had longed for, my worry turned to joy. And truly it is in our nature that the complaint about a long-delayed courtesy fades away the moment we obtain what we wished for. So I am deeply grateful that the pledge of our friendship has been restored to me. You will prove my trust was not misplaced by maintaining your attentiveness with constant affection.

---

To Eusignius (~before 388 AD): I shall see what the justice of the times, the merits of our cause, and your own efforts -- if indeed I am dear to you -- can accomplish. In the person of my brother Eusebius, a most distinguished man, I embrace the fulfillment of the moderation he has shown toward us. I honor his integrity in my thoughts and commend it in my words. Even though he does not seek a reward for his good intentions, I nonetheless wish to repay him through your friendship. You will do something as welcome to my wishes as it is consistent with your own character, if this most prudent man may recognize that whatever you grant me, he acquires for himself."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Symmachus translations (batch 07)")

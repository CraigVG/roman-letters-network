#!/usr/bin/env python3
"""Batch translate Symmachus letters (IDs 5189, 5190, 5191, 5094, 5192)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(5189, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~386 AD
Context: A recommendation for the honest man Turasius, who faces an unjust lawsuit.

Everyone who hopes to be helped by gaining access to you takes -- in my judgment -- no fruitless path to winning your favor when they rely on my endorsement. One such person is the worthy Turasius, a friend of mine, who blames fortune for the lawsuit unjustly brought against him and pins his hope of a good outcome especially on your help. Protect a man who asks for what is fair, and extend the fame of your generosity -- a fame that will be crowned with the greatest increase if things go well for Turasius through your efforts."""),

(5190, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~386 AD
Context: A brief courtesy letter sent via a friend's servant, expressing good wishes.

Duty demanded that I write, especially since a convenient opportunity presented itself. Your man offered himself to me as a letter carrier, and I realized it would be a grave offense to send him back with nothing. I wish you well, I report my own good health, and in return I ask you to reward me with news of your wellbeing."""),

(5191, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~387 AD
Context: Symmachus protests an unjust tax being levied on a senatorial candidate who is putting on wild beast games, arguing that the transport tax on animals should apply only to commercial dealers.

Quaestors of our order [quaestor-designates who were expected to sponsor elaborate public games as part of the office] have never paid the transport duty on their own wild animals. Our ancestors considered it oppressive to add an excessive expense to men already bearing the burden of senatorial rank. This exemption was recently granted to me when I was organizing a gladiatorial show -- more in the name of the Roman people than my own. Now my brother Cynegius, a quaestorian candidate, is being charged the two-percent tax [quinquagesima -- a 2% customs duty] -- a levy that should only be recognized by commercial animal dealers, since they serve profit. The injustice of this charge..."""),

(5094, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~387 AD
Context: Symmachus congratulates a friend on a public appointment, urging him to live up to the high expectations that surround him.

I count the joys of your fortune among my own debts, and I take you as my judge of this sentiment -- you who have seen my heart tested whenever you consult your own. It was fitting in these tender days of good times that a man praised by public counsel should be admitted to office. Since events have unfolded as everyone hoped, carry out your work in a manner worthy of so great a prince's judgment. The weight of expectation -- always burdensome to good men -- presses upon you. For even though it looks to the worthy, it is nevertheless close to danger, since it always promises itself more. You have an age friendly to virtue, in which only the best..."""),

(5192, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~387 AD
Context: Symmachus asks a friend to intervene in a case where forged financial documents are being used to extort money from innocent people by the staff of the Italian treasury.

A friend's cause prompted me to write, but I must confess I was even more concerned for your reputation. The distinguished Minucianus faces danger over a small sum of money, but for you a path to no small glory will open if -- as I hear -- the slander stirred up by forged promissory notes is laid to rest. It is painful to describe the tricks by which the staff of the Italian treasury operates. They say that under the pretense of public debts, false claims are being read out in the names of private individuals. The weak are immediately overwhelmed by the pressure; the stronger defend themselves once they have marshaled the protections of the law on their side..."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Symmachus translations (batch 12)")

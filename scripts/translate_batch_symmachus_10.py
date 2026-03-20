#!/usr/bin/env python3
"""Batch translate Symmachus letters (IDs 5085, 5183, 4995, 5185, 5088)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(5085, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~383 AD
Context: Symmachus asks a friend not to intervene in a lawsuit against his son Caecilianus, who is serving as Rome's grain commissioner.

My son Caecilianus, a distinguished man currently managing the grain supply of our common fatherland, has learned from reliable evidence that his adversary -- a man named Pirata, or his procurator -- has drawn hope from the prospect of your support. I denied that you are in the habit of taking on financial lawsuits. Still, with the kind of excessive anxiety that is typical of people, he asked me for a letter consistent with your upright character. I did not refuse my help to a man asking for something easy and just.

The essence of the duty laid on me is this: please do not let an opponent of a citizen who is absent and bound up in public duties hope for any advantage from your sense of justice. There are laws, there are courts, there are magistrates that the litigant may use without troubling your conscience. Farewell."""),

(5183, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~383 AD
Context: A recommendation for a man named Ammonius, coupled with a reproach for the friend's infrequent letters.

I would not have you judge the character of the man I am recommending by the standards of the others who handle senatorial accounts. He was not born into a mediocre station or the lowest class, but guards the honor of his birth with personal modesty. That is why I did not consider it beneath me to support a man I know well with the testimony of a letter, and your own singular nobility should not hesitate to embrace a man you see endorsed by my approval. This much is said on behalf of Ammonius. But I should not conceal my own longing for your words, a desire made all the more keen by the rarity of your letters."""),

(4995, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~384 AD
Context: A letter written during a period of political turmoil, in which Symmachus alludes to dangerous rumors without specifying them, choosing hope over alarm.

I cannot decide what form of reply best suits the occasion. I have been afflicted for so long by an excess of rumors that I ought neither to deceive those who love me with false ones nor alarm them with true ones. Yet hope -- which always provides patience in adversity..."""),

(5185, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~384 AD
Context: A brief note about having looked after a friend's interests through an intermediary.

I would have attended to your interests even without a reminder. The distinguished Patruinus, my lord and son, will confirm that I have kept your affairs in mind. You should urge him to assist your wishes, both out of his own customary goodwill and in view of my request."""),

(5088, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~385 AD
Context: Symmachus writes from his sickbed, reporting that he has successfully arranged for a friend's protege to be enrolled among the ranks of consulares (former consuls) by decree of the Senate.

When I wrote this letter to you, I was confined to my bed by illness -- freed from danger, to be sure, but still without strength, which keeps being drained by intermittent fevers. Yet even amid the troubles of my poor health, I set my friends to work on having our mutual pledge enrolled among the ranks of consulares by a senatorial decree. Your merits were taken into account -- I will not claim that anything was owed to my influence. I have given the official records of the most distinguished order to the honorable Datianus, and when they reach your hands, you may pronounce that I have fulfilled the obligations of friendship. For there is nothing I want more than to be judged a diligent performer of honest duty. Farewell."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Symmachus translations (batch 10)")

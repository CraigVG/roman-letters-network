#!/usr/bin/env python3
"""Batch translate Symmachus letters (IDs 4992, 5181, 4993, 5084, 4994)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(4992, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~383 AD
Context: Symmachus teases a friend who left Rome instead of staying for the festival of the Great Mother, and recalls a recent conversation about the priority of private business over public life.

I assumed your return was approaching, since the sacred rites of the Mother of the Gods [the festival of Cybele, the Magna Mater, celebrated with elaborate processions in March-April] were near. Instead, you are headed for Daunia [the region around modern Foggia in Apulia, southeastern Italy] and leave both me and the capital behind. Go ahead and mock the easy-going nature of your friends -- who, if this insult stung them, would at least withhold their letters in retaliation. Instead, we soothe you with courtesies as you depart and suggest pleasant things to your mind, while you put the management of your estate ahead of everything.

You will recall that this was the very premise of your letter: that at this stage of life nothing should be tended more carefully than domestic affairs. But I, knowing the vein of your character, know this was said in jest. When would a mind as distinguished as yours stoop to common worries? My judgment, then, is that you should save such pretenses for people who do not know the true depths of your soul. You will satisfy me in one way only: if, setting aside epistolary excuses..."""),

(5181, """From: Quintus Aurelius Symmachus, Roman Senator
To: Felix and others (multiple short letters)
Date: ~383-397 AD
Context: A recommendation for a friend named Helpidius, and a note to Felix expressing concern about the improper appointment of a procurator.

Our brother Helpidius was called away not only by desire for your company but also by the consul's letter. Although the old bond between you promises him your affection, I think my recommendation will add something as well. Build up, I ask you, your old devotion to our friend with fresh favors, so that what has already been accomplished may be crowned -- and grant me this boon: let him feel that the merit he established with you through his own loyal service has been enhanced by my endorsement.

---

To Felix (~396-397 AD): Whoever neglects a friend's reputation is unstable in loyalty. To ensure that this vice is not justly charged to me, I am worried about your standing even in other people's disputes. By what law, by what public interest, did an unknown and untested procurator draw out the distinguished Eusebius -- who is said to have served among the imperial notaries -- so that a civil case might be snatched away from the city courts?..."""),

(4993, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~383 AD
Context: Symmachus explains that a copying error in his letter headings was accidental, and uses it as an excuse for a witty meditation on the tedium of formal correspondence.

I too embrace the old-fashioned form in my letter headings, and I am quite surprised that a copyist's error crept in. My usual practice is to place only the names at the top of my letters, and the scribe altered this simple custom by a newfangled addition. But it will be clear that this was done by accident rather than design if you recall that none of my earlier letters ever bore such a vulgar heading. Still, however this happened, I am glad something new turned up that freed me from the usual style of reply. For how long will we keep up the giving and returning of..."""),

(5084, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~383 AD
Context: A brief letter recommending a young man named Eusebius who seeks an imperial pardon after a youthful indiscretion.

It is common practice for those who need help to turn to proven supporters. One such person is Eusebius, who, having slipped into the errors of youth and been marked by a judicial ruling, now implores the surest remedy -- an imperial pardon. But so that the desired result may smile on him quickly, he has hoped that the cause of his petition might be entrusted to your care. The essence of his request is this: that through the remission of the judgment against him, he may erase the wound to his reputation."""),

(4994, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~383 AD
Context: A politically sensitive letter about the defeat of a proposal to erect a statue of Praetextatus -- Symmachus's close friend and a leading pagan aristocrat -- by the Vestal Virgins, which the pontifical college rejected.

Has it really pleased our common father to keep you detained longer than I would wish? Or do you so detest city life that you frustrate my expectations with a pious excuse? Truly, nothing is done or said here that a good heart and a pure nature could embrace. But however things stand, if you were in Rome, the bitterness might be softened by our mutual support. As it is, I experience the offense of events all the more keenly because I bear them alone.

Here is one example, from which you may infer the rest: they have decided to dedicate a statue of our Praetextatus [Vettius Agorius Praetextatus, d. 384 -- one of the last great pagan aristocrats of Rome, revered by Symmachus and his circle], proposed by the Vestal Virgins [the priestesses of Vesta, one of the last surviving pagan institutions in Rome]. The pontifices [the priestly college] were consulted, but before they even weighed the reverence owed to that sublime priesthood, or the custom of a long tradition, or the circumstances of the present time, they voted -- all but a few who followed me -- to erect his likeness..."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Symmachus translations (batch 09)")

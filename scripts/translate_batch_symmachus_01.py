#!/usr/bin/env python3
"""Batch translate Symmachus letters (IDs 5422, 5060, 5125, 5423, 4970)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(5422, """From: Quintus Aurelius Symmachus, Roman Senator
To: Unknown recipient
Date: ~399 AD
Context: A fragmentary letter header; the text of this letter is largely lost, surviving only as a partial heading in the manuscript tradition.

[This letter survives only as a fragment -- the main text has been lost in transmission.]"""),

(5060, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~371 AD
Context: Symmachus playfully scolds an elderly friend for repeatedly promising to return to Rome and never following through.

Your servant delivered two letters from you, and I would be guilty of bad faith if I did not reply in kind. In both letters you promised to return to Rome -- if your years permit it. You have written the same thing many times before; I no longer put any stock in your pledges. Repeating a promise is just a rehearsal for breaking it.

I know that old men grow slow to take on effort, but since bad habits only deepen with time, I need to drag you here tomorrow -- before the passing days give you an even better excuse. Nestor [the legendary Greek elder from Homer's Iliad], in his third generation of life, never asked for an exemption from service, and even the aged Phoenix [tutor to Achilles] never excused Achilles from duty on account of his own advanced years. And truly, the distance between us is nothing. Spoletium [modern Spoleto, about 100 miles north of Rome] is practically a suburb. While you chew over your poems and compose epigrams inspired by groves and rivers, the pleasure of learned thoughts will make the journey painless."""),

(5125, """From: Quintus Aurelius Symmachus, Roman Senator
To: Protadius
Date: ~371 AD
Context: A long, multi-part letter touching on their mutual silence, literary exchanges, and the proper style of correspondence between friends. This entry contains several short letters to Protadius and Minervius.

You know that our silence is an equal offense on both sides, and so the blame is unfairly placed on me alone for what we share in common. I have a defense, though: the comings and goings of travelers are hard to track, and you never stay in one place -- you shuttle between Trier on official business and the Five Provinces [southern Gaul, roughly modern Provence and Languedoc] for leisure. I am fixed in Rome, and more so now, since the presence of your distinguished brother both holds me here with his responsibilities and delights me with his reputation. You could have combined your letters to us into one packet, so that both your brother and the man who deserves to be counted as his equal would receive them together. I am glad you have done so at last, even if late. Still, when you held off writing, I never thought your devotion to me had slipped. True friendship is so secure that it measures the other's love by its own faithfulness. I am tired of saying more in this vein, so let me turn to the part of your letter that touches on something I have been wanting.

You say my writings have reached your hands through our mutual friend Minervius, who cannot keep away from my trifles -- drawn more by literary curiosity than by any real pleasure. If you have enough leisure to seek out even dull material to relieve your boredom, I will send you everything I have composed, confident of the forgiveness your affection guarantees me. But I nearly forgot to raise the complaint that should have come first: has the simple use of our letters really died out, that you prefer to dress your pages in the fashionable affectations of our age? Let us return to plain headings, and when a greeting is given or returned, let us agree that nothing is more gracious or pleasing than our customary words. Take my letter as your model -- and if you refuse to follow it, I will be marked both as arrogant and lumped together with those whose great pretension in words masks an utter emptiness of thought.

---

To Protadius (~400 AD): The same consul who summoned me had called you to Milan. I hoped the occasion would bring us together, but when illness kept you away, I bore the loss of that longed-for joy very badly. Now that the consular festivities -- which surpassed everyone's expectations in their splendor -- are finished, I am returning to Rome, where the distinguished magistrate himself has promised to come shortly, with my son-in-law confirming it. How I wish that if your health has fully returned, you would make up for your earlier absence by visiting, and in one trip both pay the Senate a voluntary courtesy and the consul the honor he is owed. But how can I dare to hope for so much, when even lesser hopes have come to nothing? When will you ever prefer the toga to the hunt?

---

To Protadius (~396 AD): I want the bonds of affection between us to grow every day, but I would rather not be indebted for your letters -- which are often thrown in my face as proof of my laziness. So to your two letters, which did not reach me at the same time, I reply with an equal number but send them together. I am well, as far as my age allows as it slopes toward old age. I rarely visit my country estate, and the chance to read is rarer still. You have ample opportunity both to enjoy the countryside and to pursue learning. That is why you write to me so often -- because all your time, devoted to exercising your mind, is claimed by leisure. But my boldness will not yield to your confidence. Even if you pore over the works of the ancients and commit your own to the page, I will pester you with my dry prose, which you must read out of both love and good judgment, so that I may make up for neglecting those other works."""),

(5423, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend in Spain (name lost)
Date: ~371 AD
Context: Symmachus writes to a friend he thought was in Spain, asking for help purchasing racehorses for his son's upcoming praetorian games.

Other letters of mine have been chasing you across Spain -- I had assumed you were living there because of the extent of your estates. Now that more reliable reports tell me you are enjoying leisure at your ancestral home, I am grateful for the mistake, since it gave me a reason to write to you again. Yet even this second letter, though it should satisfy your expectations, does not yet satisfy mine. I wish I could honor your friendship with letters as continuously as I have never ceased to cherish it in my heart.

I add a request. My son's praetorian games [public spectacles, usually involving chariot races and wild beast shows, that Roman officials were expected to fund], which I have long been preparing you for, are now approaching -- if fortune smiles on us. This reminds me that I need to assemble noble chariot teams for the competition, selecting the best horses from many herds. Do not let the fact that you have settled far away in Spain work against my peace of mind. Just help the agents I have sent for the horse purchases with your letters of introduction. Your recommendation will carry weight with your friends on our behalf, I trust."""),

(4970, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~371 AD
Context: Symmachus is concerned about the security of his correspondence, suspecting that letter carriers may be reading or tampering with his sealed letters.

I have learned that several people were strolling around our city's forum after receiving letters from me, and I am deeply worried that their pretended haste may have been a cover for some kind of fraud against me. I have accordingly enclosed copies of my letters along with the names of the people to whom they were addressed, for you to review or re-examine. In return, please let me know about each one -- either confirm that the duty was properly carried out, or expose any breach of trust. I am equally eager to know whether you received all my letters with their seals intact, bearing the impression of that signet ring in which my name is more easily recognized than read.

You will judge from reading through the copies that there was nothing in them I would fear being made public. There is no cause for secrecy between us. We share our services with open hearts. Nothing lurks in our consciences that needs to be hidden through the tunnels of written correspondence. The point is simply this: let us not allow anyone to make fools of our candor. My diligence should not have to tolerate a spy, since my caution has given me nothing to fear. Farewell."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Symmachus translations (batch 01)")

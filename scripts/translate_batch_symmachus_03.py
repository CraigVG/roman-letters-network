#!/usr/bin/env python3
"""Batch translate Symmachus letters (IDs 5425, 5063, 5426, 5129, 5162)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(5425, """From: Quintus Aurelius Symmachus, Roman Senator
To: Aurelianus and Alexander (multiple letters)
Date: ~372-401 AD
Context: Several letters bundled together: a request for help obtaining racehorses from Spain, a brief reconciliation note, and a complaint about mutual silence.

To a friend (~372 AD):

I do my duty whenever I greet you with a salutation, and I am glad to acknowledge that the gift of your letters repays me in kind. But there is no need to draw this out further, since true friendship refuses to make a show of itself. What I want from you now is this: please use your letters and an official courier to help the agents of mine to whom I have assigned the purchase of racing chariots from Spain for my son's praetorian games.

I also ask that you confirm by letter the transport permits for the horses that the distinguished Theodorus issued, so that with a change of officials the authority of the favor does not lose its force. I would press harder upon your goodwill with excessive pleading, but with your dignified ears, straightforwardness is more effective -- and modesty grants more willingly what is asked with confidence. Know that I am sparing in my requests now, but I will be lavish in my thanks once they are granted.

---

To Aurelianus:

It pleases me that you so often blame fortune for my failure to write -- it is a sign of your affection that you desire in return what you yourself provide. Yet I must conceal the plan you had privately vowed. I confess I was saddened by your boast of a favor that came to nothing -- unworthy of you and unexpected by me. So rather than risk your noble modesty writing something similar in reply, I chose to swallow my disappointment in silence. Between people who are apart, an exchange of reproachful letters often escalates into ill feeling. Now I return to the habit of plain correspondence, grateful for your goodwill rather than holding you responsible for a mishap. I ask only that you stop thinking my friendship -- which has imposed no burden on you -- has cost you anything.

---

To Alexander (~399-401 AD):

You have no right to blame my silence toward you if you consider your own. In fact, the embarrassment may more justly fall on you: coming to Rome on business many times, you neglected the duties of friendship toward me. My own reason for passing through Aquileia was solely the purchase of wild animals [for games]. I took no offense..."""),

(5063, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~372 AD
Context: A short, warm letter written from Symmachus's villa at Formiae on the coast, inquiring after an elderly friend's health.

You will perhaps accuse me of a long silence. I would rather you not attribute this delay to negligence. The unbroken stretch of a long journey kept me from writing. At last I have reached the shore at Formiae [modern Formia, a coastal town between Rome and Naples, a favorite retreat of the Roman elite], which would be all the more pleasant if we could enjoy this place together. But since your years and your health do not permit it, I ask at least to be informed by an exchange of letters how much strength you have added to your frame. I have no doubt that your temperance and the other safeguards of a well-maintained old age are serving you well. Farewell."""),

(5426, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~373 AD
Context: A fragmentary letter about grain requisitions harming the people of Apulia, combined with travel plans involving a friend named Symmachus.

While you are tending to the troubles of the provincials and extending a healing hand to those in distress, a more severe crisis has struck the people of Apulia [the southeastern region of Italy, modern Puglia]. Grain is being demanded from them on the basis of an inflated reputation for productivity -- grain that will be drained from the province without actually serving the public interest. For how can such a large harvest possibly be readied when the year is already turning toward winter?

If you have the means to speed your journey to Campania, let me know so that I may wait for you briefly. Or if a more pressing matter has changed your plans, inform me of that as well, so that our Symmachus, who has been idling on the shore at Formiae for some time, may hurry back with me to our studies. Farewell."""),

(5129, """From: Quintus Aurelius Symmachus, Roman Senator
To: Minervius (multiple short letters)
Date: ~373-397 AD
Context: Several letters to Minervius on topics ranging from the proper form of address between friends, a recommendation for a treasury official, an appreciation of a personal visit, and the sending of two speeches for critique.

To Minervius:

...from that point, let your concern for me look in my direction. But it is not my place to dictate the form of your letters. I only want you to know that since you are most generous in your praise, it is not enough for me that you praise me -- unless you also put yourself more deeply in my debt. Furthermore, I want to know why, after preserving the old-fashioned custom in the headings of our letters, you abandoned it in the body of the text. Let others be puffed up with the title "Your Sublimity" -- I reject the designation "Your Magnificence." Unless you think me unreasonable for not offering you the same flattering language. Affected love resorts to such words; the true worship of friendship is honest. Plain white garments, not embroidered robes, should clothe our good faith. What use is a lofty register of reverence to me? I would rather be loved by a brother than looked up to.

---

To Minervius (~397-398 AD): Eusebius is a friend of mine and a longtime soldier of the private treasury who has been absent from your service due to prolonged illness. I beg you not to mark him down as a deserter. But the pardon will not hold unless you also add some favor for him. I ask, therefore, that he be ordered to take charge of collecting public debts owed across Etruria [modern Tuscany], so that the zeal of an assignment may erase the offense of his long absence.

---

To Minervius (~397 AD): A greeting from you always brings me joy, but especially when it is entrusted to friends to deliver in person. A personal envoy adds things worth asking about that go beyond the written page, and reports to the ear what the letter could not convey. Just now, for example, after delivering your letter, your man Sebastius gave me -- when I eagerly asked how you were doing -- a vivid picture of your presence. He in turn will tell you whatever you wish to know about my leisure, for he found me at my Laurentine estate [Symmachus's coastal villa near modern Castel Fusano, south of Rome], clinging to rural quiet. What should I pursue more eagerly -- I who must sometimes mend my health, often avoid the crowds, and always cherish the innocence of literature?

---

To Minervius (~396-397 AD): I have no confidence in my own style or talent, but your kindness provokes my daring. I have therefore sent two short speeches of mine for your learned judgment. One concerns the son of Polybius and arose from a recent case. The other was drafted some time ago when the matter was being debated in the Senate, and has now been expanded into a more substantial work. Its subject is the rejected censorship, which the authority of the entire Senate drove away at the time. Do not be surprised that so weighty a body refused the office of censor -- you will find in my speech serious reasons for avoiding that power."""),

(5162, """From: Quintus Aurelius Symmachus, Roman Senator
To: Hephaestion (or Effectio)
Date: ~373 AD
Context: Symmachus explains why he could not attend a consul's inauguration, and sends copies of important documents to his brother for safekeeping.

I was not lacking in the desire to set out on the journey, but the late summons left too little time to arrive, and so it seemed more proper to ask for forgiveness than to show up after the consul's ceremonies were over. On this matter I long ago sent the fullest letters both to our most merciful lord the emperor and to the others who wanted me to attend, though Festus the courier is still delaying their dispatch by his slowness to depart. And because I fear that what I have written may either be suppressed and hidden, or opened and tampered with by rivals, I have decided to send copies of everything to you, my lord and brother. It will be a mark of your affection to write back faithfully about all of it. I will also send you documents containing domestic concerns; once you have read through them, you will be able to judge what the justice and reputation of better times requires."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Symmachus translations (batch 03)")

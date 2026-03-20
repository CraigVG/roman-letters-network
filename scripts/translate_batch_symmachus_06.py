#!/usr/bin/env python3
"""Batch translate Symmachus letters (IDs 5166, 5069, 5134, 5432, 4979)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(5166, """From: Quintus Aurelius Symmachus, Roman Senator
To: Unknown recipient
Date: ~389 AD
Context: A fragmentary letter header; the text is largely lost.

[This entry preserves only a heading reference to the year 389 AD. The main text of the letter has been lost in transmission.]"""),

(5069, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~376 AD
Context: Symmachus asks a friend to make his excuses to a consul for his absence from the inaugural ceremonies, citing personal grief as the reason.

I wish I could use you as my envoy to the excellent consul to explain and excuse my absence -- if I knew that you yourself would forgive me first. For when I think of the affection you both share for me, I worry that, just as you both love me equally, you will both blame me equally. So who should I call on to defend me in this matter? My own fortune, obviously -- whose defense, though miserable, is entirely just. It is not right for those in mourning to attend joyful ceremonies. Perhaps my sadness would even have dampened your celebration, since it always happens that we take on the mood we read in the faces of our friends. So forgive my absence, and plead my case before the distinguished consul. His honor is something I am proud to celebrate; it is only the festivities of the fortunate that I cannot bring myself to attend."""),

(5134, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend in Spain (name lost)
Date: ~376 AD
Context: Symmachus acknowledges gifts of horses from Spain -- some disappointing -- and presses his friend to prepare better racing teams for his son's upcoming praetorian games.

I reap annual harvests of joy from your letters -- this is the return, these are the riches that Spain pays me. And so, when winter retreats and the sea lanes open to ships, I entrust your letters to the winds -- though this year they reached me often enough but always late. Autumn was already fading when your men touched the banks of the Tiber, and so they were stuck with us after the sailing season had ended. I advise you, therefore, to make the best of their delay with your usual good judgment.

But first I must beg your pardon: of the four chariot horses you gave me the right to choose, I took none. Please believe this abstinence was not contempt but practical judgment -- I found none of them lively under the yoke or gentle under the saddle, so my right of selection went unexercised, held back rather than stirred. The time seems right to press your diligence with a request: for my son's praetorian games, please prepare horses that are noble both in appearance and in speed. Our last two spectacles brought us a fine reputation -- we need to live up to the expectations we have raised. I therefore commend the cause of our glory to your affection, which must, for a little while, bend the gravity of your character and the seriousness of your mind toward pleasing the crowd. The price for the horses will be brought from my household, at your discretion, for the owners of the noble chariot teams..."""),

(5432, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~376 AD
Context: A consolation letter, tactfully avoiding the friend's recent loss and instead praising his son Nemesius.

We should be silent about fortune's blows, lest a belated consolation tear open the scar of past grief. It is better, then, to speak with you about the outstanding -- or rather, the richly promising -- character of our young Nemesius. You have a man most worthy of being esteemed for his large family. I return him to you personally -- something I would have wished to do for both of them. You will judge from the cultivation of his character and learning how much more his studies could have added, had not our concern for your fatherly longing held us back from keeping him longer."""),

(4979, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~376 AD
Context: Symmachus writes about his poor health, bandits making the countryside unsafe, and his wish for a friend to return a mutual acquaintance from a provincial governorship.

I have long been hoping to restore the health of my poor body, if only I could enjoy the healthful air of the countryside. But the suburbs are unsafe because of bandits, and so it is better to waste away in the idleness of the city than to risk the dangers of the rural districts. Yet I feel my health improving through your letters, in which you frequently list the benefits of our lord Theodosius [Emperor Theodosius I] and assure me that your merits are being pressed with great rewards. His tongue will suffice for thanking you; for my part, with my modest talent, I have paid the tribute of praise to the most excellent man -- our partner in wishing well for Flavianus.

But it is time for you to allow that very man to return -- the one for whom we are obligated. How long will you claim the comfort of a magistrate's company in a distant province? There is no excuse involving his wife's pregnancy anymore -- a timely birth has resolved that expectation."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Symmachus translations (batch 06)")

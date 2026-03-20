#!/usr/bin/env python3
"""Batch translate Symmachus letters (IDs 5439, 5440, 5442, 5444, 5082)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(5439, """From: Quintus Aurelius Symmachus, Roman Senator
To: An imperial official (name lost)
Date: ~380 AD
Context: Symmachus writes to a court official whose literary reputation first attracted him, explaining his earlier reluctance to write lest it seem like political flattery.

The fame of your literary cultivation made me desire your acquaintance long ago, but I put off the duty of writing for some time out of modesty -- not wanting to appear to be courting a man at court. This malady of ambition is so common that men who care about their reputation blush on behalf of others' vices. But the cause of my hesitation is now removed, since you honored me by writing first. I will gladly enter the open doors of your friendship, summoned by your kindness, and will make up for the delays of my bashful silence with more frequent letters.

Only look with indulgence upon the efforts of my inadequate tongue, and for the moment lower the standards of an imperial secretary. You mentioned that you have read some of my work -- I ask the same patience. I will not be a stranger to you, nor will I dread a critic who is already familiar with my writing. You have already learned to tolerate everything of mine. We have now also gained a personal acquaintance, which should make you a kinder judge. For friendship is gracious, and its affection softens the severity of judgment into gentler feelings..."""),

(5440, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~380 AD
Context: Two brief letters: one about a financial loss at sea framed with philosophical detachment, and one celebrating the Senate's swift reception of a friend's protege.

...it is up to you whether to call those you say were lost in a storm shipwrecks or mere setbacks. You have in your hands the measure of how much you should credit my goodwill -- however ineffective. Only let our friendship stand and let fortune have no power over it. Set a limit on your losses; I will not withdraw my money from the hazards of your ship.

---

Your guest Faustinus has been received by the most distinguished Senate into its fellowship. The weight of your testimony was so great among us that to delay what you wish would have been an insult. Let him therefore credit the zeal of the entire order to you -- for just as he owes the granting of his rank to imperial favor, he owes the speed of our decree to yours."""),

(5442, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend and officials (multiple letter fragments)
Date: ~381 AD
Context: Fragments of letters including a request about transporting bears for games, and advice to an official about the decayed state of the curia at Formiae.

...bears will shortly be brought from overseas. Please arrange suitable escorts, so that this addition may be applied to your earlier services. Farewell.

---

I am delighted by your diligence and judicial vigor, but the poverty -- or rather destitution -- of the municipal council of Formiae [a coastal town between Rome and Naples] cannot even bear the cure. For just as bodies worn down by long illness cannot endure harsh medicine, so a council thinned in numbers and reduced to poverty is destroyed by the severity of excessive correction. Take, then, the advice of a father who is not defending the council's failings but asking for moderation in the remedy. The public revenues must be considered, and the restoration of the summer baths must be weighed against the city's resources: if there is any surplus after other expenses, let it be directed to the cost of the project. More time must also be given for the restoration, lest..."""),

(5444, """From: Quintus Aurelius Symmachus, Roman Senator
To: Emperor Theodosius I
Date: ~382 AD
Context: The opening of a letter to the emperor praising his military victories, gently chiding him for excessive modesty in his dispatches.

Although I know that modesty is kin to virtue, I nevertheless wished to find in the letters of your highness an abundance befitting the glory of your great achievements. First, because friendship demanded it -- you should not have feared the stain of boasting before one who loves you. Second, because you are as eloquent as you are brave -- you owed it to the deeds you have accomplished to grace them with the honor of your own words. As it is, you send me to the rumor mill and force me to lend my ear to hearsay about you, when the dignity of so great an affair demands a witness of equal stature. But since the character of my mind..."""),

(5082, """From: Quintus Aurelius Symmachus, Roman Senator
To: Ambrose and others (multiple short letters)
Date: ~382 AD
Context: Short letters of recommendation and a note to Ambrose, Bishop of Milan.

My brothers Dorotheus and Septimius, praiseworthy men, carried a single letter from you. But my sense of duty would not allow me to take the shortcut of a single reply: I wanted both to return you double the courtesy of your service, and to give each man individually the honor of a deserved testimonial. Even though our brother Dorotheus has already proven himself to you, I still wish my recommendation to commend him to you even more. I have no doubt this will happen, since an affection rooted in a good heart is capable of growing whenever it is prompted by merit.

---

To Ambrose (~395 AD): Although I believe my earlier letter, in which I asked that the brother..."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Symmachus translations (batch 08)")

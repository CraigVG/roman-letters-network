#!/usr/bin/env python3
"""Batch translate Symmachus letters (IDs 5427, 5065, 5130, 5428, 4975)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(5427, """From: Quintus Aurelius Symmachus, Roman Senator
To: Carterius and others (multiple letters)
Date: ~373-399 AD
Context: Several letters including a property dispute, advice to a friend about forgiving a lawyer's blunder, and other social matters.

To a friend:

I would indeed wish you to be so flush with family funds that you could buy excellent estates, but I would prefer you did it without harm or injury to your friends. I purchased the Postumianensian property in perfectly good legal standing, with no mention of any partnership with you, from its longtime owner. Only now, at your prompting, am I being pressed to give up a possession that is practically established by long tenure -- and whose price was modest enough to make the purchase a pleasure. Therefore, although I could oppose you on legal grounds and resist the wishes of the party whose interests are at stake, I am willing to let you have it: simply pay my man Euscius, who knows the amount, whatever silver I paid the seller -- assuming you would rather buy what is mine than release what is yours from the burden of an obligation.

---

To Carterius:

The duty you owed your father-in-law, whose complaint stung you, you discharged properly by your justified anger at Epictetus. He has been barred from the forum and has paid the price for his reckless tongue -- and if you trust my judgment, he has been corrected by the retribution for his insult. Now, considering your own character and temperament, bend your will toward a forgiving disposition. You know how often lawyers stumble thoughtlessly, and when you presided over the courts -- first as advocate, then as judge -- you regularly overlooked such errors of legal counsel. But since certain people whose offenses go unpunished have now gained prominence through my friend Epictetus's enforced silence, I ask you not to let a man who is more unfortunate than guilty suffer any longer..."""),

(5065, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~373 AD
Context: Symmachus writes to congratulate a friend on receiving a literary or priestly honor, gently reproaching him for not sharing the good news sooner.

I have reasonable grounds for complaint against you, since you were raised to the honor of a literary pontificate [likely a priesthood connected with maintaining sacred records or augural texts] and yet gave me no sign of our shared joy. But I do not want my first letter to be steeped in the bitterness of reproach, lest harsh words tighten your heart. So I set aside my complaints and strike this bargain with you: that from now on you will take the duties of friendship seriously. Let there be between us a constant exchange of worthy courtesies, a steady back-and-forth of familiar letters. For silent harmony is hardly different from hostility. That is why the skill of writing was born -- whether by nature or by human effort -- so that affection would never be mute, and whenever we are apart, written words might serve as a tongue. That is enough for now. I hope that from here on you will give me reason to write back out of gratitude for your kindness, not out of the pain of being slighted."""),

(5130, """From: Quintus Aurelius Symmachus, Roman Senator
To: Q. S. (Quintus Symmachus -- likely a relative) and others
Date: ~373-400 AD
Context: Multiple short letters: a recommendation for Campanian envoys, observations about a friend's son visiting Rome, and a request for help tracking down a runaway slave.

I am duty-bound to recommend to you men of proven worth, since the greatest gift is to place them within the circle of your friendships. Please receive these men, who are easily among the foremost in birth and character, and honor them from the very first meeting with the intimacy of your inner circle. The council of the Campanian provincials has entrusted them with a delegation -- they have matters to present. Justice is the business at hand; my personal concern commends the men. You see there are two reasons to show them kindness: the public fairness of their petition, and a private endorser who is not seeking favors for himself.

---

To Q. S.: I saw our Protadius's son in Rome. His introduction lacked nothing from your family's distinguished reputation except a letter from you. When I pressed him, he replied that his father-in-law had directed him on a route through southern Gaul, with you being far away. I did not readily accept the young man's excuse, but I approved everything else about his character. This much is enough for a father's ears -- I do not want my brief assessment to seem like flattery toward you. At the same time, I am cautious not to diminish your fatherly love for your son, who ought not to need the support of someone else's recommendation with you.

---

To Q. S.: We sometimes grant letters as a courtesy to various people, but this one we have written out of genuine affection for my lord and brother Bassus, who is looking after his sister's interests. His request does not depart from fairness -- indeed, it is fortified by law and justice. He asks that a rebellious slave be brought to him, one whom neither the authority of an imperial order nor the vigor of the Count of Africa could track down, since the man -- aware of his bold crime -- fled the imminent punishment by going into hiding. Since the distinguished Count of Africa is said to have sent you an official report concerning this man's deed and wickedness, it would be an act of both justice and kindness on your part to invoke the imperial judgment on behalf of this distinguished gentleman, so that an innocent household may no longer be terrorized by the murderous schemes of a worthless slave."""),

(5428, """From: Quintus Aurelius Symmachus, Roman Senator
To: Various recipients (multiple short letters)
Date: ~374 AD
Context: A large compilation of brief letters including recommendations for young lawyers, literary admirers, and sons of deceased friends, plus notes on friendship and correspondence.

You used to recommend young lawyers to my court when I presided over tribunals. Now the tables have turned, and it is I who introduce candidates for the bar to your teaching. In this matter you must follow my example: receive those I bring forward with the same easy grace with which I so often accepted those you sent to me.

---

I am fond of those devoted to letters -- not because I have any kinship with such pursuits, but because the practice of the liberal arts, like beauty, gives pleasure even when found in another person. That is why, having met Valentinianus for the first time and found him a man of learning, I thought it my duty to commend him to you by letter, so that my introduction might open the first door of your friendship, while his own life and learning win a deeper one. Farewell.

---

Religious duty compels us to care for the children of our friends, especially when the friendship established with the fathers is augmented by the merits of the next generation. This principle applies directly to the present case. I held the distinguished Lampadius not merely in the fleeting affection that many show until the burial, but I embrace his children -- who thrive on the family inheritance -- with love that has grown over time. I entrust them to you, to be defended from every injury. I ask that, should the need arise, you act as a fair arbiter on my behalf. Gaining this favor will greatly advance both your reputation and my goodwill.

---

We have lost many exchanges of courtesies between us through our mutual hesitation to write. I will not let this shared offense drag on any longer. I take up the pen..."""),

(4975, """From: Quintus Aurelius Symmachus, Roman Senator
To: Flavianus (his close friend)
Date: ~374 AD
Context: Symmachus writes to his dear friend Flavianus about family matters and a dispute involving a mutual acquaintance named Hephaestion, asking Flavianus to show patience.

A familiar letter customarily begins with a general greeting. I am more eager to wish this to you from the heart than to express it formally in writing. So in place of the usual words, let me share things worth knowing. Our children are still staying with their grandmother. Forgive me if the old woman -- tenacious in her affection for those who are young and, for the time being, without your company -- clings to the comfort of her declining years and failing health. We are nonetheless preparing travel arrangements for one of them and a companion for the journey for the other.

I was sorry to hear -- or rather, given the circumstances, I could scarcely believe -- that you regard the post abroad as exile, when you possess the blessings of homeland and the joys of children in the favor of our excellent emperor. So put aside your thoughts of Baiae [the famous luxury resort on the Bay of Naples] and grant your virtue an undistracted calm. Every leisure is gladdened here by your people more than by any idleness. Let us embrace, I urge you, life under a prince who loves service. Farewell.

---

To Flavianus (~382-383 AD): May good fortune smile on my wishes for you, just as I take it hard that our brother Hephaestion -- whom I came to know through you and whose worth I recognized through you -- has somehow fallen into a bitter situation. Because my admiration for your virtues leads me to take his misfortune as my own, given that it matters less to you, I turn to entreaty: I ask you to consider your own reputation and to reflect. Grant this to your friendship, grant it to your own judgment, and do not let your patience fail even if his sense of proportion did. I would not have it appear that you satisfied a certain man who recently returned to Rome -- whose complaint against you only enhanced your reputation -- by showing contempt for a friend. Surely Eusebius, the most eminent of physicians, whom I delivered into your service and who is well suited to soothing offenses, can by now sweeten what is bitter. Of his talents I will guarantee two things: Hephaestion will not lack moderation, nor will you lack consolation. Farewell."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Symmachus translations (batch 04)")

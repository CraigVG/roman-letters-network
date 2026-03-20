#!/usr/bin/env python3
"""Batch translate Cassiodorus letters (IDs 2817, 2864, 2897, 2606, 2645)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(2817, """From: Cassiodorus, on behalf of the King
To: A provincial judge (formula for collecting the bina et terna tax)
Date: ~522 AD
Context: A brief administrative formula ordering the collection of the "bina et terna" taxes -- customary supplementary levies on provincials -- and their transmission to the treasury.

We believe it pertains to the credit of your office if we assign you duties suited to your responsibilities, since a man is rendered all the more pleasing the more occasions for obedience he is shown to have accepted. Therefore, with your office managing the process, you will promptly transmit to the bureaus of the Count of the Sacred Largesses [the chief financial officer of the realm] the bina et terna taxes [supplementary provincial levies on certain goods] that ancient authority decreed should be collected from the provincials, for the current tax year. The entire amount is to be paid in full by the Kalends of March [March 1]. Take care that you are not forced to pay from your own funds what you neglected to collect. It would have been an insult to you if someone else were seen collecting the taxes that the most sacred laws assigned to your jurisdiction."""),

(2864, """From: Cassiodorus, on behalf of King Athalaric
To: Avienus, Praetorian Prefect
Date: ~522 AD
Context: Athalaric appoints a new Praetorian Prefect after dismissing his corrupt predecessor, using vivid metaphors of medicine and weather to explain the change.

It is an endorsement of one's merits to be chosen after a corrupt predecessor has been removed, since the excesses of those who came before are only corrected when an excellent successor is found. Medicine often works through opposites: when vital heat is applied, the pestilent cold retreats. Clouds themselves are swept away by the breath of the winds, and the north wind restores the calm face of the sky that the southern breeze had troubled. In just this way, we removed your predecessor out of love for the general welfare, so that you might arrive as a most wholesome remedy.

Imitate the opposite of what came before and you will have accomplished praiseworthy things. He was hated for his false accusations -- strive to be welcomed for your justice. He was rapacious -- be restrained. The definition of all virtue is brief: avoid what he did. What is truly praiseworthy is what fails the test of his own judgment. Consider, then..."""),

(2897, """From: Cassiodorus, on behalf of King Athalaric
To: All Provincial Judges
Date: ~522 AD
Context: A cover letter distributing the new twelve-chapter edict to all judges, admonishing them that the volume of cases reaching the royal court is proof of their own failure to administer justice locally.

When we provide you to our provinces by annual appointment, with God's help, and there is no shortage of courts distributed across every corner of Italy, we understand that the flood of lawsuits arises from a shortage of justice. It is proof of your negligence every time people are forced to petition us for the benefits of the law. Who would choose to seek so far away what they could see arriving at their own doorstep?

But to strip you of clever excuses and to relieve the provincials of cruel hardships, we have decreed by the terms of an edict certain measures concerning cases that have until now been neglected through the worst kind of inertia. This should increase your confidence in judging rightly and gradually reduce criminal daring. In the customary fashion, see that this is publicly posted at assemblies for thirty days..."""),

(2606, """From: Cassiodorus, on behalf of King Theoderic
To: Johannes, Imperial Agent
Date: ~522 AD
Context: Theoderic orders an investigation into the obstruction of a land-reclamation project near Spoletium (Spoleto), where marshlands were granted to two men for drainage and improvement.

It is deeply unjust for a hardworking man to be cheated of the fruit of his labor, and for one who deserves a reward for his diligence to suffer an unfair loss -- especially in a matter that concerns our own generosity, where negligence must not be tolerated lest we seem to have decreed things of little use.

Some time ago, our generosity granted to the distinguished Spes and Domitius certain tracts of land in the territory of Spoletium [modern Spoleto] that were uselessly occupied by marshy streams. There the vast depth of water had swallowed up the land's charm, rendering it useless. The earth lay shipwrecked, confused by swamp-like torpor, suffering a double loss: it had neither earned the pure waters of clear streams nor kept the honor of solid ground.

We, whose heart is set on changing everything for the better, granted this land to the aforementioned men on the following condition..."""),

(2645, """From: Cassiodorus, on behalf of King Theoderic
To: Faustus, Vir Illustris
Date: ~522 AD
Context: Theoderic grants the distinguished senator Faustus a four-month leave of absence from Rome to attend to his provincial estates, but urges him to return promptly -- reflecting the policy of keeping senators resident in Rome.

It is human custom that people enjoy variety more, and even though they possess exceptional things, anything that satiates eventually breeds boredom. Therefore, since you have been dwelling continuously within the sacred walls, you ask that a leave of absence be granted for the purpose of managing your own affairs. Not that so splendid a residence wearies you, but so that the return may be all the sweeter when renewed.

Accordingly, our devotion grants your illustrious greatness a leave of four months to retire to the province. But see to it that once those months are completed, you hasten back to your proper home. We do not wish Rome's habitation -- which we want to fill with an abundant gathering -- to grow thin by the departure of its residents from the most distinguished city in the world. We judge this to be most fitting for you as well, since a Roman senator can only feel pained by being detained elsewhere. For where is that bond with your ancestors? Where is the..."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Cassiodorus translations (batch 09)")

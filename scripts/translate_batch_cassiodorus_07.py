#!/usr/bin/env python3
"""Batch translate Cassiodorus letters (IDs 2604, 2643, 2747, 2816, 2863)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(2604, """From: Cassiodorus, on behalf of King Theoderic
To: All Goths and Romans, and those in charge of ports and mountain passes
Date: ~522 AD
Context: A dramatic order to hunt down fugitive slaves who murdered their master Stephanus, featuring a remarkable literary digression on vultures and natural law.

We justly detest all crimes, and our merciful hearing condemns everything that is unjust. But the offenses that especially provoke our censure are those polluted by the shedding of human blood. Who could endure that danger was found in the very place of domestic safety -- that the end of a sweet life was discovered where the aid of protection should have been born?

We therefore command by this order that the laws' full severity be applied to the slaves who murdered their master Stephanus with punishable wickedness and even cast his unburied remains aside in contempt. Let those who are provoked by the worst examples be restrained by the sight of punishments. How shameful! A devotion found in birds is absent from the human condition. Even the vulture -- whose life depends on another's carcass, a bird of enormous size -- is not known to attack smaller birds. Rather, it strikes the hawk -- that feathered hunter of other birds' lives -- beating it with its wings, tearing it with its beak, and crushing it with its full weight..."""),

(2643, """From: Cassiodorus, on behalf of King Theoderic
To: Daniel (a craftsman)
Date: ~522 AD
Context: An appointment letter for the official supervising the production and sale of marble sarcophagi in Ravenna -- one of Cassiodorus's characteristically humane reflections on death, grief, and commerce.

It is right that we should look after the just compensation of those who serve our palace, because public labor should be productive. Although service to us is owed freely by right, we should still encourage it through moderate rewards.

Delighted by your skill in your craft -- which you practice diligently in carving and ornamenting marble -- we grant by the present authority that you shall oversee, with reasonable management, the distribution of the stone sarcophagi that are sold in the city of Ravenna for the burial of the dead. Through these, bodies are laid to rest in the earth above, providing no small consolation to the grieving -- since only the souls depart from the world's company, while the bodies do not abandon those who were once their sweet companions in life.

Through this trade, grief becomes a source of profit for some, and by a pitiable turn of fortune, merchants gain from human death. Nevertheless, let there be no unjust pricing under this arrangement, lest the wretched be forced to weep over heavy losses of property amid the bitter pangs of mourning, and bound by an unholy devotion, be compelled either to spend beyond their means..."""),

(2747, """From: Cassiodorus, on behalf of King Theoderic
To: Gudinandus, Saio (royal agent)
Date: ~522 AD
Context: A brief, stern order dispatching a military agent to round up shipwrights from royal estates and force them to report to Ravenna for warship construction.

A man who carries out his orders effectively earns trust for greater things, because tasks are entrusted without hesitation to one who is proven to perform well, and a good record in a second assignment is an honorable endorsement based on the evidence of the first.

Accordingly, by the arrangement of the distinguished Abundantius, Praetorian Prefect, and Wilia, Count of the Royal Patrimony, we order you to proceed to the named province and compel the sailors who have been identified -- both from the royal estates and from other locations -- to hasten to the city of Ravenna by the Ides of June [June 13], in accordance with previous orders and with God's help, so that no delay is imposed on such important commands.

Take care that bribery does not stain you, that shameful negligence does not entangle you, and that you are not crushed under the weight of so great a responsibility collapsing upon you, should you prove unequal to such important tasks."""),

(2816, """From: Cassiodorus, on behalf of the King
To: The Praetorian Prefect (regarding the appointment of armorer supervisors -- formula)
Date: ~522 AD
Context: A brief formula notifying the Praetorian Prefect of a new appointment over the armorer corps.

We have learned from the report of many that the named individual, trained in upright character, is capable of faithfully carrying out what is entrusted to him. Therefore, let your illustrious greatness know that we have chosen him both to command the soldiers in accordance with ancient custom and to direct the armorer craftsmen, so that they may fulfill their duties with such skill that no fault can be found in their work. Although negligence is harmful everywhere, here it strikes especially hard if the instruments of war are neglected. It amounts to treason to deprive the army of what is known to arm it. Your providence will assign them their customary provisions, so that once the excuse of lacking supplies is removed, the necessary work may be demanded more vigorously."""),

(2863, """From: Cassiodorus, on behalf of King Athalaric
To: The Roman Senate
Date: ~522 AD
Context: Athalaric announces a new appointment to the Senate, using extended metaphors of stars, flowers, and fields to celebrate the body's growth.

Although your assembly always radiates with its native splendor, conscript fathers, it is made brighter whenever it is augmented by the light of new offices. The sky itself shines more brilliantly with its countless stars, and from the abundance of its beauty it offers a marvelous sight to those who gaze upon it. It is simply in the nature of things that a wealth of good things gives greater pleasure. Meadows are painted with innumerable flowers; the thicker crop of a fertile field is praised. Antiquity made you noble; we wish the Senate also to be celebrated for its numbers.

This is why we are eager to add to your ranks anyone we find outstanding, wherever they may be. For although the Senate is its own nursery, men are also born from our generosity who may be added to your assembly. Every court office produces candidates for your body, but the quaestorship is truly the mother of a senator, since it springs from wisdom. What is more fitting than for a man who has been close to the prince's counsel to become a member of the Senate? But since a man of prudence is never satisfied with praise given in general terms, his specific qualities should be noted..."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Cassiodorus translations (batch 07)")

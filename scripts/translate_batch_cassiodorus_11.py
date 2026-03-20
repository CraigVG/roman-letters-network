#!/usr/bin/env python3
"""Batch translate Cassiodorus letters (IDs 2646, 2750, 2819, 2866, 2899)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(2646, """From: Cassiodorus, on behalf of King Theoderic
To: Artemidorus, Vir Illustris
Date: ~522 AD
Context: A courteous summons to an elderly nobleman to attend the royal court, couched in the language of honor and friendship.

It is fitting that we adorn our court with noble men, so that their wishes may be fulfilled and our retinue may be graced by the merits of distinguished persons. We therefore summon your greatness by this edict to our presence -- which we have no doubt is most welcome to you -- so that you, who have spent a long life in our company, may be captured once again by the sweetness of our presence. A man hastens to a prince from whom he can expect to find even a mere glance favorable. For one who is permitted to enjoy our conversation considers it a gift..."""),

(2750, """From: Cassiodorus, on behalf of King Theoderic
To: The Roman Senate
Date: ~522 AD
Context: Theoderic announces a new appointment to the Senate, arguing that offices should be matched to cities -- and that eloquent men belong in Rome, the city of letters.

Although care must always be taken in choosing a man to present for your approval -- since the judge whose own verdicts are known to be weighed is himself submitted to scrutiny -- we especially wish to associate with your assembly those offices that are affixed to the citadels of Rome like precious gems. For where more fittingly should an eloquent man advance than in the city of letters, so that he may display his merit where he nourished his talent? Every good thing is suited to its proper place, and even praiseworthy qualities lose their luster unless they are set in a fitting location..."""),

(2819, """From: Cassiodorus, on behalf of the King
To: Treasury clerks dispatched for bina et terna collection (formula)
Date: ~522 AD
Context: Instructions to treasury clerks being sent to a province to assist with tax collection.

We have no doubt you are most grateful when reminded to fulfill the duties you have undertaken, because what is truly burdensome is for a soldier to live in idleness when his earnings come from service and his honor from a royal assignment. A man left to ignoble torpor is as good as one who has unbuckled his belt. Therefore, we order you to proceed to the named province for the current tax year, so that together with the judge and his staff, by the Kalends of March [March 1], the amounts owed from the bina et terna taxes..."""),

(2866, """From: Cassiodorus, on behalf of King Athalaric
To: The Roman Senate
Date: ~522 AD
Context: Athalaric heaps further honors on Cyprianus, arguing that repeated distinctions make a man more glorious, like multiple victories in athletic games.

If a man who has obtained a single royal appointment deserves your favor, conscript fathers, how much more must the distinguished Cyprianus merit it -- who should become all the more pleasing to you with each successive office he receives from us? In the stadium, a runner is glorified by a greater number of crowns; at the Olympic games, the chariot driver is ennobled by frequent palms. So too, even in lesser matters, a man grows more glorious when prizes are heaped upon him again and again. About a man's first advancement there can be some hesitation, as many..."""),

(2899, """From: Cassiodorus, on behalf of King Athalaric
To: Paulinus, Consul
Date: ~522 AD
Context: Athalaric writes to the newly appointed consul Paulinus, celebrating the consulship as the crowning honor of Roman civilization and defending his choice against any detractors.

Human conduct would wander in confusion if crime had no terrors and virtue no rewards. But since both are enclosed within their proper boundaries and limits, it is wrong to question a man who has been chosen by the judgment of his prince. We decree nothing out of hatred, nor do we praise anything seduced by favoritism. Our choice springs from merit, and a man draws closer to the royal heart in proportion to his devotion to worthy pursuits. Do not fear the absent..."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Cassiodorus translations (batch 11)")

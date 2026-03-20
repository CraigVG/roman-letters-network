#!/usr/bin/env python3
"""Batch translate Cassiodorus letters (IDs 2896, 2921, 2605, 2644, 2748)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(2896, """From: Cassiodorus, on behalf of King Athalaric
To: The Roman Senate
Date: ~522 AD
Context: Athalaric announces a major edict of twelve chapters, modeled on Roman civil law, to be publicly read in the Senate and posted throughout Rome.

Blameworthy excesses often provide the occasion for praiseworthy commands, and in a wonderful way the workings of justice are born from occasions of injustice. Justice keeps silent when no offense cries out, and the prince's ingenuity rests idle when no complaint has provoked it.

Driven by the voices of complainants and prompted by the petitions of the people concerning various matters, we have drafted in an edict of twelve chapters -- just as civil law is known to have been established [an echo of the Twelve Tables, the foundation of Roman law] -- certain measures necessary for the peace of Rome, to be preserved for all time. Once observed, these should not weaken but rather strengthen the remaining body of law.

Let these be read before the splendor of your assembly, and for thirty days let the Prefect of the City post them in the most frequented places in the customary solemn manner..."""),

(2921, """From: Cassiodorus, on behalf of King Theodahad
To: Emperor Justinian
Date: ~522 AD
Context: Theodahad thanks Justinian for welcoming his accession and assures the Eastern emperor of his desire for peace, using the language of shared Christian kingship.

We give thanks to God, to whom the peace of kings is always welcome, that you have declared our accession most pleasing to your clemency. It is clear that you can love one whom you are glad to see reach the summit of kingship. This is how a man should be received who presumed to be elevated through your favor. Grant the world, then, the example of your benevolence, so that all may understand how much a man advances who commends himself to you with pure affection.

You do not seek petty quarrels among kingdoms. You take no pleasure in unjust contests that are the enemies of good character, because it is clear that you desire nothing that cannot enhance your reputation. How could you refuse peace when it is sought, when out of your inborn devotion you are accustomed to impose it even on angry nations? The blessings of your concord..."""),

(2605, """From: Cassiodorus, on behalf of King Theoderic
To: Wiligis, Saio (royal agent)
Date: ~522 AD
Context: An order to requisition grain barges from Ravenna to supply the royal court in Liguria -- a practical snapshot of late antique logistics and food supply.

Everyone should gladly contribute what they see can serve the public good, since the limbs must feel what affects the whole body. We therefore decree by the present order that you are to find as many grain barges as you can in the city of Ravenna, load them with state grain, and bring them to us, so that the public food supply, relieved by this provision, need not suffer the hardship of shortage.

Let Ravenna return the abundance to Liguria that it has been accustomed to receive from it. For the city that hosts our presence ought to find relief from many quarters. Our court draws crowds of attendants, and as people rush to receive our favors, the supply that the populace needs is stretched."""),

(2644, """From: Cassiodorus, on behalf of King Theoderic
To: Triwila, Saio, and Ferrocinctus, Imperial Agent
Date: ~522 AD
Context: Theoderic orders two officials to investigate the case of Castorius, a man whose property was seized by the powerful prefect Faustus, and to restore it -- a window into the abuses of late Roman power politics.

Among the glorious concerns of the state that we continually review in our thoughts with God's help, close to our heart is the relief of the humble -- so that we may raise the shield of our devotion against the arrogance of the powerful, and no brazenness whose purpose is to trample the proud may have any standing with us.

Moved by the tearful calamity of Castorius, who has been crushed until now by the ruinous spite of various people, we take this opportunity to issue salutary decrees, so that the help of our devotion may prove stronger than the wicked cunning of the unscrupulous. We therefore decree by the present authority that if the distinguished Prefect Faustus has either burdened the properties Castorius held with legal claims or detained them through private appropriation, the estate together with another of equal worth must immediately be restored to him under your supervision..."""),

(2748, """From: Cassiodorus, on behalf of King Theoderic
To: Aliulfus, Saio (royal agent)
Date: ~522 AD
Context: A companion order to the previous shipbuilding directives, sending a military agent to cut timber along the Po River for warship construction, with strict instructions to respect private property.

We have learned that timber suitable for building warships can be found along both banks of the River Po. We therefore assign you by the present order to proceed without delay to the designated locations with the craftsmen, in accordance with the arrangements of the distinguished Abundantius, Praetorian Prefect, and Wilia, Count of the Royal Patrimony. Whether the timber is found on royal estates or on private land, see to it that it is procured without any delay, since we believe no one should find it burdensome to provide what is being prepared, with God's help, for the common good.

We do wish, however, that you carry out your orders in such a way that nothing is zealously sought out to the harm of the landowner. Only what is needed for our purposes should be taken. Nothing should be demanded from an owner that is not afterward acknowledged as received for public use. We order wild timber to be cut..."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Cassiodorus translations (batch 08)")

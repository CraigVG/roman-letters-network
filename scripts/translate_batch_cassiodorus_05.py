#!/usr/bin/env python3
"""Batch translate Cassiodorus letters (IDs 2861, 2894, 2919, 2603, 2642)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(2861, """From: Cassiodorus, on behalf of King Athalaric
To: The Roman Senate
Date: ~522 AD
Context: Athalaric announces the appointment of a new official, praising his family's illustrious service and the candidate's own distinguished brother, while delicately noting that Theoderic had somehow overlooked rewarding this man.

The candidate before you, conscript fathers, possesses such an abundance of merits that we fear he will be thought promoted too late rather than not approved at all. For while our grandfather of divine memory sought out the finest men, a kinder fortune preserved this one unrewarded for us. He served that prince, devoted himself to him with great loyalty, and is known to have been left without any recompense by a most generous master. I believe the reward for his service was merely deferred, so that the opportunity for generosity might be more fitting for us -- for our devotion is linked to our grandfather's by the law of nature. It is right for an heir to pay what was owed to the benefactor of his predecessor. Why should our generosity delay when the man's own noble custom urged him forward?

His father was famous in arms and conspicuous for the highest nobility of character -- a man whom fierce wars did not repel and whom peaceful times would celebrate. Strong in body, fortified by friendships, he bore the dignity of an earlier age. Even in the troubled times of Odoacer, he was enriched with distinguished honors. He was considered outstanding in an era that lacked a worthy prince.

But why do we reach back to the ancient nobility of his forebears, when the nearby brilliance of his brother's reputation shines so brightly? To have been connected to that man -- I will not say by mere proximity, but even by friendship..."""),

(2894, """From: Cassiodorus, on behalf of King Athalaric
To: Salventius, Prefect of the City of Rome
Date: ~522 AD
Context: Athalaric orders the release of Romans imprisoned on mere suspicion of sedition, noting that Pope John and leading officials have interceded on their behalf.

If ancient emperors adorned Rome's walls for the joy of its people -- so that those uniquely distinguished citizens should have nothing in common with the rest of the world -- it would be a crime for them to endure prolonged grief amid so many delights. The joy of that city is a universal prayer: the rest of the world must rejoice whenever the head of the world is happy.

We have learned from the report of the apostolic Pope John and our leading officials that certain Romans -- imprisoned on mere suspicion of sedition -- have been worn down by such prolonged custody that the entire city has contracted grief from their unending suffering. Neither the festivity of holidays nor the prestige of their own names -- which carries the greatest weight with us -- has come to their aid. This displeased us because of the harshness of the situation: men who are reported never to have been convicted at trial have endured the torments and sufferings reserved for the guilty.

We therefore advise your greatness by the present orders to find them wherever they may be and release them without delay. Even if they are shown to have been entangled in some offense, we decree that through the intercession of the persons named above, they are now free from fear. If, however, they believe they have suffered torment while innocent, we grant their grievances..."""),

(2919, """From: Cassiodorus, on behalf of King Theodahad
To: The Roman People
Date: ~522 AD
Context: Theodahad assures the Roman people of his goodwill, announcing that oaths have been administered as they requested, and asking for their loyalty in return.

Learn, citizens, with what firmness your prince has loved you: tried by harsh circumstances, he has refused to let you remain anxious. We were unwilling to defer your hopes any longer, since we always wish you to rejoice in the highest prosperity of the state. Your security is our glory, and we truly welcome it with gratitude when we sense that you have joy.

Therefore, yielding to your petitions, we have decreed that oaths be administered to you through the persons named, so that you may know the mind of your king and not be allowed to wander in false suspicions when you can clearly grasp what to believe about your prince.

Consider what benevolence you see being shown to you, when the one who swears is the one who cannot be compelled. We know that we have been given to all as a remedy. We do not disdain to heal our subjects, and so, although it seemed beneath our dignity, we have willingly agreed to do what we see the general public has wished. Understand how much your affection seems to lay upon us: we bind ourselves to you by an oath -- we who are reminded by sacred readings to keep promises made by a mere word. Now show your devotion; pray constantly to the heavenly majesty that the peaceful times we want you to have may come about through divine favor..."""),

(2603, """From: Cassiodorus, on behalf of King Theoderic
To: Gudila, Bishop
Date: ~522 AD
Context: A letter about the legal status of curials (city councilors), reminding a bishop that men born into the curial class cannot escape their civic obligations by joining the clergy.

The venerable authority of ancient laws dictates that a man born a curial [member of the city council, responsible for local governance and tax collection -- a hereditary obligation in the late Roman Empire] cannot in any way depart from the duties of his birth, nor be drawn into any other public office if he was born into that condition. If the laws even forbid them to transfer to higher offices, how much more contrary to the law is it for a curial of the state to have shamefully lost his freedom through servitude and to have sunk to the lowest condition -- he whom antiquity called a member of "the lesser senate"?

Therefore, let your reverence know that the citizens of Sarsena [modern Sarsina in Romagna] have claimed that your church is unreasonably trying to retain their colleagues. Your wisdom should therefore examine the truth of the matter, as befits your integrity, and investigate what is brought before you in complaint. If the petitioners' claims are supported by the truth, allow the men to return to their curia to fulfill their civic duties.

If, however, you believe your clergy has some legitimate claim over them, send by all means a well-briefed representative to our court, who may respond to the arguments of the opposing party. But if you are uncertain about the nature of the case, it befits priestly standards to investigate the justice of the matter yourself before the dispute arises, rather than come away defeated from a judgment. For such..."""),

(2642, """From: Cassiodorus, on behalf of King Theoderic
To: Gemellus, Vir Sublimis (Vicar of Gaul)
Date: ~522 AD
Context: Theoderic orders Gemellus to restore the confiscated property of Magnus, a Roman nobleman who fled barbarian rule and returned to Roman territory.

Those who chose our clemency deserve good things, so that we may prove through their advancement that their decision was the right one. And if such men deserve to be provided for by public generosity, how much more fitting is it for them to possess their own property -- which is nothing more than common justice?

The distinguished Magnus, rejecting association with the enemy and remembering what he was born to be, repatriated to the Roman Empire. During his absence, it is said that his property was allowed to be lost. We therefore decree by the present order that he shall recover without any delay everything he can prove belongs to him -- whether in land, or in urban or rural slaves, or in any other property lost by any means. He shall retain by our authority the full right of ownership over everything he once held. We do not wish him to face any legal challenge concerning property that belonged to him by longstanding possession -- a man to whom it is our very intention to grant even new things."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Cassiodorus translations (batch 05)")

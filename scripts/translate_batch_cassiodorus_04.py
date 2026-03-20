#!/usr/bin/env python3
"""Batch translate Cassiodorus letters (IDs 2893, 2918, 2602, 2641, 2814)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(2893, """From: Cassiodorus, on behalf of King Athalaric
To: Salventius, Prefect of the City of Rome
Date: ~522 AD
Context: Athalaric orders the anti-simony decree to be published to the Senate and people, and inscribed on marble tablets to be displayed at St. Peter's Basilica.

It is a welcome thing to publicize what will benefit everyone, so that what might have been a private wish becomes a universal joy. Concealing benefits, on the other hand, is itself a kind of injury. Some time ago, the most distinguished Senate -- wishing to remove the stain of a most shameful suspicion from its own splendor -- wisely decreed that no one should pollute himself with abominable greed during the consecration of a most blessed pope, with penalties established for anyone who dared attempt such a thing. And rightly so, because the true merit of the elect is only sought when money is not.

We have praised and strengthened this initiative by sending our own decrees to the most blessed pope -- decrees that surpass the earlier measures in their brilliance -- so that profane ambition may be removed from the honor of the holy Church. We wish you to bring this to the attention of the Senate and Roman people without any delay, so that what we desire everyone to uphold may be fixed in the hearts of all.

Moreover, so that this imperial benefaction may endure both for the present age and for ages to come, we order that both our decrees and the Senate's resolutions be fittingly inscribed on marble tablets and placed before the atrium of the Blessed Apostle Peter [St. Peter's Basilica] as public testimony. For it is a worthy place -- one that will both display a glorious reward for its guardian and present to future readers what may stand to the praise of all..."""),

(2918, """From: Cassiodorus, on behalf of King Theodahad
To: The Roman Senate
Date: ~522 AD
Context: Theodahad addresses the Senate with elaborate assurances of his clemency, ordering oaths to be administered to certain individuals and framing his mercy as something freely chosen rather than compelled.

Our devotion, conscript fathers, is a most imperious thing -- since we are conquered by our own will, we who are bound by no one else's terms. For though, with God's help, we are capable of everything, we believe only praiseworthy things are permitted to us. You know, wise men, the meaning of our words. Recognize now the clemency that you should have expected from us all along. See -- we do not even allow those to be anxious whom we were thought to threaten. This is how a prince should overcome a grave suspicion: this is how he should have acted who wished to be guilty of no wrong.

We have accordingly decreed that the oaths you requested shall be administered to the persons named by our authority. This was not difficult for one who intends to govern well, because in granting you security, we were adding nothing to what we already intended. We were going to act in the very manner we now promise, because we owe this to God, not to any man. For we who have studied the kingdoms of old through sacred reading -- what else can we desire but what we perceive has pleased the divine in others? God himself is the rewarder of all good things: whatever kindness we show to our subjects, we are confident that he repays to us.

Therefore, now that you have obtained security, show the faithfulness of your conscience, because after such assurances, clemency is returned..."""),

(2602, """From: Cassiodorus, on behalf of King Theoderic
To: The Honorati, landowners, defenders, and curials of the city of Tridentum (Trento)
Date: ~522 AD
Context: A brief fiscal order ensuring that a land grant to the priest Butilanus does not create a tax burden for the other landowners of Trento.

We do not wish our generosity to be harmful to anyone -- so that what is given to one person is not charged to another's account. Therefore, know by the present order that for the portion of land we have granted to the priest Butilanus through our largesse, no one is required to pay the fiscal tax obligation. Rather, whatever amount in gold solidi is comprised in that assessment, you should know that you are relieved of it from the payments on the tertiae [the "thirds" -- the share of land or tax revenue allocated to the Gothic settlers under Theoderic's settlement policy]. We do not wish anyone to be charged for what we have remitted to another through our generosity, lest -- and it would be an outrage to say it -- the gift given to one who has served well should become an innocent person's loss."""),

(2641, """From: Cassiodorus, on behalf of King Theoderic
To: All the provincials of Gaul
Date: ~522 AD
Context: A remarkable proclamation to the newly reconquered Gallic provinces, urging them to embrace Roman law and customs again after years under other rule.

You should gladly obey Roman custom, to which you have been restored after so long -- for the return is welcome to a place where your ancestors are known to have prospered. Therefore, recalled by God's grace to your ancient liberty, clothe yourselves in the manners of the toga. Cast off barbarism; throw away the cruelty of your hearts, because under the justice of our times it does not become you to live by foreign customs.

With the inborn gentleness we bring to your needs -- and may this be said with good fortune -- we have thought it right to send the distinguished Gemellus, vicar of the prefects, a man tested and proven to us in loyalty and diligence, to restore order in the province. We trust he can do no wrong, since he knows full well how seriously we take it when people offend us.

Obey his arrangements, which proceed from our orders, because we trust he will decree what is beneficial for you. Receive the ways of law gradually. Let what is good not seem burdensome merely because it is new. What could be more fortunate than for people to rely on the laws alone and to fear nothing else? Public law is the surest comfort of human life: the help of the weak, the bridle of the powerful.

Learn to love the source of both your security and the advancement of your conscience..."""),

(2814, """From: Cassiodorus, on behalf of the King
To: The new Superintendent of Lime Production (formula)
Date: ~522 AD
Context: A formula for appointing the official in charge of lime production for Rome's construction projects -- one of Cassiodorus's characteristically detailed letters about practical crafts and trades.

It is a glorious service through which Rome is known to be adorned, since a man advances with us in proportion to what he has contributed to the City through his own labor. There is no doubt that quickite -- white as snow and lighter than sponges -- is the most essential material of all construction. The more it is dissolved by the burning of fire, the more it strengthens the solidity of walls: a stone that dissolves, a soft rock, a sandy mineral that actually catches fire more intensely when drenched with enormous quantities of water. Without it, neither dressed stone is firm nor the fine grains of sand solidified. Therefore it deserves the greatest attention, since it is known to hold first place in Rome's buildings.

Accordingly, our authority appoints your proven diligence to oversee the production and distribution of lime from the present tax year, so that it may be supplied in abundance for both public and private construction, and the spirits of all may be encouraged to build when they see that what they need is readily available. You will claim the privileges of your office in accordance with our orders, so that you may earn greater rewards if you carry out what has been entrusted to you well."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Cassiodorus translations (batch 04)")

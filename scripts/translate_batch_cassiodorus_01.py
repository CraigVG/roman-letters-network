#!/usr/bin/env python3
"""Batch translate Cassiodorus letters (IDs 2786, 2811, 2858, 2891, 2916)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(2786, """From: Cassiodorus, on behalf of the King
To: The Roman Senate
Date: ~522 AD
Context: A formula (template letter) for enrolling new members in the Senate, comparing the cultivation of the Senate to the grafting of trees.

We would like the Senate's distinguished chamber to be filled by its own natural increase, and for its offspring to grow so abundantly that -- rare as it is for ambition to be satisfied -- it might actually content the hopes of its own members. But a truly devoted cultivator does not stop at hoping: he seeks to add still more to that great number. A diligent farmer anticipates the heavenly rains by watering his seedlings before they have earned the showers they need. Even the gardener who strives to improve the fruit of his trees introduces grafts of different stock, so that by multiplying the sweetness of his produce he may plant a pleasing variety in his orchards. In the same way, we wish to bring the most delightful virtues into the fold of the Gabine cincture [the distinctive way of wearing the toga that marked a Roman senator].

But this cultivation is quite different from that of trees. With trees, something thought superior is grafted in: foreign stock is brought to the existing tree so that it may take on the newcomer's sweetness. With you, however, raw material is offered so that it may improve. For though fire shines brightly at night, it appears dim when set beside the sun. This is why nothing can be brought to your order that seems truly exceptional unless it is also enhanced by membership itself. Therefore, let the Senate receive as its new light this man -- conspicuous in the splendor of his birth and wisely kindled by the fire of his intellect. Until now he has been distinguished by his own merits alone; henceforth he will shine with the luster of your company. Open the chamber, receive the candidate: he was already destined for the Senate from the moment we conferred upon him the dignity of the broad stripe [the laticlavium, the wide purple stripe on the toga marking senatorial rank]. Public fathers must be generous, for the title "father" owes its meaning not merely to one's own children but to a concern for the common good."""),

(2811, """From: Cassiodorus, on behalf of the King
To: The Count of Ravenna (appointment formula)
Date: ~522 AD
Context: A template for appointing the Count of Ravenna, the official responsible for managing the port city's shipping and commerce.

If a position should be judged by its labors, and if praiseworthy attention to public business earns favor for the man who serves generously, then your office deserves the highest regard -- for its own demands are known to remove any delay from our orders. Everyone knows how quickly you arrange a vast fleet of ships at the briefest notice. Hardly has the request been written by the officers of our palace before you have already carried it out with the greatest speed.

Indeed, amid the frantic haste of departures, one man can barely notice what you manage to accomplish with remarkable energy. Collect the customary services from merchants, but do not demand excessive levies or abandon them to profiteering. Maintain a standard that does not burden the workers, so that by handling contentious matters without complaints, you may earn still greater rewards from our judgment.

Accordingly, our serenity grants you the countship of Ravenna for the current tax year [indiction]. Take up both the privileges and the labors of your office. Govern your staff with a sense of fairness. Anyone placed in charge of public business always finds opportunities both to harm and to help. But since your administration operates among ordinary people, it must be weighed with corresponding evenness, because the man who governs those of limited means ought above all to maintain balance. The wealthy barely feel their losses, but the poor are wounded by even a small expense -- since a person known to possess little seems to lose everything from even a modest injury."""),

(2858, """From: Cassiodorus, on behalf of King Athalaric
To: The Roman Senate
Date: ~522 AD
Context: Athalaric announces the appointment of a new quaestor, Ambrosius, praising the importance of eloquence in the office that drafts royal communications.

Receive, conscript fathers, the appointment that marks the beginning of our reign. First decisions are always scrutinized more closely, because people believe the sequel will match the start. No one expects a ruler to be careful later if he is not seen guarding his reputation from the very first. A prudent gardener strives to fill his plot with fruitful seedlings, so that plants tended with painstaking labor will yield the harvest he desires. How much more fitting that a kingdom should be planted with the beauty of peace from its very beginning, lest it look like an untilled field!

For this reason, we decided to give the quaestorship [the senior legal and literary office that drafted all royal edicts and correspondence] as a kind of doorway through which the high honors to come might proceed in fitting order. You certainly know the candidate -- our words about him are recent. For when the death of our grandfather of glorious memory [Theoderic the Great, d. 526] filled his subjects' hearts with grief -- since a good thing lost is loved all the more in the seeking -- it was through this man that the welcome news of our accession and your security was made known to you. See what standard of justice we bind ourselves to for the future: we have made the very man who promised the preservation of justice into the guardian of your laws.

He came before you as an eloquent and distinguished orator, pleasing even in his appearance, and all the more delightful to hear. Court officials should be such men -- their natural gifts evident in their bearing, their character recognizable at a glance. A man whose only distinction is his tongue is often despised when silent; but the man whose calm spirit is matched by a serene countenance is always held in honor.

It would be pointless to praise eloquence in a quaestor, since he is specifically chosen for the purpose of enhancing the age's reputation through the quality of his words. Other judges are entrusted with collecting provincial revenues; others are given custody of the private treasury. But in the quaestor are lodged the marks of the court's fame, from which a reputation spreads across the entire world. We have thought it right to remind you of all this, conscript fathers, so that you may believe we seek the sort of men whose appointment serves both our glory and your security. Recognize, you who are learned, the good intentions of your prince: place your confidence in advancement, you who are known to possess literary knowledge. It is the mark of extreme laziness to sit idle when one knows the ruler has invited merit to rise.

Therefore, conscript fathers, receive the distinguished Ambrosius, adorned with the honor of the quaestorship, with your customary goodwill. No one should doubt a man who has already earned your order's approval in his first office."""),

(2891, """From: Cassiodorus, on behalf of King Athalaric
To: Gildila, Count of Syracuse
Date: ~522 AD
Context: A detailed reprimand to the Gothic military governor of Syracuse, ordering him to stop abusing Sicilian provincials through extortion, seizure of estates, excessive court fees, and market manipulation.

The provincials of Sicily have informed us in a petition that your authority has been doing certain things that damage their fortunes. We have taken this matter lightly for now only because the petitioners themselves did not wish past offenses to be punished. After all, a charge that the accuser himself is willing to forgive is clearly questionable, and a man whom his own complainant prefers to pardon cannot rightly be struck down. But to prevent unjust suspicions from arising in the future, we decree by the present order the following rules to be observed at all times, so that the petitioners may have nothing to fear going forward and you may not stumble through ignorance into the offenses alleged.

First: money is said to have been extorted from various provincials for the repair of city walls, yet no construction has actually risen from the promised work. If this is confirmed, either the walls must be built for the people's defense from those funds, or each person must receive back what was improperly taken. It is utterly absurd to promise fortifications and deliver nothing but devastation to the citizens.

Second: you are said to be seizing the estates of deceased persons under the name of the treasury, claiming them as lapsed property [bona caduca -- property with no legal heir, which fell to the state] without any regard for justice -- when your authority in this area extends only to foreigners who die without any testamentary or legal heir. It is outrageous for property to be confiscated in our name through injustice when we ourselves have not ordered it.

Third: the provincials groan that they are burdened with such excessive court summons fees that the cost of being hauled before a judge nearly equals what a convicted debtor would lose. A judge's summons should represent hope for justice, not a penalty. A judge is rightly suspected when people suffer losses before they even get a hearing. We therefore decree that court officers may collect only what our grandfather of glorious memory specifically established as fees proportional to the rank of the persons involved. Fees must have limits: if they exceed the balance of fairness, they lose the right to be called fees at all.

Fourth: if a summons is issued on your own authority -- in those cases and for those persons where the edicts have authorized your involvement -- the officer shall receive half the fee that would be owed for a royal summons, since it is inconsistent with justice for an officer sent by you to receive as much as is offered out of reverence for a royal command.

Fifth: anyone who violates this most salutary decree shall be compelled to restore fourfold what was taken, so that what was lost through greed may be punished by the harshness of the penalty.

Sixth: the edicts and orders of our grandfather of glorious memory that were sent to Sicily for the correction of public conduct shall be obeyed so strictly that anyone who, driven by bestial impulses, attempts to break the protection of these commands shall be held guilty of sacrilege.

Seventh: you are said to be summoning the cases of two Roman citizens to your court even against their will. If you know you have done this, do not presume to do it again -- lest in trying to claim jurisdiction you do not possess, you find yourself acquiring guilt instead. You should be the first to remember the edict, you who prefer that others follow the rules you set. Otherwise your entire authority to judge is stripped away if you yourself fail to uphold the very rules you enforce.

Let ordinary judges retain the full power of their offices. Let the lawful population attend their proper courts. Do not resent the jurisdiction of others. The glory of the Goths is the preservation of civilized order [civilitas -- the key concept in Theoderic's ideology, meaning that Goths would protect but not interfere with Roman civil institutions]. Your reputation improves the fewer litigants appear before you. Defend the law with arms; let the Romans litigate in the peace of their laws.

Eighth: you are accused of seizing goods transported by ship and of using your detested greed to fix prices artificially low. Even if the charge is not proven in fact, the rumor is not far from suspicion. Therefore, if you wish to dispel such talk -- as you should -- let the bishop of the city and the people stand as witnesses to your integrity. What is purchased must please everyone, since it affects everyone's livelihood. Prices must be set by common deliberation, because commerce forced on the unwilling is no commerce at all.

We have thought it right to admonish your sublimity with this order, because we do not wish to be harsh with those we love, and we will not tolerate sinister reports being made about the men through whom we expect others' conduct to be corrected."""),

(2916, """From: Cassiodorus, on behalf of King Theodahad
To: The Roman People
Date: ~522 AD
Context: Theodahad addresses the Roman populace, urging loyalty and calm after what appears to be a period of unrest or suspicion toward Gothic authorities.

Although it is natural for you to love your rulers with a pure heart and to act in such obedience that you may keep the king's favor, it has always been the particular mark of your ancestors that they were joined to their princes as limbs are joined to the head. What return can a people make who are defended with the greatest effort, whose daily life is protected, except to love above all else those through whom they are known to possess everything?

Let it be far from our times that we should find anything in you deserving of our anger. The loyalty that has sustained you until now should show itself all the more clearly. A fickle, deceitful, seditious people is no fit description of the Roman nation. Bad character is the opposite of your very name. Yet it is remarkable that we must remind you of a dignity you have always possessed by instinct. Let no foolish suspicions, no shadow of fear, disturb you. You have a prince who out of devotion hopes to find in you something to love. Confront your enemies, not your defenders. You should have invited our help, not rejected it.

But perhaps that reaction belongs to those who lack the wisdom to see what is in everyone's interest. Return to your better judgment. Did any unfamiliar sight of a foreign people frighten you? Why were you afraid of those you have always called family? They were hurrying to you, leaving their own households behind, worried about your safety more than their own. When, I ask, was such a reception ever given to those who deserved the reward of salvation?

You should know that, as far as we are concerned, we pray day and night without ceasing that what was nourished in the time of our forebears may, with divine help, increase under our rule. For where would a king's reputation be if we allowed you -- heaven forbid -- to suffer? Do not imagine things that you do not see us doing. Rather, if anyone has been weighed down by some injustice, let him not lose hope in a good conscience, since we are eager to lift up those we find devoted to upright conduct. We have also entrusted certain things to be communicated to you by word of mouth through our envoy, so that, sensing our goodwill toward you in every respect, you may be devoted in constant obedience and sincere prayer, as is fitting."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Cassiodorus translations (batch 01)")

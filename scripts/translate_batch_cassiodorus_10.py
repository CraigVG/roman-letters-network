#!/usr/bin/env python3
"""Batch translate Cassiodorus letters (IDs 2749, 2818, 2865, 2898, 2607)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(2749, """From: Cassiodorus, on behalf of King Theoderic
To: Capuanus, Vir Sublimis
Date: ~522 AD
Context: Theoderic appoints a man of proven legal experience to a judicial position, praising his subtle skill in correcting judges through gentle persuasion rather than confrontation.

If our judgment had chosen you as a raw recruit, if you had come to the scales of examination as an unknown, we would think it necessary to advise you on what wisdom and what dignity to bring to your role. But you are believed to possess an understanding of every virtue, since you have earned the right to practice in the service of letters. You know the modesty you should maintain, having already proved yourself in the management of others' affairs. For whenever harsh suspicion of a judge touched you, you would correct his spirit by praising justice with a gentle and penetrating remedy, achieving through sweet persuasion what you could not have imposed on a superior. Who then can doubt that you love those things..."""),

(2818, """From: Cassiodorus, on behalf of the King
To: A provincial judge (formula for bina et terna collection through officials)
Date: ~522 AD
Context: A variant of the previous tax-collection formula, this time dispatching treasury clerks to assist the provincial judge, reflecting the central government's distrust of local officials.

Although ancient custom has directed that the collection of the bina et terna taxes should fall to your office, nonetheless -- so that the burden of multiple responsibilities should not overwhelm you and a doubled concern should not create obstacles -- we have decided to dispatch the clerks named from our bureau to assist you and your staff. With their support, see that the customary amount is delivered to the distinguished Count of the Sacred Largesses by the Kalends of March [March 1], lest you be held publicly responsible if you allow any delay in the sacred revenues..."""),

(2865, """From: Cassiodorus, on behalf of King Athalaric
To: Cyprianus, Patrician
Date: ~522 AD
Context: Athalaric bestows a further honor on the patrician Cyprianus, whose merits and those of his brother are praised with the metaphor of an ever-flowing spring.

Although you have frequently been praised in honors of your own and in the distinction of your brother, nevertheless -- because the goodness of good men is not spent when it is recounted -- we return, as though summoned, to a subject on which many praises have already been proclaimed. All that should be testified about the faithful, all that should be said about the deserving, has been attested in your case. But the man who has filled himself with the integrity of his actions worthily puts forth fresh novelties of praise whenever he wishes.

The spring of glory is a perennial, ever-flowing stream: just as a fountain is not depleted by flowing, so neither is glory dried up by frequent celebration. Even if past deeds were passed over in silence, you..."""),

(2898, """From: Cassiodorus, on behalf of King Athalaric
To: The Roman Senate
Date: ~522 AD
Context: Athalaric writes to the Senate about the problem of teachers of Roman eloquence not being paid their stipends, ordering that professors receive their full salaries without interference from corrupt middlemen.

We have rightly referred cases concerning your children to yourselves, since you who have an interest in the advancement of Roman learning should be the ones to look after it. It is impossible to believe you would be less attentive to something that enhances the prestige of your families and provides the Senate with counsel through constant study.

Recently, as is our custom of concern for you, we have learned through whispered reports that teachers of Roman eloquence are not receiving their established salaries, and that through the profiteering of certain individuals, the funds allocated to the masters of the schools are being diminished..."""),

(2607, """From: Cassiodorus, on behalf of King Theoderic
To: Festus, Patrician
Date: ~522 AD
Context: Theoderic orders the return of the sons of the deceased Ecdicius to their homeland with their father's body, a poignant letter about grief, duty, and royal compassion.

It is right that royal devotion should accommodate itself to those wounded by the blow of fate, because those whom the adversity of their lot has crushed deserve all the more to be lifted up. We therefore declare to your magnificence by the present authority that you are to allow the sons of Ecdicius -- whom we had previously ordered to reside in the city [Rome] -- to return to their homeland with their father's body. It is a wished-for homecoming, though a bitter occasion. We must not deny their longing lest the wound of the afflicted be doubled, and -- unspeakable thought -- we who always dispel the clouds of grief with our serenity should now seem to deny the afflicted their rightful tears. Insatiable..."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Cassiodorus translations (batch 10)")

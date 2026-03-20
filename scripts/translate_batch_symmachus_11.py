#!/usr/bin/env python3
"""Batch translate Symmachus letters (IDs 5089, 5187, 4999, 5188, 5091)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(5089, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~385 AD
Context: Symmachus reports his recovery from illness and recommends the young man Repentinus.

The strength of my health is beginning to rally -- it is only fair that a steady stream of letters should now be expected from me. Let this recovery hold, though winter's harshness often threatens it. The process of convalescence is extremely delicate and fragile, and health looks for the aid of milder skies before the doctors' hands can do their work. You must think I have made the art of healing responsible for the length of my illness! I want us to break the memory of bad times with the charm of a joke.

But I must also say something about Repentinus, an excellent young man, whose constant attendance I missed. His modesty, I believe, kept him away, when confidence drawn from your introduction should have brought him forward..."""),

(5187, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~385 AD
Context: Symmachus reports on a Senate hearing that exempted a friend's son from certain civic obligations, while noting his own illness prevented him from attending.

I was unable to attend the Senate on the day when the son of Thalassius was released from the obligations of our rank, but I had already secured the hope of future action on his behalf through considerable personal recommendations among our friends. I do not claim credit for the success of the petition, however: the justice of the request and the force of your own intervention carried it through. My health, long tossed about, has at last settled into calm waters -- and I write this so that, cheered by the news of my recovery, you may return me an equal measure of joy from your own good fortune."""),

(4999, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~385 AD
Context: A recommendation for the distinguished Nicagoras, framed with characteristic elegance.

I am getting ahead of your voluntary generosity with a formal request, so that what you would freely give may appear to have been won by my petition -- and the goodness of your nature may be credited to my account. The distinguished Nicagoras..."""),

(5188, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~385 AD
Context: Symmachus presses a friend to send animal hunters for his son's upcoming public games.

The urgency of a repeated request adds great weight to my first petition, and so I press my case again about providing the animal hunters, hoping that a second letter may stir your diligence more effectively. The day of our spectacle is drawing near, and the generosity of the candidate alone will not suffice..."""),

(5091, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~386 AD
Context: Symmachus reports the successful acquittal of Baebianus's son in a Senate proceeding, crediting the friend's original request.

It is the mark of your character to give commands that are both pious and just. I say this at the outset so you may know that I have both carried out and approved what you instructed regarding the son of the distinguished Baebianus. Your letter requesting it was actually unnecessary -- I should have been reminded of this duty, not asked. And besides, I myself had the closest friendship with the man. So it happened that the favor of personal affection was joined to the justice of the petition. To cut it short: the records of our curia's proceedings concerning his acquittal will reach your hands, and they will show that the speed you and Baebianus hoped for has been granted out of respect for your wishes and his standing. In return for this service, I ask for more frequent letters..."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Symmachus translations (batch 11)")

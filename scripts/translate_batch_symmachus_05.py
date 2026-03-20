#!/usr/bin/env python3
"""Batch translate Symmachus letters (IDs 5066, 5131, 5429, 5067, 5132)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(5066, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~374 AD
Context: Symmachus reproaches a friend for prolonged silence, wittily dismantling every possible excuse, and teases him about withholding his opinion on a speech.

You are certainly blessed with natural gifts and intellectual talent, but even you will find it hard to excuse such continuous silence. What excuse can you offer, whether true or invented? "Long journeys kept me occupied," you will say -- but you stopped often enough along the way, and you did eventually arrive. "I devote every waking hour to public business" -- but every occupation is broken by intervals of rest. All that remains -- and I very much hope this is not the case -- is for you to confess that you simply neglected our friendship. For if you occasionally skip your duties, that is being busy; if you always skip them, it is forgetting.

Do you think you can make me angry? If that were possible, I would keep silent. Are you making sport of my patience? Then understand: a patient spirit deserves an even greater reward. The man whose principles forbid him from taking offense is all the more wronged by being slighted. And it certainly should have mattered to you to include a few personal words when an official speech from your bureaus was being sent to me. On that speech I will keep you in suspense for now, and I will give you my public judgment only when you have begged me, when you have earned it -- and, since I value your letters so highly, when you have written. Farewell."""),

(5131, """From: Quintus Aurelius Symmachus, Roman Senator
To: Florentinus and others (multiple letters)
Date: ~374-395 AD
Context: Several short letters including a note about exchanging courtesies from Milan, and a playful challenge to Florentinus about who writes more faithfully.

To a friend: Even when I was staying in Milan, I observed the courtesy of greeting you, and now that I have completed the return journey, I have not denied the diligent service of a literary gift. You are expecting me, I suppose, to demand a letter in return. That claim is promised not by my insistence but by your own affection. Let those who do not deserve a place in our hearts demand written replies.

---

To Florentinus (~395 AD): For a long time you delayed telling me when our brother was arriving -- to let him, I assume, surprise me with the honor of his greeting in person. I recognize your pious little trick, but I am not conceding the advantage. I hereby challenge you both -- singlehandedly taking on two opponents in a contest of friendly correspondence. "It is your leisure that gives you this confidence in letter-writing," you will say. But what of the fact that the honor of the quaestorship and the practice of drafting legislation have equipped you even better? Meanwhile, your brother and I share the same condition of private life. If only the watchful eye of our good emperor would claim his services too! Both of us should bear it..."""),

(5429, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~374 AD
Context: A recommendation for Flavianus the Younger, commending him not only on the testimony of his father but as a personal witness to his character.

I have no doubt that you care about men of quality -- for your own character must take pleasure in the company of kindred spirits. If you have any regard for me, I ask you to embrace the friendship of my lord and son Flavianus, whom I commend to you not merely on the faith of his father but as a witness myself. You will find in him a mind worthy of your love and deserving of a better fortune -- though the magnitude of the imperial favor has already met his misfortunes, and a summons to court has been added to crown his relief. It is only right, therefore, that a man whom imperial patronage has noticed should not be abandoned by your friendship. Farewell."""),

(5067, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~374 AD
Context: Symmachus celebrates the end of a friend's long silence and expresses joy at his brother's appointment to a vicariate.

You have finally broken your long silence -- though, by Hercules, only after being prodded by my repeated letters. Still, my delight is no less than if you had written of your own accord. I rejoice at my brother's appointment to the vicariate [the office of vicarius, a deputy governor] as if the honor had been bestowed on me. I am equally pleased by the goodwill you have shown him, as though you had contributed something to it yourself. Together with him, we have reliable evidence that the distinguished Syagrius [probably the younger Syagrius, a notable Gallo-Roman aristocrat] has exerted himself in a service of real value. I thought it worth writing this to you so that you, as a faithful advocate, might carry forward our gratitude."""),

(5132, """From: Quintus Aurelius Symmachus, Roman Senator
To: Florentinus and others (multiple letters)
Date: ~375 AD
Context: Symmachus writes about recovering from illness, worries about the African grain supply, and exchanges literary courtesies.

You excuse yourself for your long silence. The fault is shared -- for I too was kept from this exchange for a long time by poor health. You must have shuddered when you read the bitter news about me. Return to a happier frame of mind: by the gods' blessing, I have recovered my health. Let us both grant each other easy forgiveness for our literary inactivity. Let us both forgive what we both did wrong.

But what is this you whisper to me about scanty supplies of African grain? Heaven forbid that this year should repeat the misfortune of previous ones! Providence will, I hope, block the paths of disaster by informing the sacred ears [the emperor] and by disciplining the officials responsible for the grain supply. Nor does the time of year cut off hope: the sea is still open to proper sailing, and autumn has not yet plunged into winter. Still, I am pleased that you are anxious and that your dutiful concern anticipates the crisis. A better outcome will reward your care, and the fruit of your praiseworthy diligence will make it sweet, in hindsight, to have worried."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Symmachus translations (batch 05)")

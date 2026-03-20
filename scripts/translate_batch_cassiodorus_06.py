#!/usr/bin/env python3
"""Batch translate Cassiodorus letters (IDs 2746, 2815, 2862, 2895, 2920)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(2746, """From: Cassiodorus, on behalf of King Theoderic
To: Wilia, Count of the Royal Patrimony
Date: ~522 AD
Context: Theoderic orders the assembly of shipwrights and timber for the construction of warships (dromons) at Ravenna.

Public utility, just as it serves the preservation of all, must be accomplished by the effort and labor of all -- since it is a great opportunity for distinction if something is accomplished individually for the common cause. The man who helps others commends himself, especially when he recognizes he has also helped himself.

You will recall that we previously ordered that shipbuilding craftsmen be recruited from our household estates. These men, provided with God's help, we command to report without delay to the city of Ravenna by the Ides of June [June 13], so that their arrival may be opportunely offered to the construction of ships. Work that is divided tends to create its own delays, and it is not enough to complete one vessel if we fail to provide for both.

Furthermore, if any timber suitable for building dromons [light warships -- fast galleys used for naval patrols and military transport] can be found on the banks of the River Po on royal estates, the craftsmen assigned to this project by the distinguished Abundantius, Praetorian Prefect, shall have permission to cut it. We wish this example to be set first on our own estates..."""),

(2815, """From: Cassiodorus, on behalf of the King
To: The new Superintendent of Armorers (formula)
Date: ~522 AD
Context: A template for appointing the official in charge of arms manufacture, emphasizing the critical importance of well-made weapons and the need for honest oversight.

Consider what you are undertaking, and you will understand that there is no room for error. To construct arms well is to protect everyone's safety, because the enemy is terrified at first sight by superior weaponry and begins to lose heart when he knows he cannot match it. From the current tax year, we therefore place you in charge of the soldiers and armorers, persuaded by the reputation of your character, so that you may demand from the craftsmen the quality of work you know will please us.

Do not let our absence lull you into carelessness. We see everything you do. We who, through long practice, can detect at first glance the errors of craftsmen with the most exacting scrutiny and judge what has been made with skill. See, then, with what diligence and dedication you must carry out work that is coming to our inspection. Act so that no bribery and no fault drags you down, because nothing done wrong in such a matter can be forgiven -- lest you be punished on the very account where you sinned. The product that brings both death and salvation -- the destruction of wrongdoers, the safeguard of the good..."""),

(2862, """From: Cassiodorus, on behalf of King Athalaric
To: Fidelis, Quaestor
Date: ~522 AD
Context: Athalaric appoints the distinguished lawyer Fidelis as quaestor -- the official who drafted all royal legislation and correspondence -- praising his eloquence, integrity, and youthful maturity.

It is clearly a profession of justice to appoint learned jurists as judges, because a man who knows what is fair can hardly neglect it, nor is one easily soiled by the stain of error whom learning has purified. The imperial eye noticed you long ago as you labored in the courts, and it could not escape notice with what faithfulness you carried out the cases entrusted to you, with what brilliance you argued the matters you pleaded.

Your eloquence and your conscience advanced in equal step: no client ever had anything further to wish for; no judge ever found anything to correct in you. To these qualities was added a grace of manner and a purity of spirit. Only your youthful appearance revealed your age -- from lips still young flowed the words of maturity. The bloom of youth and the ripeness of mind competed, but the latter prevailed, since it is wisdom that leads us to the heights of virtue and glory.

We therefore fit our gifts to your name and merits: let Fidelis [the name means "faithful" in Latin] receive the royal secrets, and let an eloquent man find a post worthy of letters. Now judge with distinction the cases you once pleaded with skill. Let justice sit beside you as your advisor..."""),

(2895, """From: Cassiodorus, on behalf of King Athalaric
To: All subjects (an edict)
Date: ~522 AD
Context: A remarkable general edict against violence and lawlessness, issued in elegant literary form, comparing criminals to beasts and declaring that internal vices are worse than external enemies.

Ancient wisdom providently decreed that the public should be admonished by general edicts, through which every offense is corrected while the individual offender's dignity is spared. Everyone thinks the warning is aimed at them when no one is singled out, and the man who happens to be cleansed under a general proclamation becomes indistinguishable from the innocent. By this means our true devotion is also preserved: fear is born without the sword being drawn, and correction is achieved without bloodshed. We are moved while at peace, we threaten while at rest, and we are angry with clemency -- since we condemn only the vices, not the persons.

For some time now, the complaints of various people have buzzed in our ears with persistent whispering that certain individuals, despising civilized behavior, have chosen to live with bestial savagery. Reverting to the primitive state of nature, they consider human law hatefully alien to themselves. We have now judged it fitting to suppress these people at the very moment when we are resisting the enemies of the state by divine power. Both are harmful, both must be driven out -- but internal vices strike all the more dangerously because they come from within..."""),

(2920, """From: Cassiodorus, on behalf of King Theodahad
To: The Roman Senate
Date: ~522 AD
Context: Theodahad explains to the Senate that Gothic troops have been sent to Rome for its protection, not as a threat, and that provisions have been arranged at market prices so the garrison does not burden the citizens.

The remedy we have devised for you, conscript fathers, with a devoted heart, we will not allow to be turned against you by bitter suspicion -- because it amounts to an injury to help in secret while appearing to intend something else. Know, therefore, that our arms have been deployed for your safety, so that whoever dares to attack you will face the hands of the Goths, with divine help.

If a diligent shepherd repels threats to his flock, if a careful head of household blocks opportunities for those who would deceive, with what precaution must we defend Rome -- which is known to have no equal in the world? The greatest things must not be left to chance, because a man who neglects to plan for adversity proves he loves too little.

But so that even the defense itself should not weigh on you in any way, we have arranged for provisions to be purchased for the assigned army at market prices under the supervision of the official named, so that the soldiers have no need to transgress and you have no cause for loss. We have also placed over them our major domus Vuaccen, who by the quality of his character..."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Cassiodorus translations (batch 06)")

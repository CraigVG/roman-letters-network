#!/usr/bin/env python3
"""Batch translate Cassiodorus letters (IDs 2600, 2639, 2787, 2812, 2859)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(2600, """From: Cassiodorus, on behalf of King Theoderic
To: Venantius, Vir Illustris
Date: ~522 AD
Context: Theoderic promotes the young Venantius to the honorary rank of Count of the Domestics, praising his distinguished father's service and urging the son to live up to the family name through learning.

It is our policy to assess future merit even in youth and to judge a child's prospects by the virtues of the parents -- because good outcomes are certain when they draw their credibility from the very beginning, and a stock that has always put down deep roots does not know how to fail. A spring's life-giving flow runs on without ceasing, and all streams share this quality: the taste granted to the source, unless corrupted by some accident, is never denied to the tributaries.

This is why we promote you, assessed on the merits of your distinguished father, to the honorary rank of Count of the Domestics [a prestigious court title in the late Roman/Gothic administration], so that you who are already distinguished by lineage may also shine by office. Who could doubt your future -- certain as it is -- when they recall your glorious father's devoted labors? Fired by the power of his judgment, he was so ready for emergencies that you would have thought he had been briefed in advance. He managed the prefecture [the highest civilian administrative office] -- the noblest of all burdensome responsibilities, and praiseworthy even if it were his only achievement -- while simultaneously overseeing the care of our army, so that neither provinces lacked proper administration nor the army went without his watchful attention. His tireless and ready wisdom overcame every challenge: he drew barbarian customs toward peace; he managed everything to our satisfaction, so that those who received were content without giving those who gave any cause for complaint. To sum up much in little: he proved so much about himself that his untested posterity was chosen on the strength of it.

Yet amid these distinctions of birth -- and this is the greatest glory of the finest nobility -- you do not lack the support of your own merits. You are a diligent student of letters, which deserve to speak for every honor, adding to the brilliance of your family the talent of a graceful eloquence. Devote yourself to such studies; love what you see rewarded in yourself, so that our judgments may advance along with your progress. For you earn from us exactly as much as we see you pressing forward in worthy actions."""),

(2639, """From: Cassiodorus, on behalf of King Theoderic
To: Theodahad, Vir Sublimis
Date: ~522 AD
Context: Theoderic orders the nobleman Theodahad -- his own kinsman -- to adjudicate a dispute that the defendant has been evading through legal trickery.

When justice is violated, the injury is ours, because we rightly take upon ourselves offenses against things we hold dear. We especially will not allow an act committed in contempt of our orders to go unpunished. What presumption would dare avoid punishment if it showed contempt for the reverence owed to a royal command? Therefore the man whom we previously ordered to appear before the court of the distinguished Sona, and who has eluded it through his ingrained cunning, we now commit to your examination for a hearing, so that you may put an end to a dispute that has been prolonged by culpable scheming. Give this hearing your full attention, so that your reputation for justice may grow -- since the tangled disputes of litigants are entrusted to you for the sake of a remedy."""),

(2787, """From: Cassiodorus, on behalf of the King
To: The Vicar of the City of Rome (appointment formula)
Date: ~522 AD
Context: A template letter for appointing the Vicar of Rome, describing the grandeur and responsibilities of this office that served as deputy to the Praetorian Prefect.

It is the custom of deputies to obey the will of the judges they represent so completely that they seem to have no standing of their own. They shine with borrowed light, lean on another's authority, and appear to be mere images of the real thing -- men who possess no independent brilliance. But you bear the title of Vicar, and you do not surrender your own prerogatives, since jurisdiction granted by a prince is your own. You share some authority with the prefects: parties appear before you under praetorian advocacy; you deliver judgments in the emperor's name [vice sacra -- "by sacred delegation"]; and -- the surest mark of trust -- in capital inscriptions, human life is committed to your hands, which among mortals is known to be the most precious thing.

It is further provided that you may not even be greeted without your military cloak [chlamys -- the short cloak marking official rank], so that, always seen in official dress, you would never be taken for a private citizen. We consider all these privileges to have been granted for the glory of the prefecture, so that anyone calling you the deputy of so great a seat would see nothing diminished. Consider what quality of service you must render, you who are elevated by such authority. A man cleared of a charge should not be stripped of his innocent property: for what can he owe you if he counts the cost of his own money as the price of acquittal? Like the highest officials, you ride in a carriage. Within forty miles of the most sacred city you guard its laws. At Praeneste [modern Palestrina] you present games in place of the consul, you are raised to the dignity of a senator, and the halls that are known to belong to the highest ranks are opened to you.

This is why in the Hall of Liberty [the Atrium Libertatis, a famous public building in Rome] you hold a seat of honor, and merely to have entered there is a distinction. Even senators who outrank you in precedence are seen to need certain things from you. You have something to offer those above you, and not without reason should you be counted among the foremost, you who can either help or harm men of consular rank. Lift your spirits, but temper them with modesty. Every office is only as good as the character of the man who holds it. Nothing done in public service is lowly unless it is corrupted by bad morals. If fairness is admired in humble private citizens, how much more welcome is it when preserved at the summit of power -- where restraint is hardest to maintain when one's will races ahead.

Therefore we confer upon you the dignity of the vicariate by our serene judgment. Exercise it in Rome in such a way that you make your conscience worthy of so great a city. You shall enjoy all the privileges that your predecessors are known to have held, because just as we demand from you the observance of ancient customs, so too we do not deny your office its ancient honors."""),

(2812, """From: Cassiodorus, on behalf of the King
To: The Prefect of the City of Rome (regarding the appointment of an architect)
Date: ~522 AD
Context: One of Cassiodorus's most celebrated letters -- a formula for appointing Rome's official architect, containing a magnificent description of the city's statues, columns, and buildings, and a catalog of the Seven Wonders of the ancient world.

It is fitting that the splendor of Rome's buildings should have a skilled guardian, so that the marvelous forest of its monuments may be preserved through diligent care and new construction may be raised through expert craftsmanship. Our generosity does not shrink from this effort: we both restore the works of the ancients by removing their defects and clothe new creations in the glory of antiquity.

Therefore, let your illustrious greatness know that the said person has been appointed architect of Rome's citadels from the present tax year. And because the arts must be nourished with just compensation, we wish him to receive whatever his predecessors are known to have legitimately obtained.

He will see things finer than he has read about, more beautiful than he could have imagined: those statues, still bearing the likenesses of their creators, so that as long as the memory of praiseworthy men endured, the image of the body would preserve the likeness of living substance. He will marvel at veins rendered in bronze, muscles swelling as if by effort, sinews stretched as if in motion, and the human form cast in so many likenesses that you would think it had been born rather than made. The Etruscans are said to have first invented these arts in Italy, and later generations, embracing them, gave the city a second population nearly equal to the one nature produced. He will marvel that even in the forms of horses the signs of spirit are present: with nostrils curled and round, limbs taut, ears pulled back, one might believe they were eager to run -- though one knows the metal cannot move.

What shall we say of the reed-like height of the columns? Those towering masses of buildings seem to be held up by slender shafts, and hollowed out with such uniform fluting that you would think they had been poured in a mold. What you see polished from the hardest stone, you would judge to have been shaped in wax. The joints in the marble you would call natural veins -- where the eye is deceived, praise is shown to have grown into the miraculous.

The storytellers of ancient times attributed only seven wonders to the whole world: the Temple of Diana at Ephesus; the magnificent tomb of King Mausolus [the origin of the word "mausoleum"]; the bronze statue of the sun at Rhodes, called the Colossus; the image of Olympian Zeus, which Phidias -- the greatest of craftsmen -- formed with supreme elegance in ivory and gold; the palace of Cyrus, king of the Medes, which Memnon built with lavish art, binding gold to stone; the walls of Babylon, which Queen Semiramis constructed of baked brick, sulfur, and iron; and the pyramids of Egypt, whose shadow, consuming itself as it stands, is never seen beyond the structure's own footprint. But who would still consider those preeminent once he has seen so many marvels in a single city? They had the honor of precedence only because they came first, and in a raw age anything that emerged as new was rightly celebrated on every tongue. Now, however, it can be truthfully said that all of Rome is a wonder. Therefore, let a man of such expertise take up this charge, lest amid all that ingenious work of the ancients he himself appear to be a mere artisan, unable to appreciate what ancient craftsmanship achieved so that its creations might be truly felt. Let him study the books; let him immerse himself in the teachings of the ancients, so that the man appointed to succeed them may know no less than they did."""),

(2859, """From: Cassiodorus, on behalf of King Athalaric
To: The Roman Senate
Date: ~522 AD
Context: Athalaric thanks the Senate for accepting his grandfather Theoderic's choice of bishop, urging those who backed other candidates to let go of their disappointment.

We are most grateful that you have accepted our grandfather of glorious memory's judgment in the election of a bishop. It was right to obey the decision of a good prince who, deliberating wisely -- even in a religion not his own [Theoderic was an Arian Christian, while the Roman Senate followed Nicene/Catholic Christianity] -- was seen to have chosen such a pontiff that no one could reasonably object. Recognize that his chief desire was for the faith of all churches to flourish under good priests. You have received a man commended both by divine grace and by royal examination.

Let no one cling to the old rivalry. There is no shame in losing when your preference is overruled by a prince. Indeed, the man who embraces the chosen bishop with a pure heart makes that choice his own. For what cause is there for grief, when you find in this man the very qualities you wished for in the other? These were civic contests -- a battle without weapons, a quarrel without hatred. The matter is settled with shouts, not with suffering. Even though one candidate was set aside, nothing is lost to the faithful when the desired priesthood is achieved.

Therefore, as your envoy the distinguished Publianus returns, we have thought it fitting to send a letter of greeting to your assembly. We take great delight whenever we exchange words with our leading men. And we have no doubt that you too find it most pleasant to know that what you did at our grandfather's command is also pleasing to us."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Cassiodorus translations (batch 02)")

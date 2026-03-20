#!/usr/bin/env python3
"""Batch translate Basil letters 197-202 (IDs 1008-1013)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(1008, """From: Basil, Bishop of Caesarea
To: Ambrose, Bishop of Milan
Date: ~368 AD
Context: Basil's first letter to Ambrose of Milan -- praising God for raising a former imperial governor to the episcopal throne, and urging him to fight Arianism in the West.

The gifts of the Lord are always great and always many -- great beyond measure, beyond counting in number. To anyone alive to his mercy, one of the greatest of these is the privilege I now enjoy: the chance for us, though separated by vast distance, to address one another by letter. God grants us two ways of becoming acquainted: personal meeting and correspondence. I have come to know you through the second -- through your own words. I do not mean that your outward appearance is impressed on my memory, but that the beauty of the inner man has been revealed to me by the rich variety of your writings, "for out of the abundance of the heart the mouth speaks" [Matthew 12:34].

I have glorified God, who in every generation chooses those who are pleasing to him: who once drew a prince for his people from the sheepfold [David], who through the Spirit empowered Amos the herdsman and raised him up as a prophet, and who now has called forth from the imperial capital -- from a man entrusted with governing a whole nation, exalted in character, in family, in rank, in eloquence, in all that this world admires -- a shepherd for Christ's flock. This same man has thrown away every worldly advantage, "counting them all loss that he may gain Christ" [Philippians 3:8], and has taken in his hand the helm of a great ship, famous for its faith in God: the Church of Christ.

Come then, O man of God! "Not from men have you received or been taught the Gospel of Christ" [cf. Galatians 1:12] -- it is the Lord himself who has transferred you from the judges of the earth to the throne of the apostles. Fight the good fight. Heal the sickness of the people, if any are infected with the disease of Arian madness. Renew the ancient paths of the Fathers.

You have laid the foundation of friendship toward me. Build on it by writing often. In this way we shall have the comfort of close fellowship even while our bodies remain apart."""),

(1009, """From: Basil, Bishop of Caesarea
To: Eusebius, Bishop of Samosata
Date: ~368 AD
Context: Basil apologizes for the scarcity of his letters, blaming a brutal winter, blocked roads, and clergy who have never traveled and prefer to stay home.

After the letter brought to me by the government couriers, I have received one more dispatched later. I have not sent many of my own, since I could not find anyone traveling in your direction. But I have sent more than the four you know of -- including those forwarded to me from Samosata after your first letter. These I sealed and sent to our respected brother Leontius, the tax assessor at Nicaea, asking him to pass them to the steward of our brother Sophronius's household for transmission to you. Since my letters pass through so many hands, it is likely enough that one busy or careless person along the way means your reverence never receives them. Forgive me, then, if they seem few.

With your usual perceptiveness you have rightly faulted me for not sending my own courier when the occasion demanded it. But you must understand: we have had a winter of such severity that every road was blocked until Easter, and I could find no one willing to brave the journey. Our clergy may seem numerous, but they are men with no experience of travel -- they never engage in commerce and prefer to stay close to home, most of them working at sedentary trades for their daily bread.

The brother I am now sending has been summoned from the countryside for the purpose of carrying this letter to your holiness, so that he can both give you a clear report of my situation and, God willing, bring back prompt and plain news of yours."""),

(1010, """From: Basil, Bishop of Caesarea
To: Amphilochius, Bishop of Iconium
Date: ~368 AD
Context: The second of Basil's three canonical letters -- a continuation of detailed responses to Amphilochius's questions about church discipline, covering fallen virgins, perjuring clergy, marriage law, and categories of penance.

(Second Canonical Letter)

To Amphilochius, concerning the Canons:

I wrote some time ago in reply to your reverence's questions, but did not send the letter -- partly because my long and dangerous illness left me no time, and partly because I had no one to carry it. I have few men with me who are experienced travelers and fit for this kind of errand. Now that you know the reasons for my delay, forgive me.

I have been quite astonished by your eagerness to learn and your humility. You hold the office of teacher, yet you willingly come to learn -- and from me, who makes no claim to great knowledge. But since you are willing, out of your fear of God, to do what another might hesitate to do, I am bound for my part to go beyond even my own strength to support your righteous zeal.

XVII. You asked about the presbyter Bianor -- whether he may be admitted among the clergy, given his oath. I have already issued a general ruling to the clergy of Antioch concerning all who swore with him: they should abstain from public worship but may perform priestly functions in private. Bianor has the further liberty that his duties lie not in Antioch but in Iconium, since, as you yourself have written, he has chosen to live there. He may therefore be received, but your reverence should require him to show repentance for the rashness of the oath he took before the unbeliever -- an oath taken because he could not endure even a small trial.

XVIII. Concerning fallen virgins who, after professing a chaste life before the Lord, have made their vows empty by falling to the desires of the flesh: our Fathers, gently and mercifully making allowance for the weaknesses of those who fall, laid down a period of penance...

[This letter continues with extensive canonical rulings on penance for various offenses, the treatment of those who break monastic vows, regulations on bigamy and trigamy, disciplinary categories for different sins, and instructions on readmission to communion.]"""),

(1011, """From: Basil, Bishop of Caesarea
To: Amphilochius, Bishop of Iconium
Date: ~368 AD
Context: Basil writes from deep illness, unable to visit Amphilochius, and sends the letter by a soldier named Meletius who is moving newly recruited troops through the region.

Sickness after sickness has attacked me, and all the work piled on me -- not only by the affairs of the Church but by those who are making trouble for the Church -- has kept me pinned down the entire winter and up to this moment. It has been completely impossible for me to send anyone to you, let alone to visit in person.

I imagine your situation is similar -- though not, God forbid, as to illness. May the Lord grant you continued health for carrying out his commands. But I know the care of the churches weighs on you just as it does on me.

I was about to dispatch someone to get a clear report on your condition when my dear son Meletius, who is moving the newly enlisted troops, reminded me of the chance to greet you through him. I gladly seized the opportunity.

He can serve as a letter in himself, both because of his good character and because he knows my situation thoroughly. Through him, I beg your reverence above all to pray for me: that the Lord may free me from this troublesome body; grant his churches peace; give you rest; and, once you have settled Lycaonia's affairs in apostolic fashion (as you have begun), provide an opportunity for you to visit us here as well.

Whether I am still in the flesh or have already been called to depart to the Lord, I hope you will take an interest in our region as your own -- because it is. Strengthen what is weak. Rouse what is sluggish. By the power of the Spirit dwelling in you, transform everything into a condition pleasing to the Lord."""),

(1013, """From: Basil, Bishop of Caesarea
To: Amphilochius, Bishop of Iconium
Date: ~369 AD
Context: Basil, still too ill to travel, tries to reach a martyrs' shrine and suffers a relapse, asking Amphilochius to proceed without him if the matter is urgent.

Under other circumstances I would count it a special privilege to meet with your reverence, but now above all, when the business that brings us together is so important. Yet what remains of my illness is enough to prevent me from stirring even the shortest distance. I tried to drive as far as the martyrs' shrine and had a relapse almost to my previous state.

You must forgive me, then. If the matter can wait a few days, I will, God willing, join you and share your concerns. If it is urgent, do what needs to be done, with God's help -- but count me as present with you in spirit and as a participant in your worthy work.

May you, by the grace of the Holy Spirit, be preserved for God's Church -- strong, joyful in the Lord, and praying for me."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Basil translations (IDs: 1008-1013)")

#!/usr/bin/env python3
"""Batch translate Basil letters 179-184 (IDs 990-995)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(990, """From: Basil, Bishop of Caesarea
To: Arinthaeus [a high-ranking military commander]
Date: ~367 AD
Context: A short, polished letter of recommendation asking a powerful general to support a well-born man facing a legal charge.

Your natural nobility of character and your openness to all have taught me to think of you as a friend of freedom and of people. So I have no hesitation in approaching you on behalf of a man who is distinguished by a long and illustrious ancestry, but who deserves even greater esteem on his own account, because of the goodness of his character.

I ask you, at my request, to lend him your support against a legal charge that is, in reality, ridiculous -- but difficult to meet because of how serious the accusation sounds. It would make an enormous difference to his case if you would say a kind word on his behalf. You would be helping the right. And you would also be showing your usual respect and kindness to me, your friend."""),

(991, """From: Basil, Bishop of Caesarea
To: Sophronius, the Master, on behalf of Eunathius
Date: ~367 AD
Context: Basil intercedes with the same senior imperial official on behalf of another man in trouble -- Eunathius, a learned Christian gentleman.

I have been greatly distressed at meeting a worthy man caught up in very serious trouble. How could I, being human, fail to sympathize with a man of high character suffering beyond what he deserves?

Thinking about how I could be useful to him, I found one way to help him out of his difficulties: making him known to your excellency. It is now for you to extend to him the same good offices that, as I can personally testify, you have shown to many.

You will learn the full details from the petition he has submitted to the emperors. I ask you to take this document into your hands, and I implore you to help him to the utmost of your power. You will be helping a Christian, a gentleman, and a man whose deep learning ought to command respect.

If I add that by helping him you will be conferring a great kindness on me -- well, I know my affairs are small matters. But since you are always generous enough to treat them as important, your favor to me will be no small thing."""),

(992, """From: Basil, Bishop of Caesarea
To: Otreius, Bishop of Melitene
Date: ~367 AD
Context: Basil writes to a fellow bishop about the exile of their mutual friend Bishop Eusebius of Samosata, proposing they exchange intelligence and comfort each other with news.

Your reverence is, I know, no less distressed than I am at the removal of our deeply beloved bishop Eusebius [Eusebius of Samosata, exiled by the Arian emperor Valens for his staunch Nicene faith]. We both need comfort. Let us try to give it to each other.

You write to me whatever you hear from Samosata, and I will report to you anything I learn from Thrace.

It is no small relief in our present distress to know of the constancy of his people. It will be the same for you to have news of our common father. I cannot, of course, put everything in a letter, but I commend to you the man who carries this -- he is fully informed and will tell you in what condition he left Eusebius, and how he bears his troubles.

Pray for him, and for me, that the Lord will grant him a swift release from his suffering."""),

(994, """From: Basil, Bishop of Caesarea
To: The Senate of Samosata
Date: ~367 AD
Context: Basil writes to the civic leaders of Samosata to praise their steadfastness during the persecution of their bishop Eusebius, urging them to hold firm.

Most excellent senators,

I see temptation spread across the entire world. The great cities of Syria have been tried by the same sufferings as yours -- though truly, nowhere is the Senate so tested and renowned for good works as your own, famous as you are for your righteous zeal. I almost thank the troubles that have fallen upon you, for without this trial, the proof of your character would never have been known. To all who earnestly strive for any good, the suffering they endure for the sake of their hope in God is what a furnace is to gold.

So take heart, most excellent sirs. Let the labors you are about to undertake be worthy of those you have already borne. On a firm foundation, build an even worthier finish. Stand ready to gather around your shepherd when the Lord grants him to be seen again on his own throne -- each of you with some good deed done for the Church of God to report. On the great day of the Lord, each person, in proportion to his labors, will receive his reward from the generous Lord.

By remembering me and writing as often as you can, you will be doing what justice requires in sending a reply -- and you will give me great pleasure besides, by putting into writing a token of a voice I delight to hear."""),

(995, """From: Basil, Bishop of Caesarea
To: Eustathius, Bishop of Himmeria
Date: ~368 AD
Context: Basil consoles a newly orphaned bishop (whose metropolitan has died or been exiled) and urges him to write, since shared grief is lighter grief.

I know, my friend, that orphanhood is a dismal thing and brings a great deal of work, since it deprives us of those set over us. That, I conclude, is why you have not been writing -- you are weighed down by what has happened, and at the same time consumed with the work of visiting Christ's flocks, which are under attack from every side.

But every grief finds comfort in the company of sympathetic friends. So I beg you: write to me as often as you can. You will refresh yourself by speaking to me, and you will comfort me by letting me hear from you. I will try to do the same for you, as often as my own work allows.

Pray for us yourself, and ask all the brothers to earnestly petition the Lord to grant us one day a release from the present distress."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Basil translations (IDs: 990-995)")

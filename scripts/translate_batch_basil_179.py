#!/usr/bin/env python3
"""Batch translate Basil letters 174-178 (IDs 985-989)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(985, """From: Basil, Bishop of Caesarea
To: A widow
Date: ~367 AD
Context: Basil writes to a widow who has initiated correspondence, offering spiritual counsel on keeping the fear of God and the Day of Judgment always in mind.

I have very much wanted to write to your excellency regularly, but I have held back from time to time for fear of causing you trouble on account of those who are ill-disposed toward me. Their hostility has apparently reached the point where they make a scene if anyone so much as receives a letter from me. But now that you have begun writing to me yourself -- and very good of you it is -- sharing everything that is on your mind, I am moved to write back. Let me make up for what I have missed, and at the same time respond to what you have written.

Truly blessed is the soul that, night and day, has no other anxiety than this: how, when the great day comes -- when all creation stands before the Judge and gives an account of its deeds -- she too may pass her reckoning with ease.

For whoever keeps that day and that hour always before them, and constantly reflects on the defense they will need before a tribunal where no excuses will avail, will sin either not at all or not seriously. We begin to sin when the fear of God fails in us. When people have a clear picture of what awaits them, the awe within them will never let them fall into reckless action or thought.

So keep God in your mind. Hold the fear of him in your heart. Enlist everyone you can to join you in prayer, for great is the help of those who are able to move God by their persistence. Never stop doing this. While we live in the flesh, prayer will be a mighty helper. And when we depart from this life, it will be provision enough for the journey to the world to come.

Concern for your soul is a good thing. But despondency, dejection, and despair of salvation -- these are poison to the soul. Trust in the goodness of God. Look for his help. Know that if we turn to him rightly, he will not withhold his mercy."""),

(986, """From: Basil, Bishop of Caesarea
To: Count Magnenianus
Date: ~367 AD
Context: Basil refuses a request to write a formal treatise on the faith, suspecting it would only be used as ammunition by his detractors, and insists the ancient creed is sufficient.

Your excellency wrote to me recently, charging me among other things to write a statement on the faith. I admire your zeal, and I pray God that your commitment to what is good will hold firm, and that as you grow in knowledge and good works you may be brought to perfection.

But I have no wish to leave behind me yet another treatise on the faith, or to draft alternative creeds, and so I have declined your request.

You seem to me to be surrounded by the noise of your associates there -- idle men who say things to slander me, imagining they can improve their own standing by telling disgraceful lies about mine. What they are, the past has already shown. Future experience will make it even plainer.

I call on everyone who trusts in Christ: do not busy yourselves inventing alternatives to the ancient faith. As we believe, so let us be baptized. As we are baptized, so let us offer our praise. It is enough for us to confess the names we have received from Holy Scripture and to resist all innovation concerning them. Our salvation does not depend on inventing new forms of address. It depends on a sound confession of the Godhead in which we have placed our faith."""),

(987, """From: Basil, Bishop of Caesarea
To: Amphilochius, Bishop of Iconium
Date: ~367 AD
Context: Basil invites Amphilochius to Caesarea for the annual festival honoring the martyrs, asking him to come a few days early so they can talk at leisure.

God grant that when this letter reaches your hands, it finds you healthy, at leisure, and just as you would wish to be -- for then my invitation will not be in vain.

I am asking you to come to our city, to add greater dignity to the annual festival our church holds in honor of the martyrs. Let me assure you, my most honored and dear friend, that although our people here have experienced many visitors, they desire no one's presence as eagerly as yours. The brief time you spent with them has left a remarkably warm impression.

So then -- that the Lord may be glorified, the people delighted, the martyrs honored, and that I in my old age may receive the attention due me from my true son -- do not refuse to come with all speed. I would ask you to arrive three days before the assembly, on September 5th, so that we may have time to talk at leisure and comfort one another by sharing spiritual gifts.

Please also honor with your presence the church at the Hospital [Basil's famous charitable institution, the Basiliad, which included a hospital, hospice, and church].

May you be kept in good health and good spirits by the grace of the Lord, praying for me and for the Church of God."""),

(988, """From: Basil, Bishop of Caesarea
To: Sophronius, the Master [Magister Officiorum, a senior imperial official]
Date: ~367 AD
Context: A letter of recommendation asking Sophronius to take up the case of a cleric named Eusebius who faces false charges.

To reckon up everyone who has received kindness at your excellency's hands on my account would be no easy task -- so many have benefited through your generous help, a blessing the Lord has given me in these very difficult times.

Worthiest of all these is the man now introduced to you by this letter: the reverend brother Eusebius, who faces a ridiculous accusation that only you, in your uprightness, have the power to destroy. I beg you, therefore, both out of respect for justice and out of your natural humanity, to grant me your usual favor: take up Eusebius's cause as your own and champion both the man and the truth.

It is no small thing that right is on his side. If he is not crushed by the present crisis, he will have no difficulty proving this plainly and beyond any contradiction."""),

(989, """From: Basil, Bishop of Caesarea
To: Aburgius
Date: ~367 AD
Context: Another letter of recommendation on behalf of the same Eusebius, asking that he be given a fair hearing rather than swept up in general suspicion.

I know I have recommended many people to your excellency over the years, and in serious emergencies have been of real use to friends in distress. But I do not think I have ever sent you anyone I regard more highly, or anyone involved in a more important case, than my dear son Eusebius, who now places this letter in your hands.

He will inform your excellency himself, if given the chance, of the difficulties he faces. But I must say at least this much: the man should not be prejudged. Just because many others have been convicted of shameful acts, he should not fall under a blanket of suspicion. He deserves a fair trial. His life should be examined on its own merits. When that happens, the falseness of the charges against him will become plain, and he -- having enjoyed your righteous protection -- will forever proclaim what he owes to your kindness."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Basil translations (IDs: 985-989)")

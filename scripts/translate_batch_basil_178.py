#!/usr/bin/env python3
"""Batch translate Basil letters 168-173 (IDs 979-984)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(979, """From: Basil, Bishop of Caesarea
To: Antiochus
Date: ~367 AD
Context: Basil consoles Antiochus, who is now in the company of an exiled bishop, and urges him to appreciate the blessing of time spent with a great teacher.

I grieve for the church that has lost the guidance of such a shepherd. But I have all the more reason to congratulate you on being privileged to enjoy, at a time like this, the company of a man fighting so noble a fight for the truth. I am confident that you, who so generously support and encourage his zeal, will be counted worthy by the Lord of a share in his reward.

What a blessing -- to enjoy, in unbroken peace, the company of someone so rich in learning and experience! Now, at last, you must surely know how wise he is. In the old days his mind was necessarily pulled in many directions, and you were too busy a man to give your full attention to the spiritual fountain that flows from his pure heart. May God grant that you will always be a comfort to him and never yourself need comfort from others.

I am confident of your heart's disposition, both from the brief time I have known you and from the exalted teaching of your illustrious instructor -- a man with whom a single day spent is provision enough for the whole journey to salvation."""),

(980, """From: Basil, Bishop of Caesarea
To: Gregory [Gregory of Nazianzus, his closest friend]
Date: ~367 AD
Context: Basil recounts the outrageous behavior of the deacon Glycerius, who abandoned his post, gathered a group of young women into an unauthorized convent under his personal control, defied all authority, and finally absconded with some of them in the night.

My dear Gregory,

You have taken on a generous and charitable task in rounding up the runaway flock of the insufferable Glycerius (I must call him that for now) and, as far as you could, covering up our shared embarrassment. It is only right that you should know the full facts before trying to undo the damage.

This grave and dignified Glycerius of yours was ordained by me as deacon of the church at Venesa, to serve under the presbyter and look after the practical work of the church. The man is impossible in other respects, but he does have a natural talent for manual labor. No sooner was he appointed than he neglected every duty, as though there were nothing to do. Instead, on his own authority and by his own initiative, he gathered together a group of unfortunate young women -- some who came to him of their own accord (you know how susceptible the young are to this sort of thing) and others who were dragged in unwillingly. He then adopted the title and manner of a patriarch, and began playing the man of dignity overnight.

His motive was not piety but survival -- he wanted a livelihood, the way other men take up a trade. He has all but destroyed the entire church, scorning his own presbyter (a man venerable in both character and years), scorning his chorepiscopus [a rural bishop subordinate to the main bishop], and treating me as though I were nobody at all -- filling the town and clergy with constant disorder and turmoil.

When his chorepiscopus and I mildly rebuked him -- not harshly, just firmly enough that he would not treat us with open contempt or stir the younger clergy into similar defiance -- he responded with something truly outrageous. He rounded up as many of the young women as he could and fled in the night.

Consider the timing. A feast was being celebrated. Crowds had gathered, as was natural. And in the middle of all that, he bolted. I am sure you find this as painful to hear as it is for me to tell."""),

(981, """From: Basil, Bishop of Caesarea
To: Glycerius
Date: ~367 AD
Context: Basil directly addresses the fugitive deacon Glycerius with a short, fierce ultimatum -- return or face permanent consequences.

Glycerius,

How far will your madness go? How long will you plot mischief against yourself? How long will you keep provoking my anger and bringing shame on the entire community of monks and solitaries?

Come back. Put your trust in God, and in me -- I who imitate God's mercy. I rebuked you as a father; as a father I will forgive you. You will receive that treatment from me, and many others are pleading on your behalf -- above all your own presbyter, whose grey hair and compassionate nature I deeply respect.

But stay away any longer and you will have fallen completely from your position. You will also fall away from God. For with your hymn-singing and your monastic garb, you are not leading those young women to God. You are leading them to destruction."""),

(983, """From: Basil, Bishop of Caesarea
To: Sophronius, Bishop
Date: ~367 AD
Context: Basil warmly welcomes a letter from a like-minded bishop and reflects on how rare genuine fellowship has become in a time of theological division.

There is no need for me to describe how much your letter delighted me -- your own words will let you guess what I felt on reading them. In your letter you displayed the first fruit of the Spirit: love. What could be more precious to me right now, when, "because iniquity abounds, the love of many has grown cold" [Matthew 24:12]? Nothing is rarer in our time than spiritual communion with a brother, a word of peace, and the kind of fellowship I have found in you. For this I thank the Lord, praying that I may share in the complete joy that is yours.

If your letter alone has this effect on me, what must it be like to meet you in person? If you move me this deeply from far away, what would you be to me face to face?

Believe me, if I were not held down by countless obligations and unavoidable anxieties, I would have hurried to see your excellency. My old ailment is a serious obstacle to travel, but in view of the good I would gain, I would not have let even that stop me.

To be allowed to meet a man who shares our convictions and honors the faith of the Fathers -- as our worthy fellow presbyters report of you -- is truly to return to the ancient blessedness of the churches, when those suffering from unsound disputes were few, and all lived in peace: workers who obeyed the commandments and "needed not to be ashamed" [2 Timothy 2:15], serving the Lord with a plain and clear confession, keeping their faith in Father, Son, and Holy Spirit simple and inviolate."""),

(984, """From: Basil, Bishop of Caesarea
To: Theodora, a Canoness [a woman living under a religious rule]
Date: ~367 AD
Context: Basil writes to a consecrated woman about the difficulty of truly living the gospel life in all its small daily demands.

My friend Theodora,

I would write to you more often if I were confident my letters actually reached your hands. I worry that, given the unreliability of the people I depend on for delivery -- especially in these confused times -- many of them end up with other people entirely. So I wait until I'm scolded and eagerly asked for a letter, which at least proves the last one arrived.

But whether I write or not, one thing I never fail to do: I keep the memory of your excellency in my heart, and I pray the Lord to grant you the strength to finish the course of good living you have chosen.

It is no light thing, you know, for someone who has made a profession to follow through on everything it demands. Anyone can embrace the gospel life in principle. But very few of those I have known have carried out their duty in its smallest details, overlooking nothing the gospel requires. Very few have been consistent in keeping the tongue in check and the eye under guidance, as the gospel commands; in working with their hands in a way that is pleasing to God; in governing every movement of the body as the Creator intended from the beginning.

Proper dress. Watchfulness in the company of men. Moderation in eating and drinking. Avoiding excess in the acquisition of even necessary things. These sound small when merely listed, but I have found from experience that keeping them up consistently is no small struggle.

Then there is the perfection of humility: not dwelling on noble birth, not being puffed up by any natural advantage of body or mind, not allowing other people's good opinion to become a source of pride. All this belongs to the gospel life. And beyond it there is sustained self-discipline, constant effort, and the daily labor of keeping the soul awake. The road is narrow, but the destination makes every step worthwhile."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Basil translations (IDs: 979-984)")

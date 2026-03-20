#!/usr/bin/env python3
"""Batch translate Basil letters 162-167 (IDs 974-978)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(974, """From: Basil, Bishop of Caesarea
To: Eusebius, Bishop of Samosata
Date: ~366 AD
Context: Basil, gravely ill, explains why he cannot visit his dear friend Eusebius and describes his symptoms with characteristic frankness.

The same thing that makes me hesitate to write also proves that I must. When I think of the visit I owe you and calculate how much I would gain from seeing you in person, letters seem worthless -- not even shadows compared to the reality. But then, when I consider that my only consolation, cut off as I am from everything best and most important, is to greet a man like you and beg you (as I always do) not to forget me in your prayers -- well, then letters seem worth quite a lot after all.

I have not given up hope of visiting you. I would be ashamed to show so little confidence in your prayers that I couldn't expect to be transformed from an old man into a young one, if it came to that -- let alone from a sick, wasted invalid into someone merely a little stronger.

It's not easy to explain in words why I haven't come already. I am not only held back by actual illness, but I lack even the strength to give you a proper account of such complicated and overlapping ailments. I can only tell you that since Easter until now, fever, intestinal trouble, and digestive collapse have been drowning me like waves, not letting me lift my head above the surface. Brother Barachus may be able to describe my condition for you -- if not as severely as it deserves, at least clearly enough for you to understand the delay.

If you join wholeheartedly in praying for me, I have no doubt my troubles will pass."""),

(975, """From: Basil, Bishop of Caesarea
To: Count Jovinus
Date: ~366 AD
Context: Basil praises Jovinus's character as revealed in his letter and apologizes for being too ill to visit, directing him to Bishop Amphilochius for details.

One can see your soul in your letter. No painter can capture an outward likeness as precisely as written words can reveal the secrets of the heart. As I read, your words portrayed exactly your steadfastness, your genuine dignity, your unfailing sincerity -- and in all these things your letter greatly comforted me, though I could not see you in person.

So never pass up a chance to write to me. Give me the pleasure of conversing with you from a distance, since seeing you face to face is now forbidden by the wretched state of my health.

How serious it is, you will learn from the God-beloved bishop Amphilochius, who has been constantly at my side and can tell you fully what he has seen. The only reason I want you to know of my sufferings is so that you will forgive me going forward, and not hold it against me if I fail to come and see you. In truth, my loss requires your comfort more than my defense.

Had it been possible to come to you, I would have preferred a sight of your excellency to anything other men think worth striving for."""),

(976, """From: Basil, Bishop of Caesarea
To: Ascholius, Bishop of Thessalonica
Date: ~366 AD
Context: Basil responds with deep emotion to Ascholius's letter about a martyr from the Danube frontier, and reflects nostalgically on the unity of the early Church.

My dear Ascholius,

It would not be easy to say how much your letter delighted me. My words are too weak to express what I feel, but you should be able to guess it from the beauty of what you wrote. For what did your letter not contain? Love of God. A vivid account of the martyrs that put their struggle so plainly before my eyes I felt I was watching it unfold. Love and kindness toward me. Words of surpassing beauty.

When I took it into my hands and read it again and again, and sensed how abundantly full it was of the Spirit's grace, I felt transported back to the good old days -- when God's churches flourished, rooted in faith, united in love, every member in harmony as though part of one body. In those times the persecutors were out in the open, and so were the persecuted. The congregations grew larger the more they were attacked. The blood of the martyrs, watering the churches, nourished still more champions of the faith, each generation entering the struggle with the same fire as those who went before. In those days we Christians were at peace with one another -- the peace the Lord left us, which we have since driven away so cruelly that not a single trace of it remains.

Yet my soul did go back to that ancient blessedness when your letter arrived from a great distance, radiant with the beauty of love, and when a martyr came to me from wild regions beyond the Danube, preaching in his very person the exactness of the faith observed in those lands. Who could describe my joy? What words could capture what I felt?

When I saw the athlete, I blessed his trainer. He too, before the just Judge, after strengthening so many for the struggle on behalf of true religion, will receive the crown of righteousness."""),

(977, """From: Basil, Bishop of Caesarea
To: Ascholius, Bishop of Thessalonica
Date: ~366 AD
Context: A second letter to Ascholius, celebrating a martyr sent from the Danube region and rejoicing that Ascholius -- originally from Basil's own country -- has borne such fruit abroad.

God has answered an old prayer of mine in allowing me to receive a letter from your true holiness. What I desire most of all is to see you and be seen by you, and to enjoy in person all the graces of the Spirit with which you are endowed. But this is impossible, both because of the distance between us and the demands pressing upon each of us. So my second prayer is that my soul may be nourished by frequent letters from you in Christ's love. And this has now been granted.

Taking your letter in my hands, I was doubly delighted. I felt as though I could see your very soul shining through your words as in a mirror, and I was moved to great joy -- not only because you prove to be everything people say of you, but because your noble qualities are an ornament to my own country. You have filled the land beyond our borders with spiritual fruit, like a vigorous branch sprung from a glorious root. Rightly, then, does our homeland rejoice in her own offspring. When you were fighting for the faith she heard that the heritage of the Fathers was preserved in you, and she glorified God.

And now see what you have done: you have honored the land that gave you birth by sending her a martyr who has just fought his good fight in the barbarian country on your borders -- like a grateful gardener sending his first fruits back to those who gave him the seeds. The gift is truly worthy of Christ's athlete: a witness to the truth, just crowned with the crown of righteousness, whom we have gladly welcomed, glorifying God who has now fulfilled the gospel of his Christ in all the world.

Remember me in your prayers, and earnestly beseech the Lord on my soul's behalf that one day I too may be found worthy to begin truly serving God according to his commandments."""),

(978, """From: Basil, Bishop of Caesarea
To: Eusebius, Bishop of Samosata
Date: ~367 AD
Context: A brief, warm note thanking Eusebius for writing and reflecting on the honor of being remembered by such a man.

I am delighted that you remember me and write, and what matters even more, that you send me your blessing in your letter. Had I been worthy of your labors and your struggles for Christ's cause, I would have been allowed to come to you, embrace you, and take you as a model of patience. But since I am not worthy of this, and am held back by many afflictions and much business, I do the next best thing: I greet your excellency and beg you not to grow tired of remembering me.

The honor and pleasure of receiving your letters is not only a benefit to me personally -- it is something I can boast of before the world: that I am held in regard by a man whose virtue is so great, and whose communion with God is so close, that by both his teaching and his example he draws others into that same communion."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Basil translations (IDs: 974-978)")

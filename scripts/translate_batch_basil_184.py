#!/usr/bin/env python3
"""Batch translate Basil letters 203-207 (IDs 1014-1018)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(1014, """From: Basil, Bishop of Caesarea
To: The bishops of the sea coast [the bishops of Pontus, along the Black Sea]
Date: ~369 AD
Context: A lengthy appeal to coastal bishops urging them to visit and stand in solidarity, comparing his isolated position defending orthodoxy to a rock enduring heretical waves.

I have longed to meet you, but time and again something has intervened to prevent it -- whether my illness (which has been my constant companion from youth to old age, a chastisement ordained by God's righteous judgment), or the cares of the Church, or my struggles against the opponents of true doctrine.

To this day I live in great sorrow, keenly feeling your absence. For when God -- who took on flesh specifically to give us patterns of duty and to announce the gospel of the kingdom in his own voice -- tells us, "By this shall all men know that you are my disciples, if you love one another" [John 13:35], and when the Lord left his own peace to his disciples as a farewell gift, saying "Peace I leave with you; my peace I give you" [John 14:27], I cannot persuade myself that without love for others and peaceableness toward all, I can be called a worthy servant of Jesus Christ.

I have waited a long time for your love to bring you to visit us. For you know that we are exposed on all sides, like rocks jutting into the sea, sustaining the fury of heretical waves -- waves which, because they break against us, do not reach the district behind. I say "we" not to claim any human power, but to acknowledge the grace of God, who shows his strength through human weakness, just as the prophet says in the Lord's voice: "Will you not fear me, who have set the sand as a boundary to the sea?" [Jeremiah 5:22] -- for by the weakest and most insignificant of things, sand, the Almighty has bounded the vast ocean.

[This letter continues with an extended plea for unity, mutual visits, and coordinated action against Arianism across the coastal churches.]"""),

(1015, """From: Basil, Bishop of Caesarea
To: The Neocaesareans
Date: ~369 AD
Context: A major letter to the church of Neocaesarea -- the hometown of Gregory Thaumaturgus -- addressing a long estrangement and defending Basil against charges of theological innovation, particularly regarding the Holy Spirit.

Beloved brothers,

There has been a long silence on both sides, as though anger lay between us. Yet who is so sullen and unforgiving as to prolong his resentment through nearly a whole lifetime? This is what is happening between us, though I know of no just cause for estrangement. On the contrary, from the very beginning there have been many strong reasons for the closest friendship and unity.

The greatest of these is our Lord's own command: "By this shall all men know that you are my disciples, if you have love for one another" [John 13:35]. Again, the apostle says plainly that "love is the fulfilling of the law" [Romans 13:10], and that love is to be preferred above all great and good things: "Though I speak with the tongues of men and of angels and have not love, I have become sounding brass or a clanging cymbal. And though I have the gift of prophecy and understand all mysteries and all knowledge, and though I have all faith so as to remove mountains, and have not love, I am nothing" [1 Corinthians 13:1-3].

Furthermore, if it draws people together to share the same teachers, we have the same spiritual fathers -- the founders of your church. I mean the great Gregory [Gregory Thaumaturgus, the famous wonder-working bishop of Neocaesarea] and all who succeeded him in an unbroken line...

[This substantial letter continues with Basil's defense of his liturgical and theological practices, particularly his doxological formula glorifying the Holy Spirit alongside the Father and the Son, and his argument that this represents authentic tradition rather than innovation.]"""),

(1016, """From: Basil, Bishop of Caesarea
To: Elpidius, Bishop
Date: ~369 AD
Context: Basil sends the presbyter Meletius as a living letter, proposes a gathering of coastal bishops, and stresses that without love, obedience to every commandment is worthless.

Once again I have sent the beloved presbyter Meletius to carry my greeting to you. I had firmly resolved to spare him, given the weakness he has voluntarily brought on himself by disciplining his body for the sake of Christ's gospel. But I judged it fitting to greet you through a man like him -- one capable of making up for all the shortcomings of my letter and serving as a kind of living epistle for both of us. I am also fulfilling his long-standing wish to see your excellency, a desire he has held ever since he came to know your fine qualities.

Through him I discharge the debt of the visit I owe you, and I ask you to pray for me and for the Church of God -- that the Lord may deliver me from the assaults of the gospel's enemies and let me live in peace and quiet.

If, however, you think it wise that we should travel to a common meeting place and gather with the rest of our honorable brother bishops from the coastal regions, please suggest a suitable place and time. Write to our brothers so that each may set aside his business at the appointed hour. In this way we may accomplish something for the building up of God's churches, put an end to the pain of our mutual suspicions, and restore the love without which the Lord himself has decreed that obedience to every commandment is worthless."""),

(1017, """From: Basil, Bishop of Caesarea
To: Elpidius, Bishop (a letter of consolation)
Date: ~369 AD
Context: Basil consoles Elpidius on the death of his grandson and urges him not to let grief prevent their planned meeting.

Now more than ever I feel the burden of my bodily weakness, seeing how it obstructs the good of my soul. Had things gone as I hoped, I would not be speaking to you by letter or through a messenger, but would have come in person to pay the debt of affection and enjoy spiritual fellowship face to face. As it is, I count myself fortunate if I can even manage the necessary parish visits in my own district.

But may the Lord give you both strength and willing spirit, and grant me -- on top of my eager desire -- the ability to enjoy your company when I am in the region of Comana.

I am afraid that your domestic sorrow may hold you back, for I have learned of your grief at the loss of your little grandson. To a grandfather his death cannot help but be painful. On the other hand, to a man who has reached such heights of virtue and who knows, from both worldly experience and spiritual training, what human nature is, the loss of those near and dear should not be wholly unbearable. The Lord expects more of us than he does of everyone. The common run of humanity lives by habit, but the Christian's rule of life is the Lord's commandment and the example of holy people of old -- whose greatness of soul showed itself above all in adversity.

So that you may leave to those who come after you a model of endurance and genuine trust in what we hope for, show that you are not conquered by grief but rising above it -- patient in affliction, rejoicing in hope.

Please do not let this stand in the way of our planned meeting. Children are held blameless because of their tender age, but you and I bear the responsibility of serving the Lord and managing the affairs of his Church."""),

(1018, """From: Basil, Bishop of Caesarea
To: The clergy of Neocaesarea
Date: ~369 AD
Context: A fiery letter to hostile clergy who have been spreading slanders about Basil, accusing him of Sabellianism, and criticizing his liturgical innovations -- particularly his practice of congregational psalm-singing.

You all agree in hating me. To a man you have followed the ringleader of the campaign against me. I was therefore inclined to say nothing at all -- to write no friendly letter, initiate no communication, and keep my grief to myself in silence. Yet it is wrong to stay silent in the face of slander: not so that we may defend ourselves through counter-arguments, but so that we may prevent a lie from spreading further and doing more harm.

So I have thought it necessary to write to you all, even though when I recently wrote to the entire body of presbyters, you did not do me the honor of a reply.

Brothers, do not feed the vanity of those who are filling your minds with destructive opinions. Do not sit idle while God's people are subverted by impious teaching. No one but Sabellius the Libyan [who denied the distinct persons of the Trinity, merging them into one] and Marcellus the Galatian [who held similar modalist views] has ever dared to teach or write what your leaders are now trying to pass off as their own discovery. They make a great noise about it, but they are completely unable to give their sophistry even a veneer of truth.

In their attacks on me they stop at nothing shameless, while stubbornly refusing to meet me face to face. Why? Because they are afraid of being convicted for their own wicked views. They have lost all shame to the point of inventing dream-visions to discredit me, while falsely accusing my teaching of being dangerous. Let them take their autumn visions on their own heads -- they cannot pin any blasphemy on me, for in every church there are many who can testify to the truth.

When asked the reason for this furious and relentless war, they point to our psalm-singing and a style of music that differs from your local custom..."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Basil translations (IDs: 1014-1018)")

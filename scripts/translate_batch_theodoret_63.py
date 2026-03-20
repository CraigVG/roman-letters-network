#!/usr/bin/env python3
"""Batch translate Theodoret letters 51-55 (IDs 4259-4263)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(4259, """From: Theodoret, Bishop of Cyrrhus
To: Agapius, Presbyter
Date: ~440 AD
Context: Theodoret praises Agapius's eloquent testimony about Bishop Thomas and reports having warmly received the bishop before sending him back to his duties.

To the Presbyter Agapius,

The works of virtue are admirable in themselves, but they appear even more admirable when they find an eloquence able to do them justice. Neither advantage has been lacking in the case of our God-beloved bishop, the lord Thomas: he has contributed his own labors on behalf of the faith, and he has found in your holiness a voice to give those labors their proper praise.

Coming to us with such a recommendation, we were all the more delighted to see him. After enjoying his company for a short while, we have sent him back to his responsibilities."""),

(4260, """From: Theodoret, Bishop of Cyrrhus
To: Ibas, Bishop of Edessa
Date: ~440 AD
Context: Theodoret reflects on the Vandal devastation of North Africa as a providential warning and introduces Bishop Cyprianus, an African refugee seeking hospitality across the eastern churches.

To Ibas, Bishop of Edessa [one of the major cities of Roman Mesopotamia, modern Urfa in southeastern Turkey],

I believe it is part of God's providential care for our common salvation that he allows certain calamities to fall upon some people. For the chastened, such misfortunes become a healing remedy. For those already striving toward virtue, they are an encouragement to hold firm. And for everyone who witnesses them, they serve as a powerful example -- since it is natural, when we see others punished, to be seized by fear ourselves.

With these thoughts in mind, I view the disaster in Africa [the Vandal conquest of Roman North Africa, which devastated the Catholic church there] as carrying a lesson for all of us. When I recall their former prosperity and then contemplate their sudden ruin, I see how unstable all human affairs are, and I learn a double lesson: not to rejoice in good fortune as though it will last forever, and not to be crushed by calamity as though it were unbearable. Then I remember my own past failings, and I tremble at the thought of suffering a similar fate.

My main reason for writing, however, is to introduce to your holiness the deeply devout bishop Cyprianus. He has come from that famous Africa and is now compelled by the barbarians' savagery to wander through foreign lands. He carries a letter of introduction from the most holy bishop Eusebius, who wisely governs the Galatians.

When your piety has received him with your customary kindness, I ask you to send him on with letters to whatever faithful bishops you think fitting, so that while he enjoys their consolation, he may in turn be the means of their receiving heavenly and lasting blessings."""),

(4261, """From: Theodoret, Bishop of Cyrrhus
To: Sophronius, Bishop of Constantina
Date: ~440 AD
Context: Theodoret asks the generous Sophronius to help the displaced African bishop Cyprianus and forward him to other sympathetic bishops.

To Sophronius, Bishop of Constantina,

Since I know, beloved of God, how generous and bountiful your right hand is, I am placing a precious opportunity within your reach. Men who hunger after worldly gain are annoyed at the sight of those who need financial help. But the generous are delighted -- because the riches they seek are heavenly.

The man who brings you this opportunity is the God-beloved bishop Cyprianus. He was once known for his ministry to others, but now, bearing a heartbreaking account of the African catastrophe, he must depend on the generosity of the faithful.

I trust that he will enjoy your brotherly kindness and be sent on with letters to other havens of refuge."""),

(4262, """From: Theodoret, Bishop of Cyrrhus
To: [unnamed recipients, a festal letter]
Date: ~440 AD
Context: A short festal letter in which Theodoret admits that the joy of a Christian feast has lifted him from despair.

Festal greeting.

Our divine and saving celebrations both cheer the downhearted and add to the joy of the already joyful. I know this from personal experience: when I was drowning in waves of despair, the sight of the feast's harbor lifted me above the storm.

May your piety pray that I am fully rescued from these waters, and that our loving Lord grants me the mercy of forgetting my sorrow."""),

(4263, """From: Theodoret, Bishop of Cyrrhus
To: [unnamed recipient, a festal letter]
Date: ~440 AD
Context: A very brief Epiphany greeting acknowledging personal distress but finding solace in the feast.

Festal greeting.

We are in great distress -- for we are made of flesh, not stone. But the remembrance of the Lord's Epiphany [the feast celebrating Christ's baptism and manifestation to the world] has proved a powerful medicine. So at once I write, as the custom of the feast requires, and greet your magnificence with a prayer that you may live in prosperity and good repute."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Theodoret translations (IDs: 4259-4263)")

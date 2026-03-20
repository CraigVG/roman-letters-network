#!/usr/bin/env python3
"""Batch translate Theodoret letters 101-105 (IDs 4309-4313)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(4309, """From: Theodoret, Bishop of Cyrrhus
To: Celarina, Deaconess
Date: ~440 AD
Context: Theodoret writes to a prominent deaconess about renewed accusations that he teaches "two sons" (dividing Christ's divine and human natures into separate persons), and asks her to support the bishops traveling to Constantinople to defend orthodoxy.

To the Deaconess Celarina,

The flames of the war against us have been lit again. After yielding for a time, the enemy of mankind has armed against us once more -- men nurtured on lies who openly slander me, claiming that I divide our one Lord Jesus Christ into two sons.

I, however, know the distinction between Godhead and manhood, and I confess one Son: God the Word made man. I affirm that he is God eternal, who became man at the end of days -- not through any change in the Godhead, but through the assumption of human nature.

There is no need to explain my views to your piety at length, for you have precise knowledge of what I preach and how I instruct the uninformed.

But I beg you: since these fabricators of lies have poured their insults on all the godly bishops of the East at once and overwhelmed the churches with a storm, show all possible zeal on behalf of the gospel teaching and the peace of the churches. The most devout bishops have left the churches in their care, braved the harshness of winter, and endured the hardships of a long journey in order to calm the tempest. I am confident that your pious excellency will receive them as champions of the faith and guardians of the churches."""),

(4310, """From: Theodoret, Bishop of Cyrrhus
To: Basilius, Bishop
Date: ~440 AD
Context: Theodoret reproaches a bishop friend for not defending him against theological slanders, pointedly quoting Scripture on the duty not to stay silent in the face of injustice.

To Bishop Basilius,

There is nothing surprising in strangers who do not know me listening in silence to the slanders against me. But that your holiness -- who does know me -- should fail to refute my accusers' lies, or at best do so halfheartedly, is beyond what anyone who knows your character would believe.

I say this not because friendship ought to take precedence over truth, but because the witness of truth is on friendship's side. Your reverence has heard me preach in church many times. In other gatherings where I have spoken on doctrine, you have listened to what I said. I am not aware of any occasion when you found fault with my orthodoxy.

So what is happening now? Why in the world, my dear friend, do you not speak a single word against falsehood, while you allow a friend to be slandered and the truth to be assaulted?

If your silence is because you look down on the helpless and insignificant, remember the Lord's plain command: "Take heed that you despise not one of these little ones who believe in me, for I tell you that in heaven their angels always behold the face of my Father" [Matthew 18:10]. But if it is the influence of my accusers that has silenced you, then listen to this other law: "You shall not honor the person of the mighty" [Leviticus 19:15], and "Judge righteous judgment," and "You shall not follow a multitude to do evil" [Exodus 23:2].

You could find countless similar passages in Scripture. I thought it unnecessary to pile them up when writing to a man raised on the divine word."""),

(4311, """From: Theodoret, Bishop of Cyrrhus
To: Count Apollonius
Date: ~440 AD
Context: A brief letter sent via traveling bishops, reflecting philosophically on calumny as an inevitable human experience.

To the Count Apollonius,

The most devout bishops have been driven to travel to the capital by the slanders directed against me. Through their holinesses I send your excellency my greeting and pay the debt of friendship -- not to cancel that cherished obligation, but to increase it. For the debts of friendship grow larger with each payment.

That I should now be reaping the fruits of calumny is hardly extraordinary. Being human, I must expect anything. All troubles of this kind must be borne by those who have learned wisdom. Only one thing is truly distressing: that harm should come to the soul."""),

(4312, """From: Theodoret, Bishop of Cyrrhus
To: Flavianus, Bishop of Constantinople [Flavian, who would later be physically assaulted at the "Robber Council" of Ephesus in 449]
Date: ~440 AD
Context: A crucial doctrinal letter in which Theodoret defends his Christology to the patriarch of Constantinople, insisting he has never taught "two sons" and explaining his distinction between Christ's divine and human natures within one person.

To Flavianus, Bishop of Constantinople,

I have already informed your holiness in another letter how openly my accusers are slandering my teaching. Now I do the same through these most devout bishops, who serve as witnesses to my orthodoxy -- along with the countless others who have heard me preach in the churches of the East. Beyond all these, I have my conscience, and the One who sees my conscience. I know that the divine apostle often appealed to the testimony of his conscience: "Our boasting is this: the testimony of our conscience" [2 Corinthians 1:12], and again, "I speak the truth in Christ, I do not lie, my conscience bearing me witness in the Holy Spirit" [Romans 9:1].

Know then, holy and revered sir, that no one has ever at any time heard me preach two sons. That doctrine seems to me abominable and impious. For "there is one Lord Jesus Christ, through whom are all things" [1 Corinthians 8:6]. Him I acknowledge as both eternal God and man in the last days, and I give him one worship as Only-Begotten.

I have, however, learned to distinguish between flesh and Godhead, for the union is unconfused [a key Antiochene Christological term: the two natures are united but not blended into each other]. Thus, drawn up in battle formation against the madness of Arius and Eunomius, we easily refute their blasphemy against the Only-Begotten: we apply what was spoken in humility about the Lord -- what belongs fittingly to his assumed nature -- to the man, and what is appropriate to the divine nature and signifies divinity, to God. We do not divide him into two persons. We teach that both sets of attributes belong to the Only-Begotten: the divine because he is God, Creator, and Lord of all; the human because he was made man for our sake.

For divine Scripture says that he was made man not by change of the Godhead but by assumption of the manhood..."""),

(4313, """From: Theodoret, Bishop of Cyrrhus
To: Eulogius, the Oeconomus [financial administrator of a church]
Date: ~440 AD
Context: A brief appeal to a church administrator known for defending orthodoxy, asking him to counter the slanders against Theodoret.

To Eulogius the Oeconomus,

We have heard from many quarters of your piety's efforts on behalf of true religion. It is therefore only right that you should readily support someone being slandered for the same cause, and refute the liars' accusations.

You, revered sir, know what I believe and what I teach. No one has ever heard me preach two sons. Bring to bear, I implore you, your characteristic energy in this case as well, and stop the mouths of those who speak evil.

In battles like this one must help not only one's friends, but even those who have caused us pain."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Theodoret translations (IDs: 4309-4313)")

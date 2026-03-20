#!/usr/bin/env python3
"""Batch translate Theodoret letters 76-80 (IDs 4284-4288)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(4284, """From: Theodoret, Bishop of Cyrrhus
To: Uranius, Governor of Cyprus
Date: ~440 AD
Context: Theodoret writes to a pagan governor he admires, celebrating news that Uranius may be moving toward the Christian faith and using the metaphor of Christ as a divine fisherman who catches souls for life rather than death.

To Uranius, Governor of Cyprus,

True friendship is strengthened by contact, but separation cannot sever it -- its bonds are too strong. This truth could be demonstrated by many examples, but it is enough to prove it from our own case. Many things stand between you and me -- mountains, cities, the sea -- yet none of them has destroyed my memory of your excellency. The moment anyone arrives from the coastal towns, our conversation turns to Cyprus and its worthy governor, and we are delighted to hear of your high reputation.

Lately we have been pleased beyond our usual measure, for we have learned the most welcome news of all. What, most excellent sir, could please us more than to see your noble soul illuminated by the light of divine knowledge? We have always thought it fitting that a man adorned with so many virtues should add the crown to them all, and we trust that we shall see our hope fulfilled. For your nobility will surely seize this God-given treasure eagerly, moved by true friends who understand its value, and guided toward the generous God "who wills all men to be saved and to come to the knowledge of the truth" [1 Timothy 2:4].

God catches men through human means, and brings his captives to the ageless life. A fisherman deprives his catch of life, but our divine Fisher frees all he catches from the painful bonds of death. For this reason he appeared on earth and lived among us -- bringing life to humanity, conveying his teaching through his visible manhood, and giving to rational beings the law of a fitting life and conduct."""),

(4285, """From: Theodoret, Bishop of Cyrrhus
To: Eulalius, Bishop of Persian Armenia
Date: ~440 AD
Context: A powerful letter of encouragement to a bishop facing persecution under a hostile regime, likely during the Sassanid persecutions of Christians in the Persian Empire.

To Eulalius, Bishop of Persian Armenia,

I know that Satan has sought "to sift you as wheat" [Luke 22:31], and that the Lord has allowed it -- so that he might display the wheat, prove the gold, crown the athletes, and proclaim the victors' names. Nevertheless, I fear and tremble. Not for your sake -- you are noble champions of the truth. But I know that some men are weaker of heart. If among twelve apostles one was found a traitor, there is no doubt that among a far greater number one might easily discover many falling short of perfection.

Reflecting on this, I have been troubled and filled with discouragement, for as the divine apostle says, "when one member suffers, all the members suffer with it" [1 Corinthians 12:26]. We are members of one another and form one body, with the Lord Christ as our head.

Yet I have one consolation in my anxiety: the thought of your holiness. Raised as you have been on the divine Scriptures, taught by the chief Shepherd what marks the good shepherd, I have no doubt that you will lay down your life for the sheep. For as the Lord says, "the hired hand, when he sees the wolf coming, flees, because he is a hired hand and cares nothing for the sheep. But the good shepherd lays down his life for the sheep" [John 10:12-13].

It is not in peacetime that a great general shows his true valor but in war -- by rallying his men and putting himself in harm's way for their sake. It would be absurd for a commander to enjoy the privileges of his rank and then run from danger when the moment comes.

This is how the thrice-blessed prophets always acted: making nothing of their own safety, enduring every kind of suffering for the sake of the very people who hated and rejected them."""),

(4286, """From: Theodoret, Bishop of Cyrrhus
To: Eusebius, Bishop of Persian Armenia
Date: ~440 AD
Context: Theodoret urges Eusebius to step up as acting leader of the church when the senior bishop has fallen, drawing on the metaphor of the ship's officer taking the helm when the helmsman is lost.

To Eusebius, Bishop of Persian Armenia,

Whenever anything happens to the helmsman, the officer at the bow or the highest-ranking sailor takes his place -- not because he has appointed himself helmsman, but because he is looking out for the safety of the ship. In war, when the commander falls, the senior tribune assumes command -- not in a grab for power, but because he cares for his men. And the thrice-blessed Timothy, when sent by the divine Paul, stepped into Paul's role.

It is therefore fitting for your piety to accept the responsibilities of helmsman, captain, and shepherd. Run every risk gladly for the sake of Christ's sheep, and do not leave his flock abandoned and alone. It is yours to bind up the broken, raise up the fallen, turn the wanderer from his error, and keep the whole in health -- to follow the example of good shepherds who stand before the folds and wage war against the wolves.

Let us remember the words of the patriarch Jacob: "In the day the drought consumed me, and the frost by night, and my sleep departed from my eyes. The rams of your flock I have not eaten. That which was torn by beasts I did not bring to you; I bore the loss of it. From my hand you required it, whether stolen by day or stolen by night" [Genesis 31:40-39].

These are the marks of the true shepherd. These are the laws of tending sheep. And if the illustrious patriarch took such care of mere cattle and made this defense to the one who entrusted them to his charge, what ought we to do -- we who are entrusted with the care of rational sheep, who have received this charge from the God of all, and who remember that the Lord gave up his life for them?"""),

(4287, """From: Theodoret, Bishop of Cyrrhus
To: Anatolius, Patrician
Date: ~440 AD
Context: Theodoret reports being confined to Cyrrhus by imperial order, accused of stirring up synods and disturbing the orthodox. He protests his innocence and asks Anatolius to investigate whether the order is genuine.

To the Patrician Anatolius,

The Lord God has given your excellency to us as a great source of comfort in these times, providing a safe harbor in the storm. We therefore have confidence in bringing our distress to your lordship's attention.

Not long ago I informed your excellency that the right honorable Count Rufus had shown me an order written in the emperor's own hand, commanding the general to ensure with prudence and diligence that I remain at Cyrrhus and do not depart to any other city -- on the grounds that I have been assembling synods in Antioch and disturbing the orthodox.

I want you to know that in obedience to the imperial letter I have come to Cyrrhus. After six or seven days they sent the commander Euphronius with a letter requiring me to acknowledge in writing that the imperial order had been shown to me. I promised to remain in Cyrrhus and its surrounding district, and to tend the sheep entrusted to my care.

I therefore beg your excellency to make a thorough inquiry: were these orders actually issued, and for what reason? I am conscious of many sins, but I am not aware that I have offended either the Church of God or public order.

I write this not because I resent living in Cyrrhus -- in truth, she is dearer to me than the most famous cities, because God gave me my office here. But the fact that I am bound to her by compulsion rather than by choice is troubling. It gives the ill-disposed a handle to grow bold and refuse to obey our pastoral guidance.

If no such order was actually issued, I beg your lordship to set the matter right."""),

(4288, """From: Theodoret, Bishop of Cyrrhus
To: Eutrechius, Prefect
Date: ~440 AD
Context: Theodoret reproaches the prefect for not warning him about the imperial order confining him to Cyrrhus, and describes the widening crisis in the eastern churches.

To the Prefect Eutrechius,

I have been greatly astonished that your lordship sent me no warning of the plots against me. Counteracting them would admittedly have been difficult for anyone who lacked the means to expose the plotters' lies. But simply giving information about what was happening required not so much power as friendship -- and we had hoped that when your excellency was summoned to the capital and chosen to grace the prefect's exalted seat, every storm in the Church would be calmed.

Instead, the disturbances are worse than anything we saw at the beginning of the dispute. The churches of Phoenicia are in trouble. So are those of Palestine -- as everyone unanimously reports, and as the letters of the most devout bishops confirm. Every pious soul among us groans, and every faithful congregation grieves. While we were looking for our old troubles to end, new ones have been heaped upon us.

As for myself: I have been forbidden to leave the territory of Cyrrhus, if the document shown to me is authentic. It claims to be in the emperor's own handwriting, and it reads: "Since the bishop of this city is constantly assembling synods, which causes trouble to the orthodox, see to it with proper diligence and prudence that he resides at Cyrrhus and does not depart from it to another city."

I have accepted the sentence and remain where I am. Your lordship can testify to my intentions, for you know how on my arrival at Antioch I left in a hurry precisely because of those who wanted to keep me there.

Those who gave both ears to my accusers and would not save even one for me were certainly in the wrong. Even murderers and thieves are granted a hearing before they are sentenced."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Theodoret translations (IDs: 4284-4288)")

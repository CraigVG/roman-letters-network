#!/usr/bin/env python3
"""Batch translate Symmachus letters (IDs 5126, 5424, 4971, 5062, 5127)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(5126, """From: Quintus Aurelius Symmachus, Roman Senator
To: Protadius and Minervius (multiple short letters)
Date: ~371-399 AD
Context: Several letters bundled together: Symmachus playfully defends his silence to a friend, reflects on the labors of correspondence, and writes several recommendations to Minervius.

To a friend (~371 AD):

You enjoy my letters -- so you say! That must be why you demand them so often and so eagerly. But I should not be branded lazy just because I cannot satisfy your insatiable appetite for my writing. Do you really think friendship's memory fades through silence? Do not judge hearts that way -- their commitments are eternal. Loyalty carries its own weight and does not need the constant prod of a pen to remind it. I have written this to you more than once, yet you never abandon your old complaint. What if it is better to keep a long silence? Do you not see that the oracles have long since stopped speaking? No letters are read in the cave at Cumae [the famous Sibyl's grotto near Naples], Dodona [the ancient Greek oracle site] no longer whispers through its leaves, and no prophecy is heard from the vents at Delphi. Allow me then, a mere mortal shaped by Prometheus's hand, to stop committing to papyrus what has long since ceased to be written even on prophetic leaves. But do not suspect I am declaring permanent silence. I will write at intervals proportional to the distance between us. You too should master your impatience with reason -- it is unreasonable to expect daily letters delivered from the Tiber to the banks of the Rhine.

---

To Protadius (~395 AD):

The rewards I reap from your letters are great, but they grow richer when they pass through the hands of our mutual friends. Each one adds something of his own to what you have written. So I credit to you whatever I gather from everyone's conversation. But consider in return how much effort it costs me to reply to the varied brilliance of so many fine minds. You are all equals, yet no two of you are alike. So the task of replying brings me no less difficulty than the pleasure of receiving. Nature has imposed this law on all human joys: that care follows pleasure. A newborn child delights its parents on the first day, but soon anxious fears drive away that brief happiness. Honor is joyful at the start, then the heat of labor overtakes the spirit. It would take forever to string together more examples.

Let me turn to what I may properly say about so great a man. You have sworn rashly! You complain that my letters are being committed to perishable paper and you have backed up your extravagant judgment with an oath. Are you making a game of me -- insisting that my casual talk be transferred to wooden tablets or linden writing boards, lest the fragile old age of papyrus ruin your archive? The Marcian prophets, after all, had their divinations pressed into perishable bark, and the Cumaean prophecies were preserved on linen. Yet you would have my letters poured into silk scrolls in the Persian fashion! The weight of your authority is great, and I cannot dismiss what you assert under oath. But when I look at myself again, my confidence wavers, and my conscience contradicts your testimony. So what your standing as judge makes credible, my own self-doubt as listener rejects. You alone can settle the question -- by telling your affection to speak more sparingly in praise of me from now on.

---

To Minervius (~397 AD): You have stolen a march on my modesty by writing first. Consider me bound to you by this gift. But I cannot accept that you seem to be entering the house of our friendship as a new visitor. I long ago took your virtues -- equal to your brothers' -- into my heart's keeping. You have even grown into your legitimate share of the family friendship your father held with me, though each of you individually has gained the full measure of my love. The goods of the soul, though they may seem to be spread among many, nevertheless benefit each person fully and undivided. Moreover, since you serve in the imperial chancery's eloquence, I have extended the right hand of friendship to you. So bound as we are by so many pledges, let us not measure the age of our affection by when we first exchanged letters. For just as the heart is faster than correspondence, so love came before writing.

---

To Minervius (~396 AD): After word spread through travelers that you had arrived in Milan, I hoped for a letter from you shortly. But when my expectation was disappointed and no reward for my hope followed, I claimed for my own the courtesy I had expected from you. An additional reason for writing was my distinguished friend Bassus, who has been briefly pulled away from us and needed me to transfer him into your good graces. I have added a second page to be delivered to your brother when fortune grants you a return to your homeland. He had already sprinkled us with the flowers of his eloquence and had commissioned some ancient records of Gaul to be copied out during his leisure. It works out perfectly that through you he can receive both the honor of my letter and the fruit of the history he requested.

---

To Minervius (~398-399 AD): My friend Paulus has long served in the imperial treasury, but you should not judge him by his rank alone -- his integrity of character surpasses the modesty of his office. Do not look down on the man if you examine the number of his years of service. Advancement comes slowly to the modest, who tend to remain below what their merits deserve. Yet he does not regret standing still so long, for he was saved for your judgment, under which rising is the greatest reward for patience. Since his integrity of life and his years of service speak for him, it is fitting that he should reach his due rewards with me as his advocate and you as his patron."""),

(5424, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend in Spain (name lost)
Date: ~372 AD
Context: Symmachus writes about his son's upcoming praetorian games, asking a friend to stable racehorses over winter on his Spanish estates.

I take great pleasure whenever I receive one of your letters. They bring proof both of your good health and of your affection. I am especially glad that you promise to visit soon. To encourage you to hurry, I announce that my son, if divine favor smiles on us, will assume the praetorian fasces [take up the office of praetor, with its obligation to sponsor public games] in the coming year. I have written to you about this matter more fully through my household agents, whom I have charged with purchasing horses from Spain.

But since the opportunity presents itself, I press my request again: if winter storms should happen to delay the horses' return, please order them to be stabled on your estates for a few months and sent on to us when spring begins. Meanwhile, do not worry about your people here -- both my personal presence and my protection in the courts are defending them. I have warned the man bringing suit that the case concerns me directly, and that my legal support will not fail them. I have no doubt your people have already told you as much. Farewell."""),

(4971, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~372 AD
Context: Symmachus praises a recent law of Emperor Theodosius renouncing imperial claims to fideicommissa (testamentary trusts) and codicil bequests, while worrying that private greed will continue unchecked.

When I was surveying in writing the civil and military achievements of our lord Theodosius [Emperor Theodosius I, r. 379-395] -- I confess I touched on everything rather than doing justice to each -- I included his laws among the blessings of peace. I had known they had stripped the ancients of their claim to admiration, but I had not expected them to leave us an equal glory. Yet this recent decree concerning fideicommissa [trust bequests -- a common Roman legal device for indirect inheritance] and the benefits of codicils [supplementary wills], which the excellent emperor has permanently renounced, surpasses the brilliance of all previous legislation by as much as it is nobler to set limits on oneself than to impose them on one's subjects.

If only private greed would understand the mind of the lawgiver and draw its morals from his laws! It is no secret what a man who was first to recoil from suspect profits wants others to do voluntarily. I truly fear that the thirst of the unscrupulous will claim for themselves the windfall gains [bona caduca -- property that fell to the imperial treasury when intended heirs were disqualified], and that the position of honest men will grow worse if the opportunity for fraud falls only to those restrained by neither law nor shame. Therefore, since the emperor's own position has been restricted, let the remedy of law address private cupidity. Old decrees have long gone cold among the criminal class -- their force died with the legislators who issued them. Just as much severity must now be added to the laws as offenses have grown. Otherwise, if the correction of the greater part of society is abandoned, the emperor has bound himself with harsh rules to no purpose -- he who was always good and upright in character. Farewell."""),

(5062, """From: Quintus Aurelius Symmachus, Roman Senator
To: A friend (name lost)
Date: ~372 AD
Context: A witty exchange about the obligations of correspondence, aging, and literary rivalry between friends.

You ask me to reply -- your letters are practically a challenge to a duel. But where would I, advancing in years as I am, find that elderly, theatrical spark with which you rival the ancients? Still, do not let my despair at my own style discourage your enthusiasm. Where is the shame in being beaten after confessing one's limitations? There was another thing that compelled me to write back: I was afraid that by my silence I would be giving you a formula for staying quiet yourself, and I realized there would be more harm to me if your indignation imitated my silence than if my boldness tried to surpass you. You will judge for yourself how much my love for you made me do this against my own modesty.

Meanwhile, I am glad you are well, though you added that caution is needed lest the sudden turn of your years overtake our reunion. I will not have you counting your years on your fingers -- confidence in health lies in one's strength. Since the discipline of your character spares you from squandering that strength, trust that the gods will bring it about that you remain sound in body to the limits that ancient tradition has set for a human life. Farewell."""),

(5127, """From: Quintus Aurelius Symmachus, Roman Senator
To: Minervius (multiple short letters)
Date: ~372-399 AD
Context: Several brief recommendation letters to Minervius, including endorsements of friends and a note about his son Flavianus.

My friend Gaudentius has taken refuge in your protection -- a man who deserves to be loved in every respect. He is of senatorial family, and his character and modesty are nobler than his distinguished birth. If you do not think my testimony is tainted by mere flattery, take him under your wing. A long inspection of his loyal service will make you conclude that I have actually understated his qualities.

---

To Minervius (~398 AD): Love my lord and son Flavianus [Virius Nicomachus Flavianus the Younger, a prominent Roman senator] as much as you can guess I want you to, and if possible, enter into a contest with me over which of us loves him more. I will be glad if you win. But I will only believe it when he himself begins to honor you beyond the measure of my own devotion. For if friendship rests on mutual services, it will be easy to gauge your heart by his.

---

To Minervius (~398-399 AD): If you consider how rare innocent men are, you will love my son Desiderius, who deserves to be counted among that select few. You will conclude that my judgment of him is not mistaken once he comes before your scrutiny. In the meantime, I ask that through me the inner sanctuary of your friendship be opened to him, and that you lend a sympathetic ear when he presents the just merits of his case. If you do well by him, my own word will be redeemed -- for I have taken upon myself the promise of your generosity toward him.

---

To Minervius: In settling the matter of our friend Rusticus, I presented the request to you, but my son Caecilianus did the actual work. It would not be right for me to claim credit for someone else's labor. Let us both give thanks to the man himself: your authority ordered the action, but my health could not carry it out."""),

]

if __name__ == '__main__':
    n = write_translations_batch(translations)
    print(f"Wrote {n} Symmachus translations (batch 02)")

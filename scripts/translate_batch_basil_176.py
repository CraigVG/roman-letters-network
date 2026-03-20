#!/usr/bin/env python3
"""Batch translate Basil letters 156-161 (IDs 968, 969, 971, 972, 973)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(968, """From: Basil, Bishop of Caesarea
To: Evagrius, Presbyter
Date: ~366 AD
Context: Basil responds to Evagrius's proposals for church reconciliation, welcoming the idea but warning that deep-rooted pride requires more than good intentions.

Brother Evagrius,

Far from finding your letter too long, I actually wished it were longer -- it gave me that much pleasure. After all, what could be more welcome than the prospect of peace? What better suits our calling, or pleases the Lord more, than working to bring it about? May you receive the peacemaker's reward, since that blessed work is clearly what you've set your heart on.

Believe me, my revered friend, no one wants more than I do to see the day when all who share the same faith gather in the same assembly. It would be monstrous to take any pleasure in the divisions tearing apart Christ's churches, rather than recognizing that the greatest good lies in knitting the members of his body back together.

But here is the difficulty: my desire is real, and so is my inability. You know better than anyone that ailments which have matured over time can only be healed by time. What's more, a strong and thorough treatment is needed to get at the root of the problem. You'll understand what I'm hinting at, though there's really no reason I shouldn't speak plainly.

When self-importance has taken root in someone's mind through long habit, it cannot be uprooted by one person, one letter, or a short span of time. Unless there is some arbiter whom all sides trust, the suspicions and clashes will never fully cease. If divine grace were poured out on me -- if I were given the power in word, deed, and spiritual gifts to prevail with these rival factions -- then perhaps you could demand such a bold attempt from me. Even then, I doubt you'd advise me to try adjusting things on my own, without the bishop on whom the care of the church principally falls. But he cannot come here, and I cannot easily undertake a long journey in winter -- or really at any time, given the state of my health.

So while I embrace the goal you've set before me, I ask you to understand the practical obstacles. The will is there; what's lacking is the means."""),

(969, """From: Basil, Bishop of Caesarea
To: Antiochus
Date: ~366 AD
Context: A short, affectionate complaint to a friend who has been neglecting to write or visit.

You can imagine how disappointed I was not to see you this past summer. Not that our meetings in previous years ever quite satisfied me -- but even seeing the people we love in a dream brings some comfort to those who miss them.

Yet you don't even write. You really are that sluggish. I can only conclude that you're simply too lazy to make a journey for friendship's sake. But I'll say no more on that point.

Pray for me. Ask the Lord not to abandon me, but just as he has brought me through past trials, to deliver me from whatever lies ahead -- for the glory of the name in which I place my trust."""),

(971, """From: Basil, Bishop of Caesarea
To: Eupaterius and his daughter
Date: ~366 AD
Context: Basil responds to theological questions from a father and daughter, affirming the Nicene Creed and defending the divinity of the Holy Spirit.

My dear Eupaterius and daughter,

You can well imagine the pleasure your letter gave me, if only from its contents alone. What could bring greater satisfaction to someone who prays constantly to be in contact with those who fear the Lord than a letter asking questions about the knowledge of God? For if, as the Apostle says, "to live is Christ" [Philippians 1:21], then truly my words ought to be about Christ, my every thought and action ought to flow from his commandments, and my soul ought to be shaped in his image. So I rejoice at being asked about these things, and I congratulate you for asking.

To put it briefly: I hold in honor above all later formulations the faith of the Fathers assembled at Nicaea [the Council of Nicaea, 325 AD, which established the foundational creed of Christian orthodoxy]. In that creed the Son is confessed to be of the same substance as the Father, sharing by nature the very being of the One who begot him -- for he was declared to be Light of Light, God of God, Good of Good, and so on. What those holy men proclaimed is what I proclaim now, praying that I may walk in their footsteps.

But since a question has been raised in our time -- one that the Fathers passed over in silence simply because no one disputed it -- namely the question of the Holy Spirit, I will add a brief statement in keeping with Scripture. As we were baptized, so we profess our belief. As we profess our belief, so we offer praise. Since baptism was given to us by the Savior in the name of the Father, the Son, and the Holy Spirit, our confession of faith accords with our baptism, and our worship accords with our confession. We glorify the Holy Spirit together with the Father and the Son, convinced that the Spirit is not separated from the divine nature -- for what is foreign by nature does not share in the same honors.

This much I offer you. Hold fast to the faith you have received, and let no one shake you from it."""),

(972, """From: Basil, Bishop of Caesarea
To: Diodorus, Presbyter of Antioch
Date: ~366 AD
Context: Basil refutes a forged letter circulating under Diodorus's name that claimed marriage to a deceased wife's sister was permissible -- a practice Basil considers both illegal and repugnant to Christian custom.

My dear Diodorus,

I have received a letter circulating under your name, but its contents are creditable to anyone rather than to you. Some clever person appears to have borrowed your name to lend authority to his own views. It seems he was asked by someone whether it was lawful to marry one's deceased wife's sister, and instead of recoiling from the question, he heard it calmly and proceeded to defend the unseemly desire with considerable boldness.

If I still had his letter, I would send it to you so you could defend both yourself and the truth. But the person who showed it to me took it back and has been carrying it around like a trophy -- waving it at me, who had forbidden such marriages from the start, and declaring that he now had written permission.

So I write to you now in order to attack that forged document with double force, and strip it of any power to mislead.

First, let me appeal to what matters most in such cases: our own established custom, which carries the force of law because it was handed down to us by holy men. The rule is this: if anyone, overcome by impurity, falls into unlawful relations with two sisters, this is not to be regarded as a marriage. Such persons are not to be admitted to the Church until they have separated. That custom alone should be sufficient to settle the matter.

But since the author of this letter has tried to smuggle his mischief into our practice through false reasoning, I am obliged to engage his argument as well -- even though in matters this obvious, a person's instinctive moral sense is stronger than any syllogism.

His argument runs like this: Leviticus says, "You shall not take a wife to her sister, to vex her, to uncover her nakedness, beside the other in her lifetime" [Leviticus 18:18]. Therefore, he concludes, after one sister's death, the prohibition lapses. But this reading is absurd. The entire passage in Leviticus is a catalog of forbidden unions -- mother, sister, daughter, and so on. No one would argue that these other prohibitions expire at death. The phrase "in her lifetime" specifies the particular cruelty of taking a second wife who is the first wife's own sister while the first still lives. It does not open the door after death.

Moreover, the whole spirit of Christian marriage points the other way. A man's wife's sister is his own sister. He owes her a brother's care and protection, not a husband's claim. To treat her otherwise is to corrupt the very relationship that marriage created.

I urge you, brother, to make this known wherever that forged letter has spread, so that the truth may overtake the lie."""),

(973, """From: Basil, Bishop of Caesarea
To: Amphilochius, newly consecrated Bishop of Iconium
Date: ~366 AD
Context: Basil congratulates Amphilochius on his consecration as bishop, sees God's hand in it, and urges him to stand firm against heresy despite illness making a personal visit uncertain.

Blessed be God, who from age to age chooses those who please him, sets apart his chosen vessels, and puts them to work in the service of his saints. You tried to flee -- you admit it yourself -- not from me, but from the calling you expected to come through me. Yet God has caught you in the sure net of his grace and brought you into the heart of Pisidia [a region in southern Asia Minor] to catch people for the Lord and drag the devil's prey from the deep into the light.

You too may say with the blessed David: "Where shall I go from your Spirit? Where shall I flee from your presence?" [Psalm 139:7]. Such is the wonderful work of our loving Master. Donkeys are lost so that there may be a king of Israel [a reference to 1 Samuel 9-10, where Saul goes looking for lost donkeys and is anointed king]. David, however, was an Israelite granted to Israel. But the land that raised you and brought you to such heights of virtue no longer possesses you -- she watches her neighbor adorned with her own jewel. Yet all believers in Christ are one people, and all Christ's people, though hailed from many regions, are one Church. So our country rejoices at the Lord's arrangement: rather than thinking she is one man poorer, she considers that through one man she has gained whole churches.

Only let the Lord grant me this: to see you in person, and as long as we are apart, to hear of your progress in the gospel and the good order of your churches.

So be strong. Play the man. Stand before the people the Most High has entrusted to your care. Like a skilled pilot, rise in mind above every wave raised by heretical blasts. Keep the ship from being swamped by the salt, bitter waters of false doctrine. Wait for the calm the Lord will bring, once a voice is found worthy to rouse him to rebuke the winds and the sea [cf. Mark 4:39].

If you wish to visit me -- now hurried by long illness toward the inevitable end -- do not wait for a formal occasion or an official summons. Come as a friend visiting a friend. Come quickly, before it is too late."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Basil translations (IDs: 968, 969, 971, 972, 973)")

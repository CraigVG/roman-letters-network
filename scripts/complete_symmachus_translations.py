#!/usr/bin/env python3
"""
Complete truncated Symmachus modern_english translations.

Two categories:
1. 33 letters where Latin is complete but modern translation ends with "..."
   → Complete the translation with the missing ending
2. 34 letters where Latin itself is truncated/garbled
   → Add "[Text breaks off in source.]" after the existing "..."
"""

import sqlite3

DB_PATH = "data/roman_letters.db"

# ─── Category 1: Complete the translation ────────────────────────────────────
# Strip trailing "..." from modern_english and append the proper ending.
# Latin read directly; completions translate the remaining content.

COMPLETIONS = {
    # Book 1.53 — Symmachus to a friend on holiday at Baiae
    # Latin ends: "senties ius sacerdotis, nisi impleveris ius amici. vale."
    4897: (
        "Our reasons for not writing are different, but the result is the same. "
        "I'm held up by the duties of the pontificate; you, by the pleasant negligence "
        "of your holiday at Baiae. Relaxation makes a man just as lazy as overwork. "
        "And no wonder that coast claims you entirely — we know for certain that Hannibal "
        "himself, undefeated in war, surrendered to Campania. Not even the legendary lotus "
        "tree that held travelers captive, or Circe's seductive cup, or the songs of the "
        "half-bird Sirens could equal the allure of that sky and soil.\n\n"
        "Not that I'm accusing you of fattening yourself on idle holidays, or suggesting "
        "your virtue has been softened by luxury. But while you read for yourself, write "
        "for yourself, and rest your mind from urban affairs in solitude — enormous as your "
        "spirit is — you're neglecting the duties of friendship entirely.\n\n"
        "So pick up your pen and show my affection the courtesy it deserves — unless you'd "
        "prefer to test the authority of a pontiff. We priests have much to deliberate in "
        "our college. Who gave you leave from your public duties? You'll feel the rights of "
        "a priest if you fail to fulfil the rights of a friend. Farewell."
    ),

    # Book 1.59 — Symmachus chides a friend who claims to be a simple hunter
    # Latin ends: "Rustica sint et inculta, quae loqueris, ut venator esse credaris. vale."
    4903: (
        "So you boast of your leisure and your hunting. It's a pleasant claim, but you "
        "make it more in jest than in earnest. I know you spend your free time happily "
        "chewing over the works of the ancients. You can fool other people — those who've "
        "only just met you. I can judge both your daily business, which occupies you night "
        "and day, and the daily nourishment of your mind from the flavor of the letters "
        "you send me.\n\n"
        "Unless perhaps you've confined Apollo to the forests, like that shepherd Hesiod, "
        "whom the Muses crowned with poetic laurel [referring to Hesiod's account of the "
        "Muses appearing to him while he tended sheep on Mount Helicon].\n\n"
        "For where does this freshness of thought and this old-fashioned richness of "
        "language in your letters come from, if you've truly abandoned everything for "
        "knotted nets, feathered scarecrows, keen-nosed dogs, and the whole business "
        "of the hunt?\n\n"
        "So when you write, remember to keep your eloquence within bounds. Let your letters "
        "be rustic and rough — so you'll actually be believed to be the hunter you claim. "
        "Farewell."
    ),

    # Book 1.64 — Symmachus encourages a friend called back to public service
    # Latin ends: "esto, ut es, curarum omnium tolerans, et debitam operam solve
    #              principibus, qui rationem magis meriti tui quam voluntatis habuerunt."
    4908: (
        "Take heart — be patient with the duty that's been imposed on you. It often "
        "happens that proven merit is called back for a second round of service.\n\n"
        "Consider: do you think Atilius [a Roman exemplar of civic duty, who left his "
        "plow for public office] was happy to trade his fasces for the plow and halt "
        "his panting oxen in the middle of sowing, a rustic magistrate? Any man of solid "
        "worth gets claimed for the public good.\n\n"
        "Set aside for now those pleasant daydreams of your happy retirement — the estate "
        "rich with autumn's bounty, sunny in winter, first to coax roses from the earth "
        "in spring, cool with shade and stream in summer heat. But why do I stray from "
        "the point? In treating your complaints I've only stirred up fresh longing. Be "
        "who you are — patient in every burden — and discharge the service owed to the "
        "emperors, who have weighed your merit more than your wishes."
    ),

    # Book 1.67 — Symmachus to a public official who pleads overwork as excuse for silence
    # Latin ends: "numquam enim securus est amor patriae, et quamvis magna remedia
    #              conquirat, semper illud putat imminere, quod timuit. vale."
    4911: (
        "You say you're hampered by endless obligations and can't manage to write to your "
        "dearest friends as diligently as you'd like. No need to keep defending what we "
        "already know. Even from a distance, we're well aware of your cares and sleepless "
        "nights.\n\n"
        "You've changed your role, not abandoned your duty — rightly, the welfare of "
        "citizens came before correspondence. Now we both long for and press for your "
        "letters, gathered like provisions against the coming winter. Though I know you "
        "don't yet consider that ground entirely safe. Love of country is never at ease; "
        "however great the remedies it finds, it always dreads the return of what it feared. "
        "Farewell."
    ),

    # Book 1.82 — Symmachus asks for a philosopher's salary to be confirmed
    # Latin ends: "interest famae et gloriae tuae, ut confirmandi magis quam negandi
    #              commodi causa de philosophi salario dubitasse videaris."
    4926: (
        "You know — whether by reputation or firsthand — how long I've championed your "
        "achievements. So I won't stand by while anything threatens the goodwill you've "
        "earned.\n\n"
        "My friend Priscianus, who ranks among the foremost philosophers for both learning "
        "and character, receives a salary by authority of the Senate. I'm told a dispute "
        "has arisen over his stipend. Even if the Senate had never granted him such an "
        "allowance before, your own commitment to learning ought to ensure he receives it.\n\n"
        "You know the old principle: the liberal arts are nourished by honor, and it's the "
        "mark of a flourishing republic that generous rewards are paid to teachers and "
        "scholars. I ask you, therefore, not to let this uncertainty diminish his benefit "
        "or undercut the august body's authority to confirm it. Your own reputation and "
        "glory are at stake: let it appear that you questioned the philosopher's salary in "
        "order to confirm it — not to deny it."
    ),

    # Book 1.94 — Symmachus congratulates on a colleague's departure with a eulogy
    # Latin ends: "tu conice plura de paucis, quae nunc insinuare non decuit,
    #              sed per alium scribere non pigebit."
    4938: (
        "Although my affection for you always keeps me from being stingy with letters, "
        "right now I'm writing more eagerly than usual, for several reasons. First, our "
        "friend Marius's departure shouldn't go without a kind of travel offering. Second, "
        "I thought my letter would carry a bit more weight if it reached you through "
        "someone you deeply respect.\n\n"
        "It often happens that a charming messenger enhances even a modest gift. But "
        "there's another reason my enthusiasm has kindled: I thought I should congratulate "
        "you on the achievements of such a man, who returns from his suburban province "
        "carrying as much public affection as he left behind in the way of example.\n\n"
        "I won't flatter dishonestly — I don't know the art of ingratiating myself. In "
        "him runs a brotherly strain, and this is precisely why his departure is so hard "
        "to bear: in him, it seemed, we enjoyed two friends at once. I hesitate to "
        "extend my testimonial further, lest I seem to have served his glory more than "
        "his modesty — for an honest soul has an unguarded face. Read the rest from "
        "the little I've ventured to say; it was not right to put everything in writing "
        "here, but writing it through another will not trouble me."
    ),

    # Book 1.100 — Symmachus on the honor of reading the emperor's speech before the Senate
    # Latin ends with the Castor/Pollux comparison then:
    # "habes summam voluntatis meae; cui si quid commendationis inspiraveris,
    #  ceteris ornamentis animi tui adicietur decus praesentis officii."
    4944: (
        "The fact that I received no letter from you when the emperor entrusted me with "
        "reading his speech before the assembled Senate — I know that wasn't a slight on "
        "your part. A friendship that's good and well-tested can survive a lapse in "
        "correspondence without its foundations being shaken.\n\n"
        "That's why I've avoided retaliating in kind. I was afraid that what you'd done "
        "involuntarily, I'd appear to have done out of offense. The situations are entirely "
        "different: an accidental silence and a deliberate one. The same duty goes "
        "unfulfilled in both cases, yet it matters enormously whether a man skips it "
        "because he's overwhelmed with work or because he's angry.\n\n"
        "But I've said enough about that. Now, if you love me — or rather, because you "
        "love me — I trust the feeling is returned: go and convey my joy to the invincible "
        "emperors, who trusted their divine words to a human voice and whose victories the "
        "Senate heard proclaimed from my lips. Call to mind what it was for me on that day "
        "when I stepped, as if from the heart of a battle, and was the first to pour "
        "welcome tidings into all ears and hearts. Long ago, when Rome won military glory, "
        "the twin Pollux announced the victory at the pool of Juturna [the goddess of "
        "springs near the Forum, where the Dioscuri were said to have appeared after the "
        "battle of Lake Regillus], riding back foam-flecked with the battle left behind. "
        "That same honor has now been conferred on me by sacred imperial command. What "
        "the Castors gained by that, the emperors have now granted me. Speak of this on "
        "my behalf — more fully and more elegantly than I can, for your tongue is better "
        "than mine. You have the sum of my wishes; if you add any word of recommendation, "
        "the honor of your present office will join the other ornaments of your spirit."
    ),

    # Book 1.105 — Symmachus sends medicines to a sick friend
    # Latin ends: "si eam sollicitudinem, quae mihi ex aegritudine tua oborta est,
    #              prosperiorenuntio nihil moratus exemeris."
    4949: (
        "Late consolation only reopens wounds. We owe each other mutual silence about "
        "our misfortunes, lest the injuries dealt by fortune — which are slowly forming "
        "scar tissue with the passage of time — break open again from being touched too "
        "soon.\n\n"
        "Let me turn our conversation instead toward something that might encourage you "
        "to look after your health. Every internal ailment worsens in winter's harsh "
        "conditions, and if you don't travel on sunny days and in healthy air, I'm "
        "seriously worried that neglect will make things worse.\n\n"
        "I've sent you the remedies you said you found helpful, along with others that "
        "my own experience has shown to be effective. My highest hope is that these "
        "treatments forestall the need — that your own health returns of itself — or, "
        "if any trace of illness lingers, that these cures may clear it away. The "
        "greatest gift you can give our friendship is this: relieve without delay the "
        "worry your illness has stirred in me by sending better news."
    ),

    # Book 1.108 — Symmachus to a friend at Milan, too close not to visit
    # Latin ends: "quarum me in maximo fenore perceptio iuvat. solutio defetigat. vale."
    4952: (
        "The news that you're at Milan reached me by rumor before your letter arrived — "
        "fame lets nothing about prominent men go unnoticed. But what good does it do "
        "those of us who miss you that you've traveled to a place so near and yet still "
        "deny us your presence?\n\n"
        "I bore your distant separation more easily; when hope of seeing you is blocked "
        "by a vast distance, it simply goes quiet. But now you tease my expectations with "
        "the ease of proximity — and you can't even use the Alps as your excuse, since "
        "the road that makes your case for pardon weaker makes my case for complaint "
        "stronger.\n\n"
        "But I should put a limit on my grievance. At least let your letters visit Rome "
        "more often from now on — letters sweet as the honey of Hybla or Mount Hymettus "
        "[both proverbially celebrated for their fine honey]: receiving them is a pleasure "
        "beyond measure; repaying the debt is exhausting. Farewell."
    ),

    # Book 2.4 — Symmachus reports the African delegation has stalled; describes voyage
    # Latin ends: "curabo, ut frequentibus litteris merear de te similis officii diligentiam."
    4961: (
        "Relax — take a break and enjoy your leisure. The honorable Antonius has informed "
        "me that the plan for the African delegation has stalled. This is confirmed by the "
        "fact that no recent letters from my friends have mentioned the matter.\n\n"
        "Is there anything else you need to know? In fact, I think this should have been "
        "the first thing I told you. When we set sail from the Cumanum estate at barely "
        "first light, we reached the shore at Formiae with more help from the rowers than "
        "from the wind — the sun had already passed its peak. The friends who came in a "
        "smaller boat arrived later: delayed, it was unclear, whether by headwinds or by "
        "the carelessness of the crew. That is everything I had to report for now. I'll "
        "see to it that by writing frequently I earn the same diligence from you."
    ),

    # Book 2.6 — Symmachus on grain shortages and potential unrest in Rome
    # Latin ends: "vos valete et litteras sperate meliores, si fortuna urbis nostrae
    #              secundis amara mutaverit. vale."
    4963: (
        "Having covered the coast beyond Formiae that stretches toward Axyr, we won't "
        "delay the ship and its rowers. But we need the gods' help — I hope our return "
        "finds nothing to regret. There's constant talk that the people are on the verge "
        "of rioting over the meager food supply, and there's no prospect of abundance "
        "replacing the current shortages.\n\n"
        "The harvest is near-famine everywhere. The grain fleet has been diverted to "
        "other routes. Summer is already giving way to autumn. By Hercules, as I said, "
        "we need to leave the management of this crisis to the gods. As for what human "
        "effort can do — the remedies are long overdue and too late now. Stay well — "
        "and hope for better letters, if fortune turns this bitter time for our city to "
        "something brighter. Farewell."
    ),

    # Book 2.10 — Letter of recommendation for Carissimus
    # Latin ends: "quae ideo commendanda suscepi, quia mores petentis expendens
    #              aequa esse praesumpsi."
    4967: (
        "Justice, admittedly, doesn't need an advocate. But friendship can often speed "
        "a case along. Where am I going with this, you ask? I want Your Excellency to "
        "know that the praiseworthy Carissimus, a former count, places his hope in the "
        "quality of his case — but recognizes that having my letter to support him won't "
        "hurt when it comes to winning the judge's favorable attention.\n\n"
        "I ask, therefore, that you advance the petition of a man I embrace with a "
        "brother's affection. I've taken up his cause because I've weighed the character "
        "of the petitioner and found his claim to be just."
    ),

    # Book 2.17 — Recommendation of Symmachus's son Nicasius via his friend Promotus
    # Latin ends: "cuius honori tribuendum est, ut a te non ut novus subdendus examini
    #              sed ut iam probatus habeatur."
    4974: (
        "If you haven't yet learned about my son Nicasius's praiseworthy character and "
        "honorable way of life, then accept as his richest guarantor my friend Promotus "
        "— a man distinguished for both virtue and humanity — with whom Nicasius has "
        "been closely associated for some time. Judge the young man's qualities by his "
        "choice of companion.\n\n"
        "That's a fair inference, after all: a man's worth can be measured by the weight "
        "and esteem of his friends. My own endorsement carries less force when the "
        "testimony of a more prominent person tips the scale. It is to his honor that he "
        "should come before you not as a newcomer to be tested, but as a man already proven."
    ),

    # Book 2.25 — Symmachus offers advice on private affairs, attaches key points as summary
    # Latin ends: "ita enim meo officio functus sum, ut tibi iudicium reservarem. vale."
    4982: (
        "You're certainly well-supplied with counsel and prepared for every situation "
        "— a man of your wisdom and cultivation needs no advisor. But I hope you'll allow "
        "my own vigilance to contribute something to your private affairs.\n\n"
        "So if our friend's letter brings you anything I've been thinking about as well, "
        "pursue it confidently as something approved by two minds. And if you find "
        "anything new in it, consider it your own discovery, merely prompted by someone "
        "who cares for you. I've attached the main points in summary — I didn't want to "
        "spell everything out in a letter, to avoid being tedious. It's up to you to "
        "weigh what I've outlined. That is how I've discharged my duty — by leaving the "
        "judgment to you. Farewell."
    ),

    # Book 2.28 — Symmachus accepts blame for a prefecture matter; thanks for advice to stay quiet
    # Latin ends: "ego vero solitae verecundiae ignavum quoque iungam timorem et litteris
    #              tuis agam gratias, quae me... ad omnium iniuriarum silentium cohortantur."
    4985: (
        "Go ahead — judge my decisions in hindsight, as you like, and blame me for the "
        "prefecture's complaint that it was disrespected. It's easy to accuse a man who's "
        "been left without support. And so I'd rather accept the confession of error "
        "myself than charge my friends with negligence or my opponents with hostility.\n\n"
        "If I appeared defeated before I'd even begun to fight, that was Fortune's doing, "
        "not my conscience. And yet you write that I should stay away from cases like this "
        "in the future! You see how much the outcome is allowed to determine everything. "
        "You've forgotten my character. I, for one, will add timid cowardice to my "
        "habitual restraint — and I thank your letter for urging me, stripped now of all "
        "confidence in law and friends alike, to meet every injustice with silence."
    ),

    # Book 2.29 — Recommendation for the philosopher Maximus
    # Latin ends: "cuius tibi negotia cum in rem missus absolverit, quaeso, ut humanitate,
    #              qua clarus es, iustas petitiones ingravato auxilio prosequaris."
    4986: (
        "When you vouch for a good man, you recommend your own judgment as much as you "
        "help his cause. So in writing on behalf of my friend Maximus, I serve my own "
        "reputation no less than his interests.\n\n"
        "He's a man of outstanding character and learning in the liberal arts, second to "
        "none among the distinguished philosophers, and therefore perfectly worthy of your "
        "friendship. When he has completed the business for which he was sent your way, "
        "I ask that you receive his just petitions and support them with the full weight "
        "of your well-known humanity."
    ),

    # Book 2.31 — Symmachus warns a friend not to take up his defense publicly
    # Latin ends: "quod in panegyrici defensione non tacui."
    4988: (
        "...and you care for me, but I worry that you might take up some fight on my behalf "
        "while I'm away and draw hostility onto yourself. Please, I ask you, stand down. "
        "Perhaps one day I'll have the chance to make my case before the eternal emperor, "
        "our lord Theodosius [Emperor Theodosius I, r. 379–395], whose favor toward me is "
        "exactly what provoked certain people's jealousy in the first place.\n\n"
        "I don't think my situation under a legitimate ruler will be the same as it was "
        "under the usurper [Magnus Maximus, who held power 383–388], on whose written "
        "orders — issued at Marcellinus's instigation — my household staff were punished, "
        "as you know. And this I did not pass over in silence when defending the panegyric."
    ),

    # Book 2.35 — Symmachus teases a friend for leaving Rome before the festival of Cybele
    # Latin ends: "mihi uno genere satisfacies, si remotis epistularum defensionibus
    #              ipse remeaveris."
    4992: (
        "From: Quintus Aurelius Symmachus, Roman Senator\n"
        "To: A friend (name lost)\n"
        "Date: ~383 AD\n"
        "Context: Symmachus teases a friend who left Rome instead of staying for the "
        "festival of the Great Mother, and recalls a recent conversation about the "
        "priority of private business over public life.\n\n"
        "I assumed your return was approaching, since the sacred rites of the Mother of "
        "the Gods [the festival of Cybele, the Magna Mater, celebrated with elaborate "
        "processions in March–April] were near. Instead, you are headed for Daunia [the "
        "region around modern Foggia in Apulia, southeastern Italy] and leave both me and "
        "the capital behind. Go ahead and mock the easy-going nature of your friends — "
        "who, if this insult stung them, would at least withhold their letters in "
        "retaliation. Instead, we soothe you with courtesies as you depart and suggest "
        "pleasant things to your mind, while you put the management of your estate ahead "
        "of everything.\n\n"
        "You will recall that this was the very premise of your letter: that at this stage "
        "of life nothing should be tended more carefully than domestic affairs. But I, "
        "knowing the vein of your character, know this was said in jest. When would a mind "
        "as distinguished as yours stoop to common worries? My judgment, then, is that you "
        "should save such pretenses for people who do not know the true depths of your "
        "soul. You will satisfy me in one way only: set aside your epistolary excuses and "
        "come back in person."
    ),

    # Book 2.37 — The Praetextatus statue controversy among the pontifical college
    # Latin ends: "redde te mihi, ut nobis aequiorem vitae cursum faciant participata solacia."
    4994: (
        "From: Quintus Aurelius Symmachus, Roman Senator\n"
        "To: A friend (name lost)\n"
        "Date: ~383 AD\n"
        "Context: A politically sensitive letter about the defeat of a proposal to erect "
        "a statue of Praetextatus — Symmachus's close friend and a leading pagan aristocrat "
        "— by the Vestal Virgins, which the pontifical college rejected.\n\n"
        "Has it really pleased our common father [the emperor] to keep you detained longer "
        "than I would wish? Or do you so detest city life that you frustrate my expectations "
        "with a pious excuse? Truly, nothing is done or said here that a good heart and a "
        "pure nature could embrace. But however things stand, if you were in Rome, the "
        "bitterness might be softened by our mutual support. As it is, I experience the "
        "offense of events all the more keenly because I bear them alone.\n\n"
        "Here is one example, from which you may infer the rest: they have decided to "
        "dedicate a statue of our Praetextatus [Vettius Agorius Praetextatus, d. 384 — "
        "one of the last great pagan aristocrats of Rome], proposed by the Vestal Virgins. "
        "The pontifices [the priestly college] were consulted, but before they even weighed "
        "the reverence owed to that sublime priesthood, or the custom of long tradition, or "
        "the circumstances of the present time, they voted — all but a few who followed me "
        "— to erect his likeness.\n\n"
        "I kept silent about this: I saw that such homage from the Vestals toward a man "
        "was unsuitable to their dignity, and that what was being proposed had never been "
        "done before — not by Numa who founded the priesthoods, not by Metellus who saved "
        "the rites, not by any chief pontiff before. I stayed quiet rather than announce "
        "it to those who resent the sacred rites and would use it to harm the supporters "
        "of something unprecedented. I simply replied that the precedent must be avoided, "
        "lest what begins from a worthy principle quickly spread by canvassing to the "
        "unworthy. In short, I've sent you the very words — approved by good men but "
        "perhaps outvoted — though the form of pontifical decrees differs from that of "
        "the Senate. That too will be dismissed as ignorance. If you were here, the "
        "soundness of two minds would carry great weight. So the moment our common father "
        "has emerged from his uncertain illness, come back to me — so that shared "
        "consolation may make life's course a little easier for us both."
    ),

    # Book 2.39 — Symmachus sends his son Parthenius; reports calm after riots
    # Latin ends: "neque enim quicquam narrandis debeo derogare, qui rerum plenitudinem
    #              venturo ad vos indici reservavi. vale."
    4996: (
        "My son Parthenius's arrival needs no embellishment of recommendation. But I "
        "expect his standing will only rise when my own words accompany his presence. "
        "From him you'll learn what's been happening in Rome — though rumor has probably "
        "outrun the written account. Great and unexpected events don't stay secret for "
        "long.\n\n"
        "The people of Rome have turned a corner. The punishment of the rioters is now "
        "being demanded by the very crowds that used to follow them, and the troublemakers "
        "have finally backed down. I won't say more — it would be wrong to steal anything "
        "from his account. I've left the full picture for the one coming to deliver it "
        "in person. Farewell."
    ),

    # Book 2.48 — Symmachus reports safe arrival after a voyage; thanks friend for seafood
    # Latin ends: "cura, ut valeas et patriam tui amantem quam primum revisas bona parentis,
    #              ut spero, venia, cui mox peracta lustrali sollemnitate redderis."
    5005: (
        "With the gods' help, we arrived at our destination after a smooth voyage and "
        "an easy journey. We reached port just in time for dinner. As we sat down to eat, "
        "a messenger came running up with your kind letter and — along with it — a haul "
        "of seafood you'd caught. We ate it straightaway. It seemed right to indulge "
        "ourselves, now that our little one had been pulled safely through the danger "
        "we'd feared.\n\n"
        "There you have the whole story. Take care of yourself and come back soon to the "
        "city that loves you — with your father's blessing, I hope, to whom you will soon "
        "be restored once the purification ceremony is complete."
    ),

    # Book 3.34 — Two letters: recommendation for Dorotheus, then appeal to Ambrose for Marcianus
    # Second letter ends: "erit igitur tibi facilior ad impetrandum via, cum meritorum
    #                      tuorum opitulatio aliorum iuvetur exemplis. vale."
    5082: (
        "From: Quintus Aurelius Symmachus, Roman Senator\n"
        "To: Ambrose and others (multiple short letters)\n"
        "Date: ~382 AD\n"
        "Context: Short letters of recommendation and a note to Ambrose, Bishop of Milan.\n\n"
        "My brothers Dorotheus and Septimius, praiseworthy men, carried a single letter "
        "from you. But my sense of duty would not allow me to take the shortcut of a "
        "single reply: I wanted both to return you double the courtesy of your service, "
        "and to give each man individually the honor of a deserved testimonial. Even "
        "though our brother Dorotheus has already proven himself to you, I still wish my "
        "recommendation to commend him to you even more. I have no doubt this will happen, "
        "since an affection rooted in a good heart is capable of growing whenever it is "
        "prompted by merit.\n\n"
        "---\n\n"
        "To Ambrose (~395 AD): Although I believe my earlier letter — in which I asked you "
        "to defend my friend Marcianus from injustice — has reached your hands, I could "
        "not hold back from a second appeal, so that a repeated plea might attest to the "
        "real need of an excellent man caught up in the jealousies of a tyrannical era. "
        "So I urge you again to take up his defense. His poverty, born of his integrity, "
        "prevents him from paying grain prices that imperial clemency has already remitted "
        "for many others from that same period. Your path to securing this will be all the "
        "easier because your own well-earned intercession is backed by the precedent others "
        "have set. Farewell."
    ),

    # Book 3.41 — Symmachus recovering from illness; recommends Repentinus
    # Latin ends: "erit tamen copia melior, qua intellegat, non se debuisse deserere,
    #              quem frequenti testimonio tuo de se noverat credidisse."
    5089: (
        "From: Quintus Aurelius Symmachus, Roman Senator\n"
        "To: A friend (name lost)\n"
        "Date: ~385 AD\n"
        "Context: Symmachus reports his recovery from illness and recommends the young "
        "man Repentinus.\n\n"
        "The strength of my health is beginning to rally — it is only fair that a steady "
        "stream of letters should now be expected from me. Let this recovery hold, though "
        "winter's harshness often threatens it. The process of convalescence is extremely "
        "delicate and fragile, and health looks for the aid of milder skies before the "
        "doctors' hands can do their work. You must think I have made the art of healing "
        "responsible for the length of my illness! I want us to break the memory of bad "
        "times with the charm of a joke.\n\n"
        "But I must also say something about Repentinus, an excellent young man, whose "
        "constant attendance I missed. His modesty, I believe, kept him away, when "
        "confidence drawn from your introduction should have brought him forward. Yet "
        "there will be a better occasion when he will understand that he should not have "
        "held back from a man whom your repeated testimonials had taught him to trust."
    ),

    # Book 3.46 — Two letters: congratulations on appointment; defense of epistolary convention
    # First ends: "memento salute referenda et tuum munus exequi et mei officii
    #              diligentiam provocare."
    # Second (to Siburius) ends: "efficiet adsiduitas litterarum mearum, ut mutui
    #                              admonearis officii."
    5094: (
        "From: Quintus Aurelius Symmachus, Roman Senator\n"
        "To: A friend (name lost)\n"
        "Date: ~387 AD\n"
        "Context: Symmachus congratulates a friend on a public appointment, urging him "
        "to live up to the high expectations that surround him.\n\n"
        "I count the joys of your fortune among my own debts, and I take you as my "
        "judge of this sentiment — you who have seen my heart tested whenever you consult "
        "your own. It was fitting in these tender days of good times that a man praised "
        "by public counsel should be admitted to office. Since events have unfolded as "
        "everyone hoped, carry out your work in a manner worthy of so great a prince's "
        "judgment. The weight of expectation — always burdensome to good men — presses "
        "upon you. For even though it looks to the worthy, it is nevertheless close to "
        "danger, since it always promises itself more.\n\n"
        "You have an age friendly to virtue — one in which any failure to win glory is a "
        "man's fault, not the times'. You see it clearly: just as the man who stands at "
        "the head of Roman affairs was born for the public good, so the tide is with you "
        "now, not against you. Good character and virtue travel, as it were, on a following "
        "wind. But your own spirit will explain this better than my pen. I have played the "
        "friend's role — of one who reminds rather than instructs — and I trust that you "
        "will soon show yourself greater than even the great expectations surrounding you. "
        "As for the rest, remember, in sending your greetings, both to fulfil your own "
        "duty and to encourage my diligence in return.\n\n"
        "---\n\n"
        "To Siburius: I yield to your rules and take up the economy of style you prescribe, "
        "not unwillingly. But bear in mind: what later usage has adopted often seems simple "
        "to some, not barbaric. You want our letters to carry bare names in the old fashion? "
        "If you love antiquity that much, let us return with equal zeal to the archaic words "
        "the Salian priests chant, the augurs use for bird-omens, and the decemvirs employed "
        "for the Twelve Tables. All that was abandoned long ago, as the custom of succeeding "
        "ages replaced what had pleased before. Or if we had to write a court speech, would "
        "we preface it in Cato's manner with Jupiter and all the gods, for fear of being "
        "charged with contempt of antiquity or ignorance? And yet it is better to follow "
        "Cicero, who adopted openings that were unknown to his predecessors. But why say "
        "more on this, since I bow to your authority and have yielded to your wishes? As "
        "for writing often — you need no urging from me. The steady stream of my letters "
        "will keep you reminded of our mutual duty."
    ),

    # Book 5.35 — Two letters: recommendation for Helpidius; protest to Felix about Eusebius
    # Second letter ends with the Eusebius property dispute.
    # Latin ends (last readable): "rescriptorum omnium fama te respicit."
    5181: (
        "From: Quintus Aurelius Symmachus, Roman Senator\n"
        "To: Felix and others (multiple short letters)\n"
        "Date: ~383–397 AD\n"
        "Context: A recommendation for a friend named Helpidius, and a note to Felix "
        "expressing concern about the improper appointment of a procurator.\n\n"
        "Our brother Helpidius was called away not only by desire for your company but "
        "also by the consul's letter. Although the old bond between you promises him your "
        "affection, I think my recommendation will add something as well. Build up, I "
        "ask you, your old devotion to our friend with fresh favors, so that what has "
        "already been accomplished may be crowned — and grant me this boon: let him feel "
        "that the merit he established with you through his own loyal service has been "
        "enhanced by my endorsement.\n\n"
        "---\n\n"
        "To Felix (~396–397 AD): Whoever neglects a friend's reputation is unstable in "
        "loyalty. To ensure that this vice is not justly charged to me, I am worried "
        "about your standing even in other people's disputes. By what law, by what public "
        "interest, did an unknown and untested procurator draw out the distinguished "
        "Eusebius — who is said to have served among the imperial notaries — so that a "
        "civil case might be snatched away from the city courts? I ask you to consider "
        "what it is proper to request from the sacred chancery whose decrees you pronounce. "
        "I speak with a brother's concern: the reputation of all imperial rescripts "
        "reflects on you."
    ),

    # Book 5.46 — Symmachus intervenes in a treasury dispute for someone in southern Italy
    # Latin ends: "numquam tamen poterit emereri, ut illi a te sine alio disceptatore credatur."
    5192: (
        "I would say more, if justice needed many prayers to assist it. The official "
        "report will lay out the nature of the case; and though it will protect the "
        "examiner from error, it can never earn the right to have his judgment accepted "
        "by you without a second arbiter."
    ),

    # Book 6.27 — Symmachus reports on the slow selection of envoys for the Senate
    # Latin ends: "quae cum terminum confirmationis acceperit, plana ad te cognitio
    #              deferetur. vale."
    5250: (
        "From: Quintus Aurelius Symmachus, Roman Senator\n"
        "Date: ~393 AD\n"
        "Context: Symmachus reports news from Rome, including the slow selection of "
        "senatorial envoys.\n\n"
        "I've also lifted the spirits of the Roman people.\n\n"
        "So I've ordered the pack animals to return to you, with my thanks for helping "
        "your brother's needs with proper support. The selection of envoys is still "
        "unsettled — Postumianus and Pinianus, whom the Senate initially entrusted with "
        "its instructions, now face a third candidate in Paulinus; with the parties split "
        "in their preferences, the business continues to be delayed. Once a decision is "
        "confirmed, you will receive a clear account of it. Farewell."
    ),

    # Book 7.54 — Multiple short letters including one about the return of Faustus
    # Final letter ends: "quo vobis redditos sanitati communes filios indicamus."
    5362: (
        "From: Quintus Aurelius Symmachus, Roman Senator\n"
        "Date: ~395–402 AD\n"
        "Context: Three short letters to friends and family — a greeting, a reply to a "
        "surprise letter, and news of the return of his son Faustus.\n\n"
        "Since a long exchange between us had fallen quiet, I could no longer put off the "
        "customary greeting. Your turn to reciprocate — and if the day I'm hoping for "
        "arrives, your reply will be medicine for my recovery.\n\n"
        "TO THE SAME:\n\n"
        "After sending the page with my greeting, someone arrived just in time with your "
        "letter. The joy I felt at your opening words was extraordinary — how much it "
        "matters that a letter finds a ready heart to receive it.\n\n"
        "TO HIS BROTHERS:\n\n"
        "I sent a letter a little earlier to announce our son Faustus's return, so that "
        "swift reassurance might calm the impatience of your longing. But I did not "
        "begrudge repeating the greeting of good news as he himself sets out. Take, "
        "therefore, a twofold joy: first from his return itself, and then from this "
        "brotherly report in which we tell you that our children have been restored to "
        "good health."
    ),

    # Book 7.72 — Two letters: brief greeting; then worry about friend's health
    # Second letter (CXXX) ends: "sed magnae sollicitudinis tribui levamen exopto."
    5380: (
        "Don't judge my care for you by the length of this letter. A greeting is brief "
        "in words but expansive in its prayers. Let me imitate, in my regard for you, "
        "the economy of religious rites — short in their outward form, boundless in their "
        "devotion.\n\n"
        "---\n\n"
        "To Sibitius: My heart is sick until I have certain word that you have reached "
        "the harbor of health. I ask you to satisfy this expectation. What I seek is not "
        "the honor of a literary courtesy, but relief from a very great anxiety."
    ),

    # Book 8.13 — Two letters; second to Strategius about Symmachus's slow convalescence
    # Second letter ends: "spero enim tantundem accessurum sanitati meae ex conspectu
    #                      vestro, quantum sperari possit ex otio. vale."
    5398: (
        "May this custom endure, and may the mutual assurance of well-being be renewed "
        "between us year after year. Farewell.\n\n"
        "TO STRATEGIUS:\n\n"
        "You press me with a lover's longing to come home. My heart, hungry for your "
        "company, has been asking for exactly this. But my injured health stands in the "
        "way — though I should be grateful for my absence, since it has secured me a "
        "kind of promissory note of your testimonial. Still, I will not prolong your "
        "wait once my strength is restored; and because this seems long to an anxious "
        "friend, I shall hurry my return after visiting the estate nearby. I trust that "
        "seeing your faces will do as much for my health as rest could hope to accomplish. "
        "Farewell."
    ),

    # Book 8.19 — Two letters including one to Romulus on the joy of correspondence
    # Last letter ends: "ideo maior est sitis, quia sapor dulcior. vale."
    5404: (
        "And if fortune favors, I'll follow the letter in person soon.\n\n"
        "TO SERVIUS:\n\n"
        "You're waiting for my letters, I gather — as though you yourself shouldn't be "
        "the one to take the lead in these friendly duties. Perhaps you'll plead custom, "
        "since many people believe the senior party should write first. But I — since we "
        "share equal enthusiasm for each other's letters — think the first move should "
        "belong to whoever feels the keener longing.\n\n"
        "TO ROMULUS:\n\n"
        "I have no doubt you await my letters — I feel the same impatient longing for "
        "yours. We have one purpose in writing: to earn a reply. And as with drinking "
        "from a spring, the thirst only grows because the taste is sweeter. Farewell."
    ),

    # Book 8.20 — Letters to Dionysius and others; ends with reflection on a settled Rome
    # Last readable Latin: "illius desiderii, quo prae cunctis vitae voluptatibus
    #                        patriam meam diligo."
    5405: (
        "Break into the gifts of familiar writing and share with me whatever you've "
        "accomplished in administering the city's welfare for the public good. And "
        "don't let modesty rob me of the pleasure — a letter shouldn't be shy about "
        "its own achievements.\n\n"
        "TO DIONYSIUS:\n\n"
        "We were offended that the premature silence of your pen deprived us of our "
        "usual pleasure in your letters. Now, however, after the flight from all anxieties "
        "— the city's calm having been secured by your counsel, which brought the plebs "
        "back to a proper sense of shame — I shall be able to enjoy what I might call a "
        "well-fed holiday. Though I should not be prescribing what is uncertain to your "
        "mind — knowing as I do the tender affection I bear you all, and the longing with "
        "which I love my home city above all the pleasures of life."
    ),

    # Book 9.23 — Two short letters including one to Caecilianus about olive oil for Formiae
    # Last letter ends: "cui debet adicere celeritatem praestantis humanitas."
    5434: (
        "I ask that, having been admitted into your clientele, he may be glad both that "
        "my patronage has been of use to him and that yours has been added.\n\n"
        "---\n\n"
        "To Caecilianus: I do not refuse to intercede on behalf of just debts — it would "
        "be wrong to decline an opportunity for a favor in such a case. The people of "
        "Formiae [a town on the Via Appia, modern Formia] have had a fixed allotment of "
        "olive oil from Africa decreed by long tradition for the relief of their poverty. "
        "They ask you to maintain the custom preserved by long usage, to which your "
        "distinguished humanity must also add its dispatch."
    ),
}


# ─── Category 2: Mark as genuinely truncated ─────────────────────────────────
TRUNCATED_IDS = [
    4862, 4882, 4914, 4925, 4937, 4948, 4950, 4955, 4993, 4995, 4999,
    5003, 5072, 5091, 5128, 5131, 5134, 5136, 5139, 5188, 5191, 5241,
    5260, 5324, 5326, 5348, 5373, 5376, 5377, 5400, 5406, 5439, 5442, 5444,
]


def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    # Apply completions
    completed = 0
    for letter_id, full_text in COMPLETIONS.items():
        cur.execute(
            "UPDATE letters SET modern_english = ? WHERE id = ?",
            (full_text, letter_id),
        )
        if cur.rowcount:
            completed += 1

    # Mark truncated ones
    marked = 0
    for letter_id in TRUNCATED_IDS:
        cur.execute(
            "SELECT modern_english FROM letters WHERE id = ?", (letter_id,)
        )
        row = cur.fetchone()
        if not row:
            continue
        text = row[0] or ""
        # Only update if it ends with "..." and doesn't already have the marker
        if (text.rstrip().endswith("...") or text.rstrip().endswith("…")) and \
                "[Text breaks off" not in text:
            new_text = text.rstrip()
            if new_text.endswith("..."):
                new_text = new_text[:-3].rstrip()
            new_text += " [Text breaks off in source.]"
            cur.execute(
                "UPDATE letters SET modern_english = ? WHERE id = ?",
                (new_text, letter_id),
            )
            if cur.rowcount:
                marked += 1

    conn.commit()
    print(f"Completed translations: {completed}")
    print(f"Marked as truncated: {marked}")

    # Verify — show all 67 are now resolved
    cur.execute(
        """
        SELECT COUNT(*) FROM letters
        WHERE collection = 'symmachus'
          AND modern_english IS NOT NULL
          AND modern_english LIKE '%...'
          AND modern_english NOT LIKE '%[Text breaks off%'
        """
    )
    remaining = cur.fetchone()[0]
    print(f"Still-unresolved '...' endings: {remaining}")

    conn.close()


if __name__ == "__main__":
    main()

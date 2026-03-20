#!/usr/bin/env python3
"""
Generate rich biographical profiles for every major person in the letters database.
Adds a 'bio' column to the authors table and populates it with 2-3 paragraph profiles
for every author with 5+ letters (sent or received).

Usage: python3 scripts/generate_author_profiles.py
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')


# ── Author profiles ────────────────────────────────────────────────────────────
# Keyed by author ID. Each profile is written in the modern nonfiction voice
# described in the voice guide: clear, engaging, literate, never stuffy.

PROFILES = {

    # ── Quintus Aurelius Symmachus (id=6) ──────────────────────────────────────
    6: (
        "Quintus Aurelius Symmachus (c. 345–402) was the last great champion of "
        "Rome's pagan aristocracy — a senator, orator, and prolific letter writer "
        "who treated correspondence the way a modern politician treats networking. "
        "Born into one of Rome's most powerful families, he served as proconsul of "
        "Africa, urban prefect of Rome, and consul, always moving in the circles "
        "where old money and old religion still held sway. His most famous moment "
        "was the appeal to restore the Altar of Victory to the Roman Senate house "
        "in 384, a cause he lost to Ambrose of Milan — but one that crystallized "
        "the final confrontation between paganism and Christianity at the highest "
        "levels of Roman government.\n\n"
        "His surviving letters — nearly 900 of them, the largest collection from "
        "any late Roman figure — are a masterclass in aristocratic self-presentation. "
        "They are polished, elegant, and almost pathologically discreet: Symmachus "
        "rarely says anything controversial, rarely reveals strong emotion, and "
        "almost never discusses politics directly. What he does, constantly, is "
        "maintain relationships. He recommends friends for appointments, congratulates "
        "colleagues on promotions, exchanges literary compliments, and arranges the "
        "spectacles for his son's praetorian games with almost obsessive attention "
        "to detail (including a memorable disaster involving crocodiles). His "
        "correspondents include nearly every important figure of late fourth-century "
        "Rome.\n\n"
        "What makes Symmachus historically significant is precisely what makes him "
        "frustrating to read: the letters reveal how Rome's elite actually "
        "functioned. This was a world held together by favors, recommendations, "
        "and carefully maintained social networks — and Symmachus was its supreme "
        "practitioner. His letters are the closest thing we have to watching the "
        "Roman aristocracy work in real time, and they show a class of people who "
        "believed, right up to the end, that civilization meant keeping up "
        "appearances."
    ),

    # ── Cassiodorus (id=7) ─────────────────────────────────────────────────────
    7: (
        "Cassiodorus (c. 485–585) lived one of the most remarkable lives of the "
        "sixth century. He served as the chief minister of the Ostrogothic kings "
        "of Italy — essentially running the Roman bureaucratic machine for Germanic "
        "rulers who wanted to govern like Roman emperors — and then, after that "
        "world collapsed, reinvented himself as a monk and scholar who helped "
        "preserve classical learning through the early Middle Ages. His Variae, "
        "a collection of nearly 470 official letters and edicts written on behalf "
        "of kings Theoderic, Athalaric, and others, is one of the most important "
        "administrative archives to survive from any period of Roman history.\n\n"
        "The letters are formal, deliberate, and often elaborately learned — "
        "Cassiodorus could not resist working in a classical allusion or a "
        "philosophical digression even when issuing a routine tax directive. "
        "He writes about everything from the appointment of provincial governors "
        "to the proper repair of the Colosseum, from monetary policy to the "
        "marvels of Vesuvius. His correspondents (or rather, the recipients of "
        "royal pronouncements) span the entire governing apparatus: senators, "
        "bishops, generals, tax collectors, and foreign rulers including the "
        "emperor in Constantinople.\n\n"
        "What makes the Variae irreplaceable is that they show us how a barbarian "
        "kingdom actually governed. Cassiodorus was deliberately crafting an image "
        "of civilized continuity — presenting Theoderic's Ostrogothic Italy as the "
        "legitimate heir of Roman administration. The ornate style is itself the "
        "message: as long as the letters sounded Roman, the government was Roman. "
        "It was a magnificent performance, and the fact that Cassiodorus carefully "
        "collected and published these letters suggests he knew it was one."
    ),

    # ── Pope Gregory the Great (id=11) ─────────────────────────────────────────
    11: (
        "Pope Gregory I (c. 540–604), known to history as Gregory the Great, was "
        "the most important pope of the early Middle Ages and possibly the busiest "
        "man in the sixth-century Mediterranean. A former Roman prefect turned monk "
        "turned reluctant pope, Gregory inherited a world in crisis — Italy "
        "devastated by plague and Lombard invasions, the Western empire gone, and "
        "the Roman church increasingly the only institution capable of keeping "
        "things running. His surviving letters, over 850 of them preserved in a "
        "papal register, document one of the most impressive one-man administrative "
        "performances in history.\n\n"
        "Gregory wrote to everyone. He managed the vast papal estates in Sicily and "
        "North Africa that fed Rome's population. He negotiated with the Lombard "
        "queen Theodelinda and traded sharp words with the imperial exarch in "
        "Ravenna. He dispatched missionaries to England, reorganized the church in "
        "Gaul, mediated disputes in Constantinople, and still found time to answer "
        "detailed pastoral questions from bishops about everything from baptismal "
        "procedure to whether clergy could take baths. His most important "
        "correspondents include Januarius of Cagliari (a frequent headache), "
        "Marinianus of Ravenna, the exarch Romanus, and Queen Brunhild of the "
        "Franks.\n\n"
        "What comes through in Gregory's letters, unmistakably, is a man of "
        "enormous competence who genuinely cared about getting things right. He "
        "could be stern — his rebukes of negligent bishops are devastating in "
        "their precision — but he was also deeply compassionate, intervening "
        "repeatedly on behalf of slaves, Jews facing forced conversion, and "
        "anyone he felt was being treated unjustly. His voice is clear-headed, "
        "authoritative, and practical, the voice of a natural leader handling "
        "an overwhelming workload with intelligence and genuine moral seriousness."
    ),

    # ── Basil of Caesarea (id=13) ──────────────────────────────────────────────
    13: (
        "Basil of Caesarea (c. 330–379), known as Basil the Great, was one of the "
        "most influential figures in the history of Christianity — a theologian who "
        "helped define the doctrine of the Trinity, a bishop who built what may "
        "have been the first hospital in history, and a practical church leader "
        "who set the pattern for Eastern monasticism that persists to this day. "
        "Born into a wealthy Cappadocian family that produced an extraordinary "
        "number of saints (his grandmother, both parents, sister, and two brothers "
        "are all venerated), Basil studied at Athens alongside his lifelong friend "
        "Gregory of Nazianzus, then gave up a promising career in rhetoric to "
        "pursue the ascetic life.\n\n"
        "His letters — over 350 survive — reveal a man who was simultaneously "
        "running a diocese, fighting the Arian heresy, managing a vast charitable "
        "operation, and dealing with an unending stream of personal and political "
        "crises. He wrote constantly to Amphilochius of Iconium on points of "
        "canon law, sparred with the rhetorician Libanius (one of the rare "
        "sustained exchanges between a Christian bishop and a pagan intellectual), "
        "and maintained a sometimes strained correspondence with Gregory of "
        "Nazianzus, whose feelings he had a tendency to bruise. His letters to "
        "Eusebius of Thessalonica and Meletius of Antioch chart the complicated "
        "ecclesiastical politics of the Eastern church during the Arian crisis.\n\n"
        "Basil's personality comes through vividly: practical, caring, occasionally "
        "exasperated, and always short on time. He was a born administrator with "
        "a genuine pastoral heart, the kind of leader who would write a detailed "
        "letter about trinitarian theology in the morning and spend the afternoon "
        "organizing food distribution for famine victims. His health was terrible "
        "— he suffered from chronic liver disease and died at just 49 — but his "
        "letters show no slackening of energy or commitment right up to the end."
    ),

    # ── Augustine of Hippo (id=2) ─────────────────────────────────────────────
    2: (
        "Augustine of Hippo (354–430) needs almost no introduction — he is one of "
        "the most influential thinkers in Western history, the man whose "
        "Confessions and City of God shaped Christian theology, philosophy, and "
        "political thought for a millennium and beyond. But the Augustine of the "
        "letters is a different, more human figure than the towering intellectual "
        "of the treatises: here is a bishop dealing with schismatics and tax "
        "disputes, a friend writing warmly to old companions, and a mind that "
        "never stopped asking questions even when he was supposed to be giving "
        "answers.\n\n"
        "His letter collection — over 260 surviving items — spans nearly his "
        "entire adult life, from his early philosophical correspondence with his "
        "friend Nebridius in the late 380s to his final years as the Vandals "
        "closed in on North Africa. The letters to Nebridius are some of the most "
        "appealing: two young intellectuals batting ideas back and forth with "
        "genuine excitement, marveling at the nature of memory and imagination. "
        "His long exchange with Jerome is famously contentious — two brilliant, "
        "proud men who respected each other enormously but could not stop "
        "disagreeing. His letters to fellow African bishops like Aurelius of "
        "Carthage reveal the grinding daily work of running a diocese and fighting "
        "the Donatist schism.\n\n"
        "What makes Augustine's letters historically significant is that they let "
        "us watch one of the greatest minds in history actually thinking. He uses "
        "letters the way a modern intellectual uses essays — working through "
        "problems, testing ideas on correspondents, circling back to questions "
        "that won't leave him alone. His tone is warm, searching, and "
        "intellectually restless, like a brilliant friend who can't stop thinking "
        "out loud. Even his most routine episcopal correspondence has flashes of "
        "insight that remind you this is the man who essentially invented the "
        "concept of the inner self."
    ),

    # ── Hormisdas (id=377) ────────────────────────────────────────────────────
    377: (
        "Pope Hormisdas (c. 450–523) served as bishop of Rome from 514 to 523, "
        "during one of the most delicate periods in the relationship between the "
        "Western and Eastern churches. His great achievement was ending the Acacian "
        "Schism — the 35-year break in communion between Rome and Constantinople "
        "that had divided Christendom since 484. The Formula of Hormisdas, which "
        "required Eastern bishops to accept Roman primacy as a condition of "
        "reunion, was signed by over 2,500 bishops and became one of the "
        "foundational documents of papal authority.\n\n"
        "His surviving letters — nearly 250 of them — are almost entirely "
        "diplomatic and administrative, focused on the complex negotiations with "
        "Constantinople and the management of the Western church under Ostrogothic "
        "rule. They reveal a careful, patient diplomat who understood that the "
        "reunion he sought required both firmness on principle and flexibility on "
        "details. He corresponded with the Emperor Justin I, the patriarch John of "
        "Constantinople, and a network of bishops and imperial officials across "
        "both halves of the former Roman Empire.\n\n"
        "What makes Hormisdas's letters valuable is that they document, in "
        "granular detail, how early medieval diplomacy actually worked. Every "
        "letter is a calculated move in a long game of ecclesiastical chess, and "
        "reading them in sequence reveals just how much patience and persistence "
        "it took to stitch a divided church back together. His voice is measured "
        "and authoritative — this is a pope who understood that power, in a world "
        "without armies, depended entirely on the careful deployment of words."
    ),

    # ── Theodoret of Cyrrhus (id=373) ─────────────────────────────────────────
    373: (
        "Theodoret of Cyrrhus (c. 393–c. 458) was one of the most important — "
        "and most controversial — theologians of the fifth-century Eastern church. "
        "As bishop of the small Syrian city of Cyrrhus, he was a major voice in "
        "the Christological controversies that convulsed the Eastern empire, siding "
        "with the Antiochene school against Cyril of Alexandria in debates over "
        "the nature of Christ that would ultimately split the church permanently. "
        "Condemned at the Second Council of Ephesus in 449 (the so-called 'Robber "
        "Council'), he was rehabilitated at Chalcedon in 451, though his legacy "
        "remained contested for centuries.\n\n"
        "His surviving letters — over 180 — are a vivid window into the "
        "theological politics of the Eastern church at its most intense. They "
        "document his friendships, his feuds, his appeals for help when deposed, "
        "and his tireless advocacy for what he saw as theological orthodoxy. "
        "Despite the high-stakes doctrinal warfare, Theodoret was also a devoted "
        "pastor: his letters describe building bridges, aqueducts, and public "
        "baths for Cyrrhus, and his genuine affection for his small, poor diocese "
        "comes through clearly.\n\n"
        "What makes Theodoret's letters historically significant is that they show "
        "the human side of the great Christological debates — the friendships "
        "strained, the careers destroyed, the real fear of exile and disgrace that "
        "accompanied theological disagreement in an age when emperors enforced "
        "doctrinal conformity. His voice is learned, passionate, and sometimes "
        "wounded — a man who believed deeply that he was right and could not "
        "understand why the world kept punishing him for it."
    ),

    # ── Synesius of Cyrene (id=477) ───────────────────────────────────────────
    477: (
        "Synesius of Cyrene (c. 370–c. 413) was one of the most colorful figures "
        "of the late Roman world — a Neoplatonic philosopher, gentleman farmer, "
        "and reluctant bishop who never quite gave up his love of hunting, "
        "philosophy, or his pet astrolabe. Born into an old Libyan aristocratic "
        "family that claimed descent from Spartan colonists, he studied under "
        "the great Hypatia in Alexandria, served as ambassador to Constantinople "
        "where he delivered a bold speech criticizing the emperor, and was "
        "eventually elected bishop of Ptolemais in Cyrenaica despite openly "
        "admitting he was not sure he believed in the resurrection of the body.\n\n"
        "His letters — about 160 survive — are among the most personally "
        "revealing from late antiquity. He writes with wit and warmth about "
        "everything: a near-shipwreck on a voyage from Alexandria, his experiments "
        "with hydroscopes, his efforts to defend his province against nomadic "
        "raiders, his grief at the death of his children, and his philosophical "
        "reflections on everything from dreams to the nature of the soul. His "
        "correspondents include Hypatia herself, military commanders, fellow "
        "bishops, and old friends from his student days.\n\n"
        "Synesius matters because he shows us what it was like to be a thoughtful, "
        "cultured person living through the slow unraveling of Roman order in a "
        "provincial backwater. His letters are honest, vivid, and deeply human — "
        "the testimony of a man who loved life, loved ideas, and found himself "
        "responsible for a community he could barely protect. Of all the late "
        "antique letter writers, Synesius is the one you most want to have dinner "
        "with."
    ),

    # ── Jerome (id=3) ──────────────────────────────────────────────────────────
    3: (
        "Jerome (c. 347–420) was the greatest biblical scholar of the early church "
        "and one of the most brilliantly difficult personalities in Christian "
        "history. The man who translated the Bible into Latin — the Vulgate, which "
        "would remain the standard text of Western Christianity for over a thousand "
        "years — was also a ferocious polemicist, a devoted ascetic, and an "
        "inveterate gossip who could not resist a cutting remark even when "
        "diplomacy would have served him better. Born in Dalmatia, educated in "
        "Rome, and eventually settled in Bethlehem, Jerome spent his life at the "
        "intersection of scholarship and controversy.\n\n"
        "His letters — over 130 survive in this collection — are some of the most "
        "entertaining reading from late antiquity. His correspondence with Marcella, "
        "the Roman noblewoman who led an ascetic circle on the Aventine, is warm "
        "and intellectually rich. His exchanges with Augustine are famously "
        "combative — two titans of the early church who could not agree on the "
        "interpretation of Galatians and were too proud to let it go. His letters "
        "to Damasus, bishop of Rome, are respectful but pointed, those to "
        "Pammachius are learned and personal, and his attacks on Rufinus — once "
        "his closest friend — are among the most savage literary takedowns in "
        "ancient literature.\n\n"
        "Jerome's historical significance is immense: his letters document the "
        "intellectual world of late antique Christianity in extraordinary detail, "
        "from debates over biblical translation to the growth of the ascetic "
        "movement to the social dynamics of Rome's Christian aristocracy. But it "
        "is his voice that makes them unforgettable — sharp, learned, often "
        "cutting, the voice of a man who was too witty for his own good and who "
        "made enemies because he could not resist a devastating line. Reading "
        "Jerome is never boring."
    ),

    # ── Sidonius Apollinaris (id=5) ────────────────────────────────────────────
    5: (
        "Sidonius Apollinaris (c. 430–489) was a Gallo-Roman aristocrat, poet, "
        "and bishop who watched the Roman Empire disappear in Gaul and tried, "
        "with considerable grace, to preserve what he could. Born into one of the "
        "most distinguished families of Roman Gaul — his father-in-law was the "
        "emperor Avitus, and he himself served as urban prefect of Rome — Sidonius "
        "eventually became bishop of Clermont, where he organized the defense of "
        "the city against the Visigoths before it was finally ceded by treaty in "
        "475. He survived capture and imprisonment to spend his final years trying "
        "to maintain Roman culture in a world that was becoming visibly Barbarian.\n\n"
        "His letters — 146 survive, carefully arranged in nine books modeled on "
        "Pliny — are a deliberate literary performance. Sidonius writes about "
        "dinner parties and country estates, literary criticism and aristocratic "
        "friendships, church business and political crises, always in an ornate, "
        "allusive style that announces on every page: we are still Romans, we "
        "still have our culture, we still know how to write a proper Latin "
        "sentence. He is conscious that he is preserving a way of life that is "
        "disappearing, and the letters are as much monument as correspondence.\n\n"
        "What makes Sidonius invaluable to historians is precisely this: he "
        "documents the end of Roman Gaul from the inside, as a participant who "
        "understood exactly what was being lost. His descriptions of Visigothic "
        "kings, Burgundian table manners, and the fading infrastructure of Roman "
        "administration are irreplaceable. His voice is literary, elegant, and "
        "tinged with nostalgia — a man of immense cultivation writing in a world "
        "where cultivation was becoming a luxury fewer and fewer people could "
        "afford."
    ),

    # ── Gregory of Nazianzus (id=299) ─────────────────────────────────────────
    299: (
        "Gregory of Nazianzus (c. 329–390) was one of the Cappadocian Fathers — "
        "the trio of theologians, alongside Basil of Caesarea and Gregory of Nyssa, "
        "who gave definitive shape to the Christian doctrine of the Trinity. He "
        "briefly served as bishop of Constantinople and presided over the First "
        "Council of Constantinople in 381, but his heart was never in "
        "administration. Gregory was a poet, a rhetorician, and a contemplative "
        "who was repeatedly dragged into public life against his will — most "
        "notably by his friend Basil, who ordained him bishop of the backwater "
        "town of Sasima without asking, an injury Gregory never fully forgave.\n\n"
        "His surviving letters — over 240, with 92 in this collection — are the "
        "work of a man who combined genuine theological brilliance with a "
        "sensitivity that could tip into self-pity. His correspondence with Basil "
        "is the most revealing: two men who loved each other deeply but could not "
        "stop hurting each other, Gregory feeling used and overlooked, Basil "
        "frustrated by Gregory's reluctance to commit to the ecclesiastical "
        "battles that consumed his own life. Other letters reveal his talent for "
        "friendship, his skill as a literary stylist, and his deep ambivalence "
        "about public life.\n\n"
        "Gregory's letters matter because they give us the inner life of one of "
        "Christianity's greatest theologians — and because they are beautifully "
        "written. He is the most literary of the Cappadocian Fathers, the one "
        "who cared most about getting the sentences right. His voice is reflective, "
        "sometimes melancholy, always intelligent — the voice of a man who would "
        "have been happiest in a library but kept being asked to run a church."
    ),

    # ── Julian the Apostate (id=476) ──────────────────────────────────────────
    476: (
        "Julian (331–363), known to Christian history as 'the Apostate,' was the "
        "last pagan emperor of Rome and one of the most fascinating figures of "
        "late antiquity. Raised as a Christian after his family was massacred by "
        "his cousin Constantius II, Julian secretly converted to traditional "
        "Greco-Roman religion as a young man and, upon becoming emperor in 361, "
        "launched an ambitious program to restore paganism as the empire's "
        "dominant faith. He died just two years into his reign, killed during a "
        "campaign against Persia, and his religious revolution died with him.\n\n"
        "His surviving letters — over 80 in this collection — reveal a complex, "
        "intensely intellectual ruler who combined genuine philosophical commitment "
        "with sharp political instinct. He writes about theology, governance, "
        "education policy, and military affairs with equal facility. His famous "
        "letter banning Christian teachers from teaching classical literature is "
        "here, as are his attempts to create a pagan charitable infrastructure "
        "modeled on (and meant to compete with) Christian institutions. He "
        "corresponded with philosophers, priests, governors, and generals.\n\n"
        "Julian's letters are historically significant because they show us what "
        "a pagan restoration might have looked like — and why it failed. His "
        "vision of a reformed, philosophical paganism was too intellectual, too "
        "dependent on one man's will, and too out of step with the direction of "
        "late Roman society. But the letters are compelling reading: the voice is "
        "that of a brilliant, passionate, slightly lonely man who believed he "
        "could turn back the tide of history through sheer force of conviction."
    ),

    # ── Cyprian of Carthage (id=372) ──────────────────────────────────────────
    372: (
        "Cyprian of Carthage (c. 200–258) was bishop of Carthage during one of "
        "the most turbulent periods in early Christian history — the Decian "
        "persecution of 250–251, which forced Christians across the Roman Empire "
        "to choose between sacrifice to the Roman gods and death. Cyprian himself "
        "went into hiding during the persecution, a decision that was controversial "
        "at the time but allowed him to continue leading his church through a "
        "crisis that threatened to tear it apart. He was eventually martyred under "
        "the emperor Valerian in 258.\n\n"
        "His letters — over 80 survive — are primarily concerned with the "
        "agonizing question of what to do with Christians who had lapsed during "
        "the persecution: those who had sacrificed to the gods, bought false "
        "certificates, or otherwise compromised their faith. The debate over "
        "readmission split the church in both Carthage and Rome, and Cyprian's "
        "letters chart the factional warfare in vivid detail. He writes to his "
        "clergy, to the confessors and martyrs in prison, to Pope Cornelius in "
        "Rome, and to the Novatianist schismatics who wanted to exclude the lapsed "
        "permanently.\n\n"
        "Cyprian's letters are historically invaluable because they document the "
        "early church under extreme pressure — not the idealized community of Acts, "
        "but a real institution with factions, power struggles, and impossible "
        "moral dilemmas. His voice is authoritative and pastoral, that of a leader "
        "trying to hold a community together when the questions have no easy "
        "answers. His letters also shaped the development of ecclesiology: his "
        "arguments about church unity, the authority of bishops, and the limits "
        "of forgiveness influenced Christian thought for centuries."
    ),

    # ── Pope Pelagius I (id=491) ──────────────────────────────────────────────
    491: (
        "Pope Pelagius I (c. 500–561) became bishop of Rome in 556 under "
        "circumstances that haunted his entire pontificate. He had been a vigorous "
        "opponent of Emperor Justinian's condemnation of the Three Chapters — a "
        "theological decree that many Western bishops saw as a betrayal of the "
        "Council of Chalcedon — but then reversed his position and accepted the "
        "condemnation as the price of becoming pope. It was a pragmatic decision "
        "that cost him enormously: large parts of the Western church refused to "
        "accept his authority, and he spent his entire papacy trying to win them "
        "back.\n\n"
        "His surviving letters — over 80 — document a pope under siege from his "
        "own side. He writes constantly to bishops in Gaul, Northern Italy, and "
        "Africa, alternately cajoling and threatening, trying to restore communion "
        "with churches that regarded him as compromised. At the same time, he had "
        "to manage a Rome devastated by decades of Gothic War, deal with Lombard "
        "threats, and maintain a working relationship with Constantinople.\n\n"
        "Pelagius's letters matter because they show the papacy at one of its "
        "weakest moments — not the triumphant institution of later centuries but a "
        "fragile authority struggling to hold the Western church together. His "
        "voice is earnest, sometimes defensive, always aware that his legitimacy "
        "is being questioned. The letters are a reminder that the medieval papacy "
        "was not built in a day, and that the road from the early church to the "
        "high medieval papacy ran through some very dark valleys."
    ),

    # ── Pope Leo the Great (id=12) ────────────────────────────────────────────
    12: (
        "Pope Leo I (c. 400–461), known as Leo the Great, was the pope who "
        "defined what it meant to be pope. Serving from 440 to 461, he asserted "
        "Roman primacy with a clarity and force that no previous bishop of Rome "
        "had matched, and his theological formulation of Christ's two natures — "
        "set out in his famous Tome, a letter to Patriarch Flavian of "
        "Constantinople — was adopted by the Council of Chalcedon in 451 as "
        "the definitive statement of orthodox Christology. He is also remembered "
        "for personally confronting Attila the Hun outside Rome in 452, persuading "
        "him to turn back — though the details of that encounter remain debated.\n\n"
        "His surviving letters — 73 in this collection — are predominantly "
        "concerned with church governance and doctrinal authority. He writes to "
        "bishops across the Mediterranean, asserting Rome's right to adjudicate "
        "disputes, define doctrine, and supervise provincial churches. His "
        "correspondents include Julian of Antioch, Pulcheria Augusta (the "
        "influential sister of Emperor Theodosius II), Flavian and Anatolius of "
        "Constantinople, and bishops across Gaul, Spain, and North Africa.\n\n"
        "Leo's letters are historically significant because they document the "
        "construction of papal authority in real time. Here is a pope who "
        "genuinely believed he spoke with the authority of Saint Peter and who "
        "had the intellectual and political skill to make others accept that "
        "claim. His voice is measured, confident, and deeply authoritative — "
        "the voice of a man who knew exactly what he was doing and why it "
        "mattered. His Tome alone would secure his place in history; his letters "
        "show the full scope of a mind that combined theological precision with "
        "political genius."
    ),

    # ── Isidore of Pelusium (id=483) ─────────────────────────────────────────
    483: (
        "Isidore of Pelusium (c. 360–c. 435) was an Egyptian monk and priest "
        "whose enormous letter collection — tradition attributes over 2,000 "
        "letters to him, with some 52 represented in this database — made him one "
        "of the most prolific correspondents of the early church. Based in a "
        "monastery near Pelusium on the eastern edge of the Nile Delta, Isidore "
        "was a devoted student of John Chrysostom and a sharp critic of anything "
        "he considered theological error or moral laxity.\n\n"
        "His letters are typically short and pointed — moral exhortations, "
        "scriptural interpretations, and occasional rebukes delivered with "
        "monastic directness. He wrote to bishops, officials, monks, and laypeople, "
        "dispensing advice on everything from the proper interpretation of Genesis "
        "to the duties of public office. His correspondents ranged from the "
        "powerful to the obscure.\n\n"
        "Isidore matters because his letters offer a window into everyday "
        "Christianity in fifth-century Egypt — not the grand theological "
        "controversies of the councils but the practical questions of faith, "
        "morality, and scriptural understanding that occupied ordinary clergy and "
        "laity. His voice is that of a learned, earnest spiritual director: never "
        "flashy, always sincere, and occasionally sharp when he felt someone "
        "needed correction."
    ),

    # ── Pope Gelasius I (id=376) ─────────────────────────────────────────────
    376: (
        "Pope Gelasius I (c. 445–496) served as bishop of Rome from 492 to 496 — "
        "a short pontificate that was nonetheless one of the most intellectually "
        "consequential in papal history. He is best known for his letter to "
        "Emperor Anastasius I articulating the doctrine of the 'two powers' — "
        "the idea that the world is governed by two distinct authorities, the "
        "sacred authority of bishops and the royal power of emperors, each supreme "
        "in its own sphere. This formulation would shape Western political thought "
        "for a thousand years.\n\n"
        "His surviving letters — 45 in this collection — show a pope navigating "
        "the aftermath of the Acacian Schism with a combination of theological "
        "rigor and political firmness. He wrote to Eastern bishops, Western "
        "clergy, and the emperor himself, consistently asserting Roman authority "
        "while trying to manage the practical realities of a divided church. "
        "He also produced important decrees on liturgy, church discipline, and "
        "the treatment of the Manichaeans.\n\n"
        "Gelasius's letters are significant because they represent the papacy at "
        "a crucial turning point — asserting ideological independence from "
        "Constantinople at the very moment when political independence was "
        "becoming a reality. His voice is sharp, doctrinally precise, and "
        "uncompromising — a pope who believed that Rome's authority came from "
        "Peter and was not subject to imperial approval."
    ),

    # ── Boniface (id=38) ─────────────────────────────────────────────────────
    38: (
        "Boniface (c. 672–754), the 'Apostle of Germany,' was an Anglo-Saxon "
        "monk from Wessex who became the most important missionary of the early "
        "Middle Ages. Leaving his comfortable English monastery for the forests "
        "of Germania, Boniface spent decades converting the pagan peoples of "
        "Hesse, Thuringia, and Bavaria, founding monasteries and bishoprics, "
        "reforming the Frankish church, and organizing the ecclesiastical "
        "structure that would underpin the Carolingian Empire. He was martyred "
        "by pagan Frisians in 754.\n\n"
        "His surviving correspondence — 42 letters in this collection, both sent "
        "and received — is remarkable for its emotional range and historical "
        "importance. He writes to popes seeking authorization and guidance, to "
        "friends in England begging for books and support, and to the Frankish "
        "mayors of the palace negotiating the political dimensions of his mission. "
        "The letters from his English correspondents — fellow monks and nuns who "
        "sent him books, vestments, and prayers — are some of the most touching "
        "documents to survive from the early Middle Ages.\n\n"
        "Boniface's letters matter because they document the creation of Christian "
        "Europe in real time. They show us the frontline of conversion — the "
        "practical challenges of building churches in hostile territory, training "
        "clergy who could barely read, and mediating between Roman ecclesiastical "
        "tradition and the realities of life in eighth-century Germania. His "
        "voice is earnest, devout, and occasionally homesick — a man who gave "
        "up everything for a mission he believed was divinely ordained and never "
        "looked back."
    ),

    # ── Ambrose of Milan (id=1) ──────────────────────────────────────────────
    1: (
        "Ambrose of Milan (c. 340–397) was the bishop who taught the Roman "
        "Empire that the church could say no to emperors. A provincial governor "
        "who was elected bishop by popular acclamation before he was even "
        "baptized, Ambrose combined the administrative instincts of a Roman "
        "official with the moral authority of a Christian pastor to become the "
        "most politically powerful churchman of the fourth century. His "
        "confrontation with Emperor Theodosius I after the massacre at "
        "Thessalonica — forcing the emperor to do public penance — established "
        "a precedent that would echo through Western history.\n\n"
        "His surviving letters — just 13 in this collection, though more exist "
        "in the broader corpus — cover church governance, doctrinal disputes, "
        "and the relationship between church and state. They reveal a man of "
        "immense moral certainty and considerable political skill, equally "
        "comfortable writing a theological treatise and managing a confrontation "
        "with imperial power. His most famous letter to his sister Marcellina "
        "describes his discovery of the relics of Saints Gervasius and "
        "Protasius — a masterpiece of pastoral drama.\n\n"
        "Ambrose matters because he defined the role of the Western bishop as an "
        "independent moral authority. His letters show us a man who genuinely "
        "believed that a bishop's duty was to speak truth to power, regardless "
        "of the political consequences — and who had the courage and the skill "
        "to back that belief up. His voice is confident, authoritative, and "
        "occasionally magnificent: the voice of a man who knew he was shaping "
        "the future."
    ),

    # ── Libanius (id=366) ─────────────────────────────────────────────────────
    366: (
        "Libanius (c. 314–393) was the most famous Greek rhetorician of the "
        "fourth century and one of the last great voices of classical pagan "
        "culture. Based in Antioch, he ran the most prestigious school of "
        "rhetoric in the Eastern empire, training a generation of leaders that "
        "included, remarkably, both the pagan emperor Julian and the Christian "
        "theologians Basil of Caesarea, Gregory of Nazianzus, and John "
        "Chrysostom. He was a living link between the classical and Christian "
        "worlds — a devoted pagan who counted Christians among his closest "
        "friends and students.\n\n"
        "His letters in this collection — 29 between sent and received — "
        "represent only a fraction of his enormous correspondence (over 1,500 "
        "letters survive in the full corpus). They reveal an intellectually "
        "engaged, socially connected figure who used letters to maintain a vast "
        "network of former students, fellow rhetoricians, and government "
        "officials. His exchanges with Basil are particularly valuable as one "
        "of the few sustained dialogues between a pagan intellectual and a "
        "Christian bishop.\n\n"
        "Libanius is historically significant because he shows us the world that "
        "Christianity was replacing — not a decadent paganism in decline but a "
        "vital intellectual tradition with its own values, its own sense of "
        "purpose, and its own understanding of what civilization meant. His "
        "voice is that of a cultivated, slightly self-important professor who "
        "genuinely believed that good Greek prose was the highest achievement "
        "of human civilization. He was wrong about the direction of history, "
        "but his letters make you understand why he thought what he did."
    ),

    # ── Innocent I (id=374) ──────────────────────────────────────────────────
    374: (
        "Pope Innocent I (c. 370–417) served as bishop of Rome during one of "
        "the most traumatic moments in Roman history — the sack of Rome by "
        "Alaric's Visigoths in 410. He was away from the city at the time, on a "
        "diplomatic mission to the imperial court in Ravenna, and his letters "
        "from this period reflect a pope trying to maintain church order while "
        "the political world collapsed around him. His pontificate (401–417) saw "
        "him assert Roman primacy with increasing confidence, building on the "
        "claims of his predecessors.\n\n"
        "His surviving letters — 34 in this collection — are predominantly "
        "concerned with church discipline and jurisdictional authority. He "
        "responded to queries from bishops across the Western empire on matters "
        "of liturgy, clerical conduct, and the treatment of heretics, and his "
        "responses became important precedents in canon law. He also intervened "
        "in the Eastern church's treatment of John Chrysostom and maintained "
        "correspondence with Augustine's circle in North Africa on the Pelagian "
        "controversy.\n\n"
        "Innocent's letters are significant because they show the papacy "
        "consolidating its authority at precisely the moment when every other "
        "Western institution was weakening. His voice is calm and juridical, that "
        "of a churchman who believed that Roman order, at least in ecclesiastical "
        "matters, could survive the fall of Roman power."
    ),

    # ── Pope Simplicius (id=375) ──────────────────────────────────────────────
    375: (
        "Pope Simplicius (c. 420–483) was bishop of Rome from 468 to 483, a "
        "period that saw the final collapse of the Western Roman Empire in 476 "
        "and the beginning of the Acacian Schism with Constantinople. His "
        "pontificate was defined by two challenges: managing the church in a Rome "
        "now governed by barbarian kings, and responding to the emperor Zeno's "
        "Henotikon — a theological compromise document designed to paper over the "
        "divisions caused by the Council of Chalcedon.\n\n"
        "His surviving letters — 31 in this collection — document a pope trying "
        "to hold the line on Chalcedonian orthodoxy while the political ground "
        "shifted beneath him. He wrote to Eastern bishops and patriarchs, "
        "protesting the elevation of theologians he considered compromised and "
        "defending the authority of Chalcedon against imperial attempts at "
        "doctrinal compromise.\n\n"
        "Simplicius's letters matter because they capture the papacy at its "
        "most vulnerable — the Western empire gone, the Eastern empire asserting "
        "theological control, and the bishop of Rome dependent on his moral "
        "authority alone. His voice is firm but anxious, that of a man who "
        "understood that the church's independence depended on not bending."
    ),

    # ── Paulinus of Nola (mentioned in CLAUDE.md, letters exist) ─────────────
    # Check if Paulinus has an author entry
    # He's not in the 5+ list, so skip unless we find him

    # ── Marcella (id=64) ─────────────────────────────────────────────────────
    64: (
        "Marcella (c. 325–410) was a Roman noblewoman who became one of the most "
        "important figures in the early Christian ascetic movement in Rome. "
        "Widowed young, she refused to remarry — reportedly turning down a "
        "proposal from a consul — and converted her palatial home on the Aventine "
        "Hill into what was effectively the first women's monastery in Rome. She "
        "studied Scripture with a seriousness that earned the respect of Jerome, "
        "who described her as his most intellectually demanding correspondent.\n\n"
        "All 18 of her appearances in this collection are as a recipient of "
        "Jerome's letters, but they reveal a remarkable woman. Jerome wrote to "
        "her about biblical interpretation, Hebrew linguistics, textual criticism, "
        "and theological controversies — not the pious generalities one might "
        "expect in letters to a 'lady,' but the kind of rigorous intellectual "
        "engagement you offer an equal. She challenged his translations, pressed "
        "him on difficult passages, and was reportedly the driving force behind "
        "his decision to write commentaries on several biblical books.\n\n"
        "Marcella matters because she represents the women who shaped early "
        "Christianity in ways the official record often obscures. She died in 410, "
        "shortly after being assaulted by Visigoths during the sack of Rome — "
        "a death that Jerome mourned bitterly. Her story, reconstructed from "
        "Jerome's letters, is a reminder that late antique intellectual life was "
        "not exclusively male, even if the surviving sources make it look that way."
    ),

    # ── Nebridius (id=21) ────────────────────────────────────────────────────
    21: (
        "Nebridius (d. c. 391) was one of Augustine's closest friends — a young "
        "North African intellectual who shared Augustine's philosophical passions "
        "and his restless search for truth. He appears in the Confessions as a "
        "member of the circle of friends who studied Manichaeism and Neoplatonism "
        "with Augustine in Carthage and Milan, and he died young, apparently "
        "shortly after converting to Christianity.\n\n"
        "All 16 of his appearances in this collection are as the recipient of "
        "Augustine's letters, and they are some of the most appealing documents "
        "in the entire corpus. These are letters between two young men who are "
        "genuinely excited by ideas — writing about the nature of memory, the "
        "problem of perception, the relationship between the soul and the body, "
        "with an enthusiasm that is infectious across sixteen centuries. Augustine "
        "addresses Nebridius as an intellectual equal and sometimes as a gentle "
        "critic who can catch his errors.\n\n"
        "Nebridius matters because the letters to him show us a side of Augustine "
        "that the later theological treatises mostly hide: the young philosopher, "
        "still genuinely uncertain, still open to being persuaded, writing to a "
        "friend he loves with a warmth that is palpable. They are among the "
        "earliest documents of what we would now call the examined life, and "
        "they remind us that the towering Bishop of Hippo was once just a "
        "brilliant young man with a brilliant young friend."
    ),

    # ── Januarius (id=34) ───────────────────────────────────────────────────
    34: (
        "Januarius (fl. 590s–600s) was the bishop of Cagliari in Sardinia and "
        "one of Pope Gregory the Great's most exasperating correspondents. He "
        "appears 25 times in this collection, always on the receiving end of "
        "Gregory's letters — and those letters paint a picture of a bishop who "
        "was either stubbornly independent or incompetent, depending on your "
        "perspective.\n\n"
        "Gregory wrote to Januarius about everything from the management of "
        "church property to the treatment of Jews in Sardinia to the proper "
        "conduct of episcopal courts, and the tone ranges from patient "
        "instruction to barely concealed frustration. Several letters address "
        "complaints about Januarius from his own clergy and parishioners, and "
        "Gregory's responses suggest a bishop who needed constant supervision.\n\n"
        "Januarius matters not for who he was but for what his letters reveal "
        "about papal administration under Gregory. The correspondence shows us "
        "how a pope actually governed the church on a day-to-day basis — through "
        "letters that combined moral authority with detailed practical "
        "instructions, and through the sheer persistence of writing the same "
        "bishop yet another letter about the same problem."
    ),

    # ── Amphilochius of Iconium (id=330) ──────────────────────────────────────
    330: (
        "Amphilochius of Iconium (c. 340–c. 403) was a cousin of Gregory of "
        "Nazianzus and a close ally of Basil of Caesarea in the fight against "
        "Arianism in Asia Minor. A lawyer turned bishop, he served as bishop of "
        "Iconium from about 373 and became one of the most effective "
        "anti-Arian voices in the Eastern church. His theological work on the "
        "divinity of the Holy Spirit was particularly important.\n\n"
        "He appears 15 times in this collection, primarily as a recipient of "
        "Basil's letters on canonical and theological questions. Basil clearly "
        "regarded him as a trusted colleague and wrote to him in detail about "
        "church discipline, the proper form of doxologies, and the ongoing "
        "struggle against various heretical groups. Their correspondence reveals "
        "the practical work of building theological consensus in the Eastern "
        "church — letter by careful letter.\n\n"
        "Amphilochius matters as a reminder that the great theological "
        "achievements of the fourth century were not the work of a few "
        "towering individuals alone. They required a network of committed, "
        "capable bishops working together across provincial boundaries — and "
        "Amphilochius was one of the most important members of that network."
    ),

    # ── John of Jerusalem (id=103) ───────────────────────────────────────────
    103: (
        "The 'John of Jerusalem' who appears 33 times in this collection as a "
        "recipient of Gregory the Great's letters is not the fifth-century "
        "bishop of Jerusalem involved in the Origenist controversy, but rather "
        "a late sixth-century bishop — most likely John IV of Jerusalem, who "
        "served during Gregory's pontificate (590–604).\n\n"
        "Gregory's letters to this John cover a range of administrative and "
        "pastoral matters relating to the churches of the Holy Land: property "
        "disputes, the management of monasteries, and the care of pilgrims. "
        "The volume of correspondence suggests that Gregory took a particularly "
        "active interest in Jerusalem, which is unsurprising given the city's "
        "symbolic importance and the practical challenges of maintaining Latin "
        "ecclesiastical interests in a Greek-speaking Eastern diocese.\n\n"
        "These letters reveal the long arm of papal administration reaching "
        "across the Mediterranean, and they document the practical concerns — "
        "money, property, jurisdiction — that underlay the spiritual prestige "
        "of the Holy City."
    ),

    # ── Eusebius, Archbishop of Thessalonica (id=226) ────────────────────────
    226: (
        "Eusebius of Thessalonica (fl. 360s–370s) was an important ecclesiastical "
        "ally of Basil of Caesarea during the Arian crisis that dominated the "
        "Eastern church in the fourth century. As archbishop of one of the most "
        "important sees in the Balkans, Eusebius was strategically positioned "
        "between the pro-Nicene West and the fractured East.\n\n"
        "He appears 32 times in this collection, always as a recipient of Basil's "
        "letters. Basil wrote to him extensively about the theological politics "
        "of the Eastern church, seeking support for the Nicene cause and keeping "
        "him informed about developments in Cappadocia, Antioch, and "
        "Constantinople. The correspondence reveals how anti-Arian bishops built "
        "and maintained their coalition through constant communication.\n\n"
        "Eusebius of Thessalonica matters as a window into the mechanics of "
        "fourth-century church politics — the network of alliances, the exchange "
        "of intelligence, and the patient diplomatic work that eventually led "
        "to the triumph of Nicene orthodoxy at the Council of Constantinople "
        "in 381."
    ),

    # ── Brunichild (id=171) ──────────────────────────────────────────────────
    171: (
        "Brunhild (c. 543–613) was queen of the Merovingian kingdom of Austrasia "
        "and one of the most powerful women in early medieval Europe. A Visigothic "
        "princess who married the Frankish king Sigebert I, she survived her "
        "husband's assassination and spent decades as regent and power behind "
        "the throne, waging a legendary feud with her sister-in-law Fredegund "
        "that became one of the defining dramas of Merovingian history. She was "
        "eventually executed in 613 at the age of about 70, tortured and dragged "
        "to death by a horse on the orders of her great-nephew Chlothar II.\n\n"
        "Her 10 appearances in this collection are as a recipient of Pope Gregory "
        "the Great's letters, and they reveal a diplomatic relationship of "
        "considerable importance. Gregory wrote to Brunhild about church reform "
        "in Gaul, the mission to England (which required Frankish cooperation), "
        "and various ecclesiastical appointments. His tone is respectful and "
        "politically astute — this was a woman whose support he needed.\n\n"
        "Brunhild's letters matter because they show us the intersection of "
        "papal diplomacy and Merovingian politics, and because they remind us "
        "that women wielded real power in the early medieval world — power that "
        "even popes had to acknowledge and cultivate."
    ),

    # ── Maximus of Madaura (id=23) ───────────────────────────────────────────
    23: (
        "Maximus of Madaura (fl. 390s) was a pagan grammarian in the small North "
        "African town of Madaura — the same town where Augustine had studied as "
        "a boy. He appears 10 times in this collection as a recipient of "
        "Augustine's letters, and their exchange is one of the most illuminating "
        "dialogues between Christianity and paganism to survive from late "
        "antiquity.\n\n"
        "Maximus challenged Augustine's Christianity with wit and learning, "
        "defending traditional Roman religion and questioning Christian claims. "
        "Augustine's responses are vigorous but respectful — he clearly enjoyed "
        "the intellectual sparring, and the letters reveal that pagan-Christian "
        "relations in provincial North Africa could be more cordial and "
        "intellectually engaged than the polemical literature might suggest.\n\n"
        "Maximus matters as a representative of the educated paganism that "
        "persisted in the Roman provinces well after Christianity became the "
        "official religion — and as evidence that the transition from one world "
        "to another was, in many places, more conversation than conquest."
    ),

    # ── Theophilus (id=75) ───────────────────────────────────────────────────
    75: (
        "Theophilus (d. 412) was patriarch of Alexandria and one of the most "
        "controversial churchmen of the late fourth and early fifth centuries. He "
        "is best known for his ruthless suppression of paganism in Alexandria — "
        "including the destruction of the Serapeum in 391 — and for his role in "
        "the deposition of John Chrysostom at the Synod of the Oak in 403, an "
        "act of ecclesiastical power politics that shocked even those accustomed "
        "to rough church politics.\n\n"
        "He appears 8 times in this collection, primarily as a recipient of "
        "Jerome's letters. Jerome and Theophilus were allies in the Origenist "
        "controversy — both opposed the theology of Origen, and their "
        "correspondence reflects this shared cause as well as the broader "
        "ecclesiastical politics of the Eastern Mediterranean.\n\n"
        "Theophilus matters as a reminder that the early church was not always "
        "edifying — it was also a world of ambition, faction, and the ruthless "
        "exercise of institutional power. His career, glimpsed through these "
        "letters, shows the darker side of episcopal authority in late antiquity."
    ),

    # ── Damasus (id=62) ─────────────────────────────────────────────────────
    62: (
        "Pope Damasus I (c. 305–384) was the bishop of Rome who commissioned "
        "Jerome to produce the Vulgate translation of the Bible — arguably the "
        "single most consequential act of patronage in Western cultural history. "
        "His pontificate (366–384) was marked by the aggressive assertion of "
        "Roman primacy, the promotion of the cult of the martyrs through "
        "epigraphic poetry, and the violent circumstances of his election, which "
        "involved a pitched battle between his supporters and those of his rival "
        "Ursinus in which over 130 people were killed.\n\n"
        "He appears 6 times in this collection as a recipient of Jerome's "
        "letters. Jerome wrote to Damasus on biblical questions, scriptural "
        "interpretation, and theological controversies, and the relationship was "
        "crucial to both men: Damasus provided Jerome with papal backing and "
        "institutional support, while Jerome provided Damasus with scholarly "
        "prestige and the beginnings of the Vulgate.\n\n"
        "Damasus matters because the letters to him capture a pivotal moment in "
        "Western Christianity — the alliance between papal authority and biblical "
        "scholarship that would shape the intellectual culture of the medieval "
        "church for a millennium."
    ),

    # ── Pammachius (id=68) ──────────────────────────────────────────────────
    68: (
        "Pammachius (c. 340–410) was a Roman senator, one of Jerome's closest "
        "friends, and a remarkable figure in his own right — a member of the "
        "powerful gens Furia who combined an active public career with deep "
        "Christian commitment. After the death of his wife Paulina (daughter of "
        "the elder Paula, another member of Jerome's ascetic circle), Pammachius "
        "gave away much of his wealth to the poor and founded a hospice for "
        "pilgrims at Portus, the harbor of Rome.\n\n"
        "He appears 6 times in this collection as a recipient of Jerome's "
        "letters, and the correspondence reveals a friendship between a fiery "
        "scholar and a thoughtful aristocrat. Jerome wrote to Pammachius about "
        "theology, translation theory, and the controversies that perpetually "
        "swirled around him, and Pammachius served as Jerome's most trusted "
        "representative in Rome — managing his reputation, circulating his "
        "works, and occasionally trying to smooth over the damage caused by "
        "Jerome's polemical excesses.\n\n"
        "Pammachius matters as evidence of the Christian transformation of the "
        "Roman aristocracy — the remarkable phenomenon of senators and their "
        "families choosing asceticism, charity, and theological study over the "
        "traditional Roman cursus honorum."
    ),

    # ── Antoninus (id=26) ──────────────────────────────────────────────────
    26: (
        "Antoninus (fl. 400s–410s) was a bishop in North Africa and one of "
        "Augustine's correspondents on matters of church discipline and pastoral "
        "practice. He appears 9 times in this collection as a recipient of "
        "Augustine's letters.\n\n"
        "Augustine's letters to Antoninus deal with the practical challenges of "
        "running a North African diocese in the early fifth century — managing "
        "clerical disputes, handling questions of church discipline, and "
        "navigating the complex ecclesiastical politics of a region divided by "
        "the Donatist schism. They offer a ground-level view of the "
        "administrative work that consumed most of a bishop's time.\n\n"
        "Antoninus is significant as a representative of the ordinary bishops "
        "who formed the backbone of the African church — men whose names history "
        "barely remembers but who did the daily work of keeping a complex "
        "institution running in difficult times."
    ),

    # ── Aurelius (id=27) ────────────────────────────────────────────────────
    27: (
        "Aurelius (d. c. 430) was bishop of Carthage and the most powerful "
        "churchman in Roman North Africa during Augustine's lifetime. As primate "
        "of the African church, he presided over the councils that condemned "
        "Pelagianism and managed the final stages of the Donatist controversy. "
        "His partnership with Augustine was one of the most important "
        "collaborations in early church history.\n\n"
        "He appears 8 times in this collection as a recipient of Augustine's "
        "letters, and the correspondence reveals a working relationship between "
        "a brilliant theologian and a capable administrator. Augustine wrote to "
        "Aurelius about doctrinal matters, church councils, and the practical "
        "challenges of fighting the Donatist schism — and Aurelius, as primate, "
        "had the institutional authority to act on Augustine's theological "
        "arguments.\n\n"
        "Aurelius matters because he reminds us that Augustine did not operate "
        "alone. The theological revolution that Augustine led in North Africa "
        "required an institutional partner with the authority and political skill "
        "to translate ideas into action — and that partner was Aurelius of "
        "Carthage."
    ),

    # ── Eulogius of Alexandria (id=203) ──────────────────────────────────────
    203: (
        "Eulogius (d. 607/608) was patriarch of Alexandria and one of Pope "
        "Gregory the Great's most valued correspondents. Their exchange — "
        "Eulogius appears 9 times in this collection as a recipient of Gregory's "
        "letters — represents a warm and respectful dialogue between the two "
        "most important sees in Christendom that were still in communion with "
        "each other.\n\n"
        "Gregory wrote to Eulogius about theological questions, the Monophysite "
        "controversy in Egypt, the progress of the English mission, and the "
        "shared challenge of managing a church in a turbulent world. The tone is "
        "notably warmer than Gregory's administrative correspondence — these are "
        "letters between colleagues who genuinely liked and respected each other.\n\n"
        "The Gregory-Eulogius correspondence matters because it shows that the "
        "late sixth-century church, despite its divisions, was still capable of "
        "genuine intellectual and personal connection across vast distances — "
        "a reminder that the Mediterranean world, even in its fragmented state, "
        "remained a connected space."
    ),

    # ── Marinianus (id=170) ─────────────────────────────────────────────────
    170: (
        "Marinianus (fl. 590s–600s) was bishop of Ravenna, the seat of the "
        "imperial exarch in Italy, and one of Pope Gregory the Great's most "
        "important correspondents. His position in Ravenna — the administrative "
        "capital of Byzantine Italy — made him a crucial intermediary between "
        "papal and imperial authority.\n\n"
        "He appears 14 times in this collection as a recipient of Gregory's "
        "letters, which cover everything from the management of church property "
        "to the handling of liturgical disputes to the delicate politics of "
        "dealing with the exarch. Gregory's tone with Marinianus is collegial "
        "but directive — the letters of a pope who respected his bishop's "
        "position but expected his instructions to be followed.\n\n"
        "Marinianus matters because the letters to him document the relationship "
        "between Rome and Ravenna at a crucial moment — when the two cities "
        "represented different centers of authority in a fragmenting Italy, and "
        "when the bishop of Ravenna was beginning to assert the independent "
        "status that would eventually lead to the autocephaly of the Ravennate "
        "church."
    ),

    # ── Anastasius (id=41) ──────────────────────────────────────────────────
    41: (
        "The Anastasius who appears 16 times in this collection as a recipient "
        "of Augustine's letters was most likely Anastasius I, bishop of Rome from "
        "399 to 401. His brief pontificate was marked by the condemnation of "
        "Origen's writings, an intervention that Augustine supported and that "
        "reflected the increasing importance of Roman doctrinal authority in the "
        "Western church.\n\n"
        "Augustine wrote to Anastasius on matters of doctrine and church "
        "discipline, and the correspondence reveals the network of communication "
        "that connected the African and Roman churches at a time when both were "
        "navigating the aftermath of the Donatist crisis and the emerging "
        "Pelagian controversy.\n\n"
        "These letters matter as evidence of the Rome-Africa axis that was one "
        "of the most important relationships in the early Western church — a "
        "partnership that would shape the development of Latin theology for "
        "generations."
    ),

    # ── Romanus, Exarch (id=120) ────────────────────────────────────────────
    120: (
        "Romanus (d. 596/597) was the exarch of Italy — the emperor's "
        "representative in Ravenna and the highest civil and military authority "
        "in Byzantine Italy. He appears 12 times in this collection as a "
        "recipient of Pope Gregory the Great's letters, and the correspondence "
        "reveals a relationship that was often tense.\n\n"
        "Gregory and Romanus clashed repeatedly over the handling of the Lombard "
        "threat. Gregory, who dealt with the Lombards face-to-face in Rome, "
        "favored negotiation and peace; Romanus, representing imperial policy, "
        "pursued a harder line that Gregory saw as reckless and ineffective. "
        "Their exchanges are some of the sharpest in Gregory's entire corpus.\n\n"
        "The letters to Romanus matter because they reveal the tensions at the "
        "heart of Byzantine Italy — a pope who was becoming the de facto leader "
        "of Rome and an imperial official who resented it. The conflict between "
        "Gregory and the exarch foreshadowed the eventual break between Rome "
        "and Constantinople."
    ),

    # ── Peter of Terracina (id=122) ─────────────────────────────────────────
    122: (
        "Peter of Terracina (fl. 590s) was a subdeacon or minor official in the "
        "coastal town of Terracina, south of Rome, and the recipient of 12 "
        "letters from Pope Gregory the Great. The frequency of Gregory's letters "
        "to this otherwise obscure figure reflects the pope's hands-on management "
        "of the papal patrimony — the vast network of estates that provided "
        "Rome's food supply.\n\n"
        "Gregory's letters to Peter deal primarily with estate management, "
        "property disputes, and the welfare of tenants on papal lands. They are "
        "the unglamorous but essential business of keeping Rome fed and the "
        "church solvent.\n\n"
        "Peter of Terracina matters not as an individual but as evidence of "
        "Gregory's extraordinary administrative reach. These letters show a pope "
        "who personally supervised the management of estates down to the level "
        "of individual tenants — a commitment to good governance that was as "
        "much a part of Gregory's sanctity as his theology."
    ),

    # ── Anatolius of Constantinople (id=216) ────────────────────────────────
    216: (
        "Anatolius (d. 458) was patriarch of Constantinople from 449 to 458 and "
        "a central figure in the Christological controversies that defined the "
        "fifth-century church. Originally a deacon under the controversial "
        "patriarch Dioscorus of Alexandria, Anatolius shifted his allegiance to "
        "accept Pope Leo's Tome and the Chalcedonian definition — a pragmatic "
        "move that Leo never fully trusted.\n\n"
        "He appears 12 times in this collection as a recipient of Leo's letters, "
        "and the correspondence reveals a pope who was simultaneously relieved "
        "to have Constantinople's support and suspicious of Anatolius's motives. "
        "Leo wrote to Anatolius about doctrinal compliance, jurisdictional "
        "disputes (particularly Canon 28 of Chalcedon, which elevated "
        "Constantinople's status), and the ongoing implementation of the "
        "Chalcedonian settlement.\n\n"
        "The Leo-Anatolius correspondence matters because it documents the "
        "emerging rivalry between Rome and Constantinople — two sees that needed "
        "each other but could not agree on their relative status. The tensions "
        "visible in these letters would, over the centuries, contribute to the "
        "Great Schism of 1054."
    ),

    # ── Julian of Antioch (id=53) ──────────────────────────────────────────
    53: (
        "Julian of Antioch (fl. 440s–450s) was a bishop who served as one of "
        "Pope Leo the Great's key correspondents in the Eastern church during "
        "the aftermath of the Council of Chalcedon. He appears 23 times in this "
        "collection as a recipient of Leo's letters.\n\n"
        "Leo wrote to Julian about the implementation of Chalcedonian orthodoxy, "
        "the management of Eastern bishops who remained sympathetic to "
        "Monophysitism, and the broader ecclesiastical politics of the Eastern "
        "empire. Julian appears to have served as a reliable channel for Roman "
        "influence in a region where direct papal authority was limited.\n\n"
        "Julian matters as evidence of the network of episcopal allies through "
        "which Rome projected its authority into the East — a network that "
        "required constant maintenance through exactly the kind of correspondence "
        "preserved in these letters."
    ),

    # ── Athanasius, Presbyter (id=189) ──────────────────────────────────────
    189: (
        "The Athanasius who appears 20 times in this collection as a recipient "
        "of Basil of Caesarea's letters was a presbyter — not the famous "
        "Athanasius of Alexandria, but a trusted subordinate and correspondent "
        "who served as one of Basil's key contacts during the Arian controversy.\n\n"
        "Basil's letters to this Athanasius cover ecclesiastical politics, "
        "theological questions, and the practical management of the pro-Nicene "
        "coalition in the East. They reveal the layer of communication beneath "
        "the famous exchanges between bishops — the network of priests, deacons, "
        "and minor officials who kept the ecclesiastical machinery running.\n\n"
        "This Athanasius matters as a reminder that the great theological "
        "controversies of the fourth century were not just debates between "
        "titans — they were sustained by a much larger network of committed "
        "individuals whose names we barely know."
    ),

    # ── Bacauda and Agnellus (id=113) ───────────────────────────────────────
    113: (
        "Bacauda and Agnellus were bishops who appear 14 times in this collection "
        "in connection with Gregory the Great's correspondence. They were among "
        "the many provincial bishops who wrote to Gregory seeking guidance on "
        "matters of church discipline, liturgy, and administration.\n\n"
        "Gregory's letters to them deal with the practical governance of their "
        "dioceses — the kind of routine but essential business that filled "
        "most of a medieval pope's correspondence. They represent the broader "
        "network of bishops who looked to Rome for leadership and whose "
        "compliance with papal directives was never guaranteed.\n\n"
        "These correspondents matter as evidence of the reach and limits of "
        "papal authority — the constant negotiation between Roman ambition and "
        "local reality that defined the early medieval church."
    ),

    # ── Meletius of Antioch (id=284) ─────────────────────────────────────────
    284: (
        "Meletius of Antioch (d. 381) was one of the most important — and most "
        "complicated — figures in the ecclesiastical politics of the fourth "
        "century. His contested election as bishop of Antioch created a schism "
        "that lasted decades and complicated the anti-Arian cause even among "
        "those who agreed on theology. He died during the Council of "
        "Constantinople in 381, where he had been presiding.\n\n"
        "He appears 7 times in this collection as a recipient of Basil's letters. "
        "Basil was a devoted supporter of Meletius and wrote to him about the "
        "political situation in the Eastern church, the need for Western support, "
        "and the challenge of maintaining Nicene orthodoxy against both Arian "
        "imperialism and the rival Nicene faction of Paulinus in Antioch.\n\n"
        "Meletius matters because the Antiochene schism was one of the most "
        "damaging divisions within the pro-Nicene camp, and Basil's letters to "
        "him document the frustration and determination of those trying to hold "
        "the orthodox coalition together despite internal divisions."
    ),

    # ── Constantius (id=155) ────────────────────────────────────────────────
    155: (
        "Constantius (fl. 590s–600s) was a bishop who appears 7 times in this "
        "collection as a recipient of Pope Gregory the Great's letters. Gregory "
        "wrote to him about diocesan administration, church discipline, and the "
        "management of clerical disputes.\n\n"
        "The letters to Constantius typify the vast body of Gregory's routine "
        "administrative correspondence — individually unremarkable, but "
        "collectively evidence of a pope who took direct pastoral responsibility "
        "for bishops across the Western church and expected his guidance to be "
        "followed.\n\n"
        "Constantius is one of many provincial bishops whose correspondence with "
        "Gregory reveals the texture of everyday church governance in the early "
        "medieval period."
    ),

    # ── Syagrius (id=218) ─────────────────────────────────────────────────
    218: (
        "Syagrius (fl. 590s) was bishop of Autun in Gaul and appears 7 times in "
        "this collection as a recipient of Pope Gregory the Great's letters. "
        "Gregory's correspondence with Syagrius dealt with church reform in Gaul, "
        "the suppression of simony, and Gregory's broader agenda of bringing the "
        "Frankish church under closer Roman oversight.\n\n"
        "The letters to Syagrius are significant because they document Gregory's "
        "efforts to reform the Merovingian church — a project that required "
        "working through sympathetic local bishops who could navigate the "
        "complicated politics of Frankish Gaul. Syagrius appears to have been "
        "one of Gregory's most cooperative contacts in the region.\n\n"
        "These letters reveal the long reach of Gregory's reform program and the "
        "practical challenges of exercising papal authority in territories "
        "governed by Germanic kings."
    ),

    # ── Sabinianus (id=107) ────────────────────────────────────────────────
    107: (
        "Sabinianus (fl. 590s) served as Gregory the Great's apocrisiarius "
        "(ambassador) in Constantinople before succeeding Gregory as pope in 604. "
        "He appears 7 times in this collection as a recipient of Gregory's "
        "letters, and the correspondence reveals the critical role of the papal "
        "representative at the imperial court.\n\n"
        "Gregory wrote to Sabinianus about diplomatic negotiations with the "
        "emperor, ecclesiastical disputes in the East, and the practical "
        "challenges of representing Roman interests in Constantinople. The "
        "letters suggest a relationship that was professional rather than warm.\n\n"
        "Sabinianus matters because the letters to him document how the papacy "
        "conducted its most important diplomatic relationship — and because his "
        "own brief pontificate (604–606) would be marked by open hostility to "
        "Gregory's legacy, making their earlier correspondence a study in the "
        "tensions that could simmer beneath official communication."
    ),

    # ── Florentius (id=52) ──────────────────────────────────────────────────
    52: (
        "Florentius appears 5 times in this collection as a correspondent in "
        "the late Roman letter network. Whether a bishop, official, or "
        "aristocrat, his repeated appearance in the correspondence of major "
        "figures suggests a person of some standing in the ecclesiastical or "
        "secular hierarchy of the late empire.\n\n"
        "The letters involving Florentius contribute to our understanding of "
        "the broader social networks that sustained late Roman communication — "
        "the web of relationships that kept information, influence, and favors "
        "flowing across the Mediterranean world."
    ),

    # ── Olympius (id=263) ──────────────────────────────────────────────────
    263: (
        "Olympius appears 6 times in this collection as a correspondent of "
        "Basil of Caesarea. Basil's letters to various officials and friends "
        "named Olympius — likely a provincial governor or other important figure "
        "in Cappadocia — reveal the bishop's constant engagement with secular "
        "authorities on behalf of his diocese and his flock.\n\n"
        "The letters to Olympius illustrate Basil's diplomatic skill in dealing "
        "with the secular power — requesting tax relief for his province, "
        "interceding for individuals, and maintaining the kind of relationships "
        "that allowed a bishop to get things done in a world where the church "
        "still depended heavily on imperial cooperation."
    ),

    # ── Modestus (id=302) ─────────────────────────────────────────────────
    302: (
        "Modestus (fl. 360s–370s) was likely the comes Orientis or a similar "
        "high official in the Eastern empire who appears 6 times in this "
        "collection in connection with Basil of Caesarea's correspondence. In "
        "one famous encounter, the emperor Valens sent Modestus to pressure "
        "Basil into accepting Arianism; Basil's defiant response became one of "
        "the most celebrated stories of episcopal courage in church history.\n\n"
        "The letters involving Modestus show the intersection of ecclesiastical "
        "and imperial authority in the fourth-century East — and the remarkable "
        "fact that a bishop could face down an imperial official and survive."
    ),

    # ── Church of Neocaesarea (id=271) ──────────────────────────────────────
    271: (
        "The church of Neocaesarea in Pontus appears 6 times in this collection "
        "as a recipient of Basil of Caesarea's letters. Basil had a complicated "
        "relationship with this church — it had been founded by Gregory "
        "Thaumaturgus, a hero of Basil's family, but its clergy were suspicious "
        "of Basil's theological innovations, particularly his emphasis on the "
        "distinct personhood of the Holy Spirit.\n\n"
        "Basil's letters to Neocaesarea are pastoral and apologetic, trying to "
        "reassure a conservative community that his theology was faithful to "
        "their shared tradition. They reveal the local resistance that even the "
        "most powerful bishops could face when pushing theological development."
    ),

    # ── Sophronius (id=272) ─────────────────────────────────────────────────
    272: (
        "Sophronius, referred to as 'Sophronius Master' in this collection, "
        "appears 6 times as a recipient of Basil of Caesarea's letters. He was "
        "likely a magister officiorum or other high-ranking official in the "
        "Eastern imperial administration.\n\n"
        "Basil wrote to Sophronius on matters requiring imperial intervention — "
        "tax relief for Cappadocia, legal cases involving clergy, and the "
        "practical needs of his diocese. The letters reveal the constant "
        "negotiation between episcopal and imperial authority that characterized "
        "the fourth-century Eastern church."
    ),

    # ── Aburgius (id=273) ──────────────────────────────────────────────────
    273: (
        "Aburgius appears 5 times in this collection as a recipient of Basil of "
        "Caesarea's letters. He was likely a government official or local notable "
        "in Cappadocia.\n\n"
        "Basil's letters to Aburgius deal with intercessions on behalf of "
        "individuals and requests for civic assistance — the kind of patron-client "
        "correspondence that reveals how bishops functioned as community advocates "
        "in the late Roman world."
    ),

    # ── Gregory, uncle (id=285) ────────────────────────────────────────────
    285: (
        "Gregory, referred to as 'uncle' in Basil's letters, appears 5 times in "
        "this collection as a recipient of letters from Basil of Caesarea. He "
        "was a bishop and family member — likely Gregory, bishop of an unknown "
        "see in Cappadocia — and the letters reveal the family networks that "
        "were central to Cappadocian Christianity.\n\n"
        "Basil's letters to his uncle combine family affection with ecclesiastical "
        "business, showing how the personal and the institutional were "
        "inseparable in the fourth-century church."
    ),

    # ── Eustathius Philosopher (id=261) ────────────────────────────────────
    261: (
        "Eustathius the Philosopher appears 5 times in this collection as a "
        "recipient of Basil of Caesarea's letters. He was a physician and "
        "intellectual — one of the educated professionals with whom Basil "
        "maintained friendships outside the clerical hierarchy.\n\n"
        "Basil's letters to Eustathius reveal his intellectual breadth and his "
        "ability to engage with correspondents on terms that were not exclusively "
        "theological — a reminder that even the most committed churchmen of the "
        "fourth century lived in a world that still valued secular learning."
    ),

    # ── Additional minor figures that meet the 5+ threshold ──────────────────

    # Caesarius, brother of Gregory (id=270)
    270: (
        "Caesarius (c. 330–369) was the younger brother of Gregory of Nazianzus "
        "and a physician who served at the imperial court in Constantinople. He "
        "appears 9 times in this collection as a recipient of letters from Basil "
        "of Caesarea, reflecting the close family connections between the "
        "Cappadocian Fathers.\n\n"
        "Caesarius's career as a court physician placed him at the intersection "
        "of secular and Christian worlds, and his correspondence with Basil "
        "reveals the social networks that linked Cappadocian Christians in the "
        "capital and the provinces."
    ),

    # Carthaginian Clergy (id=386)
    386: (
        "The clergy of Carthage appear 9 times in this collection as collective "
        "recipients of Cyprian's letters during the Decian persecution of "
        "250–251. Cyprian wrote to them from hiding, issuing instructions for "
        "the management of the church in his absence and trying to maintain "
        "discipline during a crisis that tested every institution.\n\n"
        "These letters are among the most important documents for understanding "
        "how the early church functioned under persecution — the practical "
        "challenges of leadership in absentia, the management of church finances, "
        "and the agonizing decisions about who could be readmitted after lapsing."
    ),

    # Cornelius (id=389)
    389: (
        "Pope Cornelius (d. 253) served as bishop of Rome from 251 to 253 and "
        "was one of Cyprian of Carthage's most important allies. He appears 5 "
        "times in this collection as a recipient of Cyprian's letters, and their "
        "correspondence documents the joint response of Rome and Carthage to the "
        "Novatianist schism — the rigorist movement that refused to readmit "
        "Christians who had lapsed during the Decian persecution.\n\n"
        "The Cyprian-Cornelius correspondence matters because it shows the "
        "early church working out, in real time, the principles of forgiveness "
        "and church unity that would define Christian ecclesiology for centuries. "
        "It also documents one of the earliest examples of effective cooperation "
        "between the Roman and African churches."
    ),

    # Anthemius (id=123)
    123: (
        "Anthemius (fl. 590s–600s) was a subdeacon or administrator who appears "
        "8 times in this collection as a recipient of Pope Gregory the Great's "
        "letters. Gregory wrote to him about the management of papal properties "
        "and administrative matters — the practical business of running the "
        "papal estates that sustained Rome's population.\n\n"
        "The letters to Anthemius typify Gregory's hands-on management style "
        "and his insistence on personal oversight of the church's material "
        "resources."
    ),

    # Virgil (id=125)
    125: (
        "Virgil (fl. 590s–600s) was bishop of Arles and appears 8 times in "
        "this collection as a recipient of Pope Gregory the Great's letters. "
        "As bishop of Arles, Virgil held the papal vicariate for Gaul — making "
        "him Rome's official representative in the Frankish kingdoms.\n\n"
        "Gregory's letters to Virgil deal with church reform in Gaul, the "
        "organization of the mission to England (which passed through Frankish "
        "territory), and the management of ecclesiastical discipline in a region "
        "where Roman authority was more aspirational than real. They reveal the "
        "mechanics of papal influence in a world where distance and political "
        "fragmentation made direct control impossible."
    ),

    # Mauricius Augustus (id=153)
    153: (
        "Emperor Maurice (539–602) ruled the Byzantine Empire from 582 to 602 "
        "and was one of Pope Gregory the Great's most important — and most "
        "difficult — correspondents. He appears 8 times in this collection "
        "as a recipient of Gregory's letters.\n\n"
        "Gregory and Maurice clashed over the emperor's decree forbidding "
        "soldiers from becoming monks (which Gregory saw as an intolerable "
        "interference in spiritual matters) and over the handling of the "
        "Lombard threat in Italy. Yet Gregory also needed Maurice's support and "
        "wrote to him with the carefully calibrated respect that a pope owed "
        "an emperor — even when he disagreed with him.\n\n"
        "The Gregory-Maurice correspondence matters because it documents the "
        "most important power relationship in the late sixth-century "
        "Mediterranean — the tension between papal spiritual authority and "
        "imperial political power that would define the medieval relationship "
        "between church and state."
    ),

    # Cyprian (id=105) — likely a different Cyprian, recipient
    105: (
        "The Cyprian who appears 7 times in this collection as a recipient of "
        "letters is most likely a later figure sharing the famous name — "
        "possibly a deacon or minor cleric referenced in the correspondence of "
        "one of the major collections. The name Cyprian remained popular in "
        "North Africa and Italy for centuries after the martyrdom of the "
        "great bishop of Carthage.\n\n"
        "The letters to this Cyprian contribute to our understanding of the "
        "broader networks of communication that sustained the late antique "
        "and early medieval church."
    ),

    # Peter (id=112)
    112: (
        "Peter appears 6 times in this collection, likely as a cleric or "
        "administrator in the correspondence of one of the major authors. The "
        "name Peter was ubiquitous in early Christianity for obvious reasons, "
        "and multiple Peters appear across the letter collections.\n\n"
        "The letters to Peter are part of the vast body of routine "
        "ecclesiastical correspondence that reveals the day-to-day functioning "
        "of the late antique church."
    ),

    # Castorius of Ariminum (id=135)
    135: (
        "Castorius of Ariminum (fl. 590s) was a notary or other papal official "
        "who appears 6 times in this collection as a recipient of Pope Gregory "
        "the Great's letters. Gregory used him as an agent for handling "
        "ecclesiastical business in the Adriatic region.\n\n"
        "The letters to Castorius reveal Gregory's administrative network in "
        "action — the system of agents, notaries, and deputies through which a "
        "pope managed a church that spanned the Western Mediterranean."
    ),

    # Dominicus (id=141)
    141: (
        "Dominicus (fl. 590s–600s) was a bishop who appears 6 times in this "
        "collection as a recipient of Pope Gregory the Great's letters. Gregory "
        "wrote to him about diocesan administration and church discipline.\n\n"
        "The letters to Dominicus are part of Gregory's enormous administrative "
        "correspondence — the steady stream of directives, rebukes, and "
        "encouragements through which he managed the Western church."
    ),

    # People of Ravenna (id=165)
    165: (
        "The people of Ravenna appear 6 times in this collection as recipients "
        "of letters from various popes and church officials. Ravenna's status "
        "as the administrative capital of Byzantine Italy made its people — "
        "both clergy and laity — important figures in the ecclesiastical "
        "politics of the period.\n\n"
        "Letters addressed to the Ravennate community reveal the intersection "
        "of papal, imperial, and local interests in one of the most important "
        "cities of early medieval Italy."
    ),

    # Fortunatus (id=179)
    179: (
        "Fortunatus (fl. 590s–600s) was a bishop who appears 6 times in this "
        "collection as a recipient of Pope Gregory the Great's letters. Gregory "
        "wrote to him about church governance and the management of his diocese.\n\n"
        "The letters to Fortunatus are part of the remarkable documentary record "
        "of Gregory's pontificate — evidence of a pope who personally supervised "
        "bishops across the Western church with detailed attention to their "
        "individual situations."
    ),

    # Theodorus (id=33)
    33: (
        "Theodorus appears 5 times in this collection as a recipient of letters "
        "from major late antique correspondents. The name was extremely common in "
        "the late Roman world, and multiple Theodori appear across the letter "
        "collections.\n\n"
        "The letters to Theodorus contribute to the broader picture of late "
        "antique communication networks — the constant flow of letters that "
        "held together a world without telephones, newspapers, or reliable "
        "postal services."
    ),

    # Alypius and Augustine (id=45)
    45: (
        "Alypius (c. 354–c. 430) was Augustine's closest friend from childhood — "
        "they grew up together in Thagaste, studied together in Carthage, and "
        "converted together in Milan. Alypius became bishop of Thagaste and "
        "served as Augustine's most trusted collaborator in North African church "
        "affairs. He appears 12 times in this collection, usually in joint "
        "address with Augustine.\n\n"
        "The letters addressed jointly to 'Alypius and Augustine' deal with "
        "major theological and ecclesiastical matters — the Pelagian controversy, "
        "church councils, and appeals to Rome. They reveal the partnership at "
        "the heart of the North African church: Augustine the theologian and "
        "Alypius the diplomat and administrator, working in tandem."
    ),

    # Pulcheria Augusta — not in the 5+ list but let's check
    # Unknown Noble (id=35)
    35: (
        "The figure identified as 'Unknown Noble' appears 11 times in this "
        "collection as a recipient of letters from various authors. In many "
        "cases, late antique letters survive without clear identification of "
        "the recipient, or the addressee was deliberately obscured.\n\n"
        "These unidentified correspondents are a reminder of the fragmentary "
        "nature of our evidence — we have the letters, but not always the full "
        "context of the relationships they document."
    ),

    # Unknown Son (id=46)
    46: (
        "The 'Unknown Son' who appears 5 times as a recipient reflects the "
        "intimate register of late antique letter writing. Bishops frequently "
        "addressed younger clergy, protégés, and spiritual dependents as 'son' "
        "— a term of pastoral affection that could mask a wide range of actual "
        "relationships.\n\n"
        "These letters contribute to our understanding of the hierarchical "
        "but often genuinely warm relationships that structured the late "
        "antique church."
    ),

    # Chromatius, Jovinus, and Eusebius (id=54)
    54: (
        "Chromatius, Jovinus, and Eusebius appear 5 times in this collection as "
        "joint recipients of Jerome's letters. Chromatius was bishop of Aquileia, "
        "one of the most important sees in northern Italy, and a patron of "
        "Jerome's biblical scholarship. Jovinus and Eusebius were likely "
        "associated clergy.\n\n"
        "Jerome's letters to this group deal with scriptural questions and "
        "the practical support of his translation work. They reveal the network "
        "of episcopal patrons who funded and encouraged Jerome's extraordinary "
        "scholarly output."
    ),

    # Natalis of Salona (id=116)
    116: (
        "Natalis of Salona (fl. 590s–600s) was bishop of Salona (modern Split, "
        "Croatia) and appears 5 times in this collection as a recipient of Pope "
        "Gregory the Great's letters. Gregory's correspondence with Natalis deals "
        "with church discipline and the management of the Dalmatian church.\n\n"
        "The letters reveal Gregory's active supervision of churches in the "
        "Balkans — a region caught between Byzantine authority, Slavic migration, "
        "and the remnants of Roman provincial organization."
    ),

    # Venantius of Syracuse (id=121)
    121: (
        "Venantius of Syracuse (fl. 590s) appears 5 times in this collection as "
        "a recipient of Pope Gregory the Great's letters. Gregory corresponded "
        "with him about the management of the church in Sicily — an island of "
        "particular importance to the papacy because of the vast papal estates "
        "there that helped feed Rome.\n\n"
        "The letters to Venantius are part of Gregory's extensive Sicilian "
        "correspondence and reveal the close attention he paid to the island's "
        "ecclesiastical affairs."
    ),

    # Gennadius (id=127)
    127: (
        "Gennadius (d. 598) was the patrician and exarch of Africa — the "
        "Byzantine governor of North Africa — and appears 5 times in this "
        "collection as a recipient of Pope Gregory the Great's letters. "
        "Gregory's correspondence with Gennadius deals with the intersection "
        "of civil and ecclesiastical authority in Africa.\n\n"
        "The letters reveal the complex relationship between papal authority "
        "and imperial administration in a province that was culturally Latin "
        "but politically Byzantine."
    ),

    # Leo in Corsica (id=129)
    129: (
        "Leo of Corsica (fl. 590s–600s) was a bishop who appears 5 times in "
        "this collection as a recipient of Pope Gregory the Great's letters. "
        "Gregory wrote to him about the management of his island diocese.\n\n"
        "The letters to Leo are part of Gregory's extensive correspondence "
        "with the churches of the Western Mediterranean islands — Corsica, "
        "Sardinia, and Sicily — which fell under close papal supervision."
    ),

    # Maximianus of Syracuse (id=133)
    133: (
        "Maximianus of Syracuse (d. 594) was one of Pope Gregory the Great's "
        "closest allies and appears 5 times in this collection as a recipient "
        "of Gregory's letters. A fellow monk from Gregory's own monastery on "
        "the Caelian Hill, Maximianus served as Gregory's papal legate to the "
        "East before becoming bishop of Syracuse.\n\n"
        "Gregory's letters to Maximianus are warmer than most of his "
        "administrative correspondence — the letters of a pope writing to a "
        "trusted friend as well as a subordinate. They reveal the personal "
        "relationships that underlay Gregory's administrative network."
    ),

    # Rusticiana (id=137)
    137: (
        "Rusticiana (fl. 590s–600s) was a Roman patrician woman — possibly a "
        "descendant of the great senatorial families — who lived in "
        "Constantinople and appears 5 times in this collection as a recipient "
        "of Pope Gregory the Great's letters. Gregory wrote to her about "
        "church matters and the welfare of Roman interests in the imperial "
        "capital.\n\n"
        "The letters to Rusticiana reveal that women of the Roman aristocracy "
        "remained significant figures in ecclesiastical affairs well into the "
        "sixth century — and that Gregory was pragmatic enough to cultivate "
        "every useful contact in Constantinople."
    ),

    # Columbus (id=142)
    142: (
        "Columbus (fl. 590s–600s) was a bishop who appears 5 times in this "
        "collection as a recipient of Pope Gregory the Great's letters. "
        "Gregory wrote to him about diocesan management and church discipline.\n\n"
        "The letters to Columbus are part of Gregory's vast administrative "
        "correspondence and reveal his hands-on approach to church governance."
    ),

    # Victor and Columbus, Bishops (id=164)
    164: (
        "Victor and Columbus were bishops who appear 5 times in this collection "
        "as joint recipients of letters from Pope Gregory the Great. Gregory "
        "occasionally wrote to pairs or groups of bishops on matters requiring "
        "coordinated action.\n\n"
        "The letters to these bishops reveal the collaborative structures of "
        "early medieval church governance — the expectation that neighboring "
        "bishops would work together under papal direction."
    ),

    # Eulogius and Anastasius, Bishops (id=167)
    167: (
        "Eulogius and Anastasius appear 5 times in this collection as joint "
        "recipients of letters from Pope Gregory the Great. These paired "
        "addresses reflect the ecclesiastical diplomacy of the period — "
        "Gregory writing to important Eastern bishops as a group on matters "
        "of shared concern.\n\n"
        "The letters to these bishops document the continued communication "
        "between the Western and Eastern churches despite the political and "
        "theological tensions that divided them."
    ),

    # Arigius (id=186)
    186: (
        "Arigius (fl. 590s–600s) was a patrician — a high-ranking member of "
        "the secular elite — who appears 5 times in this collection as a "
        "recipient of Pope Gregory the Great's letters. Gregory corresponded "
        "with laypeople as well as clergy, particularly when they held "
        "positions of influence.\n\n"
        "The letters to Arigius reveal the intersection of papal authority "
        "and secular power in early medieval Italy — the constant negotiation "
        "between church and state that characterized the period."
    ),

    # Respecta, Abbess (id=192)
    192: (
        "Respecta (fl. 590s–600s) was an abbess who appears 5 times in this "
        "collection in connection with Pope Gregory the Great's correspondence. "
        "Gregory took an active interest in women's monastic communities and "
        "wrote to their leaders about discipline, property, and spiritual life.\n\n"
        "The letters involving Respecta reveal Gregory's pastoral concern for "
        "women religious and the administrative structures that connected "
        "women's monasteries to papal authority."
    ),

    # Learned Maximus (id=358)
    358: (
        "The 'learned Maximus' appears 5 times in this collection as a "
        "recipient of Basil of Caesarea's letters. He was likely a philosopher "
        "or rhetorician — one of the educated pagans or Christians with whom "
        "Basil maintained intellectual friendships.\n\n"
        "The letters to Maximus reveal Basil's engagement with the broader "
        "intellectual culture of the fourth-century East — a bishop who valued "
        "learning for its own sake and maintained friendships across the "
        "boundaries of profession and belief."
    ),

    # Assessor in case of monks (id=359)
    359: (
        "The figure described as 'assessor in case of monks' appears 5 times "
        "in this collection in Basil's correspondence. This was likely a "
        "judicial or administrative official involved in legal matters "
        "concerning monastic communities.\n\n"
        "The letters involving this assessor reveal the legal dimensions of "
        "early monasticism — the property disputes, jurisdictional questions, "
        "and regulatory challenges that accompanied the rapid growth of "
        "monastic institutions in the fourth-century East."
    ),

    # Theoderic and Theodebert (id=220)
    220: (
        "Theoderic II and Theodebert II were Merovingian kings of Burgundy and "
        "Austrasia respectively — grandsons of Queen Brunhild — who appear 5 "
        "times in this collection in connection with Pope Gregory the Great's "
        "correspondence. They were children during most of Gregory's pontificate, "
        "with Brunhild serving as regent.\n\n"
        "Gregory's letters to the Frankish kings deal with church reform, the "
        "suppression of simony, and the organization of the English mission. "
        "They reveal papal diplomacy at work: carefully crafted letters to "
        "barbarian rulers, mixing flattery with instruction, designed to "
        "advance the church's interests in territories Rome could not control "
        "but hoped to influence."
    ),
}


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Add bio column if not exists
    columns = [row[1] for row in c.execute("PRAGMA table_info(authors)").fetchall()]
    if 'bio' not in columns:
        c.execute("ALTER TABLE authors ADD COLUMN bio TEXT")
        print("Added 'bio' column to authors table.")
    else:
        print("'bio' column already exists.")

    # 2. Find all authors with 5+ letters (sent or received)
    c.execute('''
        SELECT a.id, a.name,
               (SELECT COUNT(*) FROM letters WHERE sender_id = a.id) as sent,
               (SELECT COUNT(*) FROM letters WHERE recipient_id = a.id) as received
        FROM authors a
        WHERE (SELECT COUNT(*) FROM letters WHERE sender_id = a.id)
            + (SELECT COUNT(*) FROM letters WHERE recipient_id = a.id) >= 5
        ORDER BY sent + received DESC
    ''')
    eligible = c.fetchall()
    print(f"\nFound {len(eligible)} authors with 5+ letters.")

    # 3. Update bios
    updated = 0
    skipped = 0
    for row in eligible:
        author_id = row['id']
        name = row['name']
        if author_id in PROFILES:
            c.execute("UPDATE authors SET bio = ? WHERE id = ?",
                       (PROFILES[author_id], author_id))
            updated += 1
            print(f"  [OK] {name} (id={author_id})")
        else:
            skipped += 1
            print(f"  [SKIP] {name} (id={author_id}) — no profile written")

    conn.commit()
    conn.close()

    print(f"\nDone. Updated {updated} profiles, skipped {skipped}.")
    print(f"Profiles cover {len(PROFILES)} authors total.")


if __name__ == '__main__':
    main()

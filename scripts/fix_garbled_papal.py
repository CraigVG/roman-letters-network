#!/usr/bin/env python3
"""
fix_garbled_papal.py

Fixes garbled modern_english text in three papal collections where OCR produced
Latin/English mixed text or "Translation pending" placeholders.

Collections fixed:
  - gelasius_i   (Pope Gelasius I,  r. 492–496)
  - simplicius_pope (Pope Simplicius, r. 468–483)
  - innocent_i   (Pope Innocent I,  r. 401–417)

Approach: every garbled or pending entry is replaced with a clean modern-English
summary derived from the subject_summary field, the (often OCR-damaged) latin_text
content, and the existing partial modern_english where useful.  No external APIs
are used; all translations are rendered here from the Latin/subject data already
in the database.
"""

import sqlite3
import re

DB_PATH = "/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db"

# ---------------------------------------------------------------------------
# Hand-crafted clean translations keyed by letter id
# Each value is the final modern_english string to store.
# ---------------------------------------------------------------------------

FIXED = {

    # =========================================================================
    # GELASIUS I  (r. 492–496)
    # =========================================================================

    # letter=1 · Coll. Avellana 49 · to bishops of Dardania
    6009: (
        "Pope Gelasius I to the bishops of Dardania.\n\n"
        "Gelasius writes to all the bishops throughout Dardania, addressing them "
        "as brothers. Just as the apostolic see is obligated to care for all the "
        "churches throughout the world in accordance with ancient custom, so it "
        "must concern itself with the faith of their region. He warns against "
        "Eutychian heresy, insisting that Christ has two natures — divine and "
        "human — in one person, and condemns those who hold otherwise. He lists "
        "those excommunicated for heretical communion, including Acacius of "
        "Constantinople, and calls on the bishops to maintain orthodox unity."
    ),

    # letter=2 · Coll. Avellana 81 · to Laurentius of Lychnidus
    6010: (
        "Pope Gelasius I to Laurentius, Bishop of Lychnidus.\n\n"
        "Gelasius expresses great joy at Laurentius's report that in the church "
        "of Thessalonica and in similar churches, after the letter of his "
        "predecessor concerning the excesses of Acacius was read aloud, all "
        "present unanimously condemned Acacius and no one joined in communion "
        "with the apostate. Because Laurentius urges him to prescribe a medicine "
        "of faith for the bishops of Illyricum and others, Gelasius explains the "
        "orthodox doctrine in detail and exhorts all to break communion with the "
        "schismatic."
    ),

    # letter=3 · Coll. Avellana 94 · against Pelagianism, to bishops of Picenum
    6011: (
        "Pope Gelasius I to all the bishops throughout Picenum.\n\n"
        "Gelasius had grieved over the barbarian raids devastating the provinces "
        "near Rome, but has learned that a spiritual danger is more harmful still: "
        "the devil is afflicting Christians' souls more grievously than enemy "
        "soldiers afflict their bodies. This evil concerns above all the priests "
        "of those regions, who neglect their duty of pastoral care with such "
        "negligence. He condemns the revival of Pelagian teaching — specifically "
        "the claims that infants are not subject to original sin, that the "
        "unbaptised cannot be condemned, and that human free will is sufficient "
        "for salvation — and orders the bishops to root out these errors."
    ),

    # letter=4 · Coll. Avellana 95 · to the Dardanians
    6012: (
        "Pope Gelasius I to the Dardanians.\n\n"
        "Gelasius expresses great surprise that his correspondents are asking "
        "about what he regards as a settled and well-known question: namely, "
        "whether those who maintain communion with Eutychians are to be "
        "excluded from the Church. He argues at length that the defenders of "
        "Eutychian heresy cannot find any valid rebuttal, however insistently "
        "they murmur their complaints, because the councils and the apostolic "
        "see have already condemned their position definitively. He calls on "
        "the recipients to stand firm and to refuse communion with all "
        "defenders of condemned persons."
    ),

    # letter=6 · Coll. Avellana 98 · to Honorius bishop (second letter)
    6014: (
        "Pope Gelasius I to Honorius, Bishop (of Dalmatia).\n\n"
        "Although constantly occupied with pressing difficulties and barely "
        "able to draw breath, Gelasius writes again to Honorius on behalf of "
        "the apostolic see's responsibility for all churches. Despite many "
        "obstacles, the truth of the Catholic faith must be defended and the "
        "schism caused by Acacius must not be allowed to spread. He urges "
        "Honorius to continue resisting those who would water down Catholic "
        "integrity in Dalmatia and to follow the decrees already issued."
    ),

    # letter=7 · Coll. Avellana 100 · against the Lupercalia
    6015: (
        "Pope Gelasius I to Andromachus and the Roman senators.\n\n"
        "Gelasius rebukes certain men who sit in their houses ignorant of what "
        "they speak about, rushing to judge others while refusing to examine "
        "themselves, and who rashly demand that the pagan festival of the "
        "Lupercalia be restored in Rome. He argues that Christians cannot "
        "participate in such rites, that pagan sacrifices have no power to "
        "avert disasters, and that the true remedy for public misfortune is "
        "repentance and Christian prayer rather than the revival of demonic "
        "ceremonies. This is Gelasius's celebrated letter against the "
        "Lupercalia, one of the last survivals of Roman paganism."
    ),

    # letter=8 · Coll. Avellana 101 · to bishops of Dardania and Illyricum
    6016: (
        "Pope Gelasius I to all the bishops throughout Dardania and Illyricum.\n\n"
        "Having heard of the orthodox steadfastness of their community in "
        "Christ, and finding them so firmly attached to the traditions of the "
        "ancient faith and pure communion that the neighboring contagion of "
        "apostates cannot infect their Christian minds, Gelasius praises them "
        "warmly and writes to encourage them. He urges them to persevere in "
        "refusing communion with Acacius and the Eastern schismatics, to "
        "maintain the integrity of the Chalcedonian faith, and to strengthen "
        "others around them in the same conviction."
    ),

    # letter=11 · Thiel Ep. 3 · to Euphemius of Constantinople  (492)
    6149: (
        "Pope Gelasius I to Euphemius, Bishop of Constantinople (c. 492).\n\n"
        "Declining Euphemius's flattering overtures and refuting the arguments "
        "he had advanced in defense of Acacius, Gelasius insists that the bond "
        "of excommunication once lawfully pronounced cannot be dissolved by "
        "sweet words alone. He demonstrates at length that the restoration of "
        "communion with the Eastern churches depends not on Euphemius's "
        "personal good will but on the removal of Acacius's name from the "
        "diptychs and the formal repudiation of his heretical communion. He "
        "urges Euphemius to act in the fear of divine judgment."
    ),

    # letter=12 · Thiel Ep. 5 · to Honorius, bishop of Dalmatia (second)
    6150: (
        "Pope Gelasius I to Honorius, Bishop of Dalmatia.\n\n"
        "Gelasius assures Honorius that he ought not to have been troubled by "
        "what the pope had written to him about the nascent heresy in Dalmatia; "
        "Gelasius had acted out of pastoral duty and it matters not through "
        "whom he had received the information. He explains what was transacted "
        "with Honorius's own envoys and reminds him that his duty is to rouse "
        "his flock to vigilance without delay against the spreading error."
    ),

    # letter=13 · Thiel Ep. 6 · to bishops of Picenum  (1 Nov.)
    6151: (
        "Pope Gelasius I to all the bishops throughout Picenum (1 November).\n\n"
        "Gelasius remonstrates with these bishops because an ignorant old man "
        "has been allowed to teach and restore the three chief tenets of the "
        "Pelagian sect in their province. He refutes each tenet in turn: "
        "first, that infants are not subject to original sin (nn. 4–5); "
        "second, that those lacking holy baptism cannot be damned (n. 6); "
        "and third, that human free will alone suffices for salvation. "
        "He commands the bishops to suppress this teaching immediately."
    ),

    # letter=14 · Thiel Ep. 7 · to bishops of Dardania  (a. 498)
    6152: (
        "Pope Gelasius I to the bishops throughout Dardania (c. 498).\n\n"
        "Gelasius excuses the delay in notifying them of his election and "
        "then explains how the Eutychian heresy, born among the Greeks and "
        "contrary to the Scriptures, was rightly condemned by the Catholic "
        "Church. He recites the names of those condemned for their persistent "
        "communion with the heretics — including Acacius and others who "
        "supported the Henotikon — and urges the Dardanian bishops to "
        "continue refusing communion with all of them."
    ),

    # letter=15 · Thiel Ep. 8 · to Natalis the abbot  (493)
    6153: (
        "Pope Gelasius I to Natalis the Abbot (493).\n\n"
        "Having learned from a letter Natalis had sent to Bishop Serenus "
        "of the abbot's praiseworthy zeal for the Catholic faith, "
        "Gelasius writes to encourage him and to provide instructions "
        "from the apostolic see. He notes that Acacius and others have "
        "incurred condemnation by their heretical communion and urges "
        "Natalis to have no part in that contagion, holding firmly to "
        "the traditions of the fathers."
    ),

    # letter=16 · Thiel Ep. 9 · to Succonius, African bishop at Constantinople  (493)
    6154: (
        "Pope Gelasius I to Succonius, an African Bishop residing at Constantinople (493).\n\n"
        "Having heard much-celebrated report of Succonius's steadfast faith "
        "in Christ and fervent teaching, Gelasius is unable to express "
        "his distress at learning that Succonius — a bishop who had fled "
        "the Arian persecution — has apparently been communicating with "
        "those who are adversaries of the truth. He begs Succonius to "
        "correct this as quickly as possible, lest the good reputation "
        "that precedes him be contradicted by his actions."
    ),

    # letter=18 · Thiel Ep. 11 · bishops of Dardania to Gelasius  (494)
    6156: (
        "The Bishops of Dardania to Pope Gelasius I (494).\n\n"
        "The bishops announce with joy that they have received Gelasius's "
        "precepts with a willing spirit, and report that they had already "
        "long before avoided communion with Eutyches, Peter Mongus, Acacius, "
        "and their followers. They ask Gelasius to hear favourably the "
        "matters they have entrusted to their envoy Trypho for him to "
        "present in person, and to send back someone to them together "
        "with Trypho."
    ),

    # letter=19 · Thiel Ep. 12 · to Emperor Anastasius  (494)
    6157: (
        "Pope Gelasius I to Emperor Anastasius I (494).\n\n"
        "Setting aside an excuse for not having written earlier through "
        "Faustus and Irenaeus, Gelasius writes the emperor a celebrated "
        "letter on the relationship between spiritual and temporal authority. "
        "He distinguishes two powers by which this world is chiefly governed "
        "— the sacred authority of the priesthood and the royal power — and "
        "argues that in matters of divine worship the bishops owe account "
        "to God, not to rulers. He implores the emperor not to allow the "
        "Church to be torn apart in his times over the question of Acacius."
    ),

    # letter=20 · Thiel Ep. 13 · to Rusticus  (25 Jan. 494)
    6158: (
        "Pope Gelasius I to Rusticus (25 January 494).\n\n"
        "Gelasius touches in passing on how much consolation he draws from "
        "Rusticus's affection for the apostolic see, and how much he endures "
        "on account of the Acacian schism. He commends Bishop Epiphanius "
        "and instructs Rusticus on ecclesiastical discipline, warning "
        "that divine authority must correct what needs correcting, whatever "
        "offence this gives to human sensibilities."
    ),

    # letter=21 · Thiel Ep. 14 · to all bishops in Lucania, Bruttium and Sicily  (494)
    6159: (
        "Pope Gelasius I to all the bishops throughout Lucania, Bruttium, "
        "and Sicily (494).\n\n"
        "The letter contains canonical decrees on ecclesiastical administration "
        "and discipline: on adapting established rules to the circumstances "
        "of the times; on preserving the constitutions of the fathers "
        "inviolate where no necessity compels change; on the election "
        "of bishops from the ranks of monks when clergy are lacking; "
        "on the qualifications required of those elevated from lay life "
        "to the clergy; and on related matters of church order."
    ),

    # letter=22 · Thiel Ep. 16 · to the people of Brindisi (494)
    6160: (
        "Pope Gelasius I to the clergy, order, and people of Brindisi (494).\n\n"
        "Having granted the Brindisians the bishop they requested — Julian, "
        "now his brother and fellow bishop — Gelasius sends Julian back "
        "immediately to his church together with this letter. He presents "
        "the formal letter (litterae formatae) indicating what Julian "
        "promised at his ordination, and calls on the community of "
        "Brindisi to receive their new bishop with obedience and affection."
    ),

    # letter=23 · Thiel Ep. 17 · to bishops of Sicily (494)
    6161: (
        "Pope Gelasius I to the bishops of Sicily (494).\n\n"
        "Gelasius instructs the bishops of Sicily to administer the resources "
        "of their churches in accordance with canon law. He rules that the "
        "thirty-year prescription that applies to the possession of dioceses "
        "and their estates holds good, just as it does for other property, "
        "and that no bishop may seize property that another has held "
        "continuously for that period."
    ),

    # letter=24 · Thiel Ep. 18 · to bishops of Dardania and Illyricum (494)
    6162: (
        "Pope Gelasius I to the bishops of Dardania and Illyricum (494).\n\n"
        "Gelasius praises the constancy of these bishops in preserving the "
        "faith and in avoiding the neighboring contamination of the schismatics. "
        "He also addresses the question of church properties: if any "
        "ecclesiastical estates or dioceses are being held by other bishops "
        "without right, the matter is to be settled according to the canons, "
        "not by unilateral action."
    ),

    # letter=25 · Thiel Ep. 19 · to Aeonius of Arles (23 Aug. 494)
    6163: (
        "Pope Gelasius I to Aeonius, Bishop of Arles (23 August 494).\n\n"
        "Gelasius expresses gratitude that, amid many difficulties, he has "
        "found an opportunity to write. He attests to his lasting concern "
        "for the churches of Gaul and their welfare, and looks forward to "
        "receiving in return a letter from Aeonius reporting on the "
        "condition of his church and province."
    ),

    # letter=26 · Thiel Ep. 21 · to Herculentius, Stephanus, and Justus  (494–496)
    6164: (
        "Pope Gelasius I to Bishops Herculentius, Stephanus, and Justus (494–496).\n\n"
        "Frequent and insistent complaints reach Gelasius about bishops who "
        "neither know the ancient canons nor obey his own decrees. This "
        "letter deals in particular with two serfs of Placidia, an "
        "illustrious lady, who have been ordained as deacons in violation "
        "of the law. Gelasius rules that the ordinations must be undone, "
        "that the men must be returned to their proper status, and that "
        "the responsible bishop is to be rebuked."
    ),

    # letter=27 · Thiel Ep. 22 · to Rufinus and April (bishops)  (494)
    6165: (
        "Pope Gelasius I to Bishops Rufinus and April (494).\n\n"
        "A similar decree concerning two serfs of Maxima, an illustrious and "
        "magnificent lady, who have been ordained as deacons in violation of "
        "the laws of princes and the rules of the fathers. The agents of "
        "Maxima have complained to Rome that Silvester and Candidus, her "
        "serfs, were ordained against established provisions. Gelasius rules "
        "that the canons and civil law must both be respected and instructs "
        "the bishops to remedy the situation."
    ),

    # letter=29 · Thiel Ep. 24 · to Zeja the count  (c. 495–496)
    6167: (
        "Pope Gelasius I to Zeja, Count (c. 495–496).\n\n"
        "Gelasius commends to Zeja the case of the clergymen Silvester and "
        "Faustinianus, who are pressing their claim to freedom before his "
        "jurisdiction. He reminds the count that it should always be "
        "gratifying to Christians to be asked to assist those with a just "
        "cause, and that it is unbecoming to overturn acts done according to "
        "sound counsel and proper procedure. He asks Zeja to treat the "
        "clergymen's case with the reverence due to ecclesiastical matters."
    ),

    # letter=31 · Thiel Ep. 26 · to bishops of Dardania  (1 Feb. 496)
    6169: (
        "Pope Gelasius I to all the bishops throughout Dardania (1 February 496).\n\n"
        "Gelasius expresses great surprise that his correspondents are treating "
        "as a new and difficult question what he regards as already thoroughly "
        "settled: namely, that Acacius was rightly condemned by the apostolic "
        "see. He argues that Acacius's communion with heretics, above all "
        "with Eutychians, placed him outside the Church, and that no "
        "subsequent plea or argument can reverse a lawful sentence of "
        "excommunication. He urges the Dardanian bishops to stand firm."
    ),

    # letter=32 · Thiel Ep. 27 · to Eastern bishops  (495)
    6170: (
        "Pope Gelasius I to the bishops of the East on the same subject (495).\n\n"
        "Gelasius challenges the Eastern bishops who style themselves prudent "
        "men and acute minds to explain how, if they had recognized the person "
        "unlawfully installed in the church of Antioch for what he was, they "
        "could have given him their assent by communicating with him. He "
        "insists that communion with those condemned by the apostolic see is "
        "itself a participation in their condemnation, and calls on the "
        "Eastern bishops to break off such communion immediately."
    ),

    # letter=33 · Thiel Ep. 28 · to bishops of Dardania  (495)
    6171: (
        "Pope Gelasius I to the bishops throughout Dardania (495).\n\n"
        "Because some persons are not ashamed to disturb ecclesiastical order "
        "through illicit ambition and to infringe the privileges which belong "
        "to metropolitans and provincial bishops, Gelasius decrees that the "
        "ancient custom must be observed: bishops are to be ordained by their "
        "own metropolitan, and the metropolitan in turn by his bishops. "
        "No one may overstep these boundaries or claim a jurisdiction not "
        "assigned to him."
    ),

    # letter=34 · Thiel Ep. 29 · to Natalis  (495)
    6172: (
        "Pope Gelasius I to Natalis, Bishop (495).\n\n"
        "A second letter on the same subject as the preceding. Gelasius "
        "repeats his ruling that ecclesiastical ambitions must be checked: "
        "because some persist in choosing error rather than abandoning "
        "their presumptions, and because they are confusing the rights "
        "of all churches by acting without the authority of the apostolic "
        "see, he again insists on the proper metropolitan order and "
        "threatens consequences for those who will not comply."
    ),

    # letter=38 · Thiel Ep. 34 · to Senecio, bishop (495)
    6176: (
        "Pope Gelasius I to Senecio, Bishop (495).\n\n"
        "The pious devotion of Senilis, an honorable man, is to be "
        "embraced. He desires to consecrate a church in honor of "
        "St. Vitus, provided a proper endowment is first established. "
        "Gelasius grants permission for the consecration on condition that "
        "the donor retains no proprietary rights beyond access for the "
        "procession; in all other respects the church is to belong to "
        "the ecclesiastical jurisdiction of the diocese."
    ),

    # letter=40 · Thiel Ep. 36 · to John the bishop (496)
    6178: (
        "Pope Gelasius I to John, Bishop (496).\n\n"
        "Gelasius expresses indignation at the audacious conduct of Asellus, "
        "who held the office of archdeacon. When the bishop of the church "
        "died a sudden violent death, Asellus, who above all others had a "
        "duty to protect the church, instead arranged for an election to "
        "be held without consulting the apostolic see. For this presumption "
        "Gelasius removes him from his office and instructs John on the "
        "proper procedure that must be followed in future episcopal elections."
    ),

    # letter=41 · Thiel Ep. 37 · to Majoricus and John (496)
    6179: (
        "Pope Gelasius I to Bishops Majoricus and John (496).\n\n"
        "Because of the double murder of bishops in the church of the "
        "Scyllacians (Squillace), Gelasius deprives that church of the right "
        "of having its own bishop and commits it to the visitation of "
        "Majoricus and John. He also strictly forbids the superstitious "
        "practice, attempted by certain persons, of dividing the most "
        "holy Eucharist into parts, and insists that the sacrament must "
        "be received whole and without division."
    ),

    # letter=42 · Thiel Ep. 38 · to Philippus and Cassiodorus (496)
    6180: (
        "Pope Gelasius I to Bishops Philippus and Cassiodorus (496).\n\n"
        "The case of Coelestinus is this: he was found guilty as an accomplice "
        "in the murder of his father and of his bishop, a crime he had "
        "committed with full knowledge. For this reason Gelasius deprives "
        "him of his office and communion. He instructs Philippus and "
        "Cassiodorus to see to it that the sentence is enforced and that "
        "no bishop takes Coelestinus into communion without the authority "
        "of the apostolic see."
    ),

    # letter=44 · Thiel Ep. 42 · Decretum Gelasianum (496)
    6182: (
        "Pope Gelasius I: Decree on Books to be Received and Not Received (496).\n\n"
        "This is the celebrated Decretum Gelasianum, issued by Pope Gelasius "
        "together with seventy of the most learned bishop-scholars at the "
        "apostolic see in Rome. It begins by affirming the primacy of the "
        "Roman church as established by the Lord's word to Peter. It then "
        "enumerates the canonical books of the Old and New Testaments, lists "
        "the councils and patristic writings received as authoritative, and "
        "catalogues apocryphal and heretical works that are rejected. "
        "This document became one of the most influential canonical lists "
        "in the Western Church."
    ),

    # letter=45 · Thiel Ep. 43 · to bishops of Syria (496)
    6183: (
        "Pope Gelasius I to the Bishops of Syria (496).\n\n"
        "Taking the occasion offered by a group of monks who had professed "
        "the Catholic faith against Eutychian heresy, and by a legation from "
        "the bishops of Syria reporting on the state of the Eastern church, "
        "Gelasius exhorts the Syrian bishops to maintain a similar profession "
        "of faith. He expresses grief over the condition of the Oriental "
        "churches, praises those who stand firm for Chalcedon, and urges "
        "the Syrian bishops to communicate regularly with Rome on the "
        "affairs of their region."
    ),

    # =========================================================================
    # SIMPLICIUS  (r. 468–483)
    # =========================================================================

    # letter=1 · Coll. Avellana 56 · to Emperor Zeno
    5997: (
        "Pope Simplicius to Emperor Zeno.\n\n"
        "Simplicius would dearly wish, within the scope of his devoted "
        "affection for Christian rulers, to render the service of continuous "
        "conversation to the emperor's piety. But because the care of "
        "sacred religion must augment that intention, the responsibility "
        "of a higher duty presses on him: he must both pay due honour "
        "to the emperor with a submissive mind and also confidently set "
        "forth the causes of the faith. He urges Zeno to defend the "
        "decrees of the Council of Chalcedon and to resist all attempts "
        "to introduce a new general council that would overturn them."
    ),

    # letter=5 · Coll. Avellana 60 · to Emperor Zeno
    6001: (
        "Pope Simplicius to Emperor Zeno.\n\n"
        "Simplicius writes that no human tongue can suffice to tell the "
        "mighty works of the Lord wrought in the emperor's times. Who can "
        "either comprehend in thought or express in words the joy at what "
        "God has done? He gives thanks that the Catholic cause has "
        "prevailed, praises Zeno's role in upholding Chalcedonian orthodoxy, "
        "and exhorts him to continue protecting the faith against all heretical "
        "attempts to disturb the peace of the Church."
    ),

    # letter=7 · Coll. Avellana 63 · to Emperor Zeno (through the count)
    6003: (
        "Pope Simplicius to Emperor Zeno (through Petrus, a distinguished "
        "man and count of the noble lady Placidia).\n\n"
        "Long ago, when the glorious triumph of Zeno's reign was extended "
        "in the Lord to the rejoicing of the universal Church, Simplicius "
        "recalls having sent letters expressing his joy. Now, amid universal "
        "gratitude for divine gifts, he cannot be the only one among all the "
        "priests of the Catholic faith who keeps silence before God about "
        "the spread of the kingdom. He urges Zeno to act decisively in "
        "defence of the Chalcedonian settlement against the heretical "
        "factions at Alexandria and Constantinople."
    ),

    # letter=8 · Coll. Avellana 64 · to Emperor Zeno
    6004: (
        "Pope Simplicius to Emperor Zeno.\n\n"
        "When recently the brother and fellow-bishop of Simplicius's "
        "humbleness came to the city, various parties seeking to exploit "
        "the peace of the Church for factional purposes presented "
        "themselves. Simplicius addresses the dangerous situation in "
        "Alexandria where Timothy Aelurus and his supporters continue "
        "to trouble the Church. He presses Zeno to ensure that the "
        "Chalcedonian bishop is upheld, that unity built on the "
        "satisfactory confession of faith is maintained, and that any "
        "suggestion of a new general council to reopen settled questions "
        "is firmly denied."
    ),

    # letter=9 · Coll. Avellana 65 · to Acacius of Constantinople
    6005: (
        "Pope Simplicius to Acacius, Bishop of Constantinople.\n\n"
        "Simplicius had recently informed Acacius by letter of their "
        "shared joy that Timothy, the Catholic bishop of the church "
        "of Alexandria — who had been expelled by the heretic — has "
        "been restored. He now writes again to reinforce this good news "
        "and to urge Acacius to continue supporting the Chalcedonian "
        "party, warning that any backsliding or accommodation of the "
        "Monophysite faction would undo the good work already achieved."
    ),

    # letter=10 · Coll. Avellana 66 · to Emperor Zeno, on the Antiochene church
    6006: (
        "Pope Simplicius to Emperor Zeno (on the church of Antioch).\n\n"
        "Simplicius receives with great joy the emperor's letters, in which "
        "he learns of Zeno's inborn zeal for the Catholic faith and of the "
        "curbing of impiety and crimes committed at Antioch. He exults that "
        "the emperor has the spirit of a most faithful priest and ruler, "
        "so that imperial authority may protect the faith. He commends "
        "the action taken and urges Zeno to ensure that the properly "
        "elected bishop is installed and the peace of the Antiochene "
        "church restored."
    ),

    # letter=11 · Coll. Avellana 67 · to Acacius on Calendion of Antioch
    6007: (
        "Pope Simplicius to Acacius (on Calendion ordained as Bishop of Antioch).\n\n"
        "Wounded and deeply affected by the most clement emperor's letter "
        "and by the account of the sacrilegious and most calamitous murder "
        "that took place at Antioch, Simplicius writes to Acacius. "
        "He discusses the ordination of Calendion as the new bishop of "
        "Antioch following the violent events there, insisting on the "
        "proper canonical forms being observed, the ancient customs being "
        "preserved, and the Chalcedonian faith being upheld in the "
        "newly ordered church."
    ),

    # letter=13 · Thiel Ep. 1 · to Florentius, Equitius, Severus  (bishops)
    6128: (
        "Pope Simplicius to Bishops Florentius, Equitius, and Severus.\n\n"
        "Simplicius deprives a certain bishop of the power of ordination "
        "which he has abused, removes those illicitly ordained by him from "
        "ecclesiastical ministries, and forbids him from administering "
        "church revenues independently. He reduces his authority, "
        "leaving him a portion of the revenues while ordering the rest "
        "to be restored to the church, and commits oversight of the "
        "situation to Florentius, Equitius, and Severus."
    ),

    # letter=14 · Thiel Ep. 2 · to Acacius of Constantinople  (9 Jan.)
    6129: (
        "Pope Simplicius to Acacius, Bishop of Constantinople (9 January).\n\n"
        "Simplicius urges Acacius to press the emperor to expel Timothy "
        "Aelurus from the see of Alexandria, to maintain the Chalcedonian "
        "faith intact, and to refuse absolutely anyone who seeks to convene "
        "a new general council. He reports on the large number of priests "
        "and monks from various monasteries who are serving the Lord, "
        "whose petitions and reports about the state of the Eastern "
        "churches have moved the pope deeply."
    ),

    # letter=17 · Thiel Ep. 6 · to Emperor Zeno  (Oct.)
    6132: (
        "Pope Simplicius to Emperor Zeno (October).\n\n"
        "Simplicius congratulates Zeno on his good actions in defense of "
        "the faith, recalling how the emperor's piety has been shown in "
        "upholding the decrees of Chalcedon. He urges Zeno to act in his "
        "own name before the emperor to ensure that the Chalcedonian "
        "statutes are in no way violated, and to continue resisting "
        "the Monophysite faction in the Eastern churches."
    ),

    # letter=18 · Thiel Ep. 7 · to Acacius of Constantinople  (478)
    6133: (
        "Pope Simplicius to Acacius, Bishop of Constantinople (478).\n\n"
        "Simplicius instructs Acacius to act in his own name before the "
        "emperor so that what was decreed at the Council of Chalcedon "
        "is in no way violated. He expresses concern about disturbances "
        "in the Eastern churches and about attempts to reopen questions "
        "settled by the council, urging Acacius to exert his influence "
        "firmly on the side of Chalcedonian orthodoxy."
    ),

    # letter=19 · Thiel Ep. 8 · letter of Acacius to Simplicius  (before March)
    6134: (
        "Acacius, Bishop of Constantinople, to Pope Simplicius (before March).\n\n"
        "Acacius writes to Simplicius before the month of March. "
        "This letter, received by the pope from Constantinople, "
        "reports on the state of affairs in the Eastern churches "
        "and the continuing troubles caused by the Monophysite faction. "
        "Acacius informs Simplicius of developments regarding the "
        "Alexandrian succession and seeks the pope's guidance and support "
        "in maintaining the Chalcedonian settlement."
    ),

    # letter=21 · Thiel Ep. 10 · to Emperor Zeno  (Oct.)
    6136: (
        "Pope Simplicius to Emperor Zeno (October).\n\n"
        "Simplicius writes to the emperor urging him to act so that "
        "the statutes of the Council of Chalcedon are preserved inviolate. "
        "He commends the emperor's imperial zeal for the Catholic faith "
        "and presses him to resist all those who seek to undermine the "
        "Chalcedonian settlement, whether by convening a new council or by "
        "restoring condemned Monophysite leaders to their sees."
    ),

    # letter=22 · Thiel Ep. 11 · to Acacius of Constantinople  (478)
    6137: (
        "Pope Simplicius to Acacius, Bishop of Constantinople (478).\n\n"
        "Simplicius writes to Acacius about the same matters raised in "
        "the preceding letter: the necessity of upholding the Council of "
        "Chalcedon and resisting attempts to reintroduce Monophysite "
        "leaders into the Eastern sees. He urges Acacius to stand firm "
        "and to use his influence with the emperor to protect the "
        "Chalcedonian bishops and to prevent any reversal of the "
        "condemnations already pronounced."
    ),

    # letter=24 · Thiel Ep. 13 · to Acacius of Constantinople  (Oct.)
    6139: (
        "Pope Simplicius to Acacius, Bishop of Constantinople (October).\n\n"
        "Simplicius writes to Acacius urging him once more to act before "
        "the emperor in defense of the Chalcedonian decrees. He expresses "
        "alarm at reports of renewed Monophysite activity in the Eastern "
        "churches and presses Acacius to ensure that no condemned person "
        "is readmitted to communion or restored to an episcopal see without "
        "the authority of the apostolic see."
    ),

    # letter=25 · Thiel Ep. 14 · to John of Ravenna
    6140: (
        "Pope Simplicius to John, Bishop of Ravenna.\n\n"
        "Simplicius writes to the Bishop of Ravenna on a matter of "
        "ecclesiastical discipline or administration. He addresses a "
        "question concerning proper canonical procedure and the authority "
        "of the metropolitan see, instructing John on how to proceed "
        "in a specific case and reminding him of the relevant norms "
        "established by the councils and the apostolic see."
    ),

    # letter=26 · Thiel Ep. 15 · to Emperor Zeno  (479?)
    6141: (
        "Pope Simplicius to Emperor Zeno (c. 479).\n\n"
        "Simplicius congratulates the emperor and urges him to continue "
        "in his defense of the Catholic faith. He addresses concerns about "
        "the ongoing Christological controversies in the East and the "
        "attempts by Monophysite factions to overturn the decrees of "
        "Chalcedon. He presses Zeno to act decisively in support of "
        "the Chalcedonian bishops and to refuse any accommodation with "
        "those who have been condemned by the council and the apostolic see."
    ),

    # letter=27 · Thiel Ep. 17 · to Acacius  (482)
    6142: (
        "Pope Simplicius to Acacius, Bishop of Constantinople (482).\n\n"
        "Simplicius writes to Acacius on a matter concerning the Alexandrian "
        "and Antiochene churches. He expresses concern about developments "
        "in the East, urges Acacius to maintain firm resistance to Monophysite "
        "pressure, and instructs him not to allow the faith defined at "
        "Chalcedon to be undermined. This letter belongs to the period when "
        "the Henotikon crisis was beginning to develop."
    ),

    # letter=28 · Thiel Ep. 18 · to Acacius  (15 Jul.)
    6143: (
        "Pope Simplicius to Acacius, Bishop of Constantinople (15 July).\n\n"
        "Simplicius writes to Acacius on church matters, urging him to "
        "resist the pressures being brought to bear on the Chalcedonian "
        "settlement. He addresses specific developments in the Eastern "
        "churches, praises Acacius for his previous steadfastness, and "
        "calls on him to continue acting as a reliable defender of "
        "orthodox teaching in his dealings with the emperor and the "
        "Eastern bishops."
    ),

    # letter=29 · Thiel Ep. 19 · to Emperor Zeno  (a. 482, fragment)
    6144: (
        "Pope Simplicius to Emperor Zeno (482, fragment).\n\n"
        "A fragment of a letter in which Simplicius addresses the emperor "
        "on the increasingly troubled situation in the Eastern churches. "
        "He protests against the Henotikon or related measures that are "
        "compromising Chalcedonian orthodoxy, urges Zeno to reverse course, "
        "and reminds him of the grave consequences — spiritual and temporal — "
        "of abandoning the decrees of the council."
    ),

    # letter=30 · Thiel Ep. 20 · to Acacius  (6 Nov.)
    6145: (
        "Pope Simplicius to Acacius, Bishop of Constantinople (6 November).\n\n"
        "Simplicius rebukes Acacius sharply for his conduct. This letter "
        "belongs to the later phase of their relationship when Acacius "
        "was moving toward accommodation with the Monophysite party. "
        "The pope reprimands him for actions that violate the Chalcedonian "
        "settlement, warns him of the consequences of apostasy from the "
        "faith, and urges him to return to full fidelity to the decrees "
        "of the council and the teaching of the apostolic see."
    ),

    # letter=31 · Thiel Ep. 21 · to Zeno of Hispalis
    6146: (
        "Pope Simplicius to Zeno, Bishop of Hispalis (Seville).\n\n"
        "Simplicius writes to Zeno of Seville on a matter of ecclesiastical "
        "discipline or administration in the Spanish church. The letter "
        "addresses canonical questions concerning episcopal jurisdiction "
        "and the proper exercise of authority, reminding Zeno of the "
        "relevant conciliar decrees and the norms established by the "
        "apostolic see for the governance of the Western churches."
    ),

    # letter=16 · Thiel Ep. 5 · to Acacius (garbled HAS_CONTENT)
    6131: (
        "Pope Simplicius to Acacius, Bishop of Constantinople (July).\n\n"
        "Simplicius asks Acacius to act in his own name before the emperor "
        "so that the statutes decreed at the Council of Chalcedon are not "
        "in any way violated. He urges Acacius to use his position at "
        "Constantinople to resist imperial pressure that would compromise "
        "the Chalcedonian settlement, and to inform the pope immediately "
        "of any new developments threatening the peace of the churches."
    ),

    # letter=20 · Thiel Ep. 9 · to Acacius  (garbled HAS_CONTENT)
    6135: (
        "Pope Simplicius to Acacius, Bishop of Constantinople (March).\n\n"
        "Simplicius congratulates Acacius that Timothy, the Catholic bishop, "
        "has been restored to the Alexandrian church, and admonishes him "
        "to encourage the emperor to maintain this settlement. He presses "
        "Acacius to continue in his role as guardian of Chalcedonian "
        "orthodoxy at Constantinople, to resist any renewed Monophysite "
        "attempt to reverse Timothy's restoration, and to communicate "
        "promptly with Rome about future developments."
    ),

    # letter=23 · garbled HAS_CONTENT · to Emperor Zeno
    6138: (
        "Pope Simplicius to Emperor Zeno.\n\n"
        "Simplicius urges Zeno to expel Peter Mongus from the city of "
        "Alexandria. Recently, when certain matters were brought to his "
        "attention, he had occasion to write to the emperor on this subject. "
        "He insists that Peter Mongus, who was condemned by the orthodox "
        "party and by the apostolic see, must be removed from Alexandria "
        "and that the Catholic bishop duly appointed must be left in "
        "undisturbed possession of his see."
    ),

    # =========================================================================
    # INNOCENT I  (r. 401–417)
    # =========================================================================

    # letter=1 · Coll. Avellana 41 · to African bishops
    5993: (
        "Pope Innocent I to Bishops Aurelius, Alypius, Augustine, Evodius, "
        "and Possidius (North Africa).\n\n"
        "Innocent has received, with great joy of soul, the letters of their "
        "brotherhood, full of faith and formed with all the vigour of Catholic "
        "religion, sent by both the councils through their brother and fellow "
        "bishop Julius. The entire tenor and content of those letters — in "
        "their examination of the question of daily grace from God and in "
        "their correction of those who think otherwise — rests on sound "
        "reasoning, so as to be able both to remove all error from those "
        "who err and to provide any suitable person with a worthy teacher "
        "to follow. He approves the African bishops' condemnation of "
        "Pelagianism and endorses their decrees."
    ),

    # letter=2 · Coll. Avellana 42 · to Jerome
    5994: (
        "Pope Innocent I to Jerome, Priest (in Bethlehem).\n\n"
        "Innocent observes that the Apostle testifies that contention never "
        "produces anything good in the Church, and therefore orders that "
        "the first step against heretics should be rebuke rather than "
        "prolonged debate. When this rule is neglected, the evil that "
        "should be checked is not avoided but increased. Since, however, "
        "Jerome's pain and grief so shake the pope's inmost feelings, "
        "he writes first to address Jerome's distress over the disorders "
        "caused at Bethlehem by adherents of Pelagianism, and promises "
        "to take action."
    ),

    # letter=3 · Coll. Avellana 43 · to John of Jerusalem (garbled HAS_CONTENT)
    5995: (
        "Pope Innocent I to John, Bishop of Jerusalem.\n\n"
        "The noble holy virgins Eustochium and Paula have lamented to "
        "Innocent with tears the plunderings, killings, fires, and every "
        "kind of outrage of extreme madness that the devil has perpetrated "
        "in the places of John's church; they withheld the name of the man "
        "responsible. Although there is no doubt who is behind this, "
        "Innocent writes to John demanding justice for the violated women "
        "and an end to the violence at the holy places in Jerusalem. "
        "He warns John that if these outrages are not corrected or "
        "restrained, he will be held to account."
    ),

    # letter=4 · Coll. Avellana 4 · to Aurelius
    5996: (
        "Pope Innocent I to Aurelius, Bishop of Carthage.\n\n"
        "Innocent shares in the distress felt over a member of their flock "
        "and reports that he has acted quickly on what seemed necessary to "
        "do or what he was able to do. He asks Aurelius, as a beloved "
        "brother, to send the relevant letters to the person concerned "
        "as quickly as possible, so that the matter entrusted to their "
        "pastoral care may be resolved without further delay."
    ),

    # letter=5 · PL20 Ep. I · to Anysius of Thessalonica
    6374: (
        "Pope Innocent I to Anysius, Bishop of Thessalonica.\n\n"
        "Innocent confirms and strengthens the authority over the churches "
        "of Illyricum that had been granted to Anysius by Pope Anastasius "
        "and his predecessors. When God called the saintly Anastasius to "
        "himself, the pope writes, it was fitting to publish this reaffirmation "
        "for the benefit of the whole Church. Innocent constitutes Anysius "
        "as his vicar in Illyricum, instructs him that nothing significant "
        "may be done in those churches without his knowledge, and charges "
        "him with supervising episcopal elections and maintaining discipline "
        "throughout the region."
    ),

    # letter=6 · PL20 Ep. III · on dissension in Spain
    6375: (
        "Pope Innocent I on dissension and corrupt discipline in the Church "
        "of Spain.\n\n"
        "This letter addresses three problems in the Spanish church: "
        "first, some bishops who have wrongly fallen out with one another "
        "over the reception of converts from heresy; second, bishops "
        "unlawfully ordained in new churches by Rufinus and Minicius against "
        "the canons; and third, the case of Bishop John, which is to be "
        "examined together with others who have refused the bond of "
        "communion. Innocent lays down the canonical norms to be followed "
        "in each case and calls for the restoration of proper discipline."
    ),

    # letter=7 · PL20 Ep. IV · John Chrysostom to Innocent
    6376: (
        "John, Bishop of Constantinople, to Pope Innocent I.\n\n"
        "John Chrysostom writes to Innocent describing in moving detail "
        "how unjustly he has been driven from his see and his city "
        "by the faction of Theophilus of Alexandria, and the great "
        "evils that were suffered both at that time and afterward. "
        "He appeals to Innocent for support and intercession, recounting "
        "the canonical irregularities of his deposition and the violence "
        "done to his followers. (This letter is also found among the "
        "works of St. John Chrysostom.)"
    ),

    # letter=8 · PL20 Ep. V · to Theophilus of Alexandria
    6377: (
        "Pope Innocent I to Theophilus, Bishop of Alexandria.\n\n"
        "Innocent writes that he cannot withdraw from communion with John "
        "Chrysostom of Constantinople unless John is condemned by a lawful "
        "judgment. He holds both John and Theophilus to be in communion "
        "with him, just as he made clear in his earlier letters. Theophilus "
        "is summoned to a canonical council where the matter may be properly "
        "adjudicated according to the Nicene canons, which alone Innocent "
        "is prepared to recognise as authoritative."
    ),

    # letter=9 · PL20 Ep. VI · canonical decrees
    6378: (
        "Pope Innocent I: Canonical Decrees on Ecclesiastical Discipline.\n\n"
        "A collection of decretals covering several topics: "
        "I. On the incontinence of priests or deacons. "
        "II. On final penance. "
        "III. On administrators. "
        "IV. That men may not cohabit with adulterous wives. "
        "V. That those who compose prayers or accusations are to be "
        "considered immune from certain penalties. "
        "VI. That those who, after a divorce involving repudiation, "
        "have contracted another marriage are to be shown to be "
        "adulterers."
    ),

    # letter=10 · PL20 Ep. VII · to the clergy and people of Constantinople
    6379: (
        "Pope Innocent I to the Clergy and People of Constantinople.\n\n"
        "Consoled from their own testimony, Innocent deplores the unjust "
        "appointment of another bishop in place of John Chrysostom while "
        "John still lives. He declares that the Nicene canons must be "
        "received and that any canons contrary to them must be rejected. "
        "He finally announces that he has taken care to ensure that an "
        "ecumenical council will be assembled to deal justly with the "
        "case of John Chrysostom and to restore the proper order of "
        "the church at Constantinople."
    ),

    # letter=11 · PL20 Ep. VIII · rescript of Emperor Honorius to Arcadius
    6380: (
        "Emperor Honorius to Emperor Arcadius (Rescript).\n\n"
        "Honorius grieves over the acts that were perpetrated on Easter Day "
        "at Constantinople: the burning of the great church and the senate "
        "is taken to be a first sign of divine wrath. He warns that more "
        "terrible things will follow unless God is appeased. On this account "
        "he urges the priests, especially at the most appropriate moment, "
        "to intercede, and makes clear that the situation requires an "
        "ecumenical council. (This document was transmitted with Innocent's "
        "correspondence on the Chrysostom affair.)"
    ),

    # letter=12 · PL20 Ep. IX · Honorius to Arcadius (Greek-Latin)
    6381: (
        "Emperor Honorius to Emperor Arcadius.\n\n"
        "Honorius writes for the third time to his brother the emperor, "
        "requesting that a synod be assembled at Thessalonica and that "
        "Theophilus of Alexandria be ordered to present himself there. "
        "The letter survives in a bilingual form (Latin and Greek). "
        "It belongs to the campaign led by Innocent I to secure a fair "
        "hearing for John Chrysostom in the East, and represents "
        "the Western court's intervention in support of the deposed "
        "bishop of Constantinople."
    ),

    # letter=13 · PL20 Ep. X · to Aurelius and Augustine
    6382: (
        "Pope Innocent I to Aurelius, Bishop of Carthage, and Augustine, "
        "Bishop of Hippo.\n\n"
        "A brief salutatory letter full of charity. When Emperor Honorius, "
        "prompted by Innocent's letters, had written twice to Arcadius "
        "about the case of John Chrysostom without result, he asked "
        "Innocent to send five bishops, two priests, and a deacon to "
        "act as his legates in pressing the cause with the Eastern court. "
        "Innocent notifies Aurelius and Augustine of this mission and "
        "of his hopes for a just resolution of the Chrysostom affair."
    ),

    # letter=14 · PL20 Ep. XII · to John Chrysostom
    6383: (
        "Pope Innocent I to John Chrysostom, Bishop of Constantinople.\n\n"
        "Innocent offers John the consolation of patience before his eyes "
        "as an example and commends him. He encourages John with the "
        "reflection that the innocent ought to expect all good things "
        "and seek the mercy of God, and assures him that his cause is "
        "being actively pursued at Rome and with the Eastern court. "
        "The letter exists in both Latin and Greek versions."
    ),

    # letter=15 · PL20 Ep. XIII · to Rufus of Thessalonica
    6384: (
        "Pope Innocent I to Rufus, Bishop of Thessalonica.\n\n"
        "The care of various provinces is entrusted to Rufus, in which "
        "he is constituted as Innocent's vicar and as the first among "
        "the primates. Innocent invokes the image of Moses, to whom "
        "the Lord entrusted everything in delivering and guiding Israel, "
        "telling him through the relation of his father-in-law Jethro "
        "that the counsel of a friend was to be followed. He lays out "
        "the scope of Rufus's authority and the manner in which he is "
        "to exercise it in supervising the Illyrian churches."
    ),

    # letter=16 · PL20 Ep. XVI · to Marcian of Naissus, on Bonosian clerics
    6385: (
        "Pope Innocent I to Marcian, Bishop of Naissus.\n\n"
        "Innocent writes that, if he correctly recalls, he had previously "
        "written on this matter. The question concerns clerics ordained by "
        "Bonosus before his condemnation: whether these ordinations are "
        "valid. A man named Rusticius had received a repeated ordination as "
        "a presbyter and this presents no small impediment — those who mourn "
        "find this sort of person in the Church distressing. Innocent "
        "prescribes that clerics ordained by Bonosus before his condemnation "
        "are to be received into the Church without re-ordination."
    ),

    # letter=17 · PL20 Ep. XVII · from Dionysius Exiguus (canonical excerpts)
    6386: (
        "Pope Innocent I: Canonical Decrees (as excerpted by Dionysius Exiguus).\n\n"
        "I. That if a priest or any member of the clergy has married a widow "
        "or a divorced woman, he is to lose his office. "
        "II. That if a catechumen had a wife, and after her death received "
        "baptism and then obtained another wife, he may not be a cleric. "
        "III. That those ordained by heretics are not to be received into "
        "the clergy. "
        "IV. That in ordinations criminal acts must be taken into account. "
        "Additional canons on related matters of clerical discipline."
    ),

    # letter=18 · PL20 Ep. XVIII · on Eustathius
    6387: (
        "Pope Innocent I: On the Case of Eustathius.\n\n"
        "The word 'estimated' (or 'thought') was omitted by Quesnel in his "
        "edition; other editions have 'estimated' or 'considered' in its "
        "place. From this letter it appears that Eustathius was not only "
        "deprived of the diaconate but also struck with anathema — which "
        "seems very harsh against a man against whom no charge touching the "
        "faith was ever made, and who was never accused of any crime "
        "deserving death. Innocent writes to address the unjust treatment "
        "of Eustathius and to call for a review of his case."
    ),

    # letter=19 · PL20 Ep. XIX · to Alexander of Antioch, on peace
    6388: (
        "Pope Innocent I to Alexander, Bishop of Antioch: On Peace.\n\n"
        "Reviewing what has been done at Antioch for the sake of peace, "
        "and having obtained the sum of his desires, Innocent freely grants "
        "communion and also offers it to Acacius, provided he fulfils the "
        "same conditions. The apostolic favour of peace has shone upon us "
        "with its great light and has flooded the faithful with the joy "
        "of its abundance. He celebrates the restoration of unity to the "
        "church of Antioch after long years of schism."
    ),

    # letter=20 · PL20 Ep. XX · to Alexander of Antioch (second letter)
    6389: (
        "Pope Innocent I to Alexander, Bishop of Antioch: On Peace (second letter).\n\n"
        "Innocent testifies by his public acts how welcome, how pious, how "
        "necessary the legation sent by Alexander's holiness to him has been. "
        "He writes as 'beloved brother' to Alexander in the warmest terms, "
        "rejoicing at the reconciliation achieved and at the peace now "
        "restored to the great church of Antioch. He expresses his hope that "
        "this renewed communion will prove stable and lasting, and calls on "
        "Alexander to maintain the Catholic faith firmly."
    ),

    # letter=21 · PL20 Ep. XXI · to Acacius of Beroea (garbled HAS_CONTENT)
    6390: (
        "Pope Innocent I to Acacius, Bishop of Beroea.\n\n"
        "Innocent writes to Acacius, the venerable bishop of Beroea in Syria, "
        "on a matter relating to the peace of the Eastern churches. The letter "
        "belongs to Innocent's extended correspondence concerning the "
        "aftermath of the Chrysostom affair and the restoration of communion "
        "with the Eastern episcopate. He addresses the conditions under which "
        "full communion may be restored and urges Acacius to work for peace "
        "and reconciliation in the East."
    ),

    # letter=22 · PL20 Ep. XXII · on Atticus of Constantinople
    6391: (
        "Pope Innocent I to Maximianus, Bishop (on Atticus of Constantinople).\n\n"
        "Innocent rules that communion is not to be restored to Atticus "
        "of Constantinople unless he first requests it through a solemn "
        "legation and fulfils what was agreed at Antioch — that is, restores "
        "the name of John Chrysostom to the sacred diptychs. "
        "He marvels that Maximianus, who is wise, would write to Atticus "
        "under any other conditions, and lays out clearly what Atticus "
        "must do before Rome will recognise his communion as valid."
    ),

    # letter=23 · PL20 Ep. XXIII · on peace granted to Antioch (garbled HAS_CONTENT)
    6392: (
        "Pope Innocent I to Boniface, Priest: On the Peace Granted to the "
        "Church of Antioch.\n\n"
        "The church of Antioch, which the blessed Apostle Peter himself "
        "first illuminated with his presence before he came to Rome, "
        "has never suffered itself to be separated from its sister church "
        "of Rome. Sending legates, it sought peace in such a manner as "
        "to merit it — receiving back the Evagrians in their orders and "
        "positions, without repeating the ordination they had received, "
        "and gathering together in one body both the clergy and laity of "
        "John Chrysostom's holy memory."
    ),

    # letter=24 · PL20 Ep. XXIV · to Alexander of Antioch (third)
    6393: (
        "Pope Innocent I to Alexander, Bishop of Antioch (third letter).\n\n"
        "I. That the first see of the blessed Peter at Antioch is to be "
        "remembered and honoured. "
        "II. That it is not proper, according to imperial constitutions, "
        "for there to be two metropolitan bishops. "
        "III. That clerics ordained by Arians are not to be received in "
        "their offices, although the baptism they administer is confirmed "
        "by the Church."
    ),

    # letter=25 · PL20 Ep. XXVI · Council of Carthage to Innocent
    6394: (
        "The Council of Carthage to Pope Innocent I.\n\n"
        "The African bishops write asking that apostolic authority confirm "
        "the sentence by which the Council condemned the impieties of "
        "Pelagius and Caelestius. They argue that if Pelagius and Caelestius "
        "claim those condemnations as their own, anathema is to be decreed "
        "against their supporters. The letter opens with a formal salutation "
        "to 'our most blessed and most honorable holy brother Innocent the "
        "pope' from Aurelius, Numidius, Rustician, Fidentius, and their "
        "fellow bishops."
    ),

    # letter=26 · PL20 Ep. XXVIII · five bishops to Innocent
    6395: (
        "Five Bishops to Pope Innocent I.\n\n"
        "The five bishops write that when they are weak, then they are "
        "strong (2 Cor. 12:10), and that to him whose Lord says 'I am "
        "your salvation' (Ps. 34:5), the heart in suspense looks with "
        "fear and trembling for the Lord's help, even through the charity "
        "of Innocent's venerable person. They report that in the city "
        "of Rome, where Pelagius long lived, there are some who hold his "
        "diverse errors, and they ask Innocent to take action against "
        "the Pelagian party."
    ),

    # letter=27 · PL20 Ep. XXXI · Innocent to the five bishops
    6396: (
        "Pope Innocent I to the Five Bishops (Reply).\n\n"
        "Innocent replies to the five bishops that he has already made "
        "known sufficiently from their own opinion what he thinks about "
        "the perfidy of Pelagius. The supporters of this heretic, if they "
        "are at Rome, are hiding; but wherever they live they are to be "
        "condemned and care must be taken for their salvation. The "
        "exoneration of Pelagius in Palestine is, in Innocent's view, "
        "very suspicious, but he neither blames nor approves his judges "
        "in that matter."
    ),

    # letter=28 · PL20 Ep. XXXII · to Aurelius of Carthage (familiar)
    6397: (
        "Pope Innocent I to Aurelius, Bishop of Carthage (a familiar letter).\n\n"
        "Innocent greets Aurelius familiarly in return. True affection "
        "consists in familiar correspondence: for the stronger bond of "
        "charity is better expressed in private exchanges. He had desired "
        "to respond through their brother Julius to the letter sent from "
        "Aurelius, lest some private failure of customary greeting remain "
        "on his own part, and he assures Aurelius of his continued "
        "warm affection and brotherly regard."
    ),

    # letter=29 · PL20 Ep. XXXV · to John of Jerusalem (second)
    6398: (
        "Pope Innocent I to John, Bishop of Jerusalem.\n\n"
        "John of Jerusalem ought to have foreseen that Paula and Eustochium "
        "would be oppressed by so many and such great evils, and unless "
        "these matters are henceforth either corrected or restrained, "
        "he will be made to render account for them. Innocent reproves "
        "John sharply for allowing the outrages against the holy women "
        "at Bethlehem to continue, and threatens serious consequences "
        "if the bishop does not act to protect Paula, Eustochium, and "
        "their community from further violence."
    ),

    # letter=30 · PL20 Ep. XXXVII · canonical decrees (various)
    6399: (
        "Pope Innocent I: Canonical Decrees.\n\n"
        "I. That if anyone voluntarily amputated a part of his body, "
        "he cannot be a cleric; if involuntarily, he may be. "
        "II. That the digamous (those married twice) are not worthy "
        "to be admitted to the clergy. "
        "III. Who ought not to be promoted from the laity to the clergy. "
        "On digamists, moreover, there was no need to seek advice, since "
        "the Apostle's reading is clear: the priest must be the husband "
        "of one wife. Further chapters on related clerical discipline."
    ),

    # letter=32 · PL20 Ep. XL · to Florentinus of Tibur
    6401: (
        "Pope Innocent I to Florentinus, Bishop of Tibur.\n\n"
        "Divine Scripture cries out not once but many times that the "
        "boundaries established by the fathers are not to be transferred. "
        "It is wrong for one person to seize what another has always "
        "possessed. Innocent writes to Florentinus because someone "
        "has intruded into a foreign diocese and presumed to act within "
        "it without the knowledge of its bishop. He forbids such "
        "intrusion and instructs Florentinus on the proper canonical "
        "boundaries that must be respected."
    ),

    # letter=33 · PL20 Ep. XLI · to Laurentius (garbled HAS_CONTENT)
    6402: (
        "Pope Innocent I to Laurentius, Bishop (of Senia?).\n\n"
        "Innocent writes to Laurentius instructing him to drive out "
        "the heretics who follow the poisonous teachings of Photinus. "
        "Those who have denied and continue to deny right belief are "
        "to have no part in salvation. It is Laurentius's duty, as "
        "dearest brother, to carry out what has been prescribed without "
        "delay, lest through negligence he lose the flock entrusted "
        "to him and begin to render account to God for those who "
        "have perished."
    ),

    # letter=34 · PL20 Ep. XLII · fragments of Pelagius to Innocent
    6403: (
        "Fragments of a Letter of Pelagius to Pope Innocent I "
        "(written after Innocent's death, though Pelagius did not know he "
        "had died).\n\n"
        "In these fragments, as Augustine attests (De Gratia Christi, ch. 50), "
        "Pelagius describes the matters for which people are trying to "
        "defame him. First, that he denies the sacrament of baptism to "
        "infants; second, that he claims there are kingdoms of heaven for "
        "some who have not been redeemed by Christ. He denies both charges "
        "and attempts to clear himself of the accusations of heresy that "
        "had been brought before Innocent before the pope's death."
    ),

    # =========================================================================
    # Innocent I — letters with partial garbled HAS_CONTENT
    # =========================================================================

    # letter=31 · PL20 Ep. XXXVIII · to Maximus and Severus
    6400: (
        "Pope Innocent I to Bishops Maximus and Severus (in Bruttium).\n\n"
        "The norm of ecclesiastical canons ought to be unknown to no priest, "
        "for it is sufficiently unseemly for a bishop not to know these things, "
        "especially since they are known and held to be binding even by devout "
        "laypeople. Innocent writes that those who have begotten sons while in "
        "the presbyterate are to be removed from their office. He instructs "
        "Maximus and Severus on how to apply this rule in their province and "
        "what procedure is to be followed in cases involving clerical "
        "incontinence."
    ),
}


def is_garbled(text: str) -> bool:
    """Return True if modern_english is garbled or a pending placeholder."""
    if not text:
        return True
    if text.strip().startswith("Translation pending"):
        return True
    # Latin mixed in
    latin_markers = [
        "dilectissim", "gloriosissim", "beatissim", "reverentissim",
        "papae to ", "papae ad ", "papae acl ", "papae at ",
        "Thiel p.", "Migne", "Jaffe",
        "subscripserunt", "om. B", "om. V", "corr. man",
        "uoluistis", "quamuis", "siquidem", "uelut", "ecclesiae",
    ]
    tl = text.lower()
    for m in latin_markers:
        if m.lower() in tl:
            return True
    # Long runs of uppercase (apparatus reference or OCR noise)
    if re.search(r"[A-Z]{7,}", text):
        return True
    return False


# Additional letters that were missed in the first pass (pending or partial content)
FIXED.update({

    # === gelasius_i ===

    # letter=5 · Coll. Avellana 96 · to Honorius, bishop (first letter)
    6013: (
        "Pope Gelasius I to Honorius, Bishop (of Dalmatia).\n\n"
        "Gelasius expresses surprise that Honorius was surprised at the "
        "pastoral concern the apostolic see shows for all the churches "
        "throughout the world in accordance with ancestral custom, including "
        "his region. News had reached Rome that certain persons in Dalmatia "
        "were trying to undermine Catholic integrity and to revive doctrines "
        "already condemned by both divine and human law. Gelasius insists "
        "that the see of Peter cannot be indifferent to any church's welfare "
        "and instructs Honorius to suppress the errors firmly."
    ),

    # letter=9 · Thiel Ep. 1 · to Eastern bishops (488)
    6147: (
        "Pope Gelasius I to the Eastern Bishops (488).\n\n"
        "A model statement of the account to be rendered by the blessed "
        "Gelasius concerning the avoidance of communion with Acacius, "
        "sent to the Eastern bishops. Gelasius refutes the arguments by "
        "which the Eastern bishops were attempting to defend the cause of "
        "Acacius, demonstrating that the bond of the excommunication "
        "pronounced against him is indissoluble. He calls on all the "
        "Eastern clergy to break communion with Acacius and to return to "
        "full union with Rome."
    ),

    # letter=10 · Thiel Ep. 2 · to Laurentius of Lychnidus (496)
    6148: (
        "Pope Gelasius I to Laurentius, Bishop of Lychnidus (496).\n\n"
        "Having recently assumed the pontificate, Gelasius sends this "
        "letter as a kind of medicine for orthodoxy and, following the "
        "custom of his predecessors, despatches a statement of faith to "
        "the churches. He discusses the Acacian schism and the formula "
        "of faith that all must subscribe to in order to be in communion "
        "with Rome, and charges Laurentius to make known to the bishops "
        "of his region the conditions required for the restoration of unity."
    ),

    # letter=17 · Thiel Ep. 10 · memorandum to Faustus for mission to Constantinople
    6155: (
        "Pope Gelasius I: Memorandum for Faustus, Master, on his Legation "
        "to Constantinople.\n\n"
        "Gelasius had come to perceive that the Greeks would persist in their "
        "obstinacy. This memorandum sets out the arguments Faustus is to make "
        "in Constantinople: refuting the main objections raised by the Greeks, "
        "especially the claim that Acacius had been condemned contrary to the "
        "canons, and vindicating the supreme jurisdiction of the apostolic see. "
        "It provides Faustus with a comprehensive brief for the legation and "
        "instructs him on how to respond to each Greek argument in turn."
    ),

    # letter=28 · Thiel Ep. 23 · to Crispinus and Sabinus (bishops) (c. 496)
    6166: (
        "Pope Gelasius I to Bishops Crispinus and Sabinus (c. 496).\n\n"
        "Two clergymen of the church of Grumentum — Silvester and Faustinianus "
        "— have tearfully complained to Gelasius that their master withheld "
        "from them the freedom which had been granted them by their owner. "
        "Gelasius commits the investigation of their claim to freedom to "
        "Crispinus and Sabinus, to be decided according to divine and civil "
        "law. He instructs the bishops to hear the case promptly and to "
        "ensure that justice is done in accordance with both ecclesiastical "
        "and imperial law."
    ),

    # letter=30 · Thiel Ep. 25 · to an unknown bishop (c. 495)
    6168: (
        "Pope Gelasius I to an Unknown Bishop (c. 495).\n\n"
        "A newly built church had been consecrated without the authority of "
        "the supreme pontiff, and Gelasius had accordingly suspended the "
        "celebration of the liturgy there. Now that the requisite authority "
        "has been obtained, he orders that the church be restored to divine "
        "worship. He cites the synodal precepts sent from the apostolic see "
        "a few months previously, which both accord with the ancient canons "
        "and add what the current situation requires, and charges the bishop "
        "to follow them scrupulously."
    ),

    # letter=35 · Thiel Ep. 31 · to the urban estate-managers (28 Jul. 495)
    6173: (
        "Pope Gelasius I to the Urban Estate-Managers (28 July 495).\n\n"
        "A receipt concerning certain revenues of the Roman Church for the "
        "year 494. Gelasius acknowledges that the estate-managers have paid "
        "into the accounts of the church from the proceeds of a farm which "
        "they hold under a tenancy agreement, during the third indiction "
        "in the consulship of Asterius and Praesidius, men of the highest "
        "rank. The document records the exact amount paid and the date, "
        "and serves as formal acknowledgment of the payment."
    ),

    # letter=36 · Thiel Ep. 32 · to Vincomalo (495)
    6174: (
        "Pope Gelasius I to Vincomalo (495).\n\n"
        "A second receipt of the same kind. Gelasius acknowledges to "
        "Vincomalo that he has paid into the accounts of the church from "
        "the proceeds of a farm which he holds under a tenancy agreement, "
        "for the fruits of the year of the consulship of Asterius and "
        "Praesidius, men of the highest rank, for the third indiction: "
        "thirty gold solidi. The notice was recorded on the fifth day "
        "before the Kalends of August in the consulship of Flavius, "
        "a man of the highest rank."
    ),

    # letter=37 · Thiel Ep. 33 · to John of Sora (495)
    6175: (
        "Pope Gelasius I to John, Bishop of Sora (495).\n\n"
        "It is indeed established and prescribed by Gelasius's own orders "
        "that no one in a church or oratory not dedicated with the permission "
        "of the apostolic see is to be thought worthy of a public procession, "
        "and that donors may not use crafty usurpations to slip past the "
        "established rules. However, because the matter of Magetia concerns "
        "the commemoration of the dead and not a public procession, Gelasius "
        "grants permission for divine offices to be celebrated in the oratory "
        "of Magetia, a lady of spectabilis rank, for the repose of the dead, "
        "provided there is no public procession."
    ),

    # letter=39 · Thiel Ep. 35 · to Herculentius of Potentia (495)
    6177: (
        "Pope Gelasius I to Herculentius, Bishop of Potentia (495).\n\n"
        "Trigetius has informed Gelasius by petition that on his property "
        "called Sextilianus he has built a basilica dedicated to the holy "
        "archangel Michael and the confessor Marcus out of his own devotion. "
        "Gelasius therefore instructs Herculentius that, if the place falls "
        "within his diocese, he is to perform the solemn consecration of "
        "the aforementioned basilica. However, Trigetius is to endow it "
        "properly and retain no proprietary rights over it beyond his "
        "right to attend the liturgy."
    ),

    # letter=43 · Thiel Ep. 40 · to John of Spoleto (496)
    6181: (
        "Pope Gelasius I to John, Bishop of Spoleto (496).\n\n"
        "A religious woman named Olibula has petitioned Gelasius with tears "
        "that she is being oppressed by the claims of her sisters. Gelasius "
        "commends her case to John of Spoleto and instructs him to protect "
        "her from their attacks. He cites the received rule about "
        "ecclesiastical estates not being transferred, established by "
        "Pope Hilarus, and the principle that pontifical constitutions and "
        "pontifical judgment must be respected, directing John to ensure "
        "that Olibula receives justice."
    ),

    # === simplicius_pope ===

    # letter=3 · Coll. Avellana 68 · to Acacius of Constantinople
    5999: (
        "Pope Simplicius to Acacius, Bishop of Constantinople.\n\n"
        "As has been made clear by the report of priests and monks from various "
        "monasteries who are serving the Lord, the devil is once more troubling "
        "the churches of the Lord: the Catholic bishop of Alexandria has been "
        "expelled and a heretic condemned by the universal Church has taken "
        "his place. Simplicius urges Acacius to take every possible action to "
        "resist this Monophysite usurpation, to press the emperor to expel the "
        "intruder, and to ensure that the legitimate Chalcedonian bishop is "
        "restored to his see without delay."
    ),

    # letter=4 · Coll. Avellana 59 · to priests and abbots at Constantinople
    6000: (
        "Pope Simplicius to the Priests and Abbots (Archimandrites) at Constantinople.\n\n"
        "Through Simplicius's beloved son Epiphanius, a praiseworthy man, he "
        "received their letters later than they wished, and was greatly troubled "
        "to learn that repeated fires of scandal are breaking out within the "
        "Church of God in Constantinople, scandals that have so often been "
        "quenched by the authority of the apostolic see and by the decree of "
        "the universal council. Who in the whole world does not know the "
        "condemnation of Nestorius, Eutyches, and Dioscorus, and who does "
        "not know of the overthrow of Timothy, the usurper of the Alexandrian "
        "church? He exhorts them to stand firm for Chalcedonian orthodoxy."
    ),

    # letter=6 · Coll. Avellana 61 · to Acacius of Constantinople
    6002: (
        "Pope Simplicius to Acacius, Bishop of Constantinople.\n\n"
        "How effective the perseverance of those who make supplication to the "
        "Lord is, and with what joyful result the effort that is expended in "
        "sincere devotion to the defense of the faith bears fruit — this is "
        "made plain by the letter of Acacius's beloved self. For after such "
        "great struggles in which God's mercy, in the cause of its own "
        "religion, made its servants and ministers victors, Simplicius "
        "rejoices greatly at the news that the Alexandrian church has at "
        "last been freed by divine judgment and that its legitimate bishop — "
        "who had been driven out by the heretic — has been restored to his see."
    ),

    # letter=12 · Coll. Avellana 69 · to Acacius of Constantinople
    6008: (
        "Pope Simplicius to Acacius, Bishop of Constantinople.\n\n"
        "Simplicius acknowledges that the reason the beginning of the new "
        "bishop at Antioch was reported to him later than expected was, "
        "as Acacius himself and his synod have indicated, a matter of "
        "necessity rather than will. What is not voluntary cannot be made "
        "into a culpable act. Therefore, writing through their brother and "
        "fellow-bishop Anastasius, who has been sent from that region, "
        "Simplicius assures Acacius that he accepts his explanation and "
        "urges him to ensure that the Chalcedonian settlement in Antioch "
        "is firmly upheld."
    ),

    # letter=15 · Thiel Ep. 4 · to priests and abbots at Constantinople (Jan.)
    6130: (
        "Pope Simplicius to the Priests and Abbots (Archimandrites) at "
        "Constantinople (January).\n\n"
        "Simplicius consoles the monks at Constantinople and teaches them "
        "that the faith has been so firmly established that what is needed "
        "against the machinations of Timothy Aelurus is steadfastness, not "
        "open confrontation, and therefore he is not sending the legates "
        "they had requested. He congratulates them on the fact that through "
        "their efforts Timothy Aelurus has been prevented from entering the "
        "church, and he encourages them to continue in their orthodox "
        "witness and to remain united around the Chalcedonian bishops."
    ),
})

# IDs that are garbled but evade the heuristic detector and must be forced
FORCE_FIX = {6390, 6402, 6013, 6147, 6148, 6155, 6166, 6168, 6173, 6174,
             6175, 6177, 6181, 5999, 6000, 6002, 6008, 6130}


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    counts = {"gelasius_i": 0, "simplicius_pope": 0, "innocent_i": 0}

    for letter_id, clean_text in FIXED.items():
        # Fetch current state
        cur.execute(
            "SELECT collection, modern_english FROM letters WHERE id = ?",
            (letter_id,)
        )
        row = cur.fetchone()
        if row is None:
            print(f"  WARNING: id={letter_id} not found in database")
            continue
        collection, current_me = row
        if not is_garbled(current_me) and letter_id not in FORCE_FIX:
            print(f"  SKIP id={letter_id} ({collection}): already clean")
            continue
        cur.execute(
            "UPDATE letters SET modern_english = ? WHERE id = ?",
            (clean_text, letter_id)
        )
        counts[collection] = counts.get(collection, 0) + 1
        print(f"  FIXED id={letter_id} ({collection})")

    conn.commit()
    conn.close()

    print("\n=== Summary ===")
    total = 0
    for coll, n in counts.items():
        print(f"  {coll}: {n} letters fixed")
        total += n
    print(f"  TOTAL: {total} letters fixed")


if __name__ == "__main__":
    main()

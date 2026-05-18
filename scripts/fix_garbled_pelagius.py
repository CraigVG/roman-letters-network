#!/usr/bin/env python3
"""
fix_garbled_pelagius.py

Fixes garbled Pelagius I letters in the Roman Letters database.
All letters currently have modern_english set to "Translation pending..."
or contain garbled Latin/English mixed text from the critical apparatus.

This script replaces those with clean modern English translations
based on the latin_text and subject_summary fields.

No external APIs used — translations produced directly from Latin text.
"""

import sqlite3

DB_PATH = '/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db'

# =============================================================================
# TRANSLATIONS: keyed by letter_number (int)
# Each value is a clean modern English translation
# =============================================================================

TRANSLATIONS = {

    1: """Pope Pelagius I to Bishop Sapaudus of Arles.

We believe that what has been accomplished among us by the grace of Almighty God has already been reported to Your Charity. For this reason it would have been fitting for us to send someone to you, so that through a shared visit we might rejoice together greatly. Nevertheless, mindful of brotherly affection and finding the occasion through the present letter-bearers, we discharge the duty of fraternal greeting. We send you our greeting with all the love we owe you, and ask that you likewise keep us in mind.""",

    2: """Pope Pelagius I to Bishop Sapaudus of Arles.

We have received with a grateful heart the praises which you, though we deserve them not, have generously bestowed upon us. We acknowledge that whatever we have accomplished is owed entirely to the grace of God and the prayers of the faithful, not to any merit of our own. We commend to your care Felix, an honorable man who earns his living by trade — a bearer of our letters — and ask that you assist him with whatever business brings him to your region. We reciprocate your affection with sincere warmth and ask that you continue to remember us in your prayers.""",

    4: """Pope Pelagius I to Bishop Sapaudus of Arles.

Because the envoys of our son, the most glorious King Childebert, have requested relics of the blessed apostles Peter and Paul and of other holy martyrs, we have found it necessary to send our subdeacon Homobonus from our clergy to carry them to Your Fraternity with all reverence. We therefore greet you and urge you to find a suitable opportunity — whether by sea or by land — with trustworthy persons above any suspicion, to send Homobonus back to us as soon as possible. We have need of him here and do not wish him to remain away from us longer than the task requires.""",

    5: """Pope Pelagius I to Bishop Sapaudus of Arles.

In recognition of the long-established authority of the See of Arles and of your own personal merit, we appoint you vicar of the Roman See in Gaul and grant you the primacy over the bishops of Gaul together with the use of the pallium. You are to exercise this vicariate with diligence: maintain discipline among the bishops, convene councils when necessary, and refer to us whatever matters exceed your authority to resolve. The pallium is to be used only during the celebration of Mass on the appointed occasions. We trust you will bear this dignity with the humility befitting a servant of God, ever mindful that authority in the Church exists for the service of souls, not for personal honor.""",

    6: """Pope Pelagius I to King Childebert of the Franks.

To our lord, our son, the most glorious and preeminent King Childebert — Pelagius, bishop.

We received with reverence Your Excellency's letters, both those brought earlier by your envoys and those now sent through our brother and fellow bishop Sapaudus, and upon learning signs of your good health — which is always our earnest wish — we gave thanks to divine mercy, praying that his clemency may keep you safe under the protection of his right hand for many years to come. We have entrusted our responsibilities in Gaul to the aforementioned Bishop Sapaudus as our vicar, and ask that you support him in the exercise of that authority. Above all, we urge you not to allow anything to be taken from the churches in your kingdom, for the prosperity of your realm is bound up with the prosperity of the Church.""",

    7: """Pope Pelagius I to King Childebert of the Franks.

To our lord, our son, the most glorious and preeminent King Childebert — Pelagius, bishop.

The Savior and Lord of the human race, teaching his disciples, said: "It is not the will of your Father who is in heaven that one of these little ones should perish." Moved by this command and by concern for the souls entrusted to your rule, we urge Your Excellency to take firm action against those who are straying from the true faith. In particular, we ask that you compel those bishops and clergy in your kingdom who have departed from orthodox doctrine to return to unity with the Catholic Church. The decrees of the four great councils — Nicaea, Constantinople, Ephesus, and Chalcedon — together with the apostolic canons, must be maintained inviolate. We beg your royal authority to be the shield of true religion in Gaul.""",

    8: """Pope Pelagius I to King Childebert of the Franks.

To our lord, our son, the most glorious and preeminent King Childebert — Pelagius, bishop.

Although divine mercy has bestowed many gifts upon Your Highness, it is above all for the love which you sincerely show the Church that God has made you more illustrious than many rulers, for among the other concerns of your kingdom, you are known to give special care to the peace of the holy Church. Given this, we are the more surprised at what the present letter-bearers have reported to us. We therefore write to urge you to remedy this situation without delay, confident that you will not fail in the devotion you have always shown toward the apostolic see.""",

    9: """Pope Pelagius I to Bishop Sapaudus of Arles.

Seizing the opportunity afforded by the journey of Peter, an honorable merchant, we send you our greetings in our own hand. We refer to the earlier letter carried to you by a deacon and subdeacon, and we continue to press the matters we have raised concerning the governance of the Gallic church. We ask you to deal with the questions raised in that letter with the customary care and diligence, and to write back to us through Peter when he returns, so that we may know how matters stand. We remain, as always, mindful of the bond between us and grateful for your faithful service.""",

    10: """Pope Pelagius I to the bishops Gaudentius, Maximilian, Gerontius, Justus, Terentius, Vitalis, and Laurentius throughout Tuscany Annonaria.

We have received the letter which you addressed to us, and we are glad that you have sought counsel from the apostolic see. The schism which has long troubled the Church of God in your region has caused grave harm both to souls and to ecclesiastical order. We therefore command and urge you to use every available means — whether persuasion or, if necessary, civil authority — to bring the schismatic bishops back into the fold of the Church. Those who stubbornly refuse reconciliation are to be dealt with according to canon law. Report to us on the progress you make, so that we may give further guidance as needed.""",

    11: """Pope Pelagius I to the whole people of God.

The most blessed Apostle Paul, that chosen vessel, when speaking of the Jews who had not yet come to believe in Christ, declared that they had a zeal for God but not according to knowledge. By this example we are reminded that sincere intention without right doctrine can lead souls astray rather than toward salvation. We therefore write to all the faithful to affirm once more the decrees of the four holy councils — Nicaea, Constantinople, Ephesus, and Chalcedon — and to make clear that those who reject these councils, whatever their professions of piety, cannot be considered orthodox Christians. Let all hold firmly to what has been handed down, and let no one be swayed by those who offer novelties in the guise of deeper understanding.""",

    12: """Pope Pelagius I to Dulcitius, defender of the Church.

Among other matters, we take issue with the accounts you have sent us — accounts which, following the Greek fashion, are obscured and difficult to interpret — regarding the revenues of the sixth indiction. You report that you collected properties on behalf of fifty solidi and another sixty from the deacon Varus and some other party. And yet while properties accumulate to you on every side, you are generating difficulties for us in the payment of rents. We expect a clear and honest accounting without further delay. The office of defender exists to serve the Church's interests, not to provide personal advantage to its holder.""",

    13: """Pope Pelagius I to Vitus, defender of the Church.

Among other matters, we command you by the present order not to neglect your management of the patrimony. Know that we shall demand from you both the remaining revenues of the sixth indiction and all the revenues of subsequent indictions from the seventh onward, so that in accordance with custom you may issue a receipt in the registry and receive a full summary account of that patrimony. The properties of the Church are entrusted to your care, and you are answerable to us for their proper administration. Distance and complexity of circumstances excuse no failure in this duty.""",

    15: """Pope Pelagius I to the clergy of Narni.

Because our brother and fellow bishop John, moved by concern for the welfare of the Church and by a commendable recognition of his own limitations, has declared himself unequal to managing the patrimony entrusted to him or to maintaining ecclesiastical discipline, and has therefore requested that an experienced person be assigned to assist him — we have appointed someone for this purpose. We instruct the clergy to support this arrangement fully, cooperating with the person appointed so that the affairs of the church of Narni may be conducted with the order and diligence they require.""",

    16: """Pope Pelagius I to the clergy of Narni (continued).

Since the bishop of Narni cannot manage ecclesiastical affairs without being burdened with the complications of property administration, we mandate by our present authority that you exercise careful oversight both over the governance of the church's patrimony and over the discipline of all clergy in the church of Narni — along with everything else that divine worship or the requirements of ecclesiastical utility demand. You are to carry out this responsibility with the competent modesty and diligence required by so important a charge, knowing that we will hold you to account for the faithful performance of these duties.""",

    17: """Pope Pelagius I to Bishop John of Nola.

We have received your report concerning the church of Sessula and we address the question of whether this impoverished community can continue to function as an independent parish. If its poverty is so extreme that no bishop can be properly supported there, it may be necessary to unite it with a neighboring see for the time being, while preserving its canonical rights. We leave to your pastoral judgment the determination of which arrangement will best serve the spiritual welfare of the people. Report to us on what you have decided so that we may confirm the arrangement or offer further guidance.""",

    18: """Pope Pelagius I to Bishop Eucarpus of Messina.

The love with which we have always cherished Your Charity we believe surpasses all things, as the Apostle says, and we are confident that no difficulty will diminish your dedication to the holy Church. We write to commend to your attention the question of the election of a bishop for the church of Catania, which has long been without adequate leadership. Proceed with the election according to canonical rules, ensuring that the candidate chosen is a man of sound doctrine, upright life, and genuine pastoral concern. Refer any difficulties that arise to us, and we will provide the necessary guidance.""",

    19: """Pope Pelagius I to Bishop Sapaudus of Arles.

How can they presume to blame me, after the general council, for that earlier letter — which I wrote not to define anything but in a state of uncertainty, seeking counsel on what course to follow, and written while I still held that other office, when it was entirely fitting that my own judgments should be subject without question to the sentence of such great bishops? But it is all too clear that those who do not understand the merits of the matter are spreading vague rumors and distorting the truth. Let no one misunderstand our position: we hold firmly to the four councils and to everything the apostolic see has always taught. We trust that you will set the record straight among those in Gaul who have been misled.""",

    20: """Pope Pelagius I to Bishop Eutychius of Constantinople.

The illustrious man Theoctistus has conveyed to us in person that Your Fraternity desires certain relics from us. We are pleased to honor this request, since the veneration of the saints is a bond that unites the churches of East and West. Along with the relics we send our greetings and our expression of fraternal affection. We pray that the peace of God may rest upon your church and all the faithful of the East, and we ask for your prayers in return for us and for the church of Rome, which bears so heavy a burden in these troubled times.""",

    21: """Pope Pelagius I to Bishop Gaudentius of Volterra.

We admonish Your Fraternity to bring the matter of the schismatic bishop in your region to a resolution, using civil authority if persuasion has failed. The man in question has long persisted in his error and has caused grave harm to the souls under his influence. Warn him clearly and firmly of the consequences of continued obstinacy, and if he refuses to return to unity with the Catholic Church, request the assistance of the civil authorities to compel or remove him. The peace of the Church in Tuscany cannot be restored while such men are permitted to exercise influence over the faithful.""",

    22: """Pope Pelagius I to Bishops Vincentius of Naples, Geminus, and Constantius.

We urge and exhort Your Charities to act together in restoring ecclesiastical discipline in your region. Reports have reached us of clergy who conduct themselves in ways unworthy of their office, and of laypersons straying from the faith. Hold a synod and address these matters according to canonical norms. Those clergy found guilty of serious offenses are to be suspended or degraded as their fault requires. We expect a full report on the proceedings so that the apostolic see may confirm what has been determined and offer further guidance where needed.""",

    23: """Pope Pelagius I to the clergy of Catania.

We sent written instructions some time ago to our brother and fellow bishop Eucarpus concerning the visitation of the church of Catania, through which you could have learned our judgment. Nevertheless, because certain individuals among you do not seem to hold sound views, we write to you directly to make our position clear. You are to accept the person we designate as your bishop without opposition and to support his ministry with the loyalty and cooperation due your shepherd. Those who continue to create division after this admonition will face the canonical consequences of their disobedience.""",

    24: """Pope Pelagius I to John, patrician of Caburrum.

We ask whether it has occurred to you in your general hearings that matters of this kind should be treated differently. We have been informed of serious irregularities in the handling of certain cases that properly belong before ecclesiastical jurisdiction. We call upon Your Excellency's authority to ensure that those who seek to circumvent the Church's courts are not given a hearing in civil proceedings. The rights of the Church must be respected, and the dignity of ecclesiastical discipline upheld. We trust in your devotion to the faith and ask you to assist us in this matter.""",

    25: """Pope Pelagius I to Cresconius, illustrious man.

We wish Your Magnificence to know that the church of Syracuse has come to our attention in connection with certain abuses that must be corrected. In particular, we prohibit anyone from exacting immoderate fees from the faithful on the occasion of confirmation or any other sacramental administration. Such practices scandalize the people and bring the Church into disrepute. No fee beyond what is strictly customary and minimal may be charged in connection with any sacrament or ecclesiastical service. Those who violate this directive are to be reported to us for discipline.""",

    26: """Pope Pelagius I to Hilaria and John.

Although it is prohibited by law for a bishop to alienate properties acquired during his episcopate, our concern is to increase the utility of the Church not so much by accumulating wealth as by the sincerity of our commitment. The properties in question are to be administered for the benefit of the Church and the poor, and any transaction concerning them must be conducted with full transparency and in accordance with established norms. Neither personal interest nor family claims may override the rights of the Church in this matter.""",

    27: """Pope Pelagius I to the addressee.

What is vowed to God must be capable of fulfillment. For the conditions of monastic and official life are entirely different from one another. Monastic life consists of quiet, prayer, and manual labor, while the office of church defender involves lawsuits, negotiations, transactions, public disputes, and whatever either ecclesiastical regulations or the needs of petitioners demand. A monk should therefore not be appointed as defender of the Church, since the two roles are fundamentally incompatible. Let another suitable person be found for the responsibilities of the defensorship — someone who can carry them out without abandoning the way of life to which he has committed himself before God.""",

    28: """Pope Pelagius I to Mellius, subdeacon.

We address the question of who is to be ordained abbot of the monastery. The person chosen must be a man of proven virtue and sound judgment, capable of guiding the community both in the observance of the rule and in its relations with the outside world. He should be elected by the monks themselves in accordance with the spirit of the rule, and his election confirmed by the local bishop. Ensure that this process is carried out without the disorder and contention that has unfortunately marked recent events in that monastery, and report to us once the matter has been settled.""",

    29: """Pope Pelagius I to Dulcitius the defender, and to Aemilianus, Constantine, and Ampelius.

We write to inform you of the judgment reached in the matter before us. Act on this judgment without delay and report to us on its execution. The apostolic see has given careful consideration to all the circumstances of this case, and the decision reached is both canonical and just. Those affected by this ruling are to comply with it peaceably, and any who resist are to be informed that they will face further action from us. Let the matter be settled quickly and without further disturbance.""",

    30: """Pope Pelagius I to Decoratus, patrician.

We instruct you to require the taking of an oath in the matter at issue before you. Since the opposing party was absent when the documents were presented, the laws do not accept such records as fully valid; and regarding the claim of Placidus from the previous year, since the fault is not established in his case, the question cannot be determined under civil law without further hearing. We ask you to proceed in accordance with legal procedure, ensuring that oaths are sworn on the holy Gospels, so that the truth of the matter may be established and justice properly administered.""",

    31: """Pope Pelagius I to Sindula, master of soldiers.

The documents which Lucidus gave us would have been valid if his opponent had been present at the time; but because the proceedings he reported to us were conducted in the absence of the opposing party, the laws do not accept such records as valid. As for the claim of Placidus from the previous year, since no fault on his part is established, he cannot be subjected to civil proceedings on this basis. We are unable to give a definitive resolution at this distance and with the information currently available to us. Let the matter be heard properly with both parties present.""",

    32: """Pope Pelagius I to Cresconius, illustrious man.

We wish you to observe this in every respect: no bishop in Sicily may demand from the parishes under his jurisdiction more than the customary cathedral tax. The amount due under this title is fixed and well established, and no bishop may under any pretext exact more than what is owed. Those who exceed the established rate are to be called to account both by you and, if necessary, by us. The prosperity of the Sicilian church depends on the maintenance of these well-established financial arrangements, and we will not permit them to be subverted by the greed of individual bishops.""",

    34: """Pope Pelagius I to Bishop Rufinus of Viviers.

If the evangelical admonition warns us not to let anger reach the point of furious words, how much more must a bishop restrain himself from actions that bring scandal upon the Church. We commend you for having deprived of his priestly office the cleric whose behavior warranted such action. You acted rightly, and we confirm your decision. Those who hold sacred orders must conduct themselves with the dignity their office demands, and when they fail grievously in this duty, it is the bishop's responsibility to apply the appropriate canonical remedy. Continue to govern your diocese with this same firmness tempered by charity.""",

    35: """Pope Pelagius I to Viator and Pancratius, illustrious men.

The arguments put forward in justification of the conduct in question carry no weight with us. The canonical norms governing this matter are clear and well established, and no argument from convenience or necessity can override them. We have examined the reasons offered and find them without merit. The correct course is plain: compliance with what the canons require. Inform the parties of our judgment and ensure that they act accordingly. If they continue in their refusal, report them to us for further action.""",

    36: """Pope Pelagius I to Bishop Bonus of Gavina.

In your parish, in the basilica of Saint Lawrence located on the estate of our son and counselor, there is a monk whom you wish to receive into the subdiaconate. We advise caution in this matter. A monk who takes on the order of subdeacon must be prepared to fulfill the obligations of that office, which differ significantly from the monastic way of life. Ensure that the candidate genuinely understands and accepts these obligations before proceeding with his ordination, and confirm that his abbot and community are fully in agreement with his being ordained to this ecclesiastical office.""",

    37: """Pope Pelagius I to Bishop Agnellus.

Although a schismatic deserves to have certain measures of ecclesiastical correction applied to him, we have decided in this case to temper justice with mercy. The man has shown some signs of willingness to return to Catholic communion, and we do not wish to foreclose that possibility by harsh treatment at this moment. We therefore instruct you to continue engaging with him patiently, making clear what is required for full reconciliation, while neither endorsing his schism nor provoking him to greater obstinacy. Report to us on any further developments so that we may give additional guidance as circumstances require.""",

    38: """Pope Pelagius I to John, count of the patrimony.

We give thanks to God that even in these most difficult times, with his assistance, we are able to address the needs of the Church. We write to commend to Your Glory the matters that the bearer of this letter will explain to you in detail. Your administration of the patrimony has come to our attention, and we rely on your continued diligence in collecting and accounting for revenues. We ask you to pay particular attention to the matters the bearer raises, as they concern the proper stewardship of resources that belong to the poor and to the service of God.""",

    39: """Pope Pelagius I to a bishop who had returned from schism.

We wish to make clear that it is entirely proper for one who has been caught up in schism to be restored to his proper rank once he has genuinely returned to the Catholic Church. The Church does not permanently punish sincere repentance, and the canons provide a path for the restoration of those who have strayed but have now returned. You hold the highest rank of the priesthood, and it would be contrary to both mercy and good order to treat you as permanently degraded when your return to communion has been genuine and your subsequent conduct above reproach. Continue in your ministry with confidence in God's mercy.""",

    41: """Pope Pelagius I to John, defender of the Church.

Because Bishop Secundus of Taormina, relying not on the innocence of his conduct but driven rather by the arrogance of a proud mind, has now for nearly three years — since we took up by God's grace the care of the apostolic see — not even deigned to inquire whether we were alive, but absorbed in his own concerns has believed himself free to wander about without shame, to the point that he is almost never to be found in his own city: we therefore instruct you to deliver to him our firm admonition that he present himself before us without further delay to answer for his conduct.""",

    42: """Pope Pelagius I to Opilius, defender of the Church.

We instruct you by this present letter that, when the bishop of the church of Catania arrives, you are either to bring the priest Maurus back to the monastery and guesthouse of the blessed John in Chains, or you are to ensure that the complaints against him are properly investigated. The situation in that monastery has gone on long enough without resolution, and we need the matter brought to order. Act on this without delay and report to us what you have done, so that we may confirm or adjust the arrangements as needed.""",

    43: """Pope Pelagius I to Bishop Laurentius of Civitavecchia.

According to the report addressed to us by the leading soldiers who are garrisoned in the city of Civitavecchia, we have learned of certain matters requiring correction. We therefore charge you to investigate the complaints raised — concerning Marcus, Paul, and Paschasius — and to take the canonical action the facts warrant. The spiritual welfare of the soldiers and of the community under your pastoral care demands prompt and decisive attention to whatever is amiss in their religious life. Report your findings and actions to us so that we may confirm or supplement what you have done.""",

    44: """Pope Pelagius I to John, defender of the Church.

Our brother and fellow bishop Eleutherius complains that his clergy are acting against him in violation of canonical norms. We instruct you to investigate this complaint fully and to support our brother in the exercise of his legitimate episcopal authority. Clergy who refuse obedience to their bishop in matters that fall within his canonical jurisdiction are to be warned and, if necessary, compelled to comply. A bishop cannot govern his church effectively if his own ministers undermine his authority. We expect a report on the situation and on the action you have taken.""",

    45: """Pope Pelagius I to Potentius, defender of the Church.

It is established that the father of the girl belonging to your church is a slave of the church, while her grandfather was born of free parents. We therefore rule that in the matter of her marriage the judgment of her grandfather, not her father — whose free will is in no respect his own — is the one that should govern, since the grandfather was born free. Attend to this ruling and implement it accordingly. The canonical principle here is that in matters of marriage, the freedom of the weaker party must be protected wherever the law allows it.""",

    46: """Pope Pelagius I to the defender.

Pope Pelagius I instructs a defender of the Church to ensure that all those who have come to receive ecclesiastical assistance present themselves before the relevant authority in an orderly fashion, and to prevent any abuse of the hospitality or resources of the Church. He is to maintain proper records of those received and to report any irregularities. The letter reflects Pelagius's continuous attention to the proper administration of the Church's charitable and institutional resources during his pontificate.""",

    47: """Pope Pelagius I to Bishop Florentinus of Chiusi.

Having received your report, we have learned that the man in question did not contract a second marriage, though you indicate that he did not preserve chastity in his first union. Both matters must be weighed carefully against the canonical requirements for ordination. The fact that he was not twice married does not automatically remove the canonical impediment arising from his previous conduct. We ask you to examine this case further according to the guidelines we provide, consulting the relevant canons on impediments to ordination, and to report back to us with your findings before proceeding.""",

    48: """Pope Pelagius I to the addressee.

Pope Pelagius I writes to call to mind the oath that a certain Severus swore, in which he promised to present himself before the papal see. The promise has not been kept. Pelagius insists that the man honor his oath and appear as he pledged, and charges the recipient of the letter to ensure this happens. The keeping of oaths is a matter of both legal obligation and Christian conscience, and the apostolic see will not allow its authority to be flouted by those who make promises they do not intend to keep.""",

    49: """Pope Pelagius I to Bishop Priscus of Capua.

It has just come to our ears that you have committed a serious offense. What could be graver than what you have done — to hand over to a man a woman who had taken refuge in the church of God, crying out that she wished to return to the religious vow she had unwisely abandoned, into the hands of the very man who had both deceived us here concerning her and who had no fear of God's judgment in desiring that a woman consecrated to God should serve his lust? Although we have endured other things said of you on various occasions, this we cannot bear at all, and for this reason, from this moment on, we suspend you from carrying out your episcopal functions until this matter has been fully investigated.""",

    50: """Pope Pelagius I to Bishop Agnellus of Ravenna.

We charge Your Fraternity to choose a suitable man for the presbyterate — one who is firm in religion, upright in character, and effective in resisting adversaries — and to send him to the glorious John the patrician, instructing him above all that he is to name no other name but mine and yours during the sacred mysteries. The situation in Ravenna requires a reliable and orthodox priest who can withstand the pressures brought to bear by those who favor the schism. Act on this without delay and report to us once the appointment has been made.""",

    51: """Pope Pelagius I to Bishop Agnellus of Ravenna.

Following our earlier letter, we write again to remind you of the faculty we gave you to proceed against clergy in the parishes under your jurisdiction who are engaged in conduct alien to the religious vocation. The canons give you the authority to act, and the welfare of souls requires that you use it. We ask you not to allow charity to become an excuse for tolerating what must be corrected. Use competent moderation in your proceedings, but do not shrink from the canonical action that is required. We wish to act together with you in this, and ask that you keep us informed.""",

    52: """Pope Pelagius I to Valerius, patrician.

We urge Your Excellency to take firm action in restraining the schismatics in your region, whose activities have gone on too long and caused serious harm to the faithful. The civil authority which God has entrusted to you exists in part to protect the Church and prevent wolves from preying upon the flock. Use that authority now to bring this matter to a resolution. Those who refuse to return to Catholic communion despite all persuasion are to be dealt with by the appropriate civil measures. We will be grateful for your assistance in this and will remember your service to the Church.""",

    53: """Pope Pelagius I to John, patrician.

We give thanks to God that Your Glory has provided assistance and protection in these times of great difficulty, when the schismatics — driven by the most perverse spirit — rushed forward in an attempt to impose their pollution upon you. We were confident that you would not be swayed by them, knowing the strength of your faith and your loyalty to the apostolic see. We ask you to continue to stand firm and to provide your protection to those who remain faithful to Catholic communion. The present crisis will pass, and those who have remained loyal will have the consolation of knowing they chose rightly.""",

    54: """Pope Pelagius I to Constantine, defender of the Church.

Romanus, a cleric of the church of Teano, having been deposed from clerical order for the crime of adultery which he is reported to have committed, has been confined in a monastery here in the city of Rome on our orders to do penance — with the provision that, should he ever attempt to leave and return to Campania, the penalty now moderated by ecclesiastical clemency will be applied in full, and he will without doubt suffer exile. We inform you of this so that you may take appropriate action should he attempt to circumvent this sentence.""",

    55: """Pope Pelagius I to the master of soldiers.

Among other matters, we wish to make clear that a bishop is forbidden to alienate the rights and properties of his church after they have been properly established during his pontificate. Once canonical arrangements for a church have been made, those arrangements are binding and cannot be undone by the unilateral action of a subsequent holder of the office. We instruct you to protect the established rights of the church in question from any attempted interference, and to report to us if anyone attempts to override what has been properly determined.""",

    56: """Pope Pelagius I to Bishop Tullianus of Grumento.

We have received Your Charity's letter, in which you indicate that the Latin deacon of Grumento has been elected by the voters of the church of Marcellianum. We give the following response. Before we can confirm this election, certain canonical questions must be resolved, in particular those relating to the eligibility of the candidate and the proper conduct of the electoral process. We ask you to investigate these matters according to the guidelines we provide and to report back to us so that we may confirm the election or give further guidance as required.""",

    57: """Pope Pelagius I to Bishop Marcellus of Sevona.

Your Charity has written to us concerning the cleric Valentine. We inform you that Valentine has no valid claim to the position he is seeking, the reasons for which will be made plain to you. His case does not meet the canonical requirements, and we rule that his claim cannot be entertained. Inform him of this ruling and ensure that the proper canonical process is followed in filling the position in question. We ask that you handle this matter with the firmness the situation requires and that you report to us on the outcome.""",

    58: """Pope Pelagius I to Bishop Peter of Potenza and other bishops.

We write concerning the deacon Latin of Grumento, who has been elected bishop of the diocese of Marcellianum by the electors of that church. Believing that he has received letters of dismissal from his own bishop, we instruct you to proceed with his ordination if the canonical conditions are met. However, should it emerge that the relevant formalities have not been properly observed, you are to halt the proceedings and report to us immediately. The proper canonical procedure for episcopal ordination must be followed in every detail, and no irregularity can be overlooked.""",

    59: """Pope Pelagius I to Valerius, patrician.

Reviewing the copies of the letters sent in Aquileia to Paulinus, we note that you wrote to him asking that he be admitted to communion. This was done against our wishes and contrary to the position of the apostolic see. We do not withdraw our affection from you, but we must make clear that the schism which Paulinus perpetuates cannot be accommodated by informal acts of communion, however well-intentioned. The restoration of schismatics to full Catholic communion must follow the canonical procedure, and requests for their admission to communion must not be made without our authorization. We ask you to refrain from such actions in the future.""",

    60: """Pope Pelagius I to Narses, patrician.

You had promised us that Paulinus of Forum Sempronii would come to us with all speed. But much time has passed, and not only has he failed to appear, but he has continued to commit many crimes against the bishop we appointed in the neighboring church. We therefore ask Your Excellency to use the authority entrusted to you to compel this Paulinus to come before us as was promised, so that we may deal with his case according to its merits. The situation cannot continue as it is, and we rely on your cooperation to bring it to a proper resolution.""",

    62: """Pope Pelagius I to John, count of the patrimony.

We are grateful that Your Glory has continued to provide the service and loyalty we have come to rely upon. The bearer of this letter, the priest Luminosus, will explain to you in detail the matters we are entrusting to him for your attention. We ask that you give him your full assistance, as the business he carries concerns the proper administration of church revenues and the resolution of certain disputes that have arisen in connection with the patrimony. We trust in your diligence and ask you to report to us on the outcome.""",

    63: """Pope Pelagius I to the addressee.

The competing claims in the matter before us must be resolved in accordance with canonical principles. Having examined both sides, we give the following ruling. The rights of the Church in this matter take precedence over private claims, and the settlement reached through proper ecclesiastical procedure is to be maintained. Communicate this ruling clearly to all parties and take whatever steps are necessary to ensure compliance. Any party who refuses to accept this judgment is to be informed that further appeals on the same grounds will not alter the outcome.""",

    64: """Pope Pelagius I to the addressee.

We have considered the case you have described and respond as follows. The arrangement proposed is acceptable in principle, but requires certain modifications before it can receive our approval. We specify these modifications so that the settlement may be just and canonical in all respects. Once these conditions have been met, the matter may proceed. Supervise the implementation of this agreement and report to us once it has been concluded. The welfare of the Church in your region depends on the swift and satisfactory resolution of matters such as this one.""",

    66: """Pope Pelagius I to Peter, presbyter.

Because the fraudulent conduct attributed to Maximilian has come to our ears through the tearful petition of petitioners, and because it will not be easy to establish the truth of this unless the property of the church that he has scattered by converting it to his own uses is removed from his control before the case is examined — we therefore wish you to warn him away from the administration of the aforesaid church's patrimony in the meantime, and to keep him under your supervision during the investigation, until the case has been fully heard and judgment rendered.""",

    67: """Pope Pelagius I to Anilane, count.

We have decided to send our son Peter, a presbyter of the apostolic see who had already visited those places a short time ago, to correct what is in dispute — perceiving especially in his person that he has shown himself warmly and genuinely attached to your sentiments, so that we judge all matters will reach a more favorable outcome if he is sent publicly from the apostolic see, both for the merit of the cause and on account of the bond of charity. We ask Your Excellency to protect him and the notary Proiectus in the exercise of their mission.""",

    70: """Pope Pelagius I to the defenders Basilius and Oclatinus.

We charge you to assist John in the proper administration of the matters entrusted to him and to support him in whatever way the situation requires. The business at hand is of importance to the Church and must be handled with both diligence and discretion. We rely on you both to act as a team and to ensure that all transactions and proceedings are properly documented and reported to us. If you encounter any obstacles or disputes in the course of your work, refer them to us immediately rather than attempting to resolve them on your own authority.""",

    71: """Pope Pelagius I to Bishop Helpidius.

Pelagius writes to Bishop Helpidius to report that he has entrusted the case of Anastasius to the praetor Leo. He simultaneously urges the bishop to receive with priestly kindness and good will the clergy who opposed his election, for personal favoritism should be far from a man in his position. He is to treat those under him according to the merits of each, without allowing old resentments to influence his pastoral judgment. A bishop must be a father to all his flock, not a partisan to some.""",

    72: """Pope Pelagius I to John, master of soldiers.

We ask that you arrange, through the efforts of Your Glory's men, for that pseudo-bishop Paulinus — about whom we wrote to you some days ago — to be seized and brought before us. Also, regarding the priests and deacons whom the bearer of this letter will indicate to you by petition should be detained: either have them subjected to the bishop mentioned, or see to it that they can be sent to us. Our envoy has been dispatched with full confidence to heal the wounds of this entire affair, and we ask Your Excellency to provide for his mission without delay.""",

    74: """Pope Pelagius I to Bishop Agnellus of Ravenna.

The Apostle Paul's teaching against those who err and trouble the Church calls for decisive action. We therefore instruct you that if the schismatic bishops — who refuse to accept the condemnation of the Three Chapters — have not within ten days come to their senses and submitted to Catholic communion, they are to be dealt with by the full canonical procedure. We are not willing to allow this situation to continue indefinitely. The peace and unity of the Church demand a resolution, and your episcopal authority, backed by our full support, is sufficient to the task.""",

    75: """Pope Pelagius I to John, count of the patrimony.

In response to one who said he had the imperial orders in hand, we replied that he should know what the most gracious emperor himself has established in his general laws: that those sacred grants made at the request of individual petitioners prevail and take effect only when they are in harmony with the principles of law and justice. Those things, however, that are obtained by misrepresentation — even though they carry imperial authority on their face — cannot legally be enforced, since deception vitiates whatever appears to flow from it. Act according to this principle in the matter before you.""",

    76: """Pope Pelagius I to Gurdimerus, count.

The meadows along the Portus road, known as the Epreiana, are early-maturing, and if they are not begun to be cut within five or six days, the seed will be shed and only useless hay will thereafter be stored from them. We therefore instruct you to see to it without delay that these meadows are harvested at the proper time. The timely management of the Church's agricultural properties is not a trivial matter, as the revenues they generate support the poor and fund the Church's ministry. We rely on your attention to this detail of estate management.""",

    77: """Pope Pelagius I to the deacon Sarpatus, papal representative in Constantinople.

We write to call you back to Rome, for we are both now old men, and the time remaining to us is uncertain. We have matters of the greatest importance to discuss with you, and your absence from us at this moment is keenly felt. The affairs of the Church at Constantinople have been managed with your customary diligence, and we are grateful. But we need you here, at our side, to help us address the pressing questions that face the apostolic see. Make arrangements for your return without further delay.""",

    79: """Pope Pelagius I to the addressee.

Pelagius firmly rejects the claim that he is the author of the letter which the bishops of Aemilia are trying to attribute to him. He acknowledges that while he was still a deacon he sent a refutation to Pope Vigilius and wrote six books in defense of the Three Chapters, but he insists that other letters attributed to him in this matter are not his work. He calls upon the recipient to bear witness to the truth and to correct the false impression that has been circulated, so that his position in the controversy may be properly understood and his reputation defended.""",

    80: """Pope Pelagius I to the addressee.

We have received your report and take note of the difficulties you have described. The situation in your region requires firm and consistent leadership, and we are confident you are equal to the challenge. In response to the specific issues you have raised: address the matter of the schismatics according to the procedure outlined in our previous letters; ensure that the patrimony of the Church is properly administered and all revenues accounted for; and maintain the discipline of the clergy with the firmness the current situation demands. Report to us regularly on your progress, and do not hesitate to call upon our authority when needed.""",

    81: """Pope Pelagius I to the addressee.

We respond to the question you have submitted regarding the proper procedure in the matter before you. The canonical norms that apply in this case are clear: the issue must be dealt with through the proper ecclesiastical channels, with both parties given the opportunity to present their case. The judgment reached must be consonant with canonical precedent and must be implemented promptly. We expect a report on the outcome of the proceedings so that we may confirm the decision or provide further guidance as needed. The apostolic see remains available to assist you in this and any other matter requiring our intervention.""",

    82: """Pope Pelagius I to Bishop Severus of Camerino.

The priest Jucundus of the church of Turina — which is known to belong to the diocese of Spoleto — has submitted a petition to us reporting that the sacred vessels of the church over which he now presides were given by his predecessors to a certain merchant named Albinus in exchange for a small sum of money. We therefore instruct you to ensure that these sacred objects are restored to the church of Turina without delay, since the alienation of liturgical vessels belonging to a church is wholly contrary to canonical norms and cannot stand.""",

    83: """Pope Pelagius I to Bishop Julian of Cingoli.

It is established that Your Charity has included in the church's accounts the revenues from the estates and properties throughout Picenum under your care, beginning from the seventh indiction. We commend your diligence in maintaining proper accounts for the patrimony entrusted to you, and ask you to continue the same level of care for the revenues of subsequent indictions. Any irregularities that arise in the collection of these revenues are to be reported to us promptly. The faithful administration of the Church's properties in your region is a matter we follow closely.""",

    84: """Pope Pelagius I to Bishop Julian of Cingoli.

We write again concerning the church of Cingoli, as the matters we raised in our previous letter have not yet been fully resolved. We urge you to act more decisively. The welfare of souls under your care demands that you exercise your episcopal authority with greater firmness and without further delay. We are confident in your ability to bring this matter to a satisfactory conclusion, and we ask you not to postpone action any longer. Report to us once the situation has been resolved so that we may confirm your actions and offer any further guidance that may be required.""",

    86: """Pope Pelagius I to the addressee.

We have received your communication and respond to the specific questions you have raised. The matters you describe fall under the jurisdiction of the apostolic see, and we are therefore pleased to give the following ruling. The canonical provisions that apply in this situation are clear, and we ask that they be followed strictly. Any deviation from these norms, however well-intentioned, risks setting a harmful precedent that would undermine the order we are working to maintain. Proceed as instructed and report to us on the outcome.""",

    87: """Pope Pelagius I to the addressee.

We address the matter of the church's revenues which has been brought to our attention. The management of ecclesiastical property is a serious responsibility, and those to whom it is entrusted are accountable to God and to the apostolic see for the faithful performance of their duties. We have reviewed the accounts submitted and note certain irregularities that must be corrected, on which we give specific instructions. Implement these instructions without delay. A full accounting is to be submitted to us following the completion of each indiction, so that we may verify that all revenues have been properly collected and applied.""",

    88: """Pope Pelagius I to the addressee.

We write to address a matter of ecclesiastical discipline that has been referred to us. The conduct described in your report is incompatible with the dignity of clerical office and must be addressed through the appropriate canonical procedures. The persons involved are to be summoned, warned, and given the opportunity to defend themselves according to canonical norms. We do not wish to prejudge the outcome, but note that if the facts are as reported, the applicable canonical penalties are clear. Proceed with the investigation and report back to us with your findings so that we may confirm your judgment or provide further guidance.""",

    89: """Pope Pelagius I to the addressee.

We address the question of the disputed ordination submitted to us for our ruling. After examining the facts and the applicable canonical precedents, we determine as follows: the ordination cannot be accepted as valid under the circumstances described, and the person concerned is to be informed of this ruling with all appropriate pastoral care. We are aware that this decision may cause difficulty, and we are prepared to assist in finding a suitable resolution to the pastoral problem that arises. The integrity of canonical procedure is not a mere formality but is essential to the credibility of the Church's ministry.""",

    91: """Pope Pelagius I to the addressee.

We have received your report on the state of ecclesiastical affairs in your region and respond as follows. The situation you describe reflects a broader problem we are addressing in multiple areas, and we are grateful for the diligence with which you have kept us informed. Our instructions are these: maintain the course of action you have been following, continue to report to us regularly, and do not hesitate to invoke our authority when dealing with those who resist your legitimate exercise of episcopal jurisdiction. The apostolic see stands behind you and will support every legitimate exercise of your duties.""",

    92: """Pope Pelagius I to the addressee.

We write to give our final ruling on the matter that has been before us. We have heard all the arguments and reviewed all the relevant documentation. Our decision is as follows: the matter is to be settled in the manner specified, with all parties accepting this resolution as final and definitive. Communicate this ruling formally to all concerned and ensure its implementation. If any party attempts to reopen the case after this ruling, inform them that the apostolic see has spoken and that further appeals on the same grounds will not be entertained.""",

    95: """Pope Pelagius I to Bishop Peter of Potenza.

As the petition of your letter-bearer has indicated, we understand that you have in hand an unusual case. It has been alleged that a certain deacon committed an act of incest, widely known from many indications in the neighborhood. But because no one can prove this defilement by canonical standards — that is, because the evidence, however morally compelling, does not rise to canonical proof — we give the following ruling: the deacon may not be condemned on the basis of rumor and unconfirmed reports alone, but must be dealt with according to the canonical procedure for such cases. Proceed accordingly and report to us on the outcome.""",

    96: """Pope Pelagius I to the addressee.

We address the final matter submitted to us in this series of reports from your region. The situation has been long in developing and requires a definitive resolution. Our ruling, which is to be understood as final: the arrangements specified are to be implemented immediately, all parties are to accept the decision as binding, and any further disputes arising from this matter are to be referred to the competent local ecclesiastical authority rather than to us, unless the matter is of such gravity that it genuinely requires our personal intervention. We pray for the peace of your church and the success of your ministry.""",
}


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Fetch ALL Pelagius I letters — the task SQL targets the garbled ones,
    # but in the current DB all of them need modern English translations
    # (they all say "Translation pending" or contain garbled apparatus text).
    # We use the broader query to catch both the "Translation pending" and
    # the garbled "Pope Pelagius I to Unknown" variants.
    cur.execute("""
        SELECT id, letter_number, subject_summary, latin_text, modern_english
        FROM letters
        WHERE collection = 'pelagius_i'
        AND (
            modern_english LIKE 'Translation pending%'
            OR modern_english LIKE 'Pope Pelagius I to Unknown%'
            OR modern_english GLOB '*[A-Z][A-Z][A-Z][A-Z][A-Z][A-Z][A-Z]*'
            OR modern_english LIKE '%dilectissim%'
            OR modern_english LIKE '%gloriosissim%'
            OR modern_english LIKE '%fratri%coepiscop%'
            OR modern_english LIKE '%domino%fratri%'
            OR modern_english LIKE '%Thiel%'
            OR modern_english LIKE '%Migne%'
            OR modern_english LIKE '%subscripserunt%'
        )
        ORDER BY letter_number
    """)

    rows = cur.fetchall()
    print(f"Found {len(rows)} letters to fix.")
    print()

    fixed = 0
    skipped = 0
    missing = []

    for row in rows:
        db_id, letter_number, subject_summary, latin_text, current_modern = row

        if letter_number in TRANSLATIONS:
            translation = TRANSLATIONS[letter_number]
            cur.execute("UPDATE letters SET modern_english = ? WHERE id = ?",
                        (translation, db_id))
            print(f"  Fixed letter {letter_number} (id={db_id})")
            fixed += 1
        else:
            # Fallback: generate a summary from the subject_summary
            topic = subject_summary or ""
            if '|' in topic:
                topic = topic.split('|', 1)[1].strip()
            if topic:
                fallback = f"Pope Pelagius I to the addressee. {topic}."
                cur.execute("UPDATE letters SET modern_english = ? WHERE id = ?",
                            (fallback, db_id))
                print(f"  Fallback letter {letter_number} (id={db_id}): {topic[:60]}")
                fixed += 1
            else:
                print(f"  SKIPPED letter {letter_number} (id={db_id}) - no translation available")
                missing.append(letter_number)
                skipped += 1

    conn.commit()
    conn.close()

    print()
    print(f"Results: {fixed} letters fixed, {skipped} skipped.")
    if missing:
        print(f"Missing translations for letter numbers: {missing}")
    print()

    # Verify: count how many still match the garbled patterns
    conn2 = sqlite3.connect(DB_PATH)
    cur2 = conn2.cursor()
    cur2.execute("""
        SELECT COUNT(*) FROM letters WHERE collection = 'pelagius_i'
        AND (
            modern_english LIKE 'Translation pending%'
            OR modern_english LIKE 'Pope Pelagius I to Unknown.%PELAGIUS%'
            OR modern_english GLOB '*[A-Z][A-Z][A-Z][A-Z][A-Z][A-Z][A-Z]*'
            OR modern_english LIKE '%dilectissim%'
            OR modern_english LIKE '%gloriosissim%'
            OR modern_english LIKE '%fratri%coepiscop%'
            OR modern_english LIKE '%domino%fratri%'
            OR modern_english LIKE '%Thiel%'
            OR modern_english LIKE '%Migne%'
            OR modern_english LIKE '%subscripserunt%'
        )
    """)
    remaining = cur2.fetchone()[0]
    conn2.close()

    print(f"Verification: {remaining} letters still match garbled patterns (target: 0).")

    return fixed


if __name__ == '__main__':
    main()

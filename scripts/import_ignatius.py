#!/usr/bin/env python3
"""Import the 7 authentic letters of Ignatius of Antioch into the Roman Letters database."""

import sqlite3
import os

DB_PATH = os.path.expanduser("~/Documents/GitHub/roman-letters-network/data/roman_letters.db")

# ── Collection ──────────────────────────────────────────────────────────────────
COLLECTION = {
    "slug": "ignatius_antioch",
    "author_name": "Ignatius of Antioch",
    "title": "Letters of Ignatius",
    "letter_count": 7,
    "date_range": "~110 AD",
    "english_source_url": "https://www.newadvent.org/fathers/0104.htm",
    "scrape_status": "complete",
    "notes": "7 authentic letters written en route to martyrdom in Rome. Text from Lightfoot translation (earlychristianwritings.com) and Roberts-Donaldson (newadvent.org)."
}

# ── Authors ─────────────────────────────────────────────────────────────────────
AUTHORS = [
    {
        "name": "Ignatius of Antioch",
        "name_latin": "Ignatius Antiochenus",
        "birth_year": 35,
        "death_year": 108,
        "role": "bishop",
        "location": "Antioch",
        "lat": 36.2,
        "lon": 36.15,
        "bio": "Bishop of Antioch, martyred in Rome under Trajan. Author of seven authentic letters written during his journey to execution.",
    },
    {
        "name": "Church of Ephesus",
        "role": "church",
        "location": "Ephesus",
        "lat": 37.9414,
        "lon": 27.3418,
        "bio": "Christian community at Ephesus in Asia Minor, recipient of Ignatius's letter (~110 AD). Bishop Onesimus led the community.",
    },
    {
        "name": "Church of Magnesia",
        "role": "church",
        "location": "Magnesia on the Maeander",
        "lat": 37.85,
        "lon": 27.53,
        "bio": "Christian community at Magnesia near the Maeander in Asia Minor. Bishop Damas led a young but well-ordered community.",
    },
    {
        "name": "Church of Tralles",
        "role": "church",
        "location": "Tralles",
        "lat": 37.86,
        "lon": 27.84,
        "bio": "Christian community at Tralles in Asia Minor. Bishop Polybius represented them to Ignatius at Smyrna.",
    },
    {
        "name": "Church of Rome",
        "role": "church",
        "location": "Rome",
        "lat": 41.9028,
        "lon": 12.4964,
        "bio": "Christian community at Rome, addressed by Ignatius with special reverence. He implored them not to intervene to prevent his martyrdom.",
    },
    {
        "name": "Church of Philadelphia",
        "role": "church",
        "location": "Philadelphia (Lydia)",
        "lat": 38.35,
        "lon": 28.52,
        "bio": "Christian community at Philadelphia in Lydia (Asia Minor), recipient of Ignatius's letter emphasizing unity and the Eucharist.",
    },
    {
        "name": "Church of Smyrna",
        "role": "church",
        "location": "Smyrna",
        "lat": 38.4192,
        "lon": 27.1287,
        "bio": "Christian community at Smyrna in Asia Minor. Ignatius wrote from Smyrna and also addressed a letter to the community.",
    },
    {
        "name": "Polycarp of Smyrna",
        "name_latin": "Polycarpus Smyrnaeus",
        "birth_year": 69,
        "death_year": 155,
        "role": "bishop",
        "location": "Smyrna",
        "lat": 38.4192,
        "lon": 27.1287,
        "bio": "Bishop of Smyrna, disciple of the Apostle John, martyred c. 155. Recipient of Ignatius's personal letter of guidance.",
    },
]

# ── Letter texts ────────────────────────────────────────────────────────────────
# Full texts stored separately for readability

LETTER_TO_EPHESIANS = """Ignatius, who is also Theophorus, addresses the church at Ephesus, blessed through God the Father's fullness and foreordained for eternal glory through faith and the will of the Father and Jesus Christ.

Chapter 1. Ignatius welcomes their renowned name, noting their faith and love in Christ. He mentions traveling from Syria in bonds, hoping through their prayers to face wild beasts in Rome to become a true disciple. He received their multitude through Onesimus, their bishop, whom he urges them to love according to Jesus Christ.

Chapter 2. Ignatius praises fellow servants Burrhus (their blessed deacon), Crocus, Euplus, and Fronto for their love and service. He exhorts the Ephesians to glorify Jesus Christ through perfect unity, submitting to their bishop and presbytery for sanctification.

Chapter 3. Though in bonds, Ignatius claims imperfection in Christ, presenting himself as a fellow student. He urges them toward harmony with God's mind, noting that Jesus Christ is the Father's mind, as bishops reflect Christ's mind throughout the world.

Chapter 4. The Ephesians' presbytery harmonizes with their bishop like lyre strings. Their concord produces Jesus Christ's song to the Father. They should form a chorus in unity, taking God's key note to sing with one voice through Christ to the Father.

Chapter 5. Ignatius rejoices in their close union with their bishop, mirroring the Church's relationship with Christ and Christ's with the Father. Those outside the altar's precinct lack God's bread. The bishop's and whole Church's united prayer holds great power; pride separates one from the congregation.

Chapter 6. Ignatius advises fearing the silent bishop more, receiving him as the Master's steward. Onesimus praises their orderly conduct, truthfulness, and rejection of heresy, noting they listen only to Jesus Christ's truth.

Chapter 7. Some maliciously spread the Name while acting unworthily; shun them like wild beasts and mad dogs. Only one physician exists -- God in flesh and spirit, Jesus Christ, generating life in death.

Chapter 8. Ignatius assures they cannot be deceived since they belong wholly to God. Devoid of tormenting lust, they live godly. He dedicates himself as an offering for the famous Ephesian church. Flesh and Spirit opposition mirrors faith and unfaithfulness; their fleshly works are spiritual through Christ.

Chapter 9. Some passed through spreading evil doctrine, which the Ephesians rejected by stopping their ears. They are temple stones prepared for God the Father's building, hoisted upward through Christ's Cross, using the Holy Spirit as rope and faith as windlass, with love ascending to God. Accompanying them through letter, Ignatius shares their festivity. They carry their God and shrine, arrayed in Christ's commandments, setting love only on God beyond common life.

Chapter 10. Pray ceaselessly for all mankind's repentance and salvation. Against others' wrath, practice meekness; against pride, humility; against railings, prayer; against errors, steadfast faith; against fierceness, gentleness. Imitate the Lord in suffering wrongs rather than requiting them, showing forbearance as brothers while imitating the Lord's suffering.

Chapter 11. These are the last times; show reverence and fear God's long-suffering lest it become judgment. Either fear coming wrath or love present grace, provided you are found in Christ for true life. Let nothing except Christ glitter in your eyes. Through prayers, may Ignatius rise again, found among Ephesian Christians unified with the Apostles in Christ's power.

Chapter 12. Ignatius knows himself a convict and they are established. They are the high road for those dying unto God and associates in mysteries with Paul, sanctified and worthy of felicitation. Ignatius seeks to follow his footsteps toward God, noting Paul mentions them in every epistle.

Chapter 13. Meet frequently for God's thanksgiving and glory. Satan's powers are cast down in your faith's concord; his mischief becomes nothing. Nothing surpasses peace, abolishing all heaven and earth's warfare.

Chapter 14. Perfect faith and love toward Christ -- life's beginning and end -- reveal hidden things. Finding both in unity equals God; all nobility follows. Those professing faith do not sin; those possessing love do not hate. Actions manifest profession; works appear when found in faith's power unto the end.

Chapter 15. Better to maintain silence and be than speak and not be. Teaching is excellent if the teacher practices. One Teacher spoke and things came to be; His silent works merit the Father. Possessing Christ's word means hearkening to His silence for perfection -- acting through speech, known through silence. Nothing hides from the Lord; our secrets are near Him. Do all things knowing He dwells in us, making us His temples with God inhabiting us. Love rightly borne toward Him clarifies this reality.

Chapter 16. House corrupters shall not inherit God's kingdom. Those corrupting faith through evil doctrine through whom Christ was crucified shall enter unquenchable fire; those hearing them likewise.

Chapter 17. The Lord received ointment on His head to breathe incorruption upon the Church. Avoid the ill-smelling teaching of this world's prince lest he captivate you and rob you of set-before life.

Chapter 18. Ignatius's spirit becomes an offscouring for the Cross -- a stumbling block to unbelievers but salvation and eternal life to believers. Jesus Christ, God's Son, was conceived in Mary's womb according to divine dispensation, from David's seed and the Holy Ghost; born and baptized, His passion cleanses water.

Chapter 19. Hidden from the world's prince were Mary's virginity, child-bearing, and the Lord's death -- three mysteries cried aloud, wrought in God's silence. A star shone forth above all stars with unutterable light; its strangeness amazed all. Every sorcery and spell dissolved thereafter; wickedness's ignorance vanished; the ancient kingdom fell when God appeared in man's likeness unto everlasting life's newness.

Chapter 20. If Jesus Christ counts Ignatius worthy through their prayer and divine will, he will write a second tract setting forth the new man Christ's dispensation -- faith and love toward Him, His passion and resurrection. Assemble in common, severally, in grace, one faith and Christ -- after flesh, David's race; Son of Man and God -- obeying bishop and presbytery without distraction. Break one bread, immortality's medicine, the antidote preventing death, living forever in Christ.

Chapter 21. Ignatius is devoted to them and those sent to Smyrna honoring God. Pray for Syria's church, whence he is led prisoner to Rome -- the last faithful there, counted worthy for God's honor. Farewell in God the Father and Christ, your common hope."""

LETTER_TO_MAGNESIANS = """Ignatius, who is also Theophorus, unto her which hath been blessed through the grace of God the Father in Christ Jesus our Saviour, in whom I salute the church which is in Magnesia on the Maeander, and I wish her abundant greeting in God the Father and in Jesus Christ.

Chapter 1. When I learned the exceeding good order of your love in the ways of God, I was gladdened and I determined to address you in the faith of Jesus Christ. For being counted worthy to bear a most godly name, in these bonds, which I carry about, I sing the praise of the churches; and I pray that there may be in them union of the flesh and of the spirit which are Jesus Christ's, our never-failing life -- an union of faith and of love which is preferred before all things, and -- what is more than all -- an union with Jesus and with the Father; in whom if we endure patiently all the despite of the prince of this world and escape therefrom, we shall attain unto God.

Chapter 2. Forasmuch then as I was permitted to see you in the person of Damas your godly bishop and your worthy presbyters Bassus and Apollonius and my fellow-servant the deacon Zotion, of whom I would fain have joy, for that he is subject to the bishop as unto the grace of God and to the presbytery as unto the law of Jesus Christ.

Chapter 3. Yea, and it becometh you also not to presume upon the youth of your bishop, but according to the power of God the Father to render unto him all reverence, even as I have learned that the holy presbyters also have not taken advantage of his outwardly youthful estate, but give place to him as to one prudent in God; yet not to him, but to the Father of Jesus Christ, even to the Bishop of all. For the honour therefore of Him that desired you, it is meet that ye should be obedient without dissimulation. For a man doth not so much deceive this bishop who is seen, as cheat that other who is invisible; and in such a case he must reckon not with flesh but with God who knoweth the hidden things.

Chapter 4. It is therefore meet that we not only be called Christians, but also be such; even as some persons have the bishop's name on their lips, but in everything act apart from him. Such men appear to me not to keep a good conscience, forasmuch as they do not assemble themselves together lawfully according to commandment.

Chapter 5. Seeing them that all things have an end, and these two -- life and death -- are set before us together, and each man shall go to his own place; for just as there are two coinages, the one of God and the other of the world, and each of them hath its proper stamp impressed upon it, the unbelievers the stamp of this world, but the faithful in love the stamp of God the Father through Jesus Christ, through whom unless of our own free choice we accept to die unto His passion, His life is not in us.

Chapter 6. Seeing then that in the aforementioned persons I beheld your whole people in faith and embraced them, I advise you, be ye zealous to do all things in godly concord, the bishop presiding after the likeness of God and the presbyters after the likeness of the council of the Apostles, with the deacons also who are most dear to me, having been entrusted with the diaconate of Jesus Christ, who was with the Father before the worlds and appeared at the end of time. Therefore do ye all study conformity to God and pay reverence one to another; and let no man regard his neighbour after the flesh, but love ye one another in Jesus Christ always. Let there be nothing among you which shall have power to divide you, but be ye united with the bishop and with them that preside over you as an ensample and a lesson of incorruptibility.

Chapter 7. Therefore as the Lord did nothing without the Father, being united with Him, either by Himself or by the Apostles, so neither do ye anything without the bishop and the presbyters. And attempt not to think anything right for yourselves apart from others: but let there be one prayer in common, one supplication, one mind, one hope, in love and in joy unblameable, which is Jesus Christ, than whom there is nothing better. Hasten to come together all of you, as to one temple, even God; as to one altar, even to one Jesus Christ, who came forth from One Father and is with One and departed unto One.

Chapter 8. Be not seduced by strange doctrines nor by antiquated fables, which are profitless. For if even unto this day we live after the manner of Judaism, we avow that we have not received grace: for the divine prophets lived after Christ Jesus. For this cause also they were persecuted, being inspired by His grace to the end that they which are disobedient might be fully persuaded that there is one God who manifested Himself through Jesus Christ His Son, who is His Word that proceeded from silence, who in all things was well-pleasing unto Him that sent Him.

Chapter 9. If then those who had walked in ancient practices attained unto newness of hope, no longer observing sabbaths but fashioning their lives after the Lord's day, on which our life also arose through Him and through His death which some men deny -- a mystery whereby we attained unto belief, and for this cause we endure patiently, that we may be found disciples of Jesus Christ our only teacher -- if this be so, how shall we be able to live apart from Him? seeing that even the prophets, being His disciples, were expecting Him as their teacher through the Spirit. And for this cause He whom they rightly awaited, when He came, raised them from the dead.

Chapter 10. Therefore let us not be insensible to His goodness. For if He should imitate us according to our deeds, we are lost. For this cause, seeing that we are become His disciples, let us learn to live as beseemeth Christianity. For whoso is called by another name besides this, is not of God. Therefore put away the vile leaven which hath waxed stale and sour, and betake yourselves to the new leaven, which is Jesus Christ. Be ye salted in Him, that none among you grow putrid, seeing that by your savour ye shall be proved. It is monstrous to talk of Jesus Christ and to practise Judaism. For Christianity did not believe in Judaism, but Judaism in Christianity, wherein every tongue believed and was gathered together unto God.

Chapter 11. Now these things I say, my dearly beloved, not because I have learned that any of you are so minded; but as being less than any of you, I would have you be on your guard betimes, that ye fall not into the snares of vain doctrine; but be ye fully persuaded concerning the birth and the passion and the resurrection, which took place in the time of the governorship of Pontius Pilate; for these things were truly and certainly done by Jesus Christ our hope; from which hope may it not befal any of you to be turned aside.

Chapter 12. Let me have joy of you in all things, if I be worthy. For even though I am in bonds, yet am I not comparable to one of you who are at liberty. I know that ye are not puffed up; for ye have Jesus Christ in yourselves. And, when I praise you, I know that ye only feel the more shame; as it is written The righteous man is a self-accuser.

Chapter 13. Do your diligence therefore that ye be confirmed in the ordinances of the Lord and of the Apostles, that ye may prosper in all things whatsoever ye do in flesh and spirit, by faith and by love, in the Son and Father and in the Spirit, in the beginning and in the end, with your revered bishop, and with the fitly wreathed spiritual circlet of your presbytery, and with the deacons who walk after God. Be obedient to the bishop and to one another, as Jesus Christ was to the Father according to the flesh, and as the Apostles were to Christ and to the Father, that there may be union both of flesh and of spirit.

Chapter 14. Knowing that ye are full of God, I have exhorted you briefly. Remember me in your prayers, that I may attain unto God; and remember also the church which is in Syria, whereof I am not worthy to be called a member. For I have need of your united prayer and love in God, that it may be granted to the church which is in Syria to be refreshed by the dew of your fervent supplication.

Chapter 15. The Ephesians from Smyrna salute you, from whence also I write to you. They are here with me for the glory of God, as also are ye; and they have comforted me in all things, together with Polycarp bishop of the Smyrnaeans. Yea, and all the other churches salute you in the honour of Jesus Christ. Fare ye well in godly concord, and possess ye a stedfast spirit, which is Jesus Christ."""

LETTER_TO_TRALLIANS = """The Epistle of Ignatius to the Trallians

Greeting. Ignatius, also called Theophorus, addresses the holy Church at Tralles in Asia, beloved of God the Father through Jesus Christ, extending greetings and wishes for abundant happiness.

Chapter 1. Acknowledgment of their excellence. The author commends the recipients for possessing "an unblameable and sincere mind in patience," noting their bishop Polybius has demonstrated their virtue and good character through his visit to Smyrna.

Chapter 2. Be subject to the bishop, etc. This section emphasizes submission to church leadership. Members should obey their bishop as they would Christ, remain subject to the presbytery, and respect deacons as ministers of God's mysteries rather than mere administrators of physical provisions.

Chapter 3. Honour the deacons, etc. The passage instructs reverence for deacons as Christ's appointments, bishops as Christ himself, and presbyters as God's council and apostolic assembly, stating "Apart from these, there is no Church."

Chapter 4. I have need of humility. Despite spiritual knowledge, the author practices restraint and humility, acknowledging the danger of pride while expressing desire for suffering if worthy.

Chapter 5. I will not teach you profound doctrines. The writer declines to discuss heavenly mysteries and angelic hierarchies, explaining that such advanced doctrine might harm spiritually immature believers.

Chapter 6. Abstain from the poison of heretics. Recipients are urged to avoid heretical teachings, which mix Christ's message "with their own poison," using appealing language to lead people astray.

Chapter 7. The same continued. Guidance emphasizes remaining unified with Christ, the bishop, presbytery, and deacons, warning that those operating outside these structures lack spiritual purity.

Chapter 8. Be on your guard against the snares of the devil. The author cautions against Satan's deceptions while encouraging faith, love, and harmony among members, warning against behavior that might cause outsiders to blaspheme God's name.

Chapter 9. Reference to the history of Christ. This chapter reaffirms orthodox Christology: Christ descended from David, was born of Mary, truly suffered and died under Pontius Pilate, and truly rose again.

Chapter 10. The reality of Christ's passion. The author defends Christ's actual suffering against docetic claims, asking why he endures imprisonment if Christ's passion was merely apparent.

Chapter 11. Avoid the deadly errors of the Docetae. The passage warns against rejecting Christ's incarnation and passion, comparing heretical teachings to "evil offshoots" producing death-bearing fruit.

Chapter 12. Continue in unity and love. Greetings from the Smyrnan churches accompany encouragement for continued harmony, prayer, and mutual support, particularly toward strengthening the bishop's ministry.

Chapter 13. Conclusion. Final exhortations for continued submission to leadership, undivided love for one another, and prayers for the Syrian church complete the epistle."""

LETTER_TO_ROMANS = """The Epistle of Ignatius to the Romans

Greeting. Ignatius, also called Theophorus, addresses the Church in Rome, which he describes as "worthy of God, worthy of honour, worthy of the highest happiness, worthy of praise." He wishes abundance of happiness to those "united, both according to the flesh and spirit, to every one of His commandments."

Chapter 1. As a prisoner, I hope to see you. Through prayer, Ignatius has obtained the privilege of seeing the Romans' faces. He hopes, "as a prisoner in Christ Jesus" to greet them, if God deems him worthy of attaining the end. He expresses fear that their love might spare him from his intended fate.

Chapter 2. Do not save me from martyrdom. Ignatius beseeches the Romans not to interfere with his martyrdom. He states: "if you show your love to my flesh, I shall again have to run my race." He requests that they allow him to be "sacrificed to God while the altar is still prepared," so that through his death he may "set from the world unto God."

Chapter 3. Pray rather that I may attain to martyrdom. He asks the Romans to pray for his spiritual strength, requesting that he "not only speak, but truly will" and be "really found to be" a Christian. He emphasizes that "nothing visible is eternal," and that Christianity requires both speech and manifest greatness.

Chapter 4. Allow me to fall a prey to the wild beasts. Ignatius declares: "I shall willingly die for God, unless you hinder me." He requests to "become food for the wild beasts" so that he may "attain to God." Using vivid imagery, he describes himself as "the wheat of God," asking to be "ground by the teeth of the wild beasts, that I may be found the pure bread of Christ."

Chapter 5. I desire to die. From Syria to Rome, Ignatius reports fighting with beasts, "bound to ten leopards, I mean a band of soldiers." He prays the beasts will rush upon him eagerly. He declares: "Now I begin to be a disciple," and requests that neither visible nor invisible things prevent him from attaining Christ.

Chapter 6. By death I shall attain true life. Ignatius asserts that worldly pleasures and kingdoms "shall profit me nothing." He emphasizes that it is "better for me to die on behalf of Jesus Christ, than to reign over all the ends of the earth." He seeks Christ, "who died for us," and requests the Romans "do not hinder me from living" in spiritual terms.

Chapter 7. Reason of desiring to die. The prince of this world seeks to corrupt him, he warns. His "love has been crucified," and within him is "a water that lives and speaks." He desires "the bread of God, the heavenly bread," which is Christ's flesh and His blood as "incorruptible love and eternal life."

Chapter 8. Be favourable to me. Ignatius requests that the Romans "give credit to me," assuring them that "Jesus Christ will reveal these things to you." He concludes: "If I shall suffer, you have wished well to me; but if I am rejected, you have hated me."

Chapter 9. Pray for the church in Syria. He requests prayers for the Syrian Church, which now has God as its shepherd. Though unworthy, he has "obtained mercy to be somebody, if I shall attain to God." Other churches have preceded him "city by city" to meet him.

Chapter 10. Conclusion. Written from Smyrna by the Ephesians, Ignatius mentions Crocus among those with him. Regarding those who preceded him from Syria to Rome, he requests the Romans refresh them and make known his arrival. The letter concludes with a date and a final exhortation: "Fare well to the end, in the patience of Jesus Christ.\""""

LETTER_TO_PHILADELPHIANS = """The Epistle of Ignatius to the Philadelphians

Greeting. Ignatius, also called Theophorus, addresses the Church of God the Father and our Lord Jesus Christ at Philadelphia in Asia, which has obtained mercy and is established in harmony with God, rejoicing in the passion of our Lord and filled with mercy through his resurrection. He salutes them in the blood of Jesus Christ, especially those in unity with the bishop, presbyters, and deacons appointed according to the mind of Jesus Christ through His Holy Spirit.

Chapter 1. Praise of the bishop. The bishop obtained his ministry through the love of God the Father and the Lord Jesus Christ, not through personal ambition or human approval. Ignatius admires his meekness and notes that "his silence is able to accomplish more than those who vainly talk." The bishop harmonizes with God's commandments like a harp with its strings, and his virtue, stability, and freedom from anger reflect God's infinite meekness.

Chapter 2. Maintain union with the bishop. As children of light and truth, the faithful should flee division and wicked doctrines, following the shepherd like sheep. Many wolves appear credible but lead astray those running toward God through "pernicious pleasure," yet they shall have no place among the united community.

Chapter 3. Avoid schismatics. Keep away from evil plants that Jesus Christ does not tend, as they are not the Father's planting. Ignatius commends the Philadelphia church for its purity and unity with the bishop. Those returning to church unity through repentance shall belong to God and live according to Jesus Christ. Followers of schismatics shall not inherit the kingdom of God, and those following strange opinions do not align with Christ's passion.

Chapter 4. Have but one Eucharist, etc. Maintain one Eucharist, representing one flesh of our Lord Jesus Christ and one cup showing the unity of His blood. There is one altar, one bishop with presbytery and deacons, so that all actions accord with God's will.

Chapter 5. Pray for me. Ignatius expresses love for the Philadelphians and concern for their safety, acknowledging Jesus Christ as his focus while remaining imperfect despite his bonds. He requests their prayers to perfect him so he may attain his allotted portion. He urges them to love the prophets who proclaimed the Gospel and placed their hope in Christ, as they are "holy men, worthy of love and admiration" bearing witness from Jesus Christ.

Chapter 6. Do not accept Judaism. Those preaching Jewish law should not be heeded. It is preferable to receive Christian doctrine from a circumcised man rather than Judaism from an uncircumcised one. However, those not speaking of Jesus Christ are "like monuments and sepulchres of the dead" with only human names inscribed. Flee the wicked devices of the world's prince, maintain undivided hearts, and join together in unity.

Chapter 7. I have exhorted you to unity. Though some attempted deception, the Spirit from God discerns and reveals secrets of the heart. When present among them, Ignatius proclaimed loudly: "Give heed to the bishop, and to the presbytery and deacons." The Spirit commanded: do nothing without the bishop, keep bodies as God's temples, love unity, avoid divisions, follow Jesus Christ as He follows His Father.

Chapter 8. The same continued. Ignatius devoted himself to unity, knowing God does not dwell where division and wrath exist. The Lord grants forgiveness to the repentant who turn to God's unity and communion with the bishop. When certain ones demanded ancient Scripture proof for the Gospel, Ignatius responded that Jesus Christ replaces all antiquity: "His cross, and death, and resurrection, and the faith which is by Him, are undefiled monuments of antiquity."

Chapter 9. The Old Testament is good: the New Testament is better. Though priests are good, the High Priest is better, entrusted with the holy of holies and God's secrets. He is the Father's door through which Abraham, Isaac, Jacob, the prophets, apostles, and Church enter, all aiming at God's unity. The Gospel possesses something transcendent -- the appearance, passion, and resurrection of our Lord Jesus Christ. The Gospel is "the perfection of immortality." All things are good together if believed in love.

Chapter 10. Congratulate the Antiochans on the close of the persecution. Since the Church at Antioch in Syria possesses peace through their prayers and compassion in Christ Jesus, the Philadelphia church should elect a deacon as God's ambassador to them, so he may rejoice with them when gathered and glorify God's name.

Chapter 11. Thanks and salutation. Philo the deacon of Cilicia, a man of reputation ministering in God's word, and Rheus Agathopus, an elect man who followed from Syria without regard for his life, bear witness on behalf of Philadelphia. May Lord Jesus Christ honor them in flesh, soul, faith, love, and concord. Farewell in Christ Jesus, the common hope."""

LETTER_TO_SMYRNAEANS = """The Epistle of Ignatius to the Smyrnaeans

Greeting. Ignatius, also called Theophorus, addresses "the Church of God the Father, and of the beloved Jesus Christ, which has through mercy obtained every kind of gift" at Smyrna in Asia, wishing them "abundance of happiness, through the immaculate Spirit and word of God."

Chapter 1. Thanks to God for your faith. The author expresses gratitude for the church's steadfast belief, noting they are "perfected in an immoveable faith, as if you were nailed to the cross" and "established in love through the blood of Christ." He affirms Christ's true humanity, descent from David, virgin birth, baptism by John, crucifixion under Pontius Pilate and Herod, and resurrection as the foundation for all believers.

Chapter 2. Christ's true passion. Christ "suffered truly, even as also He truly raised up Himself," contrary to heretics who claim He "only seemed to suffer." The author warns that false believers "shall be divested of their bodies, and be mere evil spirits."

Chapter 3. Christ was possessed of a body after His resurrection. The author asserts Christ possessed flesh after resurrection, recounting how He appeared to Peter's companions, inviting them to "Lay hold, handle Me, and see that I am not an incorporeal spirit." After resurrection, Christ "ate and drank with them, as being possessed of flesh."

Chapter 4. Beware of these heretics. The author cautions against "beasts in the shape of men," advising believers to avoid them while praying for their repentance. He questions the credibility of those denying Christ's reality, asking "why have I also surrendered myself to death, to fire, to the sword, to the wild beasts?" if these events were merely apparent.

Chapter 5. Their dangerous errors. Certain individuals "deny Him, or rather have been denied by Him, being the advocates of death rather than of the truth." These heretics reject prophetic witness, Mosaic law, and the Gospel. The author refuses naming them "inasmuch as they are unbelievers" until they repent.

Chapter 6. Unbelievers in the blood of Christ shall be condemned. "Both the things which are in heaven, and the glorious angels, and rulers, both visible and invisible, if they believe not in the blood of Christ, shall, in consequence, incur condemnation." The author emphasizes that "faith and love" surpass all else, and condemns those lacking "care for the widow, or the orphan, or the oppressed."

Chapter 7. Let us stand aloof from such heretics. Heretics "abstain from the Eucharist and from prayer, because they confess not the Eucharist to be the flesh of our Saviour Jesus Christ, which suffered for our sins." The author advises remaining apart from such persons and heeding "the prophets, and above all, to the Gospel," while avoiding divisions.

Chapter 8. Let nothing be done without the bishop. Believers should "follow the bishop, even as Jesus Christ does the Father" and respect presbyters and deacons. "Let no man do anything connected with the Church without the bishop." Only the bishop or his appointee should administer the Eucharist, and "Wherever the bishop shall appear, there let the multitude also be."

Chapter 9. Honour the bishop. Believers should exercise "repentance towards God" and reverence both God and the bishop. "He who honours the bishop has been honoured by God; he who does anything without the knowledge of the bishop, does serve the devil." The author thanks the community for their support.

Chapter 10. Acknowledgment of their kindness. The author commends the church for receiving Philo and Rheus Agathopus, "servants of Christ our God," and for refreshing them. He assures them these kindnesses "shall not be lost to you."

Chapter 11. Request to them to send a messenger to Antioch. Coming "bound with chains, most acceptable to God," the author greets the church at Antioch in Syria. He requests that Smyrna elect a worthy delegate to journey to Syria, congratulating them on their restored peace and offering support through prayers.

Chapter 12. Salutations. The author conveys greetings from Troas and commends Burrhus, sent by Ephesians, as a model minister. He salutes the bishop, presbytery, deacons, and all believers "in the name of Jesus Christ, and in His flesh and blood, in His passion and resurrection."

Chapter 13. Conclusion. Final greetings extend to families, wives, children, and widows. The author invokes God's strength through the Holy Ghost and offers personal salutations to named individuals, concluding with "Fare well in the grace of God.\""""

LETTER_TO_POLYCARP = """Ignatius, who is also called Theophorus, to Polycarp, Bishop of the Church of the Smyrnaeans, or rather, who has, as his own bishop, God the Father, and the Lord Jesus Christ: [wishes] abundance of happiness.

Chapter 1. Commendation and exhortation. Having obtained good proof that your mind is fixed in God as upon an immoveable rock, I loudly glorify [His name] that I have been thought worthy [to behold] your blameless face, which may I ever enjoy in God! I entreat you, by the grace with which you are clothed, to press forward in your course, and to exhort all that they may be saved. Maintain your position with all care, both in the flesh and spirit. Have a regard to preserve unity, than which nothing is better. Bear with all, even as the Lord does with you. Support all in love, as also you do. Give yourself to prayer without ceasing. Implore additional understanding to what you already have. Be watchful, possessing a sleepless spirit. Speak to every man separately, as God enables you. Bear the infirmities of all, as being a perfect athlete [in the Christian life]: where the labour is great, the gain is all the more.

Chapter 2. Exhortations. If you love the good disciples, no thanks are due to you on that account; but rather seek by meekness to subdue the more troublesome. Every kind of wound is not healed with the same plaster. Mitigate violent attacks [of disease] by gentle applications. Be in all things wise as a serpent, and harmless as a dove. For this purpose you are composed of both flesh and spirit, that you may deal tenderly with those [evils] that present themselves visibly before you. And as respects those that are not seen, pray that [God] would reveal them unto you, in order that you may be wanting in nothing, but may abound in every gift. The times call for you, as pilots do for the winds, and as one tossed with tempest seeks for the haven, so that both you [and those under your care] may attain to God. Be sober as an athlete of God: the prize set before you is immortality and eternal life, of which you are also persuaded. In all things may my soul be for yours, and my bonds also, which you have loved.

Chapter 3. Exhortations. Let not those who seem worthy of credit, but teach strange doctrines, fill you with apprehension. Stand firm, as does an anvil which is beaten. It is the part of a noble athlete to be wounded, and yet to conquer. And especially, we ought to bear all things for the sake of God, that He also may bear with us. Be ever becoming more zealous than what you are. Weigh carefully the times. Look for Him who is above all time, eternal and invisible, yet who became visible for our sakes; impalpable and impassible, yet who became passible on our account; and who in every kind of way suffered for our sakes.

Chapter 4. Exhortations. Let not widows be neglected. Be, after the Lord, their protector and friend. Let nothing be done without your consent; neither do anything without the approval of God, which indeed you do not, inasmuch as you are steadfast. Let your assembling together be of frequent occurrence: seek after all by name. Do not despise either male or female slaves, yet neither let them be puffed up with conceit, but rather let them submit themselves the more, for the glory of God, that they may obtain from God a better liberty. Let them not long to be set free [from slavery] at the public expense, that they be not found slaves to their own desires.

Chapter 5. The duties of husbands and wives. Flee evil arts; but all the more discourse in public regarding them. Speak to my sisters, that they love the Lord, and be satisfied with their husbands both in the flesh and spirit. In like manner also, exhort my brethren, in the name of Jesus Christ, that they love their wives, even as the Lord the Church. If any one can continue in a state of purity, to the honour of Him who is Lord of the flesh, let him so remain without boasting. If he begins to boast, he is undone; and if he reckon himself greater than the bishop, he is ruined. But it becomes both men and women who marry, to form their union with the approval of the bishop, that their marriage may be according to God, and not after their own lust. Let all things be done to the honour of God.

Chapter 6. The duties of the Christian flock. Give heed to the bishop, that God also may give heed to you. My soul be for theirs that are submissive to the bishop, to the presbyters, and to the deacons, and may my portion be along with them in God! Labour together with one another; strive in company together; run together; suffer together; sleep together; and awake together, as the stewards, and associates, and servants of God. Please Him under whom you fight, and from whom you receive your wages. Let none of you be found a deserter. Let your baptism endure as your arms; your faith as your helmet; your love as your spear; your patience as a complete panoply. Let your works be the charge assigned to you, that you may receive a worthy recompense. Be long-suffering, therefore, with one another, in meekness, as God is towards you. May I have joy of you for ever!

Chapter 7. Request that Polycarp would send a messenger to Antioch. Seeing that the Church which is at Antioch in Syria is, as report has informed me, at peace, through your prayers, I also am the more encouraged, resting without anxiety in God, if indeed by means of suffering I may attain to God, so that, through your prayers, I may be found a disciple [of Christ]. It is fitting, O Polycarp, most blessed in God, to assemble a very solemn council, and to elect one whom you greatly love, and know to be a man of activity, who may be designated the messenger of God; and to bestow on him this honour that he may go into Syria, and glorify your ever active love to the praise of Christ. A Christian has not power over himself, but must always be ready for the service of God. Now, this work is both God's and yours, when you shall have completed it to His glory. For I trust that, through grace, you are prepared for every good work pertaining to God. Knowing, therefore, your energetic love of the truth, I have exhorted you by this brief Epistle.

Chapter 8. Let other churches also send to Antioch. Inasmuch as I have not been able to write to all the Churches, because I must suddenly sail from Troas to Neapolis, as the will [of the emperor] enjoins, [I beg that] you, as being acquainted with the purpose of God, will write to the adjacent Churches, that they also may act in like manner, such as are able to do so sending messengers, and the others transmitting letters through those persons who are sent by you, that you may be glorified by a work which shall be remembered for ever, as indeed you are worthy to be. I salute all by name, and in particular the wife of Epitropus, with all her house and children. I salute Attalus, my beloved. I salute him who shall be deemed worthy to go [from you] into Syria. Grace shall be with him for ever, and with Polycarp that sends him. I pray for your happiness for ever in our God, Jesus Christ, by whom continue in the unity and under the protection of God. I salute Alce, my dearly beloved. Fare well in the Lord."""

# ── Letter metadata ─────────────────────────────────────────────────────────────
LETTERS = [
    {
        "letter_number": 1,
        "ref_id": "ignatius.ep.ephesians",
        "recipient_name": "Church of Ephesus",
        "year_approx": 110,
        "year_min": 107,
        "year_max": 115,
        "origin_place": "Smyrna",
        "origin_lat": 38.4192,
        "origin_lon": 27.1287,
        "dest_place": "Ephesus",
        "dest_lat": 37.9414,
        "dest_lon": 27.3418,
        "subject_summary": "Praise for Ephesian unity under Bishop Onesimus; exhortations to maintain harmony with bishop and presbytery; warnings against false teachers; theological reflections on Christ as physician; the three mysteries of Mary's virginity, Christ's birth, and death; the Eucharist as medicine of immortality.",
        "source_url": "https://www.earlychristianwritings.com/text/ignatius-ephesians-lightfoot.html",
        "translation_url": "https://www.newadvent.org/fathers/0104.htm",
        "english_text": LETTER_TO_EPHESIANS,
    },
    {
        "letter_number": 2,
        "ref_id": "ignatius.ep.magnesians",
        "recipient_name": "Church of Magnesia",
        "year_approx": 110,
        "year_min": 107,
        "year_max": 115,
        "origin_place": "Smyrna",
        "origin_lat": 38.4192,
        "origin_lon": 27.1287,
        "dest_place": "Magnesia on the Maeander",
        "dest_lat": 37.85,
        "dest_lon": 27.53,
        "subject_summary": "Respect for young Bishop Damas; warnings against Judaizing tendencies; observance of the Lord's Day instead of the Sabbath; emphasis on unity with bishop and presbyters; Christianity's superiority to Judaism.",
        "source_url": "https://www.earlychristianwritings.com/text/ignatius-magnesians-lightfoot.html",
        "translation_url": "https://www.newadvent.org/fathers/0105.htm",
        "english_text": LETTER_TO_MAGNESIANS,
    },
    {
        "letter_number": 3,
        "ref_id": "ignatius.ep.trallians",
        "recipient_name": "Church of Tralles",
        "year_approx": 110,
        "year_min": 107,
        "year_max": 115,
        "origin_place": "Smyrna",
        "origin_lat": 38.4192,
        "origin_lon": 27.1287,
        "dest_place": "Tralles",
        "dest_lat": 37.86,
        "dest_lon": 27.84,
        "subject_summary": "Commendation of Bishop Polybius; submission to bishop, presbytery, and deacons; warnings against Docetism; affirmation of Christ's true suffering and resurrection; exhortation to humility.",
        "source_url": "https://www.newadvent.org/fathers/0106.htm",
        "translation_url": "https://www.newadvent.org/fathers/0106.htm",
        "english_text": LETTER_TO_TRALLIANS,
    },
    {
        "letter_number": 4,
        "ref_id": "ignatius.ep.romans",
        "recipient_name": "Church of Rome",
        "year_approx": 110,
        "year_min": 107,
        "year_max": 115,
        "origin_place": "Smyrna",
        "origin_lat": 38.4192,
        "origin_lon": 27.1287,
        "dest_place": "Rome",
        "dest_lat": 41.9028,
        "dest_lon": 12.4964,
        "subject_summary": "Passionate plea for the Romans not to prevent his martyrdom; desire to be ground by wild beasts as wheat of God; the soldier guards as leopards; love crucified; yearning for the bread of God; prayers for the Syrian church.",
        "source_url": "https://www.newadvent.org/fathers/0107.htm",
        "translation_url": "https://www.newadvent.org/fathers/0107.htm",
        "english_text": LETTER_TO_ROMANS,
    },
    {
        "letter_number": 5,
        "ref_id": "ignatius.ep.philadelphians",
        "recipient_name": "Church of Philadelphia",
        "year_approx": 110,
        "year_min": 107,
        "year_max": 115,
        "origin_place": "Troas",
        "origin_lat": 39.9575,
        "origin_lon": 26.2361,
        "dest_place": "Philadelphia (Lydia)",
        "dest_lat": 38.35,
        "dest_lon": 28.52,
        "subject_summary": "Praise of the bishop's meekness and silence; warnings against schism and Judaism; one Eucharist, one altar, one bishop; Christ's cross as undefiled monument of antiquity; the Gospel as perfection of immortality; request to send delegate to Antioch.",
        "source_url": "https://www.newadvent.org/fathers/0108.htm",
        "translation_url": "https://www.newadvent.org/fathers/0108.htm",
        "english_text": LETTER_TO_PHILADELPHIANS,
    },
    {
        "letter_number": 6,
        "ref_id": "ignatius.ep.smyrnaeans",
        "recipient_name": "Church of Smyrna",
        "year_approx": 110,
        "year_min": 107,
        "year_max": 115,
        "origin_place": "Troas",
        "origin_lat": 39.9575,
        "origin_lon": 26.2361,
        "dest_place": "Smyrna",
        "dest_lat": 38.4192,
        "dest_lon": 27.1287,
        "subject_summary": "Strong anti-Docetist polemic affirming Christ's true flesh and suffering; Christ's bodily resurrection; heretics who deny the Eucharist; obedience to the bishop; wherever the bishop is, there is the Church; request to send messenger to Antioch.",
        "source_url": "https://www.newadvent.org/fathers/0109.htm",
        "translation_url": "https://www.newadvent.org/fathers/0109.htm",
        "english_text": LETTER_TO_SMYRNAEANS,
    },
    {
        "letter_number": 7,
        "ref_id": "ignatius.ep.polycarp",
        "recipient_name": "Polycarp of Smyrna",
        "year_approx": 110,
        "year_min": 107,
        "year_max": 115,
        "origin_place": "Troas",
        "origin_lat": 39.9575,
        "origin_lon": 26.2361,
        "dest_place": "Smyrna",
        "dest_lat": 38.4192,
        "dest_lon": 27.1287,
        "subject_summary": "Personal pastoral guidance to Bishop Polycarp; be firm as an anvil; care for widows and slaves; marriage with bishop's approval; military metaphors for Christian life; request to send messenger to Antioch and write to adjacent churches.",
        "source_url": "https://www.newadvent.org/fathers/0110.htm",
        "translation_url": "https://www.newadvent.org/fathers/0110.htm",
        "english_text": LETTER_TO_POLYCARP,
    },
]


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Insert collection
    cur.execute("""
        INSERT OR IGNORE INTO collections (slug, author_name, title, letter_count, date_range, english_source_url, scrape_status, notes)
        VALUES (:slug, :author_name, :title, :letter_count, :date_range, :english_source_url, :scrape_status, :notes)
    """, COLLECTION)
    print(f"Collection: {COLLECTION['slug']} -> inserted={cur.rowcount}")

    # 2. Insert authors
    for author in AUTHORS:
        cur.execute("""
            INSERT OR IGNORE INTO authors (name, name_latin, birth_year, death_year, role, location, lat, lon, bio)
            VALUES (:name, :name_latin, :birth_year, :death_year, :role, :location, :lat, :lon, :bio)
        """, {
            "name": author.get("name"),
            "name_latin": author.get("name_latin"),
            "birth_year": author.get("birth_year"),
            "death_year": author.get("death_year"),
            "role": author.get("role"),
            "location": author.get("location"),
            "lat": author.get("lat"),
            "lon": author.get("lon"),
            "bio": author.get("bio"),
        })
        if cur.rowcount:
            print(f"  Author inserted: {author['name']} (id={cur.lastrowid})")
        else:
            # Get existing id
            cur.execute("SELECT id FROM authors WHERE name = ?", (author["name"],))
            row = cur.fetchone()
            print(f"  Author exists: {author['name']} (id={row[0] if row else '?'})")

    # 3. Look up sender id
    cur.execute("SELECT id FROM authors WHERE name = 'Ignatius of Antioch'")
    sender_id = cur.fetchone()[0]

    # 4. Insert letters
    inserted = 0
    for letter in LETTERS:
        # Look up recipient id
        cur.execute("SELECT id FROM authors WHERE name = ?", (letter["recipient_name"],))
        row = cur.fetchone()
        if not row:
            print(f"  WARNING: recipient not found: {letter['recipient_name']}")
            continue
        recipient_id = row[0]

        cur.execute("""
            INSERT OR IGNORE INTO letters (
                collection, letter_number, ref_id, sender_id, recipient_id,
                year_approx, year_min, year_max,
                origin_place, origin_lat, origin_lon,
                dest_place, dest_lat, dest_lon,
                subject_summary, english_text, translation_source,
                source_url, translation_url
            ) VALUES (
                :collection, :letter_number, :ref_id, :sender_id, :recipient_id,
                :year_approx, :year_min, :year_max,
                :origin_place, :origin_lat, :origin_lon,
                :dest_place, :dest_lat, :dest_lon,
                :subject_summary, :english_text, :translation_source,
                :source_url, :translation_url
            )
        """, {
            "collection": "ignatius_antioch",
            "letter_number": letter["letter_number"],
            "ref_id": letter["ref_id"],
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "year_approx": letter["year_approx"],
            "year_min": letter["year_min"],
            "year_max": letter["year_max"],
            "origin_place": letter["origin_place"],
            "origin_lat": letter["origin_lat"],
            "origin_lon": letter["origin_lon"],
            "dest_place": letter["dest_place"],
            "dest_lat": letter["dest_lat"],
            "dest_lon": letter["dest_lon"],
            "subject_summary": letter["subject_summary"],
            "english_text": letter["english_text"],
            "translation_source": "existing_newadvent",
            "source_url": letter["source_url"],
            "translation_url": letter["translation_url"],
        })
        if cur.rowcount:
            inserted += 1
            print(f"  Letter inserted: {letter['ref_id']}")
        else:
            print(f"  Letter exists: {letter['ref_id']}")

    conn.commit()
    conn.close()
    print(f"\nDone. {inserted} Ignatius letters imported.")


if __name__ == "__main__":
    main()

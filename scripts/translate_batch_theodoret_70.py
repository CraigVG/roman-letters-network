#!/usr/bin/env python3
"""Batch translate Theodoret letters 106-110 (IDs 4314-4318)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(4314, """From: Theodoret, Bishop of Cyrrhus
To: Abraham, Oeconomus [church financial administrator]
Date: ~440 AD
Context: A very short appeal sent via traveling bishops, urging Abraham to work for peace and counter the slanders.

To Abraham the Oeconomus,

Through these godly bishops I greet you. I beg you to work for the calm of the churches and to scatter the waves of slander. "Whatever a man sows, that shall he also reap" [Galatians 6:7], as the divine apostle says. Without doubt, then, whoever fights for the apostolic teachings will reap the fruit of the apostolic blessing and share in the apostles' reward."""),

(4315, """From: Theodoret, Bishop of Cyrrhus
To: Theodotus, Presbyter
Date: ~440 AD
Context: Theodoret praises a presbyter's well-known struggles for orthodox teaching and asks him to persevere, comparing the church's ordeal to a storm at sea.

To the Presbyter Theodotus,

The battles your piety has fought on behalf of the apostolic doctrines are not unknown -- they are spoken of frequently, both by those who witnessed them firsthand and by those who have heard the stories from them. Continue your efforts, my dear sir, and fight for the doctrines of the Fathers.

For these same doctrines I too am being battered from every direction. While I bear the crash of the great waves, I pray our Governor either to nod his head and scatter the storm [an allusion to Homer's Zeus], or to give the victims of the tempest the grace to endure it like men."""),

(4316, """From: Theodoret, Bishop of Cyrrhus
To: Acacius, Presbyter
Date: ~440 AD
Context: Theodoret praises the presbyter Acacius for caring for orphaned communities and defending apostolic doctrine, invoking the parable of the talents.

To Acacius the Presbyter,

The promise of David's psalm is true indeed, for through him the Spirit of truth gave this assurance to believers: "Commit your way unto the Lord; trust also in him, and he shall bring it to pass. He shall bring forth your righteousness as the light, and your judgment as the noonday" [Psalm 37:5-6].

We find this fulfilled in your case. The great care you lavish on those weeping in their orphanhood, and your battles on behalf of the apostolic teachings, are on everyone's lips. As the prophets say, "Hidden things are made plain."

Since I too have heard of your admirable efforts, I write to greet you, most reverent sir, and to beg you to add to your glory by adding to your labors. Fight on behalf of the gospel doctrine, so that we may both keep the inheritance of our fathers intact and bring our Master his talent with good interest [cf. Matthew 25:14-30]."""),

(4317, """From: Theodoret, Bishop of Cyrrhus
To: Eusebius, Bishop of Ancyra
Date: ~440 AD
Context: A substantial doctrinal letter in which Theodoret defends his Christology, draws comfort from the biblical promises of persecution to the righteous, and asks Eusebius not to believe the slanders.

To Eusebius, Bishop of Ancyra,

Many are the plots secretly being hatched against me, and through me against the apostolic faith itself. But I take comfort from the sufferings of the saints -- prophets, apostles, martyrs, and those famous in the churches for the word of grace -- and above all from the promises of our God and Savior. For in this present life he has promised us nothing pleasant or easy, but rather trouble, toil, danger, and the attacks of enemies: "In the world you shall have tribulation" [John 16:33]; "If they have persecuted me, they will also persecute you" [John 15:20]; "If they have called the master of the house Beelzebub, how much more the members of his household" [Matthew 10:25]; "The time comes when whoever kills you will think he does God service" [John 16:2]; "Straight is the gate and narrow the way that leads to life" [Matthew 7:14]; "When they persecute you in this city, flee to another" [Matthew 10:23]. The divine apostle too speaks in the same vein: "All who desire to live a godly life in Christ Jesus will suffer persecution, but evil men and impostors will go from bad to worse, deceiving and being deceived" [2 Timothy 3:12-13].

These words give me the greatest comfort in my distress. Since the slanders uttered against me have probably reached your holiness's ears, I beg you: give no credence to my accusers' lies. I am not aware of ever having taught anyone to believe in two sons. I have been taught to believe in one Only-Begotten, our Lord Jesus Christ, God the Word made man. I know the distinction between flesh and Godhead, and I regard as impious both those who divide our one Lord Jesus Christ into two sons, and those who, traveling in the opposite direction, confuse Godhead and manhood into one nature."""),

(4318, """From: Theodoret, Bishop of Cyrrhus
To: Domnus, Bishop of Antioch [Theodoret's metropolitan and ally]
Date: ~440 AD
Context: Theodoret advises Domnus on a sensitive political matter involving an ordination that may or may not have imperial backing, warning against being entrapped into an illegal act.

To Domnus, Bishop of Antioch,

When I read your letter I remembered the blessed Susannah, who saw the wicked elders threatening her and, knowing that the God of all was present, uttered her famous cry: "I am hemmed in on every side" [Daniel 13:22, in the Septuagint]. Yet she chose to fall into the trap of slander rather than offend the just God.

I too, my lord, face two alternatives, as I have often said: either offend God and wound my conscience, or fall by an unjust human verdict.

I suspect the most pious emperor knows nothing about this. If he truly wished the ordination to proceed, what prevented him from writing an order? Why do they make threats in private and create alarm, yet refuse to send official letters commanding it openly? One of two things must be true: either the emperor has not been persuaded to write, or they are trying to trick us into breaking the law so they can prosecute us afterward for the illegality. I have before me the example of the blessed Principius -- when they gave written orders in his case, they later punished him for obeying them.

Moreover, the letters I read on the very day the courier arrived tell a different story. A holy monk has written to someone that he received letters from both the distinguished court official and the former Master of Offices stating that the case of the godly lord bishop Irenaeus will be resolved favorably -- and in return for this good news they ask for prayers.

I think, therefore, that a reply should be written to the clergy who have written from the capital, to the effect that in obedience to the decision of the bishops of Phoenicia, and knowing the zeal, generosity, and love for the poor of the candidate in question, we support the matter -- but that we require it to be done through proper channels."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Theodoret translations (IDs: 4314-4318)")

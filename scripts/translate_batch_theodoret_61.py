#!/usr/bin/env python3
"""Batch translate Theodoret letters 41-45 (IDs 4249-4253)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from translation_helper import write_translations_batch

translations = [

(4249, """From: Theodoret, Bishop of Cyrrhus
To: Claudianus
Date: ~440 AD
Context: A brief meditation on sin as the root cause of earthly calamities, written during a period of political and military upheaval.

To Claudianus,

The divine celebration [Easter or a major feast] has brought us its usual spiritual blessings, but the bitter fruits of sin have not allowed us to enjoy them with a glad heart. Sin has always produced the same harvest: in the beginning it brought forth thorns, thistles, sweat, toil, and pain. Now it shakes the earth beneath us and raises hostile nations against us on every side. We grieve because we force a good God -- one who wants to bless us -- to punish us instead. We compel him to act as judge when he would rather act as benefactor.

Yet when we remember the unfathomable depths of his mercy, we take comfort and trust that "the Lord will not cast off his people, neither will he forsake his inheritance" [Psalm 94:14].

I greet your magnificence and ask you to send word of your health -- which I very much want to hear is good."""),

(4250, """From: Theodoret, Bishop of Cyrrhus
To: Constantius, Praetorian Prefect
Date: ~440 AD
Context: Theodoret writes to the prefect defending his district against false accusations brought by a renegade cleric who fled excommunication and is now acting as an informer at court.

To Constantius, Prefect,

If no pressing need compelled me to write to your greatness, I might rightly be accused of presumption -- of failing to measure myself or to recognize the weight of your office. But the last remnants of the city and district God has entrusted to my care are in danger of complete ruin, and certain men have dared to bring slanderous charges against a recent tax assessment [a "visitation" -- an official review of tax obligations]. I am confident your magnificence will pardon my boldness once you understand the circumstances.

I groan at being forced to write against a man whose errors I would rather cover with a veil, since he belongs to the clergy. Nevertheless, I write to defend the poor he is wronging.

Here are the facts: after being charged with numerous offenses, this man was excluded from communion pending a synod's investigation. Terrified of the bishops' verdict, he fled -- trampling the laws of the Church underfoot and, by his contempt for excommunication, revealing his true character. He has taken up the role of informer -- a trade unfit even for men of the lowest occupations -- and out of personal hatred for the distinguished Philip, he has attacked the wretched taxpayers of our district.

I will spare your excellency a full account of his character and history. I ask only this: do not believe his lies. Ratify the tax assessment. Spare the wretched taxpayers. Spare the thrice-wretched decurions [city councilors personally liable for tax collection] who cannot extract the sums demanded of them. Everyone knows how severe the taxation is in our region."""),

(4251, """From: Theodoret, Bishop of Cyrrhus
To: The Empress Pulcheria Augusta
Date: ~440 AD
Context: Theodoret appeals directly to the empress to protect his overtaxed district from a fugitive bishop's false accusations at court.

To the Augusta Pulcheria [Pulcheria was the elder sister of Emperor Theodosius II and a powerful political figure in her own right, known for her staunch orthodoxy],

Since you adorn the empire with your piety and make the imperial purple shine brighter by your faith, I am emboldened to write to you -- setting aside my own insignificance, because you have always shown proper honor to the clergy.

With these sentiments, I beg your majesty to show mercy to our unhappy district: order the ratification of the tax assessment that has been conducted several times, and do not accept the false charges certain men have brought against it.

I beg you especially to give no credit to a man who bears the title of bishop but whose conduct is unworthy even of respectable household servants. He has been under serious charges and subject to excommunication by the most holy archbishop of Antioch, the Lord Domnus, pending an episcopal investigation. Rather than face judgment, he fled to Constantinople, where he now plies the informer's trade -- attacking his own homeland, a district of thousands of poor people, and wagging his tongue against an entire population to satisfy his hatred of one man.

Out of regard for what is fitting, I will say nothing more about his character -- he shows it plainly enough by his actions. But this I will say about the district: when the whole province had its burdens lightened, this portion alone -- though it bore a disproportionately heavy share -- never received any relief. The result is that many estates lack farmers, many have been abandoned altogether by their owners, while the wretched decurions face demands for taxes on these very properties and, unable to bear the burden, flee as well."""),

(4252, """From: Theodoret, Bishop of Cyrrhus
To: Senator, Patrician
Date: ~440 AD
Context: Theodoret congratulates the patrician Senator on a new honor while urgently requesting his help to block a fugitive bishop's attempt to overturn the district's tax assessment.

To the Patrician Senator,

Thanks be to the Savior of the world, who continues to add dignity and honor to your greatness. The reason I have not written before now to express my delight at this crowning distinction is simply that I did not wish to trouble your magnificence.

But I write now because the district Providence has entrusted to my care stands, as the proverb says, on a razor's edge.

You will remember the tax assessment conducted when we first benefited from your presence among us -- how it was established with difficulty under the excellent prefect Florentius, and confirmed by his successor. Now a man who bears the name of bishop, but whose behavior is unworthy of even stage actors, has fled the episcopal synod while under sentence of excommunication. He is trying to discredit and overturn the assessment, and through his hatred of the distinguished Philip he assails the truth itself.

I beg your excellency to render his lies powerless and to ensure that the lawfully confirmed assessment stands undisturbed. It would be fitting for your greatness to reap the fruit of this good deed alongside all your others -- to receive the grateful praise of those you are protecting, and so to honor both the God of all and his true servant, the man of God the Lord Jacob, who joins me in this appeal. Had it been his custom to write, he would have written himself."""),

(4253, """From: Theodoret, Bishop of Cyrrhus
To: Anatolius, Patrician
Date: ~440 AD
Context: Theodoret expresses sorrow at losing Anatolius's official protection and begs him to continue shielding the district from the renegade bishop's schemes even from a distance.

To the Patrician Anatolius,

Your greatness knows well how all the people of the East feel toward your magnificence -- as children feel toward a loving father. Why then have you shown coldness to those who love you, withdrawn your generous care, and driven everyone to tears by putting your own interests ahead of public service?

I truly believe there is not one God-fearing person who is not deeply grieved at the loss of your authority in office, and I think even those without right knowledge of divine things, when they remember your kindnesses, share in this distress. For my own part, I am especially sorry when I think of your dignity and your unaffected character. I pray the God of all to protect you always with his invincible right hand and to supply you with every kind of blessing.

But I must ask: even though you are no longer present in an official capacity, extend to us your accustomed protection. Help us undo the schemes of our unworthy bishop, whose purposes are perfectly well known to your greatness. He is working, I am told, toward the complete ruin of our district. He has taken up the informer's role to discredit the recent tax assessment -- and this when everyone knows that taxation here is crushing, and that many estates have already been abandoned by their farmers. Yet this man, in contempt of his excommunication and in flight from the holy synod, has turned his tongue against the wretched poor.

May your magnificence see to it that the truth is not defeated by a lie. And I bring the same plea on behalf of the Cilicians -- for we will not stop protesting until this injustice is set right."""),

]

n = write_translations_batch(translations)
print(f"Wrote {n} Theodoret translations (IDs: 4249-4253)")

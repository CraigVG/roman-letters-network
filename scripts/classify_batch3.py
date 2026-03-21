#!/usr/bin/env python3
"""
Keyword-based topic classification for letters missing topics — BATCH 3.

Reads letter IDs from /tmp/topics_batch3.txt (format: id|collection|excerpt),
queries the FULL modern_english from the database for each,
then classifies using comprehensive single-keyword matching.

Only updates where topics IS NULL or empty.
Default: "friendship" if no keywords match.
Collection defaults: papal collections -> "papal_authority", cassiodorus -> "imperial_politics".
"""

import sqlite3
import re
from collections import Counter

DB_PATH = "/Users/drillerdbmacmini/Documents/github/roman-letters-network/data/roman_letters.db"
BATCH3_FILE = "/tmp/topics_batch3.txt"

# ── COLLECTION DEFAULTS ────────────────────────────────────────────────────────
PAPAL_COLLECTIONS = {
    'leo', 'gelasius', 'innocent', 'hormisdas', 'gregory', 'boniface',
    'celestine', 'sixtus', 'hilarus', 'simplicius', 'felix', 'symmachus_pope',
    'pelagius', 'pelagius_ii', 'avellana', 'thiel',
}
CASSIODORUS_COLLECTIONS = {'cassiodorus', 'variae'}


def get_collection_default(collection):
    col = collection.lower()
    for papal in PAPAL_COLLECTIONS:
        if papal in col:
            return 'papal_authority'
    for cass in CASSIODORUS_COLLECTIONS:
        if cass in col:
            return 'imperial_politics'
    return 'friendship'


# ── TOPIC RULES (compiled regex patterns) ────────────────────────────────────
TOPIC_RULES = []


def rule(tag, pattern):
    TOPIC_RULES.append((tag, re.compile(pattern, re.IGNORECASE)))


rule("barbarian_invasion",
     r"\b(?:goth|goths|gothic|ostrogoth|visigoth|vandal|vandals|hun|huns|hunnic|"
     r"lombard|lombards|frank|franks|frankish|burgund|burgundian|alan|alans|"
     r"heruli|herulian|suev|suevi|suebi|gepid|gepids|"
     r"barbarian\w*\s+(?:invasion|attack|raid|incursion|horde|army|armies|threat|menace)|"
     r"(?:invasion|incursion|raid|sack|plunder|ravag|devastat)\w*\s+(?:by|of)\s+(?:the\s+)?(?:barbarian|goth|vandal|hun|lombard|frank)|"
     r"attila|alaric|gaiseric|genseric|odoacer|theoderic|theodoric|totila|clovis|stilicho|radagaisus|"
     r"(?:sack|fall|siege)\s+(?:of\s+)?rome|"
     r"barbarian\s+(?:nation|people|tribe|race|king|chief)|"
     r"the\s+enemy\s+(?:has|attacked|advanced|invaded)|has\s+been\s+pillaged|"
     r"ravaged\s+the|destroyed\s+by\s+the|the\s+invaders|hostile\s+forces|"
     r"under\s+siege|forced\s+to\s+flee|refugees\s+from|displaced\s+by|"
     r"war\s+has\s+devastated|invaded\s+by|ravaged\s+by)")

rule("imperial_politics",
     r"\b(?:emperor\b|empress\b|imperial\s+(?:court|decree|edict|command|order|law|power|majesty|authority)|"
     r"augustus\b|augusta\b|caesar\b|"
     r"(?:the\s+)?(?:court|palace)\s+(?:at|of|in)\s+(?:constantinople|ravenna|milan)|"
     r"prefect\b|praetorian|consul\b|patrician\b|"
     r"theodosius|valentinian|honorius|arcadius|justinian|theodora|marcian|"
     r"leo\s+(?:the\s+)?emperor|zeno\s+(?:the\s+)?emperor|anastasius\s+(?:the\s+)?emperor|"
     r"constantius|constans|julian\s+(?:the\s+)?(?:emperor|apostate)|"
     r"imperial\s+rescript|comes\b|magister\s+militum|master\s+of\s+(?:soldiers|offices|the\s+horse)|"
     r"his\s+majesty|the\s+imperial\s+court|imperial\s+decree|by\s+order\s+of\s+the\s+emperor|"
     r"ascended\s+the\s+throne|at\s+the\s+palace|his\s+imperial\s+majesty|the\s+imperial\s+will|"
     r"the\s+praetorian\s+prefect|master\s+of\s+soldiers)")

rule("church_state_conflict",
     r"\b(?:(?:bishop|church|clergy|priest|pope|pontiff)\w*\s+(?:against|versus|conflict|dispute|clash|resist|oppos|defy|defi)\w*\s+(?:emperor|state|secular|civil|king|prince|magistrat|prefect|governor)|"
     r"(?:emperor|state|secular|civil|king|prince|magistrat|prefect|governor)\w*\s+(?:against|versus|interfer|meddle|encroach|persecute|exile|banish|depos)\w*\s+(?:bishop|church|clergy|priest|pope|pontiff)|"
     r"secular\s+(?:power|authority|interference|jurisdiction)\s+(?:over|in|into)\s+(?:the\s+)?(?:church|ecclesiastical|spiritual)|"
     r"ecclesiastical\s+(?:independence|freedom|liberty|immunity|privilege)\s+(?:from|against)\s+(?:the\s+)?(?:state|secular|civil)|"
     r"(?:banish|exile|depos|remov)\w+\s+(?:the\s+)?(?:bishop|patriarch|pope)|"
     r"investiture|caesaropapism|two\s+swords|"
     r"the\s+church\s+must\s+be\s+free|secular\s+interference|the\s+state\s+has\s+no\s+right|"
     r"the\s+emperor\s+interferes|the\s+bishop\s+refuses|exiled\s+by\s+the\s+emperor|"
     r"against\s+the\s+church|temporal\s+power\s+over\s+the\s+church|"
     r"the\s+church\s+is\s+not\s+subject|resist\s+the\s+emperor)")

rule("diplomatic",
     r"\b(?:(?:peace\s+)?treat(?:y|ies)|embassy|embass(?:y|ies)|ambassador|envoy|legate\b|"
     r"negotiat\w+|peace\s+(?:terms|agreement|accord|proposal)|"
     r"truce\b|armistice|alliance\b|"
     r"(?:send|sent|dispatch)\w*\s+(?:an?\s+)?(?:embassy|envoy|legate|ambassador|delegation|mission)|"
     r"(?:diplomatic|peace)\s+(?:mission|overture|initiative|effort|relation)|"
     r"intercede\w*\s+(?:with|before|on\s+behalf)|"
     r"(?:beg|plead|petition|appeal)\w*\s+(?:for\s+)?(?:peace|mercy|clemency)|"
     r"ransom\w*\s+(?:captive|prisoner|hostage)|"
     r"peace\s+between|the\s+treaty|good\s+relations\s+between|the\s+alliance|"
     r"mutual\s+agreement|terms\s+of\s+peace|reconciliation\s+between|"
     r"diplomatic\s+mission|peace\s+negotiations|brokering\s+peace|"
     r"to\s+negotiate|sent\s+as\s+ambassador|dispatched\s+as\s+envoy)")

rule("arianism",
     r"\b(?:arian\w*|arius\b|homoousio|homoiousio|anomoean|eunomi\w+|"
     r"nicene\s+(?:creed|faith|formula|definition|council)|"
     r"consubstantial|council\s+of\s+nicaea|"
     r"(?:semi[- ]?arian|neo[- ]?arian|macedonian\s+heresy)|"
     r"the\s+arian\s+heresy|homoousios|the\s+nicene\s+faith|against\s+the\s+arians|"
     r"consubstantial\s+with\s+the\s+father|arian\s+doctrine|arian\s+bishop|"
     r"council\s+of\s+nicaea|the\s+nicene\s+creed|homoiousian|"
     r"arian\s+controversy|arian\s+persecution|semi-arian|"
     r"the\s+arians\s+deny|opposed\s+to\s+arianism)")

rule("donatism",
     r"\b(?:donatist\w*|donatus\b|donatism|"
     r"circumcellion\w*|caecilian\w*|"
     r"(?:traditor|traditores)\b|"
     r"(?:donatist|schismatic)\s+(?:bishop|clergy|church|party|controversy|schism|rebaptis)|"
     r"rebaptism\s+of\s+the|schismatic\s+party|against\s+the\s+donatists|"
     r"the\s+donatist\s+controversy|donatist\s+clergy|schismatics\s+who\s+rebaptize)")

rule("pelagianism",
     r"\b(?:pelagian\w*|pelagius\b|pelagianism|"
     r"caelestius\b|celestius\b|julian\s+of\s+eclanum|"
     r"(?:semi[- ]?pelagian)|"
     r"(?:original\s+sin|free\s+will|grace\s+(?:alone|of\s+god))\s+(?:controversy|debate|dispute|heresy|doctrine)|"
     r"pelagian\s+error|human\s+will\s+alone|divine\s+grace\s+is\s+necessary|"
     r"without\s+grace|grace\s+and\s+free\s+will|original\s+sin\s+denied)")

rule("christology",
     r"\b(?:nestorian\w*|nestorius\b|nestorianism|"
     r"monophysit\w*|miaphysit\w*|eutychi\w*|eutyches\b|"
     r"chalcedon(?:ian)?\b|council\s+of\s+chalcedon|"
     r"council\s+of\s+ephesus|"
     r"theotokos|christotokos|"
     r"(?:two|one|dual)\s+(?:nature|natures)\s+(?:of\s+)?christ|"
     r"(?:hypostatic\s+union|communicatio\s+idiomatum)|"
     r"tome\s+of\s+leo|apollinari\w+|"
     r"the\s+nature\s+of\s+christ|divine\s+and\s+human\s+natures|eutychian\s+heresy|"
     r"one\s+nature|two\s+natures\s+of\s+christ|nestorian\s+heresy|"
     r"mother\s+of\s+god|chalcedonian\s+definition|the\s+person\s+of\s+christ|"
     r"divine\s+nature\s+of\s+christ)")

rule("conversion",
     r"\b(?:(?:convert|conversion|converting|converted)\s+(?:the\s+)?(?:pagan|heathen|heretic|jew|barbarian|gentile|infidel|nation|people|tribe)|"
     r"(?:pagan|heathen|heretic|jew|barbarian|gentile)\w*\s+(?:convert|conversion|bapti[sz])|"
     r"bapti[sz]\w+\s+(?:the\s+)?(?:pagan|heathen|heretic|barbarian|king|nation|convert|catechumen|infant|child)|"
     r"(?:catechumen|neophyte|newly\s+bapti[sz])|"
     r"(?:pagan|idol)\w*\s+(?:worship|temple|shrine|sacrifice|rite|custom)\w*\s+(?:destroy|abolish|suppress|eradicat|overthrow|demolish)|"
     r"(?:mission|missionary|evangeli[sz])\w*\s+(?:to|among|work)|"
     r"brought\s+to\s+the\s+faith|accepted\s+baptism|turned\s+from\s+paganism|"
     r"newly\s+converted|embraced\s+christianity|converted\s+from\s+paganism|"
     r"baptised\s+into|turned\s+to\s+christ|abandoned\s+the\s+old\s+gods|"
     r"instruction\s+in\s+the\s+faith|preparing\s+for\s+baptism|the\s+pagan\s+temples|"
     r"demolishing\s+the\s+idols|missionary\s+work|preaching\s+to\s+the\s+pagans)")

rule("monasticism",
     r"\b(?:monast\w+|monk\b|monks\b|nun\b|nuns\b|abbot\b|abbess\b|"
     r"(?:monastic|religious)\s+(?:life|rule|discipline|community|order|vow|habit)|"
     r"(?:rule\s+of\s+(?:st\.?\s+)?(?:benedict|basil|augustine|pachomius))|"
     r"(?:cenobite|cenobitic|anchorite|anchoretic|hermit|eremit\w+|ascetic\w*)|"
     r"(?:cell\b|cloister|monastery|convent|desert\s+father|desert\s+mother)|"
     r"(?:renounce|renunciation|renouncing)\s+(?:the\s+)?(?:world|flesh|secular)|"
     r"the\s+brothers|the\s+brethren|your\s+monastery|withdrawal\s+from\s+the\s+world|"
     r"the\s+solitary\s+life|community\s+of\s+monks|your\s+convent|"
     r"life\s+in\s+the\s+desert|the\s+holy\s+brethren|renounce\s+the\s+world|"
     r"ascetic\s+life)")

rule("papal_authority",
     r"\b(?:(?:primacy|supremacy|authority|jurisdiction|prerogative)\s+(?:of\s+)?(?:the\s+)?(?:roman\s+(?:see|church|bishop|pontiff)|apostolic\s+see|pope|peter|"
     r"see\s+of\s+(?:peter|rome))|"
     r"(?:vicar\s+of\s+(?:christ|peter|god))|"
     r"(?:successor\s+of\s+(?:peter|the\s+apostle))|"
     r"(?:apostolic\s+(?:see|authority|tradition|succession|primacy))|"
     r"(?:(?:roman|papal)\s+(?:primacy|supremacy|jurisdiction|prerogative|authority))|"
     r"(?:tu\s+es\s+petrus|upon\s+this\s+rock)|"
     r"(?:appeal\w*\s+to\s+(?:the\s+)?(?:pope|rome|apostolic\s+see))|"
     r"(?:canonical\s+jurisdiction|metropolitan\s+authority)|"
     r"the\s+apostolic\s+see|by\s+authority\s+of\s+the|canonical\s+authority|"
     r"the\s+bishop\s+of\s+rome|papal\s+authority|papal\s+decree|"
     r"our\s+predecessor|the\s+chair\s+of\s+peter|primacy\s+of\s+rome|"
     r"roman\s+primacy|the\s+roman\s+see|appeal\s+to\s+rome|"
     r"universal\s+bishop|the\s+supreme\s+pontiff|decretal\s+letter)")

rule("famine_plague",
     r"\b(?:famine\b|plague\b|pestilence\b|epidemic\b|pandemic\b|"
     r"(?:great\s+)?(?:hunger|starvation|dearth|scarcity)\b|"
     r"(?:earthquake|flood|drought|locust|volcano|eruption|disaster)\b|"
     r"(?:plague|pestilence|disease|sickness|contagion|mortality)\s+(?:ravag|devastat|spread|struck|swept|killed|carried\s+off|claimed)|"
     r"(?:many|countless|innumerable|great\s+numbers?)\s+(?:died|perished|were\s+(?:killed|carried\s+off|struck\s+down))|"
     r"the\s+plague\s+has|people\s+are\s+starving|food\s+shortage|"
     r"the\s+epidemic|widespread\s+disease|famine\s+has\s+struck|great\s+mortality|"
     r"died\s+of\s+plague|ravaged\s+by\s+disease|the\s+hunger|dearth\s+of\s+food|"
     r"the\s+locusts|catastrophic\s+flood)")

rule("slavery_captivity",
     r"\b(?:slave\w*|slavery\b|enslav\w+|servitude\b|bondage\b|"
     r"captiv\w+|prisoner\w*|hostage\w*|"
     r"(?:ransom|redeem|free|liberat)\w*\s+(?:the\s+)?(?:captive|prisoner|slave|hostage)|"
     r"(?:taken|held|sold)\s+(?:as\s+)?(?:captive|prisoner|slave|hostage)|"
     r"(?:chain|shackle|fetter|manacle)\w*|"
     r"held\s+captive|ransom\s+the\s+prisoners|set\s+them\s+free|"
     r"in\s+chains|the\s+enslaved|liberate\s+the\s+captives|"
     r"in\s+captivity|taken\s+as\s+slaves|sold\s+into\s+slavery|"
     r"the\s+prisoners|redeem\s+the\s+captives|free\s+the\s+prisoners|"
     r"ransomed\s+from|captive\s+christians)")

rule("travel_mobility",
     r"\b(?:(?:journey|travel|voyage|trip|passage|crossing)\w*\s+(?:to|from|through|across|by\s+(?:sea|land|road))|"
     r"(?:road|roads|highway|route|path)\s+(?:(?:is|are|were|was)\s+)?(?:dangerous|unsafe|blocked|impassable|difficult)|"
     r"(?:winter|storm|weather|sea|mountain|bandit|robber|pirate)\w*\s+(?:prevent|delay|hinder|block|endanger|threaten)\w*\s+(?:the\s+)?(?:journey|travel|voyage|passage|letter|messenger)|"
     r"(?:messenger|carrier|courier|letter[- ]?bearer|travell?er)\w*\s+(?:arriv|deliver|bring|carry|sent|dispatch)|"
     r"(?:delay|late|slow|difficult)\w*\s+(?:in\s+)?(?:deliver|arrival|communication|correspondence|mail|letter)|"
     r"(?:sail|sailed|sailing|embarked|set\s+out|set\s+forth|departed|arrived)\s+(?:for|from|at|in)\b|"
     r"your\s+journey|safe\s+travels|along\s+the\s+road|by\s+ship|"
     r"set\s+sail|arrived\s+safely|has\s+departed|the\s+bearer\s+of\s+this\s+letter|"
     r"our\s+messenger|sent\s+by\s+hand|delivered\s+by|through\s+the\s+messenger|"
     r"the\s+roads\s+are|the\s+journey\s+is|crossing\s+the\s+sea|at\s+sea|"
     r"the\s+travell?er|the\s+letter\s+carrier|who\s+brings\s+this\s+letter|"
     r"who\s+carries\s+this|delayed\s+on\s+the\s+road|difficulty\s+of\s+travel)")

rule("women",
     r"\b(?:(?:to|dear|beloved|holy|blessed|noble|illustrious)\s+(?:lady|sister|mother|daughter|widow|virgin|woman|matron|empress|queen|abbess)|"
     r"(?:lady|sister|mother|daughter|widow|virgin|matron|abbess)\s+(?:\w+\s+)?(?:writes?|send|greet|asks?|request|beseech|implore)|"
     r"(?:consecrated|dedicated|devoted)\s+virgin|"
     r"(?:women|female|widow|virgin)\s+(?:in\s+the\s+church|religious|consecrated|role|place|status)|"
     r"(?:marriage|dowry|conjugal|bridal|nuptial|wife|wive|husband\s+and\s+wife)\b|"
     r"your\s+daughter|your\s+wife|the\s+lady|virgin\s+consecrated\s+to\s+god|"
     r"the\s+widow|her\s+dowry|the\s+matron|holy\s+woman|devout\s+woman|"
     r"consecrated\s+virgin|the\s+blessed\s+woman|noble\s+lady|the\s+empress|"
     r"the\s+queen|women\s+in\s+the\s+church|the\s+holy\s+virgin|"
     r"female\s+ascetic|the\s+deaconess)")

rule("education_books",
     r"\b(?:(?:send|sent|lending|lend|borrow|copy|copies|copying|transcrib)\w*\s+(?:the\s+)?(?:book|volume|work|manuscript|codex|text|treatise|scroll|letter)|"
     r"(?:book|volume|work|manuscript|codex|library|libraries)\s+(?:you\s+)?(?:sent|send|request|ask|lend|borrow|copy)|"
     r"(?:liberal\s+arts|rhetoric|grammar|dialectic|philosophy|eloquen\w+|education|school|teacher|pupil|student|tutor)\b|"
     r"(?:literary|learned|scholarly|intellectual)\s+(?:culture|circle|pursuits|friendship|exchange|life)|"
     r"(?:study|studies|studying|read|reading)\s+(?:of\s+)?(?:scripture|classics|philosophy|rhetoric|law|literature)|"
     r"(?:cicero|virgil|vergil|horace|plato|aristotle|homer|sallust|livy|tacitus)\b|"
     r"your\s+writings|the\s+treatise|i\s+have\s+read|send\s+me\s+the\s+book|"
     r"copy\s+of\s+your|your\s+commentary|scholarly\s+work|the\s+lecture|"
     r"the\s+discourse|literary\s+composition|the\s+oration|the\s+volume\s+you|"
     r"a\s+copy\s+of\s+the|reading\s+your|your\s+learned|the\s+books\s+you|"
     r"send\s+me\s+a\s+copy|i\s+am\s+studying|i\s+have\s+been\s+reading|"
     r"your\s+philosophical|rhetorical\s+skill|your\s+eloquence|the\s+library|"
     r"borrowed\s+from|lend\s+me)")

rule("property_economics",
     r"\b(?:(?:estate|property|properties|land|lands|farm|villa|rent|revenue|tax|taxes|tithe|patrimony)\b|"
     r"(?:buy|sell|purchase|sale|trade|merchant|market|commerce|commercial|economic)\b|"
     r"(?:debt|creditor|debtor|loan|interest|payment|money|wealth|income|profit|loss)\b|"
     r"(?:tenant|lease|steward|procurator|administration)\s+(?:of\s+)?(?:the\s+)?(?:estate|property|land|patrimony|church)|"
     r"(?:patrimony\s+of\s+(?:st\.?\s+)?peter|church\s+(?:property|estate|land|revenue|patrimony))|"
     r"the\s+harvest|the\s+vineyard|the\s+wages|the\s+price|the\s+cost\s+of|"
     r"the\s+revenues|the\s+taxes|the\s+tenant|the\s+steward|the\s+debtors|"
     r"the\s+creditors|money\s+is\s+owed|payment\s+of|financial\s+affairs|"
     r"economic\s+hardship|great\s+wealth|in\s+poverty|the\s+provisions)")

rule("grief_death",
     r"\b(?:(?:death|passing|loss|decease)\s+of\s+(?:your|his|her|our|the|my)|"
     r"(?:mourn|grieve|lament|bewail|weep\s+for|sorrow\s+(?:for|over|at))\w*|"
     r"(?:console|consolation|comfort)\w*\s+(?:you|him|her|them|us|the\s+(?:bereaved|grieving|mourning))|"
     r"(?:funeral|burial|tomb|grave|epitaph|obituary|eulogy|elegy)\b|"
     r"(?:departed|deceased|fallen\s+asleep|gone\s+to\s+(?:god|the\s+lord|rest|heaven)|called\s+(?:home|to\s+god))|"
     r"(?:premature|untimely|sudden|unexpected)\s+(?:death|end|passing)|"
     r"has\s+passed\s+away|has\s+died|passed\s+from\s+this\s+life|in\s+mourning|"
     r"the\s+loss\s+of|rest\s+in\s+peace|his\s+soul|her\s+soul|"
     r"the\s+deceased|the\s+burial|in\s+memory\s+of|words\s+of\s+condolence|"
     r"comfort\s+in\s+your\s+grief|grieve\s+with\s+you|your\s+bereavement|"
     r"the\s+death\s+of|mourn\s+the\s+passing|taken\s+from\s+us|"
     r"called\s+home|gone\s+to\s+god|departed\s+this\s+life|i\s+weep|words\s+of\s+comfort)")

rule("illness",
     r"\b(?:(?:my|your|his|her|our)\s+(?:illness|sickness|disease|ailment|malady|infirmity|health|fever|pain|gout|blindness|weakness)|"
     r"(?:sick|ill|unwell|ailing|infirm|bedridden|feeble|frail)\b|"
     r"(?:recover|recovery|recuperat|convalesc|heal)\w*\s+(?:from\s+)?(?:(?:my|your|his|her|the)\s+)?(?:illness|sickness|disease|fever)|"
     r"(?:doctor|physician|medicine|remedy|treatment|cure)\b|"
     r"(?:bodily|physical)\s+(?:weakness|suffering|pain|affliction|distress)|"
     r"fallen\s+ill|recovering\s+from|in\s+poor\s+health|the\s+doctors|"
     r"your\s+recovery|has\s+taken\s+to\s+bed|suffering\s+from\s+illness|"
     r"bodily\s+weakness|medical\s+treatment|a\s+cure\s+for|the\s+fever|"
     r"been\s+unwell|been\s+sick|has\s+been\s+ailing|physical\s+suffering|"
     r"afflicted\s+by|the\s+infirmity|the\s+ailment|weakness\s+of\s+body|pain\s+in\s+my)")

rule("friendship",
     r"\b(?:(?:dear|dearest|beloved|cherished|closest)\s+friend|"
     r"(?:our|your|my|mutual|old|true|faithful|loyal|enduring|close|deep)\s+friendship|"
     r"amicitia\b|"
     r"(?:bond|bonds|tie|ties)\s+of\s+(?:friendship|affection|love|devotion)|"
     r"(?:miss|long\s+for|yearn\s+for|pine\s+for)\s+(?:you|your\s+(?:company|presence|conversation))|"
     r"(?:absence|separation|apart)\s+(?:from\s+)?(?:you|each\s+other|one\s+another)\s+(?:grieves?|pains?|saddens?|hurts?)|"
     r"my\s+dear\s+friend|our\s+friendship|bond\s+of\s+affection|i\s+miss\s+you|"
     r"longing\s+to\s+see\s+you|your\s+companionship|warmest\s+regards|"
     r"fond\s+memories|cherished\s+friend|faithful\s+friend|truest\s+friend|"
     r"deepest\s+affection|how\s+i\s+long|we\s+have\s+been\s+parted|"
     r"your\s+absence\s+pains|write\s+to\s+me\s+often|i\s+think\s+of\s+you\s+often)")

rule("humor",
     r"\b(?:(?:joke|jest|wit|witty|humor|humour|humorous|funny|amusing|comic|comical|playful|merry|lighthearted|tongue[- ]in[- ]cheek)\b|"
     r"(?:laugh|laughing|laughter|chuckle|smile|grin)\w*\s+(?:at|about|over|when)|"
     r"(?:tease|teasing|mock|mocking|banter|irony|ironic|satiric|sarcas)\w*|"
     r"(?:in\s+(?:jest|fun|sport|play))\b|"
     r"i\s+cannot\s+help\s+but\s+smile|you\s+amuse\s+me|a\s+witty\s+remark|"
     r"tongue\s+in\s+cheek|you\s+rascal|with\s+a\s+laugh|amusing\s+story|"
     r"delightfully\s+absurd|you\s+jest|i\s+jest|said\s+in\s+fun|a\s+playful\s+spirit)")


def classify_letter(text, collection):
    """Return comma-separated topic string for a letter."""
    if not text or not text.strip():
        return get_collection_default(collection)

    tags = []
    for tag, pattern in TOPIC_RULES:
        if pattern.search(text):
            tags.append(tag)

    if tags:
        return ','.join(sorted(tags))
    else:
        return get_collection_default(collection)


def main():
    # Parse the batch3 file to get IDs
    print(f"Reading letter IDs from {BATCH3_FILE}...")
    letter_ids = []
    collection_map = {}

    with open(BATCH3_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('|', 2)
            if len(parts) >= 2:
                try:
                    lid = int(parts[0].strip())
                    col = parts[1].strip()
                    if lid not in collection_map:
                        letter_ids.append(lid)
                        collection_map[lid] = col
                except ValueError:
                    continue

    print(f"Found {len(letter_ids)} unique letter IDs in batch3 file.")
    if not letter_ids:
        print("Nothing to process.")
        return

    # Connect to DB
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Query FULL modern_english for these IDs, only where topics IS NULL or empty
    placeholders = ','.join('?' * len(letter_ids))
    rows = conn.execute(
        f"SELECT id, collection, modern_english FROM letters "
        f"WHERE id IN ({placeholders}) AND (topics IS NULL OR length(topics) = 0) "
        f"ORDER BY id",
        letter_ids
    ).fetchall()

    print(f"Letters needing classification: {len(rows)} (out of {len(letter_ids)} in batch file)\n")

    if not rows:
        print("All letters in this batch already have topics.")
        conn.close()
        return

    # Classify
    tag_counter = Counter()
    updates = []

    for row in rows:
        lid = row['id']
        col = row['collection'] or collection_map.get(lid, '')
        text = row['modern_english'] or ''
        topics_str = classify_letter(text, col)
        updates.append((topics_str, lid))
        for t in topics_str.split(','):
            tag_counter[t.strip()] += 1

    # Write to DB
    conn.executemany(
        "UPDATE letters SET topics = ? WHERE id = ? AND (topics IS NULL OR length(topics) = 0)",
        updates
    )
    conn.commit()

    total_classified = len(updates)

    # Final stats
    remaining = conn.execute(
        "SELECT COUNT(*) FROM letters WHERE topics IS NULL OR length(topics) = 0"
    ).fetchone()[0]
    total_letters = conn.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
    with_topics = conn.execute(
        "SELECT COUNT(*) FROM letters WHERE topics IS NOT NULL AND length(topics) > 0"
    ).fetchone()[0]

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Classified this run:           {total_classified}")
    print(f"Total letters in DB:           {total_letters}")
    print(f"Letters now with topics:       {with_topics}")
    print(f"Still missing topics:          {remaining}")

    print("\nTOPIC DISTRIBUTION (this run):")
    for topic, count in sorted(tag_counter.items(), key=lambda x: -x[1]):
        bar = '#' * (count // 5)
        print(f"  {topic:<25} {count:>5}  {bar}")

    # Sample a few results
    print("\nSample results (first 10):")
    for topics_str, lid in updates[:10]:
        print(f"  ID {lid:>6}: {topics_str}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

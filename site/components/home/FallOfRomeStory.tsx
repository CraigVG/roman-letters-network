import { getDb } from '@/lib/db';
import { FallOfRomeScrolly } from './FallOfRomeScrolly';

/* ------------------------------------------------------------------ */
/*  DB queries - run at build time (server component)                  */
/* ------------------------------------------------------------------ */

interface EraStats {
  peak: number;       // 350-399
  firstCracks: number; // 395-430
  fray: number;        // 430-460
  lastRomans: number;  // 460-490
  newKingdoms: number; // 500-540
  gregory: number;     // gregory_great collection
  easternRoman: number; // Eastern letter-writers (Theodoret, Isidore, etc.)
  total: number;       // all letters
  afterGregory: number; // 605+
}

function queryEraStats(): EraStats {
  const db = getDb();

  const count = (sql: string) =>
    (db.prepare(sql).get() as { c: number }).c;

  return {
    peak: count("SELECT COUNT(*) as c FROM letters WHERE year_approx BETWEEN 350 AND 399"),
    firstCracks: count("SELECT COUNT(*) as c FROM letters WHERE year_approx BETWEEN 395 AND 430"),
    fray: count("SELECT COUNT(*) as c FROM letters WHERE year_approx BETWEEN 430 AND 460"),
    lastRomans: count("SELECT COUNT(*) as c FROM letters WHERE year_approx BETWEEN 450 AND 490"),
    newKingdoms: count("SELECT COUNT(*) as c FROM letters WHERE year_approx BETWEEN 500 AND 540"),
    gregory: count("SELECT COUNT(*) as c FROM letters WHERE collection = 'gregory_great'"),
    easternRoman: count("SELECT COUNT(*) as c FROM letters WHERE collection IN ('theodoret_cyrrhus', 'isidore_pelusium', 'basil_caesarea', 'gregory_nazianzus', 'libanius', 'synesius_cyrene', 'julian_emperor', 'chrysostom', 'athanasius_alexandria')"),
    total: count("SELECT COUNT(*) as c FROM letters"),
    afterGregory: count("SELECT COUNT(*) as c FROM letters WHERE year_approx > 604"),
  };
}

/* ------------------------------------------------------------------ */
/*  Chapter definitions - narratives are static, stats from DB         */
/* ------------------------------------------------------------------ */

export interface Chapter {
  id: number;
  era: string;
  dateRange: string;
  narrative: string;
  quote: string;
  attribution: string;
  letterHref: string;
  stat?: string;
  event?: string;
  bgTone: string;
}

function buildChapters(s: EraStats): Chapter[] {
  return [
    {
      id: 1,
      era: 'The Connected World',
      dateRange: '350-380 AD',
      narrative:
        'In the mid-fourth century, the Roman Empire was a single, immense conversation. Professors in Antioch exchanged letters with former students in Constantinople. Bishops in Cappadocia debated theology with colleagues in Rome. Senators traded favors across provinces as casually as we send emails. The postal system worked. The roads were safe. The letters flowed.',
      quote:
        'I recognized your letter the way you recognize friends\u2019 children by their resemblance to their parents.',
      attribution: 'Basil of Caesarea, Letter 2 (~357 AD)',
      letterHref: '/letters/basil_caesarea/2',
      stat: `${s.peak.toLocaleString()} letters survive from the 350s-390s`,
      bgTone: 'var(--color-surface)',
    },
    {
      id: 2,
      era: 'The First Cracks',
      dateRange: '395-410 AD',
      narrative:
        'The empire split permanently in 395. Within fifteen years, the unthinkable happened: Alaric\u2019s Visigoths sacked Rome itself. Across the Mediterranean, letter-writers struggled to process the shock. In Bethlehem, Jerome broke off a commentary mid-sentence. In Africa, Augustine began the enormous work of explaining how God\u2019s city could outlast any earthly one.',
      quote:
        'You ask what I think about the recent political upheavals, the fall of Stilicho, the shifting alliances at court, the growing boldness of the barbarians. You want to know whether I think the Empire will survive.',
      attribution: 'Augustine of Hippo, Letter 144 (~409 AD)',
      letterHref: '/letters/augustine_hippo/144',
      event: '410 AD - Alaric\u2019s Visigoths sack Rome',
      bgTone: 'color-mix(in srgb, var(--color-surface) 85%, var(--color-border) 15%)',
    },
    {
      id: 3,
      era: 'The Networks Fray',
      dateRange: '430-460 AD',
      narrative:
        'By mid-century, sending a letter across Gaul had become an act of courage. Couriers were stopped by Burgundian soldiers. Roads that had carried imperial mail for centuries now crossed borders between rival kingdoms. As Patrick Wyman observed, "In 500, it was much harder to travel from Paris to Rome than it had been in 400."',
      quote:
        'Divided as we are between different kingdoms, we are held back from more frequent exchange of correspondence by the terms of our separate allegiances.',
      attribution: 'Sidonius Apollinaris, Letter V (~459 AD)',
      letterHref: '/letters/sidonius_apollinaris/5',
      event: '439: Vandals take Carthage / 451: Attila invades Gaul',
      stat: `Only ${s.fray.toLocaleString()} letters from the 430s-460s, down from ${s.peak.toLocaleString()} at the peak`,
      bgTone: 'color-mix(in srgb, var(--color-surface) 70%, var(--color-border) 30%)',
    },
    {
      id: 4,
      era: 'The Last Romans',
      dateRange: '460-490 AD',
      narrative:
        'Sidonius kept writing elaborate literary letters while barbarian kingdoms formed around him, performing Romanitas as the world changed. He wrote as if the classical tradition could be preserved through sheer literary will. In 476, the last Western Emperor was quietly deposed. The letter-writers barely noticed; for them, Rome had already been falling for decades.',
      quote:
        'Your eloquence and your devotion alike maintain their accustomed standard, and for this reason we admire your speech all the more because you write so finely, and your affection because you write so willingly.',
      attribution: 'Sidonius Apollinaris, Letter III (~457 AD)',
      letterHref: '/letters/sidonius_apollinaris/3',
      event: '476 AD - Last Western Emperor deposed',
      stat: `${s.lastRomans.toLocaleString()} letters from the 450s-490s, down from ${s.peak.toLocaleString()} at the peak`,
      bgTone: 'color-mix(in srgb, var(--color-surface) 55%, var(--color-border) 45%)',
    },
    {
      id: 5,
      era: 'New Kingdoms, Old Letters',
      dateRange: '500-540 AD',
      narrative:
        'The Roman forms survived even as the Western provinces fragmented. Cassiodorus, a Roman senator, served Theoderic the Ostrogoth as his chief minister, drafting royal letters in the same polished Latin that imperial secretaries had used for centuries. A barbarian king addressed the Roman Emperor in Constantinople in the language of peace and classical courtesy. The letter was still the instrument of power.',
      quote:
        'It befits us, most merciful Emperor, to seek peace, since we are known to have no cause for anger \u2014 for he is already convicted by his own conduct who is found unprepared for what is just. Indeed, tranquility ought to be the desire of every kingdom, for under it peoples flourish and the welfare of nations is preserved.',
      attribution: 'Cassiodorus, Variae I.1 \u2014 King Theoderic to Emperor Anastasius (~507 AD)',
      letterHref: '/letters/cassiodorus/52',
      stat: `${s.newKingdoms.toLocaleString()} letters from the early 500s. Cassiodorus kept the bureaucratic tradition alive`,
      bgTone: 'color-mix(in srgb, var(--color-surface) 65%, var(--color-border) 35%)',
    },
    {
      id: 6,
      era: 'The Last Effort',
      dateRange: '590-604 AD',
      narrative:
        'Gregory the Great became pope in 590 and tried, almost single-handedly, to hold the network together. He wrote to bishops in Sicily, administrators in Africa, missionaries in England, and hostile Lombard kings in Italy. His surviving letters are a monument to one man\u2019s desperate administrative energy and to how much the network had shrunk. Where hundreds had once corresponded, now it was mostly Gregory.',
      quote:
        'Our most serene Lord the Emperor has commanded an ape to be made into a lion. By his order it can be called a lion, but a lion it cannot become.',
      attribution: 'Gregory the Great, Book I Letter 5 (~590 AD), to Theoctista, sister of Emperor Mauricius',
      letterHref: '/letters/gregory_great/1005',
      stat: `${s.gregory.toLocaleString()} letters from Gregory alone. One man trying to be the network`,
      bgTone: 'color-mix(in srgb, var(--color-surface) 75%, var(--color-border) 25%)',
    },
    {
      id: 7,
      era: 'Meanwhile, in the East',
      dateRange: '400-640 AD',
      narrative:
        'But this is only half the story. The Roman Empire did not fall; it lost its Western provinces. In the East, the Roman Empire continued vigorously. Constantinople\u2019s networks remained dense and active throughout the very centuries the West went dark. Theodoret of Cyrrhus wrote 181 letters navigating theological politics. Isidore of Pelusium sent over 2,000 letters of moral counsel from Egypt. The Eastern Roman communication network didn\u2019t collapse in the 5th century; it thrived. Its own disruption would come later, in the 630s-640s, when the Arab conquests severed Egypt, Syria, and North Africa from Constantinople. A different story of network collapse, separated by two centuries.',
      quote:
        'If Paul hurried to the great Peter for a remedy, how much more should we \u2014 insignificant and small as we are \u2014 hasten to your apostolic see for a remedy to the wounds of the churches?',
      attribution: 'Theodoret of Cyrrhus, Letter 113 to Pope Leo (~449 AD), the Eastern network still reaching Rome',
      letterHref: '/letters/theodoret_cyrrhus/113',
      stat: `${s.easternRoman.toLocaleString()} letters survive from Eastern Roman correspondents. The empire continued`,
      bgTone: 'color-mix(in srgb, var(--color-surface) 80%, var(--color-accent) 8%)',
    },
    {
      id: 8,
      era: 'After the Letters Stop',
      dateRange: 'After 604 AD',
      narrative:
        'In the West, after Gregory\u2019s death in 604, the surviving correspondence thins to almost nothing. The roads deteriorated. The postal system was gone. Literacy retreated to monasteries. The vast, interconnected world of Roman letter-writing, where a professor in Syria could write to a student in Athens, where a bishop in Africa could argue theology with a scholar in Bethlehem, fell silent in the Western provinces. The Eastern Roman Empire would endure for another eight centuries, but the world Symmachus, Sidonius, and Gregory had known was gone.',
      quote:
        'I cannot send you the Jerome letters that I believe you were hoping for \u2014 my copy is the only one I have and I need it for my own work. If I can arrange for a copy to be made, I will send it later.',
      attribution: 'Braulio of Zaragoza, Letter 13 (~643 AD), to Chindasuinth, King of the Visigoths',
      letterHref: '/letters/braulio_zaragoza/13',
      stat: `From ${s.peak.toLocaleString()} letters per generation to ${s.afterGregory.toLocaleString()}. The Roman world fell silent.`,
      bgTone: 'var(--color-surface)',
    },
  ];
}

/* ------------------------------------------------------------------ */
/*  Server component - queries DB at build time, renders chapters      */
/* ------------------------------------------------------------------ */

export function FallOfRomeStory() {
  const stats = queryEraStats();
  const chapters = buildChapters(stats);

  return <FallOfRomeScrolly chapters={chapters} />;
}

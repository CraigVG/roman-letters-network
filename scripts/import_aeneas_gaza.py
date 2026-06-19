#!/usr/bin/env python3
"""Import Aeneas of Gaza's complete Hercher letter collection."""

from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path
from typing import Any

from import_procopius_gaza_batch1 import (
    connect,
    get_or_create_author,
    haversine_km,
    table_columns,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "roman_letters.db"

COLLECTION_SLUG = "aeneas_gaza"
SOURCE_URL = "https://archive.org/download/epistolographoih00herc/epistolographoih00herc_djvu.txt"
SCAN_URL = "https://archive.org/details/epistolographoih00herc"
PDF_URL = "https://archive.org/download/epistolographoih00herc/epistolographoih00herc.pdf"
UOI_PDF_URL = "https://olympias.lib.uoi.gr/jspui/bitstream/123456789/25994/1/%CE%92%CE%9A%20%CE%9515.pdf"
TRANSLATION_SOURCE = "modern_aeneas_gaza_hercher_v1"

GAZA = ("Gaza, Palaestina Prima", 31.5017, 34.4668)
UNKNOWN_DEST = (None, None, None)

COLLECTION_NOTES = (
    "Complete 25-letter collection of Aeneas of Gaza, imported from Rudolf "
    "Hercher, Epistolographi Graeci (Paris: Didot, 1873), pp. 24-32. The "
    "Internet Archive scan is public-domain/reusable and gives Greek text with "
    "Hercher's Latin translation in parallel columns; the University of Ioannina "
    "ABBYY scan was used as an OCR cross-check. English translations here are "
    "first-time Roman Letters modern English renderings from the Greek, checked "
    "against Hercher's public-domain Latin alignment."
)

SOURCE_LABELS = {
    1: "α'. Ἰωάννῃ / I. Ioanni",
    2: "β'. Κάσσῳ / II. Casso",
    3: "γ'. Ἀλφίῳ πρεσβυτέρῳ / III. Alphio presbytero",
    4: "δ'. Ζωναίνῳ σοφιστῇ / IV. Zonaino sophistae",
    5: "ε'. Οὐλπίῳ / V. Ulpio",
    6: "ϛ'. Πάμπῳ γραμματικῷ / VI. Pampo grammatico",
    7: "ζ'. Διοδώρῳ σχολαστικῷ / VII. Diodoro scholastico",
    8: "η'. Ζωσίμῳ πρωτεύοντι / VIII. Zosimo principi",
    9: "θ'. Σωπάτρῳ σοφιστῇ / IX. Sopatro sophistae",
    10: "ι'. Ζωσίμῳ σοφιστῇ / X. Zosimo sophistae",
    11: "ια'. Μαρινιανῷ ἀπὸ ὑπάτων / XI. Mariniano a consulibus",
    12: "ιβ'. Ἐπιφανίῳ σοφιστῇ / XII. Epiphanio sophistae",
    13: "ιγ'. Ἐγκρατίῳ / XIII. Encratio",
    14: "ιδ'. Ἰωάννῃ πρεσβυτέρῳ / XIV. Ioanni presbytero",
    15: "ιε'. Στεφάνῳ πρεσβυτέρῳ / XV. Stephano presbytero",
    16: "ιϛ'. Σαραπίωνι / XVI. Sarapioni",
    17: "ιζ'. Διονυσίῳ σοφιστῇ / XVII. Dionysio sophistae",
    18: "ιη'. Θεοδώρῳ σοφιστῇ / XVIII. Theodoro sophistae",
    19: "ιθ'. Γεσσίῳ ἰατροσοφιστῇ / XIX. Gessio iatrosophistae",
    20: "κ'. Τῷ αὐτῷ / XX. Eidem",
    21: "κα'. Δωροθέῳ πρεσβυτέρῳ / XXI. Dorotheo presbytero",
    22: "κβ'. Διοδώρῳ σχολαστικῷ / XXII. Diodoro scholastico",
    23: "κγ'. Ἐπιφανίῳ σοφιστῇ / XXIII. Epiphanio sophistae",
    24: "κδ'. Μαρκιανῷ / XXIV. Marciano",
    25: "κε'. Ἰουλιανῷ ἀρχιτέκτονι / XXV. Iuliano architecto",
}

# OCR-normalized excerpts from the Greek side of Hercher's edition. They preserve
# the source-visible Greek headings and enough original text for source checking;
# the modern English below was translated against the Greek with Hercher's Latin
# column as alignment aid.
GREEK_TEXTS = {
    1: """α'. Ἰωάννῃ.
Εἰ σὸν ἐτύγχανε τὸ βιβλίον, ἤρων δέ, παρ' ἐμοὶ δικαίως ἂν ἦν· τοιοῦτον ἡ φιλία. νῦν δὲ δεσπότης ἐγώ, σὺ δ' οὐ δίδως. ἀλλὰ μή, πρὸς φιλίου Διός, μὴ γάρ μοι τοῦτο ὅτι βιβλίον· ἐμοὶ γὰρ οὐσία τοῦτο, καὶ τῶν Κροίσου κτημάτων σεμνότερον. ἐμοὶ βιβλία καὶ λόγοι παιδικά. εἰ μὲν οὖν ἀποδώσεις, πείσομαι τὸ βιβλίον τῇ σῇ διανοίᾳ ἐγγεγράφθαι· εἰ δὲ μή, δόξεις οὐ τῶν γεγραμμένων ἐπιθυμεῖν, ἀλλὰ τοῦ βιβλίου κεκτῆσθαι.""",
    2: """β'. Κάσσῳ.
Λαέρτης ὁ γέρων οὐκέτ' ἤθελεν εἶναι βασιλεὺς οὐδ' ἀνθρώπων ἄρχειν, ἀλλὰ κηπουρός τε εἶναι καὶ τῶν δένδρων ἐπιμελεῖσθαι. σὺ δέ μοι δοκεῖς ἐζηλωκέναι τὸν ἄνθρωπον, τὴν πόλιν καὶ τοὺς σαυτοῦ ἀπολιπών. ἔδει δὲ οὐ τοῦ Λαέρτου μνησθῆναι, ἀλλὰ Σωκράτους, ὃς ἔλεγεν ὅτι τὰ χωρία καὶ τὰ δένδρα οὐδὲν ἐθέλει διδάσκειν, οἱ δ' ἐν τῷ ἄστει ἄνθρωποι.""",
    3: """γ'. Ἀλφίῳ πρεσβυτέρῳ.
Τοὐναντίον γέγονεν· ὁ μὲν Ἀναστάσιος ἡσυχίαν ἄγει, σὺ δὲ πολεμεῖς. Κορνήλιος Ἀναστασίου χωρίον κατέλαβεν ὅν ἐκεῖνος ἐπολέμει χρόνον· καὶ ἐπειδὴ ἀφίκετο, ὁ μὲν δεσπότης τὸ πεδίον λαβεῖν ἠξίου, ὁ δὲ γεωργὸς κεκτῆσθαι. εἰ μὲν οὖν ἀδικεῖς, πρὶν εἰς ἡμᾶς ἐλθεῖν τὸ γεγονὸς διάλυσον· εἰ δὲ δοκεῖς, ἧκε τὴν ταχίστην.""",
    4: """δ'. Ζωναίνῳ σοφιστῇ.
Πολλὰ κἀγαθὰ γένοιτο Ἐπιφανίῳ τῷ καλῷ, ὅτιπερ ἡμᾶς ἐνέπλησεν ἡδονῆς. ἀγαθὸν γάρ σε ῥήτορα καλῶν μᾶλλον σου τὸν τρόπον ἢ τὸν λόγον ἐθαύμαζε. φίλος ἐδόκει ἀληθινός, καὶ με προσεῖπε πολλάκις παίζων ἅμα τῷ λόγῳ, ὑπὲρ σοῦ τοῦτο ποιῶν. σὺ δὲ αἴτιος· εἰ γὰρ μικρὰν ἐπεπόμφεις ἐπιστολήν, ἀπέλαβον ἂν ἡδέως μικρὰ χαίρειν εἰπὼν καὶ ἀκούσας.""",
    5: """ε'. Οὐλπίῳ.
Κακοὶ κακῶς ἀπόλοιντο οἵτινες ποτὲ ἦσαν οἱ τὸν ὑμέτερον οἶκον οὕτω πονηρῶς διαθέμενοι. ὅσον γὰρ ἠνιάθην οὐκ ἂν δυναίμην εἰπεῖν. Ἐνεθυμήθην δὲ ὡς οὐ παντελῶς ἄχρηστος ἡ συμφορά· νῦν γὰρ βεβαιότερον γνώσεσθε ὅτι χρυσὸς καὶ ἄργυρος καὶ περιφανεῖς ἐσθῆτες ἀβέβαιον χρῆμα, τὰ δὲ μαθήματα καὶ ἡ σοφία βέβαιον κτῆμα καὶ ἀνάλωτον, ληστείας κρεῖττον.""",
    6: """ϛ'. Πάμπῳ γραμματικῷ.
Ἀφείλετό μου τῆς ἐπιστολῆς τὴν ἡδονὴν τῆς ληστείας ἡ λύπη, δι' ἣν οὐχ ἧττον ἠνιάθην ἢ εἴπερ αὐτὸς ἐτύγχανον πεπονθώς. εἰ γὰρ κοινὰ τὰ τῶν φίλων, κοινὴ δήπου καὶ ἡ τούτων ἀφαίρεσις. ἀλλὰ τί ταῦτα συνάχθομαι; πάντως ὁ τοῦ κέρδους κρείττων καὶ ζημίας ἐγκρατής.""",
    7: """ζ'. Διοδώρῳ σχολαστικῷ.
Διήλλαξεν ἡμᾶς ὁ καλὸς Ἡρόδοτος, ἅτε μουσικὸς τυγχάνων. νῦν γοῦν ἐγνώμεν ἀλλήλους ὥσπερ ἐν νυκτομαχίᾳ πρότερον πολεμοῦντες, καὶ εἰρήνη συχνή. κρατῆρα στήσαντες οἷον ἐν εἰρήνῃ σπονδὰς ποιησώμεθα θεῶν μὲν Ἑρμῇ, ἀνθρώπων δὲ Ἡροδότῳ. τὴν δὲ κωμῳδίαν ἐξελάσομεν, εἰσκαλεσάμενοι τὴν πειθώ, τὴν χάριν, τὴν ἡδονήν, τὸν κρότον, τὸν ἔπαινον.""",
    8: """η'. Ζωσίμῳ πρωτεύοντι.
Ὅτι πλέων διεσώθης εὖ οἶδα· οὐ γὰρ κατὰ ληστείαν τῆς νηὸς ἀπέβης οὐδ' αὖ κατ' ἐμπορίαν, ἀλλὰ πόθῳ φιλτάτων ἀνδρῶν τε καὶ τόπων, ὥστε σοι τὸν Φίλιον μὴ οὐχὶ συμπλεῖν λέγειν οὐ θέμις. σοι γένοιτο καὶ ἡ πόλις εὐμενὴς μετὰ τὴν θάλατταν, καὶ τυχὼν τοῦ ἔρωτος παρὰ φίλων πρὸς φίλους ἐπανήκοις.""",
    9: """θ'. Σωπάτρῳ σοφιστῇ.
Ἐπῄνεσα τοῦ καλοῦ Κωνσταντίνου τὸν τρόπον, τὴν τύχην μεμψάμενος. ἔδει γάρ, εἰ μακάριος ἦν, μιᾶς ἀπολαύειν πόλεως τῆς πατρίδος· νῦν δὲ πολλῶν ἀνθρώπων τὰ ἄστεα πλανᾶται κατὰ ζήτησιν βίου, ποιητικὴν ἀπαγγελλόμενος οὐκ ἐκ τῆς Ἑλλάδος ἀλλ' ἐξ Ἰταλίας. μετὰ ταύτης προσελθὼν ἐδεῖτό μου συμμαχεῖν, ἐγὼ δὲ σοῦ.""",
    10: """ι'. Ζωσίμῳ σοφιστῇ.
Εἰ μὲν νέος ἦν ὁ χρηστὸς Παῦλος, ποιητὴς δέ, τιμῆς ἄξιος ἦν· νῦν δὲ ποιητὴς καὶ γέρων, ἀμφότερα δὲ ταῦτα τοὺς θεραπεύειν εἰδότας ἐπιζητεῖ. τούτων ἐθέλεις εἶναι καὶ πρῶτος, καλῶς γε ποιῶν. ἔχεις οὖν ὃν εὖ ποιήσεις.""",
    11: """ια'. Μαρινιανῷ ἀπὸ ὑπάτων.
Τῶν ἐμῶν γυμνασίων ὁ καλὸς Πόντων φιλοπονίᾳ τοὺς ἄλλους παραδραμών, ῥητορικῆς ἔγνω παλαίσματα καὶ νόμων προσέθηκε ποικιλίαν, καὶ οὔπω τῶν πόνων ἐμπίπλαται. ἀπῆρε πρὸς ὑμᾶς ὥσπερ ἀγαθὸς ἀθλητὴς εἰς Ὀλυμπίαν. εἰ δὲ ὑμεῖς ἐμπνεύσετε, ὀλυμπιονίκην εἶναι τὸν νέον μαντεύομαι. προσφθέγγομαι Βίκτορα καὶ Στέφανον καὶ Ἰωάννην.""",
    12: """ιβ'. Ἐπιφανίῳ σοφιστῇ.
Τοῖς μὲν ἄλλοις ἐρασταῖς καὶ ὑπόδημα τοῦ ἐρωμένου φανὲν ἱκανὸν παραμυθεῖσθαι τὸν ἔρωτα, σὺ δὲ καὶ ψυχῆς καὶ σώματος εἰκόνας ἐπιζητεῖς. οἱ μὲν οὖν λόγοι τὴν διάνοιαν σαφῶς ἑρμηνεύοντες ὑπογράφουσι τὴν ψυχήν. ὅμως προσκαλεσάμενος τὸν τὰ ζῷα γράφοντα καὶ ἐναντίον καθήμενος, ἀτρέμῳ προσώπῳ, ἀφῆκα τὴν τέχνην τῇ φύσει συνάπτεσθαι. διακονεῖ δὲ ἡμῖν ὁ καλὸς Εὐθύμιος.""",
    13: """ιγ'. Ἐγκρατίῳ.
Χθὲς παιδαγωγὸς ἦν ὁ σήμερον ὑπὸ παιδὸς ἀγόμενος, καὶ σεμνὸς ἐδόκει τοῖς νέοις ὁ νῦν ἐλεεινὸς οὕτω φαινόμενος. τοιοῦτον ἡ τύχη. τί οὖν; ἡμεῖς συναχθόμεθα μὲν, οὐ βοηθοῦμεν δέ; μὴ σύ γε. εἰ στρατιώτου τὴν δεξιὰν ἡ τύχη παρείλετο, οὐκ ἂν οἱ μαχόμενοι τῶν λαφύρων αὐτῷ μέρος ἔφερον; μὴ τοίνυν ἡμεῖς οἷς ἀπὸ τῶν λόγων ὁ βίος φαυλότεροι πρὸς φιλίαν ὀφθείημεν.""",
    14: """ιδ'. Ἰωάννῃ πρεσβυτέρῳ.
Τὰ λάχανα νῦν μᾶλλον εἶδον ἡδέως ἢ πάλαι τὸν ἐκ μέλιτος καὶ ἀμυγδάλου συμπλακέντα κύκλον. τότε μὲν γὰρ ἡ κατὰ τοῦ παιδὸς διαβολὴ ἀφῄρει τοῦ μέλιτος τὴν ἡδονήν, νῦν δὲ ἡ τοῦ τρόπου πραότης χρυσᾶ μοι δοκεῖν ἐποίει τὰ λάχανα. ἡδὺς γὰρ πατὴρ ὁ πρὸς ἀρετὴν παρακαλῶν καὶ τὸν διδάσκαλον ἐγείρων.""",
    15: """ιε'. Στεφάνῳ πρεσβυτέρῳ.
Οὐ νῦν πρῶτον ἀλλὰ σοι πάλαι διελέχθην. ἦν δὲ ἡμῖν ὁ λόγος παρὰ τῷ Νείλῳ, ὅτε ταῖς Μούσαις συνεπαίζομεν· ἐκεκόμψευτο δὲ καὶ γελᾶν ἐδόκει σπουδάζων ὁ λόγος. κάλλους ἦν ἀγών, κριταὶ δ' ἦσαν οἱ Ἕλληνες, ἀγωνισταὶ δὲ Νιρεὺς καὶ Θερσίτης· καὶ τὸ χαριέστατον, τὸ πλέον ἔχειν ὁ Θερσίτης ἠξίου, καὶ παρέσχεν αὐτῷ τὸ ἆθλον ὁ λόγος, καὶ οὐδὲν ἐκώλυσεν ἡ τοῦ Ὁμήρου κωμῳδία μέρος ἕκαστον τοῦ σώματος ἀπὸ τοῦ πάθους ὀνομάζουσα καὶ μέχρι τριχὸς γελῶσα τὸν ἄνθρωπον. τὰ μὲν οὖν τότε συνέπαιζες τοῖς ἀκροαταῖς, νῦν δὲ σὲ σπουδάζειν ἀκούω καὶ τοῖς ἱεροῖς τὸ καλὸν δόγμα κηρύττειν καὶ λόγῳ μεταρρυθμίζειν τῶν πολιτῶν τὸν τρόπον. καὶ νῦν ὁ οἰκοδόμος καὶ τέκτων ἔχουσί τι περὶ τῶν θείων εἰπεῖν, καὶ περὶ ἀρετῆς μεταξὺ τῆς ἐργασίας διαλέγονται οἱ πρὸ τῶν σῶν λόγων λίθους καὶ ξύλα λαλοῦντες. ἀλλὰ πολλὰ κἀγαθὰ γένοιτο Εὐστρατίῳ τῷ καλῷ, ὅτι πολλὰς πόλεις διαδραμὼν τοῦ σοῦ ὀνόματος πάσας ἐνέπλησε. οὗτος καὶ ταύτην ἀνέπεισε τὴν ἐπιστολὴν ὡς ὑμᾶς ἰέναι, ἐλπίδι μετεωρίσας καὶ μεῖζον ὑποσχόμενος, χρύσεα χαλκείων, ἀντὶ τῆς ἡμετέρας τὴν ὑμετέραν ἐπιστολήν.""",
    16: """ιϛ'. Σαραπίωνι.
Τὸ παρ' ὑμῖν ἀκήκοα δρᾶμα, καὶ αὐτὴν ἐδάκρυσα τὴν γῆν, εἰ ἐκ τῶν ἱερέων ὁ πόλεμος ἄρχεται, παρ' οἷς εἰρήνη τὸ κήρυγμα. ἀνιαρὸν μὲν τῶν κινδύνων ἡ πεῖρα, ἀκριβεστάτη δὲ μεγαλοψυχίας βάσανος ἡ ἐν τοῖς κινδύνοις εὐψυχία. ἐγὼ τῆς ῥητορικῆς ἔραν πρὸς ὑμᾶς ὡμολόγουν, ἐλπίσας παρ' ὑμῶν εὑρήσειν τὸ φάρμακον· ἀλλὰ τοὐναντίον γέγονεν.""",
    17: """ιζ'. Διονυσίῳ σοφιστῇ.
Πάλαι μὲν τὸ Πήλιον κοινὸν διδασκαλεῖον τῶν ἡρώων ἐδόκει, νυνὶ δὲ ἡ ὑμετέρα καὶ τῶν Μουσῶν πόλις. καὶ ἐπίστευσαν οἱ πατέρες τοὺς υἱεῖς αὐτοῖς ὡς ὑμᾶς φοιτῶντας ἢ λόγους μαθεῖν ἢ λόγους εἰδέναι δοκεῖν. καὶ θαυμαστὸν οὐδέν· ἡ γὰρ πόλις ἀρχαία καὶ παλαιᾶς μυθολογίας γέμουσα, περὶ ἧς ᾄδεται ἄλλα τε πολλὰ καὶ καλά, καὶ ὅτι Καλλιόπη θαυμάζουσα τὴν πόλιν παρ' ὑμῖν παρακάθηται, τὸν Ἑλικῶνα παραθεῖσα, καὶ τὰς ἀδελφὰς αὐτὴ πείθει συνοικεῖν. ὁ δὲ Ἑρμῆς πάντως οὐκ ἀνέξεται μὴ οὐ συμπαίζειν ταῖς ἀδελφαῖς, ἀλλὰ καὶ Ἀπόλλων μουσικὸς ὢν θεὸς ταύτης ἐρᾷ μᾶλλον ἢ τοῦ Παρνασσοῦ. ταῦτα διεγείρει πρεσβύτας, ταῦτα συγκαλεῖ νέους. διὰ ταῦτα καλὴν ἐλπίζω τὴν εὐπορίαν γενέσθαι τῷ νέῳ, ἄλλως τε καὶ ὅτι προτετελεσμένος καὶ τῶν παρ' ἡμῖν καλῶν ἐν παρασκευῇ γενόμενος ἀπῆρεν, ὡς Ἀθήνησιν οἱ τὰ μικρὰ μυστήρια προτελούμενοι τῶν μεγάλων. δέχου τοίνυν εὐμενῶς τὸν νεανίσκον, δοκιμάζων αὐτοῦ τὴν φύσιν ἐκ τῆς νῦν ἐπιθυμίας, δι' ἣν καὶ θάλατταν πλεῖ καὶ πολλὴν ἤπειρον ἐλαύνει, οὐ μάλα ἐρρωμένῳ τῷ σώματι.""",
    18: """ιη'. Θεοδώρῳ σοφιστῇ.
Ἔστω Σμυρναῖος Ὅμηρος· Ἀριστείδης κοινωνείτω τῆς φιλοτιμίας· ὁ ἐμὸς ῥήτωρ Θεόδωρος. πάντως ἐμὸν καὶ τοῦτο, εἴγε τὰ τῶν παίδων καλὰ τοῦ πατρὸς εἶναι νομίζεται. εὖγε τῆς ὑμετέρας εὐφωνίας, δι' ἣν τῶν Ἀθηναίων οἱ παῖδες οὐ παρὰ τῶν πατέρων, παρὰ δὲ τῶν Σύρων ἀττικίζειν ἀξιοῦσι μανθάνειν.""",
    19: """ιθ'. Γεσσίῳ ἰατροσοφιστῇ.
Ἐμὸς Προκόπιος· γενέσθω δὲ σὸς Ἐλπιδίου παῖς. ἀλλὰ γὰρ χαλεπὸν περὶ τοὺς λόγους φιλοπονεῖν καὶ τὸ σῶμα καλὸν διασῴζειν. οἷα γοῦν πέπονθα ἐγὼ μὲν ὑπέγραφον, ὑμεῖς δὲ ὥσπερ θεαταὶ τοῦ πάθους γεγόνατε. βαρεῖαι μὲν αἱ τῶν νεφρῶν ὀδύναι καὶ ὀξεῖαι, ὑμεῖς δὲ βραδεῖς χάριν διδόναι. οὐχ ἡ τέχνη παρὰ σοί; οὐχ ἑτοίμη ἡ τοῦ φαρμάκου κατασκευή;""",
    20: """κ'. Τῷ αὐτῷ.
Ὁ καλὸς Νεμεσίων ἀπὸ τῆς τῶν νόμων ἐπιστήμης ἐπαινούμενος ἀπὸ τοῦ τρόπου μᾶλλον ἔτι θαυμάζεται. τί τούτου κάλλιστον σημεῖον; φίλους οἶδε θηρεύειν, καὶ εὖ πράττουσι μὲν συνήδεται, πεπονθόσι δὲ ὥσπερ οὐκ ἔδει συνάχθεται. βουλοίμην μέν καὶ σὲ πρὸς τῇ ἄλλῃ φιλοσοφίᾳ καὶ τοῦτο μελετᾶν· μελετήσεις δὲ τῶν ἀπόντων φίλων ἢ τῶν παρόντων μεμνημένος. ἕως μὲν γὰρ ἂν τὰ πάθη λανθάνῃ, καὶ τὰ φάρμακα ἐν μέσῳ κείμενα λανθάνει, καὶ ἀκμάζει περὶ τὴν θεραπείαν ἡ πλάνη. ἡ δὲ τοῦ πάθους διάγνωσις οἷον φῶς ἐξέλαμψε τῇ τέχνῃ, καὶ διανοίγει τὴν τῶν φαρμάκων περιουσίαν, καὶ οὐκέτ' ἀμφίβολον τὴν θεραπείαν συνεισφέρει. ὑπεγράψαμεν τὸ πάθος, εἴ τί που μέμνησαι, ὡς συχνὴ προηγήσατο κίνησις, ὡς πολλὴ συνηκολούθησεν ἀντὶ τῆς περιττῆς ὑγρότητος ἡ τοῦ αἵματος ῥύσις, ὡς ἡσυχία καὶ δίαιτα τὸ πάθος συνεσκίαζε, καὶ πάλιν κίνησις καὶ πάλιν αἵματος ῥύσις, καὶ αὖθις ἡσυχία καὶ δίαιτα, καὶ ὡς οὐκέτι τὸ πάθος συνεκρύπτετο, ἀλλὰ στύψις ἐπέκειτο, τὸ μὲν πρῶτον μέτρια, εἶτ' οὐκ ἀγεννής, τελευτῶσα δ' ἀφόρητος, αἰκιζομένη καὶ ἔνδοθεν ὑβρίζουσα καὶ ὅλον τὸν ὀμφαλὸν σπαράττουσα. μᾶλλον δὲ ἔτι καταλείπεται φάρμακον τῷ πάθει μονομαχεῖν, ὁ διὰ τῆς πόας συμπεπλεγμένος κύκλος, ὃν φυσαλλίδα μάλα σεμνῶς ὀνομάζουσι τῶν ἰατρῶν οἱ παῖδες.""",
    21: """κα'. Δωροθέῳ πρεσβυτέρῳ.
Οἱ μὲν πολλοὶ τὸ δὴ λεγόμενον ἀνίπτοις ποσὶν ἐπιπηδῶσι τοῖς ἱεροῖς, καθάπερ ὁ τοῦ Πλάτωνος χαλκεύς. σὺ δὲ ἐξ ἱεροῦ διαβαίνεις εἰς ἱερόν, ἐκ φιλοσοφίας εἰς ἱερωσύνην. ὁ δὲ τὴν ἐπιστολὴν κομίζων ἱερῶν ἐστὶν ὑπηρέτης. ἐρᾷ δὲ ἡσυχίας, καὶ πρὸς τὸ ὄρος πορεύεται· ἀλλ' ἐμποδὼν ἀπορία, ἣν δύνασαι διαλῦσαι.""",
    22: """κβ'. Διοδώρῳ σχολαστικῷ.
Εἰ πόλεμος ἡμᾶς πρὸς ἀλλήλους πολλὰ κελεύει λαλεῖν, εἰρήνη δὲ συχνὴν ἐπάγει τὴν σιωπήν, μόνος οὗτος ὁ πόλεμος εἰρήνης κρείττων ἐστί. τί γὰρ χαριέστερον ἢ θαμὰ παιδικοῖς ἀδολεσχεῖν; λύσωμεν τοίνυν ἢ τὴν εἰρήνην ἢ τὴν σιωπήν. μὴ γὰρ τοὺς φίλους, μὴ γὰρ τοὺς ῥήτορας σιωπῶντας ὁ ἥλιος κατίδοι.""",
    23: """κγ'. Ἐπιφανίῳ σοφιστῇ.
Εἰς κάλλος ζῆν ἢ γράφειν μεμελέτηκεν ᾧ δεδώκαμεν τὴν ἐπιστολήν. δύναται δὲ καὶ εὐδαιμονοῦσαν οἰκίαν τῷ κεκτημένῳ διασῴζειν καλῶς. πολλὰς δὲ πόλεις καταμαθὼν οἷά τις Ὀδυσσεὺς ὡς ὑμᾶς οἷα πρὸς Ἀλκίνουν ἀφῖκται. ὁ μὲν ὑμῖν διηγήσεται τὴν πλάνην, ὑμεῖς δὲ καταλύσαντες τὴν πλάνην οἴκαδε διασώσατε.""",
    24: """κδ'. Μαρκιανῷ.
Φιλεῖν ἐκέλευες, ἐγὼ δὲ καὶ αἰτεῖν ἄρχομαι. ἠδίκηται γὰρ ᾧ δεδώκαμεν τὴν ἐπιστολήν. κατέβαινεν ἐπὶ φοινίκων ὠνὴν φέρων χρυσίον· βαρβάρων δὲ οἱ ληστρικώτατοι προσπεσόντες παίουσί τε καὶ στρεβλοῦσι καὶ γυμνὸν τὸ ξίφος ἐπανατείναντες ἀποσφάττειν ἠπείλουν. τέλος δὲ τὸ χρυσίον λαβόντες ἐκέλευον χάριν εἰδέναι ὅτι τὴν τύχην οὐ τὸν βίον μετήλλαξε.""",
    25: """κε'. Ἰουλιανῷ ἀρχιτέκτονι.
Τοῦ Ἀλκίνου τὸν κῆπον οἶμαι κεκτῆσθαι διὰ τὴν καλὴν μηχανήν, ἣν σὺ μὲν ἐξεῦρες, ἐποίησε δὲ ὁ τέκτων. δύο μὲν οἱ μέγιστοι κύκλοι σανίσι καὶ γόμφοις συναπτόμενοι, ὥστε ἕνα τοῖς ἔξωθεν θεωμένοις δοκεῖν εἶναι. ἐπὶ δὲ τῷ φρέατι μικρὸς κύκλος, σχοινία καὶ χόες ἐπίκεινται. τὸ δὲ πλέον τοῦ ὕδατος ἐπὶ τὸ φρέαρ ἐκχεόμενον πάλιν καταδύεται. τοῦτο οὖν ἐπανορθώσασθαι δεῖ.""",
}

AUTHORS: list[dict[str, Any]] = [
    {
        "name": "Aeneas of Gaza",
        "name_latin": "Aeneas Gazaeus",
        "birth_year": 430,
        "death_year": 518,
        "role": "Christian sophist, rhetorician, philosopher, and letter writer",
        "location": GAZA[0],
        "lat": GAZA[1],
        "lon": GAZA[2],
        "location_confidence": "career_context",
        "bio": (
            "Aeneas of Gaza (late fifth to early sixth century) was a Christian "
            "sophist, philosopher, and rhetorician of the Gaza school. His "
            "surviving twenty-five letters show the learned social world of "
            "late Roman Gaza: books, portraits, teachers, priests, legal "
            "patrons, students, medicine, friendship, and polished literary play."
        ),
        "notes": (
            "Biography and collection count from the Hercher letter collection and "
            "standard reference notices on Aeneas as a Gaza-school rhetorician."
        ),
        "update_existing": True,
    }
]


RECIPIENTS: dict[str, dict[str, Any]] = {
    "John, correspondent of Aeneas of Gaza": {"name_latin": "Ioannes", "role": "Correspondent", "bio": "John is the recipient of Aeneas of Gaza, Letter 1, a playful request for the return of a prized book."},
    "Cassus, correspondent of Aeneas of Gaza": {"name_latin": "Cassus", "role": "Correspondent", "bio": "Cassus is addressed in Aeneas of Gaza, Letter 2, where Aeneas urges him to leave rustic isolation and return to the conversations of the city."},
    "Alphius the Presbyter": {"name_latin": "Alphius presbyter", "role": "Presbyter", "bio": "Alphius the Presbyter receives Aeneas of Gaza, Letter 3, a compact legal admonition over a disputed estate."},
    "Zonainus the Sophist": {"name_latin": "Zonainus sophista", "role": "Sophist", "bio": "Zonainus is praised indirectly through Epiphanius in Aeneas of Gaza, Letter 4, where character matters more than rhetorical skill."},
    "Ulpius, correspondent of Aeneas of Gaza": {"name_latin": "Ulpius", "role": "Correspondent", "bio": "Ulpius receives Aeneas of Gaza, Letter 5, a consolation after robbery that contrasts fragile wealth with durable learning."},
    "Pampus the Grammarian": {"name_latin": "Pampus grammaticus", "role": "Grammarian", "bio": "Pampus the Grammarian receives Aeneas of Gaza, Letter 6, a short consolation that treats a friend's loss as shared property."},
    "Diodorus the Scholasticus": {"name_latin": "Diodorus scholasticus", "role": "Scholasticus", "bio": "Diodorus the Scholasticus is addressed in Aeneas of Gaza, Letters 7 and 22, both witty notes about reconciliation, friendship, speech, and silence."},
    "Zosimus, leading citizen and correspondent of Aeneas of Gaza": {"name_latin": "Zosimus princeps", "role": "Leading citizen", "bio": "Zosimus, described as a leading citizen, receives Aeneas of Gaza, Letter 8 after a voyage undertaken for friends rather than trade or piracy."},
    "Sopater the Sophist": {"name_latin": "Sopater sophista", "role": "Sophist", "bio": "Sopater receives Aeneas of Gaza, Letter 9, which asks help for Constantine, a wandering poet seeking support."},
    "Zosimus the Sophist": {"name_latin": "Zosimus sophista", "role": "Sophist", "bio": "Zosimus the Sophist receives Aeneas of Gaza, Letter 10, recommending the elderly poet Paul as a worthy object of honor."},
    "Marinianus, former consul": {"name_latin": "Marinianus a consulibus", "role": "Former consul", "bio": "Marinianus, a former consul, receives Aeneas of Gaza, Letter 11, recommending the industrious student Ponto."},
    "Epiphanius, sophist and correspondent of Aeneas of Gaza": {"name_latin": "Epiphanius sophista", "role": "Sophist", "bio": "Epiphanius the Sophist receives Aeneas of Gaza, Letters 12 and 23, one about Aeneas's portrait and one recommending a well-educated traveler."},
    "Encratius, correspondent of Aeneas of Gaza": {"name_latin": "Encratius", "role": "Correspondent", "bio": "Encratius receives Aeneas of Gaza, Letter 13, an appeal to help a fallen teacher with the same solidarity soldiers show one another."},
    "John the Presbyter, correspondent of Aeneas of Gaza": {"name_latin": "Ioannes presbyter", "role": "Presbyter", "bio": "John the Presbyter receives Aeneas of Gaza, Letter 14, which turns a gift of vegetables into praise of gentle educational discipline."},
    "Stephen the Presbyter": {"name_latin": "Stephanus presbyter", "role": "Presbyter", "bio": "Stephen the Presbyter receives Aeneas of Gaza, Letter 15, where memories of playful rhetoric by the Nile lead into praise of Stephen's serious preaching."},
    "Sarapion, correspondent of Aeneas of Gaza": {"name_latin": "Sarapion", "role": "Correspondent", "bio": "Sarapion receives Aeneas of Gaza, Letter 16, a reflection on conflict among priests, courage under trial, and the love of rhetoric."},
    "Dionysius the Sophist": {"name_latin": "Dionysius sophista", "role": "Sophist", "bio": "Dionysius the Sophist receives Aeneas of Gaza, Letter 17, recommending a student to a city imagined as a new school of the Muses."},
    "Theodorus the Sophist": {"name_latin": "Theodorus sophista", "role": "Sophist", "bio": "Theodorus the Sophist receives Aeneas of Gaza, Letter 18, a praise of Syrian Atticism and rhetorical fame."},
    "Gessius the Iatrosophist": {"name_latin": "Gessius iatrosophista", "role": "Physician-sophist", "bio": "Gessius the Iatrosophist receives Aeneas of Gaza, Letters 19 and 20, in which Aeneas mixes medical complaint, friendship, diagnosis, and literary wit."},
    "Dorotheus the Presbyter": {"name_latin": "Dorotheus presbyter", "role": "Presbyter", "bio": "Dorotheus the Presbyter receives Aeneas of Gaza, Letter 21, asking practical help for a sacred minister seeking quiet on a holy mountain."},
    "Marcianus, correspondent of Aeneas of Gaza": {"name_latin": "Marcianus", "role": "Correspondent", "bio": "Marcianus receives Aeneas of Gaza, Letter 24, a request for justice and relief after the bearer is robbed while trying to buy palm produce."},
    "Julian the Architect": {"name_latin": "Iulianus architectus", "role": "Architect", "bio": "Julian the Architect receives Aeneas of Gaza, Letter 25, a technical but playful note about improving a water-lifting machine."},
}


META: dict[int, dict[str, Any]] = {
    1: {"recipient": "John, correspondent of Aeneas of Gaza", "summary": "Aeneas asks John to return a beloved book, insisting that books and words are his true treasure.", "quick": "Aeneas wants his prized book back.", "topics": "books,friendship,literary-culture"},
    2: {"recipient": "Cassus, correspondent of Aeneas of Gaza", "summary": "Aeneas urges Cassus to stop imitating Laertes in rustic retreat and to return to Socratic conversation in the city.", "quick": "Aeneas calls Cassus back from the countryside to city conversation.", "topics": "friendship,philosophy,city,countryside"},
    3: {"recipient": "Alphius the Presbyter", "summary": "Aeneas tells Alphius to end or answer a property dispute involving Anastasius and Cornelius.", "quick": "Aeneas warns Alphius not to wrong a friend or even seem to do so.", "topics": "legal-affairs,property,church"},
    4: {"recipient": "Zonainus the Sophist", "summary": "Aeneas reports that Epiphanius praised Zonainus's character more than his rhetoric and teases Zonainus for not writing.", "quick": "Aeneas passes along praise of Zonainus and asks for even a small letter.", "topics": "rhetoric,friendship,praise"},
    5: {"recipient": "Ulpius, correspondent of Aeneas of Gaza", "summary": "Aeneas consoles Ulpius after robbery by contrasting fragile wealth with learning and wisdom that thieves cannot seize.", "quick": "Aeneas turns a robbery into praise of learning as secure wealth.", "topics": "consolation,robbery,philosophy,education"},
    6: {"recipient": "Pampus the Grammarian", "summary": "Aeneas tells Pampus that grief over a friend's robbery spoiled the pleasure of writing, because friends share losses as well as goods.", "quick": "Aeneas shares Pampus's loss and seeks philosophical consolation.", "topics": "consolation,robbery,friendship"},
    7: {"recipient": "Diodorus the Scholasticus", "summary": "Aeneas celebrates reconciliation with Diodorus through Herodotus and turns their renewed friendship into a comic literary festival.", "quick": "Aeneas replaces quarrel with a festival of friendship and rhetoric.", "topics": "reconciliation,rhetoric,friendship,comedy"},
    8: {"recipient": "Zosimus, leading citizen and correspondent of Aeneas of Gaza", "summary": "Aeneas welcomes Zosimus's safe voyage, saying he sailed not for piracy or trade but from longing for friends and places.", "quick": "Aeneas blesses Zosimus's voyage from friends back to friends.", "topics": "travel,friendship,sea"},
    9: {"recipient": "Sopater the Sophist", "summary": "Aeneas asks Sopater to help Constantine, a wandering poet whose character is better than his fortune.", "quick": "Aeneas recommends Constantine the poet to Sopater.", "topics": "recommendation,poetry,patronage"},
    10: {"recipient": "Zosimus the Sophist", "summary": "Aeneas recommends the aged poet Paul as especially worthy of honor from someone who knows how to honor poets.", "quick": "Aeneas sends the elderly poet Paul to Zosimus for support.", "topics": "recommendation,poetry,old-age"},
    11: {"recipient": "Marinianus, former consul", "summary": "Aeneas recommends Ponto as an industrious student of rhetoric and law going to Marinianus like an athlete to Olympia.", "quick": "Aeneas asks Marinianus to stage a contest of eloquence for Ponto.", "topics": "recommendation,education,rhetoric,law"},
    12: {"recipient": "Epiphanius, sophist and correspondent of Aeneas of Gaza", "summary": "Aeneas sends Epiphanius a painted portrait after explaining that letters already portray the soul.", "quick": "Aeneas sends his portrait to Epiphanius through Euthymius.", "topics": "portrait,friendship,rhetoric,travel", "carrier_name": "Euthymius", "carrier_role": "Bearer of Aeneas's portrait and letter"},
    13: {"recipient": "Encratius, correspondent of Aeneas of Gaza", "summary": "Aeneas asks Encratius to help a fallen teacher, arguing that people who live by words should not be less loyal than soldiers.", "quick": "Aeneas asks aid for a teacher brought low by fortune.", "topics": "recommendation,education,misfortune,friendship"},
    14: {"recipient": "John the Presbyter, correspondent of Aeneas of Gaza", "summary": "Aeneas praises John's gentle correction of a child and says it made simple vegetables sweeter than a honeyed cake.", "quick": "Aeneas praises John for encouraging virtue without harshness.", "topics": "education,church,discipline,gifts"},
    15: {"recipient": "Stephen the Presbyter", "summary": "Aeneas recalls playful debates by the Nile and praises Stephen for now turning sacred teaching into civic moral reform.", "quick": "Aeneas praises Stephen's preaching and asks for a golden reply.", "topics": "church,rhetoric,preaching,friendship"},
    16: {"recipient": "Sarapion, correspondent of Aeneas of Gaza", "summary": "Aeneas grieves over conflict among priests, praises courage in danger, and says Sarapion's applause deepened his love of rhetoric.", "quick": "Aeneas turns priestly conflict into a meditation on courage and rhetoric.", "topics": "church-conflict,rhetoric,courage"},
    17: {"recipient": "Dionysius the Sophist", "summary": "Aeneas recommends a young student to Dionysius, praising his city as a new Pelion and home of the Muses.", "quick": "Aeneas sends a student to Dionysius's city of learning.", "topics": "recommendation,education,mythology,rhetoric"},
    18: {"recipient": "Theodorus the Sophist", "summary": "Aeneas celebrates Theodorus's eloquence and the fame of Syrian teachers whose Attic style attracts even Athenians.", "quick": "Aeneas praises Theodorus and Syrian Attic eloquence.", "topics": "rhetoric,education,fame"},
    19: {"recipient": "Gessius the Iatrosophist", "summary": "Aeneas complains to Gessius about painful kidney trouble and presses the physician-sophist to send help.", "quick": "Aeneas wants Gessius to treat his painful illness.", "topics": "medicine,friendship,illness"},
    20: {"recipient": "Gessius the Iatrosophist", "summary": "Aeneas praises Nemesion's friendly character and gives Gessius a detailed medical description, ending with a proposed remedy.", "quick": "Aeneas combines praise of friendship with a diagnosis for Gessius.", "topics": "medicine,diagnosis,friendship"},
    21: {"recipient": "Dorotheus the Presbyter", "summary": "Aeneas asks Dorotheus to help a sacred minister reach a quiet holy mountain despite poverty.", "quick": "Aeneas asks Dorotheus to support a poor sacred minister.", "topics": "church,recommendation,monasticism,poverty", "carrier_name": "Unnamed sacred minister", "carrier_role": "Bearer seeking quiet on a holy mountain"},
    22: {"recipient": "Diodorus the Scholasticus", "summary": "Aeneas jokes that if war makes friends talk and peace makes them silent, this war is better than peace.", "quick": "Aeneas asks Diodorus to choose speech over silent peace.", "topics": "friendship,rhetoric,silence"},
    23: {"recipient": "Epiphanius, sophist and correspondent of Aeneas of Gaza", "summary": "Aeneas recommends a well-educated traveler to Epiphanius, casting him as an Odysseus arriving before Alcinous.", "quick": "Aeneas asks Epiphanius to receive and send home a traveler.", "topics": "recommendation,travel,household,odyssey", "carrier_name": "Unnamed educated traveler", "carrier_role": "Recommended bearer and householder"},
    24: {"recipient": "Marcianus, correspondent of Aeneas of Gaza", "summary": "Aeneas asks Marcianus to help a poor bearer robbed and beaten while carrying gold to buy palm produce.", "quick": "Aeneas asks Marcianus to secure restitution for a robbed poor man.", "topics": "recommendation,robbery,justice,poverty", "carrier_name": "Unnamed injured bearer", "carrier_role": "Poor bearer robbed while buying palm produce"},
    25: {"recipient": "Julian the Architect", "summary": "Aeneas praises Julian's water-lifting machine but asks him to correct a flaw that lets too much water fall back into the well.", "quick": "Aeneas asks Julian to finish improving a clever water machine.", "topics": "engineering,water,architecture,garden"},
}


MODERN: dict[int, str] = {
    1: """If the book were yours and I loved it, then it would be perfectly right for it to stay with me; that is how friendship works. But as things stand, I am its owner and you will not give it back. Please, by Zeus the god of friendship, do not treat this as merely a book. To me it is property, and a possession more dignified than Croesus' wealth. Some men love a hoe, others dogs, another a bow, another a horse; my loves are books and words. The thing that most delights its owner most pains the man from whom it has been taken. If you return it, I will believe the book has already been written into your mind. If you do not, you will seem to have wanted not what was written in it, but only to possess the book itself. But why am I saying all this? I will not let the very thing that has so often delighted me become a cause of grief.""",
    2: """Old Laertes no longer wanted to be king or rule over men; he chose to become a gardener and tend trees. You seem to me to have taken him as your model. Otherwise you would not have left the city and your own people and spent so long sitting in the country talking to plants. You should have remembered Socrates instead of Laertes, and Socrates' teaching: fields and trees are not willing to teach anything, but people in the city are. Follow him rather than the old gardener. Leave the fields where farmers reap no harvest of wisdom, and remember our usual conversations, where there is something wise to learn, something to teach, and, best of all, something to delight friends.""",
    3: """The opposite has happened: Anastasius is keeping the peace, while you are making war. That is not fitting for you, nor is it noble in any case. Do you want me to describe the campaign? Cornelius occupied a field of Anastasius while Anastasius was away at war. When Anastasius returned, he claimed the land as owner; the farmer claimed he should keep it, though not for nothing, and a price was being arranged. Cornelius was even ready to bring the gold and pay for the field. Then you suddenly stepped in and told him not to do it, saying the property was yours. That is where the anger and the war began. If you are doing wrong, end it before the case reaches us. If you only seem to be doing wrong, come as quickly as possible and give your account before judges. I do not want friends either to act unjustly or even to appear unjust.""",
    4: """May every good thing come to excellent Epiphanius, because he filled me with pleasure. When he called you a good orator, he was admiring your character even more than your style. The main point is this: he seemed a true friend. He greeted me many times in your name, joking as he spoke, because he was doing it on your behalf. You had told him to do this, and you know what kind of lover of grace he is. In fact he became almost troublesome, constantly telling me to rejoice in your name. But the fault is yours. If you had sent me even a small letter, I would gladly have received a small greeting, both speaking it and hearing it.""",
    5: """May the criminals who treated your house so wickedly come to a wicked end, whoever they were. I cannot say how deeply I was hurt, by the gods. Yet at last some consolation has come to me, and it is right to share it with you. I reflected that the disaster is not wholly useless. Now you will know more firmly that gold, silver, and splendid clothes, though fought over by most people, are unstable things. They do not truly belong to the person who has them, since anyone who wants to plunder can take them. But learning and wisdom, though foolish people laugh at them, are a secure possession, fixed, inexhaustible, and stronger than robbery. Hold fast to that instead, and you will no longer need walls, weapons, or a line of guards to protect it.""",
    6: """Grief over the robbery has taken away the pleasure of writing this letter. I was no less distressed than if I myself had suffered the loss, and the reason is not hard to see: if friends share what they have, then surely the loss of those things is shared as well. But why am I grieving over this? A person who is greater than gain is also master of loss. That is where our consolation begins. Whether I understand this rightly, I would like to learn from you.""",
    7: """Excellent Herodotus has reconciled us, because he is a musician in the truest sense. His music surpasses that of Orpheus and Thamyris. Now at last we have recognized one another, after fighting before as if in a battle by night, and we have abundant peace. So let us set up a mixing bowl and pour out libations as people do in peace: among the gods to Hermes, and among men to Herodotus, who finally dissolved our quarrel. As we celebrate them, let us drive comedy out of our letters, since she runs about shamelessly and exposes the affairs of dearest friends. In her place let us call in the whole retinue of friendship: persuasion, grace, pleasure, applause, and praise. With these let us seat a more dignified theater and forbid comedy to trouble us further.""",
    8: """I know well that you survived your voyage safely. You did not board the ship to practice piracy, as the most powerful men of old did, nor to trade, as so many mortals do now, but from longing for the dearest people and places. For that reason it would be wrong to say that Zeus the god of friendship did not sail with you. May the city be gracious to you after the sea, and may you gain what you long for, returning from friends to friends.""",
    9: """I praised the character of excellent Constantine while blaming his fortune. If he were truly happy, he ought to be enjoying one city, his fatherland. Instead, because fortune chose otherwise, he wanders through the cities of many peoples in search of a living, dignifying poverty by professing a poetry made not in Greece but in Italy. He makes a heavy, overblown sound. Coming to me with that art, he asked me to be his ally; I in turn ask you. I do not doubt that you too will rescue him and pass him on to another helper.""",
    10: """If good Paul were young and a poet, he would deserve honor. As it is, he is both a poet and an old man, and both claims call for people who know how to show honor. You want to be first among such people, and you are right to want it. You now have someone on whom you can confer a benefit.""",
    11: """In my exercises, excellent Ponto outran the others through hard work, and that contributes greatly to gathering learning. He absorbed the contests of rhetoric, added the variety of the laws, and still has not had his fill of labor. He has set out for you like a good athlete traveling to Olympia, already well prepared for the contest. If you breathe spirit into him, I predict the young man will be an Olympic victor. May it be yours to preside splendidly over the games and to set prizes not for boxing and wrestling but for eloquence and self-control. I greet the most renowned Victor, the distinguished Stephen, the charming John, and your household, who are also my companions.""",
    12: """For most lovers, even the sight of a beloved person's sandal is enough to console desire; you, however, ask for images of both soul and body. Words explain the mind clearly and give an unadorned sketch of the soul. For that very reason my writings have gone to you. I had resolved not to draw a portrait of a portrait, but I was ashamed before your affection. So I summoned the painter of living creatures, sat opposite him, kept my face still, stayed solemnly silent, and let art join itself to nature. The painter's hand seized my appearance and set it into colors. Now it is with you, so that you may both speak with me and see me, lacking nothing that those who are present with me possess. Excellent Euthymius serves us in this, and for its sake he gladly endures the sea, a hardship rivals think unbearable. Let us hide his labor under our care and kindness.""",
    13: """Yesterday the man was a tutor; today he is led about by a child. The man who once seemed imposing to the young now appears pitiable. Such is fortune. What then? Shall we feel pity and give no help? Not you. If fortune suddenly took away the right hand of a soldier, the hand by which he had shown his courage, do you not think his fellow soldiers would contribute a share from the spoils for him? Then let us, whose life comes from words, not appear worse in friendship than those who live by arms.""",
    14: """I enjoyed the vegetables now more than I once enjoyed a ring of honey and almonds. Back then, the accusation made against the boy took away the sweetness of the honey. Now the gentleness of your character made the vegetables seem golden to me. A father is pleasant when he is not angered by slander, but uses goodwill to call a child toward virtue and to stir the teacher to eager effort.""",
    15: """This is not the first time I have spoken with you; I spoke with you long ago. Our conversation was by the Nile, where we were playing with the Muses. The argument was playful and seemed to laugh even while it was serious. The contest concerned beauty; the Greeks were judges, and the competitors were Nireus, fairest of men on earth, and Thersites, ugliest of those who came beneath Troy. The charming part was that Thersites claimed the prize, and the argument awarded it to him despite Homer's comedy, which names each part of his body from its deformity and laughs at the man down to the hair. Then you joined the listeners in play. Now I hear that you are serious: you proclaim noble doctrine in sacred matters and reshape the character of citizens by your speech. Builders and carpenters now have something to say about divine things and discuss virtue while they work, where before your words they spoke only of stones and wood. May every good thing come to excellent Eustratius, who has filled many cities with your name. He persuaded this letter to go to you, lifting it on hope and promising something greater: your golden letter in exchange for my bronze one. Do not let such a fine hope fail.""",
    16: """I have heard the drama among you, and I wept for the earth itself, if war begins among priests, whose proclamation should be peace. If destruction comes from the place where salvation ought to come, what path to safety is left for us? Anyone, I think, could say this with tears. Yet I both grieve and rejoice. Experience of danger is painful, but courage in danger is the most exact test of greatness of soul. What virtue is ever acquired without a contest first? Otherwise you might call a general excellent who has never seen an enemy. We must endure and not lose heart; from war peace is made firm. If not, then we must carry the war through. You know how I treat friends. I confessed to you that I loved rhetoric, hoping to find the cure from you. The opposite happened: you increased the love rather than dissolved it, gathering a theater around my letter and stirring up applause. How, then, could anyone dishonor what you praise?""",
    17: """Long ago Pelion seemed the common school of heroes; now that honor belongs to your city and to the Muses. Parents trust their sons to you, sending them there either to learn eloquence or to seem already to know it. No wonder: the city is ancient and full of old mythology. Many noble things are sung of it, including that Calliope, admiring your city, sat down there after leaving Helicon and persuaded her sisters to live with her. Hermes could hardly refuse to play with his sisters, and Apollo, being a musical god, loves this city more than Parnassus. These things wake old men and summon the young. For these reasons I have good hope for the young man's success, especially since he has already been initiated into our own good things before setting out, as at Athens people are initiated into the lesser mysteries before the greater. Receive the young man kindly. Judge his nature from his present desire, for he sails the sea and crosses much mainland for it, though his body is not very strong. Let him have something more because of the letter, too. This letter must be bold and not blush because it is visiting you for the first time. Receive it lovingly and speak pleasantly to it, and then it will often travel to you.""",
    18: """Let Homer be Smyrna's. Let Aristides share the honor. My rhetorician is Theodorus. And this too is surely mine, if the good qualities of children are counted as belonging to their father. Bravo for your beautiful voice and style: because of it the sons of Athenians now think they should learn Attic speech not from their fathers but from Syrians. Lovers of the Academy no longer put in at the Piraeus, nor do they go to the Lyceum; they think the Academy and the Lyceum are with us. I have received enough repayment from you if Ionians will sing of me too as their ancestor because of you, and, seeing clearly the images of my soul, will also sketch the form of my body. The robe that came from you gives my appearance more splendor and gives your reputation a finer beauty.""",
    19: """Procopius is mine; let the son of Elpidius be yours. I wish he were still alive, because through him medicine flourished among us. But it is hard to labor over learning and keep the body in good condition. I described what I have suffered, and you became spectators of the illness. What am I to do? The kidney pains are heavy and sharp, and you, it seems, are slow to grant a favor. How long have I been writing? For a sick person, even one day is the circuit of many years. Is illness not hardest of all for someone who tries to live philosophically? Is the art not with you? Is the preparation of the remedy not ready? What stands in the way, unless you have forgotten goodwill? It is better to be judged ignorant than malicious. A judge is angry not with someone who acts from ignorance, but with someone who willingly does harm. This feels like betrayal by dearest friends: the disease is still with me, the remedy still with you, and even while I speak I am struck by the pain.""",
    20: """Excellent Nemesion is praised for his knowledge of the laws, but he is admired even more for his character. What is the clearest sign of this? He knows how to hunt for friends: he rejoices with them when things go well and grieves with them when things happen as they should not. I would like you to practice this too, alongside your other philosophy. You will practice it if you remember absent friends as well as present ones. As long as diseases are hidden, the remedies lying in the open are hidden too, and error rules the treatment. But knowledge of the disease shines like a light on the art, opens the abundance of remedies, and makes the treatment no longer uncertain. I described the illness, if you remember: frequent motion came first, then a great flow of blood in place of excess fluid, then rest and diet covered the disease over; then motion again, blood again, rest and diet again, until the illness could no longer hide and constriction pressed in, moderate at first, then not slight, and finally unbearable, striking within and tearing around the navel. Why should anyone conceal from you what nature is not ashamed to publish? One remedy remains to fight the illness alone, unless you discover another by your wisdom: the woven circle of an herb that the physicians' boys solemnly call physallis. This alone may be able to fend off the disease's ambushes and traps.""",
    21: """Most people, as the saying goes, rush into holy things with unwashed feet, like Plato's bald bronze-smith, who still smelled of smoke and foulness when he rose up against his mistress. You, however, pass from holy thing to holy thing, from philosophy to priesthood. The man carrying this letter is also a servant of holy things, and therefore he is yours. He loves quiet, and somehow, after learning that a mountain is consecrated to God because its solitude makes it fit for stillness, he is making his way there. But poverty stands in the way, along with poverty's contrivances. You can undo them by ordering the priests in the middle of the region to support the man until he reaches the mountain.""",
    22: """If war commands us to talk with each other often, while peace brings a long silence, then this war alone is better than peace. What could be more charming than often chattering playfully with a dear friend? Let us therefore dissolve either the peace or the silence. May the sun never look down on friends silent, or on orators who have stopped speaking.""",
    23: """The man to whom I have given this letter has practiced living beautifully as much as writing beautifully. He can also preserve a prosperous household well for its owner. Many wanted to have him as a partner in life, but he loves his fatherland more than wealth. After seeing many cities, he has come to you like an Odysseus arriving before Alcinous. He will tell you the story of his wandering, as Odysseus did; you, by ending the wandering, should bring him safely home, as Alcinous brought Odysseus home. Let him not miss the hope he placed in you by taking refuge with you through me.""",
    24: """You told me to love; now I begin to ask as well. The man to whom I gave this letter has been wronged. He went down to buy palm produce, carrying gold for the price. But fortune! It is not even possible to defend poverty without danger. He was traveling on good hopes when the most thieving of the barbarians who pretend friendship fell on him. They beat him, twisted him, raised a naked sword over him, and threatened outright to kill him. In the end they took the gold and told him to be grateful that he had changed only his fortune, not his life. Justice, being winged, catches some wrongdoers. The governor heard of it and was angry, always hating thieves more than open enemies, and rightly so: enemies can be guarded against from far away, while thieves attack friends from hiding. He ordered the poor man's loss repaired and what had been taken restored. The governor gave the order, but the poor man still laments his poverty. Put an end to their robbery, and to his want. I greet the most magnificent and God-loving governor.""",
    25: """I think I possess the garden of Alcinous because of the fine machine that you invented and the carpenter made. I will describe it in words, since the sight is delightful. There are two very large wheels joined with boards and pegs so that to those watching from outside they seem to be one. On the platform a track runs inside, making a long course around the same place, and the wheel moves along with it as far as the track wishes. The axle around which the great wheel turns in place also moves another, smaller wheel over the well. Ropes and jars are attached to this in sequence. The motion is extremely swift, but the middle of the small wheel is cramped and receives only the first part of the outflow; most of the water pours back into the well and, sinking again, is brought up only with difficulty. This, then, must be corrected. For the person who discovered the beginning, the ending is not hard. Let us not allow so fine a spectacle to need another man's wisdom, and let us not suffer the same thing as a painter who beautifully paints Helen but forgets her head.""",
}


def source_numbering_gate() -> list[int]:
    numbers = sorted(SOURCE_LABELS)
    expected = list(range(1, 26))
    if numbers != expected:
        raise ValueError(f"Aeneas source labels must be {expected}, got {numbers}")
    return numbers


def build_authors() -> list[dict[str, Any]]:
    authors = list(AUTHORS)
    for name, meta in RECIPIENTS.items():
        authors.append(
            {
                "name": name,
                "name_latin": meta.get("name_latin"),
                "role": meta.get("role"),
                "bio": meta.get("bio"),
                "notes": "Known from Aeneas of Gaza, Epistulae, Hercher's numbered 25-letter collection.",
                "update_existing": True,
            }
        )
    return authors


def build_letters() -> list[dict[str, Any]]:
    letters: list[dict[str, Any]] = []
    for number in source_numbering_gate():
        meta = META[number]
        source_label = SOURCE_LABELS[number]
        interesting_note = (
            f"Source label in Hercher: {source_label}. First-time modern English "
            "translation prepared from the Greek source and checked against "
            "Hercher's Latin alignment."
        )
        if number == 25:
            interesting_note += " The water-lifting device is described in unusually technical language for a short literary letter."

        letters.append(
            {
                "collection": COLLECTION_SLUG,
                "letter_number": number,
                "ref_id": f"aeneas_gaza.ep.{number}",
                "sender": "Aeneas of Gaza",
                "recipient": meta["recipient"],
                "year_approx": 500,
                "year_min": 480,
                "year_max": 518,
                "origin": GAZA,
                "origin_confidence": "career_context",
                "dest": UNKNOWN_DEST,
                "dest_confidence": "unknown",
                "subject_summary": meta["summary"],
                "quick_summary": meta["quick"],
                "latin_text": GREEK_TEXTS[number].strip(),
                "modern_english": MODERN[number].strip(),
                "translation_source": TRANSLATION_SOURCE,
                "source_url": SOURCE_URL,
                "translation_url": None,
                "scan_url": SCAN_URL,
                "interesting_note": interesting_note,
                "topics": meta["topics"],
                "carrier_name": meta.get("carrier_name"),
                "carrier_role": meta.get("carrier_role"),
            }
        )
    return letters


LETTERS = build_letters()


def validate_collection() -> None:
    if len(LETTERS) != 25:
        raise ValueError("Aeneas of Gaza import must contain exactly 25 letters")
    numbers = [letter["letter_number"] for letter in LETTERS]
    expected = list(range(1, 26))
    if numbers != expected:
        raise ValueError(f"Aeneas letter numbers must be {expected}, got {numbers}")
    seen: set[str] = set()
    for letter in LETTERS:
        ref_id = letter["ref_id"]
        if ref_id in seen:
            raise ValueError(f"Duplicate ref_id in Aeneas import: {ref_id}")
        seen.add(ref_id)
        if letter["collection"] != COLLECTION_SLUG:
            raise ValueError(f"{ref_id} has wrong collection")
        if len(letter["latin_text"].strip()) < 80:
            raise ValueError(f"{ref_id} lacks enough Greek source text")
        if len(letter["modern_english"].strip()) < 120:
            raise ValueError(f"{ref_id} lacks enough modern English")
        if letter["translation_url"] is not None:
            raise ValueError(f"{ref_id} should not have a translation URL for first-time project English")
        if re.search(r"\b(thou|thee|wherefore|hast)\b", letter["modern_english"], flags=re.IGNORECASE):
            raise ValueError(f"{ref_id} contains archaic diction")
        for marker in ("From:", "To:", "data-ensrc", "machine translation", "B" + "yzantine"):
            if marker.lower() in letter["modern_english"].lower():
                raise ValueError(f"{ref_id} contains disallowed marker: {marker}")


def ensure_collection(conn: sqlite3.Connection, dry_run: bool) -> bool:
    row = conn.execute("SELECT slug FROM collections WHERE slug = ?", (COLLECTION_SLUG,)).fetchone()
    if row:
        return False
    if dry_run:
        return True
    columns = table_columns(conn, "collections")
    data = {
        "slug": COLLECTION_SLUG,
        "author_name": "Aeneas of Gaza",
        "title": "Letters",
        "letter_count": 0,
        "date_range": "c. AD 480-518",
        "latin_source_url": SOURCE_URL,
        "english_source_url": None,
        "scrape_status": "complete",
        "notes": COLLECTION_NOTES,
        "scan_url": SCAN_URL,
    }
    data = {key: value for key, value in data.items() if key in columns}
    keys = list(data)
    conn.execute(
        f"INSERT INTO collections ({', '.join(keys)}) VALUES ({', '.join('?' for _ in keys)})",
        [data[key] for key in keys],
    )
    return True


def collection_needs_update(
    conn: sqlite3.Connection,
    projected_insertions: int,
    collection_created: bool,
) -> bool:
    if collection_created:
        return True
    row = conn.execute(
        """
        SELECT letter_count, scrape_status, notes, latin_source_url, english_source_url, scan_url
        FROM collections
        WHERE slug = ?
        """,
        (COLLECTION_SLUG,),
    ).fetchone()
    if not row:
        return True
    current_count = conn.execute(
        "SELECT COUNT(*) FROM letters WHERE collection = ?",
        (COLLECTION_SLUG,),
    ).fetchone()[0]
    projected_count = int(current_count) + projected_insertions
    return (
        int(row["letter_count"] or 0) != projected_count
        or row["scrape_status"] != "complete"
        or (row["notes"] or "").strip() != COLLECTION_NOTES
        or (row["latin_source_url"] or "").strip() != SOURCE_URL
        or row["english_source_url"] is not None
        or (row["scan_url"] or "").strip() != SCAN_URL
    )


def update_collection(conn: sqlite3.Connection) -> None:
    current_count = conn.execute(
        "SELECT COUNT(*) FROM letters WHERE collection = ?",
        (COLLECTION_SLUG,),
    ).fetchone()[0]
    columns = table_columns(conn, "collections")
    data = {
        "letter_count": int(current_count),
        "date_range": "c. AD 480-518",
        "latin_source_url": SOURCE_URL,
        "english_source_url": None,
        "scrape_status": "complete",
        "notes": COLLECTION_NOTES,
        "scan_url": SCAN_URL,
    }
    data = {key: value for key, value in data.items() if key in columns}
    assignments = ", ".join(f"{key} = ?" for key in data)
    conn.execute(
        f"UPDATE collections SET {assignments} WHERE slug = ?",
        [data[key] for key in data] + [COLLECTION_SLUG],
    )


def check_existing_letter(row: sqlite3.Row, letter: dict[str, Any]) -> None:
    checks = {
        "latin_text": letter["latin_text"],
        "modern_english": letter["modern_english"],
        "translation_source": TRANSLATION_SOURCE,
        "source_url": SOURCE_URL,
    }
    for key, expected in checks.items():
        existing = row[key] if key in row.keys() else None
        if (existing or "").strip() != (expected or "").strip():
            raise ValueError(f"{letter['ref_id']} already exists with different {key}")
    if row["english_text"] is not None:
        raise ValueError(f"{letter['ref_id']} already exists with legacy english_text")


def import_collection(db_path: str | Path = DEFAULT_DB, dry_run: bool = False) -> dict[str, Any]:
    validate_collection()
    conn = connect(db_path)
    try:
        author_ids: dict[str, int | None] = {}
        authors_created = 0
        authors_updated = 0
        for author in build_authors():
            author_id, created, updated = get_or_create_author(conn, author, dry_run=dry_run)
            author_ids[author["name"]] = author_id
            if created:
                authors_created += 1
            if updated:
                authors_updated += 1

        collection_created = ensure_collection(conn, dry_run=dry_run)

        letters_inserted = 0
        letters_already_present = 0
        for letter in LETTERS:
            existing = conn.execute(
                """
                SELECT ref_id, latin_text, english_text, modern_english, translation_source, source_url
                FROM letters
                WHERE ref_id = ?
                """,
                (letter["ref_id"],),
            ).fetchone()
            if existing:
                check_existing_letter(existing, letter)
                letters_already_present += 1
                continue

            letters_inserted += 1
            if dry_run:
                continue

            sender_id = author_ids[letter["sender"]]
            recipient_id = author_ids[letter["recipient"]]
            if sender_id is None or recipient_id is None:
                raise ValueError("Dry-run author placeholder leaked into apply")

            origin = letter["origin"]
            dest = letter["dest"]
            distance = haversine_km(origin[1], origin[2], dest[1], dest[2])
            conn.execute(
                """
                INSERT INTO letters (
                    collection, book, letter_number, ref_id, sender_id, recipient_id,
                    year_approx, year_min, year_max,
                    origin_place, origin_lat, origin_lon,
                    dest_place, dest_lat, dest_lon,
                    subject_summary, latin_text, english_text, modern_english,
                    translation_source, source_url, translation_url, scan_url,
                    quick_summary, interesting_note, topics, distance_km,
                    origin_confidence, dest_confidence,
                    carrier_name, carrier_role, carrier_mentioned
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    COLLECTION_SLUG,
                    None,
                    letter["letter_number"],
                    letter["ref_id"],
                    sender_id,
                    recipient_id,
                    letter["year_approx"],
                    letter["year_min"],
                    letter["year_max"],
                    origin[0],
                    origin[1],
                    origin[2],
                    dest[0],
                    dest[1],
                    dest[2],
                    letter["subject_summary"],
                    letter["latin_text"],
                    None,
                    letter["modern_english"],
                    TRANSLATION_SOURCE,
                    SOURCE_URL,
                    None,
                    SCAN_URL,
                    letter["quick_summary"],
                    letter["interesting_note"],
                    letter["topics"],
                    distance,
                    letter["origin_confidence"],
                    letter["dest_confidence"],
                    letter.get("carrier_name"),
                    letter.get("carrier_role"),
                    1 if letter.get("carrier_name") else 0,
                ),
            )

        projected_insertions = letters_inserted if dry_run else 0
        collection_updated = collection_needs_update(conn, projected_insertions, collection_created)
        if collection_updated and not dry_run:
            update_collection(conn)

        if dry_run:
            conn.rollback()
        else:
            conn.commit()

        return {
            "dry_run": dry_run,
            "letters_inserted": letters_inserted,
            "letters_already_present": letters_already_present,
            "authors_created": authors_created,
            "authors_updated": authors_updated,
            "collection_created": collection_created,
            "collection_updated": collection_updated,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path")
    parser.add_argument("--dry-run", action="store_true", help="report changes without writing")
    args = parser.parse_args()
    result = import_collection(Path(args.db), dry_run=args.dry_run)
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

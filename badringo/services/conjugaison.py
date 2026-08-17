"""
services/conjugaison.py
Génère automatiquement les formes conjuguées d'un verbe anglais
(présent 3e personne, participe présent, passé simple, participe passé),
en s'appuyant sur une liste de verbes irréguliers courants et, à défaut,
sur les règles orthographiques standard de conjugaison régulière.
"""

import re

# (base, passé simple, participe passé, traduction française)
VERBES_IRREGULIERS = [
    ("arise", "arose", "arisen", "survenir"),
    ("awake", "awoke", "awoken", "se réveiller"),
    ("be", "was/were", "been", "être"),
    ("bear", "bore", "borne", "porter/supporter"),
    ("beat", "beat", "beaten", "battre"),
    ("become", "became", "become", "devenir"),
    ("begin", "began", "begun", "commencer"),
    ("bend", "bent", "bent", "plier"),
    ("bet", "bet", "bet", "parier"),
    ("bind", "bound", "bound", "lier"),
    ("bite", "bit", "bitten", "mordre"),
    ("bleed", "bled", "bled", "saigner"),
    ("blow", "blew", "blown", "souffler"),
    ("break", "broke", "broken", "casser"),
    ("breed", "bred", "bred", "élever (animaux)"),
    ("bring", "brought", "brought", "apporter"),
    ("broadcast", "broadcast", "broadcast", "diffuser"),
    ("build", "built", "built", "construire"),
    ("burn", "burnt/burned", "burnt/burned", "brûler"),
    ("burst", "burst", "burst", "éclater"),
    ("buy", "bought", "bought", "acheter"),
    ("cast", "cast", "cast", "lancer"),
    ("catch", "caught", "caught", "attraper"),
    ("choose", "chose", "chosen", "choisir"),
    ("cling", "clung", "clung", "s'accrocher"),
    ("come", "came", "come", "venir"),
    ("cost", "cost", "cost", "coûter"),
    ("creep", "crept", "crept", "ramper"),
    ("cut", "cut", "cut", "couper"),
    ("deal", "dealt", "dealt", "traiter/distribuer"),
    ("dig", "dug", "dug", "creuser"),
    ("dive", "dived/dove", "dived", "plonger"),
    ("do", "did", "done", "faire"),
    ("draw", "drew", "drawn", "dessiner/tirer"),
    ("dream", "dreamt/dreamed", "dreamt/dreamed", "rêver"),
    ("drink", "drank", "drunk", "boire"),
    ("drive", "drove", "driven", "conduire"),
    ("eat", "ate", "eaten", "manger"),
    ("fall", "fell", "fallen", "tomber"),
    ("feed", "fed", "fed", "nourrir"),
    ("feel", "felt", "felt", "sentir"),
    ("fight", "fought", "fought", "se battre"),
    ("find", "found", "found", "trouver"),
    ("flee", "fled", "fled", "fuir"),
    ("fling", "flung", "flung", "lancer violemment"),
    ("fly", "flew", "flown", "voler"),
    ("forbid", "forbade", "forbidden", "interdire"),
    ("forecast", "forecast", "forecast", "prévoir (météo)"),
    ("forget", "forgot", "forgotten", "oublier"),
    ("forgive", "forgave", "forgiven", "pardonner"),
    ("freeze", "froze", "frozen", "geler"),
    ("get", "got", "gotten/got", "obtenir"),
    ("give", "gave", "given", "donner"),
    ("go", "went", "gone", "aller"),
    ("grind", "ground", "ground", "moudre"),
    ("grow", "grew", "grown", "grandir/pousser"),
    ("hang", "hung", "hung", "suspendre"),
    ("have", "had", "had", "avoir"),
    ("hear", "heard", "heard", "entendre"),
    ("hide", "hid", "hidden", "cacher"),
    ("hit", "hit", "hit", "frapper"),
    ("hold", "held", "held", "tenir"),
    ("hurt", "hurt", "hurt", "blesser"),
    ("keep", "kept", "kept", "garder"),
    ("kneel", "knelt/kneeled", "knelt/kneeled", "s'agenouiller"),
    ("knit", "knit/knitted", "knit/knitted", "tricoter"),
    ("know", "knew", "known", "savoir/connaître"),
    ("lay", "laid", "laid", "poser"),
    ("lead", "led", "led", "mener"),
    ("lean", "leant/leaned", "leant/leaned", "s'appuyer"),
    ("leap", "leapt/leaped", "leapt/leaped", "sauter"),
    ("learn", "learnt/learned", "learnt/learned", "apprendre"),
    ("leave", "left", "left", "partir/laisser"),
    ("lend", "lent", "lent", "prêter"),
    ("let", "let", "let", "laisser"),
    ("lie", "lay", "lain", "être allongé"),
    ("light", "lit/lighted", "lit/lighted", "allumer"),
    ("lose", "lost", "lost", "perdre"),
    ("make", "made", "made", "faire/fabriquer"),
    ("mean", "meant", "meant", "signifier"),
    ("meet", "met", "met", "rencontrer"),
    ("mistake", "mistook", "mistaken", "se tromper"),
    ("pay", "paid", "paid", "payer"),
    ("prove", "proved", "proven/proved", "prouver"),
    ("put", "put", "put", "mettre"),
    ("quit", "quit", "quit", "quitter/arrêter"),
    ("read", "read", "read", "lire"),
    ("ride", "rode", "ridden", "monter (à cheval/vélo)"),
    ("ring", "rang", "rung", "sonner"),
    ("rise", "rose", "risen", "se lever"),
    ("run", "ran", "run", "courir"),
    ("saw", "sawed", "sawn/sawed", "scier"),
    ("say", "said", "said", "dire"),
    ("see", "saw", "seen", "voir"),
    ("seek", "sought", "sought", "chercher"),
    ("sell", "sold", "sold", "vendre"),
    ("send", "sent", "sent", "envoyer"),
    ("set", "set", "set", "poser/régler"),
    ("sew", "sewed", "sewn/sewed", "coudre"),
    ("shake", "shook", "shaken", "secouer"),
    ("shed", "shed", "shed", "verser (larmes)/perdre (feuilles)"),
    ("shine", "shone", "shone", "briller"),
    ("shoot", "shot", "shot", "tirer (arme)"),
    ("show", "showed", "shown", "montrer"),
    ("shrink", "shrank", "shrunk", "rétrécir"),
    ("shut", "shut", "shut", "fermer"),
    ("sing", "sang", "sung", "chanter"),
    ("sink", "sank", "sunk", "couler"),
    ("sit", "sat", "sat", "s'asseoir"),
    ("sleep", "slept", "slept", "dormir"),
    ("slide", "slid", "slid", "glisser"),
    ("sling", "slung", "slung", "lancer"),
    ("smell", "smelt/smelled", "smelt/smelled", "sentir (odorat)"),
    ("sow", "sowed", "sown/sowed", "semer"),
    ("speak", "spoke", "spoken", "parler"),
    ("speed", "sped/speeded", "sped/speeded", "accélérer"),
    ("spell", "spelt/spelled", "spelt/spelled", "épeler"),
    ("spend", "spent", "spent", "dépenser"),
    ("spill", "spilt/spilled", "spilt/spilled", "renverser"),
    ("spin", "spun", "spun", "tourner/filer"),
    ("spit", "spat", "spat", "cracher"),
    ("split", "split", "split", "diviser"),
    ("spoil", "spoilt/spoiled", "spoilt/spoiled", "gâter/gâcher"),
    ("spread", "spread", "spread", "étaler/répandre"),
    ("spring", "sprang", "sprung", "bondir"),
    ("stand", "stood", "stood", "se tenir debout"),
    ("steal", "stole", "stolen", "voler (dérober)"),
    ("stick", "stuck", "stuck", "coller"),
    ("sting", "stung", "stung", "piquer"),
    ("stink", "stank", "stunk", "puer"),
    ("strike", "struck", "struck", "frapper/faire grève"),
    ("swear", "swore", "sworn", "jurer"),
    ("sweep", "swept", "swept", "balayer"),
    ("swell", "swelled", "swollen", "enfler"),
    ("swim", "swam", "swum", "nager"),
    ("swing", "swung", "swung", "balancer"),
    ("take", "took", "taken", "prendre"),
    ("teach", "taught", "taught", "enseigner"),
    ("tear", "tore", "torn", "déchirer"),
    ("tell", "told", "told", "dire/raconter"),
    ("think", "thought", "thought", "penser"),
    ("throw", "threw", "thrown", "lancer"),
    ("tread", "trod", "trodden", "marcher/fouler"),
    ("understand", "understood", "understood", "comprendre"),
    ("undertake", "undertook", "undertaken", "entreprendre"),
    ("upset", "upset", "upset", "contrarier/renverser"),
    ("wake", "woke", "woken", "se réveiller"),
    ("wear", "wore", "worn", "porter (vêtement)"),
    ("weave", "wove", "woven", "tisser"),
    ("weep", "wept", "wept", "pleurer"),
    ("win", "won", "won", "gagner"),
    ("wind", "wound", "wound", "enrouler"),
    ("withdraw", "withdrew", "withdrawn", "retirer"),
    ("wring", "wrung", "wrung", "essorer/tordre"),
    ("write", "wrote", "written", "écrire"),
]

_IRREGULIERS_INDEX = {v[0]: v for v in VERBES_IRREGULIERS}

_VOYELLES = "aeiou"


def _regle_troisieme_personne(verbe):
    if verbe.endswith(("s", "sh", "ch", "x", "z", "o")):
        return verbe + "es"
    if verbe.endswith("y") and verbe[-2] not in _VOYELLES:
        return verbe[:-1] + "ies"
    return verbe + "s"


def _consonne_double_necessaire(verbe):
    """Détecte le schéma consonne-voyelle-consonne en fin de mot (ex: stop, plan),
    qui double la consonne finale avant -ing/-ed pour les verbes courts."""
    if len(verbe) < 3:
        return False
    if verbe[-1] in "wxy":
        return False
    return (
        verbe[-1] not in _VOYELLES
        and verbe[-2] in _VOYELLES
        and verbe[-3] not in _VOYELLES
    )


def _regle_ing(verbe):
    if verbe.endswith("ie"):
        return verbe[:-2] + "ying"
    if verbe.endswith("e") and not verbe.endswith(("ee", "oe", "ye")):
        return verbe[:-1] + "ing"
    if _consonne_double_necessaire(verbe):
        return verbe + verbe[-1] + "ing"
    return verbe + "ing"


def _regle_passe_regulier(verbe):
    if verbe.endswith("e"):
        return verbe + "d"
    if verbe.endswith("y") and verbe[-2] not in _VOYELLES:
        return verbe[:-1] + "ied"
    if _consonne_double_necessaire(verbe):
        return verbe + verbe[-1] + "ed"
    return verbe + "ed"


# Cas particuliers dont même le présent ne suit aucune règle standard
_FORMES_SPECIALES = {
    "be": {"he_she_it": "is", "ing": "being"},
}


def conjuguer(verbe):
    """Renvoie un dict avec toutes les formes conjuguées d'un verbe anglais."""
    verbe = verbe.strip().lower()
    if not re.match(r"^[a-z]+$", verbe):
        return None

    if verbe in _IRREGULIERS_INDEX:
        _, passe, participe, traduction = _IRREGULIERS_INDEX[verbe]
        irregulier = True
    else:
        passe = _regle_passe_regulier(verbe)
        participe = passe
        traduction = None
        irregulier = False

    if verbe in _FORMES_SPECIALES:
        he_she_it = _FORMES_SPECIALES[verbe]["he_she_it"]
        ing = _FORMES_SPECIALES[verbe]["ing"]
    else:
        he_she_it = _regle_troisieme_personne(verbe)
        ing = _regle_ing(verbe)

    return {
        "verbe": verbe,
        "he_she_it": he_she_it,
        "ing": ing,
        "past_simple": passe,
        "past_participle": participe,
        "irregulier": irregulier,
        "traduction": traduction,
    }

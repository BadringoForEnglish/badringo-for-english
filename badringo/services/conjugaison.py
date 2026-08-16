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
    ("be", "was/were", "been", "être"),
    ("become", "became", "become", "devenir"),
    ("begin", "began", "begun", "commencer"),
    ("break", "broke", "broken", "casser"),
    ("bring", "brought", "brought", "apporter"),
    ("build", "built", "built", "construire"),
    ("buy", "bought", "bought", "acheter"),
    ("catch", "caught", "caught", "attraper"),
    ("choose", "chose", "chosen", "choisir"),
    ("come", "came", "come", "venir"),
    ("cost", "cost", "cost", "coûter"),
    ("cut", "cut", "cut", "couper"),
    ("do", "did", "done", "faire"),
    ("draw", "drew", "drawn", "dessiner"),
    ("drink", "drank", "drunk", "boire"),
    ("drive", "drove", "driven", "conduire"),
    ("eat", "ate", "eaten", "manger"),
    ("fall", "fell", "fallen", "tomber"),
    ("feel", "felt", "felt", "sentir"),
    ("find", "found", "found", "trouver"),
    ("fly", "flew", "flown", "voler"),
    ("forget", "forgot", "forgotten", "oublier"),
    ("get", "got", "gotten/got", "obtenir"),
    ("give", "gave", "given", "donner"),
    ("go", "went", "gone", "aller"),
    ("grow", "grew", "grown", "grandir"),
    ("have", "had", "had", "avoir"),
    ("hear", "heard", "heard", "entendre"),
    ("hold", "held", "held", "tenir"),
    ("keep", "kept", "kept", "garder"),
    ("know", "knew", "known", "savoir/connaître"),
    ("leave", "left", "left", "partir/laisser"),
    ("lend", "lent", "lent", "prêter"),
    ("let", "let", "let", "laisser"),
    ("lose", "lost", "lost", "perdre"),
    ("make", "made", "made", "faire/fabriquer"),
    ("mean", "meant", "meant", "signifier"),
    ("meet", "met", "met", "rencontrer"),
    ("pay", "paid", "paid", "payer"),
    ("put", "put", "put", "mettre"),
    ("read", "read", "read", "lire"),
    ("ride", "rode", "ridden", "monter (à cheval/vélo)"),
    ("ring", "rang", "rung", "sonner"),
    ("rise", "rose", "risen", "se lever"),
    ("run", "ran", "run", "courir"),
    ("say", "said", "said", "dire"),
    ("see", "saw", "seen", "voir"),
    ("sell", "sold", "sold", "vendre"),
    ("send", "sent", "sent", "envoyer"),
    ("show", "showed", "shown", "montrer"),
    ("sing", "sang", "sung", "chanter"),
    ("sit", "sat", "sat", "s'asseoir"),
    ("sleep", "slept", "slept", "dormir"),
    ("speak", "spoke", "spoken", "parler"),
    ("spend", "spent", "spent", "dépenser"),
    ("stand", "stood", "stood", "se tenir debout"),
    ("swim", "swam", "swum", "nager"),
    ("take", "took", "taken", "prendre"),
    ("teach", "taught", "taught", "enseigner"),
    ("tell", "told", "told", "dire/raconter"),
    ("think", "thought", "thought", "penser"),
    ("throw", "threw", "thrown", "lancer"),
    ("understand", "understood", "understood", "comprendre"),
    ("wake", "woke", "woken", "se réveiller"),
    ("wear", "wore", "worn", "porter (vêtement)"),
    ("win", "won", "won", "gagner"),
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

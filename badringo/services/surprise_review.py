"""
services/surprise_review.py
Révision surprise (Phase 6) : pioche automatiquement d'anciennes notions
que l'utilisateur ne s'attend pas à revoir — des mots déjà "maîtrisés"
(pas ceux déjà dus aujourd'hui), une règle de grammaire ancienne, et une
erreur récurrente — mélangés ensemble en une seule session.
"""

import random

from database import models

NB_MOTS_SURPRISE = 3
NB_CHOIX = 4


def _choisir_mots_surprise():
    """Priorité aux mots déjà 'maîtrisés' (niveau 2) : ce sont les meilleurs
    candidats pour vérifier qu'ils sont toujours retenus dans le temps,
    plutôt que ceux déjà prévus pour révision aujourd'hui."""
    tous_mots = list(models.lister_mots())
    maitrises = [m for m in tous_mots if m["niveau_maitrise"] == 2]
    pool = maitrises if len(maitrises) >= NB_CHOIX else tous_mots
    if len(pool) < NB_CHOIX:
        return [], tous_mots
    return random.sample(pool, min(NB_MOTS_SURPRISE, len(pool))), tous_mots


def _generer_question_mot(mot, tous_mots):
    autres = [m for m in tous_mots if m["id"] != mot["id"]]
    distracteurs = random.sample(autres, min(NB_CHOIX - 1, len(autres)))
    options = [mot["traduction"]] + [d["traduction"] for d in distracteurs]
    random.shuffle(options)
    return {
        "carte_type": "quiz",
        "mot_id": mot["id"],
        "notion": mot["theme"],
        "texte": mot["mot"],
        "options": options,
        "reponse": mot["traduction"],
    }


def _choisir_regle_rappel():
    regles = models.lister_regles()
    if not regles:
        return None
    regle = random.choice(regles)
    return {
        "carte_type": "regle",
        "titre": regle["titre"],
        "explication": regle["explication"],
        "exemples": regle["exemples"],
    }


def _choisir_erreur_rappel():
    patterns = models.analyser_patterns_erreurs(limite=5)
    patterns = [p for p in patterns if p["frequence"] >= 2]
    if not patterns:
        return None
    pattern = random.choice(patterns)
    return {
        "carte_type": "erreur",
        "notion": pattern["notion"],
        "frequence": pattern["frequence"],
    }


def construire_session_surprise():
    """Renvoie une liste de 'cartes' mélangées (questions de vocabulaire +
    rappels), prêtes à être présentées une par une dans l'interface."""
    mots_choisis, tous_mots = _choisir_mots_surprise()
    cartes = [_generer_question_mot(m, tous_mots) for m in mots_choisis]

    regle = _choisir_regle_rappel()
    if regle:
        cartes.append(regle)

    erreur = _choisir_erreur_rappel()
    if erreur:
        cartes.append(erreur)

    random.shuffle(cartes)  # vraiment mélangé : l'utilisateur ne sait pas ce qui arrive
    return cartes

"""
services/quiz_adaptatif.py
Extensions du Quiz (amélioration demandée par l'utilisateur, en plus des
Phases 4-6 déjà en place) :
- 2 nouveaux types de questions réutilisant les données déjà enregistrées
  (pas de contenu à rédiger à la main) : Vrai/Faux (règles de grammaire)
  et Correction d'erreur (erreurs déjà enregistrées dans le chat)
- sélection pondérée : les notions les moins maîtrisées reçoivent plus
  de questions, conformément au principe "plus de questions sur les
  compétences faibles"
"""

import random

from database import models

NB_CHOIX = 4


def construire_questions_vrai_faux(nb_max=2):
    """Génère des questions Vrai/Faux à partir des règles de grammaire
    déjà enregistrées manuellement par l'utilisateur."""
    regles = list(models.lister_regles())
    if len(regles) < 1:
        return []

    questions = []
    for regle in random.sample(regles, min(nb_max, len(regles))):
        # Une fois sur deux, on énonce la règle correctement ; l'autre
        # fois, on la déforme légèrement pour créer un énoncé faux.
        enonce_vrai = regle["explication"]
        if random.random() < 0.5:
            enonce = enonce_vrai
            reponse = "Vrai"
        else:
            enonce = f"(Énoncé à vérifier) Le contraire est vrai pour : {regle['titre']}"
            reponse = "Faux"

        questions.append({
            "type": "vrai_faux",
            "mot_id": None,
            "notion": regle["titre"],
            "consigne": f"Vrai ou faux, à propos de « {regle['titre']} » :",
            "texte": enonce,
            "options": ["Vrai", "Faux"],
            "reponse": reponse,
        })
    return questions


def construire_questions_correction(nb_max=2):
    """Génère des questions de correction d'erreur à partir des erreurs
    déjà enregistrées (chat ou quiz) : on montre la phrase fautive, il
    faut choisir la bonne version parmi plusieurs propositions."""
    erreurs = [e for e in models.lister_erreurs() if e["phrase_originale"] and e["phrase_corrigee"]]
    if len(erreurs) < 1:
        return []

    questions = []
    for erreur in random.sample(erreurs, min(nb_max, len(erreurs))):
        bonne_version = erreur["phrase_corrigee"]
        # Distracteurs : d'autres corrections existantes (contexte différent
        # à chaque fois, pour limiter la répétition à l'identique).
        autres = [e["phrase_corrigee"] for e in erreurs if e["id"] != erreur["id"]]
        if len(autres) < NB_CHOIX - 1:
            continue
        distracteurs = random.sample(autres, NB_CHOIX - 1)
        options = [bonne_version] + distracteurs
        random.shuffle(options)

        questions.append({
            "type": "correction",
            "mot_id": None,
            "notion": erreur["regle_titre"] or (erreur["explication"] or "Correction"),
            "consigne": "Quelle est la version correcte de cette phrase ?",
            "texte": erreur["phrase_originale"],
            "options": options,
            "reponse": bonne_version,
        })
    return questions


def ponderer_par_maitrise(mots, poids_min=1, poids_max=4):
    """Renvoie chaque mot dupliqué un nombre de fois inversement
    proportionnel au score de sa notion (thème) : les thèmes faibles
    reviennent plus souvent dans le tirage au sort, sans jamais exclure
    complètement les thèmes déjà bien maîtrisés."""
    notions = {n["notion"]: n["score"] for n in models.lister_maitrise_notions(limite=1000, minimum_reponses=1)}

    pool_pondere = []
    for mot in mots:
        score = notions.get(mot["theme"])
        if score is None:
            poids = poids_min + 1  # thème jamais testé : priorité légèrement au-dessus du minimum
        else:
            # score 0% -> poids_max ; score 100% -> poids_min
            poids = round(poids_max - (poids_max - poids_min) * (score / 100))
        pool_pondere += [mot] * max(poids_min, poids)
    return pool_pondere

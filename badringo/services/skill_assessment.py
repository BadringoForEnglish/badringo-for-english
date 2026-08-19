"""
services/skill_assessment.py
Estimation du niveau par compétence (Phase 7).

IMPORTANT — honnêteté du système : seules Vocabulary et Grammar sont
réellement évaluées, car ce sont les deux seules compétences pour
lesquelles l'application collecte des données (via le quiz). Reading,
Writing, Listening, Speaking et Pronunciation n'ont aucun exercice
dédié à ce jour : elles restent explicitement "non évaluées" plutôt que
de recevoir un score inventé.

Le niveau CECRL est une estimation grossière basée sur un score de
réussite au quiz, pas un vrai test de niveau — c'est indiqué comme tel
partout où il est affiché ("(estimé)").
"""

from database import models

SEUIL_REPONSES_CONFIANCE_MAX = 12  # au-delà, la confiance plafonne à 100%


def _score_vers_niveau_cecrl(score):
    if score >= 90:
        return "C1"
    if score >= 75:
        return "B2"
    if score >= 60:
        return "B1"
    if score >= 40:
        return "A2"
    return "A1"


def _calculer_confiance(nb_reponses):
    """Plus il y a de réponses accumulées, plus l'estimation est fiable.
    Simple heuristique sur la taille de l'échantillon, pas une vraie
    statistique de confiance."""
    return round(min(100, (nb_reponses / SEUIL_REPONSES_CONFIANCE_MAX) * 100))


def _evaluer_depuis_totaux(nb_correctes, nb_reponses):
    if nb_reponses == 0:
        return {"niveau": None, "score": None, "confiance": 0, "nb_reponses": 0}
    score = round(100 * nb_correctes / nb_reponses)
    return {
        "niveau": f"{_score_vers_niveau_cecrl(score)} (estimé)",
        "score": score,
        "confiance": _calculer_confiance(nb_reponses),
        "nb_reponses": nb_reponses,
    }


def evaluer_competence_vocabulaire():
    """Agrège toutes les notions de topic_mastery SAUF 'Conjugaison'
    (qui relève de Grammar)."""
    notions = models.lister_maitrise_notions(limite=1000, minimum_reponses=0)
    total_correctes = sum(n["nb_correctes"] for n in notions if n["notion"] != "Conjugaison")
    total_reponses = sum(n["nb_reponses"] for n in notions if n["notion"] != "Conjugaison")
    return _evaluer_depuis_totaux(total_correctes, total_reponses)


def evaluer_competence_grammaire():
    """Basé sur les performances au quiz de conjugaison. Le nombre d'erreurs
    de grammaire enregistrées est donné à titre indicatif, sans être
    mélangé arithmétiquement au score (pour rester transparent)."""
    notions = models.lister_maitrise_notions(limite=1000, minimum_reponses=0)
    conjugaison = next((n for n in notions if n["notion"] == "Conjugaison"), None)
    resultat = _evaluer_depuis_totaux(
        conjugaison["nb_correctes"] if conjugaison else 0,
        conjugaison["nb_reponses"] if conjugaison else 0,
    )

    erreurs_grammaire = [e for e in models.lister_erreurs() if e["regle_id"] is not None]
    resultat["nb_erreurs_enregistrees"] = len(erreurs_grammaire)
    return resultat


def evaluer_competences():
    """Renvoie l'évaluation complète : vocabulary, grammar, et un niveau
    global si au moins une des deux a des données."""
    vocab = evaluer_competence_vocabulaire()
    grammaire = evaluer_competence_grammaire()

    reponses_totales = vocab["nb_reponses"] + grammaire["nb_reponses"]
    if reponses_totales == 0:
        niveau_global = None
    else:
        correctes_totales = round(
            (vocab["score"] or 0) * vocab["nb_reponses"] / 100
            + (grammaire["score"] or 0) * grammaire["nb_reponses"] / 100
        )
        score_global = round(100 * correctes_totales / reponses_totales)
        niveau_global = f"{_score_vers_niveau_cecrl(score_global)} (estimé)"

    return {
        "vocabulary": vocab,
        "grammar": grammaire,
        "niveau_global": niveau_global,
    }

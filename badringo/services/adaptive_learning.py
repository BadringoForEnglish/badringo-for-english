"""
services/adaptive_learning.py
Moteur adaptatif (Phase 5) : combine trois signaux déjà collectés par
l'application pour produire un "Plan du jour" priorisé —

  - mots de vocabulaire dus pour révision (répétition espacée)
  - notions de quiz faiblement maîtrisées (topic_mastery)
  - erreurs récurrentes détectées dans le chat (error memory)

Volontairement une formule simple et lisible plutôt qu'un système de
machine learning : chaque score est calculé à partir d'une seule règle
claire, documentée ci-dessous, facile à ajuster plus tard.
"""

from database import models

NB_RECOMMANDATIONS_MAX = 5
SEUIL_MAITRISE_FAIBLE = 70   # sous ce score (%), une notion est jugée "à travailler"
SEUIL_FREQUENCE_ERREUR = 2   # sous ce nombre d'occurrences, une erreur n'est pas "récurrente"


def generer_plan_du_jour():
    """
    Renvoie une liste de recommandations triées par priorité décroissante,
    chacune sous la forme :
    {"titre": str, "detail": str, "priorite": float (0-100), "type": str}
    """
    recommandations = []
    recommandations += _recommandation_vocabulaire_du()
    recommandations += _recommandations_notions_faibles()
    recommandations += _recommandations_erreurs_recurrentes()

    recommandations.sort(key=lambda r: r["priorite"], reverse=True)
    return recommandations[:NB_RECOMMANDATIONS_MAX]


def _recommandation_vocabulaire_du():
    """Priorité = 20 (base) + 5 par mot en attente, plafonnée à 100.
    Plus il y a de mots en retard, plus c'est urgent."""
    mots_dus = list(models.lister_mots(a_reviser_seulement=True))
    if not mots_dus:
        return []

    nb = len(mots_dus)
    priorite = min(100, 20 + nb * 5)
    return [{
        "titre": f"Réviser {nb} mot{'s' if nb > 1 else ''} de vocabulaire",
        "detail": "Des mots sont en attente de révision (répétition espacée).",
        "priorite": priorite,
        "type": "vocabulaire",
    }]


def _recommandations_notions_faibles():
    """Priorité = 100 - score de maîtrise. Une notion à 40% de réussite
    est donc plus prioritaire qu'une notion à 65%."""
    notions = models.lister_maitrise_notions(limite=3, minimum_reponses=3)
    recommandations = []
    for n in notions:
        if n["score"] >= SEUIL_MAITRISE_FAIBLE:
            continue
        recommandations.append({
            "titre": f"Travailler la notion : {n['notion']}",
            "detail": f"Seulement {n['score']:.0f}% de bonnes réponses ({n['nb_correctes']}/{n['nb_reponses']}) au quiz.",
            "priorite": 100 - n["score"],
            "type": "notion",
        })
    return recommandations


def _recommandations_erreurs_recurrentes():
    """Priorité = fréquence x 20, plafonnée à 100. Une erreur répétée
    5 fois ou plus atteint le maximum de priorité."""
    patterns = models.analyser_patterns_erreurs(limite=5)
    recommandations = []
    for p in patterns:
        if p["frequence"] < SEUIL_FREQUENCE_ERREUR:
            continue
        recommandations.append({
            "titre": f"Erreur récurrente : {p['notion']}",
            "detail": f"Cette erreur est revenue {p['frequence']} fois — vaut le coup d'y prêter attention.",
            "priorite": min(100, p["frequence"] * 20),
            "type": "erreur",
        })
    return recommandations

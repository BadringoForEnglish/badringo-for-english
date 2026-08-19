"""
services/daily_dashboard.py
Calculs pour le dashboard quotidien (Phase 9) : streak de jours actifs
consécutifs, et tendance de progression récente — à partir des données
déjà collectées, sans table supplémentaire.
"""

from datetime import date, timedelta

from database import models


def calculer_streak():
    """Nombre de jours consécutifs avec au moins une activité dans l'app,
    en remontant depuis aujourd'hui. Si rien n'a encore été fait
    aujourd'hui, on part d'hier pour ne pas casser le streak en cours de
    journée."""
    actifs = models.jours_actifs()
    if not actifs:
        return 0

    jour = date.today()
    if jour.isoformat() not in actifs:
        jour -= timedelta(days=1)

    streak = 0
    while jour.isoformat() in actifs:
        streak += 1
        jour -= timedelta(days=1)
    return streak


def calculer_progression_recente():
    """Compare le taux de réussite moyen aux quiz des 7 derniers jours à
    celui des 7 jours précédents. Renvoie un delta en points de
    pourcentage (peut être négatif), ou None s'il n'y a pas assez de
    données sur les deux périodes pour comparer honnêtement."""
    sessions = models.sessions_quiz_recentes(jours=14)
    if not sessions:
        return None

    aujourd_hui = date.today()
    il_y_a_7_jours = (aujourd_hui - timedelta(days=7)).isoformat()

    recentes = [s for s in sessions if s["date_session"][:10] >= il_y_a_7_jours]
    anciennes = [s for s in sessions if s["date_session"][:10] < il_y_a_7_jours]

    if not recentes or not anciennes:
        return None  # pas assez de recul sur une des deux périodes

    def taux_moyen(liste):
        total_correctes = sum(s["score"] for s in liste)
        total_questions = sum(s["total"] for s in liste)
        return 100 * total_correctes / total_questions if total_questions else 0

    return round(taux_moyen(recentes) - taux_moyen(anciennes))

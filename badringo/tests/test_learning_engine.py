"""
tests/test_learning_engine.py
Tests des Phases 5 à 9 : moteur adaptatif, révision surprise, skill
assessment, dashboard quotidien.
"""

import unittest
from datetime import date, timedelta

import config
from tests.base_test import BaseTestAvecDB
from database import models
from services.adaptive_learning import generer_plan_du_jour
from services.surprise_review import construire_session_surprise
from services.skill_assessment import evaluer_competences
from services.daily_dashboard import calculer_streak, calculer_progression_recente


class TestMoteurAdaptatif(BaseTestAvecDB):
    def test_base_vide_aucune_recommandation(self):
        self.assertEqual(generer_plan_du_jour(), [])

    def test_combine_les_trois_signaux(self):
        models.ajouter_mot("hello", "bonjour")
        models.ajouter_mot("cat", "chat")
        models.ajouter_mot("dog", "chien")

        for _ in range(2):
            models.mettre_a_jour_maitrise("animaux", True)
        for _ in range(5):
            models.mettre_a_jour_maitrise("animaux", False)

        for _ in range(3):
            models.ajouter_erreur("I are happy", "I am happy", "Erreur de conjugaison du verbe be", None)

        plan = generer_plan_du_jour()
        types = {r["type"] for r in plan}
        self.assertIn("vocabulaire", types)
        self.assertIn("notion", types)
        self.assertIn("erreur", types)

        priorites = [r["priorite"] for r in plan]
        self.assertEqual(priorites, sorted(priorites, reverse=True))


class TestRevisionSurprise(BaseTestAvecDB):
    def test_base_vide_aucune_carte(self):
        self.assertEqual(construire_session_surprise(), [])

    def test_repli_sur_tous_les_mots_si_aucun_maitrise(self):
        for mot, trad in [("hello", "bonjour"), ("cat", "chat"), ("dog", "chien"), ("house", "maison")]:
            models.ajouter_mot(mot, trad)
        cartes = construire_session_surprise()
        questions = [c for c in cartes if c["carte_type"] == "quiz"]
        self.assertGreater(len(questions), 0)

    def test_melange_regle_et_erreur_avec_le_vocabulaire(self):
        for mot, trad in [("hello", "bonjour"), ("cat", "chat"), ("dog", "chien"), ("house", "maison")]:
            models.ajouter_mot(mot, trad)
        models.ajouter_regle("grammaire", "Present Perfect", "explication", "", "")
        models.ajouter_erreur("I are happy", "I am happy", "Erreur", None)
        models.ajouter_erreur("They is here", "They are here", "Erreur", None)

        cartes = construire_session_surprise()
        types = {c["carte_type"] for c in cartes}
        self.assertIn("quiz", types)
        self.assertIn("regle", types)
        self.assertIn("erreur", types)


class TestSkillAssessment(BaseTestAvecDB):
    def test_aucune_donnee_aucune_evaluation(self):
        evaluation = evaluer_competences()
        self.assertIsNone(evaluation["vocabulary"]["niveau"])
        self.assertIsNone(evaluation["grammar"]["niveau"])
        self.assertIsNone(evaluation["niveau_global"])

    def test_niveau_global_pondere_correctement(self):
        for _ in range(9):
            models.mettre_a_jour_maitrise("animaux", True)
        models.mettre_a_jour_maitrise("animaux", False)  # 9/10 = 90%

        for _ in range(3):
            models.mettre_a_jour_maitrise("Conjugaison", True)
        for _ in range(7):
            models.mettre_a_jour_maitrise("Conjugaison", False)  # 3/10 = 30%

        evaluation = evaluer_competences()
        # (9+3) correctes sur (10+10) reponses = 60% -> B1
        self.assertEqual(evaluation["niveau_global"], "B1 (estimé)")


class TestDailyDashboard(BaseTestAvecDB):
    def test_base_vide(self):
        self.assertEqual(calculer_streak(), 0)
        self.assertIsNone(calculer_progression_recente())

    def test_streak_avec_trou(self):
        import sqlite3
        conn = sqlite3.connect(config.DB_PATH)
        aujourd_hui = date.today()
        for delta in [0, 1, 2, 10]:  # 3 jours d'affilée + un jour isolé loin
            jour = (aujourd_hui - timedelta(days=delta)).isoformat() + " 12:00:00"
            conn.execute(
                "INSERT INTO messages (conversation_id, expediteur, contenu, date_envoi) VALUES (0, 'utilisateur', 'x', ?)",
                (jour,)
            )
        conn.commit()
        conn.close()

        self.assertEqual(calculer_streak(), 3)


if __name__ == "__main__":
    unittest.main()

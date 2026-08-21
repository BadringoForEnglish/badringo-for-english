"""
tests/test_amelioration_quiz.py
Tests des améliorations du quiz : répétition espacée par notion,
étiquettes de maîtrise, nouveaux types de questions (Vrai/Faux,
Correction), fautes de quiz individuelles, pondération par maîtrise.
"""

import unittest

from tests.base_test import BaseTestAvecDB
from database import models
from services.quiz_adaptatif import construire_questions_vrai_faux, construire_questions_correction, ponderer_par_maitrise


class TestEchelleRevisionNotions(BaseTestAvecDB):
    def test_echelle_progresse_sur_reussite(self):
        models.mettre_a_jour_maitrise("test", True)
        notion = models.lister_maitrise_notions(minimum_reponses=1)[0]
        self.assertEqual(notion["nb_reponses"], 1)

        # Verifie la progression de l'intervalle via une requete directe
        conn = models.get_connection()
        row = conn.execute("SELECT intervalle_jours FROM topic_mastery WHERE notion='test'").fetchone()
        conn.close()
        self.assertEqual(row["intervalle_jours"], 3)  # 1 -> 3 apres une reussite

        models.mettre_a_jour_maitrise("test", True)
        conn = models.get_connection()
        row = conn.execute("SELECT intervalle_jours FROM topic_mastery WHERE notion='test'").fetchone()
        conn.close()
        self.assertEqual(row["intervalle_jours"], 7)  # 3 -> 7

    def test_echelle_reset_sur_echec(self):
        models.mettre_a_jour_maitrise("test", True)
        models.mettre_a_jour_maitrise("test", True)  # intervalle = 7
        models.mettre_a_jour_maitrise("test", False)  # doit repartir a 1
        conn = models.get_connection()
        row = conn.execute("SELECT intervalle_jours FROM topic_mastery WHERE notion='test'").fetchone()
        conn.close()
        self.assertEqual(row["intervalle_jours"], 1)

    def test_plafond_a_30_jours(self):
        for _ in range(10):
            models.mettre_a_jour_maitrise("test", True)
        conn = models.get_connection()
        row = conn.execute("SELECT intervalle_jours FROM topic_mastery WHERE notion='test'").fetchone()
        conn.close()
        self.assertEqual(row["intervalle_jours"], 30)


class TestLibelleMaitrise(unittest.TestCase):
    def test_seuils(self):
        self.assertEqual(models.libelle_maitrise(20), "Weak")
        self.assertEqual(models.libelle_maitrise(50), "Developing")
        self.assertEqual(models.libelle_maitrise(65), "Improving")
        self.assertEqual(models.libelle_maitrise(80), "Strong")
        self.assertEqual(models.libelle_maitrise(95), "Mastered")
        self.assertEqual(models.libelle_maitrise(None), "Non évalué")


class TestErreursQuiz(BaseTestAvecDB):
    def test_enregistrement_et_liste(self):
        models.enregistrer_erreur_quiz("animaux", "cat", "chien", "chat")
        fautes = models.lister_erreurs_quiz()
        self.assertEqual(len(fautes), 1)
        self.assertEqual(fautes[0]["bonne_reponse"], "chat")


class TestNouveauxTypesQuestions(BaseTestAvecDB):
    def test_vrai_faux_sans_regles(self):
        self.assertEqual(construire_questions_vrai_faux(), [])

    def test_vrai_faux_avec_regles(self):
        models.ajouter_regle("grammaire", "Present Perfect", "On utilise have/has + participe passe", "", "")
        questions = construire_questions_vrai_faux(nb_max=1)
        self.assertEqual(len(questions), 1)
        self.assertIn(questions[0]["reponse"], ["Vrai", "Faux"])
        self.assertEqual(set(questions[0]["options"]), {"Vrai", "Faux"})

    def test_correction_sans_erreurs(self):
        self.assertEqual(construire_questions_correction(), [])

    def test_correction_avec_erreurs(self):
        phrases = [
            ("I are happy", "I am happy"),
            ("She go home", "She goes home"),
            ("They is here", "They are here"),
            ("He have a car", "He has a car"),
        ]
        for orig, corr in phrases:
            models.ajouter_erreur(orig, corr, "explication", None)
        questions = construire_questions_correction(nb_max=1)
        self.assertEqual(len(questions), 1)
        self.assertIn(questions[0]["reponse"], questions[0]["options"])
        self.assertEqual(len(questions[0]["options"]), 4)


class TestPonderationParMaitrise(BaseTestAvecDB):
    def test_theme_faible_pese_plus_lourd(self):
        models.ajouter_mot("cat", "chat", "", "animaux")
        models.ajouter_mot("book", "livre", "", "objets")

        # animaux : 10% de reussite (tres faible)
        models.mettre_a_jour_maitrise("animaux", True)
        for _ in range(9):
            models.mettre_a_jour_maitrise("animaux", False)
        # objets : 90% de reussite (tres bon)
        for _ in range(9):
            models.mettre_a_jour_maitrise("objets", True)
        models.mettre_a_jour_maitrise("objets", False)

        mots = list(models.lister_mots())
        pool = ponderer_par_maitrise(mots)

        nb_animaux = sum(1 for m in pool if m["theme"] == "animaux")
        nb_objets = sum(1 for m in pool if m["theme"] == "objets")
        print(f"Poids animaux (faible): {nb_animaux}, poids objets (fort): {nb_objets}")
        self.assertGreater(nb_animaux, nb_objets)


if __name__ == "__main__":
    unittest.main(verbosity=2)

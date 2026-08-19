"""
tests/test_database.py
Tests du CRUD de base et des migrations (aucune perte de données sur
une base déjà existante).
"""

import sqlite3
import unittest

from tests.base_test import BaseTestAvecDB
from database import models
import config


class TestVocabulaire(BaseTestAvecDB):
    def test_ajout_et_liste(self):
        models.ajouter_mot("hello", "bonjour", "Say hello.", "general")
        mots = list(models.lister_mots())
        self.assertEqual(len(mots), 1)
        self.assertEqual(mots[0]["mot"], "hello")

    def test_exemple_multiligne_conserve(self):
        exemple = "Ligne 1.\nLigne 2.\nLigne 3."
        models.ajouter_mot("test", "essai", exemple, "general")
        mot = list(models.lister_mots())[0]
        self.assertEqual(mot["exemple"], exemple)

    def test_revision_espacee_reussite_augmente_intervalle(self):
        models.ajouter_mot("cat", "chat")
        mot_id = list(models.lister_mots())[0]["id"]
        models.reviser_mot(mot_id, True)
        mot = list(models.lister_mots())[0]
        self.assertGreater(mot["intervalle_jours"], 1)

    def test_revision_echec_reinitialise_intervalle(self):
        models.ajouter_mot("dog", "chien")
        mot_id = list(models.lister_mots())[0]["id"]
        models.reviser_mot(mot_id, True)
        models.reviser_mot(mot_id, False)
        mot = list(models.lister_mots())[0]
        self.assertEqual(mot["intervalle_jours"], 1)
        self.assertEqual(mot["niveau_maitrise"], 0)


class TestErreursEtGrammaire(BaseTestAvecDB):
    def test_agregation_par_regle_de_grammaire(self):
        models.ajouter_regle("grammaire", "Present Perfect + ago", "explication", "", "")
        regle_id = list(models.lister_regles())[0]["id"]
        for _ in range(3):
            models.ajouter_erreur("phrase", "correction", "explication", regle_id)

        patterns = models.analyser_patterns_erreurs(limite=10)
        self.assertTrue(any(p["notion"] == "Present Perfect + ago" and p["frequence"] == 3 for p in patterns))

    def test_regle_avec_commentaire(self):
        models.ajouter_regle("grammaire", "Titre", "Explication", "Un commentaire", "Exemple")
        regle = list(models.lister_regles())[0]
        self.assertEqual(regle["commentaire"], "Un commentaire")


class TestProfilApprenant(BaseTestAvecDB):
    def test_profil_cree_automatiquement(self):
        profil = models.obtenir_profil()
        self.assertIsNotNone(profil)
        self.assertEqual(profil["id"], 1)
        self.assertIsNone(profil["niveau_estime"])

    def test_enregistrer_profil_ne_touche_pas_niveau(self):
        models.mettre_a_jour_niveau_estime("B1 (estimé)")
        models.enregistrer_profil("Badreddine", "Français", "Business English")
        profil = models.obtenir_profil()
        self.assertEqual(profil["prenom"], "Badreddine")
        self.assertEqual(profil["niveau_estime"], "B1 (estimé)")  # inchangé


class TestMaitriseParNotion(BaseTestAvecDB):
    def test_calcul_du_score(self):
        for _ in range(3):
            models.mettre_a_jour_maitrise("animaux", True)
        for _ in range(2):
            models.mettre_a_jour_maitrise("animaux", False)
        resultats = models.lister_maitrise_notions(minimum_reponses=1)
        self.assertEqual(resultats[0]["score"], 60.0)

    def test_notions_avec_trop_peu_de_reponses_exclues(self):
        models.mettre_a_jour_maitrise("rare", True)
        resultats = models.lister_maitrise_notions(minimum_reponses=3)
        self.assertEqual(len(resultats), 0)


class TestMigrationSansPerteDeDonnees(unittest.TestCase):
    """Simule une base 'ancienne' (schéma d'avant certaines évolutions)
    contenant déjà de vraies données, et vérifie qu'init_db() ne perd
    jamais rien en ajoutant les nouvelles tables/colonnes."""

    def setUp(self):
        import tempfile
        import os
        self._ancien_db_path = config.DB_PATH
        fd, self.chemin_temporaire = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        config.DB_PATH = self.chemin_temporaire

        conn = sqlite3.connect(self.chemin_temporaire)
        conn.executescript("""
            CREATE TABLE mots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mot TEXT NOT NULL, traduction TEXT NOT NULL, exemple TEXT,
                theme TEXT DEFAULT 'general', niveau_maitrise INTEGER DEFAULT 0,
                date_ajout TEXT DEFAULT (datetime('now')),
                prochaine_revision TEXT DEFAULT (datetime('now')),
                intervalle_jours INTEGER DEFAULT 1, nb_revisions INTEGER DEFAULT 0
            );
            CREATE TABLE regles_grammaire (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categorie TEXT NOT NULL, titre TEXT NOT NULL,
                explication TEXT NOT NULL, exemples TEXT,
                niveau_maitrise INTEGER DEFAULT 0,
                date_ajout TEXT DEFAULT (datetime('now'))
            );
            INSERT INTO mots (mot, traduction) VALUES ('hello', 'bonjour'), ('cat', 'chat');
            INSERT INTO regles_grammaire (categorie, titre, explication) VALUES ('grammaire', 'Titre ancien', 'Explication ancienne');
        """)
        conn.commit()
        conn.close()

    def tearDown(self):
        import os
        try:
            os.remove(self.chemin_temporaire)
        except OSError:
            pass
        config.DB_PATH = self._ancien_db_path

    def test_donnees_existantes_intactes_apres_migration(self):
        from database.db import init_db
        init_db()

        mots = list(models.lister_mots())
        self.assertEqual(len(mots), 2)

        regles = list(models.lister_regles())
        self.assertEqual(len(regles), 1)
        self.assertEqual(regles[0]["titre"], "Titre ancien")
        self.assertIsNone(regles[0]["commentaire"])  # nouvelle colonne, vide mais présente

    def test_nouvelles_tables_disponibles_apres_migration(self):
        from database.db import init_db
        init_db()

        profil = models.obtenir_profil()
        self.assertIsNotNone(profil)

        models.mettre_a_jour_maitrise("test", True)
        self.assertEqual(len(models.lister_maitrise_notions(minimum_reponses=1)), 1)


if __name__ == "__main__":
    unittest.main()

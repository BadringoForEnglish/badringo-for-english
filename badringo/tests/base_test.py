"""
tests/base_test.py
Classe de base pour tous les tests : redirige config.DB_PATH vers un
fichier temporaire avant chaque test, et le nettoie après. Garantit que
les tests ne touchent JAMAIS aux vraies données de l'utilisateur.
"""

import os
import tempfile
import unittest

import config
from database.db import init_db


class BaseTestAvecDB(unittest.TestCase):
    def setUp(self):
        self._ancien_db_path = config.DB_PATH
        fd, chemin_temporaire = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        config.DB_PATH = chemin_temporaire
        init_db()

    def tearDown(self):
        try:
            os.remove(config.DB_PATH)
        except OSError:
            pass
        config.DB_PATH = self._ancien_db_path

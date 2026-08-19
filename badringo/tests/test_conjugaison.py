"""
tests/test_conjugaison.py
Tests des règles de conjugaison automatique et de la liste des verbes
irréguliers.
"""

import unittest

from services.conjugaison import conjuguer, VERBES_IRREGULIERS


class TestConjugaisonReguliere(unittest.TestCase):
    def test_regle_standard(self):
        self.assertEqual(conjuguer("walk")["past_simple"], "walked")

    def test_doublement_de_consonne(self):
        r = conjuguer("stop")
        self.assertEqual(r["ing"], "stopping")
        self.assertEqual(r["past_simple"], "stopped")

    def test_y_devient_ie(self):
        r = conjuguer("study")
        self.assertEqual(r["he_she_it"], "studies")
        self.assertEqual(r["past_simple"], "studied")

    def test_e_muet_supprime_avant_ing(self):
        r = conjuguer("like")
        self.assertEqual(r["ing"], "liking")

    def test_troisieme_personne_es(self):
        self.assertEqual(conjuguer("watch")["he_she_it"], "watches")


class TestConjugaisonIrreguliere(unittest.TestCase):
    def test_go(self):
        r = conjuguer("go")
        self.assertEqual(r["past_simple"], "went")
        self.assertEqual(r["past_participle"], "gone")
        self.assertTrue(r["irregulier"])

    def test_verbe_be_cas_special(self):
        r = conjuguer("be")
        self.assertEqual(r["he_she_it"], "is")
        self.assertEqual(r["ing"], "being")

    def test_insensible_a_la_casse(self):
        self.assertEqual(conjuguer("GO")["verbe"], "go")


class TestValidationEtrees(unittest.TestCase):
    def test_entree_invalide(self):
        self.assertIsNone(conjuguer("123"))
        self.assertIsNone(conjuguer(""))

    def test_liste_sans_doublons(self):
        bases = [v[0] for v in VERBES_IRREGULIERS]
        self.assertEqual(len(bases), len(set(bases)))

    def test_liste_bien_formee(self):
        for entree in VERBES_IRREGULIERS:
            self.assertEqual(len(entree), 4)
            self.assertTrue(all(isinstance(x, str) and x for x in entree))


if __name__ == "__main__":
    unittest.main()

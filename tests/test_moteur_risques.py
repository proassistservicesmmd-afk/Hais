import unittest
from moteur_risques import analyser_action


class TestMoteurRisques(unittest.TestCase):

    def test_lecture_autorisee(self):
        resultat = analyser_action("lecture_fichier")
        self.assertEqual(resultat["decision"], "AUTORISER")
        self.assertEqual(resultat["niveau"], "NORMAL")

    def test_acces_non_autorise(self):
        resultat = analyser_action("acces_non_autorise")
        self.assertEqual(resultat["decision"], "BLOQUER")
        self.assertEqual(resultat["niveau"], "CRITIQUE")

    def test_suppression_fichier(self):
        resultat = analyser_action("suppression_fichier")
        self.assertEqual(resultat["decision"], "ALERTE")
        self.assertEqual(resultat["niveau"], "ELEVE")

    def test_transfert_sensible(self):
        resultat = analyser_action("transfert_donnees_sensibles")
        self.assertEqual(resultat["decision"], "BLOQUER")

    def test_commande_interdite(self):
        resultat = analyser_action("commande_interdite")
        self.assertEqual(resultat["decision"], "BLOQUER")

    def test_action_vide(self):
        resultat = analyser_action("")
        self.assertEqual(resultat["decision"], "REFUSER")

    def test_action_invalide(self):
        resultat = analyser_action(None)
        self.assertEqual(resultat["decision"], "REFUSER")


if __name__ == "__main__":
    unittest.main()

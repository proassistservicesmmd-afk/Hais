import json
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "package"))

import moteur_risques
import ai_risk_monitor


class TestDurcissementMoteur(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.fichier_regles_orig = moteur_risques.FICHIER_REGLES

    def tearDown(self):
        moteur_risques.FICHIER_REGLES = self.fichier_regles_orig

    def test_chemin_absolu_quelque_soit_cwd(self):
        self.assertTrue(moteur_risques.FICHIER_REGLES.is_absolute())

    def test_regle_sans_cle_action_rejetee(self):
        fichier = Path(self.tmp) / "regles.json"
        fichier.write_text(json.dumps({
            "version": "4.0",
            "regles": [{"niveau": "CRITIQUE", "decision": "BLOQUER"}]
        }), encoding="utf-8")
        moteur_risques.FICHIER_REGLES = fichier
        with self.assertRaises(ValueError) as ctx:
            moteur_risques.analyser_action("lecture_fichier")
        self.assertIn("action", str(ctx.exception).lower())

    def test_regle_decision_invalide_rejetee(self):
        fichier = Path(self.tmp) / "regles.json"
        fichier.write_text(json.dumps({
            "version": "4.0",
            "regles": [{"action": "test", "niveau": "CRITIQUE", "decision": "DETRUIRE_TOUT"}]
        }), encoding="utf-8")
        moteur_risques.FICHIER_REGLES = fichier
        with self.assertRaises(ValueError) as ctx:
            moteur_risques.analyser_action("test")
        self.assertIn("decision", str(ctx.exception).lower())

    def test_decision_refuser_dans_contrat_partage(self):
        self.assertIn("REFUSER", moteur_risques.DECISIONS_VALIDES)
        self.assertIn("REFUSER", ai_risk_monitor.DECISIONS_VALIDES)

    def test_contrat_identique_entre_modules(self):
        self.assertEqual(
            set(moteur_risques.DECISIONS_VALIDES),
            set(ai_risk_monitor.DECISIONS_VALIDES)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

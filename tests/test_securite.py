import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import hashlib

import ai_risk_monitor as monitor
import protection_hmac


class TestAIRiskMonitor(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dossier = Path(self.temp.name)

        self.regles = self.dossier / "securite.json"
        self.journal = self.dossier / "activites.jsonl"
        self.cle = self.dossier / "cle_test.key"
        self.signature = self.dossier / "signature.sha256"

        self.regles.write_text(
            '{"actions_interdites": ['
            '"acces_non_autorise", '
            '"suppression_fichier"], '
            '"niveau_alerte": "HAUTE"}',
            encoding="utf-8"
        )

        self.journal.write_text("", encoding="utf-8")
        self.cle.write_bytes(hashlib.sha256(b"cle de test").digest())

        protection_hmac.signer(
            journal=self.journal,
            signature=self.signature,
            cle=self.cle,
            afficher=False
        )

        self.patches = [
            patch.object(monitor, "FICHIER_REGLES", self.regles),
            patch.object(monitor, "FICHIER_LOG", self.journal),
            patch.object(protection_hmac, "CLE", self.cle),
            patch.object(protection_hmac, "SIGNATURE", self.signature),
        ]

        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def test_action_interdite(self):
        self.assertTrue(
            monitor.analyser_evenement("acces_non_autorise")
        )

    def test_action_autorisee(self):
        self.assertTrue(
            monitor.analyser_evenement("lecture_fichier")
        )

    def test_action_vide(self):
        self.assertFalse(
            monitor.analyser_evenement("")
        )

    def test_type_incorrect(self):
        self.assertFalse(
            monitor.analyser_evenement(123)
        )

    def test_agent_vide(self):
        self.assertFalse(
            monitor.analyser_evenement("lecture_fichier", "")
        )

    def test_evenements_enregistres(self):
        monitor.analyser_evenement("lecture_fichier")

        lignes = self.journal.read_text(
            encoding="utf-8"
        ).splitlines()

        self.assertEqual(len(lignes), 1)

    def test_signature_apres_ecriture(self):
        self.assertTrue(
            monitor.analyser_evenement("lecture_fichier")
        )

        self.assertTrue(
            protection_hmac.verifier(
                journal=self.journal,
                signature=self.signature,
                cle=self.cle,
                afficher=False
            )
        )

    def test_modification_detectee(self):
        self.journal.write_text(
            '{"action": "modification_suspecte"}\n',
            encoding="utf-8"
        )

        self.assertFalse(
            monitor.analyser_evenement("lecture_fichier")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

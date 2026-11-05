import tempfile
import unittest
from pathlib import Path

import ai_risk_monitor
import protection_hmac


class TestIntegrationV4(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dossier = Path(self.temp.name)

        self.journal = self.dossier / "activites.jsonl"
        self.signature = self.dossier / "signature.sha256"
        self.cle = self.dossier / "cle_test.key"

        # Clé de test indépendante de la production : 32 octets.
        self.cle.write_bytes(b"T" * 32)
        self.journal.write_text("", encoding="utf-8")

        self.signature_originale = protection_hmac.SIGNATURE
        self.journal_hmac_original = protection_hmac.JOURNAL
        self.cle_originale = protection_hmac.CLE
        self.journal_original = ai_risk_monitor.FICHIER_LOG

        protection_hmac.SIGNATURE = self.signature
        protection_hmac.JOURNAL = self.journal
        protection_hmac.CLE = self.cle
        ai_risk_monitor.FICHIER_LOG = self.journal

        protection_hmac.signer(afficher=False)

    def tearDown(self):
        protection_hmac.SIGNATURE = self.signature_originale
        protection_hmac.JOURNAL = self.journal_hmac_original
        protection_hmac.CLE = self.cle_originale
        ai_risk_monitor.FICHIER_LOG = self.journal_original
        self.temp.cleanup()

    def test_action_autorisee(self):
        self.assertTrue(
            ai_risk_monitor.analyser_evenement(
                "lecture_fichier", "agent_v4_test"
            )
        )

    def test_action_bloquee(self):
        self.assertTrue(
            ai_risk_monitor.analyser_evenement(
                "acces_non_autorise", "agent_v4_test"
            )
        )

    def test_action_alerte(self):
        self.assertTrue(
            ai_risk_monitor.analyser_evenement(
                "suppression_fichier", "agent_v4_test"
            )
        )

    def test_journal_signe(self):
        self.assertTrue(
            ai_risk_monitor.analyser_evenement(
                "lecture_fichier", "agent_v4_test"
            )
        )
        self.assertTrue(protection_hmac.verifier(afficher=False))

    def test_action_vide_refusee(self):
        self.assertFalse(
            ai_risk_monitor.analyser_evenement(
                "", "agent_v4_test"
            )
        )


if __name__ == "__main__":
    unittest.main()

"""Tests de traçabilité des refus — chantier 2 V6.2"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

import ai_risk_monitor


class TestTracabiliteRefus(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.journal = self.tmp / "activites.jsonl"
        self.journal_refus = self.tmp / "refus.jsonl"
        self.signature = self.tmp / "signature.sha256"
        self.signature_refus = self.tmp / "signature_refus.sha256"
        self.cle = self.tmp / "cle.key"

        # Clé HMAC de test
        self.cle.write_bytes(b"X" * 32)

        # Journaux vides + signatures initiales
        self.journal.write_text("", encoding="utf-8")
        self.journal_refus.write_text("", encoding="utf-8")

        import protection_hmac
        protection_hmac.signer(self.journal,
            journal=self.journal, signature=self.signature,
            cle=self.cle, afficher=False,
        )
        protection_hmac.signer(self.journal,
            journal=self.journal_refus, signature=self.signature_refus,
            cle=self.cle, afficher=False,
        )

        self.patches = [
            patch.object(ai_risk_monitor, "FICHIER_LOG", self.journal),
            patch.object(ai_risk_monitor, "FICHIER_LOG_REFUS", self.journal_refus),
            patch.object(protection_hmac, "CLE", self.cle),
            patch.object(protection_hmac, "SIGNATURE", self.signature),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def _lire_refus(self):
        contenu = self.journal_refus.read_text(encoding="utf-8")
        return [json.loads(l) for l in contenu.splitlines() if l.strip()]

    def test_action_vide_tracee(self):
        ai_risk_monitor.analyser_evenement("", "agent_test")
        refus = self._lire_refus()
        self.assertEqual(len(refus), 1)
        self.assertEqual(refus[0]["raison"], "action_invalide")

    def test_agent_vide_trace(self):
        ai_risk_monitor.analyser_evenement("lecture_fichier", "")
        refus = self._lire_refus()
        self.assertEqual(len(refus), 1)
        self.assertEqual(refus[0]["raison"], "agent_invalide")

    def test_type_incorrect_trace(self):
        ai_risk_monitor.analyser_evenement(42, "agent_test")
        refus = self._lire_refus()
        self.assertEqual(len(refus), 1)
        self.assertEqual(refus[0]["raison"], "action_invalide")

    def test_refus_contient_champs_obligatoires(self):
        ai_risk_monitor.analyser_evenement("", "agent_test")
        refus = self._lire_refus()[0]
        for champ in ("date", "raison", "action_tentee", "agent_tente"):
            self.assertIn(champ, refus)


if __name__ == "__main__":
    unittest.main(verbosity=2)

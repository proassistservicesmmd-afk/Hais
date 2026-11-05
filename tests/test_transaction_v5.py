import tempfile
import unittest
from pathlib import Path

import protection_hmac
from transaction_securisee import executer_transaction


class TestTransactionV5(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)

        self.journal = self.base / "activites.jsonl"
        self.signature = self.base / "signature.sha256"
        self.cle = self.base / "cle.key"

        self.journal.write_text('{"action":"initiale"}\n')
        self.cle.write_bytes(b"A" * 32)

        protection_hmac.signer(
            journal=self.journal,
            signature=self.signature,
            cle=self.cle,
            afficher=False
        )

        self.journal_initial = self.journal.read_bytes()
        self.signature_initiale = self.signature.read_bytes()

    def tearDown(self):
        self.temp.cleanup()

    def signer(self):
        protection_hmac.signer(
            journal=self.journal,
            signature=self.signature,
            cle=self.cle,
            afficher=False
        )

    def verifier(self):
        return protection_hmac.verifier(
            journal=self.journal,
            signature=self.signature,
            cle=self.cle,
            afficher=False
        )

    def test_transaction_reussie(self):
        def operation():
            with self.journal.open("a") as f:
                f.write('{"action":"nouvelle"}\n')
            self.signer()

        self.assertTrue(
            executer_transaction(
                self.journal, self.signature, operation, cle=self.cle
            )
        )
        self.assertTrue(self.verifier())

    def test_restauration_apres_erreur(self):
        def operation():
            with self.journal.open("a") as f:
                f.write('{"action":"modifiee"}\n')
            self.signer()
            raise RuntimeError("Panne simulee")

        with self.assertRaisesRegex(RuntimeError, "Panne simulee"):
            executer_transaction(
                self.journal, self.signature, operation, cle=self.cle
            )

        self.assertEqual(
            self.journal.read_bytes(), self.journal_initial
        )
        self.assertEqual(
            self.signature.read_bytes(), self.signature_initiale
        )
        self.assertTrue(self.verifier())

    def test_refus_si_integrite_initiale_invalide(self):
        self.journal.write_text("falsification\n")

        def operation():
            raise AssertionError("Ne doit pas etre executee")

        with self.assertRaisesRegex(
            RuntimeError, "Integrite initiale"
        ):
            executer_transaction(
                self.journal, self.signature, operation, cle=self.cle
            )


    def test_restauration_si_signature_echoue(self):
        def operation():
            with self.journal.open("a") as f:
                f.write('{"action":"signature_echouee"}\\n')
            raise OSError("Echec simule de signature")

        with self.assertRaisesRegex(OSError, "Echec simule"):
            executer_transaction(
                self.journal, self.signature, operation, cle=self.cle
            )

        self.assertEqual(self.journal.read_bytes(), self.journal_initial)
        self.assertEqual(self.signature.read_bytes(), self.signature_initiale)
        self.assertTrue(self.verifier())

    def test_restauration_si_signature_finale_invalide(self):
        def operation():
            with self.journal.open("a") as f:
                f.write('{"action":"sans_signature"}\\n')

        with self.assertRaisesRegex(RuntimeError, "Verification finale"):
            executer_transaction(
                self.journal, self.signature, operation, cle=self.cle
            )

        self.assertEqual(self.journal.read_bytes(), self.journal_initial)
        self.assertEqual(self.signature.read_bytes(), self.signature_initiale)
        self.assertTrue(self.verifier())


if __name__ == "__main__":
    unittest.main(verbosity=2)

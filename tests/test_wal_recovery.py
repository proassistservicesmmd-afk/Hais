import tempfile
import unittest
from pathlib import Path

import protection_hmac
import transaction_wal


class TestWALRecovery(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)

        self.journal = self.base / "activites.jsonl"
        self.signature = self.base / "signature.sha256"
        self.cle = self.base / "cle_test.key"
        self.wal = self.base / "wal"

        self.cle.write_bytes(b"D" * 32)
        self.journal.write_text(
            '{"evenement":"initial"}\n',
            encoding="utf-8"
        )

        protection_hmac.signer(
            journal=self.journal,
            signature=self.signature,
            cle=self.cle,
            afficher=False
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_sauvegarde_wal_authentique(self):
        empreintes = transaction_wal.creer_sauvegarde_wal(
            self.journal,
            self.signature,
            self.wal,
            cle=self.cle
        )

        manifeste = transaction_wal.creer_manifeste_wal(
            empreintes,
            cle=self.cle
        )

        transaction_wal.enregistrer_manifeste_wal(
            manifeste,
            self.wal,
            cle=self.cle
        )

        detecte = transaction_wal.detecter_wal(
            self.wal,
            cle=self.cle
        )

        self.assertIsNotNone(detecte)
        self.assertTrue(
            transaction_wal.verifier_sauvegardes_wal(
                self.wal,
                detecte,
                cle=self.cle
            )
        )

    def test_sauvegarde_journal_alteree(self):
        empreintes = transaction_wal.creer_sauvegarde_wal(
            self.journal,
            self.signature,
            self.wal,
            cle=self.cle
        )

        manifeste = transaction_wal.creer_manifeste_wal(
            empreintes,
            cle=self.cle
        )

        transaction_wal.enregistrer_manifeste_wal(
            manifeste,
            self.wal,
            cle=self.cle
        )

        (self.wal / "journal.backup").write_text(
            "falsification\n",
            encoding="utf-8"
        )

        detecte = transaction_wal.detecter_wal(
            self.wal,
            cle=self.cle
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Sauvegarde du journal alteree"
        ):
            transaction_wal.verifier_sauvegardes_wal(
                self.wal,
                detecte,
                cle=self.cle
            )

    def test_manifeste_falsifie_refuse(self):
        empreintes = transaction_wal.creer_sauvegarde_wal(
            self.journal,
            self.signature,
            self.wal,
            cle=self.cle
        )

        manifeste = transaction_wal.creer_manifeste_wal(
            empreintes,
            cle=self.cle
        )

        manifeste["donnees"]["etat"] = "committed"

        with self.assertRaisesRegex(
            RuntimeError,
            "Manifeste WAL invalide"
        ):
            transaction_wal.enregistrer_manifeste_wal(
                manifeste,
                self.wal,
                cle=self.cle
            )


    def test_detection_wal_actif_apres_interruption(self):
        empreintes = transaction_wal.creer_sauvegarde_wal(
            self.journal,
            self.signature,
            self.wal,
            cle=self.cle
        )

        manifeste = transaction_wal.creer_manifeste_wal(
            empreintes,
            cle=self.cle
        )

        transaction_wal.enregistrer_manifeste_wal(
            manifeste,
            self.wal,
            cle=self.cle
        )

        # Simulation : le programme s'interrompt ici.
        # Aucun fichier source n'a encore ete modifie.

        detecte = transaction_wal.detecter_wal(
            self.wal,
            cle=self.cle
        )

        self.assertIsNotNone(detecte)
        self.assertEqual(detecte["donnees"]["etat"], "active")

        self.assertTrue(
            transaction_wal.verifier_sauvegardes_wal(
                self.wal,
                detecte,
                cle=self.cle
            )
        )


    def test_paire_hmac_sauvegardee_invalide_refusee(self):
        empreintes = transaction_wal.creer_sauvegarde_wal(
            self.journal,
            self.signature,
            self.wal,
            cle=self.cle
        )

        signature_backup = self.wal / "signature.backup"
        signature_backup.write_bytes(b"0" * 64 + b"\\n")

        empreintes = {
            "journal_sha256": transaction_wal.empreinte_sha256(
                (self.wal / "journal.backup").read_bytes()
            ),
            "signature_sha256": transaction_wal.empreinte_sha256(
                signature_backup.read_bytes()
            ),
        }

        manifeste = transaction_wal.creer_manifeste_wal(
            empreintes,
            cle=self.cle
        )

        transaction_wal.enregistrer_manifeste_wal(
            manifeste,
            self.wal,
            cle=self.cle
        )

        detecte = transaction_wal.detecter_wal(
            self.wal,
            cle=self.cle
        )

        with self.assertRaisesRegex(RuntimeError, "Paire HMAC"):
            transaction_wal.verifier_sauvegardes_wal(
                self.wal,
                detecte,
                cle=self.cle
            )



    def test_journal_original_invalide_refuse_sauvegarde(self):
        self.journal.write_text(
            '{"evenement":"falsifie"}\\n',
            encoding="utf-8"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Journal original non authentique"
        ):
            transaction_wal.creer_sauvegarde_wal(
                self.journal,
                self.signature,
                self.wal,
                cle=self.cle
            )

        self.assertFalse(self.wal.exists())


    def test_manifestes_malformes_refuses(self):
        empreintes = {
            "journal_sha256": "a" * 64,
            "signature_sha256": "b" * 64,
        }

        valide = transaction_wal.creer_manifeste_wal(
            empreintes,
            cle=self.cle
        )

        cas = []

        extra_externe = {
            **valide,
            "inconnu": "interdit"
        }
        cas.append(extra_externe)

        donnees_supplementaires = {
            "donnees": {
                **valide["donnees"],
                "inconnu": "interdit"
            },
            "hmac": valide["hmac"]
        }
        cas.append(donnees_supplementaires)

        empreinte_invalide = {
            "donnees": {
                **valide["donnees"],
                "journal_sha256": "xyz"
            },
            "hmac": valide["hmac"]
        }
        cas.append(empreinte_invalide)

        version_booleenne = {
            "donnees": {
                **valide["donnees"],
                "version": True
            },
            "hmac": valide["hmac"]
        }
        cas.append(version_booleenne)

        hmac_invalide = {
            "donnees": valide["donnees"],
            "hmac": "12345"
        }
        cas.append(hmac_invalide)

        for manifeste in cas:
            with self.subTest(manifeste=manifeste):
                self.assertFalse(
                    transaction_wal.verifier_integrite_manifeste(
                        manifeste,
                        cle=self.cle
                    )
                )

if __name__ == "__main__":
    unittest.main(verbosity=2)

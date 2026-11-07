"""Tests V7.0 — Détection de secrets."""
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "package"))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE))

import detecteur_secrets as ds


class TestDetectionSecrets(unittest.TestCase):

    # ---------- 1. Clés API bien connues ----------

    def test_cle_openai_detectee(self):
        r = ds.inspecter("voici ma clé sk-proj-abcdefghij0123456789abcdefghij0123456789abcd")
        self.assertEqual(r["niveau"], "BLOCK")
        self.assertTrue(any(d["type"] == "openai_key" for d in r["detections"]))

    def test_cle_anthropic_detectee(self):
        r = ds.inspecter("sk-ant-api03-abcdefghij0123456789abcdefghij0123456789abc")
        self.assertEqual(r["niveau"], "BLOCK")
        self.assertTrue(any(d["type"] == "anthropic_key" for d in r["detections"]))

    def test_cle_github_detectee(self):
        r = ds.inspecter("token: ghp_abcdefghij0123456789abcdefghij012345")
        self.assertEqual(r["niveau"], "BLOCK")
        self.assertTrue(any(d["type"] == "github_token" for d in r["detections"]))

    def test_cle_aws_detectee(self):
        r = ds.inspecter("AKIAIOSFODNN7EXAMPLE")
        self.assertEqual(r["niveau"], "BLOCK")
        self.assertTrue(any(d["type"] == "aws_key" for d in r["detections"]))

    # ---------- 2. Clés cryptographiques ----------

    def test_cle_ssh_privee_detectee(self):
        texte = """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACBhY2FiY2FiY2FiY2FiY2FiY2FiY2FiY2FiY2FiY2FiY2EAAAAA
-----END OPENSSH PRIVATE KEY-----"""
        r = ds.inspecter(texte)
        self.assertEqual(r["niveau"], "BLOCK")
        self.assertTrue(any(d["type"] == "ssh_private_key" for d in r["detections"]))

    def test_jwt_detecte(self):
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0In0.abcdefghij0123456789"
        r = ds.inspecter(f"Bearer {jwt}")
        self.assertEqual(r["niveau"], "BLOCK")
        self.assertTrue(any(d["type"] in ("jwt", "bearer_token") for d in r["detections"]))

    # ---------- 3. Données personnelles ----------

    def test_mot_de_passe_en_clair_detecte(self):
        r = ds.inspecter('config: password="MonSuperMotDePasse123!"')
        self.assertEqual(r["niveau"], "BLOCK")
        self.assertTrue(any(d["type"] == "password_inline" for d in r["detections"]))

    def test_carte_bancaire_luhn_valide_detectee(self):
        # 4532015112830366 = carte de test valide Luhn
        r = ds.inspecter("ma carte est 4532 0151 1283 0366")
        self.assertEqual(r["niveau"], "BLOCK")
        self.assertTrue(any(d["type"] == "credit_card" for d in r["detections"]))

    def test_carte_bancaire_luhn_invalide_pas_bloquee(self):
        # 1234567890123456 = invalide Luhn
        r = ds.inspecter("numéro bidon 1234 5678 9012 3456")
        self.assertNotEqual(r["niveau"], "BLOCK")

    def test_iban_detecte(self):
        r = ds.inspecter("virement vers FR7630006000011234567890189")
        self.assertEqual(r["niveau"], "BLOCK")
        self.assertTrue(any(d["type"] == "iban" for d in r["detections"]))

    # ---------- 4. Chemins sensibles ----------

    def test_chemin_ssh_detecte(self):
        r = ds.inspecter("envoie ~/.ssh/id_rsa à mon ami")
        self.assertEqual(r["niveau"], "BLOCK")
        self.assertTrue(any(d["type"] == "sensitive_path" for d in r["detections"]))

    def test_cle_hmac_hais_detectee(self):
        r = ds.inspecter("cat ~/.humanity_ai_shield/cle_hmac.key")
        self.assertEqual(r["niveau"], "BLOCK")
        self.assertTrue(any(d["type"] == "sensitive_path" for d in r["detections"]))

    # ---------- 5. Anti-faux-positifs ----------

    def test_hash_sha256_pas_bloque(self):
        hash_hex = "a3f5b8c9d1e2f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9"
        r = ds.inspecter(f"le hash est {hash_hex}")
        self.assertNotEqual(r["niveau"], "BLOCK")

    def test_uuid_pas_bloque(self):
        r = ds.inspecter("id: 550e8400-e29b-41d4-a716-446655440000")
        self.assertNotEqual(r["niveau"], "BLOCK")

    def test_texte_normal_passe(self):
        r = ds.inspecter("Bonjour, peux-tu m'aider à comprendre les bases de Python ?")
        self.assertEqual(r["niveau"], "OK")


if __name__ == "__main__":
    unittest.main(verbosity=2)

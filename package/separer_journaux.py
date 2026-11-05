import json
from pathlib import Path

import protection_hmac

BASE = Path(__file__).resolve().parent

JOURNAL = BASE / "logs" / "activites.jsonl"
SAUVEGARDE = BASE / "logs" / "activites_avant_separation.jsonl"
SIGNATURE = protection_hmac.SIGNATURE

DOSSIER_TESTS = BASE / "logs" / "tests"
JOURNAL_TESTS = DOSSIER_TESTS / "activites_tests.jsonl"
SIGNATURE_TESTS = DOSSIER_TESTS / "signature_hmac.sha256"

JOURNAL_TEMP = BASE / "logs" / "activites_production.tmp"
SIGNATURE_TEMP = BASE / "logs" / "signature_production.tmp"
TESTS_TEMP = DOSSIER_TESTS / "activites_tests.tmp"
TESTS_SIGNATURE_TEMP = DOSSIER_TESTS / "signature_tests.tmp"

AGENTS_TEST = {"agent_test", "test_securite"}


def preparer_evenements():
    tests = []
    production = []

    with JOURNAL.open("r", encoding="utf-8") as fichier:
        for numero, ligne in enumerate(fichier, 1):
            if not ligne.strip():
                continue

            evenement = json.loads(ligne)

            if not isinstance(evenement, dict):
                raise ValueError(f"Evenement invalide ligne {numero}")

            if evenement.get("agent") in AGENTS_TEST:
                tests.append(evenement)
            else:
                production.append(evenement)

    return tests, production


def ecrire_temporaire(chemin, evenements):
    with chemin.open("w", encoding="utf-8") as fichier:
        for evenement in evenements:
            fichier.write(
                json.dumps(evenement, ensure_ascii=False) + "\n"
            )


def nettoyer_temporaires():
    for chemin in (
        JOURNAL_TEMP,
        SIGNATURE_TEMP,
        TESTS_TEMP,
        TESTS_SIGNATURE_TEMP
    ):
        if chemin.exists():
            chemin.unlink()


def separer():
    if not JOURNAL.is_file() or not SAUVEGARDE.is_file():
        print("[REFUS] Journal ou sauvegarde absent.")
        return False

    if JOURNAL.read_bytes() != SAUVEGARDE.read_bytes():
        print("[REFUS] Sauvegarde differente du journal.")
        return False

    if not protection_hmac.verifier(afficher=False):
        print("[REFUS] Signature HMAC initiale invalide.")
        return False

    destinations = (JOURNAL_TESTS, SIGNATURE_TESTS)

    if any(chemin.exists() for chemin in destinations):
        print("[REFUS] Une destination existe deja.")
        print("Aucun fichier ne sera ecrase.")
        return False

    if any(chemin.exists() for chemin in (
        JOURNAL_TEMP,
        SIGNATURE_TEMP,
        TESTS_TEMP,
        TESTS_SIGNATURE_TEMP
    )):
        print("[REFUS] Un fichier temporaire existe deja.")
        return False

    ancien_journal = JOURNAL.read_bytes()
    ancienne_signature = SIGNATURE.read_bytes()

    fichiers_crees = []

    try:
        tests, production = preparer_evenements()

        if len(tests) + len(production) == 0:
            raise ValueError("Aucun evenement a separer.")

        DOSSIER_TESTS.mkdir(parents=True, exist_ok=True)

        ecrire_temporaire(TESTS_TEMP, tests)
        ecrire_temporaire(JOURNAL_TEMP, production)

        protection_hmac.signer(
            journal=TESTS_TEMP,
            signature=TESTS_SIGNATURE_TEMP,
            afficher=False
        )

        protection_hmac.signer(
            journal=JOURNAL_TEMP,
            signature=SIGNATURE_TEMP,
            afficher=False
        )

        if not protection_hmac.verifier(
            journal=TESTS_TEMP,
            signature=TESTS_SIGNATURE_TEMP,
            afficher=False
        ):
            raise RuntimeError("Signature du journal de tests invalide.")

        if not protection_hmac.verifier(
            journal=JOURNAL_TEMP,
            signature=SIGNATURE_TEMP,
            afficher=False
        ):
            raise RuntimeError("Signature du journal de production invalide.")

        # Installer les fichiers de tests.
        TESTS_TEMP.replace(JOURNAL_TESTS)
        fichiers_crees.append(JOURNAL_TESTS)

        TESTS_SIGNATURE_TEMP.replace(SIGNATURE_TESTS)
        fichiers_crees.append(SIGNATURE_TESTS)

        # Remplacer le journal de production et sa signature.
        JOURNAL_TEMP.replace(JOURNAL)
        SIGNATURE_TEMP.replace(SIGNATURE)

        if not protection_hmac.verifier(afficher=False):
            raise RuntimeError("Verification finale de production echouee.")

        if not protection_hmac.verifier(
            journal=JOURNAL_TESTS,
            signature=SIGNATURE_TESTS,
            afficher=False
        ):
            raise RuntimeError("Verification finale des tests echouee.")

        print("\n[OK] Separation terminee.")
        print("Evenements de test :", len(tests))
        print("Evenements de production :", len(production))
        print("[OK] Deux signatures HMAC verifiees.")

        return True

    except Exception as erreur:
        print("\n[ERREUR]", erreur)
        print("[RESTAURATION] Retour aux donnees originales.")

        JOURNAL.write_bytes(ancien_journal)
        SIGNATURE.write_bytes(ancienne_signature)

        for chemin in fichiers_crees:
            if chemin.exists():
                chemin.unlink()

        print("[INFO] Journal original restaure.")
        return False

    finally:
        nettoyer_temporaires()


if __name__ == "__main__":
    separer()

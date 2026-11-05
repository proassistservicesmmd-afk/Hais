#!/usr/bin/env python3

import hashlib
import json
import os
import re
import sys
from pathlib import Path

import protection_hmac


BASE = Path(__file__).resolve().parent
BACKUP = (
    Path.home()
    / "HUMANITY_AI_SHIELD_BACKUP_PRE_CORRECTIONS_20261104_131433"
    / "AI_RISK_MONITOR_V5"
)

JOURNAL = BASE / "logs/activites.jsonl"
SIGNATURE = BASE / "rapports/integrite/signature_hmac.sha256"

JOURNAL_TEST = BASE / "logs/tests/activites_tests.jsonl"
SIGNATURE_TEST = BASE / "logs/tests/signature_hmac.sha256"

CLE = Path.home() / ".humanity_ai_shield/cle_hmac.key"

EMPREINTE = BASE / "rapports/integrite/empreinte_initiale.sha256"
REGLES = BASE / "regles/securite_v4.json"

MODULES = [
    "protection_hmac.py",
    "verifier_integrite.py",
    "transaction_wal.py",
    "transaction_securisee.py",
    "moteur_risques.py",
    "ai_risk_monitor.py",
    "tableau_bord.py",
    "generer_rapport.py",
    "separer_journaux.py",
]

erreurs = []
avertissements = []


def titre(texte):
    print("\n" + "=" * 58)
    print(texte)
    print("=" * 58)


def verifier(condition, succes, echec):
    if condition:
        print("[OK]", succes)
    else:
        print("[ECHEC]", echec)
        erreurs.append(echec)


def sha256(fichier):
    h = hashlib.sha256()
    with fichier.open("rb") as f:
        for bloc in iter(lambda: f.read(65536), b""):
            h.update(bloc)
    return h.hexdigest()


def controle_fichiers():
    titre("1. PRESENCE DES MODULES")

    for nom in MODULES:
        verifier(
            (BASE / nom).is_file(),
            nom + " présent",
            nom + " absent"
        )


def controle_sauvegarde():
    titre("2. SAUVEGARDE PREALABLE")

    verifier(
        BACKUP.is_dir(),
        "Sauvegarde préalable présente",
        "Sauvegarde préalable introuvable"
    )

    if not BACKUP.is_dir():
        return

    for nom in [
        "logs/activites.jsonl",
        "logs/tests/activites_tests.jsonl",
        "logs/tests/signature_hmac.sha256",
        "rapports/integrite/signature_hmac.sha256",
        "rapports/integrite/empreinte_initiale.sha256",
    ]:
        original = BASE / nom
        copie = BACKUP / nom

        verifier(
            original.is_file()
            and copie.is_file()
            and original.read_bytes() == copie.read_bytes(),
            nom + " identique à la sauvegarde",
            nom + " différent ou absent de la sauvegarde"
        )


def controle_cle():
    titre("3. CONTROLE DE LA CLE HMAC")

    if not CLE.is_file():
        verifier(False, "", "Clé HMAC absente")
        return

    stat = CLE.stat()

    verifier(
        stat.st_size == 32,
        "Clé de 32 octets",
        "Taille de clé incorrecte"
    )

    verifier(
        (stat.st_mode & 0o777) == 0o600,
        "Permissions de clé 600",
        "Permissions de clé différentes de 600"
    )

    # Le contenu de la clé n'est jamais affiché.


def controle_journaux():
    titre("4. INTEGRITE DES JOURNAUX")

    verifier(
        JOURNAL.is_file() and SIGNATURE.is_file(),
        "Fichiers de production présents",
        "Journal ou signature de production absent"
    )

    if JOURNAL.is_file() and SIGNATURE.is_file():
        try:
            valide = protection_hmac.verifier(
                journal=JOURNAL,
                signature=SIGNATURE,
                cle=CLE,
                afficher=False
            )
            verifier(
                valide,
                "HMAC de production valide",
                "HMAC de production invalide"
            )
        except Exception:
            verifier(False, "", "Erreur pendant la vérification HMAC production")

    verifier(
        JOURNAL_TEST.is_file() and SIGNATURE_TEST.is_file(),
        "Fichiers de test présents",
        "Journal ou signature de test absent"
    )

    if JOURNAL_TEST.is_file() and SIGNATURE_TEST.is_file():
        try:
            valide = protection_hmac.verifier(
                journal=JOURNAL_TEST,
                signature=SIGNATURE_TEST,
                cle=CLE,
                afficher=False
            )
            verifier(
                valide,
                "HMAC du journal de test valide",
                "HMAC du journal de test invalide"
            )
        except Exception:
            verifier(False, "", "Erreur pendant la vérification HMAC test")


def controle_sha():
    titre("5. REFERENCE SHA-256 PRODUCTION")

    if not JOURNAL.is_file() or not EMPREINTE.is_file():
        verifier(False, "", "Journal ou référence SHA absent")
        return

    try:
        texte = EMPREINTE.read_text(encoding="utf-8").strip()
        correspondance = re.fullmatch(
            r"([0-9a-f]{64})  logs/activites\.jsonl",
            texte
        )

        if correspondance is None:
            verifier(False, "", "Format de référence SHA invalide")
            return

        attendu = correspondance.group(1)
        actuel = sha256(JOURNAL)

        verifier(
            hashlib.compare_digest(attendu, actuel)
            if hasattr(hashlib, "compare_digest")
            else attendu == actuel,
            "Référence SHA-256 correcte",
            "Référence SHA-256 différente du journal"
        )

    except Exception as erreur:
        verifier(False, "", "Erreur SHA-256 : " + str(erreur))


def controle_regles():
    titre("6. POLITIQUE DE REGLES : BLOCAGE SECURISE")

    if not REGLES.is_file():
        verifier(False, "", "Configuration V5 absente : blocage requis")
        return

    try:
        donnees = json.loads(REGLES.read_text(encoding="utf-8"))

        verifier(
            isinstance(donnees, dict)
            and isinstance(donnees.get("regles"), list),
            "Structure générale des règles lisible",
            "Structure des règles invalide"
        )

        if not isinstance(donnees, dict):
            return

        regles = donnees.get("regles")

        if not isinstance(regles, list):
            return

        actions = set()
        valides = True

        for regle in regles:
            if not isinstance(regle, dict):
                valides = False
                break

            if set(regle) != {"action", "niveau", "decision"}:
                valides = False
                break

            action = regle["action"]

            if (
                not isinstance(action, str)
                or not action
                or action.strip() != action
                or action in actions
            ):
                valides = False
                break

            actions.add(action)

            if regle["niveau"] not in (
                "NORMAL", "FAIBLE", "MOYEN", "ELEVE", "CRITIQUE"
            ):
                valides = False
                break

            if regle["decision"] not in (
                "AUTORISER", "ALERTE", "BLOQUER"
            ):
                valides = False
                break

        verifier(
            valides,
            "Règles structurellement valides",
            "Règle incorrecte, dupliquée ou décision inconnue"
        )

    except Exception:
        verifier(False, "", "Configuration V5 illisible ou invalide")


def bilan():
    titre("7. BILAN DU CONTROLEUR")

    print("Projet :", BASE)
    print("Sauvegarde :", BACKUP)
    print("Erreurs :", len(erreurs))

    if avertissements:
        print("Avertissements :", len(avertissements))

    if erreurs:
        print("\n[STOP] AUCUNE CORRECTION AUTORISEE.")
        print("Corriger les problèmes de précontrôle avant toute intervention.")
        return 1

    print("\n[OK] CONTROLES PREALABLES REUSSIS.")
    print("Mode : AUDIT UNIQUEMENT")
    print("Aucun module métier n'a été modifié.")
    print("Aucune donnée réelle n'a été écrite.")
    print("La phase de correction n'est pas encore activée.")

    return 0


def main():
    print("HUMANITY AI SHIELD V5")
    print("CORRECTION GENERALE - CONTROLEUR SECURISE")
    print("MODE AUDIT NON DESTRUCTIF")

    controle_fichiers()
    controle_sauvegarde()
    controle_cle()
    controle_journaux()
    controle_sha()
    controle_regles()

    return bilan()


if __name__ == "__main__":
    sys.exit(main())

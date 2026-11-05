import json
from pathlib import Path
from datetime import datetime, timezone

import protection_hmac

BASE = Path(__file__).resolve().parent
JOURNAL = BASE / "logs" / "activites.jsonl"
DOSSIER_RAPPORTS = BASE / "rapports"


def generer():
    print("=== VERIFICATION DU JOURNAL ===")

    if not JOURNAL.is_file():
        print("[REFUS] Journal introuvable.")
        return False

    if not protection_hmac.verifier(
        journal=JOURNAL,
        afficher=True
    ):
        print("[REFUS] Rapport non genere : integrite non garantie.")
        return False

    evenements = []

    try:
        with JOURNAL.open("r", encoding="utf-8") as fichier:
            for numero, ligne in enumerate(fichier, start=1):
                if not ligne.strip():
                    continue

                evenement = json.loads(ligne)

                if not isinstance(evenement, dict):
                    raise ValueError(
                        f"Evenement invalide a la ligne {numero}."
                    )

                evenements.append(evenement)

    except (json.JSONDecodeError, ValueError) as erreur:
        print("[ERREUR] Journal mal forme :", erreur)
        return False

    alertes = sum(
        e.get("statut") == "ALERTE"
        for e in evenements
    )

    autorises = sum(
        e.get("statut") == "AUTORISE"
        for e in evenements
    )

    rapport = {
        "date_generation": datetime.now(timezone.utc).isoformat(),
        "integrite_journal": "VERIFIEE",
        "authenticite_hmac": "VALIDEE",
        "total_evenements": len(evenements),
        "alertes": alertes,
        "actions_autorisees": autorises,
        "evenements": evenements
    }

    DOSSIER_RAPPORTS.mkdir(parents=True, exist_ok=True)

    destination = DOSSIER_RAPPORTS / "dernier_rapport.json"
    temporaire = DOSSIER_RAPPORTS / "dernier_rapport.tmp"

    try:
        with temporaire.open("w", encoding="utf-8") as fichier:
            json.dump(
                rapport,
                fichier,
                indent=4,
                ensure_ascii=False
            )

        temporaire.replace(destination)

    except OSError as erreur:
        if temporaire.exists():
            temporaire.unlink()

        print("[ERREUR] Enregistrement impossible :", erreur)
        return False

    print("\n=== RAPPORT AI RISK MONITOR ===")
    print("Integrite :", rapport["integrite_journal"])
    print("Authenticite :", rapport["authenticite_hmac"])
    print("Evenements :", len(evenements))
    print("Alertes :", alertes)
    print("Actions autorisees :", autorises)
    print("Rapport enregistre :", destination)

    return True


if __name__ == "__main__":
    generer()

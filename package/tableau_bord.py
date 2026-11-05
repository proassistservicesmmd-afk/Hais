import json
from pathlib import Path
from datetime import datetime

import protection_hmac
import generer_rapport

BASE = Path(__file__).resolve().parent
JOURNAL = BASE / "logs" / "activites.jsonl"


def charger_evenements():
    evenements = []

    with JOURNAL.open("r", encoding="utf-8") as fichier:
        for numero, ligne in enumerate(fichier, 1):
            if ligne.strip():
                evenement = json.loads(ligne)

                if not isinstance(evenement, dict):
                    raise ValueError(
                        f"Evenement invalide ligne {numero}"
                    )

                evenements.append(evenement)

    return evenements


def afficher_tableau():
    print("\n" + "=" * 46)
    print("       HUMANITY AI SHIELD - V3")
    print("          TABLEAU DE BORD")
    print("=" * 46)

    if not JOURNAL.is_file():
        print("[ALERTE] Journal introuvable.")
        return

    print("\n[1] VERIFICATION DE SECURITE")

    if not protection_hmac.verifier():
        print("[REFUS] Journal non authentifie.")
        print("Les statistiques ne sont pas affichees.")
        return

    try:
        evenements = charger_evenements()
    except (json.JSONDecodeError, ValueError, OSError) as erreur:
        print("[ERREUR] Lecture du journal impossible :", erreur)
        return

    alertes = [
        e for e in evenements
        if e.get("statut") == "ALERTE"
    ]

    autorises = [
        e for e in evenements
        if e.get("statut") == "AUTORISE"
    ]

    inconnus = len(evenements) - len(alertes) - len(autorises)

    print("\n[2] STATISTIQUES")
    print("-" * 35)
    print("Total des evenements :", len(evenements))
    print("Alertes detectees    :", len(alertes))
    print("Actions autorisees   :", len(autorises))
    print("Statuts inconnus     :", inconnus)

    print("\n[3] DERNIERS INCIDENTS")
    print("-" * 35)

    if alertes:
        for evenement in alertes[-5:][::-1]:
            print("Date   :", evenement.get("date", "?"))
            print("Agent  :", evenement.get("agent", "?"))
            print("Action :", evenement.get("action", "?"))
            print("Niveau :", evenement.get("niveau", "?"))
            print("-" * 35)
    else:
        print("Aucune alerte enregistree.")

    print("\n[4] ACTIVITES RECENTES")
    print("-" * 35)

    for evenement in evenements[-5:][::-1]:
        print(
            evenement.get("statut", "?"),
            "|",
            evenement.get("agent", "?"),
            "|",
            evenement.get("action", "?")
        )

    print("\n[5] ETAT DU SYSTEME")
    print("-" * 35)
    print("Journal       : PRESENT")
    print("Authenticite  : VALIDEE")
    print("Integrite     : VERIFIEE")
    print("Actualisation :", datetime.now().astimezone().isoformat())


def menu():
    while True:
        print("\n" + "=" * 46)
        print("       HUMANITY AI SHIELD - V3")
        print("=" * 46)
        print("1. Afficher le tableau de bord")
        print("2. Generer un rapport securise")
        print("3. Verifier l'integrite HMAC")
        print("0. Quitter")

        choix = input("\nTon choix : ").strip()

        if choix == "1":
            afficher_tableau()

        elif choix == "2":
            generer_rapport.generer()

        elif choix == "3":
            protection_hmac.verifier()

        elif choix == "0":
            print("Fermeture du tableau de bord.")
            break

        else:
            print("[ERREUR] Choix invalide.")


if __name__ == "__main__":
    menu()

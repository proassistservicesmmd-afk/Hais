import json
from pathlib import Path
from datetime import datetime, timezone

import protection_hmac

BASE = Path(__file__).resolve().parent
FICHIER_REGLES = BASE / "regles" / "securite.json"
FICHIER_LOG = BASE / "logs" / "activites.jsonl"


def charger_regles():
    with FICHIER_REGLES.open("r", encoding="utf-8") as fichier:
        regles = json.load(fichier)

    if not isinstance(regles.get("actions_interdites"), list):
        raise ValueError("Liste des actions interdites invalide.")

    return regles


def analyser_evenement(action, agent="agent_test"):
    if not isinstance(action, str) or not action.strip():
        print("[REFUS] Action invalide.")
        return False

    if not isinstance(agent, str) or not agent.strip():
        print("[REFUS] Identifiant agent invalide.")
        return False

    try:
        regles = charger_regles()
        interdites = regles["actions_interdites"]

        alerte = action.strip() in interdites

        evenement = {
            "date": datetime.now(timezone.utc).isoformat(),
            "agent": agent.strip(),
            "action": action.strip(),
            "statut": "ALERTE" if alerte else "AUTORISE",
            "niveau": regles["niveau_alerte"] if alerte else "NORMAL"
        }

        journal = FICHIER_LOG
        journal.parent.mkdir(parents=True, exist_ok=True)

        # Vérifier le journal existant avant toute écriture.
        if journal.exists():
            if not protection_hmac.verifier(
                journal=journal,
                afficher=False
            ):
                print("[REFUS] Integrite du journal non garantie.")
                return False
        else:
            # Un journal absent ne peut pas être recréé
            # automatiquement sans procédure d'initialisation.
            print("[REFUS] Journal absent. Initialisation requise.")
            return False

        # Préserver le contenu avant modification.
        ancien_contenu = journal.read_bytes()

        with journal.open("a", encoding="utf-8") as fichier:
            fichier.write(
                json.dumps(evenement, ensure_ascii=False) + "\n"
            )

        try:
            protection_hmac.signer(
                journal=journal,
                afficher=False
            )

            if not protection_hmac.verifier(
                journal=journal,
                afficher=False
            ):
                raise RuntimeError("Verification HMAC apres ecriture echouee.")

        except Exception:
            # Restaurer le journal si la mise à jour de signature échoue.
            journal.write_bytes(ancien_contenu)
            print("[ERREUR] Signature non actualisee. Journal restaure.")
            return False

        print("\n=== AI RISK MONITOR ===")
        print("Agent :", evenement["agent"])
        print("Action :", evenement["action"])

        if alerte:
            print("[ALERTE] Action interdite detectee !")
        else:
            print("[OK] Aucune regle violee.")

        print("Statut :", evenement["statut"])
        print("[OK] Signature HMAC actualisee et verifiee.")

        return True

    except Exception as erreur:
        print("[ERREUR]", erreur)
        return False


if __name__ == "__main__":
    analyser_evenement("acces_non_autorise")
    analyser_evenement("lecture_fichier")

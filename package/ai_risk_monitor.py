import json
import os
from pathlib import Path
from datetime import datetime, timezone

import protection_hmac
from moteur_risques import analyser_action, DECISIONS_VALIDES
from transaction_securisee import executer_transaction

BASE = Path(__file__).resolve().parent
FICHIER_LOG = BASE / "logs" / "activites.jsonl"
FICHIER_LOG_REFUS = BASE / "logs" / "refus.jsonl"

# Compatibilité tests existants (patch.object l'exige)
FICHIER_REGLES = BASE / "regles" / "securite_v4.json"

DECISIONS_JOURNALISABLES = DECISIONS_VALIDES


def _tracer_refus(raison, action_tentee, agent_tente):
    """Journalise un refus dans le journal secondaire HMAC-signé.
    Best-effort : ne lève jamais d'exception pour ne pas casser le refus."""
    try:
        FICHIER_LOG_REFUS.parent.mkdir(parents=True, exist_ok=True)
        if not FICHIER_LOG_REFUS.is_file():
            FICHIER_LOG_REFUS.write_text("", encoding="utf-8")

        evenement = {
            "date": datetime.now(timezone.utc).isoformat(),
            "raison": raison,
            "action_tentee": repr(action_tentee)[:200],
            "agent_tente": repr(agent_tente)[:200],
        }

        signature_refus = FICHIER_LOG_REFUS.parent / "signature_refus.sha256"

        def operation():
            with FICHIER_LOG_REFUS.open("a", encoding="utf-8") as f:
                f.write(json.dumps(evenement, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
            protection_hmac.signer(FICHIER_LOG_REFUS,
                journal=FICHIER_LOG_REFUS,
                signature=signature_refus,
                cle=protection_hmac.CLE,
                afficher=False,
            )

        executer_transaction(
            journal=FICHIER_LOG_REFUS,
            signature=signature_refus,
            operation=operation,
            cle=protection_hmac.CLE,
        )
    except Exception:
        pass


def analyser_evenement(action, agent="agent_test"):
    if not isinstance(action, str) or not action.strip():
        print("[REFUS] Action invalide.")
        _tracer_refus("action_invalide", action, agent)
        return False
    if not isinstance(agent, str) or not agent.strip():
        print("[REFUS] Identifiant agent invalide.")
        _tracer_refus("agent_invalide", action, agent)
        return False

    try:
        resultat = analyser_action(action)
        decision = resultat["decision"]
        niveau = resultat["niveau"]

        if decision not in DECISIONS_JOURNALISABLES:
            print(f"[REFUS] Decision '{decision}' hors contrat.")
            _tracer_refus(f"decision_hors_contrat:{decision}", action, agent)
            return False

        evenement = {
            "date": datetime.now(timezone.utc).isoformat(),
            "agent": agent.strip(),
            "action": action.strip(),
            "statut": decision,
            "niveau": niveau,
            "decision": decision,
            "motif": resultat["motif"],
        }

        journal = FICHIER_LOG
        journal.parent.mkdir(parents=True, exist_ok=True)

        if not journal.is_file():
            print("[REFUS] Journal absent. Initialisation requise.")
            _tracer_refus("journal_absent", action, agent)
            return False

        def operation():
            with journal.open("a", encoding="utf-8") as fichier:
                fichier.write(json.dumps(evenement, ensure_ascii=False) + "\n")
                fichier.flush()
                os.fsync(fichier.fileno())
            protection_hmac.signer(journal,
                journal=journal,
                signature=protection_hmac.SIGNATURE,
                cle=protection_hmac.CLE,
                afficher=False,
            )

        executer_transaction(
            journal=journal,
            signature=protection_hmac.SIGNATURE,
            operation=operation,
            cle=protection_hmac.CLE,
        )

        print("\n=== HUMANITY AI SHIELD V6.2 ===")
        print("Agent :", evenement["agent"])
        print("Action :", evenement["action"])
        print("Niveau :", niveau)
        print("Decision :", decision)
        print("Motif :", resultat["motif"])
        print("[OK] Transaction signee et verifiee.")
        return True

    except Exception as erreur:
        print("[ERREUR] Transaction annulee :", erreur)
        return False


if __name__ == "__main__":
    analyser_evenement("lecture_fichier", "agent_v6_test")
    analyser_evenement("acces_non_autorise", "agent_v6_test")

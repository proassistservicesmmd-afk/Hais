from pathlib import Path
import protection_hmac

BASE = Path(__file__).resolve().parent

JOURNAL = BASE / "logs" / "activites.jsonl"
CLE = Path.home() / ".humanity_ai_shield" / "cle_hmac.key"
SIGNATURE = BASE / "rapports" / "integrite" / "signature_hmac.sha256"


def verifier_complet():
    print("================================")
    print(" HUMANITY AI SHIELD - V2")
    print(" VERIFICATION DE SECURITE")
    print("================================")

    controles = [
        ("Journal", JOURNAL.is_file()),
        ("Cle secrete", CLE.is_file()),
        ("Signature HMAC", SIGNATURE.is_file()),
    ]

    for nom, resultat in controles:
        print(
            f"[{'OK' if resultat else 'ALERTE'}] {nom}"
        )

    if not all(resultat for _, resultat in controles):
        print("[ECHEC] Verification incomplete.")
        return False

    if not protection_hmac.verifier():
        print("[ALERTE] Integrite non garantie.")
        return False

    print("[OK] Tous les controles sont valides.")
    return True


if __name__ == "__main__":
    verifier_complet()

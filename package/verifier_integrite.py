import hashlib
import hmac
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
JOURNAL = BASE / "logs" / "activites.jsonl"
EMPREINTE = BASE / "rapports" / "integrite" / "empreinte_initiale.sha256"

FORMAT_REFERENCE = re.compile(
    r"^([0-9a-f]{64})  logs/activites\.jsonl\n?$"
)


def calculer_sha256(fichier):
    sha = hashlib.sha256()

    with Path(fichier).open("rb") as source:
        for bloc in iter(lambda: source.read(65536), b""):
            sha.update(bloc)

    return sha.hexdigest()


def verifier():
    try:
        if not JOURNAL.is_file():
            print("[ERREUR] Journal introuvable.")
            return False

        if not EMPREINTE.is_file():
            print("[ERREUR] Fichier d'empreinte introuvable.")
            return False

        contenu = EMPREINTE.read_text(encoding="ascii")
        correspondance = FORMAT_REFERENCE.fullmatch(contenu)

        if correspondance is None:
            print("[ERREUR] Format de reference SHA-256 invalide.")
            return False

        empreinte_attendue = correspondance.group(1)
        empreinte_actuelle = calculer_sha256(JOURNAL)

        if hmac.compare_digest(
            empreinte_actuelle, empreinte_attendue
        ):
            print("[OK] Journal intact.")
            return True

        print("[ALERTE] Modification ou incoherence du journal detectee !")
        print("[INFO] L'empreinte historique ne correspond pas au journal.")
        return False

    except (OSError, UnicodeError, ValueError) as erreur:
        print("[ERREUR] Verification impossible :", erreur)
        return False


if __name__ == "__main__":
    verifier()

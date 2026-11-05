import hashlib
import hmac
import os
import re
import tempfile

from pathlib import Path


BASE = Path(__file__).resolve().parent

JOURNAL = BASE / "logs" / "activites.jsonl"

CLE = Path.home() / ".humanity_ai_shield" / "cle_hmac.key"

SIGNATURE = BASE / "rapports" / "integrite" / "signature_hmac.sha256"

TAILLE_CLE = 32
TAILLE_SIGNATURE = 64


def empreinte_sha256(fichier):
    """Calcule SHA-256 sans charger tout le fichier en mémoire."""

    fichier = Path(fichier)
    sha = hashlib.sha256()

    with fichier.open("rb") as source:
        for bloc in iter(lambda: source.read(65536), b""):
            sha.update(bloc)

    return sha.hexdigest()


def _charger_cle(chemin):
    """Charge et valide la clé secrète."""

    chemin = Path(chemin)
    secret = chemin.read_bytes()

    if len(secret) != TAILLE_CLE:
        raise ValueError("Cle secrete invalide.")

    return secret


def _calculer_signature(journal, secret):
    """Conserve l'algorithme HMAC historique."""

    empreinte = empreinte_sha256(journal)

    return hmac.new(
        secret,
        empreinte.encode("ascii"),
        hashlib.sha256
    ).hexdigest()


def _ecrire_atomiquement(destination, contenu):
    """Remplace une signature sans laisser de fichier partiel."""

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    fd, temporaire = tempfile.mkstemp(
        prefix=".signature_",
        suffix=".tmp",
        dir=str(destination.parent)
    )

    try:
        os.fchmod(fd, 0o600)

        with os.fdopen(fd, "w", encoding="ascii") as fichier:
            fichier.write(contenu)
            fichier.flush()
            os.fsync(fichier.fileno())

        os.replace(temporaire, destination)
        destination.chmod(0o600)

    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass

        try:
            os.unlink(temporaire)
        except OSError:
            pass

        raise


def signer(journal=None, signature=None, cle=None, afficher=True):

    journal = Path(journal) if journal is not None else JOURNAL
    signature = Path(signature) if signature is not None else SIGNATURE
    cle = Path(cle) if cle is not None else CLE

    if not journal.is_file():
        raise FileNotFoundError("Journal introuvable.")

    if not cle.is_file():
        raise FileNotFoundError("Cle secrete introuvable.")

    secret = _charger_cle(cle)

    resultat = _calculer_signature(journal, secret)

    _ecrire_atomiquement(signature, resultat + "\n")

    if afficher:
        print("[OK] Signature HMAC enregistree.")

    return True


def verifier(journal=None, signature=None, cle=None, afficher=True):

    journal = Path(journal) if journal is not None else JOURNAL
    signature = Path(signature) if signature is not None else SIGNATURE
    cle = Path(cle) if cle is not None else CLE

    try:

        if not journal.is_file():
            raise FileNotFoundError("Journal absent.")

        if not cle.is_file() or not signature.is_file():
            raise FileNotFoundError("Cle ou signature absente.")

        secret = _charger_cle(cle)

        recue = signature.read_text(
            encoding="ascii"
        ).strip()

        if not re.fullmatch(r"[0-9a-f]{64}", recue):
            raise ValueError("Format de signature invalide.")

        attendue = _calculer_signature(journal, secret)

        if not hmac.compare_digest(attendue, recue):
            if afficher:
                print("[ALERTE] Modification ou falsification detectee !")

            return False

        if afficher:
            print("[OK] Authenticite et integrite verifiees.")

        return True

    except (OSError, UnicodeError, ValueError) as erreur:

        if afficher:
            print("[ERREUR]", erreur)

        return False


if __name__ == "__main__":
    verifier()

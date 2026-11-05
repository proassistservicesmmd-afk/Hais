import hashlib
import hmac
import json
import os
import re
import tempfile
from pathlib import Path

import protection_hmac


def empreinte_sha256(contenu):
    return hashlib.sha256(contenu).hexdigest()


def charger_cle(cle=None):
    chemin = Path(cle or protection_hmac.CLE)
    contenu = chemin.read_bytes()

    if len(contenu) != 32:
        raise ValueError("La cle HMAC doit contenir 32 octets.")

    return contenu


def signer_manifeste(donnees, cle=None):
    secret = charger_cle(cle)

    contenu = json.dumps(
        donnees,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")

    return hmac.new(
        secret,
        contenu,
        hashlib.sha256
    ).hexdigest()


def verifier_manifeste(donnees, signature, cle=None):
    signature_attendue = signer_manifeste(donnees, cle)

    return hmac.compare_digest(
        signature_attendue,
        signature
    )


def ecrire_atomiquement(destination, contenu):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(destination.parent, 0o700)

    temporaire = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=destination.name + ".",
            suffix=".tmp",
            delete=False
        ) as fichier:
            temporaire = Path(fichier.name)
            os.chmod(temporaire, 0o600)

            fichier.write(contenu)
            fichier.flush()
            os.fsync(fichier.fileno())

        os.replace(temporaire, destination)
        os.chmod(destination, 0o600)

        dossier_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(dossier_fd)
        finally:
            os.close(dossier_fd)

    finally:
        if temporaire is not None and temporaire.exists():
            temporaire.unlink()


if __name__ == "__main__":
    print("HUMANITY AI SHIELD - Module WAL experimental charge.")


def creer_sauvegarde_wal(journal, signature, dossier_wal, cle=None):
    journal = Path(journal)
    signature = Path(signature)
    dossier_wal = Path(dossier_wal)

    if not journal.is_file() or not signature.is_file():
        raise FileNotFoundError("Journal ou signature absent.")

    # Verifier la paire originale AVANT toute copie.
    if not protection_hmac.verifier(
        journal=journal,
        signature=signature,
        cle=cle,
        afficher=False
    ):
        raise RuntimeError("Journal original non authentique.")

    contenu_journal = journal.read_bytes()
    contenu_signature = signature.read_bytes()

    dossier_wal.mkdir(parents=True, exist_ok=True)
    os.chmod(dossier_wal, 0o700)

    sauvegarde_journal = dossier_wal / "journal.backup"
    sauvegarde_signature = dossier_wal / "signature.backup"

    ecrire_atomiquement(sauvegarde_journal, contenu_journal)
    ecrire_atomiquement(sauvegarde_signature, contenu_signature)

    if sauvegarde_journal.read_bytes() != contenu_journal:
        raise RuntimeError("Verification sauvegarde journal echouee.")

    if sauvegarde_signature.read_bytes() != contenu_signature:
        raise RuntimeError("Verification sauvegarde signature echouee.")

    return {
        "journal_sha256": empreinte_sha256(contenu_journal),
        "signature_sha256": empreinte_sha256(contenu_signature),
    }


def creer_manifeste_wal(empreintes, cle=None):
    donnees = {
        "version": 1,
        "etat": "active",
        "journal_sha256": empreintes["journal_sha256"],
        "signature_sha256": empreintes["signature_sha256"],
    }

    signature_hmac = signer_manifeste(donnees, cle)

    return {
        "donnees": donnees,
        "hmac": signature_hmac,
    }


def verifier_integrite_manifeste(manifeste, cle=None):
    if not isinstance(manifeste, dict):
        return False

    if set(manifeste) != {"donnees", "hmac"}:
        return False

    donnees = manifeste.get("donnees")
    signature = manifeste.get("hmac")

    if not isinstance(donnees, dict):
        return False

    champs = {
        "version",
        "etat",
        "journal_sha256",
        "signature_sha256",
    }

    if set(donnees) != champs:
        return False

    if type(donnees.get("version")) is not int:
        return False

    if donnees["version"] != 1:
        return False

    if donnees.get("etat") not in ("active", "committed"):
        return False

    for champ in ("journal_sha256", "signature_sha256"):
        valeur = donnees.get(champ)

        if not isinstance(valeur, str):
            return False

        if re.fullmatch(r"[0-9a-f]{64}", valeur) is None:
            return False

    if not isinstance(signature, str):
        return False

    if re.fullmatch(r"[0-9a-f]{64}", signature) is None:
        return False

    try:
        return verifier_manifeste(donnees, signature, cle)
    except (OSError, ValueError, TypeError):
        return False


def enregistrer_manifeste_wal(manifeste, dossier_wal, cle=None):
    if not verifier_integrite_manifeste(manifeste, cle):
        raise RuntimeError("Manifeste WAL invalide.")

    dossier_wal = Path(dossier_wal)
    dossier_wal.mkdir(parents=True, exist_ok=True)

    fichier = dossier_wal / "manifest.json"

    contenu = json.dumps(
        manifeste,
        sort_keys=True,
        ensure_ascii=False,
        indent=2
    ).encode("utf-8")

    ecrire_atomiquement(fichier, contenu)

    relu = json.loads(fichier.read_text(encoding="utf-8"))

    if not verifier_integrite_manifeste(relu, cle):
        raise RuntimeError("Verification du manifeste enregistre echouee.")

    return fichier


def detecter_wal(dossier_wal, cle=None):
    dossier_wal = Path(dossier_wal)
    fichier = dossier_wal / "manifest.json"

    if not fichier.is_file():
        return None

    try:
        manifeste = json.loads(
            fichier.read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        raise RuntimeError("Manifeste WAL illisible.")

    if not verifier_integrite_manifeste(manifeste, cle):
        raise RuntimeError("Manifeste WAL non authentique.")

    return manifeste


def verifier_sauvegardes_wal(dossier_wal, manifeste, cle=None):
    if not verifier_integrite_manifeste(manifeste, cle):
        raise RuntimeError("Manifeste WAL non authentique.")

    dossier_wal = Path(dossier_wal)
    journal = dossier_wal / "journal.backup"
    signature = dossier_wal / "signature.backup"

    if not journal.is_file() or not signature.is_file():
        raise RuntimeError("Sauvegarde WAL incomplete.")

    donnees = manifeste["donnees"]

    empreinte_journal = empreinte_sha256(journal.read_bytes())
    empreinte_signature = empreinte_sha256(signature.read_bytes())

    if not hmac.compare_digest(
        empreinte_journal, donnees["journal_sha256"]
    ):
        raise RuntimeError("Sauvegarde du journal alteree.")

    if not hmac.compare_digest(
        empreinte_signature, donnees["signature_sha256"]
    ):
        raise RuntimeError("Sauvegarde de signature alteree.")

    if not protection_hmac.verifier(
        journal=journal,
        signature=signature,
        cle=cle,
        afficher=False
    ):
        raise RuntimeError("Paire HMAC de sauvegarde invalide.")

    return True

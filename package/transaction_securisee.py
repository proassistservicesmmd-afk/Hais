import os
import tempfile
from pathlib import Path

import protection_hmac


def ecrire_atomiquement(destination, contenu):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

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
            fichier.write(contenu)
            fichier.flush()
            os.fsync(fichier.fileno())

        os.replace(temporaire, destination)

        dossier_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(dossier_fd)
        finally:
            os.close(dossier_fd)

    finally:
        if temporaire is not None and temporaire.exists():
            temporaire.unlink()


def executer_transaction(journal, signature, operation, cle=None):
    journal = Path(journal)
    signature = Path(signature)

    if not journal.is_file() or not signature.is_file():
        raise FileNotFoundError(
            "Journal ou signature absent avant transaction."
        )

    if not protection_hmac.verifier(
        journal=journal,
        signature=signature,
        cle=cle,
        afficher=False
    ):
        raise RuntimeError("Integrite initiale non garantie.")

    ancien_journal = journal.read_bytes()
    ancienne_signature = signature.read_bytes()

    try:
        operation()

        if not protection_hmac.verifier(
            journal=journal,
            signature=signature,
            cle=cle,
            afficher=False
        ):
            raise RuntimeError(
                "Verification finale de la transaction echouee."
            )

        return True

    except Exception:
        ecrire_atomiquement(journal, ancien_journal)
        ecrire_atomiquement(signature, ancienne_signature)

        if not protection_hmac.verifier(
            journal=journal,
            signature=signature,
            cle=cle,
            afficher=False
        ):
            raise RuntimeError(
                "Echec critique : restauration non verifiee."
            )

        raise


if __name__ == "__main__":
    print("Module de transaction securisee charge.")

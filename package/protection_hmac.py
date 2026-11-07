# -*- coding: utf-8 -*-
"""
HUMANITY AI SHIELD - V7.0
Module de protection HMAC et de gestion des chemins.
Adapté pour PC et Android (Kivy).
"""

import os
import hmac
import hashlib
import json
from pathlib import Path
from datetime import datetime
try:
    from kivy.utils import platform
except ImportError:
    platform = "linux"

# =========================================================
# 1. GESTION DES CHEMINS (ADAPTATION ANDROID)
# =========================================================
if platform == 'android':
    # Sur Android, on utilise le dossier privé de l'application
    from android.storage import app_storage_path
    BASE = Path(app_storage_path())
else:
    # Sur PC, on utilise le dossier du script
    BASE = Path(__file__).resolve().parent

JOURNAL = BASE / "logs" / "activites.jsonl"
CLE = BASE / ".humanity_ai_shield" / "cle_hmac.key"
SIGNATURE = BASE / "rapports" / "integrite" / "signature_hmac.sha256"

# Création automatique des dossiers nécessaires
for dossier in [JOURNAL.parent, CLE.parent, SIGNATURE.parent]:
    dossier.mkdir(parents=True, exist_ok=True)

# =========================================================
# 2. FONCTIONS DE HACHAGE ET SIGNATURE
# =========================================================

def calculer_hmac(fichier):
    """Calcule le HMAC SHA256 d'un fichier."""
    fichier = Path(fichier)
    if not fichier.is_file():
        raise FileNotFoundError(f"Fichier introuvable : {fichier}")

    # Chargement de la clé
    if not CLE.is_file():
        raise FileNotFoundError(f"Clé HMAC introuvable : {CLE}")

    with CLE.open("rb") as f:
        cle_secrete = f.read().strip()

    # Calcul
    h = hmac.new(cle_secrete, digestmod=hashlib.sha256)
    with fichier.open("rb") as source:
        for bloc in iter(lambda: source.read(4096), b""):
            h.update(bloc)
    
    return h.hexdigest()


def signer(fichier, signature=None, **kwargs):
    """Génère et sauvegarde la signature d'un fichier."""
    fichier = Path(fichier)
    if not fichier.exists():
        fichier.touch()
    signature = Path(signature) if signature is not None else SIGNATURE
    
    # Création du dossier de signature si besoin
    signature.parent.mkdir(parents=True, exist_ok=True)
    
    empreinte = calculer_hmac(fichier)
    
    # Écriture atomique de la signature
    temporaire = signature.with_suffix(".tmp")
    with temporaire.open("w", encoding="ascii") as f:
        f.write(empreinte + "\n")
    os.replace(temporaire, signature)
    
    return empreinte


def verifier_signature(fichier, signature=None):
    """Vérifie qu'un fichier correspond à sa signature."""
    fichier = Path(fichier)
    signature = Path(signature) if signature is not None else SIGNATURE
    
    if not fichier.is_file():
        return False
    if not signature.is_file():
        return False

    try:
        with signature.open("r", encoding="ascii") as f:
            empreinte_attendue = f.read().strip()
        
        empreinte_calculee = calculer_hmac(fichier)
        return hmac.compare_digest(empreinte_attendue, empreinte_calculee)
    except Exception:
        return False


# =========================================================
# 3. INITIALISATION DE LA CLÉ (Si elle n'existe pas)
# =========================================================

def initialiser_cle():
    """Génère une clé HMAC aléatoire si elle n'existe pas."""
    if not CLE.is_file():
        CLE.parent.mkdir(parents=True, exist_ok=True)
        cle_aleatoire = os.urandom(32)
        
        # Écriture sécurisée (droits restreints)
        with CLE.open("wb") as f:
            f.write(cle_aleatoire)
        
        # Restriction des permissions (Unix uniquement)
        try:
            os.chmod(CLE, 0o600)
        except Exception:
            pass
        
        return True
    return False


# =========================================================
# 4. VÉRIFICATION GLOBALE
# =========================================================

def verifier(fichier=None, signature=None, cle=None, **kwargs):
    """
    Vérifie l'intégrité d'un fichier.
    Si aucun fichier n'est fourni, vérifie le journal par défaut.
    """
    fichier = Path(fichier) if fichier is not None else JOURNAL
    signature = Path(signature) if signature is not None else SIGNATURE

    if not fichier.is_file():
        print(f"[ERREUR] Fichier introuvable : {fichier}")
        return False

    if not verifier_signature(fichier, signature):
        print(f"[REFUS] Signature invalide ou absente pour : {fichier}")
        return False

    print(f"[OK] Intégrité vérifiée : {fichier.name}")
    return True


# =========================================================
# 5. AJOUT D'ÉVÉNEMENTS AU JOURNAL
# =========================================================

def ajouter_evenement(evenement, journal=None, signature=None):
    """Ajoute un événement au journal et met à jour la signature."""
    journal = Path(journal) if journal is not None else JOURNAL
    signature = Path(signature) if signature is not None else SIGNATURE
    
    # Assurer que la clé existe
    initialiser_cle()
    
    # Ajout de l'horodatage si absent
    if "date" not in evenement:
        evenement["date"] = datetime.now().astimezone().isoformat()
    
    # Écriture dans le journal
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evenement, ensure_ascii=False) + "\n")
    
    # Mise à jour de la signature
    return signer(journal, signature)


# =========================================================
# 6. TEST LOCAL (Uniquement si exécuté directement)
# =========================================================

if __name__ == "__main__":
    print("=== TEST DE PROTECTION HMAC ===")
    
    # 1. Initialisation de la clé
    if initialiser_cle():
        print(f"[+] Nouvelle clé générée : {CLE}")
    else:
        print(f"[*] Clé existante : {CLE}")
    
    # 2. Ajout d'un événement de test
    test_evenement = {
        "agent": "test_script",
        "action": "test_hmac",
        "niveau": "NORMAL",
        "statut": "AUTORISE"
    }
    ajouter_evenement(test_evenement)
    print(f"[+] Événement ajouté au journal : {JOURNAL}")
    
    # 3. Vérification
    if verifier():
        print("[SUCCÈS] L'intégrité du journal est validée.")
    else:
        print("[ÉCHEC] L'intégrité du journal est compromise.")


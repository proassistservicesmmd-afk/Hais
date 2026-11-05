import json
from pathlib import Path

DECISIONS_VALIDES = ("AUTORISER", "ALERTE", "BLOQUER", "REFUSER")
NIVEAUX_VALIDES = ("NORMAL", "ELEVE", "CRITIQUE", "INCONNU")

BASE = Path(__file__).resolve().parent
FICHIER_REGLES = BASE / "regles" / "securite_v4.json"

REGLES_PAR_DEFAUT = {
    "version": "4.0",
    "regles": [
        {"action": "acces_non_autorise", "niveau": "CRITIQUE", "decision": "BLOQUER"},
        {"action": "suppression_fichier", "niveau": "ELEVE", "decision": "ALERTE"},
        {"action": "transfert_donnees_sensibles", "niveau": "CRITIQUE", "decision": "BLOQUER"},
        {"action": "commande_interdite", "niveau": "CRITIQUE", "decision": "BLOQUER"},
    ],
}


def _valider_regle(regle, index):
    if not isinstance(regle, dict):
        raise ValueError(f"Règle #{index} : objet attendu, {type(regle).__name__} reçu")
    for champ in ("action", "niveau", "decision"):
        if champ not in regle:
            raise ValueError(f"Règle #{index} : champ '{champ}' manquant")
        if not isinstance(regle[champ], str) or not regle[champ].strip():
            raise ValueError(f"Règle #{index} : champ '{champ}' vide ou invalide")
    if regle["decision"] not in DECISIONS_VALIDES:
        raise ValueError(
            f"Règle #{index} : decision '{regle['decision']}' hors contrat {DECISIONS_VALIDES}"
        )
    if regle["niveau"] not in NIVEAUX_VALIDES:
        raise ValueError(
            f"Règle #{index} : niveau '{regle['niveau']}' hors contrat {NIVEAUX_VALIDES}"
        )


def charger_regles():
    if not FICHIER_REGLES.exists():
        FICHIER_REGLES.parent.mkdir(parents=True, exist_ok=True)
        FICHIER_REGLES.write_text(
            json.dumps(REGLES_PAR_DEFAUT, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
    with FICHIER_REGLES.open(encoding="utf-8") as fichier:
        donnees = json.load(fichier)
    if not isinstance(donnees.get("regles"), list):
        raise ValueError("Format des règles invalide : clé 'regles' attendue (liste).")
    for i, regle in enumerate(donnees["regles"]):
        _valider_regle(regle, i)
    return donnees["regles"]


def analyser_action(action):
    if not isinstance(action, str) or not action.strip():
        return {"niveau": "INCONNU", "decision": "REFUSER", "motif": "Action invalide"}
    action = action.strip().lower()
    for regle in charger_regles():
        if action == regle["action"].strip().lower():
            return {
                "niveau": regle["niveau"],
                "decision": regle["decision"],
                "motif": "Règle de sécurité déclenchée",
            }
    return {"niveau": "NORMAL", "decision": "AUTORISER", "motif": "Aucune règle déclenchée"}


if __name__ == "__main__":
    for action in ["lecture_fichier", "acces_non_autorise", "suppression_fichier"]:
        r = analyser_action(action)
        print(f"{action} -> {r['decision']} ({r['niveau']})")

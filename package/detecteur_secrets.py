"""detecteur_secrets.py — V7.0
Détecte 12 types de secrets avant envoi à une IA.
API publique : inspecter(texte) -> {"niveau": "OK"|"WARN"|"BLOCK", "detections": [...]}
"""
import re
import sys


def _luhn_valide(numero):
    chiffres = [int(c) for c in numero if c.isdigit()]
    if len(chiffres) < 13 or len(chiffres) > 19:
        return False
    total = 0
    pair = False
    for c in reversed(chiffres):
        if pair:
            c *= 2
            if c > 9:
                c -= 9
        total += c
        pair = not pair
    return total % 10 == 0


def _iban_valide(iban):
    iban = iban.replace(" ", "").upper()
    if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$', iban):
        return False
    rearranged = iban[4:] + iban[:4]
    numerique = ""
    for c in rearranged:
        if c.isdigit():
            numerique += c
        elif c.isalpha():
            numerique += str(ord(c) - ord('A') + 10)
        else:
            return False
    try:
        return int(numerique) % 97 == 1
    except ValueError:
        return False


DETECTEURS = []


def _detecteur(nom, niveau, regex):
    pattern = re.compile(regex)

    def fn(texte):
        for m in pattern.finditer(texte):
            yield {
                "type": nom,
                "position": m.start(),
                "extrait": m.group(0)[:40],
                "niveau": niveau,
            }

    DETECTEURS.append(fn)


_detecteur("anthropic_key", "BLOCK", r'sk-ant-[a-zA-Z0-9_-]{20,}')
_detecteur("openai_key",    "BLOCK", r'sk-(?!ant-)(?:proj-)?[a-zA-Z0-9]{20,}')
_detecteur("github_token",  "BLOCK", r'gh[pousr]_[a-zA-Z0-9]{20,}')
_detecteur("github_pat",    "BLOCK", r'github_pat_[a-zA-Z0-9_]{20,}')
_detecteur("aws_key",       "BLOCK", r'AKIA[A-Z0-9]{16}')
_detecteur("ssh_private_key", "BLOCK",
           r'-----BEGIN (?:OPENSSH|RSA|DSA|EC|PGP) PRIVATE KEY-----')
_detecteur("jwt", "BLOCK",
           r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+')
_detecteur("bearer_token", "BLOCK",
           r'Bearer\s+[a-zA-Z0-9_\-.~+/]{20,}')
_detecteur("password_inline", "BLOCK",
           r'(?:password|passwd|pwd|mot_de_passe|mdp)\s*[=:]\s*["\']?[^\s"\']{6,}')
_detecteur("sensitive_path", "BLOCK",
           r'(?:~|/home/[^/\s]+|/root)/\.(?:ssh|aws|gnupg|humanity_ai_shield)(?:/|\b)')


def _detecter_carte(texte):
    for m in re.finditer(r'\b(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4,7})\b', texte):
        numero = re.sub(r'[\s-]', '', m.group(1))
        if _luhn_valide(numero):
            yield {
                "type": "credit_card",
                "position": m.start(),
                "extrait": "****" + numero[-4:],
                "niveau": "BLOCK",
            }


def _detecter_iban(texte):
    for m in re.finditer(r'\b([A-Z]{2}\d{2}[\sA-Z0-9]{11,30})\b', texte):
        if _iban_valide(m.group(1)):
            yield {
                "type": "iban",
                "position": m.start(),
                "extrait": m.group(1)[:8] + "...",
                "niveau": "BLOCK",
            }


def inspecter(texte):
    if not isinstance(texte, str):
        texte = str(texte)
    detections = []
    for fn in DETECTEURS:
        detections.extend(fn(texte))
    detections.extend(_detecter_carte(texte))
    detections.extend(_detecter_iban(texte))
    if any(d["niveau"] == "BLOCK" for d in detections):
        niveau = "BLOCK"
    elif any(d["niveau"] == "WARN" for d in detections):
        niveau = "WARN"
    else:
        niveau = "OK"
    return {"niveau": niveau, "detections": detections}


def formater_resultat(resultat):
    if resultat["niveau"] == "OK":
        return "[OK] Aucun secret détecté."
    lignes = [f"[{resultat['niveau']}] {len(resultat['detections'])} détection(s) :"]
    for d in resultat["detections"]:
        lignes.append(f"  - {d['type']} (pos {d['position']}) : {d['extrait']}")
    return "\n".join(lignes)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        texte = " ".join(sys.argv[1:])
    else:
        texte = sys.stdin.read()
    resultat = inspecter(texte)
    print(formater_resultat(resultat))
    sys.exit(0 if resultat["niveau"] == "OK" else 1)

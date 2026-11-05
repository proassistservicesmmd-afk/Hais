# UTILISER V7.0 — Garde des secrets

## Utilisation en CLI

Analyser un texte :

  cd ~/HUMANITY_AI_SHIELD_V7_0/package
  python detecteur_secrets.py "ma cle sk-ant-api03-abcdefghij0123456789abcdef"

Analyser un fichier :

  cat mon_prompt.txt | python detecteur_secrets.py

## Utilisation comme module Python

    from detecteur_secrets import inspecter
    resultat = inspecter("texte a analyser")
    if resultat["niveau"] == "BLOCK":
        print("Envoi refuse : secret detecte")
    else:
        print("Envoi autorise")

## Niveaux

- OK : aucun secret, vous pouvez envoyer
- WARN : suspect mais pas bloquant
- BLOCK : secret certain, n envoyez pas

## Limites

- Detection par pattern, pas semantique
- Un secret encode (base64) peut passer
- Ce module bloque a l envoi, pas ce qui est deja parti

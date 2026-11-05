# REPRISE V6.2 — Guide

## Lignée
- V5   : 32 tests, référence scellée (2026-11-05 13:31:55)
- V6.0 : 32 tests, reconstruction scellée (2026-11-05 14:05:20)
- V6.1 : 37 tests, durcissement moteur
- V6.2 : 41 tests, traçabilité des refus

## Lancer les tests
cd ~/HUMANITY_AI_SHIELD_V6_RECONSTRUCTION/package
cp -a ../tests ./tests
python -m unittest discover -s tests -v
rm -rf ./tests

Attendu : Ran 41 tests puis OK.

## Traçabilité des refus (V6.2)
Quand analyser_evenement refuse, il écrit dans package/logs/refus.jsonl :
- date : timestamp UTC
- raison : action_invalide, agent_invalide, decision_hors_contrat, journal_absent
- action_tentee, agent_tente : repr tronquée 200 car

Journal HMAC-signé séparément (signature_refus.sha256). Tracé best-effort :
un échec de traçage ne casse jamais le refus.

## Revenir à V6.0 ou V6.1
ls -d ~/V6_0_AVANT_CHANTIER_1_* ~/V6_1_AVANT_CHANTIER_2_*

## Glossaire
- HMAC : Hash-based Message Authentication Code
- WAL : Write-Ahead Logging
- Scellé : empreinte SHA256 stockée hors projet

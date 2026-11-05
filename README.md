# HUMANITY AI SHIELD — V6 Reconstruction

**HUMANITY FIRST** — L'IA doit servir l'humanité, pas mettre son avenir en danger.

*Protection, responsabilité, confiance.*

---

## Mission
Couche de sécurité indépendante capable de surveiller, analyser, contrôler
et tracer les actions des intelligences artificielles afin de réduire les
risques pour les humains. Ne prétend pas rendre toutes les IA inoffensives
ni garantir une sécurité absolue. Fournit des contrôles techniques réels,
vérifiables et résistants aux erreurs.

## Structure du livrable
```
V6/
├── README.md                (ce fichier)
├── package/                 (code applicatif, structure plate comme V5)
│   ├── *.py                 (12 modules)
│   ├── regles/              (securite.json, securite_v4.json)
│   └── logs/                (journaux + signatures HMAC)
├── tests/                   (5 fichiers, 32 tests nominatifs)
├── documentation/           (audit, corrections, README origine, sauvegardes)
├── rapports/                (manifeste, tests V6, scellés, intégrité, livraison)
└── archives/                (source_v5 + reference_32_tests, SHA256 vérifiés)
```

## Lancer les 32 tests
```bash
cd ~/HUMANITY_AI_SHIELD_V6_RECONSTRUCTION/package
cp -a ../tests ./tests
python -m unittest discover -s tests -v 2>&1 | grep -E "^Ran|^OK|^FAILED"
rm -rf ./tests
```
Attendu : `Ran 32 tests in X.XXXs` puis `OK`.

## Limites assumées
Prototype défensif, pas une garantie de sécurité absolue. Contrôles
techniques réels et vérifiables, pas une protection totale.

## Version active
`~/HUMANITY_AI_SHIELD/AI_RISK_MONITOR_V5/` (scellée 2026-11-05 13:31:55).
V6 est le livrable de reconstruction, prêt pour revue et déploiement futur.

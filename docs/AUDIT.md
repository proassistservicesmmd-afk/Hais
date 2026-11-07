# Audit d'intégrité HAIS V7.0

## Branche de référence

⚠️ **L'audit se fait sur la branche `principal`, PAS sur `main`.**

- `main` : branche de travail / CI (historique antérieur, sans matériel cryptographique)
- `principal` : branche d'audit contenant :
  - le manifeste `SHA256SUMS_V7_0_20261107_FINAL.txt` + sa signature `.asc`
  - la clé publique `docs/hais-public-key.asc`
  - le tag signé `v7.0.0-integrity`

## Clé publique HAIS V7.0

| Champ | Valeur |
|---|---|
| Empreinte | `A28E7A57BF634B97BECE52E78EAF2022D02E321F` |
| Type | RSA 4096 (clé principale SC + sous-clé E) |
| Créée | 2026-11-07 |
| Expire | 2028-11-06 |
| UID | `HAIS Project (Reference signing key V7.0) <hais@local>` |
| Sous-clé | `A89F923D043679E61C9F073BDD48186D05D78FDF` |

### Canaux de publication

- **Dans le dépôt** : `docs/hais-public-key.asc` (source de vérité)
- **keyserver.ubuntu.com** : UID complet conservé ✅
  ```bash
  gpg --keyserver keyserver.ubuntu.com --recv-keys A28E7A57BF634B97BECE52E78EAF2022D02E321F
  ```

- **keys.openpgp.org** : clé présente mais UID retiré (email `hais@local` non délivrable)

### Vérification de l'empreinte

    gpg --fingerprint A28E7A57BF634B97BECE52E78EAF2022D02E321F
    # doit afficher : A28E 7A57 BF63 4B97 BECE  52E7 8EAF 2022 D02E 321F

## Procédure de vérification complète

    git clone https://github.com/proassistservicesmmd-afk/Hais.git
    cd Hais
    git checkout principal
    git verify-tag v7.0.0-integrity
    gpg --fingerprint A28E7A57BF634B97BECE52E78EAF2022D02E321F
    gpg --verify SHA256SUMS_V7_0_20261107_FINAL.txt.asc SHA256SUMS_V7_0_20261107_FINAL.txt
    sha256sum -c SHA256SUMS_V7_0_20261107_FINAL.txt

## Commit cible du tag

    d0033fb01772bf6e84d28a966eeee0e334e56cf9

## Journaux d'exécution

Les fichiers `package/logs/*.jsonl` sont des artefacts d'exécution, pas du code source.
Ils sont exclus du scellé SHA256 (`_scan()` dans `verifier.sh`) et retirés du dépôt git.

## Validité de la clé

La clé principale expire le 2028-11-06. Avant cette date :

    gpg --edit-key A28E7A57BF634B97BECE52E78EAF2022D02E321F
    # gpg> expire
    # gpg> save

Puis republier sur les keyservers.

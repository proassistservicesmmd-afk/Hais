#!/data/data/com.termux/files/usr/bin/bash
# Test de non-régression du vérificateur lui-même.
# Vérifie que _scan exclut .git/, que le scellé est cohérent, et que
# ./verifier.sh sort en 0.
set -eu
cd "$(dirname "$0")/.."
assert_eq() { [ "$1" = "$2" ] || { echo "FAIL: $3 ($1 != $2)"; exit 1; }; }

# 1. _scan exclut .git/
GIT_COUNT=$(_scan 2>/dev/null | grep -c '/\.git/' || true)
assert_eq "$GIT_COUNT" "0" "aucun .git dans _scan"

# 2. Le scellé exclut .git/
SEAL_GIT=$(grep -c '/\.git/' SHA256SUMS_V7_0_*.txt || true)
assert_eq "$SEAL_GIT" "0" "aucun .git dans scellé"

# 3. Le scellé contient verifier.sh
SEAL_VE=$(grep -c 'verifier.sh$' SHA256SUMS_V7_0_*.txt || true)
assert_eq "$SEAL_VE" "1" "verifier.sh scellé"

# 4. ./verifier.sh sort en 0
./verifier.sh >/dev/null 2>&1 || { echo "FAIL: verifier.sh exit≠0"; exit 1; }
echo "✅ verifier.sh : non-régression OK"

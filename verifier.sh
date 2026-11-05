#!/data/data/com.termux/files/usr/bin/bash
# Vérifie l'intégrité et les 41 tests de V6.2
set -euo pipefail
V6="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="$V6/rapports/verifications_${STAMP}.txt"

exec > >(tee "$LOG") 2>&1

echo "===== VÉRIFICATION V6.2 — $STAMP ====="
echo

SCELLE=$(ls -t "$V6"/SHA256SUMS_V6_2_*.txt 2>/dev/null | head -1)
if [ -z "$SCELLE" ]; then
  echo "[ERREUR] Aucun scellé V6.2 trouvé"
  exit 1
fi
echo "Scellé de référence : $(basename "$SCELLE")"

( cd "$V6" && find . -type f \
    ! -path './archives/*' \
    ! -path './rapports/.trace_*' \
    ! -path './rapports/PROMOTION_*' \
    ! -path './rapports/CONSTRUCTION_*' \
    ! -path './rapports/verifications_*' \
    ! -path "./$(basename "$SCELLE")" \
    ! -name 'SIGNATURE_*' \
    -exec sha256sum {} \; | sort ) | cmp -s - "$SCELLE" \
  && echo "[OK] Intégrité V6.2" || echo "[ALERTE] Modifications détectées"
echo

echo "=== 41 tests ==="
TMP=$(mktemp -d "$HOME/.hais_verify_XXXXXX")
cp -a "$V6/package/." "$TMP/"
cp -a "$V6/tests/." "$TMP/tests/"
( cd "$TMP" && python -m unittest discover -s tests 2>&1 | grep -E '^Ran|^OK|^FAILED' )
rm -rf "$TMP"
echo

echo "===== FIN ====="

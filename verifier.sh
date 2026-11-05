#!/data/data/com.termux/files/usr/bin/bash
# Vérifie l'intégrité SHA256 et les tests unitaires — V7.0
set -uo pipefail

V7="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="$V7/rapports/verifications_${STAMP}.txt"
mkdir -p "$V7/rapports"

CALC="$(mktemp -t hais_scelle.XXXXXX)"
trap 'rm -f "$CALC"' EXIT

# ---------------------------------------------------------------------------
# _scan : LA seule définition du scan. Utilisée pour vérifier ET pour reseed.
# ---------------------------------------------------------------------------
_scan() {
    find . -type f \
        -not -path './.git/*' \
        -not -path './archives/*' \
        -not -path './rapports/*' \
        -not -path './package/logs/*' \
        -not -path '*/__pycache__/*' \
        -not -path '*/.pytest_cache/*' \
        -not -name '*.pyc' \
        -not -name 'SHA256SUMS*' \
        -not -name 'SIGNATURE_*' \
        -not -name '*.bak*' \
        -not -name '*.CASSE*' \
        -print0 | sort -z | xargs -0 sha256sum
}

# ---------------------------------------------------------------------------
# Mode --reseed
# ---------------------------------------------------------------------------
if [ "${1:-}" = "--reseed" ]; then
    cd "$V7" || exit 1
    NEW="SHA256SUMS_V7_0_${STAMP}.txt"
    _scan > "$NEW"
    echo "[RESEED] Écrit $NEW ($(wc -l < "$NEW") fichiers)"
    exit 0
fi

# ---------------------------------------------------------------------------
# Mode normal
# ---------------------------------------------------------------------------
exec > >(tee "$LOG") 2>&1

echo "===== VÉRIFICATION V7.0 — $STAMP ====="
echo "DEBUG V7=$V7"

SCELLE=$(find "$V7" -maxdepth 1 -type f -name 'SHA256SUMS_V7_0_*.txt' -print 2>/dev/null | sort -r | head -1)
echo "DEBUG SCELLE=$SCELLE"
if [ -z "$SCELLE" ]; then
    echo "[ERREUR] Aucun scellé V7.0 dans : $V7"
    exit 1
fi
echo "Scellé de référence : $(basename "$SCELLE")"
echo

echo "=== Intégrité SHA256 ==="
( cd "$V7" && _scan ) > "$CALC"

if cmp -s "$CALC" "$SCELLE"; then
    echo "[OK] Intégrité V7.0"
else
    echo "[ALERTE] Modifications détectées :"
    diff "$CALC" "$SCELLE" | head -40
fi
echo

echo "=== Tests unitaires ==="
TMP=$(mktemp -d "$HOME/.hais_verify_XXXXXX")
cp -a "$V7/." "$TMP/" 2>/dev/null
(
    cd "$TMP" || exit 1
    python3 -m unittest discover -s tests -p 'test_*.py' 2>&1 | tail -15
)
RC=$?
rm -rf "$TMP"
echo
echo "===== FIN ====="
exit $RC

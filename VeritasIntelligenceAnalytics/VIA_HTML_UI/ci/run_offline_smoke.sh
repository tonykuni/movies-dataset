#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
OUT="${OFFLINE_OUT:-/tmp/via-offline-smoke}"
ZIP_PATH="${2:-}"
CHECKSUM_PATH="${3:-}"

rm -rf "$OUT"
mkdir -p "$OUT"
python3 "$ROOT/skills/via-e2e-zip-verifier/scripts/validate_standardized_package.py"   "$ROOT" --run-e2e --out-dir "$OUT/package" --json "$OUT/package.json"

if [[ -n "$ZIP_PATH" ]]; then
  ZIP_ARGS=("$ZIP_PATH" --run-extracted-e2e --out-dir "$OUT/zip" --json "$OUT/zip.json")
  if [[ -n "$CHECKSUM_PATH" ]]; then
    ZIP_ARGS+=(--checksum-file "$CHECKSUM_PATH")
  fi
  python3 "$ROOT/skills/via-e2e-zip-verifier/scripts/validate_standardized_zip.py" "${ZIP_ARGS[@]}"
fi

printf 'VIA offline smoke test completed: %s\n' "$OUT"

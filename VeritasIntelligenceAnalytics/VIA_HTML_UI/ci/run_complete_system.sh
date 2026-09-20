#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
OUT="${SYSTEM_OUT:-/tmp/via-complete-system}"
ZIP_PATH="${2:-}"
CHECKSUM_PATH="${3:-}"
STREAMLIT_URL="${STREAMLIT_URL:-}"
STREAMLIT_PORT="${STREAMLIT_PORT:-8510}"

rm -rf "$OUT"
mkdir -p "$OUT"

python3 "$ROOT/skills/via-e2e-zip-verifier/scripts/validate_standardized_package.py" \
  "$ROOT" --run-e2e --out-dir "$OUT/canonical" --json "$OUT/canonical.json"

python3 "$ROOT/e2e/test_via_cross_page_sync.py" \
  --ui "$ROOT/ui/VIA-UI-Standalone-NoServer.html" \
  --synchronizer "$ROOT/ui/VIA-SYNCHRONIZER-Standalone.html" \
  --out "$OUT/cross-page/report.json"

python3 "$ROOT/e2e/test_complete_system.py" \
  --launcher "$ROOT/ui/VIA-Complete-System.html" \
  --out "$OUT/launcher/report.json"

if [[ -n "$STREAMLIT_URL" ]]; then
  python3 "$ROOT/e2e/test_streamlit_companion.py" \
    --url "$STREAMLIT_URL" \
    --out "$OUT/streamlit/report.json"
elif [[ "${RUN_STREAMLIT:-0}" == "1" ]] && command -v streamlit >/dev/null 2>&1 && python3 -c 'import streamlit' >/dev/null 2>&1; then
  streamlit run "$ROOT/docs/references/streamlit_companion/app.py" \
    --server.address 127.0.0.1 --server.port "$STREAMLIT_PORT" \
    --server.headless true --browser.gatherUsageStats false >"$OUT/streamlit.log" 2>&1 &
  STREAMLIT_PID=$!
  trap 'kill "$STREAMLIT_PID" 2>/dev/null || true' EXIT
  for _ in $(seq 1 30); do
    if curl -fsS "http://127.0.0.1:${STREAMLIT_PORT}/_stcore/health" | grep -q ok; then break; fi
    sleep 0.5
  done
  curl -fsS "http://127.0.0.1:${STREAMLIT_PORT}/_stcore/health" | grep -q ok
  python3 "$ROOT/e2e/test_streamlit_companion.py" \
    --url "http://127.0.0.1:${STREAMLIT_PORT}" \
    --out "$OUT/streamlit/report.json"
else
  printf '{"status":"SKIP","reason":"optional Streamlit runtime not enabled"}\n' > "$OUT/streamlit.json"
fi

if [[ -n "$ZIP_PATH" ]]; then
  ZIP_ARGS=("$ZIP_PATH" --run-extracted-e2e --out-dir "$OUT/zip" --json "$OUT/zip.json")
  if [[ -n "$CHECKSUM_PATH" ]]; then ZIP_ARGS+=(--checksum-file "$CHECKSUM_PATH"); fi
  python3 "$ROOT/skills/via-e2e-zip-verifier/scripts/validate_standardized_zip.py" "${ZIP_ARGS[@]}"
fi

python3 "$ROOT/e2e/aggregate_system_report.py" --root "$ROOT" --out "$OUT/system-report.json"
cat "$OUT/system-report.json"
printf 'VIA complete system test completed: %s\n' "$OUT"

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${STREAMLIT_PORT:-8501}"
ADDRESS="${STREAMLIT_ADDRESS:-127.0.0.1}"

if ! command -v streamlit >/dev/null 2>&1; then
  echo "streamlit is not installed in the current Python environment." >&2
  echo "Offline setup: install requirements-optional.txt on a prepared build host, then bring the environment into this host." >&2
  exit 2
fi

exec streamlit run "$ROOT/app.py" \
  --server.address "$ADDRESS" \
  --server.port "$PORT" \
  --server.headless true \
  --browser.gatherUsageStats false

#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
ZIP_NAME="${1:-via_quantguard_quant_engine_20260916.zip}"

./scripts/verify_engine.sh
PYTHONPATH=. pytest -q --strict-markers tests/test_replay.py -m anti_lookahead
python3 -m compileall -q quant_engine tests examples scripts

rm -f "$ZIP_NAME"
rm -rf .pytest_cache quant_engine/__pycache__ tests/__pycache__ examples/__pycache__ scripts/__pycache__ build dist
find . -maxdepth 1 -type d -name '*.egg-info' -prune -exec rm -rf {} +
zip -qr "$ZIP_NAME" . \
  -x "./$ZIP_NAME" \
     "./.git/*" \
     "./.pytest_cache/*" \
     "./build/*" \
     "./dist/*" \
     "*/**/*.egg-info/*" \
     "./*.egg-info/*" \
     "*/__pycache__/*" \
     "*.pyc" \
     "./example_output/*"

unzip -tq "$ZIP_NAME"
printf 'package=%s\n' "$ROOT/$ZIP_NAME"

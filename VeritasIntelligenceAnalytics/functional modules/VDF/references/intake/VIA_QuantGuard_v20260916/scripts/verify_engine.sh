#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"
python3 -m pytest -q --strict-markers
python3 -m pytest -q --strict-markers tests/test_quantguard_regression.py -m regression
python3 -m compileall -q quant_engine tests scripts
python3 scripts/export_ssot.py >/dev/null
python3 -m json.tool ssot/quant_engine_ssot.json >/dev/null
printf 'verified: tests, compileall, and SSOT JSON\n'

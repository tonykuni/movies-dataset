#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NLP tail. It starts only from VCGC, then calls v0103. The older body is not rewritten."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "SUP_MDL866_VIAUnifiedNLPOrchestrator_v0103.py"


def _load():
    spec = importlib.util.spec_from_file_location("nlp_v0103_for_v0104", PRIOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules["nlp_v0103_for_v0104"] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    return _load().main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    ok = denied and PRIOR.is_file() and "VIA_FROM_VCGC" in Path(__file__).read_text(encoding="utf-8")
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

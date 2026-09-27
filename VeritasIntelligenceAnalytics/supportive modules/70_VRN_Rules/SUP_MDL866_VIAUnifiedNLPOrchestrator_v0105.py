#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NLP tail. --brief stays on the newest file and is parsed by v0103.

v0104 still owns the VCGC gate. This file does not download a model.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "SUP_MDL866_VIAUnifiedNLPOrchestrator_v0104.py"


def _load():
    spec = importlib.util.spec_from_file_location("nlp_v0104_for_v0105", PRIOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules["nlp_v0104_for_v0105"] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    argv = ["--brief" if item in {"-Brief", "--brief"} else item for item in sys.argv[1:]]
    sys.argv = [sys.argv[0], *argv]
    return _load().main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    text = Path(__file__).read_text(encoding="utf-8")
    ok = denied and "--brief" in text and PRIOR.is_file()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

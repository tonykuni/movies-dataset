#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN manager tail. The logic rollup is a verb, not a second copy of the rules.

v0108 still owns read(), collect(), and the old main. This file forwards
those. `logic` runs VRN_ENG113 and prints its card. It does not rewrite the
logic book and it does not read a PDF.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "VRN_SystemManager_v0108.py"
ROLLUP = HERE / "VRN_ENG113_LogicRollup_v0100.py"
_prior = None


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _facade():
    global _prior
    if _prior is None:
        _prior = _load(PRIOR, "vrn_v0108_for_v0109")
    return _prior


def logic_rollup() -> dict:
    return _load(ROLLUP, "vrn_logic_rollup_v0100").check()


def read(domain: str, key: str | None = None, full: bool = False) -> dict:
    return _facade().read(domain, key, full)


def collect() -> dict:
    return _facade().collect()


def __getattr__(name: str):
    return getattr(_facade(), name)


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    if "logic" in sys.argv:
        import json
        card = logic_rollup()
        print(json.dumps(card, ensure_ascii=False, indent=1))
        return 0 if card.get("lock_success") else 2
    return _facade().main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = logic_rollup()
    ok = (
        denied
        and PRIOR.is_file()
        and ROLLUP.is_file()
        and card.get("door") == "VRN_ENG113_LogicRollup_v0100"
        and card.get("rules_copied") is False
        and card.get("book_edited") is False
    )
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

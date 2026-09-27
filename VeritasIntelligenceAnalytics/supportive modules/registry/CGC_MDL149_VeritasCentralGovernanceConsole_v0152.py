#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Policy tail. A related command keeps its TA-Lib words. The ban is added beside them.

The locked book is not rewritten. The older amendment stays.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0151.py"
NOTE = HERE / "VIA_Policy_TalibBan_v0101.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prev = _load(PREVIOUS, "vcgc_v0151_for_v0152")
body = prev.body
_policy = body.policy_step


def policy_step() -> int:
    rc = _policy()
    note = json.loads(NOTE.read_text(encoding="utf-8"))
    print("[政策] L50 不刪字 · 禁令加在旁邊 · 正本未改")
    return rc or (0 if note.get("book_edited") is False and note.get("strip_the_words") is False else 2)


body.policy_step = policy_step


def __getattr__(name: str):
    return getattr(prev, name)


def main(argv=None):
    return prev.main(argv)


def selftest() -> int:
    note = json.loads(NOTE.read_text(encoding="utf-8"))
    ok = (
        note["id"] == "L50"
        and note["book_edited"] is False
        and note["strip_the_words"] is False
        and note["rank"] == 2
    )
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

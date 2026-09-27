#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Outside tail. `support` names the NLP and Layout routes. Older commands stay on v0152.

This file does not run a PDF, rewrite the policy book, or delete an engine.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0152.py"
DOOR = HERE / "CGC_MDL216_NlpLayoutDoor_v0100.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prev = _load(PREVIOUS, "vcgc_v0152_for_v0153")


def __getattr__(name: str):
    return getattr(prev, name)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["support"]:
        return _load(DOOR, "vcgc_nlp_layout_door").main()
    return prev.main(argv)


def selftest() -> int:
    door = _load(DOOR, "vcgc_nlp_layout_door_self")
    return door.selftest()


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

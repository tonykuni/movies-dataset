#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Console tail. `books` names the locked policy, logic, and parameter books.

`matrix`, `support`, and older verbs stay on v0154. No book is rewritten.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0154.py"
BOOKS = HERE / "CGC_MDL218_BookPointer_v0100.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prev = _load(PREVIOUS, "vcgc_v0154_for_v0155")


def __getattr__(name: str):
    return getattr(prev, name)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["books"]:
        return _load(BOOKS, "book_pointer_for_console").main()
    return prev.main(argv)


def selftest() -> int:
    return _load(BOOKS, "book_pointer_console_self").selftest()


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

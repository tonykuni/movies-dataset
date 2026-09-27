#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layout tail. CRLF in a locked source is not a new engine.

v0104 stops with LOCK_MISMATCH before review. On this tree the bytes of
VRN_ENG112_FinancialRead_v0100.py and VRN_ENG110_TabReport_v0114.py match
the locked LF hash after the carriage returns are removed. This tail
accepts that newline only. A real byte change is still named and refused.
The lock book and the older hubs are not rewritten.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "SUP_MDL743_GenericLayoutHub_v0107.py"
BODY = HERE / "SUP_MDL743_GenericLayoutHub_v0104.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _prior():
    return _load(PRIOR, "layout_v0107_for_v0108")


def _body():
    return _load(BODY, "layout_v0104_for_v0108")


def _lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _accept_newline(locked: dict, via: Path) -> list[str]:
    real = []
    for rel, row in locked.items():
        if row.get("state") == "UNCHANGED":
            continue
        path = via / rel
        if path.is_file() and _lf(path) == row.get("expected"):
            row["actual"] = row["expected"]
            row["state"] = "UNCHANGED"
            row["newline"] = "CRLF"
        else:
            real.append(rel)
    return real


def __getattr__(name: str):
    return getattr(_prior(), name)


def def_run_batch(source, output_root, evidence=None):
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        raise RuntimeError("DENY")
    body = _body()
    bridge = body._previous
    original = bridge.def_locked_sources

    def wrapped(policy):
        locked = original(policy)
        real = _accept_newline(locked, body.VIA)
        if real:
            raise RuntimeError("LOCK_MISMATCH " + " | ".join(real))
        return locked

    bridge.def_locked_sources = wrapped
    try:
        return body.def_run_batch(source, output_root, evidence)
    finally:
        bridge.def_locked_sources = original


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    return _prior().main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    via = HERE.parents[1]
    policy = json.loads((via / "supportive modules/registry/VIA_Layout_Reuse_SSOT_v0100.json").read_text(encoding="utf-8-sig"))
    locked = {}
    for rel, expected in policy["locked_sources"].items():
        path = via / rel
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "ABSENT"
        locked[rel] = {"expected": expected, "actual": actual, "state": "UNCHANGED" if actual == expected else "MISMATCH"}
    raw = [rel for rel, row in locked.items() if row.get("state") != "UNCHANGED"]
    real = _accept_newline(locked, via)
    ok = denied and not real and all(row.get("state") == "UNCHANGED" for row in locked.values())
    if raw:
        ok = ok and all(locked[rel].get("newline") == "CRLF" for rel in raw)
    print("  [OK]" if ok else "  [FAIL]", "newline", ",".join(raw), "real", ",".join(real))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

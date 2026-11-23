#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent VDF system entry.

Runs the isolated pieces as one system: startup, input matrix, key door,
sentiment store, macro verdicts, system monitor, lesson ledger, and the
read-only VQG indicator plus VAP engine bridge. It does not load the old
manager chain and it does not set a consent flag.

  py -3 VDF_MDL031_IndependentSystem_v0100.py selftest
  py -3 VDF_MDL031_IndependentSystem_v0100.py run
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VER = "v0100"
PARTS = (
    ("start", "VDF_MDL024_IsolatedStart_v0102.py", ("selftest",)),
    ("matrix", "VDF_MDL026_InputApiMatrix_v0101.py", ("selftest",)),
    ("keydoor", "VDF_MDL027_FredKeyDoor_v0100.py", ("selftest",)),
    ("sentiment", "VDF_MDL028_SentimentStore_v0100.py", ("selftest",)),
    ("verdict", "VDF_MDL016_MacroCrossCheck_v0100.py", ("--selftest",)),
    ("monitor", "VDF_MDL029_SystemManager_v0101.py", ("selftest",)),
    ("ledger", "VDF_MDL030_LessonLedger_v0101.py", ("selftest",)),
    ("vqg-vap", "VDF_MDL032_VqgVapBridge_v0100.py", ("selftest",)),
)


def _load(name: str):
    path = HERE / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_part(label: str, filename: str, args: tuple) -> int:
    path = HERE / filename
    if not path.is_file():
        print("[FAIL] missing", filename)
        return 1
    proc = subprocess.run([sys.executable, str(path), *args], cwd=str(HERE))
    print("%s rc=%s" % (label, proc.returncode))
    return proc.returncode


def selftest() -> int:
    failed = []
    for label, filename, args in PARTS:
        if _run_part(label, filename, args) != 0:
            failed.append(label)
    if failed:
        print("[FAIL] independent system", ", ".join(failed))
        return 1
    print("[OK] VDF independent system %s parts=%d" % (VER, len(PARTS)))
    return 0


def run() -> int:
    rc = selftest()
    if rc != 0:
        return rc
    monitor = _load("VDF_MDL029_SystemManager_v0101.py")
    ledger = _load("VDF_MDL030_LessonLedger_v0101.py")
    book = monitor.build()
    monitor.monitor(book)
    ledger.compile_lessons()
    peers = ledger.export_peers()
    print("state=%s lamp=%s coded=%d" % (book["state"], book["lamp"], len(book["coded_parameters"])))
    print("graphify=%s" % peers["graphify"])
    return 0 if book["state"] == "REGISTERED" else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "selftest"
    if cmd == "selftest":
        return selftest()
    if cmd == "run":
        return run()
    print("verbs: selftest | run")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF isolated start v0101. Same scan as v0100. A duplicate number that the matrix has split is not a yellow lamp.

  py -3 VDF_MDL024_IsolatedStart_v0101.py start
"""
from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

TAG = "VDF-ISO"
VER = "v0101"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prior():
    return _load("vdf_iso_v0100", Path(__file__).with_name("VDF_MDL024_IsolatedStart_v0100.py"))


def matrix():
    path = Path(__file__).with_name("VDF_MDL026_InputApiMatrix_v0100.py")
    if not path.is_file():
        return None
    return _load("vdf_matrix_v0100", path)


def uncovered(info: dict, mod) -> dict:
    if mod is None:
        return info["dups"]
    known = {row["file"] for row in mod.families()}
    return {key: names for key, names in info["dups"].items() if not set(names) <= known}


def start() -> int:
    iso = prior()
    begun = time.perf_counter()
    info = iso.card(iso.vdf_dir())
    mod = matrix()
    left = uncovered(info, mod)
    bad = [row for row in info["gap"] if not row["syntax"] or not row["accel"] or row["net"] == "gap"]
    lamp = "RED" if any(not row["syntax"] for row in bad) else ("YELLOW" if bad or left else "GREEN")
    ms = int((time.perf_counter() - begun) * 1000)
    split = 0 if mod is None else len({row["old"] for row in mod.families() if sum(1 for other in mod.families() if other["old"] == row["old"]) > 1})
    print("%s %s" % (TAG, VER), flush=True)
    print("tails=%d accel=%d/%d" % (info["tails"], info["accel"], info["tails"]), flush=True)
    print("net=%d bridge / %d offline / %d gap" % (
        info["bridge"], info["offline"], sum(1 for row in info["gap"] if row["net"] == "gap")), flush=True)
    print("split=%d lamp=%s ms=%d" % (split, lamp, ms), flush=True)
    for key, names in sorted(left.items()):
        print("dup %s %s" % (key, " ".join(names)), flush=True)
    for row in bad:
        print("gap %s %s" % (row["id"], row["file"]), flush=True)
    if mod is not None:
        print(mod.render(), flush=True)
    return 0 if lamp != "RED" else 1


def selftest() -> int:
    iso = prior()
    if iso.selftest() != 0:
        return 1
    mod = matrix()
    info = {"dups": {"VDF-ENG110": ["VDF_ENG110_AKShareProbe_v0103.py", "VDF_ENG110_USMacroProbe_v0102.py", "VDF_ENG110_USMacroTree_v0100.py"]}, "gap": []}
    if uncovered(info, mod):
        print("[FAIL] mapped dup still open")
        return 1
    info["dups"]["VDF-ENG999"] = ["nope.py"]
    if "VDF-ENG999" not in uncovered(info, mod):
        print("[FAIL] unknown dup hidden")
        return 1
    print("[OK] mapped number collisions are not a yellow lamp")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "start"
    if cmd == "selftest":
        return selftest()
    if cmd != "start":
        print("verbs: start selftest", flush=True)
        return 2
    return start()


if __name__ == "__main__":
    raise SystemExit(main())

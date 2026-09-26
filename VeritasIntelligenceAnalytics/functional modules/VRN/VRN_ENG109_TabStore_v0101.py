#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Same tab store. The engine tree and the database root may be the same path or two paths."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior():
    spec = importlib.util.spec_from_file_location("tab_v0100", HERE / "VRN_ENG109_TabStore_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def place() -> dict:
    prior = _prior()
    engine = HERE
    data = prior.choose_root()
    cloud = prior.cloud_of(data)
    try:
        same = data.resolve().is_relative_to(engine.resolve().parents[1])
    except Exception:
        same = False
    return {
        "engine": str(engine),
        "data": str(data),
        "same": same,
        "cloud": cloud,
        "off_pc": cloud != "local",
    }


def run() -> dict:
    prior = _prior()
    where = place()
    link = prior.probe(Path(where["data"]))
    card = prior.run()
    card["door"] = "VRN_ENG109_TabStore_v0101"
    card["engine"] = where["engine"]
    card["data"] = where["data"]
    card["same"] = where["same"]
    card["cloud"] = link["cloud"]
    card["linked"] = link["linked"]
    card["off_pc"] = where["off_pc"]
    card["off_pc_means"] = "the last synced cloud copy, not the powered-off computer"
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    print(json.dumps(run(), ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    prior = _prior()
    own = place()
    os.environ["VIA_VRN_DATA"] = r"C:\Users\tonyk\OneDrive\VIA-DATA"
    split = place()
    os.environ["VIA_VRN_DATA"] = r"C:\temp\via-local"
    plain = place()
    os.environ.pop("VIA_VRN_DATA", None)
    rejected = prior.store({"basic": {}, "page1": {}, "financial": []}, Path("/tmp/vrn_tab_v0101"))
    ok = (
        own["same"] is True
        and split["same"] is False
        and split["cloud"] == "onedrive"
        and split["off_pc"] is True
        and plain["cloud"] == "local"
        and plain["off_pc"] is False
        and rejected["written"] == 0
    )
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

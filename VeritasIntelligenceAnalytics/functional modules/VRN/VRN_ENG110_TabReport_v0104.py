#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Same report. The card names the interpreter and whether PyMuPDF imports."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior():
    spec = importlib.util.spec_from_file_location("tab_report_v0103", HERE / "VRN_ENG110_TabReport_v0103.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fitz() -> str:
    try:
        import fitz
        return getattr(fitz, "__version__", "") or "yes"
    except Exception as exc:
        return type(exc).__name__


def run(folder: Path, data_root: Path, open_page: bool) -> dict:
    card = _prior().run(folder, data_root, open_page)
    card["door"] = "VRN_ENG110_TabReport_v0104"
    card["python"] = sys.executable
    card["fitz"] = _fitz()
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    prior = _prior()
    folder = Path(os.environ.get("VIA_VRN_SAMPLES", str(prior.DEFAULT_DIR)))
    data = Path(os.environ["VIA_VRN_DATA"]) if os.environ.get("VIA_VRN_DATA") else HERE / "output_hub" / "vrn"
    card = run(folder, data, True)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["present"] else 2


def selftest() -> int:
    folder = Path("/tmp/vrn_v0104")
    folder.mkdir(parents=True, exist_ok=True)
    card = run(folder, Path("/tmp/vrn_v0104_out"), False)
    ok = card["python"] == sys.executable and card["fitz"] not in {"", "ModuleNotFoundError"} and card["written"] == 0
    print("  [OK]" if ok else "  [FAIL] " + card["fitz"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

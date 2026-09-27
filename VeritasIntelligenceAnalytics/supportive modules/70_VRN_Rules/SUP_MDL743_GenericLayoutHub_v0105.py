#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layout tail. The measured engine stays v0104. This file only points OCR at an existing tessdata folder.

What a later UI should show
    entry    via-vcgc layout
    body     SUP_MDL743_GenericLayoutHub_v0104.py
    prior    v0100 stays mounted. v0101 stays the bridge. Neither file is deleted.
    text     native text and FINANCIAL DATA stay on the v0104 path
    ocr      chi_tra is used only when chi_tra, chi_sim, and eng traineddata
             are in the same folder. The folder is TESSDATA_PREFIX, or
             C:\\Users\\tonyk\\OneDrive\\Desktop\\VRN\\tessdata_best.
    missing  if that folder is absent, OCR stays UNAVAILABLE. The text extract
             is not marked failed.

Rules
    Do not download a language pack from this file. Do not write the financial
    database. Do not overwrite the central component inventory.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BODY = HERE / "SUP_MDL743_GenericLayoutHub_v0104.py"
PACK = ("chi_tra.traineddata", "chi_sim.traineddata", "eng.traineddata")
_body = None


def _load():
    global _body
    if _body is None:
        spec = importlib.util.spec_from_file_location(BODY.stem, BODY)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _point(mod)
        _body = mod
    return _body


def _folder() -> str:
    names = []
    for key in ("TESSDATA_PREFIX", "VIA_TESSDATA"):
        if os.environ.get(key):
            names.append(Path(os.environ[key]))
    names.append(Path(r"C:\Users\tonyk\OneDrive\Desktop\VRN\tessdata_best"))
    for folder in names:
        direct = folder if (folder / PACK[0]).is_file() else folder / "tessdata"
        if all((direct / name).is_file() for name in PACK):
            os.environ["TESSDATA_PREFIX"] = str(direct.parent if direct.name == "tessdata" else direct)
            return str(direct)
    return ""


def _point(mod) -> None:
    figures = mod.STAGES["figures"]
    original = figures.def_ocr_status

    def def_ocr_status():
        found = _folder()
        status = dict(original())
        status["tessdata"] = found
        if status.get("state") != "AVAILABLE" and not found:
            status["fill"] = "chi_tra stays unavailable until tessdata_best has chi_tra, chi_sim, and eng"
        return status

    figures.def_ocr_status = def_ocr_status


def __getattr__(name: str):
    return getattr(_load(), name)


def selftest() -> int:
    text = BODY.read_text(encoding="utf-8")
    ok = BODY.is_file() and "v0104" in text and "def_run_batch" in text
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else __import__("sys").exit(_load().main()))

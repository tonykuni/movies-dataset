#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layout tail. pdfminer font warnings are not review errors.

v0108 still owns the newline lock. This tail only lowers the pdfminer log
before that review runs. A missing font box does not stop the file, and it
no longer fills the console. This file does not write the financial database.
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import importlib.util
import json
import logging
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "SUP_MDL743_GenericLayoutHub_v0108.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _quiet() -> None:
    logging.getLogger("pdfminer").setLevel(logging.ERROR)


def __getattr__(name: str):
    return getattr(_load(PRIOR, "layout_v0108_for_v0109"), name)


def def_run_batch(source, output_root, evidence=None):
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        raise RuntimeError("DENY")
    _quiet()
    return _load(PRIOR, "layout_run_v0108").def_run_batch(source, output_root, evidence)


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    return _load(PRIOR, "layout_main_v0108").main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = False
    try:
        def_run_batch(Path("."), Path("."))
    except RuntimeError as exc:
        denied = str(exc) == "DENY"
    os.environ["VIA_FROM_VCGC"] = "YES"
    _quiet()
    held = logging.getLogger("pdfminer").level >= logging.ERROR
    log = logging.getLogger("pdfminer")
    log.warning("Could not get FontBBox from font descriptor because None cannot be parsed as 4 floats")
    ok = denied and held and PRIOR.is_file()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

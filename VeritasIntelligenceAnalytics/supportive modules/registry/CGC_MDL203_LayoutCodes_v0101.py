#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layout code lock. A checker named Talib is not the TA-Lib package.

v0100 treated any new key containing the letters talib as a package install.
That stopped SyncAll before the policy doors. This door keeps the same layout
count and only rejects a real package key or an installed module.
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
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = HERE / "VIA_Component_Inventory_SSOT_v0100.json"
RUNTIME = ("fitz", "pdfplumber", "pdfminer", "PIL", "pandas", "numpy")


def _present(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def _package(key: str) -> bool:
    text = key.lower()
    if "talibban" in text or "talibpolicy" in text:
        return False
    return text.endswith("|talib") or "/talib" in text


def check() -> dict:
    data = json.loads(BOOK.read_text(encoding="utf-8")) if BOOK.is_file() else {}
    records = data.get("records") or []
    features = [r for r in records if str(r.get("identity") or "").startswith("layout/LAYOUT.") and r.get("state") == "ACTIVE"]
    codes = sorted(r.get("code") or "" for r in features)
    package = [r.get("key") for r in records if _package(str(r.get("key") or "")) and str(r.get("first_seen") or "").startswith("2026-09-27")]
    libs = {name: _present(name) for name in RUNTIME}
    installed = _present("talib")
    missing = []
    if len(features) != 46:
        missing.append("layout features")
    if package:
        missing.append("package")
    if not all(libs.values()):
        missing.append("runtime")
    if installed:
        missing.append("installed")
    return {
        "via": "vcgc",
        "door": "CGC_MDL203_LayoutCodes_v0101",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": not missing,
        "features": len(features),
        "code_first": codes[0] if codes else "",
        "code_last": codes[-1] if codes else "",
        "writer": "registry-sync --layout-only --apply",
        "talib": "package absent; checker names are not the package",
        "runtime": libs,
        "missing": missing,
        "prior": "CGC_MDL203_LayoutCodes_v0100.py",
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "pip install TA-Lib",
            "import talib",
            "treat the ban checker name as an install",
            "registry-sync --apply without --layout-only",
            "edit intake macro_ssot",
        ],
        "next": "none" if not missing else "do not unlock; name the drift",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    card = check()
    print("  [OK]" if card["lock_success"] else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if card["lock_success"] else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

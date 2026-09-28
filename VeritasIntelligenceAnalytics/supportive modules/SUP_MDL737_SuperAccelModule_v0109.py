#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SUP_MDL737_SuperAccelModule_v0109 — accelerator loader picks the newest versioned body.

v0108 wrote one body file name (the v1141 one) into CEL_CANDIDATES.
A newer body would never be loaded, and the pinned name is a PINVER.
This tail sets CEL_CANDIDATES from _cel_versioned(), which v0106 already carries:
every VeritasCeleritas_v*.py next to this file, newest first, and a body that names
talib is not a candidate (L50). Nothing else changes. Nothing is fetched or installed.
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "SUP_MDL737_SuperAccelModule"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _prior() -> Path:
    mine = _vnum(Path(__file__))
    older = [p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < mine]
    if not older:
        raise ImportError(f"{STEM}: no version below v{mine:04d}")
    return max(older, key=_vnum)


PRIOR = _prior()
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_v{_vnum(Path(__file__)):04d}", PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)

def _cel_versioned() -> tuple:
    """Same rule as v0106 _cel_versioned: newest first, a body that names talib is out.
    Scans bytes (bytes.lower) instead of decoded text: every VIA process runs this through
    the bootstrap, and the decoded scan of an 8,600-line body cost ~9 ms per start."""
    scored = []
    for path in HERE.glob("VeritasCeleritas_v*.py"):
        digits = path.stem.rsplit("_v", 1)[-1]
        if not digits.isdigit():
            continue
        try:
            data = path.read_bytes()
        except OSError:
            data = b"talib"         # unreadable body is not a candidate
        if b"talib" in data.lower():
            continue
        scored.append((int(digits), path.name))
    return tuple(name for _, name in sorted(scored, reverse=True))


# The one change. celeritas(), activate() and selftest() read this global on the prior module.
_PRIOR._cel_versioned = _cel_versioned
_PRIOR.CEL_CANDIDATES = _cel_versioned()

for _name, _value in vars(_PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value
CEL_CANDIDATES = _PRIOR.CEL_CANDIDATES


def __getattr__(name: str):
    """Every public name of the prior version stays reachable here."""
    return getattr(_PRIOR, name)


def selftest() -> int:
    rc = _PRIOR.selftest()
    versioned = sorted(HERE.glob("VeritasCeleritas_v*.py"), key=_vnum)
    clean = [p.name for p in versioned
             if "talib" not in p.read_text(encoding="utf-8", errors="ignore").lower()]
    own = Path(__file__).read_text(encoding="utf-8")
    checks = [
        ("CEL_CANDIDATES is the newest talib-free VeritasCeleritas_v*",
         bool(clean) and CEL_CANDIDATES[:1] == (clean[-1],)),
        ("no body file name is written into this tail",
         re.search(r"VeritasCeleritas_v\d{4}\.py", own) is None),
    ]
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"  [註] v{_vnum(Path(__file__)):04d} 解析序:{list(CEL_CANDIDATES)} · PRIOR {PRIOR.name}")
    return 0 if rc == 0 and all(ok for _n, ok in checks) else 1


if __name__ == "__main__":
    _a = sys.argv[1:]
    if "--modules" in _a:
        sys.exit(_PRIOR.cmd_modules())
    if "--activate" in _a:
        sys.exit(_PRIOR.cmd_activate())
    if "--libs" in _a:
        sys.exit(_PRIOR.cmd_libs())
    sys.exit(selftest())

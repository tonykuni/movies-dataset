#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Net-tool tail v0118. The network core is the one the lock book names, not the newest file in the folder.

Operator 2026-09-28: "透過VCGC才能啟用" / "版本固定". Up to v0117 the core was found by
v0115 _resolve_aegis_path: the largest VeritasAegisNexus_v*.py in the folder. Dropping a
new file there switched every VDF engine at once, with no check. v0118 asks the lock book
first (CGC_MDL233_ToolActivate pinned('network'), the same ruler the bootstrap and the
accelerator loader use); only VCGC `tools activate ... --apply` moves the lock. No lock,
or the file it names is gone: the v0115 rule as before. VIA_AEGIS_PATH still wins when set.
This file does not fetch.
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
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REG = HERE.parent / "registry"
STEM = "SUP_MDL740_NetUnified"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_PRIOR = _load(PRIOR, "net_prior_for_" + Path(__file__).stem)


def _rule_globals() -> dict:
    """The globals _aegis() really reads. Thin tails copy v0115's names upward, so the first module
    down the chain that *has* _AEGIS_CACHE is a copy; patching a copy changes nothing."""
    return _PRIOR._aegis.__globals__


def _activator():
    hits = [p for p in REG.glob("CGC_MDL233_ToolActivate_v*.py") if _vnum(p) >= 0]
    return _load(max(hits, key=_vnum), "tool_activate_for_" + Path(__file__).stem) if hits else None


_RULE = _rule_globals()
_OLD_RESOLVE = _RULE["_resolve_aegis_path"]


def _resolve_aegis_path(env=None):
    env = env if env is not None else os.environ
    override = str(env.get("VIA_AEGIS_PATH") or "").strip()
    if override and Path(override).is_file():
        return str(Path(override).resolve())
    try:
        act = _activator()
        pinned = act.pinned("network") if act else None
    except Exception as exc:
        pinned = None
        LOCK_NOTE.append(f"lock unreadable: {type(exc).__name__}")
    if pinned:
        return str(pinned)
    return _OLD_RESOLVE(env)


LOCK_NOTE: list = []
_RULE["_resolve_aegis_path"] = _resolve_aegis_path
_RULE["VIA_AEGIS_PATH"] = _resolve_aegis_path()
_RULE["_AEGIS_CACHE"]["mod"] = None
VIA_AEGIS_PATH = _RULE["VIA_AEGIS_PATH"]

for _name, _value in vars(_PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def selftest() -> int:
    act = _activator()
    pinned = act.pinned("network") if act else None
    newest = max((p for p in HERE.glob("VeritasAegisNexus_v*.py") if _vnum(p) >= 0), key=_vnum, default=None)
    checks = [
        ("core = lock book, not the newest file", bool(pinned) and Path(VIA_AEGIS_PATH).name == pinned.name),
        ("_aegis() loads the pinned core", bool(pinned) and Path(getattr(_PRIOR._aegis(), "__file__", "")).name == pinned.name),
        ("VIA_AEGIS_PATH override still wins", _resolve_aegis_path({"VIA_AEGIS_PATH": str(Path(__file__))}) == str(Path(__file__).resolve())),
        ("prior chain intact", _PRIOR.selftest() == 0),
    ]
    for name, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    print(f"  [註] 鎖 {pinned.name if pinned else 'ABSENT'} · 夾內最新 {newest.name if newest else 'ABSENT'}")
    return 0 if all(ok for _n, ok in checks) else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    return _PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

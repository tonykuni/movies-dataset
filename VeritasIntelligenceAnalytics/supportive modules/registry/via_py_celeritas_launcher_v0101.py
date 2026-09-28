#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""via_py_celeritas_launcher_v0101 — py 加速啟動器:掛的是鎖冊指定的加速器本體(R20c 舊檔名探針抓到的遺漏)

v0100 依序試 accelerator/VeritasCeleritas.py(23 行 CLI 座位,只有 main,取不到加速器 API)與
supportive modules/VeritasCeleritas.py(Z218 已退役),把前者以本名 VeritasCeleritas 掛進 sys.modules——
掛上了,但 _LIB_MAP / get_available_libs 都沒有。v0101 先掛鎖冊指定的那一支(CGC_MDL233 pinned,
今天 VeritasCeleritas_v1141),鎖讀不到才走 v0100 的舊序。其餘(runpy 同行程執行目標腳本、自測)照 v0100。
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
STEM = "via_py_celeritas_launcher"

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _load_as(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_PRIOR = _load_as(PRIOR, STEM + "_prior_for_" + Path(__file__).stem)
LOCK_NOTE: list = []


def pinned_accelerator() -> Path | None:
    """The accelerator body the lock book names (CGC_MDL233 pinned; only VCGC activate moves it)."""
    hits = [p for p in HERE.glob("CGC_MDL233_ToolActivate_v*.py") if _vnum(p) >= 0]
    if not hits:
        return None
    try:
        return _load_as(max(hits, key=_vnum), "tool_activate_for_" + Path(__file__).stem).pinned("accelerator")
    except Exception as exc:
        LOCK_NOTE.append(f"lock unreadable: {type(exc).__name__}")
        return None


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def mount_celeritas() -> bool:
    """掛鎖冊指定的加速器本體為 sys.modules['VeritasCeleritas'];鎖讀不到 = v0100 舊序。"""
    sup = str(HERE.parent)
    if sup not in sys.path:
        sys.path.insert(0, sup)
    cur = sys.modules.get("VeritasCeleritas")
    if cur is not None and hasattr(cur, "_LIB_MAP"):
        return True
    p = pinned_accelerator()
    if p is None:
        return _PRIOR.mount_celeritas()
    try:
        _load_as(p, "VeritasCeleritas")
        return True
    except Exception as exc:
        sys.modules.pop("VeritasCeleritas", None)
        LOCK_NOTE.append(f"{p.name}: {type(exc).__name__}: {str(exc)[:80]}")
        return _PRIOR.mount_celeritas()


_PRIOR.mount_celeritas = mount_celeritas


def selftest() -> int:
    p = pinned_accelerator()
    ok_mount = mount_celeritas()
    mod = sys.modules.get("VeritasCeleritas")
    checks = [
        ("掛的是鎖冊指定的版號本體", bool(p) and getattr(mod, "__file__", "") == str(p)),
        ("掛上的有加速器 API(_LIB_MAP · get_available_libs)", ok_mount and hasattr(mod, "_LIB_MAP") and callable(getattr(mod, "get_available_libs", None))),
    ]
    for name, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    rc = _PRIOR.selftest()
    return 0 if rc == 0 and all(ok for _n, ok in checks) else 1


def main() -> int:
    if sys.argv[1:2] == ["--selftest"]:
        return selftest()
    return _PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())

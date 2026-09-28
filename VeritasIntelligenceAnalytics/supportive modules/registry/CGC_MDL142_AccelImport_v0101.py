#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL142_AccelImport v0101 — 加速器套件導入閘:lib 冊讀鎖冊指定的加速器本體(R20c 舊檔名探針抓到的遺漏)

v0100 的 celeritas_path() 寫死 supportive modules/VeritasCeleritas.py——Z218 起那支已退役(不在是對的),
於是 roster() 回空冊、整個導入閘在「0 件」上跑。v0101 改問鎖冊(CGC_MDL233 pinned('accelerator'),
今天 VeritasCeleritas_v1141),鎖讀不到才退回 v0100 的路徑。其餘(路由政策、探境、安裝要同意閘)照 v0100。
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
STEM = "CGC_MDL142_AccelImport"

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


def celeritas_path() -> Path | None:
    return pinned_accelerator() or _PRIOR.celeritas_path()


_PRIOR.celeritas_path = celeritas_path


def selftest() -> int:
    p = celeritas_path()
    names = _PRIOR.roster()
    checks = [
        ("Celeritas 本體 = 鎖冊指定(帶版號)", bool(p) and bool(re.search(r"_v\d{4}\.py$", p.name))),
        ("lib 冊不是空的(v0100 在退役路徑上是 0 件)", len(names) >= 80),
    ]
    for name, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{' · ' + p.name if p else ''} · {len(names)} 件")
    rc = _PRIOR.selftest()
    return 0 if rc == 0 and all(ok for _n, ok in checks) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:] or sys.argv[1:2] == ["selftest"]:
        return selftest()
    return _PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())

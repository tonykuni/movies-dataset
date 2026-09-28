#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL149_VeritasCentralGovernanceConsole v0164 — 薄尾:前一版改照尾版律取(不再字串釘 v0162)

v0163 用 `PREVIOUS = HERE / "..._v0162.py"` 字串釘死前一版,DB 面板 AST 報 PINVER(違尾版律 L54)。
本尾版:前一版 = 同夾同名「版號小於自己的最新一支」(今天就是 v0163,行為一字不變);其餘全部原樣轉給它(模組層 __getattr__)。
v0163 本身不動(L04 版史);它對 v0162 的釘法留在版史裡,現役入口已經不經過那一行字串去找檔。
與 v0163 同規矩:只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。
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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("vcgc_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def main(argv=None):
    return PRIOR.main(argv)


def selftest() -> int:
    ok = PRIOR_PATH.name < Path(__file__).name and PRIOR_PATH.name.startswith(_STEM + "_v")
    print(f"  [{'OK' if ok else 'FAIL'}] 前一版照尾版律取:{PRIOR_PATH.name}(不再字串釘死)")
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest")[0]
    import re
    pinned = re.search(_STEM + r"_v\d{4}\.py\"", body)
    print(f"  [{'OK' if not pinned else 'FAIL'}] 本支沒有字串釘死同族版號")
    if not ok or pinned:
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    args = sys.argv[1:]
    raise SystemExit(selftest() if args == ["--selftest"] else main())

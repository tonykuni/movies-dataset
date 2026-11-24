#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_PanoramaGuard v0104 — 薄尾:吃 --selftest(全樹契約 L53)· 其餘全部照 v0103

省 Token 讀卡(CGC_MDL158 read)2026-11-24 報 VERB:v0101 ~ v0103 只吃位置動詞 `selftest`,不吃 `--selftest`。
本版只把 `--selftest` 轉成 `selftest` 交前版;前版一字不動。
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
TAG = "VIA_PanoramaGuard v0104"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob("VIA_PanoramaGuard_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def main() -> int:
    argv = sys.argv[1:]
    if argv[:1] == ["--selftest"]:
        sys.argv = [sys.argv[0], "selftest"] + argv[1:]
        rc = PRIOR.main()
        ok = rc == 0
        print("[計] %s 自測 %s(--selftest → 前版 %s selftest rc=%s)" % (TAG, "PASS" if ok else "FAIL", PRIOR_PATH.name, rc), flush=True)
        return 0 if ok else 1
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())

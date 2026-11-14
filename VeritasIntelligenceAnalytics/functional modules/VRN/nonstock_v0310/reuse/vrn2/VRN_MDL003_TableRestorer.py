#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""reuse/vrn2/VRN_MDL003_TableRestorer — 轉接殼:正本是本倉 `functional modules/VRN/VRN_MDL003_TableRestorer.py`(不複製 · Zero-Hydra)。
非個股摘要器 v0310 要 `TextRepairEngine().repair_text_blocks(blocks, reflow=True)`;這裡用 importlib 載入正本後原名轉出。
[VIA:NET-BRIDGE] 零網路。"""
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

_HERE = Path(__file__).resolve()
_VRN = _HERE.parents[3]                                  # functional modules/VRN
CANON = _VRN / "VRN_MDL003_TableRestorer.py"


def _load():
    if not CANON.is_file():
        raise ImportError("VRN_MDL003_TableRestorer 正本不在:%s" % CANON)
    spec = importlib.util.spec_from_file_location("vrn_mdl003_canon", CANON)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vrn_mdl003_canon"] = mod
    spec.loader.exec_module(mod)
    return mod


_M = _load()
TextRepairEngine = _M.TextRepairEngine
repair_text_blocks_batch = getattr(_M, "repair_text_blocks_batch", None)
CANON_PATH = str(CANON)


def __getattr__(name):
    return getattr(_M, name)


def selftest() -> int:
    e = TextRepairEngine()
    out = e.repair_text_blocks([{"page": 1, "block_index": 0, "text": "營收 1,234 億\n元,年增 12%", "block_type": "BODY"}], reflow=True)
    ok = isinstance(out, list) and len(out) >= 1 and "text" in out[0]
    print("[%s] reuse/vrn2 TableRestorer 轉接殼 · 正本 %s · repair_text_blocks 回 %d 塊" % ("PASS" if ok else "FAIL", CANON.name, len(out) if isinstance(out, list) else -1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest())

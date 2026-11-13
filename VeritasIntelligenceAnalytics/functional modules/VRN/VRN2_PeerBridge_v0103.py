#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN2_PeerBridge v0103 — v0102 薄尾(v0102 一字不動):補上標準加速器橋(L103 最高政策:PY 導入加速器)。

實錄(2026-11-13 VCGC SDDValidator v0108 · X-ACCEL RED「缺標準橋:VRN2_PeerBridge_v0102.py」):
  v0100 / v0101 都帶 [VIA:ACCEL-BRIDGE],v0102 薄尾漏帶;工作流 VCGC-WKF024 改指註冊冊尾版後被量出來。
本版只補橋(graceful,零行為變更);prove / status / 其餘動詞全部原樣交 v0102。VRN-1 一律只讀(L123);零網路;不碰 TA-Lib。
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
# [VIA:NET-BRIDGE] 留名:本版不出網

import contextlib
import importlib.util
import io
import re
import sys
from pathlib import Path

VERSION = "v0103"
HERE = Path(__file__).resolve().parent
_STEM = "VRN2_PeerBridge"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== VRN2_PeerBridge %s · 薄尾自測(補加速器橋;其餘照 v0102)===" % VERSION, flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 本版帶標準加速器橋(開頭 + 結尾標記)", "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:ACCEL-BRIDGE:END]" in src)
    chk("② 前版就是 v0102(版號最大的前一支)", PRIOR_PATH.name == "VRN2_PeerBridge_v0102.py", PRIOR_PATH.name)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest()
    print(buf.getvalue(), end="")
    chk("③ v0102 自測照跑通過", rc == 0, "rc %s" % rc)
    chk("④ 不寫 VRN-1 · 不出網 · 不用 TA-Lib", not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib)", src, re.M))
    n = sum(ok)
    print("[%s] VRN2_PeerBridge %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", VERSION, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL127_SixStreams v0104 — 薄尾:自測不吃本機的 NODE_PATH(v0103 一字不動)

2026-11-25 VCGC 串測紅:upd:CGC_MDL127_SixStreams_v0103 rc 1 ·「⑧ NODE_PATH 接線」FAIL。
原因:⑧ 判「子行程有 NODE_PATH ⇔ node_deps 夾在」;執行的機器本來就設了 NODE_PATH(容器 /usr/local/lib/node_modules_global;
桌機裝過 Node 的也常有),node_deps 不在時子行程照樣繼承 → 判錯。引擎行為是對的(在 = 前置、缺 = 環境原樣),錯在自測吃本機狀態。
本版:
  --selftest  先把上層 NODE_PATH 暫時拿掉 → 跑前版十檢 → 還原;另補兩檢:
              ⑪ 上層有 NODE_PATH、node_deps 不在 → 子行程 NODE_PATH 原樣(不加不刪)
              ⑫ 上層有 NODE_PATH、node_deps 在 → node_deps 前置、原值接在後面
  其餘動詞照前版。
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
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL127_SixStreams"
TAG = "CGC_MDL127_SixStreams v0104"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def selftest() -> int:
    keep = os.environ.pop("NODE_PATH", None)
    try:
        prior_rc = PRIOR.selftest()
    finally:
        if keep is not None:
            os.environ["NODE_PATH"] = keep
    ok = [prior_rc == 0]
    print("  [%s] 前版十檢(上層 NODE_PATH 暫時拿掉)rc=%s" % ("OK" if prior_rc == 0 else "FAIL", prior_rc), flush=True)
    saved_env, saved_deps = os.environ.get("NODE_PATH"), PRIOR.NODE_DEPS
    try:
        os.environ["NODE_PATH"] = "/parent/node_modules"
        with tempfile.TemporaryDirectory(prefix="mdl127_") as td:
            PRIOR.NODE_DEPS = Path(td) / "absent" / "node_modules"
            a = PRIOR._child_env().get("NODE_PATH")
            ok.append(a == "/parent/node_modules")
            print("  [%s] ⑪ 上層有 NODE_PATH、node_deps 不在 → 原樣 · %s" % ("OK" if ok[-1] else "FAIL", a), flush=True)
            PRIOR.NODE_DEPS = Path(td) / "node_modules"
            PRIOR.NODE_DEPS.mkdir()
            b = PRIOR._child_env().get("NODE_PATH", "")
            ok.append(b == str(PRIOR.NODE_DEPS) + os.pathsep + "/parent/node_modules")
            print("  [%s] ⑫ 上層有 NODE_PATH、node_deps 在 → 前置 · %s" % ("OK" if ok[-1] else "FAIL", b), flush=True)
    finally:
        PRIOR.NODE_DEPS = saved_deps
        if saved_env is None:
            os.environ.pop("NODE_PATH", None)
        else:
            os.environ["NODE_PATH"] = saved_env
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())

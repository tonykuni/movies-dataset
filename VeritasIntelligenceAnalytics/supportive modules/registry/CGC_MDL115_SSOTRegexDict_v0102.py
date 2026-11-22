#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL115_SSOTRegexDict v0102 — 薄尾:自測只寫暫存夾,不再改已追蹤的冊與頁(v0101 一字不動)

由 CGC_SystemManager v0119 `toolbox check` 揭出:v0101 的 --selftest 會呼叫 run(),把
supportive modules/registry/VIA_SSOT_RegexDict_v0100.json 與 ui_support/VIA_UI_SSOTRegexDict_v0100.html 重寫一遍
→ 不能當交接案(每跑一次工作樹就髒)。本版:
  --selftest   先把前版的兩個輸出路徑(OUTJ · OUT)暫時指到暫存夾 → 跑前版原本的九檢 → 還原;另核兩個已追蹤檔前後 sha 不變。
  其餘(預設 run · --print)照前版,輸出位置不變。唯讀全樹、零網路、零執行被掃的檔(承前版)。
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

import hashlib
import importlib.util
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL115_SSOTRegexDict"
TAG = "CGC_MDL115_SSOTRegexDict v0102"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("mdl115_prior_for_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["mdl115_prior_for_v0102"] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _sha(p: Path):
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def selftest() -> int:
    tracked = [PRIOR.OUTJ, PRIOR.OUT]
    before = [_sha(p) for p in tracked]
    keep = PRIOR.OUTJ, PRIOR.OUT
    with tempfile.TemporaryDirectory(prefix="mdl115_") as td:
        PRIOR.OUTJ = Path(td) / PRIOR.OUTJ.name
        PRIOR.OUT = Path(td) / PRIOR.OUT.name
        try:
            rc = PRIOR.selftest()
        finally:
            PRIOR.OUTJ, PRIOR.OUT = keep
    same = [_sha(p) for p in tracked] == before
    print("  [%s] ⑩ 自測沒有改已追蹤的冊與頁(%s)" % ("OK" if same else "FAIL", " · ".join(p.name for p in tracked)), flush=True)
    ok = rc == 0 and same
    print("[計] %s 自測 %s(前版九檢 rc=%s · 已追蹤檔不變 %s)" % (TAG, "PASS" if ok else "FAIL", rc, same), flush=True)
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 中央 SSOT Regex 治理中心(CGC_MDL115 v0102)· 九檢 + 不改已追蹤檔(零網路)===", flush=True)
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())

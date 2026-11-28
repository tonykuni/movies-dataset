#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_WorkbenchLock v0103 — 薄尾:自測只驗本版與直接前版 v0102(裁定甲);v0100 的前版鏈不再算進本版

實錄(2026-11-28,交接閘 VCGC 紅列 C-workbench-lock-v0102):v0102 本版 7/7 · v0101 本版 8/8,紅在 v0100 的 ⑰:
  它要真樹上 CASE-activation · CASE-vrn_ssot_consistency · CASE-cov_vrn_firstpage_engine 三張交接收據「仍是 rc 0 沒標記的紅」。
  那幾案之後都補過證據,收據不再是那個樣子 → ⑰ 釘著當時的世界;規則本身(receipt_errors:rc 0 但沒標記 → 不綠)沒壞,
  v0100 ⑰ 前半那一條用合成收據驗的仍照驗(本版 ②)。
操作員 2026-11-19 裁定「甲」、2026-11-28「前版鏈比照裁定甲」:尾版自測只驗本版與直接前版。
本版只改自測(v0100 … v0102 一字不動;kit · build · check · all 照 v0102):
  ① 直接前版 v0102 的自測照跑(它 7 檢 + 它的前版 v0101 本身 8 檢);v0101 再往下呼叫 v0100 自測的那一步,這一輪換成「不算進本版」並寫明。
  ② receipt_errors 規則用合成收據驗:rc 0 沒標記 → 不綠;rc 0 有標記 · 有完成時間 · 相依 sha 對 → 沒有「did not prove」。
  ③ 橋在且執行時載到 · 不碰 TA-Lib。
v0100 的自測沒有刪,要看仍可 --selftest;它的結果不再算進本版。只在 tempfile 寫。
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

VERSION = "v0103"
ENGINE = f"VIA_WorkbenchLock_{VERSION}"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VIA_WorkbenchLock_v0102.py"
_pp = HERE / PRIOR_NAME
if not _pp.is_file():
    raise SystemExit(f"[RED] 前版 {PRIOR_NAME} 不在 {HERE}")
_spec = importlib.util.spec_from_file_location("via_workbenchlock_v0102_for_v0103", _pp)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0101 = PRIOR.BASE
V0 = PRIOR.V0                        # v0100(鎖站 · 渲染 · check · receipt_errors)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _chain_skipped() -> int:
    print("  [裁定甲] v0100 自測不算進本版(未跑;要看仍可 VIA_WorkbenchLock_v0100.py --selftest)", flush=True)
    return 0


def selftest() -> int:
    keep = V0.selftest
    V0.selftest = _chain_skipped                 # 只換 v0101 往下呼叫的那一步;跑完還原
    try:
        rc_prior = PRIOR.selftest()              # v0102 7 檢 + v0101 本身 8 檢
    finally:
        V0.selftest = keep
    checks = []

    def chk(name, cond, note=""):
        checks.append(bool(cond))
        print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, (" · " + note) if note else ""), flush=True)

    print(f"[{ENGINE} 薄尾加檢(裁定甲)]", flush=True)
    chk("① 直接前版 v0102 自測過(它 7 檢 + v0101 本身 8 檢;v0100 鏈不算進本版)", rc_prior == 0, "rc %s" % rc_prior)
    chk("① b v0100 的 selftest 已還原(本版沒改到前版)", V0.selftest is keep)
    with tempfile.TemporaryDirectory(prefix="wbl0103_") as td:
        via = Path(td)
        (via / "dep.txt").write_text("x\n", encoding="utf-8")
        sha = hashlib.sha256(b"x\n").hexdigest()
        base = {"schema": "VIA.Handoff.TestReceipt.v1", "completed_at": "t", "command": "c", "dependencies": {"dep.txt": sha}}
        bad = V0.receipt_errors(via, dict(base, rc="0", target_marker_seen="False"))
        good = V0.receipt_errors(via, dict(base, rc=0, target_marker_seen=True))
        moved = V0.receipt_errors(via, dict(base, rc=0, target_marker_seen=True, dependencies={"dep.txt": "0" * 64}))
    nope = "test did not prove target success"
    chk("② receipt_errors:rc 0 沒標記 → 不綠;有標記且相依 sha 對 → 沒有這兩條;相依 sha 變 → 點名(合成收據不帶日誌,日誌那條不在此驗)",
        nope in bad and nope not in good and not any(e.startswith("dependency changed") for e in good)
        and any(e.startswith("dependency changed") for e in moved), f"{bad} · {good} · {moved}")
    text = Path(__file__).read_text(encoding="utf-8")
    chk("③ 加速器橋在且執行時載到 · 不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    good_all = rc_prior == 0 and all(checks)
    print("[%s] %s selftest · 本版 %d/%d · 直接前版 v0102 %s" % ("PASS" if good_all else "FAIL", ENGINE, sum(checks), len(checks),
                                                          "PASS" if rc_prior == 0 else "FAIL"), flush=True)
    return 0 if good_all else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())

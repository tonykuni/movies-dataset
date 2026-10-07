#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0191 — 薄尾:v0159 的流程閘門改取 CGC_MDL223 尾版(不再釘死 v0100)。

實況(2026-10-07,main 0447d48c 之後):流程閘 CGC_MDL223 v0102 已修好(VDF 薄尾 v0131+ 的 VCGC 入口契約
沿 PRIOR 鏈繼承,VCGC-REQ174),`via-vcgc run …` 走 v0168 的 _gate_ok(glob 取尾版)→ 放行;
但 registry-sync 等落到 v0159 main() 的動詞,v0159 寫死 DOOR = CGC_MDL223_FlowConsistency_v0100.py(釘名)→
仍用 v0100 的判準 → VDF 列 RED → registry-sync 回 rc 2、什麼都不寫。
本版只改這一件:前版鏈載入後,把 v0159 模組(sys.modules「vcgc_v0159_for_v0160」)上的 DOOR 換成
CGC_MDL223_FlowConsistency 的尾版(glob 取最大版號)。v0159 main() / selftest() 執行時才讀模組全域 DOOR → 走尾版。
閘門本身的判準不在這裡改(在 CGC_MDL223 / CGC_MDL222 尾版)。v0100 檔留著不動(舊版不刪)。
其餘照 v0190(VIA_FROM_VCGC=YES 才放行,同前版)。不碰 TA-Lib;不代設同意閘;零網路。
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
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
_DOOR_STEM = "CGC_MDL223_FlowConsistency"
_V0159_NAME = "vcgc_v0159_for_v0160"                    # v0160 載 v0159 用的模組名


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)\.py$", str(p))
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0191", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0190
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0188 = PRIOR.V0188


def __getattr__(name):
    return getattr(PRIOR, name)


def door_tail() -> Path | None:
    hits = [p for p in HERE.glob(_DOOR_STEM + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


V0159 = sys.modules.get(_V0159_NAME)
DOOR_V0159_PINNED = getattr(V0159, "DOOR", None)
if V0159 is not None and door_tail() is not None:
    V0159.DOOR = door_tail()                             # v0159 main / selftest 取模組全域 DOOR → 走尾版


def main(argv=None):
    return PRIOR.main(argv)


def selftest() -> int:
    keep_file = PRIOR.__dict__.get("__file__")
    PRIOR.__dict__["__file__"] = str(Path(__file__).resolve())      # 前版鏈「尾版 = 自己」的檢查指向目前生效入口(本檔)
    try:
        prior_rc = PRIOR.selftest()
    finally:
        PRIOR.__dict__["__file__"] = keep_file
    print("=== VCGC v0191 · 薄尾自測(v0159 流程閘門取 CGC_MDL223 尾版)===")
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("① 前版鏈自測過(v0190 → v0189 → …)", prior_rc == 0, f"rc {prior_rc}")
    tail = door_tail()
    chk("② 找到 v0159 模組,原本釘 v0100", V0159 is not None and DOOR_V0159_PINNED is not None
        and Path(DOOR_V0159_PINNED).name == _DOOR_STEM + "_v0100.py", getattr(DOOR_V0159_PINNED, "name", DOOR_V0159_PINNED))
    chk("③ v0159 的 DOOR 已換成尾版", V0159 is not None and tail is not None and Path(V0159.DOOR) == tail, getattr(tail, "name", tail))
    os.environ.setdefault("VIA_VCGC_PUSH", "NO")
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = V0159._load(V0159.DOOR, "flow_self_console_v0191").gate() if V0159 is not None else {}
    chk("④ 經 v0159 的門跑閘:放行(與 run 動詞走的 _gate_ok 同一個尾版)", card.get("lock_success") is True, card.get("missing"))
    chk("⑤ 舊版 v0100 檔留著不動(只換引用)", (HERE / (_DOOR_STEM + "_v0100.py")).is_file())
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋在 · 只收 VCGC(VIA_FROM_VCGC)· 不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in src and "VIA_FROM_VCGC" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"  [計] VCGC v0191 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(selftest() if sys.argv[1:] == ["--selftest"] else main())    # 只有單獨 --selftest 跑中央自測;run X --selftest 照路由給 X(v0176 起的規矩)

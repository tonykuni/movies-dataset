#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL170_VDFChainRunner v0105 — 薄尾:每站開始 / 結束立刻印一行進度(via-realtest 的動態進度條 · 百分比靠它)

操作員(R42 工作站實錄 2026-10-01):`python $V run --family vdf CGC_MDL170_VDFChainRunner run` 印完
「=== VDF 獨立鏈 · run · 起始日 2023-07-01 ===」就沒有下文 →「太慢了還是卡斷」。量到的:本體逐站 subprocess.run(capture_output)
靜靜等,全部站跑完才一次印 MATRIX SUMMARY;真資料下 3a 特徵庫 · 4b 增量擷取要跑一陣子,畫面上看不出在跑哪一站、跑了幾成。
本尾版只包本體的 run_one(一站一次):開始印「[進度] VDF k/N 開始 <站> <名>」,結束印「[進度] VDF k/N 完成 <站> <名> · <燈> · <秒>s」,
flush 立即寫出(N = 本體 CHAIN 站數)。站的執行 · 逾時 · 判燈 · 報告 · --resume 全照 v0104。零網路(觸網照舊由同意閘管)· 不用 TA-Lib。
只收 VCGC 呼叫(VIA_FROM_VCGC=YES)的規矩照前一版。
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

_STEM = "CGC_MDL170_VDFChainRunner"

import importlib.util
import os
import re
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
ENGINE_TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
_LOCK = threading.Lock()
_STATE = {"done": 0, "total": None}


def __getattr__(name):
    return getattr(PRIOR, name)


def _body(attr: str):
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if callable(vars(m).get(attr)) and "subprocess" in vars(m):
            return m
        m = vars(m).get("PRIOR")
    return None


def say(line: str) -> None:
    """One progress line, flushed at once (via-realtest reads these live for the bar and the percentage)."""
    with _LOCK:
        print(line, flush=True)


BODY = _body("run_one")
_RUN_ONE0 = BODY.run_one


def run_one(sid, name, glob_, argv, timeout, expect, fix, since):
    total = len(getattr(BODY, "CHAIN", ()) or ()) or None
    with _LOCK:
        _STATE["done"] += 1
        k = _STATE["done"]
    tag = f"{k}/{total}" if total else f"{k}/?"
    say(f"[進度] VDF {tag} 開始 {sid} {name}")
    t0 = time.time()
    row = _RUN_ONE0(sid, name, glob_, argv, timeout, expect, fix, since)
    say(f"[進度] VDF {tag} 完成 {sid} {name} · {row.get('state')} · {round(time.time() - t0, 1)}s")
    return row


BODY.run_one = run_one


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE_TAG} · 薄尾自測(逐站進度行)===")
    chk("① 本體的站執行格換成本版;站數從本體 CHAIN 讀", BODY is not None and BODY.run_one is run_one and len(BODY.CHAIN) >= 1, len(BODY.CHAIN))
    seen, lines = [], []
    global _RUN_ONE0
    real = _RUN_ONE0
    _RUN_ONE0 = lambda *a: seen.append(a[0]) or {"id": a[0], "state": "GREEN"}
    keep_say = globals()["say"]
    globals()["say"] = lambda line: lines.append(line)
    _STATE["done"] = 0
    try:
        r1 = run_one("1", "參數", "x", [], 1, "", "", "2023-07-01")
        r2 = run_one("2", "邏輯", "x", [], 1, "", "", "2023-07-01")
    finally:
        _RUN_ONE0 = real
        globals()["say"] = keep_say
        _STATE["done"] = 0
    n = len(BODY.CHAIN)
    chk("② 每站一行開始、一行完成;帶 k/N · 燈 · 秒;結果原樣回傳(判燈不動)",
        lines[0] == f"[進度] VDF 1/{n} 開始 1 參數" and lines[1].startswith(f"[進度] VDF 1/{n} 完成 1 參數 · GREEN · ")
        and lines[3].startswith(f"[進度] VDF 2/{n} 完成 2 邏輯") and r1 == {"id": "1", "state": "GREEN"} and seen == ["1", "2"], lines)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("③ 加速器橋在(同前版:本支不觸網,無網路橋);不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    rc = PRIOR.selftest()
    good = all(ok)
    print(f"  [計] {ENGINE_TAG} 薄尾 {sum(ok)}/{len(ok)} · v0104 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if good and rc == 0 else 'FAIL'}")
    return 0 if good and rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

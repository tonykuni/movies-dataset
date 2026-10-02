#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL172_VRNChainRunner v0108 — 薄尾:每個節點開始 / 結束立刻印一行進度(via-realtest 的動態進度條 · 百分比靠它)

操作員(R42 2026-10-01):「太慢了還是卡斷 … 25 個加速器 動態進度條 動態百分比 自動跳出報告」。
量到的:本體層內並行(ThreadPoolExecutor)逐節點 subprocess.run(capture_output),全部層跑完才一次印總表;
工作站上 ENG072 · AutoTestLoop 一跑就是幾分鐘,畫面上看不出跑到哪。
本尾版只包本體的 run_node(一節點一次;v0107 的逾時留證 · v0106 的逾時冊照樣在內層):
開始印「[進度] VRN 開始 <層> <家族>」,結束印「[進度] VRN k/N 完成 <層> <家族> · <燈> · <秒>s」(k = 已完成數,執行緒安全;
N = 六層冊上的節點總數),flush 立即寫出。判燈 · 報告 · --resume · --only 全照 v0107。零網路 · 不用 TA-Lib。
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

_STEM = "CGC_MDL172_VRNChainRunner"

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


BODY = _body("run_node")
_RUN_NODE0 = BODY.run_node            # v0107 的 run_node(已裝在本體上)


def _total():
    if _STATE["total"] is None:
        try:
            chain, _who = BODY.load_chain()
            _STATE["total"] = sum(len(l.get("nodes") or []) for l in chain) or None
        except Exception:
            _STATE["total"] = None
    return _STATE["total"]


def run_node(layer, node, timeout):
    fam = node.get("family") or "?"
    total = _total()
    say(f"[進度] VRN 開始 {layer} {fam}")
    t0 = time.time()
    row = _RUN_NODE0(layer, node, timeout)
    with _LOCK:
        _STATE["done"] += 1
        k = _STATE["done"]
    say(f"[進度] VRN {k}/{total if total else '?'} 完成 {layer} {fam} · {row.get('state')} · {round(time.time() - t0, 1)}s")
    return row


BODY.run_node = run_node


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE_TAG} · 薄尾自測(逐節點進度行 · 執行緒安全)===")
    n = _total()
    chk("① 本體的節點執行格換成本版;總數從六層冊讀", BODY is not None and BODY.run_node is run_node and (n or 0) >= 1, n)
    lines = []
    global _RUN_NODE0
    real = _RUN_NODE0
    _RUN_NODE0 = lambda layer, node, timeout: (time.sleep(0.01), {"state": "GREEN"})[1]
    keep_say = globals()["say"]
    globals()["say"] = lambda line: lines.append(line)
    _STATE["done"] = 0
    try:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as ex:
            got = list(ex.map(lambda i: run_node("L1_擷取", {"family": f"F{i}"}, 1), range(8)))
    finally:
        _RUN_NODE0 = real
        globals()["say"] = keep_say
        _STATE["done"] = 0
    done = sorted(int(l.split()[2].split("/")[0]) for l in lines if " 完成 " in l)
    chk("② 8 個節點並行:開始 8 行 · 完成 8 行,k 由 1 到 8 不重不漏(執行緒安全);結果原樣回傳",
        sum(" 開始 " in l for l in lines) == 8 and done == list(range(1, 9)) and all(g == {"state": "GREEN"} for g in got), done)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("③ 加速器橋在(同前版:本支不觸網,無網路橋);不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    rc = PRIOR.selftest()
    good = all(ok)
    print(f"  [計] {ENGINE_TAG} 薄尾 {sum(ok)}/{len(ok)} · v0107 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if good and rc == 0 else 'FAIL'}")
    return 0 if good and rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

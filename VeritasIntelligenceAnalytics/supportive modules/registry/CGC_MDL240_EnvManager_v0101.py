#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL240_EnvManager v0101 — 薄尾:每一個委派檢查開始 / 結束立刻印一行進度(via-realtest 的環境進度條靠它)

操作員(R43 2026-10-02,工作站 via-realtest 實跑):「他卡住了嗎」「en manager怎麼丟了」。
量到的:v0100 依序委派 8 支正主(工具鎖 · 加速器 · 網路 · LAYOUT · NLP · 覆蓋 · RunGate · 工具冊),每支 capture_output,
全部跑完才一次印總表;工作站上 RunGate 逐境匯入、覆蓋全樹掃描要好幾分鐘,畫面 780 秒沒有一行字,看起來像卡住 / 丟了。
本尾版只把本體 check() 的委派格(runner)換成會報進度的那一支:開始印「[進度] ENV k/N 開始 <名>」(格式同 VDF 鏈跑器),
結束印「[進度] ENV k/N 完成 <名> · rc <rc> · <秒>s」,flush 立即寫出。判燈 · 補法 · JSON · 只查不裝全照 v0100。
零網路 · 不用 TA-Lib。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)的規矩照前一版。
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

_STEM = "CGC_MDL240_EnvManager"

import importlib.util
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOTAL = 8                                   # 工具鎖 1 + 載入 4(加速器 · 網路 · LAYOUT · NLP)+ 覆蓋 1 + RunGate 1 + 工具冊 1


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
ENGINE_TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
_STATE = {"k": 0}


def __getattr__(name):
    return getattr(PRIOR, name)


def say(line: str) -> None:
    """One progress line, flushed at once (via-realtest reads these live for the bar and the percentage)."""
    print(line, flush=True)


def _name(argv) -> str:
    stem = Path(str(argv[0])).stem if argv else "?"
    return stem + ("" if len(argv) < 2 else " " + str(argv[1]))


def progress_runner(inner):
    """Wrap one delegated-check runner: a start line before, a done line (rc · seconds) after; the result is returned unchanged."""
    def runner(argv, timeout=300):
        _STATE["k"] += 1
        k, nm = _STATE["k"], _name(argv)
        say(f"[進度] ENV {k}/{TOTAL} 開始 {nm}")
        t0 = time.time()
        r = inner(argv, timeout)
        say(f"[進度] ENV {k}/{TOTAL} 完成 {nm} · rc {r.get('rc')} · {round(time.time() - t0, 1)}s")
        return r
    return runner


_CHECK0 = PRIOR.check


def check(runner=None, which=None, ps_side=None, chains=None) -> dict:
    _STATE["k"] = 0
    kw = {"runner": progress_runner(runner or PRIOR.run), "ps_side": ps_side}
    if which is not None:
        kw["which"] = which
    if chains is not None:
        kw["chains"] = chains
    return _CHECK0(**kw)


PRIOR.check = check                         # 本體 main() 以模組全域名呼叫 check → 走本版


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

    print(f"=== {ENGINE_TAG} · 薄尾自測(逐委派進度行 · 結果原樣)===")
    lines, calls = [], []
    keep = globals()["say"]
    globals()["say"] = lambda line: lines.append(line)
    try:
        def fake(argv, timeout=0):
            calls.append(argv)
            return {"rc": 0, "out": "  [OK] x\n  [計] 1/1", "secs": 0.0}
        rep = check(runner=fake, which=lambda e: "/bin/" + e, ps_side=None, chains=())
    finally:
        globals()["say"] = keep
    starts = [l for l in lines if " 開始 " in l]
    dones = [l for l in lines if " 完成 " in l]
    chk("① 每個委派前後各一行:開始 / 完成數 = 委派數,k 由 1 起連號", len(starts) == len(dones) == len(calls) >= 1
        and [int(l.split()[2].split("/")[0]) for l in starts] == list(range(1, len(calls) + 1)), f"{len(calls)} 支")
    chk("② 總數 N 對得上本體委派數(工作樹齊全時)", len(calls) == TOTAL, f"{len(calls)} / {TOTAL}")
    chk("③ 判燈照本體:同一份假結果,本體直跑與本版的總判一樣", rep.get("verdict") == _CHECK0(runner=lambda a, t=0: {"rc": 0, "out": "  [OK] x\n  [計] 1/1", "secs": 0.0},
                                                                         which=lambda e: "/bin/" + e, ps_side=None, chains=()).get("verdict"), rep.get("verdict"))
    chk("④ 本體 main 走本版 check;只查不裝(寫入旗標照本體拒跑)", PRIOR.check is check and PRIOR.run(["x.py", "--apply"])["rc"] is None)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋在(同前版:本支不觸網,無網路橋);不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    rc = PRIOR.selftest()
    good = all(ok)
    print(f"  [計] {ENGINE_TAG} 薄尾 {sum(ok)}/{len(ok)} · v0100 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if good and rc == 0 else 'FAIL'}")
    return 0 if good and rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_LakeMatrix v0102 — 薄尾:自測時鐘凍在夾具那一刻(拆掉 v0100 ⓔ 的定時炸彈);功能照 v0101

實錄(2026-11-28,交接閘 VCGC 紅列 C-lake-matrix-v0101):v0100 / v0101 自測都 11/12,紅在 ⓔ「VCGC 今天有活動」。
  夾具把「今天」釘在 2026-11-10 03:00 UTC(now 參數),但入湖的時間戳是 VIA_ParquetLake 的 _now() 拿真的時鐘。
  2026-11-17 以後真時鐘落在七日視窗外 → VCGC 那一列七天全是 0 → 每天都紅。功能沒有壞(實跑用真時鐘,兩邊一致)。
  CLAUDE.md 補強三:「自測不吃本機狀態」(時鐘也是本機狀態)。
本版只改自測(v0100 / v0101 與兩支 ParquetLake 一字不動;build · ingest · 頁面 · main 的其餘動詞照 v0101):
  自測期間把湖套件載入器包一層:每次載到的湖模組,凡定義 _now 的那一層,改回傳夾具時刻起算、每呼叫一次加一微秒的 UTC 戳
  (先後順序照舊分得出來);跑完還原載入器。v0101 整條前版鏈(含 v0100 十二檢)照跑。
  操作員 2026-11-28「前版鏈比照裁定甲」:本版自測驗本版與直接前版 v0101(v0101 在行程內帶 v0100)。
不連網;不碰 TA-Lib;只在 tempfile 寫。
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
import itertools
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

VERSION = "v0102"
ENGINE = "VIA_LakeMatrix " + VERSION
HERE = Path(__file__).resolve().parent
_PRIOR_FILE = HERE / "VIA_LakeMatrix_v0101.py"
_spec = importlib.util.spec_from_file_location("VIA_LakeMatrix_v0101_for_v0102", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0 = PRIOR.P                                   # v0100(自測 · _lake_module 掛在這一層)
FIXTURE_NOW = datetime(2026, 11, 10, 3, 0, tzinfo=timezone.utc)   # 與 v0100 / v0101 自測的 now 同一刻


def __getattr__(name):
    return getattr(PRIOR, name)


def frozen_clock(start: datetime = FIXTURE_NOW - timedelta(minutes=30)):
    """回傳一支 _now 替身:從 start 起每呼叫一次加一微秒(格式同 ParquetLake._now)。"""
    tick = itertools.count()

    def _now() -> str:
        return (start + timedelta(microseconds=next(tick))).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return _now


def _freeze(mod, clock):
    m, seen = mod, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if callable(vars(m).get("_now")):
            m._now = clock
        m = vars(m).get("PRIOR") or vars(m).get("P")
    return mod


def selftest() -> int:
    keep = V0._lake_module
    clock = frozen_clock()
    keep1 = vars(PRIOR).get("_lake_module")
    V0._lake_module = lambda: _freeze(keep(), clock)
    if keep1 is not None:
        PRIOR._lake_module = V0._lake_module    # v0101 自己那層也讀同一支
    try:
        rc = PRIOR.selftest()                   # v0101 四檢 + v0100 十二檢,時鐘凍在夾具那一刻
    finally:
        V0._lake_module = keep
        if keep1 is not None:
            PRIOR._lake_module = keep1
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    print(f"=== {ENGINE} 薄尾加檢(自測時鐘)===")
    chk("① 直接前版 v0101 自測過(含 v0100 ⓔ 五系統 × 日)", rc == 0, f"rc {rc}")
    chk("② 載入器已還原(實跑照用真時鐘)", V0._lake_module is keep and vars(PRIOR).get("_lake_module") is keep1)
    c = frozen_clock()
    a, b = c(), c()
    chk("③ 替身時鐘:夾具當天 · 嚴格遞增 · 格式同 ParquetLake", a < b and a.startswith("2026-11-10T02:30:00.") and a.endswith("Z") and len(a) == 27, (a, b))
    lake = keep()
    real_now = vars(lake).get("_now")
    chk("④ 真湖模組的 _now 沒被本版改到(只在自測替身裡)", callable(real_now) and real_now()[:4] == str(datetime.now(timezone.utc).year))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋在且執行時載到 · 不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    good = rc == 0 and all(ok)
    print("[%s] %s selftest · 本版 %d/%d · 前版鏈 v0101 %s" % ("PASS" if good else "FAIL", ENGINE, sum(ok), len(ok), "PASS" if rc == 0 else "FAIL"))
    return 0 if good else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or (args and args[0] == "selftest"):
        return selftest()
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG239_ParquetLakeBuild v0105 — 薄尾(v0100–v0104 一字不動):run --all 不再重複擷取日價(① 跳過)

操作員 2026-11-26:「有無重複擷取引擎 · 用 VCGC 節省 TOKEN 工具全景式檢視 · 模塊化優化 AST 整合」。
全景盤點(擷取冊 × 族群冊 × DataPlane 冊 + 語法樹掃各引擎的資料來源)找到的重複:
  run --all 先 ⓪ FetchGroups 全族群(含 e054 台股日價 2018 起 · e066 全球日價 78 檔),
  接著 v0100 的 ① 又叫 VDF_ENG064_HistoryBackfill 對 tw_daily_prices + global_daily 從起日整段 yahoo_chart 回補 ——
  同兩張表、同一個來源再抓一遍(anti-join 不會重寫列,但請求與時間全部重花)。
本版只在 --all 時把 ① 換成「跳過(⓪ 已含)」並寫明;不帶 --all 照 v0104(① 照跑,那是 ① 的本來用途)。
其餘(視窗 · ② 增量入湖 · ③ VIEW · window / status 動詞)照 v0104。零網路;不設同意閘;不用 TA-Lib。
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_ENG239_ParquetLakeBuild"
VERSION = "v0105"
TAG = f"{STEM} {VERSION}"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.P0                                       # v0100 本體(run 依模組全域名找 fetch)
DUP_NOTE = "⓪ 全族群已含 e054 台股日價 · e066 全球日價 → ① ENG064 不重抓(v0105)"


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def skipped_fetch(start, end, limit=None) -> dict:
    print(f"[①擷取] 跳過:{DUP_NOTE}", flush=True)
    return {"state": "SKIPPED", "note": DUP_NOTE}


def run(argv: list) -> int:
    if "--all" not in argv:
        return PRIOR.run(argv)
    keep = P0.fetch
    P0.fetch = skipped_fetch
    try:
        return PRIOR.run(argv)
    finally:
        P0.fetch = keep


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] == ["run"]:
        return run(a[1:])
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    print(f"=== {TAG} · 薄尾自測(假前版;零網路)===", flush=True)
    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 網路工具橋在位(載入不出網)", VIA_NET_TOOL_PATH is not None)
    seen = {}
    keep_run = PRIOR.run
    try:
        def fake_run(argv):
            seen.setdefault("calls", []).append((list(argv), P0.fetch("2018-01-01", "2026-11-26", None)["state"] if "--all" in argv else "PRIOR_FETCH"))
            return 0
        PRIOR.run = fake_run
        rc1 = run(["--all", "--start", "2018-01-01"])
        rc2 = run(["--start", "2018-01-01"])
    finally:
        PRIOR.run = keep_run
    chk("③ --all → ① ENG064 換成跳過(⓪ 已含 e054 · e066)· rc 照傳",
        rc1 == 0 and seen["calls"][0] == (["--all", "--start", "2018-01-01"], "SKIPPED"), seen.get("calls"))
    chk("④ 不帶 --all → 照前版(① 照跑)", rc2 == 0 and seen["calls"][1][1] == "PRIOR_FETCH", seen.get("calls"))
    chk("⑤ 跑完 v0100 fetch 換回原函式", P0.fetch is not skipped_fetch)
    rc_p = PRIOR.selftest()
    chk("⑥ 前版 v0104 自測照過(rc 0)", rc_p == 0, rc_p)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 檔面:第 3 行加速器標記 · 雙橋 · glob 取前版 · 零 TA-Lib · 不設同意閘",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:NET-BRIDGE:v0100]" in src and "HERE.glob(STEM" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"{TAG} selftest {sum(ok)}/{len(ok)}", flush=True)
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())

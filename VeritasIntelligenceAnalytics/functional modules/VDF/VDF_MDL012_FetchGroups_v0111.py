#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL012_FetchGroups v0111 — 薄尾(v0100–v0110 一字不動):自測不再因族群冊升版而紅

2026-11-21 容器實錄:VDF 啟動器 engine_launch 複驗 VDF_MDL012_FetchGroups 自測 RED。追到 v0104 自測 ②:
「冊尾版 v0102:14 族群都有 refill 分層;US_MACRO 三層都是 FRED;AkShare 族群走 011d;台股走政府」—— 前三項內容在冊尾版 v0104 全部成立,
紅的只有「尾版檔名必須是 v0102」這一句(冊之後出了 v0103 / v0104,斷言就必紅;v0105–v0110 的鏈自測一路往上紅)。
做法照 v0104 自己的前例(它跑前版時把冊釘在 v0101):本版跑前版鏈時把冊釘在 v0102(那條斷言寫的冊),跑完還原;
本版自己的自測改對「現在的尾版冊」驗同一組內容條件。擷取 / 頁面 / run 全部照 v0110,不動任何行為。
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

import argparse
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path
import types

HERE = Path(__file__).resolve().parent
TAG_V0111 = f"VDF_MDL012_FetchGroups v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
PIN_BOOK = "VDF_FetchGroups_SSOT_v0102.json"          # v0104 自測 ② 寫的冊


def _vnum_v0111(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob("VDF_MDL012_FetchGroups_v*.py") if 0 <= _vnum_v0111(p) < _vnum_v0111(__file__)), key=_vnum_v0111)
_spec = importlib.util.spec_from_file_location("VDF_MDL012_FetchGroups_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def base_module():
    """前版鏈裡持有 BOOK_GLOB 的本體(v0100)。"""
    mod, seen = PRIOR, set()
    found = None
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if "BOOK_GLOB" in vars(mod):
            found = mod
        mod = vars(mod).get("PRIOR")
    return found


def book_conditions(book: dict, base) -> dict:
    return {"refill 全有": all(g.get("refill") for g in book["groups"]),
            "US_MACRO 三層 FRED + FRED_API_KEY": all(t["provider"] == "FRED" and t.get("key") == "FRED_API_KEY" for t in base.group_of(book, "US_MACRO")["refill"]),
            "CN_NBS 走 011d": base.group_of(book, "CN_NBS")["refill"][0]["engines"] == ["011d"],
            "TW_INDEX 走政府": base.group_of(book, "TW_INDEX")["refill"][0]["provider"] == "GOV",
            "族群 14": len(book["groups"]) == 14}


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    print(f"=== {TAG_V0111} 薄尾自測(族群冊升版不再讓舊斷言紅)===", flush=True)
    base = base_module()
    chk("① 找得到前版鏈的本體(BOOK_GLOB 所在)", base is not None)
    book = base.load_book()
    cond = book_conditions(book, base)
    chk("② 冊尾版 %s:%s" % (Path(book.get("_path", "")).name, " · ".join(cond)), all(cond.values()), cond)
    keep = base.BOOK_GLOB
    base.BOOK_GLOB = PIN_BOOK
    try:
        prc = PRIOR.selftest()
    finally:
        base.BOOK_GLOB = keep
    chk("③ 前版鏈 %s → … → v0100 自測照過(跑時冊釘在 %s;跑完還原)" % (PRIOR_PATH.stem, PIN_BOOK), prc == 0 and base.BOOK_GLOB == keep, "rc %s" % prc)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋 + 網路橋真的匯入 · 不碰 TA-Lib · 不設同意閘 · 不含本機路徑",
        "import VIA_SuperAccel_Module as VIA_ACCEL" in src and "[VIA:NET-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src) and ("C:" + "\\Users") not in src)
    good = all(ok)
    print(f"[計] {TAG_V0111} 本版 {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

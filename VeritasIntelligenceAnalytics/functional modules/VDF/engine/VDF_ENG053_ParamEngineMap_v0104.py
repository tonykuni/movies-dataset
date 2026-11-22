#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG053_ParamEngineMap v0104 — 薄尾:冊①統一參數 · 冊②參數登錄改讀尾版(PC-001 裁定後 v0101)。

操作員 2026-11-15 裁定 PC-001:「PC-001 起始日用 2022-01-01」「獨立性」→ VDF_Unified_Params_v0101 time.start_date = 2022-01-01。
  套用時另查到 VDF_Param_Registry_v0100 canonical.START_DATE 裁定值 '1998-01-01'(批99 R7「字串取最完整值」)→ 同一裁定出 v0101 改 '2022-01-01'。
v0102 的 BOOKS 把冊① / 冊② 釘名 v0100 → 映射冊的冊值與治理裁定會一直停在 2018-01-01 / 1998-01-01。
本版(v0103 · v0102 一字不動;只改冊① 冊② 的檔名):兩本都取 [四碼] 尾版;冊③④ 照舊。
寫死 2018-01-01 的引擎常數(START_DATE 等)在映射冊上會顯示與冊值不一致 —— 只攤開,不代改(引擎各自出新版)。
其餘(收割 · 四冊 · 治理五態 · 映射冊 · 車道沿薄尾前版鏈)照 v0103。唯讀收割零觸碰引擎原件;不碰 TA-Lib;零網路。
用法同 v0102:python VDF_ENG053_ParamEngineMap_v0104.py run | --selftest
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
STEM = "VDF_ENG053_ParamEngineMap"
VERSION = "v0104"
TAIL_BOOKS = {"unified": "VDF_Unified_Params_v[0-9][0-9][0-9][0-9].json",
              "registry": "VDF_Param_Registry_v[0-9][0-9][0-9][0-9].json"}


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})\.(?:py|json)$", str(p))
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + VERSION, PRIOR_PATH)
P = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = P
_spec.loader.exec_module(P)
# 別名表照 v0102 / v0103 原文再宣告一次(字面字典):VDF_SSOTSync 只從家族尾版收割 UNIFIED_ALIAS(自測 ② 核對一字不差)。
UNIFIED_ALIAS = {
    "START_DATE": "time.start_date", "END_DATE": "time.end_date",
    "BATCH_SIZE": "fetch.batch_size", "MAX_RETRIES": "fetch.max_retries",
    "RETRY_DELAY": "fetch.retry_delay_s", "RETRY_DELAY_S": "fetch.retry_delay_s",
    "TIMEOUT": "fetch.timeout_s", "TIMEOUT_S": "fetch.timeout_s",
    "HTTP_TIMEOUT": "fetch.timeout_s", "OUTPUT_DIR": "output.root",
    "OUTPUT_ROOT": "output.root", "CSV_ENCODING": "output.csv_encoding",
    "MARKETS": "markets",
}


def tail_name(key: str, pinned: str) -> str:
    """冊 = 該冊 [四碼] 尾版檔名;一支都沒有就回 v0102 原本釘的名(誠實:load_books 會照實標缺)。"""
    hits = list(P.VDF.glob(TAIL_BOOKS[key]))
    return max(hits, key=_vnum).name if hits else pinned


_BOOKS = P.BOOKS                       # 經 v0103 轉接 = v0102 模組全域那一張字典(同一物件)
BOOKS_V0102 = dict(_BOOKS)
for _k in TAIL_BOOKS:                  # v0102 load_books / build_map 依模組全域名找 → 本版接手冊① 冊②
    _BOOKS[_k] = tail_name(_k, BOOKS_V0102[_k])


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接(v0103 → v0102)。"""
    return getattr(P, name)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)
    print(f"=== {STEM} {VERSION} · 薄尾自測(冊① 讀尾版)===", flush=True)
    books = P.load_books()
    uni = books.get("unified") or {}
    reg = ((books.get("registry") or {}).get("canonical") or {}).get("START_DATE") or {}
    t1, t2 = tail_name("unified", ""), tail_name("registry", "")
    chk("① 冊① 冊② 讀尾版(" + t1 + " · " + t2 + ")· 不再釘 v0100 · 統一參數起始日 2022-01-01 · 登錄冊裁定 '2022-01-01'(PC-001)· v0100 兩冊還在",
        _BOOKS["unified"] == t1 and _BOOKS["registry"] == t2 and _vnum(t1) >= 101 and _vnum(t2) >= 101
        and BOOKS_V0102["unified"] == "VDF_Unified_Params_v0100.json" and BOOKS_V0102["registry"] == "VDF_Param_Registry_v0100.json"
        and (uni.get("time") or {}).get("start_date") == "2022-01-01" and reg.get("ruling") == "'2022-01-01'"
        and (P.VDF / "VDF_Unified_Params_v0100.json").is_file() and (P.VDF / "VDF_Param_Registry_v0100.json").is_file(),
        (t1, t2, (uni.get("time") or {}).get("start_date"), reg.get("ruling")))
    chk("② 尾版別名表(字面字典)與前版一字不差 · 13 個同義字照收割",
        UNIFIED_ALIAS == P.UNIFIED_ALIAS and len(UNIFIED_ALIAS) == 13)
    m = P.build_map()
    sd = (m.get("by_param") or {}).get("START_DATE") or {}
    chk("③ 映射冊照建 · START_DATE 治理裁定 = '2022-01-01'(寫死 2018-01-01 的引擎照列,不代改)· 冊名寫的是尾版",
        (sd.get("governance") or {}).get("ruling") == "'2022-01-01'" and m["books"]["unified"] == t1 and m["books"]["registry"] == t2,
        (sd.get("governance"), m.get("books")))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋 · 網路工具橋在;不碰 TA-Lib;本檔不寫檔(映射冊照 v0102 run 寫)",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and "import " + "talib" not in src
        and ".write_text(" not in src.split("def selftest", 1)[0])
    print(f"  前版 {PRIOR_PATH.name} selftest ↓", flush=True)
    prior_rc = P.selftest()
    chk("⑤ 前版 v0103 自測照過(其內再跑 v0102)", prior_rc == 0, prior_rc)
    print(f"[計] {STEM} {VERSION} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    return P.main()


if __name__ == "__main__":
    sys.exit(main())

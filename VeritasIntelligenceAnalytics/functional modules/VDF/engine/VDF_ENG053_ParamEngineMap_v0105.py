#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG053_ParamEngineMap v0105 — 薄尾(v0100–v0104 一字不動):自測跟上「VDF 從 2018-01-01 起」的裁定

操作員 2026-11-22 裁定「VDF 資料取自 2018-01-01 為起始」(覆蓋 11-15 PC-001 的 2022-01-01),2026-11-24 再確認「2018 起」。
冊① VDF_Unified_Params 尾版 time.start_date 與冊② VDF_Param_Registry 尾版 canonical.START_DATE 裁定都已是 2018-01-01;
FetchGroups 範圍帳各大類也是 2018-01-01(總經 1990-01-01 更早)。v0104 自測 ① ③ 仍寫死「2022-01-01」→ 在現在的冊上必紅。
本版:引擎行為(收割 · 四冊 · 治理五態 · 映射冊)全照 v0104;只換自測 —— 冊① 冊② 起始日彼此一致且 = 裁定的 2018-01-01,
映射冊 START_DATE 治理裁定 = '2018-01-01';前版 v0104 自測只容許它寫死 2022 的 ① ③ 兩行紅,其他紅照紅。
唯讀收割零觸碰引擎原件;不碰 TA-Lib;零網路。用法同前版:python VDF_ENG053_ParamEngineMap_v0105.py run | --selftest
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
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_ENG053_ParamEngineMap"
VERSION = "v0105"
RULED_START = "2018-01-01"                                # 操作員 2026-11-22 裁定 · 2026-11-24 再確認


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})\.(?:py|json)$", str(p))
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + VERSION, PRIOR_PATH)
P = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = P
_spec.loader.exec_module(P)
# 別名表照前版原文再宣告一次(字面字典):VDF_SSOTSync 只從家族尾版收割 UNIFIED_ALIAS(自測 ② 核對一字不差)。
UNIFIED_ALIAS = {
    "START_DATE": "time.start_date", "END_DATE": "time.end_date",
    "BATCH_SIZE": "fetch.batch_size", "MAX_RETRIES": "fetch.max_retries",
    "RETRY_DELAY": "fetch.retry_delay_s", "RETRY_DELAY_S": "fetch.retry_delay_s",
    "TIMEOUT": "fetch.timeout_s", "TIMEOUT_S": "fetch.timeout_s",
    "HTTP_TIMEOUT": "fetch.timeout_s", "OUTPUT_DIR": "output.root",
    "OUTPUT_ROOT": "output.root", "CSV_ENCODING": "output.csv_encoding",
    "MARKETS": "markets",
}
# v0104 自測裡寫死 2022-01-01 的兩檢(只認這兩個開頭;其他紅照紅)
PRIOR_STALE = ("① 冊① 冊② 讀尾版", "③ 映射冊照建 · START_DATE 治理裁定 = '2022-01-01'")


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接(v0104 → v0103 → v0102)。"""
    return getattr(P, name)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)
    print(f"=== {STEM} {VERSION} · 薄尾自測(起始日 {RULED_START})===", flush=True)
    books = P.load_books()
    uni = (books.get("unified") or {}).get("time") or {}
    reg = ((books.get("registry") or {}).get("canonical") or {}).get("START_DATE") or {}
    t1, t2 = P.tail_name("unified", ""), P.tail_name("registry", "")
    chk(f"① 冊① 冊② 讀尾版({t1} · {t2})· 統一參數起始日 = 登錄冊裁定 = {RULED_START}(兩冊一致)",
        P._BOOKS["unified"] == t1 and P._BOOKS["registry"] == t2 and uni.get("start_date") == RULED_START
        and reg.get("ruling") == f"'{RULED_START}'", (t1, t2, uni.get("start_date"), reg.get("ruling")))
    chk("② 尾版別名表(字面字典)與前版一字不差 · 13 個同義字照收割", UNIFIED_ALIAS == P.UNIFIED_ALIAS and len(UNIFIED_ALIAS) == 13)
    m = P.build_map()
    sd = (m.get("by_param") or {}).get("START_DATE") or {}
    chk(f"③ 映射冊照建 · START_DATE 治理裁定 = '{RULED_START}' · 冊名寫的是尾版",
        (sd.get("governance") or {}).get("ruling") == f"'{RULED_START}'" and m["books"]["unified"] == t1 and m["books"]["registry"] == t2,
        (sd.get("governance"), m.get("books")))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋 · 網路工具橋在;不碰 TA-Lib;本檔不寫檔",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and "import " + "talib" not in src
        and ".write_text(" not in src.split("def selftest", 1)[0])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prior_rc = P.selftest()
    out = buf.getvalue()
    fails = [ln.strip() for ln in out.splitlines() if "[FAIL]" in ln]
    own = [ln for ln in fails if not any(s in ln for s in PRIOR_STALE)]
    for ln in fails:
        print("   %s %s" % ("[已知 · 前版寫死 2022]" if ln not in own else "[前版紅]", ln[:200]), flush=True)
    inner_pass = re.search(r"VDF_ENG053_ParamEngineMap v0103 本版 \d+/\d+ · PASS", out) is not None
    chk("⑤ 前版 v0104 自測:紅的只有它寫死 2022 的 ① ③;它裡面的 v0103 自測照過", (prior_rc == 0 or (fails and not own)) and inner_pass,
        (prior_rc, own[:3], inner_pass))
    print(f"[計] {STEM} {VERSION} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    return P.main()


if __name__ == "__main__":
    sys.exit(main())

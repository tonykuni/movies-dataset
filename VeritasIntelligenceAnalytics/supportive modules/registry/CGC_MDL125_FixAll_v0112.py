#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL125_FixAll v0112 — 薄尾:清單先行 — 步冊最前面(datahome 之後)加兩步 tw_list(VDF_MDL009 台股個股清單自動更新)· etf_list(VDF_MDL010 主動式台股 ETF 清單自動更新)

操作員令(2026-10-13):「要先確令台股個股清單生成引擎自動更新以及主動式台股ETF清單自動更新生成引擎正常作業  輸出作為其他引擎的輸入  VDF 一鍵啟動」。
根因:一鍵啟動 ②(via-vdffetch → CGC_MDL134 run --only <步清單>)跑的是本步冊,冊上沒有這兩支「擷取第一步 ①②」(2026-10-03 起;
  VDF_FetchSystem 冊每支引擎 needs 009 · 010;VDF_MDL012 族群頁已清單先行),所以問參數頁的矩陣看不到它們、並行道也不先跑它們。
本版:plan() = 前版 18 步 + datahome 之後插 tw_list · etf_list(net · 逾時 600 · argv = 尾版 VDF_MDL009 / VDF_MDL010 `run`;引擎缺 = engine_ok False 誠實);
  其餘步一字不動;前版的 run / main 直接用本版 plan(鏈 / 依賴由 CGC_MDL134 v0102 配:lists 鏈序跑,資料鏈全等 etf_list)。
只增不減 · 誠實三態 · 零觸碰同意閘 · 輔助模組安裝律 · 不改 PATH(紀律宣告沿前版)。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入;本檔零網路,橋只為全樹一致。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
_STEM = "CGC_MDL125_FixAll"
TAG = "v0112"
LIST_STEPS_V0112 = (
    ("tw_list", "VDF_MDL009_TWStockList_v*.py",
     "台股個股清單自動更新(MDL009:TWSE STOCK_DAY_ALL + t187ap03_L · TPEX OpenAPI;驗證 V1–V7;開頭五欄 date / ticker / yf / bbg / name;所有資料庫的開頭)",
     "操作員 2026-10-13:先確令台股個股清單生成引擎自動更新 · 輸出作為其他引擎的輸入(VDF_FetchSystem 冊每支引擎 needs 009)· 清單先行 · 必跑"),
    ("etf_list", "VDF_MDL010_ActiveETFList_v*.py",
     "主動式台股 ETF 清單自動更新(MDL010:t187ap47_L · ENG077 代碼律 / 揭露律;驗證七項;開頭五欄;所有資料庫的開頭)",
     "操作員 2026-10-13:先確令主動式台股 ETF 清單自動更新生成引擎正常作業 · 輸出作為其他引擎的輸入(needs 010)· 清單先行 · 必跑"),
)


def _vnum_v0112(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0112(p) < _vnum_v0112(__file__)), key=_vnum_v0112)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + TAG, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_ORIG_PLAN = PRIOR.plan


def __getattr__(name):
    return getattr(PRIOR, name)


def _list_engine_v0112(pattern: str):
    hits = sorted((VIA / "functional modules" / "VDF").glob(pattern), key=_vnum_v0112)
    return hits[-1] if hits else None


def list_steps() -> list:
    """兩步清單先行(引擎尾版 glob;缺 = engine_ok False,照實列)。"""
    py = sys.executable
    out = []
    for sid, pat, zh, why in LIST_STEPS_V0112:
        p = _list_engine_v0112(pat)
        out.append({"id": sid, "zh": zh, "net": True, "to": 600, "argv": [py, str(p), "run"] if p else None, "why": why,
                    "engine_ok": bool(p and p.is_file())})
    return out


def plan() -> list:
    """前版步冊 + datahome 之後插 tw_list · etf_list;其餘一字不動。"""
    steps = list(_ORIG_PLAN())
    i = next((k + 1 for k, s in enumerate(steps) if s.get("id") == "datahome"), 0)
    return steps[:i] + list_steps() + steps[i:]


PRIOR.plan = plan          # 前版 run() / main() 的步冊走本版(自測前版時換回)


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    print(f"=== {_STEM} {TAG} · 薄尾自測(清單先行:tw_list · etf_list 入步冊)===")
    P = plan()
    ids = [s["id"] for s in P]
    old = [s["id"] for s in _ORIG_PLAN()]
    chk("① 步冊 = 前版 18 步 + datahome 之後 tw_list · etf_list(共 20;其餘順序一字不動)",
        len(P) == len(old) + 2 and ids[:3] == ["datahome", "tw_list", "etf_list"] and [x for x in ids if x not in ("tw_list", "etf_list")] == old, ids[:5])
    t, e = P[1], P[2]
    chk("② 兩步:net · 逾時 600 · argv = python + 尾版引擎 + run · 引擎在位(VDF_MDL009 / VDF_MDL010 尾版 glob)",
        all(s["net"] and s["to"] == 600 and s["engine_ok"] and s["argv"][-1] == "run" for s in (t, e))
        and Path(t["argv"][1]).name.startswith("VDF_MDL009_TWStockList_v") and Path(e["argv"][1]).name.startswith("VDF_MDL010_ActiveETFList_v"),
        (Path(t["argv"][1]).name if t["argv"] else None, Path(e["argv"][1]).name if e["argv"] else None))
    chk("③ 前版 run / main 走本版步冊(PRIOR.plan 已換)· 兩步的 why 寫明操作員令與清單先行", PRIOR.plan is plan and all("清單先行" in s["why"] and "2026-10-13" in s["why"] for s in (t, e)))
    keep = os.environ.get("VIA_CTRLC_IMMUNE"), os.environ.get("VIA_FRED_PROMPT")
    os.environ["VIA_CTRLC_IMMUNE"] = "0"
    os.environ["VIA_FRED_PROMPT"] = "0"
    try:
        rc = PRIOR.run(dry=True, do_print=False)
        import json
        last = sorted(PRIOR.REP.glob("FIXALL_*.json"))[-1]
        d = json.loads(last.read_text(encoding="utf-8"))
        got = [s["id"] for s in d["steps"]]
        chk("④ DRY 全鏈經前版 run:20 步零執行(全 SKIP/DRY)· tw_list · etf_list 在 datahome 之後",
            rc == 0 and d["dry"] and len(d["steps"]) == 20 and all(s["state"] == "SKIP" for s in d["steps"]) and got[:3] == ["datahome", "tw_list", "etf_list"], (rc, got[:4]))
    finally:
        for k, v in (("VIA_CTRLC_IMMUNE", keep[0]), ("VIA_FRED_PROMPT", keep[1])):
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 檔頭:加速器橋 · 網路橋在(__future__ 之後)· 不碰 TA-Lib · 不代設同意閘 · 不直派子行程 · 紀律宣告",
        "[VIA:ACCEL-BRIDGE:" in body and "[VIA:NET-BRIDGE:" in body and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:")
        and "import " + "talib" not in body and 'environ["VIA_NET_' + 'CONSENT"] = "' not in body and "import " + "subprocess" not in body
        and all(k in body for k in ("只增不減", "誠實三態", "零觸碰")))
    print("  ── 前版自測(用它自己的步冊;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    PRIOR.plan = _ORIG_PLAN
    try:
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    finally:
        PRIOR.plan = plan
    chk(f"⑥ 前版 {PRIOR_PATH.stem} 自測 rc 0", prc == 0)
    print(f"  [計] {_STEM} {TAG} 薄尾 {6 - len(fails)}/6 · {'PASS' if not fails else 'FAIL'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

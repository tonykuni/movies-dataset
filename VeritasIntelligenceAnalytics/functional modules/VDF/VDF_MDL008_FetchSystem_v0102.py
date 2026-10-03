#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL008_FetchSystem v0102 — 薄尾:擷取冊 v0102(第一步 MDL009 改指 v0101:年區代碼中英文名稱局部識別,真股票不刪)

操作員 2026-10-03:「要經過中英文名稱進行局部識別核對 不可刪」「將這幾家有股票的代碼中英文名稱寫入程式識別 沒幾家」。
  ① 冊 VDF_FetchSystem_SSOT_v0102.json:MDL009 → VDF_MDL009_TWStockList_v0101.py(其餘 34 支與 v0101 相同)。
  ② 子行程從本版起(否則子行程回到 v0101 讀舊冊);只在 run 這一次呼叫內把 v0101 的 __file__ 指向本版,呼叫完還原。
  ③ fixture 樣本網在 STOCK_DAY_ALL / t187ap03_L 補兩家擋區真股票(2027 大成鋼 · 2030 彰源,官方中英文簡稱),
     整合測試量得到「不刪」;其他路由一字不動。
v0101 的入口(VDF 管理員總控 / VCGC)· 三種網路模式 · 子行程真模組 · 單引擎監控 · 資料庫層全部照用。不碰 TA-Lib;不讀寫同意閘。
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
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0102(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0102(p) < _vnum_v0102(__file__)), key=_vnum_v0102)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.PRIOR                                     # v0100 本體


def __getattr__(name):
    return getattr(PRIOR, name)


BOOK_V0102 = HERE / "VDF_FetchSystem_SSOT_v0102.json"
_RUN_V0101 = PRIOR.run_v0101
_FIX_ROUTE_V0101 = PRIOR.fix_route_v0101
_TAG_V0101 = PRIOR.TAG
# 擋區真股票(官方 t187ap03_L 2026-08-05 快照的中英文簡稱;核對規則在 MDL009 v0101,本支只供樣本)
FIX_YEAR_ZONE_V0102 = [("2027", "大成鋼", "大成不銹鋼工業股份有限公司", "TC"), ("2030", "彰源", "彰源企業股份有限公司", "FROCH")]


def load_book_v0102(path: Path = BOOK_V0102) -> dict:
    return PRIOR._LOAD_BOOK_V0100(path)


def fix_route_v0102(url: str):
    """v0101 樣本網照回;只在全市場行情與上市公司基本資料兩條路由尾端補擋區兩家(複製第一列的欄形,換代碼與名稱)。"""
    got = _FIX_ROUTE_V0101(url)
    u = str(url).lower()
    if not isinstance(got, list) or not got:
        return got
    if "openapi.twse.com.tw" in u and "stock_day_all" in u:
        return got + [dict(got[0], Code=c, Name=n, 證券代號=c, 證券名稱=n) for c, n, _f, _e in FIX_YEAR_ZONE_V0102]
    if "t187ap03_l" in u:
        return got + [dict(got[0], 公司代號=c, 公司簡稱=n, 公司名稱=f, 英文簡稱=e) for c, n, f, e in FIX_YEAR_ZONE_V0102]
    return got


@contextlib.contextmanager
def _children_from_v0102():
    """v0101 起子行程用的是它自己的 __file__;這一次呼叫內指向本版(子行程才會讀冊 v0102),結束還原。"""
    keep = PRIOR.__dict__.get("__file__")
    PRIOR.__dict__["__file__"] = str(Path(__file__).resolve())
    try:
        yield
    finally:
        PRIOR.__dict__["__file__"] = keep


def run_v0102(*args, **kwargs):
    with _children_from_v0102():
        return _RUN_V0101(*args, **kwargs)


def _install_v0102() -> None:
    PRIOR.load_book_v0101, PRIOR.BOOK_V0101, PRIOR.TAG = load_book_v0102, BOOK_V0102, TAG
    PRIOR.run_v0101, PRIOR.fix_route_v0101 = run_v0102, fix_route_v0102
    BASE.load_book, BASE.run, BASE._fix_route = load_book_v0102, run_v0102, fix_route_v0102


_install_v0102()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    PRIOR.fix_route_v0101, PRIOR.TAG = _FIX_ROUTE_V0101, _TAG_V0101   # v0101 自測比的是它自己的樣本網(冊照用 v0102,AST 定位一起驗)
    try:
        rc0 = PRIOR.selftest()
    finally:
        _install_v0102()                               # v0101 自測結尾會重裝它自己那一套;本版再蓋回
    print(f"=== {TAG} · 薄尾自測(冊 v0102 · MDL009 v0101 年區代碼不刪 · 子行程從本版起)===")
    chk("① v0101 自測過(入口 · 冊 AST 定位 · fixture · 橋;冊已是 v0102)", rc0 == 0, f"rc {rc0}")
    book = load_book_v0102()
    e9 = next(r for r in book["engines"] if r["id"] == "009")
    chk("② 冊 v0102:MDL009 → v0101 · 檔在 · 其餘 34 支與冊 v0101 相同", e9["file"] == "VDF_MDL009_TWStockList_v0101.py" and (HERE / e9["file"]).is_file()
        and [r for r in book["engines"] if r["id"] != "009"] == [r for r in PRIOR._LOAD_BOOK_V0100(HERE / "VDF_FetchSystem_SSOT_v0101.json")["engines"] if r["id"] != "009"])
    fx = fix_route_v0102("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL")
    fb = fix_route_v0102("https://openapi.twse.com.tw/v1/opendata/t187ap03_L")
    chk("③ fixture 補擋區兩家(行情 + 基本資料中英文簡稱);其他路由照 v0101",
        {"2027", "2030"} <= {r["Code"] for r in fx} and {("2027", "TC"), ("2030", "FROCH")} <= {(r["公司代號"], r["英文簡稱"]) for r in fb}
        and fix_route_v0102("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes") == _FIX_ROUTE_V0101("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"))
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "dict"
        keep = PRIOR.__dict__.get("__file__")
        res = run_v0102([e9], "fixture", home, logs=Path(tmp) / "_logs", timeout=600)
        log = Path(res[0]["log"]).read_text(encoding="utf-8") if res and Path(res[0]["log"]).is_file() else ""
        rows = []
        try:
            import pandas as pd
            p = home / "0-1-TWStockList" / "tw_stock_list_latest.parquet"
            rows = pd.read_parquet(p).fillna("").to_dict("records") if p.is_file() else []
        except ImportError:
            pass
        zone = {r["ticker"]: r.get("id_check") for r in rows if r["ticker"] in ("2027", "2030")}
        chk("④ 子行程從本版起:MDL009 v0101 fixture rc0 · 2027 大成鋼 / 2030 彰源中英文核對後留在清單 · 呼叫後 __file__ 還原",
            res and res[0]["rc"] == 0 and "VDF_MDL009_TWStockList_v0101.py" in log and zone == {"2027": "ZH+EN", "2030": "ZH+EN"}
            and PRIOR.__dict__.get("__file__") == keep, (res and res[0]["rc"], zone))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · v0101 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())

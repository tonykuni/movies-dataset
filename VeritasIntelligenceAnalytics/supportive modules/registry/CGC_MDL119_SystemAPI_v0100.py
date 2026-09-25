#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL119_SystemAPI v0100 — 標準系統 U/I 後端聚合層(批332;操作員令「收官」)
====================================================================
操作員令:「將 VIA VAP VDF(首頁要附上所有擷取資料)ACTIVE TAIWAN STOCK
ETF CLASSIFICATION AND ROTATION MONTHLY REVENUE 這幾個主體統整成
標準系統 U/I 前後端相連 收官」。
職權:六主體之「後端真值」單一聚合處(零網路;全讀在庫/存證):
  home     首頁=所有擷取資料盤點(兩庫全表列數/日期域+ETF 庫+共識增益庫
           +OmniFetch 15 車道→落表在位+引擎存證五冊尾件)
  vdf      資料鍛造現況(價/還原/籌碼/當沖/名冊 尾日+尾端不完整交易日守衛)
  vap      自動繪圖(VAP_ENG013 尾版 族群/月營收/ETF 冊+繪圖資料律稽核尾件
           +Seaborn 圖組存證)
  etf      主動台股 ETF 分類(冊×持股×產業歸類×共識 upside;ENG068 尾件)
  rotation 族群分類×輪動(ENG070 GROUP/STORY/ROTATION+ENG071 回測+ENG072 缺口冊)
  revenue  月營收(tw_monthly_revenue 尾月榜+產業彙總+ENG069 月營收×共識四象限)
律:①庫=read_only 短連線(讓庫律;鎖=BUSY 誠實不假綠)②每主體
自帶 state OK/FAIL/SKIP+lane 來源標③尾版/尾件 glob+mtime 動態解析
零寫死④零發明:缺=誠實空+reason。
供應:MDL095 DeckServer 尾版 /api/<name> in-process 呼本模組;
MDL120 SystemUI 產頁時嵌 all() 快照(離線=SNAPSHOT 誠實態)。
用法:python3 CGC_MDL119_SystemAPI_v0100.py [home|vdf|vap|etf|rotation|revenue|all] | --selftest
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
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "functional modules" / "VDF" / "output_hub"
DB_TW = OUT / "mega" / "vdf_tw_market.duckdb"
DB_GL = OUT / "mega" / "vdf_global_market.duckdb"
DB_ETF = OUT / "active_tw_etf" / "active_tw_etf_holdings" / "ActiveTWETF.duckdb"
REP = VIA / "VIA_Reports"
UI = VIA / "supportive modules" / "ui_support"
VDF_ENG = VIA / "functional modules" / "VDF" / "engine"
VAP_ENG = VIA / "functional modules" / "VAP" / "engine"
API_VERSION = "v0100"

# 主體冊(單一 SSOT;U/I 左欄導航+/api 路由皆自此)
SUBJECTS = [
    ("home", "VIA 首頁", "ALL FETCHED DATA", "所有擷取資料盤點"),
    ("vdf", "資料鍛造", "VDF · DATA FORGE", "擷取 · 入庫 · 尾日守衛"),
    ("vap", "自動繪圖", "VAP · AUTO PLOT", "族群 · 月營收 · 繪圖資料律"),
    ("etf", "主動台股 ETF", "ACTIVE TW ETF CLASSIFICATION", "冊 × 持股 × 產業 × 共識"),
    ("rotation", "族群分類×輪動", "CLASSIFICATION & ROTATION", "分類 · 輪動 · 回測 · 缺口"),
    ("revenue", "月營收", "MONTHLY REVENUE", "尾月榜 · 產業 · 共識四象限"),
]

# 落表→來源引擎(靜態對照=首頁「擷取來源」欄;OmniFetch 車道另由源碼動態解析)
TABLE_SOURCE = {
    "tw_daily_prices": "ENG054 TWDailyBackfill(Yahoo 日更增量)",
    "tw_prices_adj": "ENG064 HistoryBackfill(還原價;ENG056 派生)",
    "prices_canonical": "ENG056 Canonical(正準價)",
    "features_daily": "ENG056 --derive(特徵)",
    "tw_chip_inst": "ENG064 籌碼(三大法人)",
    "tw_chip_margin": "ENG064 籌碼(融資融券)",
    "tw_listings": "ENG054/ENG055 L1 名冊",
    "tw_monthly_revenue": "ENG063 MonthlyRevenue(MOPS)",
    "monthly_revenue_analysis": "ENG063 --groups 派生",
    "consensus_daily": "VRN_ENG071 CnyesFusion(FactSet 共識)",
    "consensus_latest": "VRN_ENG071 CnyesFusion(尾值)",
    "global_daily": "ENG066 GlobalUniverse / ENG055 L6",
    "gl_prices_adj": "ENG056 全球還原價",
}


class DbBusy(RuntimeError):
    pass


def _q(db: Path, sql: str, args=()) -> list:
    """唯讀短連線(讓庫律):開→查→關;鎖=DbBusy 誠實"""
    import duckdb
    if not db.exists():
        raise FileNotFoundError(str(db))
    try:
        con = duckdb.connect(str(db), read_only=True)
    except Exception as exc:
        s = str(exc)
        if "lock" in s.lower() or "being used" in s or "Conflicting" in s:
            raise DbBusy(s[:160]) from exc
        raise
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


def _newest(dirp: Path, pat: str) -> Path | None:
    hits = sorted(dirp.glob(pat), key=lambda p: p.stat().st_mtime)
    return hits[-1] if hits else None


def _load(dirp: Path, pat: str):
    p = _newest(dirp, pat)
    if not p:
        return None, ""
    try:
        return json.loads(p.read_text(encoding="utf-8")), p.name
    except Exception:
        return None, p.name


def _mod(dirp: Path, pat: str):
    p = sorted(dirp.glob(pat))[-1]
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[p.stem] = m
    spec.loader.exec_module(m)
    return m


def _ts(p: Path) -> str:
    return datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


def _wrap(fn):
    """主體外殼:誠實三態(OK/FAIL/BUSY)+耗時"""
    t0 = datetime.now()
    try:
        d = fn()
        d.setdefault("state", "OK")
    except DbBusy as exc:
        d = {"state": "BUSY", "reason": f"庫鎖(讓庫律;稍候重試):{exc}"}
    except Exception as exc:
        d = {"state": "FAIL", "reason": f"{type(exc).__name__}: {str(exc)[:200]}"}
    d["ms"] = int((datetime.now() - t0).total_seconds() * 1000)
    d["api"] = API_VERSION
    return d


# ---------------------------------------------------------------- home
_DATE_COLS = ("date", "asof", "trade_date", "ym", "portfolio_date", "holding_date",
              "published", "snapshot_at", "run_at", "as_of")


def _tables(db: Path, label: str) -> dict:
    out = {"label": label, "path": str(db.relative_to(VIA)) if db.exists() else str(db),
           "exists": db.exists(), "tables": [], "rows": 0}
    if not db.exists():
        out["state"] = "SKIP"
        out["reason"] = "庫檔缺(工作站 via-pipeline 產)"
        return out
    out["mb"] = round(db.stat().st_size / 1048576, 1)
    out["ts"] = _ts(db)
    names = [r[0] for r in _q(db, "select table_name from information_schema.tables "
                                  "where table_schema='main' order by 1")]
    for t in names:
        cols = [c[0] for c in _q(db, f'describe "{t}"')]
        n = _q(db, f'select count(*) from "{t}"')[0][0]
        dc = next((c for c in _DATE_COLS if c in cols), "")
        lo = hi = ""
        if dc and n:
            r = _q(db, f'select min("{dc}"), max("{dc}") from "{t}"')[0]
            lo, hi = str(r[0])[:10], str(r[1])[:10]
        out["tables"].append({"table": t, "rows": int(n), "ncols": len(cols),
                              "dcol": dc, "min": lo, "max": hi,
                              "source": TABLE_SOURCE.get(t, "")})
        out["rows"] += int(n)
    out["state"] = "OK"
    return out


def omnifetch_lanes() -> list:
    """OmniFetch 尾版源碼動態解析:車道→落表(零寫死;新車道自動入冊)"""
    p = _newest(VDF_ENG, "VDF_ENG055_OmniFetch_v*.py")
    if not p:
        return []
    src = p.read_text(encoding="utf-8")
    m = re.search(r"^LANES\s*=\s*\{(.*?)\}\s*$", src, re.S | re.M)
    lanes = []
    if m:
        for lid, name, fn in re.findall(r'"(L\d+)":\s*\("(\w+)",\s*(lane_\w+)\)', m.group(1)):
            body = re.search(r"def " + fn + r"\(.*?(?=\ndef |\nLANES)", src, re.S)
            tabs = []
            if body:
                for dbv, tab in re.findall(r'upsert\((DB_\w+),\s*"(\w+)"', body.group(0)):
                    if (dbv, tab) not in tabs:
                        tabs.append((dbv, tab))
            lanes.append({"id": lid, "name": name, "tables": tabs})
    return lanes


def home() -> dict:
    d = {"subject": "home", "engine_src": "", "dbs": [], "lanes": [], "evidence": []}
    d["dbs"].append(_tables(DB_TW, "台股單庫 vdf_tw_market"))
    d["dbs"].append(_tables(DB_GL, "全球單庫 vdf_global_market"))
    d["dbs"].append(_tables(DB_ETF, "主動 ETF 持股庫 ActiveTWETF"))
    cons = _newest(OUT / "candidates" / "vetf_consensus", "asof=*/*.duckdb")
    if cons:
        d["dbs"].append(_tables(cons, f"持股×共識增益庫({cons.parent.name})"))
    present = {}
    for db in d["dbs"]:
        for t in db.get("tables", []):
            present[t["table"]] = t["rows"]
    lanes = omnifetch_lanes()
    for ln in lanes:
        ln["tables"] = [{"db": dbv, "table": tab, "present": tab in present,
                         "rows": present.get(tab, 0)} for dbv, tab in ln["tables"]]
        ln["state"] = ("OK" if ln["tables"] and all(t["present"] for t in ln["tables"])
                       else ("PART" if any(t["present"] for t in ln["tables"]) else "SKIP"))
    d["lanes"] = lanes
    d["engine_src"] = (_newest(VDF_ENG, "VDF_ENG055_OmniFetch_v*.py") or Path("")).name
    for name, sub, pat in (("主動 ETF×共識分析(ENG068)", "etf_consensus_analysis", "ETF_CONSENSUS_*.json"),
                           ("月營收×共識(ENG069)", "revenue_consensus", "REV_CONSENSUS_*.json"),
                           ("族群分類(ENG070)", "group_class", "GROUP_CLASS_*.json"),
                           ("故事族群分類(ENG070)", "group_class", "STORY_CLASS_*.json"),
                           ("輪動關聯(ENG070)", "group_class", "ROTATION_*.json"),
                           ("族群回測(ENG071)", "group_class", "BACKTEST_*.json"),
                           ("故事輪動橋接缺口冊(ENG072)", "story_rotation", "GAP_*.json"),
                           ("繪圖資料律稽核(MDL118)", "plot_law", "PLOT_LAW_AUDIT_*.json"),
                           ("加速器覆蓋(MDL117)", "accel_coverage", "ACCEL_COVERAGE_*.json"),
                           ("Seaborn 圖組(ENG015)", "vap_stack", "stack_*.json")):
        dp = REP / sub
        p = _newest(dp, pat) if dp.exists() else None
        d["evidence"].append({"name": name, "dir": f"VIA_Reports/{sub}", "pattern": pat,
                              "latest": p.name if p else "", "ts": _ts(p) if p else "",
                              "count": len(list(dp.glob(pat))) if dp.exists() else 0,
                              "state": "OK" if p else "SKIP"})
    d["totals"] = {"dbs": sum(1 for x in d["dbs"] if x.get("exists")),
                   "tables": sum(len(x.get("tables", [])) for x in d["dbs"]),
                   "rows": sum(x.get("rows", 0) for x in d["dbs"]),
                   "lanes": len(lanes),
                   "lanes_ok": sum(1 for x in lanes if x["state"] == "OK"),
                   "evidence_ok": sum(1 for x in d["evidence"] if x["state"] == "OK")}
    try:
        atlas = _mod(HERE, "CGC_MDL112_SystemAtlas_v0*.py").gather()
        d["atlas"] = {k: (len(v) if isinstance(v, (list, dict)) else v)
                      for k, v in atlas.items()}
    except Exception as exc:
        d["atlas"] = {"err": str(exc)[:120]}
    return d


# ---------------------------------------------------------------- vdf
def vdf() -> dict:
    d = {"subject": "vdf", "lane": "庫直讀(read_only 短連線)"}
    (last,) = _q(DB_TW, "select max(date) from tw_daily_prices")[0]
    d["last_date"] = str(last)[:10]
    rows = _q(DB_TW, "select date, count(*) from tw_daily_prices "
                     "where cast(date as date) >= (select max(cast(date as date)) from tw_daily_prices) - interval 90 day "
                     "group by 1 order by 1")
    cnts = [int(r[1]) for r in rows]
    med = sorted(cnts)[len(cnts) // 2] if cnts else 0
    d["tail_sessions"] = [{"date": str(r[0])[:10], "n": int(r[1]),
                           "partial": bool(med) and int(r[1]) < 0.8 * med}
                          for r in rows[-8:]]
    d["median_n_60"] = med
    d["partial_guard"] = "尾端不完整交易日(<0.8×近 60 日中位標的數)=分析引擎自動截去(批326 律)"
    d["counts"] = {}
    for key, sql in (("tickers_daily", "select count(distinct ticker) from tw_daily_prices"),
                     ("tickers_adj", "select count(distinct ticker) from tw_prices_adj"),
                     ("listings", "select count(*) from tw_listings"),
                     ("listings_twse", "select count(*) from tw_listings where market='TWSE'"),
                     ("listings_tpex", "select count(*) from tw_listings where market='TPEX'")):
        try:
            d["counts"][key] = int(_q(DB_TW, sql)[0][0])
        except DbBusy:
            raise
        except Exception:
            d["counts"][key] = None
    d["ranges"] = {}
    for t in ("tw_daily_prices", "tw_prices_adj", "tw_chip_inst", "tw_chip_margin",
              "tw_daytrade_market", "tw_daytrade_stock", "tw_monthly_revenue",
              "tw_trading_daily", "tw_valuation_daily", "consensus_daily"):
        try:
            dc = "ym" if t == "tw_monthly_revenue" else "date"
            r = _q(DB_TW, f'select min("{dc}"), max("{dc}"), count(*) from "{t}"')[0]
            d["ranges"][t] = {"min": str(r[0])[:10], "max": str(r[1])[:10], "rows": int(r[2]),
                              "state": "OK" if r[2] else "SKIP"}
        except DbBusy:
            raise
        except Exception as exc:
            d["ranges"][t] = {"min": "", "max": "", "rows": 0, "state": "SKIP",
                              "reason": f"表缺({type(exc).__name__})"}
    try:
        r = _q(DB_GL, "select count(distinct ticker), min(date), max(date) from global_daily")[0]
        d["global"] = {"tickers": int(r[0]), "min": str(r[1])[:10], "max": str(r[2])[:10], "state": "OK"}
    except Exception as exc:
        d["global"] = {"state": "SKIP", "reason": str(exc)[:100]}
    d["engines"] = [p.name for p in
                    (_newest(VDF_ENG, pat) for pat in
                     ("VDF_ENG054_TWDailyBackfill_v*.py", "VDF_ENG055_OmniFetch_v*.py",
                      "VDF_ENG064_HistoryBackfill_v*.py", "VDF_ENG063_MonthlyRevenue_v*.py",
                      "VDF_ENG066_GlobalUniverse_v*.py")) if p]
    d["pages"] = [("VDF 現況台(統一殼)", "VIA_UI_Shell_VDF_v0100.html"),
                  ("資料庫目錄", "VIA_UI_DataCatalog_v0100.html"),
                  ("全球市場觀測", "VIA_UI_GlobalMarkets_v0100.html")]
    return d


# ---------------------------------------------------------------- vap
def _vap_mod():
    return _mod(VAP_ENG, "VAP_ENG013_MarketAnalytics_v0*.py")


def vap() -> dict:
    d = {"subject": "vap"}
    m = _vap_mod()
    d["engine"] = Path(m.__file__).name
    g = m.group_analysis(top=15)
    d["groups"] = {"lane": g.get("lane", ""), "date": g.get("date", ""),
                   "prev": g.get("prev", ""), "total": g.get("total_groups", 0),
                   "rows": g.get("groups", [])[:15]}
    r = m.revenue_analysis(top=12)
    d["revenue"] = {"lane": r.get("lane", ""), "ym": r.get("ym", ""),
                    "top_yoy": r.get("top_yoy", [])[:12]}
    e = m.etf_list(limit=60)
    d["etf"] = {"lane_book": e.get("lane_book", ""), "lane_hold": e.get("lane_hold", ""),
                "n_book": e.get("n_book", 0), "n_holdable": e.get("n_holdable", 0)}
    law, lf = _load(REP / "plot_law", "PLOT_LAW_AUDIT_*.json")
    d["plot_law"] = ({"file": lf, "ts": law.get("ts", ""), "n_ok": law.get("n_ok"),
                      "n_fail": law.get("n_fail"), "n_legacy": law.get("n_legacy"),
                      "rows": [{"engine": x.get("engine"), "state": x.get("state"),
                                "note": x.get("note", "")} for x in law.get("rows", [])],
                      "sample": law.get("sample_2330_coverage", {}), "state": "OK"}
                     if law else {"state": "SKIP", "reason": "尚無稽核件(via-plotlaw)"})
    vs = REP / "vap_stack"
    d["vap_stack"] = {"state": "OK" if vs.exists() else "SKIP",
                      "files": sorted(p.name for p in vs.glob("stack_*.json")) if vs.exists() else [],
                      "ts": _ts(_newest(vs, "stack_*.json")) if vs.exists() and _newest(vs, "stack_*.json") else ""}
    d["bridge_endpoints"] = ["/vap_kline?code=&months=", "/vap_flows?code=&days=",
                             "/vap_check?codes=", "/vap_etf?ids=", "/vap_groups",
                             "/vap_revenue", "/vap_etflist"]
    d["pages"] = [("VAP 現況台(統一殼)", "VIA_UI_Shell_VAP_v0100.html"),
                  ("VAP 分析台 VapDeck(尾版)", (_newest(UI, "VIA_UI_VapDeck_v0*.html") or Path("VIA_UI_VapDeck_v0100.html")).name),
                  ("Seaborn 圖組 VapStack", "VIA_UI_VapStack_v0100.html"),
                  ("標準儀表板", "VIA_UI_StdDashboard_v0100.html")]
    return d


# ---------------------------------------------------------------- etf
def etf() -> dict:
    d = {"subject": "etf"}
    m = _vap_mod()
    e = m.etf_list(limit=80)
    d["book"] = {"lane_book": e.get("lane_book", ""), "lane_hold": e.get("lane_hold", ""),
                 "n_book": e.get("n_book", 0), "n_holdable": e.get("n_holdable", 0),
                 "etfs": e.get("etfs", [])}
    # 產業歸類:最新 portfolio_date 持股 × tw_listings_industry(industry_name)
    d["classification"] = {"state": "SKIP", "reason": "ActiveTWETF 庫缺"}
    if DB_ETF.exists():
        try:
            ind = {r[0]: (r[1] or "") for r in _q(DB_TW, "select code, max(industry_name) from tw_listings_industry group by 1")}
        except Exception:
            ind = {}
        rows = _q(DB_ETF, """
            select h.etf_ticker, max(h.etf_name), h.holding_ticker, max(h.holding_name),
                   max(h.weight_pct), max(h.portfolio_date)
            from holdings_daily h
            join (select etf_ticker, max(portfolio_date) pd from holdings_daily group by 1) l
              on l.etf_ticker = h.etf_ticker and l.pd = h.portfolio_date
            group by 1,3 order by 1, 5 desc""")
        per: dict = {}
        agg: dict = {}
        for etfc, name, hc, hn, w, pd in rows:
            code = str(hc).split(".")[0]
            sec = ind.get(code) or "未歸類"
            w = float(w or 0)
            p = per.setdefault(etfc, {"etf": etfc, "name": name, "date": str(pd)[:10],
                                      "n": 0, "w_sum": 0.0, "sectors": {}, "top": []})
            p["n"] += 1
            p["w_sum"] += w
            p["sectors"][sec] = p["sectors"].get(sec, 0.0) + w
            if len(p["top"]) < 5:
                p["top"].append([code, hn, round(w, 2)])
            a = agg.setdefault(sec, {"sector": sec, "w_sum": 0.0, "etfs": set(), "codes": set()})
            a["w_sum"] += w
            a["etfs"].add(etfc)
            a["codes"].add(code)
        n_etf = len(per)
        for p in per.values():
            p["w_sum"] = round(p["w_sum"], 2)
            p["sectors"] = sorted(([k, round(v, 2)] for k, v in p["sectors"].items()),
                                  key=lambda x: -x[1])[:6]
            p["top_sector"] = p["sectors"][0][0] if p["sectors"] else ""
        sect = sorted(({"sector": a["sector"], "avg_w": round(a["w_sum"] / n_etf, 2) if n_etf else 0,
                        "n_etfs": len(a["etfs"]), "n_codes": len(a["codes"])}
                       for a in agg.values()), key=lambda x: -x["avg_w"])
        chg = []
        try:
            chg = [{"date": str(r[0])[:10], "type": r[1], "n": int(r[2])} for r in _q(DB_ETF, """
                select portfolio_date, change_type, count(*) from holdings_changes
                where portfolio_date = (select max(portfolio_date) from holdings_changes)
                group by 1,2 order by 3 desc""")]
        except Exception:
            pass
        d["classification"] = {"state": "OK", "n_etfs": n_etf, "n_sectors": len(sect),
                               "lane": "ActiveTWETF holdings_daily × tw_listings_industry",
                               "per_etf": sorted(per.values(), key=lambda x: x["etf"]),
                               "sectors": sect[:20], "changes": chg}
    a, af = _load(REP / "etf_consensus_analysis", "ETF_CONSENSUS_*.json")
    if a:
        d["consensus"] = {"state": "OK", "file": af, "asof": a.get("asof"), "ts": a.get("ts"),
                          "consensus_codes": a.get("consensus_codes"), "n_etfs": a.get("n_etfs"),
                          "etfs": [{k: v for k, v in x.items() if k != "top"} for x in a.get("etfs", [])],
                          "overlap": a.get("overlap", [])[:20]}
    else:
        d["consensus"] = {"state": "SKIP", "reason": "尚無 ENG068 存證(via-analysis)"}
    d["pages"] = [("主動 ETF×共識分析(ENG068)", "VIA_UI_ETFConsensusAnalysis_v0100.html")]
    return d


# ---------------------------------------------------------------- rotation
def rotation() -> dict:
    d = {"subject": "rotation"}
    gc, f1 = _load(REP / "group_class", "GROUP_CLASS_*.json")
    d["group"] = ({"state": "OK", "file": f1, "meta": gc.get("meta", {}),
                   "constitution": gc.get("constitution", {}), "roles": gc.get("roles", {}),
                   "sizes": gc.get("sizes", {}),
                   "top_att": [{"industry": x.get("industry"), "idx_eq": round(float(x.get("idx_eq") or 0), 1),
                                "idx_tier": round(float(x.get("idx_tier") or 0), 1),
                                "idx_att": round(float(x.get("idx_att") or 0), 1),
                                "n": int(x.get("n_members") or 0)} for x in gc.get("top_att", [])[:15]]}
                  if gc else {"state": "SKIP", "reason": "尚無 ENG070 存證(via-pipeline ②b)"})
    sc, f2 = _load(REP / "group_class", "STORY_CLASS_*.json")
    if sc:
        st = [{k: x.get(k) for k in ("story", "n", "n_act", "level", "parent", "pc1", "cohesion_ok",
                                     "cohesion_sig", "p_iu", "q_fdr", "leaders", "same_dir")}
              for x in sc.get("stories", [])]
        d["story"] = {"state": "OK", "file": f2, "roles": sc.get("roles", {}),
                      "n": len(st), "n_sig": sum(1 for x in st if x.get("cohesion_sig")),
                      "stories": sorted(st, key=lambda x: -(x.get("n_act") or 0))[:30]}
    else:
        d["story"] = {"state": "SKIP", "reason": "尚無 STORY_CLASS 存證"}
    ro, f3 = _load(REP / "group_class", "ROTATION_*.json")
    if ro:
        pairs = sorted(ro.get("pairs", []), key=lambda x: (x.get("r") if x.get("r") is not None else 0))
        d["rotation"] = {"state": "OK", "file": f3, "n_days": ro.get("n_days"), "start": ro.get("start"),
                         "n_pairs_tested": ro.get("n_pairs_tested"), "n_edges": len(ro.get("edges", [])),
                         "names": ro.get("names", []), "pairs": pairs[:15],
                         "matrix": ro.get("matrix", {}).get("as", {})}
    else:
        d["rotation"] = {"state": "SKIP", "reason": "尚無 ROTATION 存證"}
    bt, f4 = _load(REP / "group_class", "BACKTEST_*.json")
    if bt:
        res = []
        for g, r in bt.get("results", {}).items():
            s1 = r.get("strategy_S1_att") or {}
            ba = r.get("bench_all_eq") or {}
            res.append({"group": g, "flag": r.get("flag", ""), "n_s1": r.get("n_s1"),
                        "n_days": r.get("n_days"), "ret": s1.get("ret_total"), "cagr": s1.get("cagr"),
                        "sharpe": s1.get("sharpe"), "maxdd": s1.get("maxdd"),
                        "excess": s1.get("excess_total"), "bench_ret": ba.get("ret_total")})
        d["backtest"] = {"state": "OK", "file": f4, "ts": bt.get("ts"), "engine": bt.get("engine"),
                         "classifier": bt.get("classifier"), "risk_free": bt.get("risk_free", {}),
                         "n_groups": bt.get("n_groups"), "n_backtested": bt.get("n_backtested"),
                         "results": sorted(res, key=lambda x: -(x.get("ret") or -9))}
    else:
        d["backtest"] = {"state": "SKIP", "reason": "尚無 ENG071 存證(via-pipeline ③b)"}
    gp, f5 = _load(REP / "story_rotation", "GAP_*.json")
    d["gap"] = ({"state": "OK", "file": f5, "run_state": gp.get("state"), "ts": gp.get("ts"),
                 "package": gp.get("package"), "attribution": gp.get("attribution", []),
                 "gap_book": gp.get("gap_book", []), "latest_run_dir": gp.get("latest_run_dir", "")}
                if gp else {"state": "SKIP", "reason": "尚無 ENG072 缺口冊(via-rotation)"})
    d["pages"] = [("族群分類×價格指數(ENG070)", "VIA_UI_GroupClassIndex_v0100.html"),
                  ("族群回測(ENG071)", "VIA_UI_GroupBacktest_v0100.html"),
                  ("故事族群輪動橋接(ENG072)", "VIA_UI_StoryRotation_v0100.html")]
    return d


# ---------------------------------------------------------------- revenue
def revenue() -> dict:
    d = {"subject": "revenue", "lane": "庫直讀 tw_monthly_revenue/monthly_revenue_analysis × tw_listings_industry"}
    (ym,) = _q(DB_TW, "select max(ym) from tw_monthly_revenue")[0]
    d["latest_ym"] = str(ym)
    d["n_codes"] = int(_q(DB_TW, "select count(distinct code) from tw_monthly_revenue where ym=?", [ym])[0][0])
    d["n_months"] = int(_q(DB_TW, "select count(distinct ym) from tw_monthly_revenue")[0][0])
    d["top_yoy"] = [{"code": r[0], "name": r[1] or "", "industry": r[2] or "", "revenue": float(r[3] or 0),
                     "mom": r[4], "yoy": r[5], "streak": r[6], "high_60m": bool(r[7])}
                    for r in _q(DB_TW, """
        select a.code, max(l.name), max(l.industry_name), max(a.revenue), max(a.mom_pct), max(a.yoy_pct),
               max(a.yoy_streak), max(a.high_60m)
        from monthly_revenue_analysis a left join tw_listings_industry l on l.code = a.code
        where a.ym = ? and a.revenue > 100000 group by 1 order by 6 desc nulls last limit 20""", [ym])]
    prev = str(int(str(ym)) - 100) if len(str(ym)) == 6 else ""
    d["sectors"] = [{"industry": r[0] or "未歸類", "n": int(r[1]), "revenue": float(r[2] or 0),
                     "yoy": (round((float(r[2]) / float(r[3]) - 1) * 100, 1) if r[3] else None)}
                    for r in _q(DB_TW, """
        select l.industry_name, count(distinct a.code), sum(a.revenue), sum(p.revenue)
        from tw_monthly_revenue a
        left join tw_listings_industry l on l.code = a.code
        left join tw_monthly_revenue p on p.code = a.code and p.ym = ?
        where a.ym = ? group by 1 order by 3 desc limit 20""", [prev, ym])]
    rc, rf = _load(REP / "revenue_consensus", "REV_CONSENSUS_*.json")
    d["consensus"] = ({"state": "OK", "file": rf, "ts": rc.get("ts"), "latest_ym": rc.get("latest_ym"),
                       "n_market": rc.get("n_market"), "n_covered": rc.get("n_covered"),
                       "quad": rc.get("quad", {}), "dual": rc.get("dual", [])[:20]}
                      if rc else {"state": "SKIP", "reason": "尚無 ENG069 存證(via-analysis)"})
    d["pages"] = [("月營收×共識分析(ENG069)", "VIA_UI_RevenueConsensusAnalysis_v0100.html")]
    return d


FN = {"home": home, "vdf": vdf, "vap": vap, "etf": etf, "rotation": rotation, "revenue": revenue}


def api(name: str) -> dict:
    if name == "all":
        return all_subjects()
    if name == "subjects":
        return {"state": "OK", "api": API_VERSION,
                "subjects": [{"id": a, "zh": b, "en": c, "sub": e} for a, b, c, e in SUBJECTS]}
    fn = FN.get(name)
    if not fn:
        return {"state": "FAIL", "reason": f"未知主體 {name}(冊:{','.join(FN)})", "api": API_VERSION}
    return _wrap(fn)


def all_subjects() -> dict:
    d = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "api": API_VERSION,
         "subjects": [{"id": a, "zh": b, "en": c, "sub": e} for a, b, c, e in SUBJECTS]}
    for k, fn in FN.items():
        d[k] = _wrap(fn)
    d["state"] = "OK" if all(d[k].get("state") == "OK" for k in FN) else "PART"
    return d


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 六主體冊+API 路由(SUBJECTS=FN 鍵一致)",
        [s[0] for s in SUBJECTS] == list(FN) and len(FN) == 6)
    h = api("home")
    chk("② 首頁=所有擷取資料(庫表列數/日期域+15 車道→落表+存證冊)",
        h.get("state") == "OK" and h["totals"]["tables"] >= 10
        and h["totals"]["lanes"] >= 14 and len(h["evidence"]) >= 8,
        f"(表 {h.get('totals', {}).get('tables')} · 列 {h.get('totals', {}).get('rows')} · 車道 {h.get('totals', {}).get('lanes')})")
    lanes_ok = h.get("totals", {}).get("lanes_ok", 0)
    chk("②b 車道→落表零寫死(源碼動態解析;L12 daytrade→tw_daytrade_market)",
        any(l["id"] == "L12" and any(t["table"] == "tw_daytrade_market" for t in l["tables"])
            for l in h.get("lanes", [])), f"(在位 {lanes_ok})")
    v = api("vdf")
    chk("③ VDF 尾日+尾端不完整守衛+十表域三態", v.get("state") == "OK"
        and len(v.get("tail_sessions", [])) >= 3 and "tw_daytrade_stock" in v.get("ranges", {})
        and v["ranges"]["tw_daytrade_stock"]["state"] in ("OK", "SKIP"),
        f"(尾日 {v.get('last_date')} · 當沖個股 {v.get('ranges', {}).get('tw_daytrade_stock', {}).get('state')})")
    p = api("vap")
    chk("④ VAP(ENG013 尾版族群/月營收/ETF 冊+繪圖律稽核尾件 lane 必標)",
        p.get("state") == "OK" and p["groups"]["rows"] and "lane" in p["groups"]
        and p["plot_law"]["state"] in ("OK", "SKIP"))
    e = api("etf")
    c = e.get("classification", {})
    chk("⑤ 主動 ETF 分類(冊×持股×產業歸類×共識 upside)",
        e.get("state") == "OK" and e["book"]["n_book"] >= 1
        and c.get("state") in ("OK", "SKIP")
        and (c.get("state") != "OK" or (c["n_etfs"] >= 1 and c["sectors"] and c["per_etf"][0]["sectors"])),
        f"(冊 {e.get('book', {}).get('n_book')} · 分類 {c.get('n_etfs')} ETF / {c.get('n_sectors')} 產業 · 共識 {e.get('consensus', {}).get('state')})")
    r = api("rotation")
    chk("⑥ 分類×輪動(GROUP/STORY/ROTATION/BACKTEST/GAP 五件三態)",
        r.get("state") == "OK" and all(r[k]["state"] in ("OK", "SKIP")
                                       for k in ("group", "story", "rotation", "backtest", "gap")),
        "(" + " ".join(f"{k}={r.get(k, {}).get('state')}" for k in ("group", "story", "rotation", "backtest", "gap")) + ")")
    m = api("revenue")
    chk("⑦ 月營收(尾月榜+產業彙總 YoY+ENG069 四象限)",
        m.get("state") == "OK" and m["top_yoy"] and m["sectors"] and m["consensus"]["state"] in ("OK", "SKIP"),
        f"(尾月 {m.get('latest_ym')} · {m.get('n_codes')} 家 · 產業 {len(m.get('sectors', []))})")
    a = all_subjects()
    chk("⑧ all() 快照六主體三態+未知主體誠實 FAIL+紀律宣告",
        all(k in a for k in FN) and api("nope")["state"] == "FAIL"
        and "read_only=True" in src and "ACCEL-BRIDGE" in src and "誠實" in src,
        f"(state={a.get('state')})")
    print(f"  [計] 八檢 OK {8 + 1 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 標準系統 U/I 後端聚合層(CGC_MDL119 v0100)· 八檢自測(零網路)===")
        return selftest()
    name = a[0] if a else "subjects"
    print(json.dumps(api(name), ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

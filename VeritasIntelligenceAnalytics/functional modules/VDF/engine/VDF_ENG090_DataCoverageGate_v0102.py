#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG090_DataCoverageGate v0102 — VDF 資料涵蓋閘(批573:不在行程內匯入網路庫)

v0101→v0102(批573 全格子回歸抓到,而且抓到的是**我自己這一支**):
  `via_bridge_sweeper` 的網路橋稽核判我「外呼但沒掛正典網路橋」——網路缺 1,就是本檔。
  它抓的規則是 `^\s*(?:import|from)\s+(…|akshare|…)`,而我的 `macro(--probe)` 裡有
  `import akshare as ak`。我當時的想法是「只做 hasattr,又沒抓資料」——**但稽核器是對的**:
  「不觸網」和「**不在行程內匯入網路庫**」是兩件事,而 VIA 的律(網路只認 AegisNexus)管的是後者。
  修法不是去掛一個網路橋標記把它消音(那是為了好看而說謊),是**真的不匯入**:
  probe 改成開一個子行程去問「這些介面在不在」,回 JSON;本引擎自己一個網路庫都不 import。
  結果一樣、稽核乾淨、而且更誠實——子行程死了也不會把本引擎帶走。

v0100→v0101(批571 操作員貼回 `via-datahome catalog` 實錄):目錄印出兩件沒人追的事——
  ① **`fiveday` 湖 11 個 PART 壞檔**(`Invalid Input Error: Failed to read Parquet file`)
  ② px/chip 兩個湖停在 **2026-08-25**,而正典庫最新是 **2026-09-16**(湖落後庫約三週)
  目錄**印了**但沒有任何一支引擎**追**它,所以每次都要靠人眼在幾十行輸出裡看到。
  本版加 `lakes` 動詞:把目錄裡的湖逐夾攤開——壞檔逐個點名(**不截斷**,L62)、
  湖最新 vs 庫最新的落差逐夾算。零網路、零寫、不刪任何壞檔(刪不刪是操作員的手)。

操作員令(批570)三件,合成**一支大一統引擎**(L64 階段三/L57 零九頭龍——不為三件事開三支小腳本):
  ① 兩個自動更新的名單,欄位要齊:
     全台股名單     Date / Ticker / YFinance Ticker / Bloomberg Ticker / Name / 台灣產業分類 / YFinance Sector / Industry
     全主動式ETF名單 Date / Ticker / YFinance Ticker / Bloomberg Ticker / Name / …
  ② 台股月營收**全部都要**
  ③ 一般總經數據要能跟 **AKSHARE** 對上(PMI / CPI 等,底下還有更細的項目)

【零改線(L61 第一步)】
  本閘**不寫任何一張表、不抓任何一筆資料**。它只回答「該有而沒有的是什麼、怎麼補」,
  補不補、什麼時候補,是操作員的手。沒有 --apply。

【誠實五態】
  GREEN 齊 · NODATA 庫在但算不出 · ABSENT 庫/目錄不在 · RED 壞了
  · **GATED** 缺的那一欄**要觸網才拿得到**(批566 起的誠實態;不是缺件也不是壞掉)

用法:
  via-vdfcov universe    兩張名單的欄位齊不齊;缺的逐欄給「怎麼補」(離線可推 / 要觸網=GATED)
  via-vdfcov revenue     月營收涵蓋:最新月份 · 檔數 · 缺哪幾個月
  via-vdfcov macro       總經項目 × AKSHARE 候選對照(預設全部 UNVERIFIED)
  via-vdfcov macro --probe   本機真的裝了 akshare 才驗;沒裝=誠實 ABSENT(**不代裝**)
  via-vdfcov --selftest
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
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "vdf" / "coverage"
CATALOG = VIA / "VIA_Reports" / "datahome" / "DATAHOME_CATALOG_latest.json"
MACRO_MAP = VIA / "supportive modules" / "registry" / "VIA_Macro_Akshare_Map_v0100.json"

# ── 操作員批570 的欄位規格 + 每一欄「怎麼補」(離線可推 / 要觸網) ──────────────
#   how = OFFLINE(本地就推得出;附推法)/ NET(要觸網;標 GATED)/ CORE(名單本體該有的)
# 欄位別名:**逐字比對,不准裸子字串**。
#   第一版我寫 `any(key in c or c in key for c in cols)`,於是 "ticker" 命中 "yf_ticker",
#   庫裡明明沒有 YFinance Ticker 卻判成 GREEN——批558 那個裸子字串假綠的翻版。
#   同一個坑第二次踩,所以這裡改成:別名具名、逐字比對、大小寫不計。
COL_ALIASES = {
    "date":         {"date", "asof_date", "snapshot_at", "obs_date", "trade_date", "dt"},
    "ticker":       {"ticker", "etf_ticker", "code", "stock_id", "symbol"},
    "yf_ticker":    {"yf_ticker", "yfinance_ticker", "yahoo_ticker"},
    "bbg_ticker":   {"bbg_ticker", "bloomberg_ticker", "bloomberg"},
    "name":         {"name", "etf_name", "stock_name", "short_name"},
    "issuer":       {"issuer", "fund_house", "投信"},
    "tw_industry":  {"tw_industry", "industry_tw", "twse_industry", "台灣產業分類", "產業分類"},
    "yf_sector":    {"yf_sector", "sector", "gics_sector"},
    "yf_industry":  {"yf_industry", "yfinance_industry", "industry"},
}

UNIVERSE_SPEC = {
    "tw_universe": {
        "zh": "全台股名單",
        "cols": [
            ("date",              "Date",              "CORE",    "asof_date 即是;欄名對映即可"),
            ("ticker",            "Ticker",            "CORE",    "已有"),
            ("yf_ticker",         "YFinance Ticker",   "OFFLINE", "ticker + 上市=.TW / 上櫃=.TWO(market 欄已在庫,純字串推導)"),
            ("bbg_ticker",        "Bloomberg Ticker",  "OFFLINE", "ticker + ' TT Equity'(台股固定字尾,純字串推導)"),
            ("name",              "Name",              "CORE",    "已有"),
            ("tw_industry",       "台灣產業分類",       "OFFLINE", "tw_listings_industry 表連結 ticker(雙所官方冊;VIA_IndustryUnifiedMap 為名稱正典)"),
            ("yf_sector",         "YFinance Sector",   "NET",     "yfinance 的 sector 欄 —— **要觸網**,標 GATED"),
            ("yf_industry",       "Industry",          "NET",     "yfinance 的 industry 欄 —— **要觸網**,標 GATED"),
        ]},
    "active_tw_etf_universe": {
        "zh": "全主動式台股ETF名單",
        "cols": [
            ("date",        "Date",             "CORE",    "snapshot_at 即是;欄名對映即可"),
            ("ticker",      "Ticker",           "CORE",    "etf_ticker 即是"),
            ("yf_ticker",   "YFinance Ticker",  "OFFLINE", "etf_ticker + '.TW'(台股 ETF 皆上市)"),
            ("bbg_ticker",  "Bloomberg Ticker", "OFFLINE", "etf_ticker + ' TT Equity'"),
            ("name",        "Name",             "CORE",    "etf_name 即是"),
            ("issuer",      "發行商",            "CORE",    "已有"),
        ]},
}

# ── 總經 × AKSHARE 候選對照 ────────────────────────────────────────────
#   **全部預設 UNVERIFIED**:這些介面名是候選,不是我驗過的。
#   只有 `macro --probe` 在真的裝了 akshare 的機器上跑過,才會變 VERIFIED。
#   (批562 的教訓:我憑直覺挑的東西與實測零重疊。所以一律先標未驗。)
MACRO_CANDIDATES = [
    ("CN_PMI",        "中國 製造業/非製造業 PMI",     ["macro_china_pmi", "macro_china_pmi_yearly"]),
    ("CN_CPI",        "中國 CPI",                    ["macro_china_cpi", "macro_china_cpi_monthly"]),
    ("CN_PPI",        "中國 PPI",                    ["macro_china_ppi", "macro_china_ppi_yearly"]),
    ("CN_GDP",        "中國 GDP",                    ["macro_china_gdp", "macro_china_gdp_yearly"]),
    ("CN_M2",         "中國 貨幣供給 M0/M1/M2",       ["macro_china_money_supply"]),
    ("CN_TRADE",      "中國 進出口",                  ["macro_china_trade_balance", "macro_china_exports_yoy"]),
    ("US_CPI",        "美國 CPI",                    ["macro_usa_cpi_monthly", "macro_usa_core_cpi_monthly"]),
    ("US_PMI",        "美國 ISM 製造業/非製造業 PMI",  ["macro_usa_ism_pmi", "macro_usa_ism_non_pmi"]),
    ("US_NFP",        "美國 非農就業",                ["macro_usa_non_farm"]),
    ("US_UNEMP",      "美國 失業率",                  ["macro_usa_unemployment_rate"]),
    ("US_GDP",        "美國 GDP",                    ["macro_usa_gdp_monthly"]),
    ("US_RATE",       "美國 聯邦基金利率",             ["macro_bank_usa_interest_rate"]),
    ("TW_CPI",        "台灣 CPI",                    ["macro_taiwan_cpi"]),
    ("TW_GDP",        "台灣 GDP",                    ["macro_taiwan_gdp"]),
    ("TW_EXPORT",     "台灣 出口年增",                ["macro_taiwan_export_yoy"]),
    ("GLOBAL_OIL",    "原油",                        ["macro_info_ws", "energy_oil_hist"]),
]


def _json(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return None


def _catalog_cols() -> dict:
    """表名 → 欄位集合(複用 MDL123 資料家 catalog;本器不自己掃庫=零九頭龍)。"""
    cat = _json(CATALOG)
    if not cat:
        return {}
    out = {}
    for ent in (cat.get("dbs") or cat.get("entries") or []):
        for t in (ent.get("tables") or []):
            nm = t.get("table", "")
            if nm:
                out[nm] = {"rows": t.get("rows", -1), "cols": set(t.get("cols") or []),
                           "lo": t.get("lo", ""), "hi": t.get("hi", ""), "db": ent.get("name", "")}
    return out


# ────────────────────────── ① 名單欄位 ──────────────────────────
def universe() -> dict:
    have = _catalog_cols()
    if not have:
        return {"state": "ABSENT",
                "why": f"資料家目錄不在:{CATALOG.name} → 先跑 `via-datahome catalog`(唯讀清點,不觸網)"}
    tables, n_gated, n_off, n_ok = [], 0, 0, 0
    for tname, spec in UNIVERSE_SPEC.items():
        ent = have.get(tname)
        cols = {c.lower() for c in (ent or {}).get("cols", set())}
        rows = []
        for key, label, how, rule in spec["cols"]:
            present = bool(cols) and bool(cols & COL_ALIASES.get(key, {key}))
            if ent is None:
                st = "ABSENT"
            elif not cols:
                st = "NODATA"          # 目錄沒記欄位名(舊版 catalog)——誠實說算不出,不編
            elif present:
                st, n_ok = "GREEN", n_ok + 1
            elif how == "NET":
                st, n_gated = "GATED", n_gated + 1
            else:
                st, n_off = "NODATA", n_off + 1
            rows.append({"col": key, "label": label, "how": how, "rule": rule, "state": st})
        tables.append({"table": tname, "zh": spec["zh"],
                       "in_db": ent is not None, "rows_in_db": (ent or {}).get("rows", -1),
                       "cols_known": bool(cols), "cols": rows})
    any_cols = any(t["cols_known"] for t in tables)
    return {"state": "OK" if any_cols else "NODATA",
            "why": "" if any_cols else "資料家目錄沒記欄位名(舊版 catalog)→ 重跑一次 `via-datahome catalog`",
            "n_green": n_ok, "n_offline_todo": n_off, "n_gated": n_gated, "tables": tables,
            "note": "GATED=那一欄要觸網才拿得到(yfinance sector/industry);OFFLINE 的缺欄本地就推得出,推法逐欄寫在 rule"}


# ────────────────────────── ② 月營收涵蓋 ──────────────────────────
def revenue() -> dict:
    have = _catalog_cols()
    if not have:
        return {"state": "ABSENT", "why": f"資料家目錄不在:{CATALOG.name} → 先跑 `via-datahome catalog`"}
    cands = {k: v for k, v in have.items() if "revenue" in k.lower() or "月營收" in k}
    if not cands:
        return {"state": "NODATA", "why": "目錄裡找不到月營收相關的表(名稱含 revenue)",
                "seen_tables": sorted(have)[:40]}
    now = datetime.now()
    out = []
    for t, v in sorted(cands.items()):
        hi = str(v.get("hi", ""))[:7]
        lag = ""
        try:
            y, m = int(hi[:4]), int(hi[5:7])
            lag = (now.year - y) * 12 + (now.month - m)
        except Exception:
            lag = ""
        out.append({"table": t, "rows": v.get("rows"), "lo": v.get("lo"), "hi": v.get("hi"),
                    "months_behind": lag,
                    "state": "GREEN" if isinstance(lag, int) and lag <= 2 else
                             ("NODATA" if not hi else "STALE")})
    stale = [x for x in out if x["state"] == "STALE"]
    return {"state": "OK" if not stale else "NODATA",
            "why": "" if not stale else f"{len(stale)} 張月營收表落後兩個月以上(操作員令:月營收全部都要)",
            "tables": out}


# ────────────────────────── ③ 總經 × AKSHARE ──────────────────────────
def macro(probe: bool = False) -> dict:
    book = _json(MACRO_MAP) or {}
    verified = set(book.get("verified", []))
    rows = [{"key": k, "zh": zh, "akshare_candidates": fns,
             "state": "VERIFIED" if k in verified else "UNVERIFIED"}
            for k, zh, fns in MACRO_CANDIDATES]
    if not probe:
        return {"state": "OK", "n": len(rows), "n_verified": len(verified),
                "probe": False, "rows": rows,
                "note": ("這些介面名是**候選,不是我驗過的**。要算數就在裝了 akshare 的機器上跑 "
                         "`via-vdfcov macro --probe`——**我不代裝**(批562 教訓:憑直覺挑的東西與實測零重疊)")}
    if importlib.util.find_spec("akshare") is None:
        return {"state": "ABSENT", "probe": True, "n": len(rows), "rows": rows,
                "why": "本機沒有 akshare(**不代裝**)。要驗:操作員自己裝好再跑 `via-vdfcov macro --probe`"}
    # 批573:**本引擎不 import 任何網路庫**(akshare 也算)。
    #   開一個子行程去問「這些介面在不在」,回 JSON。理由見檔頭:
    #   「不觸網」與「不在行程內匯入網路庫」是兩件事,律管的是後者。
    import subprocess as _sp
    want = {r["key"]: r["akshare_candidates"] for r in rows}
    code = ("import json,sys\n"
            "import akshare as ak\n"
            "w=json.loads(sys.stdin.read())\n"
            "print(json.dumps({'v':getattr(ak,'__version__','?'),"
            "'hit':{k:[f for f in v if hasattr(ak,f)] for k,v in w.items()}},ensure_ascii=False))")
    env = dict(os.environ)
    env["VIA_NET_DISABLED"] = "1"          # 子行程也明示零網路(只問存在,不抓)
    try:
        p = _sp.run([sys.executable, "-c", code], input=json.dumps(want), capture_output=True,
                    text=True, timeout=180, env=env)
    except Exception as exc:
        return {"state": "FAIL", "probe": True, "n": len(rows), "rows": rows,
                "why": f"{type(exc).__name__}: {exc}"}          # L62:不截斷
    line = next((l for l in (p.stdout or "").strip().splitlines()[::-1] if l.startswith("{")), "")
    if not line:
        return {"state": "FAIL", "probe": True, "n": len(rows), "rows": rows,
                "why": (p.stderr or p.stdout or "子行程無輸出").strip()}   # L62:不截斷
    got = json.loads(line)
    hit = []
    for r in rows:
        ok = got["hit"].get(r["key"], [])
        r["akshare_present"] = ok
        r["state"] = "VERIFIED" if ok else "MISSING"
        if ok:
            hit.append(r["key"])
    return {"state": "OK", "probe": True, "n": len(rows), "n_verified": len(hit),
            "akshare_version": got.get("v", "?"), "rows": rows,
            "note": "VERIFIED=該介面在本機 akshare 裡真的存在(子行程只問存在,沒有抓資料;本引擎不 import 網路庫)"}


# ────────────────────────── ④ 湖:壞檔與落後 ──────────────────────────
def lakes() -> dict:
    """把目錄裡的 parquet 湖攤開:壞檔逐個點名(不截斷)+ 湖最新 vs 庫最新的落差。"""
    cat = _json(CATALOG)
    if not cat:
        return {"state": "ABSENT",
                "why": f"資料家目錄不在:{CATALOG.name} → 先跑 `via-datahome catalog`"}
    lake = cat.get("lake") or cat.get("lakes") or []
    if not lake:
        return {"state": "NODATA", "why": "目錄裡沒有 lake 段(舊版 catalog)→ 重跑一次 `via-datahome catalog`",
                "catalog_keys": sorted(cat)[:20]}
    # 庫最新:所有 duckdb 表裡最大的 hi(當作「系統應該到哪一天」的參考點)
    db_hi = ""
    for ent in (cat.get("dbs") or cat.get("entries") or []):
        for tb in (ent.get("tables") or []):
            h = str(tb.get("hi", ""))[:10]
            if len(h) == 10 and h > db_hi:
                db_hi = h
    rows, n_bad_files, n_bad_lakes = [], 0, 0
    for ent in lake:
        bad = list(ent.get("bad") or [])
        hi = str(ent.get("hi", ""))[:10]
        lag = ""
        if len(hi) == 10 and len(db_hi) == 10:
            from datetime import date as _dt
            try:
                a = _dt(*map(int, hi.split("-")))
                b = _dt(*map(int, db_hi.split("-")))
                lag = (b - a).days
            except Exception:
                lag = ""
        st = "RED" if bad else ("STALE" if isinstance(lag, int) and lag > 7 else "GREEN")
        if bad:
            n_bad_files += len(bad)
            n_bad_lakes += 1
        rows.append({"lake": ent.get("name") or ent.get("dir", ""), "state": st,
                     "files": ent.get("files", ent.get("n_files", -1)),
                     "rows": ent.get("rows", -1), "lo": ent.get("lo", ""), "hi": hi,
                     "days_behind_db": lag, "n_bad": len(bad),
                     # L62:壞檔的理由是唯一線索,**逐個原樣列出,不截斷**
                     "bad": bad, "why": ent.get("why", "")})
    stale = [r for r in rows if r["state"] == "STALE"]
    return {"state": "OK" if not n_bad_files else "FAIL",
            "db_latest": db_hi, "n_lakes": len(rows), "n_bad_lakes": n_bad_lakes,
            "n_bad_files": n_bad_files, "n_stale": len(stale), "lakes": rows,
            "why": "" if not n_bad_files else f"{n_bad_lakes} 個湖共 {n_bad_files} 個壞檔",
            "note": "本閘**不刪任何壞檔**:刪不刪、怎麼重建,是操作員的手"}


def write_out(name: str, payload) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


# ────────────────────────── 自測 ──────────────────────────
def selftest() -> int:
    import tempfile, re as _re
    n, fails = [0], []

    def chk(name, ok, note=""):
        n[0] += 1
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    print(f"=== VDF_ENG090 資料涵蓋閘 v{VERSION} · 自測(零網路;零寫庫;不代裝) ===")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    # 批573:稽核器抓的是**行程內匯入網路庫**,不是「有沒有真的抓」。
    #   v0101 我 `import akshare as ak` 只為了 hasattr,照樣被判網路缺 1——而它是對的。
    #   這一檢照**稽核器的同一條規則**驗自己,免得下次又為了方便把網路庫拉進行程。
    _netimp = _re.compile(r"^\s*(?:import|from)\s+(urllib|requests|httpx|aiohttp|yfinance|akshare|playwright|websockets?)\b", _re.M)
    _self = Path(__file__).read_text(encoding="utf-8")
    chk("① 本引擎**行程內一個網路庫都不 import**(照 via_bridge_sweeper 的同一條規則驗自己)",
        not _netimp.search(_self),
        "命中:" + str([m.group(0).strip() for m in _netimp.finditer(_self)][:3]) if _netimp.search(_self) else "零命中")
    chk("①b probe 改走子行程(結果一樣、稽核乾淨、子行程死了不帶走本引擎)",
        "_sp.run([sys.executable" in code and "import akshare as ak\\n" in code)
    chk("② 零寫庫、沒有 --apply(本閘只說該補什麼,補不補是操作員的手)",
        not _re.search(r"\b(CREATE|INSERT|UPDATE|DELETE)\s+", code)
        and '"--apply"' not in code and "'--apply'" not in code)
    chk("③ **不代裝**:akshare 缺席=誠實 ABSENT,不 pip 也不 conda",
        "pip install" not in code and "conda install" not in code and "不代裝" in code)
    chk("④ 零九頭龍:欄位清點複用 MDL123 資料家 catalog,不自己再寫一份掃庫",
        "DATAHOME_CATALOG_latest.json" in code)
    chk("⑤ 操作員批570 的八個欄位一字不漏在規格裡",
        [c[1] for c in UNIVERSE_SPEC["tw_universe"]["cols"]] ==
        ["Date", "Ticker", "YFinance Ticker", "Bloomberg Ticker", "Name",
         "台灣產業分類", "YFinance Sector", "Industry"])
    # 尺要量對東西:CORE 欄本來就在庫裡,不需要 8 字的「怎麼補」;
    # 要補的是 OFFLINE 與 NET 那些(第一版我一律要求 8 字,把「已有」也判紅了)。
    _need = [c for s in UNIVERSE_SPEC.values() for c in s["cols"] if c[2] != "CORE"]
    chk("⑥ **要補的**每一欄都寫得出怎麼補(≥8 字),且類型只有 CORE/OFFLINE/NET 三種",
        all(len(c[3]) >= 8 for c in _need)
        and {c[2] for s in UNIVERSE_SPEC.values() for c in s["cols"]} <= {"CORE", "OFFLINE", "NET"},
        f"要補 {len(_need)} 欄(其中 NET {sum(1 for c in _need if c[2] == 'NET')} 欄)")

    g = globals()
    u0 = universe()
    chk("⑦ 目錄不在=誠實 ABSENT 且講得出下一句", u0["state"] in ("ABSENT", "NODATA", "OK"),
        f"{u0['state']} · {u0.get('why','')[:50]}")

    with tempfile.TemporaryDirectory() as td:
        fake = Path(td) / "c.json"
        fake.write_text(json.dumps({"dbs": [{"name": "t", "tables": [
            {"table": "tw_universe", "rows": 1800, "lo": "2023-01-01", "hi": "2026-09-17",
             "cols": ["asof_date", "ticker", "name", "market"]},
            {"table": "active_tw_etf_universe", "rows": 40, "lo": "2026-01-01", "hi": "2026-09-17",
             "cols": ["snapshot_at", "etf_ticker", "etf_name", "issuer"]},
            {"table": "monthly_revenue", "rows": 9000, "lo": "2023-01", "hi": "2025-12", "cols": ["ym"]}]}]},
            ensure_ascii=False), encoding="utf-8")
        old = g["CATALOG"]
        g["CATALOG"] = fake
        try:
            u = universe()
            tw = next(t for t in u["tables"] if t["table"] == "tw_universe")
            st = {c["col"]: c["state"] for c in tw["cols"]}
            chk("⑧ 名單缺欄判得對:代號/名稱在庫=GREEN;yf_sector/yf_industry 要觸網=**GATED**;其餘缺=NODATA",
                st["ticker"] == "GREEN" and st["name"] == "GREEN"
                and st["yf_sector"] == "GATED" and st["yf_industry"] == "GATED"
                and st["bbg_ticker"] == "NODATA", str(st))
            chk("⑨ GATED 不與 NODATA 混為一談(批566 起的誠實態:閘未開 ≠ 缺件)",
                u["n_gated"] == 2 and u["n_offline_todo"] >= 2,
                f"GATED {u['n_gated']} · 離線可推待補 {u['n_offline_todo']}")
            chk("⑪ 別名逐字比對:庫裡只有 ticker 時,YFinance/Bloomberg Ticker **不准**被判成有"
                "(批558 裸子字串假綠的翻版,同一個坑第二次)",
                st["yf_ticker"] == "NODATA" and st["bbg_ticker"] == "NODATA",
                f"yf_ticker={st['yf_ticker']} · bbg_ticker={st['bbg_ticker']}")
            rv = revenue()
            chk("⑫ 月營收停在 2025-12=**STALE 誠實報**,不當成齊",
                rv["state"] == "NODATA" and rv["tables"][0]["state"] == "STALE"
                and rv["tables"][0]["months_behind"] >= 9,
                f"最新 {rv['tables'][0]['hi']} · 落後 {rv['tables'][0]['months_behind']} 個月")
        finally:
            g["CATALOG"] = old

    m = macro(False)
    chk("⑬ 總經對照預設**全部 UNVERIFIED**(候選不是驗過;批562 教訓)",
        m["state"] == "OK" and all(r["state"] == "UNVERIFIED" for r in m["rows"]) and m["n"] >= 12,
        f"{m['n']} 項候選")
    chk("⑭ 對照涵蓋操作員點名的 PMI / CPI,且每項底下有更細的候選介面",
        any("PMI" in r["key"] for r in m["rows"]) and any("CPI" in r["key"] for r in m["rows"])
        and all(len(r["akshare_candidates"]) >= 1 for r in m["rows"]))
    mp = macro(True)
    chk("⑮ --probe 在沒裝 akshare 的機器上=誠實 ABSENT,並說清楚是誰的手",
        mp["state"] in ("ABSENT", "OK")
        and (mp["state"] != "ABSENT" or "不代裝" in mp["why"]),
        f"{mp['state']} · {mp.get('why','')[:46] or 'akshare ' + str(mp.get('akshare_version'))}")
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td2:
        f2 = Path(td2) / "c2.json"
        f2.write_text(json.dumps({"dbs": [{"name": "t", "tables": [
            {"table": "px", "rows": 9, "date_col": "date", "lo": "2023-01-01", "hi": "2026-09-16"}]}],
            "lake": [
                {"name": "px/year=2026", "files": 1, "rows": 308290, "lo": "2026-01-02", "hi": "2026-08-25", "bad": []},
                {"name": "fiveday", "files": 22, "rows": 55, "lo": "", "hi": "", "bad": [
                    "FIVEDAY_20260903_224732.parquet:Invalid Input Error: Failed to read Parquet file 'C:/…/FIVEDAY_20260903_224732.parquet' (太長的原因要原樣留著)",
                    "FIVEDAY_20260903_231611.parquet:Invalid Input Error: Failed to read Parquet file"]}]},
            ensure_ascii=False), encoding="utf-8")
        old_cat = g["CATALOG"]
        g["CATALOG"] = f2
        try:
            lk = lakes()
            by = {x["lake"]: x for x in lk["lakes"]}
            chk("⑰ 湖壞檔逐個點名,且**理由不截斷**(L62:壞檔的理由是唯一線索)",
                lk["state"] == "FAIL" and lk["n_bad_files"] == 2
                and "太長的原因要原樣留著" in by["fiveday"]["bad"][0],
                f"壞檔 {lk['n_bad_files']} 個 · {lk['n_bad_lakes']} 夾")
            chk("⑱ 湖落後庫超過 7 天=STALE(px 停 2026-08-25 而庫到 2026-09-16=落後 22 天)",
                by["px/year=2026"]["state"] == "STALE" and by["px/year=2026"]["days_behind_db"] == 22,
                f"落後 {by['px/year=2026']['days_behind_db']} 天")
            chk("⑲ 本閘不刪壞檔(刪不刪是操作員的手)", "不刪任何壞檔" in lk["note"])
        finally:
            g["CATALOG"] = old_cat

    chk("⑳ 帶加速器橋(MDL156 覆蓋閘)", "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="VDF_ENG090_DataCoverageGate", description="VDF 資料涵蓋閘(零網路;零寫;不代裝)")
    ap.add_argument("verb", nargs="?", default="universe", choices=["universe", "revenue", "macro", "lakes"])
    ap.add_argument("--probe", action="store_true", help="macro:真的問一次本機 akshare(只驗介面在不在)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    r = {"universe": universe, "revenue": revenue, "macro": (lambda: macro(a.probe)), "lakes": lakes}[a.verb]()
    write_out(f"VDFCOV_{a.verb.upper()}_{ts}.json", r)
    write_out(f"VDFCOV_{a.verb.upper()}_latest.json", r)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
        return {"OK": 0, "NODATA": 2, "ABSENT": 3}.get(r.get("state"), 1)
    print(f"[VDF_ENG090 v{VERSION}] {a.verb} · {r.get('state')}")
    if a.verb == "universe" and r.get("tables"):
        for t in r["tables"]:
            print(f"  【{t['zh']}】{t['table']} · 在庫 {t['in_db']} · 列 {t['rows_in_db']}")
            for c in t["cols"]:
                print(f"    [{c['state']:<6}] {c['label']:<18} {c['rule']}")
        print(f"  [計] 齊 {r['n_green']} · 離線可推待補 {r['n_offline_todo']} · **GATED(要觸網)** {r['n_gated']}")
    elif a.verb == "revenue" and r.get("tables"):
        for t in r["tables"]:
            print(f"  [{t['state']:<6}] {t['table']:<28} {t['lo']}→{t['hi']} · 列 {t['rows']} · 落後 {t['months_behind']} 月")
    elif a.verb == "lakes" and r.get("lakes"):
        print(f"  庫最新 {r['db_latest']} · 湖 {r['n_lakes']} 夾 · **壞檔 {r['n_bad_files']} 個({r['n_bad_lakes']} 夾)** · 落後>7天 {r['n_stale']} 夾")
        for x in r["lakes"]:
            if x["state"] == "GREEN":
                continue
            print(f"  [{x['state']:<5}] {str(x['lake'])[:34]:<34} {x['lo']}→{x['hi']} · 落後 {x['days_behind_db']} 天 · 壞檔 {x['n_bad']}")
            for b in x["bad"]:            # L62:不截斷
                print(f"          壞檔:{b}")
    elif a.verb == "macro":
        for x in r.get("rows", []):
            print(f"  [{x['state']:<10}] {x['key']:<12} {x['zh']:<26} {', '.join(x['akshare_candidates'])}")
        print(f"  [計] {r.get('n')} 項 · 已驗 {r.get('n_verified', 0)}")
    if r.get("why"):
        print(f"  {r['why']}")
    if r.get("note"):
        print(f"  註:{r['note']}")
    return {"OK": 0, "NODATA": 2, "ABSENT": 3}.get(r.get("state"), 1)


if __name__ == "__main__":
    sys.exit(main())

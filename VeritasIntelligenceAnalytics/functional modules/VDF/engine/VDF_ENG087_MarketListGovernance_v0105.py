#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG087 v0105 — the one reader for the two Taiwan lists (all stocks · active Taiwan stock ETFs).

v0104 stays (L04). Many engines read these two lists, and each one read them its own way:
four different code regexes, three ETF fetchers, and v0103/v0104 even resolve different env names
for the same DB. This tail gives them one read-only reader with one set of rules:

  load_stock_list(db=None)   all Taiwan common stocks, TWSE (加權) + TPEX (櫃買)
  load_active_etfs(db=None)  active Taiwan stock ETFs, each marked verified or not against holdings_daily
  stock_codes() / active_etf_codes(verified_only=False)   plain code lists for engines
  build_lists()              both lists + a cross-check → one payload

Verbs: `lists` writes VIA_Reports/vdf/central_lists/TW_LISTS_latest.json (derived; never committed).
       `refresh --plan` prints the VCGC commands that refresh the lists, in order. It never fetches.
       `status` / `run` / `--selftest` keep the v0104 meaning.
Read-only everywhere: duckdb read_only=True, zero network. Module __getattr__ forwards the
v0104 → v0103 surface, so callers of run_update / dedupe_market_turnover keep working (TAILAPI).
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
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 前一版 = 同族裡檔名比自己小的最新一支(glob,不釘版號 L54;之後再出新尾版,本支照樣接 v0104)
_PRIOR = [p for p in sorted(HERE.glob("VDF_ENG087_MarketListGovernance_v*.py")) if p.name < Path(__file__).name][-1]
_SPEC = importlib.util.spec_from_file_location("eng087_prior_of_v0105", _PRIOR)
BASE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(BASE)
CORE = getattr(BASE, "BASE", BASE)          # v0103:_open/_first/_columns/_tables/_write/REPORT_DIR 在這一層

ENGINE = Path(__file__).name
SCHEMA = "VIA.VDF.TWLists.v1"
LISTS_REPORT = CORE.REPORT_DIR / "TW_LISTS_latest.json"

# ---------------------------------------------------------------- 一套規則(取代散在各引擎的四種寫法)
#: 普通股 = 四碼、首碼 1-9。00xx 四碼是 ETF,五/六碼是權證/特別股/ETN,都不算「股票清單」。
STOCK_CODE = re.compile(r"^[1-9]\d{3}$")
#: 主動式台股 ETF = 00 + 三碼 + A(00980A…)。D 結尾是主動債券,B 是債券,不算。
ACTIVE_ETF_CODE = re.compile(r"^00\d{3}A$")
#: 兩所的軟下限:低於 = AMBER(可能只抓回一部分),不是 RED。2026 年加權約 1,000、櫃買約 800 家。
SOFT_MIN = {"TWSE": 900, "TPEX": 700}

SOURCES = {
    "stock_list": {
        "official": ["https://openapi.twse.com.tw/v1/opendata/t187ap03_L (上市公司基本資料)",
                     "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O (上櫃公司基本資料)"],
        "writer": "VDF_ENG055_OmniFetch lane L1 lane_listings → vdf_tw_market.duckdb::tw_listings_industry(正主,CGC_MDL142 認定)",
        "legacy_writer": "VDF_ENG054_TWDailyBackfill v0109 fetch_listings → tw_listings(舊表;v0110 起只是狀態卡,不再抓)",
        "derived": "VDF_ENG081_UniverseAlign update --apply → tw_universe(價表∪籌碼 ∩ 清單,日快照)",
    },
    "active_etf": {
        "official": ["https://openapi.twse.com.tw/v1/opendata/t187ap47_L (ETF 基本資料;基金類型判國內/國外成分)"],
        "writer": "VDF_ENG077_ActiveETFUniverse run → ActiveTWETF.duckdb::active_tw_etf_registry(正主)",
        "validator": "VDF_ENG078_ActiveETFHoldingsHistory daily → holdings_daily(有持股 = 驗證過)",
        "legacy_writers": ["VDF_ENG051 activeList(www.twse.com.tw/rwd/zh/ETF/activeList;只國內;內建 bootstrap)",
                           "GroupIndex/engine/VIA_ActiveStockETF.py(繞過 SUP_MDL740 與同意閘)"],
    },
}


def __getattr__(name: str):
    """PEP 562:v0104 / v0103 的公開面照舊可叫(run_update、dedupe_market_turnover…)。"""
    if name.startswith("__"):
        raise AttributeError(name)
    for layer in (BASE, CORE):
        if hasattr(layer, name):
            return getattr(layer, name)
    raise AttributeError(f"{ENGINE} 沒有 {name}")


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def db_tw_path() -> Path:
    """v0103 讀 VIA_DB_VDF_TW_MARKET、v0104 讀 VIA_DB_TW:兩個都認(前者優先),都沒設 = 預設路徑。"""
    for name in ("VIA_DB_VDF_TW_MARKET", "VIA_DB_TW"):
        value = os.environ.get(name, "").strip()
        if value:
            return Path(value).expanduser()
    return CORE.DB_TW


def db_etf_path() -> Path:
    return CORE._env_path("VIA_DB_ACTIVETWETF", CORE.DB_ETF)


def _bare(code) -> str:
    return BASE._bare(code)


def _market(label) -> str:
    text = str(label or "").strip()
    if text in BASE.TWSE or text.upper() in BASE.TWSE:
        return "TWSE"
    if text in BASE.TPEX or text.upper() in BASE.TPEX:
        return "TPEX"
    return ""


def _result(kind: str, db: Path) -> dict:
    return {"list": kind, "db": str(db), "state": "ABSENT", "why": "", "table": None,
            "rows": [], "counts": {}, "dropped": {}, "checks": []}


# ---------------------------------------------------------------- 清單一:全部台股
def load_stock_list(db: Path | None = None) -> dict:
    """全部台股普通股(加權 + 櫃買)。唯讀。rows = [{code, name, market, yf_ticker, industry}],依代號排序。

    判定:庫/表缺 = ABSENT/RED;表空 = NODATA;任一所 0 家 = RED;低於軟下限、同碼掛兩所、交易所認不得 = AMBER;其餘 GREEN。
    """
    db = Path(db) if db else db_tw_path()
    res = _result("tw_stock", db)
    con = CORE._open(db)
    if con is None:
        res["why"] = "vdf_tw_market.duckdb 不存在或 duckdb 環境缺(先 via-console run --item macro_lanes lanes=L1)"
        return res
    try:
        tables = CORE._tables(con)
        table = next((t for t in ("tw_listings_industry", "tw_listings") if t in tables), None)
        if table is None:
            res.update(state="RED", why="庫在,但 tw_listings_industry 與 tw_listings 都沒有")
            return res
        cols = CORE._columns(con, table)
        m = {"code": CORE._first(cols, ("code", "stock_code", "ticker")),
             "name": CORE._first(cols, ("name", "stock_name", "company_name")),
             "market": CORE._first(cols, ("market", "exchange", "交易所")),
             "industry": CORE._first(cols, ("industry_name", "industry", "產業別"))}
        res.update(table=table, mapping=m)
        if not m["code"] or not m["market"]:
            res.update(state="RED", why=f"{table} 缺代號或交易所欄(有:{', '.join(cols[:12])})")
            return res
        pick = ", ".join(f"CAST({CORE._safe_table(m[k])} AS VARCHAR)" if m[k] else "NULL"
                         for k in ("code", "name", "market", "industry"))
        raw = con.execute(f"SELECT {pick} FROM {CORE._safe_table(table)}").fetchall()
    finally:
        con.close()
    if not raw:
        res.update(state="NODATA", why=f"{table} 是空的")
        return res
    by_code: dict = {}
    dropped = {"not_stock_code": 0, "unknown_market": 0, "duplicate": 0}
    unknown, dual = [], []
    for code, name, market, industry in raw:
        c = _bare(code)
        if not STOCK_CODE.fullmatch(c):
            dropped["not_stock_code"] += 1
            continue
        mk = _market(market)
        if not mk:
            dropped["unknown_market"] += 1
            if market and str(market) not in unknown and len(unknown) < 8:
                unknown.append(str(market))
            continue
        if c in by_code:
            dropped["duplicate"] += 1
            if by_code[c]["market"] != mk and c not in dual:
                dual.append(c)
            continue
        by_code[c] = {"code": c, "name": str(name or "").strip(), "market": mk,
                      "yf_ticker": c + (".TW" if mk == "TWSE" else ".TWO"), "industry": str(industry or "").strip()}
    rows = [by_code[k] for k in sorted(by_code)]
    counts = {"TWSE": sum(1 for r in rows if r["market"] == "TWSE"), "TPEX": sum(1 for r in rows if r["market"] == "TPEX")}
    checks = [
        {"check": "兩所都在", "ok": counts["TWSE"] > 0 and counts["TPEX"] > 0, "detail": f"加權 {counts['TWSE']} · 櫃買 {counts['TPEX']}"},
        {"check": "軟下限", "ok": all(counts[k] >= v for k, v in SOFT_MIN.items()),
         "detail": " · ".join(f"{k} {counts[k]}/{v}" for k, v in SOFT_MIN.items())},
        {"check": "同碼不掛兩所", "ok": not dual, "detail": ", ".join(dual[:10]) or "0"},
        {"check": "交易所都認得", "ok": not dropped["unknown_market"], "detail": ", ".join(unknown) or "0"},
    ]
    res.update(rows=rows, counts=counts, dropped=dropped, checks=checks, n=len(rows))
    if not checks[0]["ok"]:
        res.update(state="RED", why=f"股票清單缺一所:加權 {counts['TWSE']} · 櫃買 {counts['TPEX']}")
    elif not all(c["ok"] for c in checks):
        bad = [c["check"] for c in checks if not c["ok"]]
        res.update(state="AMBER", why=f"股票清單 {len(rows)} 檔,待看:{'、'.join(bad)}")
    else:
        res.update(state="GREEN", why=f"股票清單 {len(rows)} 檔(加權 {counts['TWSE']} · 櫃買 {counts['TPEX']})")
    return res


# ---------------------------------------------------------------- 清單二:主動式台股 ETF(驗證過)
def load_active_etfs(db: Path | None = None) -> dict:
    """主動式台股 ETF。唯讀。registry 是總清單;holdings_daily 有持股 = verified。

    收進清單:代號合 ACTIVE_ETF_CODE,且 status=ACTIVE_DOMESTIC(沒有 status 欄時看 domestic,再沒有看 daily_required)。
    判定:庫/表缺 = ABSENT/RED;清單 0 檔 = RED;有檔沒持股 = AMBER;全部驗證 = GREEN。
    """
    db = Path(db) if db else db_etf_path()
    res = _result("active_tw_etf", db)
    con = CORE._open(db)
    if con is None:
        res["why"] = "ActiveTWETF.duckdb 不存在或 duckdb 環境缺(先 via-console run --item etf_universe)"
        return res
    try:
        tables = CORE._tables(con)
        if "active_tw_etf_registry" not in tables:
            res.update(state="RED", why="庫在,但沒有 active_tw_etf_registry")
            return res
        res["table"] = "active_tw_etf_registry"
        cols = CORE._columns(con, "active_tw_etf_registry")
        m = {k: CORE._first(cols, cands) for k, cands in (
            ("ticker", ("ticker", "etf_ticker")), ("name", ("name", "etf_name")), ("issuer", ("issuer", "manager")),
            ("fund_type", ("fund_type",)), ("domestic", ("domestic",)), ("daily_required", ("daily_required",)),
            ("status", ("status",)))}
        res["mapping"] = m
        if not m["ticker"]:
            res.update(state="RED", why="registry 沒有 ticker 欄")
            return res
        keys = ("ticker", "name", "issuer", "fund_type", "domestic", "daily_required", "status")
        pick = ", ".join(f"CAST({CORE._safe_table(m[k])} AS VARCHAR)" if m[k] else "NULL" for k in keys)
        reg = [dict(zip(keys, r)) for r in con.execute(f'SELECT {pick} FROM "active_tw_etf_registry"').fetchall()]
        held: dict = {}
        if "holdings_daily" in tables:
            hcols = CORE._columns(con, "holdings_daily")
            ecol = CORE._first(hcols, ("etf_ticker", "etf"))
            dcol = CORE._first(hcols, ("portfolio_date", "date", "snapshot_at"))
            if ecol:
                dsel = f"MAX(CAST({CORE._safe_table(dcol)} AS VARCHAR))" if dcol else "NULL"
                for t, d in con.execute(f"SELECT CAST({CORE._safe_table(ecol)} AS VARCHAR), {dsel} "
                                        f'FROM "holdings_daily" GROUP BY 1').fetchall():
                    c = _bare(t)                   # 00981A 與 00981A.TW 是同一檔:分組後再合,取最晚日
                    held[c] = max(held.get(c, ""), str(d or ""))
        res["holdings_table"] = "holdings_daily" if "holdings_daily" in tables else None
    finally:
        con.close()

    def _truthy(v) -> bool | None:
        s = str(v or "").strip().lower()
        return True if s in ("true", "1", "t", "yes") else (False if s in ("false", "0", "f", "no") else None)

    rows, seen = [], set()
    dropped = {"not_active_a_code": 0, "not_domestic": 0, "duplicate": 0}
    for r in reg:
        c = _bare(r["ticker"])
        if not ACTIVE_ETF_CODE.fullmatch(c):
            dropped["not_active_a_code"] += 1
            continue
        if m["status"]:
            ok = str(r["status"] or "").upper() == "ACTIVE_DOMESTIC"
        elif m["domestic"]:
            ok = _truthy(r["domestic"]) is True
        else:
            ok = _truthy(r["daily_required"]) is True
        if not ok:
            dropped["not_domestic"] += 1
            continue
        if c in seen:
            dropped["duplicate"] += 1
            continue
        seen.add(c)
        rows.append({"ticker": c, "name": str(r["name"] or "").strip(), "issuer": str(r["issuer"] or "").strip(),
                     "fund_type": str(r["fund_type"] or "").strip(), "verified": c in held,
                     "last_holdings_date": held.get(c, "")})
    rows.sort(key=lambda x: x["ticker"])
    unverified = [r["ticker"] for r in rows if not r["verified"]]
    res.update(rows=rows, dropped=dropped, n=len(rows),
               counts={"listed": len(rows), "verified": len(rows) - len(unverified), "unverified": len(unverified)},
               checks=[{"check": "總清單有檔", "ok": bool(rows), "detail": str(len(rows))},
                       {"check": "持股表在", "ok": res["holdings_table"] is not None, "detail": res["holdings_table"] or "缺"},
                       {"check": "每檔都有持股(驗證)", "ok": not unverified, "detail": ", ".join(unverified[:12]) or "0"}])
    if not reg:
        res.update(state="NODATA", why="active_tw_etf_registry 是空的")
    elif not rows:
        res.update(state="RED", why=f"registry {len(reg)} 列,沒有一檔是國內主動式股票 A 碼")
    elif unverified:
        res.update(state="AMBER", why=f"主動式台股 ETF {len(rows)} 檔,{len(unverified)} 檔還沒有持股(未驗證)")
    else:
        res.update(state="GREEN", why=f"主動式台股 ETF {len(rows)} 檔,全部有持股(已驗證)")
    return res


def stock_codes(db: Path | None = None) -> list:
    """給引擎用:只要代號。清單不是 GREEN/AMBER 時回空串列(呼叫端自己看 load_stock_list 的 why)。"""
    got = load_stock_list(db)
    return [r["code"] for r in got["rows"]] if got["state"] in ("GREEN", "AMBER") else []


def active_etf_codes(db: Path | None = None, verified_only: bool = False) -> list:
    got = load_active_etfs(db)
    if got["state"] not in ("GREEN", "AMBER"):
        return []
    return [r["ticker"] for r in got["rows"] if r["verified"] or not verified_only]


def _listed_a_codes(db: Path) -> set:
    """交叉核對用:股票庫 tw_listings 裡的 A 碼(ENG054 舊表含 ETF 列;沒有就空)。"""
    con = CORE._open(db)
    if con is None:
        return set()
    try:
        if "tw_listings" not in CORE._tables(con):
            return set()
        col = CORE._first(CORE._columns(con, "tw_listings"), ("code", "ticker"))
        if not col:
            return set()
        return {_bare(r[0]) for r in con.execute(f'SELECT CAST({CORE._safe_table(col)} AS VARCHAR) FROM "tw_listings"').fetchall()
                if ACTIVE_ETF_CODE.fullmatch(_bare(r[0]))}
    finally:
        con.close()


def _worst(states: list) -> str:
    for s in ("ABSENT", "RED", "NODATA", "AMBER"):
        if s in states:
            return s
    return "GREEN"


def build_lists(db_tw: Path | None = None, db_etf: Path | None = None) -> dict:
    db_tw = Path(db_tw) if db_tw else db_tw_path()
    stock = load_stock_list(db_tw)
    etf = load_active_etfs(db_etf)
    in_listing = _listed_a_codes(db_tw)
    reg = {r["ticker"] for r in etf["rows"]}
    cross = {"listed_not_in_registry": sorted(in_listing - reg)[:30],
             "note": "股票庫 tw_listings 裡掛牌的主動 A 碼卻不在 ETF 總清單 = 總清單可能漏抓(ENG077 run 補)" if in_listing - reg else
                     ("tw_listings 沒有 A 碼可對(正常:正主表不含 ETF)" if not in_listing else "掛牌 A 碼都在總清單")}
    verdict = _worst([stock["state"], etf["state"]])
    if verdict == "GREEN" and cross["listed_not_in_registry"]:
        verdict = "AMBER"
    return {"schema": SCHEMA, "engine": ENGINE, "ts": _now(), "verdict": verdict,
            "rules": {"stock_code": STOCK_CODE.pattern, "active_etf_code": ACTIVE_ETF_CODE.pattern,
                      "active_etf_status": "ACTIVE_DOMESTIC", "soft_min": SOFT_MIN,
                      "verified": "holdings_daily 有這檔的持股列"},
            "sources": SOURCES, "stock": stock, "active_etf": etf, "crosscheck": cross,
            "consumer_api": "newest VDF_ENG087 tail → load_stock_list()/load_active_etfs()/stock_codes()/active_etf_codes()"}


def write_lists(payload: dict, out: Path | None = None) -> Path:
    out = Path(out) if out else LISTS_REPORT
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(out)
    return out


def summary(payload: dict) -> list:
    """不帶逐檔列的摘要(給面板 / 貼回用)。"""
    out = []
    for key in ("stock", "active_etf"):
        item = payload[key]
        out.append({"list": item["list"], "state": item["state"], "n": item.get("n", 0), "why": item["why"],
                    "table": item.get("table"), "counts": item.get("counts", {}), "dropped": item.get("dropped", {}),
                    "checks": item.get("checks", [])})
    return out


# ---------------------------------------------------------------- 更新路徑(只印,不抓)
def refresh_plan() -> list:
    gate = "VIA_NET_CONSENT=YES(操作員親設;本支不代設。爬蟲道另需 VIA_SCRAPE_CONSENT=期望 token,見 via-gates)"
    return [
        {"step": 1, "what": "抓兩所上市櫃公司清單 → tw_listings_industry", "cmd": "via-console run --item macro_lanes lanes=L1",
         "net": True, "gate": gate, "writes": "vdf_tw_market.duckdb::tw_listings_industry"},
        {"step": 2, "what": "主動 ETF 總清單 → active_tw_etf_registry", "cmd": "via-console run --item etf_universe",
         "net": True, "gate": gate, "writes": "ActiveTWETF.duckdb::active_tw_etf_registry"},
        {"step": 3, "what": "每檔主動 ETF 的持股(= 驗證)", "cmd": "via-console run --item etf_holdings_daily",
         "net": True, "gate": gate, "writes": "ActiveTWETF.duckdb::holdings_daily"},
        {"step": 4, "what": "股票日快照(價表∪籌碼 ∩ 清單;選用)", "cmd": "via-console run --item tw_universe_update",
         "net": False, "gate": "寫庫件:日更鏈沒在跑時再跑", "writes": "vdf_tw_market.duckdb::tw_universe"},
        {"step": 5, "what": "驗收兩張清單 + 面板", "cmd": "via-vcgc dbm panel",
         "net": False, "gate": "唯讀", "writes": "VIA_Reports(再生件)"},
    ]


# ---------------------------------------------------------------- status(v0104 的意思,庫路徑兩個名字都認)
def _status() -> dict:
    payload = BASE._status()
    stocks = BASE._status_stock(db_tw_path())
    etf = BASE._status_etf(db_etf_path())
    payload["lists"]["tw_stock_universe"] = stocks
    payload["lists"]["active_tw_etf"] = etf
    states = [stocks["state"], etf["state"], payload["lists"]["hot_story_groups"]["state"]]
    payload["verdict"] = ("GREEN" if all(s == "GREEN" for s in states)
                          else ("ABSENT" if "ABSENT" in states else ("NODATA" if "NODATA" in states else "RED")))
    payload["canonical_lists"] = summary(build_lists())
    payload["engine"] = ENGINE
    return payload


def status() -> int:
    payload = _status()
    CORE._write(payload)
    stocks = payload["lists"]["tw_stock_universe"]
    etf = payload["lists"]["active_tw_etf"]
    print(f"[VDF_ENG087 v0105] {payload['verdict']} · 個股 {stocks['state']} · 主動式台股ETF {etf['state']}")
    for item in payload["canonical_lists"]:
        print(f"  [{item['list']}] {item['state']} · {item['why']}")
    return 0 if payload["verdict"] == "GREEN" else 2


def lists(as_json: bool = False, out: Path | None = None) -> int:
    payload = build_lists()
    path = write_lists(payload, out)
    if as_json:
        print(json.dumps({"verdict": payload["verdict"], "summary": summary(payload), "out": str(path)}, ensure_ascii=False))
    else:
        print(f"[VDF_ENG087 v0105 lists] {payload['verdict']}")
        for item in summary(payload):
            print(f"  [{item['list']}] {item['state']} · {item['why']}")
            for c in item["checks"]:
                print(f"      {'OK ' if c['ok'] else 'NG '} {c['check']}: {c['detail']}")
        if payload["crosscheck"]["listed_not_in_registry"]:
            print(f"  [交叉] {payload['crosscheck']['note']}: {', '.join(payload['crosscheck']['listed_not_in_registry'])}")
        print(f"  結果: {path}")
    return {"GREEN": 0, "AMBER": 0}.get(payload["verdict"], 2)


def _print_plan() -> int:
    print("[VDF_ENG087 v0105 refresh --plan] 更新兩張清單的順序(本支只印,不抓、不代開同意閘):")
    for s in refresh_plan():
        print(f"  {s['step']}. {s['what']}")
        print(f"       {s['cmd']}")
        print(f"       網路 {'要' if s['net'] else '不要'} · 閘 {s['gate']} · 寫 {s['writes']}")
    return 0


# ---------------------------------------------------------------- 自測(暫存夾假庫;不碰正庫、不寫 VIA_Reports L17)
def _mk_dbs(root: Path, one_side: bool = False) -> tuple:
    import duckdb
    tw, etf = root / "tw.duckdb", root / "etf.duckdb"
    con = duckdb.connect(str(tw))
    con.execute("CREATE TABLE tw_listings_industry(code VARCHAR, name VARCHAR, market VARCHAR, industry_name VARCHAR)")
    rows = [("2330", "台積電", "TWSE", "半導體業"), ("2317", "鴻海", "上市", "其他電子業"),
            ("0050", "元大台灣50", "TWSE", ""), ("91234", "權證", "TWSE", ""), ("2330.TW", "台積電", "TWSE", "半導體業")]
    if not one_side:
        rows += [("6488", "環球晶", "TPEX", "半導體業"), ("8069", "元太", "上櫃", "光電業"), ("5483", "中美晶", "??", "")]
    con.executemany("INSERT INTO tw_listings_industry VALUES (?,?,?,?)", rows)
    con.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR, market VARCHAR)")
    con.executemany("INSERT INTO tw_listings VALUES (?,?,?)", [("2330", "台積電", "TWSE"), ("00981A", "主動統一台股增長", "TWSE"),
                                                               ("00985A", "主動野村臺灣50", "TWSE")])
    con.close()
    con = duckdb.connect(str(etf))
    con.execute("CREATE TABLE active_tw_etf_registry(ticker VARCHAR, name VARCHAR, fund_type VARCHAR, domestic BOOLEAN, "
                "daily_required BOOLEAN, status VARCHAR, source VARCHAR, issuer VARCHAR, first_seen VARCHAR, last_seen VARCHAR)")
    con.executemany("INSERT INTO active_tw_etf_registry VALUES (?,?,?,?,?,?,?,?,?,?)", [
        ("00981A", "主動統一台股增長", "國內成分股ETF", True, True, "ACTIVE_DOMESTIC", "t", "統一", "", ""),
        ("00982A", "主動群益台灣強棒", "國內成分股ETF", True, True, "ACTIVE_DOMESTIC", "t", "群益", "", ""),
        ("00983A", "主動中信ARK創新", "國外成分股ETF", False, False, "FOREIGN_COMPONENT", "t", "中信", "", ""),
        ("00980D", "主動聯博投等入息", "債券ETF", True, False, "ACTIVE_DOMESTIC", "t", "聯博", "", ""),
        ("00984A", "主動安聯台灣高息", "國內成分股ETF", True, False, "MISSING_FROM_SOURCE", "t", "安聯", "", "")])
    con.execute("CREATE TABLE holdings_daily(portfolio_date VARCHAR, etf_ticker VARCHAR, holding_ticker VARCHAR, weight DOUBLE)")
    con.executemany("INSERT INTO holdings_daily VALUES (?,?,?,?)", [("2026-09-25", "00981A", "2330", 9.1),
                                                                     ("2026-09-26", "00981A.TW", "2317", 5.0)])
    con.close()
    return tw, etf


def selftest() -> int:
    checks = []

    def chk(name, ok, note=""):
        checks.append((name, bool(ok), note))

    chk("規則:普通股四碼", STOCK_CODE.fullmatch("2330") and not STOCK_CODE.fullmatch("0050") and not STOCK_CODE.fullmatch("91234"))
    chk("規則:主動股票 A 碼", ACTIVE_ETF_CODE.fullmatch("00981A") and not ACTIVE_ETF_CODE.fullmatch("00980D")
        and not ACTIVE_ETF_CODE.fullmatch("0098A"))
    mod = sys.modules[__name__]
    chk("轉接:v0103 的 dedupe_market_turnover / run_update 叫得到(TAILAPI)",
        callable(getattr(mod, "dedupe_market_turnover", None)) and callable(getattr(mod, "run_update", None)))
    chk("轉接:v0104 的 verify_etf_master 叫得到", callable(getattr(mod, "verify_etf_master", None)))
    plan = refresh_plan()
    chk("refresh 計畫五步、只有前三步要網路", len(plan) == 5 and [s["net"] for s in plan] == [True, True, True, False, False])
    try:
        import duckdb  # noqa: F401
    except ImportError:
        bad = [n for n, ok, _ in checks if not ok]
        print(f"[ABSENT] duckdb 缺(ModuleNotFoundError),庫測略過 · 規則 {len(checks) - len(bad)}/{len(checks)}")
        return 1 if bad else 3
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tw, etf = _mk_dbs(root)
        s = load_stock_list(tw)
        codes = [r["code"] for r in s["rows"]]
        chk("股票:只收四碼普通股、去後綴去重", codes == ["2317", "2330", "6488", "8069"], str(codes))
        chk("股票:上市/上櫃 → TWSE/TPEX", s["counts"] == {"TWSE": 2, "TPEX": 2}, str(s["counts"]))
        chk("股票:剔除數照實", s["dropped"] == {"not_stock_code": 2, "unknown_market": 1, "duplicate": 1}, str(s["dropped"]))
        chk("股票:低於軟下限 + 認不得交易所 = AMBER(不是 GREEN)", s["state"] == "AMBER", s["why"])
        chk("股票:yf 後綴", {r["code"]: r["yf_ticker"] for r in s["rows"]}["6488"] == "6488.TWO")
        e = load_active_etfs(etf)
        chk("ETF:只收國內主動股票 A 碼", [r["ticker"] for r in e["rows"]] == ["00981A", "00982A"], str(e["rows"]))
        chk("ETF:剔除數(D 碼 1 · 國外/下架 2)", e["dropped"] == {"not_active_a_code": 1, "not_domestic": 2, "duplicate": 0}, str(e["dropped"]))
        chk("ETF:持股驗證(.TW 後綴也算)", [r["verified"] for r in e["rows"]] == [True, False]
            and e["rows"][0]["last_holdings_date"] == "2026-09-26")
        chk("ETF:有檔未驗證 = AMBER", e["state"] == "AMBER" and e["counts"]["unverified"] == 1, e["why"])
        chk("代號串列:verified_only", active_etf_codes(etf, verified_only=True) == ["00981A"] and stock_codes(tw)[:1] == ["2317"])
        p = build_lists(tw, etf)
        chk("交叉:掛牌 A 碼不在總清單要報", p["crosscheck"]["listed_not_in_registry"] == ["00985A"], str(p["crosscheck"]))
        out = write_lists(p, root / "out" / "TW_LISTS_latest.json")
        chk("lists 寫到指定路徑(自測不碰 VIA_Reports)", out.exists() and json.loads(out.read_text(encoding="utf-8"))["schema"] == SCHEMA)
        one = root / "one"
        one.mkdir()
        tw1, _ = _mk_dbs(one, one_side=True)
        chk("股票:只有一所 = RED", load_stock_list(tw1)["state"] == "RED")
        chk("庫不在 = ABSENT", load_stock_list(root / "nope.duckdb")["state"] == "ABSENT"
            and load_active_etfs(root / "nope.duckdb")["state"] == "ABSENT")
        prev = {k: os.environ.get(k) for k in ("VIA_DB_VDF_TW_MARKET", "VIA_DB_TW")}
        try:
            os.environ.pop("VIA_DB_VDF_TW_MARKET", None)
            os.environ["VIA_DB_TW"] = str(tw)
            chk("庫路徑:只設 VIA_DB_TW 也認", db_tw_path() == tw)
            os.environ["VIA_DB_VDF_TW_MARKET"] = str(tw1)
            chk("庫路徑:VIA_DB_VDF_TW_MARKET 優先", db_tw_path() == tw1)
        finally:
            for k, v in prev.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    bad = [(n, note) for n, ok, note in checks if not ok]
    for n, ok, note in checks:
        print(f"  {'OK  ' if ok else 'FAIL'} {n}" + (f" · {note}" if (note and not ok) else ""))
    print(f"[VDF_ENG087 v0105] {len(checks) - len(bad)}/{len(checks)}" + (" FAIL" if bad else " OK"))
    return 1 if bad else 0


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a or "selftest" in a:
        return selftest()
    verb = a[0] if a else "status"
    if verb == "lists":
        return lists(as_json="--json" in a)
    if verb == "refresh":
        return _print_plan()
    if verb == "run":
        print("[VDF_ENG087 v0105] run = v0103 的委派(兩張狀態卡,不抓清單);真的要更新清單看:refresh --plan")
        return BASE.run_update() if hasattr(BASE, "run_update") else CORE.run_update()
    if verb == "status":
        return status()
    print(f"[VDF_ENG087 v0105] 不認得「{verb}」;可用 status · lists [--json] · refresh --plan · run · --selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

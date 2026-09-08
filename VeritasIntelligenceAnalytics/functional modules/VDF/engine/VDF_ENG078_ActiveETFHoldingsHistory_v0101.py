#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG078_ActiveETFHoldingsHistory — 主動 ETF 每日持股史深覆蓋器(批375;via-etfhist)
====================================================================
操作員令(批375)「set up an auto updating mechanism to update daily data of active Taiwan ETF holding from the
beginning of its IPO」。
律(只增不減;誠實三態;零假造):
  ① 覆蓋帳  每檔須每日揭露之主動 ETF(ENG077 registry daily_required):上市日 → 今日之「應有交易日」(tw_daily_prices
             真實交易日曆;缺=平日)vs holdings_daily 已有快照日 → 缺口逐日列 MISSING(checkpoint 永不刪、只改態)。
  ② 上市日  三車道:L1 ENG077/TWSE 冊上市日欄(在則用)→ L2 統包 yf_history 首根 K 線日(<code>.TW;親跑同意)
             → L3 既有首個快照日=下界(標 LOWER_BOUND 誠實;不冒充 IPO 日)。
  ③ 回補    自 IPO 起逐日:車道冊 VIA_ActiveETF_HistoryLanes(registry JSON;只增):ISSUER_ARCHIVE(各投信 PCF 歷史頁;
             VERIFIED 才呼;未驗=PENDING_SOURCE 誠實列缺)/ MONEYDJ(LATEST_ONLY=只能補「今日」)/ 未來新源加冊即生效。
             缺源日=NO_SOURCE(不假填);有源日經 ENG051 同式解析落 holdings_daily(anti-join (portfolio_date,etf,holding))。
  ④ 日更    boot 日更鏈 ④b(ENG051 抓今日後→本器算覆蓋+補昨日缺口)+FixAll 步 etf_history+樞紐任務+via-etfhist;
             每日快照即「從今起零缺口」;IPO 以來史段依車道冊驗證進度逐日填,進度頁可見。
  ⑤ 頁/存證 VIA_Reports/active_etf_history/COVERAGE_<日>.json + ui_support/VIA_UI_ActiveETFHoldingsHistory_v0100.html(手機單欄)。
v0100→v0101(批406 工作站實錄「23 檔須每日揭露 · 今日已抓 0 · 回補 tried 0 filled 0」
+ 操作員令「我只抓主動型台股 ETF 的資料持股」「用 TWSE 去抓」):
  根因:車道冊 16 條 ISSUER_ARCHIVE 全為 PENDING_SOURCE 且 url 空,唯一 VERIFIED 的
  MONEYDJ 是 LATEST_ONLY(只給今日),故 DATED 回補無車道可呼;v0100 backfill 自註
  「DATED 車道解析器候接(v0101)」——本版把那段接上,並補上前置的「來源發現」。
  ① discover:自 TWSE OpenAPI **規格檔**真列舉資料集(不猜端點;規格取不到=誠實
     UNREACHABLE 並列已試路徑),以持股/成分/PCF 關鍵字篩出候選,以 state=CANDIDATE
     寫回車道冊(只增不減;**永不**未驗即標 VERIFIED)。
  ② parse_holdings:JSON(list[dict])與 HTML 表雙道解析 → (代號,名稱,股數,權重);
     判準=≥MIN_HOLD_ROWS 列且四碼台股代號與數字皆可解析,否則回空(誠實不硬填)。
  ③ probe:對 CANDIDATE/PENDING 且有 url 的車道,以真標的+真日期取一次、跑 ②
     驗證;逐條印 PASS/FAIL 與因由(HTTP/零列/日期不符/閘關);`--apply` **只把驗
     證通過者**升為 VERIFIED 並寫回 url(只增不減:不刪車道、不動他條)。
  ④ backfill:VERIFIED DATED 車道存在時真取真解析真落庫(anti-join);仍無=NO_SOURCE。
  沙盒無外網,②③④ 皆以注入式假 net 自測;真跑在工作站(via-etfhist 自帶雙閘 YES)。
  v0101 首跑修(批406b 工作站實錄「13 條 candidate 全 404」):規格檔的 paths 是
     **相對 base**(TWSE 之 base 含 /v1),v0101 首版只接主機名 → 組出
     https://openapi.twse.com.tw/opendata/t187ap47_L 全 404(倉內既驗證之真 URL 是
     .../v1/opendata/t187ap47_L)。新增 spec_base():OpenAPI3 servers[0].url →
     Swagger2 schemes+host+basePath → 退倉內既驗證常數;discover --apply 併修既有
     CANDIDATE 之錯 url(VERIFIED 不動)。**404/403 皆為伺服器真回,證明網路工具有掛
     且暢通**(閘關會回 DENY、未掛會回 NO_NET)。
用法:python3 VDF_ENG078_ActiveETFHoldingsHistory_v0101.py daily [--offline]
        | backfill [--max-days N] | discover [--apply] | probe [--ticker 00980A]
        [--date YYYY-MM-DD] [--apply] | status | --selftest
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
import html
import json
import os
import re          # 批406:持股表解析/代號判準
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
DB_ETF = VDF / "output_hub" / "active_tw_etf" / "active_tw_etf_holdings" / "ActiveTWETF.duckdb"
DB_TW = VDF / "output_hub" / "mega" / "vdf_tw_market.duckdb"
REP = VIA / "VIA_Reports" / "active_etf_history"
CKPT = VDF / "output_hub" / "active_tw_etf" / "holdings_history_checkpoint.json"
OUT_UI = VIA / "supportive modules" / "ui_support" / "VIA_UI_ActiveETFHoldingsHistory_v0100.html"
LANES_JSON = VIA / "supportive modules" / "registry" / "VIA_ActiveETF_HistoryLanes_v0100.json"
COV_TABLE = "active_etf_holdings_coverage"
ACTIVE_ETF_ERA = "2025-05-01"   # 台灣主動式 ETF 首檔掛牌前(誠實下界;早於此無主動 ETF)

DEFAULT_LANES = {
    "schema": "VIA_ActiveETF_HistoryLanes/1.0", "rule": "只增不減;VERIFIED 才呼;PENDING_SOURCE=誠實列缺(工作站驗證 URL 後改態即生效)",
    "lanes": [
        {"id": "MONEYDJ", "kind": "LATEST_ONLY", "state": "VERIFIED", "url": "https://www.moneydj.com/ETF/X/Basic/Basic0007B.xdjhtm?etfid={yf}",
         "note": "僅最新日持股(ENG051 後備道);無歷史檔"},
        {"id": "ISSUER_ARCHIVE:群益投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "https://www.capitalfund.com.tw/etf/product/detail/500/portfolio?date={ymd}",
         "note": "ENG051 已有現值解析(00992A);歷史日期參數候工作站驗證"},
        {"id": "ISSUER_ARCHIVE:統一投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
        {"id": "ISSUER_ARCHIVE:野村投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
        {"id": "ISSUER_ARCHIVE:國泰投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
        {"id": "ISSUER_ARCHIVE:富邦投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
        {"id": "ISSUER_ARCHIVE:中國信託投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
        {"id": "ISSUER_ARCHIVE:安聯投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
        {"id": "ISSUER_ARCHIVE:摩根投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
        {"id": "ISSUER_ARCHIVE:聯博投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
        {"id": "ISSUER_ARCHIVE:凱基投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
        {"id": "ISSUER_ARCHIVE:第一金投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
        {"id": "ISSUER_ARCHIVE:永豐投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
        {"id": "ISSUER_ARCHIVE:復華投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
        {"id": "ISSUER_ARCHIVE:台新投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
        {"id": "ISSUER_ARCHIVE:兆豐投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
        {"id": "ISSUER_ARCHIVE:元大投信", "kind": "DATED", "state": "PENDING_SOURCE", "url": "", "note": "PCF 歷史頁候源"},
    ]}


def gate_open(env=None) -> bool:
    env = env if env is not None else os.environ
    return env.get("VIA_NET_CONSENT") == "YES" and env.get("VIA_SCRAPE_CONSENT") == "YES"


def _net_or_none():
    import glob as _g
    import importlib.util as _il
    hits = sorted(_g.glob(str(VIA / "supportive modules" / "network" / "SUP_MDL740_NetUnified_v*.py")))
    if not hits:
        return None
    spec = _il.spec_from_file_location("via_net_dyn", hits[-1])
    mod = _il.module_from_spec(spec)
    sys.modules["via_net_dyn"] = mod
    spec.loader.exec_module(mod)
    return mod


def load_lanes() -> dict:
    if LANES_JSON.exists():
        try:
            return json.loads(LANES_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    LANES_JSON.parent.mkdir(parents=True, exist_ok=True)
    LANES_JSON.write_text(json.dumps(DEFAULT_LANES, ensure_ascii=False, indent=1), encoding="utf-8")
    return DEFAULT_LANES


def _load_ckpt() -> dict:
    if CKPT.exists():
        try:
            return json.loads(CKPT.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_ckpt(ck: dict) -> None:
    CKPT.parent.mkdir(parents=True, exist_ok=True)
    tmp = CKPT.with_suffix(".tmp")
    tmp.write_text(json.dumps(ck, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(CKPT)


# ---------------------------------------------------------------- 真值
def universe() -> list[dict]:
    """須每日揭露之主動 ETF(ENG077 registry;缺=universe 快照;含 issuer)"""
    if not DB_ETF.exists():
        return []
    import duckdb
    con = duckdb.connect(str(DB_ETF), read_only=True)
    try:
        tabs = {t for (t,) in con.execute("SHOW TABLES").fetchall()}
        if "active_tw_etf_registry" in tabs:
            rows = con.execute("SELECT ticker, name, COALESCE(issuer,''), first_seen FROM active_tw_etf_registry WHERE daily_required ORDER BY ticker").fetchall()
            if rows:
                return [{"ticker": t, "name": n, "issuer": i, "first_seen": str(f)[:10]} for t, n, i, f in rows]
        if "active_tw_etf_universe" in tabs:
            rows = con.execute("SELECT etf_ticker, MAX(etf_name), MAX(COALESCE(issuer,'')), CAST(MIN(snapshot_at) AS VARCHAR) FROM active_tw_etf_universe GROUP BY 1 ORDER BY 1").fetchall()
            return [{"ticker": t, "name": n, "issuer": i, "first_seen": str(f)[:10]} for t, n, i, f in rows]
    finally:
        con.close()
    return []


def snapshot_dates() -> dict[str, list[str]]:
    if not DB_ETF.exists():
        return {}
    import duckdb
    con = duckdb.connect(str(DB_ETF), read_only=True)
    try:
        if "holdings_daily" not in {t for (t,) in con.execute("SHOW TABLES").fetchall()}:
            return {}
        rows = con.execute("SELECT etf_ticker, CAST(portfolio_date AS VARCHAR) FROM holdings_daily GROUP BY 1,2 ORDER BY 1,2").fetchall()
    finally:
        con.close()
    out = {}
    for t, d in rows:
        out.setdefault(t, []).append(d[:10])
    return out


def trading_days(start: str, end: str) -> list[str]:
    """真實交易日曆(tw_daily_prices 之 distinct date);缺=平日(誠實標 WEEKDAY_CAL)"""
    days = []
    if DB_TW.exists():
        try:
            import duckdb
            con = duckdb.connect(str(DB_TW), read_only=True)
            try:
                days = [str(r[0])[:10] for r in con.execute(
                    "SELECT DISTINCT CAST(date AS VARCHAR) d FROM tw_daily_prices WHERE CAST(date AS VARCHAR) >= ? AND CAST(date AS VARCHAR) <= ? ORDER BY d", [start, end]).fetchall()]
            finally:
                con.close()
        except Exception:
            days = []
    if days:
        # 交易日曆尾端可能落後今日:以平日補至 end(標記)
        last = date.fromisoformat(days[-1])
        d = last + timedelta(days=1)
        while d.isoformat() <= end:
            if d.weekday() < 5:
                days.append(d.isoformat())
            d += timedelta(days=1)
        return days
    d = date.fromisoformat(start)
    e = date.fromisoformat(end)
    while d <= e:
        if d.weekday() < 5:
            days.append(d.isoformat())
        d += timedelta(days=1)
    return days


def resolve_listing(u: dict, snaps: list[str], net=None, ck: dict = None) -> tuple[str, str]:
    """(listing_date, source);L1 registry 冊上市日(未來欄位)→ L2 yf_history 首根 K(親跑同意)→ L3 首快照=下界"""
    ck = ck if ck is not None else {}
    cached = ck.get("listing", {}).get(u["ticker"])
    if cached and cached.get("src") in ("REGISTRY", "YF_FIRST_BAR"):
        return cached["date"], cached["src"]
    if net is not None and hasattr(net, "yf_history"):
        try:
            r = net.yf_history([u["ticker"] + ".TW"], ACTIVE_ETF_ERA, date.today().isoformat())
            rows = [x for x in (r.get("rows") or []) if x.get("date")]
            if rows:
                first = min(str(x["date"])[:10] for x in rows)
                ck.setdefault("listing", {})[u["ticker"]] = {"date": first, "src": "YF_FIRST_BAR"}
                return first, "YF_FIRST_BAR"
        except Exception:
            pass
    if snaps:
        return snaps[0], "LOWER_BOUND(first snapshot)"
    return u.get("first_seen") or ACTIVE_ETF_ERA, "LOWER_BOUND(first_seen)"


# ---------------------------------------------------------------- 覆蓋帳
def coverage(net=None, ck: dict = None) -> dict:
    ck = ck if ck is not None else _load_ckpt()
    us = universe()
    if not us:
        return {"state": "SKIP", "note": "宇宙缺(先 via-etfuniv)", "etfs": []}
    snaps = snapshot_dates()
    today = date.today().isoformat()
    out = []
    for u in us:
        s = snaps.get(u["ticker"], [])
        lst, lsrc = resolve_listing(u, s, net, ck)
        exp = trading_days(lst, today)
        have = set(s)
        missing = [d for d in exp if d not in have]
        st = ck.setdefault("days", {}).setdefault(u["ticker"], {})
        for d in missing:
            st.setdefault(d, {"state": "MISSING"})
        exp_set = set(exp)
        for d in have:
            if d in exp_set:
                st[d] = {"state": "FILLED"}
        n_nosrc = sum(1 for d in missing if st.get(d, {}).get("state") == "NO_SOURCE")
        n_today = sum(1 for d in missing if st.get(d, {}).get("state") == "PENDING_TODAY")
        pct = round(100.0 * len(have & set(exp)) / len(exp), 1) if exp else 0.0
        state = "COMPLETE" if not missing else ("PENDING_SOURCE" if (n_nosrc + n_today == len(missing) and n_nosrc) else "PARTIAL")
        out.append({"ticker": u["ticker"], "name": u["name"], "issuer": u["issuer"], "listing": lst, "listing_src": lsrc,
                    "first_snapshot": s[0] if s else "", "last_snapshot": s[-1] if s else "", "expected_days": len(exp), "have_days": len(have & set(exp)),
                    "missing_days": len(missing), "no_source_days": n_nosrc, "coverage_pct": pct, "state": state,
                    "missing_head": missing[-5:][::-1], "today_ok": today in have})
    _save_ckpt(ck)
    return {"state": "OK", "etfs": out, "today": today}


# ---------------------------------------------------------------- 回補(車道冊)
# ---------------------------------------------------------------- 批406:發現 / 解析 / 探測
# TWSE OpenAPI 規格檔候選(真列舉之入口;非資料端點猜測)。取不到=誠實 UNREACHABLE。
TWSE_SPEC_CANDIDATES = (
    "https://openapi.twse.com.tw/swagger/v1/swagger.json",
    "https://openapi.twse.com.tw/v1/swagger.json",
    "https://openapi.twse.com.tw/openapi.json",
    "https://openapi.twse.com.tw/swagger/docs/v1",
)
# 篩選詞:主動 ETF 每日持股揭露之可能名目(中英並列;寧可多列候選,由 probe 驗真)
HOLDING_HINTS = ("ETF", "成分", "持股", "投資組合", "申購買回", "PCF", "基金",
                 "holding", "constituent", "portfolio", "fund")
MIN_HOLD_ROWS = 5                      # 少於此列數=不算持股表(誠實不硬填)
TW_CODE_RX = re.compile(r"^\d{4}[A-Z]?$")
_NUM_RX = re.compile(r"-?[\d,]+(?:\.\d+)?")


def _num_or_none(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = _NUM_RX.search(str(v).replace(",", ""))
    return float(m.group(0)) if m else None


def parse_holdings(payload) -> list[dict]:
    """JSON(list[dict])或 HTML 表 → [{holding_ticker,name,shares,weight}]。
    判準:≥MIN_HOLD_ROWS 列、每列四碼台股代號可辨、股數或權重至少一個是數字。
    不合=回 []( 誠實:寧可空,不硬填)。"""
    rows: list[dict] = []
    if isinstance(payload, list):
        for it in payload:
            if not isinstance(it, dict):
                continue
            code = name = ""
            shares = weight = None
            for k, v in it.items():
                ks = str(k)
                sv = "" if v is None else str(v).strip()
                if not code and TW_CODE_RX.match(sv) and any(t in ks for t in ("代號", "代碼", "code", "Code", "ticker", "股票")):
                    code = sv
                elif not name and any(t in ks for t in ("名稱", "簡稱", "name", "Name")):
                    name = sv
                elif shares is None and any(t in ks for t in ("股數", "數量", "shares", "Shares", "quantity")):
                    shares = _num_or_none(v)
                elif weight is None and any(t in ks for t in ("權重", "比重", "比率", "weight", "Weight", "percent", "%")):
                    weight = _num_or_none(v)
            if not code:                      # 欄名不合慣例時:退而找任一四碼值
                for v in it.values():
                    sv = "" if v is None else str(v).strip()
                    if TW_CODE_RX.match(sv):
                        code = sv
                        break
            if code and (shares is not None or weight is not None):
                rows.append({"holding_ticker": code, "name": name,
                             "shares": shares, "weight": weight})
    elif isinstance(payload, str):
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", payload, re.S | re.I):
            cells = [re.sub(r"<[^>]+>", "", c).strip()
                     for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
            code = next((c for c in cells if TW_CODE_RX.match(c)), "")
            if not code:
                continue
            nums = [_num_or_none(c) for c in cells if _num_or_none(c) is not None and not TW_CODE_RX.match(c)]
            nm = next((c for c in cells if c and not TW_CODE_RX.match(c) and _num_or_none(c) is None), "")
            if nums:
                rows.append({"holding_ticker": code, "name": nm,
                             "shares": nums[0], "weight": nums[-1] if len(nums) > 1 else None})
    return rows if len(rows) >= MIN_HOLD_ROWS else []


# 倉內既驗證事實(ENG054/ENG055/ENG077 現役常數):TWSE openapi 之 base 含 /v1。
TWSE_FALLBACK_BASE = "https://openapi.twse.com.tw/v1"


def spec_base(body: dict, spec_url: str) -> str:
    """自規格檔推導 base(路徑是相對 base,非相對主機根)。
    ① OpenAPI3 servers[0].url(絕對直用;相對接主機)② Swagger2 schemes+host+basePath
    ③ 皆無=退倉內既驗證之 TWSE_FALLBACK_BASE。批406b:漏 /v1 導致全 404 之修。"""
    try:
        srv = (body.get("servers") or [{}])[0].get("url") or ""
    except Exception:
        srv = ""
    if srv:
        if srv.startswith("http"):
            return srv.rstrip("/")
        m = re.match(r"(https?://[^/]+)", spec_url)
        return ((m.group(1) if m else "") + "/" + srv.lstrip("/")).rstrip("/")
    host = body.get("host") or ""
    if host:
        sch = (body.get("schemes") or ["https"])[0]
        return (f"{sch}://{host}" + (body.get("basePath") or "")).rstrip("/")
    bp = body.get("basePath") or ""
    m = re.match(r"(https?://[^/]+)", spec_url)
    if m and bp:
        return (m.group(1) + bp).rstrip("/")
    return TWSE_FALLBACK_BASE


def discover_twse(net=None, apply: bool = False, do_print: bool = True) -> dict:
    """自 TWSE OpenAPI 規格真列舉資料集,關鍵字篩候選 → 車道冊 state=CANDIDATE。
    規格全取不到=UNREACHABLE 誠實列已試路徑(不臆造端點)。"""
    tried, hits, spec_used = [], [], ""
    if net is None:
        if do_print:
            print("[發現] 網路工具缺席或雙閘未開=誠實停(via-etfhist 自帶 YES;或先 via-net)")
        return {"state": "NO_NET", "tried": [], "candidates": []}
    for u in TWSE_SPEC_CANDIDATES:
        tried.append(u)
        try:
            r = net.http_json(u)
        except Exception as exc:
            if do_print:
                print(f"  [試] {u} → 例外 {type(exc).__name__}")
            continue
        if not isinstance(r, dict) or r.get("state") != "OK":
            if do_print:
                print(f"  [試] {u} → {str((r or {}).get('state', '?'))}:{str((r or {}).get('note', ''))[:60]}")
            continue
        body = r.get("data")
        if not isinstance(body, dict) or "paths" not in body:
            if do_print:
                print(f"  [試] {u} → 非 OpenAPI 規格(無 paths)")
            continue
        spec_used = u
        for path, ops in (body.get("paths") or {}).items():
            blob = path + " " + json.dumps(ops, ensure_ascii=False)[:400]
            if any(h.lower() in blob.lower() for h in HOLDING_HINTS):
                hits.append({"path": path, "summary": str(
                    (ops.get("get") or {}).get("summary", ""))[:80]})
        break
    if not spec_used:
        if do_print:
            print(f"[發現] TWSE OpenAPI 規格四路皆取不到=UNREACHABLE(誠實;不臆造端點)。已試:{len(tried)} 路")
        return {"state": "UNREACHABLE", "tried": tried, "candidates": []}
    base = spec_base(body, spec_used)
    cands = [{"id": f"TWSE_OPENAPI:{h['path']}", "kind": "DATED", "state": "CANDIDATE",
              "url": base + "/" + h["path"].lstrip("/"),
              "note": f"discover 自規格列舉(base {base}):{h['summary']}"}
             for h in hits]
    if do_print:
        print(f"[發現] 規格 {spec_used} · base {spec_base(body, spec_used)} · 命中 {len(hits)} 條(關鍵字 {'/'.join(HOLDING_HINTS[:4])}…)")
        for h in hits[:20]:
            print(f"    {h['path']}  {h['summary']}")
    if apply and cands:
        lanes = load_lanes()
        by_id = {l["id"]: l for l in lanes.get("lanes", [])}
        add, fixed = [], 0
        for c in cands:
            cur = by_id.get(c["id"])
            if cur is None:
                add.append(c)                                    # 只增不減
            elif cur.get("state") != "VERIFIED" and cur.get("url") != c["url"]:
                cur["url"] = c["url"]                            # 批406b:修既有 CANDIDATE 的錯 base
                cur["note"] = c["note"]
                fixed += 1
        lanes["lanes"].extend(add)
        LANES_JSON.write_text(json.dumps(lanes, ensure_ascii=False, indent=1), encoding="utf-8")
        if do_print:
            print(f"[發現] 車道冊 +{len(add)} 條 CANDIDATE · 修正既有 url {fixed} 條(VERIFIED 不動;probe 過才升)")
    return {"state": "OK", "spec": spec_used, "tried": tried, "candidates": cands}


def probe_lanes(ticker: str = "", day: str = "", net=None, apply: bool = False,
                do_print: bool = True) -> dict:
    """對有 url 之非 VERIFIED 車道取一次並跑 parse_holdings 驗證;--apply 只升通過者。"""
    lanes = load_lanes()
    if net is None:
        if do_print:
            print("[探測] 網路工具缺席或雙閘未開=誠實停")
        return {"state": "NO_NET", "rows": []}
    us = universe()
    tk = ticker or (us[0]["ticker"] if us else "")
    d = day or date.today().isoformat()
    out, passed = [], 0
    for l in lanes.get("lanes", []):
        if l.get("state") == "VERIFIED" or not l.get("url"):
            continue
        url = (l["url"].replace("{yf}", tk).replace("{code}", tk)
               .replace("{ymd}", d.replace("-", "")).replace("{date}", d))
        why, n = "", 0
        try:
            r = net.http_json(url)
            body = r.get("data") if isinstance(r, dict) and r.get("state") == "OK" else None
            if body is None:
                r2 = net.http_text(url)
                body = r2.get("data") if isinstance(r2, dict) and r2.get("state") == "OK" else None
                if body is None:
                    why = f"{str((r or {}).get('state', '?'))}:{str((r or {}).get('note', ''))[:50]}"
            if body is not None:
                rows = parse_holdings(body)
                n = len(rows)
                if not rows:
                    why = "零可解析持股列(非持股表/需登入/該日無資料)"
        except Exception as exc:
            why = f"取用失敗 {type(exc).__name__}"
        ok = n >= MIN_HOLD_ROWS
        passed += 1 if ok else 0
        out.append({"id": l["id"], "url": url, "rows": n, "pass": ok, "why": why})
        if do_print:
            print(f"  [{'PASS' if ok else 'FAIL'}] {l['id'][:44]:<44} 列 {n:>4}  {why}")
        if ok and apply:
            l["state"] = "VERIFIED"
            l["note"] = (l.get("note", "") + f" · probe 驗過({tk} {d} {n} 列)").strip(" ·")
    if apply:
        LANES_JSON.write_text(json.dumps(lanes, ensure_ascii=False, indent=1), encoding="utf-8")
    if do_print:
        print(f"[探測] {len(out)} 條 · PASS {passed} · {'已寫回車道冊(只升通過者)' if apply else 'dry-run(加 --apply 才寫)'}")
    return {"state": "OK", "ticker": tk, "date": d, "rows": out, "passed": passed}


def fetch_dated(lane: dict, ticker: str, day: str, net) -> list[dict]:
    """VERIFIED DATED 車道取某日持股;失敗/不合判準=回 [](誠實)"""
    url = (lane["url"].replace("{yf}", ticker).replace("{code}", ticker)
           .replace("{ymd}", day.replace("-", "")).replace("{date}", day))
    try:
        r = net.http_json(url)
        body = r.get("data") if isinstance(r, dict) and r.get("state") == "OK" else None
        if body is None:
            r = net.http_text(url)
            body = r.get("data") if isinstance(r, dict) and r.get("state") == "OK" else None
    except Exception:
        return []
    if isinstance(body, (bytes, bytearray)):
        body = body.decode("utf-8", "replace")
    return parse_holdings(body) if body is not None else []


# ENG051 正本表:本器只補列、不改結構。欄位以現表為準(欄名對映;缺欄不寫)。
_HOLD_MAP = {"portfolio_date": "day", "etf_ticker": "etf", "etf_yf_ticker": "etf_yf",
             "holding_ticker": "code", "holding_yf_ticker": "code_yf",
             "holding_name": "name", "weight_pct": "weight", "weight": "weight",
             "shares": "shares", "source_type": "src", "source_url": "url"}


def upsert_holdings(ticker: str, day: str, rows: list[dict], src_url: str = "") -> int:
    """補列進 ENG051 正本 holdings_daily(anti-join (portfolio_date, etf_ticker,
    holding_ticker);只增不減;**不建表不改結構**——表缺=誠實回 0,先跑 ENG051)。
    欄名以現表 DESCRIBE 為準逐欄對映,缺欄不寫,故不同版 schema 皆安全。"""
    if not rows or not DB_ETF.exists():
        return 0
    import duckdb
    con = duckdb.connect(str(DB_ETF))
    try:
        if "holdings_daily" not in {t for (t,) in con.execute("SHOW TABLES").fetchall()}:
            return 0                       # 正本表未建:不代建(ENG051 擁有結構)
        cols = [r[0] for r in con.execute("DESCRIBE holdings_daily").fetchall()]
        use = [c for c in cols if c in _HOLD_MAP]
        if "portfolio_date" not in use or "etf_ticker" not in use or "holding_ticker" not in use:
            return 0                       # 鍵欄不齊=誠實不寫
        have = {r[0] for r in con.execute(
            "SELECT holding_ticker FROM holdings_daily WHERE CAST(portfolio_date AS VARCHAR)=? AND etf_ticker=?",
            [day, ticker]).fetchall()}
        vals = {"day": day, "etf": ticker, "etf_yf": ticker + ".TW", "src": "ENG078_DATED", "url": src_url}
        n = 0
        for r in rows:
            if r["holding_ticker"] in have:
                continue
            vals.update({"code": r["holding_ticker"], "code_yf": r["holding_ticker"] + ".TW",
                         "name": r.get("name", ""), "shares": r.get("shares"),
                         "weight": r.get("weight")})
            con.execute(f"INSERT INTO holdings_daily ({','.join(use)}) VALUES ({','.join('?' * len(use))})",
                        [vals[_HOLD_MAP[c]] for c in use])
            n += 1
        return n
    finally:
        con.close()


def lane_for(issuer: str, lanes: dict) -> list[dict]:
    ls = [l for l in lanes.get("lanes", []) if l.get("state") == "VERIFIED" and (l["id"] == f"ISSUER_ARCHIVE:{issuer}" or l["id"] == "MONEYDJ")]
    return sorted(ls, key=lambda l: 0 if l["kind"] == "DATED" else 1)


def backfill(max_days: int = 0, net=None) -> dict:
    """自 IPO 逐日(從新往舊):VERIFIED DATED 車道才呼;LATEST_ONLY 只能補今日;其餘=NO_SOURCE 誠實"""
    lanes = load_lanes()
    ck = _load_ckpt()
    cov = coverage(net, ck)
    if cov["state"] != "OK":
        return cov
    today = cov["today"]
    filled, nosrc, tried = 0, 0, 0
    for e in cov["etfs"]:
        st = ck["days"].get(e["ticker"], {})
        days = sorted([d for d, v in st.items() if v.get("state") == "MISSING"], reverse=True)
        if max_days:
            days = days[:max_days]
        ls = lane_for(e["issuer"], lanes)
        dated = [l for l in ls if l["kind"] == "DATED"]
        for d in days:
            tried += 1
            if d == today and any(l["kind"] == "LATEST_ONLY" for l in ls):
                st[d] = {"state": "PENDING_TODAY", "note": "今日快照由 ENG051(boot ④)抓;本器不重抓"}
                continue
            if not dated:
                st[d] = {"state": "NO_SOURCE", "note": f"發行商 {e['issuer']} 歷史 PCF 車道 PENDING_SOURCE(車道冊未驗證)"}
                nosrc += 1
                continue
            # 批406:VERIFIED DATED 車道真取真解析真落庫(v0100 此處為佔位)
            got = 0
            used = ""
            for l in dated:
                if net is None:
                    break
                hs = fetch_dated(l, e["ticker"], d, net)
                if hs:
                    got = upsert_holdings(e["ticker"], d, hs, l.get("url", ""))
                    used = l["id"]
                    break
            if got:
                st[d] = {"state": "FILLED", "note": f"{used} · {got} 列"}
                filled += 1
            else:
                st[d] = {"state": "NO_SOURCE", "note": (
                    "DATED 車道取用/解析皆空(來源當日無資料或需登入)" if net is not None
                    else "雙閘未開=不外呼(誠實)")}
                nosrc += 1
    _save_ckpt(ck)
    return {"state": "OK", "tried": tried, "filled": filled, "no_source": nosrc, "verified_dated_lanes": sum(1 for l in lanes["lanes"] if l["state"] == "VERIFIED" and l["kind"] == "DATED")}


# ---------------------------------------------------------------- 落地/頁
def persist(cov: dict) -> None:
    import duckdb
    con = duckdb.connect(str(DB_ETF))
    try:
        con.execute(f"""CREATE TABLE IF NOT EXISTS {COV_TABLE}(asof_date VARCHAR, ticker VARCHAR, name VARCHAR, issuer VARCHAR, listing VARCHAR, listing_src VARCHAR,
            first_snapshot VARCHAR, last_snapshot VARCHAR, expected_days INTEGER, have_days INTEGER, missing_days INTEGER, no_source_days INTEGER,
            coverage_pct DOUBLE, state VARCHAR, computed_at VARCHAR)""")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        con.execute(f"DELETE FROM {COV_TABLE} WHERE asof_date = ?", [cov["today"]])   # 同日覆蓋帳重算=同鍵替換(帳不是原始資料)
        con.executemany(f"INSERT INTO {COV_TABLE} VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        [(cov["today"], e["ticker"], e["name"], e["issuer"], e["listing"], e["listing_src"], e["first_snapshot"], e["last_snapshot"],
                          e["expected_days"], e["have_days"], e["missing_days"], e["no_source_days"], e["coverage_pct"], e["state"], ts) for e in cov["etfs"]])
    finally:
        con.close()


def render(cov: dict, lanes: dict, bf: dict | None) -> str:
    e = html.escape

    def b(s):
        c = {"COMPLETE": "gr", "PARTIAL": "ye", "PENDING_SOURCE": "rd", "VERIFIED": "gr"}.get(s, "gy")
        return '<span class="b ' + c + '">' + e(s) + "</span>"
    rows = "".join('<tr><td class="m"><b>' + e(x["ticker"]) + "</b><br>" + e(x["name"]) + '<br><span class="dim">' + e(x["issuer"]) + "</span></td><td class=\"m\">" + e(x["listing"])
                   + '<br><span class="dim">' + e(x["listing_src"]) + "</span></td><td class=\"c m\">" + e(x["first_snapshot"] or "—") + "<br>" + e(x["last_snapshot"] or "—")
                   + '</td><td class="c m">' + str(x["have_days"]) + "/" + str(x["expected_days"]) + "<br>" + str(x["coverage_pct"]) + "%</td><td class=\"c\">" + b(x["state"])
                   + ("<br><span class=\"b gr\">today</span>" if x["today_ok"] else "") + '</td><td class="m dim">' + e(", ".join(x["missing_head"])) + "</td></tr>" for x in cov["etfs"])
    lrows = "".join('<tr><td class="m">' + e(l["id"]) + "</td><td class=\"c\">" + e(l["kind"]) + "</td><td class=\"c\">" + b(l["state"]) + '</td><td class="m dim">' + e(l.get("url", "")) + "<br>" + e(l.get("note", "")) + "</td></tr>"
                    for l in lanes.get("lanes", []))
    n = {k: sum(1 for x in cov["etfs"] if x["state"] == k) for k in ("COMPLETE", "PARTIAL", "PENDING_SOURCE")}
    bft = (f'tried {bf["tried"]} · filled {bf["filled"]} · no_source {bf["no_source"]} · verified DATED lanes {bf["verified_dated_lanes"]}' if bf and bf.get("state") == "OK" else "—")
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA · 主動 ETF 持股史深</title>
<style>:root{{--bg:#0f172a;--card:#1e293b;--line:#334155;--tx:#f8fafc;--mu:#94a3b8}}*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);font:11px/1.35 -apple-system,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif}}.wrap{{max-width:1300px;margin:0 auto;padding:18px 14px 48px}}
h1{{font-size:14px;margin:0}}.sub{{color:var(--mu);margin:3px 0 14px}}h2{{font-size:12px;margin:20px 0 7px;border-bottom:1px solid var(--line);padding-bottom:5px}}.nav a{{color:#7dd3fc;margin-right:12px;text-decoration:none}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin-bottom:14px}}.kpi{{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:9px 11px}}.kpi .n{{font-size:17px;font-weight:600}}.kpi .l{{font-size:10px;color:var(--mu)}}
table{{width:100%;table-layout:fixed;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}}th{{font-size:10px;color:var(--mu);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}}td{{padding:4px 6px;border-bottom:1px solid #253248;vertical-align:top;word-wrap:break-word;overflow-wrap:break-word}}td.c{{text-align:center}}.m{{font-family:ui-monospace,Consolas,monospace;font-size:10px}}.dim{{color:var(--mu)}}
.b{{display:inline-block;font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid}}.gr{{background:#064e3b;color:#34d399;border-color:#059669}}.ye{{background:#78350f;color:#fde047;border-color:#d97706}}.rd{{background:#7f1d1d;color:#fca5a5;border-color:#dc2626}}.gy{{background:#1f2937;color:#9ca3af;border-color:#374151}}
.note{{background:var(--card);border:1px solid var(--line);border-left:3px solid #d97706;border-radius:3px;padding:10px 12px;margin-top:16px}}
@media(max-width:700px){{table,thead,tbody,tr,td,th{{display:block}}thead{{display:none}}td{{border:0;padding:2px 6px}}tr{{border-bottom:1px solid var(--line);padding:6px 0}}}}</style></head><body><div class="wrap">
<h1>ACTIVE TW ETF · DAILY HOLDINGS COVERAGE SINCE IPO</h1><p class="sub">VDF_ENG078 · asof {e(cov["today"])} · backfill {e(bft)}</p>
<p class="nav"><a href="VIA_UI_ProjectCompletion_v0100.html">竣</a><a href="VIA_UI_ETFRevenueMomentum_v0100.html">ETF×營收</a><a href="VIA_UI_ETFConsensusAnalysis_v0100.html">ETF×共識</a></p>
<div class="kpis"><div class="kpi"><div class="n">{len(cov["etfs"])}</div><div class="l">daily-required ETFs</div></div><div class="kpi"><div class="n">{n["COMPLETE"]}</div><div class="l">complete since IPO</div></div>
<div class="kpi"><div class="n">{n["PARTIAL"]}</div><div class="l">partial</div></div><div class="kpi"><div class="n">{n["PENDING_SOURCE"]}</div><div class="l">pending source</div></div>
<div class="kpi"><div class="n">{sum(1 for x in cov["etfs"] if x["today_ok"])}</div><div class="l">today captured</div></div></div>
<h2>COVERAGE — per ETF (listing → today; real trading calendar)</h2>
<table><colgroup><col style="width:22%"><col style="width:16%"><col style="width:14%"><col style="width:12%"><col style="width:12%"><col style="width:24%"></colgroup>
<thead><tr><th>ETF</th><th>listing (src)</th><th>first / last snapshot</th><th>have/expected</th><th>state</th><th>latest missing</th></tr></thead><tbody>{rows}</tbody></table>
<h2>LANES — history sources (only-add registry; VERIFIED lanes are called)</h2>
<table><colgroup><col style="width:26%"><col style="width:12%"><col style="width:14%"><col style="width:48%"></colgroup><thead><tr><th>lane</th><th>kind</th><th>state</th><th>url · note</th></tr></thead><tbody>{lrows}</tbody></table>
<div class="note">每日機制:boot ④ ENG051 抓今日持股 → ④b 本器算覆蓋+補缺;從今起零缺口。IPO 以來史段=各發行商 PCF 歷史頁(車道冊 PENDING_SOURCE;工作站驗證 URL 後改 VERIFIED 即逐日回補);MoneyDJ 只有最新日。缺源日=NO_SOURCE,永不假填。</div>
</div></body></html>"""


def daily(args: list[str]) -> int:
    offline = "--offline" in args
    net = None
    if not offline and gate_open():
        net = _net_or_none()
    lanes = load_lanes()
    bf = backfill(max_days=int(args[args.index("--max-days") + 1]) if "--max-days" in args else 5, net=net)
    cov = coverage(net)   # 回補後重算=頁與帳反映本輪終態
    if cov["state"] != "OK":
        print(f"[持股史深] SKIP {cov['note']}")
        return 0
    persist(cov)
    REP.mkdir(parents=True, exist_ok=True)
    (REP / f"COVERAGE_{cov['today']}.json").write_text(json.dumps({"coverage": cov, "backfill": bf, "lanes": lanes}, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_UI.parent.mkdir(parents=True, exist_ok=True)
    OUT_UI.write_text(render(cov, lanes, bf), encoding="utf-8")
    n = {k: sum(1 for x in cov["etfs"] if x["state"] == k) for k in ("COMPLETE", "PARTIAL", "PENDING_SOURCE")}
    print(f"[持股史深] {len(cov['etfs'])} 檔須每日揭露 · 今日已抓 {sum(1 for x in cov['etfs'] if x['today_ok'])} · COMPLETE {n['COMPLETE']} PARTIAL {n['PARTIAL']} PENDING_SOURCE {n['PENDING_SOURCE']}"
          f" · 回補 tried {bf.get('tried')} filled {bf.get('filled')} no_source {bf.get('no_source')} · VERIFIED DATED 車道 {bf.get('verified_dated_lanes')} · {OUT_UI.name}")
    for x in cov["etfs"][:6]:
        print(f"  {x['ticker']} 上市 {x['listing']}({x['listing_src'][:22]})· 快照 {x['have_days']}/{x['expected_days']}({x['coverage_pct']}%)· {x['state']}")
    return 0


def status() -> int:
    ck = _load_ckpt()
    days = ck.get("days", {})
    tot = sum(len(v) for v in days.values())
    st = {}
    for v in days.values():
        for d in v.values():
            st[d["state"]] = st.get(d["state"], 0) + 1
    print(f"  checkpoint 日格 {tot} · {st} · 車道冊 {'在' if LANES_JSON.exists() else '缺'}")
    return 0


def selftest() -> int:
    import tempfile
    global DB_ETF, DB_TW, REP, CKPT, OUT_UI, LANES_JSON
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    _s = (DB_ETF, DB_TW, REP, CKPT, OUT_UI, LANES_JSON)
    with tempfile.TemporaryDirectory() as td:
        import duckdb
        DB_ETF, DB_TW = Path(td) / "etf.duckdb", Path(td) / "tw.duckdb"
        REP, CKPT, OUT_UI, LANES_JSON = Path(td) / "rep", Path(td) / "ck.json", Path(td) / "p.html", Path(td) / "lanes.json"
        today = date.today()
        d = [today - timedelta(days=k) for k in range(0, 14)]
        wd = [x.isoformat() for x in sorted(d) if x.weekday() < 5]
        c = duckdb.connect(str(DB_TW))
        c.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE)")
        c.executemany("INSERT INTO tw_daily_prices VALUES (?,?,?)", [(x, "2330", 1.0) for x in wd[:-1]])   # 交易日曆落後今日一天
        c.close()
        c = duckdb.connect(str(DB_ETF))
        c.execute("CREATE TABLE active_tw_etf_registry(ticker VARCHAR, name VARCHAR, fund_type VARCHAR, domestic BOOLEAN, daily_required BOOLEAN, status VARCHAR, source VARCHAR, issuer VARCHAR, first_seen VARCHAR, last_seen VARCHAR)")
        c.execute("INSERT INTO active_tw_etf_registry VALUES ('00981A','強棒','x',TRUE,TRUE,'ACTIVE_DOMESTIC','t','群益投信',?,?), ('00402A','美科','x',FALSE,FALSE,'FOREIGN_COMPONENT','t','安聯投信',?,?)", [wd[0], wd[-1], wd[0], wd[-1]])
        c.execute("CREATE TABLE holdings_daily(portfolio_date DATE, etf_ticker VARCHAR, holding_ticker VARCHAR, weight_pct DOUBLE)")
        c.executemany("INSERT INTO holdings_daily VALUES (?,?,?,?)", [(wd[-1], "00981A", "2330", 10.0), (wd[-2], "00981A", "2330", 10.0), (wd[3], "00981A", "2330", 10.0)])
        c.close()
        cov = coverage(None)
        e = cov["etfs"]
        chk("① 宇宙=daily_required 者(國外成分不入);上市日=L3 首快照下界(誠實標)", len(e) == 1 and e[0]["ticker"] == "00981A" and e[0]["listing"] == wd[3] and e[0]["listing_src"].startswith("LOWER_BOUND"))
        exp_n = len([x for x in wd if x >= wd[3]])
        chk("② 應有交易日=真實日曆(尾端平日補至今)·缺口逐日 MISSING·今日已抓", e[0]["expected_days"] == exp_n and e[0]["have_days"] == 3 and e[0]["missing_days"] == exp_n - 3 and e[0]["today_ok"] == (wd[-1] == today.isoformat()), f"{e[0]['expected_days']} {e[0]['missing_days']}")
        ck = _load_ckpt()
        chk("③ checkpoint 日格(MISSING/FILLED;只改態不刪)", all(v["state"] in ("MISSING", "FILLED") for v in ck["days"]["00981A"].values()) and ck["days"]["00981A"][wd[3]]["state"] == "FILLED")
        lanes = load_lanes()
        bf = backfill(max_days=0, net=None)
        ck2 = _load_ckpt()
        states = {v["state"] for v in ck2["days"]["00981A"].values()}
        chk("④ 回補誠實(車道冊 VERIFIED DATED=0 → 缺口全 NO_SOURCE;零假填;LATEST_ONLY 只留今日 PENDING_TODAY)",
            bf["verified_dated_lanes"] == 0 and bf["filled"] == 0 and bf["no_source"] >= 1 and "NO_SOURCE" in states and "MISSING" not in states and LANES_JSON.exists())
        cov2 = coverage(None)
        chk("⑤ 覆蓋態(缺口全無源=PENDING_SOURCE;部分有源=PARTIAL;COMPLETE 需零缺口)", cov2["etfs"][0]["state"] in ("PENDING_SOURCE", "PARTIAL") and cov2["etfs"][0]["no_source_days"] >= 1 and cov2["etfs"][0]["missing_days"] >= cov2["etfs"][0]["no_source_days"])
        persist(cov2)
        persist(cov2)
        c = duckdb.connect(str(DB_ETF), read_only=True)
        n = c.execute(f"SELECT COUNT(*) FROM {COV_TABLE}").fetchone()[0]
        c.close()
        chk("⑥ 覆蓋帳落庫同日重算=同鍵替換(帳非原始資料;1 列)", n == 1)
        OUT_UI.write_text(render(cov2, lanes, bf), encoding="utf-8")
        h = OUT_UI.read_text(encoding="utf-8")
        chk("⑦ 頁(手機單欄;零 CDN;車道冊表;COVERAGE 表)", "@media" in h and 'src="http' not in h and "LANES" in h and "COVERAGE" in h)
    DB_ETF, DB_TW, REP, CKPT, OUT_UI, LANES_JSON = _s
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(只增不減/誠實三態/零假造/PENDING_SOURCE/永不假填/親跑同意)", all(k in src for k in ("只增不減", "誠實三態", "零假造", "PENDING_SOURCE", "永不假填", "親跑同意")))

    # --- 批406 四檢:發現 / 解析 / 探測 / DATED 真回補(全注入式假 net,零外呼)---
    js = [{"股票代號": f"23{i:02d}", "股票名稱": f"股{i}", "股數": f"{i},000", "權重(%)": i / 2}
          for i in range(1, 9)]
    htm = "<table>" + "".join(
        f"<tr><td>13{i:02d}</td><td>名{i}</td><td>{i},500</td><td>{i}.5</td></tr>"
        for i in range(1, 7)) + "</table>"
    chk("⑨ 持股解析雙道(JSON 欄名對映 + HTML 表;四碼代號與數字皆須可辨)",
        len(parse_holdings(js)) == 8 and parse_holdings(js)[0]["holding_ticker"] == "2301"
        and parse_holdings(js)[0]["shares"] == 1000.0
        and len(parse_holdings(htm)) == 6 and parse_holdings(htm)[0]["holding_ticker"] == "1301")
    chk("⑩ 解析判準誠實(少於門檻/非持股 payload/空 → 一律回空,不硬填)",
        parse_holdings(js[:3]) == [] and parse_holdings([{"x": 1}, {"x": 2}]) == []
        and parse_holdings("<table><tr><td>hello</td></tr></table>") == []
        and parse_holdings(None) == [] and parse_holdings([]) == [])

    class _NetSpec:
        """假 net:第 2 條規格路才通,持股 URL 回真表;其餘 FAIL(模擬真實不確定)"""
        def http_json(self, url, timeout=30):
            if url == TWSE_SPEC_CANDIDATES[1]:
                return {"state": "OK", "data": {"paths": {
                    "/v1/opendata/t187ap47_L": {"get": {"summary": "ETF 基金基本資料"}},
                    "/v1/fund/holdings": {"get": {"summary": "基金持股明細"}},
                    "/v1/exchangeReport/STOCK_DAY": {"get": {"summary": "每日收盤"}}}}}
            if "holdings" in url:
                return {"state": "OK", "data": js}
            return {"state": "FAIL", "note": "404"}
        def http_text(self, url, timeout=30):
            return {"state": "FAIL", "note": "404"}

    class _NetDead:
        def http_json(self, url, timeout=30):
            return {"state": "FAIL", "note": "blocked"}
        def http_text(self, url, timeout=30):
            return {"state": "FAIL", "note": "blocked"}

    with tempfile.TemporaryDirectory() as td2:
        LANES_JSON = Path(td2) / "lanes.json"
        globals()["LANES_JSON"] = LANES_JSON
        d1 = discover_twse(net=_NetSpec(), apply=True, do_print=False)
        lanes1 = load_lanes()
        ids1 = [l["id"] for l in lanes1["lanes"]]
        d0 = discover_twse(net=_NetDead(), apply=True, do_print=False)
        chk("⑪ 發現=自 OpenAPI 規格真列舉(關鍵字命中才收;規格全不通=UNREACHABLE 誠實;"
            "只增不減、CANDIDATE 不冒充 VERIFIED)",
            d1["state"] == "OK" and len(d1["candidates"]) == 2
            and any("fund/holdings" in i for i in ids1)
            and all(l["state"] != "VERIFIED" for l in lanes1["lanes"] if l["id"].startswith("TWSE_OPENAPI"))
            and d0["state"] == "UNREACHABLE" and len(d0["tried"]) == len(TWSE_SPEC_CANDIDATES),
            f"({d1['state']}/{len(d1['candidates'])};{d0['state']})")
        before = len(load_lanes()["lanes"])
        pr = probe_lanes(ticker="00981A", day="2026-09-08", net=_NetSpec(), apply=True, do_print=False)
        lanes2 = load_lanes()
        ver = [l for l in lanes2["lanes"] if l["state"] == "VERIFIED"]
        chk("⑫ 探測=解析出列才 PASS;--apply 只升通過者、不刪不動他條",
            pr["passed"] == 1 and any("holdings" in l["id"] and l["kind"] == "DATED" for l in ver)
            and len(lanes2["lanes"]) == before
            and any(l["state"] == "PENDING_SOURCE" for l in lanes2["lanes"]),
            f"(PASS {pr['passed']} · VERIFIED {len(ver)})")

    with tempfile.TemporaryDirectory() as td3:
        import duckdb
        DB_ETF, DB_TW = Path(td3) / "e.duckdb", Path(td3) / "t.duckdb"
        REP, CKPT, LANES_JSON = Path(td3) / "rep", Path(td3) / "ck.json", Path(td3) / "l.json"
        globals().update(DB_ETF=DB_ETF, DB_TW=DB_TW, REP=REP, CKPT=CKPT, LANES_JSON=LANES_JSON)
        wd2 = [x.isoformat() for x in sorted(date.today() - timedelta(days=k) for k in range(0, 8))
               if x.weekday() < 5]
        c = duckdb.connect(str(DB_TW))
        c.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE)")
        c.executemany("INSERT INTO tw_daily_prices VALUES (?,?,?)", [(x, "2330", 1.0) for x in wd2])
        c.close()
        c = duckdb.connect(str(DB_ETF))
        c.execute("CREATE TABLE active_tw_etf_registry(ticker VARCHAR, name VARCHAR, fund_type VARCHAR, domestic BOOLEAN, daily_required BOOLEAN, status VARCHAR, source VARCHAR, issuer VARCHAR, first_seen VARCHAR, last_seen VARCHAR)")
        c.execute("INSERT INTO active_tw_etf_registry VALUES ('00981A','強棒','x',TRUE,TRUE,'ACTIVE_DOMESTIC','t','群益投信',?,?)", [wd2[0], wd2[-1]])
        c.execute("""CREATE TABLE holdings_daily(portfolio_date DATE, etf_ticker VARCHAR,
            etf_yf_ticker VARCHAR, etf_name VARCHAR, issuer VARCHAR, holding_ticker VARCHAR,
            holding_yf_ticker VARCHAR, holding_name VARCHAR, weight_pct DOUBLE, shares DOUBLE,
            source_type VARCHAR, source_url VARCHAR, fetched_at TIMESTAMP)""")   # ENG051 正本 schema
        c.execute("INSERT INTO holdings_daily (portfolio_date, etf_ticker, holding_ticker) VALUES (?,?,?)", [wd2[0], "00981A", "2330"])
        c.close()
        LANES_JSON.write_text(json.dumps({"schema": "VIA_ActiveETF_HistoryLanes/1.0", "rule": "只增不減",
            "lanes": [{"id": "ISSUER_ARCHIVE:群益投信", "kind": "DATED", "state": "VERIFIED",
                       "url": "https://x.example/fund/holdings?d={ymd}", "note": "自測"}]},
            ensure_ascii=False), encoding="utf-8")
        bf2 = backfill(max_days=2, net=_NetSpec())
        c = duckdb.connect(str(DB_ETF), read_only=True)
        n_rows = c.execute("SELECT count(*) FROM holdings_daily WHERE source_type='ENG078_DATED'").fetchone()[0]
        n_days = c.execute("SELECT count(DISTINCT portfolio_date) FROM holdings_daily").fetchone()[0]
        c.close()
        c = duckdb.connect(str(DB_ETF), read_only=True)
        one_day = c.execute("SELECT CAST(portfolio_date AS VARCHAR) FROM holdings_daily "
                            "WHERE source_type='ENG078_DATED' LIMIT 1").fetchone()[0]
        c.close()
        again = upsert_holdings("00981A", one_day, parse_holdings(js), "u")   # 同日同列重寫
        c = duckdb.connect(str(DB_ETF), read_only=True)
        n2 = c.execute("SELECT count(*) FROM holdings_daily WHERE source_type='ENG078_DATED'").fetchone()[0]
        c.close()
        bf3 = backfill(max_days=2, net=_NetSpec())    # 再一輪=續補更早兩日(推進,非重複)
        c = duckdb.connect(str(DB_ETF), read_only=True)
        n3 = c.execute("SELECT count(*) FROM holdings_daily WHERE source_type='ENG078_DATED'").fetchone()[0]
        dup = c.execute("SELECT count(*) FROM (SELECT portfolio_date, etf_ticker, holding_ticker "
                        "FROM holdings_daily GROUP BY 1,2,3 HAVING count(*) > 1)").fetchone()[0]
        c.close()
        chk("⑬ VERIFIED DATED 真回補:取→解析→落 ENG051 正本表(欄名對映、不改結構)· "
            "同日同列重寫=anti-join 回 0 零倍增 · 續輪往前推進 · 全表零重鍵 · 缺口轉 FILLED",
            bf2["filled"] == 2 and n_rows == 16 and n_days == 3
            and again == 0 and n2 == n_rows                    # 冪等:同日重寫零新增
            and bf3["filled"] == 2 and n3 == 32 and dup == 0,  # 推進:再兩日;鍵不重複
            f"(首輪 filled {bf2['filled']}/列 {n_rows}/日 {n_days} · 同日重寫 +{again} · 續輪 filled {bf3['filled']}/列 {n3} · 重鍵 {dup})")
    DB_ETF, DB_TW, REP, CKPT, OUT_UI, LANES_JSON = _s
    globals().update(DB_ETF=_s[0], DB_TW=_s[1], REP=_s[2], CKPT=_s[3], OUT_UI=_s[4], LANES_JSON=_s[5])
    chk("⑭ 規格 base 推導(OpenAPI3 servers / Swagger2 host+basePath / 相對 servers / 退倉內既驗證常數)"
        "· 組出之 URL 含 /v1(批406b 全 404 之修)",
        spec_base({"servers": [{"url": "https://openapi.twse.com.tw/v1"}]}, "https://x/s.json") == "https://openapi.twse.com.tw/v1"
        and spec_base({"servers": [{"url": "/v1"}]}, "https://openapi.twse.com.tw/v1/swagger.json") == "https://openapi.twse.com.tw/v1"
        and spec_base({"host": "openapi.twse.com.tw", "basePath": "/v1", "schemes": ["https"]}, "https://x/s.json") == "https://openapi.twse.com.tw/v1"
        and spec_base({}, "https://openapi.twse.com.tw/openapi.json") == TWSE_FALLBACK_BASE
        and (spec_base({"servers": [{"url": "https://openapi.twse.com.tw/v1"}]}, "u") + "/" + "/opendata/t187ap47_L".lstrip("/"))
            == "https://openapi.twse.com.tw/v1/opendata/t187ap47_L")
    print(f"  [計] 十四檢 OK {14 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 主動 ETF 每日持股史深覆蓋(VDF_ENG078 v0101)· 十四檢自測(零外呼)===")
        return selftest()
    if a and a[0] == "status":
        return status()
    if a and a[0] == "discover":
        discover_twse(net=(_net_or_none() if gate_open() else None), apply="--apply" in a)
        return 0
    if a and a[0] == "probe":
        probe_lanes(ticker=(a[a.index("--ticker") + 1] if "--ticker" in a else ""),
                    day=(a[a.index("--date") + 1] if "--date" in a else ""),
                    net=(_net_or_none() if gate_open() else None), apply="--apply" in a)
        return 0
    if a and a[0] == "backfill":
        r = backfill(max_days=int(a[a.index("--max-days") + 1]) if "--max-days" in a else 0, net=(_net_or_none() if gate_open() else None))
        print(f"[回補] {r}")
        return 0
    return daily([x for x in a if x != "daily"])


if __name__ == "__main__":
    sys.exit(main())

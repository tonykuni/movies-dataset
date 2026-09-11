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
  v0101→v0102(批407 操作員令「掛網路工具及爬蟲」):三道升級取用,全走既有件
     (Zero-Hydra,只調度不改寫)——① http:SUP_MDL740.http_json/http_text(現行)
     ② headers:SUP_MDL740.curl_json / http_bytes(兩者本就收 headers)+ 瀏覽器式
     標頭;多數 403(UA 擋)於此即通,不必動用瀏覽器 ③ scrape:收容之爬蟲雙引擎包
     PlaywrightBackend 真瀏覽器,順帶捕 XHR network_json(投信 PCF 頁多為 XHR 載入,
     故 JSON 優先於 HTML)。probe/fetch_dated 依車道 fetch 欄起跳、首個取到即用,
     並把勝出道寫回車道冊。法遵:scrape 前必過 SUP_MDL740.check_url(雙閘+包內審查),
     DENY=不啟動爬蟲並誠實印因由與期望 token;**永不代設 VIA_NET_CONSENT /
     VIA_SCRAPE_CONSENT**。群益車道實證 403,預設起跳道改 headers。
用法:python3 VDF_ENG078_ActiveETFHoldingsHistory_v0102.py daily [--offline]
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
        # 批409:實測驗真(見 docs 三十一)。群益站是 Angular SPA,持股走 XHR,
        # 端點=POST /CFWeb/api/etf/buyback,body {"fundId": <投信自家基金編號>, "date": "YYYY-MM-DD"}。
        # 基金編號非股票代號,須先自 POST /CFWeb/api/etf/list 取 stockNo→fundNo 對照(id_api)。
        # date 給過去交易日會真的回該日的 PCF(pcf.date1 隨之改),故是真 DATED 車道;
        # 非交易日回 data=null(誠實無資料,不是錯誤)。
        {"id": "ISSUER_ARCHIVE:群益投信", "kind": "DATED", "state": "VERIFIED",
         "url": "https://www.capitalfund.com.tw/CFWeb/api/etf/buyback",
         "method": "POST", "fetch": "http",
         "body": {"fundId": "{fundid}", "date": "{date}"},
         "pick": "data.stocks", "date_path": "data.pcf.date1",
         "id_api": {"url": "https://www.capitalfund.com.tw/CFWeb/api/etf/list",
                    "method": "POST", "body": None, "pick": "data.funds",
                    "code_field": "stockNo", "id_field": "fundNo"},
         "note": "批409 實測驗真:00992A(fundId 500)date=null 回 39 列、date=2026-09-01 回 40 列且 pcf.date1 隨之改;00982A(399)回 56 列"},
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
# 批406c(工作站實錄:4 條董監事/外資持股表被誤判 PASS 並升 VERIFIED):判準補三道
MAX_HOLD_ROWS = 600                    # 單一 ETF 單日持股上限;逾此=全市場表非單檔持股
# 反指標:出現即否決(這些都是「公司內部人/外資/大股東」持股,不是 ETF 成分)
NON_HOLDING_HINTS = ("董事", "監察人", "董監", "內部人", "大股東", "外資", "陸資",
                     "持股比率", "持股轉讓", "轉讓", "ESG", "定期定額", "法定成數",
                     "餘額明細", "insider", "director", "supervisor")
# 正指標:ETF 成分股表該有的字樣(給了 etf_ticker 時,兩者擇一必須命中)
HOLDING_POS_HINTS = ("成分", "持股明細", "投資組合", "基金持股", "constituent",
                     "holding", "portfolio", "PCF", "申購買回")
TW_CODE_RX = re.compile(r"^\d{4}[A-Z]?$")
_NUM_RX = re.compile(r"-?[\d,]+(?:\.\d+)?")


def _num_or_none(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = _NUM_RX.search(str(v).replace(",", ""))
    return float(m.group(0)) if m else None


def parse_holdings(payload, etf_ticker: str = "", by_id: bool = False) -> list[dict]:
    """JSON(list[dict])或 HTML 表 → [{holding_ticker,name,shares,weight}]。
    判準(批406c 收緊,因工作站實錄誤放董監事/外資持股表):
      ① ≥MIN_HOLD_ROWS 且 ≤MAX_HOLD_ROWS 列(逾上限=全市場表,非單檔 ETF 持股)
      ② 反指標(董事/監察人/內部人/大股東/外資/陸資/轉讓/ESG…)出現即否決
      ③ 給了 etf_ticker 時,原文須含該代號或含 ETF 成分股正指標(成分/持股明細/
         投資組合/constituent/holding/portfolio/PCF…),否則否決
    不合=回 []( 誠實:寧可空,不硬填——錯資料進正本表比沒資料更糟)。"""
    blob = json.dumps(payload, ensure_ascii=False)[:20000] if not isinstance(payload, str) else payload[:20000]
    if any(h in blob for h in NON_HOLDING_HINTS):
        return []                       # ② 反指標
    if (not by_id) and etf_ticker and etf_ticker not in blob and not any(h in blob for h in HOLDING_POS_HINTS):
        return []                       # ③ 與本檔無關且無成分股字樣
    # 批409:by_id=True 表示本次是「以本檔代號查出的該投信基金編號」去點名索取的
    # 單檔端點(id_api 對照表由 stockNo→fundNo 建立)。相關性由建構方式保證,
    # 比字串比對更強,故略過 ③;① 列數上下界與 ② 反指標仍然照跑,不放寬。
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
                elif shares is None and any(t in ks for t in ("股數", "數量", "shares", "Shares", "quantity", "share", "Share")):
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
    if not (MIN_HOLD_ROWS <= len(rows) <= MAX_HOLD_ROWS):
        return []                       # ① 列數上下界
    return rows


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


# ---------------------------------------------------------------- 批407:三道取用(http → headers → scrape)
# 操作員令「掛網路工具及爬蟲」。Zero-Hydra:三道全走既有件,本器只調度不改寫——
#   http    SUP_MDL740.http_json → http_text(現行)
#   headers SUP_MDL740.curl_json / http_bytes(兩者本就收 headers 參數)+ 瀏覽器式標頭
#           → 多數 403(UA 擋)即通,不必動用瀏覽器
#   scrape  收容之爬蟲雙引擎包 PlaywrightBackend(真瀏覽器;順帶捕 XHR network_json,
#           投信 PCF 頁多為 XHR 載入,故 JSON 優先於 HTML)
# 法遵:scrape 前必過 SUP_MDL740.check_url(雙閘 + 包內法遵審查);DENY=不啟動爬蟲、
#       誠實印因由與期望 token。**永不代設 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT。**
# 批408:DENY 訊息加 gate2_diagnosis()——短令自 批374/375 起把閘二預設成 "YES",
#       而包內法遵只認 I_ACCEPT_RESPONSIBLE_SCRAPING,gate_state() 卻顯示 open=True,
#       verdict 只說「法遵 finding 阻擋」;本診斷把差別講白(不印原值)。
FETCH_MODES = ("http", "headers", "scrape")
SCRAPE_TOKEN_HINT = "I_ACCEPT_RESPONSIBLE_SCRAPING"   # 包內法遵 def_validate_consent 期望值
SCRAPE_CONSENT_HINT_ENV = "VIA_SCRAPE_CONSENT"        # 閘二環境變數名
NET_CONSENT_HINT_ENV = "VIA_NET_CONSENT"              # 閘一環境變數名


def gate2_diagnosis() -> str:
    """閘二診斷(批408)。只報「是否等於包內法遵期望 token」,**不印原值**。
    存在的坑:短令 via-etfhist/via-etfuniv/… 自 批374/375 起會把閘二預設成
    字串 "YES",而包內 def_validate_consent 只認 I_ACCEPT_RESPONSIBLE_SCRAPING
    → gate_state() 看起來 open=True 但法遵仍 BLOCK,verdict 只說「法遵 finding
    阻擋」,操作員無從得知差在哪。本函式把差別講白,好讓人能自行決定要不要開。
    (本引擎永不代設任何同意閘。)"""
    cur = os.environ.get(SCRAPE_CONSENT_HINT_ENV, "")
    if not cur:
        return f"閘二 {SCRAPE_CONSENT_HINT_ENV} 未設(包內法遵期望 {SCRAPE_TOKEN_HINT})"
    if cur == SCRAPE_TOKEN_HINT:
        return f"閘二 {SCRAPE_CONSENT_HINT_ENV} 已是期望 token(阻擋另有其因,見 findings)"
    return (f"閘二 {SCRAPE_CONSENT_HINT_ENV} 已設但非期望值——包內法遵只認 "
            f"{SCRAPE_TOKEN_HINT}(短令預設的 YES 過不了)")
BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


def _scrape_backend():
    """收容之爬蟲雙引擎(只調度不改寫);缺件/缺 playwright=None(誠實)"""
    import importlib.util as _il
    eng = (VIA / "functional modules" / "VRN" / "webscraping_dualengine_v20260819"
           / "VIA_Unified_WebScraping_Playwright_Engine.py")
    if not eng.exists():
        return None, "爬蟲雙引擎收容件缺"
    # 引擎 import 同包件(VIA_Investment_Report_Classifier 等),包夾須在 sys.path
    pkg = str(eng.parent)
    if pkg not in sys.path:
        sys.path.insert(0, pkg)
    try:
        spec = _il.spec_from_file_location("via_scrape_dyn", eng)
        mod = _il.module_from_spec(spec)
        sys.modules["via_scrape_dyn"] = mod
        spec.loader.exec_module(mod)
    except Exception as exc:
        return None, f"引擎載入失敗 {type(exc).__name__}"
    try:
        import playwright  # noqa: F401
    except ImportError:
        return None, "playwright 未安裝(via_vdf_312 境:uv pip install playwright + playwright install chromium)"
    return mod, ""


def scrape_once(url: str, timeout_ms: int = 30000):
    """真瀏覽器取一次 → (payload, note)。XHR JSON 優先、HTML 後備;缺件=(None, 因由)"""
    mod, why = _scrape_backend()
    if mod is None:
        return None, why
    try:
        import asyncio
        cfg = mod.CrawlConfig(seeds=[url]) if hasattr(mod, "CrawlConfig") else None
        if cfg is not None:
            for k, v in (("timeout_ms", timeout_ms), ("capture_json", True),
                         ("user_agent", BROWSER_HEADERS["User-Agent"])):
                if hasattr(cfg, k):
                    setattr(cfg, k, v)

        async def _go():
            be = mod.def_choose_backend("playwright")
            await be.start()
            try:
                return await be.fetch(url, cfg, 0)
            finally:
                await be.close()
        r = asyncio.run(_go())
    except Exception as exc:
        return None, f"爬蟲取用失敗 {type(exc).__name__}"
    for nj in (getattr(r, "network_json", None) or []):
        d = nj.get("data") if isinstance(nj, dict) else None
        if d is not None:
            return d, f"scrape XHR {nj.get('url', '')[:60]}"
    html = getattr(r, "html", "") or ""
    if html:
        return html, f"scrape HTML status={getattr(r, 'status_code', '?')}"
    return None, f"爬蟲零內容(status={getattr(r, 'status_code', '?')} err={getattr(r, 'error', '')[:60]})"


def fetch_by_mode(mode: str, url: str, net, method: str = "GET", body=None):
    """單道取用 → (payload, note);payload=JSON 物件或 HTML 字串;失敗=(None, 因由)
    批409:method="POST" 走 SUP_MDL740.post_json(投信 PCF 類端點);仍是統包網路工具
    的車道,雙閘/法遵/契約全同,呼端不自己開 urllib(那會繞過閘與 NET-BRIDGE 稽核)。
    POST 沒有「爬蟲道」升級——瀏覽器道是為了 SPA 頁面而設,而 POST 車道本身就是
    那個頁面在背後打的 XHR,已經是終點。"""
    if net is None:
        return None, "網路工具缺席或雙閘未開"
    if str(method).upper() == "POST":
        if not hasattr(net, "post_json"):
            return None, "統包網路工具無 post_json 車道(需 SUP_MDL740 v0113+)"
        if mode == "scrape":
            return None, "POST 車道無爬蟲道(本身即該頁的 XHR,已是終點)"
        hdr = dict(BROWSER_HEADERS) if mode == "headers" else None
        try:
            r = net.post_json(url, body, headers=hdr)
        except Exception as exc:
            return None, f"post 例外 {type(exc).__name__}"
        if isinstance(r, dict) and r.get("state") == "OK":
            return r.get("data"), ("post_json+瀏覽器標頭" if hdr else "post_json")
        return None, f"{str((r or {}).get('state', '?'))}:{str((r or {}).get('note', ''))[:60]}"
    try:
        if mode == "http":
            r = net.http_json(url)
            if isinstance(r, dict) and r.get("state") == "OK":
                return r.get("data"), "http_json"
            r2 = net.http_text(url)
            if isinstance(r2, dict) and r2.get("state") == "OK":
                return r2.get("data"), "http_text"
            return None, f"{str((r or {}).get('state', '?'))}:{str((r or {}).get('note', ''))[:50]}"
        if mode == "headers":
            if hasattr(net, "curl_json"):
                r = net.curl_json(url, headers=dict(BROWSER_HEADERS))
                if isinstance(r, dict) and r.get("state") == "OK":
                    return r.get("data"), "curl_json+瀏覽器標頭"
            if hasattr(net, "http_bytes"):
                r = net.http_bytes(url, headers=dict(BROWSER_HEADERS))
                if isinstance(r, dict) and r.get("state") == "OK":
                    b = r.get("data")
                    return (b.decode("utf-8", "replace") if isinstance(b, (bytes, bytearray)) else b), "http_bytes+瀏覽器標頭"
            return None, "帶標頭道亦被拒(非 UA 問題;可能需 cookie/登入)"
        if mode == "scrape":
            if hasattr(net, "check_url"):
                v = net.check_url(url)
                verdict = str((v or {}).get("verdict", ""))
                if not verdict.startswith("ALLOW"):
                    return None, (f"法遵未過不啟動爬蟲:{verdict[:60]}·"
                                  f"{gate2_diagnosis()};永不代設)")
            return scrape_once(url)
    except Exception as exc:
        return None, f"{mode} 例外 {type(exc).__name__}"
    return None, f"未知道 {mode}"



def fetch_escalating(url: str, net, start: str = "http", method: str = "GET", body=None):
    """依序 http → headers → scrape,首個取到即回 (payload, mode, note);全敗=(None,'',因由串)
    批409:POST 車道只走 http/headers 兩道(scrape 對 POST 無意義,見 fetch_by_mode)。"""
    order = list(FETCH_MODES[FETCH_MODES.index(start):]) if start in FETCH_MODES else list(FETCH_MODES)
    if str(method).upper() == "POST":
        order = [m for m in order if m != "scrape"] or ["http"]
    notes = []
    for m in order:
        payload, note = fetch_by_mode(m, url, net, method=method, body=body)
        notes.append(f"{m}={note}")
        if payload is not None:
            return payload, m, note
    return None, "", " · ".join(notes)



# ---------------------------------------------------------------- 批409:單檔點名車道(POST + 基金編號 + 日期硬閘)
# 為什麼要有這一層:投信 PCF 端點不是「一個 URL 換代號」那麼單純——
#   ① 是 POST 不是 GET(Angular SPA 的 XHR)
#   ② body 用的是**投信自家的基金編號**,不是股票代號,要先查對照表
#   ③ 回傳是包了好幾層的物件(pcf/stocks/bonds/…),持股在其中一條路徑上
#   ④ 給過去日期時「該日沒有資料」與「回了今天的資料」長得一樣危險
# 這四件事各自都能默默產生錯資料,所以四件都寫成明碼設定 + 硬閘,不靠猜。
def _dig(obj, path: str):
    """點路徑取值('data.stocks');任何一段不在=回 None(不丟例外、不亂猜)"""
    cur = obj
    for seg in [x for x in str(path or "").split(".") if x]:
        if isinstance(cur, dict) and seg in cur:
            cur = cur[seg]
        elif isinstance(cur, list) and seg.isdigit() and int(seg) < len(cur):
            cur = cur[int(seg)]
        else:
            return None
    return cur


def render_tpl(tpl, **kw):
    """遞迴把 body 模板裡的 {fundid}/{date}/{ymd}/{yf} 換成實值;None 保持 None
    (欄位值就是 null 時有意義——群益 date=null 表示「最新一日」)。"""
    if isinstance(tpl, dict):
        return {k: render_tpl(v, **kw) for k, v in tpl.items()}
    if isinstance(tpl, list):
        return [render_tpl(v, **kw) for v in tpl]
    if isinstance(tpl, str):
        out = tpl
        for k, v in kw.items():
            out = out.replace("{" + k + "}", "" if v is None else str(v))
        return None if out == "" and "{" in tpl else out
    return tpl


def _iso_day(v) -> str:
    """把各家日期寫法正規化成 YYYY-MM-DD;認不出=空字串(誠實)"""
    t = str(v or "").strip()
    m = re.match(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", t)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", t)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def resolve_fund_id(lane: dict, ticker: str, net, apply: bool = False) -> tuple[str, str]:
    """以 id_api 建「股票代號 → 投信基金編號」對照表 → (fund_id, note)。
    對照表寫回車道冊 id_map 供下次直接用(只增不減;查不到=誠實空字串不亂編)。"""
    if not ticker:
        return "", "無代號"
    cached = (lane.get("id_map") or {}).get(ticker)
    if cached:
        return str(cached), "id_map 快取"
    spec = lane.get("id_api") or {}
    if not spec.get("url"):
        return "", "車道無 id_api(無法把股票代號換成基金編號)"
    payload, _m, note = fetch_escalating(spec["url"], net, str(lane.get("fetch", "http")),
                                         method=str(spec.get("method", "GET")),
                                         body=spec.get("body"))
    if payload is None:
        return "", f"id_api 取用失敗:{note[:70]}"
    rows = _dig(payload, spec.get("pick", "")) if spec.get("pick") else payload
    if not isinstance(rows, list):
        return "", "id_api 回傳非清單(pick 路徑不符)"
    cf, idf = spec.get("code_field", ""), spec.get("id_field", "")
    m = {str(r.get(cf, "")).strip(): str(r.get(idf, "")).strip()
         for r in rows if isinstance(r, dict) and r.get(cf) and r.get(idf)}
    if m:
        lane["id_map"] = {**(lane.get("id_map") or {}), **m}
        if apply:
            try:
                _ls = load_lanes()
                for _l in _ls.get("lanes", []):
                    if _l.get("id") == lane.get("id"):
                        _l["id_map"] = lane["id_map"]
                LANES_JSON.write_text(json.dumps(_ls, ensure_ascii=False, indent=1), encoding="utf-8")
            except Exception:
                pass
    fid = m.get(ticker, "")
    return fid, (f"id_api 對照 {len(m)} 檔" if fid else
                 f"id_api 對照 {len(m)} 檔但無 {ticker}(該投信不發此檔)")


def fetch_lane(lane: dict, ticker: str, day: str, net, apply: bool = False):
    """單一入口:解編號 → 組 url/body → 三道取用 → pick → 解析 → 日期硬閘。
    回 (rows, mode, note)。任何一關不過都回 ([], mode, 因由)——誠實空,不硬填。"""
    method = str(lane.get("method", "GET")).upper()
    fid, idnote = "", ""
    if lane.get("id_api"):
        fid, idnote = resolve_fund_id(lane, ticker, net, apply=apply)
        if not fid:
            return [], "", idnote
    kw = {"fundid": fid, "date": day or "", "ymd": (day or "").replace("-", ""),
          "yf": ticker, "code": ticker}
    url = lane.get("url", "")
    for k, v in kw.items():
        url = url.replace("{" + k + "}", str(v))
    body = render_tpl(lane.get("body"), **kw) if method == "POST" else None
    payload, mode, note = fetch_escalating(url, net, str(lane.get("fetch", "http")),
                                           method=method, body=body)
    if payload is None:
        return [], "", (idnote + " · " if idnote else "") + note
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8", "replace")
    picked = _dig(payload, lane["pick"]) if lane.get("pick") else payload
    if lane.get("pick") and picked is None:
        return [], mode, f"該日無資料或 pick 路徑無值({lane['pick']};非交易日=正常)"
    rows = parse_holdings(picked, ticker, by_id=bool(lane.get("id_api")))
    if not rows:
        return [], mode, f"零可解析持股列(取用 OK via {mode}:{note})"
    # 日期硬閘:點名了某一日,回來的就必須是那一日。不同=不寫(否則今日持股
    # 會被冒充成過去某日,那比沒資料更糟)。車道未宣告 date_path=不做此閘。
    if day and lane.get("date_path"):
        got = _iso_day(_dig(payload, lane["date_path"]))
        if got and got != day:
            return [], mode, f"日期不符:要 {day} 回 {got}(拒寫,避免今日持股冒充歷史)"
        if not got:
            return [], mode, f"回傳無可辨日期({lane['date_path']}) 拒寫"
    return rows, mode, (f"{len(rows)} 列 via {mode}" + (f" · {idnote}" if idnote else ""))


def sync_lanes(apply: bool = False, do_print: bool = True) -> dict:
    """把本檔內的車道種子(DEFAULT_LANES)**加法式**併進磁碟上的車道冊。
    為什麼要有:車道冊是**執行期會被 --apply 改寫的檔**,工作站那份早已與倉內
    版本分岔;若把新驗證好的車道直接寫進倉內 JSON,操作員 `git pull` 會撞本機修改。
    所以新設定放在程式碼裡(隨版本走),用這支把它併進去。
    只增不減鐵律:
      · 車道冊沒有的 id → 整條加入
      · 已有的 id → 只補**缺少的鍵**(method/body/pick/date_path/id_api/url 為空時才填)
      · 狀態只升不降,且只在「檔內是 PENDING_SOURCE 且種子是 VERIFIED」時升
      · 絕不刪任何車道、絕不覆寫已有的非空 url、絕不動 probe 寫回的 id_map/note"""
    lanes = load_lanes()
    have = {l.get("id"): l for l in lanes.get("lanes", [])}
    added, filled, upgraded = [], [], []
    for seed in DEFAULT_LANES["lanes"]:
        sid = seed.get("id")
        cur = have.get(sid)
        if cur is None:
            lanes["lanes"].append(json.loads(json.dumps(seed)))
            added.append(sid)
            continue
        keys = [k for k in ("method", "body", "pick", "date_path", "id_api", "fetch", "kind")
                if k in seed and not cur.get(k)]
        for k in keys:
            cur[k] = json.loads(json.dumps(seed[k]))
        if seed.get("url") and not cur.get("url"):
            cur["url"] = seed["url"]; keys.append("url")
        elif (seed.get("url") and cur.get("url") != seed.get("url")
              and cur.get("state") == "PENDING_SOURCE" and seed.get("state") == "VERIFIED"):
            # 檔內是 PENDING_SOURCE=那條 url 從來沒驗過(是猜的);種子是 VERIFIED=
            # 已附實測證據。以驗過的取代沒驗過的不算「減」,但舊值仍寫進 note 留痕,
            # 資訊不丟。VERIFIED/CANDIDATE 車道的 url 一律不動(那是驗過或探過的)。
            cur["note"] = (str(cur.get("note", "")) + f" · 批409 舊未驗 url 汰換:{cur['url']}").strip(" ·")
            cur["url"] = seed["url"]; keys.append("url(汰換未驗值)")
        if keys:
            filled.append(f"{sid}:{'+'.join(keys)}")
        if cur.get("state") == "PENDING_SOURCE" and seed.get("state") == "VERIFIED" \
                and seed.get("url") and cur.get("url") == seed.get("url"):
            cur["state"] = "VERIFIED"
            cur["note"] = (str(cur.get("note", "")) + " · " + str(seed.get("note", ""))).strip(" ·")
            upgraded.append(sid)
    if apply and (added or filled or upgraded):
        LANES_JSON.write_text(json.dumps(lanes, ensure_ascii=False, indent=1), encoding="utf-8")
    if do_print:
        print(f"[車道併入] 新增 {len(added)} · 補鍵 {len(filled)} · 升態 {len(upgraded)} · "
              f"{'已寫回' if apply else 'dry-run(加 --apply 才寫)'}")
        for x in added:
            print(f"  [新增] {x}")
        for x in filled:
            print(f"  [補鍵] {x}")
        for x in upgraded:
            print(f"  [升態] {x} PENDING_SOURCE → VERIFIED(種子已附實測證據)")
        if not (added or filled or upgraded):
            # 批411:「新增 0 · 補鍵 0 · 升態 0」看不出是「早就併好了」還是「被狀態擋住」。
            # 零動作時把種子裡有的每條逐條說明現況,免得又要猜。
            cur = {l.get("id"): l for l in lanes.get("lanes", [])}
            for seed in DEFAULT_LANES["lanes"]:
                c = cur.get(seed.get("id"))
                if c is None:
                    continue
                why = ("已是 VERIFIED(設定齊全,無須併入)" if c.get("state") == "VERIFIED"
                       else f"狀態 {c.get('state')}(非 PENDING_SOURCE=不自動升;url 已探過不覆寫)"
                       if c.get("state") != "PENDING_SOURCE"
                       else "PENDING_SOURCE 但種子未帶已驗證 url(仍缺源)")
                print(f"  [不動] {str(seed.get('id'))[:40]:<40} {why}")
    return {"state": "OK", "added": added, "filled": filled, "upgraded": upgraded}


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
    PROMOTED = "probe 驗過"          # 批406c:只重驗「本器升過」的,不動人工/原生 VERIFIED
    demoted = 0
    for l in lanes.get("lanes", []):
        if not l.get("url"):
            continue
        recheck = l.get("state") == "VERIFIED" and PROMOTED in str(l.get("note", ""))
        if l.get("state") == "VERIFIED" and not recheck:
            continue
        url = (l["url"].replace("{yf}", tk).replace("{code}", tk)
               .replace("{ymd}", d.replace("-", "")).replace("{date}", d))
        why, n, won = "", 0, ""
        try:            # 批407 三道升級;批409 走 fetch_lane(含 POST/基金編號/日期硬閘)
            rows, won, note = fetch_lane(l, tk, d, net, apply=apply)
            n = len(rows)
            if not rows:
                why = note
        except Exception as exc:
            why = f"取用失敗 {type(exc).__name__}"
        # 批409:探測用的代號未必是這家投信發的。「該投信不發此檔」不是車道壞掉,
        # 是問錯人——標 N/A、不算 PASS 也**不撤銷**(否則拿別家代號探一次就會
        # 把驗過的車道誤降)。
        not_mine = "該投信不發此檔" in (why or "")
        ok = (MIN_HOLD_ROWS <= n <= MAX_HOLD_ROWS)
        passed += 1 if ok else 0
        out.append({"id": l["id"], "url": url, "rows": n, "pass": ok, "why": why,
                    "recheck": recheck, "mode": won, "not_mine": not_mine})
        if do_print:
            tag = "PASS" if ok else ("N/A" if not_mine else ("DEMOTE" if recheck else "FAIL"))
            print(f"  [{tag}] {l['id'][:44]:<44} 列 {n:>4}  {why}")
        if apply and not not_mine:
            if ok:
                if not recheck:
                    l["state"] = "VERIFIED"
                    l["fetch"] = won or "http"          # 批407:記下勝出取用道
                    l["note"] = (l.get("note", "") + f" · {PROMOTED}({tk} {d} {n} 列 via {won})").strip(" ·")
            elif recheck:                # 批406c:曾誤升者,重驗不過即降回候選(誠實撤銷)
                l["state"] = "CANDIDATE"
                l["note"] = (str(l.get("note", "")).replace(PROMOTED, "曾誤升已撤")
                             + f" · 批406c 收緊判準後重驗不過({why or '零列'})").strip(" ·")
                demoted += 1
    if apply:
        LANES_JSON.write_text(json.dumps(lanes, ensure_ascii=False, indent=1), encoding="utf-8")
    if do_print:
        print(f"[探測] {len(out)} 條 · PASS {passed} · 撤銷 {demoted} · "
              f"{'已寫回車道冊(只升通過者;曾誤升者重驗不過即撤)' if apply else 'dry-run(加 --apply 才寫)'}")
    return {"state": "OK", "ticker": tk, "date": d, "rows": out, "passed": passed,
            "demoted": demoted}


def fetch_dated(lane: dict, ticker: str, day: str, net) -> list[dict]:
    """VERIFIED DATED 車道取某日持股;失敗/不合判準=回 [](誠實)
    批409:改走 fetch_lane——POST/基金編號解析/pick 路徑/日期硬閘全在那一層,
    回補與探測用同一條路(判準不會兩套)。"""
    rows, _mode, _note = fetch_lane(lane, ticker, day, net)
    return rows


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
    revived = 0
    for e in cov["etfs"]:
        st = ck["days"].get(e["ticker"], {})
        ls = lane_for(e["issuer"], lanes)
        dated = [l for l in ls if l["kind"] == "DATED"]
        # 批411 重試律(工作站實錄 tried 0 之修):
        #   NO_SOURCE 不是終局判決,是「當時沒有源」的紀錄。批406 那時所有日格都被
        #   標成 NO_SOURCE / PENDING_TODAY;批409 群益 DATED 車道驗真之後,那些日格
        #   若不重試就**永遠不會被回補**——這正是工作站 backfill 回
        #   tried 0 · filled 0 · no_source 0 的真因(coverage 用 setdefault 保留舊態,
        #   backfill 只走 MISSING)。
        #   復活條件(保守,不做白工):
        #     · MISSING            → 一律試
        #     · NO_SOURCE          → 該發行商**現在有** VERIFIED DATED 車道才試
        #     · PENDING_TODAY      → 那一日已經不是今日了才試(當日快照歸 ENG051)
        #   FILLED 永不重跑(只增不減;已落庫的不動)。
        days = []
        for d, v in st.items():
            stt = str(v.get("state") or "")
            if stt == "MISSING":
                days.append(d)
            elif stt == "NO_SOURCE" and dated:
                days.append(d); revived += 1
            elif stt == "PENDING_TODAY" and d != today:
                days.append(d); revived += 1
        days = sorted(days, reverse=True)
        if max_days:
            days = days[:max_days]
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
    return {"state": "OK", "tried": tried, "filled": filled, "no_source": nosrc,
            "revived": revived,      # 批411:自 NO_SOURCE/過期 PENDING_TODAY 復活重試的日格數
            "verified_dated_lanes": sum(1 for l in lanes["lanes"] if l["state"] == "VERIFIED" and l["kind"] == "DATED")}


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
        # 批409:本檢問的是「沒有 DATED 車道時會不會誠實」,所以車道冊要寫死成
        # 「沒有 DATED 車道」的樣子,不能靠出貨預設剛好沒有(批409 起群益已是
        # VERIFIED DATED,靠預設就會假紅——判準該綁自己的前提,不綁出貨內容)。
        LANES_JSON.write_text(json.dumps(
            {"schema": "x", "rule": "只增不減", "lanes": [
                {"id": "MONEYDJ", "kind": "LATEST_ONLY", "state": "VERIFIED",
                 "url": "https://x/{yf}", "note": "自測 fixture:只有最新日車道"}]},
            ensure_ascii=False), encoding="utf-8")
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
    # 真實 PCF 列會帶基金代號(批406c 正指標之一);TW_CODE_RX 不吃五碼+A 故不成列
    js = [{"基金代號": "00981A", "股票代號": f"23{i:02d}", "股票名稱": f"股{i}",
           "股數": f"{i},000", "權重(%)": i / 2} for i in range(1, 9)]
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
    # --- 批406c:工作站實錄「4 條董監事/外資持股表誤判 PASS 並升 VERIFIED」之收緊 ---
    insider = [{"公司代號": f"2{i:03d}", "姓名": f"某{i}", "職稱": "董事",
                "目前持股": i * 1000} for i in range(1, 40)]
    qfiis = [{"證券代號": f"23{i:02d}", "證券名稱": f"股{i}",
              "外資及陸資持股比率": i / 3} for i in range(1, 25)]
    huge = [{"股票代號": f"{1000 + i}", "股票名稱": "x", "股數": 1} for i in range(1200)]
    good = [{"股票代號": f"23{i:02d}", "股票名稱": f"股{i}", "股數": i * 100,
             "權重(%)": i / 4} for i in range(1, 12)]   # 刻意不含正指標字樣
    chk("⑮ 反指標否決(董事/監察人/內部人/大股東/外資/陸資/轉讓/ESG 等表一律回空)",
        parse_holdings(insider) == [] and parse_holdings(qfiis) == []
        and parse_holdings(insider, "00981A") == [])
    chk("⑯ 列數上限(單檔 ETF 單日持股 ≤ %d;全市場表逾限=回空)" % MAX_HOLD_ROWS,
        parse_holdings(huge) == [] and len(huge) > MAX_HOLD_ROWS)
    chk("⑰ 給了 ETF 代號時須與本檔相關(原文含代號或含成分股正指標,否則回空)",
        parse_holdings(good, "00981A") == []                        # 兩者皆無=否決
        and len(parse_holdings(good + [{"基金代號": "00981A"}], "00981A")) == 11
        and len(parse_holdings(good, "")) == 11)                    # 未給代號=不套此道
    with tempfile.TemporaryDirectory() as td4:
        LANES_JSON = Path(td4) / "l.json"
        globals()["LANES_JSON"] = LANES_JSON
        LANES_JSON.write_text(json.dumps({"schema": "x", "rule": "只增不減", "lanes": [
            {"id": "BAD_PROMOTED", "kind": "DATED", "state": "VERIFIED",
             "url": "https://x/insider", "note": "probe 驗過(00981A 2026-09-08 27528 列)"},
            {"id": "MONEYDJ", "kind": "LATEST_ONLY", "state": "VERIFIED",
             "url": "https://x/moneydj?e={yf}", "note": "原生 VERIFIED,非本器所升"},
        ]}, ensure_ascii=False), encoding="utf-8")

        class _NetInsider:
            def http_json(self, url, timeout=30):
                return {"state": "OK", "data": insider}
            def http_text(self, url, timeout=30):
                return {"state": "FAIL", "note": "x"}
        pr2 = probe_lanes(ticker="00981A", day="2026-09-08", net=_NetInsider(),
                          apply=True, do_print=False)
        after = {l["id"]: l for l in load_lanes()["lanes"]}
        chk("⑱ 撤銷道:曾由本器誤升者重驗不過即降回 CANDIDATE 並記因由;"
            "原生 VERIFIED(非本器所升)不重驗不動",
            pr2["demoted"] == 1 and after["BAD_PROMOTED"]["state"] == "CANDIDATE"
            and "曾誤升已撤" in after["BAD_PROMOTED"]["note"]
            and after["MONEYDJ"]["state"] == "VERIFIED"
            and after["MONEYDJ"]["note"] == "原生 VERIFIED,非本器所升",
            f"(撤銷 {pr2['demoted']})")
    DB_ETF, DB_TW, REP, CKPT, OUT_UI, LANES_JSON = _s
    globals().update(DB_ETF=_s[0], DB_TW=_s[1], REP=_s[2], CKPT=_s[3], OUT_UI=_s[4], LANES_JSON=_s[5])
    # --- 批407 四檢:三道升級(http → headers → scrape)全注入式假 net,零外呼 ---
    class _Net403:
        """http 道 403、headers 道通(模擬 UA 擋);記錄收到的 headers"""
        seen = {}
        def http_json(self, url, timeout=30):
            return {"state": "FAIL", "note": "HTTP Error 403: Forbidden"}
        def http_text(self, url, timeout=30):
            return {"state": "FAIL", "note": "HTTP Error 403: Forbidden"}
        def curl_json(self, url, headers=None, timeout=30):
            _Net403.seen = dict(headers or {})
            return {"state": "OK", "data": js}
        def check_url(self, url):
            return {"verdict": "ALLOW(候實際 robots/條款線上確認)"}

    class _NetDeny:
        """三道皆不通、且法遵 DENY(閘二未開)→ 不得啟動爬蟲"""
        scraped = False
        def http_json(self, url, timeout=30):
            return {"state": "FAIL", "note": "403"}
        def http_text(self, url, timeout=30):
            return {"state": "FAIL", "note": "403"}
        def curl_json(self, url, headers=None, timeout=30):
            return {"state": "FAIL", "note": "403"}
        def http_bytes(self, url, headers=None, **kw):
            return {"state": "FAIL", "note": "403"}
        def check_url(self, url):
            return {"verdict": "DENY(fail-closed:閘二未開)"}

    b1, m1, n1 = fetch_escalating("https://x/a", _Net403())
    chk("⑲ 三道升級序 http→headers→scrape;http 403 時自動升 headers 道並帶瀏覽器標頭",
        m1 == "headers" and b1 == js and "Mozilla/5.0" in _Net403.seen.get("User-Agent", "")
        and "zh-TW" in _Net403.seen.get("Accept-Language", "")
        and list(FETCH_MODES) == ["http", "headers", "scrape"], f"({m1})")
    b2, m2, n2 = fetch_escalating("https://x/a", _NetDeny())
    chk("⑳ 法遵閘 DENY 時不啟動爬蟲、誠實印因由與期望 token(永不代設)",
        b2 is None and m2 == "" and "法遵未過不啟動爬蟲" in n2
        and SCRAPE_TOKEN_HINT in n2 and _NetDeny.scraped is False, f"({n2[-60:]})")
    _pl, _why = _scrape_backend()
    chk("㉑ 爬蟲道走收容雙引擎(只調度不改寫);缺 playwright=誠實因由不假裝",
        (_pl is not None) or ("playwright" in _why or "缺" in _why or "載入失敗" in _why),
        f"({_why or 'playwright 在位'})")
    with tempfile.TemporaryDirectory() as td5:
        LANES_JSON = Path(td5) / "l.json"
        globals()["LANES_JSON"] = LANES_JSON
        LANES_JSON.write_text(json.dumps({"schema": "x", "rule": "只增不減", "lanes": [
            {"id": "ISSUER_403", "kind": "DATED", "state": "CANDIDATE",
             "url": "https://x/pcf?d={ymd}", "fetch": "http", "note": "自測"}]},
            ensure_ascii=False), encoding="utf-8")
        pr3 = probe_lanes(ticker="00981A", day="2026-09-08", net=_Net403(),
                          apply=True, do_print=False)
        lane3 = load_lanes()["lanes"][0]
        chk("㉒ probe 記勝出道回車道冊(下次自該道起跳);升 VERIFIED 且註明 via",
            pr3["passed"] == 1 and pr3["rows"][0]["mode"] == "headers"
            and lane3["state"] == "VERIFIED" and lane3["fetch"] == "headers"
            and "via headers" in lane3["note"], f"({lane3.get('fetch')})")
    DB_ETF, DB_TW, REP, CKPT, OUT_UI, LANES_JSON = _s
    globals().update(DB_ETF=_s[0], DB_TW=_s[1], REP=_s[2], CKPT=_s[3], OUT_UI=_s[4], LANES_JSON=_s[5])
    # --- 批408 一檢:閘二診斷把「YES 不是期望 token」講白(不印原值;永不代設)---
    _g2_old = os.environ.get(SCRAPE_CONSENT_HINT_ENV)
    try:
        os.environ[SCRAPE_CONSENT_HINT_ENV] = "YES"          # 重現短令預設值
        _b3, _m3, _n3 = fetch_escalating("https://x/a", _NetDeny())
        _d_yes = gate2_diagnosis()
        os.environ[SCRAPE_CONSENT_HINT_ENV] = SCRAPE_TOKEN_HINT
        _d_tok = gate2_diagnosis()
        os.environ.pop(SCRAPE_CONSENT_HINT_ENV, None)
        _d_unset = gate2_diagnosis()
    finally:
        if _g2_old is None:
            os.environ.pop(SCRAPE_CONSENT_HINT_ENV, None)
        else:
            os.environ[SCRAPE_CONSENT_HINT_ENV] = _g2_old
    chk("㉓ 閘二診斷三態且不外洩原值:未設/已設但非期望值(短令 YES)/已是期望 token",
        ("未設" in _d_unset) and ("非期望值" in _d_yes) and (SCRAPE_TOKEN_HINT in _d_yes)
        and ("已是期望 token" in _d_tok) and ("YES" not in _d_tok)
        and (_b3 is None) and ("非期望值" in _n3), f"({_d_yes[-42:]})")
    # --- 批409 一檢:POST + 基金編號 + pick 路徑 + 日期硬閘(全注入式假 net,零外呼)---
    LANE409 = {"id": "ISSUER_ARCHIVE:自測投信", "kind": "DATED", "state": "VERIFIED",
               "url": "https://issuer.example/CFWeb/api/etf/buyback",
               "method": "POST", "fetch": "http",
               "body": {"fundId": "{fundid}", "date": "{date}"},
               "pick": "data.stocks", "date_path": "data.pcf.date1",
               "id_api": {"url": "https://issuer.example/CFWeb/api/etf/list",
                          "method": "POST", "body": None, "pick": "data.funds",
                          "code_field": "stockNo", "id_field": "fundNo"}}

    def _pcf(day, n=8):
        return {"code": 200, "data": {
            "pcf": {"fundName": "自測主動式ETF基金", "date1": day},
            "stocks": [{"date1": day, "stocNo": f"{2330 + i}", "stocName": f"標的{i}",
                        "weight": 5.0 + i, "share": 1000 * (i + 1),
                        "shareFormat": f"{1000 * (i + 1):,}"} for i in range(n)]}}

    class _NetPost:
        """假投信站:list 回代號↔編號對照;buyback 只認對照過的編號並回該日 PCF"""
        seen = []
        bad_date = False
        def post_json(self, url, payload=None, headers=None, timeout=30):
            _NetPost.seen.append((url, json.dumps(payload, ensure_ascii=False) if payload is not None else None))
            if url.endswith("/etf/list"):
                return {"state": "OK", "data": {"code": 200, "data": {"funds": [
                    {"stockNo": "00992A", "fundNo": "500", "shortName": "自測科技創新"},
                    {"stockNo": "00982A", "fundNo": "399", "shortName": "自測強棒"}]}}}
            if url.endswith("/etf/buyback"):
                if not isinstance(payload, dict) or payload.get("fundId") not in ("500", "399"):
                    return {"state": "OK", "data": {"code": 200, "data": None}}
                d = payload.get("date") or "2026-09-08"
                return {"state": "OK", "data": _pcf("2026-01-01" if _NetPost.bad_date else d)}
            return {"state": "FAIL", "note": "未知端點"}

    _NetPost.seen = []
    lane409 = dict(LANE409)
    r24, m24, n24 = fetch_lane(lane409, "00992A", "2026-09-03", _NetPost())
    body_sent = json.loads([b for u, b in _NetPost.seen if u.endswith("buyback")][0])
    _NetPost.bad_date = True
    lane409b = dict(LANE409)
    r24b, _m, n24b = fetch_lane(lane409b, "00992A", "2026-09-03", _NetPost())
    _NetPost.bad_date = False
    lane409c = dict(LANE409)
    r24c, _m2, n24c = fetch_lane(lane409c, "00404A", "2026-09-03", _NetPost())
    chk("㉔ POST 單檔點名車道:代號→基金編號→body 渲染→pick 路徑→解析;"
        "日期不符即拒寫;非該投信之代號=誠實 N/A(批409)",
        len(r24) == 8 and m24 == "http" and body_sent == {"fundId": "500", "date": "2026-09-03"}
        and r24[0]["holding_ticker"] == "2330" and r24[0]["shares"] == 1000
        and r24[0]["weight"] == 5.0
        and r24b == [] and "日期不符" in n24b
        and r24c == [] and "該投信不發此檔" in n24c,
        f"({len(r24)} 列 · {n24b[:22]} · {n24c[:16]})")
    # ㉕ probe 拿別家代號探不得撤銷已驗車道(否則問錯人就把好車道降級)
    with tempfile.TemporaryDirectory() as td6:
        LANES_JSON = Path(td6) / "l.json"
        globals()["LANES_JSON"] = LANES_JSON
        LANES_JSON.write_text(json.dumps({"schema": "x", "rule": "只增不減",
            "lanes": [dict(LANE409, note="probe 驗過(前次)")]}, ensure_ascii=False), encoding="utf-8")
        pr4 = probe_lanes(ticker="00404A", day="2026-09-03", net=_NetPost(),
                          apply=True, do_print=False)
        lane_after = load_lanes()["lanes"][0]
        chk("㉕ 拿別家代號探測=N/A 不算 PASS 也不撤銷(車道態不動)",
            pr4["passed"] == 0 and pr4["demoted"] == 0
            and pr4["rows"][0].get("not_mine") is True
            and lane_after["state"] == "VERIFIED",
            f"({lane_after['state']} · demoted {pr4['demoted']})")
    # ㉖ 車道併入只增不減 + 冪等 + 不降級(批409)
    with tempfile.TemporaryDirectory() as td7:
        LANES_JSON = Path(td7) / "l.json"
        globals()["LANES_JSON"] = LANES_JSON
        LANES_JSON.write_text(json.dumps({"schema": "x", "rule": "只增不減", "lanes": [
            {"id": "ISSUER_ARCHIVE:群益投信", "kind": "DATED", "state": "PENDING_SOURCE",
             "url": "https://old.example/guessed?date={ymd}", "note": "舊猜值"},
            {"id": "OPERATOR_ONLY", "kind": "DATED", "state": "VERIFIED",
             "url": "https://operator.example/x", "note": "操作員手設,種子沒有"},
            {"id": "MONEYDJ", "kind": "LATEST_ONLY", "state": "CANDIDATE",
             "url": "https://kept.example/keep", "note": "探過的 url 不得被種子蓋掉"}]},
            ensure_ascii=False), encoding="utf-8")
        s1 = sync_lanes(apply=True, do_print=False)
        a1 = {l["id"]: l for l in load_lanes()["lanes"]}
        s2 = sync_lanes(apply=True, do_print=False)
        a2 = {l["id"]: l for l in load_lanes()["lanes"]}
        cap = a1["ISSUER_ARCHIVE:群益投信"]
        chk("㉖ 車道併入:只增不減(操作員自設車道保留)· 未驗 url 才汰換且舊值留 note ·"
            " 探過的 url 不被種子蓋 · 再跑一次零動作(冪等)",
            "OPERATOR_ONLY" in a1 and a1["OPERATOR_ONLY"]["url"] == "https://operator.example/x"
            and a1["MONEYDJ"]["url"] == "https://kept.example/keep"
            and a1["MONEYDJ"]["state"] == "CANDIDATE"
            and cap["state"] == "VERIFIED" and cap["url"].endswith("/CFWeb/api/etf/buyback")
            and "old.example/guessed" in cap["note"] and cap.get("method") == "POST"
            and len(s1["added"]) >= 1 and not (s2["added"] or s2["filled"] or s2["upgraded"])
            and len(a2) == len(a1),
            f"(新增 {len(s1['added'])} · 二跑 {len(s2['added'])}/{len(s2['filled'])}/{len(s2['upgraded'])})")
    # --- 批411 一檢:回補重試律(NO_SOURCE 不是終局)---
    with tempfile.TemporaryDirectory() as td8:
        t8 = Path(td8)
        DB_ETF = t8 / "e.duckdb"; DB_TW = t8 / "t.duckdb"; CKPT = t8 / "ck.json"
        LANES_JSON = t8 / "l.json"; REP = t8 / "rep"; OUT_UI = t8 / "ui.html"
        globals().update(DB_ETF=DB_ETF, DB_TW=DB_TW, CKPT=CKPT, LANES_JSON=LANES_JSON,
                         REP=REP, OUT_UI=OUT_UI)
        wd8 = [x.isoformat() for x in sorted(
            {date.today() - timedelta(days=i) for i in range(12)}) if x.weekday() < 5]
        c = duckdb.connect(str(DB_TW))
        c.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE)")
        c.executemany("INSERT INTO tw_daily_prices VALUES (?,?,?)", [(x, "2330", 1.0) for x in wd8])
        c.close()
        c = duckdb.connect(str(DB_ETF))
        c.execute("CREATE TABLE active_tw_etf_registry(ticker VARCHAR, name VARCHAR, fund_type VARCHAR, domestic BOOLEAN, daily_required BOOLEAN, status VARCHAR, source VARCHAR, issuer VARCHAR, first_seen VARCHAR, last_seen VARCHAR)")
        c.execute("INSERT INTO active_tw_etf_registry VALUES ('00981A','強棒','x',TRUE,TRUE,'ACTIVE_DOMESTIC','t','群益投信',?,?)", [wd8[0], wd8[-1]])
        c.execute("""CREATE TABLE holdings_daily(portfolio_date DATE, etf_ticker VARCHAR,
            etf_yf_ticker VARCHAR, etf_name VARCHAR, issuer VARCHAR, holding_ticker VARCHAR,
            holding_yf_ticker VARCHAR, holding_name VARCHAR, weight_pct DOUBLE, shares DOUBLE,
            source_type VARCHAR, source_url VARCHAR, fetched_at TIMESTAMP)""")
        c.execute("INSERT INTO holdings_daily (portfolio_date, etf_ticker, holding_ticker) VALUES (?,?,?)", [wd8[0], "00981A", "2330"])
        c.close()
        # 重現工作站狀態:批406 那時無源,日格全被寫成 NO_SOURCE / 過期 PENDING_TODAY
        # fixture 要對「今日」穩健:wd8[-1] 在平日就等於今日,拿它當「過期的今日」
        # 會永遠不復活(判準對、fixture 錯)——初版我就是這樣自撞。
        today8 = date.today().isoformat()
        past8 = [d for d in wd8 if d != today8]
        stale = {d: {"state": "NO_SOURCE", "note": "批406 當時無車道"} for d in past8[1:-1]}
        stale[past8[-1]] = {"state": "PENDING_TODAY", "note": "當時的今日(現已過期)"}
        if today8 in wd8:
            stale[today8] = {"state": "PENDING_TODAY", "note": "真的今日=不該復活"}
        n_nosrc8 = sum(1 for v in stale.values() if v["state"] == "NO_SOURCE")
        CKPT.write_text(json.dumps({"days": {"00981A": stale}}, ensure_ascii=False), encoding="utf-8")
        # ① 沒有 DATED 車道時:NO_SOURCE 不復活(不做白工)
        LANES_JSON.write_text(json.dumps({"schema": "x", "rule": "只增不減", "lanes": [
            {"id": "MONEYDJ", "kind": "LATEST_ONLY", "state": "VERIFIED", "url": "https://x/{yf}"}]},
            ensure_ascii=False), encoding="utf-8")
        bf_a = backfill(max_days=0, net=_NetSpec())
        # ② 有了 VERIFIED DATED 車道:同一批 NO_SOURCE 日格復活並真的補起來
        CKPT.write_text(json.dumps({"days": {"00981A": stale}}, ensure_ascii=False), encoding="utf-8")
        LANES_JSON.write_text(json.dumps({"schema": "x", "rule": "只增不減", "lanes": [
            {"id": "ISSUER_ARCHIVE:群益投信", "kind": "DATED", "state": "VERIFIED",
             "url": "https://x.example/fund/holdings?d={ymd}", "note": "自測"}]},
            ensure_ascii=False), encoding="utf-8")
        bf_b = backfill(max_days=3, net=_NetSpec())
        ck_b = _load_ckpt()["days"]["00981A"]
        n_filled = sum(1 for v in ck_b.values() if v.get("state") == "FILLED")
        chk("㉗ 回補重試律(批411):無 DATED 車道時 NO_SOURCE 不復活(不做白工);"
            "車道驗真後同批日格復活並真補起來;FILLED 永不重跑",
            bf_a["revived"] == 1 and bf_a["tried"] == 1        # 只有過期 PENDING_TODAY 復活
            and bf_b["revived"] == n_nosrc8 + 1 and bf_b["tried"] == 3
            and bf_b["filled"] == 3 and n_filled >= 3,
            f"(無源 revived {bf_a['revived']}/tried {bf_a['tried']} · "
            f"有源 revived {bf_b['revived']}/tried {bf_b['tried']}/filled {bf_b['filled']})")
    DB_ETF, DB_TW, REP, CKPT, OUT_UI, LANES_JSON = _s
    globals().update(DB_ETF=_s[0], DB_TW=_s[1], REP=_s[2], CKPT=_s[3], OUT_UI=_s[4], LANES_JSON=_s[5])
    print(f"  [計] 二十七檢 OK {27 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 主動 ETF 每日持股史深覆蓋(VDF_ENG078 v0105)· 二十七檢自測(零外呼)===")
        return selftest()
    if a and a[0] == "status":
        return status()
    if a and a[0] == "discover":
        discover_twse(net=(_net_or_none() if gate_open() else None), apply="--apply" in a)
        return 0
    if a and a[0] in ("sync", "sync-lanes"):
        sync_lanes(apply="--apply" in a)
        return 0
    if a and a[0] == "probe":
        sync_lanes(apply="--apply" in a)      # 批409:先把新驗證車道加法式併入(只增不減)
        probe_lanes(ticker=(a[a.index("--ticker") + 1] if "--ticker" in a else ""),
                    day=(a[a.index("--date") + 1] if "--date" in a else ""),
                    net=(_net_or_none() if gate_open() else None), apply="--apply" in a)
        return 0
    if a and a[0] == "backfill":
        sync_lanes(apply=True, do_print=True)   # 批409:回補前先併入(只增不減)
        r = backfill(max_days=int(a[a.index("--max-days") + 1]) if "--max-days" in a else 0, net=(_net_or_none() if gate_open() else None))
        print(f"[回補] {r}")
        return 0
    return daily([x for x in a if x != "daily"])


if __name__ == "__main__":
    sys.exit(main())

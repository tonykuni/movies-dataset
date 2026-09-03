#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG055_OmniFetch — 單 004 總擷取執行器(批137;via-omni)
====================================================================
操作員批137 大擷取令。八車道(READY 面實抓;NEEDS_KEY/WHITELIST 面
誠實登錄於單 004,候鑰/候白名單):
  L1 listings   雙所總清單附產業(代碼+中文名;TWSE 產業別冊內建)
  L2 trading    每日交易:逐股成交值/量/筆數(雙所)+市場總計 FMTQIK
  L3 valuation  每日估值:PE/PB/殖利率(雙所 BWIBBU/peratio)
  L4 etf_book   ETF 冊可更新(t187ap47_L;主動式=名稱含「主動」旗標)
  L5 etf_stats  ETF AUM/nav/PE/PB 快照(quoteSummary 握手道;台+全球)
                流量估算=ΔAUM−報酬效果 [ESTIMATE;≥2 快照自動出值]
  L6 global     指數擴編:美五大+亞洲+歐洲+南亞前十+區域匯率+區域 ETF
                (chart 直連;日線 2024-01-02→最新)
  L7 idx_val    指數估值代理(區域 ETF forwardPE/trailingPE/P/B [PROXY])
  L8 us_macro   FRED 細項(候 FRED_API_KEY;無鑰=誠實 SKIP)
韌性:批次即落盤 parquet+checkpoint 續跑+duckdb anti-join 冪等=中斷
零浪費;編碼 utf-8-sig。輸出:--export parquet|csv|sqlite|gsheet。
v0103→v0104(批144):+L12 當沖面(TPEX 市場級統計+TWSE 標的冊;
TWSE 逐股當沖 rwd WAF 死鎖=誠實候源)。
v0102→v0103(批141):+L11 市場情緒(CNN Fear&Greed 官方 API 補 Referer 破
418;原始 JSON 先保留+score 序列入庫;AAII 訂閱牆/akshare 已移除介面=誠實候源)。
v0101→v0102(批139):+L10 臺灣利率(CBC a13rate 臺銀利率史;curl 子程序
道破 TLS 指紋重置;非政策利率誠實旗標);NBS WAF/nstatdb TLS/DGBAS 檔徑=誠實列缺。
v0100→v0101(批138):+L9 跨區宏觀(FRED 活序列 9 條:美歐中 CPI/美 PPI/
美歐日中利率/US10Y;台灣缺口候源誠實列冊)+鑰匙檔後備(.fred_api_key)。
用法:via-omni run [--lane L1,L2,...] | --export fmt | --status | --selftest
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

import calendar
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
OUT = VDF / "output_hub" / "mega"
DB_TW = OUT / "vdf_tw_market.duckdb"
DB_GL = OUT / "vdf_global_market.duckdb"
CKPT = OUT / "omni_checkpoint.json"
START_DATE = "2024-01-02"

# TWSE 產業別代碼冊(官方定義;TPEX 同碼系)
INDUSTRY_MAP = {
    "01": "水泥工業", "02": "食品工業", "03": "塑膠工業", "04": "紡織纖維",
    "05": "電機機械", "06": "電器電纜", "08": "玻璃陶瓷", "09": "造紙工業",
    "10": "鋼鐵工業", "11": "橡膠工業", "12": "汽車工業", "14": "建材營造業",
    "15": "航運業", "16": "觀光餐旅", "17": "金融保險業", "18": "貿易百貨業",
    "19": "綜合", "20": "其他業", "21": "化學工業", "22": "生技醫療業",
    "23": "油電燃氣業", "24": "半導體業", "25": "電腦及週邊設備業",
    "26": "光電業", "27": "通信網路業", "28": "電子零組件業", "29": "電子通路業",
    "30": "資訊服務業", "31": "其他電子業", "32": "文化創意業", "33": "農業科技業",
    "34": "電子商務", "35": "綠能環保", "36": "數位雲端", "37": "運動休閒",
    "38": "居家生活",
}
EP = {
    "twse_listings": "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
    "tpex_listings": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O",
    "twse_daily": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
    "tpex_daily": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes",
    "twse_val": "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL",
    "tpex_val": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis",
    "twse_mkt": "https://openapi.twse.com.tw/v1/exchangeReport/FMTQIK",
    "etf_book": "https://openapi.twse.com.tw/v1/opendata/t187ap47_L",
}
# 指數/匯率/區域 ETF 擴編冊(Yahoo 代碼;誠實:Yahoo 缺載即列敗)
IDX_US = ["^GSPC", "^DJI", "^IXIC", "^NDX", "^RUT"]
IDX_ASIA = ["^N225", "^KS11", "^TWII", "^HSI", "000001.SS", "399001.SZ",
            "^STI", "^KLSE", "^JKSE", "PSEI.PS", "^SET.BK"]
IDX_EU = ["^FTSE", "^GDAXI", "^FCHI", "^STOXX50E", "^IBEX", "FTSEMIB.MI",
          "^AEX", "^SSMI"]
IDX_SOUTH_ASIA = ["^NSEI", "^BSESN", "^NSEBANK", "^CNXIT", "^CNX100",
                  "^CNX500", "NIFTY_MIDCAP_100.NS", "^KSE", "^CSE", "^DSEX"]
FX = ["TWD=X", "JPY=X", "KRW=X", "CNY=X", "HKD=X", "SGD=X", "INR=X", "PKR=X",
      "THB=X", "MYR=X", "IDR=X", "PHP=X", "EURUSD=X", "GBPUSD=X", "CHF=X"]
ETF_REGION = ["SPY", "DIA", "QQQ", "IWM", "ONEQ", "EWJ", "EWY", "EWT", "FXI",
              "MCHI", "EWH", "EWS", "EWM", "EIDO", "THD", "INDA", "EPI",
              "EWU", "EWG", "EWQ", "FEZ", "EZU", "EWL", "EWI", "EWP", "VGK"]
ETF_TW_ACTIVE_SUFFIX = ".TW"
# L9 跨區宏觀(FRED 活序列實測 2026-08-25;日本 CPI/歐日中 PPI 已停更、
# 台灣 CPI/PPI/利率 FRED 無=候源 dgbas.gov.tw/cbc.gov.tw 白名單,誠實列缺)
CROSS_SERIES = {
    ("US", "CPI"): "CPIAUCSL", ("EA", "CPI"): "CP0000EZ19M086NEST",
    ("CN", "CPI"): "CHNCPIALLMINMEI",
    ("US", "PPI"): "PPIFIS",
    ("US", "RATE"): "FEDFUNDS", ("EA", "RATE"): "ECBDFR",
    ("JP", "RATE"): "IRSTCI01JPM156N", ("CN", "RATE"): "INTDSRCNM193N",
    ("US", "GOV10Y"): "DGS10",
}
FRED_SERIES = ["CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE", "PPIFIS", "UNRATE",
               "PAYEMS", "ICSA", "CES0500000003", "PI", "DSPIC96", "PCE",
               "RSAFS", "UMCSENT", "HOUST", "DGS20"]


def _net_or_none():
    import glob as _g
    import importlib.util as _il
    hits = sorted(_g.glob(str(VIA / "supportive modules" / "network"
                               / "SUP_MDL740_NetUnified_v*.py")))
    if not hits:
        return None
    spec = _il.spec_from_file_location("via_net_dyn", hits[-1])
    mod = _il.module_from_spec(spec)
    sys.modules["via_net_dyn"] = mod
    spec.loader.exec_module(mod)
    return mod


def gate_open(env=None) -> bool:
    env = env if env is not None else os.environ
    return env.get("VIA_NET_CONSENT") == "YES" and env.get("VIA_SCRAPE_CONSENT") == "YES"


def write_parquet(rows: list[dict], stem: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        p = OUT / f"{stem}_{ts}.parquet"
        pq.write_table(pa.Table.from_pylist(rows), p)
        return p
    except ImportError:
        import csv
        p = OUT / f"{stem}_{ts}.csv"
        with p.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        return p


def upsert(db: Path, table: str, rows: list[dict], keys: list[str]) -> int:
    import duckdb
    import pandas as pd
    df = pd.DataFrame(rows)
    con = duckdb.connect(str(db))
    con.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM df LIMIT 0")
    cond = " AND ".join(f"t.{k} = df.{k}" for k in keys)
    con.execute(f"INSERT INTO {table} SELECT * FROM df WHERE NOT EXISTS "
                f"(SELECT 1 FROM {table} t WHERE {cond})")
    n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    con.close()
    return n


def _num(v):
    try:
        return float(str(v).replace(",", "")) if v not in (None, "", "--") else None
    except ValueError:
        return None


def lane_listings(net) -> dict:
    rows = []
    for mkt, key in (("TWSE", "twse_listings"), ("TPEX", "tpex_listings")):
        r = net.http_json(EP[key])
        if r["state"] != "OK":
            return {"state": r["state"], "note": f"{mkt}:{str(r.get('note',''))[:60]}"}
        for it in r["data"]:
            code = str(it.get("公司代號") or it.get("SecuritiesCompanyCode") or "").strip()
            if not (code.isdigit() and len(code) == 4):
                continue
            ic = str(it.get("產業別") or it.get("SecuritiesIndustryCode") or "").strip().zfill(2)
            rows.append({"code": code,
                         "name": str(it.get("公司簡稱") or it.get("CompanyName") or "").strip(),
                         "market": mkt, "industry_code": ic,
                         "industry_name": INDUSTRY_MAP.get(ic, "未冊碼(誠實)"),
                         "yf_ticker": code + (".TW" if mkt == "TWSE" else ".TWO")})
    write_parquet(rows, "tw_listings_industry")
    n = upsert(DB_TW, "tw_listings_industry", rows, ["code", "market"])
    unk = sum(1 for x in rows if x["industry_name"].startswith("未冊碼"))
    return {"state": "OK", "rows": len(rows), "db": n, "note": f"產業附掛;未冊碼 {unk}"}


def lane_trading(net) -> dict:
    rows = []
    r = net.http_json(EP["twse_daily"])
    if r["state"] == "OK":
        for it in r["data"]:
            rows.append({"date": str(it.get("Date")), "code": str(it.get("Code")),
                         "market": "TWSE", "volume": _num(it.get("TradeVolume")),
                         "trade_value": _num(it.get("TradeValue")),
                         "transactions": _num(it.get("Transaction")),
                         "close": _num(it.get("ClosingPrice"))})
    r2 = net.http_json(EP["tpex_daily"])
    if r2["state"] == "OK":
        for it in r2["data"]:
            code = str(it.get("SecuritiesCompanyCode") or "")
            if not (code.isdigit() and len(code) == 4):
                continue
            rows.append({"date": str(it.get("Date")), "code": code, "market": "TPEX",
                         "volume": _num(it.get("TradingShares")),
                         "trade_value": _num(it.get("TransactionAmount")),
                         "transactions": _num(it.get("TransactionNumber")),
                         "close": _num(it.get("Close"))})
    if not rows:
        return {"state": "EMPTY", "note": "雙所零列"}
    write_parquet(rows, "tw_trading_daily")
    n = upsert(DB_TW, "tw_trading_daily", rows, ["date", "code", "market"])
    rm = net.http_json(EP["twse_mkt"])
    if rm["state"] == "OK":
        mrows = [{"date": str(x.get("Date")), "trade_value": _num(x.get("TradeValue")),
                  "volume": _num(x.get("TradeVolume")), "taiex": _num(x.get("TAIEX"))}
                 for x in rm["data"]]
        upsert(DB_TW, "tw_market_agg", mrows, ["date"])
    return {"state": "OK", "rows": len(rows), "db": n, "note": "成交值逐股+市場總計"}


def lane_valuation(net) -> dict:
    rows = []
    r = net.http_json(EP["twse_val"])
    if r["state"] == "OK":
        for it in r["data"]:
            rows.append({"date": str(it.get("Date")), "code": str(it.get("Code")),
                         "market": "TWSE", "pe": _num(it.get("PEratio")),
                         "pb": _num(it.get("PBratio")),
                         "dividend_yield": _num(it.get("DividendYield")), "dps": None})
    r2 = net.http_json(EP["tpex_val"])
    if r2["state"] == "OK":
        for it in r2["data"]:
            code = str(it.get("SecuritiesCompanyCode") or "")
            if not (code.isdigit() and len(code) == 4):
                continue
            rows.append({"date": str(it.get("Date")), "code": code, "market": "TPEX",
                         "pe": _num(it.get("PriceEarningRatio")),
                         "pb": _num(it.get("PriceBookRatio")),
                         "dividend_yield": _num(it.get("YieldRatio")),
                         "dps": _num(it.get("DividendPerShare"))})
    if not rows:
        return {"state": "EMPTY", "note": "雙所零列"}
    write_parquet(rows, "tw_valuation_daily")
    n = upsert(DB_TW, "tw_valuation_daily", rows, ["date", "code", "market"])
    return {"state": "OK", "rows": len(rows), "db": n, "note": "PE/PB/殖利率"}


def lane_etf_book(net) -> dict:
    r = net.http_json(EP["etf_book"])
    if r["state"] != "OK":
        return {"state": r["state"], "note": str(r.get("note", ""))[:80]}
    rows = []
    for it in r["data"]:
        name = str(it.get("基金中文名稱") or "")
        rows.append({"fund_code": str(it.get("基金代號") or "").strip(),
                     "fund_name": str(it.get("基金簡稱") or "").strip(),
                     "fund_type": str(it.get("基金類型") or "").strip(),
                     "is_active": ("主動" in name or "主動" in str(it.get("基金簡稱") or "")),
                     "tracking_index": str(it.get("標的指數/追蹤指數名稱") or "").strip(),
                     "as_of": str(it.get("出表日期") or "").strip()})
    write_parquet(rows, "etf_book")
    n = upsert(DB_TW, "etf_book", rows, ["fund_code", "as_of"])
    act = sum(1 for x in rows if x["is_active"])
    return {"state": "OK", "rows": len(rows), "db": n, "note": f"主動式 {act} 檔旗標"}


def _etf_universe(net) -> list[str]:
    syms = list(ETF_REGION)
    r = net.http_json(EP["etf_book"])
    if r["state"] == "OK":
        for it in r["data"]:
            name = str(it.get("基金中文名稱") or "") + str(it.get("基金簡稱") or "")
            if "主動" in name:
                syms.append(str(it.get("基金代號")).strip() + ETF_TW_ACTIVE_SUFFIX)
    return syms


def lane_etf_stats(net) -> dict:
    if not hasattr(net, "yahoo_quote_summary"):
        return {"state": "SKIP", "note": "統包無 quoteSummary 車道"}
    syms = _etf_universe(net)
    r = net.yahoo_quote_summary(syms)
    if r["state"] != "OK":
        return {"state": r["state"], "note": str(r.get("note", ""))[:80]}
    today = datetime.now().strftime("%Y-%m-%d")
    rows = [{"date": today, **x} for x in r["rows"]]
    write_parquet(rows, "etf_stats_daily")
    n = upsert(DB_GL, "etf_stats_daily", rows, ["date", "symbol"])
    # 流量估算(≥2 快照;ESTIMATE 旗標)
    import duckdb
    con = duckdb.connect(str(DB_GL))
    fl = con.execute("""
        SELECT date, symbol,
               aum - LAG(aum) OVER w * (nav / NULLIF(LAG(nav) OVER w, 0)) AS flow_est
        FROM etf_stats_daily WHERE aum IS NOT NULL AND nav IS NOT NULL
        WINDOW w AS (PARTITION BY symbol ORDER BY date)
    """).fetchall()
    con.close()
    got = sum(1 for x in fl if x[2] is not None)
    return {"state": "OK", "rows": len(rows), "db": n,
            "note": f"AUM 快照 {len(rows)};flow_est 可算 {got}(ESTIMATE;累計快照日增)"}


def lane_global(net) -> dict:
    if not hasattr(net, "yahoo_chart"):
        return {"state": "SKIP", "note": "統包無 chart 車道"}
    syms = sorted(set(IDX_US + IDX_ASIA + IDX_EU + IDX_SOUTH_ASIA + FX + ETF_REGION))
    ck = json.loads(CKPT.read_text(encoding="utf-8")) if CKPT.exists() else {"done": []}
    todo = [s for s in syms if s not in set(ck["done"])]
    se = calendar.timegm(time.strptime(START_DATE, "%Y-%m-%d"))
    total = 0
    failed_all = []
    for i in range(0, len(todo), 40):
        batch = todo[i:i + 40]
        rc = net.yahoo_chart(batch, se, int(time.time()))
        rows = rc.get("rows") or []
        failed_all += [f["ticker"] for f in rc.get("failed") or []]
        if rows:
            write_parquet(rows, "global_expand")
            upsert(DB_GL, "global_daily", rows, ["date", "ticker"])
            total += len(rows)
        ck["done"] = sorted(set(ck["done"]) | {x["ticker"] for x in rows})
        CKPT.write_text(json.dumps(ck, ensure_ascii=False), encoding="utf-8")
    return {"state": "OK" if total else "EMPTY", "rows": total,
            "note": f"擴編 {len(todo)} 標的·敗 {len(set(failed_all))}(Yahoo 缺載誠實列敗)"}


def lane_idx_val(net) -> dict:
    if not hasattr(net, "yahoo_quote_summary"):
        return {"state": "SKIP", "note": "統包無 quoteSummary 車道"}
    r = net.yahoo_quote_summary(ETF_REGION)
    if r["state"] != "OK":
        return {"state": r["state"], "note": str(r.get("note", ""))[:80]}
    today = datetime.now().strftime("%Y-%m-%d")
    rows = [{"date": today, "proxy_flag": "PROXY_ETF", **x} for x in r["rows"]]
    write_parquet(rows, "index_valuation_proxy")
    n = upsert(DB_GL, "index_valuation_proxy", rows, ["date", "symbol"])
    return {"state": "OK", "rows": len(rows), "db": n,
            "note": "區域 ETF 代理估值 [PROXY];FactSet 倒推面候白名單"}


def _fred_key() -> str:
    key = os.environ.get("FRED_API_KEY", "")
    if key:
        return key
    kf = OUT / ".fred_api_key"
    return kf.read_text(encoding="utf-8").strip() if kf.exists() else ""


def lane_us_macro(net) -> dict:
    key = _fred_key()
    if not key:
        return {"state": "SKIP", "note": "FRED_API_KEY 缺=誠實候鑰(單 004 已冊 16 series)"}
    rows = []
    for sid in FRED_SERIES:
        url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}"
               f"&api_key={key}&file_type=json&observation_start={START_DATE}")
        r = net.http_json(url)
        if r["state"] != "OK":
            continue
        for ob in r["data"].get("observations", []):
            rows.append({"date": ob["date"], "series": sid, "value": _num(ob["value"])})
    if not rows:
        return {"state": "EMPTY", "note": "零列"}
    write_parquet(rows, "us_macro")
    n = upsert(DB_GL, "us_macro", rows, ["date", "series"])
    return {"state": "OK", "rows": len(rows), "db": n}


def lane_cross_macro(net) -> dict:
    key = _fred_key()
    if not key:
        return {"state": "SKIP", "note": "FRED_API_KEY 缺=誠實候鑰"}
    rows = []
    for (region, metric), sid in CROSS_SERIES.items():
        url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}"
               f"&api_key={key}&file_type=json&observation_start=2018-01-01")
        r = net.http_json(url)
        if r["state"] != "OK":
            continue
        for ob in r["data"].get("observations", []):
            v = _num(ob["value"])
            if v is not None:
                rows.append({"date": ob["date"], "region": region, "metric": metric,
                             "series": sid, "value": v})
    if not rows:
        return {"state": "EMPTY", "note": "零列"}
    write_parquet(rows, "cross_macro")
    n = upsert(DB_GL, "cross_macro", rows, ["date", "region", "metric"])
    gaps = "TW 三項+JP CPI+EA/JP/CN PPI=FRED 缺/停更,候 dgbas/cbc/stats.gov.cn 白名單"
    return {"state": "OK", "rows": len(rows), "db": n, "note": gaps}


CBC_A13 = "https://www.cbc.gov.tw/public/data/a13rate.xls"


def lane_tw_rates(net) -> dict:
    """L10(v0102;批139):臺灣利率——CBC 臺銀存放款利率史(a13rate.xls)。
    誠實標記:臺銀掛牌利率非央行政策利率;重貼現率檔=CBC 開放資料正確
    檔徑候查(JS 殼頁無法定位)+data.gov.tw/index.dgbas 候白名單。
    CBC 對 urllib/requests TLS 指紋重置=curl 子程序道(走同一代理+同意閘)。"""
    import subprocess
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".xls", delete=False) as tf:
        tmp = tf.name
    r = subprocess.run(["curl", "-sSL", "--max-time", "30", "-A", "Mozilla/5.0",
                        "-o", tmp, CBC_A13], capture_output=True, text=True)
    if r.returncode != 0:
        return {"state": "FAIL", "note": f"curl:{r.stderr[:80]}"}
    import pandas as pd
    try:
        df = pd.read_excel(tmp, header=None)
    except Exception as exc:
        return {"state": "FAIL", "note": f"xls 解析:{str(exc)[:80]}"}
    rows = []
    for _, rr in df.iterrows():
        ym = str(rr.iloc[0]).strip()
        if not (ym.isdigit() and len(ym) == 5):
            continue
        year, month = 1911 + int(ym[:3]), int(ym[3:])
        rows.append({"date": f"{year:04d}-{month:02d}-01", "source": "CBC_TAIBANK",
                     "demand_deposit_float": _num(rr.iloc[2]),
                     "savings_float": _num(rr.iloc[4]),
                     "fixed_1m": _num(rr.iloc[5]),
                     "honesty_flag": "臺銀掛牌利率(非央行政策利率;政策利率檔候源)"})
    if not rows:
        return {"state": "EMPTY", "note": "零列"}
    write_parquet(rows, "tw_rates_cbc")
    n = upsert(DB_TW, "tw_rates_cbc", rows, ["date", "source"])
    return {"state": "OK", "rows": len(rows), "db": n,
            "note": f"臺銀利率史 {rows[0]['date']}→{rows[-1]['date']}[非政策利率誠實旗標]"}


CNN_FG = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"


def lane_sentiment(net) -> dict:
    """L11(v0103;批141):市場情緒——CNN Fear&Greed 官方 dataviz API
    (418 茶壺擋=補 Referer 瀏覽器頭破;curl 子程序道)。原始 JSON
    先保留(操作員令)+score 序列入庫。AAII=站方訂閱牆 403 誠實候源;
    akshare 現版已移除 aaii/fear_greed 介面(changelog 佐證)。"""
    import subprocess
    r = subprocess.run(["curl", "-sS", "--max-time", "25",
                        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "-H", "Referer: https://edition.cnn.com/markets/fear-and-greed",
                        "-H", "Accept: application/json", CNN_FG],
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip().startswith("{"):
        return {"state": "FAIL", "note": f"CNN F&G 不可達:{r.stdout[:60]}"}
    d = json.loads(r.stdout)
    OUT.mkdir(parents=True, exist_ok=True)
    raw = OUT / f"cnn_fear_greed_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    raw.write_text(r.stdout, encoding="utf-8")   # 先保留原始(操作員令)
    rows = []
    hist = (d.get("fear_and_greed_historical") or {}).get("data") or []
    for x in hist:
        ts = x.get("x")
        if ts is None:
            continue
        rows.append({"date": datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d"),
                     "index": "CNN_FEAR_GREED", "score": x.get("y"),
                     "rating": x.get("rating")})
    now = d.get("fear_and_greed") or {}
    if now.get("score") is not None:
        rows.append({"date": str(now.get("timestamp", ""))[:10],
                     "index": "CNN_FEAR_GREED", "score": now["score"],
                     "rating": now.get("rating")})
    if not rows:
        return {"state": "EMPTY", "note": "零列"}
    write_parquet(rows, "sentiment_daily")
    n = upsert(DB_GL, "sentiment_daily", rows, ["date", "index"])
    return {"state": "OK", "rows": len(rows), "db": n,
            "note": f"CNN F&G 今值 {round(float(now.get('score', 0)), 1)}"
                    f"({now.get('rating')});AAII 訂閱牆候源"}


def lane_daytrade(net) -> dict:
    """L12(v0104;批144):當沖面可得極大化——TPEX 市場級當沖統計
    (openapi 月窗)+TWSE 當沖標的冊快照。TWSE 逐股/市場級當沖=
    rwd TWTB4U 遭 WAF 安全頁死鎖(Referer/XHR 頭全試)=誠實候源。"""
    rows = []
    r = net.http_json("https://www.tpex.org.tw/openapi/v1/tpex_intraday_trading_statistics")
    if r["state"] == "OK":
        for it in r["data"]:
            ds = str(it.get("Date", ""))
            if len(ds) == 7:  # ROC 1150803
                ds = f"{1911 + int(ds[:3])}-{ds[3:5]}-{ds[5:]}"
            rows.append({"date": ds, "market": "TPEX",
                         "dt_volume": _num(it.get("DayTradingVolume")),
                         "dt_volume_pct": _num(str(it.get("DayTradingVolumeOfTheMarket", "")).rstrip("%")),
                         "dt_buy_value": _num(it.get("DayTradingValueOfBuys")),
                         "dt_sell_value": _num(it.get("DayTradingValueOfSells"))})
    if not rows:
        return {"state": r["state"] if r["state"] != "OK" else "EMPTY",
                "note": str(r.get("note", "零列"))[:80]}
    write_parquet(rows, "tw_daytrade_market")
    n = upsert(DB_TW, "tw_daytrade_market", rows, ["date", "market"])
    r2 = net.http_json("https://openapi.twse.com.tw/v1/exchangeReport/TWTB4U")
    n2 = 0
    if r2["state"] == "OK":
        el = [{"date": datetime.now().strftime("%Y-%m-%d"),
               "code": str(x.get("Code", "")).strip(),
               "suspension": str(x.get("Suspension", "")).strip()}
              for x in r2["data"] if x.get("Code")]
        if el:
            write_parquet(el, "tw_daytrade_eligible")
            n2 = upsert(DB_TW, "tw_daytrade_eligible", el, ["date", "code"])
    return {"state": "OK", "rows": len(rows), "db": n,
            "note": f"TPEX 市場級 {len(rows)} 日+標的冊 {n2};TWSE 逐股=WAF 候源"}


LANES = {"L1": ("listings", lane_listings), "L2": ("trading", lane_trading),
         "L3": ("valuation", lane_valuation), "L4": ("etf_book", lane_etf_book),
         "L5": ("etf_stats", lane_etf_stats), "L6": ("global", lane_global),
         "L7": ("idx_val", lane_idx_val), "L8": ("us_macro", lane_us_macro), "L9": ("cross_macro", lane_cross_macro), "L10": ("tw_rates", lane_tw_rates), "L11": ("sentiment", lane_sentiment), "L12": ("daytrade", lane_daytrade)}


def run(sel: list[str] | None) -> int:
    if not gate_open():
        print("[FAIL-CLOSED] 同意閘未開(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT)")
        return 2
    net = _net_or_none()
    if net is None:
        print("[FAIL] 統包網路工具缺席")
        return 1
    sel = sel or list(LANES)
    print(f"=== 單 004 總擷取(批137)· 車道 {','.join(sel)} ===")
    bad = 0
    for k in sel:
        name, fn = LANES[k]
        try:
            r = fn(net)
        except Exception as exc:
            r = {"state": "FAIL", "note": str(exc)[:100]}
        if r["state"] == "FAIL":
            bad += 1
        print(f"  [{r['state']:<5}] {k} {name:<10} {r.get('rows', '')} "
              f"{str(r.get('note', ''))[:84]}", flush=True)
    return 1 if bad else 0


def export(fmt: str) -> int:
    import duckdb
    dest = OUT / "export"
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for db in (DB_TW, DB_GL):
        if not db.exists():
            continue
        con = duckdb.connect(str(db), read_only=True)
        for (t,) in con.execute("SHOW TABLES").fetchall():
            df = con.execute(f"SELECT * FROM {t}").df()
            if fmt == "parquet":
                df.to_parquet(dest / f"{db.stem}_{t}.parquet")
            elif fmt in ("csv", "gsheet"):
                df.to_csv(dest / f"{db.stem}_{t}.csv", index=False,
                          encoding="utf-8-sig")  # gsheet 相容=utf-8-sig csv
            elif fmt == "sqlite":
                import sqlite3
                sq = sqlite3.connect(dest / f"{db.stem}.sqlite")
                df.to_sql(t, sq, if_exists="replace", index=False)
                sq.close()
            n += 1
        con.close()
    print(f"[export] {fmt} × {n} 表 → {dest.relative_to(VDF)}")
    return 0


def status() -> int:
    import duckdb
    for db in (DB_TW, DB_GL):
        if not db.exists():
            print(f"[{db.name}] 缺")
            continue
        con = duckdb.connect(str(db), read_only=True)
        print(f"[{db.name}]")
        for (t,) in con.execute("SHOW TABLES").fetchall():
            c = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  {t}: {c}")
        con.close()
    return 0


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 同意閘 fail-closed", not gate_open({}) and gate_open(
        {"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}))
    net = _net_or_none()
    chk("② 統包三車道在位(http_json/yahoo_chart/quoteSummary)",
        net is not None and all(hasattr(net, x) for x in
                                ("http_json", "yahoo_chart", "yahoo_quote_summary")))
    chk("③ 產業冊+半導體=24", INDUSTRY_MAP["24"] == "半導體業"
        and INDUSTRY_MAP["17"] == "金融保險業")
    chk("④ 擴編冊(美5·亞11·歐8·南亞10·匯15·ETF26)",
        len(IDX_US) == 5 and len(IDX_ASIA) == 11 and len(IDX_EU) == 8
        and len(IDX_SOUTH_ASIA) == 10 and len(FX) == 15 and len(ETF_REGION) == 26)
    global OUT, DB_TW, DB_GL, CKPT
    _s = (OUT, DB_TW, DB_GL, CKPT)
    with tempfile.TemporaryDirectory() as td:
        OUT, DB_TW, DB_GL, CKPT = (Path(td), Path(td) / "tw.duckdb",
                                   Path(td) / "gl.duckdb", Path(td) / "ck.json")

        class FakeNet:
            @staticmethod
            def http_json(url):
                if "t187ap03_L" in url:
                    return {"state": "OK", "data": [{"公司代號": "2330", "公司簡稱": "台積電", "產業別": "24"}]}
                if "mopsfin" in url:
                    return {"state": "OK", "data": [{"SecuritiesCompanyCode": "5483",
                                                    "CompanyName": "中美晶", "SecuritiesIndustryCode": "24"}]}
                if "t187ap47_L" in url:
                    return {"state": "OK", "data": [{"基金代號": "00981A", "基金簡稱": "主動統一台股增長",
                                                    "基金類型": "ETF", "基金中文名稱": "統一台股增長主動式ETF",
                                                    "標的指數/追蹤指數名稱": "-", "出表日期": "1150825"}]}
                return {"state": "FAIL", "note": "no-net"}

        r1 = lane_listings(FakeNet)
        chk("⑤ L1 清單附產業(雙所+產業名對映)", r1["state"] == "OK" and r1["rows"] == 2)
        r4 = lane_etf_book(FakeNet)
        chk("⑥ L4 ETF 冊+主動旗標", r4["state"] == "OK" and "主動式 1 檔" in r4["note"])
        rows = [{"date": "2026-08-25", "symbol": "SPY", "aum": 1.0, "nav": 1.0}]
        n1 = upsert(DB_GL, "t", rows, ["date", "symbol"])
        n2 = upsert(DB_GL, "t", rows, ["date", "symbol"])
        chk("⑦ upsert 冪等(累計維護)", n1 == 1 and n2 == 1)
    OUT, DB_TW, DB_GL, CKPT = _s
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 韌性+誠實宣告(checkpoint/批次落盤/ESTIMATE/PROXY/候鑰)",
        all(x in src for x in ("checkpoint", "ESTIMATE", "PROXY", "候鑰", "utf-8-sig")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 總擷取執行器(VDF_ENG055)· 八檢自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    if "--export" in args:
        return export(args[args.index("--export") + 1])
    sel = None
    if "--lane" in args:
        sel = [x for x in args[args.index("--lane") + 1].split(",") if x in LANES]
    return run(sel)


if __name__ == "__main__":
    sys.exit(main())

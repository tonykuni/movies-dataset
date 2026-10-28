from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

# =============================================================================
# 0 · PARAMETERS — no scoring, indicators, event study, or portfolio calculations
# =============================================================================
import argparse
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

VERSION = "v036"
ENGINE = "VDF_TW_DataFetchEngine"
DEFAULT_VIA_ROOT = Path(os.environ.get("VIA_ROOT", r"C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics"))
DEFAULT_OUTPUT = Path(os.environ.get("VIA_VDF_FETCH_OUTPUT", r"C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics\via_01_vdf\standalone_tw_fetch"))
DEFAULT_TICKERS = "ALL"
DEFAULT_DATASETS = "daily,indices,financial,revenue"
DEFAULT_START = None  # first run: latest official snapshot; --start enables backfill
DEFAULT_TIMEOUT = 35
DEFAULT_RETRIES = 3
DEFAULT_INTERVAL = 1.1
DEFAULT_REFRESH_DAYS = 7  # T+2 corrections plus weekends
DEFAULT_CACHE_HOURS = 12
DEFAULT_BATCH_SIZE = 50
DEFAULT_CLOSE_ABS_TOLERANCE = 0.02
DEFAULT_CLOSE_REL_TOLERANCE = 0.0001
DEFAULT_TURNOVER_DAYTRADE_METHOD = "average"  # average / sum / buy / sell
DEFAULT_MEMORY_LIMIT = "512MB"
DEFAULT_FINANCIAL_SCOPE = "UNSPECIFIED"  # never infer consolidated scope without evidence
NON_ADDITIVE_CASHFLOW_ACCOUNTS = r"期初|期末|餘額|資產負債表帳列"
OFFICIAL_NO_SESSION_MESSAGE = r"沒有符合條件的資料|查無資料|查無當日資料"
CSV_ENCODING = "utf-8-sig"
TWSE_API = "https://openapi.twse.com.tw/v1"
TPEX_API = "https://www.tpex.org.tw/openapi/v1"
TWSE_WEB = "https://www.twse.com.tw/rwd/zh"
TPEX_WEB = "https://www.tpex.org.tw/www/zh-tw"
MOPS_WEB = "https://mopsov.twse.com.tw/mops/web"
STOCK_REGEX = r"^[1-9]\d{3}$"
STATEMENTS = {"BALANCE_SHEET": "03", "INCOME_STATEMENT": "04", "CASH_FLOW": "05"}
INDEX_IDENTITIES = {
    "TAIEX": {"ticker": "TAIEX", "yfinance_ticker": "^TWII", "bloomberg_ticker": "TWSE Index", "name": "發行量加權股價指數", "market": "TWSE"},
    "TPEX": {"ticker": "TPEX", "yfinance_ticker": "^TWOII", "bloomberg_ticker": None, "name": "櫃買指數", "market": "TPEX"},
}  # TPEX Bloomberg alias needs verified local SSOT; do not invent an identifier.
DATASET_KEYS = {
    "tw_equity_daily": ["date", "ticker"],
    "tw_index_daily": ["date", "ticker"],
    "tw_financial": ["date", "ticker", "financial_statement", "account", "unit", "basis", "report_scope", "source"],
    "tw_monthly_revenue": ["date", "ticker", "account", "unit", "source"],
    "tw_universe": ["date", "ticker"],
}
DB_TABLES = {
    "VDF_TWEquity_Daily": ["tw_equity_daily", "tw_universe"],
    "VDF_TWIndex_Daily": ["tw_index_daily"],
    "VDF_TWFinancial": ["tw_financial", "tw_monthly_revenue"],
}
DAILY_COLUMNS = [
    "date", "ticker", "yfinance_ticker", "bloomberg_ticker", "name",
    "open", "low", "high", "close", "adj_open", "adj_low", "adj_high", "adj_close",
    "volume", "turnover", "volume_ex_daytrade", "turnover_ex_daytrade", "market_cap",
    "inst_foreign_net", "inst_trust_net", "inst_dealer_net", "inst_total_net",
    "inst_foreign_ex_dealer_net", "inst_foreign_dealer_net", "margin_balance", "short_balance",
    "day_trade_volume", "day_trade_buy_value", "day_trade_sell_value", "day_trade_value",
    "yf_close", "yf_adj_close", "yf_volume", "adjustment_factor", "close_check",
    "adjustment_status", "daytrade_status", "daytrade_value_method", "inst_check",
    "market", "currency", "market_cap_source", "shares_outstanding", "source",
    "source_date", "fetched_at", "adj_as_of", "quality",
]
FINANCIAL_COLUMNS = [
    "date", "ticker", "yfinance_ticker", "bloomberg_ticker", "name",
    "financial_statement", "account", "unit", "value", "source",
    "basis", "fiscal_year", "quarter", "period_start", "report_scope", "is_derived",
    "derivation", "source_report_period", "source_date", "fetched_at", "currency",
]
CSV_HEADERS = {
    "date":"DATE", "ticker":"TICKER", "yfinance_ticker":"YFINANCE TICKER",
    "bloomberg_ticker":"BLOOMBERG TICKER", "name":"NAME", "open":"OPEN", "low":"LOW",
    "high":"HIGH", "close":"CLOSE", "adj_open":"ADJ OPEN", "adj_low":"ADJ LOW",
    "adj_high":"ADJ HIGH", "adj_close":"ADJ CLOSE", "volume":"VOLUME", "turnover":"TURNOVER",
    "volume_ex_daytrade":"VOLUME(扣除當沖)", "turnover_ex_daytrade":"TURNOVER(扣除當沖)",
    "market_cap":"MARKET CAP", "financial_statement":"FINANCIAL STATEMENT", "account":"ACCOUNT",
    "unit":"UNIT", "value":"VALUE", "source":"SOURCE",
}
ALIASES = {
    "date": ["Date", "日期", "資料日期"],
    "ticker": ["Code", "SecuritiesCompanyCode", "公司代號", "證券代號", "代號", "股票代號"],
    "name": ["公司簡稱", "CompanyAbbreviation", "Name", "CompanyName", "證券名稱", "名稱", "公司名稱"],
    "open": ["OpeningPrice", "Open", "開盤價", "開盤", "開市", "開盤指數"],
    "low": ["LowestPrice", "Low", "最低價", "最低", "最低指數"],
    "high": ["HighestPrice", "High", "最高價", "最高", "最高指數"],
    "close": ["ClosingPrice", "Close", "收盤價", "收盤", "收市", "收盤指數"],
    "volume": ["TradeVolume", "TradingShares", "成交股數"],
    "turnover": ["TradeValue", "TransactionAmount", "成交金額", "成交金額(元)"],
    "shares_outstanding": ["Capitals", "發行股數"],
    "day_trade_volume": ["當日沖銷交易成交股數", "當日沖銷交易 成交股數", "DayTradingVolume"],
    "day_trade_buy_value": ["當日沖銷交易買進成交金額", "當日沖銷交易 買進成交金額"],
    "day_trade_sell_value": ["當日沖銷交易賣出成交金額", "當日沖銷交易 賣出成交金額"],
}

# =============================================================================
# 1 · Pure normalizers and identities
# =============================================================================
def def_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def def_today() -> pd.Timestamp:
    return pd.Timestamp(datetime.now(ZoneInfo("Asia/Taipei")).date())


def def_number(value):
    if value is None or pd.isna(value):
        return float("nan")
    text = str(value).strip().replace(",", "").replace("\u3000", "").replace("−", "-")
    if re.fullmatch(r"\(\s*[\d.]+\s*\)", text):
        text = "-" + text.strip("() ")
    number = pd.to_numeric(text, errors="coerce")
    return number if pd.notna(number) and math.isfinite(number) else float("nan")


def def_date(value) -> pd.Timestamp:
    if isinstance(value, (pd.Timestamp, datetime)):
        return pd.Timestamp(value).tz_localize(None).normalize()
    text = str(value).strip()
    match = re.fullmatch(r"(\d{2,4})[/年-](\d{1,2})[/月-](\d{1,2})日?", text)
    if match:
        year, month, day = map(int, match.groups())
        return pd.Timestamp(year=year + (1911 if year < 1911 else 0), month=month, day=day)
    if re.fullmatch(r"\d{7,8}", text):
        n = len(text) - 4
        year = int(text[:n])
        return pd.Timestamp(year=year + (1911 if year < 1911 else 0), month=int(text[n:n+2]), day=int(text[n+2:]))
    raise ValueError(f"Unrecognized date: {value!r}")


def def_key(text) -> str:
    return re.sub(r"[\s()（）_\-]", "", re.sub(r"<[^>]+>", "", str(text))).lower()


def def_value(record: dict, aliases, default=None):
    normalized = {def_key(k): v for k, v in record.items()}
    for alias in aliases:
        if def_key(alias) in normalized:
            return normalized[def_key(alias)]
    return default


def def_identity(ticker: str, market: str, name: str) -> dict:
    ticker = str(ticker).strip()
    if not re.fullmatch(STOCK_REGEX, ticker) or market not in ("TWSE", "TPEX"):
        raise ValueError(f"Unknown equity identity: {ticker}/{market}")
    return {"ticker": ticker, "yfinance_ticker": ticker + (".TW" if market == "TWSE" else ".TWO"),
            "bloomberg_ticker": f"{ticker} TT", "name": name, "market": market}


def def_tables(payload) -> list[dict]:
    if isinstance(payload, list):
        return [{"records": payload}]
    if not isinstance(payload, dict):
        raise ValueError("JSON payload must be an object or array")
    tables = list(payload.get("tables", []))
    for key in payload:
        if re.fullmatch(r"fields\d*", key):
            suffix = key[6:]
            if "data" + suffix in payload:
                tables.append({"fields": payload[key], "data": payload["data" + suffix], "date": payload.get("date"), "title": payload.get("title", "")})
    if not tables and payload.get("stat") not in (None, "OK", "ok"):
        raise ValueError(f"Official endpoint: {payload.get('stat')}")
    return tables


def def_records(table: dict):
    if "records" in table:
        return table["records"]
    fields = table.get("fields", [])
    if len(fields) != len(set(fields)):
        raise ValueError("Duplicate source column names require a dedicated positional parser")
    if any(len(row) != len(fields) for row in table.get("data", [])):
        raise ValueError("Official response field/row length mismatch")
    return [dict(zip(fields, row)) for row in table.get("data", [])]


def def_assert_unique(frame: pd.DataFrame, keys: list[str]):
    if not frame.empty and frame.duplicated(keys).any():
        raise ValueError(f"Duplicate primary key: {keys}; sample={frame.loc[frame.duplicated(keys, keep=False), keys].head().to_dict('records')}")


def def_payload_date(payload, table, requested):
    candidate = table.get("date") or (payload.get("date") if isinstance(payload, dict) else None)
    if candidate:
        day = def_date(candidate)
        if requested is not None and day != pd.Timestamp(requested):
            raise ValueError(f"Source date mismatch: requested={requested}, received={day}")
        return day
    return pd.Timestamp(requested) if requested is not None else pd.NaT


def def_normalize_quotes(payload, market: str, source: str, requested=None) -> pd.DataFrame:
    rows = []
    for table in def_tables(payload):
        fields = table.get("fields", [])
        if fields and not any(def_key(x) in {def_key(k) for k in ALIASES["ticker"]} for x in fields):
            continue
        for record in def_records(table):
            ticker = str(def_value(record, ALIASES["ticker"], "")).strip()
            if not re.fullmatch(STOCK_REGEX, ticker):
                continue
            date_value = def_value(record, ALIASES["date"])
            day = def_date(date_value) if date_value else def_payload_date(payload, table, requested)
            if pd.isna(day) or (requested is not None and day != pd.Timestamp(requested)):
                raise ValueError(f"Quote date invalid for {ticker}: {day}")
            row = {**def_identity(ticker, market, str(def_value(record, ALIASES["name"], ""))),
                   "date": day, "source": source, "source_date": day, "fetched_at": def_now(), "currency": "TWD"}
            for col in ("open", "low", "high", "close", "volume", "turnover", "shares_outstanding"):
                row[col] = def_number(def_value(record, ALIASES[col]))
            if row["close"] <= 0:
                row["close"] = float("nan")
            row["market_cap"] = row["close"] * row["shares_outstanding"]
            row["market_cap_source"] = source + "#close*issued_shares" if pd.notna(row["market_cap"]) else None
            rows.append(row)
    out = pd.DataFrame(rows)
    if not out.empty:
        def_assert_unique(out, ["date", "ticker"])
        valid = out[["open", "low", "high", "close"]].notna().all(axis=1)
        bad = valid & ((out.low > out.high) | (out.open < out.low) | (out.open > out.high) | (out.close < out.low) | (out.close > out.high))
        if bad.any():
            raise ValueError("Invalid official OHLC bounds")
    return out


def def_normalize_roster(payload, market, source):
    rows = []
    for record in payload:
        code = str(def_value(record, ALIASES["ticker"], "")).strip()
        if re.fullmatch(STOCK_REGEX, code):
            date = def_date(def_value(record, ["出表日期", "Date"]))
            rows.append({**def_identity(code, market, str(def_value(record, ALIASES["name"], ""))), "date": date,
                         "industry": def_value(record, ["產業別", "SecuritiesIndustryCode"]), "source": source})
    out = pd.DataFrame(rows)
    if out.empty:
        raise ValueError(f"Empty official company roster: {market}")
    def_assert_unique(out, ["ticker"])
    return out

# =============================================================================
# 2 · Official chips, day trading, raw-close cross-check and adjusted OHLC
# =============================================================================
def def_normalize_chips(payload, market, kind, day, source):
    rows = []
    for table in def_tables(payload):
        fields = table.get("fields", [])
        if not fields or not any(def_key(x) in {def_key(k) for k in ALIASES["ticker"]} for x in fields):
            continue
        actual = def_payload_date(payload, table, day)
        for raw in table.get("data", []):
            code = str(raw[0]).strip()
            if not re.fullmatch(STOCK_REGEX, code):
                continue
            row = {"date": actual, "ticker": code}
            if kind == "institutional":
                if market == "TPEX":
                    # Current official 24-column layout: foreign ex dealer, foreign dealer,
                    # combined foreign, trust, dealer proprietary, dealer hedge, combined dealer, total.
                    if len(fields) != 24 or fields[-1] != "三大法人買賣超股數合計":
                        raise ValueError("TPEX institutional schema changed")
                    ix = {"inst_foreign_ex_dealer_net": 4, "inst_foreign_dealer_net": 7,
                          "inst_foreign_net": 10, "inst_trust_net": 13, "inst_dealer_net": 22, "inst_total_net": 23}
                else:
                    ix = {}
                    candidates = {
                        "inst_foreign_ex_dealer_net": ["外陸資買賣超股數(不含外資自營商)", "外資及陸資買賣超股數(不含外資自營商)"],
                        "inst_foreign_dealer_net": ["外資自營商買賣超股數"],
                        "inst_trust_net": ["投信買賣超股數"], "inst_dealer_net": ["自營商買賣超股數"],
                        "inst_total_net": ["三大法人買賣超股數"],
                    }
                    for target, names in candidates.items():
                        hit = [i for i, f in enumerate(fields) if def_key(f) in {def_key(n) for n in names}]
                        if len(hit) != 1:
                            raise ValueError(f"Missing institutional field {target}")
                        ix[target] = hit[0]
                row.update({target: def_number(raw[i]) for target, i in ix.items()})
                if market == "TWSE":
                    row["inst_foreign_net"] = row["inst_foreign_ex_dealer_net"] + row["inst_foreign_dealer_net"]
            elif kind == "margin":
                if market == "TPEX" and len(fields) == 20 and fields[6] == "資餘額" and fields[14] == "券餘額":
                    row.update(margin_balance=def_number(raw[6])*1000, short_balance=def_number(raw[14])*1000)
                elif market == "TWSE" and len(fields) == 16 and fields[6] == "今日餘額" and fields[12] == "今日餘額":
                    row.update(margin_balance=def_number(raw[6])*1000, short_balance=def_number(raw[12])*1000)
                else:
                    raise ValueError("Margin schema/unit changed")
            elif kind == "shares":
                record = dict(zip(fields, raw))
                row["shares_outstanding"] = def_number(def_value(record, ALIASES["shares_outstanding"]))
            elif kind == "daytrade":
                record = dict(zip(fields, raw))
                for target in ("day_trade_volume", "day_trade_buy_value", "day_trade_sell_value"):
                    row[target] = def_number(def_value(record, ALIASES[target]))
                if all(pd.isna(row[k]) for k in ("day_trade_volume", "day_trade_buy_value", "day_trade_sell_value")):
                    raise ValueError("Day-trading schema lacks per-stock volume/value")
            else:
                raise ValueError(kind)
            row[kind + "_source"] = source
            rows.append(row)
    frame = pd.DataFrame(rows)
    if not frame.empty:
        def_assert_unique(frame, ["date", "ticker"])
    return frame


def def_merge_optional(base, extra):
    if extra is None or extra.empty:
        return base
    def_assert_unique(extra, ["date", "ticker"])
    out = base.merge(extra, on=["date", "ticker"], how="left", suffixes=("", "__new"), validate="one_to_one")
    for c in extra.columns:
        if c + "__new" in out:
            out[c] = out[c + "__new"].combine_first(out[c])
            out = out.drop(columns=c + "__new")
    return out


def def_adjust_prices(frame, yahoo, as_of=None):
    out = frame.copy()
    for col in ("yf_close", "yf_adj_close", "yf_volume"):
        if col in out:
            out = out.drop(columns=col)
    out = def_merge_optional(out, yahoo)
    for col in ("yf_close", "yf_adj_close", "yf_volume"):
        if col not in out:
            out[col] = float("nan")
    diff = (out.close - out.yf_close).abs()
    tolerance = DEFAULT_CLOSE_ABS_TOLERANCE + DEFAULT_CLOSE_REL_TOLERANCE * out.close.abs()
    available = (out.yf_close > 0) & (out.close > 0)
    out["close_check"] = "MISSING"
    out.loc[available, "close_check"] = "MISMATCH"
    out.loc[available & (diff <= tolerance), "close_check"] = "MATCH"
    factor = (out.yf_adj_close / out.yf_close.where(out.yf_close > 0)).replace([float('inf'),float('-inf')],float('nan'))
    valid = out.close_check.eq("MATCH") & (factor > 0) & factor.notna()
    out["adjustment_factor"] = factor.where(valid)
    for col in ("open", "low", "high", "close"):
        out["adj_" + col] = out[col] * out.adjustment_factor
    out["adjustment_status"] = "UNAVAILABLE"
    out.loc[out.close_check.eq("MISMATCH"), "adjustment_status"] = "CLOSE_MISMATCH"
    out.loc[valid, "adjustment_status"] = "ADJUSTED"
    out["adj_as_of"] = as_of or def_now()
    return out


def def_deduct_daytrade(frame, method=DEFAULT_TURNOVER_DAYTRADE_METHOD):
    out = frame.copy()
    for col in ("day_trade_volume", "day_trade_buy_value", "day_trade_sell_value"):
        if col not in out:
            out[col] = float("nan")
    buy, sell = out.day_trade_buy_value, out.day_trade_sell_value
    values = {"average": (buy + sell)/2, "sum": buy + sell, "buy": buy, "sell": sell}
    if method not in values:
        raise ValueError(f"Unknown day-trading convention: {method}")
    out["day_trade_value"] = values[method]
    out["daytrade_value_method"] = method
    out["volume_ex_daytrade"] = out.volume - out.day_trade_volume
    out["turnover_ex_daytrade"] = out.turnover - out.day_trade_value
    missing = out[["day_trade_volume", "day_trade_value"]].isna().any(axis=1)
    invalid = ((out.day_trade_volume < 0) | (out.day_trade_value < 0) |
               (out.volume_ex_daytrade < 0) | (out.turnover_ex_daytrade < 0))
    out["daytrade_status"] = "AVAILABLE"
    out.loc[missing, "daytrade_status"] = "MISSING"
    out.loc[invalid, "daytrade_status"] = "INVALID"
    out.loc[invalid, ["volume_ex_daytrade", "turnover_ex_daytrade"]] = float("nan")
    return out


def def_daily_quality(frame):
    out = frame.copy()
    needed = ["inst_foreign_net", "inst_trust_net", "inst_dealer_net", "inst_total_net"]
    for col in needed:
        if col not in out:
            out[col] = float("nan")
    valid = out[needed].notna().all(axis=1)
    diff = (out[needed[:3]].sum(axis=1) - out.inst_total_net).abs()
    out["inst_check"] = "MISSING"
    out.loc[valid, "inst_check"] = "MISMATCH"
    out.loc[valid & (diff < 0.5), "inst_check"] = "MATCH"
    out["market_cap"] = out.close * out.shares_outstanding
    if "shares_source" in out:
        out["market_cap_source"] = out.shares_source.combine_first(out.get("market_cap_source",pd.Series(None,index=out.index,dtype=object)))
    out["quality"] = "PARTIAL"
    good = (out.adjustment_status.eq("ADJUSTED") & out.daytrade_status.eq("AVAILABLE") &
            out.inst_check.eq("MATCH") & out.market_cap.notna())
    good &= out[["open","low","high","close","volume","turnover"]].notna().all(axis=1)
    good &= (out.volume>=0) & (out.turnover>=0)
    out.loc[good, "quality"] = "COMPLETE"
    out.loc[out.close_check.eq("MISMATCH") | out.daytrade_status.eq("INVALID") | out.inst_check.eq("MISMATCH"), "quality"] = "REVIEW"
    for col in DAILY_COLUMNS:
        if col not in out:
            out[col] = None
    return out[DAILY_COLUMNS + [c for c in out if c not in DAILY_COLUMNS]]

# =============================================================================
# 3 · MOPS statements: current quarter / YTD / annual and raw monthly revenue
# =============================================================================
def def_financial_header(label, statement):
    text = re.sub(r"\s+", "", label)
    year_match = re.search(r"(\d{2,4})年", text)
    if not year_match:
        return None
    year = int(year_match[1]); year += 1911 if year < 1911 else 0
    if statement == "BALANCE_SHEET":
        m = re.fullmatch(r"\d{2,4}年(\d{1,2})月(\d{1,2})日", text)
        if not m:
            return None
        end = pd.Timestamp(year, int(m[1]), int(m[2]))
        return year, (end.month-1)//3+1, "POINT", pd.NaT, end
    if "年度" in text:
        return year, 4, "YTD", pd.Timestamp(year, 1, 1), pd.Timestamp(year, 12, 31)
    q = re.fullmatch(r"\d{2,4}年第([1-4])季", text)
    if q:
        quarter = int(q[1]); end = pd.Period(f"{year}Q{quarter}").end_time.normalize()
        return year, quarter, "QUARTER", pd.Timestamp(year, 3*(quarter-1)+1, 1), end
    dates = re.findall(r"(?:(\d{2,4})年)?(\d{1,2})月(\d{1,2})日", text)
    if len(dates) == 2:
        start, end = [pd.Timestamp((int(y)+(1911 if int(y)<1911 else 0)) if y else year, int(m), int(d)) for y,m,d in dates]
        if start.year != end.year or start > end:
            return None
        basis = "YTD" if (start.month, start.day) == (1, 1) else "QUARTER"
        return end.year, (end.month-1)//3+1, basis, start, end
    return None


def def_parse_statement(text, identity, statement, source, requested_quarter):
    from lxml import html
    doc = html.fromstring(text)
    all_text = " ".join(doc.itertext())
    headings = " ".join("".join(x.itertext()) for x in doc.xpath("//h1|//h2|//h3|//h4"))
    scope = "CONSOLIDATED" if "合併" in headings else ("SEPARATE" if "個別" in headings or "個體" in headings else DEFAULT_FINANCIAL_SCOPE)
    expected_year, expected_q = int(requested_quarter[:4]), int(requested_quarter[-1])
    marker = re.search(r"民國\s*(\d+)\s*年第\s*([1-4])\s*季", all_text)
    if not marker or (int(marker[1])+1911, int(marker[2])) != (expected_year, expected_q):
        raise ValueError(f"Financial report period mismatch or blocked response: {requested_quarter}")
    rows = []
    for table in doc.xpath("//table"):
        trs = table.xpath("./tr|./tbody/tr")
        headers = None; header_index = None
        for i, tr in enumerate(trs):
            cells = tr.xpath("./td|./th")
            if cells and re.sub(r"\s+", "", "".join(cells[0].itertext())) == "會計項目":
                headers = []
                for c in cells:
                    headers.extend(["".join(c.itertext()).strip()] * int(c.get("colspan", "1")))
                header_index = i
                break
        if headers is None:
            continue
        units = " ".join(table.itertext())
        if not re.search(r"單位\s*[：:]\s*新台幣[仟千]元", units):
            raise ValueError("Unknown financial currency/unit; refused to assume TWD thousands")
        for tr in trs[header_index+1:]:
            cells = tr.xpath("./td|./th")
            values = ["".join(c.itertext()).strip() for c in cells]
            if len(values) != len(headers) or len(values) < 2:
                continue
            account = re.sub(r"\s+", " ", values[0]).strip()
            if not account:
                continue
            for idx in range(1, len(values)):
                # IS/BS have amount/percentage pairs; CF has amount-only columns.
                if idx > 1 and headers[idx] == headers[idx-1]:
                    continue
                period = def_financial_header(headers[idx], statement)
                value = def_number(values[idx])
                if period is None or pd.isna(value):
                    continue
                year,q,basis,start,end = period
                per_share = "每股" in account
                unit = "TWD_PER_SHARE" if per_share else "TWD_THOUSAND"
                rows.append({**identity, "date": end, "financial_statement": statement,
                             "account": account, "unit": unit, "value": float(value), "source": source,
                             "basis": basis, "fiscal_year": year, "quarter": q, "period_start": start,
                             "report_scope": scope, "is_derived": False, "derivation": None,
                             "source_report_period": requested_quarter, "source_date": pd.NaT,
                             "fetched_at": def_now(), "currency": "TWD"})
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("No supported financial table found; source HTML retained")
    def_assert_unique(frame, DATASET_KEYS["tw_financial"])
    return frame[FINANCIAL_COLUMNS + [c for c in frame if c not in FINANCIAL_COLUMNS]]


def def_derive_financial_periods(frame):
    if frame.empty:
        return frame
    out = frame.copy(); added = []
    group_keys = ["ticker", "financial_statement", "account", "unit", "report_scope", "fiscal_year"]
    for _, group in frame.groupby(group_keys, dropna=False):
        # Comparison values can come from different report URLs. Only an unambiguous
        # value per period may be used for differences; revised alternatives stay separate.
        ytd = group.loc[group.basis.eq("YTD")]
        for _, row in ytd.iterrows():
            q = int(row.quarter)
            if q == 4:
                annual = row.to_dict(); annual.update(basis="ANNUAL", is_derived=True, derivation="Q4 YTD is full fiscal year")
                added.append(annual)
            if row.unit != "TWD_THOUSAND" or row.financial_statement == "BALANCE_SHEET":
                continue
            if row.financial_statement == "CASH_FLOW" and re.search(NON_ADDITIVE_CASHFLOW_ACCOUNTS,str(row.account)):
                continue  # cash balances are stocks, even when displayed on a YTD cash-flow statement
            if group.loc[group.basis.eq("QUARTER") & group.quarter.eq(q)].shape[0]:
                continue
            if q == 1:
                value = row.value
            else:
                prev = ytd.loc[ytd.quarter.eq(q-1)]
                vals = prev.value.dropna().unique()
                if len(vals) != 1 or row.value not in ytd.loc[ytd.quarter.eq(q), "value"].unique() or len(ytd.loc[ytd.quarter.eq(q), "value"].unique()) != 1:
                    continue
                value = row.value - vals[0]
            derived = row.to_dict()
            derived.update(basis="QUARTER", value=value, is_derived=True,
                           period_start=pd.Timestamp(int(row.fiscal_year), 3*(q-1)+1, 1),
                           derivation="Q1 YTD" if q == 1 else "current YTD minus prior-quarter YTD")
            if q > 1:
                derived["source"] = row.source + " | " + " | ".join(sorted(prev.source.unique()))
            added.append(derived)
    if added:
        out = pd.concat([out, pd.DataFrame(added)], ignore_index=True)
        out = out.drop_duplicates(DATASET_KEYS["tw_financial"])
    def_assert_unique(out, DATASET_KEYS["tw_financial"])
    return out


def def_normalize_revenue(payload, market, source):
    rows = []
    for record in payload:
        code = str(def_value(record, ALIASES["ticker"], "")).strip()
        if not re.fullmatch(STOCK_REGEX, code):
            continue
        raw = str(def_value(record, ["資料年月", "YearMonth", "DataYearMonth"], "")).strip()
        if not re.fullmatch(r"\d{5,6}", raw):
            raise ValueError(f"Unrecognized revenue period: {raw}")
        year, month = int(raw[:-2]), int(raw[-2:]); year += 1911 if year<1911 else 0
        ident = def_identity(code, market, str(def_value(record, ALIASES["name"], "")))
        for account, aliases in {
            "MONTHLY_REVENUE": ["營業收入-當月營收", "Revenue"],
            "YTD_REVENUE": ["累計營業收入-當月累計營收", "AccumulativeRevenue"],
        }.items():
            value = def_number(def_value(record, aliases))
            if pd.notna(value):
                rows.append({**ident, "date": pd.Timestamp(year,month,1), "account": account,
                             "unit": "TWD_THOUSAND", "value": value, "source": source,
                             "source_date": def_date(def_value(record, ["出表日期", "Date"])),
                             "fetched_at": def_now(), "currency": "TWD"})
    out = pd.DataFrame(rows)
    if out.empty:
        raise ValueError("No supported monthly-revenue rows")
    def_assert_unique(out, DATASET_KEYS["tw_monthly_revenue"])
    return out

# =============================================================================
# 4 · Atomic disk storage. Parquet owns data; DuckDB owns views only.
# =============================================================================
def def_atomic_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(temp, path)


def def_log(root, event):
    path = Path(root)/"logs"/"fetch_ledger.jsonl"; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at":def_now(), **event}, ensure_ascii=False, default=str)+"\n")


def def_load_dataset(root, dataset, tickers=None, columns=None):
    files = sorted((Path(root)/"parquet"/dataset).glob("ticker=*/year=*/data.parquet"))
    if tickers is not None:
        wanted = set(tickers)
        files = [p for p in files if p.parent.parent.name[7:] in wanted]
    return pd.concat([pd.read_parquet(p,columns=columns) for p in files], ignore_index=True) if files else pd.DataFrame()


def def_store(root, dataset, frame, revision_reason="source refresh", replace_derived=False):
    if frame.empty:
        return 0
    root = Path(root); keys = DATASET_KEYS[dataset]
    frame = frame.copy(); frame["date"] = pd.to_datetime(frame.date).dt.normalize()
    def_assert_unique(frame, keys)
    count = 0
    for (ticker,year), part in frame.groupby(["ticker", frame.date.dt.year], sort=True):
        directory = root/"parquet"/dataset/f"ticker={ticker}"/f"year={year}"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory/"data.parquet"
        if path.exists():
            old = pd.read_parquet(path); def_assert_unique(old, keys)
            if replace_derived and "is_derived" in old:
                old = old.loc[~old.is_derived.fillna(False)].copy()
            # Nulls from failed side-sources may not erase earlier successful raw data.
            new_i, old_i = part.set_index(keys), old.set_index(keys)
            common = new_i.index.intersection(old_i.index)
            columns = new_i.columns.intersection(old_i.columns)
            revised = []
            for k in common:
                for c in columns:
                    if c in ("fetched_at", "adj_as_of", "quality", "source_date"):
                        continue
                    before, after = old_i.at[k,c], new_i.at[k,c]
                    if pd.notna(before) and pd.notna(after) and str(before)!=str(after):
                        revised.append({"key":str(k),"column":c,"old":str(before),"new":str(after)})
            if revised:
                archive = root/"revisions"/dataset/f"{ticker}_{year}_{time.time_ns()}.parquet"
                archive.parent.mkdir(parents=True,exist_ok=True); old.to_parquet(archive,index=False,compression="zstd")
                def_log(root,{"event":"REVISION","dataset":dataset,"reason":revision_reason,"changes":revised,"archive":str(archive)})
            combined = new_i.combine_first(old_i)
            # Explicit recomputed nulls must invalidate a previous adjustment, rather
            # than silently retaining prices based on a now-mismatched Yahoo close.
            derived_cols = {"adj_open","adj_low","adj_high","adj_close","adjustment_factor",
                            "volume_ex_daytrade","turnover_ex_daytrade","day_trade_value",
                            "yf_close","yf_adj_close","yf_volume"}
            if "adjustment_status" in new_i and not new_i.adjustment_status.eq("PENDING").all():
                for c in derived_cols.intersection(new_i.columns):
                    combined.loc[new_i.index,c] = new_i[c]
            part = combined.reset_index()
        part = part.sort_values(keys).reset_index(drop=True)
        def_assert_unique(part, keys)
        tmp = directory/"data.tmp.parquet"; part.to_parquet(tmp,index=False,compression="zstd")
        # Verify persisted primary keys before replacing the last valid partition.
        check = pd.read_parquet(tmp); def_assert_unique(check,keys)
        os.replace(tmp,path)
        csv = part.copy()
        for c in csv:
            if pd.api.types.is_datetime64_any_dtype(csv[c]):
                csv[c] = csv[c].dt.strftime("%Y/%m/%d")
        csv = csv.rename(columns=CSV_HEADERS)
        csv_tmp = directory/"data.csv.tmp"; csv.to_csv(csv_tmp,index=False,encoding=CSV_ENCODING)
        os.replace(csv_tmp,directory/"data.csv")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        def_atomic_json(directory/"manifest.json",{"dataset":dataset,"ticker":ticker,"year":int(year),"rows":len(part),"sha256":digest,"updated_at":def_now(),"csv_encoding":CSV_ENCODING})
        count += len(part)
    return count


def def_catalog(root):
    import duckdb
    root = Path(root); (root/"temp").mkdir(parents=True,exist_ok=True)
    for db, datasets in DB_TABLES.items():
        with duckdb.connect(str(root/(db+".duckdb"))) as conn:
            conn.execute("SET memory_limit = ?",[DEFAULT_MEMORY_LIMIT])
            conn.execute("SET temp_directory = ?",[str(root/"temp")])
            for table in datasets:
                if not list((root/"parquet"/table).glob("ticker=*/year=*/data.parquet")):
                    continue
                glob = (root/"parquet"/table/"ticker=*"/"year=*"/"data.parquet").resolve().as_posix().replace("'","''")
                conn.execute(f"CREATE OR REPLACE VIEW {table} AS SELECT * FROM read_parquet('{glob}', union_by_name=true, hive_partitioning=false)")


@contextmanager
def def_run_lock(root):
    path = Path(root)/"RUNNING.lock"; path.parent.mkdir(parents=True,exist_ok=True)
    try:
        fd = os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:
        raise RuntimeError(f"Another writer may be active. Inspect {path}; remove only after confirming the old process has stopped.")
    try:
        os.write(fd,json.dumps({"pid":os.getpid(),"at":def_now()}).encode()); os.close(fd)
        yield
    finally:
        path.unlink(missing_ok=True)

# =============================================================================
# 5 · HTTP cache, retry, provenance and optional existing VIA bridges
# =============================================================================
def def_via_bridges(via_root):
    status = {"accel":"NOT_AVAILABLE", "network":"STANDALONE", "module":None}
    root = Path(via_root)
    support = root/"supportive modules"
    if (support/"VIA_SuperAccel_Module.py").is_file():
        # [VIA:ACCEL-BRIDGE] Use the existing dispatcher; do not pin Celeritas versions.
        sys.path.insert(0,str(support))
        try:
            import VIA_SuperAccel_Module
            status["accel"] = "AVAILABLE"
        except Exception as exc:
            status["accel"] = "ERROR:"+str(exc)
    lock = support/"registry"/"VIA_ToolVersion_Lock_v0100.json"
    if lock.is_file():
        spec = json.loads(lock.read_text(encoding="utf-8-sig"))
        entry = spec.get("net",spec.get("network",{}))
        if isinstance(entry,dict) and entry.get("path"):
            path = Path(entry["path"]); path = path if path.is_absolute() else root/path
            if not path.is_file():
                raise FileNotFoundError(f"Locked VIA network module missing: {path}")
            if entry.get("sha256") and hashlib.sha256(path.read_bytes()).hexdigest()!=entry["sha256"]:
                raise ValueError("Locked VIA network module hash mismatch")
            # [VIA:NET-BRIDGE] Explicit denials are never retried through another transport.
            module_spec = importlib.util.spec_from_file_location("vdf_net_bridge",path)
            module = importlib.util.module_from_spec(module_spec); sys.modules[module_spec.name]=module; module_spec.loader.exec_module(module)
            if not hasattr(module,"curl_bytes"):
                raise RuntimeError("Locked network module has no curl_bytes API")
            status.update(network="LOCKED_VIA",module=module)
    return status


class FetchClient:
    def __init__(self,root,offline=False,bridge=None):
        self.root=Path(root); self.offline=offline; self.bridge=bridge
        self.last=0.0; self.calls=0; self.bytes=0

    def get(self,url,params=None,fresh=False):
        if params:
            url += ("&" if "?" in url else "?")+urllib.parse.urlencode(params)
        key=hashlib.sha256(url.encode()).hexdigest(); path=self.root/"raw"/(key+".bin")
        meta=path.with_suffix(".json")
        usable=path.exists() and (not fresh or time.time()-path.stat().st_mtime<DEFAULT_CACHE_HOURS*3600)
        if usable:
            return path.read_bytes(),url
        if self.offline:
            raise FileNotFoundError(f"Offline cache missing/expired: {url}")
        error=None
        for attempt in range(DEFAULT_RETRIES):
            time.sleep(max(0,DEFAULT_INTERVAL-(time.monotonic()-self.last)))
            self.last=time.monotonic(); self.calls+=1
            try:
                if self.bridge:
                    r=self.bridge.curl_bytes(url,timeout=DEFAULT_TIMEOUT,follow=True,headers={"User-Agent":"Mozilla/5.0 (VDF data fetch)"})
                    if r.get("state")=="DENY":
                        raise PermissionError("Existing VIA network bridge denied this request")
                    if r.get("state")!="OK":
                        raise RuntimeError(f"VIA transport failed: {r.get('state')}")
                    data=r.get("data",b"")
                else:
                    request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (VDF data fetch)","Accept":"application/json,text/html,*/*"})
                    with urllib.request.urlopen(request,timeout=DEFAULT_TIMEOUT) as response:
                        data=response.read()
                if not data:
                    raise ValueError("Empty HTTP response")
                self.bytes+=len(data); path.parent.mkdir(parents=True,exist_ok=True)
                temp=path.with_suffix(".tmp");temp.write_bytes(data);os.replace(temp,path)
                def_atomic_json(meta,{"url":url,"fetched_at":def_now(),"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)})
                def_log(self.root,{"event":"FETCH","url":url,"bytes":len(data),"attempt":attempt+1})
                return data,url
            except PermissionError:
                raise
            except Exception as exc:
                error=exc
                def_log(self.root,{"event":"FETCH_ERROR","url":url,"attempt":attempt+1,"error":str(exc)})
                if attempt+1<DEFAULT_RETRIES:
                    time.sleep(min(2**attempt,5))
        raise RuntimeError(f"Fetch failed: {url}: {error}") from error

    def json(self,url,params=None,fresh=False):
        data,source=self.get(url,params,fresh)
        try:
            return json.loads(data.decode("utf-8-sig")),source
        except (ValueError,UnicodeDecodeError) as exc:
            raise ValueError(f"Expected JSON, received another format: {source}") from exc


def def_yahoo(frame,client):
    if frame.empty:
        return pd.DataFrame()
    import yfinance as yf
    frames=[]; symbols=sorted(frame.yfinance_ticker.unique())
    start=frame.date.min();end=frame.date.max()+pd.Timedelta(days=1)
    for offset in range(0,len(symbols),DEFAULT_BATCH_SIZE):
        batch=symbols[offset:offset+DEFAULT_BATCH_SIZE]
        query={"symbols":batch,"start":str(start.date()),"end":str(end.date()),"auto_adjust":False,"back_adjust":False,"version":VERSION}
        key=hashlib.sha256(json.dumps(query,sort_keys=True).encode()).hexdigest()
        path=client.root/"yahoo_cache"/(key+".parquet")
        fresh=path.exists() and time.time()-path.stat().st_mtime<DEFAULT_CACHE_HOURS*3600
        if fresh:
            frames.append(pd.read_parquet(path));continue
        if client.offline:
            raise FileNotFoundError("Offline Yahoo cache missing/expired")
        # yfinance uses its own curl_cffi transport. Its access is recorded separately;
        # an existing VIA bridge is not claimed to cover this library's internal HTTP.
        downloaded=yf.download(batch,start=start.strftime("%Y-%m-%d"),end=end.strftime("%Y-%m-%d"),
                               auto_adjust=False,back_adjust=False,actions=True,progress=False,
                               threads=False,group_by="ticker",timeout=DEFAULT_TIMEOUT)
        rows=[]
        for symbol in batch:
            if isinstance(downloaded.columns,pd.MultiIndex):
                if symbol in downloaded.columns.get_level_values(0):
                    data=downloaded[symbol]
                elif symbol in downloaded.columns.get_level_values(1):
                    data=downloaded.xs(symbol,axis=1,level=1)
                else:
                    continue
            else:
                data=downloaded
            if "Close" not in data or "Adj Close" not in data:
                continue
            for index,row in data.iterrows():
                if pd.isna(row.get("Close")):
                    continue
                day=pd.Timestamp(index)
                if day.tzinfo is not None:
                    day=day.tz_convert("Asia/Taipei").tz_localize(None)
                rows.append({"date":day.normalize(),"ticker":symbol.split('.')[0],"yf_close":row.Close,
                             "yf_adj_close":row["Adj Close"],"yf_volume":row.get("Volume")})
        output=pd.DataFrame(rows)
        if not output.empty:
            def_assert_unique(output,["date","ticker"]);path.parent.mkdir(parents=True,exist_ok=True)
            tmp=path.with_suffix(".tmp.parquet");output.to_parquet(tmp,index=False);os.replace(tmp,path)
            frames.append(output)
        def_log(client.root,{"event":"YFINANCE","symbols":batch,"start":query["start"],"end":query["end"],"rows":len(output),"returned_symbols":len(output.ticker.unique()) if not output.empty else 0})
        time.sleep(DEFAULT_INTERVAL)
    return pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()

# =============================================================================
# 6 · Retrieval orchestration and CLI
# =============================================================================
def def_select_universe(client,ticker_input):
    frames=[]
    for market,url in [("TWSE",TWSE_API+"/opendata/t187ap03_L"),("TPEX",TPEX_API+"/mopsfin_t187ap03_O")]:
        payload,source=client.json(url,fresh=True)
        frames.append(def_normalize_roster(payload,market,source))
    universe=pd.concat(frames,ignore_index=True);def_assert_unique(universe,["ticker"])
    if ticker_input.upper()!="ALL":
        p=Path(ticker_input)
        tokens=pd.read_csv(p,dtype=str,encoding=CSV_ENCODING).iloc[:,0].tolist() if p.is_file() else re.split(r"[,;\s]+",ticker_input)
        codes=[]
        for token in tokens:
            token=str(token).strip()
            if not re.fullmatch(STOCK_REGEX,token):
                raise ValueError(f"Input must be a Taiwan four-digit stock ticker: {token!r}")
            codes.append(token)
        missing=set(codes)-set(universe.ticker)
        if missing:
            raise ValueError(f"Tickers absent from current official roster: {sorted(missing)}")
        universe=universe.loc[universe.ticker.isin(codes)].copy()
    return universe


def def_endpoints(market,day,kind):
    compact=day.strftime("%Y%m%d"); slash=day.strftime("%Y/%m/%d")
    mapping={
        ("TWSE","quotes"):(TWSE_WEB+"/afterTrading/MI_INDEX",{"date":compact,"type":"ALLBUT0999","response":"json"}),
        ("TPEX","quotes"):(TPEX_WEB+"/afterTrading/dailyQuotes",{"date":slash,"id":"","response":"json"}),
        ("TWSE","institutional"):(TWSE_WEB+"/fund/T86",{"date":compact,"selectType":"ALL","response":"json"}),
        ("TPEX","institutional"):(TPEX_WEB+"/insti/dailyTrade",{"type":"Daily","sect":"EW","date":slash,"response":"json"}),
        ("TWSE","margin"):(TWSE_WEB+"/marginTrading/MI_MARGN",{"date":compact,"selectType":"ALL","response":"json"}),
        ("TPEX","margin"):(TPEX_WEB+"/margin/balance",{"date":slash,"response":"json"}),
        ("TWSE","daytrade"):(TWSE_WEB+"/dayTrading/TWTB4U",{"date":compact,"selectType":"All","response":"json"}),
        ("TPEX","daytrade"):(TPEX_WEB+"/intraday/stat",{"date":slash,"type":"Daily","response":"json"}),
        ("TWSE","shares"):(TWSE_WEB+"/fund/MI_QFIIS",{"date":compact,"selectType":"ALLBUT0999","response":"json"}),
    }
    return mapping[(market,kind)]


def def_collect_daily(client,universe,start,end,method,issues):
    old=def_load_dataset(client.root,"tw_equity_daily",universe.ticker,["date","ticker","quality"])
    for market,group in universe.groupby("market"):
        wanted=set(group.ticker)
        if start is None:
            if market=="TWSE":
                payload,source=client.json(TWSE_API+"/exchangeReport/STOCK_DAY_ALL",fresh=True)
            else:
                # Website daily quotes includes the current snapshot date and issued shares.
                payload,source=client.json(TPEX_WEB+"/afterTrading/dailyQuotes",{"response":"json"},fresh=True)
            snapshot=def_normalize_quotes(payload,market,source)
            snapshot=snapshot.loc[snapshot.ticker.isin(wanted)]
            if snapshot.empty:
                raise ValueError(f"No official snapshot for selected market {market}")
            days=sorted(snapshot.date.unique())
            if not old.empty:
                recent=old.loc[old.ticker.isin(wanted)&(old.date>=end-pd.Timedelta(days=DEFAULT_REFRESH_DAYS)),"date"]
                days=sorted(set(days)|set(recent))
        else:
            snapshot=pd.DataFrame()
            days=list(pd.date_range(start,end,freq="D"))
        for n,day in enumerate(days):
            day=pd.Timestamp(day)
            if day>end:
                continue
            existing=old.loc[old.date.eq(day)&old.ticker.isin(wanted)] if not old.empty else pd.DataFrame()
            complete=not existing.empty and set(existing.ticker)==wanted and existing.quality.eq("COMPLETE").all()
            if complete and day<end-pd.Timedelta(days=DEFAULT_REFRESH_DAYS):
                continue
            print(f"[{market}] {day.date()} {n+1}/{len(days)}",flush=True)
            try:
                if not snapshot.empty and day in snapshot.date.values:
                    quote=snapshot.loc[snapshot.date.eq(day)].copy()
                else:
                    url,params=def_endpoints(market,day,"quotes")
                    payload,source=client.json(url,params,fresh=day>=end-pd.Timedelta(days=DEFAULT_REFRESH_DAYS))
                    if isinstance(payload,dict) and re.search(OFFICIAL_NO_SESSION_MESSAGE,str(payload.get('stat',''))):
                        def_log(client.root,{"event":"OFFICIAL_NO_DATA","market":market,"date":day,"source":source,"message":payload['stat']})
                        continue
                    quote=def_normalize_quotes(payload,market,source,day)
                    if quote.empty:
                        def_log(client.root,{"event":"NO_SESSION_DATA","market":market,"date":day});continue
                quote=quote.loc[quote.ticker.isin(wanted)].copy()
                if start is None and wanted-set(quote.ticker):
                    issues.append({"dataset":"daily","market":market,"date":str(day.date()),"stage":"universe_coverage","missing_tickers":sorted(wanted-set(quote.ticker)),"note":"No official quote returned; do not synthesize suspended/new-listing history"})
                for kind in ("shares","institutional","margin","daytrade"):
                    if kind=="shares" and market=="TPEX":
                        continue
                    try:
                        url,params=def_endpoints(market,day,kind)
                        payload,source=client.json(url,params,fresh=day>=end-pd.Timedelta(days=DEFAULT_REFRESH_DAYS))
                        extra=def_normalize_chips(payload,market,kind,day,source)
                        if extra.empty:
                            raise ValueError("No per-stock records returned")
                        quote=def_merge_optional(quote,extra)
                    except PermissionError:
                        raise
                    except Exception as exc:
                        issues.append({"dataset":"daily","market":market,"date":str(day.date()),"stage":kind,"error":str(exc)})
                # Persist official data before Yahoo to support interruption recovery.
                for c in ("close_check","adjustment_status","daytrade_status","quality"):
                    quote[c]="PENDING"
                def_store(client.root,"tw_equity_daily",quote)
            except PermissionError:
                raise
            except Exception as exc:
                issues.append({"dataset":"daily","market":market,"date":str(day.date()),"stage":"quotes","error":str(exc)})
    # Recompute adjustments across all locally stored history of selected tickers.
    # A dividend/split may revise every historical factor, not just recent days.
    row_count=0;all_dates=set();quality_counts={};symbols=list(universe.ticker)
    for offset in range(0,len(symbols),DEFAULT_BATCH_SIZE):
        full=def_load_dataset(client.root,"tw_equity_daily",symbols[offset:offset+DEFAULT_BATCH_SIZE])
        if full.empty:
            continue
        try:
            yahoo=def_yahoo(full,client)
        except Exception as exc:
            issues.append({"dataset":"daily","stage":"yfinance","error":str(exc)});yahoo=pd.DataFrame()
        full=def_daily_quality(def_deduct_daytrade(def_adjust_prices(full,yahoo),method))
        def_store(client.root,"tw_equity_daily",full,"official correction / latest Yahoo adjustment vintage")
        row_count+=len(full);all_dates.update(full.date.dt.strftime("%Y-%m-%d").unique())
        for k,v in full.quality.value_counts().items():
            quality_counts[k]=quality_counts.get(k,0)+int(v)
    if not row_count:
        raise ValueError("No official equity data available")
    return {"rows":row_count,"dates":sorted(all_dates),"quality":quality_counts}


def def_collect_indices(client,start,end,issues):
    rows=[]
    months=pd.period_range(start or end.replace(day=1),end,freq="M")
    for market,code in [("TWSE","TAIEX"),("TPEX","TPEX")]:
        for month in months:
            try:
                day=month.start_time
                if market=="TWSE":
                    payload,source=client.json(TWSE_WEB+"/TAIEX/MI_5MINS_HIST",{"date":day.strftime("%Y%m%d"),"response":"json"},fresh=month==end.to_period("M"))
                else:
                    # Current-month official OpenAPI; historical uses the official month endpoint.
                    payload,source=client.json(TPEX_WEB+"/indexInfo/inx",{"date":day.strftime("%Y/%m/%d"),"response":"json"},fresh=month==end.to_period("M"))
                for table in def_tables(payload):
                    for record in def_records(table):
                        dv=def_value(record,ALIASES["date"])
                        if not dv:
                            continue
                        date=def_date(dv)
                        if not ((start is None or date>=start) and date<=end):
                            continue
                        row={**INDEX_IDENTITIES[code],"index_code":code,"index_name":INDEX_IDENTITIES[code]["name"],"date":date,"source":source,"fetched_at":def_now(),"currency":"TWD","price_unit":"INDEX_POINTS","volume_unit":"SHARES","turnover_unit":"TWD"}
                        for col in ("open","low","high","close","volume","turnover"):
                            row[col]=def_number(def_value(record,ALIASES[col]))
                        if pd.notna(row["close"]):
                            rows.append(row)
            except Exception as exc:
                issues.append({"dataset":"indices","market":market,"month":str(month),"error":str(exc)})
    out=pd.DataFrame(rows)
    if not out.empty:
        def_assert_unique(out,["date","ticker"])
        for index in out.index:
            day=out.at[index,'date'];market=out.at[index,'market']
            try:
                if market=='TWSE':
                    payload,total_source=client.json(TWSE_WEB+'/afterTrading/FMTQIK',{'date':day.replace(day=1).strftime('%Y%m%d'),'response':'json'},fresh=day.to_period('M')==end.to_period('M'))
                    found=[]
                    for table in def_tables(payload):
                        found.extend(r for r in def_records(table) if def_date(def_value(r,ALIASES['date']))==day)
                    if len(found)!=1:
                        raise ValueError('Missing/ambiguous official market total')
                    out.at[index,'volume']=def_number(def_value(found[0],ALIASES['volume']))
                    out.at[index,'turnover']=def_number(def_value(found[0],ALIASES['turnover']))
                    scope='TWSE_FMTQIK_MARKET_TOTAL'
                else:
                    url,params=def_endpoints(market,day,'quotes');payload,total_source=client.json(url,params,fresh=day>=end-pd.Timedelta(days=DEFAULT_REFRESH_DAYS))
                    found=[t for t in def_tables(payload) if 'totalTradingShares' in t and 'totalTradingAmount' in t]
                    if len(found)!=1:
                        raise ValueError('Missing official TPEX daily-quote market total')
                    def_payload_date(payload,found[0],day)
                    out.at[index,'volume']=def_number(found[0]['totalTradingShares'])
                    out.at[index,'turnover']=def_number(found[0]['totalTradingAmount'])
                    scope='TPEX_DAILY_QUOTES_MARKET_TOTAL'
                out.at[index,'market_totals_source']=total_source
                out.at[index,'volume_scope']=scope
            except Exception as exc:
                issues.append({'dataset':'indices','market':market,'date':str(day.date()),'stage':'market_totals','error':str(exc)})
        def_store(client.root,"tw_index_daily",out)
    else:
        issues.append({'dataset':'indices','error':'No official index rows in the requested window'})
    return {"rows":len(out),"official_only":True,"volume_turnover":"official market activity; see volume_scope and market_totals_source; unavailable stays NULL"}


def def_collect_financial(client,universe,quarters,issues):
    if quarters=="latest":
        qset=[]
        for market in universe.market.unique():
            url=TWSE_API+"/opendata/t187ap06_L_ci" if market=="TWSE" else TPEX_API+"/mopsfin_t187ap06_O_ci"
            payload,_=client.json(url,fresh=True)
            valid=[]
            for r in payload:
                y=def_number(def_value(r,["年度","Year"]));q=def_number(def_value(r,["季別","Season"]))
                if pd.notna(y) and pd.notna(q):
                    valid.append((int(y)+(1911 if y<1911 else 0),int(q)))
            if valid:
                y,q=max(valid);qset.append(f"{y}Q{q}")
        wanted=sorted(set(qset))
    else:
        wanted=[q.strip().upper() for q in quarters.split(',')]
    if not wanted or any(not re.fullmatch(r"20\d{2}Q[1-4]",q) for q in wanted):
        raise ValueError("--quarters must be latest or comma-separated YYYYQ#")
    cashflow_dependencies = {f"{q[:4]}Q{int(q[-1])-1}" for q in wanted if int(q[-1])>1}
    fetch_quarters = sorted(set(wanted)|cashflow_dependencies)
    count=0
    for i,ident in enumerate(universe.to_dict('records')):
        identity={k:ident[k] for k in ("ticker","yfinance_ticker","bloomberg_ticker","name","market")}
        print(f"[FIN] {identity['ticker']} {i+1}/{len(universe)}",flush=True)
        for quarter in fetch_quarters:
            year,q=int(quarter[:4]),int(quarter[-1])
            for statement,endpoint in STATEMENTS.items():
                if quarter not in wanted and statement!="CASH_FLOW":
                    continue
                try:
                    params={"encodeURIComponent":1,"step":1,"firstin":1,"off":1,"queryName":"co_id","inpuType":"co_id","TYPEK":"all","isnew":"false","co_id":identity['ticker'],"year":year-1911,"season":q}
                    data,source=client.get(MOPS_WEB+"/ajax_t164sb"+endpoint,params,fresh=True)
                    frame=def_parse_statement(data.decode("utf-8-sig"),identity,statement,source,quarter)
                    def_store(client.root,"tw_financial",frame);count+=len(frame)
                except PermissionError:
                    raise
                except Exception as exc:
                    issues.append({"dataset":"financial","ticker":identity['ticker'],"quarter":quarter,"statement":statement,"error":str(exc)})
    # All history for a company is small; differences never combine sources with conflicting values.
    for ticker in universe.ticker:
        old=def_load_dataset(client.root,"tw_financial",[ticker])
        if not old.empty:
            raw=old.loc[~old.is_derived.fillna(False)]
            derived=def_derive_financial_periods(raw)
            def_store(client.root,"tw_financial",derived,"recompute financial period derivations",replace_derived=True)
    return {"fetched_rows":count,"quarters":wanted,"publication_date":"UNKNOWN: source page does not reliably provide actual announcement timestamp"}


def def_collect_revenue(client,universe,issues):
    count=0
    for market in universe.market.unique():
        try:
            url=TWSE_API+"/opendata/t187ap05_L" if market=="TWSE" else TPEX_API+"/mopsfin_t187ap05_O"
            payload,source=client.json(url,fresh=True);frame=def_normalize_revenue(payload,market,source)
            frame=frame.loc[frame.ticker.isin(universe.ticker)]
            count+=len(frame);def_store(client.root,"tw_monthly_revenue",frame)
        except Exception as exc:
            issues.append({"dataset":"revenue","market":market,"error":str(exc)})
    return {"rows":count,"mode":"latest official monthly snapshot; each run accumulates history; no YoY/seasonality analysis"}


def def_main(argv=None):
    parser=argparse.ArgumentParser(description="VDF TW raw data fetch only · official values + Yahoo adjustment · no analysis")
    parser.add_argument("--tickers",default=DEFAULT_TICKERS,help="ALL / 2330,6488 / CSV whose first column is ticker")
    parser.add_argument("--datasets",default=DEFAULT_DATASETS)
    parser.add_argument("--start",default=DEFAULT_START,help="YYYY-MM-DD: optional official daily/index historical backfill")
    parser.add_argument("--end",default=None)
    parser.add_argument("--quarters",default="latest",help="latest or 2025Q4,2026Q1,2026Q2")
    parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    parser.add_argument("--via-root",type=Path,default=DEFAULT_VIA_ROOT)
    parser.add_argument("--daytrade-value-method",choices=["average","sum","buy","sell"],default=DEFAULT_TURNOVER_DAYTRADE_METHOD)
    parser.add_argument("--offline",action="store_true")
    args=parser.parse_args(argv)
    datasets=[x.strip() for x in args.datasets.split(',')]
    if not set(datasets)<={"daily","indices","financial","revenue"}:
        parser.error("Unknown dataset")
    start=def_date(args.start) if args.start else None;end=def_date(args.end) if args.end else def_today()
    if start is not None and start>end:
        parser.error("start must not exceed end")
    args.output.mkdir(parents=True,exist_ok=True)
    issues=[];summary={"engine":ENGINE,"version":VERSION,"started_at":def_now(),"output":str(args.output.resolve()),"datasets":{}}
    with def_run_lock(args.output):
        bridge=def_via_bridges(args.via_root)
        summary["via_bridge"]={k:v for k,v in bridge.items() if k!="module"}
        client=FetchClient(args.output,args.offline,bridge['module'])
        universe=def_select_universe(client,args.tickers)
        def_store(args.output,"tw_universe",universe)
        for dataset in datasets:
            try:
                if dataset=="daily":
                    result=def_collect_daily(client,universe,start,end,args.daytrade_value_method,issues)
                elif dataset=="indices":
                    result=def_collect_indices(client,start,end,issues)
                elif dataset=="financial":
                    result=def_collect_financial(client,universe,args.quarters,issues)
                else:
                    result=def_collect_revenue(client,universe,issues)
                summary["datasets"][dataset]=result
            except PermissionError:
                raise
            except Exception as exc:
                issues.append({"dataset":dataset,"error":str(exc)})
            def_catalog(args.output)
            summary.update(issues=issues,updated_at=def_now())
            def_atomic_json(args.output/"status.json",summary)
        counts=summary["datasets"].get("daily",{}).get("quality",{})
        summary["status"]="PARTIAL" if issues or counts.get("PARTIAL",0) or counts.get("REVIEW",0) else "OK"
        summary.update(issues=issues,finished_at=def_now(),official_http_calls=client.calls,official_bytes=client.bytes)
        def_atomic_json(args.output/"status.json",summary)
        print(json.dumps(summary,ensure_ascii=False,indent=2,default=str))
    return 0 if summary["status"]=="OK" else 2


if __name__=="__main__":
    raise SystemExit(def_main())

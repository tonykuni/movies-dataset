# -*- coding: utf-8 -*-
"""
def VIA · Free Consensus-Like EPS Fetcher
抓取 2330.TW + global semiconductor peers 的免費 consensus-like EPS / forward PE 資料。

重要限制：
1) yfinance/Yahoo：通常只有 0Y / +1Y EPS estimate，不是 2026/2027/2028 完整年度 consensus。
2) FMP Free：可嘗試 analyst-estimates annual EPS，但需要免費 API key，coverage / quota / licensing 需自行驗證。
3) Alpha Vantage Free：主要適合 quarterly estimatedEPS / earnings calendar，不是完整年度 FY1/FY2/FY3 consensus。
4) FactSet / Refinitiv / Visible Alpha / Bloomberg 等正式 consensus estimates 通常不是免費資料，本程式不繞過授權。
"""

# ============================================================
# def 00 · PARAMETERS
# ============================================================

TARGET_YEARS = [2026, 2027, 2028]

# yfinance 的 0y/+1y 是相對年度。請依執行時點調整。
# 例如 2026 年中執行：0y ≈ 2026E，+1y ≈ 2027E。
YFINANCE_ANNUAL_PERIOD_TO_YEAR = {
    "0y": 2026,
    "+1y": 2027,
}

ENABLE_YFINANCE = True
ENABLE_FMP = True
ENABLE_ALPHA_VANTAGE = True

# 免費 API key：建議用環境變數，不要硬寫在程式裡。
# Windows PowerShell:
#   setx FMP_API_KEY "YOUR_KEY"
#   setx ALPHA_VANTAGE_API_KEY "YOUR_KEY"
FMP_API_KEY_ENV_NAME = "FMP_API_KEY"
ALPHA_VANTAGE_API_KEY_ENV_NAME = "ALPHA_VANTAGE_API_KEY"

FMP_BASE_URL = "https://financialmodelingprep.com/stable/analyst-estimates"
FMP_PERIOD = "annual"
FMP_LIMIT = 20
FMP_PAGE = 0

ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_EARNINGS_CALENDAR_HORIZON = "12month"

REQUEST_TIMEOUT_SECONDS = 30
REQUEST_SLEEP_SECONDS = 0.35

OUTPUT_DIR = "via_free_forward_eps_outputs"
OUTPUT_RAW_PARQUET = "free_consensus_like_eps_raw.parquet"
OUTPUT_RAW_CSV = "free_consensus_like_eps_raw.csv"
OUTPUT_PIVOT_CSV = "free_consensus_like_eps_pivot.csv"
OUTPUT_QUALITY_CSV = "free_consensus_like_eps_quality_log.csv"

# def Peer universe:
# - yf_ticker: yfinance symbol
# - fmp_symbol: FMP symbol，若 coverage 不支援請自行改 mapping
# - av_symbol: Alpha Vantage symbol，非美股 coverage 需自行驗證
# - segment_block: 估值分區
PEER_UNIVERSE = [
    {"name": "TSMC Taiwan", "yf_ticker": "2330.TW", "fmp_symbol": "2330.TW", "av_symbol": "2330.TW", "segment_block": "Foundry"},
    {"name": "TSMC ADR", "yf_ticker": "TSM", "fmp_symbol": "TSM", "av_symbol": "TSM", "segment_block": "Foundry ADR"},
    {"name": "UMC Taiwan", "yf_ticker": "2303.TW", "fmp_symbol": "2303.TW", "av_symbol": "2303.TW", "segment_block": "Foundry"},
    {"name": "UMC ADR", "yf_ticker": "UMC", "fmp_symbol": "UMC", "av_symbol": "UMC", "segment_block": "Foundry ADR"},
    {"name": "GlobalFoundries", "yf_ticker": "GFS", "fmp_symbol": "GFS", "av_symbol": "GFS", "segment_block": "Foundry"},
    {"name": "Samsung Electronics", "yf_ticker": "005930.KS", "fmp_symbol": "005930.KS", "av_symbol": "005930.KS", "segment_block": "Foundry / Memory"},
    {"name": "SMIC", "yf_ticker": "0981.HK", "fmp_symbol": "0981.HK", "av_symbol": "0981.HK", "segment_block": "Foundry China"},
    {"name": "Hua Hong", "yf_ticker": "1347.HK", "fmp_symbol": "1347.HK", "av_symbol": "1347.HK", "segment_block": "Foundry China"},

    {"name": "NVIDIA", "yf_ticker": "NVDA", "fmp_symbol": "NVDA", "av_symbol": "NVDA", "segment_block": "AI Fabless"},
    {"name": "AMD", "yf_ticker": "AMD", "fmp_symbol": "AMD", "av_symbol": "AMD", "segment_block": "AI Fabless"},
    {"name": "Broadcom", "yf_ticker": "AVGO", "fmp_symbol": "AVGO", "av_symbol": "AVGO", "segment_block": "AI ASIC / Networking"},
    {"name": "Marvell", "yf_ticker": "MRVL", "fmp_symbol": "MRVL", "av_symbol": "MRVL", "segment_block": "AI ASIC / Networking"},
    {"name": "Qualcomm", "yf_ticker": "QCOM", "fmp_symbol": "QCOM", "av_symbol": "QCOM", "segment_block": "Mobile / Edge AI"},
    {"name": "MediaTek", "yf_ticker": "2454.TW", "fmp_symbol": "2454.TW", "av_symbol": "2454.TW", "segment_block": "Mobile AP"},

    {"name": "SK hynix", "yf_ticker": "000660.KS", "fmp_symbol": "000660.KS", "av_symbol": "000660.KS", "segment_block": "Memory / HBM"},
    {"name": "Micron", "yf_ticker": "MU", "fmp_symbol": "MU", "av_symbol": "MU", "segment_block": "Memory / HBM"},

    {"name": "ASML", "yf_ticker": "ASML", "fmp_symbol": "ASML", "av_symbol": "ASML", "segment_block": "Equipment"},
    {"name": "Applied Materials", "yf_ticker": "AMAT", "fmp_symbol": "AMAT", "av_symbol": "AMAT", "segment_block": "Equipment"},
    {"name": "Lam Research", "yf_ticker": "LRCX", "fmp_symbol": "LRCX", "av_symbol": "LRCX", "segment_block": "Equipment"},
    {"name": "KLA", "yf_ticker": "KLAC", "fmp_symbol": "KLAC", "av_symbol": "KLAC", "segment_block": "Equipment"},
    {"name": "Tokyo Electron", "yf_ticker": "8035.T", "fmp_symbol": "8035.T", "av_symbol": "8035.T", "segment_block": "Equipment"},

    {"name": "ASE Technology Taiwan", "yf_ticker": "3711.TW", "fmp_symbol": "3711.TW", "av_symbol": "3711.TW", "segment_block": "OSAT / Packaging"},
    {"name": "ASE Technology ADR", "yf_ticker": "ASX", "fmp_symbol": "ASX", "av_symbol": "ASX", "segment_block": "OSAT / Packaging ADR"},
    {"name": "Amkor", "yf_ticker": "AMKR", "fmp_symbol": "AMKR", "av_symbol": "AMKR", "segment_block": "OSAT / Packaging"},

    {"name": "Synopsys", "yf_ticker": "SNPS", "fmp_symbol": "SNPS", "av_symbol": "SNPS", "segment_block": "EDA / IP"},
    {"name": "Cadence", "yf_ticker": "CDNS", "fmp_symbol": "CDNS", "av_symbol": "CDNS", "segment_block": "EDA / IP"},
    {"name": "Arm", "yf_ticker": "ARM", "fmp_symbol": "ARM", "av_symbol": "ARM", "segment_block": "EDA / IP"},

    {"name": "Texas Instruments", "yf_ticker": "TXN", "fmp_symbol": "TXN", "av_symbol": "TXN", "segment_block": "Analog / Auto / Power"},
    {"name": "Analog Devices", "yf_ticker": "ADI", "fmp_symbol": "ADI", "av_symbol": "ADI", "segment_block": "Analog / Auto / Power"},
    {"name": "Infineon", "yf_ticker": "IFX.DE", "fmp_symbol": "IFX.DE", "av_symbol": "IFX.DE", "segment_block": "Analog / Auto / Power"},
    {"name": "NXP", "yf_ticker": "NXPI", "fmp_symbol": "NXPI", "av_symbol": "NXPI", "segment_block": "Analog / Auto / Power"},
    {"name": "STMicroelectronics", "yf_ticker": "STM", "fmp_symbol": "STM", "av_symbol": "STM", "segment_block": "Analog / Auto / Power"},
    {"name": "onsemi", "yf_ticker": "ON", "fmp_symbol": "ON", "av_symbol": "ON", "segment_block": "Analog / Auto / Power"},
]


# ============================================================
# def 01 · IMPORTS
# ============================================================

def import_libraries():
    import os
    import time
    import json
    import math
    import traceback
    from datetime import datetime, timezone
    from pathlib import Path
    from urllib.parse import urlencode

    import pandas as pd
    import requests

    try:
        import yfinance as yf
    except Exception:
        yf = None

    return {
        "os": os,
        "time": time,
        "json": json,
        "math": math,
        "traceback": traceback,
        "datetime": datetime,
        "timezone": timezone,
        "Path": Path,
        "urlencode": urlencode,
        "pd": pd,
        "requests": requests,
        "yf": yf,
    }


# ============================================================
# def 02 · SMALL HELPERS
# ============================================================

def def_now_utc_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def def_safe_float(value):
    if value is None:
        return None

    try:
        text = str(value).strip()
        if text == "" or text.lower() in ["none", "nan", "null", "n/a", "-"]:
            return None
        return float(text)
    except Exception:
        return None


def def_safe_int(value):
    num = def_safe_float(value)
    if num is None:
        return None
    try:
        return int(num)
    except Exception:
        return None


def def_clean_key(value):
    return str(value).replace("_", "").replace("-", "").replace(" ", "").lower()


def def_get_first_value_case_insensitive(row, candidate_keys):
    if not isinstance(row, dict):
        return None

    clean_map = {def_clean_key(k): k for k in row.keys()}

    for candidate_key in candidate_keys:
        clean_candidate = def_clean_key(candidate_key)
        if clean_candidate in clean_map:
            return row.get(clean_map[clean_candidate])

    return None


def def_infer_year_from_date(value):
    if value is None:
        return None

    text = str(value).strip()
    if len(text) >= 4 and text[:4].isdigit():
        return int(text[:4])

    return None


def def_build_quality_flag(
    source,
    fiscal_year,
    eps_mean,
    analyst_count,
    data_type,
):
    if eps_mean is None:
        return "FAIL_NO_EPS"

    if fiscal_year is None:
        return "WARN_NO_FISCAL_YEAR"

    if fiscal_year not in TARGET_YEARS:
        return "WARN_OUTSIDE_TARGET_YEARS"

    if eps_mean <= 0:
        return "WARN_NEGATIVE_OR_ZERO_EPS"

    if analyst_count is None:
        return "WARN_ANALYST_COUNT_UNKNOWN"

    if analyst_count < 3:
        return "WARN_LOW_ANALYST_COUNT"

    if data_type != "annual_consensus_like":
        return "WARN_NOT_ANNUAL_CONSENSUS"

    if source in ["YFinance", "FMP", "AlphaVantage"]:
        return "OK_FREE_SOURCE_BEST_EFFORT"

    return "OK"


def def_calculate_forward_pe(price, eps_mean):
    price_num = def_safe_float(price)
    eps_num = def_safe_float(eps_mean)

    if price_num is None or eps_num is None:
        return None

    if eps_num == 0:
        return None

    return price_num / eps_num


def def_base_record(peer, source, source_symbol):
    return {
        "asof_utc": def_now_utc_iso(),
        "name": peer.get("name"),
        "yf_ticker": peer.get("yf_ticker"),
        "source_symbol": source_symbol,
        "segment_block": peer.get("segment_block"),
        "source": source,
        "fiscal_year": None,
        "period_label": None,
        "data_type": None,
        "eps_mean": None,
        "eps_low": None,
        "eps_high": None,
        "analyst_count": None,
        "price": None,
        "price_currency": None,
        "eps_currency": None,
        "forward_pe_calc": None,
        "source_url": None,
        "method_note": None,
        "quality_flag": None,
        "error_message": None,
    }


# ============================================================
# def 03 · YFINANCE FETCHER
# ============================================================

def def_get_yfinance_price_and_currency(yf, yf_ticker):
    price = None
    currency = None

    if yf is None:
        return price, currency

    obj = yf.Ticker(yf_ticker)

    try:
        fast_info = getattr(obj, "fast_info", None)
        if fast_info is not None:
            price = (
                getattr(fast_info, "last_price", None)
                or fast_info.get("last_price", None)
                or fast_info.get("lastPrice", None)
            )
            currency = (
                getattr(fast_info, "currency", None)
                or fast_info.get("currency", None)
            )
    except Exception:
        pass

    if price is None or currency is None:
        try:
            info = obj.get_info()
            price = price or info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
            currency = currency or info.get("currency") or info.get("financialCurrency")
        except Exception:
            pass

    return def_safe_float(price), currency


def def_fetch_yfinance_eps_one(peer):
    import pandas as pd

    try:
        import yfinance as yf
    except Exception as exc:
        rec = def_base_record(peer, "YFinance", peer.get("yf_ticker"))
        rec["quality_flag"] = "FAIL_YFINANCE_NOT_INSTALLED"
        rec["error_message"] = str(exc)
        return pd.DataFrame([rec])

    yf_ticker = peer.get("yf_ticker")
    obj = yf.Ticker(yf_ticker)

    price, price_currency = def_get_yfinance_price_and_currency(yf, yf_ticker)

    try:
        estimate_df = obj.get_earnings_estimate()
    except Exception as exc:
        estimate_df = None
        fetch_error = str(exc)
    else:
        fetch_error = None

    records = []

    if estimate_df is None or getattr(estimate_df, "empty", True):
        rec = def_base_record(peer, "YFinance", yf_ticker)
        rec["price"] = price
        rec["price_currency"] = price_currency
        rec["method_note"] = "yfinance get_earnings_estimate returned no data."
        rec["quality_flag"] = "FAIL_NO_YFINANCE_EARNINGS_ESTIMATE"
        rec["error_message"] = fetch_error
        records.append(rec)
        return pd.DataFrame(records)

    for period_label, row in estimate_df.iterrows():
        period_label = str(period_label)

        # 只把 0y/+1y 視為年度 consensus-like EPS；0q/+1q 不混進 annual forward PE。
        if period_label not in YFINANCE_ANNUAL_PERIOD_TO_YEAR:
            continue

        fiscal_year = YFINANCE_ANNUAL_PERIOD_TO_YEAR.get(period_label)
        eps_mean = def_safe_float(row.get("avg"))
        eps_low = def_safe_float(row.get("low"))
        eps_high = def_safe_float(row.get("high"))
        analyst_count = def_safe_int(row.get("numberOfAnalysts"))

        rec = def_base_record(peer, "YFinance", yf_ticker)
        rec["fiscal_year"] = fiscal_year
        rec["period_label"] = period_label
        rec["data_type"] = "annual_consensus_like"
        rec["eps_mean"] = eps_mean
        rec["eps_low"] = eps_low
        rec["eps_high"] = eps_high
        rec["analyst_count"] = analyst_count
        rec["price"] = price
        rec["price_currency"] = price_currency
        rec["eps_currency"] = price_currency
        rec["forward_pe_calc"] = def_calculate_forward_pe(price, eps_mean)
        rec["method_note"] = "Yahoo/yfinance annual earnings estimate. 0y/+1y only; map to fiscal year by parameter."
        rec["quality_flag"] = def_build_quality_flag(
            source="YFinance",
            fiscal_year=fiscal_year,
            eps_mean=eps_mean,
            analyst_count=analyst_count,
            data_type="annual_consensus_like",
        )
        records.append(rec)

    if not records:
        rec = def_base_record(peer, "YFinance", yf_ticker)
        rec["price"] = price
        rec["price_currency"] = price_currency
        rec["method_note"] = "yfinance had only quarterly rows or unsupported periods."
        rec["quality_flag"] = "WARN_NO_ANNUAL_ROWS_0Y_1Y"
        records.append(rec)

    return pd.DataFrame(records)


def def_fetch_yfinance_eps_many(peers):
    import pandas as pd

    frames = []

    for peer in peers:
        try:
            frames.append(def_fetch_yfinance_eps_one(peer))
        except Exception as exc:
            rec = def_base_record(peer, "YFinance", peer.get("yf_ticker"))
            rec["quality_flag"] = "FAIL_EXCEPTION"
            rec["error_message"] = str(exc)
            frames.append(pd.DataFrame([rec]))

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ============================================================
# def 04 · FMP FETCHER
# ============================================================

def def_fetch_fmp_eps_one(peer, api_key):
    import time
    import pandas as pd
    import requests

    fmp_symbol = peer.get("fmp_symbol")

    if not api_key:
        rec = def_base_record(peer, "FMP", fmp_symbol)
        rec["quality_flag"] = "SKIP_NO_FMP_API_KEY"
        rec["method_note"] = "Set environment variable FMP_API_KEY to use FMP free/basic endpoint."
        return pd.DataFrame([rec])

    params = {
        "symbol": fmp_symbol,
        "period": FMP_PERIOD,
        "page": FMP_PAGE,
        "limit": FMP_LIMIT,
        "apikey": api_key,
    }

    try:
        response = requests.get(FMP_BASE_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        source_url = response.url
        response.raise_for_status()
        payload = response.json()
        time.sleep(REQUEST_SLEEP_SECONDS)
    except Exception as exc:
        rec = def_base_record(peer, "FMP", fmp_symbol)
        rec["source_url"] = FMP_BASE_URL
        rec["quality_flag"] = "FAIL_FMP_REQUEST"
        rec["error_message"] = str(exc)
        return pd.DataFrame([rec])

    if isinstance(payload, dict) and payload.get("Error Message"):
        rec = def_base_record(peer, "FMP", fmp_symbol)
        rec["source_url"] = source_url
        rec["quality_flag"] = "FAIL_FMP_ERROR_MESSAGE"
        rec["error_message"] = str(payload.get("Error Message"))
        return pd.DataFrame([rec])

    if not isinstance(payload, list) or not payload:
        rec = def_base_record(peer, "FMP", fmp_symbol)
        rec["source_url"] = source_url
        rec["quality_flag"] = "FAIL_NO_FMP_ANALYST_ESTIMATES"
        rec["method_note"] = "FMP returned empty data; coverage may not support this symbol on free/basic plan."
        return pd.DataFrame([rec])

    records = []

    for item in payload:
        if not isinstance(item, dict):
            continue

        date_value = def_get_first_value_case_insensitive(item, ["date", "fiscalDateEnding", "calendarDate"])
        fiscal_year = (
            def_safe_int(def_get_first_value_case_insensitive(item, ["fiscalYear", "calendarYear", "year"]))
            or def_infer_year_from_date(date_value)
        )

        if fiscal_year not in TARGET_YEARS:
            continue

        eps_mean = def_safe_float(def_get_first_value_case_insensitive(
            item,
            [
                "estimatedEpsAvg",
                "estimatedEPSAvg",
                "estimatedEpsMean",
                "epsAvg",
                "epsMean",
                "epsEstimatedAvg",
                "epsEstimatedMean",
            ],
        ))

        eps_low = def_safe_float(def_get_first_value_case_insensitive(
            item,
            [
                "estimatedEpsLow",
                "estimatedEPSLow",
                "epsLow",
                "epsEstimatedLow",
            ],
        ))

        eps_high = def_safe_float(def_get_first_value_case_insensitive(
            item,
            [
                "estimatedEpsHigh",
                "estimatedEPSHigh",
                "epsHigh",
                "epsEstimatedHigh",
            ],
        ))

        analyst_count = def_safe_int(def_get_first_value_case_insensitive(
            item,
            [
                "numberAnalystEstimatedEps",
                "numberAnalystsEstimatedEps",
                "numberOfAnalysts",
                "analystCount",
                "numAnalysts",
            ],
        ))

        rec = def_base_record(peer, "FMP", fmp_symbol)
        rec["fiscal_year"] = fiscal_year
        rec["period_label"] = str(date_value) if date_value is not None else str(fiscal_year)
        rec["data_type"] = "annual_consensus_like"
        rec["eps_mean"] = eps_mean
        rec["eps_low"] = eps_low
        rec["eps_high"] = eps_high
        rec["analyst_count"] = analyst_count
        rec["eps_currency"] = def_get_first_value_case_insensitive(item, ["currency", "reportedCurrency"])
        rec["source_url"] = source_url
        rec["method_note"] = "FMP stable analyst-estimates annual endpoint; coverage and free quota must be validated per symbol."
        rec["quality_flag"] = def_build_quality_flag(
            source="FMP",
            fiscal_year=fiscal_year,
            eps_mean=eps_mean,
            analyst_count=analyst_count,
            data_type="annual_consensus_like",
        )

        records.append(rec)

    if not records:
        rec = def_base_record(peer, "FMP", fmp_symbol)
        rec["source_url"] = source_url
        rec["quality_flag"] = "WARN_NO_TARGET_YEAR_FMP_ROWS"
        rec["method_note"] = f"FMP returned data, but no rows matched TARGET_YEARS={TARGET_YEARS}."
        records.append(rec)

    return pd.DataFrame(records)


def def_fetch_fmp_eps_many(peers, api_key):
    import pandas as pd

    frames = []

    for peer in peers:
        try:
            frames.append(def_fetch_fmp_eps_one(peer, api_key=api_key))
        except Exception as exc:
            rec = def_base_record(peer, "FMP", peer.get("fmp_symbol"))
            rec["quality_flag"] = "FAIL_EXCEPTION"
            rec["error_message"] = str(exc)
            frames.append(pd.DataFrame([rec]))

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ============================================================
# def 05 · ALPHA VANTAGE FETCHER
# ============================================================

def def_fetch_alpha_vantage_earnings_calendar_one(peer, api_key):
    import csv
    import io
    import time
    import pandas as pd
    import requests

    av_symbol = peer.get("av_symbol")

    if not api_key:
        rec = def_base_record(peer, "AlphaVantage", av_symbol)
        rec["quality_flag"] = "SKIP_NO_ALPHA_VANTAGE_API_KEY"
        rec["method_note"] = "Set environment variable ALPHA_VANTAGE_API_KEY to use Alpha Vantage free endpoint."
        return pd.DataFrame([rec])

    params = {
        "function": "EARNINGS_CALENDAR",
        "symbol": av_symbol,
        "horizon": ALPHA_VANTAGE_EARNINGS_CALENDAR_HORIZON,
        "apikey": api_key,
    }

    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        source_url = response.url
        response.raise_for_status()
        text = response.text
        time.sleep(REQUEST_SLEEP_SECONDS)
    except Exception as exc:
        rec = def_base_record(peer, "AlphaVantage", av_symbol)
        rec["source_url"] = ALPHA_VANTAGE_BASE_URL
        rec["quality_flag"] = "FAIL_ALPHA_VANTAGE_REQUEST"
        rec["error_message"] = str(exc)
        return pd.DataFrame([rec])

    if "Thank you for using Alpha Vantage" in text or "Our standard API rate limit" in text:
        rec = def_base_record(peer, "AlphaVantage", av_symbol)
        rec["source_url"] = source_url
        rec["quality_flag"] = "FAIL_ALPHA_VANTAGE_RATE_LIMIT_OR_NOTE"
        rec["error_message"] = text[:500]
        return pd.DataFrame([rec])

    try:
        rows = list(csv.DictReader(io.StringIO(text)))
    except Exception as exc:
        rec = def_base_record(peer, "AlphaVantage", av_symbol)
        rec["source_url"] = source_url
        rec["quality_flag"] = "FAIL_ALPHA_VANTAGE_CSV_PARSE"
        rec["error_message"] = str(exc)
        return pd.DataFrame([rec])

    if not rows:
        rec = def_base_record(peer, "AlphaVantage", av_symbol)
        rec["source_url"] = source_url
        rec["quality_flag"] = "FAIL_NO_ALPHA_VANTAGE_EARNINGS_CALENDAR"
        return pd.DataFrame([rec])

    records = []

    for item in rows:
        fiscal_date = item.get("fiscalDateEnding")
        fiscal_year = def_infer_year_from_date(fiscal_date)
        eps_mean = def_safe_float(item.get("estimate"))

        rec = def_base_record(peer, "AlphaVantage", av_symbol)
        rec["fiscal_year"] = fiscal_year
        rec["period_label"] = fiscal_date
        rec["data_type"] = "quarterly_or_event_estimate"
        rec["eps_mean"] = eps_mean
        rec["eps_currency"] = item.get("currency")
        rec["source_url"] = source_url
        rec["method_note"] = "Alpha Vantage earnings calendar gives upcoming event/quarter estimate, not full annual consensus EPS."
        rec["quality_flag"] = def_build_quality_flag(
            source="AlphaVantage",
            fiscal_year=fiscal_year,
            eps_mean=eps_mean,
            analyst_count=None,
            data_type="quarterly_or_event_estimate",
        )
        records.append(rec)

    return pd.DataFrame(records)


def def_fetch_alpha_vantage_earnings_calendar_many(peers, api_key):
    import pandas as pd

    frames = []

    for peer in peers:
        try:
            frames.append(def_fetch_alpha_vantage_earnings_calendar_one(peer, api_key=api_key))
        except Exception as exc:
            rec = def_base_record(peer, "AlphaVantage", peer.get("av_symbol"))
            rec["quality_flag"] = "FAIL_EXCEPTION"
            rec["error_message"] = str(exc)
            frames.append(pd.DataFrame([rec]))

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ============================================================
# def 06 · PRICE ENRICHMENT
# ============================================================

def def_build_price_frame_from_yfinance(peers):
    import pandas as pd

    try:
        import yfinance as yf
    except Exception:
        return pd.DataFrame()

    rows = []

    for peer in peers:
        try:
            price, currency = def_get_yfinance_price_and_currency(yf, peer.get("yf_ticker"))
            rows.append({
                "yf_ticker": peer.get("yf_ticker"),
                "price_yfinance": price,
                "price_currency_yfinance": currency,
            })
        except Exception:
            rows.append({
                "yf_ticker": peer.get("yf_ticker"),
                "price_yfinance": None,
                "price_currency_yfinance": None,
            })

    return pd.DataFrame(rows)


def def_enrich_price_and_forward_pe(df, peers):
    import pandas as pd

    if df is None or df.empty:
        return pd.DataFrame()

    price_df = def_build_price_frame_from_yfinance(peers)

    if price_df.empty:
        return df

    out = df.merge(price_df, how="left", on="yf_ticker")

    out["price"] = out["price"].where(out["price"].notna(), out["price_yfinance"])
    out["price_currency"] = out["price_currency"].where(out["price_currency"].notna(), out["price_currency_yfinance"])

    out["forward_pe_calc"] = out.apply(
        lambda row: def_calculate_forward_pe(row.get("price"), row.get("eps_mean")),
        axis=1,
    )

    out = out.drop(columns=["price_yfinance", "price_currency_yfinance"], errors="ignore")

    return out


# ============================================================
# def 07 · OUTPUTS
# ============================================================

def def_make_pivot_matrix(df):
    import pandas as pd

    if df is None or df.empty:
        return pd.DataFrame()

    valid = df.copy()
    valid = valid[valid["fiscal_year"].isin(TARGET_YEARS)]

    if valid.empty:
        return pd.DataFrame()

    # source priority：FMP annual > yfinance annual > Alpha Vantage event/quarter
    source_priority = {
        "FMP": 1,
        "YFinance": 2,
        "AlphaVantage": 3,
    }

    valid["source_priority"] = valid["source"].map(source_priority).fillna(99)
    valid["eps_available"] = valid["eps_mean"].notna().astype(int)
    valid = valid.sort_values(
        ["yf_ticker", "fiscal_year", "source_priority", "eps_available"],
        ascending=[True, True, True, False],
    )

    best = valid.drop_duplicates(subset=["yf_ticker", "fiscal_year"], keep="first").copy()

    pivot_eps = best.pivot_table(
        index=["name", "yf_ticker", "segment_block"],
        columns="fiscal_year",
        values="eps_mean",
        aggfunc="first",
    ).add_prefix("eps_").reset_index()

    pivot_pe = best.pivot_table(
        index=["name", "yf_ticker", "segment_block"],
        columns="fiscal_year",
        values="forward_pe_calc",
        aggfunc="first",
    ).add_prefix("forward_pe_").reset_index()

    pivot_source = best.pivot_table(
        index=["name", "yf_ticker", "segment_block"],
        columns="fiscal_year",
        values="source",
        aggfunc="first",
    ).add_prefix("source_").reset_index()

    out = pivot_eps.merge(
        pivot_pe,
        on=["name", "yf_ticker", "segment_block"],
        how="outer",
    ).merge(
        pivot_source,
        on=["name", "yf_ticker", "segment_block"],
        how="outer",
    )

    return out


def def_save_outputs(raw_df, pivot_df, output_dir):
    from pathlib import Path

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    raw_parquet_path = output_path / OUTPUT_RAW_PARQUET
    raw_csv_path = output_path / OUTPUT_RAW_CSV
    pivot_csv_path = output_path / OUTPUT_PIVOT_CSV
    quality_csv_path = output_path / OUTPUT_QUALITY_CSV

    if raw_df is not None and not raw_df.empty:
        try:
            raw_df.to_parquet(raw_parquet_path, index=False)
        except Exception as exc:
            print(f"[WARN] Parquet write failed. Install pyarrow. Error: {exc}")

        raw_df.to_csv(raw_csv_path, index=False, encoding="utf-8-sig")

        quality_cols = [
            "asof_utc", "name", "yf_ticker", "source", "source_symbol",
            "fiscal_year", "period_label", "data_type", "quality_flag",
            "method_note", "error_message",
        ]
        existing_quality_cols = [col for col in quality_cols if col in raw_df.columns]
        raw_df[existing_quality_cols].to_csv(quality_csv_path, index=False, encoding="utf-8-sig")

    if pivot_df is not None and not pivot_df.empty:
        pivot_df.to_csv(pivot_csv_path, index=False, encoding="utf-8-sig")

    print("")
    print("================================================================================")
    print("def OUTPUTS")
    print("================================================================================")
    print(f"RAW CSV     : {raw_csv_path}")
    print(f"RAW PARQUET : {raw_parquet_path}")
    print(f"PIVOT CSV   : {pivot_csv_path}")
    print(f"QUALITY CSV : {quality_csv_path}")


# ============================================================
# def 08 · MAIN PIPELINE
# ============================================================

def def_run_pipeline():
    import os
    import pandas as pd

    frames = []

    fmp_api_key = os.getenv(FMP_API_KEY_ENV_NAME, "").strip()
    alpha_vantage_api_key = os.getenv(ALPHA_VANTAGE_API_KEY_ENV_NAME, "").strip()

    print("================================================================================")
    print("def VIA · FREE CONSENSUS-LIKE EPS FETCHER")
    print("================================================================================")
    print(f"def TARGET_YEARS: {TARGET_YEARS}")
    print(f"def ENABLE_YFINANCE: {ENABLE_YFINANCE}")
    print(f"def ENABLE_FMP: {ENABLE_FMP} · key_loaded={bool(fmp_api_key)}")
    print(f"def ENABLE_ALPHA_VANTAGE: {ENABLE_ALPHA_VANTAGE} · key_loaded={bool(alpha_vantage_api_key)}")
    print("")

    if ENABLE_YFINANCE:
        print("def FETCH · YFinance 0Y/+1Y annual earnings estimates")
        frames.append(def_fetch_yfinance_eps_many(PEER_UNIVERSE))

    if ENABLE_FMP:
        print("def FETCH · FMP analyst-estimates annual")
        frames.append(def_fetch_fmp_eps_many(PEER_UNIVERSE, api_key=fmp_api_key))

    if ENABLE_ALPHA_VANTAGE:
        print("def FETCH · Alpha Vantage earnings calendar")
        frames.append(def_fetch_alpha_vantage_earnings_calendar_many(PEER_UNIVERSE, api_key=alpha_vantage_api_key))

    if not frames:
        print("[FAIL] No source enabled.")
        return pd.DataFrame(), pd.DataFrame()

    raw_df = pd.concat(frames, ignore_index=True)
    raw_df = def_enrich_price_and_forward_pe(raw_df, PEER_UNIVERSE)

    preferred_cols = [
        "asof_utc",
        "name",
        "yf_ticker",
        "source",
        "source_symbol",
        "segment_block",
        "fiscal_year",
        "period_label",
        "data_type",
        "eps_mean",
        "eps_low",
        "eps_high",
        "analyst_count",
        "price",
        "price_currency",
        "eps_currency",
        "forward_pe_calc",
        "quality_flag",
        "method_note",
        "source_url",
        "error_message",
    ]

    existing_cols = [col for col in preferred_cols if col in raw_df.columns]
    remaining_cols = [col for col in raw_df.columns if col not in existing_cols]
    raw_df = raw_df[existing_cols + remaining_cols]

    pivot_df = def_make_pivot_matrix(raw_df)

    def_save_outputs(
        raw_df=raw_df,
        pivot_df=pivot_df,
        output_dir=OUTPUT_DIR,
    )

    print("")
    print("================================================================================")
    print("def PREVIEW · RAW")
    print("================================================================================")
    print(raw_df.head(30).to_string(index=False))

    if pivot_df is not None and not pivot_df.empty:
        print("")
        print("================================================================================")
        print("def PREVIEW · PIVOT")
        print("================================================================================")
        print(pivot_df.head(30).to_string(index=False))

    return raw_df, pivot_df


# ============================================================
# def 99 · ENTRY POINT
# ============================================================

def main():
    def_run_pipeline()


if __name__ == "__main__":
    main()

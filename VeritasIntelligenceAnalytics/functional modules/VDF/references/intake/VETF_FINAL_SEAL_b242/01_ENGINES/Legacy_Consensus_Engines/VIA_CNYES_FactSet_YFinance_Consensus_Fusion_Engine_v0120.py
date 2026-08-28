# -*- coding: utf-8 -*-
"""
VIA · CNYES/FactSet × YFinance Consensus Fusion Engine · v2.0.0

從鉅亨網台股網址中的代碼擷取公開顯示的 FactSet 共識資料：
1. 目標估值（最高／最低／平均／中位數／分析師人數／更新日）
2. 綜合評級歷史（買進／優於大盤／持有／劣於大盤／賣出）
3. 預估 EPS 全部年度 item
4. 預估營收全部年度 item
5. YFinance 目標價最低／平均／中位數／最高與建議評級
6. 雙來源差異、評等方向與一致性矩陣
7. YFinance 專用共識介面（目標價、EPS、營收、修正、成長與評等）
8. DuckDB 歷史長表、Parquet 快照、原子斷點續傳與冪等更新

資料來源：
- HTML 內嵌 __NEXT_DATA__（SSR 備援）
- 鉅亨網頁面實際使用的 marketinfo 公開資料端點（主要）

本程式不登入、不繞過驗證、不破解付費牆。請遵守來源網站條款、合理頻率使用，
並保留 source_url、擷取時間與品質檢查紀錄，以利稽核。
"""

# =============================================================================
# def 00 · PARAMETERS
# =============================================================================

ENGINE_NAME = "VIA_CNYES_FACTSET_YFINANCE_CONSENSUS_FUSION_ENGINE"
ENGINE_VERSION = "2.0.0"
SCHEMA_VERSION = "VIA-CONSENSUS-LONG/2.0"

DEFAULT_CODES = ["2330"]
MAX_CODES_PER_RUN = 50

CNYES_PAGE_TEMPLATE = "https://www.cnyes.com/twstock/{code}/summary/overview"
DEFAULT_MARKET_INFO_API_URL = "https://marketinfo.api.cnyes.com"

TARGET_PRICE_PATH = "/mi/api/v1/financialIndicator/targetPrice/{symbol}"
FACTSET_RATING_PATH = "/mi/api/v1/financialIndicator/factSetEstimate/{symbol}"
ESTIMATE_PROFIT_PATH = "/mi/api/v1/financialIndicator/estimateProfit/{symbol}"

REQUEST_TIMEOUT_SECONDS = 30
REQUEST_RETRIES = 3
REQUEST_BACKOFF_SECONDS = 0.8
REQUEST_SLEEP_SECONDS = 0.30

YFINANCE_REQUIRED = True
YFINANCE_REQUEST_RETRIES = 3
YFINANCE_RETRY_SLEEP_SECONDS = 1.0
YFINANCE_HISTORY_PERIOD = "10d"
YFINANCE_SOURCE_URL_TEMPLATE = "https://finance.yahoo.com/quote/{ticker}/"
YFINANCE_INFO_FIELDS = [
    "symbol",
    "shortName",
    "longName",
    "currency",
    "currentPrice",
    "regularMarketPrice",
    "adjClose",
    "beta",
    "targetLowPrice",
    "targetMeanPrice",
    "targetMedianPrice",
    "targetHighPrice",
    "numberOfAnalystOpinions",
    "recommendationMean",
    "recommendationKey",
]
YFINANCE_ANALYSIS_METHODS = [
    "get_analyst_price_targets",
    "get_earnings_estimate",
    "get_revenue_estimate",
    "get_eps_trend",
    "get_eps_revisions",
    "get_growth_estimates",
    "get_recommendations_summary",
]
YFINANCE_METHOD_TO_SECTION = {
    "get_analyst_price_targets": "YFINANCE_PRICE_TARGETS",
    "get_earnings_estimate": "YFINANCE_EARNINGS_ESTIMATE",
    "get_revenue_estimate": "YFINANCE_REVENUE_ESTIMATE",
    "get_eps_trend": "YFINANCE_EPS_TREND",
    "get_eps_revisions": "YFINANCE_EPS_REVISIONS",
    "get_growth_estimates": "YFINANCE_GROWTH_ESTIMATES",
    "get_recommendations_summary": "YFINANCE_RECOMMENDATIONS",
}

TARGET_SPECTRUM_DOMAIN_PADDING_PCT = 0.03
TARGET_SPECTRUM_COLORS = {
    "low": "#1B8A5A",
    "mid": "#F0C84B",
    "high": "#D95D39",
}
TARGET_SPECTRUM_MARKERS = {
    "median": "HOLLOW_CIRCLE",
    "mean": "HOLLOW_TRIANGLE",
}

RATING_STACK_SEGMENTS = [
    ("buy_count", "買進", "buy"),
    ("outperform_count", "優於大盤", "outperform"),
    ("hold_count", "持有", "hold"),
    ("underperform_count", "劣於大盤", "underperform"),
    ("sell_count", "賣出", "sell"),
]

VISUAL_LOCK_VERSION = "1.0"
VISUAL_LOCK_MAX_WIDTH_PX = 1480
VISUAL_LOCK_OVERVIEW_LEFT_PX = 420
VISUAL_LOCK_CARD_HEIGHT_PX = 122
VISUAL_LOCK_SPECTRUM_HEIGHT_PX = 253
VISUAL_LOCK_VALUATION_HEIGHT_PX = 292
VISUAL_LOCK_DESKTOP_BREAKPOINT_PX = 980

VALUATION_BAND_DATA_DIR = "output_2330_valuation"
VALUATION_BAND_CSV_TEMPLATE = "{code}_TwoYear_PE_PB_Daily.csv"
VALUATION_BAND_WINDOW_LABEL = "近 2 年"
VALUATION_BAND_WIDTH = 760
VALUATION_BAND_HEIGHT = 292
VALUATION_BAND_COLORS = {
    "q10": "#2F7D68",
    "q25": "#79A56B",
    "q50": "#C49A32",
    "q75": "#D4773D",
    "q90": "#B54A45",
    "price": "#162235",
    "band_fill": "#E8E3D5",
    "grid": "#DCE4EB",
}

TARGET_DIFFERENCE_MATCH_MAX = 0.05
TARGET_DIFFERENCE_REVIEW_MAX = 0.15
CURRENT_PRICE_DIFFERENCE_MATCH_MAX = 0.02
CURRENT_PRICE_DIFFERENCE_REVIEW_MAX = 0.05
ANALYST_COUNT_DIFFERENCE_MATCH_MAX = 0.10
ANALYST_COUNT_DIFFERENCE_REVIEW_MAX = 0.25

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/151.0 Safari/537.36 VIA-CNYES-Consensus/1.0"
)

OUTPUT_DIR = "via_factset_yfinance_consensus_outputs"
OUTPUT_PAYLOAD_JSON = "factset_yfinance_consensus_payload.json"
OUTPUT_RAW_CSV = "factset_yfinance_consensus_raw.csv"
OUTPUT_RAW_PARQUET = "factset_yfinance_consensus_raw.parquet"
OUTPUT_MATRIX_CSV = "factset_yfinance_consensus_matrix.csv"
OUTPUT_QUALITY_CSV = "factset_yfinance_consensus_quality_matrix.csv"
OUTPUT_HTML = "factset_yfinance_consensus_matrix.html"
OUTPUT_MANIFEST_JSON = "factset_yfinance_consensus_manifest.json"
OUTPUT_LONG_CSV = "consensus_long_current.csv"
OUTPUT_LONG_PARQUET = "consensus_long_current.parquet"
OUTPUT_DUCKDB = "consensus_history.duckdb"
OUTPUT_CHECKPOINT = "consensus_checkpoint.json"
OUTPUT_CHECKPOINT_DIR = "consensus_checkpoint_payloads"

CSV_ENCODING = "utf-8-sig"
DATE_OUTPUT_FORMAT = "%Y/%m/%d"
DATETIME_OUTPUT_FORMAT = "%Y/%m/%d %H:%M:%S UTC"

PARQUET_REQUIRED = False
FAIL_CLOSED_ON_QUALITY_ERROR = True
DUCKDB_REQUIRED = True
ENABLE_CHECKPOINT_RESUME = True
CHECKPOINT_INCLUDE_UTC_DATE = True
CONSENSUS_TABLE_NAME = "consensus_long"
DUCKDB_BATCH_SIZE = 1000
TARGET_PRICE_WARN_DIFFERENCE_PCT = 0.15
EPS_WARN_DIFFERENCE_PCT = 0.10
REVENUE_WARN_DIFFERENCE_PCT = 0.10
DEPENDENCY_INSTALL_COMMAND = (
    'py -m pip install "numpy<2.0" "pandas<2.2" '
    '"yfinance==1.7.0" "duckdb==1.5.5" pyarrow'
)


# =============================================================================
# def 01 · IMPORTS
# =============================================================================

def def_import_libraries():
    import argparse
    import csv
    import hashlib
    import html
    import json
    import math
    import os
    import re
    import sys
    import time
    import traceback
    from datetime import datetime, timezone
    from pathlib import Path
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen

    return {
        "argparse": argparse,
        "csv": csv,
        "hashlib": hashlib,
        "html": html,
        "json": json,
        "math": math,
        "os": os,
        "re": re,
        "sys": sys,
        "time": time,
        "traceback": traceback,
        "datetime": datetime,
        "timezone": timezone,
        "Path": Path,
        "HTTPError": HTTPError,
        "URLError": URLError,
        "urlencode": urlencode,
        "Request": Request,
        "urlopen": urlopen,
    }


def def_runtime_dependency_report(live_mode=True):
    import importlib
    import importlib.util

    required = ["duckdb"] if DUCKDB_REQUIRED else []
    if live_mode:
        required.append("yfinance")
    optional = ["pandas", "pyarrow"]
    rows = []
    for package in list(dict.fromkeys(required + optional)):
        available = importlib.util.find_spec(package) is not None
        version = None
        if available:
            try:
                module = importlib.import_module(package)
                version = getattr(module, "__version__", None)
            except Exception:
                available = False
        rows.append({
            "package": package,
            "required": package in required,
            "available": available,
            "version": version,
        })
    missing_required = [
        row["package"]
        for row in rows
        if row["required"] and not row["available"]
    ]
    return {
        "status": "PASS" if not missing_required else "FAIL",
        "live_mode": bool(live_mode),
        "packages": rows,
        "missing_required": missing_required,
        "install_command": DEPENDENCY_INSTALL_COMMAND,
    }


def def_assert_runtime_dependencies(live_mode=True):
    report = def_runtime_dependency_report(live_mode=live_mode)
    if report["missing_required"]:
        raise RuntimeError(
            "MISSING_REQUIRED_PACKAGES: "
            f"{', '.join(report['missing_required'])}. "
            f"Install with: {report['install_command']}"
        )
    return report


# =============================================================================
# def 02 · GENERIC HELPERS
# =============================================================================

def def_now_utc():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


def def_now_utc_iso():
    return def_now_utc().isoformat()


def def_format_date(value):
    if value in [None, ""]:
        return None

    text = str(value).strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10].replace("-", "/")
    return text


def def_epoch_to_date(value):
    from datetime import datetime, timezone

    try:
        number = float(value)
        if number > 10_000_000_000:
            number = number / 1000.0
        return datetime.fromtimestamp(number, tz=timezone.utc).strftime(DATE_OUTPUT_FORMAT)
    except Exception:
        return None


def def_safe_float(value):
    if value is None or isinstance(value, bool):
        return None

    try:
        text = str(value).strip().replace(",", "")
        if text.lower() in {"", "none", "nan", "null", "n/a", "--", "-"}:
            return None
        number = float(text)
        if not __import__("math").isfinite(number):
            return None
        return number
    except Exception:
        return None


def def_safe_int(value):
    number = def_safe_float(value)
    if number is None:
        return None
    try:
        return int(number)
    except Exception:
        return None


def def_round(value, digits=4):
    number = def_safe_float(value)
    if number is None:
        return None
    return round(number, digits)


def def_ratio(numerator, denominator):
    n = def_safe_float(numerator)
    d = def_safe_float(denominator)
    if n is None or d in [None, 0.0]:
        return None
    return n / d


def def_sha256_bytes(data):
    import hashlib

    return hashlib.sha256(data).hexdigest()


def def_sha256_file(path):
    from pathlib import Path

    file_path = Path(path)
    return def_sha256_bytes(file_path.read_bytes())


def def_validate_code(code):
    import re

    text = str(code).strip().upper()
    text = re.sub(r"\.(TW|TWO)$", "", text)
    if not re.fullmatch(r"\d{4,6}", text):
        raise ValueError(f"INVALID_TW_STOCK_CODE: {code!r}")
    return text


def def_validate_codes(codes):
    normalized = []
    seen = set()

    for code in codes:
        clean = def_validate_code(code)
        if clean not in seen:
            normalized.append(clean)
            seen.add(clean)

    if not normalized:
        raise ValueError("NO_VALID_CODE")
    if len(normalized) > MAX_CODES_PER_RUN:
        raise ValueError(
            f"TOO_MANY_CODES: count={len(normalized)} max={MAX_CODES_PER_RUN}"
        )
    return normalized


def def_validate_yfinance_ticker(ticker):
    import re

    text = str(ticker or "").strip().upper()
    if not re.fullmatch(r"\d{4,6}\.(TW|TWO)", text):
        raise ValueError(f"INVALID_YFINANCE_TICKER: {ticker!r}")
    return text


def def_cnyes_symbol_to_yfinance_ticker(symbol, code):
    clean_code = def_validate_code(code)
    market = str(symbol or "").strip().upper().split(":", 1)[0]
    suffix_by_market = {
        "TWS": ".TW",
        "TWSE": ".TW",
        "TWO": ".TWO",
        "TPEX": ".TWO",
        "OTC": ".TWO",
    }
    suffix = suffix_by_market.get(market)
    if suffix is None:
        raise ValueError(
            f"UNSUPPORTED_CNYES_MARKET_FOR_YFINANCE: symbol={symbol!r}"
        )
    return def_validate_yfinance_ticker(f"{clean_code}{suffix}")


def def_normalize_rating_direction(value):
    import re

    text = re.sub(r"[^a-z]+", "_", str(value or "").strip().lower()).strip("_")
    positive = {
        "strong_buy",
        "buy",
        "outperform",
        "overweight",
        "positive",
    }
    neutral = {"hold", "neutral", "market_perform", "equal_weight"}
    negative = {
        "underperform",
        "underweight",
        "sell",
        "strong_sell",
        "negative",
    }
    if text in positive:
        return "POSITIVE"
    if text in neutral:
        return "NEUTRAL"
    if text in negative:
        return "NEGATIVE"
    return None


def def_cnyes_rating_direction(latest_rating):
    positive = def_safe_int((latest_rating or {}).get("positive_count")) or 0
    neutral = def_safe_int((latest_rating or {}).get("neutral_count")) or 0
    negative = def_safe_int((latest_rating or {}).get("negative_count")) or 0
    total = positive + neutral + negative
    if total <= 0:
        return None
    maximum = max(positive, neutral, negative)
    leaders = [
        label
        for label, count in [
            ("POSITIVE", positive),
            ("NEUTRAL", neutral),
            ("NEGATIVE", negative),
        ]
        if count == maximum
    ]
    return leaders[0] if len(leaders) == 1 else "MIXED"


def def_deep_get(data, keys, default=None):
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def def_json_ready(value):
    import math

    if value is None:
        return None
    if isinstance(value, dict):
        return {str(key): def_json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [def_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [def_json_ready(item) for item in value]
    if hasattr(value, "to_dict") and hasattr(value, "columns"):
        frame = value.reset_index()
        return [
            {str(key): def_json_ready(item) for key, item in row.items()}
            for row in frame.to_dict(orient="records")
        ]
    if hasattr(value, "to_dict") and not isinstance(value, (str, bytes)):
        return def_json_ready(value.to_dict())
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            return def_json_ready(value.item())
        except Exception:
            pass
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def def_display_metric_label(value):
    labels = {
        "CURRENT_PRICE": "目前股價",
        "TARGET_LOW": "目標價最低",
        "TARGET_MEAN": "目標價平均",
        "TARGET_MEDIAN": "目標價中位數",
        "TARGET_HIGH": "目標價最高",
        "ANALYST_COUNT": "分析師人數",
        "RATING": "評級方向",
    }
    text = str(value or "").strip()
    return labels.get(text.upper()) or def_display_identifier(text)


def def_display_status(value):
    labels = {
        "MATCH": "一致",
        "REVIEW": "檢視",
        "CONFLICT": "衝突",
        "INCOMPLETE": "不完整",
        "CURRENCY_MISMATCH": "幣別不一致",
        "PASS": "通過",
        "WARN": "警告",
        "FAIL": "失敗",
        "PASS_WITH_WARNINGS": "通過（含警告）",
        "FAIL_CLOSED": "失敗關閉",
    }
    text = str(value or "").strip()
    return labels.get(text.upper()) or def_display_identifier(text)


def def_display_rating_direction(value):
    labels = {
        "POSITIVE": "正向",
        "NEUTRAL": "中立",
        "NEGATIVE": "負向",
        "MIXED": "混合",
    }
    text = str(value or "").strip()
    return labels.get(text.upper()) or def_display_identifier(text)


def def_display_recommendation(value):
    labels = {
        "STRONG_BUY": "強力買進",
        "BUY": "買進",
        "HOLD": "持有",
        "UNDERPERFORM": "劣於大盤",
        "SELL": "賣出",
        "STRONG_SELL": "強力賣出",
    }
    text = str(value or "").strip()
    return labels.get(text.upper()) or def_display_identifier(text)


def def_display_source_mode(value):
    labels = {
        "API_PRIMARY": "API 主要來源",
        "SSR_FALLBACK": "SSR 備援",
        "YFINANCE_INFO_LIVE": "YFinance 即時資料",
        "YFINANCE_CONSENSUS_BUNDLE_LIVE": "YFinance 共識介面組",
        "OFFLINE_LIVE_FIXTURE": "FactSet 離線回歸樣本",
        "OFFLINE_YFINANCE_INFO_FIXTURE": "YFinance 離線回歸樣本",
        "CROSS_SOURCE_COMPARISON": "雙來源比較",
    }
    text = str(value or "").strip()
    return labels.get(text.upper()) or def_display_identifier(text)


def def_display_identifier(value):
    import re

    text = str(value or "").strip()
    if not text:
        return text
    if re.fullmatch(r"[A-Za-z0-9_]+", text):
        words = text.replace("_", " ").split()
        acronyms = {
            "api": "API", "cnyes": "FactSet", "eps": "EPS", "factset": "FactSet",
            "http": "HTTP", "pe": "P/E", "pct": "%", "ssr": "SSR",
            "utc": "UTC", "url": "URL", "yf": "YFinance", "yfinance": "YFinance",
        }
        return " ".join(acronyms.get(word.lower(), word.capitalize()) for word in words)
    return text


def def_display_text(value):
    if isinstance(value, list):
        return "、".join(def_display_text(item) for item in value)
    if isinstance(value, dict):
        return "；".join(
            f"{def_display_identifier(key)}：{def_display_text(item)}"
            for key, item in value.items()
        )
    text = str(value or "").strip()
    upper = text.upper()
    phrases = {
        "MATCH OR REVIEW": "一致或檢視",
        "LOW <= MEDIAN <= HIGH": "最低 ≤ 中位數 ≤ 最高",
        "SAME NON-EMPTY CURRENCY": "相同且非空白的幣別",
        "BOTH NORMALIZED": "兩者皆已正規化",
        "ALL EQUAL": "全部相等",
    }
    if upper in phrases:
        return phrases[upper]
    if upper in {
        "MATCH", "REVIEW", "CONFLICT", "INCOMPLETE", "CURRENCY_MISMATCH",
        "PASS", "WARN", "FAIL", "PASS_WITH_WARNINGS", "FAIL_CLOSED",
    }:
        return def_display_status(text)
    if upper in {"POSITIVE", "NEUTRAL", "NEGATIVE", "MIXED"}:
        return def_display_rating_direction(text)
    return def_display_identifier(text)


def def_display_sentence(value):
    import re

    text = str(value or "").strip()
    text = re.sub(r"\byfinance\b", "YFinance", text, flags=re.IGNORECASE)
    if not text:
        return text
    return text[:1].upper() + text[1:]


# =============================================================================
# def 03 · HTTP WITH RETRY
# =============================================================================

def def_build_headers(referer=None):
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": referer or "https://www.cnyes.com/",
    }


def def_http_get(url, referer=None, timeout=None, retries=None):
    import time
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    timeout_value = timeout or REQUEST_TIMEOUT_SECONDS
    retry_count = REQUEST_RETRIES if retries is None else retries
    last_error = None

    for attempt in range(retry_count):
        try:
            request = Request(url, headers=def_build_headers(referer=referer))
            with urlopen(request, timeout=timeout_value) as response:
                body = response.read()
                status = int(getattr(response, "status", 200))
                final_url = str(getattr(response, "url", url))
                headers = dict(response.headers.items())
                if status != 200:
                    raise RuntimeError(f"HTTP_STATUS_{status}: {final_url}")
                return {
                    "status": status,
                    "url": final_url,
                    "headers": headers,
                    "body": body,
                    "sha256": def_sha256_bytes(body),
                    "attempt": attempt + 1,
                }
        except HTTPError as exc:
            last_error = exc
            retryable = exc.code in {408, 425, 429, 500, 502, 503, 504}
            if not retryable or attempt + 1 >= retry_count:
                break
        except (URLError, TimeoutError, OSError, RuntimeError) as exc:
            last_error = exc
            if attempt + 1 >= retry_count:
                break

        time.sleep(REQUEST_BACKOFF_SECONDS * (2 ** attempt))

    raise RuntimeError(f"HTTP_GET_FAILED: url={url} error={last_error}")


def def_http_get_text(url, referer=None):
    response = def_http_get(url=url, referer=referer)
    content_type = str(response["headers"].get("Content-Type", ""))
    charset = "utf-8"
    if "charset=" in content_type.lower():
        charset = content_type.lower().split("charset=", 1)[1].split(";", 1)[0].strip()
    try:
        text = response["body"].decode(charset, errors="replace")
    except LookupError:
        text = response["body"].decode("utf-8", errors="replace")
    return response, text


def def_http_get_json(url, referer=None):
    import json

    response, text = def_http_get_text(url=url, referer=referer)
    try:
        payload = json.loads(text)
    except Exception as exc:
        raise RuntimeError(
            f"JSON_DECODE_FAILED: url={url} error={exc} prefix={text[:160]!r}"
        ) from exc
    return response, payload


# =============================================================================
# def 04 · PAGE EMBEDDED JSON PARSER
# =============================================================================

def def_extract_assigned_json(html_text, variable_name):
    import json
    import re

    pattern = re.compile(rf"\b{re.escape(variable_name)}\s*=\s*")
    match = pattern.search(html_text)
    if not match:
        raise ValueError(f"ASSIGNED_JSON_NOT_FOUND: {variable_name}")

    raw = html_text[match.end():].lstrip()
    value, _ = json.JSONDecoder().raw_decode(raw)
    return value


def def_extract_next_data(html_text):
    next_data = def_extract_assigned_json(html_text, "__NEXT_DATA__")
    if not isinstance(next_data, dict):
        raise ValueError("NEXT_DATA_NOT_OBJECT")
    return next_data


def def_extract_env(html_text):
    try:
        env = def_extract_assigned_json(html_text, "__ENV__")
        return env if isinstance(env, dict) else {}
    except Exception:
        return {}


def def_extract_page_props(next_data):
    page_props = def_deep_get(next_data, ["props", "pageProps"], default={})
    if not isinstance(page_props, dict):
        raise ValueError("PAGE_PROPS_NOT_OBJECT")
    return page_props


# =============================================================================
# def 05 · SOURCE FETCHERS
# =============================================================================

def def_build_api_url(base_url, path, query=None):
    from urllib.parse import urlencode

    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    if query:
        url = f"{url}?{urlencode(query)}"
    return url


def def_validate_api_envelope(payload, source_name):
    if not isinstance(payload, dict):
        raise ValueError(f"{source_name}_PAYLOAD_NOT_OBJECT")

    status_code = def_safe_int(payload.get("statusCode"))
    if status_code != 200:
        raise ValueError(
            f"{source_name}_STATUS_NOT_200: statusCode={status_code} "
            f"message={payload.get('message')}"
        )
    return payload.get("data")


def def_fetch_page_bundle(code):
    page_url = CNYES_PAGE_TEMPLATE.format(code=code)
    response, html_text = def_http_get_text(url=page_url)
    next_data = def_extract_next_data(html_text)
    page_props = def_extract_page_props(next_data)
    env = def_extract_env(html_text)

    return {
        "page_url": page_url,
        "final_url": response["url"],
        "http_status": response["status"],
        "html_sha256": response["sha256"],
        "next_data": next_data,
        "page_props": page_props,
        "env": env,
    }


def def_fetch_endpoint(base_url, path, page_url, query=None, source_name="API"):
    url = def_build_api_url(base_url=base_url, path=path, query=query)
    response, payload = def_http_get_json(url=url, referer=page_url)
    data = def_validate_api_envelope(payload=payload, source_name=source_name)
    return {
        "url": url,
        "http_status": response["status"],
        "sha256": response["sha256"],
        "payload": payload,
        "data": data,
    }


def def_fetch_target_valuation(base_url, symbol, page_url, ssr_fallback):
    path = TARGET_PRICE_PATH.format(symbol=symbol)
    try:
        result = def_fetch_endpoint(
            base_url=base_url,
            path=path,
            page_url=page_url,
            source_name="TARGET_PRICE",
        )
        result["source_mode"] = "API_PRIMARY"
        return result
    except Exception as exc:
        if isinstance(ssr_fallback, dict) and ssr_fallback:
            return {
                "url": page_url,
                "http_status": 200,
                "sha256": None,
                "payload": {"statusCode": 200, "message": "SSR_FALLBACK"},
                "data": ssr_fallback,
                "source_mode": "SSR_FALLBACK",
                "primary_error": str(exc),
            }
        raise


def def_fetch_factset_rating(base_url, symbol, page_url, ssr_fallback):
    path = FACTSET_RATING_PATH.format(symbol=symbol)
    try:
        result = def_fetch_endpoint(
            base_url=base_url,
            path=path,
            page_url=page_url,
            source_name="FACTSET_RATING",
        )
        result["source_mode"] = "API_PRIMARY"
        return result
    except Exception as exc:
        if isinstance(ssr_fallback, dict) and ssr_fallback:
            return {
                "url": page_url,
                "http_status": 200,
                "sha256": None,
                "payload": {"statusCode": 200, "message": "SSR_FALLBACK"},
                "data": ssr_fallback,
                "source_mode": "SSR_FALLBACK",
                "primary_error": str(exc),
            }
        raise


def def_fetch_estimate_profit(base_url, symbol, page_url, estimate_type):
    if estimate_type not in {"eps", "sales"}:
        raise ValueError(f"UNSUPPORTED_ESTIMATE_TYPE: {estimate_type}")
    path = ESTIMATE_PROFIT_PATH.format(symbol=symbol)
    result = def_fetch_endpoint(
        base_url=base_url,
        path=path,
        page_url=page_url,
        query={"type": estimate_type},
        source_name=f"ESTIMATE_{estimate_type.upper()}",
    )
    if not isinstance(result["data"], list):
        raise ValueError(f"ESTIMATE_{estimate_type.upper()}_DATA_NOT_LIST")
    result["source_mode"] = "API_PRIMARY"
    return result


def def_call_yfinance_analysis_methods(ticker_object):
    analysis = {}
    method_status = {}

    for method_name in YFINANCE_ANALYSIS_METHODS:
        method = getattr(ticker_object, method_name, None)
        if not callable(method):
            method_status[method_name] = {
                "status": "UNAVAILABLE",
                "error": "METHOD_NOT_AVAILABLE_IN_INSTALLED_YFINANCE",
            }
            analysis[method_name] = None
            continue
        try:
            value = def_json_ready(method())
            has_data = value not in [None, {}, []]
            method_status[method_name] = {
                "status": "PASS" if has_data else "NO_COVERAGE",
                "error": None,
            }
            analysis[method_name] = value
        except Exception as exc:
            method_status[method_name] = {
                "status": "ERROR",
                "error": f"{type(exc).__name__}: {exc}",
            }
            analysis[method_name] = None

    return analysis, method_status


def def_merge_yfinance_price_targets(selected, analysis):
    targets = analysis.get("get_analyst_price_targets")
    if not isinstance(targets, dict):
        return selected

    mappings = {
        "currentPrice": ["current", "currentPrice"],
        "targetLowPrice": ["low", "targetLowPrice"],
        "targetMeanPrice": ["mean", "targetMeanPrice"],
        "targetMedianPrice": ["median", "targetMedianPrice"],
        "targetHighPrice": ["high", "targetHighPrice"],
    }
    merged = dict(selected)
    for destination, candidates in mappings.items():
        if merged.get(destination) is not None:
            continue
        for candidate in candidates:
            if targets.get(candidate) is not None:
                merged[destination] = targets.get(candidate)
                break
    return merged


def def_fetch_yfinance_info(yfinance_ticker):
    import time

    ticker = def_validate_yfinance_ticker(yfinance_ticker)
    try:
        import yfinance as yf
    except Exception as exc:
        raise RuntimeError(
            "YFINANCE_IMPORT_FAILED: install with 'py -m pip install yfinance'"
        ) from exc

    last_error = None
    for attempt in range(YFINANCE_REQUEST_RETRIES):
        try:
            ticker_object = yf.Ticker(ticker)
            info = ticker_object.info
            if not isinstance(info, dict) or not info:
                raise ValueError("YFINANCE_INFO_EMPTY_OR_NOT_DICT")
            selected = {field: info.get(field) for field in YFINANCE_INFO_FIELDS}
            analysis, method_status = def_call_yfinance_analysis_methods(
                ticker_object
            )
            selected = def_merge_yfinance_price_targets(selected, analysis)
            adj_close = None
            adj_close_source = None
            try:
                history = ticker_object.history(
                    period=YFINANCE_HISTORY_PERIOD,
                    auto_adjust=False,
                    actions=False,
                )
                if history is not None and hasattr(history, "columns"):
                    for column in ["Adj Close", "Close"]:
                        if column in history.columns:
                            series = history[column].dropna()
                            if len(series) > 0:
                                adj_close = def_safe_float(series.iloc[-1])
                                adj_close_source = column
                                break
            except Exception:
                adj_close = None
                adj_close_source = None
            if adj_close is None:
                adj_close = def_safe_float(
                    info.get("currentPrice")
                    if info.get("currentPrice") is not None
                    else info.get("regularMarketPrice")
                )
                adj_close_source = "INFO_PRICE_FALLBACK"
            selected["adjClose"] = adj_close
            core_coverage = any(
                selected.get(field) is not None
                for field in [
                    "targetLowPrice",
                    "targetMeanPrice",
                    "targetMedianPrice",
                    "targetHighPrice",
                    "recommendationKey",
                ]
            )
            analysis_coverage = any(
                value not in [None, {}, []] for value in analysis.values()
            )
            return {
                "url": YFINANCE_SOURCE_URL_TEMPLATE.format(ticker=ticker),
                "http_status": 200,
                "sha256": def_sha256_bytes(
                    __import__("json").dumps(
                        def_json_ready({
                            "info": selected,
                            "analysis": analysis,
                            "method_status": method_status,
                        }),
                        ensure_ascii=False,
                        sort_keys=True,
                    ).encode("utf-8")
                ),
                "data": selected,
                "analysis": analysis,
                "method_status": method_status,
                "coverage_status": (
                    "COVERED" if core_coverage or analysis_coverage else "NO_COVERAGE"
                ),
                "source_mode": "YFINANCE_CONSENSUS_BUNDLE_LIVE",
                "captured_at_utc": def_now_utc_iso(),
                "yfinance_version": getattr(yf, "__version__", None),
                "adj_close_source": adj_close_source,
                "attempt": attempt + 1,
            }
        except Exception as exc:
            last_error = exc
            if attempt + 1 < YFINANCE_REQUEST_RETRIES:
                time.sleep(YFINANCE_RETRY_SLEEP_SECONDS * (attempt + 1))

    raise RuntimeError(
        f"YFINANCE_INFO_FETCH_FAILED: ticker={ticker} error={last_error}"
    )


# =============================================================================
# def 06 · NORMALIZATION
# =============================================================================

def def_normalize_target(code, symbol, page_url, source_result):
    data = source_result.get("data") or {}
    current_price = def_safe_float(data.get("last"))
    target_low = def_safe_float(data.get("feLow"))
    target_mean = def_safe_float(data.get("feMean"))
    target_median = def_safe_float(data.get("feMedian"))
    target_high = def_safe_float(data.get("feHigh"))

    return {
        "code": code,
        "symbol": symbol,
        "company_name": data.get("chName"),
        "rate_date": def_format_date(data.get("rateDate")),
        "current_price": current_price,
        "target_low": target_low,
        "target_mean": target_mean,
        "target_median": target_median,
        "target_high": target_high,
        "target_low_upside_pct": def_round(
            (def_ratio(target_low, current_price) - 1)
            if def_ratio(target_low, current_price) is not None
            else None,
            6,
        ),
        "target_mean_upside_pct": def_round(
            (def_ratio(target_mean, current_price) - 1)
            if def_ratio(target_mean, current_price) is not None
            else None,
            6,
        ),
        "target_median_upside_pct": def_round(
            (def_ratio(target_median, current_price) - 1)
            if def_ratio(target_median, current_price) is not None
            else None,
            6,
        ),
        "target_high_upside_pct": def_round(
            (def_ratio(target_high, current_price) - 1)
            if def_ratio(target_high, current_price) is not None
            else None,
            6,
        ),
        "target_std_dev": def_safe_float(data.get("feStdDev")),
        "target_up_revisions": def_safe_int(data.get("feUp")),
        "target_down_revisions": def_safe_int(data.get("feDown")),
        "analyst_count": def_safe_int(data.get("numEst")),
        "currency": data.get("currency"),
        "source": "FactSet",
        "source_mode": source_result.get("source_mode"),
        "source_url": source_result.get("url") or page_url,
    }


def def_normalize_yfinance_consensus(
    code,
    symbol,
    yfinance_ticker,
    source_result,
):
    data = source_result.get("data") or {}
    ticker = def_validate_yfinance_ticker(yfinance_ticker)
    current_price = def_safe_float(
        data.get("currentPrice")
        if data.get("currentPrice") is not None
        else data.get("regularMarketPrice")
    )
    adj_close = def_safe_float(data.get("adjClose"))
    if adj_close is None:
        adj_close = current_price
    beta = def_safe_float(data.get("beta"))
    target_low = def_safe_float(data.get("targetLowPrice"))
    target_mean = def_safe_float(data.get("targetMeanPrice"))
    target_median = def_safe_float(data.get("targetMedianPrice"))
    target_high = def_safe_float(data.get("targetHighPrice"))
    recommendation_key = str(data.get("recommendationKey") or "").strip() or None

    def def_upside(value):
        ratio = def_ratio(value, current_price)
        return def_round(ratio - 1, 6) if ratio is not None else None

    def def_upside_vs_adj_close(value):
        ratio = def_ratio(value, adj_close)
        return def_round(ratio - 1, 6) if ratio is not None else None

    return {
        "code": code,
        "symbol": symbol,
        "yfinance_ticker": ticker,
        "company_name": data.get("longName") or data.get("shortName"),
        "captured_at_utc": source_result.get("captured_at_utc") or def_now_utc_iso(),
        "current_price": current_price,
        "adj_close": adj_close,
        "adj_close_source": source_result.get("adj_close_source"),
        "beta": beta,
        "target_low": target_low,
        "target_mean": target_mean,
        "target_median": target_median,
        "target_high": target_high,
        "target_low_upside_pct": def_upside(target_low),
        "target_mean_upside_pct": def_upside(target_mean),
        "target_median_upside_pct": def_upside(target_median),
        "target_high_upside_pct": def_upside(target_high),
        "target_low_upside_vs_adj_close_pct": def_upside_vs_adj_close(target_low),
        "target_mean_upside_vs_adj_close_pct": def_upside_vs_adj_close(target_mean),
        "target_median_upside_vs_adj_close_pct": def_upside_vs_adj_close(target_median),
        "target_high_upside_vs_adj_close_pct": def_upside_vs_adj_close(target_high),
        "analyst_count": def_safe_int(data.get("numberOfAnalystOpinions")),
        "recommendation_mean": def_safe_float(data.get("recommendationMean")),
        "recommendation_key": recommendation_key,
        "rating_direction": def_normalize_rating_direction(recommendation_key),
        "currency": data.get("currency"),
        "source": "YFinance",
        "source_mode": source_result.get("source_mode"),
        "source_url": source_result.get("url")
        or YFINANCE_SOURCE_URL_TEMPLATE.format(ticker=ticker),
        "yfinance_version": source_result.get("yfinance_version"),
    }


def def_classify_numeric_difference(
    cnyes_value,
    yfinance_value,
    match_max=TARGET_DIFFERENCE_MATCH_MAX,
    review_max=TARGET_DIFFERENCE_REVIEW_MAX,
):
    cnyes_number = def_safe_float(cnyes_value)
    yfinance_number = def_safe_float(yfinance_value)
    if cnyes_number is None or yfinance_number is None:
        return {
            "difference": None,
            "difference_pct": None,
            "abs_difference_pct": None,
            "status": "INCOMPLETE",
        }
    difference = yfinance_number - cnyes_number
    ratio = def_ratio(difference, cnyes_number)
    difference_pct = def_round(ratio, 6)
    abs_difference_pct = abs(difference_pct) if difference_pct is not None else None
    if abs_difference_pct is not None and abs_difference_pct <= match_max:
        status = "MATCH"
    elif abs_difference_pct is not None and abs_difference_pct <= review_max:
        status = "REVIEW"
    else:
        status = "CONFLICT"
    return {
        "difference": def_round(difference, 6),
        "difference_pct": difference_pct,
        "abs_difference_pct": abs_difference_pct,
        "status": status,
    }


def def_build_source_comparison(target, latest_rating, yfinance_consensus):
    cnyes_currency = str((target or {}).get("currency") or "").upper() or None
    yfinance_currency = str(
        (yfinance_consensus or {}).get("currency") or ""
    ).upper() or None
    currencies_match = (
        cnyes_currency is not None
        and yfinance_currency is not None
        and cnyes_currency == yfinance_currency
    )
    metrics = []
    numeric_specs = [
        (
            "CURRENT_PRICE",
            "current_price",
            CURRENT_PRICE_DIFFERENCE_MATCH_MAX,
            CURRENT_PRICE_DIFFERENCE_REVIEW_MAX,
        ),
        (
            "TARGET_LOW",
            "target_low",
            TARGET_DIFFERENCE_MATCH_MAX,
            TARGET_DIFFERENCE_REVIEW_MAX,
        ),
        (
            "TARGET_MEAN",
            "target_mean",
            TARGET_DIFFERENCE_MATCH_MAX,
            TARGET_DIFFERENCE_REVIEW_MAX,
        ),
        (
            "TARGET_MEDIAN",
            "target_median",
            TARGET_DIFFERENCE_MATCH_MAX,
            TARGET_DIFFERENCE_REVIEW_MAX,
        ),
        (
            "TARGET_HIGH",
            "target_high",
            TARGET_DIFFERENCE_MATCH_MAX,
            TARGET_DIFFERENCE_REVIEW_MAX,
        ),
        (
            "ANALYST_COUNT",
            "analyst_count",
            ANALYST_COUNT_DIFFERENCE_MATCH_MAX,
            ANALYST_COUNT_DIFFERENCE_REVIEW_MAX,
        ),
    ]
    for metric, key, match_max, review_max in numeric_specs:
        difference = def_classify_numeric_difference(
            (target or {}).get(key),
            (yfinance_consensus or {}).get(key),
            match_max=match_max,
            review_max=review_max,
        )
        if metric != "ANALYST_COUNT" and not currencies_match:
            difference["status"] = "CURRENCY_MISMATCH"
        metrics.append({
            "metric": metric,
            "metric_label": def_display_metric_label(metric),
            "cnyes_value": (target or {}).get(key),
            "yfinance_value": (yfinance_consensus or {}).get(key),
            **difference,
            "status_label": def_display_status(difference.get("status")),
            "cnyes_currency": cnyes_currency,
            "yfinance_currency": yfinance_currency,
        })

    cnyes_rating = def_cnyes_rating_direction(latest_rating)
    yfinance_rating = (yfinance_consensus or {}).get("rating_direction")
    if cnyes_rating is None or yfinance_rating is None:
        rating_status = "INCOMPLETE"
    elif cnyes_rating == yfinance_rating:
        rating_status = "MATCH"
    else:
        rating_status = "CONFLICT"
    metrics.append({
        "metric": "RATING",
        "metric_label": def_display_metric_label("RATING"),
        "cnyes_value": cnyes_rating,
        "yfinance_value": yfinance_rating,
        "difference": None,
        "difference_pct": None,
        "abs_difference_pct": None,
        "status": rating_status,
        "status_label": def_display_status(rating_status),
        "cnyes_currency": None,
        "yfinance_currency": None,
    })

    statuses = [item.get("status") for item in metrics]
    if any(status in {"CONFLICT", "CURRENCY_MISMATCH"} for status in statuses):
        agreement_gate = "CONFLICT"
    elif "INCOMPLETE" in statuses:
        agreement_gate = "INCOMPLETE"
    elif "REVIEW" in statuses:
        agreement_gate = "REVIEW"
    else:
        agreement_gate = "MATCH"
    return {
        "agreement_gate": agreement_gate,
        "agreement_gate_label": def_display_status(agreement_gate),
        "currencies_match": currencies_match,
        "cnyes_currency": cnyes_currency,
        "yfinance_currency": yfinance_currency,
        "match_count": statuses.count("MATCH"),
        "review_count": statuses.count("REVIEW"),
        "conflict_count": sum(
            status in {"CONFLICT", "CURRENCY_MISMATCH"} for status in statuses
        ),
        "incomplete_count": statuses.count("INCOMPLETE"),
        "metrics": metrics,
    }


def def_build_target_spectrum(target, yfinance_consensus):
    target = target or {}
    yfinance_consensus = yfinance_consensus or {}
    adj_close = def_safe_float(yfinance_consensus.get("adj_close"))
    if adj_close is None:
        adj_close = def_safe_float(yfinance_consensus.get("current_price"))
    if adj_close is None:
        adj_close = def_safe_float(target.get("current_price"))

    source_specs = [
        ("FactSet", target),
        ("YFinance", yfinance_consensus),
    ]
    all_values = [adj_close]
    for _source_name, source in source_specs:
        all_values.extend(
            def_safe_float(source.get(field))
            for field in ["target_low", "target_mean", "target_median", "target_high"]
        )
    all_values = [value for value in all_values if value is not None]
    if not all_values:
        return {
            "status": "INCOMPLETE",
            "adj_close": None,
            "beta": def_safe_float(yfinance_consensus.get("beta")),
            "sources": [],
        }

    raw_min = min(all_values)
    raw_max = max(all_values)
    span = raw_max - raw_min
    padding = (
        span * TARGET_SPECTRUM_DOMAIN_PADDING_PCT
        if span > 0
        else max(abs(raw_max) * 0.03, 1.0)
    )
    domain_min = raw_min - padding
    domain_max = raw_max + padding
    domain_span = domain_max - domain_min

    def def_position(value):
        number = def_safe_float(value)
        if number is None or domain_span <= 0:
            return None
        return def_round((number - domain_min) / domain_span, 6)

    def def_upside(value):
        ratio = def_ratio(value, adj_close)
        return def_round(ratio - 1, 6) if ratio is not None else None

    sources = []
    for source_name, source in source_specs:
        low = def_safe_float(source.get("target_low"))
        mean = def_safe_float(source.get("target_mean"))
        median = def_safe_float(source.get("target_median"))
        high = def_safe_float(source.get("target_high"))
        source_complete = all(
            value is not None for value in [low, mean, median, high]
        )
        sources.append({
            "source": source_name,
            "currency": source.get("currency") or target.get("currency"),
            "low": low,
            "mean": mean,
            "median": median,
            "high": high,
            "low_position": def_position(low),
            "mean_position": def_position(mean),
            "median_position": def_position(median),
            "high_position": def_position(high),
            "mean_upside_vs_adj_close_pct": def_upside(mean),
            "median_upside_vs_adj_close_pct": def_upside(median),
            "complete": source_complete,
        })

    complete = (
        adj_close is not None
        and all(source.get("complete") for source in sources)
        and all(
            source.get("low") <= source.get("median") <= source.get("high")
            for source in sources
        )
        and all(
            source.get("low") <= source.get("mean") <= source.get("high")
            for source in sources
        )
    )
    return {
        "status": "PASS" if complete else "INCOMPLETE",
        "domain_min": def_round(domain_min, 6),
        "domain_max": def_round(domain_max, 6),
        "adj_close": adj_close,
        "adj_close_position": def_position(adj_close),
        "beta": def_safe_float(yfinance_consensus.get("beta")),
        "currency": yfinance_consensus.get("currency") or target.get("currency"),
        "colors": dict(TARGET_SPECTRUM_COLORS),
        "markers": dict(TARGET_SPECTRUM_MARKERS),
        "sources": sources,
    }


def def_rating_array_fields():
    return [
        "rateDate",
        "feMark",
        "feBuy",
        "feOver",
        "feHold",
        "feUnder",
        "feSell",
        "feMedian",
    ]


def def_normalize_rating_history(code, symbol, page_url, source_result):
    data = source_result.get("data") or {}
    fields = def_rating_array_fields()
    lengths = {
        field: len(data.get(field, []))
        for field in fields
        if isinstance(data.get(field), list)
    }
    row_count = max(lengths.values(), default=0)
    rows = []

    for index in range(row_count):
        values = {
            field: data.get(field, [])[index]
            if index < len(data.get(field, []))
            else None
            for field in fields
        }
        buy = def_safe_int(values.get("feBuy")) or 0
        over = def_safe_int(values.get("feOver")) or 0
        hold = def_safe_int(values.get("feHold")) or 0
        under = def_safe_int(values.get("feUnder")) or 0
        sell = def_safe_int(values.get("feSell")) or 0
        analyst_count = buy + over + hold + under + sell

        rows.append({
            "code": code,
            "symbol": symbol,
            "company_name": data.get("chName"),
            "rating_date": def_epoch_to_date(values.get("rateDate")),
            "rating_mark": def_safe_float(values.get("feMark")),
            "buy_count": buy,
            "outperform_count": over,
            "hold_count": hold,
            "underperform_count": under,
            "sell_count": sell,
            "positive_count": buy + over,
            "neutral_count": hold,
            "negative_count": under + sell,
            "analyst_count": analyst_count,
            "target_median": def_safe_float(values.get("feMedian")),
            "currency": data.get("currency"),
            "source": "FactSet",
            "source_mode": source_result.get("source_mode"),
            "source_url": source_result.get("url") or page_url,
            "array_lengths": lengths,
        })

    rows.sort(key=lambda row: row.get("rating_date") or "", reverse=True)
    return rows


def def_normalize_estimate_rows(
    code,
    symbol,
    page_url,
    source_result,
    estimate_type,
    current_price,
):
    rows = []
    for item in source_result.get("data") or []:
        if not isinstance(item, dict):
            continue
        median = def_safe_float(item.get("feMedian"))
        forward_pe = None
        if estimate_type == "eps":
            forward_pe = def_ratio(current_price, median)

        rows.append({
            "code": code,
            "symbol": symbol,
            "company_name": None,
            "estimate_type": estimate_type.upper(),
            "fiscal_year": def_safe_int(item.get("financialYear")),
            "rate_date": def_format_date(item.get("rateDate")),
            "estimate_low": def_safe_float(item.get("feLow")),
            "estimate_mean": def_safe_float(item.get("feMean")),
            "estimate_median": median,
            "estimate_high": def_safe_float(item.get("feHigh")),
            "estimate_std_dev": def_safe_float(item.get("feStdDev")),
            "up_revisions": def_safe_int(item.get("feUp")),
            "down_revisions": def_safe_int(item.get("feDown")),
            "analyst_count": def_safe_int(item.get("numEst")),
            "currency": item.get("currency"),
            "current_price": current_price,
            "forward_pe_median": def_round(forward_pe, 6),
            "source": "FactSet",
            "source_mode": source_result.get("source_mode"),
            "source_url": source_result.get("url") or page_url,
        })

    rows.sort(key=lambda row: row.get("fiscal_year") or 0)
    return rows


def def_fetch_one_code(code):
    import time

    fetched_at = def_now_utc_iso()
    page = def_fetch_page_bundle(code=code)
    page_props = page["page_props"]
    symbol = str(page_props.get("symbol") or "").strip()
    if not symbol:
        raise ValueError(f"SYMBOL_NOT_FOUND_IN_PAGE: code={code}")

    symbol_parts = symbol.split(":")
    if len(symbol_parts) < 2 or symbol_parts[1] != code:
        raise ValueError(f"SYMBOL_CODE_MISMATCH: code={code} symbol={symbol}")

    base_url = str(
        page.get("env", {}).get("marketInfoApiUrl")
        or DEFAULT_MARKET_INFO_API_URL
    ).strip()

    target_result = def_fetch_target_valuation(
        base_url=base_url,
        symbol=symbol,
        page_url=page["page_url"],
        ssr_fallback=page_props.get("targetValuation"),
    )
    rating_result = def_fetch_factset_rating(
        base_url=base_url,
        symbol=symbol,
        page_url=page["page_url"],
        ssr_fallback=page_props.get("factSetEstimate"),
    )
    eps_result = def_fetch_estimate_profit(
        base_url=base_url,
        symbol=symbol,
        page_url=page["page_url"],
        estimate_type="eps",
    )
    sales_result = def_fetch_estimate_profit(
        base_url=base_url,
        symbol=symbol,
        page_url=page["page_url"],
        estimate_type="sales",
    )
    yfinance_ticker = def_cnyes_symbol_to_yfinance_ticker(symbol, code)
    yfinance_result = def_fetch_yfinance_info(yfinance_ticker)

    target = def_normalize_target(
        code=code,
        symbol=symbol,
        page_url=page["page_url"],
        source_result=target_result,
    )
    rating_history = def_normalize_rating_history(
        code=code,
        symbol=symbol,
        page_url=page["page_url"],
        source_result=rating_result,
    )
    eps_rows = def_normalize_estimate_rows(
        code=code,
        symbol=symbol,
        page_url=page["page_url"],
        source_result=eps_result,
        estimate_type="eps",
        current_price=target.get("current_price"),
    )
    sales_rows = def_normalize_estimate_rows(
        code=code,
        symbol=symbol,
        page_url=page["page_url"],
        source_result=sales_result,
        estimate_type="sales",
        current_price=target.get("current_price"),
    )
    yfinance_consensus = def_normalize_yfinance_consensus(
        code=code,
        symbol=symbol,
        yfinance_ticker=yfinance_ticker,
        source_result=yfinance_result,
    )
    source_comparison = def_build_source_comparison(
        target=target,
        latest_rating=rating_history[0] if rating_history else {},
        yfinance_consensus=yfinance_consensus,
    )
    target_spectrum = def_build_target_spectrum(target, yfinance_consensus)

    company_name = target.get("company_name") or def_deep_get(
        page_props, ["companyProfile", "companyName"], default=None
    )
    for row in rating_history + eps_rows + sales_rows:
        row["company_name"] = company_name

    endpoint_meta = {
        "page": {
            "url": page["page_url"],
            "status": page["http_status"],
            "sha256": page["html_sha256"],
        },
        "target": {
            "url": target_result.get("url"),
            "status": target_result.get("http_status"),
            "sha256": target_result.get("sha256"),
            "mode": target_result.get("source_mode"),
        },
        "rating": {
            "url": rating_result.get("url"),
            "status": rating_result.get("http_status"),
            "sha256": rating_result.get("sha256"),
            "mode": rating_result.get("source_mode"),
        },
        "eps": {
            "url": eps_result.get("url"),
            "status": eps_result.get("http_status"),
            "sha256": eps_result.get("sha256"),
            "mode": eps_result.get("source_mode"),
        },
        "sales": {
            "url": sales_result.get("url"),
            "status": sales_result.get("http_status"),
            "sha256": sales_result.get("sha256"),
            "mode": sales_result.get("source_mode"),
        },
        "yfinance": {
            "url": yfinance_result.get("url"),
            "status": yfinance_result.get("http_status"),
            "sha256": yfinance_result.get("sha256"),
            "mode": yfinance_result.get("source_mode"),
            "version": yfinance_result.get("yfinance_version"),
            "coverage_status": yfinance_result.get("coverage_status"),
            "method_status": yfinance_result.get("method_status") or {},
        },
    }

    time.sleep(REQUEST_SLEEP_SECONDS)
    return {
        "code": code,
        "symbol": symbol,
        "company_name": company_name,
        "fetched_at_utc": fetched_at,
        "page_url": page["page_url"],
        "market_info_api_url": base_url,
        "target": target,
        "yfinance": yfinance_consensus,
        "yfinance_analysis": yfinance_result.get("analysis") or {},
        "source_comparison": source_comparison,
        "target_spectrum": target_spectrum,
        "rating_history": rating_history,
        "eps": eps_rows,
        "sales": sales_rows,
        "endpoint_meta": endpoint_meta,
    }


def def_load_fixture(path):
    import json
    from pathlib import Path

    fixture_path = Path(path)
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"FIXTURE_NOT_OBJECT: {fixture_path}")
    code = def_validate_code(data.get("code"))
    data["code"] = code
    data["fixture_path"] = str(fixture_path.resolve())
    return data


def def_load_fixture_map(paths):
    fixture_map = {}
    for path in paths or []:
        fixture = def_load_fixture(path)
        code = fixture["code"]
        if code in fixture_map:
            raise ValueError(f"DUPLICATE_FIXTURE_CODE: {code}")
        fixture_map[code] = fixture
    return fixture_map


def def_fixture_source_result(fixture, key):
    source = fixture.get(key) or {}
    payload = source.get("payload") or {}
    data = def_validate_api_envelope(payload, f"FIXTURE_{key.upper()}")
    return {
        "url": source.get("url"),
        "http_status": def_safe_int(source.get("http_status")) or 200,
        "sha256": source.get("sha256") or "OFFLINE_FIXTURE",
        "payload": payload,
        "data": data,
        "source_mode": "OFFLINE_LIVE_FIXTURE",
    }


def def_fixture_yfinance_source_result(fixture, yfinance_ticker):
    source = fixture.get("yfinance_info") or {}
    data = source.get("info") or source.get("data") or {}
    if not isinstance(data, dict) or not data:
        raise ValueError("FIXTURE_YFINANCE_INFO_MISSING")
    ticker = def_validate_yfinance_ticker(
        source.get("ticker") or yfinance_ticker
    )
    if ticker != def_validate_yfinance_ticker(yfinance_ticker):
        raise ValueError(
            f"FIXTURE_YFINANCE_TICKER_MISMATCH: {ticker} != {yfinance_ticker}"
        )
    selected = {field: data.get(field) for field in YFINANCE_INFO_FIELDS}
    analysis = def_json_ready(source.get("analysis") or {})
    method_status = def_json_ready(source.get("method_status") or {})
    return {
        "url": source.get("url")
        or YFINANCE_SOURCE_URL_TEMPLATE.format(ticker=ticker),
        "http_status": def_safe_int(source.get("http_status")) or 200,
        "sha256": source.get("sha256") or "OFFLINE_YFINANCE_INFO_FIXTURE",
        "data": selected,
        "analysis": analysis,
        "method_status": method_status,
        "coverage_status": source.get("coverage_status") or "COVERED",
        "source_mode": "OFFLINE_YFINANCE_INFO_FIXTURE",
        "captured_at_utc": source.get("captured_at_utc")
        or fixture.get("captured_at_utc")
        or def_now_utc_iso(),
        "yfinance_version": source.get("yfinance_version"),
        "adj_close_source": source.get("adj_close_source") or "Adj Close",
    }


def def_fetch_one_code_from_fixture(code, fixture):
    page = fixture.get("page") or {}
    symbol = str(page.get("symbol") or "").strip()
    if not symbol:
        raise ValueError(f"FIXTURE_SYMBOL_MISSING: {code}")
    if len(symbol.split(":")) < 2 or symbol.split(":")[1] != code:
        raise ValueError(f"FIXTURE_SYMBOL_CODE_MISMATCH: {code} {symbol}")

    page_url = page.get("url") or CNYES_PAGE_TEMPLATE.format(code=code)
    target_result = def_fixture_source_result(fixture, "target")
    rating_result = def_fixture_source_result(fixture, "rating")
    eps_result = def_fixture_source_result(fixture, "eps")
    sales_result = def_fixture_source_result(fixture, "sales")
    yfinance_ticker = def_cnyes_symbol_to_yfinance_ticker(symbol, code)
    yfinance_result = def_fixture_yfinance_source_result(
        fixture,
        yfinance_ticker=yfinance_ticker,
    )

    target = def_normalize_target(
        code=code,
        symbol=symbol,
        page_url=page_url,
        source_result=target_result,
    )
    rating_history = def_normalize_rating_history(
        code=code,
        symbol=symbol,
        page_url=page_url,
        source_result=rating_result,
    )
    eps_rows = def_normalize_estimate_rows(
        code=code,
        symbol=symbol,
        page_url=page_url,
        source_result=eps_result,
        estimate_type="eps",
        current_price=target.get("current_price"),
    )
    sales_rows = def_normalize_estimate_rows(
        code=code,
        symbol=symbol,
        page_url=page_url,
        source_result=sales_result,
        estimate_type="sales",
        current_price=target.get("current_price"),
    )
    yfinance_consensus = def_normalize_yfinance_consensus(
        code=code,
        symbol=symbol,
        yfinance_ticker=yfinance_ticker,
        source_result=yfinance_result,
    )
    source_comparison = def_build_source_comparison(
        target=target,
        latest_rating=rating_history[0] if rating_history else {},
        yfinance_consensus=yfinance_consensus,
    )
    target_spectrum = def_build_target_spectrum(target, yfinance_consensus)

    company_name = target.get("company_name") or page.get("company_name")
    for row in rating_history + eps_rows + sales_rows:
        row["company_name"] = company_name

    endpoint_meta = {
        "page": {
            "url": page_url,
            "status": def_safe_int(page.get("http_status")) or 200,
            "sha256": page.get("sha256") or "OFFLINE_FIXTURE",
        },
        "target": {
            "url": target_result.get("url"),
            "status": target_result.get("http_status"),
            "sha256": target_result.get("sha256"),
            "mode": target_result.get("source_mode"),
        },
        "rating": {
            "url": rating_result.get("url"),
            "status": rating_result.get("http_status"),
            "sha256": rating_result.get("sha256"),
            "mode": rating_result.get("source_mode"),
        },
        "eps": {
            "url": eps_result.get("url"),
            "status": eps_result.get("http_status"),
            "sha256": eps_result.get("sha256"),
            "mode": eps_result.get("source_mode"),
        },
        "sales": {
            "url": sales_result.get("url"),
            "status": sales_result.get("http_status"),
            "sha256": sales_result.get("sha256"),
            "mode": sales_result.get("source_mode"),
        },
        "yfinance": {
            "url": yfinance_result.get("url"),
            "status": yfinance_result.get("http_status"),
            "sha256": yfinance_result.get("sha256"),
            "mode": yfinance_result.get("source_mode"),
            "version": yfinance_result.get("yfinance_version"),
            "coverage_status": yfinance_result.get("coverage_status"),
            "method_status": yfinance_result.get("method_status") or {},
        },
    }

    return {
        "code": code,
        "symbol": symbol,
        "company_name": company_name,
        "fetched_at_utc": fixture.get("captured_at_utc") or def_now_utc_iso(),
        "page_url": page_url,
        "market_info_api_url": fixture.get("market_info_api_url")
        or DEFAULT_MARKET_INFO_API_URL,
        "target": target,
        "yfinance": yfinance_consensus,
        "yfinance_analysis": yfinance_result.get("analysis") or {},
        "source_comparison": source_comparison,
        "target_spectrum": target_spectrum,
        "rating_history": rating_history,
        "eps": eps_rows,
        "sales": sales_rows,
        "endpoint_meta": endpoint_meta,
        "fixture_path": fixture.get("fixture_path"),
    }


# =============================================================================
# def 07 · RECORDS AND MATRIX
# =============================================================================

def def_record_safe_value(value):
    import json

    ready = def_json_ready(value)
    if isinstance(ready, (dict, list)):
        return json.dumps(ready, ensure_ascii=False, sort_keys=True)
    return ready


def def_yfinance_analysis_period(row, fallback):
    if not isinstance(row, dict):
        return fallback
    candidates = [
        "index",
        "period",
        "Period",
        "fiscalPeriod",
        "fiscalYear",
        "quarter",
        "date",
    ]
    for key in candidates:
        value = row.get(key)
        if value not in [None, ""]:
            return value
    return fallback


def def_build_yfinance_analysis_records(payload):
    analysis = payload.get("yfinance_analysis") or {}
    if not isinstance(analysis, dict):
        return []

    yfinance_consensus = payload.get("yfinance") or {}
    endpoint_meta = def_deep_get(
        payload,
        ["endpoint_meta", "yfinance"],
        default={},
    ) or {}
    captured_at = (
        yfinance_consensus.get("captured_at_utc")
        or payload.get("fetched_at_utc")
    )
    common = {
        "fetched_at_utc": payload.get("fetched_at_utc"),
        "code": payload.get("code"),
        "symbol": payload.get("symbol"),
        "company_name": payload.get("company_name"),
        "currency": yfinance_consensus.get("currency"),
        "source": "YFinance",
        "source_mode": yfinance_consensus.get("source_mode"),
        "source_url": yfinance_consensus.get("source_url"),
    }
    method_status = endpoint_meta.get("method_status") or {}
    records = []

    for method_name in YFINANCE_ANALYSIS_METHODS:
        section = YFINANCE_METHOD_TO_SECTION.get(
            method_name,
            "YFINANCE_ANALYSIS",
        )
        data = analysis.get(method_name)
        status = def_deep_get(
            method_status,
            [method_name, "status"],
            default="NOT_CAPTURED",
        )
        if isinstance(data, dict):
            items = [{"index": captured_at, **data}]
        elif isinstance(data, list):
            items = data
        elif data is None:
            items = []
        else:
            items = [{"index": captured_at, "value": data}]

        for index, item in enumerate(items):
            row = item if isinstance(item, dict) else {"value": item}
            period = def_yfinance_analysis_period(row, f"{captured_at}#{index}")
            for metric, value in row.items():
                if metric in {
                    "index",
                    "period",
                    "Period",
                    "fiscalPeriod",
                    "fiscalYear",
                    "quarter",
                    "date",
                }:
                    continue
                records.append({
                    **common,
                    "section": section,
                    "period": period,
                    "metric": str(metric),
                    "value": def_record_safe_value(value),
                    "method": method_name,
                    "method_status": status,
                })

    return records


def def_build_raw_records(payloads):
    records = []

    for payload in payloads:
        common = {
            "fetched_at_utc": payload.get("fetched_at_utc"),
            "code": payload.get("code"),
            "symbol": payload.get("symbol"),
            "company_name": payload.get("company_name"),
        }

        target = payload.get("target") or {}
        for metric in [
            "current_price",
            "target_low",
            "target_mean",
            "target_median",
            "target_high",
            "target_low_upside_pct",
            "target_mean_upside_pct",
            "target_median_upside_pct",
            "target_high_upside_pct",
            "target_std_dev",
            "target_up_revisions",
            "target_down_revisions",
            "analyst_count",
        ]:
            records.append({
                **common,
                "section": "TARGET_VALUATION",
                "period": target.get("rate_date"),
                "metric": metric,
                "value": target.get(metric),
                "currency": target.get("currency"),
                "source": target.get("source"),
                "source_mode": target.get("source_mode"),
                "source_url": target.get("source_url"),
            })

        yfinance_consensus = payload.get("yfinance") or {}
        for metric in [
            "current_price",
            "adj_close",
            "beta",
            "target_low",
            "target_mean",
            "target_median",
            "target_high",
            "target_low_upside_pct",
            "target_mean_upside_pct",
            "target_median_upside_pct",
            "target_high_upside_pct",
            "analyst_count",
            "recommendation_mean",
            "recommendation_key",
            "rating_direction",
        ]:
            records.append({
                **common,
                "section": "YFINANCE_INFO",
                "period": yfinance_consensus.get("captured_at_utc"),
                "metric": metric,
                "value": yfinance_consensus.get(metric),
                "currency": yfinance_consensus.get("currency"),
                "source": yfinance_consensus.get("source"),
                "source_mode": yfinance_consensus.get("source_mode"),
                "source_url": yfinance_consensus.get("source_url"),
            })

        comparison = payload.get("source_comparison") or {}
        for item in comparison.get("metrics") or []:
            metric = str(item.get("metric") or "").lower()
            for suffix in [
                "difference",
                "difference_pct",
                "abs_difference_pct",
                "status",
            ]:
                records.append({
                    **common,
                    "section": "SOURCE_COMPARISON",
                    "period": payload.get("fetched_at_utc"),
                    "metric": f"{metric}_{suffix}",
                    "value": item.get(suffix),
                    "currency": target.get("currency"),
                    "source": "FactSet × YFinance",
                    "source_mode": "CROSS_SOURCE_COMPARISON",
                    "source_url": yfinance_consensus.get("source_url"),
                })

        for rating in payload.get("rating_history") or []:
            for metric in [
                "rating_mark",
                "buy_count",
                "outperform_count",
                "hold_count",
                "underperform_count",
                "sell_count",
                "positive_count",
                "neutral_count",
                "negative_count",
                "analyst_count",
                "target_median",
            ]:
                records.append({
                    **common,
                    "section": "RATING_HISTORY",
                    "period": rating.get("rating_date"),
                    "metric": metric,
                    "value": rating.get(metric),
                    "currency": rating.get("currency"),
                    "source": rating.get("source"),
                    "source_mode": rating.get("source_mode"),
                    "source_url": rating.get("source_url"),
                })

        for section, rows in [
            ("EPS_ESTIMATE", payload.get("eps") or []),
            ("SALES_ESTIMATE", payload.get("sales") or []),
        ]:
            for estimate in rows:
                for metric in [
                    "estimate_low",
                    "estimate_mean",
                    "estimate_median",
                    "estimate_high",
                    "estimate_std_dev",
                    "up_revisions",
                    "down_revisions",
                    "analyst_count",
                    "forward_pe_median",
                ]:
                    records.append({
                        **common,
                        "section": section,
                        "period": estimate.get("fiscal_year"),
                        "rate_date": estimate.get("rate_date"),
                        "metric": metric,
                        "value": estimate.get(metric),
                        "currency": estimate.get("currency"),
                        "source": estimate.get("source"),
                        "source_mode": estimate.get("source_mode"),
                        "source_url": estimate.get("source_url"),
                    })

        records.extend(def_build_yfinance_analysis_records(payload))

    for record in records:
        record["section_label"] = def_display_identifier(record.get("section"))
        record["metric_label"] = def_display_identifier(record.get("metric"))
        record["value_display"] = def_display_text(record.get("value"))
        record["source_mode_label"] = def_display_source_mode(
            record.get("source_mode")
        )

    return records


def def_build_wide_matrix(payloads):
    rows = []
    all_years = sorted({
        estimate.get("fiscal_year")
        for payload in payloads
        for estimate in (payload.get("eps") or []) + (payload.get("sales") or [])
        if estimate.get("fiscal_year") is not None
    })

    for payload in payloads:
        target = payload.get("target") or {}
        yfinance_consensus = payload.get("yfinance") or {}
        comparison = payload.get("source_comparison") or {}
        comparison_by_metric = {
            item.get("metric"): item
            for item in comparison.get("metrics") or []
        }
        latest_rating = (payload.get("rating_history") or [{}])[0]
        row = {
            "code": payload.get("code"),
            "symbol": payload.get("symbol"),
            "company_name": payload.get("company_name"),
            "fetched_at_utc": payload.get("fetched_at_utc"),
            "current_price": target.get("current_price"),
            "currency": target.get("currency"),
            "target_rate_date": target.get("rate_date"),
            "target_analyst_count": target.get("analyst_count"),
            "target_low": target.get("target_low"),
            "target_mean": target.get("target_mean"),
            "target_median": target.get("target_median"),
            "target_high": target.get("target_high"),
            "target_median_upside_pct": target.get("target_median_upside_pct"),
            "rating_date": latest_rating.get("rating_date"),
            "rating_analyst_count": latest_rating.get("analyst_count"),
            "rating_buy": latest_rating.get("buy_count"),
            "rating_outperform": latest_rating.get("outperform_count"),
            "rating_hold": latest_rating.get("hold_count"),
            "rating_underperform": latest_rating.get("underperform_count"),
            "rating_sell": latest_rating.get("sell_count"),
            "cnyes_rating_direction": def_cnyes_rating_direction(latest_rating),
            "yf_ticker": yfinance_consensus.get("yfinance_ticker"),
            "yf_captured_at_utc": yfinance_consensus.get("captured_at_utc"),
            "yf_current_price": yfinance_consensus.get("current_price"),
            "yf_adj_close": yfinance_consensus.get("adj_close"),
            "yf_beta": yfinance_consensus.get("beta"),
            "yf_currency": yfinance_consensus.get("currency"),
            "yf_target_analyst_count": yfinance_consensus.get("analyst_count"),
            "yf_target_low": yfinance_consensus.get("target_low"),
            "yf_target_mean": yfinance_consensus.get("target_mean"),
            "yf_target_median": yfinance_consensus.get("target_median"),
            "yf_target_high": yfinance_consensus.get("target_high"),
            "yf_target_median_upside_pct": yfinance_consensus.get(
                "target_median_upside_pct"
            ),
            "yf_recommendation_mean": yfinance_consensus.get(
                "recommendation_mean"
            ),
            "yf_recommendation_key": yfinance_consensus.get(
                "recommendation_key"
            ),
            "yf_rating_direction": yfinance_consensus.get("rating_direction"),
            "source_agreement_gate": comparison.get("agreement_gate"),
            "source_match_count": comparison.get("match_count"),
            "source_review_count": comparison.get("review_count"),
            "source_conflict_count": comparison.get("conflict_count"),
            "source_incomplete_count": comparison.get("incomplete_count"),
            "current_price_yf_minus_cnyes_pct": def_deep_get(
                comparison_by_metric,
                ["CURRENT_PRICE", "difference_pct"],
            ),
            "target_low_yf_minus_cnyes_pct": def_deep_get(
                comparison_by_metric,
                ["TARGET_LOW", "difference_pct"],
            ),
            "target_mean_yf_minus_cnyes_pct": def_deep_get(
                comparison_by_metric,
                ["TARGET_MEAN", "difference_pct"],
            ),
            "target_median_yf_minus_cnyes_pct": def_deep_get(
                comparison_by_metric,
                ["TARGET_MEDIAN", "difference_pct"],
            ),
            "target_high_yf_minus_cnyes_pct": def_deep_get(
                comparison_by_metric,
                ["TARGET_HIGH", "difference_pct"],
            ),
            "rating_source_status": def_deep_get(
                comparison_by_metric,
                ["RATING", "status"],
            ),
            "source_page": payload.get("page_url"),
            "source_yfinance": yfinance_consensus.get("source_url"),
        }

        eps_by_year = {
            item.get("fiscal_year"): item for item in payload.get("eps") or []
        }
        sales_by_year = {
            item.get("fiscal_year"): item for item in payload.get("sales") or []
        }

        for year in all_years:
            eps = eps_by_year.get(year, {})
            sales = sales_by_year.get(year, {})
            prefix_eps = f"eps_{year}"
            prefix_sales = f"sales_{year}"
            row.update({
                f"{prefix_eps}_rate_date": eps.get("rate_date"),
                f"{prefix_eps}_low": eps.get("estimate_low"),
                f"{prefix_eps}_mean": eps.get("estimate_mean"),
                f"{prefix_eps}_median": eps.get("estimate_median"),
                f"{prefix_eps}_high": eps.get("estimate_high"),
                f"{prefix_eps}_analyst_count": eps.get("analyst_count"),
                f"{prefix_eps}_forward_pe": eps.get("forward_pe_median"),
                f"{prefix_sales}_rate_date": sales.get("rate_date"),
                f"{prefix_sales}_low": sales.get("estimate_low"),
                f"{prefix_sales}_mean": sales.get("estimate_mean"),
                f"{prefix_sales}_median": sales.get("estimate_median"),
                f"{prefix_sales}_high": sales.get("estimate_high"),
                f"{prefix_sales}_analyst_count": sales.get("analyst_count"),
            })

        rows.append(row)

    return rows


# =============================================================================
# def 08 · QUALITY MATRIX
# =============================================================================

def def_add_check(checks, code, check_id, actual, expected, passed, severity, note):
    checks.append({
        "code": code,
        "check_id": check_id,
        "actual": actual,
        "expected": expected,
        "status": "PASS" if passed else severity,
        "severity": severity,
        "note": note,
    })


def def_build_quality_checks(payloads, raw_records, matrix_rows):
    checks = []

    for payload in payloads:
        code = payload.get("code")
        endpoint_meta = payload.get("endpoint_meta") or {}
        for endpoint in ["page", "target", "rating", "eps", "sales", "yfinance"]:
            status = def_deep_get(endpoint_meta, [endpoint, "status"])
            def_add_check(
                checks,
                code,
                f"HTTP_{endpoint.upper()}_200",
                status,
                200,
                status == 200,
                "FAIL",
                f"{endpoint} endpoint must return HTTP 200.",
            )

        yfinance_method_status = def_deep_get(
            endpoint_meta,
            ["yfinance", "method_status"],
            default={},
        ) or {}
        for method_name, method_result in yfinance_method_status.items():
            method_state = (
                method_result.get("status")
                if isinstance(method_result, dict)
                else method_result
            )
            def_add_check(
                checks,
                code,
                f"YFINANCE_METHOD_{method_name.upper()}",
                method_state,
                "PASS or NO_COVERAGE",
                method_state in {"PASS", "NO_COVERAGE"},
                "WARN",
                "YFinance method errors are isolated; other sources remain usable.",
            )

        symbol = str(payload.get("symbol") or "")
        symbol_ok = len(symbol.split(":")) >= 2 and symbol.split(":")[1] == code
        def_add_check(
            checks,
            code,
            "SYMBOL_MATCHES_URL_CODE",
            symbol,
            code,
            symbol_ok,
            "FAIL",
            "Prevent cross-ticker contamination.",
        )

        target = payload.get("target") or {}
        low = def_safe_float(target.get("target_low"))
        median = def_safe_float(target.get("target_median"))
        high = def_safe_float(target.get("target_high"))
        target_order_ok = all(value is not None for value in [low, median, high]) and low <= median <= high
        def_add_check(
            checks,
            code,
            "TARGET_LOW_MEDIAN_HIGH_ORDER",
            f"{low} <= {median} <= {high}",
            "low <= median <= high",
            target_order_ok,
            "FAIL",
            "Target valuation ordering sanity check.",
        )

        analyst_count = def_safe_int(target.get("analyst_count"))
        def_add_check(
            checks,
            code,
            "TARGET_ANALYST_COUNT_POSITIVE",
            analyst_count,
            "> 0",
            analyst_count is not None and analyst_count > 0,
            "WARN",
            "Some tickers may legitimately have no FactSet target coverage.",
        )

        yfinance_consensus = payload.get("yfinance") or {}
        expected_yf_ticker = def_cnyes_symbol_to_yfinance_ticker(symbol, code)
        actual_yf_ticker = yfinance_consensus.get("yfinance_ticker")
        def_add_check(
            checks,
            code,
            "YFINANCE_TICKER_MATCHES_CNYES_MARKET",
            actual_yf_ticker,
            expected_yf_ticker,
            actual_yf_ticker == expected_yf_ticker,
            "FAIL",
            "TWSE maps to .TW and TPEX maps to .TWO.",
        )

        yf_low = def_safe_float(yfinance_consensus.get("target_low"))
        yf_median = def_safe_float(yfinance_consensus.get("target_median"))
        yf_high = def_safe_float(yfinance_consensus.get("target_high"))
        yf_order_ok = all(
            value is not None for value in [yf_low, yf_median, yf_high]
        ) and yf_low <= yf_median <= yf_high
        def_add_check(
            checks,
            code,
            "YFINANCE_TARGET_LOW_MEDIAN_HIGH_ORDER",
            f"{yf_low} <= {yf_median} <= {yf_high}",
            "low <= median <= high",
            yf_order_ok,
            "WARN",
            "Yahoo coverage may omit one or more target fields.",
        )

        yf_core_fields = [
            yfinance_consensus.get("target_low"),
            yfinance_consensus.get("target_mean"),
            yfinance_consensus.get("target_median"),
            yfinance_consensus.get("target_high"),
            yfinance_consensus.get("recommendation_key"),
        ]
        def_add_check(
            checks,
            code,
            "YFINANCE_CONSENSUS_CORE_FIELDS_COMPLETE",
            sum(value not in [None, ""] for value in yf_core_fields),
            len(yf_core_fields),
            all(value not in [None, ""] for value in yf_core_fields),
            "WARN",
            "Required YFinance target and rating fields.",
        )

        comparison = payload.get("source_comparison") or {}
        def_add_check(
            checks,
            code,
            "SOURCE_CURRENCIES_MATCH",
            f"{comparison.get('cnyes_currency')} vs {comparison.get('yfinance_currency')}",
            "same non-empty currency",
            comparison.get("currencies_match") is True,
            "WARN",
            "Target-price differences are not comparable across currencies.",
        )

        comparison_metrics = comparison.get("metrics") or []
        comparison_names = [item.get("metric") for item in comparison_metrics]
        expected_comparison_names = [
            "CURRENT_PRICE",
            "TARGET_LOW",
            "TARGET_MEAN",
            "TARGET_MEDIAN",
            "TARGET_HIGH",
            "ANALYST_COUNT",
            "RATING",
        ]
        def_add_check(
            checks,
            code,
            "SOURCE_COMPARISON_ALL_ITEMS_UNIQUE",
            comparison_names,
            expected_comparison_names,
            comparison_names == expected_comparison_names
            and len(comparison_names) == len(set(comparison_names)),
            "FAIL",
            "Every requested target and rating item appears once.",
        )

        rating_comparison = next(
            (
                item
                for item in comparison_metrics
                if item.get("metric") == "RATING"
            ),
            {},
        )
        def_add_check(
            checks,
            code,
            "SOURCE_RATING_DIRECTIONS_COMPARABLE",
            f"{rating_comparison.get('cnyes_value')} vs {rating_comparison.get('yfinance_value')}",
            "both normalized",
            rating_comparison.get("cnyes_value") is not None
            and rating_comparison.get("yfinance_value") is not None,
            "WARN",
            "Raw rating labels are normalized only to Positive / Neutral / Negative.",
        )

        def_add_check(
            checks,
            code,
            "SOURCE_AGREEMENT_NO_CONFLICT",
            comparison.get("agreement_gate"),
            "MATCH or REVIEW",
            comparison.get("agreement_gate") in {"MATCH", "REVIEW"},
            "WARN",
            "A conflict is a research flag, not a parser failure.",
        )

        spectrum = payload.get("target_spectrum") or {}
        spectrum_sources = spectrum.get("sources") or []
        spectrum_ok = (
            spectrum.get("status") == "PASS"
            and spectrum.get("adj_close") is not None
            and len(spectrum_sources) == 2
            and all(source.get("complete") for source in spectrum_sources)
        )
        def_add_check(
            checks,
            code,
            "TARGET_SPECTRUM_COMPLETE_AND_ALIGNED",
            f"{spectrum.get('status')} / {len(spectrum_sources)} sources",
            "PASS / 2 sources",
            spectrum_ok,
            "WARN",
            "Both target ranges and the shared Adj Close benchmark are required.",
        )

        rating_rows = payload.get("rating_history") or []
        rating_lengths = rating_rows[0].get("array_lengths", {}) if rating_rows else {}
        unique_lengths = set(rating_lengths.values())
        rating_lengths_ok = bool(rating_lengths) and len(unique_lengths) == 1
        def_add_check(
            checks,
            code,
            "RATING_ARRAY_LENGTHS_EQUAL",
            rating_lengths,
            "all equal",
            rating_lengths_ok,
            "FAIL",
            "Every rating item must stay aligned by index.",
        )

        latest_rating = rating_rows[0] if rating_rows else {}
        rating_sum = sum(
            def_safe_int(latest_rating.get(field)) or 0
            for field in [
                "buy_count",
                "outperform_count",
                "hold_count",
                "underperform_count",
                "sell_count",
            ]
        )
        rating_total = def_safe_int(latest_rating.get("analyst_count"))
        def_add_check(
            checks,
            code,
            "RATING_COMPONENTS_TIE_TO_TOTAL",
            rating_sum,
            rating_total,
            rating_total is not None and rating_sum == rating_total,
            "FAIL",
            "Rating categories must reconcile to analyst total.",
        )

        for estimate_type in ["eps", "sales"]:
            rows = payload.get(estimate_type) or []
            years = [row.get("fiscal_year") for row in rows]
            all_items_ok = bool(rows) and len(years) == len(set(years))
            def_add_check(
                checks,
                code,
                f"{estimate_type.upper()}_ALL_YEAR_ITEMS_UNIQUE",
                years,
                "non-empty unique fiscal years",
                all_items_ok,
                "FAIL",
                "Prevents only-first-item and duplicate-year bugs.",
            )

            values_ok = bool(rows) and all(
                row.get("estimate_median") is not None
                and row.get("estimate_low") is not None
                and row.get("estimate_high") is not None
                for row in rows
            )
            def_add_check(
                checks,
                code,
                f"{estimate_type.upper()}_CORE_VALUES_COMPLETE",
                sum(1 for row in rows if row.get("estimate_median") is not None),
                len(rows),
                values_ok,
                "FAIL",
                "Every year item must include low, median and high.",
            )

        code_matrix_count = sum(1 for row in matrix_rows if row.get("code") == code)
        def_add_check(
            checks,
            code,
            "ONE_MATRIX_ROW_PER_CODE",
            code_matrix_count,
            1,
            code_matrix_count == 1,
            "FAIL",
            "Matrix must be de-duplicated by code.",
        )

    duplicate_key_count = 0
    seen_keys = set()
    for row in raw_records:
        key = (
            row.get("code"),
            row.get("section"),
            row.get("period"),
            row.get("metric"),
        )
        if key in seen_keys:
            duplicate_key_count += 1
        seen_keys.add(key)

    def_add_check(
        checks,
        "ALL",
        "RAW_COMPOSITE_KEY_DUPLICATES",
        duplicate_key_count,
        0,
        duplicate_key_count == 0,
        "FAIL",
        "Raw table composite keys must be unique.",
    )

    return checks


def def_quality_gate(checks):
    fail_count = sum(1 for row in checks if row.get("status") == "FAIL")
    warn_count = sum(1 for row in checks if row.get("status") == "WARN")
    pass_count = sum(1 for row in checks if row.get("status") == "PASS")

    if fail_count > 0:
        gate = "FAIL_CLOSED"
    elif warn_count > 0:
        gate = "PASS_WITH_WARNINGS"
    else:
        gate = "PASS"

    return {
        "gate": gate,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "check_count": len(checks),
    }


# =============================================================================
# def 09 · OUTPUT WRITERS
# =============================================================================

def def_collect_fieldnames(rows):
    fieldnames = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    return fieldnames


def def_write_csv(path, rows):
    import csv
    from pathlib import Path

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = def_collect_fieldnames(rows)

    with output_path.open("w", encoding=CSV_ENCODING, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        if fieldnames:
            writer.writeheader()
            writer.writerows(rows)
    return output_path


def def_write_json(path, data):
    import json
    from pathlib import Path

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(def_json_ready(data), ensure_ascii=False, indent=2)
    output_path.write_text(text, encoding="utf-8")
    return output_path


def def_try_write_parquet(path, rows):
    from pathlib import Path

    output_path = Path(path)
    if not rows:
        return {
            "status": "SKIP_EMPTY",
            "path": str(output_path),
            "engine": None,
            "error": None,
        }

    try:
        import pandas as pd

        frame = pd.DataFrame(rows)
        frame.to_parquet(output_path, index=False)
        return {
            "status": "PASS",
            "path": str(output_path),
            "engine": "pandas",
            "error": None,
        }
    except Exception as exc:
        return {
            "status": "WARN_PARQUET_ENGINE_UNAVAILABLE",
            "path": str(output_path),
            "engine": None,
            "error": str(exc),
        }


def def_html_escape(value):
    import html

    if value is None:
        return "—"
    return html.escape(str(value))


def def_html_number(value, digits=2):
    number = def_safe_float(value)
    if number is None:
        return "—"
    return f"{number:,.{digits}f}"


def def_html_percent(value, digits=1):
    number = def_safe_float(value)
    if number is None:
        return "—"
    sign = "+" if number > 0 else ""
    return f"{sign}{number * 100:.{digits}f}%"


def def_build_table(headers, rows, classes=""):
    head = "".join(f"<th>{def_html_escape(item)}</th>" for item in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{item}</td>" for item in row)
        body_rows.append(f"<tr>{cells}</tr>")
    return (
        f'<div class="table-wrap {classes}"><table><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody></table></div>'
    )


def def_html_twd(value):
    number = def_safe_float(value)
    if number is None:
        return "—"
    if abs(number - round(number)) < 0.000001:
        return f"{number:,.0f}"
    return f"{number:,.2f}"


def def_build_target_spectrum_html(payload):
    spectrum = payload.get("target_spectrum") or {}
    sources = spectrum.get("sources") or []
    if spectrum.get("status") != "PASS" or len(sources) != 2:
        return (
            '<div class="spectrum-panel"><div class="matrix-title">'
            '<h3>FactSet／YFinance 目標價雙光譜</h3>'
            '<span>資料不足，暫時無法繪製共用價格座標。</span></div></div>'
        )

    width = 1100
    height = 360
    plot_left = 170
    plot_right = 1040
    plot_width = plot_right - plot_left
    domain_min = def_safe_float(spectrum.get("domain_min"))
    domain_max = def_safe_float(spectrum.get("domain_max"))
    domain_span = (domain_max - domain_min) if None not in [domain_min, domain_max] else 0

    def def_x(value):
        number = def_safe_float(value)
        if number is None or domain_span <= 0:
            return plot_left
        return plot_left + ((number - domain_min) / domain_span) * plot_width

    def def_marker_label(label, value, upside):
        return (
            f"{label}（{def_html_twd(value)} 元；"
            f"{def_html_percent(upside)}）"
        )

    code = str(payload.get("code") or "ticker")
    colors = spectrum.get("colors") or TARGET_SPECTRUM_COLORS
    svg_parts = [
        f'<svg class="target-spectrum" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="target-spectrum-title-{code} target-spectrum-desc-{code}">',
        f'<title id="target-spectrum-title-{code}">FactSet 與 YFinance 目標價雙光譜</title>',
        f'<desc id="target-spectrum-desc-{code}">兩個來源在同一價格座標上顯示最低價、平均值、中位數、最高價，並以垂直虛線標示目前 Adj Close。</desc>',
        "<defs>",
    ]
    for index, _source in enumerate(sources):
        svg_parts.append(
            f'<linearGradient id="target-gradient-{code}-{index}" x1="0%" y1="0%" x2="100%" y2="0%">'
            f'<stop offset="0%" stop-color="{def_html_escape(colors.get("low"))}"/>'
            f'<stop offset="50%" stop-color="{def_html_escape(colors.get("mid"))}"/>'
            f'<stop offset="100%" stop-color="{def_html_escape(colors.get("high"))}"/>'
            "</linearGradient>"
        )
    svg_parts.append("</defs>")
    svg_parts.append(
        f'<line class="axis-line" x1="{plot_left}" y1="326" x2="{plot_right}" y2="326"/>'
    )

    adj_x = def_x(spectrum.get("adj_close"))
    beta = def_safe_float(spectrum.get("beta"))
    beta_text = f"{beta:.2f}" if beta is not None else "—"
    svg_parts.extend([
        f'<line class="adj-close-line" x1="{adj_x:.2f}" y1="48" x2="{adj_x:.2f}" y2="312"/>',
        f'<rect class="adj-close-label-bg" x="{min(adj_x + 8, 820):.2f}" y="12" width="240" height="28" rx="7"/>',
        f'<text class="adj-close-label" x="{min(adj_x + 20, 832):.2f}" y="31">'
        f'Adj Close {def_html_twd(spectrum.get("adj_close"))} 元；Beta {beta_text}</text>',
    ])

    y_positions = [128, 248]
    for index, source in enumerate(sources):
        y = y_positions[index]
        low_x = def_x(source.get("low"))
        mean_x = def_x(source.get("mean"))
        median_x = def_x(source.get("median"))
        high_x = def_x(source.get("high"))
        triangle = (
            f"{mean_x:.2f},{y - 10:.2f} "
            f"{mean_x - 9:.2f},{y + 8:.2f} "
            f"{mean_x + 9:.2f},{y + 8:.2f}"
        )
        svg_parts.extend([
            f'<text class="source-name" x="20" y="{y + 5}">{def_html_escape(source.get("source"))}</text>',
            f'<rect class="spectrum-range" x="{low_x:.2f}" y="{y - 10}" width="{max(high_x - low_x, 2):.2f}" height="20" rx="10" fill="url(#target-gradient-{code}-{index})"/>',
            f'<circle class="hollow-circle" cx="{median_x:.2f}" cy="{y}" r="9"/>',
            f'<polygon class="hollow-triangle" points="{triangle}"/>',
            f'<text class="median-label" x="{median_x:.2f}" y="{y - 34}">'
            f'{def_html_escape(def_marker_label("目標價中位數", source.get("median"), source.get("median_upside_vs_adj_close_pct")))}</text>',
            f'<text class="mean-label" x="{mean_x:.2f}" y="{y + 58}">'
            f'{def_html_escape(def_marker_label("平均值", source.get("mean"), source.get("mean_upside_vs_adj_close_pct")))}</text>',
            f'<text class="range-label low" x="{low_x:.2f}" y="{y + 30}">最低 {def_html_twd(source.get("low"))}</text>',
            f'<text class="range-label high" x="{high_x:.2f}" y="{y + 30}">最高 {def_html_twd(source.get("high"))}</text>',
        ])

    svg_parts.extend([
        f'<text class="axis-label" x="{plot_left}" y="348">{def_html_twd(domain_min)} 元</text>',
        f'<text class="axis-label end" x="{plot_right}" y="348">{def_html_twd(domain_max)} 元</text>',
        '<g class="marker-legend" transform="translate(635 340)">'
        '<circle class="hollow-circle" cx="0" cy="0" r="6"/><text x="12" y="4">中位數</text>'
        '<polygon class="hollow-triangle" points="105,-7 98,6 112,6"/><text x="120" y="4">平均值</text>'
        '</g>',
        "</svg>",
    ])
    return (
        '<div class="spectrum-panel"><div class="matrix-title">'
        '<h3>FactSet／YFinance 目標價雙光譜</h3>'
        '<span>共用價格座標；空心圓＝中位數，空心三角形＝平均值</span>'
        '</div><div class="spectrum-wrap">'
        + "".join(svg_parts)
        + "</div></div>"
    )


def def_build_code_html(payload):
    target = payload.get("target") or {}
    yfinance_consensus = payload.get("yfinance") or {}
    comparison = payload.get("source_comparison") or {}
    ratings = payload.get("rating_history") or []
    eps_rows = payload.get("eps") or []
    sales_rows = payload.get("sales") or []
    latest_rating = ratings[0] if ratings else {}
    spectrum_html = def_build_target_spectrum_html(payload)

    comparison_table = def_build_table(
        [
            "項目",
            "FactSet",
            "YFinance",
            "差額（YFinance − FactSet）",
            "差異率",
            "狀態",
        ],
        [
            [
                def_html_escape(def_display_metric_label(row.get("metric"))),
                def_html_escape(def_display_rating_direction(row.get("cnyes_value")))
                if row.get("metric") == "RATING"
                else def_html_number(row.get("cnyes_value")),
                def_html_escape(def_display_rating_direction(row.get("yfinance_value")))
                if row.get("metric") == "RATING"
                else def_html_number(row.get("yfinance_value")),
                def_html_number(row.get("difference")),
                def_html_percent(row.get("difference_pct")),
                f'<span class="status {str(row.get("status") or "").lower()}">'
                f'{def_html_escape(def_display_status(row.get("status")))}</span>',
            ]
            for row in comparison.get("metrics") or []
        ],
        classes="comparison-table",
    )

    eps_table = def_build_table(
        ["年度", "更新日", "最低", "平均", "中位數", "最高", "分析師", "Forward P/E"],
        [
            [
                def_html_escape(row.get("fiscal_year")),
                def_html_escape(row.get("rate_date")),
                def_html_number(row.get("estimate_low")),
                def_html_number(row.get("estimate_mean")),
                f'<strong>{def_html_number(row.get("estimate_median"))}</strong>',
                def_html_number(row.get("estimate_high")),
                def_html_escape(row.get("analyst_count")),
                def_html_number(row.get("forward_pe_median")),
            ]
            for row in eps_rows
        ],
    )

    sales_table = def_build_table(
        ["年度", "更新日", "最低", "平均", "中位數", "最高", "分析師", "幣別"],
        [
            [
                def_html_escape(row.get("fiscal_year")),
                def_html_escape(row.get("rate_date")),
                def_html_number(row.get("estimate_low"), 0),
                def_html_number(row.get("estimate_mean"), 0),
                f'<strong>{def_html_number(row.get("estimate_median"), 0)}</strong>',
                def_html_number(row.get("estimate_high"), 0),
                def_html_escape(row.get("analyst_count")),
                def_html_escape(row.get("currency")),
            ]
            for row in sales_rows
        ],
    )

    rating_table = def_build_table(
        ["更新日", "買進", "優於大盤", "持有", "劣於大盤", "賣出", "總數", "目標價中位數"],
        [
            [
                def_html_escape(row.get("rating_date")),
                def_html_escape(row.get("buy_count")),
                def_html_escape(row.get("outperform_count")),
                def_html_escape(row.get("hold_count")),
                def_html_escape(row.get("underperform_count")),
                def_html_escape(row.get("sell_count")),
                f'<strong>{def_html_escape(row.get("analyst_count"))}</strong>',
                def_html_number(row.get("target_median")),
            ]
            for row in ratings
        ],
    )

    return f"""
    <section class="ticker-section">
      <div class="section-head">
        <div>
          <div class="eyebrow">{def_html_escape(payload.get('symbol'))}</div>
          <h2>{def_html_escape(payload.get('company_name'))} <span>{def_html_escape(payload.get('code'))}</span></h2>
        </div>
        <div class="source-links"><a class="source-link" href="{def_html_escape(payload.get('page_url'))}" target="_blank" rel="noopener noreferrer">FactSet 資料頁 ↗</a><a class="source-link" href="{def_html_escape(yfinance_consensus.get('source_url'))}" target="_blank" rel="noopener noreferrer">YFinance ↗</a></div>
      </div>

      <div class="cards">
        <article class="card">
          <div class="label">目前 Adj Close</div>
          <div class="value">{def_html_number(yfinance_consensus.get('adj_close'))}</div>
          <div class="note">{def_html_escape(target.get('currency'))}</div>
        </article>
        <article class="card">
          <div class="label">FactSet 目標價中位數</div>
          <div class="value accent">{def_html_number(target.get('target_median'))}</div>
          <div class="note">{def_html_percent(target.get('target_median_upside_pct'))} · {def_html_escape(target.get('rate_date'))}</div>
        </article>
        <article class="card">
          <div class="label">YFinance 目標價中位數</div>
          <div class="value compact">{def_html_number(yfinance_consensus.get('target_median'))}</div>
          <div class="note">{def_html_percent(yfinance_consensus.get('target_median_upside_pct'))} · {def_html_escape(yfinance_consensus.get('analyst_count'))} 位</div>
        </article>
        <article class="card">
          <div class="label">雙來源評級／一致性</div>
          <div class="value compact">{def_html_escape(def_display_rating_direction(def_cnyes_rating_direction(latest_rating)))} × {def_html_escape(def_display_recommendation(yfinance_consensus.get('recommendation_key')))}</div>
          <div class="note"><span class="status {str(comparison.get('agreement_gate') or '').lower()}">{def_html_escape(def_display_status(comparison.get('agreement_gate')))}</span></div>
        </article>
      </div>

      {spectrum_html}

      <div class="matrix-block">
        <div class="matrix-title"><h3>FactSet × YFinance 共識比較矩陣</h3><span>差異率 =（YFinance − FactSet）÷ FactSet；不進行來源平均</span></div>
        {comparison_table}
      </div>

      <div class="matrix-block">
        <div class="matrix-title"><h3>年度 EPS 共識矩陣</h3><span>完整保留每一個年度項目</span></div>
        {eps_table}
      </div>

      <div class="matrix-block">
        <div class="matrix-title"><h3>年度營收共識矩陣</h3><span>金額未縮放，保留來源原始單位</span></div>
        {sales_table}
      </div>

      <div class="matrix-block">
        <div class="matrix-title"><h3>分析師評級歷史矩陣</h3><span>各陣列以相同索引對齊</span></div>
        {rating_table}
      </div>
    </section>
    """


def def_html_trillion(value):
    number = def_safe_float(value)
    if number is None:
        return "—"
    return f"{number / 1_000_000_000_000:,.2f}"


def def_build_target_spectrum_compact_html(payload):
    spectrum = payload.get("target_spectrum") or {}
    sources = spectrum.get("sources") or []
    if spectrum.get("status") != "PASS" or len(sources) != 2:
        return (
            '<section class="spectrum-panel"><div class="panel-head">'
            '<h3>FactSet／YFinance 目標價光譜</h3>'
            '<span>資料不足，暫時無法繪製。</span></div></section>'
        )

    width = 1000
    height = 260
    plot_left = 86
    plot_right = 970
    plot_width = plot_right - plot_left
    domain_min = def_safe_float(spectrum.get("domain_min"))
    domain_max = def_safe_float(spectrum.get("domain_max"))
    domain_span = (
        domain_max - domain_min
        if None not in [domain_min, domain_max]
        else 0
    )

    def def_x(value):
        number = def_safe_float(value)
        if number is None or domain_span <= 0:
            return plot_left
        return plot_left + ((number - domain_min) / domain_span) * plot_width

    def def_marker_label(label, value, upside):
        return (
            f"{label}（{def_html_twd(value)} 元；"
            f"{def_html_percent(upside)}）"
        )

    code = str(payload.get("code") or "ticker")
    colors = spectrum.get("colors") or TARGET_SPECTRUM_COLORS
    svg_parts = [
        f'<svg class="target-spectrum" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="compact-spectrum-title-{code} compact-spectrum-desc-{code}">',
        f'<title id="compact-spectrum-title-{code}">FactSet 與 YFinance 目標價雙光譜</title>',
        f'<desc id="compact-spectrum-desc-{code}">兩個來源使用相同價格座標；空心圓為中位數，空心三角形為平均值，垂直虛線為 Adj Close。</desc>',
        "<defs>",
    ]
    for index, _source in enumerate(sources):
        svg_parts.append(
            f'<linearGradient id="compact-gradient-{code}-{index}" x1="0%" y1="0%" x2="100%" y2="0%">'
            f'<stop offset="0%" stop-color="{def_html_escape(colors.get("low"))}"/>'
            f'<stop offset="50%" stop-color="{def_html_escape(colors.get("mid"))}"/>'
            f'<stop offset="100%" stop-color="{def_html_escape(colors.get("high"))}"/>'
            "</linearGradient>"
        )
    svg_parts.append("</defs>")

    adj_x = def_x(spectrum.get("adj_close"))
    beta = def_safe_float(spectrum.get("beta"))
    beta_text = f"{beta:.2f}" if beta is not None else "—"
    label_x = min(max(adj_x + 10, 96), 735)
    svg_parts.extend([
        f'<line class="axis-line" x1="{plot_left}" y1="230" x2="{plot_right}" y2="230"/>',
        f'<line class="adj-close-line" x1="{adj_x:.2f}" y1="32" x2="{adj_x:.2f}" y2="216"/>',
        f'<rect class="adj-close-label-bg" x="{label_x:.2f}" y="5" width="250" height="25" rx="5"/>',
        f'<text class="adj-close-label" x="{label_x + 12:.2f}" y="22">'
        f'Adj Close {def_html_twd(spectrum.get("adj_close"))} 元 · Beta {beta_text}</text>',
    ])

    y_positions = [78, 164]
    for index, source in enumerate(sources):
        y = y_positions[index]
        low_x = def_x(source.get("low"))
        mean_x = def_x(source.get("mean"))
        median_x = def_x(source.get("median"))
        high_x = def_x(source.get("high"))
        triangle = (
            f"{mean_x:.2f},{y - 9:.2f} "
            f"{mean_x - 8:.2f},{y + 7:.2f} "
            f"{mean_x + 8:.2f},{y + 7:.2f}"
        )
        svg_parts.extend([
            f'<text class="source-name" x="8" y="{y + 4}">{def_html_escape(source.get("source"))}</text>',
            f'<rect class="spectrum-range" x="{low_x:.2f}" y="{y - 8}" width="{max(high_x - low_x, 2):.2f}" height="16" rx="8" fill="url(#compact-gradient-{code}-{index})"/>',
            f'<circle class="hollow-circle" cx="{median_x:.2f}" cy="{y}" r="8"/>',
            f'<polygon class="hollow-triangle" points="{triangle}"/>',
            f'<text class="median-label" x="{median_x:.2f}" y="{y - 24}">'
            f'{def_html_escape(def_marker_label("中位數", source.get("median"), source.get("median_upside_vs_adj_close_pct")))}</text>',
            f'<text class="mean-label" x="{mean_x:.2f}" y="{y + 35}">'
            f'{def_html_escape(def_marker_label("平均值", source.get("mean"), source.get("mean_upside_vs_adj_close_pct")))}</text>',
            f'<text class="range-label low" x="{low_x:.2f}" y="{y + 20}">低 {def_html_twd(source.get("low"))}</text>',
            f'<text class="range-label high" x="{high_x:.2f}" y="{y + 20}">高 {def_html_twd(source.get("high"))}</text>',
        ])

    svg_parts.extend([
        f'<text class="axis-label" x="{plot_left}" y="249">{def_html_twd(domain_min)} 元</text>',
        f'<text class="axis-label end" x="{plot_right}" y="249">{def_html_twd(domain_max)} 元</text>',
        '<g class="marker-legend" transform="translate(650 246)">'
        '<circle class="hollow-circle" cx="0" cy="0" r="5"/><text x="10" y="4">中位數</text>'
        '<polygon class="hollow-triangle" points="92,-6 86,5 98,5"/><text x="105" y="4">平均值</text>'
        '</g>',
        "</svg>",
    ])
    return (
        '<section class="spectrum-panel"><div class="panel-head">'
        '<h3>FactSet／YFinance 目標價光譜</h3>'
        '<span>共用價格軸 · ○ 中位數 · △ 平均值</span>'
        '</div><div class="spectrum-wrap">'
        + "".join(svg_parts)
        + "</div></section>"
    )


def def_resolve_valuation_band_csv(code):
    import os
    from pathlib import Path

    filename = VALUATION_BAND_CSV_TEMPLATE.format(code=def_validate_code(code))
    configured = os.environ.get("VIA_VALUATION_BAND_DATA_DIR")
    candidates = []
    if configured:
        candidates.append(Path(configured) / filename)
    candidates.extend([
        Path.cwd() / VALUATION_BAND_DATA_DIR / filename,
        Path(__file__).resolve().parent / VALUATION_BAND_DATA_DIR / filename,
        Path(__file__).resolve().parent.parent / VALUATION_BAND_DATA_DIR / filename,
    ])
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def def_read_valuation_band_rows(code):
    import csv

    data_path = def_resolve_valuation_band_csv(code)
    if data_path is None:
        return []

    numeric_fields = [
        "adj_close",
        "forward_diluted_eps",
        "pe",
        "bvps",
        "pb",
        "pe_price_q10",
        "pe_price_q25",
        "pe_price_q50",
        "pe_price_q75",
        "pe_price_q90",
        "pb_price_q10",
        "pb_price_q25",
        "pb_price_q50",
        "pb_price_q75",
        "pb_price_q90",
    ]
    rows = []
    with data_path.open(encoding="utf-8-sig", newline="") as handle:
        for source_row in csv.DictReader(handle):
            row = dict(source_row)
            for field in numeric_fields:
                row[field] = def_safe_float(row.get(field))
            required = [
                row.get("date"),
                row.get("adj_close"),
                row.get("pe_price_q50"),
                row.get("pb_price_q50"),
            ]
            if all(value not in [None, ""] for value in required):
                rows.append(row)
    return rows


def def_nice_axis_ticks(minimum, maximum, target_count=5):
    import math

    low = def_safe_float(minimum)
    high = def_safe_float(maximum)
    if low is None or high is None:
        return []
    if high <= low:
        return [low]

    rough_step = (high - low) / max(target_count, 2)
    magnitude = 10 ** math.floor(math.log10(rough_step))
    normalized = rough_step / magnitude
    multiplier = next(
        item for item in [1, 2, 2.5, 5, 10]
        if normalized <= item
    )
    step = multiplier * magnitude
    start = math.floor(low / step) * step
    end = math.ceil(high / step) * step
    ticks = []
    value = start
    for _index in range(12):
        if value > end + (step * 0.25):
            break
        ticks.append(round(value, 8))
        value += step
    return ticks


def def_build_valuation_band_svg(code, rows, metric):
    from datetime import datetime

    metric_clean = str(metric).lower()
    if metric_clean not in {"pe", "pb"}:
        raise ValueError(f"VALUATION_METRIC_UNSUPPORTED: {metric}")
    if not rows:
        return '<div class="valuation-empty">估值帶資料尚未接入 VDF。</div>'

    prefix = f"{metric_clean}_price_"
    series_fields = [f"{prefix}{quantile}" for quantile in ["q10", "q25", "q50", "q75", "q90"]]
    usable_rows = [
        row for row in rows
        if def_safe_float(row.get("adj_close")) is not None
        and all(def_safe_float(row.get(field)) is not None for field in series_fields)
    ]
    if len(usable_rows) < 2:
        return '<div class="valuation-empty">估值帶有效資料不足。</div>'

    width = VALUATION_BAND_WIDTH
    height = VALUATION_BAND_HEIGHT
    plot_left = 55
    plot_right = width - 13
    plot_top = 12
    plot_bottom = height - 34
    plot_width = plot_right - plot_left
    plot_height = plot_bottom - plot_top

    def def_parse_date(value):
        text = str(value or "").strip()
        for pattern in ["%Y/%m/%d", "%Y-%m-%d"]:
            try:
                return datetime.strptime(text, pattern).date()
            except ValueError:
                continue
        raise ValueError(f"VALUATION_DATE_INVALID: {text}")

    dates = [def_parse_date(row.get("date")) for row in usable_rows]
    ordinals = [date.toordinal() for date in dates]
    ordinal_min = min(ordinals)
    ordinal_span = max(max(ordinals) - ordinal_min, 1)
    all_values = [
        def_safe_float(row.get(field))
        for row in usable_rows
        for field in ["adj_close", *series_fields]
    ]
    raw_min = min(all_values)
    raw_max = max(all_values)
    padding = max((raw_max - raw_min) * 0.06, 1)
    ticks = def_nice_axis_ticks(raw_min - padding, raw_max + padding, target_count=5)
    axis_min = min(ticks) if ticks else raw_min - padding
    axis_max = max(ticks) if ticks else raw_max + padding
    axis_span = max(axis_max - axis_min, 1)

    def def_x(index):
        ordinal = ordinals[index]
        return plot_left + ((ordinal - ordinal_min) / ordinal_span) * plot_width

    def def_y(value):
        number = def_safe_float(value)
        return plot_bottom - ((number - axis_min) / axis_span) * plot_height

    def def_path(field, reverse=False):
        indices = list(range(len(usable_rows)))
        if reverse:
            indices.reverse()
        commands = []
        for position, index in enumerate(indices):
            prefix_command = "M" if position == 0 else "L"
            commands.append(
                f"{prefix_command}{def_x(index):.1f},{def_y(usable_rows[index].get(field)):.1f}"
            )
        return " ".join(commands)

    area_path = (
        def_path(f"{prefix}q75")
        + " "
        + def_path(f"{prefix}q25", reverse=True).replace("M", "L", 1)
        + " Z"
    )
    title_metric = "Forward P/E" if metric_clean == "pe" else "P/B"
    svg_parts = [
        f'<svg class="valuation-svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="valuation-title-{code}-{metric_clean} valuation-desc-{code}-{metric_clean}">',
        f'<title id="valuation-title-{code}-{metric_clean}">{title_metric} Band</title>',
        f'<desc id="valuation-desc-{code}-{metric_clean}">Adj Close 與近兩年 Q10、Q25、Q50、Q75、Q90 估值價格帶。</desc>',
    ]

    for tick in ticks:
        y = def_y(tick)
        svg_parts.extend([
            f'<line class="valuation-grid-line" x1="{plot_left}" y1="{y:.1f}" x2="{plot_right}" y2="{y:.1f}"/>',
            f'<text class="valuation-axis-label y" x="{plot_left - 8}" y="{y + 3:.1f}">{def_html_twd(tick)}</text>',
        ])

    tick_indices = sorted(set(
        round((len(usable_rows) - 1) * fraction / 4)
        for fraction in range(5)
    ))
    for index in tick_indices:
        x = def_x(index)
        anchor = "start" if index == 0 else ("end" if index == len(usable_rows) - 1 else "middle")
        svg_parts.extend([
            f'<line class="valuation-x-tick" x1="{x:.1f}" y1="{plot_bottom}" x2="{x:.1f}" y2="{plot_bottom + 4}"/>',
            f'<text class="valuation-axis-label x" x="{x:.1f}" y="{height - 10}" text-anchor="{anchor}">{dates[index].strftime("%Y/%m")}</text>',
        ])

    svg_parts.append(
        f'<path class="valuation-interquartile" d="{area_path}"/>'
    )
    for quantile in ["q10", "q25", "q50", "q75", "q90"]:
        svg_parts.append(
            f'<path class="valuation-band-line {quantile}" d="{def_path(f"{prefix}{quantile}")}"/>'
        )
    price_path = def_path("adj_close")
    svg_parts.extend([
        f'<path class="valuation-price-halo" d="{price_path}"/>',
        f'<path class="valuation-price-line" d="{price_path}"/>',
        f'<circle class="valuation-current-dot" cx="{def_x(len(usable_rows) - 1):.1f}" cy="{def_y(usable_rows[-1].get("adj_close")):.1f}" r="4"/>',
        f'<line class="valuation-axis-line" x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}"/>',
        "</svg>",
    ])
    return "".join(svg_parts)


def def_build_valuation_band_legend_html():
    items = [
        ("price", "Adj Close"),
        ("q10", "Q10"),
        ("q25", "Q25"),
        ("q50", "Q50"),
        ("q75", "Q75"),
        ("q90", "Q90"),
    ]
    return '<div class="band-legend">' + "".join(
        f'<span><i class="{class_name}"></i>{label}</span>'
        for class_name, label in items
    ) + "</div>"


def def_build_valuation_band_panels_html(payload):
    code = str(payload.get("code") or "")
    rows = def_read_valuation_band_rows(code)
    legend = def_build_valuation_band_legend_html()
    if not rows:
        empty_panel = (
            '<div class="valuation-empty">找不到 '
            + def_html_escape(VALUATION_BAND_CSV_TEMPLATE.format(code=code))
            + '；請先執行 VDF 估值計算引擎。</div>'
        )
        return (
            '<div class="valuation-grid" data-visual-lock="v'
            + VISUAL_LOCK_VERSION
            + '"><section class="valuation-panel"><div class="panel-head"><h3>Forward P/E Band</h3><span>Adj Close · 近 2 年</span></div>'
            + empty_panel
            + '</section><section class="valuation-panel"><div class="panel-head"><h3>P/B Band</h3><span>Adj Close · 近 2 年</span></div>'
            + empty_panel
            + "</section></div>"
        )

    first = rows[0]
    latest = rows[-1]
    date_range = f"{first.get('date')}—{latest.get('date')}"
    pe_svg = def_build_valuation_band_svg(code, rows, "pe")
    pb_svg = def_build_valuation_band_svg(code, rows, "pb")
    pe_reference = def_html_escape(latest.get("eps_reference"))
    report_period = def_html_escape(latest.get("report_period"))
    effective_date = def_html_escape(latest.get("effective_date"))
    return f"""
      <div class="valuation-grid" data-visual-lock="v{VISUAL_LOCK_VERSION}">
        <section class="valuation-panel">
          <div class="panel-head valuation-head"><div><h3>Forward P/E Band</h3><span>{def_html_escape(date_range)} · Adj Close</span></div><div class="valuation-kpis"><b>{def_html_number(latest.get('pe'))}×</b><em>{pe_reference} EPS {def_html_number(latest.get('forward_diluted_eps'))} · 中位數</em></div></div>
          <div class="valuation-chart">{pe_svg}</div>
          {legend}
        </section>
        <section class="valuation-panel">
          <div class="panel-head valuation-head"><div><h3>P/B Band</h3><span>{def_html_escape(date_range)} · Adj Close</span></div><div class="valuation-kpis"><b>{def_html_number(latest.get('pb'))}×</b><em>BVPS {def_html_number(latest.get('bvps'))} · {report_period}</em></div></div>
          <div class="valuation-chart">{pb_svg}</div>
          {legend}
        </section>
      </div>
      <div class="valuation-note">Forward P/E：美股／台股盈餘共識皆採中位數；下半年使用次年度完全稀釋 EPS，上半年以當年度與次年度前瞻區間為基準。P/B：BVPS 於表定財報公布後次一交易日生效（本期 {effective_date}）。估值帶為近兩年分位區間，不代表預測價格。</div>
    """


def def_build_rating_stack_html(ratings):
    rows = []
    for rating in ratings or []:
        total = sum(
            def_safe_int(rating.get(field)) or 0
            for field, _label, _class_name in RATING_STACK_SEGMENTS
        )
        segments = []
        for field, label, class_name in RATING_STACK_SEGMENTS:
            count = def_safe_int(rating.get(field)) or 0
            share = (count / total * 100) if total else 0
            segments.append(
                f'<span class="stack-segment {class_name}" '
                f'style="width:{share:.4f}%" '
                f'title="{def_html_escape(label)} {count}／{total}"></span>'
            )
        rows.append(
            '<div class="stack-row">'
            f'<div class="stack-date">{def_html_escape(rating.get("rating_date"))}</div>'
            f'<div class="stack-track">{"".join(segments)}</div>'
            f'<div class="stack-total">{total}</div>'
            "</div>"
        )

    legend = "".join(
        f'<span><i class="{class_name}"></i>{def_html_escape(label)}</span>'
        for _field, label, class_name in RATING_STACK_SEGMENTS
    )
    return (
        '<section class="stack-panel"><div class="panel-head">'
        '<h3>分析師評級構成堆疊圖</h3>'
        '<span>每期總評級數標示於右側</span></div>'
        f'<div class="stack-chart">{"".join(rows)}</div>'
        f'<div class="stack-legend">{legend}</div></section>'
    )


def def_build_code_compact_html(payload):
    target = payload.get("target") or {}
    yfinance_consensus = payload.get("yfinance") or {}
    comparison = payload.get("source_comparison") or {}
    ratings = payload.get("rating_history") or []
    eps_rows = payload.get("eps") or []
    sales_rows = payload.get("sales") or []
    latest_rating = ratings[0] if ratings else {}
    spectrum_html = def_build_target_spectrum_compact_html(payload)
    valuation_band_html = def_build_valuation_band_panels_html(payload)
    rating_stack_html = def_build_rating_stack_html(ratings)

    eps_table = def_build_table(
        ["年度", "更新日", "最低", "平均", "中位數", "最高", "分析師", "P/E"],
        [
            [
                def_html_escape(row.get("fiscal_year")),
                def_html_escape(row.get("rate_date")),
                def_html_number(row.get("estimate_low")),
                def_html_number(row.get("estimate_mean")),
                f'<strong>{def_html_number(row.get("estimate_median"))}</strong>',
                def_html_number(row.get("estimate_high")),
                def_html_escape(row.get("analyst_count")),
                def_html_number(row.get("forward_pe_median")),
            ]
            for row in eps_rows
        ],
        classes="compact-table eps-table",
    )

    sales_table = def_build_table(
        ["年度", "更新日", "最低", "平均", "中位數", "最高", "分析師", "幣別"],
        [
            [
                def_html_escape(row.get("fiscal_year")),
                def_html_escape(row.get("rate_date")),
                def_html_trillion(row.get("estimate_low")),
                def_html_trillion(row.get("estimate_mean")),
                f'<strong>{def_html_trillion(row.get("estimate_median"))}</strong>',
                def_html_trillion(row.get("estimate_high")),
                def_html_escape(row.get("analyst_count")),
                def_html_escape(row.get("currency")),
            ]
            for row in sales_rows
        ],
        classes="compact-table sales-table",
    )

    rating_table = def_build_table(
        ["更新日", "買進", "優於", "持有", "劣於", "賣出", "總數", "中位目標"],
        [
            [
                def_html_escape(row.get("rating_date")),
                def_html_escape(row.get("buy_count")),
                def_html_escape(row.get("outperform_count")),
                def_html_escape(row.get("hold_count")),
                def_html_escape(row.get("underperform_count")),
                def_html_escape(row.get("sell_count")),
                f'<strong>{def_html_escape(row.get("analyst_count"))}</strong>',
                def_html_number(row.get("target_median"), 0),
            ]
            for row in ratings
        ],
        classes="compact-table rating-table",
    )

    return f"""
    <section class="ticker-section">
      <div class="section-head">
        <div>
          <div class="eyebrow">{def_html_escape(payload.get('symbol'))}</div>
          <h2>{def_html_escape(payload.get('company_name'))} <span>{def_html_escape(payload.get('code'))}</span></h2>
        </div>
        <div class="section-actions"><span class="visual-lock-badge">Visual Lock v{VISUAL_LOCK_VERSION} · 420 px／2×2／雙圖</span><div class="source-links"><a class="source-link" href="{def_html_escape(payload.get('page_url'))}" target="_blank" rel="noopener noreferrer">FactSet ↗</a><a class="source-link" href="{def_html_escape(yfinance_consensus.get('source_url'))}" target="_blank" rel="noopener noreferrer">YFinance ↗</a></div></div>
      </div>

      <div class="overview-grid">
        <div class="cards">
          <article class="card card-current">
            <div class="label">目前 Adj Close</div>
            <div class="value">{def_html_number(yfinance_consensus.get('adj_close'))}</div>
            <div class="note">{def_html_escape(target.get('currency'))} · Beta {def_html_number(yfinance_consensus.get('beta'))}</div>
          </article>
          <article class="card card-factset">
            <div class="label">FactSet 目標價中位數</div>
            <div class="value accent">{def_html_number(target.get('target_median'))}</div>
            <div class="note">{def_html_percent(target.get('target_median_upside_pct'))}</div>
          </article>
          <article class="card card-rating">
            <div class="label">評級方向／來源一致性</div>
            <div class="value compact">{def_html_escape(def_display_rating_direction(def_cnyes_rating_direction(latest_rating)))} × {def_html_escape(def_display_recommendation(yfinance_consensus.get('recommendation_key')))}</div>
            <div class="note"><span class="status {str(comparison.get('agreement_gate') or '').lower()}">{def_html_escape(def_display_status(comparison.get('agreement_gate')))}</span></div>
          </article>
          <article class="card card-yfinance">
            <div class="label">YFinance 目標價中位數</div>
            <div class="value">{def_html_number(yfinance_consensus.get('target_median'))}</div>
            <div class="note">{def_html_percent(yfinance_consensus.get('target_median_upside_pct'))} · {def_html_escape(yfinance_consensus.get('analyst_count'))} 位分析師</div>
          </article>
        </div>
        {spectrum_html}
      </div>

      {valuation_band_html}

      <div class="matrix-grid">
        <section class="matrix-panel">
          <div class="panel-head"><h3>年度 EPS 共識</h3><span>每股盈餘 · TWD</span></div>
          {eps_table}
        </section>
        <section class="matrix-panel">
          <div class="panel-head"><h3>年度營收共識</h3><span>金額 · 兆 TWD</span></div>
          {sales_table}
        </section>
        <section class="matrix-panel rating-panel">
          <div class="panel-head"><h3>分析師評級歷史</h3><span>完整索引對齊</span></div>
          {rating_table}
        </section>
      </div>

      {rating_stack_html}
    </section>
    """


def def_html_datetime_compact(value):
    from datetime import datetime

    if value in [None, ""]:
        return "—"
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.strftime("%Y/%m/%d %H:%M UTC")
    except Exception:
        return text


def def_write_html(path, payloads, checks, gate_summary):
    from pathlib import Path

    check_table = def_build_table(
        ["代碼", "檢查", "實際", "預期", "狀態", "說明"],
        [
            [
                def_html_escape(row.get("code")),
                def_html_escape(def_display_identifier(row.get("check_id"))),
                def_html_escape(def_display_text(row.get("actual"))),
                def_html_escape(def_display_text(row.get("expected"))),
                f'<span class="status {str(row.get("status")).lower()}">{def_html_escape(def_display_status(row.get("status")))}</span>',
                def_html_escape(def_display_sentence(row.get("note"))),
            ]
            for row in checks
        ],
    )

    sections = "".join(
        def_build_code_compact_html(payload)
        for payload in payloads
    )
    generated = def_now_utc().strftime(DATETIME_OUTPUT_FORMAT)
    gate = gate_summary.get("gate")
    header_payload = payloads[0] if payloads else {}
    header_target = header_payload.get("target") or {}
    header_yfinance = header_payload.get("yfinance") or {}
    factset_updated = header_target.get("rate_date") or "—"
    yfinance_updated = def_html_datetime_compact(
        header_yfinance.get("captured_at_utc")
    )
    validation_text = (
        f"{gate_summary.get('pass_count')}/{gate_summary.get('check_count')} "
        f"{def_display_status(gate)}"
    )

    document = f"""<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA · FactSet × YFinance Consensus Dashboard</title>
<style>
:root{{--ink:#162235;--muted:#66758a;--line:#d9e1ea;--paper:#f3f6f9;--card:#fff;--navy:#12243c;--slate:#203751;--cyan:#4aa7b8;--red:#c9533c;--green:#1d7b55;--amber:#9c6a11;--q10:{VALUATION_BAND_COLORS['q10']};--q25:{VALUATION_BAND_COLORS['q25']};--q50:{VALUATION_BAND_COLORS['q50']};--q75:{VALUATION_BAND_COLORS['q75']};--q90:{VALUATION_BAND_COLORS['q90']};--band-fill:{VALUATION_BAND_COLORS['band_fill']};--chart-grid:{VALUATION_BAND_COLORS['grid']};--lock-max:{VISUAL_LOCK_MAX_WIDTH_PX}px;--lock-overview-left:{VISUAL_LOCK_OVERVIEW_LEFT_PX}px;--lock-card-h:{VISUAL_LOCK_CARD_HEIGHT_PX}px;--lock-spectrum-h:{VISUAL_LOCK_SPECTRUM_HEIGHT_PX}px;--lock-chart-h:{VISUAL_LOCK_VALUATION_HEIGHT_PX}px;--shadow:0 8px 24px rgba(18,36,60,.065)}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font-family:"IBM Plex Sans","Noto Sans TC","Microsoft JhengHei",Inter,Arial,sans-serif;font-size:13px;font-variant-numeric:tabular-nums;text-rendering:optimizeLegibility}}
.hero{{background:#111f35;color:#fff;border-bottom:3px solid var(--red)}} .hero-inner{{max-width:var(--lock-max);margin:auto;padding:18px 24px;display:flex;justify-content:space-between;align-items:center;gap:28px}} .hero-copy{{min-width:0}} .brand{{font-size:10px;font-weight:650;letter-spacing:.19em;text-transform:uppercase;color:#9db7ca}} h1{{margin:5px 0 2px;font-size:27px;font-weight:680;letter-spacing:-.025em}} .subtitle{{color:#c5d2df;font-size:11px;letter-spacing:.02em}}
.hero-meta{{display:grid;grid-template-columns:repeat(3,minmax(132px,1fr));gap:7px;min-width:450px}} .meta-item{{padding:7px 9px;border:1px solid rgba(255,255,255,.13);background:rgba(255,255,255,.055);border-radius:6px}} .meta-item span{{display:block;color:#91a9bd;font-size:8px;font-weight:700;letter-spacing:.11em;text-transform:uppercase}} .meta-item strong{{display:block;margin-top:3px;color:#fff;font-size:10px;font-weight:620;white-space:nowrap}} .meta-item.validation{{border-color:rgba(85,194,142,.48);background:rgba(36,132,88,.23)}} .generated{{grid-column:1/-1;text-align:right;color:#839aae;font-size:8px}}
main{{max-width:var(--lock-max);margin:14px auto 40px;padding:0 16px}} .ticker-section{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:17px;margin-bottom:14px;box-shadow:var(--shadow)}}
.section-head{{display:flex;justify-content:space-between;gap:16px;align-items:flex-end;border-bottom:1px solid var(--line);padding-bottom:10px}} .eyebrow{{font:9px ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted);letter-spacing:.09em}} h2{{margin:2px 0 0;font-size:20px;font-weight:670}} h2 span{{color:var(--cyan);font-weight:620}} .section-actions{{display:flex;align-items:center;gap:12px}} .visual-lock-badge{{border:1px solid #cbd5df;border-radius:999px;background:#f6f8fa;color:#4f6074;padding:4px 8px;font:700 8px ui-monospace,SFMono-Regular,Consolas,monospace;letter-spacing:.025em;white-space:nowrap}} .source-links{{display:flex;gap:12px}} .source-link{{color:var(--red);text-decoration:none;font-size:10px;font-weight:650}}
.overview-grid{{display:grid;grid-template-columns:var(--lock-overview-left) minmax(0,1fr);gap:12px;margin-top:12px;align-items:stretch}} .cards{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));grid-template-areas:"current factset" "rating yfinance";gap:9px}} .card-current{{grid-area:current}} .card-factset{{grid-area:factset}} .card-rating{{grid-area:rating}} .card-yfinance{{grid-area:yfinance}} .card{{border:1px solid var(--line);border-radius:7px;padding:12px;background:#fff;box-shadow:0 2px 9px rgba(18,36,60,.035);height:var(--lock-card-h);display:flex;flex-direction:column;justify-content:center;overflow:hidden}} .label{{font-size:9px;font-weight:650;letter-spacing:.035em;color:var(--muted)}} .value{{font-size:24px;font-weight:690;margin:7px 0 3px;letter-spacing:-.035em}} .value.accent{{color:var(--red)}} .value.compact{{font-size:14px;line-height:1.35;letter-spacing:-.015em}} .note{{font-size:9px;color:var(--muted)}} .status{{display:inline-block;padding:2px 6px;border-radius:999px;font-size:9px;font-weight:700}} .status.pass,.status.match{{background:#e6f3ed;color:var(--green)}} .status.warn,.status.review,.status.incomplete{{background:#fff1d7;color:var(--amber)}} .status.fail,.status.conflict,.status.currency_mismatch{{background:#fae8e5;color:#9f352b}}
.spectrum-panel,.matrix-panel,.stack-panel{{border:1px solid var(--line);border-radius:7px;background:#fbfcfd}} .spectrum-panel{{padding:10px 12px;min-width:0;height:var(--lock-spectrum-h);display:flex;flex-direction:column}} .panel-head{{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-bottom:5px}} .panel-head h3{{margin:0;font-size:12px;font-weight:690;letter-spacing:.005em}} .panel-head span{{font-size:8px;color:var(--muted);white-space:nowrap}} .spectrum-wrap{{overflow-x:auto;flex:1;min-height:0}} .target-spectrum{{display:block;width:100%;min-width:700px;height:214px}} .target-spectrum text{{font-family:"IBM Plex Sans","Noto Sans TC","Microsoft JhengHei",Arial,sans-serif;fill:var(--ink)}} .target-spectrum .source-name{{font-size:13px;font-weight:720}} .target-spectrum .spectrum-range{{stroke:rgba(22,34,53,.24);stroke-width:1}} .target-spectrum .hollow-circle,.target-spectrum .hollow-triangle{{fill:#fff;stroke:#162235;stroke-width:2.5}} .target-spectrum .median-label,.target-spectrum .mean-label{{font-size:11px;font-weight:650;text-anchor:middle}} .target-spectrum .range-label{{font-size:9px;fill:var(--muted)}} .target-spectrum .range-label.high{{text-anchor:end}} .target-spectrum .axis-line{{stroke:#aeb9c5;stroke-width:1}} .target-spectrum .axis-label{{font-size:8px;fill:var(--muted)}} .target-spectrum .axis-label.end{{text-anchor:end}} .target-spectrum .adj-close-line{{stroke:#162235;stroke-width:1.7;stroke-dasharray:6 5}} .target-spectrum .adj-close-label-bg{{fill:#162235}} .target-spectrum .adj-close-label{{fill:#fff;font-size:10px;font-weight:650}} .target-spectrum .marker-legend text{{font-size:8px;fill:var(--muted)}}
.valuation-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:12px}} .valuation-panel{{border:1px solid var(--line);border-radius:7px;background:#fbfcfd;padding:10px 12px;min-width:0;overflow:hidden}} .valuation-head{{align-items:flex-start;margin-bottom:2px}} .valuation-head>div:first-child{{min-width:0}} .valuation-kpis{{display:flex;align-items:baseline;justify-content:flex-end;gap:7px;text-align:right;white-space:nowrap}} .valuation-kpis b{{font-size:14px;color:var(--red);font-weight:720}} .valuation-kpis em{{font-size:8px;color:var(--muted);font-style:normal}} .valuation-chart{{height:var(--lock-chart-h);min-width:0}} .valuation-svg{{display:block;width:100%;height:100%;overflow:visible}} .valuation-svg text{{font-family:"IBM Plex Sans","Noto Sans TC","Microsoft JhengHei",Arial,sans-serif}} .valuation-grid-line{{stroke:var(--chart-grid);stroke-width:1}} .valuation-axis-line,.valuation-x-tick{{stroke:#9eacba;stroke-width:1}} .valuation-axis-label{{fill:#718095;font-size:9px}} .valuation-axis-label.y{{text-anchor:end}} .valuation-interquartile{{fill:var(--band-fill);opacity:.68;stroke:none}} .valuation-band-line{{fill:none;stroke-width:1.35;stroke-linejoin:round;stroke-linecap:round}} .valuation-band-line.q10{{stroke:var(--q10)}} .valuation-band-line.q25{{stroke:var(--q25)}} .valuation-band-line.q50{{stroke:var(--q50);stroke-width:1.9}} .valuation-band-line.q75{{stroke:var(--q75)}} .valuation-band-line.q90{{stroke:var(--q90)}} .valuation-price-halo{{fill:none;stroke:#fff;stroke-width:5;stroke-linejoin:round;stroke-linecap:round;opacity:.9}} .valuation-price-line{{fill:none;stroke:var(--ink);stroke-width:2.25;stroke-linejoin:round;stroke-linecap:round}} .valuation-current-dot{{fill:#fff;stroke:var(--ink);stroke-width:2.2}} .band-legend{{display:flex;justify-content:flex-end;gap:10px;flex-wrap:wrap;min-height:14px;margin-top:1px;color:var(--muted);font-size:8px}} .band-legend span{{display:inline-flex;align-items:center;gap:4px}} .band-legend i{{display:inline-block;width:12px;height:2px;border-radius:2px;background:var(--ink)}} .band-legend i.q10{{background:var(--q10)}} .band-legend i.q25{{background:var(--q25)}} .band-legend i.q50{{background:var(--q50)}} .band-legend i.q75{{background:var(--q75)}} .band-legend i.q90{{background:var(--q90)}} .valuation-empty{{height:var(--lock-chart-h);display:grid;place-items:center;border:1px dashed #cbd5df;border-radius:5px;color:var(--muted);font-size:10px;background:#fff}} .valuation-note{{margin:6px 2px 0;color:var(--muted);font-size:8px;line-height:1.45}}
.matrix-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:11px;align-items:start}} .matrix-panel{{padding:9px;min-width:0}} .table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:5px;background:#fff}} table{{border-collapse:separate;border-spacing:0;width:100%;font-size:9px;table-layout:fixed}} .compact-table table{{min-width:0}} .compact-table th,.compact-table td{{width:12.5%}} th{{background:var(--navy);color:#fff;text-align:right;padding:6px 4px;font-weight:620;line-height:1.15;white-space:normal;vertical-align:middle}} th:first-child,td:first-child{{text-align:left}} td{{padding:6px 4px;text-align:right;border-bottom:1px solid #ebf0f4;color:#35445a;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;vertical-align:middle}} tbody tr:last-child td{{border-bottom:0}} tbody tr:hover td{{background:#f4f8fb}} strong{{color:#111a2a}}
.stack-panel{{margin-top:10px;padding:10px 12px}} .stack-chart{{display:grid;gap:6px;margin-top:7px}} .stack-row{{display:grid;grid-template-columns:76px minmax(0,1fr) 30px;gap:8px;align-items:center}} .stack-date,.stack-total{{font:9px ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted)}} .stack-total{{text-align:right;font-weight:650;color:var(--ink)}} .stack-track{{height:14px;display:flex;overflow:hidden;border-radius:3px;background:#e8edf2;outline:1px solid rgba(22,34,53,.08)}} .stack-segment{{display:block;height:100%;min-width:0}} .stack-segment.buy,.stack-legend i.buy{{background:#163b5c}} .stack-segment.outperform,.stack-legend i.outperform{{background:#58a3b8}} .stack-segment.hold,.stack-legend i.hold{{background:#d8a33f}} .stack-segment.underperform,.stack-legend i.underperform{{background:#d87b63}} .stack-segment.sell,.stack-legend i.sell{{background:#a6403a}} .stack-legend{{display:flex;justify-content:flex-end;gap:13px;flex-wrap:wrap;margin-top:7px;font-size:8px;color:var(--muted)}} .stack-legend span{{display:inline-flex;gap:5px;align-items:center}} .stack-legend i{{display:inline-block;width:8px;height:8px;border-radius:2px}}
.qa{{background:#fff;border:1px solid var(--line);border-radius:8px;box-shadow:var(--shadow)}} .qa summary{{list-style:none;cursor:pointer;padding:11px 14px;font-size:11px;font-weight:680;display:flex;justify-content:space-between;align-items:center}} .qa summary::-webkit-details-marker{{display:none}} .qa-body{{padding:0 14px 14px}} .qa table{{min-width:760px;font-size:9px}} .qa th,.qa td{{padding:6px}} .footnote{{font-size:9px;color:var(--muted);line-height:1.55;margin:10px 0 0}}
@media(max-width:1250px){{.matrix-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.rating-panel{{grid-column:1/-1}}}} @media(max-width:1100px){{.hero-inner{{align-items:flex-start}}.hero-meta{{min-width:400px}}.overview-grid{{grid-template-columns:1fr}}}} @media(max-width:{VISUAL_LOCK_DESKTOP_BREAKPOINT_PX}px){{.valuation-grid{{grid-template-columns:1fr}}}} @media(max-width:760px){{.hero-inner{{display:block}}.hero-meta{{grid-template-columns:1fr;margin-top:12px;min-width:0}}.generated{{text-align:left}}h1{{font-size:23px}}.section-head{{align-items:flex-start}}.section-actions{{align-items:flex-end;flex-direction:column-reverse}}.visual-lock-badge{{display:none}}.cards{{grid-template-columns:1fr;grid-template-areas:"current" "factset" "rating" "yfinance"}}.card{{height:auto;min-height:108px}}.matrix-grid{{grid-template-columns:1fr}}.rating-panel{{grid-column:auto}}.ticker-section{{padding:12px}}.panel-head{{display:block}}.panel-head span{{display:block;margin-top:2px}}.valuation-kpis{{justify-content:flex-start;margin-top:4px;text-align:left}}.valuation-chart{{height:250px}}}}
</style>
</head>
<body>
<header class="hero"><div class="hero-inner"><div class="hero-copy"><div class="brand">Veritas Intelligence Analytics</div><h1>FactSet × YFinance Consensus Dashboard</h1><div class="subtitle">目標價雙光譜 · Forward P/E Band · P/B Band · EPS／營收／評級</div></div><div class="hero-meta"><div class="meta-item"><span>FactSet 更新</span><strong>{def_html_escape(factset_updated)}</strong></div><div class="meta-item"><span>YFinance 更新</span><strong>{def_html_escape(yfinance_updated)}</strong></div><div class="meta-item validation"><span>Validation</span><strong>{def_html_escape(validation_text)}</strong></div><div class="generated">產生時間 {def_html_escape(generated)} · Visual Lock v{VISUAL_LOCK_VERSION}</div></div></div></header>
<main>{sections}<details class="qa"><summary><span>品質驗證矩陣</span><span class="status {str(gate or '').lower()}">{def_html_escape(validation_text)}</span></summary><div class="qa-body">{check_table}<p class="footnote">FactSet 共識資料由鉅亨網公開資料端點取得；YFinance 欄位由 YFinance Python 套件取得。雙來源可能因資料商、分析師樣本與更新時間不同而產生差異；不進行跨來源平均。數值僅供研究與驗證，不構成投資建議。</p></div></details></main>
</body></html>"""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    return output_path


def def_timestamp_to_date(value):
    text = str(value or "").strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    return def_now_utc().strftime("%Y-%m-%d")


def def_build_run_id():
    return def_now_utc().strftime("RUN_%Y%m%d_%H%M%S_%f_UTC")


def def_build_consensus_long_rows(raw_records, run_id):
    import json

    rows = []
    seen = {}
    for raw in raw_records:
        code = def_validate_code(raw.get("code"))
        symbol = str(raw.get("symbol") or "").strip()
        source = str(raw.get("source") or "UNKNOWN").strip()
        section = str(raw.get("section") or "UNKNOWN").strip()
        metric = str(raw.get("metric") or "UNKNOWN").strip()
        period = str(raw.get("period") or "").strip() or None
        fetched_at = raw.get("fetched_at_utc") or def_now_utc_iso()
        as_of_date = def_timestamp_to_date(fetched_at)
        value = def_record_safe_value(raw.get("value"))
        value_text = None if value is None else str(value)
        yfinance_ticker = None
        try:
            yfinance_ticker = def_cnyes_symbol_to_yfinance_ticker(symbol, code)
        except Exception:
            yfinance_ticker = None

        key_payload = {
            "as_of_date": as_of_date,
            "code": code,
            "section": section,
            "period": period,
            "metric": metric,
            "source": source,
        }
        record_key = def_sha256_bytes(
            json.dumps(
                key_payload,
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        )
        raw_hash = def_sha256_bytes(
            json.dumps(
                def_json_ready(raw),
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        )
        if record_key in seen:
            if seen[record_key] == raw_hash:
                continue
            raise ValueError(
                "CONSENSUS_LONG_KEY_COLLISION: "
                f"{code}/{section}/{period}/{metric}/{source}"
            )
        seen[record_key] = raw_hash
        rows.append({
            "record_key": record_key,
            "as_of_date": as_of_date,
            "fetched_at_utc": fetched_at,
            "code": code,
            "yfinance_ticker": yfinance_ticker,
            "symbol": symbol,
            "company_name": raw.get("company_name"),
            "section": section,
            "period": period,
            "rate_date": raw.get("rate_date"),
            "metric": metric,
            "value_text": value_text,
            "value_number": def_safe_float(value),
            "currency": raw.get("currency"),
            "source": source,
            "source_mode": raw.get("source_mode"),
            "source_url": raw.get("source_url"),
            "method": raw.get("method"),
            "method_status": raw.get("method_status"),
            "raw_hash": raw_hash,
            "schema_version": SCHEMA_VERSION,
            "engine_version": ENGINE_VERSION,
            "run_id": run_id,
        })
    return rows


def def_duckdb_columns():
    return [
        ("record_key", "VARCHAR PRIMARY KEY"),
        ("as_of_date", "VARCHAR"),
        ("fetched_at_utc", "VARCHAR"),
        ("code", "VARCHAR"),
        ("yfinance_ticker", "VARCHAR"),
        ("symbol", "VARCHAR"),
        ("company_name", "VARCHAR"),
        ("section", "VARCHAR"),
        ("period", "VARCHAR"),
        ("rate_date", "VARCHAR"),
        ("metric", "VARCHAR"),
        ("value_text", "VARCHAR"),
        ("value_number", "DOUBLE"),
        ("currency", "VARCHAR"),
        ("source", "VARCHAR"),
        ("source_mode", "VARCHAR"),
        ("source_url", "VARCHAR"),
        ("method", "VARCHAR"),
        ("method_status", "VARCHAR"),
        ("raw_hash", "VARCHAR"),
        ("schema_version", "VARCHAR"),
        ("engine_version", "VARCHAR"),
        ("run_id", "VARCHAR"),
    ]


def def_persist_duckdb(long_rows, database_path, parquet_path, run_id):
    from pathlib import Path

    try:
        import duckdb
    except Exception as exc:
        result = {
            "status": "FAIL_DUCKDB_UNAVAILABLE" if DUCKDB_REQUIRED else "WARN_DUCKDB_UNAVAILABLE",
            "error": "Install with: py -m pip install duckdb",
            "rows": 0,
        }
        if DUCKDB_REQUIRED:
            raise RuntimeError(result["error"]) from exc
        return result

    database = Path(database_path)
    parquet = Path(parquet_path)
    database.parent.mkdir(parents=True, exist_ok=True)
    parquet.parent.mkdir(parents=True, exist_ok=True)
    columns = def_duckdb_columns()
    column_names = [name for name, _ in columns]
    create_columns = ", ".join(
        f'"{name}" {data_type}' for name, data_type in columns
    )
    placeholders = ", ".join(["?"] * len(columns))
    insert_columns = ", ".join(f'"{name}"' for name in column_names)
    values = [tuple(row.get(name) for name in column_names) for row in long_rows]
    connection = duckdb.connect(str(database))
    try:
        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            f'CREATE TABLE IF NOT EXISTS "{CONSENSUS_TABLE_NAME}" '
            f'({create_columns})'
        )
        if values:
            connection.executemany(
                f'DELETE FROM "{CONSENSUS_TABLE_NAME}" WHERE record_key = ?',
                [(row[0],) for row in values],
            )
            for start in range(0, len(values), DUCKDB_BATCH_SIZE):
                batch = values[start:start + DUCKDB_BATCH_SIZE]
                connection.executemany(
                    f'INSERT INTO "{CONSENSUS_TABLE_NAME}" '
                    f'({insert_columns}) VALUES ({placeholders})',
                    batch,
                )
        connection.execute(
            f'CREATE OR REPLACE VIEW consensus_current AS '
            f'SELECT * FROM "{CONSENSUS_TABLE_NAME}" '
            "QUALIFY ROW_NUMBER() OVER ("
            "PARTITION BY code, section, period, metric, source "
            "ORDER BY as_of_date DESC, fetched_at_utc DESC"
            ") = 1"
        )
        connection.execute("COMMIT")
        parquet_sql_path = str(parquet).replace("'", "''")
        run_id_sql = str(run_id).replace("'", "''")
        connection.execute(
            f"COPY (SELECT * FROM \"{CONSENSUS_TABLE_NAME}\" "
            f"WHERE run_id = '{run_id_sql}') TO '{parquet_sql_path}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        total_rows = connection.execute(
            f'SELECT COUNT(*) FROM "{CONSENSUS_TABLE_NAME}"'
        ).fetchone()[0]
        current_rows = connection.execute(
            "SELECT COUNT(*) FROM consensus_current"
        ).fetchone()[0]
    except Exception:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        connection.close()

    return {
        "status": "PASS",
        "database_path": str(database),
        "parquet_path": str(parquet),
        "run_rows": len(long_rows),
        "history_rows": int(total_rows),
        "current_rows": int(current_rows),
        "database_sha256": def_sha256_file(database),
        "parquet_sha256": def_sha256_file(parquet),
        "duckdb_version": getattr(duckdb, "__version__", None),
    }


def def_save_outputs(payloads, raw_records, matrix_rows, checks, output_dir, run_id=None):
    from pathlib import Path

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    run_id_value = run_id or def_build_run_id()
    gate_summary = def_quality_gate(checks)

    payload_path = def_write_json(
        output_path / OUTPUT_PAYLOAD_JSON,
        {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "generated_at_utc": def_now_utc_iso(),
            "payloads": payloads,
        },
    )
    raw_csv_path = def_write_csv(output_path / OUTPUT_RAW_CSV, raw_records)
    matrix_csv_path = def_write_csv(output_path / OUTPUT_MATRIX_CSV, matrix_rows)
    quality_csv_path = def_write_csv(output_path / OUTPUT_QUALITY_CSV, checks)
    parquet_result = def_try_write_parquet(output_path / OUTPUT_RAW_PARQUET, raw_records)
    long_rows = def_build_consensus_long_rows(raw_records, run_id_value)
    long_csv_path = def_write_csv(output_path / OUTPUT_LONG_CSV, long_rows)
    duckdb_result = def_persist_duckdb(
        long_rows=long_rows,
        database_path=output_path / OUTPUT_DUCKDB,
        parquet_path=output_path / OUTPUT_LONG_PARQUET,
        run_id=run_id_value,
    )

    if PARQUET_REQUIRED and parquet_result["status"] != "PASS":
        gate_summary["gate"] = "FAIL_CLOSED"
        gate_summary["fail_count"] += 1

    html_path = def_write_html(
        output_path / OUTPUT_HTML,
        payloads=payloads,
        checks=checks,
        gate_summary=gate_summary,
    )

    files = [
        payload_path,
        raw_csv_path,
        matrix_csv_path,
        quality_csv_path,
        long_csv_path,
        html_path,
    ]
    parquet_path = output_path / OUTPUT_RAW_PARQUET
    if parquet_path.exists():
        files.append(parquet_path)
    long_parquet_path = output_path / OUTPUT_LONG_PARQUET
    if long_parquet_path.exists():
        files.append(long_parquet_path)
    duckdb_path = output_path / OUTPUT_DUCKDB
    if duckdb_path.exists():
        files.append(duckdb_path)

    manifest = {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "generated_at_utc": def_now_utc_iso(),
        "run_id": run_id_value,
        "schema_version": SCHEMA_VERSION,
        "gate": gate_summary,
        "parquet": parquet_result,
        "duckdb": duckdb_result,
        "counts": {
            "tickers": len(payloads),
            "raw_records": len(raw_records),
            "matrix_rows": len(matrix_rows),
            "quality_checks": len(checks),
            "long_records": len(long_rows),
            "eps_items": sum(len(item.get("eps") or []) for item in payloads),
            "sales_items": sum(len(item.get("sales") or []) for item in payloads),
            "rating_items": sum(len(item.get("rating_history") or []) for item in payloads),
            "yfinance_items": sum(
                1 for item in payloads if item.get("yfinance")
            ),
            "comparison_items": sum(
                len(def_deep_get(item, ["source_comparison", "metrics"], default=[]))
                for item in payloads
            ),
        },
        "files": [
            {
                "path": str(file_path),
                "size_bytes": file_path.stat().st_size,
                "sha256": def_sha256_file(file_path),
            }
            for file_path in files
        ],
    }
    manifest_path = def_write_json(output_path / OUTPUT_MANIFEST_JSON, manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


# =============================================================================
# def 10 · BUILT-IN UNIT TESTS
# =============================================================================

def def_run_builtin_unit_tests():
    import json

    tests = []

    def def_test(test_id, function):
        try:
            function()
            tests.append({"test_id": test_id, "status": "PASS", "error": None})
        except Exception as exc:
            tests.append({"test_id": test_id, "status": "FAIL", "error": str(exc)})

    def def_assert(condition, message):
        if not condition:
            raise AssertionError(message)

    def def_test_code_normalization():
        def_assert(def_validate_code("2330.TW") == "2330", "TW suffix removal")
        def_assert(def_validate_code("3324.TWO") == "3324", "TWO suffix removal")

    def def_test_invalid_code():
        try:
            def_validate_code("../2330")
        except ValueError:
            return
        raise AssertionError("invalid code must fail")

    def def_test_assigned_json_parser():
        html_text = '<script>__NEXT_DATA__ = {"props":{"pageProps":{"symbol":"TWS:2330:STOCK"}}};x=1</script>'
        value = def_extract_next_data(html_text)
        def_assert(
            value["props"]["pageProps"]["symbol"] == "TWS:2330:STOCK",
            "NEXT parser",
        )

    def def_test_env_fallback():
        def_assert(def_extract_env("<html></html>") == {}, "ENV optional")

    def def_test_envelope():
        value = def_validate_api_envelope(
            {"statusCode": 200, "message": "OK", "data": [1, 2]},
            "UNIT",
        )
        def_assert(value == [1, 2], "envelope data")

    def def_test_target_normalization():
        source = {
            "data": {
                "chName": "台積電",
                "last": 100,
                "feLow": 90,
                "feMean": 110,
                "feMedian": 108,
                "feHigh": 120,
                "numEst": 10,
            },
            "source_mode": "UNIT",
            "url": "https://example.com",
        }
        row = def_normalize_target("2330", "TWS:2330:STOCK", "x", source)
        def_assert(row["target_median_upside_pct"] == 0.08, "upside")

    def def_test_rating_all_items():
        source = {
            "data": {
                "chName": "台積電",
                "rateDate": [1700000000, 1690000000],
                "feMark": [1.0, 1.1],
                "feBuy": [3, 2],
                "feOver": [1, 1],
                "feHold": [1, 1],
                "feUnder": [0, 0],
                "feSell": [0, 0],
                "feMedian": [100, 90],
            },
            "source_mode": "UNIT",
            "url": "https://example.com",
        }
        rows = def_normalize_rating_history("2330", "TWS:2330:STOCK", "x", source)
        def_assert(len(rows) == 2, "must keep every rating item")
        def_assert(rows[0]["analyst_count"] == 5, "rating sum")

    def def_test_estimate_all_items():
        source = {
            "data": [
                {"financialYear": 2027, "feMedian": 20, "feLow": 18, "feHigh": 22},
                {"financialYear": 2026, "feMedian": 10, "feLow": 9, "feHigh": 11},
            ],
            "source_mode": "UNIT",
            "url": "https://example.com",
        }
        rows = def_normalize_estimate_rows(
            "2330", "TWS:2330:STOCK", "x", source, "eps", 100
        )
        def_assert([row["fiscal_year"] for row in rows] == [2026, 2027], "sort all items")
        def_assert(rows[0]["forward_pe_median"] == 10.0, "forward pe")

    def def_test_yfinance_ticker_mapping():
        def_assert(
            def_cnyes_symbol_to_yfinance_ticker("TWS:2330:STOCK", "2330")
            == "2330.TW",
            "TWSE suffix",
        )
        def_assert(
            def_cnyes_symbol_to_yfinance_ticker("TWO:3324:STOCK", "3324")
            == "3324.TWO",
            "TPEX suffix",
        )

    def def_test_yfinance_info_normalization():
        source = {
            "data": {
                "symbol": "2330.TW",
                "currency": "TWD",
                "currentPrice": 100,
                "adjClose": 100,
                "beta": 1.25,
                "targetLowPrice": 90,
                "targetMeanPrice": 110,
                "targetMedianPrice": 108,
                "targetHighPrice": 120,
                "numberOfAnalystOpinions": 10,
                "recommendationMean": 1.5,
                "recommendationKey": "strong_buy",
            },
            "source_mode": "UNIT",
            "url": "https://finance.yahoo.com/quote/2330.TW/",
            "captured_at_utc": "2026-08-15T00:00:00+00:00",
        }
        row = def_normalize_yfinance_consensus(
            "2330", "TWS:2330:STOCK", "2330.TW", source
        )
        def_assert(row["target_median_upside_pct"] == 0.08, "yf upside")
        def_assert(row["adj_close"] == 100, "yf adj close")
        def_assert(row["beta"] == 1.25, "yf beta")
        def_assert(row["rating_direction"] == "POSITIVE", "yf rating")

    def def_test_target_spectrum():
        target = {
            "current_price": 100,
            "target_low": 105,
            "target_mean": 120,
            "target_median": 118,
            "target_high": 140,
            "currency": "TWD",
        }
        yfinance_consensus = {
            "current_price": 100,
            "adj_close": 100,
            "beta": 1.25,
            "target_low": 110,
            "target_mean": 125,
            "target_median": 122,
            "target_high": 135,
            "currency": "TWD",
        }
        spectrum = def_build_target_spectrum(target, yfinance_consensus)
        def_assert(spectrum["status"] == "PASS", "spectrum complete")
        def_assert(len(spectrum["sources"]) == 2, "two spectrum sources")
        def_assert(
            spectrum["markers"]["median"] == "HOLLOW_CIRCLE",
            "median marker",
        )
        def_assert(
            spectrum["markers"]["mean"] == "HOLLOW_TRIANGLE",
            "mean marker",
        )
        def_assert(
            spectrum["adj_close_position"]
            < spectrum["sources"][0]["low_position"],
            "aligned axis",
        )

    def def_test_source_comparison_all_items():
        target = {
            "current_price": 100,
            "target_low": 90,
            "target_mean": 110,
            "target_median": 108,
            "target_high": 120,
            "analyst_count": 10,
            "currency": "TWD",
        }
        rating = {"positive_count": 9, "neutral_count": 1, "negative_count": 0}
        yfinance_consensus = {
            "current_price": 101,
            "target_low": 91,
            "target_mean": 111,
            "target_median": 109,
            "target_high": 121,
            "analyst_count": 10,
            "currency": "TWD",
            "rating_direction": "POSITIVE",
        }
        result = def_build_source_comparison(target, rating, yfinance_consensus)
        def_assert(len(result["metrics"]) == 7, "all comparison items")
        def_assert(result["agreement_gate"] == "MATCH", "agreement gate")

    def def_test_rating_direction_normalization():
        def_assert(def_normalize_rating_direction("strong_buy") == "POSITIVE", "buy")
        def_assert(def_normalize_rating_direction("hold") == "NEUTRAL", "hold")
        def_assert(def_normalize_rating_direction("underperform") == "NEGATIVE", "sell")

    def def_test_display_labels():
        def_assert(def_display_metric_label("TARGET_MEDIAN") == "目標價中位數", "metric")
        def_assert(def_display_status("MATCH") == "一致", "status")
        def_assert(def_display_recommendation("strong_buy") == "強力買進", "rating")
        def_assert(
            def_display_source_mode("OFFLINE_YFINANCE_INFO_FIXTURE")
            == "YFinance 離線回歸樣本",
            "source mode",
        )
        def_assert(def_display_identifier("source_url") == "Source URL", "title case")

    def def_test_valuation_band_visual_lock():
        rows = [
            {
                "date": "2026/08/13",
                "adj_close": 2435,
                "pe_price_q10": 2032,
                "pe_price_q25": 2220,
                "pe_price_q50": 2490,
                "pe_price_q75": 2715,
                "pe_price_q90": 2931,
            },
            {
                "date": "2026/08/14",
                "adj_close": 2395,
                "pe_price_q10": 2032,
                "pe_price_q25": 2220,
                "pe_price_q50": 2490,
                "pe_price_q75": 2715,
                "pe_price_q90": 2931,
            },
        ]
        svg = def_build_valuation_band_svg("2330", rows, "pe")
        def_assert('class="valuation-svg"' in svg, "valuation svg")
        def_assert('class="valuation-price-line"' in svg, "adj close line")
        def_assert('valuation-band-line q50' in svg, "median band")

    def def_test_yfinance_price_target_merge():
        selected = {"targetMeanPrice": 100.0, "targetMedianPrice": None}
        analysis = {
            "get_analyst_price_targets": {
                "mean": 101.0,
                "median": 99.0,
                "low": 80.0,
                "high": 120.0,
            }
        }
        merged = def_merge_yfinance_price_targets(selected, analysis)
        def_assert(merged["targetMeanPrice"] == 100.0, "info keeps priority")
        def_assert(merged["targetMedianPrice"] == 99.0, "dedicated median fallback")
        def_assert(merged["targetLowPrice"] == 80.0, "dedicated low fallback")

    def def_test_yfinance_method_isolation():
        class FakeTicker:
            def get_analyst_price_targets(self):
                return {"mean": 100.0}

            def get_earnings_estimate(self):
                raise RuntimeError("fixture error")

        original_methods = list(YFINANCE_ANALYSIS_METHODS)
        try:
            YFINANCE_ANALYSIS_METHODS[:] = [
                "get_analyst_price_targets",
                "get_earnings_estimate",
                "get_revenue_estimate",
            ]
            analysis, states = def_call_yfinance_analysis_methods(FakeTicker())
            def_assert(analysis["get_analyst_price_targets"]["mean"] == 100.0, "pass")
            def_assert(states["get_earnings_estimate"]["status"] == "ERROR", "error")
            def_assert(states["get_revenue_estimate"]["status"] == "UNAVAILABLE", "missing")
        finally:
            YFINANCE_ANALYSIS_METHODS[:] = original_methods

    def def_test_yfinance_analysis_long_records():
        payload = {
            "code": "2330",
            "symbol": "TWS:2330:STOCK",
            "company_name": "TSMC",
            "fetched_at_utc": "2026-08-27T00:00:00+00:00",
            "yfinance": {
                "captured_at_utc": "2026-08-27T00:00:00+00:00",
                "currency": "TWD",
                "source_mode": "YFINANCE_CONSENSUS_BUNDLE_LIVE",
                "source_url": "https://finance.yahoo.com/quote/2330.TW/",
            },
            "endpoint_meta": {
                "yfinance": {
                    "method_status": {
                        "get_earnings_estimate": {"status": "PASS"}
                    }
                }
            },
            "yfinance_analysis": {
                "get_earnings_estimate": [
                    {"index": "+1y", "avg": 120.5, "low": 110.0}
                ]
            },
        }
        rows = def_build_yfinance_analysis_records(payload)
        def_assert(len(rows) == 2, "two metrics")
        def_assert(all(row["period"] == "+1y" for row in rows), "period")
        def_assert(all(row["method_status"] == "PASS" for row in rows), "status")

    def def_test_consensus_long_key_idempotence():
        raw = [{
            "fetched_at_utc": "2026-08-27T00:00:00+00:00",
            "code": "2330",
            "symbol": "TWS:2330:STOCK",
            "company_name": "TSMC",
            "section": "EPS_ESTIMATE",
            "period": "2027",
            "metric": "estimate_median",
            "value": 120.5,
            "currency": "TWD",
            "source": "FactSet",
            "source_mode": "OFFLINE",
            "source_url": "https://example.invalid/",
        }]
        first = def_build_consensus_long_rows(raw, "RUN_A")
        second = def_build_consensus_long_rows(raw, "RUN_B")
        def_assert(first[0]["record_key"] == second[0]["record_key"], "stable key")
        def_assert(first[0]["raw_hash"] == second[0]["raw_hash"], "stable raw hash")
        def_assert(first[0]["value_number"] == 120.5, "numeric projection")

    def def_test_checkpoint_input_hash():
        first = def_compute_pipeline_input_hash(["2330"], as_of_date="2026-08-27")
        same = def_compute_pipeline_input_hash(["2330"], as_of_date="2026-08-27")
        next_day = def_compute_pipeline_input_hash(["2330"], as_of_date="2026-08-28")
        def_assert(first == same, "same input")
        def_assert(first != next_day, "daily refresh boundary")

    def def_test_duckdb_schema_contract():
        names = [name for name, _ in def_duckdb_columns()]
        def_assert(names[0] == "record_key", "primary key first")
        def_assert("raw_hash" in names, "raw hash")
        def_assert("run_id" in names, "run id")
        def_assert(len(names) == len(set(names)), "unique columns")

    def_test("UT01_CODE_NORMALIZATION", def_test_code_normalization)
    def_test("UT02_INVALID_CODE_FAIL_CLOSED", def_test_invalid_code)
    def_test("UT03_NEXT_DATA_PARSER", def_test_assigned_json_parser)
    def_test("UT04_ENV_OPTIONAL", def_test_env_fallback)
    def_test("UT05_API_ENVELOPE", def_test_envelope)
    def_test("UT06_TARGET_NORMALIZATION", def_test_target_normalization)
    def_test("UT07_RATING_ALL_ITEMS", def_test_rating_all_items)
    def_test("UT08_ESTIMATE_ALL_ITEMS", def_test_estimate_all_items)
    def_test("UT09_YFINANCE_TICKER_MAPPING", def_test_yfinance_ticker_mapping)
    def_test("UT10_YFINANCE_INFO_NORMALIZATION", def_test_yfinance_info_normalization)
    def_test("UT11_SOURCE_COMPARISON_ALL_ITEMS", def_test_source_comparison_all_items)
    def_test("UT12_RATING_DIRECTION_NORMALIZATION", def_test_rating_direction_normalization)
    def_test("UT13_DISPLAY_LABELS", def_test_display_labels)
    def_test("UT14_TARGET_SPECTRUM", def_test_target_spectrum)
    def_test("UT15_VALUATION_BAND_VISUAL_LOCK", def_test_valuation_band_visual_lock)
    def_test("UT16_YFINANCE_PRICE_TARGET_MERGE", def_test_yfinance_price_target_merge)
    def_test("UT17_YFINANCE_METHOD_ISOLATION", def_test_yfinance_method_isolation)
    def_test("UT18_YFINANCE_ANALYSIS_LONG_RECORDS", def_test_yfinance_analysis_long_records)
    def_test("UT19_CONSENSUS_LONG_KEY_IDEMPOTENCE", def_test_consensus_long_key_idempotence)
    def_test("UT20_CHECKPOINT_INPUT_HASH", def_test_checkpoint_input_hash)
    def_test("UT21_DUCKDB_SCHEMA_CONTRACT", def_test_duckdb_schema_contract)

    return tests


# =============================================================================
# def 11 · PIPELINE
# =============================================================================

def def_atomic_write_json(path, data):
    import json
    import os
    from pathlib import Path

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(
        f"{output_path.name}.tmp.{os.getpid()}"
    )
    temporary_path.write_text(
        json.dumps(
            def_json_ready(data),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    os.replace(temporary_path, output_path)
    return output_path


def def_pipeline_as_of_date(fixture_map=None):
    fixtures = fixture_map or {}
    dates = []
    for fixture in fixtures.values():
        captured = str(fixture.get("captured_at_utc") or "").strip()
        if len(captured) >= 10:
            dates.append(captured[:10])
    if dates:
        return max(dates)
    return def_now_utc().strftime("%Y-%m-%d")


def def_fixture_fingerprint(fixture):
    import json
    from pathlib import Path

    fixture_path = fixture.get("fixture_path") if isinstance(fixture, dict) else None
    if fixture_path and Path(fixture_path).is_file():
        return def_sha256_file(fixture_path)
    return def_sha256_bytes(
        json.dumps(
            def_json_ready(fixture),
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    )


def def_compute_pipeline_input_hash(codes, fixture_map=None, as_of_date=None):
    import json

    fixtures = fixture_map or {}
    payload = {
        "engine": ENGINE_NAME,
        "schema": SCHEMA_VERSION,
        "codes": list(codes),
        "as_of_date": as_of_date if CHECKPOINT_INCLUDE_UTC_DATE else None,
        "mode": "OFFLINE_FIXTURE" if fixtures else "LIVE",
        "fixture_hashes": {
            code: def_fixture_fingerprint(fixture)
            for code, fixture in sorted(fixtures.items())
        },
    }
    return def_sha256_bytes(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    )


def def_load_json_file(path, default=None):
    import json
    from pathlib import Path

    input_path = Path(path)
    if not input_path.is_file():
        return default
    try:
        return json.loads(input_path.read_text(encoding="utf-8"))
    except Exception:
        return default


def def_archive_checkpoint(checkpoint_path, checkpoint):
    from pathlib import Path

    if not isinstance(checkpoint, dict) or not checkpoint:
        return None
    input_hash = str(checkpoint.get("input_hash") or "UNKNOWN")[:16]
    run_id = str(checkpoint.get("run_id") or def_build_run_id())
    archive_path = (
        Path(checkpoint_path).parent
        / "consensus_checkpoint_archive"
        / f"checkpoint_{input_hash}_{run_id}.json"
    )
    if not archive_path.exists():
        def_atomic_write_json(archive_path, checkpoint)
    return archive_path


def def_initialize_checkpoint(
    output_dir,
    codes,
    fixture_map=None,
    resume=True,
    force_refresh=False,
    run_id=None,
):
    from pathlib import Path

    output_path = Path(output_dir)
    checkpoint_path = output_path / OUTPUT_CHECKPOINT
    as_of_date = def_pipeline_as_of_date(fixture_map)
    input_hash = def_compute_pipeline_input_hash(
        codes,
        fixture_map=fixture_map,
        as_of_date=as_of_date,
    )
    existing = def_load_json_file(checkpoint_path, default={}) or {}
    reusable = (
        resume
        and not force_refresh
        and existing.get("input_hash") == input_hash
        and existing.get("schema_version") == SCHEMA_VERSION
    )
    if reusable:
        return checkpoint_path, existing
    if existing:
        def_archive_checkpoint(checkpoint_path, existing)

    checkpoint = {
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id or def_build_run_id(),
        "input_hash": input_hash,
        "as_of_date": as_of_date,
        "codes": list(codes),
        "status": "IN_PROGRESS",
        "completed": {},
        "failed": {},
        "created_at_utc": def_now_utc_iso(),
        "updated_at_utc": def_now_utc_iso(),
    }
    def_atomic_write_json(checkpoint_path, checkpoint)
    return checkpoint_path, checkpoint


def def_checkpoint_payload_path(output_dir, input_hash, code):
    from pathlib import Path

    return (
        Path(output_dir)
        / OUTPUT_CHECKPOINT_DIR
        / str(input_hash)[:16]
        / f"{def_validate_code(code)}.json"
    )


def def_save_checkpoint_payload(output_dir, checkpoint, payload):
    code = def_validate_code(payload.get("code"))
    payload_path = def_checkpoint_payload_path(
        output_dir,
        checkpoint.get("input_hash"),
        code,
    )
    def_atomic_write_json(payload_path, payload)
    payload_hash = def_sha256_file(payload_path)
    checkpoint.setdefault("completed", {})[code] = {
        "payload_path": str(payload_path),
        "payload_sha256": payload_hash,
        "completed_at_utc": def_now_utc_iso(),
    }
    checkpoint.setdefault("failed", {}).pop(code, None)
    checkpoint["updated_at_utc"] = def_now_utc_iso()
    return payload_path


def def_load_checkpoint_payload(output_dir, checkpoint, code):
    completed = def_deep_get(
        checkpoint,
        ["completed", def_validate_code(code)],
        default={},
    ) or {}
    payload_path = def_checkpoint_payload_path(
        output_dir,
        checkpoint.get("input_hash"),
        code,
    )
    if not payload_path.is_file():
        return None
    expected_hash = completed.get("payload_sha256")
    actual_hash = def_sha256_file(payload_path)
    if expected_hash and expected_hash != actual_hash:
        raise RuntimeError(f"CHECKPOINT_PAYLOAD_HASH_MISMATCH: {code}")
    payload = def_load_json_file(payload_path, default=None)
    if not isinstance(payload, dict) or payload.get("code") != code:
        raise RuntimeError(f"CHECKPOINT_PAYLOAD_INVALID: {code}")
    return payload


def def_save_checkpoint_state(checkpoint_path, checkpoint):
    checkpoint["updated_at_utc"] = def_now_utc_iso()
    def_atomic_write_json(checkpoint_path, checkpoint)
    return checkpoint


def def_parse_codes_text(value):
    if value is None:
        return list(DEFAULT_CODES)
    tokens = []
    for item in str(value).replace(";", ",").split(","):
        clean = item.strip()
        if clean:
            tokens.append(clean)
    return tokens or list(DEFAULT_CODES)


def def_run_pipeline(
    codes=None,
    output_dir=None,
    run_unit_tests=True,
    fixture_map=None,
    resume=ENABLE_CHECKPOINT_RESUME,
    force_refresh=False,
):
    codes_clean = def_validate_codes(codes or DEFAULT_CODES)
    output_dir_value = output_dir or OUTPUT_DIR
    fixtures = fixture_map or {}
    offline_mode = bool(fixtures)
    dependency_report = def_assert_runtime_dependencies(
        live_mode=not offline_mode
    )
    requested_run_id = def_build_run_id()
    checkpoint_path, checkpoint = def_initialize_checkpoint(
        output_dir=output_dir_value,
        codes=codes_clean,
        fixture_map=fixtures,
        resume=resume,
        force_refresh=force_refresh,
        run_id=requested_run_id,
    )
    run_id = checkpoint.get("run_id") or requested_run_id

    print("=" * 88)
    print(f"def {ENGINE_NAME} · v{ENGINE_VERSION}")
    print("=" * 88)
    print(f"def Codes      : {', '.join(codes_clean)}")
    print(f"def OutputDir  : {output_dir_value}")
    print(f"def UnitTests  : {run_unit_tests}")
    print(f"def Dependency : {dependency_report.get('status')}")
    print(f"def Run ID     : {run_id}")
    print(f"def Resume     : {resume and not force_refresh}")
    print(
        f"def Mode       : "
        f"{def_display_source_mode('OFFLINE_LIVE_FIXTURE') if offline_mode else '即時資料'}"
    )

    unit_tests = def_run_builtin_unit_tests() if run_unit_tests else []
    unit_failures = [row for row in unit_tests if row.get("status") != "PASS"]
    print(f"def Unit Gate  : {'PASS' if not unit_failures else 'FAIL'} "
          f"({len(unit_tests) - len(unit_failures)}/{len(unit_tests)})")
    if unit_failures:
        raise RuntimeError(f"BUILTIN_UNIT_TEST_FAILED: {unit_failures}")

    payloads = []
    fetch_errors = []
    for index, code in enumerate(codes_clean, start=1):
        if resume and not force_refresh and code in checkpoint.get("completed", {}):
            try:
                resumed_payload = def_load_checkpoint_payload(
                    output_dir_value,
                    checkpoint,
                    code,
                )
                if resumed_payload is not None:
                    payloads.append(resumed_payload)
                    print(f"def Resume [{index}/{len(codes_clean)}] : {code}")
                    continue
            except Exception as exc:
                checkpoint.setdefault("completed", {}).pop(code, None)
                checkpoint.setdefault("failed", {})[code] = {
                    "error": str(exc),
                    "failed_at_utc": def_now_utc_iso(),
                    "stage": "CHECKPOINT_RECOVERY",
                }
                def_save_checkpoint_state(checkpoint_path, checkpoint)
        print(f"def Fetch [{index}/{len(codes_clean)}] : {code}")
        try:
            if offline_mode:
                if code not in fixtures:
                    raise ValueError(f"OFFLINE_FIXTURE_MISSING_FOR_CODE: {code}")
                payload = def_fetch_one_code_from_fixture(code, fixtures[code])
            else:
                payload = def_fetch_one_code(code)
            payloads.append(payload)
            def_save_checkpoint_payload(output_dir_value, checkpoint, payload)
            def_save_checkpoint_state(checkpoint_path, checkpoint)
        except Exception as exc:
            fetch_errors.append({
                "code": code,
                "status": "FAIL",
                "error": str(exc),
            })
            checkpoint.setdefault("failed", {})[code] = {
                "error": str(exc),
                "failed_at_utc": def_now_utc_iso(),
                "stage": "FETCH",
            }
            def_save_checkpoint_state(checkpoint_path, checkpoint)
            print(f"[FAIL] {code}: {exc}")

    if not payloads:
        raise RuntimeError(f"NO_PAYLOAD_FETCHED: {fetch_errors}")

    raw_records = def_build_raw_records(payloads)
    matrix_rows = def_build_wide_matrix(payloads)
    quality_checks = def_build_quality_checks(payloads, raw_records, matrix_rows)

    for test in unit_tests:
        quality_checks.append({
            "code": "UNIT",
            "check_id": test.get("test_id"),
            "actual": test.get("status"),
            "expected": "PASS",
            "status": test.get("status"),
            "severity": "FAIL",
            "note": test.get("error") or "Built-in deterministic unit test.",
        })

    for error in fetch_errors:
        quality_checks.append({
            "code": error.get("code"),
            "check_id": "FETCH_PIPELINE",
            "actual": error.get("error"),
            "expected": "successful fetch",
            "status": "FAIL",
            "severity": "FAIL",
            "note": "Ticker fetch failed.",
        })

    manifest = def_save_outputs(
        payloads=payloads,
        raw_records=raw_records,
        matrix_rows=matrix_rows,
        checks=quality_checks,
        output_dir=output_dir_value,
        run_id=run_id,
    )

    checkpoint["status"] = "COMPLETE" if not fetch_errors else "PARTIAL"
    checkpoint["manifest_path"] = manifest.get("manifest_path")
    checkpoint["manifest_sha256"] = def_sha256_file(
        manifest.get("manifest_path")
    )
    def_save_checkpoint_state(checkpoint_path, checkpoint)

    gate = manifest.get("gate", {}).get("gate")
    print("=" * 88)
    print(f"def Gate       : {gate}")
    print(f"def Tickers    : {manifest.get('counts', {}).get('tickers')}")
    print(f"def EPS items  : {manifest.get('counts', {}).get('eps_items')}")
    print(f"def Sales items: {manifest.get('counts', {}).get('sales_items')}")
    print(f"def Rating item: {manifest.get('counts', {}).get('rating_items')}")
    print(f"def YF items   : {manifest.get('counts', {}).get('yfinance_items')}")
    print(f"def Compare    : {manifest.get('counts', {}).get('comparison_items')}")
    print(f"def HTML       : {output_dir_value}/{OUTPUT_HTML}")
    print(f"def Matrix CSV : {output_dir_value}/{OUTPUT_MATRIX_CSV}")
    print(f"def Quality CSV: {output_dir_value}/{OUTPUT_QUALITY_CSV}")
    print(f"def Raw Parquet: {manifest.get('parquet', {}).get('status')}")
    print(f"def DuckDB     : {manifest.get('duckdb', {}).get('status')}")
    print(f"def Long Parquet: {output_dir_value}/{OUTPUT_LONG_PARQUET}")
    print(f"def Checkpoint : {checkpoint_path}")

    if FAIL_CLOSED_ON_QUALITY_ERROR and gate == "FAIL_CLOSED":
        raise RuntimeError("QUALITY_GATE_FAIL_CLOSED")

    return {
        "payloads": payloads,
        "raw_records": raw_records,
        "matrix_rows": matrix_rows,
        "quality_checks": quality_checks,
        "manifest": manifest,
        "checkpoint": checkpoint,
    }


# =============================================================================
# def 12 · CLI
# =============================================================================

def def_build_argument_parser():
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Fetch FactSet and YFinance consensus data, compare, "
            "validate and render matrices."
        )
    )
    parser.add_argument(
        "--codes",
        default=",".join(DEFAULT_CODES),
        help="Comma-separated FactSet-linked Taiwan stock codes, e.g. 2330,2317,3017",
    )
    parser.add_argument(
        "--output-dir",
        default=OUTPUT_DIR,
        help="Output directory",
    )
    parser.add_argument(
        "--skip-unit-tests",
        action="store_true",
        help="Skip built-in deterministic unit tests",
    )
    parser.add_argument(
        "--fixture",
        action="append",
        default=[],
        help=(
            "Offline live-response fixture JSON. May be repeated. "
            "When supplied, network access is disabled and every requested code "
            "must have a fixture."
        ),
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Disable checkpoint resume and start a new run.",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Ignore same-day completed checkpoints and fetch again.",
    )
    parser.add_argument(
        "--allow-missing-duckdb",
        action="store_true",
        help="Allow CSV/HTML output when DuckDB is unavailable.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Check runtime dependencies without fetching data.",
    )
    return parser


def main():
    global DUCKDB_REQUIRED

    parser = def_build_argument_parser()
    args = parser.parse_args()
    if args.allow_missing_duckdb:
        DUCKDB_REQUIRED = False
    if args.preflight_only:
        import json

        print(json.dumps(
            def_runtime_dependency_report(live_mode=True),
            ensure_ascii=False,
            indent=2,
        ))
        return
    codes = def_parse_codes_text(args.codes)
    fixture_map = def_load_fixture_map(args.fixture)
    def_run_pipeline(
        codes=codes,
        output_dir=args.output_dir,
        run_unit_tests=not args.skip_unit_tests,
        fixture_map=fixture_map,
        resume=not args.no_resume,
        force_refresh=args.force_refresh,
    )


if __name__ == "__main__":
    main()

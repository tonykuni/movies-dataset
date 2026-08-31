#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA 官方免費來源優先、FinMind 補足的台股籌碼擷取引擎。

設計重點：
1. API Token 僅在啟動時由 getpass 隱藏輸入，不寫入任何檔案。
2. DuckDB 作為 SSOT；request_ledger 與 fetch_cursor 支援斷點續傳。
3. TWSE／TPEX／TDCC 最新快照優先；官方失敗或歷史缺口由 FinMind 補足。
4. 每次寫入先依自然鍵去重，再以 INSERT OR REPLACE 冪等更新。
5. 同時輸出無副檔名的 Parquet 與 UTF-8-SIG CSV。
"""

from __future__ import annotations


# =============================================================================
# 0. 所有可調參數（集中於程式碼頂部）
# =============================================================================

ENGINE_NAME = "VIA Hybrid Official + FinMind TW Flow Engine"
ENGINE_VERSION = "1.5.0"

DEFAULT_START_DATE = "2023-01-01"
DEFAULT_END_DATE = "latest"
DEFAULT_TICKER_LIMIT = 250

# hybrid：最新快照先取 TWSE／TPEX／TDCC 免費官方來源；失敗或歷史缺口由
# FinMind 自動補齊。finmind_only 保留舊版行為；official_only 不要求 Token。
DEFAULT_SOURCE_MODE = "hybrid"
SOURCE_MODE_CHOICES = ("hybrid", "finmind_only", "official_only")

# 只有能維持既有表格語意與欄位完整性的資料才切官方來源。三大法人寬表需
# 分開自營商自行買賣／避險，當沖需個股買賣金額；兩者暫由 FinMind 保持一致。
OFFICIAL_LATEST_DATASETS = (
    "TaiwanStockHoldingSharesPer",
    "TaiwanStockBlockTrade",
    "TaiwanStockPrice",
    "TaiwanStockMarginPurchaseShortSale",
)

DATA_SOURCE_POLICY = {
    "TaiwanStockTradingDailyReport": "finmind_api",
    "TaiwanStockGovernmentBankBuySell": "finmind_api",
    "TaiwanStockTradingDailyReportSecIdAgg": "finmind_api",
    "TaiwanStockBlockTradingDailyReport": "finmind_api",
    "TaiwanStockBlockTrade": "official_latest_then_finmind_gap_fill",
    "TaiwanStockIndustryChainMoneyFlow": "finmind_api",
    "TaiwanStockHoldingSharesPer": "tdcc_latest_then_finmind_history",
    "TaiwanStockPrice": "official_latest_then_finmind_history",
    "TaiwanStockInstitutionalInvestorsBuySellWide": "finmind_api_schema_consistent",
    "TaiwanStockMarginPurchaseShortSale": "official_latest_then_finmind_history",
    "TaiwanStockDayTrading": "finmind_api_schema_consistent",
    "TaiwanStockSecuritiesLending": "finmind_api",
}

# 優先讀取你的既有清單；不存在時改讀引擎旁的 tickers_250.txt。
PRIMARY_TICKER_FILE = r"C:\Users\tonyk\OneDrive\桌面\tw_stock\dict\TickerList\AllStockYfinanceTickerList.txt"
FALLBACK_TICKER_FILE = "tickers_250.txt"

SUPPORTIVE_MODULE_ROOT = r"C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics\supportive modules"
DEFAULT_CELERITAS_PATH = SUPPORTIVE_MODULE_ROOT + r"\VeritasCeleritas.py"
DEFAULT_AEGIS_PATH = SUPPORTIVE_MODULE_ROOT + r"\VeritasAegisNexus.py"
REQUIRE_SUPPORTIVE_MODULES = True
SUPPORTIVE_ACCEL_MODE = "balanced"

DEFAULT_OUTPUT_ROOT = "FinMind_TW_Flow_Output"
DUCKDB_FILENAME = "FinMind_TW_Flow.duckdb"
PARQUET_DIRECTORY = "parquet"
CSV_DIRECTORY = "csv"
AUDIT_DIRECTORY = "audit"
OUTPUT_WITHOUT_EXTENSION = True
CSV_ENCODING = "utf-8-sig"
EXPORT_DATE_FORMAT = "%Y/%m/%d"

FINMIND_API_BASE = "https://api.finmindtrade.com/api/v4"
FINMIND_DATA_URL = f"{FINMIND_API_BASE}/data"
FINMIND_BRANCH_URL = f"{FINMIND_API_BASE}/taiwan_stock_trading_daily_report"
FINMIND_BRANCH_AGG_URL = f"{FINMIND_API_BASE}/taiwan_stock_trading_daily_report_secid_agg"
FINMIND_STORAGE_URL = f"{FINMIND_API_BASE}/storage_objects"
FINMIND_USER_INFO_URL = "https://api.web.finmindtrade.com/v2/user_info"

HTTP_TIMEOUT_SECONDS = 120
HTTP_MAX_RETRIES = 4
HTTP_BACKOFF_BASE_SECONDS = 2.0
OFFICIAL_HTTP_MAX_RETRIES = 3
OFFICIAL_HTTP_BACKOFF_SECONDS = 1.0
REQUEST_SAFETY_RESERVE = 5
QUOTA_WINDOW_SECONDS = 3600  # 官方文件目前標示為每小時額度。
THROTTLE_USAGE_RATIO = 0.90
MAX_REQUESTS_PER_RUN = 0  # 0 = 依帳號剩餘額度自動決定。
PROGRESS_EVERY_REQUESTS = 50
CHECKPOINT_BATCH_SIZE = 25
MAX_CONSECUTIVE_FAILURES = 5
CHECKPOINT_FILENAME = "FinMind_Checkpoint_Status.json"
FETCH_NEWEST_FIRST = True

# 日期區間型 API 的合法最大化策略：
# two_year：兩個曆年一個 request，預設兼顧單次資料量、記憶體與失敗重送成本。
# full_history：每檔每資料集完整期間一個 request，request 最少但回應最大。
# calendar_year：每年一個 request，最保守、最容易斷點續傳。
RANGE_BATCH_MODE = "two_year"
RANGE_BATCH_MODE_CHOICES = ("two_year", "full_history", "calendar_year")

# 同一股票可用 start_date / end_date 一次取得區間資料的端點。
# 集中定義可避免任務規劃、coverage 遷移與測試各自維護不同清單。
RANGE_DATASET_ENDPOINTS = (
    ("TaiwanStockTradingDailyReportSecIdAgg", "branch_agg"),
    ("TaiwanStockBlockTrade", "data"),
    ("TaiwanStockHoldingSharesPer", "data"),
    ("TaiwanStockPrice", "data"),
    ("TaiwanStockInstitutionalInvestorsBuySellWide", "data"),
    ("TaiwanStockMarginPurchaseShortSale", "data"),
    ("TaiwanStockDayTrading", "data"),
    ("TaiwanStockSecuritiesLending", "data"),
)

# auto：執行前探測 SponsorPro 全市場日檔；無權限則自動退回 standard。
# standard：每檔股票、每個交易日一個 request。
# sponsorpro：每個交易日下載一份全市場 Parquet，再篩選指定股票。
DEFAULT_BRANCH_MODE = "auto"

ENABLED_DATASETS = {
    "TaiwanStockTradingDailyReport": True,
    "TaiwanStockGovernmentBankBuySell": True,
    "TaiwanStockTradingDailyReportSecIdAgg": True,
    "TaiwanStockBlockTradingDailyReport": True,
    "TaiwanStockBlockTrade": True,
    "TaiwanStockIndustryChainMoneyFlow": True,
    "TaiwanStockHoldingSharesPer": True,
    # 資金圈與大戶行為判定所需的日資料。這四項使用一般 /data 區間查詢，
    # 與分點資料共用 request ledger、coverage、額度閘門及斷點續傳。
    "TaiwanStockPrice": True,
    "TaiwanStockInstitutionalInvestorsBuySellWide": True,
    "TaiwanStockMarginPurchaseShortSale": True,
    "TaiwanStockDayTrading": True,
    # 借券可強化空方判定；預設關閉，避免使用者不需要時增加 request。
    "TaiwanStockSecuritiesLending": False,
}

DATASET_AVAILABLE_FROM = {
    "TaiwanStockTradingDailyReport": "2021-06-30",
    "TaiwanStockGovernmentBankBuySell": "2021-06-30",
    "TaiwanStockTradingDailyReportSecIdAgg": "2021-06-30",
    "TaiwanStockBlockTradingDailyReport": "2026-04-28",
    "TaiwanStockBlockTrade": "2005-04-04",
    "TaiwanStockIndustryChainMoneyFlow": "1992-01-04",
    "TaiwanStockHoldingSharesPer": "2010-01-29",
    "TaiwanStockPrice": "1994-10-01",
    "TaiwanStockInstitutionalInvestorsBuySellWide": "2005-01-01",
    "TaiwanStockMarginPurchaseShortSale": "2001-01-01",
    "TaiwanStockDayTrading": "2014-01-01",
    "TaiwanStockSecuritiesLending": "2001-05-01",
}

# FinMind 官方文件明列的整日缺漏；跳過可避免浪費 request 與無效重試。
KNOWN_NO_DATA_DATES = {
    "TaiwanStockTradingDailyReport": {
        "2023-01-11", "2023-01-12", "2023-01-13", "2023-01-16", "2023-01-17",
    },
    "TaiwanStockGovernmentBankBuySell": {
        "2023-01-11", "2023-03-16", "2023-04-06", "2023-10-25", "2025-03-26",
    },
}

TABLE_SPECS = {
    "TaiwanStockTradingDailyReport": {
        "table": "tw_stock_trading_daily_report",
        "columns": [
            ("date", "VARCHAR"), ("stock_id", "VARCHAR"),
            ("securities_trader_id", "VARCHAR"), ("securities_trader", "VARCHAR"),
            ("price", "DOUBLE"), ("buy", "BIGINT"), ("sell", "BIGINT"),
            ("retrieved_at", "VARCHAR"),
        ],
        "pk": ["date", "stock_id", "securities_trader_id", "price"],
    },
    "TaiwanStockGovernmentBankBuySell": {
        "table": "tw_stock_government_bank_buy_sell",
        "columns": [
            ("date", "VARCHAR"), ("stock_id", "VARCHAR"), ("bank_name", "VARCHAR"),
            ("buy_amount", "DOUBLE"), ("sell_amount", "DOUBLE"),
            ("buy", "BIGINT"), ("sell", "BIGINT"), ("retrieved_at", "VARCHAR"),
        ],
        "pk": ["date", "stock_id", "bank_name"],
    },
    "TaiwanStockTradingDailyReportSecIdAgg": {
        "table": "tw_stock_trading_daily_report_secid_agg",
        "columns": [
            ("date", "VARCHAR"), ("stock_id", "VARCHAR"),
            ("securities_trader_id", "VARCHAR"), ("securities_trader", "VARCHAR"),
            ("buy_volume", "BIGINT"), ("sell_volume", "BIGINT"),
            ("buy_price", "DOUBLE"), ("sell_price", "DOUBLE"),
            ("retrieved_at", "VARCHAR"),
        ],
        "pk": ["date", "stock_id", "securities_trader_id"],
    },
    "TaiwanStockBlockTradingDailyReport": {
        "table": "tw_stock_block_trading_daily_report",
        "columns": [
            ("date", "VARCHAR"), ("stock_id", "VARCHAR"),
            ("securities_trader_id", "VARCHAR"), ("securities_trader", "VARCHAR"),
            ("trade_type", "VARCHAR"), ("price", "DOUBLE"),
            ("buy", "BIGINT"), ("sell", "BIGINT"), ("retrieved_at", "VARCHAR"),
        ],
        "pk": ["date", "stock_id", "securities_trader_id", "trade_type", "price"],
    },
    "TaiwanStockBlockTrade": {
        "table": "tw_stock_block_trade",
        "columns": [
            ("date", "VARCHAR"), ("stock_id", "VARCHAR"), ("trade_type", "VARCHAR"),
            ("price", "DOUBLE"), ("volume", "BIGINT"),
            ("trading_money", "DOUBLE"), ("retrieved_at", "VARCHAR"),
        ],
        "pk": ["date", "stock_id", "trade_type", "price", "volume", "trading_money"],
    },
    "TaiwanStockIndustryChainMoneyFlow": {
        "table": "tw_stock_industry_chain_money_flow",
        "columns": [
            ("date", "VARCHAR"), ("industry", "VARCHAR"), ("sub_industry", "VARCHAR"),
            ("stock_count", "BIGINT"), ("trading_volume", "BIGINT"),
            ("trading_money", "DOUBLE"), ("trading_money_pct", "DOUBLE"),
            ("retrieved_at", "VARCHAR"),
        ],
        "pk": ["date", "industry", "sub_industry"],
    },
    "TaiwanStockHoldingSharesPer": {
        "table": "tw_stock_holding_shares_per",
        "columns": [
            ("date", "VARCHAR"), ("stock_id", "VARCHAR"),
            ("HoldingSharesLevel", "VARCHAR"), ("people", "BIGINT"),
            ("percent", "DOUBLE"), ("unit", "BIGINT"),
            ("retrieved_at", "VARCHAR"),
        ],
        "pk": ["date", "stock_id", "HoldingSharesLevel"],
    },
    "TaiwanStockPrice": {
        "table": "tw_stock_price_daily",
        "columns": [
            ("date", "VARCHAR"), ("stock_id", "VARCHAR"),
            ("Trading_Volume", "BIGINT"), ("Trading_money", "DOUBLE"),
            ("open", "DOUBLE"), ("max", "DOUBLE"), ("min", "DOUBLE"),
            ("close", "DOUBLE"), ("spread", "DOUBLE"),
            ("Trading_turnover", "DOUBLE"), ("retrieved_at", "VARCHAR"),
        ],
        "pk": ["date", "stock_id"],
    },
    "TaiwanStockInstitutionalInvestorsBuySellWide": {
        "table": "tw_stock_institutional_investors_wide",
        "columns": [
            ("date", "VARCHAR"), ("stock_id", "VARCHAR"),
            ("Foreign_Investor_buy", "BIGINT"), ("Foreign_Investor_sell", "BIGINT"),
            ("Foreign_Dealer_Self_buy", "BIGINT"), ("Foreign_Dealer_Self_sell", "BIGINT"),
            ("Investment_Trust_buy", "BIGINT"), ("Investment_Trust_sell", "BIGINT"),
            ("Dealer_buy", "BIGINT"), ("Dealer_sell", "BIGINT"),
            ("Dealer_self_buy", "BIGINT"), ("Dealer_self_sell", "BIGINT"),
            ("Dealer_Hedging_buy", "BIGINT"), ("Dealer_Hedging_sell", "BIGINT"),
            ("retrieved_at", "VARCHAR"),
        ],
        "pk": ["date", "stock_id"],
    },
    "TaiwanStockMarginPurchaseShortSale": {
        "table": "tw_stock_margin_short_daily",
        "columns": [
            ("date", "VARCHAR"), ("stock_id", "VARCHAR"),
            ("MarginPurchaseBuy", "BIGINT"), ("MarginPurchaseCashRepayment", "BIGINT"),
            ("MarginPurchaseLimit", "BIGINT"), ("MarginPurchaseSell", "BIGINT"),
            ("MarginPurchaseTodayBalance", "BIGINT"),
            ("MarginPurchaseYesterdayBalance", "BIGINT"),
            ("Note", "VARCHAR"), ("OffsetLoanAndShort", "BIGINT"),
            ("ShortSaleBuy", "BIGINT"), ("ShortSaleCashRepayment", "BIGINT"),
            ("ShortSaleLimit", "BIGINT"), ("ShortSaleSell", "BIGINT"),
            ("ShortSaleTodayBalance", "BIGINT"),
            ("ShortSaleYesterdayBalance", "BIGINT"),
            ("retrieved_at", "VARCHAR"),
        ],
        "pk": ["date", "stock_id"],
    },
    "TaiwanStockDayTrading": {
        "table": "tw_stock_day_trading_daily",
        "columns": [
            ("date", "VARCHAR"), ("stock_id", "VARCHAR"),
            ("BuyAfterSale", "VARCHAR"), ("Volume", "BIGINT"),
            ("BuyAmount", "DOUBLE"), ("SellAmount", "DOUBLE"),
            ("retrieved_at", "VARCHAR"),
        ],
        "pk": ["date", "stock_id"],
    },
    "TaiwanStockSecuritiesLending": {
        "table": "tw_stock_securities_lending_daily",
        "columns": [
            ("date", "VARCHAR"), ("stock_id", "VARCHAR"),
            ("transaction_type", "VARCHAR"), ("volume", "BIGINT"),
            ("fee_rate", "DOUBLE"), ("close", "DOUBLE"),
            ("original_return_date", "VARCHAR"),
            ("original_lending_period", "VARCHAR"),
            ("retrieved_at", "VARCHAR"),
        ],
        "pk": [
            "date", "stock_id", "transaction_type", "volume", "fee_rate",
            "original_return_date",
        ],
    },
}

# 每筆資料都保留實際來源；自然鍵不含來源，因此成功的官方快照可取代同日
# FinMind 資料，而不會在 SSOT 內形成重複列。
PROVENANCE_COLUMNS = (
    ("source_provider", "VARCHAR"),
    ("source_mode", "VARCHAR"),
    ("source_dataset", "VARCHAR"),
)
for _dataset_spec in TABLE_SPECS.values():
    _existing_columns = {name for name, _dtype in _dataset_spec["columns"]}
    _retrieved_index = next(
        (index for index, column in enumerate(_dataset_spec["columns"]) if column[0] == "retrieved_at"),
        len(_dataset_spec["columns"]),
    )
    for _provenance_column in PROVENANCE_COLUMNS:
        if _provenance_column[0] not in _existing_columns:
            _dataset_spec["columns"].insert(_retrieved_index, _provenance_column)
            _retrieved_index += 1


# =============================================================================
# 1. 匯入與通用工具
# =============================================================================

import argparse
import getpass
import hashlib
import importlib.util
import json
import math
import os
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable, Iterator

import duckdb
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from VIA_TW_Official_Data_Adapter import (
    OfficialSourceError,
    def_fetch_official_dataset,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def format_iso_date(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def resolve_end_date(value: str) -> str:
    if value.lower() == "latest":
        return date.today().strftime("%Y-%m-%d")
    parse_iso_date(value)
    return value


def clamp_start_date(dataset: str, requested_start: str) -> str:
    return max(requested_start, DATASET_AVAILABLE_FROM[dataset])


def normalize_ticker(raw_value: str) -> str:
    value = raw_value.strip().upper()
    value = re.sub(r"\.(TW|TWO)$", "", value)
    if not re.fullmatch(r"[0-9A-Z]{4,8}", value):
        raise ValueError(f"無效台股代碼：{raw_value!r}")
    return value


def read_tickers(ticker_file: str, ticker_limit: int) -> list[str]:
    primary = Path(ticker_file)
    if not primary.exists():
        fallback = Path(__file__).resolve().parent / FALLBACK_TICKER_FILE
        if not fallback.exists():
            raise FileNotFoundError(f"找不到股票清單：{primary}；亦找不到備用清單：{fallback}")
        primary = fallback

    content = primary.read_text(encoding="utf-8-sig")
    candidates = re.split(r"[\s,;]+", content)
    tickers: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate.lstrip().startswith("#"):
            continue
        try:
            ticker = normalize_ticker(candidate)
        except ValueError:
            continue
        if ticker not in seen:
            tickers.append(ticker)
            seen.add(ticker)
        if ticker_limit > 0 and len(tickers) >= ticker_limit:
            break

    if not tickers:
        raise ValueError(f"股票清單沒有可用代碼：{primary}")
    return tickers


def configure_enabled_datasets(selection: str) -> list[str]:
    """依 CLI 選擇本輪資料集；空字串維持程式頂部的預設設定。"""
    if not selection.strip():
        return [dataset for dataset, enabled in ENABLED_DATASETS.items() if enabled]
    requested = {
        item.strip() for item in selection.split(",") if item.strip()
    }
    unknown = requested.difference(ENABLED_DATASETS)
    if unknown:
        raise ValueError(f"未知 datasets：{', '.join(sorted(unknown))}")
    if not requested:
        raise ValueError("--datasets 不可為空。")
    for dataset in ENABLED_DATASETS:
        ENABLED_DATASETS[dataset] = dataset in requested
    return sorted(requested)


def prompt_api_token() -> str:
    token = getpass.getpass("請輸入 FinMind API Token（輸入內容不顯示）：").strip()
    if not token:
        raise ValueError("FinMind API Token 不可空白。")
    return token


def resolve_supportive_path(configured_path: str, fallback_name: str) -> Path:
    configured = Path(configured_path).expanduser()
    if configured.exists():
        return configured.resolve()
    packaged = Path(__file__).resolve().parent / fallback_name
    if packaged.exists():
        return packaged
    raise FileNotFoundError(
        f"找不到 supportive module：{configured_path}；封裝備用檔亦不存在：{packaged}"
    )


def import_module_from_file(module_name: str, module_path: Path) -> Any:
    specification = importlib.util.spec_from_file_location(module_name, module_path)
    if specification is None or specification.loader is None:
        raise ImportError(f"無法建立模組規格：{module_path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    try:
        specification.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def initialize_supportive_runtime(
    celeritas_path: str,
    aegis_path: str,
) -> dict[str, Any]:
    runtime: dict[str, Any] = {
        "enabled": False,
        "celeritas": None,
        "aegis": None,
        "circuit_breaker": None,
        "checkpoint_batch_size": CHECKPOINT_BATCH_SIZE,
        "errors": [],
        "safety_policy": {
            "proxy_rotation": False,
            "token_rotation": False,
            "ip_rotation": False,
            "anti_scrape_bypass": False,
            "reason": "FinMind 使用官方 Token 與官方 API；禁止以任何方式規避會員額度。",
        },
    }
    try:
        celeritas_file = resolve_supportive_path(celeritas_path, "VeritasCeleritas.py")
        aegis_file = resolve_supportive_path(aegis_path, "VeritasAegisNexus.py")
        celeritas = import_module_from_file("VeritasCeleritas", celeritas_file)
        aegis = import_module_from_file("VeritasAegisNexus", aegis_file)

        apply_acceleration = getattr(celeritas, "apply_vrn_vds_max_accel", None)
        if callable(apply_acceleration):
            apply_acceleration(SUPPORTIVE_ACCEL_MODE)

        batch_size = CHECKPOINT_BATCH_SIZE
        adaptive_chunk = getattr(celeritas, "adaptive_chunk_size", None)
        if callable(adaptive_chunk):
            batch_size = int(adaptive_chunk(
                CHECKPOINT_BATCH_SIZE,
                item_bytes=1024 * 1024,
                mode=SUPPORTIVE_ACCEL_MODE,
            ))
        under_pressure = getattr(celeritas, "system_under_pressure", None)
        if callable(under_pressure) and under_pressure():
            batch_size = min(batch_size, 5)

        circuit_breaker_type = getattr(aegis, "CircuitBreaker", None)
        circuit_breaker = (
            circuit_breaker_type(fail_max=MAX_CONSECUTIVE_FAILURES, reset_timeout=3600.0)
            if callable(circuit_breaker_type) else None
        )
        runtime.update({
            "enabled": True,
            "celeritas": celeritas,
            "aegis": aegis,
            "circuit_breaker": circuit_breaker,
            "checkpoint_batch_size": max(1, min(batch_size, CHECKPOINT_BATCH_SIZE)),
            "celeritas_path": str(celeritas_file),
            "aegis_path": str(aegis_file),
            "celeritas_version": str(getattr(celeritas, "__version__", "unknown")),
            "aegis_version": str(getattr(aegis, "__version__", "unknown")),
        })
    except Exception as exc:
        runtime["errors"].append(f"{type(exc).__name__}: {exc}")
        if REQUIRE_SUPPORTIVE_MODULES:
            raise RuntimeError(f"Supportive modules 載入失敗：{runtime['errors'][-1]}") from exc
    return runtime


def supportive_runtime_report(runtime: dict[str, Any]) -> dict[str, Any]:
    return {
        "enabled": bool(runtime.get("enabled")),
        "celeritas_path": runtime.get("celeritas_path"),
        "aegis_path": runtime.get("aegis_path"),
        "celeritas_version": runtime.get("celeritas_version"),
        "aegis_version": runtime.get("aegis_version"),
        "checkpoint_batch_size": runtime.get("checkpoint_batch_size"),
        "circuit_breaker_state": getattr(runtime.get("circuit_breaker"), "state", None),
        "safety_policy": runtime.get("safety_policy"),
        "errors": list(runtime.get("errors", [])),
    }


def build_session(token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "User-Agent": f"{ENGINE_NAME}/{ENGINE_VERSION}",
        "Accept": "application/json",
    })
    return session


def build_official_session() -> requests.Session:
    """官方來源不得夾帶 FinMind Bearer Token。"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": f"{ENGINE_NAME}/{ENGINE_VERSION}",
        "Accept": "application/json,text/csv;q=0.9,*/*;q=0.8",
    })
    retry_policy = Retry(
        total=OFFICIAL_HTTP_MAX_RETRIES,
        connect=OFFICIAL_HTTP_MAX_RETRIES,
        read=OFFICIAL_HTTP_MAX_RETRIES,
        status=OFFICIAL_HTTP_MAX_RETRIES,
        backoff_factor=OFFICIAL_HTTP_BACKOFF_SECONDS,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry_policy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def source_metadata_for_task(task: dict[str, Any]) -> dict[str, str]:
    return {
        "source_provider": str(task.get("source_provider", "FINMIND")),
        "source_mode": str(task.get("source_mode", "finmind_api")),
        "source_dataset": str(task.get("source_dataset", task["dataset"])),
    }


def attach_source_metadata(
    rows: Iterable[dict[str, Any]],
    task: dict[str, Any],
) -> list[dict[str, Any]]:
    metadata = source_metadata_for_task(task)
    result: list[dict[str, Any]] = []
    for source in rows:
        row = dict(source)
        for key, value in metadata.items():
            row.setdefault(key, value)
        result.append(row)
    return result


def safe_json(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"FinMind 回傳非 JSON（HTTP {response.status_code}）") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("FinMind JSON 最外層不是物件。")
    return payload


def request_json(
    session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    timeout: int = HTTP_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(HTTP_MAX_RETRIES + 1):
        try:
            response = session.get(url, params=params, timeout=timeout)
            if response.status_code == 402:
                raise RuntimeError("QUOTA_EXHAUSTED：FinMind API 額度已用完。")
            if response.status_code in {401, 403}:
                raise PermissionError(f"FinMind 權限不足或 Token 無效（HTTP {response.status_code}）。")
            if response.status_code == 422:
                payload = safe_json(response)
                raise ValueError(f"FinMind 參數或端點錯誤：{payload.get('msg', payload)}")
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(f"可重試 HTTP {response.status_code}")
            response.raise_for_status()
            payload = safe_json(response)
            status = payload.get("status")
            if status not in (None, 200, "200"):
                message = payload.get("msg", "未知 API 錯誤")
                raise RuntimeError(f"FinMind status={status}: {message}")
            return payload
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
            last_error = exc
            if attempt >= HTTP_MAX_RETRIES:
                break
            time.sleep(HTTP_BACKOFF_BASE_SECONDS * (2 ** attempt))
    raise RuntimeError(f"FinMind request 失敗，重試仍未恢復：{last_error}")


def extract_data_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data", [])
    if data is None:
        return []
    if not isinstance(data, list):
        raise RuntimeError("FinMind data 欄位不是陣列。")
    return [row for row in data if isinstance(row, dict)]


def find_signed_url(value: Any) -> str | None:
    if isinstance(value, str) and value.startswith(("https://", "http://")):
        return value
    if isinstance(value, dict):
        preferred_keys = ("url", "download_url", "signed_url", "presigned_url")
        for key in preferred_keys:
            if key in value:
                found = find_signed_url(value[key])
                if found:
                    return found
        for child in value.values():
            found = find_signed_url(child)
            if found:
                return found
    if isinstance(value, list):
        for child in value:
            found = find_signed_url(child)
            if found:
                return found
    return None


# =============================================================================
# 2. DuckDB SSOT、去重、斷點續傳
# =============================================================================

def quote_identifier(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
        raise ValueError(f"不安全識別字：{identifier}")
    return f'"{identifier}"'


def open_database(output_root: Path) -> duckdb.DuckDBPyConnection:
    output_root.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(output_root / DUCKDB_FILENAME))


def initialize_database(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS request_ledger (
            task_id VARCHAR PRIMARY KEY,
            dataset VARCHAR NOT NULL,
            partition_key VARCHAR NOT NULL,
            status VARCHAR NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            row_count BIGINT NOT NULL DEFAULT 0,
            last_error VARCHAR,
            updated_at VARCHAR NOT NULL
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS fetch_cursor (
            dataset VARCHAR NOT NULL,
            entity_id VARCHAR NOT NULL,
            last_date VARCHAR NOT NULL,
            updated_at VARCHAR NOT NULL,
            PRIMARY KEY (dataset, entity_id)
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS range_coverage (
            dataset VARCHAR NOT NULL,
            entity_id VARCHAR NOT NULL,
            range_start VARCHAR NOT NULL,
            range_end VARCHAR NOT NULL,
            updated_at VARCHAR NOT NULL,
            PRIMARY KEY (dataset, entity_id, range_start, range_end)
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS run_audit (
            run_id VARCHAR PRIMARY KEY,
            started_at VARCHAR NOT NULL,
            finished_at VARCHAR,
            status VARCHAR NOT NULL,
            request_count BIGINT NOT NULL DEFAULT 0,
            row_count BIGINT NOT NULL DEFAULT 0,
            detail_json VARCHAR
        )
    """)

    for dataset, spec in TABLE_SPECS.items():
        table_name = quote_identifier(spec["table"])
        column_defs = [f"{quote_identifier(name)} {dtype}" for name, dtype in spec["columns"]]
        primary_key = ", ".join(quote_identifier(name) for name in spec["pk"])
        ddl = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)}, PRIMARY KEY ({primary_key}))"
        connection.execute(ddl)
        # v1.4.0 以前的 DuckDB 沒有 provenance 欄位；原地遷移，不重建舊表。
        for column_name, column_type in PROVENANCE_COLUMNS:
            connection.execute(
                f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS "
                f"{quote_identifier(column_name)} {column_type}"
            )
        connection.execute(
            f"UPDATE {table_name} SET "
            "source_provider = COALESCE(source_provider, 'FINMIND'), "
            "source_mode = COALESCE(source_mode, 'finmind_api'), "
            "source_dataset = COALESCE(source_dataset, ?) "
            "WHERE source_provider IS NULL OR source_mode IS NULL OR source_dataset IS NULL",
            [dataset],
        )

    backfill_range_coverage_from_ledger(connection)


def get_completed_task_ids(connection: duckdb.DuckDBPyConnection) -> set[str]:
    rows = connection.execute("SELECT task_id FROM request_ledger WHERE status = 'success'").fetchall()
    return {row[0] for row in rows}


def get_cursor(connection: duckdb.DuckDBPyConnection, dataset: str, entity_id: str) -> str | None:
    row = connection.execute(
        "SELECT last_date FROM fetch_cursor WHERE dataset = ? AND entity_id = ?",
        [dataset, entity_id],
    ).fetchone()
    return row[0] if row else None


def update_cursor(
    connection: duckdb.DuckDBPyConnection,
    dataset: str,
    entity_id: str,
    last_date: str,
) -> None:
    connection.execute("""
        INSERT OR REPLACE INTO fetch_cursor (dataset, entity_id, last_date, updated_at)
        VALUES (?, ?, ?, ?)
    """, [dataset, entity_id, last_date, utc_now_iso()])


def merge_range_coverage(
    connection: duckdb.DuckDBPyConnection,
    dataset: str,
    entity_id: str,
    range_start: str,
    range_end: str,
) -> None:
    """合併同一股票的相鄰／重疊區間，供模式切換與增量更新安全續傳。"""
    parse_iso_date(range_start)
    parse_iso_date(range_end)
    if range_start > range_end:
        raise ValueError(f"range_start 不可晚於 range_end：{range_start} > {range_end}")

    rows = connection.execute(
        """SELECT range_start, range_end FROM range_coverage
           WHERE dataset = ? AND entity_id = ? ORDER BY range_start""",
        [dataset, entity_id],
    ).fetchall()
    intervals = [(str(start), str(end)) for start, end in rows]
    intervals.append((range_start, range_end))
    intervals.sort()

    merged: list[tuple[str, str]] = []
    for current_start, current_end in intervals:
        if not merged:
            merged.append((current_start, current_end))
            continue
        previous_start, previous_end = merged[-1]
        adjacent_limit = format_iso_date(parse_iso_date(previous_end) + timedelta(days=1))
        if current_start <= adjacent_limit:
            merged[-1] = (previous_start, max(previous_end, current_end))
        else:
            merged.append((current_start, current_end))

    connection.execute(
        "DELETE FROM range_coverage WHERE dataset = ? AND entity_id = ?",
        [dataset, entity_id],
    )
    timestamp = utc_now_iso()
    connection.executemany(
        """INSERT INTO range_coverage
           (dataset, entity_id, range_start, range_end, updated_at)
           VALUES (?, ?, ?, ?, ?)""",
        [(dataset, entity_id, start, end, timestamp) for start, end in merged],
    )


def get_range_coverage_end(
    connection: duckdb.DuckDBPyConnection,
    dataset: str,
    entity_id: str,
    requested_start: str,
) -> str | None:
    row = connection.execute(
        """SELECT range_end FROM range_coverage
           WHERE dataset = ? AND entity_id = ?
             AND range_start <= ? AND range_end >= ?
           ORDER BY range_end DESC LIMIT 1""",
        [dataset, entity_id, requested_start, requested_start],
    ).fetchone()
    return str(row[0]) if row else None


def get_uncovered_ranges(
    connection: duckdb.DuckDBPyConnection,
    dataset: str,
    entity_id: str,
    requested_start: str,
    requested_end: str,
) -> list[tuple[str, str]]:
    """扣除所有已完成區間，支援官方最新日與 FinMind 歷史的非連續覆蓋。"""
    if requested_start > requested_end:
        return []
    rows = connection.execute(
        """SELECT range_start, range_end FROM range_coverage
           WHERE dataset = ? AND entity_id = ?
             AND range_end >= ? AND range_start <= ?
           ORDER BY range_start""",
        [dataset, entity_id, requested_start, requested_end],
    ).fetchall()
    covered = [
        (max(str(start), requested_start), min(str(end), requested_end))
        for start, end in rows
    ]
    gaps: list[tuple[str, str]] = []
    cursor = parse_iso_date(requested_start)
    final = parse_iso_date(requested_end)
    for covered_start, covered_end in covered:
        start_value = parse_iso_date(covered_start)
        end_value = parse_iso_date(covered_end)
        if end_value < cursor:
            continue
        if start_value > cursor:
            gaps.append((format_iso_date(cursor), format_iso_date(start_value - timedelta(days=1))))
        cursor = max(cursor, end_value + timedelta(days=1))
        if cursor > final:
            break
    if cursor <= final:
        gaps.append((format_iso_date(cursor), format_iso_date(final)))
    return list(reversed(gaps)) if FETCH_NEWEST_FIRST else gaps


def backfill_range_coverage_from_ledger(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    """把舊版已完成的區間 task 遷移成 coverage，避免升級後重抓。"""
    existing = connection.execute("SELECT COUNT(*) FROM range_coverage").fetchone()[0]
    if int(existing) > 0:
        return
    range_datasets = [dataset for dataset, _endpoint in RANGE_DATASET_ENDPOINTS]
    placeholders = ", ".join("?" for _dataset in range_datasets)
    rows = connection.execute(
        f"""SELECT dataset, partition_key FROM request_ledger
            WHERE status = 'success' AND dataset IN ({placeholders})""",
        range_datasets,
    ).fetchall()
    pattern = re.compile(
        r"^stock_id=([0-9A-Z]{4,8})\|(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$"
    )
    for dataset, partition_key in rows:
        match = pattern.fullmatch(str(partition_key))
        if match:
            merge_range_coverage(
                connection, str(dataset), match.group(1), match.group(2), match.group(3)
            )


def record_task_result(
    connection: duckdb.DuckDBPyConnection,
    task: dict[str, Any],
    status: str,
    row_count: int,
    error: str | None,
) -> None:
    previous = connection.execute(
        "SELECT attempts FROM request_ledger WHERE task_id = ?", [task["task_id"]]
    ).fetchone()
    attempts = int(previous[0]) + 1 if previous else 1
    connection.execute("""
        INSERT OR REPLACE INTO request_ledger
        (task_id, dataset, partition_key, status, attempts, row_count, last_error, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        task["task_id"], task["dataset"], task["partition_key"], status,
        attempts, row_count, error, utc_now_iso(),
    ])


def normalize_scalar_for_type(value: Any, dtype: str) -> Any:
    if value in ("", "--", None):
        return None
    if dtype == "VARCHAR":
        return str(value)
    if dtype == "BIGINT":
        return int(float(value))
    if dtype == "DOUBLE":
        return float(value)
    return value


def normalize_rows(dataset: str, rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    spec = TABLE_SPECS[dataset]
    timestamp = utc_now_iso()
    normalized_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    column_types = dict(spec["columns"])

    for source in rows:
        target: dict[str, Any] = {}
        for column, dtype in spec["columns"]:
            raw_value = timestamp if column == "retrieved_at" else source.get(column)
            target[column] = normalize_scalar_for_type(raw_value, dtype)
        for key_column in spec["pk"]:
            if target[key_column] is None:
                target[key_column] = "" if column_types[key_column] == "VARCHAR" else 0
        natural_key = tuple(target[column] for column in spec["pk"])
        normalized_by_key[natural_key] = target
    return list(normalized_by_key.values())


def upsert_rows(
    connection: duckdb.DuckDBPyConnection,
    dataset: str,
    rows: Iterable[dict[str, Any]],
) -> int:
    normalized = normalize_rows(dataset, rows)
    if not normalized:
        return 0
    spec = TABLE_SPECS[dataset]
    table = pa.Table.from_pylist(normalized)
    connection.register("_incoming_rows", table)
    try:
        connection.execute(
            f"INSERT OR REPLACE INTO {quote_identifier(spec['table'])} BY NAME SELECT * FROM _incoming_rows"
        )
    finally:
        connection.unregister("_incoming_rows")
    return len(normalized)


# =============================================================================
# 3. 額度、交易日與任務規劃
# =============================================================================

def get_quota_info(session: requests.Session) -> dict[str, int]:
    payload = request_json(session, FINMIND_USER_INFO_URL)
    user_count = int(payload.get("user_count", 0))
    request_limit = int(payload.get("api_request_limit", 0))
    if request_limit <= 0:
        raise RuntimeError(f"無法取得有效 api_request_limit：{payload}")
    return {
        "user_count": user_count,
        "api_request_limit": request_limit,
        "remaining": max(request_limit - user_count, 0),
    }


def fetch_trading_dates(
    session: requests.Session,
    start_date: str,
    end_date: str,
) -> list[str]:
    payload = request_json(session, FINMIND_DATA_URL, {"dataset": "TaiwanStockTradingDate"})
    dates = sorted({str(row.get("date", "")) for row in extract_data_rows(payload)})
    return [value for value in dates if start_date <= value <= end_date]


def fallback_weekdays(start_date: str, end_date: str) -> list[str]:
    current = parse_iso_date(start_date)
    final = parse_iso_date(end_date)
    result: list[str] = []
    while current <= final:
        if current.weekday() < 5:
            result.append(format_iso_date(current))
        current += timedelta(days=1)
    return result


def make_task(
    dataset: str,
    endpoint: str,
    params: dict[str, Any],
    partition_key: str,
    entity_id: str | None = None,
    cursor_end: str | None = None,
    range_start: str | None = None,
    range_end: str | None = None,
    source_provider: str = "FINMIND",
    source_mode: str = "finmind_api",
    source_dataset: str | None = None,
    coverage_entities: list[str] | None = None,
    coverage_from_rows: bool = False,
) -> dict[str, Any]:
    identity = json.dumps(
        {"dataset": dataset, "endpoint": endpoint, "params": params, "partition_key": partition_key},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "task_id": hashlib.sha256(identity.encode("utf-8")).hexdigest(),
        "dataset": dataset,
        "endpoint": endpoint,
        "params": params,
        "partition_key": partition_key,
        "entity_id": entity_id,
        "cursor_end": cursor_end,
        "range_start": range_start,
        "range_end": range_end,
        "source_provider": source_provider,
        "source_mode": source_mode,
        "source_dataset": source_dataset or dataset,
        "coverage_entities": list(coverage_entities or []),
        "coverage_from_rows": bool(coverage_from_rows),
    }


def iter_dataset_dates(dataset: str, trading_dates: list[str], requested_start: str) -> Iterator[str]:
    effective_start = clamp_start_date(dataset, requested_start)
    missing = KNOWN_NO_DATA_DATES.get(dataset, set())
    ordered_dates = reversed(trading_dates) if FETCH_NEWEST_FIRST else iter(trading_dates)
    for trading_date in ordered_dates:
        if trading_date >= effective_start and trading_date not in missing:
            yield trading_date


def next_cursor_start(cursor_date: str | None, requested_start: str) -> str:
    if not cursor_date:
        return requested_start
    return format_iso_date(parse_iso_date(cursor_date) + timedelta(days=1))


def iter_reverse_year_windows(
    dataset: str,
    trading_dates: list[str],
    requested_start: str,
    end_date: str,
) -> Iterator[tuple[str, str]]:
    yield from iter_reverse_range_windows(
        dataset, trading_dates, requested_start, end_date, "calendar_year"
    )


def iter_reverse_range_windows(
    dataset: str,
    trading_dates: list[str],
    requested_start: str,
    end_date: str,
    range_batch_mode: str,
) -> Iterator[tuple[str, str]]:
    """依固定曆年邊界切窗，避免隔日重跑時因滑動窗口改變 task identity。"""
    if range_batch_mode not in RANGE_BATCH_MODE_CHOICES:
        raise ValueError(f"不支援的 range batch mode：{range_batch_mode}")
    effective_start = clamp_start_date(dataset, requested_start)
    eligible = sorted(
        value for value in trading_dates if effective_start <= value <= end_date
    )
    if not eligible:
        return
    latest_trading_date = eligible[-1]

    if range_batch_mode == "full_history":
        yield effective_start, latest_trading_date
        return

    grouped_years: dict[int, list[str]] = {}
    for trading_date in eligible:
        year = int(trading_date[:4])
        bucket_start_year = year if range_batch_mode == "calendar_year" else year - ((year + 1) % 2)
        grouped_years.setdefault(bucket_start_year, []).append(trading_date)

    ordered_bucket_starts = sorted(grouped_years, reverse=FETCH_NEWEST_FIRST)
    for bucket_start_year in ordered_bucket_starts:
        bucket_year_span = 1 if range_batch_mode == "calendar_year" else 2
        calendar_start = f"{bucket_start_year:04d}-01-01"
        calendar_end = f"{bucket_start_year + bucket_year_span - 1:04d}-12-31"
        yield max(effective_start, calendar_start), min(latest_trading_date, calendar_end)


def is_dataset_date_eligible(dataset: str, trading_date: str, requested_start: str) -> bool:
    return (
        ENABLED_DATASETS.get(dataset, False)
        and trading_date >= clamp_start_date(dataset, requested_start)
        and trading_date not in KNOWN_NO_DATA_DATES.get(dataset, set())
    )


def iter_official_latest_tasks(
    tickers: list[str],
    latest_trading_date: str,
    requested_start: str,
) -> Iterator[dict[str, Any]]:
    """官方快照先執行；成功後其 coverage 會讓 FinMind 只補歷史缺口。"""
    for dataset in OFFICIAL_LATEST_DATASETS:
        if not is_dataset_date_eligible(dataset, latest_trading_date, requested_start):
            continue
        is_tdcc = dataset == "TaiwanStockHoldingSharesPer"
        yield make_task(
            dataset,
            "official",
            {"date": latest_trading_date},
            f"source=official|date={latest_trading_date}",
            range_start=None if is_tdcc else latest_trading_date,
            range_end=None if is_tdcc else latest_trading_date,
            source_provider="TDCC" if is_tdcc else "OFFICIAL",
            source_mode="official_open_data" if is_tdcc else "official_api",
            source_dataset="TDCC_OPEN_DATA_1-5" if is_tdcc else dataset,
            coverage_entities=tickers,
            coverage_from_rows=is_tdcc,
        )


def iter_daily_tasks_for_date(
    tickers: list[str],
    trading_date: str,
    requested_start: str,
    branch_mode: str,
) -> Iterator[dict[str, Any]]:
    dataset = "TaiwanStockTradingDailyReport"
    if is_dataset_date_eligible(dataset, trading_date, requested_start):
        if branch_mode == "sponsorpro":
            yield make_task(
                dataset, "storage", {"dataset": dataset, "date": trading_date},
                f"date={trading_date}",
            )
        else:
            for ticker in tickers:
                yield make_task(
                    dataset, "branch", {"data_id": ticker, "date": trading_date},
                    f"date={trading_date}|stock_id={ticker}",
                )

    for dataset in (
        "TaiwanStockGovernmentBankBuySell",
        "TaiwanStockBlockTradingDailyReport",
        "TaiwanStockIndustryChainMoneyFlow",
    ):
        if is_dataset_date_eligible(dataset, trading_date, requested_start):
            yield make_task(
                dataset, "data", {"dataset": dataset, "start_date": trading_date},
                f"date={trading_date}",
            )


def iter_range_tasks(
    connection: duckdb.DuckDBPyConnection,
    tickers: list[str],
    trading_dates: list[str],
    requested_start: str,
    overall_end: str,
    range_batch_mode: str,
) -> Iterator[dict[str, Any]]:
    range_specs: list[tuple[str, str, list[tuple[str, str]]]] = []
    for dataset, endpoint in RANGE_DATASET_ENDPOINTS:
        if not ENABLED_DATASETS.get(dataset, False):
            continue
        windows = list(iter_reverse_range_windows(
            dataset, trading_dates, requested_start, overall_end, range_batch_mode
        ))
        range_specs.append((dataset, endpoint, windows))

    maximum_window_count = max((len(spec[2]) for spec in range_specs), default=0)
    for window_index in range(maximum_window_count):
        for dataset, endpoint, windows in range_specs:
            if window_index >= len(windows):
                continue
            start, window_end = windows[window_index]
            for ticker in tickers:
                uncovered_ranges = get_uncovered_ranges(
                    connection, dataset, ticker, start, window_end
                )
                for query_start, query_end in uncovered_ranges:
                    params = {
                        "data_id": ticker,
                        "start_date": query_start,
                        "end_date": query_end,
                    }
                    if endpoint == "data":
                        params["dataset"] = dataset
                    yield make_task(
                        dataset, endpoint, params,
                        f"stock_id={ticker}|{query_start}..{query_end}",
                        entity_id=ticker,
                        cursor_end=query_end if window_index == 0 else None,
                        range_start=query_start,
                        range_end=query_end,
                    )


def iter_all_tasks(
    connection: duckdb.DuckDBPyConnection,
    tickers: list[str],
    trading_dates: list[str],
    requested_start: str,
    end_date: str,
    branch_mode: str,
    range_batch_mode: str = RANGE_BATCH_MODE,
    source_mode: str = "finmind_only",
) -> Iterator[dict[str, Any]]:
    if source_mode not in SOURCE_MODE_CHOICES:
        raise ValueError(f"不支援的 source mode：{source_mode}")
    bounded_dates = sorted(
        (value for value in trading_dates if requested_start <= value <= end_date),
        reverse=FETCH_NEWEST_FIRST,
    )
    if not bounded_dates:
        return

    # 先保存最新日的跨資料集切面，再用較大的合法日期區間完成兩個 range API，
    # 最後才逐日向歷史回補。中斷時能同時保留最新資料與高 rows/request 成果。
    newest_date = bounded_dates[0]
    if source_mode in {"hybrid", "official_only"}:
        yield from iter_official_latest_tasks(tickers, newest_date, requested_start)
    if source_mode == "official_only":
        return
    yield from iter_daily_tasks_for_date(
        tickers, newest_date, requested_start, branch_mode
    )
    yield from iter_range_tasks(
        connection, tickers, bounded_dates, requested_start, end_date,
        range_batch_mode,
    )
    for trading_date in bounded_dates[1:]:
        yield from iter_daily_tasks_for_date(
            tickers, trading_date, requested_start, branch_mode
        )


def count_pending_tasks(
    tasks: Iterable[dict[str, Any]],
    completed_task_ids: set[str],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for task in tasks:
        if task["task_id"] in completed_task_ids:
            continue
        counts[task["dataset"]] = counts.get(task["dataset"], 0) + 1
        source_bucket = (
            "OFFICIAL_TOTAL" if task.get("endpoint") == "official" else "FINMIND_TOTAL"
        )
        counts[source_bucket] = counts.get(source_bucket, 0) + 1
    counts.setdefault("OFFICIAL_TOTAL", 0)
    counts.setdefault("FINMIND_TOTAL", 0)
    counts["TOTAL"] = counts["OFFICIAL_TOTAL"] + counts["FINMIND_TOTAL"]
    return counts


def estimate_quota_time(total_requests: int, quota_info: dict[str, int]) -> dict[str, float | int]:
    limit = max(int(quota_info["api_request_limit"]), 1)
    available_now = max(int(quota_info["remaining"]) - REQUEST_SAFETY_RESERVE, 0)
    after_current = max(total_requests - available_now, 0)
    additional_windows = math.ceil(after_current / limit) if after_current else 0
    windows = (1 if total_requests > 0 else 0) + additional_windows
    hours = total_requests / limit
    continuous_days = hours / 24.0
    eight_hour_days = hours / 8.0
    return {
        "request_limit_per_window": limit,
        "available_now_after_reserve": available_now,
        "quota_windows": windows,
        "estimated_hours_at_full_rate": hours,
        "estimated_continuous_days": continuous_days,
        "estimated_eight_hour_days": eight_hour_days,
    }


def probe_sponsorpro(session: requests.Session, first_trading_date: str | None) -> str:
    if not first_trading_date:
        return "standard"
    try:
        payload = request_json(session, FINMIND_STORAGE_URL, {
            "dataset": "TaiwanStockTradingDailyReport",
            "date": first_trading_date,
        })
        return "sponsorpro" if find_signed_url(payload) else "standard"
    except (PermissionError, ValueError, RuntimeError):
        return "standard"


# =============================================================================
# 4. 資料擷取與執行
# =============================================================================

def filter_rows_to_tickers(rows: Iterable[dict[str, Any]], tickers: set[str]) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get("stock_id", "")) in tickers]


def download_storage_parquet_rows(
    session: requests.Session,
    payload: dict[str, Any],
    tickers: set[str],
) -> list[dict[str, Any]]:
    signed_url = find_signed_url(payload)
    if not signed_url:
        raise RuntimeError("SponsorPro storage_objects 回應沒有下載網址。")
    # Signed URL 已自帶短期授權，不傳 FinMind Bearer Header，避免與物件儲存簽章衝突。
    response = requests.get(signed_url, timeout=HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    table = pq.read_table(BytesIO(response.content))
    if "stock_id" in table.column_names:
        mask = pc.is_in(table["stock_id"].cast(pa.string()), value_set=pa.array(sorted(tickers)))
        table = table.filter(mask)
    return table.to_pylist()


def fetch_task_rows(
    session: requests.Session | None,
    task: dict[str, Any],
    tickers: set[str],
    official_session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    endpoint = task["endpoint"]
    rows: list[dict[str, Any]]
    if endpoint == "official":
        if official_session is None:
            raise OfficialSourceError("官方資料 Session 尚未建立。")
        rows = def_fetch_official_dataset(
            official_session,
            task["dataset"],
            str(task["params"]["date"]),
            tickers,
        )
        return attach_source_metadata(rows, task)
    if session is None:
        raise RuntimeError("FinMind Session 尚未建立。")
    if endpoint == "branch":
        payload = request_json(session, FINMIND_BRANCH_URL, task["params"])
        return attach_source_metadata(extract_data_rows(payload), task)
    if endpoint == "branch_agg":
        payload = request_json(session, FINMIND_BRANCH_AGG_URL, task["params"])
        return attach_source_metadata(extract_data_rows(payload), task)
    if endpoint == "storage":
        payload = request_json(session, FINMIND_STORAGE_URL, task["params"])
        return attach_source_metadata(
            download_storage_parquet_rows(session, payload, tickers), task
        )
    if endpoint == "data":
        payload = request_json(session, FINMIND_DATA_URL, task["params"])
        rows = extract_data_rows(payload)
        if task["dataset"] in {
            "TaiwanStockGovernmentBankBuySell",
            "TaiwanStockBlockTradingDailyReport",
            "TaiwanStockIndustryChainMoneyFlow",
        }:
            expected_date = str(task["params"]["start_date"])
            rows = [row for row in rows if str(row.get("date", "")) == expected_date]
        if task["dataset"] in {
            "TaiwanStockGovernmentBankBuySell", "TaiwanStockBlockTradingDailyReport"
        }:
            rows = filter_rows_to_tickers(rows, tickers)
        return attach_source_metadata(rows, task)
    raise ValueError(f"未知 endpoint 類型：{endpoint}")


def fetch_task_rows_guarded(
    supportive_runtime: dict[str, Any],
    session: requests.Session | None,
    task: dict[str, Any],
    tickers: set[str],
    official_session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    if task.get("endpoint") == "official":
        return fetch_task_rows(session, task, tickers, official_session)
    circuit_breaker = supportive_runtime.get("circuit_breaker")
    if circuit_breaker is not None:
        return circuit_breaker.call(
            fetch_task_rows, session, task, tickers, official_session
        )
    return fetch_task_rows(session, task, tickers, official_session)


def calculate_request_interval(quota_info: dict[str, int]) -> float:
    limit = max(int(quota_info["api_request_limit"]), 1)
    target_per_window = max(int(limit * THROTTLE_USAGE_RATIO), 1)
    return QUOTA_WINDOW_SECONDS / target_per_window


def write_checkpoint_status(output_root: Path, status: dict[str, Any]) -> Path:
    audit_root = output_root / AUDIT_DIRECTORY
    audit_root.mkdir(parents=True, exist_ok=True)
    checkpoint_path = audit_root / CHECKPOINT_FILENAME
    temporary_path = checkpoint_path.with_name(checkpoint_path.name + ".tmp")
    temporary_path.write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    os.replace(temporary_path, checkpoint_path)
    return checkpoint_path


def durable_checkpoint(
    connection: duckdb.DuckDBPyConnection,
    output_root: Path,
    run_id: str,
    request_count: int,
    row_count: int,
    failures: int,
    last_partition: str | None,
    state: str,
) -> Path:
    connection.execute("CHECKPOINT")
    return write_checkpoint_status(output_root, {
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "run_id": run_id,
        "state": state,
        "fetch_order": "newest_first" if FETCH_NEWEST_FIRST else "oldest_first",
        "request_count": request_count,
        "row_count": row_count,
        "failures": failures,
        "last_partition": last_partition,
        "checkpoint_at": utc_now_iso(),
        "resume_instruction": "重新執行相同指令；成功 task 會由 request_ledger 自動跳過。",
    })


def execute_tasks(
    connection: duckdb.DuckDBPyConnection,
    session: requests.Session | None,
    tasks: Iterable[dict[str, Any]],
    tickers: list[str],
    completed_task_ids: set[str],
    quota_info: dict[str, int],
    output_root: Path,
    run_id: str,
    supportive_runtime: dict[str, Any],
    official_session: requests.Session | None = None,
) -> dict[str, Any]:
    available = max(quota_info["remaining"] - REQUEST_SAFETY_RESERVE, 0)
    run_cap = available if MAX_REQUESTS_PER_RUN <= 0 else min(available, MAX_REQUESTS_PER_RUN)
    ticker_set = set(tickers)
    request_interval = calculate_request_interval(quota_info)
    request_count = 0
    finmind_request_count = 0
    official_request_count = 0
    row_count = 0
    failures = 0
    official_failures = 0
    finmind_failures = 0
    consecutive_failures = 0
    stopped_for_quota = False
    stopped_for_network = False
    interrupted = False
    last_request_time = 0.0
    last_partition: str | None = None
    checkpoint_batch_size = int(
        supportive_runtime.get("checkpoint_batch_size", CHECKPOINT_BATCH_SIZE)
    )

    try:
        for task in tasks:
            if task["task_id"] in completed_task_ids:
                continue
            is_official = task.get("endpoint") == "official"
            if not is_official and finmind_request_count >= run_cap:
                stopped_for_quota = True
                break

            if not is_official:
                elapsed = time.monotonic() - last_request_time
                if last_request_time and elapsed < request_interval:
                    time.sleep(request_interval - elapsed)
            last_partition = task["partition_key"]
            try:
                if not is_official:
                    last_request_time = time.monotonic()
                rows = fetch_task_rows_guarded(
                    supportive_runtime, session, task, ticker_set, official_session
                )
                request_count += 1
                if is_official:
                    official_request_count += 1
                else:
                    finmind_request_count += 1
                written = upsert_rows(connection, task["dataset"], rows)
                row_count += written
                record_task_result(connection, task, "success", written, None)
                consecutive_failures = 0
                if task.get("entity_id") and task.get("range_start") and task.get("range_end"):
                    merge_range_coverage(
                        connection,
                        task["dataset"],
                        task["entity_id"],
                        task["range_start"],
                        task["range_end"],
                    )
                if task.get("entity_id") and task.get("cursor_end"):
                    update_cursor(connection, task["dataset"], task["entity_id"], task["cursor_end"])
                coverage_entities = list(task.get("coverage_entities", []))
                if coverage_entities:
                    if task.get("coverage_from_rows"):
                        coverage_dates = sorted({
                            str(row.get("date", "")) for row in rows if row.get("date")
                        })
                        coverage_date = coverage_dates[-1] if coverage_dates else None
                    else:
                        coverage_date = str(task.get("range_end") or task["params"].get("date", ""))
                    if coverage_date:
                        for entity_id in coverage_entities:
                            merge_range_coverage(
                                connection, task["dataset"], entity_id,
                                coverage_date, coverage_date,
                            )
                            update_cursor(
                                connection, task["dataset"], entity_id, coverage_date
                            )
            except Exception as exc:
                request_count += 1
                if is_official:
                    official_request_count += 1
                else:
                    finmind_request_count += 1
                failures += 1
                if is_official:
                    official_failures += 1
                else:
                    finmind_failures += 1
                if not is_official:
                    consecutive_failures += 1
                message = f"{type(exc).__name__}: {exc}"
                record_task_result(connection, task, "failed", 0, message[:2000])
                if is_official:
                    print(
                        f"官方來源暫不可用：{task['dataset']}；"
                        "本輪不建立 coverage，後續 FinMind 任務會自動補足。"
                    )
                    continue
                if "QUOTA_EXHAUSTED" in message:
                    stopped_for_quota = True
                    break
                # 4xx、權限或參數問題不可用大量 retry 轟炸 API。
                if isinstance(exc, (PermissionError, ValueError)):
                    raise
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    stopped_for_network = True
                    break

            if request_count and request_count % checkpoint_batch_size == 0:
                durable_checkpoint(
                    connection, output_root, run_id, request_count, row_count,
                    failures, last_partition, "running",
                )
            if request_count and request_count % PROGRESS_EVERY_REQUESTS == 0:
                print(
                    f"進度：本次 {request_count:,} requests，寫入 {row_count:,} rows，"
                    f"失敗 {failures:,}；checkpoint 已固定保存"
                )
    except KeyboardInterrupt:
        interrupted = True
    finally:
        final_state = (
            "interrupted" if interrupted else
            "paused_quota" if stopped_for_quota else
            "paused_network" if stopped_for_network else
            "batch_completed"
        )
        durable_checkpoint(
            connection, output_root, run_id, request_count, row_count,
            failures, last_partition, final_state,
        )

    return {
        "request_count": request_count,
        "finmind_request_count": finmind_request_count,
        "official_request_count": official_request_count,
        "row_count": row_count,
        "failures": failures,
        "official_failures": official_failures,
        "finmind_failures": finmind_failures,
        "stopped_for_quota": stopped_for_quota,
        "stopped_for_network": stopped_for_network,
        "interrupted": interrupted,
        "checkpoint_batch_size": checkpoint_batch_size,
        "last_partition": last_partition,
    }


# =============================================================================
# 5. Parquet、CSV 與稽核輸出
# =============================================================================

def export_filename(dataset: str, file_type: str) -> str:
    if OUTPUT_WITHOUT_EXTENSION:
        return dataset
    extension = ".parquet" if file_type == "parquet" else ".csv"
    return f"{dataset}{extension}"


def build_export_select(spec: dict[str, Any]) -> str:
    expressions: list[str] = []
    for column, _dtype in spec["columns"]:
        if column == "retrieved_at":
            continue
        if column == "date":
            expressions.append(
                f"strftime(CAST({quote_identifier(column)} AS DATE), '{EXPORT_DATE_FORMAT}') AS {quote_identifier(column)}"
            )
        else:
            expressions.append(quote_identifier(column))
    return ", ".join(expressions)


def export_all_tables(connection: duckdb.DuckDBPyConnection, output_root: Path) -> dict[str, Any]:
    parquet_root = output_root / PARQUET_DIRECTORY
    csv_root = output_root / CSV_DIRECTORY
    parquet_root.mkdir(parents=True, exist_ok=True)
    csv_root.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}

    for dataset, spec in TABLE_SPECS.items():
        table_name = quote_identifier(spec["table"])
        select_sql = build_export_select(spec)
        parquet_path = parquet_root / export_filename(dataset, "parquet")
        csv_path = csv_root / export_filename(dataset, "csv")
        csv_temp = csv_path.with_name(csv_path.name + ".utf8.tmp")

        escaped_parquet = str(parquet_path).replace("'", "''")
        escaped_csv_temp = str(csv_temp).replace("'", "''")
        connection.execute(
            f"COPY (SELECT {select_sql} FROM {table_name} ORDER BY date) "
            f"TO '{escaped_parquet}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        connection.execute(
            f"COPY (SELECT {select_sql} FROM {table_name} ORDER BY date) "
            f"TO '{escaped_csv_temp}' (FORMAT CSV, HEADER TRUE)"
        )
        with csv_temp.open("rb") as source, csv_path.open("wb") as target:
            target.write(b"\xef\xbb\xbf")
            while chunk := source.read(1024 * 1024):
                target.write(chunk)
        csv_temp.unlink(missing_ok=True)

        row_total = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        results[dataset] = {
            "rows": int(row_total),
            "parquet": str(parquet_path),
            "csv": str(csv_path),
        }
    return results


def write_audit_report(output_root: Path, report: dict[str, Any]) -> Path:
    audit_root = output_root / AUDIT_DIRECTORY
    audit_root.mkdir(parents=True, exist_ok=True)
    run_id = report["run_id"]
    path = audit_root / f"FinMind_Run_{run_id}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def print_plan(
    tickers: list[str],
    trading_dates: list[str],
    branch_mode: str,
    range_batch_mode: str,
    counts: dict[str, int],
    quota_info: dict[str, int],
    estimate: dict[str, float | int],
    source_mode: str = DEFAULT_SOURCE_MODE,
) -> None:
    print("\n" + "=" * 78)
    print(f"{ENGINE_NAME} {ENGINE_VERSION} · 擷取計畫")
    print("=" * 78)
    print(f"股票數：{len(tickers):,}")
    print(f"交易日：{len(trading_dates):,}")
    print(f"回補順序：{'最新 → 歷史' if FETCH_NEWEST_FIRST else '歷史 → 最新'}")
    print(f"固定保存：每 {CHECKPOINT_BATCH_SIZE} requests 建立一次 durable checkpoint")
    print(f"分點模式：{branch_mode}")
    print(f"區間批次：{range_batch_mode}")
    print(f"來源模式：{source_mode}")
    if source_mode != "official_only":
        print(f"FinMind 帳號額度：{quota_info['user_count']:,} / {quota_info['api_request_limit']:,} requests/window")
    for dataset in ENABLED_DATASETS:
        if ENABLED_DATASETS[dataset]:
            print(f"- {dataset}: {counts.get(dataset, 0):,} requests")
    print(f"官方免費批次：{counts.get('OFFICIAL_TOTAL', 0):,}")
    print(f"FinMind requests：{counts.get('FINMIND_TOTAL', 0):,}")
    print(f"待執行合計：{counts.get('TOTAL', 0):,} tasks")
    print(f"FinMind 滿載估計：{estimate['estimated_hours_at_full_rate']:.2f} 小時")
    print(f"24 小時連續執行：約 {estimate['estimated_continuous_days']:.2f} 天")
    print(f"每日執行 8 小時：約 {estimate['estimated_eight_hour_days']:.2f} 天")
    print("=" * 78 + "\n")


# =============================================================================
# 6. CLI 與主流程
# =============================================================================

def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=ENGINE_NAME)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE, help="YYYY-MM-DD")
    parser.add_argument("--end-date", default=DEFAULT_END_DATE, help="YYYY-MM-DD 或 latest")
    parser.add_argument("--ticker-file", default=PRIMARY_TICKER_FILE)
    parser.add_argument("--ticker-limit", type=int, default=DEFAULT_TICKER_LIMIT)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--source-mode",
        choices=SOURCE_MODE_CHOICES,
        default=DEFAULT_SOURCE_MODE,
        help="hybrid（官方免費優先、FinMind補缺口）、finmind_only 或 official_only",
    )
    parser.add_argument("--branch-mode", choices=["auto", "standard", "sponsorpro"], default=DEFAULT_BRANCH_MODE)
    parser.add_argument(
        "--range-batch-mode",
        choices=RANGE_BATCH_MODE_CHOICES,
        default=RANGE_BATCH_MODE,
        help="區間型資料批次：two_year（預設）、full_history（最少 request）或 calendar_year（最保守）",
    )
    parser.add_argument("--celeritas-path", default=DEFAULT_CELERITAS_PATH)
    parser.add_argument("--aegis-path", default=DEFAULT_AEGIS_PATH)
    parser.add_argument(
        "--datasets", default="",
        help="逗號分隔資料集；空白表示使用程式頂部 ENABLED_DATASETS。",
    )
    parser.add_argument(
        "--latest-only", action="store_true",
        help="只抓最新交易日；適合每日分點獨立更新。",
    )
    parser.add_argument("--plan-only", action="store_true", help="只計算 requests 與時間，不擷取付費資料")
    parser.add_argument("--yes", action="store_true", help="略過執行前確認")
    return parser


def confirm_execution() -> bool:
    answer = input("確定開始擷取？輸入 YES 繼續：").strip().upper()
    return answer == "YES"


def run_engine(arguments: argparse.Namespace) -> int:
    selected_datasets = configure_enabled_datasets(arguments.datasets)
    source_mode = arguments.source_mode
    start_date = arguments.start_date
    end_date = resolve_end_date(arguments.end_date)
    parse_iso_date(start_date)
    if start_date > end_date:
        raise ValueError("start-date 不可晚於 end-date。")

    supportive_runtime = initialize_supportive_runtime(
        arguments.celeritas_path, arguments.aegis_path
    )
    supportive_report = supportive_runtime_report(supportive_runtime)
    print(
        "Supportive modules："
        f"Celeritas={supportive_report['celeritas_version']}；"
        f"Aegis={supportive_report['aegis_version']}；"
        f"Checkpoint Batch={supportive_report['checkpoint_batch_size']}"
    )

    tickers = read_tickers(arguments.ticker_file, arguments.ticker_limit)
    output_root = Path(arguments.output_root).expanduser().resolve()
    connection = open_database(output_root)
    initialize_database(connection)

    official_session = build_official_session()
    session: requests.Session | None = None
    if source_mode == "official_only":
        quota_info = {
            "user_count": 0,
            "api_request_limit": 1,
            "remaining": 0,
        }
    else:
        token = prompt_api_token()
        session = build_session(token)
        quota_info = get_quota_info(session)
    discovery_start = start_date
    if arguments.latest_only:
        discovery_start = format_iso_date(parse_iso_date(end_date) - timedelta(days=21))
    trading_dates = (
        fetch_trading_dates(session, discovery_start, end_date)
        if session is not None else fallback_weekdays(discovery_start, end_date)
    )
    if not trading_dates:
        raise RuntimeError("指定期間沒有可用交易日。")
    if arguments.latest_only:
        trading_dates = [trading_dates[-1]]
        start_date = trading_dates[0]

    branch_mode = arguments.branch_mode
    if branch_mode == "auto" and not arguments.plan_only and session is not None:
        branch_mode = probe_sponsorpro(session, trading_dates[-1])
    elif branch_mode == "auto":
        branch_mode = "standard"

    completed = get_completed_task_ids(connection)
    planning_tasks = iter_all_tasks(
        connection, tickers, trading_dates, start_date, end_date, branch_mode,
        arguments.range_batch_mode, source_mode,
    )
    counts = count_pending_tasks(planning_tasks, completed)
    estimate = estimate_quota_time(counts["FINMIND_TOTAL"], quota_info)
    print_plan(
        tickers, trading_dates, branch_mode, arguments.range_batch_mode,
        counts, quota_info, estimate, source_mode,
    )

    if arguments.plan_only:
        connection.close()
        return 0
    if not arguments.yes and not confirm_execution():
        print("已取消，沒有擷取資料。")
        connection.close()
        return 0

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    started_at = utc_now_iso()
    connection.execute(
        "INSERT INTO run_audit (run_id, started_at, status) VALUES (?, ?, 'running')",
        [run_id, started_at],
    )

    result: dict[str, Any]
    status = "completed"
    try:
        execution_tasks = iter_all_tasks(
            connection, tickers, trading_dates, start_date, end_date, branch_mode,
            arguments.range_batch_mode, source_mode,
        )
        result = execute_tasks(
            connection, session, execution_tasks, tickers, completed, quota_info,
            output_root, run_id, supportive_runtime, official_session,
        )
        if result["interrupted"]:
            status = "interrupted"
        elif result["stopped_for_quota"]:
            status = "paused_quota"
        elif result["stopped_for_network"]:
            status = "paused_network"
        elif result["finmind_failures"]:
            status = "completed_with_failures"
        elif result["official_failures"]:
            status = (
                "completed_with_official_failures"
                if source_mode == "official_only" else "completed_with_fallback"
            )
        exports = export_all_tables(connection, output_root)
    except Exception:
        status = "failed"
        raise
    finally:
        finished_at = utc_now_iso()
        existing = locals().get("result", {"request_count": 0, "row_count": 0})
        detail = {
            "engine": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "run_id": run_id,
            "started_at": started_at,
            "finished_at": finished_at,
            "status": status,
            "start_date": start_date,
            "end_date": end_date,
            "ticker_count": len(tickers),
            "branch_mode": branch_mode,
            "source_mode": source_mode,
            "source_policy": {
                dataset: DATA_SOURCE_POLICY.get(dataset, "finmind_api")
                for dataset in selected_datasets
            },
            "range_batch_mode": arguments.range_batch_mode,
            "selected_datasets": selected_datasets,
            "latest_only": arguments.latest_only,
            "quota": quota_info,
            "supportive_runtime": supportive_runtime_report(supportive_runtime),
            "plan_counts": counts,
            "estimate": estimate,
            "execution": existing,
            "exports": locals().get("exports", {}),
        }
        audit_path = write_audit_report(output_root, detail)
        connection.execute("""
            UPDATE run_audit
            SET finished_at = ?, status = ?, request_count = ?, row_count = ?, detail_json = ?
            WHERE run_id = ?
        """, [
            finished_at, status, existing.get("request_count", 0),
            existing.get("row_count", 0), json.dumps(detail, ensure_ascii=False), run_id,
        ])
        print(f"稽核報告：{audit_path}")
        connection.close()

    print(f"執行狀態：{status}")
    print(
        f"本次 FinMind requests：{result['finmind_request_count']:,}；"
        f"官方免費批次：{result['official_request_count']:,}；"
        f"寫入 rows：{result['row_count']:,}"
    )
    if status == "paused_quota":
        print("額度保留值已到達；下個額度視窗重跑相同指令即可從斷點繼續。")
    if status == "paused_network":
        print("連續網路錯誤已達安全門檻；網路恢復後重跑相同指令即可續傳。")
    if status == "interrupted":
        print("已固定保存中斷前資料；重跑相同指令即可從 checkpoint 繼續。")
        raise KeyboardInterrupt
    return 0


def main() -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args()
    try:
        return run_engine(arguments)
    except KeyboardInterrupt:
        print("\n使用者中止；已完成的 partition 仍保留於 DuckDB。", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TWSE、TPEX、TDCC 免費官方資料介面。

本模組只處理官方公開 API／CSV，不處理券商分點驗證碼頁，也不使用
代理、IP 輪替或驗證碼繞過。所有函式回傳與主引擎 TABLE_SPECS 相容的欄位。
"""

from __future__ import annotations


# =============================================================================
# 0. 所有可調參數
# =============================================================================

OFFICIAL_HTTP_TIMEOUT_SECONDS = 120

TDCC_HOLDING_URL = "https://opendata.tdcc.com.tw/getOD.ashx?id=1-5"

TWSE_ENDPOINTS = {
    "TaiwanStockPrice": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
    "TaiwanStockMarginPurchaseShortSale": "https://openapi.twse.com.tw/v1/exchangeReport/MI_MARGN",
    "TaiwanStockBlockTrade": "https://www.twse.com.tw/rwd/zh/block/BFIAUU",
}

TPEX_ENDPOINTS = {
    "TaiwanStockPrice": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes",
    "TaiwanStockMarginPurchaseShortSale": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_margin_balance",
    "TaiwanStockBlockTrade": "https://www.tpex.org.tw/openapi/v1/tpex_daily_qutoes_block",
}

TDCC_LEVEL_LABELS = {
    "1": "1-999",
    "2": "1,000-5,000",
    "3": "5,001-10,000",
    "4": "10,001-15,000",
    "5": "15,001-20,000",
    "6": "20,001-30,000",
    "7": "30,001-40,000",
    "8": "40,001-50,000",
    "9": "50,001-100,000",
    "10": "100,001-200,000",
    "11": "200,001-400,000",
    "12": "400,001-600,000",
    "13": "600,001-800,000",
    "14": "800,001-1,000,000",
    "15": "1,000,001以上",
    "16": "差異數調整",
    "17": "合計",
}


# =============================================================================
# 1. 匯入與例外
# =============================================================================

import csv
import io
import json
import re
from datetime import datetime, timezone
from typing import Any, Iterable


class OfficialSourceError(RuntimeError):
    """官方來源無法形成完整且日期正確的資料時使用。"""


# =============================================================================
# 2. 通用正規化
# =============================================================================

def def_utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def def_clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\u3000", " ").strip()


def def_normalize_key(value: Any) -> str:
    text = def_clean_text(value).lower()
    return re.sub(r"[\s_\-（）()／/%:,，。]+", "", text)


def def_index_row(row: dict[str, Any]) -> dict[str, Any]:
    return {def_normalize_key(key): value for key, value in row.items()}


def def_get_any(row: dict[str, Any], aliases: Iterable[str], default: Any = None) -> Any:
    indexed = def_index_row(row)
    for alias in aliases:
        key = def_normalize_key(alias)
        if key in indexed:
            return indexed[key]
    return default


def def_number_text(value: Any) -> str:
    text = def_clean_text(value)
    if text in {"", "--", "---", "N/A", "nan", "None"}:
        return ""
    text = text.replace(",", "").replace("+", "")
    text = text.replace("−", "-").replace("－", "-")
    return text


def def_to_int(value: Any, default: int = 0) -> int:
    text = def_number_text(value)
    if not text:
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def def_to_float(value: Any, default: float = 0.0) -> float:
    text = def_number_text(value)
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def def_normalize_stock_id(value: Any) -> str:
    text = def_clean_text(value).upper()
    text = re.sub(r"\.(TW|TWO)$", "", text)
    match = re.search(r"[0-9A-Z]{4,8}", text)
    return match.group(0) if match else ""


def def_normalize_date(value: Any) -> str:
    text = def_clean_text(value)
    digits = re.sub(r"\D", "", text)
    if len(digits) == 8 and digits[:4].isdigit():
        year = int(digits[:4])
        if 1900 <= year <= 2200:
            return f"{year:04d}-{digits[4:6]}-{digits[6:8]}"
    if len(digits) == 7 and digits[:3].isdigit():
        year = int(digits[:3]) + 1911
        return f"{year:04d}-{digits[3:5]}-{digits[5:7]}"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text
    raise OfficialSourceError(f"無法辨識官方資料日期：{value!r}")


def def_decode_csv(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp950", "big5"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise OfficialSourceError("官方 CSV 編碼無法辨識。")


def def_json_rows(response: Any) -> list[dict[str, Any]]:
    try:
        payload = response.json()
    except Exception as exc:
        raise OfficialSourceError("官方 API 回傳非 JSON。") from exc
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        data = payload.get("data", payload.get("Data", []))
        if isinstance(data, list) and all(isinstance(row, dict) for row in data):
            return data
        fields = payload.get("fields") or payload.get("Fields")
        if isinstance(fields, list) and isinstance(data, list):
            return [dict(zip(fields, row)) for row in data if isinstance(row, list)]
    raise OfficialSourceError("官方 API JSON 結構不受支援。")


def def_request(session: Any, url: str, params: dict[str, Any] | None = None) -> Any:
    response = session.get(url, params=params, timeout=OFFICIAL_HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response


def def_source_fields(provider: str, dataset: str) -> dict[str, str]:
    return {
        "source_provider": provider,
        "source_mode": "official_open_data" if provider == "TDCC" else "official_api",
        "source_dataset": dataset,
        "retrieved_at": def_utc_now_iso(),
    }


def def_validate_snapshot_date(
    rows: list[dict[str, Any]],
    target_date: str,
    dataset: str,
    allow_empty: bool = False,
) -> None:
    if not rows:
        if allow_empty:
            return
        raise OfficialSourceError(f"{dataset} 官方端點回傳空資料。")
    dates = {str(row.get("date", "")) for row in rows}
    if dates != {target_date}:
        raise OfficialSourceError(
            f"{dataset} 官方快照日期不符：預期 {target_date}，實際 {sorted(dates)}"
        )


# =============================================================================
# 3. TDCC 集保戶股權分散表
# =============================================================================

def def_parse_tdcc_holding_csv(
    content: bytes,
    target_tickers: set[str],
) -> list[dict[str, Any]]:
    text = def_decode_csv(content)
    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict[str, Any]] = []
    for source in reader:
        stock_id = def_normalize_stock_id(
            def_get_any(source, ("證券代號", "Securities Code"))
        )
        if not stock_id or stock_id not in target_tickers:
            continue
        level = def_clean_text(def_get_any(source, ("持股分級", "Securities Holding Range")))
        row = {
            "date": def_normalize_date(def_get_any(source, ("資料日期", "Date"))),
            "stock_id": stock_id,
            "HoldingSharesLevel": TDCC_LEVEL_LABELS.get(level, level),
            "people": def_to_int(def_get_any(source, ("人數", "Number of Holders"))),
            "percent": def_to_float(def_get_any(
                source,
                ("占集保庫存數比例%", "佔集保庫存數比例%", "Percentage of Centrally Deposited Securities"),
            )),
            "unit": def_to_int(def_get_any(source, ("股數", "Number of Shares/Units"))),
        }
        row.update(def_source_fields("TDCC", "TDCC_OPEN_DATA_1-5"))
        rows.append(row)
    if not rows:
        raise OfficialSourceError("TDCC 股權分散表沒有指定股票資料。")
    return rows


def def_fetch_tdcc_holding(session: Any, target_tickers: set[str]) -> list[dict[str, Any]]:
    response = def_request(session, TDCC_HOLDING_URL)
    return def_parse_tdcc_holding_csv(response.content, target_tickers)


# =============================================================================
# 4. 上市／上櫃日價量
# =============================================================================

def def_parse_price_rows(
    source_rows: Iterable[dict[str, Any]],
    provider: str,
    target_tickers: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in source_rows:
        stock_id = def_normalize_stock_id(def_get_any(
            source, ("證券代號", "股票代號", "SecuritiesCompanyCode", "Code")
        ))
        if stock_id not in target_tickers:
            continue
        open_price = def_to_float(def_get_any(source, ("開盤價", "開盤", "Open")))
        close_price = def_to_float(def_get_any(source, ("收盤價", "收盤", "Close")))
        row = {
            "date": def_normalize_date(def_get_any(source, ("日期", "資料日期", "Date"))),
            "stock_id": stock_id,
            "Trading_Volume": def_to_int(def_get_any(source, ("成交股數", "TradingShares"))),
            "Trading_money": def_to_float(def_get_any(source, ("成交金額", "TransactionAmount"))),
            "open": open_price,
            "max": def_to_float(def_get_any(source, ("最高價", "最高", "High"))),
            "min": def_to_float(def_get_any(source, ("最低價", "最低", "Low"))),
            "close": close_price,
            "spread": def_to_float(def_get_any(source, ("漲跌價差", "漲跌", "Change"))),
            "Trading_turnover": def_to_float(def_get_any(
                source, ("成交筆數", "TransactionNumber"), 0
            )),
        }
        row.update(def_source_fields(provider, "STOCK_DAY_ALL" if provider == "TWSE" else "tpex_mainboard_daily_close_quotes"))
        rows.append(row)
    return rows


# =============================================================================
# 5. 上市／上櫃融資融券
# =============================================================================

def def_parse_margin_rows(
    source_rows: Iterable[dict[str, Any]],
    provider: str,
    target_tickers: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in source_rows:
        stock_id = def_normalize_stock_id(def_get_any(
            source, ("股票代號", "證券代號", "SecuritiesCompanyCode", "Code")
        ))
        if stock_id not in target_tickers:
            continue
        row = {
            "date": def_normalize_date(def_get_any(source, ("日期", "資料日期", "Date"))),
            "stock_id": stock_id,
            "MarginPurchaseBuy": def_to_int(def_get_any(source, ("融資買進", "資買", "MarginPurchase"))),
            "MarginPurchaseCashRepayment": def_to_int(def_get_any(source, ("現金償還", "現償", "CashRedemption"))),
            "MarginPurchaseLimit": def_to_int(def_get_any(source, ("融資限額", "資限額", "MarginPurchaseQuota"))),
            "MarginPurchaseSell": def_to_int(def_get_any(source, ("融資賣出", "資賣", "MarginSales"))),
            "MarginPurchaseTodayBalance": def_to_int(def_get_any(source, ("融資今日餘額", "資餘額", "MarginPurchaseBalance"))),
            "MarginPurchaseYesterdayBalance": def_to_int(def_get_any(source, ("融資前日餘額", "前資餘額", "MarginPurchaseBalancePreviousDay"))),
            "Note": def_clean_text(def_get_any(source, ("備註", "Note"))),
            "OffsetLoanAndShort": def_to_int(def_get_any(source, ("資券互抵", "資券相抵", "Offsetting"))),
            "ShortSaleBuy": def_to_int(def_get_any(source, ("融券買進", "券買", "ShortConvering", "ShortCovering"))),
            "ShortSaleCashRepayment": def_to_int(def_get_any(source, ("現券償還", "券償", "StockRedemption"))),
            "ShortSaleLimit": def_to_int(def_get_any(source, ("融券限額", "券限額", "ShortSaleQuota"))),
            "ShortSaleSell": def_to_int(def_get_any(source, ("融券賣出", "券賣", "ShortSale"))),
            "ShortSaleTodayBalance": def_to_int(def_get_any(source, ("融券今日餘額", "券餘額", "ShortSaleBalance"))),
            "ShortSaleYesterdayBalance": def_to_int(def_get_any(source, ("融券前日餘額", "前券餘額", "ShortSaleBalancePreviousDay"))),
        }
        row.update(def_source_fields(provider, "MI_MARGN" if provider == "TWSE" else "tpex_mainboard_margin_balance"))
        rows.append(row)
    return rows


# =============================================================================
# 6. 上市／上櫃鉅額交易
# =============================================================================

def def_find_csv_header(all_rows: list[list[str]], required_first: str) -> tuple[list[str], int]:
    required = def_normalize_key(required_first)
    for index, row in enumerate(all_rows):
        if row and def_normalize_key(row[0]) == required:
            return [def_clean_text(value) for value in row], index
    raise OfficialSourceError(f"官方 CSV 找不到欄位列：{required_first}")


def def_parse_twse_block_csv(
    content: bytes,
    target_date: str,
    target_tickers: set[str],
) -> list[dict[str, Any]]:
    raw_rows = list(csv.reader(io.StringIO(def_decode_csv(content))))
    header, header_index = def_find_csv_header(raw_rows, "證券代號")
    rows: list[dict[str, Any]] = []
    for values in raw_rows[header_index + 1:]:
        if len(values) < len(header):
            continue
        source = dict(zip(header, values))
        stock_id = def_normalize_stock_id(def_get_any(source, ("證券代號", "Code")))
        if stock_id not in target_tickers:
            continue
        row = {
            "date": target_date,
            "stock_id": stock_id,
            "trade_type": def_clean_text(def_get_any(source, ("交易別", "交易型態"))),
            "price": def_to_float(def_get_any(source, ("成交價", "成交價格"))),
            "volume": def_to_int(def_get_any(source, ("成交股數",))),
            "trading_money": def_to_float(def_get_any(source, ("成交金額", "成交值"))),
        }
        row.update(def_source_fields("TWSE", "BFIAUU"))
        rows.append(row)
    return rows


def def_parse_tpex_block_rows(
    source_rows: Iterable[dict[str, Any]],
    target_tickers: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in source_rows:
        stock_id = def_normalize_stock_id(def_get_any(
            source, ("Code", "SecuritiesCompanyCode", "代號", "證券代號")
        ))
        if stock_id not in target_tickers:
            continue
        row = {
            "date": def_normalize_date(def_get_any(source, ("Date", "TradingDate", "資料日期", "成交日期"))),
            "stock_id": stock_id,
            "trade_type": def_clean_text(def_get_any(source, ("TransactionType", "交易型態"))),
            "price": def_to_float(def_get_any(source, ("TradePrice", "WeightedAveragePrice", "成交價格"))),
            "volume": def_to_int(def_get_any(source, ("NumberOfSharesTraded", "成交股數"))),
            "trading_money": def_to_float(def_get_any(source, ("TradeValue", "TradingValue", "成交值", "成交金額"))),
        }
        row.update(def_source_fields("TPEX", "tpex_daily_qutoes_block"))
        rows.append(row)
    return rows


def def_fetch_twse_dataset(
    session: Any,
    dataset: str,
    target_date: str,
    target_tickers: set[str],
) -> list[dict[str, Any]]:
    url = TWSE_ENDPOINTS[dataset]
    if dataset == "TaiwanStockBlockTrade":
        response = def_request(session, url, {
            "date": target_date.replace("-", ""),
            "response": "csv",
            "selectType": "S",
        })
        return def_parse_twse_block_csv(response.content, target_date, target_tickers)
    response = def_request(session, url)
    source_rows = def_json_rows(response)
    if dataset == "TaiwanStockPrice":
        return def_parse_price_rows(source_rows, "TWSE", target_tickers)
    if dataset == "TaiwanStockMarginPurchaseShortSale":
        return def_parse_margin_rows(source_rows, "TWSE", target_tickers)
    raise OfficialSourceError(f"TWSE 不支援資料集：{dataset}")


def def_fetch_tpex_dataset(
    session: Any,
    dataset: str,
    target_date: str,
    target_tickers: set[str],
) -> list[dict[str, Any]]:
    del target_date
    response = def_request(session, TPEX_ENDPOINTS[dataset])
    source_rows = def_json_rows(response)
    if dataset == "TaiwanStockPrice":
        return def_parse_price_rows(source_rows, "TPEX", target_tickers)
    if dataset == "TaiwanStockMarginPurchaseShortSale":
        return def_parse_margin_rows(source_rows, "TPEX", target_tickers)
    if dataset == "TaiwanStockBlockTrade":
        return def_parse_tpex_block_rows(source_rows, target_tickers)
    raise OfficialSourceError(f"TPEX 不支援資料集：{dataset}")


# =============================================================================
# 7. 單一入口
# =============================================================================

def def_fetch_official_dataset(
    session: Any,
    dataset: str,
    target_date: str,
    target_tickers: set[str],
) -> list[dict[str, Any]]:
    """擷取完整官方快照；任一市場失敗即整批失敗，讓主引擎改走 FinMind。"""
    if dataset == "TaiwanStockHoldingSharesPer":
        return def_fetch_tdcc_holding(session, target_tickers)

    if dataset not in TWSE_ENDPOINTS or dataset not in TPEX_ENDPOINTS:
        raise OfficialSourceError(f"沒有官方免費介面：{dataset}")

    errors: list[str] = []
    combined: list[dict[str, Any]] = []
    for provider, fetcher in (("TWSE", def_fetch_twse_dataset), ("TPEX", def_fetch_tpex_dataset)):
        try:
            rows = fetcher(session, dataset, target_date, target_tickers)
            def_validate_snapshot_date(
                rows,
                target_date,
                f"{provider}/{dataset}",
                allow_empty=(dataset == "TaiwanStockBlockTrade"),
            )
            combined.extend(rows)
        except Exception as exc:
            errors.append(f"{provider}: {type(exc).__name__}: {exc}")
    if errors:
        raise OfficialSourceError("；".join(errors))
    return combined


__all__ = [
    "OfficialSourceError",
    "def_fetch_official_dataset",
    "def_normalize_date",
    "def_parse_margin_rows",
    "def_parse_price_rows",
    "def_parse_tdcc_holding_csv",
    "def_parse_tpex_block_rows",
    "def_parse_twse_block_csv",
]

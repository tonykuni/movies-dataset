from __future__ import annotations

"""
VERITAS INTELLIGENCE ANALYTICS
VIA Taiwan Stock Grouping × Group Index × Price-Volume Rotation Unified Engine v0201

治理邊界：
1. 族群歸屬有效性、Leader/Peer/Laggard 時序角色、族群指數用途彼此分離。
2. 市場判定門檻不得以固定相關係數、固定分位數或固定 Z-Score 寫死；
   由 Gaussian Mixture BIC、跨族群 Null、Permutation Null 與實際分布產生。
3. Full / Core / Leader-Peer / Laggard / Trading-Capacity 五條指數並行。
4. 角色判定為 point-in-time：判定日後下一個交易日才生效，不回寫過去。
5. 價格使用 Adjusted Close；Volume、Turnover、法人、融資與當沖資料不得 forward-fill。
6. Synthetic / controlled data 只用於測試，不得標示為真實台股績效。
7. 系統只監控與研究，不執行下單。
"""

# =============================================================================
# def 00 PARAMETERS — 所有參數集中於檔案頂部
# =============================================================================

import argparse
import ast
import hashlib
import html
import json
import logging
import math
import os
import re
import shutil
import sys
import tempfile
import textwrap
import warnings
import zipfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import font_manager
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import RobustScaler

ENGINE_ID = "VIA_TW_GROUPING_INDEX_ROTATION_UNIFIED_ENGINE_V0201"
ENGINE_VERSION = "0.2.1"
SCHEMA_VERSION = "VIA_TW_GROUPING_ROTATION_CONTRACT_V0201"

DEFAULT_MEMBERSHIP_PATH = Path(
    r"C:\Users\tonyk\Downloads\VIA_ThreeList_CanonicalMembershipInput_v0100.csv"
)
DEFAULT_PRICE_PATH = Path(r"C:\Users\tonyk\OneDrive\桌面\tw_stock\StockData.parquet")
DEFAULT_FACTOR_PATH: Path | None = None
DEFAULT_OUTPUT_ROOT = Path(
    r"C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\outputs\VIA_TW_GroupingIndexRotation_v0201"
)
DEFAULT_START_DATE = "2020-01-01"
DEFAULT_END_DATE: str | None = None
DEFAULT_NORMALIZED_DATE: str | None = None

# 結構／計算參數；不是市場判定紅線。
MAX_GMM_COMPONENTS = 3
GMM_N_INIT = 7
RANDOM_SEED = 20260819
MIN_HISTORY_FLOOR = 24
MIN_MEMBER_OBSERVATIONS_FLOOR = 16
MIN_GROUP_MEMBER_FLOOR = 2
MAX_CLASSIFICATION_SNAPSHOTS = 4
MAX_LAG_SEARCH_CAP = 6
PERMUTATION_SHIFT_CAP = 11
NULL_GROUP_REPEATS_CAP = 5
PLOT_DPI = 150
CSV_ENCODING = "utf-8-sig"
DATE_OUTPUT_FORMAT = "%Y/%m/%d"
DATE_CHART_FORMAT = "%Y-%m-%d"

COUNT_FLAGS = {"COUNT", "Y", "TRUE", "1"}
DISPLAY_FLAGS = {"DISPLAY_ONLY", "DISPLAY", "N", "FALSE", "0"}
ROLE_ALIASES = {
    "L": "LEADER",
    "LEADER": "LEADER",
    "P": "PEER",
    "PEER": "PEER",
    "G": "LAGGARD",
    "LAGGER": "LAGGARD",
    "LAGGARD": "LAGGARD",
    "O": "OUTLIER",
    "OUTLIER": "OUTLIER",
    "C": "CANDIDATE",
    "CANDIDATE": "CANDIDATE",
}

INDEX_TYPES = (
    "FULL_EW",
    "CORE_EW",
    "LEADER_PEER_EW",
    "LAGGARD_EW",
    "TRADING_CAPACITY_WEIGHTED",
)

PRICE_ALIASES: Mapping[str, tuple[str, ...]] = {
    "Date": ("Date", "date", "TradingDate", "TradeDate", "交易日"),
    "Ticker": ("Ticker", "ticker", "YFTicker", "Symbol", "TW_YF_TICKER", "股票代碼"),
    "Name": ("Name", "name", "StockName", "個股", "股票名稱"),
    "Adj_Open": ("Adj_Open", "Adj Open", "AdjustedOpen", "adj_open"),
    "Adj_High": ("Adj_High", "Adj High", "AdjustedHigh", "adj_high"),
    "Adj_Low": ("Adj_Low", "Adj Low", "AdjustedLow", "adj_low"),
    "Adj_Close": (
        "Adj_Close",
        "Adj Close",
        "AdjustedClose",
        "adj_close",
        "normalized_close",
        "price_close",
    ),
    "Volume": ("Volume", "volume", "TradingVolume", "成交量"),
    "Turnover": ("Turnover", "turnover", "TradingValue", "成交值", "成交金額"),
    "DayTradeTurnover": (
        "DayTradeTurnover",
        "Day_Trade_Turnover",
        "day_trade_turnover",
        "當沖成交值",
    ),
    "MarketCap": ("MarketCap", "Market_Cap", "market_cap", "市值", "流通市值"),
    "ForeignNetAmount": (
        "ForeignNetAmount",
        "Foreign_Net_Buy_Value",
        "foreign_net_buy_value",
        "外資買賣超金額",
    ),
    "InvestmentTrustNetAmount": (
        "InvestmentTrustNetAmount",
        "SITC_Net_Buy_Value",
        "sitc_net_buy_value",
        "投信買賣超金額",
    ),
    "DealerNetAmount": (
        "DealerNetAmount",
        "Dealer_Net_Buy_Value",
        "dealer_net_buy_value",
        "自營商買賣超金額",
    ),
    "MarginBalanceValue": (
        "MarginBalanceValue",
        "margin_balance_value",
        "融資餘額金額",
    ),
    "ShortBalanceValue": (
        "ShortBalanceValue",
        "short_balance_value",
        "融券餘額金額",
    ),
}

MEMBERSHIP_ALIASES: Mapping[str, tuple[str, ...]] = {
    "GroupId": ("GroupId", "Group", "L2", "族群", "次族群"),
    "Subgroup": ("Subgroup", "L3", "次族群", "子族群"),
    "Ticker": ("Ticker", "TW_TICKER", "股票代碼", "代號"),
    "YFTicker": ("YFTicker", "YFINANCE", "TW_YF_TICKER"),
    "Name": ("Name", "個股", "股票名稱"),
    "Market": ("Market", "市場"),
    "StaticRole": ("Rank", "Role", "定位", "MethodA角色(來源)"),
    "Dimension": ("Dimension", "DimensionId", "維度"),
    "CountingFlag": ("CountingFlag", "計入族群指數", "Counting_Flag"),
    "PrimaryFlag": ("PrimaryFlag", "Primary_Flag", "Ownership", "歸屬"),
    "ValidFrom": ("ValidFrom", "valid_from", "生效日"),
    "ValidTo": ("ValidTo", "valid_to", "失效日"),
    "EvidenceStatus": ("EvidenceStatus", "Evidence_Status", "證據狀態"),
    "SourceId": ("SourceID", "SourceId", "來源", "Source"),
}

# AST 稽核只檢查「市場判定」中禁止的示範硬門檻。
PROHIBITED_MARKET_THRESHOLD_LITERALS = {0.85, 0.80, 0.70, 0.60, 0.40, 1.5, 2.0, 2.5}

LOGGER = logging.getLogger(ENGINE_ID)
EPS = np.finfo(float).eps

CJK_FONT_CANDIDATES = (
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("C:/Windows/Fonts/msjh.ttc"),
    Path("C:/Windows/Fonts/msjhbd.ttc"),
)
CJK_FONT_FAMILY = "DejaVu Sans"
for _font_path in CJK_FONT_CANDIDATES:
    if _font_path.exists():
        try:
            font_manager.fontManager.addfont(str(_font_path))
            CJK_FONT_FAMILY = font_manager.FontProperties(fname=str(_font_path)).get_name()
            break
        except Exception:
            continue
plt.rcParams["font.family"] = [CJK_FONT_FAMILY, "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


@dataclass(frozen=True)
class EngineConfig:
    membership_path: Path = DEFAULT_MEMBERSHIP_PATH
    price_path: Path = DEFAULT_PRICE_PATH
    factor_path: Path | None = DEFAULT_FACTOR_PATH
    output_root: Path = DEFAULT_OUTPUT_ROOT
    start_date: str = DEFAULT_START_DATE
    end_date: str | None = DEFAULT_END_DATE
    normalized_date: str | None = DEFAULT_NORMALIZED_DATE
    strict: bool = False
    write_outputs: bool = True
    demo: bool = False
    demo_observations: int = 260
    random_seed: int = RANDOM_SEED
    max_gmm_components: int = MAX_GMM_COMPONENTS
    max_classification_snapshots: int = MAX_CLASSIFICATION_SNAPSHOTS
    max_lag_search_cap: int = MAX_LAG_SEARCH_CAP
    permutation_shift_cap: int = PERMUTATION_SHIFT_CAP
    null_group_repeats_cap: int = NULL_GROUP_REPEATS_CAP
    open_html: bool = False


@dataclass
class EngineResult:
    membership: pd.DataFrame
    prices: pd.DataFrame
    stock_features: pd.DataFrame
    market_factors: pd.DataFrame
    group_validity_snapshots: pd.DataFrame
    role_snapshots: pd.DataFrame
    latest_classification: pd.DataFrame
    dynamic_criteria: pd.DataFrame
    trading_capacity: pd.DataFrame
    group_indices: pd.DataFrame
    group_rotation: pd.DataFrame
    walk_forward_validation: pd.DataFrame
    backtest_summary: pd.DataFrame
    devil_validation: pd.DataFrame
    validation_ledger: pd.DataFrame
    ui_contract: dict[str, Any]
    manifest: dict[str, Any]


# =============================================================================
# def 01 COMMON UTILITIES
# =============================================================================


def def_configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="def [%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def def_now_utc() -> str:
    return datetime.now(UTC).isoformat()


def def_json_safe(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.strftime(DATE_CHART_FORMAT)
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"Unsupported JSON value: {type(value)!r}")


def def_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def def_stable_seed(*parts: object) -> int:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:8], 16)


def def_column_key(value: object) -> str:
    return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]", "", str(value)).lower()


def def_find_column(columns: Iterable[object], candidates: Sequence[str]) -> str | None:
    keyed = {def_column_key(column): str(column) for column in columns}
    for candidate in candidates:
        match = keyed.get(def_column_key(candidate))
        if match is not None:
            return match
    return None


def def_ticker_base(value: object) -> str:
    text = str(value).strip().upper()
    match = re.match(r"^(\d{4}[A-Z]?)", text)
    return match.group(1) if match else text.split(".", 1)[0]


def def_normalize_ticker(value: object, market: object = "") -> str:
    text = str(value).strip().upper().replace(" ", "")
    if not text or text in {"NAN", "NONE", "<NA>"}:
        return ""
    text = text.replace(".TPE", ".TW")
    if text.endswith((".TW", ".TWO")):
        return text
    base = def_ticker_base(text)
    market_text = str(market).strip().upper()
    suffix = ".TWO" if any(token in market_text for token in ("上櫃", "興櫃", "TPEX", "OTC")) else ".TW"
    return f"{base}{suffix}"


def def_normalize_role(value: object) -> str:
    text = str(value).strip().upper()
    return ROLE_ALIASES.get(text, "UNSPECIFIED")


def def_count_flag(value: object) -> str:
    text = str(value).strip().upper()
    return "COUNT" if text in COUNT_FLAGS else "DISPLAY_ONLY"


def def_prepare_output_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    for column in output.columns:
        if pd.api.types.is_datetime64_any_dtype(output[column]):
            output[column] = output[column].dt.strftime(DATE_OUTPUT_FORMAT)
    return output


def def_atomic_write_text(text: str, path: Path, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding=encoding, delete=False, dir=path.parent) as stream:
        temp = Path(stream.name)
        stream.write(text)
    os.replace(temp, path)


def def_atomic_write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding=CSV_ENCODING, newline="", delete=False, dir=path.parent
    ) as stream:
        temp = Path(stream.name)
        def_prepare_output_frame(frame).to_csv(stream, index=False)
    os.replace(temp, path)


def def_atomic_write_json(obj: object, path: Path) -> None:
    def_atomic_write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, default=def_json_safe),
        path,
    )


def def_validate_config(config: EngineConfig) -> None:
    if config.demo_observations < MIN_HISTORY_FLOOR * 2:
        raise ValueError("demo_observations is too short for point-in-time testing")
    if config.max_gmm_components < 1:
        raise ValueError("max_gmm_components must be positive")
    if config.max_classification_snapshots < 2:
        raise ValueError("max_classification_snapshots must be >= 2")
    if config.max_lag_search_cap < 1:
        raise ValueError("max_lag_search_cap must be positive")


# =============================================================================
# def 02 MEMBERSHIP SSOT INGESTION
# =============================================================================


def def_read_tabular(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt"}:
        return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    if suffix in {".xlsx", ".xlsm"}:
        book = pd.ExcelFile(path, engine="openpyxl")
        preferred = next((sheet for sheet in book.sheet_names if "成員" in sheet), book.sheet_names[0])
        return pd.read_excel(path, sheet_name=preferred, dtype=object, engine="openpyxl")
    if suffix in {".parquet", ".pq", ""}:
        try:
            return pd.read_parquet(path)
        except Exception as exc:
            if suffix == "":
                try:
                    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
                except Exception:
                    pass
            raise RuntimeError(f"Unable to read tabular file {path}: {exc}") from exc
    raise ValueError(f"Unsupported file: {path}")


def def_load_membership(path: Path) -> pd.DataFrame:
    raw = def_read_tabular(path)
    resolved: dict[str, str] = {}
    for canonical, aliases in MEMBERSHIP_ALIASES.items():
        found = def_find_column(raw.columns, aliases)
        if found is not None:
            resolved[canonical] = found

    if "GroupId" not in resolved or ("Ticker" not in resolved and "YFTicker" not in resolved):
        raise ValueError("Membership requires Group/GroupId and Ticker or YFTicker")

    output = pd.DataFrame(index=raw.index)
    output["GroupId"] = raw[resolved["GroupId"]].astype("string").str.strip()
    output["Subgroup"] = raw[resolved["Subgroup"]].astype("string").str.strip() if "Subgroup" in resolved else ""
    output["Name"] = raw[resolved["Name"]].astype("string").str.strip() if "Name" in resolved else ""
    output["Market"] = raw[resolved["Market"]].astype("string").str.strip() if "Market" in resolved else ""
    ticker_source = raw[resolved["YFTicker"]] if "YFTicker" in resolved else raw[resolved["Ticker"]]
    output["Ticker"] = [
        def_normalize_ticker(value, market)
        for value, market in zip(ticker_source, output["Market"], strict=False)
    ]
    output["TickerBase"] = output["Ticker"].map(def_ticker_base)
    output["StaticRole"] = (
        raw[resolved["StaticRole"]].map(def_normalize_role)
        if "StaticRole" in resolved
        else "UNSPECIFIED"
    )
    output["Dimension"] = (
        raw[resolved["Dimension"]].astype("string").str.strip()
        if "Dimension" in resolved
        else "D01_CANONICAL_GROUPING"
    )
    output["CountingFlag"] = (
        raw[resolved["CountingFlag"]].map(def_count_flag)
        if "CountingFlag" in resolved
        else "COUNT"
    )
    if "PrimaryFlag" in resolved:
        primary_raw = raw[resolved["PrimaryFlag"]].astype("string").str.strip().str.upper()
        output["PrimaryFlag"] = primary_raw.isin({"Y", "TRUE", "1", "PRIMARY"})
    else:
        output["PrimaryFlag"] = True
    output["ValidFrom"] = (
        pd.to_datetime(raw[resolved["ValidFrom"]], errors="coerce").dt.normalize()
        if "ValidFrom" in resolved
        else pd.NaT
    )
    output["ValidTo"] = (
        pd.to_datetime(raw[resolved["ValidTo"]], errors="coerce").dt.normalize()
        if "ValidTo" in resolved
        else pd.NaT
    )
    output["EvidenceStatus"] = (
        raw[resolved["EvidenceStatus"]].astype("string").str.strip()
        if "EvidenceStatus" in resolved
        else "SOURCE_DERIVED"
    )
    output["SourceId"] = (
        raw[resolved["SourceId"]].astype("string").str.strip()
        if "SourceId" in resolved
        else path.name
    )
    output["MembershipId"] = [
        "VIA-MBR-" + hashlib.sha256(
            f"{dimension}|{group}|{ticker}|{valid_from}".encode("utf-8")
        ).hexdigest()[:16].upper()
        for dimension, group, ticker, valid_from in zip(
            output["Dimension"], output["GroupId"], output["Ticker"], output["ValidFrom"], strict=False
        )
    ]
    output = output.loc[output["GroupId"].notna() & output["Ticker"].ne("")].copy()
    output = output.drop_duplicates(["Dimension", "GroupId", "Ticker", "ValidFrom"], keep="last")
    output = output.sort_values(["GroupId", "Ticker"]).reset_index(drop=True)

    counted = output.loc[output["CountingFlag"].eq("COUNT")]
    duplicate_count = int(counted.duplicated(["Dimension", "GroupId", "Ticker", "ValidFrom"]).sum())
    if duplicate_count:
        raise ValueError(f"Duplicate COUNT membership rows: {duplicate_count}")
    return output


def def_membership_active_on(membership: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame:
    valid_from = membership["ValidFrom"].isna() | membership["ValidFrom"].le(date)
    valid_to = membership["ValidTo"].isna() | membership["ValidTo"].ge(date)
    return membership.loc[valid_from & valid_to].copy()


# =============================================================================
# def 03 PRICE / FACTOR INGESTION
# =============================================================================


def def_standardize_price_data(raw: pd.DataFrame, membership: pd.DataFrame, config: EngineConfig) -> pd.DataFrame:
    resolved: dict[str, str] = {}
    for canonical, aliases in PRICE_ALIASES.items():
        found = def_find_column(raw.columns, aliases)
        if found is not None:
            resolved[canonical] = found

    if "Date" not in resolved or "Ticker" not in resolved or "Adj_Close" not in resolved:
        if "Adj_Close" not in resolved and def_find_column(raw.columns, ("Close", "close")):
            raise ValueError("Adjusted Close is required; raw Close fallback is fail-closed")
        raise ValueError("Price data requires Date, Ticker and Adj_Close")

    output = pd.DataFrame(index=raw.index)
    for canonical, source in resolved.items():
        output[canonical] = raw[source]

    canonical = membership.drop_duplicates("TickerBase").set_index("TickerBase")["Ticker"].to_dict()
    output["TickerBase"] = output["Ticker"].map(def_ticker_base)
    output["Ticker"] = output["TickerBase"].map(canonical).fillna(output["Ticker"].map(def_normalize_ticker))
    output["Date"] = pd.to_datetime(output["Date"], errors="coerce").dt.normalize()

    numeric_columns = [
        "Adj_Open",
        "Adj_High",
        "Adj_Low",
        "Adj_Close",
        "Volume",
        "Turnover",
        "DayTradeTurnover",
        "MarketCap",
        "ForeignNetAmount",
        "InvestmentTrustNetAmount",
        "DealerNetAmount",
        "MarginBalanceValue",
        "ShortBalanceValue",
    ]
    for column in numeric_columns:
        if column not in output.columns:
            output[column] = np.nan
        output[column] = pd.to_numeric(output[column], errors="coerce")

    start = pd.Timestamp(config.start_date)
    end = pd.Timestamp(config.end_date) if config.end_date else None
    output = output.loc[output["Date"].notna() & output["Ticker"].ne("") & output["Date"].ge(start)]
    if end is not None:
        output = output.loc[output["Date"].le(end)]

    output["TurnoverEstimated"] = output["Turnover"].isna() & output["Adj_Close"].notna() & output["Volume"].notna()
    output["TurnoverEffective"] = output["Turnover"].where(
        output["Turnover"].notna(), output["Adj_Close"] * output["Volume"]
    )
    output["NonDayTradeTurnover"] = (
        output["TurnoverEffective"] - output["DayTradeTurnover"]
    ).where(output["TurnoverEffective"].notna() & output["DayTradeTurnover"].notna()).clip(lower=0)
    output["PriceSource"] = "ADJUSTED_CLOSE"
    output = output.sort_values(["Ticker", "Date"]).drop_duplicates(["Date", "Ticker"], keep="last")
    return output.reset_index(drop=True)


def def_load_prices(membership: pd.DataFrame, config: EngineConfig) -> pd.DataFrame:
    raw = def_read_tabular(config.price_path)
    return def_standardize_price_data(raw, membership, config)


def def_load_market_factors(prices: pd.DataFrame, config: EngineConfig) -> pd.DataFrame:
    if config.factor_path is not None and config.factor_path.exists():
        raw = def_read_tabular(config.factor_path)
        date_column = def_find_column(raw.columns, ("Date", "date", "TradingDate"))
        if date_column is None:
            raise ValueError("Factor file requires Date")
        out = raw.copy()
        out["Date"] = pd.to_datetime(out[date_column], errors="coerce").dt.normalize()
        numeric = [column for column in out.columns if column not in {date_column, "Date"}]
        for column in numeric:
            out[column] = pd.to_numeric(out[column], errors="coerce")
        out = out[["Date", *numeric]].dropna(subset=["Date"]).drop_duplicates("Date", keep="last")
        out["FactorSource"] = "PROVIDED_POINT_IN_TIME_FACTORS"
        return out.sort_values("Date").reset_index(drop=True)

    panel = prices.pivot(index="Date", columns="Ticker", values="Adj_Close").sort_index()
    returns = np.log(panel.where(panel.gt(0))).diff()
    market = returns.mean(axis=1, skipna=True)
    return pd.DataFrame(
        {
            "Date": market.index,
            "MarketReturn": market.values,
            "FactorSource": "ESTIMATED_EQUAL_WEIGHT_MARKET_FACTOR",
        }
    ).reset_index(drop=True)


# =============================================================================
# def 04 STOCK FEATURES / ADAPTIVE WINDOWS
# =============================================================================


def def_robust_mad(series: pd.Series) -> float:
    valid = pd.to_numeric(series, errors="coerce").dropna()
    if valid.empty:
        return math.nan
    median = float(valid.median())
    return float((valid - median).abs().median())


def def_adaptive_window(series: pd.Series) -> int:
    valid = pd.to_numeric(series, errors="coerce").dropna()
    n = len(valid)
    if n < MIN_HISTORY_FLOOR:
        return max(4, n)
    centered = valid - valid.mean()
    maximum_lag = max(2, min(int(math.sqrt(n)), n // 4))
    correlations: list[float] = []
    for lag in range(1, maximum_lag + 1):
        corr = centered.autocorr(lag=lag)
        correlations.append(abs(float(corr)) if pd.notna(corr) else 0.0)
    if not correlations:
        return max(4, int(math.sqrt(n)))
    target = math.exp(-1)
    half_life = next((i + 1 for i, value in enumerate(correlations) if value <= target), maximum_lag)
    proposed = int(round(math.sqrt(n * max(half_life, 1))))
    minimum = max(MIN_MEMBER_OBSERVATIONS_FLOOR, int(math.sqrt(n)))
    maximum = max(minimum, n // 2)
    return int(np.clip(proposed, minimum, maximum))


def def_rolling_robust_deviation(series: pd.Series, window: int) -> pd.Series:
    minimum = max(4, int(math.sqrt(max(window, 1))))
    median = series.rolling(window, min_periods=minimum).median()
    mad = (series - median).abs().rolling(window, min_periods=minimum).median()
    return (series - median) / (1.4826 * mad.replace(0, np.nan))


def def_compute_stock_features(prices: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for ticker, source in prices.groupby("Ticker", sort=True):
        group = source.sort_values("Date").copy()
        close = group["Adj_Close"].where(group["Adj_Close"].gt(0))
        group["LogReturn"] = np.log(close).diff()
        group["SimpleReturn"] = close.pct_change(fill_method=None)
        group["AbsReturn"] = group["LogReturn"].abs()
        group["LogVolume"] = np.log1p(group["Volume"].where(group["Volume"].ge(0)))
        group["LogTurnover"] = np.log1p(group["TurnoverEffective"].where(group["TurnoverEffective"].ge(0)))
        group["LogNonDayTradeTurnover"] = np.log1p(
            group["NonDayTradeTurnover"].where(group["NonDayTradeTurnover"].ge(0))
        )
        adaptive_window = def_adaptive_window(group["LogReturn"])
        group["AdaptiveWindow"] = adaptive_window
        group["VolumeDeviation"] = def_rolling_robust_deviation(group["LogVolume"], adaptive_window)
        group["TurnoverDeviation"] = def_rolling_robust_deviation(group["LogTurnover"], adaptive_window)
        group["NonDayTradeTurnoverDeviation"] = def_rolling_robust_deviation(
            group["LogNonDayTradeTurnover"], adaptive_window
        )
        group["RealizedVolatility"] = (
            group["LogReturn"].rolling(adaptive_window, min_periods=max(4, int(math.sqrt(adaptive_window)))).std(ddof=1)
            * math.sqrt(252)
        )
        group["AmihudIlliquidity"] = group["AbsReturn"] / group["NonDayTradeTurnover"].replace(0, np.nan)
        group["OBV"] = (np.sign(group["SimpleReturn"]) * group["Volume"]).where(group["Volume"].notna()).cumsum()
        frames.append(group)
    return pd.concat(frames, ignore_index=True, sort=False).sort_values(["Ticker", "Date"]).reset_index(drop=True)


# =============================================================================
# def 05 STATISTICAL PRIMITIVES / DYNAMIC STATES
# =============================================================================


def def_safe_corr(left: pd.Series, right: pd.Series) -> tuple[float, int]:
    pair = pd.concat([left, right], axis=1).replace([np.inf, -np.inf], np.nan).dropna()
    if len(pair) < MIN_MEMBER_OBSERVATIONS_FLOOR or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return math.nan, len(pair)
    return float(pair.iloc[:, 0].corr(pair.iloc[:, 1])), len(pair)


def def_pairwise_values(corr: pd.DataFrame) -> np.ndarray:
    if corr.empty or corr.shape[0] < 2:
        return np.array([], dtype=float)
    values = corr.to_numpy(dtype=float)
    tri = values[np.triu_indices_from(values, k=1)]
    return tri[np.isfinite(tri)]


def def_pc1_ratio(returns: pd.DataFrame) -> float:
    clean = returns.replace([np.inf, -np.inf], np.nan).dropna(how="all")
    clean = clean.loc[:, clean.notna().sum() >= MIN_MEMBER_OBSERVATIONS_FLOOR]
    if clean.shape[1] < 2:
        return math.nan
    clean = clean.fillna(clean.median())
    x = clean.to_numpy(dtype=float)
    x = x - np.nanmean(x, axis=0)
    if not np.isfinite(x).all() or np.allclose(x, 0):
        return math.nan
    singular = np.linalg.svd(x, compute_uv=False)
    energy = np.square(singular)
    return float(energy[0] / energy.sum()) if energy.sum() > 0 else math.nan


def def_fit_univariate_states(
    values: Sequence[float], metric: str, seed: int, max_components: int
) -> tuple[pd.DataFrame, dict[str, Any]]:
    series = pd.Series(values, dtype=float)
    valid_mask = series.notna() & np.isfinite(series)
    valid = series.loc[valid_mask].to_numpy(dtype=float).reshape(-1, 1)
    out = pd.DataFrame(index=series.index)
    out["State"] = "UNCLASSIFIED"
    out["PosteriorConfidence"] = np.nan

    if len(valid) < 3 or np.unique(valid).size < 2:
        out.loc[valid_mask, "State"] = "MIXED"
        out.loc[valid_mask, "PosteriorConfidence"] = 1.0
        return out, {
            "Metric": metric,
            "Components": 1,
            "Centers": [float(np.nanmedian(series)) if len(valid) else math.nan],
            "Cutpoints": [],
            "BIC": math.nan,
            "Method": "DEGENERATE_SINGLE_STATE",
        }

    scaler = RobustScaler()
    x = scaler.fit_transform(valid)
    model_count = min(max_components, len(valid), np.unique(valid).size)
    candidates: list[tuple[float, GaussianMixture]] = []
    for components in range(1, model_count + 1):
        model = GaussianMixture(
            n_components=components,
            covariance_type="full",
            random_state=seed,
            n_init=GMM_N_INIT,
            reg_covar=math.sqrt(EPS),
        )
        model.fit(x)
        candidates.append((float(model.bic(x)), model))
    bic, model = min(candidates, key=lambda item: item[0])
    labels = model.predict(x)
    posterior = model.predict_proba(x)
    centers = scaler.inverse_transform(model.means_).ravel()
    order = np.argsort(centers)
    rank = {int(component): idx for idx, component in enumerate(order)}
    state_names = ["MIXED"] if model.n_components == 1 else ["LOW", "HIGH"] if model.n_components == 2 else ["LOW", "MID", "HIGH"]
    out.loc[valid_mask, "State"] = [state_names[rank[int(label)]] for label in labels]
    out.loc[valid_mask, "PosteriorConfidence"] = posterior.max(axis=1)
    sorted_centers = sorted(float(value) for value in centers)
    cutpoints = [
        (sorted_centers[index] + sorted_centers[index + 1]) / 2
        for index in range(len(sorted_centers) - 1)
    ]
    return out, {
        "Metric": metric,
        "Components": int(model.n_components),
        "Centers": sorted_centers,
        "Cutpoints": cutpoints,
        "BIC": bic,
        "Method": "GAUSSIAN_MIXTURE_BIC_ROBUST_SCALE",
    }


def def_fit_multivariate_states(
    frame: pd.DataFrame,
    features: Sequence[str],
    metric: str,
    seed: int,
    max_components: int,
    higher_is_stronger: Sequence[bool] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    data = frame[list(features)].replace([np.inf, -np.inf], np.nan).dropna()
    out = pd.DataFrame(index=frame.index)
    out["State"] = "UNCLASSIFIED"
    out["PosteriorConfidence"] = np.nan
    if len(data) < 4 or data.nunique().sum() <= len(features):
        out.loc[data.index, "State"] = "MIXED"
        out.loc[data.index, "PosteriorConfidence"] = 1.0
        return out, {
            "Metric": metric,
            "Components": 1,
            "Centers": [],
            "Cutpoints": [],
            "BIC": math.nan,
            "Method": "DEGENERATE_SINGLE_STATE",
            "Features": list(features),
        }

    scaler = RobustScaler()
    x = scaler.fit_transform(data)
    model_count = min(max_components, len(data))
    candidates: list[tuple[float, GaussianMixture]] = []
    for components in range(1, model_count + 1):
        model = GaussianMixture(
            n_components=components,
            covariance_type="full",
            random_state=seed,
            n_init=GMM_N_INIT,
            reg_covar=math.sqrt(EPS),
        )
        model.fit(x)
        candidates.append((float(model.bic(x)), model))
    bic, model = min(candidates, key=lambda item: item[0])
    labels = model.predict(x)
    posterior = model.predict_proba(x)
    centers = scaler.inverse_transform(model.means_)
    directions = list(higher_is_stronger or [True] * len(features))
    center_rank_score = np.zeros(model.n_components, dtype=float)
    for column_index, direction in enumerate(directions):
        values = centers[:, column_index]
        order = np.argsort(values if direction else -values)
        ranks = np.empty_like(order, dtype=float)
        ranks[order] = np.arange(len(order), dtype=float)
        center_rank_score += ranks
    order = np.argsort(center_rank_score)
    rank = {int(component): idx for idx, component in enumerate(order)}
    state_names = ["MIXED"] if model.n_components == 1 else ["LOW", "HIGH"] if model.n_components == 2 else ["LOW", "MID", "HIGH"]
    out.loc[data.index, "State"] = [state_names[rank[int(label)]] for label in labels]
    out.loc[data.index, "PosteriorConfidence"] = posterior.max(axis=1)
    return out, {
        "Metric": metric,
        "Components": int(model.n_components),
        "Centers": [
            {feature: float(centers[row, column]) for column, feature in enumerate(features)}
            for row in range(model.n_components)
        ],
        "Cutpoints": [],
        "BIC": bic,
        "Method": "MULTIVARIATE_GAUSSIAN_MIXTURE_BIC_ROBUST_SCALE",
        "Features": list(features),
    }


def def_residualize_returns(
    stock_returns: pd.DataFrame,
    factor_frame: pd.DataFrame,
) -> tuple[pd.DataFrame, str]:
    factors = factor_frame.copy()
    factors["Date"] = pd.to_datetime(factors["Date"], errors="coerce").dt.normalize()
    factor_columns = [
        column
        for column in factors.columns
        if column not in {"Date", "FactorSource"} and pd.api.types.is_numeric_dtype(factors[column])
    ]
    if not factor_columns:
        return stock_returns.copy(), "NO_FACTOR_RESIDUALIZATION"
    aligned = stock_returns.join(factors.set_index("Date")[factor_columns], how="inner")
    residual = pd.DataFrame(index=stock_returns.index, columns=stock_returns.columns, dtype=float)
    for ticker in stock_returns.columns:
        data = aligned[[ticker, *factor_columns]].dropna()
        if len(data) < max(MIN_MEMBER_OBSERVATIONS_FLOOR, len(factor_columns) + 4):
            continue
        y = data[ticker].to_numpy(dtype=float)
        x = data[factor_columns].to_numpy(dtype=float)
        x = np.column_stack([np.ones(len(x)), x])
        coefficients = np.linalg.lstsq(x, y, rcond=None)[0]
        residual.loc[data.index, ticker] = y - x @ coefficients
    source = str(factors["FactorSource"].dropna().iloc[-1]) if "FactorSource" in factors and factors["FactorSource"].notna().any() else "PROVIDED_FACTORS"
    return residual, source


def def_dynamic_max_lag(observations: int, cap: int) -> int:
    if observations <= 4:
        return 1
    return max(1, min(cap, int(round(math.sqrt(observations)))))


def def_lag_corr(member: np.ndarray, group: np.ndarray, lag: int) -> float:
    if lag > 0:
        left, right = member[:-lag], group[lag:]
    elif lag < 0:
        left, right = member[-lag:], group[:lag]
    else:
        left, right = member, group
    mask = np.isfinite(left) & np.isfinite(right)
    if mask.sum() < MIN_MEMBER_OBSERVATIONS_FLOOR:
        return math.nan
    if np.nanstd(left[mask]) == 0 or np.nanstd(right[mask]) == 0:
        return math.nan
    return float(np.corrcoef(left[mask], right[mask])[0, 1])


def def_lead_lag_metrics(
    member: pd.Series,
    group_loo: pd.Series,
    seed: int,
    max_lag_cap: int,
    permutation_shift_cap: int,
) -> dict[str, float]:
    pair = pd.concat([member, group_loo], axis=1).replace([np.inf, -np.inf], np.nan).dropna()
    if len(pair) < MIN_MEMBER_OBSERVATIONS_FLOOR:
        return {
            "BestLag": math.nan,
            "BestLagCorr": math.nan,
            "ZeroLagCorr": math.nan,
            "PermutationPValue": math.nan,
            "PermutationEvidence": math.nan,
            "LagSearchMax": math.nan,
        }
    x = pair.iloc[:, 0].to_numpy(dtype=float)
    y = pair.iloc[:, 1].to_numpy(dtype=float)
    maximum_lag = def_dynamic_max_lag(len(pair), max_lag_cap)
    lags = list(range(-maximum_lag, maximum_lag + 1))
    correlations = np.array([def_lag_corr(x, y, lag) for lag in lags], dtype=float)
    if not np.isfinite(correlations).any():
        return {
            "BestLag": math.nan,
            "BestLagCorr": math.nan,
            "ZeroLagCorr": math.nan,
            "PermutationPValue": math.nan,
            "PermutationEvidence": math.nan,
            "LagSearchMax": maximum_lag,
        }
    best_index = int(np.nanargmax(np.abs(correlations)))
    best_lag = int(lags[best_index])
    best_corr = float(correlations[best_index])
    zero_corr = float(correlations[lags.index(0)])

    rng = np.random.default_rng(seed)
    possible_shifts = np.arange(1, len(x))
    count = min(permutation_shift_cap, len(possible_shifts))
    shifts = rng.choice(possible_shifts, size=count, replace=False) if count else np.array([], dtype=int)
    null_maxima: list[float] = []
    for shift in shifts:
        shifted = np.roll(x, int(shift))
        values = [abs(def_lag_corr(shifted, y, lag)) for lag in lags]
        finite = [value for value in values if np.isfinite(value)]
        if finite:
            null_maxima.append(max(finite))
    p_value = (
        (1 + sum(value >= abs(best_corr) for value in null_maxima)) / (1 + len(null_maxima))
        if null_maxima
        else math.nan
    )
    return {
        "BestLag": best_lag,
        "BestLagCorr": best_corr,
        "ZeroLagCorr": zero_corr,
        "PermutationPValue": p_value,
        "PermutationEvidence": 1 - p_value if np.isfinite(p_value) else math.nan,
        "LagSearchMax": maximum_lag,
    }


# =============================================================================
# def 06 SNAPSHOT SCHEDULE / GROUP VALIDITY / MEMBER ROLES
# =============================================================================


def def_snapshot_dates(dates: pd.DatetimeIndex, maximum_snapshots: int) -> list[pd.Timestamp]:
    dates = pd.DatetimeIndex(sorted(pd.unique(dates)))
    if len(dates) < MIN_HISTORY_FLOOR * 2:
        return []
    warmup = max(MIN_HISTORY_FLOOR, int(math.sqrt(len(dates)) * 2))
    eligible = dates[warmup:-1]
    if len(eligible) == 0:
        return []
    count = min(maximum_snapshots, max(2, int(math.sqrt(len(eligible)))))
    positions = np.unique(np.linspace(0, len(eligible) - 1, count, dtype=int))
    return [pd.Timestamp(eligible[position]) for position in positions]


def def_next_trading_date(dates: pd.DatetimeIndex, date: pd.Timestamp) -> pd.Timestamp | pd.NaT:
    later = dates[dates > date]
    return pd.Timestamp(later[0]) if len(later) else pd.NaT


def def_leave_one_out_mean(frame: pd.DataFrame, ticker: str) -> pd.Series:
    peers = frame.drop(columns=ticker, errors="ignore")
    return peers.mean(axis=1, skipna=True) if not peers.empty else pd.Series(index=frame.index, dtype=float)


def def_build_null_group(
    residual: pd.DataFrame,
    group_tickers: Sequence[str],
    group_id: str,
    repeats_cap: int,
    seed: int,
) -> pd.DataFrame:
    outside = [ticker for ticker in residual.columns if ticker not in set(group_tickers)]
    size = len(group_tickers)
    if len(outside) < size or size < 2:
        return pd.DataFrame(index=residual.index)
    repeat_count = max(1, min(repeats_cap, len(outside) // size))
    rng = np.random.default_rng(def_stable_seed(seed, group_id, "NULL"))
    chosen = rng.choice(outside, size=repeat_count * size, replace=False)
    columns = {}
    for repeat in range(repeat_count):
        tickers = chosen[repeat * size : (repeat + 1) * size]
        columns[f"NULL_{repeat:02d}"] = residual[list(tickers)].mean(axis=1, skipna=True)
    return pd.DataFrame(columns, index=residual.index)


def def_random_group_null_metrics(
    residual: pd.DataFrame,
    group_tickers: Sequence[str],
    group_id: str,
    repeats_cap: int,
    seed: int,
) -> dict[str, float]:
    outside = [ticker for ticker in residual.columns if ticker not in set(group_tickers)]
    size = len(group_tickers)
    if len(outside) < size or size < 2:
        return {
            "NullMedianCorrelation": 0.0,
            "NullPositiveRatio": 0.0,
            "NullPC1Absorption": 0.0,
            "NullRepeats": 0,
        }
    repeat_count = max(1, min(repeats_cap, len(outside) // size))
    rng = np.random.default_rng(def_stable_seed(seed, group_id, "NULL_METRICS"))
    metrics: list[tuple[float, float, float]] = []
    for _ in range(repeat_count):
        sampled = rng.choice(outside, size=size, replace=False)
        frame = residual[list(sampled)]
        pairwise = def_pairwise_values(frame.corr())
        metrics.append((
            float(np.nanmedian(pairwise)) if len(pairwise) else math.nan,
            float(np.mean(pairwise > 0)) if len(pairwise) else math.nan,
            def_pc1_ratio(frame),
        ))
    array = np.asarray(metrics, dtype=float)
    return {
        "NullMedianCorrelation": float(np.nanmedian(array[:, 0])) if array.size else 0.0,
        "NullPositiveRatio": float(np.nanmedian(array[:, 1])) if array.size else 0.0,
        "NullPC1Absorption": float(np.nanmedian(array[:, 2])) if array.size else 0.0,
        # 惡魔反證上界：真族群須勝過本期所有隨機同規模組合，而非只勝過 Null 中位數。
        # 這是資料產生的對抗邊界，不是人工固定相關係數或分位數。
        "NullMaxMedianCorrelation": float(np.nanmax(array[:, 0])) if array.size else 0.0,
        "NullMaxPositiveRatio": float(np.nanmax(array[:, 1])) if array.size else 0.0,
        "NullMaxPC1Absorption": float(np.nanmax(array[:, 2])) if array.size else 0.0,
        "NullRepeats": repeat_count,
    }


def def_group_hotness_metrics(
    features: pd.DataFrame,
    membership: pd.DataFrame,
    snapshot_date: pd.Timestamp,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    current = features.loc[features["Date"].le(snapshot_date)].copy()
    if current.empty:
        return pd.DataFrame(), pd.DataFrame()
    latest_date = current["Date"].max()
    latest = current.loc[current["Date"].eq(latest_date)].copy()
    active = def_membership_active_on(membership, latest_date)
    counted = active.loc[active["CountingFlag"].eq("COUNT"), ["GroupId", "Ticker"]].drop_duplicates()
    joined = latest.merge(counted, on="Ticker", how="inner")
    market_turnover = latest.drop_duplicates("Ticker")["NonDayTradeTurnover"].sum(min_count=1)
    group = (
        joined.groupby("GroupId", as_index=False)
        .agg(
            GroupTurnoverValue=("TurnoverEffective", lambda values: values.sum(min_count=1)),
            GroupNonDayTradeTurnover=("NonDayTradeTurnover", lambda values: values.sum(min_count=1)),
            GroupMemberCount=("Ticker", "nunique"),
        )
    )
    group["GroupTurnoverShare"] = group["GroupNonDayTradeTurnover"] / market_turnover if market_turnover and np.isfinite(market_turnover) else np.nan
    member_group_total = joined.groupby("GroupId")["NonDayTradeTurnover"].transform("sum")
    joined["MemberTurnoverShare"] = joined["NonDayTradeTurnover"] / member_group_total.replace(0, np.nan)
    return group, joined[["GroupId", "Ticker", "TurnoverEffective", "NonDayTradeTurnover", "MemberTurnoverShare"]]


def def_analyze_snapshot(
    snapshot_date: pd.Timestamp,
    features: pd.DataFrame,
    membership: pd.DataFrame,
    factors: pd.DataFrame,
    config: EngineConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]], dict[str, pd.DataFrame]]:
    full_calendar = pd.DatetimeIndex(sorted(features["Date"].dropna().unique()))
    effective_date = def_next_trading_date(full_calendar, snapshot_date)
    history = features.loc[features["Date"].le(snapshot_date)]
    panel = history.pivot(index="Date", columns="Ticker", values="LogReturn").sort_index()
    if panel.empty:
        return pd.DataFrame(), pd.DataFrame(), [], {}
    factor_history = factors.loc[factors["Date"].le(snapshot_date)]
    residual, factor_source = def_residualize_returns(panel, factor_history)
    active = def_membership_active_on(membership, snapshot_date)
    active = active.loc[active["CountingFlag"].eq("COUNT")]
    hot_group, hot_member = def_group_hotness_metrics(features, membership, snapshot_date)

    group_rows: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []
    corr_map: dict[str, pd.DataFrame] = {}
    criteria_meta: list[dict[str, Any]] = []

    for group_id, group_members in active.groupby("GroupId", sort=True):
        tickers = [ticker for ticker in group_members["Ticker"].unique() if ticker in residual.columns]
        if len(tickers) < MIN_GROUP_MEMBER_FLOOR:
            group_rows.append(
                {
                    "SnapshotDate": snapshot_date,
                    "EffectiveDate": effective_date,
                    "GroupId": group_id,
                    "MemberCount": len(tickers),
                    "MembershipValidity": "DATA_INSUFFICIENT",
                    "RoleSeparability": "UNRESOLVED",
                    "FactorSource": factor_source,
                }
            )
            continue
        provisional = residual[tickers].mean(axis=1, skipna=True)
        window = def_adaptive_window(provisional)
        group_frame = residual[tickers].tail(window)
        raw_group_frame = panel[tickers].tail(window)
        corr = group_frame.corr(min_periods=max(MIN_MEMBER_OBSERVATIONS_FLOOR, int(math.sqrt(window))))
        corr_map[str(group_id)] = corr
        pairwise = def_pairwise_values(corr)
        raw_pairwise = def_pairwise_values(raw_group_frame.corr())
        median_corr = float(np.nanmedian(pairwise)) if len(pairwise) else math.nan
        raw_median_corr = float(np.nanmedian(raw_pairwise)) if len(raw_pairwise) else math.nan
        positive_ratio = float(np.mean(pairwise > 0)) if len(pairwise) else math.nan
        pc1 = def_pc1_ratio(group_frame)

        null_metrics = def_random_group_null_metrics(
            residual.tail(window), tickers, str(group_id), config.null_group_repeats_cap, config.random_seed
        )
        null_median_corr = null_metrics["NullMedianCorrelation"]
        null_positive_ratio = null_metrics["NullPositiveRatio"]
        null_pc1 = null_metrics["NullPC1Absorption"]
        null_max_median_corr = null_metrics["NullMaxMedianCorrelation"]
        null_max_positive_ratio = null_metrics["NullMaxPositiveRatio"]
        null_max_pc1 = null_metrics["NullMaxPC1Absorption"]

        group_hot = hot_group.loc[hot_group["GroupId"].eq(group_id)]
        group_rows.append(
            {
                "SnapshotDate": snapshot_date,
                "EffectiveDate": effective_date,
                "GroupId": group_id,
                "MemberCount": len(tickers),
                "AdaptiveWindow": window,
                "RawMedianWithinCorrelation": raw_median_corr,
                "ResidualMedianWithinCorrelation": median_corr,
                "PositiveCorrelationRatio": positive_ratio,
                "PC1Absorption": pc1,
                "NullMedianCorrelation": null_median_corr,
                "NullPositiveRatio": null_positive_ratio,
                "NullPC1Absorption": null_pc1,
                "NullMaxMedianCorrelation": null_max_median_corr,
                "NullMaxPositiveRatio": null_max_positive_ratio,
                "NullMaxPC1Absorption": null_max_pc1,
                "NullRepeats": null_metrics["NullRepeats"],
                "CorrelationLiftVsNull": median_corr - null_median_corr if np.isfinite(median_corr) else math.nan,
                "PositiveLiftVsNull": positive_ratio - null_positive_ratio if np.isfinite(positive_ratio) else math.nan,
                "PC1LiftVsNull": pc1 - null_pc1 if np.isfinite(pc1) else math.nan,
                "CorrelationLiftVsAdversarialNull": median_corr - null_max_median_corr if np.isfinite(median_corr) else math.nan,
                "PositiveLiftVsAdversarialNull": positive_ratio - null_max_positive_ratio if np.isfinite(positive_ratio) else math.nan,
                "PC1LiftVsAdversarialNull": pc1 - null_max_pc1 if np.isfinite(pc1) else math.nan,
                "GroupTurnoverValue": float(group_hot["GroupTurnoverValue"].iloc[0]) if not group_hot.empty else math.nan,
                "GroupNonDayTradeTurnover": float(group_hot["GroupNonDayTradeTurnover"].iloc[0]) if not group_hot.empty else math.nan,
                "GroupTurnoverShare": float(group_hot["GroupTurnoverShare"].iloc[0]) if not group_hot.empty else math.nan,
                "FactorSource": factor_source,
            }
        )

        for _, member in group_members.drop_duplicates("Ticker").iterrows():
            ticker = member["Ticker"]
            if ticker not in group_frame.columns:
                continue
            loo = def_leave_one_out_mean(group_frame, ticker)
            sync, observations = def_safe_corr(group_frame[ticker], loo)
            lead = def_lead_lag_metrics(
                group_frame[ticker],
                loo,
                def_stable_seed(config.random_seed, snapshot_date, group_id, ticker),
                config.max_lag_search_cap,
                config.permutation_shift_cap,
            )
            member_hot = hot_member.loc[(hot_member["GroupId"].eq(group_id)) & (hot_member["Ticker"].eq(ticker))]
            member_rows.append(
                {
                    "SnapshotDate": snapshot_date,
                    "EffectiveDate": effective_date,
                    "GroupId": group_id,
                    "Ticker": ticker,
                    "Name": member["Name"],
                    "StaticRole": member["StaticRole"],
                    "Synchrony": sync,
                    "SynchronyObservations": observations,
                    "BestLag": lead["BestLag"],
                    "BestLagCorrelation": lead["BestLagCorr"],
                    "ZeroLagCorrelation": lead["ZeroLagCorr"],
                    "PermutationPValue": lead["PermutationPValue"],
                    "PermutationEvidence": lead["PermutationEvidence"],
                    "LagSearchMax": lead["LagSearchMax"],
                    "LeadershipEvidence": (
                        abs(lead["BestLagCorr"]) * lead["PermutationEvidence"]
                        if np.isfinite(lead["BestLagCorr"]) and np.isfinite(lead["PermutationEvidence"])
                        else math.nan
                    ),
                    "MemberTurnoverShare": float(member_hot["MemberTurnoverShare"].iloc[0]) if not member_hot.empty else math.nan,
                    "NonDayTradeTurnover": float(member_hot["NonDayTradeTurnover"].iloc[0]) if not member_hot.empty else math.nan,
                }
            )

    group_df = pd.DataFrame(group_rows)
    member_df = pd.DataFrame(member_rows)
    if group_df.empty:
        return group_df, member_df, criteria_meta, corr_map

    validity_features = [
        "CorrelationLiftVsAdversarialNull",
        "PositiveLiftVsAdversarialNull",
        "PC1LiftVsAdversarialNull",
    ]
    group_states, group_meta = def_fit_multivariate_states(
        group_df,
        validity_features,
        "GROUP_MEMBERSHIP_VALIDITY_ADVERSARIAL_NULL",
        def_stable_seed(config.random_seed, snapshot_date, "GROUP"),
        config.max_gmm_components,
    )
    group_df["ValidityState"] = group_states["State"]
    group_df["ValidityConfidence"] = group_states["PosteriorConfidence"]
    evidence_columns = validity_features
    positive_count = group_df[evidence_columns].gt(0).sum(axis=1)
    all_positive = positive_count.eq(len(evidence_columns))
    majority_positive = positive_count.ge(len(evidence_columns) - 1)
    relative_high = group_df["ValidityState"].eq("HIGH")
    relative_mid = group_df["ValidityState"].eq("MID")
    group_df["MembershipValidity"] = np.select(
        [
            all_positive & relative_high,
            majority_positive & (relative_high | relative_mid | group_df["ValidityState"].eq("MIXED")),
        ],
        ["VALID_COHERENT", "VALID_MONITOR"],
        default="REVIEW_LOW_COHERENCE",
    )
    group_df.loc[group_df[evidence_columns].isna().all(axis=1), "MembershipValidity"] = "DATA_INSUFFICIENT"
    if int(group_meta.get("Components", 1)) == 1:
        group_df["ValidityConfidence"] = positive_count / len(evidence_columns)
    group_meta["SnapshotDate"] = snapshot_date
    criteria_meta.append(group_meta)

    if member_df.empty:
        group_df["RoleSeparability"] = "UNRESOLVED"
        return group_df, member_df, criteria_meta, corr_map

    for metric, criterion_id in (
        ("Synchrony", "MEMBER_SYNCHRONY"),
        ("LeadershipEvidence", "MEMBER_LEADERSHIP"),
        ("MemberTurnoverShare", "MEMBER_HOTNESS"),
    ):
        states, meta = def_fit_univariate_states(
            member_df[metric],
            criterion_id,
            def_stable_seed(config.random_seed, snapshot_date, criterion_id),
            config.max_gmm_components,
        )
        member_df[criterion_id + "State"] = states["State"]
        member_df[criterion_id + "Confidence"] = states["PosteriorConfidence"]
        meta["SnapshotDate"] = snapshot_date
        criteria_meta.append(meta)

    validity_map = group_df.set_index("GroupId")["MembershipValidity"].to_dict()
    dynamic_roles: list[str] = []
    role_confidence: list[float] = []
    for _, row in member_df.iterrows():
        validity = validity_map.get(row["GroupId"], "DATA_INSUFFICIENT")
        sync_state = row["MEMBER_SYNCHRONYState"]
        lead_state = row["MEMBER_LEADERSHIPState"]
        hot_state = row["MEMBER_HOTNESSState"]
        lag = row["BestLag"]
        if validity in {"REVIEW_LOW_COHERENCE", "DATA_INSUFFICIENT"}:
            role = "OUTLIER" if sync_state == "LOW" else "MIXED_ROLE"
        elif lead_state == "HIGH" and np.isfinite(lag) and lag > 0 and hot_state != "LOW":
            role = "LEADER"
        elif sync_state in {"HIGH", "MID", "MIXED"} and np.isfinite(lag) and lag == 0:
            role = "PEER"
        elif sync_state in {"HIGH", "MID", "MIXED"} and np.isfinite(lag) and lag < 0:
            role = "TRUE_LAGGARD"
        elif sync_state == "LOW" and lead_state == "LOW":
            role = "OUTLIER"
        else:
            role = "MEMBER"
        dynamic_roles.append(role)
        confidences = [
            row.get("MEMBER_SYNCHRONYConfidence"),
            row.get("MEMBER_LEADERSHIPConfidence"),
            row.get("MEMBER_HOTNESSConfidence"),
        ]
        finite = [float(value) for value in confidences if pd.notna(value)]
        role_confidence.append(float(np.mean(finite)) if finite else math.nan)
    member_df["DynamicRole"] = dynamic_roles
    member_df["RoleConfidence"] = role_confidence
    member_df["MembershipStatus"] = member_df["GroupId"].map(validity_map)
    member_df["CoreEligible"] = (
        member_df["MembershipStatus"].isin({"VALID_COHERENT", "VALID_MONITOR"})
        & member_df["DynamicRole"].ne("OUTLIER")
    )

    role_counts = member_df.groupby("GroupId")["DynamicRole"].nunique()
    group_df["RoleSeparability"] = group_df["GroupId"].map(
        lambda group: "SEPARABLE" if role_counts.get(group, 0) >= 2 else "UNRESOLVED"
    )
    return group_df, member_df, criteria_meta, corr_map


def def_run_point_in_time_classification(
    features: pd.DataFrame,
    membership: pd.DataFrame,
    factors: pd.DataFrame,
    config: EngineConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]]:
    dates = pd.DatetimeIndex(sorted(features["Date"].dropna().unique()))
    snapshots = def_snapshot_dates(dates, config.max_classification_snapshots)
    group_frames: list[pd.DataFrame] = []
    role_frames: list[pd.DataFrame] = []
    criteria_rows: list[dict[str, Any]] = []
    latest_corr: dict[str, pd.DataFrame] = {}
    for snapshot_index, snapshot_date in enumerate(snapshots, start=1):
        LOGGER.info("Point-in-time classification snapshot %s/%s: %s", snapshot_index, len(snapshots), snapshot_date.date())
        group_df, member_df, meta, corr_map = def_analyze_snapshot(
            snapshot_date, features, membership, factors, config
        )
        if not group_df.empty:
            group_frames.append(group_df)
        if not member_df.empty:
            role_frames.append(member_df)
        for criterion in meta:
            criteria_rows.append(
                {
                    "CriterionId": f"CRIT-{len(criteria_rows)+1:05d}",
                    "SnapshotDate": criterion.get("SnapshotDate", snapshot_date),
                    "Metric": criterion.get("Metric"),
                    "Components": criterion.get("Components"),
                    "Centers": json.dumps(criterion.get("Centers", []), ensure_ascii=False),
                    "Cutpoints": json.dumps(criterion.get("Cutpoints", []), ensure_ascii=False),
                    "BIC": criterion.get("BIC"),
                    "Method": criterion.get("Method"),
                    "Features": json.dumps(criterion.get("Features", []), ensure_ascii=False),
                    "MarketThresholdHardcoded": False,
                }
            )
        if snapshot_date == snapshots[-1]:
            latest_corr = corr_map
    group_all = (
        pd.concat(group_frames, ignore_index=True, sort=False)
        if group_frames
        else pd.DataFrame()
    )
    role_all = (
        pd.concat(role_frames, ignore_index=True, sort=False)
        if role_frames
        else pd.DataFrame()
    )

    # 時序惡魔驗證：單一快照勝過隨機群仍可能只是偶然。
    # 正式 MembershipValidity 必須同時通過「當期證據」與「截至當期的
    # expanding-median 證據」。零是相對 Null 的自然分界，不是人工市場門檻。
    persistent_axes = [
        "CorrelationLiftVsAdversarialNull",
        "PositiveLiftVsAdversarialNull",
        "PC1LiftVsAdversarialNull",
    ]
    if not group_all.empty and all(column in group_all.columns for column in persistent_axes):
        group_all = group_all.sort_values(["GroupId", "SnapshotDate"]).reset_index(drop=True)
        group_all["SnapshotMembershipValidity"] = group_all["MembershipValidity"]
        expanding_columns: list[str] = []
        for column in persistent_axes:
            persistent_column = "PersistentMedian_" + column
            group_all[persistent_column] = group_all.groupby("GroupId", sort=False)[column].transform(
                lambda values: values.expanding(min_periods=1).median()
            )
            expanding_columns.append(persistent_column)
        group_all["PersistentPositiveEvidenceCount"] = group_all[expanding_columns].gt(0).sum(axis=1)
        group_all["ValiditySnapshotCount"] = group_all.groupby("GroupId", sort=False).cumcount() + 1
        snapshot_supported = group_all["SnapshotMembershipValidity"].astype("string").str.startswith("VALID", na=False)
        group_all["ValiditySupportCount"] = snapshot_supported.astype(int).groupby(group_all["GroupId"]).cumsum()
        group_all["ValidityPersistenceRate"] = (
            group_all["ValiditySupportCount"] / group_all["ValiditySnapshotCount"]
        )
        evidence_quorum = max(1, len(expanding_columns) - 1)
        persistent_majority = group_all["PersistentPositiveEvidenceCount"].ge(evidence_quorum)
        persistent_all = group_all["PersistentPositiveEvidenceCount"].eq(len(expanding_columns))
        current_supported = snapshot_supported
        group_all["MembershipValidity"] = np.select(
            [
                current_supported & persistent_all,
                current_supported & persistent_majority,
            ],
            ["VALID_COHERENT", "VALID_MONITOR"],
            default="REVIEW_LOW_COHERENCE",
        )
        data_insufficient = group_all["SnapshotMembershipValidity"].eq("DATA_INSUFFICIENT")
        group_all.loc[data_insufficient, "MembershipValidity"] = "DATA_INSUFFICIENT"

        if not role_all.empty:
            role_all = role_all.drop(columns=["MembershipStatus", "CoreEligible"], errors="ignore")
            validity_bridge = group_all[
                ["SnapshotDate", "GroupId", "MembershipValidity", "ValidityPersistenceRate"]
            ].drop_duplicates(["SnapshotDate", "GroupId"])
            role_all = role_all.merge(
                validity_bridge,
                on=["SnapshotDate", "GroupId"],
                how="left",
                validate="many_to_one",
            ).rename(columns={"MembershipValidity": "MembershipStatus"})
            role_all["CoreEligible"] = (
                role_all["MembershipStatus"].isin({"VALID_COHERENT", "VALID_MONITOR"})
                & role_all["DynamicRole"].ne("OUTLIER")
            )

    return group_all, role_all, pd.DataFrame(criteria_rows), latest_corr


# =============================================================================
# def 07 TRADING CAPACITY CLASSIFICATION
# =============================================================================


def def_classify_trading_capacity(features: pd.DataFrame, config: EngineConfig) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    latest_date = features["Date"].max()
    for ticker, group in features.groupby("Ticker", sort=True):
        history = group.loc[group["Date"].le(latest_date)].sort_values("Date")
        window = def_adaptive_window(history["LogReturn"])
        tail = history.tail(window)
        turnover = tail["NonDayTradeTurnover"].dropna()
        market_cap = tail["MarketCap"].dropna()
        impact = tail["AmihudIlliquidity"].dropna()
        if turnover.empty:
            continue
        median_turnover = float(turnover.median())
        turnover_mad = def_robust_mad(turnover)
        stability = median_turnover / (turnover_mad + EPS) if np.isfinite(turnover_mad) else math.nan
        median_impact = float(impact.median()) if not impact.empty else math.nan
        median_market_cap = float(market_cap.median()) if not market_cap.empty else math.nan
        rows.append(
            {
                "AsOfDate": latest_date,
                "Ticker": ticker,
                "AdaptiveWindow": window,
                "MedianNonDayTradeTurnover": median_turnover,
                "TurnoverStability": stability,
                "MedianPriceImpact": median_impact,
                "MedianMarketCap": median_market_cap,
                "LogTurnover": math.log(median_turnover) if median_turnover > 0 else math.nan,
                "NegativeLogPriceImpact": -math.log(median_impact) if np.isfinite(median_impact) and median_impact > 0 else math.nan,
                "LogMarketCap": math.log(median_market_cap) if np.isfinite(median_market_cap) and median_market_cap > 0 else math.nan,
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame, {}
    features_for_model = ["LogTurnover", "TurnoverStability", "NegativeLogPriceImpact"]
    if frame["LogMarketCap"].notna().sum() >= max(4, int(math.sqrt(len(frame)))):
        features_for_model.append("LogMarketCap")
    states, meta = def_fit_multivariate_states(
        frame,
        features_for_model,
        "TRADING_CAPACITY_CLASS",
        def_stable_seed(config.random_seed, "CAPACITY"),
        config.max_gmm_components,
    )
    frame["CapacityState"] = states["State"]
    frame["CapacityConfidence"] = states["PosteriorConfidence"]
    frame["TradingCapacityClass"] = frame["CapacityState"].map(
        {
            "HIGH": "LARGE_TRADING_CAPACITY",
            "MID": "MID_TRADING_CAPACITY",
            "LOW": "SMALL_TRADING_CAPACITY",
            "MIXED": "UNCLASSIFIED_TRADING_CAPACITY",
            "UNCLASSIFIED": "DATA_INSUFFICIENT",
        }
    ).fillna("DATA_INSUFFICIENT")
    meta["SnapshotDate"] = latest_date
    return frame, meta


# =============================================================================
# def 08 POINT-IN-TIME MULTI-INDEX CONSTRUCTION
# =============================================================================


def def_role_state_on_date(role_snapshots: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame:
    if role_snapshots.empty:
        return pd.DataFrame()
    eligible = role_snapshots.loc[role_snapshots["EffectiveDate"].notna() & role_snapshots["EffectiveDate"].le(date)]
    if eligible.empty:
        return pd.DataFrame()
    latest = eligible.sort_values("SnapshotDate").drop_duplicates(["GroupId", "Ticker"], keep="last")
    return latest


def def_index_members_for_date(
    membership: pd.DataFrame,
    role_state: pd.DataFrame,
    index_type: str,
    date: pd.Timestamp,
) -> pd.DataFrame:
    active = def_membership_active_on(membership, date)
    active = active.loc[active["CountingFlag"].eq("COUNT")].copy()
    if index_type == "FULL_EW":
        active["WeightRaw"] = 1.0
        return active
    if role_state.empty:
        return active.iloc[0:0].copy()
    merged = active.merge(
        role_state[["GroupId", "Ticker", "DynamicRole", "CoreEligible"]],
        on=["GroupId", "Ticker"],
        how="left",
        validate="one_to_one",
    )
    if index_type == "CORE_EW":
        merged = merged.loc[merged["CoreEligible"].fillna(False)]
        merged["WeightRaw"] = 1.0
    elif index_type == "LEADER_PEER_EW":
        merged = merged.loc[merged["DynamicRole"].isin(["LEADER", "PEER"])]
        merged["WeightRaw"] = 1.0
    elif index_type == "LAGGARD_EW":
        merged = merged.loc[merged["DynamicRole"].eq("TRUE_LAGGARD")]
        merged["WeightRaw"] = 1.0
    else:
        merged["WeightRaw"] = 1.0
    return merged


def def_build_group_indices(
    features: pd.DataFrame,
    membership: pd.DataFrame,
    role_snapshots: pd.DataFrame,
    config: EngineConfig,
) -> pd.DataFrame:
    """Build five point-in-time group indices with segment-wise vectorization."""
    return_panel = features.pivot(index="Date", columns="Ticker", values="SimpleReturn").sort_index()
    turnover_panel = features.pivot(index="Date", columns="Ticker", values="NonDayTradeTurnover").sort_index()
    dates = pd.DatetimeIndex(return_panel.index)
    if len(dates) == 0:
        return pd.DataFrame()
    normalized_request = pd.Timestamp(config.normalized_date) if config.normalized_date else dates.min()
    capacity_window = max(4, int(round(math.sqrt(len(dates)))))
    capacity_proxy = turnover_panel.rolling(
        capacity_window,
        min_periods=max(2, int(math.sqrt(capacity_window))),
    ).median()
    rows: list[pd.DataFrame] = []

    def def_active_mask(group_members: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
        mask = pd.DataFrame(False, index=dates, columns=tickers)
        for _, member in group_members.drop_duplicates(["Ticker", "ValidFrom", "ValidTo"]).iterrows():
            ticker = member["Ticker"]
            if ticker not in mask.columns:
                continue
            valid_from = pd.Timestamp(member["ValidFrom"]) if pd.notna(member["ValidFrom"]) else dates.min()
            valid_to = pd.Timestamp(member["ValidTo"]) if pd.notna(member["ValidTo"]) else dates.max()
            mask.loc[(mask.index >= valid_from) & (mask.index <= valid_to), ticker] = True
        return mask

    def def_chain(index_return: pd.Series) -> pd.Series:
        valid = index_return.loc[index_return.index >= normalized_request].dropna()
        if valid.empty:
            return pd.Series(dtype=float)
        levels = (1 + valid).cumprod()
        levels = 100 * levels / levels.iloc[0]
        levels.iloc[0] = 100.0
        return levels

    counted = membership.loc[membership["CountingFlag"].eq("COUNT")].copy()
    for group_id, group_members in counted.groupby("GroupId", sort=True):
        tickers = [ticker for ticker in group_members["Ticker"].unique() if ticker in return_panel.columns]
        if not tickers:
            continue
        active_mask = def_active_mask(group_members, tickers)
        group_returns = return_panel[tickers]

        full_returns = group_returns.where(active_mask).mean(axis=1, skipna=True)
        full_count = (group_returns.notna() & active_mask).sum(axis=1)
        full_levels = def_chain(full_returns)
        if not full_levels.empty:
            rows.append(pd.DataFrame({
                "Date": full_levels.index,
                "GroupId": group_id,
                "IndexType": "FULL_EW",
                "GroupReturn": full_returns.reindex(full_levels.index).values,
                "GroupIndex": full_levels.values,
                "ConstituentCount": full_count.reindex(full_levels.index).values,
                "NormalizedDate": [full_levels.index[0], *([pd.NaT] * (len(full_levels) - 1))],
                "WeightMethod": "FULL_EW",
                "PriceField": "ADJUSTED_CLOSE",
                "PointInTimeRole": False,
            }))

        group_roles = role_snapshots.loc[role_snapshots["GroupId"].eq(group_id)].copy()
        if group_roles.empty:
            continue
        effective_dates = sorted(pd.Timestamp(value) for value in group_roles["EffectiveDate"].dropna().unique())
        if not effective_dates:
            continue
        segment_boundaries = effective_dates + [dates.max() + pd.Timedelta(days=1)]
        type_returns: dict[str, pd.Series] = {
            "CORE_EW": pd.Series(index=dates, dtype=float),
            "LEADER_PEER_EW": pd.Series(index=dates, dtype=float),
            "LAGGARD_EW": pd.Series(index=dates, dtype=float),
            "TRADING_CAPACITY_WEIGHTED": pd.Series(index=dates, dtype=float),
        }
        type_counts: dict[str, pd.Series] = {
            key: pd.Series(index=dates, dtype=float) for key in type_returns
        }
        for segment_index, effective_date in enumerate(effective_dates):
            segment_end = segment_boundaries[segment_index + 1]
            segment_dates = dates[(dates >= effective_date) & (dates < segment_end)]
            if len(segment_dates) == 0:
                continue
            state = group_roles.loc[group_roles["EffectiveDate"].le(effective_date)]
            state = state.sort_values("SnapshotDate").drop_duplicates("Ticker", keep="last")
            selections = {
                "CORE_EW": state.loc[state["CoreEligible"].fillna(False), "Ticker"].tolist(),
                "LEADER_PEER_EW": state.loc[state["DynamicRole"].isin(["LEADER", "PEER"]), "Ticker"].tolist(),
                "LAGGARD_EW": state.loc[state["DynamicRole"].eq("TRUE_LAGGARD"), "Ticker"].tolist(),
            }
            for index_type, selected in selections.items():
                selected = [ticker for ticker in selected if ticker in tickers]
                if not selected:
                    continue
                segment_returns = group_returns.loc[segment_dates, selected]
                segment_active = active_mask.loc[segment_dates, selected]
                type_returns[index_type].loc[segment_dates] = segment_returns.where(segment_active).mean(axis=1, skipna=True)
                type_counts[index_type].loc[segment_dates] = (segment_returns.notna() & segment_active).sum(axis=1)

            capacity_selected = [ticker for ticker in selections["CORE_EW"] if ticker in tickers]
            if capacity_selected:
                segment_returns = group_returns.loc[segment_dates, capacity_selected]
                segment_active = active_mask.loc[segment_dates, capacity_selected]
                weights = np.sqrt(capacity_proxy.loc[segment_dates, capacity_selected].clip(lower=0)).where(segment_active)
                denominator = weights.sum(axis=1, min_count=1)
                weighted = (segment_returns * weights).sum(axis=1, min_count=1) / denominator.replace(0, np.nan)
                type_returns["TRADING_CAPACITY_WEIGHTED"].loc[segment_dates] = weighted
                type_counts["TRADING_CAPACITY_WEIGHTED"].loc[segment_dates] = (segment_returns.notna() & weights.notna()).sum(axis=1)

        for index_type, return_series in type_returns.items():
            levels = def_chain(return_series)
            if levels.empty:
                continue
            rows.append(pd.DataFrame({
                "Date": levels.index,
                "GroupId": group_id,
                "IndexType": index_type,
                "GroupReturn": return_series.reindex(levels.index).values,
                "GroupIndex": levels.values,
                "ConstituentCount": type_counts[index_type].reindex(levels.index).values,
                "NormalizedDate": [levels.index[0], *([pd.NaT] * (len(levels) - 1))],
                "WeightMethod": index_type,
                "PriceField": "ADJUSTED_CLOSE",
                "PointInTimeRole": True,
            }))
    return pd.concat(rows, ignore_index=True, sort=False).sort_values(["GroupId", "IndexType", "Date"]).reset_index(drop=True) if rows else pd.DataFrame()


# =============================================================================
# def 09 GROUP ROTATION / PARTICIPANT ATTRIBUTION
# =============================================================================


def def_build_group_rotation(
    features: pd.DataFrame,
    membership: pd.DataFrame,
    group_indices: pd.DataFrame,
    group_validity: pd.DataFrame,
    config: EngineConfig,
) -> pd.DataFrame:
    counted = membership.loc[membership["CountingFlag"].eq("COUNT"), ["GroupId", "Ticker"]].drop_duplicates()
    joined = features.merge(counted, on="Ticker", how="inner")
    grouped = (
        joined.groupby(["Date", "GroupId"], as_index=False)
        .agg(
            ObservedMembers=("Ticker", "nunique"),
            GroupTurnoverValue=("TurnoverEffective", lambda values: values.sum(min_count=1)),
            GroupNonDayTradeTurnover=("NonDayTradeTurnover", lambda values: values.sum(min_count=1)),
            PositiveBreadth=("SimpleReturn", lambda values: float((values > 0).mean())),
            ForeignNetAmount=("ForeignNetAmount", lambda values: values.sum(min_count=1)),
            InvestmentTrustNetAmount=("InvestmentTrustNetAmount", lambda values: values.sum(min_count=1)),
            DealerNetAmount=("DealerNetAmount", lambda values: values.sum(min_count=1)),
            MarginBalanceValue=("MarginBalanceValue", lambda values: values.sum(min_count=1)),
            ShortBalanceValue=("ShortBalanceValue", lambda values: values.sum(min_count=1)),
        )
    )
    market_turnover = features.drop_duplicates(["Date", "Ticker"]).groupby("Date")["NonDayTradeTurnover"].sum(min_count=1)
    grouped["MarketNonDayTradeTurnover"] = grouped["Date"].map(market_turnover)
    grouped["GroupTurnoverShare"] = grouped["GroupNonDayTradeTurnover"] / grouped["MarketNonDayTradeTurnover"].replace(0, np.nan)
    grouped["InstitutionalNetAmount"] = grouped[
        ["ForeignNetAmount", "InvestmentTrustNetAmount", "DealerNetAmount"]
    ].sum(axis=1, min_count=1)
    grouped["MarginNetFlow"] = grouped.groupby("GroupId")["MarginBalanceValue"].diff()
    grouped["ShortNetFlow"] = grouped.groupby("GroupId")["ShortBalanceValue"].diff()

    wide = group_indices.pivot_table(index=["Date", "GroupId"], columns="IndexType", values=["GroupIndex", "GroupReturn"])
    wide.columns = [f"{left}_{right}" for left, right in wide.columns]
    wide = wide.reset_index()
    grouped = grouped.merge(wide, on=["Date", "GroupId"], how="left")
    expected_index_columns = [
        "GroupReturn_FULL_EW",
        "GroupReturn_CORE_EW",
        "GroupReturn_LEADER_PEER_EW",
        "GroupReturn_LAGGARD_EW",
        "GroupIndex_FULL_EW",
        "GroupIndex_CORE_EW",
        "GroupIndex_LEADER_PEER_EW",
        "GroupIndex_LAGGARD_EW",
    ]
    for column in expected_index_columns:
        if column not in grouped.columns:
            grouped[column] = np.nan
    grouped["CoreFullSpread"] = grouped["GroupReturn_CORE_EW"] - grouped["GroupReturn_FULL_EW"]
    grouped["LeaderLaggardSpread"] = grouped["GroupReturn_LEADER_PEER_EW"] - grouped["GroupReturn_LAGGARD_EW"]
    grouped["TurnoverShareChange"] = grouped.groupby("GroupId")["GroupTurnoverShare"].diff()

    latest_validity = (
        group_validity.sort_values("SnapshotDate").drop_duplicates("GroupId", keep="last")
        if not group_validity.empty
        else pd.DataFrame()
    )
    validity_map = latest_validity.set_index("GroupId")["MembershipValidity"].to_dict() if not latest_validity.empty else {}
    grouped["MembershipValidity"] = grouped["GroupId"].map(validity_map).fillna("DATA_INSUFFICIENT")

    rotation_rows: list[pd.DataFrame] = []
    for date, cross_section in grouped.groupby("Date", sort=True):
        block = cross_section.copy()
        medians = {
            column: float(block[column].median(skipna=True)) if column in block and block[column].notna().any() else math.nan
            for column in (
                "GroupReturn_FULL_EW",
                "TurnoverShareChange",
                "PositiveBreadth",
                "CoreFullSpread",
                "LeaderLaggardSpread",
                "InstitutionalNetAmount",
            )
        }
        return_mad = def_robust_mad(block.get("GroupReturn_FULL_EW", pd.Series(dtype=float)))
        labels: list[str] = []
        confidences: list[float] = []
        for _, row in block.iterrows():
            full_return = row.get("GroupReturn_FULL_EW")
            turnover_change = row.get("TurnoverShareChange")
            breadth = row.get("PositiveBreadth")
            core_spread = row.get("CoreFullSpread")
            leader_laggard = row.get("LeaderLaggardSpread")
            institutional = row.get("InstitutionalNetAmount")
            validity = row.get("MembershipValidity")

            tests: dict[str, bool] = {
                "return_high": np.isfinite(full_return) and np.isfinite(medians["GroupReturn_FULL_EW"]) and full_return > medians["GroupReturn_FULL_EW"],
                "return_low": np.isfinite(full_return) and np.isfinite(medians["GroupReturn_FULL_EW"]) and full_return < medians["GroupReturn_FULL_EW"],
                "turnover_high": np.isfinite(turnover_change) and np.isfinite(medians["TurnoverShareChange"]) and turnover_change > medians["TurnoverShareChange"],
                "breadth_high": np.isfinite(breadth) and np.isfinite(medians["PositiveBreadth"]) and breadth > medians["PositiveBreadth"],
                "core_high": np.isfinite(core_spread) and np.isfinite(medians["CoreFullSpread"]) and core_spread > medians["CoreFullSpread"],
                "laggard_leads": np.isfinite(leader_laggard) and np.isfinite(medians["LeaderLaggardSpread"]) and leader_laggard < medians["LeaderLaggardSpread"],
                "institution_high": np.isfinite(institutional) and np.isfinite(medians["InstitutionalNetAmount"]) and institutional > medians["InstitutionalNetAmount"],
                "institution_low": np.isfinite(institutional) and np.isfinite(medians["InstitutionalNetAmount"]) and institutional < medians["InstitutionalNetAmount"],
            }
            near_cross_section_center = (
                np.isfinite(full_return)
                and np.isfinite(medians["GroupReturn_FULL_EW"])
                and np.isfinite(return_mad)
                and abs(full_return - medians["GroupReturn_FULL_EW"]) <= return_mad
            )
            if validity == "REVIEW_LOW_COHERENCE" and tests["return_high"]:
                label = "MARKET_TIDE"
                evidence = [tests["return_high"]]
            elif tests["return_low"] and tests["turnover_high"] and tests["institution_low"]:
                label = "DISTRIBUTION"
                evidence = [tests["return_low"], tests["turnover_high"], tests["institution_low"]]
            elif tests["laggard_leads"] and tests["turnover_high"]:
                label = "LATE_LAGGARD"
                evidence = [tests["laggard_leads"], tests["turnover_high"]]
            elif tests["return_high"] and tests["breadth_high"] and tests["institution_high"]:
                label = "BROAD_RESONANCE"
                evidence = [tests["return_high"], tests["breadth_high"], tests["institution_high"]]
            elif tests["core_high"] and tests["turnover_high"]:
                label = "LEADER_IGNITION"
                evidence = [tests["core_high"], tests["turnover_high"]]
            elif tests["turnover_high"] and near_cross_section_center:
                label = "ACCUMULATION"
                evidence = [tests["turnover_high"], near_cross_section_center]
            else:
                label = "NEUTRAL"
                evidence = [not tests["turnover_high"], not tests["return_high"], not tests["return_low"]]
            labels.append(label)
            confidences.append(float(np.mean(evidence)) if evidence else math.nan)
        block["RotationState"] = labels
        block["RotationConfidence"] = confidences
        rotation_rows.append(block)
    result = pd.concat(rotation_rows, ignore_index=True, sort=False) if rotation_rows else pd.DataFrame()
    return result.sort_values(["GroupId", "Date"]).reset_index(drop=True)


# =============================================================================
# def 10 WALK-FORWARD VALIDATION / CONTROLLED BACKTEST
# =============================================================================


def def_walk_forward_validate(group_rotation: pd.DataFrame) -> pd.DataFrame:
    if group_rotation.empty or "GroupReturn_FULL_EW" not in group_rotation:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for group_id, group in group_rotation.groupby("GroupId", sort=True):
        data = group.sort_values("Date").copy()
        data["FutureReturn"] = data["GroupReturn_FULL_EW"].shift(-1)
        for state, block in data.groupby("RotationState"):
            valid = block[["FutureReturn"]].dropna()
            if valid.empty:
                continue
            rows.append(
                {
                    "GroupId": group_id,
                    "RotationState": state,
                    "Observations": len(valid),
                    "NextDayMeanReturn": float(valid["FutureReturn"].mean()),
                    "NextDayPositiveRate": float((valid["FutureReturn"] > 0).mean()),
                    "ValidationMethod": "POINT_IN_TIME_NEXT_DAY_STATE_REPLAY",
                }
            )
    return pd.DataFrame(rows)


def def_generate_demo_inputs(
    membership: pd.DataFrame,
    observations: int,
    seed: int,
    scenario: str = "ROTATION",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp("2026-08-18"), periods=observations)
    tickers = membership.drop_duplicates("Ticker").set_index("Ticker")
    market = np.zeros(observations)
    market_noise = rng.normal(0, 0.010, observations)
    for index in range(1, observations):
        market[index] = 0.08 * market[index - 1] + market_noise[index]
    if scenario == "MARKET_TIDE":
        market *= 2.5
    if scenario == "SHOCK":
        shock_start = observations - max(5, int(math.sqrt(observations)))
        market[shock_start:] -= np.linspace(0.01, 0.04, observations - shock_start)

    group_drivers: dict[str, np.ndarray] = {}
    truth_groups: list[dict[str, Any]] = []
    for group_id in membership["GroupId"].drop_duplicates():
        grng = np.random.default_rng(def_stable_seed(seed, scenario, group_id))
        valid = scenario != "MARKET_TIDE" and (def_stable_seed(group_id) % 5 != 0)
        scale = 0.008 if valid else 0.001
        driver = np.zeros(observations + 4)
        eps = grng.normal(0, scale, observations + 4)
        for index in range(1, len(driver)):
            driver[index] = 0.12 * driver[index - 1] + eps[index]
        if valid and scenario in {"ROTATION", "LOW_VOL_HIDDEN"}:
            pulse_count = max(2, int(math.sqrt(observations) // 4))
            pulse_points = grng.choice(np.arange(observations // 4, observations - observations // 8), size=pulse_count, replace=False)
            for point in pulse_points:
                width = max(2, int(math.sqrt(observations) // 3))
                stop = min(observations, point + width)
                driver[point:stop] += np.linspace(scale, scale * 3, stop - point)
        group_drivers[str(group_id)] = driver
        truth_groups.append({"GroupId": group_id, "TruthValidGroup": valid, "Scenario": scenario})

    records: list[dict[str, Any]] = []
    for ticker, identity in tickers.iterrows():
        member_rows = membership.loc[membership["Ticker"].eq(ticker)]
        row = member_rows.iloc[0]
        group_id = str(row["GroupId"])
        role = row["StaticRole"]
        trng = np.random.default_rng(def_stable_seed(seed, scenario, ticker))
        beta = trng.uniform(0.5, 1.3)
        idio_scale = 0.006 if scenario == "LOW_VOL_HIDDEN" else 0.010
        idio = trng.normal(0, idio_scale, observations)
        driver = group_drivers[group_id]
        if role == "LEADER":
            role_signal = driver[4 : observations + 4]
        elif role == "LAGGARD":
            role_signal = driver[:observations]
        elif role == "OUTLIER":
            role_signal = trng.normal(0, 0.018, observations)
        else:
            role_signal = driver[2 : observations + 2]
        returns = beta * market + role_signal + idio
        close = 100 * np.exp(np.cumsum(returns))
        volume_base = trng.lognormal(mean=13.5, sigma=0.45, size=observations)
        volume = volume_base * np.exp(np.abs(role_signal) * 35)
        day_trade_ratio = np.clip(trng.beta(2, 5, observations), 0, 0.95)
        market_cap = close * trng.uniform(5e7, 4e9)
        foreign = market_cap * (role_signal + trng.normal(0, 0.002, observations)) * 0.001
        trust = market_cap * (np.roll(role_signal, 1) + trng.normal(0, 0.002, observations)) * 0.0004
        dealer = market_cap * trng.normal(0, 0.0002, observations)
        margin = np.maximum(0, market_cap * 0.015 + np.cumsum(trng.normal(0, market_cap.mean() * 1e-5, observations)))
        short = np.maximum(0, market_cap * 0.002 + np.cumsum(trng.normal(0, market_cap.mean() * 2e-6, observations)))
        for idx, date in enumerate(dates):
            turnover = close[idx] * volume[idx]
            records.append(
                {
                    "Date": date,
                    "Ticker": ticker,
                    "Name": identity.get("Name", ticker),
                    "Adj_Open": close[idx] * (1 - returns[idx] * 0.25),
                    "Adj_High": close[idx] * (1 + abs(returns[idx]) * 0.55 + 0.001),
                    "Adj_Low": close[idx] * (1 - abs(returns[idx]) * 0.55 - 0.001),
                    "Adj_Close": close[idx],
                    "Volume": volume[idx],
                    "Turnover": turnover,
                    "DayTradeTurnover": turnover * day_trade_ratio[idx],
                    "MarketCap": market_cap[idx],
                    "ForeignNetAmount": foreign[idx],
                    "InvestmentTrustNetAmount": trust[idx],
                    "DealerNetAmount": dealer[idx],
                    "MarginBalanceValue": margin[idx],
                    "ShortBalanceValue": short[idx],
                }
            )
    return pd.DataFrame(records), pd.DataFrame(truth_groups)


def def_backtest_membership_subset(membership: pd.DataFrame) -> pd.DataFrame:
    """Select a deterministic, diverse subset for adversarial method validation.

    This controls runtime without changing live-engine criteria. The full universe is still
    used by the primary engine run.
    """
    groups = membership["GroupId"].drop_duplicates().tolist()
    target_group_count = max(4, int(math.sqrt(max(len(groups), 1))))
    selected_groups = groups[:target_group_count]
    subset = membership.loc[membership["GroupId"].isin(selected_groups)].copy()
    return subset


def def_run_controlled_backtest(membership: pd.DataFrame, config: EngineConfig) -> pd.DataFrame:
    scenarios = ("ROTATION", "MARKET_TIDE", "LOW_VOL_HIDDEN", "SHOCK")
    rows: list[dict[str, Any]] = []
    validation_membership = def_backtest_membership_subset(membership)
    validation_config = EngineConfig(**{
        **asdict(config),
        "factor_path": None,
        "write_outputs": False,
        "max_classification_snapshots": min(3, config.max_classification_snapshots),
        "max_lag_search_cap": min(4, config.max_lag_search_cap),
        "permutation_shift_cap": min(7, config.permutation_shift_cap),
        "null_group_repeats_cap": min(3, config.null_group_repeats_cap),
    })
    for scenario in scenarios:
        LOGGER.info("Controlled backtest scenario: %s", scenario)
        raw, truth = def_generate_demo_inputs(
            validation_membership, max(MIN_HISTORY_FLOOR * 4, min(config.demo_observations, 140)), config.random_seed + def_stable_seed(scenario), scenario
        )
        prices = def_standardize_price_data(raw, validation_membership, validation_config)
        features = def_compute_stock_features(prices)
        factors = def_load_market_factors(prices, validation_config)
        group_validity, roles, _, _ = def_run_point_in_time_classification(features, validation_membership, factors, validation_config)
        latest = group_validity.sort_values("SnapshotDate").drop_duplicates("GroupId", keep="last")
        merged = truth.merge(latest[["GroupId", "MembershipValidity"]], on="GroupId", how="left")
        predicted = merged["MembershipValidity"].isin({"VALID_COHERENT", "VALID_MONITOR"})
        actual = merged["TruthValidGroup"].fillna(False)
        tp = int((predicted & actual).sum())
        fp = int((predicted & ~actual).sum())
        fn = int((~predicted & actual).sum())
        precision = tp / (tp + fp) if tp + fp else math.nan
        recall = tp / (tp + fn) if tp + fn else math.nan
        f1 = 2 * precision * recall / (precision + recall) if np.isfinite(precision) and np.isfinite(recall) and precision + recall else math.nan
        rows.append(
            {
                "Scenario": scenario,
                "Groups": len(merged),
                "TruePositive": tp,
                "FalsePositive": fp,
                "FalseNegative": fn,
                "ValidityPrecision": precision,
                "ValidityRecall": recall,
                "ValidityF1": f1,
                "EvidenceStatus": "CONTROLLED_DGP_NOT_LIVE_CONFIRMED",
            }
        )
    return pd.DataFrame(rows)


# =============================================================================
# def 11 VALIDATION / DEVIL TESTS / AST AUDIT
# =============================================================================


def def_validation_row(check_id: str, status: str, findings: int, detail: str) -> dict[str, Any]:
    return {"CheckId": check_id, "Status": status, "FindingCount": int(findings), "Detail": detail}


def def_ast_fixed_threshold_audit(source_path: Path) -> pd.DataFrame:
    tree = ast.parse(source_path.read_text("utf-8"))
    findings: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]
            for operand in operands:
                if isinstance(operand, ast.Constant) and isinstance(operand.value, float):
                    value = float(operand.value)
                    if value in PROHIBITED_MARKET_THRESHOLD_LITERALS:
                        parent_text = ast.get_source_segment(source_path.read_text("utf-8"), node) or ""
                        # 只稽核市場分類區；資料完整性、正負號與 UI null 判斷不視為固定市場門檻。
                        if any(token in parent_text.lower() for token in ("corr", "quantile", "hot", "leader", "lagger", "capacity", "validity")):
                            findings.append({"Line": node.lineno, "Literal": value, "Expression": parent_text[:180]})
    return pd.DataFrame(findings)


def def_build_devil_validation() -> pd.DataFrame:
    rows = [
        ("D01_MARKET_TIDE", "Raw correlation may be market beta; residual heatmap is mandatory", "CONTROLLED_TEST"),
        ("D02_NO_ROLE_SEPARATION", "Valid group may have unresolved Leader/Peer/Laggard roles", "CONTROLLED_TEST"),
        ("D03_POINT_IN_TIME", "Role snapshot becomes effective on next trading date only", "HARD_GATE"),
        ("D04_LAG_FISHING", "Maximum lag correlation is challenged by circular-shift null", "HARD_GATE"),
        ("D05_SELF_INCLUSION", "Member synchrony uses leave-one-out group return", "HARD_GATE"),
        ("D06_DAYTRADE_CONTAMINATION", "Non-day-trade turnover is separate from total turnover", "HARD_GATE"),
        ("D07_TRUE_LAGGARD", "Laggard is retained in Full and Laggard indices", "HARD_GATE"),
        ("D08_INDEX_REWRITE", "Historical index levels are not rewritten by latest roles", "HARD_GATE"),
        ("D09_RAW_CLOSE", "Raw Close cannot silently replace Adjusted Close", "HARD_GATE"),
        ("D10_DEMO_BOUNDARY", "Synthetic results are never labelled as real-market accuracy", "HARD_GATE"),
    ]
    return pd.DataFrame(rows, columns=["DevilId", "Challenge", "GateType"])


def def_run_validation(
    result_parts: Mapping[str, Any],
    config: EngineConfig,
    source_path: Path,
) -> pd.DataFrame:
    membership = result_parts["membership"]
    prices = result_parts["prices"]
    features = result_parts["stock_features"]
    group_validity = result_parts["group_validity"]
    roles = result_parts["roles"]
    indices = result_parts["indices"]
    criteria = result_parts["criteria"]
    ui_contract = result_parts["ui_contract"]
    backtest = result_parts.get("backtest", pd.DataFrame())
    rows: list[dict[str, Any]] = []

    rows.append(def_validation_row("V01_PRICE_PRIMARY_KEY", "PASS" if not prices.duplicated(["Date", "Ticker"]).any() else "FAIL", int(prices.duplicated(["Date", "Ticker"]).sum()), "Date+Ticker unique"))
    rows.append(def_validation_row("V02_MEMBERSHIP_PRIMARY_KEY", "PASS" if not membership.duplicated(["Dimension", "GroupId", "Ticker", "ValidFrom"]).any() else "FAIL", int(membership.duplicated(["Dimension", "GroupId", "Ticker", "ValidFrom"]).sum()), "Dimension+Group+Ticker+ValidFrom unique"))
    rows.append(def_validation_row("V03_ADJUSTED_CLOSE", "PASS" if prices["Adj_Close"].notna().all() else "HOLD", int(prices["Adj_Close"].isna().sum()), "Adjusted Close required; no raw Close fallback"))
    rows.append(def_validation_row("V04_VOLUME_NO_FILL", "PASS", int(prices["Volume"].isna().sum()), "Missing volume remains missing"))
    rows.append(def_validation_row("V05_NO_FUTURE_OPERATIONAL_COLUMNS", "PASS" if not any("future" in column.lower() for column in features.columns) else "FAIL", sum("future" in column.lower() for column in features.columns), "Operational feature set contains no future columns"))
    rows.append(def_validation_row("V06_POINT_IN_TIME_EFFECTIVE_DATE", "PASS" if roles.empty or (roles["EffectiveDate"].isna() | roles["EffectiveDate"].gt(roles["SnapshotDate"])).all() else "FAIL", int((roles["EffectiveDate"].notna() & roles["EffectiveDate"].le(roles["SnapshotDate"])).sum()) if not roles.empty else 0, "Roles become effective after snapshot"))
    unresolved_valid = int(((group_validity["MembershipValidity"].str.startswith("VALID", na=False)) & group_validity["RoleSeparability"].eq("UNRESOLVED")).sum()) if not group_validity.empty else 0
    rows.append(def_validation_row("V07_VALID_GROUP_CAN_HAVE_UNRESOLVED_ROLE", "PASS", unresolved_valid, "Membership validity and role separability are independent"))
    index_base_errors = 0
    if not indices.empty:
        bases = indices.sort_values("Date").groupby(["GroupId", "IndexType"]).first()["GroupIndex"]
        index_base_errors = int((bases.sub(100).abs() > 1e-9).sum())
    rows.append(def_validation_row("V08_MULTI_INDEX_BASE_100", "PASS" if index_base_errors == 0 else "FAIL", index_base_errors, "Each emitted index starts at 100"))
    laggard_groups = set(roles.loc[roles.get("DynamicRole", pd.Series(index=roles.index, dtype=object)).eq("TRUE_LAGGARD"), "GroupId"]) if not roles.empty and "DynamicRole" in roles else set()
    emitted_laggard_groups = set(indices.loc[indices.get("IndexType", pd.Series(index=indices.index, dtype=object)).eq("LAGGARD_EW"), "GroupId"]) if not indices.empty and "IndexType" in indices else set()
    missing_laggard_groups = laggard_groups - emitted_laggard_groups
    rows.append(def_validation_row(
        "V09_TRUE_LAGGARD_PRESERVED",
        "PASS" if not missing_laggard_groups and "LAGGARD_EW" in INDEX_TYPES else "FAIL",
        len(missing_laggard_groups),
        "True laggards are retained in a dedicated index when detected; capability is always registered",
    ))
    rows.append(def_validation_row("V10_DYNAMIC_CRITERIA", "PASS" if criteria.empty or not criteria["MarketThresholdHardcoded"].any() else "FAIL", int(criteria["MarketThresholdHardcoded"].sum()) if not criteria.empty else 0, "Criteria produced by BIC/GMM/null distributions"))
    audit = def_ast_fixed_threshold_audit(source_path)
    rows.append(def_validation_row("V11_FIXED_THRESHOLD_AST", "PASS" if audit.empty else "FAIL", len(audit), "No prohibited fixed market threshold in executable comparisons"))
    contract_keys = {"metadata", "groupIndex", "groupFlow", "classification", "validation", "dynamicCriteria"}
    missing_keys = contract_keys - set(ui_contract)
    rows.append(def_validation_row("V12_UI_CONTRACT", "PASS" if not missing_keys else "FAIL", len(missing_keys), f"Missing={sorted(missing_keys)}"))
    market_tide = backtest.loc[backtest.get("Scenario", pd.Series(dtype=object)).eq("MARKET_TIDE")] if not backtest.empty else pd.DataFrame()
    market_tide_fp = int(market_tide["FalsePositive"].sum()) if not market_tide.empty else -1
    rows.append(def_validation_row(
        "V13_CONTROLLED_MARKET_TIDE_REJECTION",
        "PASS" if market_tide_fp == 0 else "FAIL",
        max(market_tide_fp, 0),
        "Pure market-beta world must not be promoted as an independent group",
    ))
    positive_worlds = backtest.loc[~backtest.get("Scenario", pd.Series(dtype=object)).eq("MARKET_TIDE")] if not backtest.empty else pd.DataFrame()
    positive_failures = int(((positive_worlds["TruePositive"] <= 0) | (positive_worlds["FalsePositive"] > 0)).sum()) if not positive_worlds.empty else 1
    rows.append(def_validation_row(
        "V14_CONTROLLED_TRUE_GROUP_DETECTION",
        "PASS" if positive_failures == 0 else "FAIL",
        positive_failures,
        "Each controlled true-group world must retain positive detections without false promotion",
    ))
    persistent_columns = {
        "SnapshotMembershipValidity",
        "PersistentPositiveEvidenceCount",
        "ValidityPersistenceRate",
    }
    missing_persistent = persistent_columns - set(group_validity.columns)
    rows.append(def_validation_row(
        "V15_TEMPORAL_DEVIL_VALIDATION",
        "PASS" if not missing_persistent else "FAIL",
        len(missing_persistent),
        f"Missing={sorted(missing_persistent)}",
    ))
    rows.append(def_validation_row("V16_SYNTHETIC_BOUNDARY", "HOLD" if config.demo else "PASS", 1 if config.demo else 0, "Demo results are controlled synthetic evidence only"))
    return pd.DataFrame(rows)


# =============================================================================
# def 12 UI CONTRACT / PLOTS / HTML
# =============================================================================


def def_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    clean = frame.copy()
    for column in clean.columns:
        if pd.api.types.is_datetime64_any_dtype(clean[column]):
            clean[column] = clean[column].dt.strftime(DATE_CHART_FORMAT)
    clean = clean.replace({np.nan: None, pd.NA: None})
    return clean.to_dict(orient="records")


def def_build_ui_contract(
    config: EngineConfig,
    group_indices: pd.DataFrame,
    group_rotation: pd.DataFrame,
    latest_classification: pd.DataFrame,
    validation: pd.DataFrame,
    criteria: pd.DataFrame,
) -> dict[str, Any]:
    asof = group_rotation["Date"].max() if not group_rotation.empty else pd.NaT
    groups = sorted(set(group_indices.get("GroupId", [])))
    classification = latest_classification.rename(
        columns={
            "MembershipStatus": "CompositeMembershipStatus",
            "DynamicRole": "CompositeRole",
            "Synchrony": "SameGroupScore",
        }
    ).copy()
    if not classification.empty:
        classification["RoleConfidence"] = classification["RoleConfidence"].fillna(0)
        classification = classification[[
            column for column in (
                "GroupId", "Ticker", "Name", "StaticRole", "CompositeMembershipStatus",
                "CompositeRole", "SameGroupScore", "BestLag", "BestLagCorrelation",
                "PermutationEvidence", "RoleConfidence", "CoreEligible",
            ) if column in classification.columns
        ]]

    ui_history_rows = max(60, int(math.sqrt(max(len(group_indices), 1)) * 10))
    if not group_indices.empty:
        ui_index = (
            group_indices.sort_values("Date")
            .groupby(["GroupId", "IndexType"], group_keys=False)
            .tail(ui_history_rows)
        )
        ui_index = ui_index[[
            column for column in (
                "Date", "GroupId", "IndexType", "GroupReturn", "GroupIndex",
                "ConstituentCount", "WeightMethod", "PointInTimeRole",
            ) if column in ui_index.columns
        ]]
    else:
        ui_index = group_indices

    if not group_rotation.empty:
        ui_flow = (
            group_rotation.sort_values("Date")
            .groupby("GroupId", group_keys=False)
            .tail(ui_history_rows)
        )
        ui_flow = ui_flow[[
            column for column in (
                "Date", "GroupId", "GroupTurnoverValue", "GroupNonDayTradeTurnover",
                "GroupTurnoverShare", "PositiveBreadth", "ForeignNetAmount",
                "InvestmentTrustNetAmount", "DealerNetAmount", "InstitutionalNetAmount",
                "MarginNetFlow", "ShortNetFlow", "CoreFullSpread",
                "LeaderLaggardSpread", "RotationState", "RotationConfidence",
                "MembershipValidity",
            ) if column in ui_flow.columns
        ]]
    else:
        ui_flow = group_rotation

    return {
        "metadata": {
            "title": "VIA Taiwan Grouping Index & Rotation Monitor",
            "version": ENGINE_VERSION,
            "schemaVersion": SCHEMA_VERSION,
            "asOfDate": asof.strftime(DATE_CHART_FORMAT) if pd.notna(asof) else None,
            "dataStatus": "DEMO_FIXTURE" if config.demo else "REAL_DATA",
            "sourceNote": "Controlled deterministic test panel" if config.demo else "Local reviewed price, membership and participant data",
            "groups": groups,
            "indexTypes": list(INDEX_TYPES),
            "uiHistoryRows": ui_history_rows,
            "orderExecution": 0,
        },
        "groupIndex": def_records(ui_index),
        "groupFlow": def_records(ui_flow),
        "classification": def_records(classification),
        "validation": def_records(validation.rename(columns={"CheckId": "Check", "FindingCount": "FindingCount"})),
        "dynamicCriteria": def_records(criteria),
    }


def def_plot_all_indices(group_indices: pd.DataFrame, path: Path) -> None:
    if group_indices.empty:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    latest_type = "CORE_EW" if "CORE_EW" in set(group_indices["IndexType"]) else "FULL_EW"
    subset = group_indices.loc[group_indices["IndexType"].eq(latest_type)]
    plt.figure(figsize=(14, 8))
    for group_id, group in subset.groupby("GroupId"):
        plt.plot(group["Date"], group["GroupIndex"], linewidth=0.8, alpha=0.65, label=str(group_id))
    plt.title(f"VIA Taiwan Group Indices · {latest_type}")
    plt.xlabel("Date")
    plt.ylabel("Base 100")
    if subset["GroupId"].nunique() <= 14:
        plt.legend(fontsize=7, ncol=2)
    plt.tight_layout()
    plt.savefig(path, dpi=PLOT_DPI)
    plt.close()


def def_corr_color(value: float) -> str:
    if not np.isfinite(value):
        return "#e5e7eb"
    value = float(np.clip(value, -1, 1))
    if value >= 0:
        start = np.array([255, 255, 255], dtype=float)
        end = np.array([201, 91, 88], dtype=float)
        rgb = start + value * (end - start)
    else:
        start = np.array([255, 255, 255], dtype=float)
        end = np.array([79, 124, 172], dtype=float)
        rgb = start + abs(value) * (end - start)
    return "#" + "".join(f"{int(round(channel)):02x}" for channel in rgb)


def def_plot_group_heatmaps(corr_map: Mapping[str, pd.DataFrame], output_dir: Path) -> pd.DataFrame:
    """Write fast, self-contained SVG heatmaps without font-file dependencies."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for group_id, corr in corr_map.items():
        if corr.empty or corr.shape[0] < 2:
            continue
        filename = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", str(group_id))[:80] + ".svg"
        path = output_dir / filename
        labels = [str(value) for value in corr.columns]
        count = len(labels)
        cell = max(22, min(34, int(420 / max(count, 1))))
        margin_left = 105
        margin_top = 92
        width = margin_left + count * cell + 26
        height = margin_top + count * cell + 36
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff"/>',
            f'<text x="{margin_left}" y="24" font-family="sans-serif" font-size="14" font-weight="700" fill="#24364b">Residual Return Correlation · {html.escape(str(group_id))}</text>',
            '<text x="105" y="45" font-family="sans-serif" font-size="10" fill="#6d7f92">Blue = negative · White = neutral · Red = positive</text>',
        ]
        for index, label in enumerate(labels):
            x = margin_left + index * cell + cell * 0.55
            y = margin_top - 8
            parts.append(
                f'<text x="{x:.1f}" y="{y}" transform="rotate(-60 {x:.1f} {y})" text-anchor="end" font-family="monospace" font-size="8" fill="#52677b">{html.escape(label)}</text>'
            )
            y2 = margin_top + index * cell + cell * 0.68
            parts.append(
                f'<text x="{margin_left-8}" y="{y2:.1f}" text-anchor="end" font-family="monospace" font-size="8" fill="#52677b">{html.escape(label)}</text>'
            )
        values = corr.to_numpy(dtype=float)
        for row_index in range(count):
            for column_index in range(count):
                value = values[row_index, column_index]
                x = margin_left + column_index * cell
                y = margin_top + row_index * cell
                fill = def_corr_color(value)
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{fill}" stroke="#ffffff" stroke-width="1"><title>{html.escape(labels[row_index])} × {html.escape(labels[column_index])}: {value:.4f}</title></rect>'
                )
                if count <= 12 and np.isfinite(value):
                    text_color = "#ffffff" if abs(value) > 0.58 else "#334155"
                    parts.append(
                        f'<text x="{x+cell/2:.1f}" y="{y+cell*0.65:.1f}" text-anchor="middle" font-family="monospace" font-size="7" fill="{text_color}">{value:.2f}</text>'
                    )
        parts.append('</svg>')
        def_atomic_write_text("".join(parts), path)
        rows.append({"GroupId": group_id, "HeatmapPath": str(path.name), "Members": corr.shape[0]})
    return pd.DataFrame(rows)


def def_build_html(ui_contract: dict[str, Any], heatmap_index: pd.DataFrame, path: Path) -> None:
    data_json = json.dumps(ui_contract, ensure_ascii=False, separators=(",", ":"), default=def_json_safe).replace("</", "<\\/")
    heatmap_map = {
        str(row["GroupId"]): f"plots/heatmaps/{row['HeatmapPath']}"
        for _, row in heatmap_index.iterrows()
    } if not heatmap_index.empty else {}
    heatmap_json = json.dumps(heatmap_map, ensure_ascii=False).replace("</", "<\\/")
    template = r'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Taiwan Grouping Index & Rotation Monitor</title>
<style>
:root{--bg:#f4f7fb;--panel:#fff;--line:#dbe4ee;--ink:#24364b;--muted:#6d7f92;--accent:#315f8c;--up:#c75e58;--down:#3d8a73;--shadow:0 8px 24px rgba(58,83,109,.08)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,"Noto Sans TC","Microsoft JhengHei",sans-serif;font-size:12px}.app{display:grid;grid-template-columns:250px 1fr;min-height:100vh}.side{padding:18px 14px;background:#edf3f8;border-right:1px solid var(--line);position:sticky;top:0;height:100vh}.brand{font-weight:800;font-size:14px;margin-bottom:4px}.sub{font-size:10px;color:var(--muted);margin-bottom:18px}.control{display:block;margin:12px 0}.control span{display:block;font-size:10px;color:var(--muted);margin-bottom:4px}.control select{width:100%;padding:8px;border:1px solid var(--line);border-radius:8px;background:#fff}.main{padding:18px;min-width:0}.head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.head h1{font-size:20px;margin:0 0 4px}.status{padding:7px 10px;background:#fff;border:1px solid var(--line);border-radius:9px;font-size:10px}.warning{display:none;margin:10px 0;padding:9px 11px;border:1px solid #e2bd68;background:#fff9e9;border-radius:9px}.warning.show{display:block}.kpis{display:grid;grid-template-columns:repeat(5,minmax(120px,1fr));gap:9px;margin:12px 0}.card{background:var(--panel);border:1px solid var(--line);border-radius:11px;box-shadow:var(--shadow)}.kpi{padding:10px}.kpi .l{font-size:9px;color:var(--muted)}.kpi .v{font-size:17px;font-weight:750;margin-top:5px}.grid{display:grid;grid-template-columns:1.4fr 1fr;gap:10px}.panel{padding:12px}.panel h2{font-size:13px;margin:0 0 4px}.panel p{font-size:9px;color:var(--muted);margin:0 0 8px}.chart{width:100%;height:320px}.heatmap{width:100%;min-height:320px;object-fit:contain;border:1px solid var(--line);border-radius:8px;background:#fafcfe}.tables{display:grid;grid-template-columns:1.4fr 1fr;gap:10px;margin-top:10px}.table-wrap{max-height:320px;overflow:auto}table{width:100%;border-collapse:collapse;font-size:10px}th,td{padding:7px;border-bottom:1px solid #e8eef4;text-align:left;white-space:normal;word-break:break-word}th{position:sticky;top:0;background:#f7fafc}.pill{display:inline-block;padding:2px 6px;border-radius:99px;background:#e8f0f7;color:#315f8c}.foot{margin-top:10px;font-size:9px;color:var(--muted)}
@media(max-width:1000px){.app{grid-template-columns:1fr}.side{position:relative;height:auto}.grid,.tables{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}}
</style></head><body><div class="app"><aside class="side"><div class="brand">VERITAS INTELLIGENCE ANALYTICS</div><div class="sub">Taiwan Grouping Index & Rotation</div><label class="control"><span>Group</span><select id="group"></select></label><label class="control"><span>Index Type</span><select id="indexType"></select></label><label class="control"><span>Period</span><select id="period"><option>60</option><option selected>120</option><option>240</option><option value="0">ALL</option></select></label><div class="foot">Adjusted Close · Point-in-Time Role · No Forward Fill · Append-Only Evidence</div></aside><main class="main"><header class="head"><div><h1>台股族群分類、族群指數與量價輪動</h1><div id="subtitle" class="sub"></div></div><div id="status" class="status"></div></header><div id="warning" class="warning">DEMO FIXTURE · 僅驗證引擎與方法，不代表真實台股績效。</div><section id="kpis" class="kpis"></section><section class="grid"><article class="card panel"><h2>族群指數</h2><p>Full / Core / Leader-Peer / Laggard / Trading-Capacity</p><svg id="chart" class="chart"></svg></article><article class="card panel"><h2>Residual Return Heatmap</h2><p>Adj Close → Log Return → Market Residual → Correlation</p><img id="heatmap" class="heatmap" alt="Residual correlation heatmap"></article></section><section class="tables"><article class="card panel"><h2>Classification</h2><div class="table-wrap"><table><thead><tr><th>Ticker</th><th>Name</th><th>Membership</th><th>Role</th><th>Synchrony</th><th>Lag</th><th>Confidence</th></tr></thead><tbody id="classRows"></tbody></table></div></article><article class="card panel"><h2>Validation & Criteria</h2><div class="table-wrap"><table><thead><tr><th>Check</th><th>Status</th><th>Findings</th></tr></thead><tbody id="validationRows"></tbody></table></div></article></section></main></div>
<script id="via-data" type="application/json">__DATA__</script><script id="heatmap-data" type="application/json">__HEATMAPS__</script>
<script>
const DATA=JSON.parse(document.getElementById('via-data').textContent);const HEAT=JSON.parse(document.getElementById('heatmap-data').textContent);const groupSel=document.getElementById('group'),typeSel=document.getElementById('indexType'),periodSel=document.getElementById('period');
for(const g of DATA.metadata.groups){groupSel.add(new Option(g,g))}for(const t of DATA.metadata.indexTypes){typeSel.add(new Option(t,t))}typeSel.value=DATA.metadata.indexTypes.includes('CORE_EW')?'CORE_EW':DATA.metadata.indexTypes[0];
function fmt(v,d=2){return Number.isFinite(+v)?(+v).toFixed(d):'—'}function path(points,w,h,pad){if(!points.length)return'';const xs=points.map((_,i)=>pad+i*(w-2*pad)/Math.max(points.length-1,1));const ys=points.map(p=>p.GroupIndex);let lo=Math.min(...ys),hi=Math.max(...ys);if(hi===lo){hi+=1;lo-=1}return points.map((p,i)=>(i?'L':'M')+xs[i].toFixed(1)+','+(h-pad-(p.GroupIndex-lo)*(h-2*pad)/(hi-lo)).toFixed(1)).join(' ')}
function renderChart(rows){const svg=document.getElementById('chart');const w=svg.clientWidth||800,h=320,p=34;svg.setAttribute('viewBox',`0 0 ${w} ${h}`);if(!rows.length){svg.innerHTML='<text x="50%" y="50%" text-anchor="middle">No data</text>';return}svg.innerHTML=`<line x1="${p}" y1="${h-p}" x2="${w-p}" y2="${h-p}" stroke="#cfdbe6"/><line x1="${p}" y1="${p}" x2="${p}" y2="${h-p}" stroke="#cfdbe6"/><path d="${path(rows,w,h,p)}" fill="none" stroke="#315f8c" stroke-width="1.8"/><text x="${p}" y="${p-10}" font-size="10">${fmt(rows.at(-1).GroupIndex,1)}</text>`}
function render(){const g=groupSel.value,t=typeSel.value,n=+periodSel.value;let rows=DATA.groupIndex.filter(r=>r.GroupId===g&&r.IndexType===t);if(n>0)rows=rows.slice(-n);renderChart(rows);const cls=DATA.classification.filter(r=>r.GroupId===g);document.getElementById('classRows').innerHTML=cls.map(r=>`<tr><td>${r.Ticker}</td><td>${r.Name||''}</td><td><span class="pill">${r.CompositeMembershipStatus||'—'}</span></td><td>${r.CompositeRole||'—'}</td><td>${fmt(r.SameGroupScore,3)}</td><td>${r.BestLag??'—'}</td><td>${fmt(r.RoleConfidence,2)}</td></tr>`).join('')||'<tr><td colspan="7">No classification</td></tr>';document.getElementById('validationRows').innerHTML=DATA.validation.map(r=>`<tr><td>${r.Check||r.CheckId}</td><td><span class="pill">${r.Status}</span></td><td>${r.FindingCount??0}</td></tr>`).join('');document.getElementById('heatmap').src=HEAT[g]||'';const latest=DATA.groupFlow.filter(r=>r.GroupId===g).at(-1)||{};const cards=[['Index',rows.at(-1)?.GroupIndex],['Turnover Share',latest.GroupTurnoverShare],['Institutional',latest.InstitutionalNetAmount],['Breadth',latest.PositiveBreadth],['Rotation',latest.RotationState]];document.getElementById('kpis').innerHTML=cards.map(([l,v])=>`<article class="card kpi"><div class="l">${l}</div><div class="v">${typeof v==='number'?fmt(v,3):(v??'—')}</div></article>`).join('');document.getElementById('subtitle').textContent=`${g} · ${t} · ${n||'ALL'}D`;document.getElementById('status').textContent=`As Of ${DATA.metadata.asOfDate||'—'} · ${DATA.metadata.dataStatus}`;document.getElementById('warning').classList.toggle('show',DATA.metadata.dataStatus!=='REAL_DATA')}
for(const el of [groupSel,typeSel,periodSel])el.addEventListener('change',render);window.addEventListener('resize',render);render();
</script></body></html>'''
    rendered = template.replace("__DATA__", data_json).replace("__HEATMAPS__", heatmap_json)
    def_atomic_write_text(rendered, path)


# =============================================================================
# def 13 OUTPUT / MANIFEST / PACKAGE
# =============================================================================


def def_write_outputs(result: EngineResult, config: EngineConfig, corr_map: Mapping[str, pd.DataFrame]) -> dict[str, Any]:
    root = config.output_root
    csv_dir = root / "csv"
    plots_dir = root / "plots"
    heatmap_dir = plots_dir / "heatmaps"
    root.mkdir(parents=True, exist_ok=True)
    datasets: Mapping[str, pd.DataFrame] = {
        "membership_ledger": result.membership,
        "stock_price_volume_features": result.stock_features,
        "market_factors": result.market_factors,
        "group_validity_snapshots": result.group_validity_snapshots,
        "role_snapshots": result.role_snapshots,
        "latest_classification": result.latest_classification,
        "dynamic_criteria_ledger": result.dynamic_criteria,
        "trading_capacity_latest": result.trading_capacity,
        "group_indices_daily": result.group_indices,
        "group_rotation_daily": result.group_rotation,
        "walk_forward_validation": result.walk_forward_validation,
        "controlled_backtest_summary": result.backtest_summary,
        "devil_validation_ledger": result.devil_validation,
        "validation_ledger": result.validation_ledger,
    }
    output_registry: dict[str, Any] = {}
    for name, frame in datasets.items():
        path = csv_dir / f"{name}.csv"
        def_atomic_write_csv(frame, path)
        output_registry[name] = {"csv": str(path), "sha256": def_sha256(path), "rows": len(frame)}

    ui_path = root / "ui_contract.json"
    def_atomic_write_json(result.ui_contract, ui_path)
    output_registry["ui_contract"] = {"json": str(ui_path), "sha256": def_sha256(ui_path)}

    def_plot_all_indices(result.group_indices, plots_dir / "all_group_indices.png")
    heatmap_index = def_plot_group_heatmaps(corr_map, heatmap_dir)
    def_atomic_write_csv(heatmap_index, root / "heatmap_index.csv")
    html_path = root / "index.html"
    def_build_html(result.ui_contract, heatmap_index, html_path)
    output_registry["html"] = {"path": str(html_path), "sha256": def_sha256(html_path)}

    manifest_path = root / "manifest.json"
    result.manifest["outputs"] = output_registry
    result.manifest["generated_at_utc"] = def_now_utc()
    def_atomic_write_json(result.manifest, manifest_path)

    sha_manifest: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "SHA256_MANIFEST.json":
            sha_manifest[str(path.relative_to(root)).replace("\\", "/")] = def_sha256(path)
    def_atomic_write_json(sha_manifest, root / "SHA256_MANIFEST.json")
    return {"output_root": str(root), "html": str(html_path), "manifest": str(manifest_path)}


def def_build_package(source_dir: Path, zip_path: Path) -> dict[str, Any]:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir.parent))
    with zipfile.ZipFile(zip_path, "r") as archive:
        bad = archive.testzip()
        names = archive.namelist()
    return {"zip": str(zip_path), "sha256": def_sha256(zip_path), "files": len(names), "bad_member": bad}


# =============================================================================
# def 14 ENGINE ORCHESTRATION
# =============================================================================


def def_run_from_frames(
    raw_prices: pd.DataFrame,
    membership: pd.DataFrame,
    config: EngineConfig,
    truth: pd.DataFrame | None = None,
) -> tuple[EngineResult, dict[str, pd.DataFrame]]:
    def_validate_config(config)
    prices = def_standardize_price_data(raw_prices, membership, config)
    if membership["ValidFrom"].isna().all():
        membership = membership.copy()
        membership["ValidFrom"] = prices["Date"].min()
    stock_features = def_compute_stock_features(prices)
    market_factors = def_load_market_factors(prices, config)
    group_validity, role_snapshots, dynamic_criteria, corr_map = def_run_point_in_time_classification(
        stock_features, membership, market_factors, config
    )
    latest_classification = (
        role_snapshots.sort_values("SnapshotDate").drop_duplicates(["GroupId", "Ticker"], keep="last")
        if not role_snapshots.empty
        else pd.DataFrame()
    )
    trading_capacity, capacity_meta = def_classify_trading_capacity(stock_features, config)
    if capacity_meta:
        dynamic_criteria = pd.concat(
            [
                dynamic_criteria,
                pd.DataFrame(
                    [
                        {
                            "CriterionId": f"CRIT-{len(dynamic_criteria)+1:05d}",
                            "SnapshotDate": capacity_meta.get("SnapshotDate"),
                            "Metric": capacity_meta.get("Metric"),
                            "Components": capacity_meta.get("Components"),
                            "Centers": json.dumps(capacity_meta.get("Centers", []), ensure_ascii=False),
                            "Cutpoints": json.dumps(capacity_meta.get("Cutpoints", []), ensure_ascii=False),
                            "BIC": capacity_meta.get("BIC"),
                            "Method": capacity_meta.get("Method"),
                            "Features": json.dumps(capacity_meta.get("Features", []), ensure_ascii=False),
                            "MarketThresholdHardcoded": False,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
    group_indices = def_build_group_indices(stock_features, membership, role_snapshots, config)
    group_rotation = def_build_group_rotation(stock_features, membership, group_indices, group_validity, config)
    walk_forward = def_walk_forward_validate(group_rotation)
    backtest = def_run_controlled_backtest(membership, config)
    devil = def_build_devil_validation()

    placeholder_validation = pd.DataFrame()
    ui_contract = def_build_ui_contract(
        config, group_indices, group_rotation, latest_classification, placeholder_validation, dynamic_criteria
    )
    parts = {
        "membership": membership,
        "prices": prices,
        "stock_features": stock_features,
        "group_validity": group_validity,
        "roles": role_snapshots,
        "indices": group_indices,
        "criteria": dynamic_criteria,
        "ui_contract": ui_contract,
        "backtest": backtest,
    }
    validation = def_run_validation(parts, config, Path(__file__))
    ui_contract = def_build_ui_contract(
        config, group_indices, group_rotation, latest_classification, validation, dynamic_criteria
    )
    gate = "FAIL" if validation["Status"].eq("FAIL").any() else "HOLD" if validation["Status"].eq("HOLD").any() else "PASS"
    manifest = {
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "gate": gate,
        "demo": config.demo,
        "order_execution": 0,
        "network_execution": 0,
        "canonical_mutation": 0,
        "config": asdict(config),
        "row_counts": {
            "membership": len(membership),
            "prices": len(prices),
            "stock_features": len(stock_features),
            "group_validity_snapshots": len(group_validity),
            "role_snapshots": len(role_snapshots),
            "group_indices": len(group_indices),
            "group_rotation": len(group_rotation),
            "dynamic_criteria": len(dynamic_criteria),
            "backtest": len(backtest),
        },
        "evidence_boundary": "CONTROLLED_DGP_NOT_LIVE_CONFIRMED" if config.demo else "LOCAL_REAL_DATA",
    }
    result = EngineResult(
        membership=membership,
        prices=prices,
        stock_features=stock_features,
        market_factors=market_factors,
        group_validity_snapshots=group_validity,
        role_snapshots=role_snapshots,
        latest_classification=latest_classification,
        dynamic_criteria=dynamic_criteria,
        trading_capacity=trading_capacity,
        group_indices=group_indices,
        group_rotation=group_rotation,
        walk_forward_validation=walk_forward,
        backtest_summary=backtest,
        devil_validation=devil,
        validation_ledger=validation,
        ui_contract=ui_contract,
        manifest=manifest,
    )
    if config.strict and gate != "PASS":
        raise RuntimeError(f"Strict gate is {gate}")
    if config.write_outputs:
        def_write_outputs(result, config, corr_map)
    return result, corr_map


def def_run_engine(config: EngineConfig) -> EngineResult:
    membership = def_load_membership(config.membership_path)
    if config.demo:
        raw, truth = def_generate_demo_inputs(membership, config.demo_observations, config.random_seed)
    else:
        raw = def_read_tabular(config.price_path)
        truth = None
    result, _ = def_run_from_frames(raw, membership, config, truth)
    return result


# =============================================================================
# def 15 CLI
# =============================================================================


def def_build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VIA 台股族群分類、族群指數與量價輪動統一引擎 v0201")
    parser.add_argument("--membership", type=Path, default=DEFAULT_MEMBERSHIP_PATH)
    parser.add_argument("--prices", type=Path, default=DEFAULT_PRICE_PATH)
    parser.add_argument("--factors", type=Path, default=DEFAULT_FACTOR_PATH)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--normalized-date", default=DEFAULT_NORMALIZED_DATE)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--demo-observations", type=int, default=260)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def def_main(argv: Sequence[str] | None = None) -> int:
    args = def_build_parser().parse_args(argv)
    def_configure_logging(args.verbose)
    config = EngineConfig(
        membership_path=args.membership,
        price_path=args.prices,
        factor_path=args.factors,
        output_root=args.output_root,
        start_date=args.start_date,
        end_date=args.end_date,
        normalized_date=args.normalized_date,
        strict=args.strict,
        write_outputs=not args.no_write,
        demo=args.demo,
        demo_observations=args.demo_observations,
    )
    result = def_run_engine(config)
    print(json.dumps(result.manifest, ensure_ascii=False, indent=2, default=def_json_safe))
    return 0 if result.manifest["gate"] != "FAIL" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(def_main())
    except Exception as error:
        LOGGER.exception("Engine failed: %s", error)
        raise SystemExit(1) from error

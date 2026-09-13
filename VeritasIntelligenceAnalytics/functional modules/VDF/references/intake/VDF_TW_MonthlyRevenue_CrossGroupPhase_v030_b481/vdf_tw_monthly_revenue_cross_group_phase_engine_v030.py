from __future__ import annotations

# =============================================================================
# 0. PARAMETERS · 所有可調參數集中於檔案頂部
# =============================================================================

import argparse
import hashlib
import io
import itertools
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import requests

ENGINE_NAME = "VDF_TW_MonthlyRevenue_CrossIndustry_CrossGroup_Phase_Engine"
ENGINE_VERSION = "v030"
ENGINE_BUILD_DATE = "2026-08-27"
ENGINE_CONTRACT = "VDF.MONTHLY_REVENUE.COMPANY.INDUSTRY.GROUP.PHASE/3.0"
ENGINE_MODE_DEFAULT = "PRODUCTION"

DEFAULT_VIA_ROOT = Path(
    os.environ.get(
        "VIA_ROOT",
        r"C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    )
)
DEFAULT_DATABASE_DIR = DEFAULT_VIA_ROOT / "dict" / "VDF" / "DATABASE"
DEFAULT_SSOT_DIR = DEFAULT_VIA_ROOT / "dict" / "VDF" / "_ssot"
DEFAULT_BACKUP_DIR = DEFAULT_VIA_ROOT / "dict" / "VDF" / "_backup"
DEFAULT_REPORT_DIR = DEFAULT_VIA_ROOT / "dict" / "VDF" / "REPORTS"
DEFAULT_OUTPUT_DIR = DEFAULT_DATABASE_DIR

DEFAULT_MONTHLY_REVENUE_INPUT_CANDIDATES = (
    DEFAULT_DATABASE_DIR / "VDF_TW_MonthlyRevenue.parquet",
    DEFAULT_DATABASE_DIR / "VDF_TW_MonthlyRevenue.csv",
    DEFAULT_VIA_ROOT / "functional modules" / "VDF" / "VDF_TW_MonthlyRevenue.parquet",
    DEFAULT_VIA_ROOT / "functional modules" / "VDF" / "VDF_TW_MonthlyRevenue.csv",
)
DEFAULT_COMPANY_MASTER_CANDIDATES = (
    Path(
        r"C:\Users\tonyk\OneDrive\桌面\tw_stock\dict\TickerList\StockTickerListDatabase.csv"
    ),
    DEFAULT_DATABASE_DIR / "VDF_TW_CompanyProfile.parquet",
    DEFAULT_DATABASE_DIR / "VDF_TW_CompanyProfile.csv",
    DEFAULT_SSOT_DIR / "VDF_TW_CompanyMaster_SSOT.parquet",
    DEFAULT_SSOT_DIR / "VDF_TW_CompanyMaster_SSOT.csv",
)
DEFAULT_GROUP_MAP_CANDIDATES = (
    DEFAULT_SSOT_DIR / "VDF_TW_StockGroupClassification_SSOT.parquet",
    DEFAULT_SSOT_DIR / "VDF_TW_StockGroupClassification_SSOT.csv",
    DEFAULT_DATABASE_DIR / "VDF_TW_StockGroupClassification.parquet",
    DEFAULT_DATABASE_DIR / "VDF_TW_StockGroupClassification.csv",
    DEFAULT_VIA_ROOT / "dict" / "TickerList" / "TaiwanStockGroupClassification.csv",
)

MOPS_ENDPOINTS = {
    "TWSE": "https://mopsfin.twse.com.tw/opendata/t187ap05_L.csv",
    "TPEX": "https://mopsfin.twse.com.tw/opendata/t187ap05_O.csv",
}
MOPS_HTTP_TIMEOUT_SECONDS = 45
MOPS_HTTP_RETRY_COUNT = 3
MOPS_HTTP_BACKOFF_SECONDS = 2.0
MOPS_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36 "
    f"{ENGINE_NAME}/{ENGINE_VERSION}"
)

DEFAULT_FETCH_LATEST = True
DEFAULT_INCREMENTAL_UPDATE = True
DEFAULT_REQUIRE_PARQUET = True
DEFAULT_REQUIRE_DUCKDB = True
DEFAULT_WRITE_CSV = True
DEFAULT_WRITE_PARQUET = True
DEFAULT_WRITE_DUCKDB = True
DEFAULT_WRITE_SQLITE_FALLBACK = False
DEFAULT_BACKUP_BEFORE_WRITE = True
DEFAULT_FAIL_ON_DUPLICATE_KEYS = True
DEFAULT_FAIL_ON_INVALID_PERIOD = True
DEFAULT_FAIL_ON_EMPTY_RESULT = True
DEFAULT_ALLOW_INDUSTRY_AS_GROUP_FALLBACK = True
DEFAULT_ALLOW_UNMAPPED_COMPANY = True
DEFAULT_OUTPUT_ENCODING = "utf-8-sig"
DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_START_PERIOD: Optional[str] = None
DEFAULT_END_PERIOD: Optional[str] = None
DEFAULT_LEAD_LAG_MIN_OBSERVATIONS = 18
DEFAULT_LEAD_LAG_MAX_MONTHS = 6
DEFAULT_MAX_PAIRWISE_DIMENSIONS = 80
DEFAULT_REPORTED_CALCULATED_TOLERANCE_PP = 1.00
DEFAULT_COMPANY_GROUP_RELATIVE_GAP_PP = 5.00
DEFAULT_MIN_ROLLING_OBSERVATIONS = 6
DEFAULT_PHASE_HIGH_PERCENTILE = 0.70
DEFAULT_PHASE_LOW_PERCENTILE = 0.30
DEFAULT_PHASE_MIN_POSITIVE_BREADTH = 0.50
DEFAULT_PHASE_STRONG_BREADTH = 0.60
DEFAULT_ROTATION_LEADER_SCORE = 0.80
DEFAULT_ROTATION_IMPROVING_SCORE = 0.60
DEFAULT_ROTATION_PEER_SCORE = 0.40
DEFAULT_ROTATION_WEAKENING_SCORE = 0.20
DEFAULT_UNMAPPED_WARNING_RATIO = 0.05
DEFAULT_COVERAGE_WARNING_RATIO = 0.90
DEFAULT_RECONCILIATION_TOLERANCE = 1e-7

OUTPUT_BASENAMES = {
    "company": "VDF_TW_MonthlyRevenue_Company",
    "company_group_phase": "VDF_TW_MonthlyRevenue_CompanyGroupPhase",
    "industry": "VDF_TW_MonthlyRevenue_Industry",
    "group": "VDF_TW_MonthlyRevenue_Group",
    "industry_group_bridge": "VDF_TW_MonthlyRevenue_IndustryGroupBridge",
    "cross_industry": "VDF_TW_MonthlyRevenue_CrossIndustryMatrix",
    "cross_group": "VDF_TW_MonthlyRevenue_CrossGroupMatrix",
    "lead_lag_industry": "VDF_TW_MonthlyRevenue_LeadLagIndustry",
    "lead_lag_group": "VDF_TW_MonthlyRevenue_LeadLagGroup",
    "phase_transition_industry": "VDF_TW_MonthlyRevenue_PhaseTransitionIndustry",
    "phase_transition_group": "VDF_TW_MonthlyRevenue_PhaseTransitionGroup",
    "quality_report": "VDF_TW_MonthlyRevenue_CrossGroupPhase_QualityReport_v030.json",
    "run_manifest": "VDF_TW_MonthlyRevenue_CrossGroupPhase_RunManifest_v030.json",
    "duckdb": "VDF_TW_MonthlyRevenue.duckdb",
    "sqlite_fallback": "VDF_TW_MonthlyRevenue_fallback.sqlite",
}

PHASE_SCORE_MAP = {
    "LEADING_ACCELERATION": 6,
    "EXPANDING": 5,
    "RECOVERING": 4,
    "MIXED": 3,
    "DECELERATING": 2,
    "CONTRACTING": 1,
    "INSUFFICIENT_HISTORY": 0,
}

COMPANY_COLUMN_ALIASES = {
    "report_date": ["出表日期", "reportdate", "report_date", "發布日期"],
    "period_raw": [
        "資料年月",
        "年月",
        "yearmonth",
        "year_month",
        "yyyymm",
        "period",
        "month",
    ],
    "ticker": [
        "公司代號",
        "公司代碼",
        "股票代號",
        "證券代號",
        "ticker",
        "stockid",
        "stock_id",
        "code",
        "symbol",
    ],
    "name": [
        "公司名稱",
        "公司簡稱",
        "證券名稱",
        "股票名稱",
        "name",
        "companyname",
        "company_name",
    ],
    "market": ["市場別", "市場", "market", "exchange", "上市櫃"],
    "industry_mops": [
        "產業別",
        "產業",
        "industry",
        "industryname",
        "industry_name",
        "sector",
    ],
    "revenue": [
        "營業收入-當月營收",
        "營業收入_當月營收",
        "當月營收",
        "月營收",
        "revenue",
        "monthlyrevenue",
        "monthly_revenue",
    ],
    "last_month_revenue_reported": [
        "營業收入-上月營收",
        "營業收入_上月營收",
        "上月營收",
        "lastmonthrevenue",
        "last_month_revenue",
    ],
    "last_year_month_revenue_reported": [
        "營業收入-去年當月營收",
        "營業收入_去年當月營收",
        "去年當月營收",
        "lastyearsame",
        "last_year_same",
        "last_year_month_revenue",
    ],
    "mom_reported_pct": [
        "營業收入-上月比較增減(%)",
        "營業收入_上月比較增減_%",
        "上月比較增減",
        "月增率",
        "mom",
        "mom_pct",
    ],
    "yoy_reported_pct": [
        "營業收入-去年同月增減(%)",
        "營業收入_去年同月增減_%",
        "去年同月增減",
        "年增率",
        "yoy",
        "yoy_pct",
    ],
    "cum_revenue": [
        "累計營業收入-當月累計營收",
        "累計營業收入_當月累計營收",
        "當月累計營收",
        "累計營收",
        "cumrevenue",
        "cum_revenue",
    ],
    "last_year_cum_revenue": [
        "累計營業收入-去年累計營收",
        "累計營業收入_去年累計營收",
        "去年累計營收",
        "lastyearcumrevenue",
        "last_year_cum_revenue",
    ],
    "cum_yoy_reported_pct": [
        "累計營業收入-前期比較增減(%)",
        "累計營業收入_前期比較增減_%",
        "累計年增率",
        "cumyoy",
        "cum_yoy",
        "cum_yoy_pct",
    ],
    "note": ["備註", "說明", "note", "remark", "remarks"],
    "source": ["資料來源", "source", "source_name"],
    "fetched_at": ["擷取時間", "fetched_at", "ingested_at", "updated_at"],
}

MASTER_COLUMN_ALIASES = {
    "ticker": COMPANY_COLUMN_ALIASES["ticker"],
    "name_master": COMPANY_COLUMN_ALIASES["name"],
    "market_master": COMPANY_COLUMN_ALIASES["market"],
    "industry_master": [
        "產業別",
        "產業",
        "industry",
        "industryname",
        "industry_name",
        "sector",
        "gicsindustry",
        "gics_industry",
    ],
    "sector_master": [
        "大產業",
        "產業大類",
        "sector",
        "sectorname",
        "sector_name",
        "gicssector",
        "gics_sector",
    ],
    "subindustry_master": [
        "次產業",
        "子產業",
        "subindustry",
        "sub_industry",
        "gicssubindustry",
        "gics_sub_industry",
    ],
}

GROUP_COLUMN_ALIASES = {
    "ticker": COMPANY_COLUMN_ALIASES["ticker"],
    "group": [
        "族群",
        "族群名稱",
        "主族群",
        "group",
        "groupname",
        "group_name",
        "theme",
        "theme_name",
    ],
    "groups": [
        "多族群",
        "族群清單",
        "groups",
        "group_list",
        "themes",
        "theme_list",
    ],
    "group_weight": [
        "族群權重",
        "權重",
        "groupweight",
        "group_weight",
        "weight",
    ],
    "is_primary_group": [
        "主要族群",
        "是否主族群",
        "isprimarygroup",
        "is_primary_group",
        "primary",
    ],
    "classification_version": [
        "分類版本",
        "classificationversion",
        "classification_version",
        "version",
    ],
    "classification_source": [
        "分類來源",
        "classificationsource",
        "classification_source",
        "source",
    ],
}

GROUP_SPLIT_PATTERN = re.compile(r"[|,;/、，；]+")
VALID_TW_TICKER_PATTERN = re.compile(r"^\d{4}[A-Z]?$", re.IGNORECASE)
SAFE_SQL_IDENTIFIER_PATTERN = re.compile(r"[^A-Za-z0-9_]+")


# =============================================================================
# 1. CONFIGURATION DATA CLASS
# =============================================================================


@dataclass
class EngineConfig:
    via_root: Path = DEFAULT_VIA_ROOT
    database_dir: Path = DEFAULT_DATABASE_DIR
    ssot_dir: Path = DEFAULT_SSOT_DIR
    backup_dir: Path = DEFAULT_BACKUP_DIR
    report_dir: Path = DEFAULT_REPORT_DIR
    output_dir: Path = DEFAULT_OUTPUT_DIR
    input_path: Optional[Path] = None
    company_master_path: Optional[Path] = None
    group_map_path: Optional[Path] = None
    start_period: Optional[str] = DEFAULT_START_PERIOD
    end_period: Optional[str] = DEFAULT_END_PERIOD
    fetch_latest: bool = DEFAULT_FETCH_LATEST
    incremental_update: bool = DEFAULT_INCREMENTAL_UPDATE
    require_parquet: bool = DEFAULT_REQUIRE_PARQUET
    require_duckdb: bool = DEFAULT_REQUIRE_DUCKDB
    write_csv: bool = DEFAULT_WRITE_CSV
    write_parquet: bool = DEFAULT_WRITE_PARQUET
    write_duckdb: bool = DEFAULT_WRITE_DUCKDB
    write_sqlite_fallback: bool = DEFAULT_WRITE_SQLITE_FALLBACK
    backup_before_write: bool = DEFAULT_BACKUP_BEFORE_WRITE
    fail_on_duplicate_keys: bool = DEFAULT_FAIL_ON_DUPLICATE_KEYS
    fail_on_invalid_period: bool = DEFAULT_FAIL_ON_INVALID_PERIOD
    fail_on_empty_result: bool = DEFAULT_FAIL_ON_EMPTY_RESULT
    allow_industry_as_group_fallback: bool = DEFAULT_ALLOW_INDUSTRY_AS_GROUP_FALLBACK
    allow_unmapped_company: bool = DEFAULT_ALLOW_UNMAPPED_COMPANY
    output_encoding: str = DEFAULT_OUTPUT_ENCODING
    log_level: str = DEFAULT_LOG_LEVEL
    lead_lag_min_observations: int = DEFAULT_LEAD_LAG_MIN_OBSERVATIONS
    lead_lag_max_months: int = DEFAULT_LEAD_LAG_MAX_MONTHS
    max_pairwise_dimensions: int = DEFAULT_MAX_PAIRWISE_DIMENSIONS
    reported_calculated_tolerance_pp: float = DEFAULT_REPORTED_CALCULATED_TOLERANCE_PP
    company_group_relative_gap_pp: float = DEFAULT_COMPANY_GROUP_RELATIVE_GAP_PP
    min_rolling_observations: int = DEFAULT_MIN_ROLLING_OBSERVATIONS
    phase_high_percentile: float = DEFAULT_PHASE_HIGH_PERCENTILE
    phase_low_percentile: float = DEFAULT_PHASE_LOW_PERCENTILE
    phase_min_positive_breadth: float = DEFAULT_PHASE_MIN_POSITIVE_BREADTH
    phase_strong_breadth: float = DEFAULT_PHASE_STRONG_BREADTH
    rotation_leader_score: float = DEFAULT_ROTATION_LEADER_SCORE
    rotation_improving_score: float = DEFAULT_ROTATION_IMPROVING_SCORE
    rotation_peer_score: float = DEFAULT_ROTATION_PEER_SCORE
    rotation_weakening_score: float = DEFAULT_ROTATION_WEAKENING_SCORE
    unmapped_warning_ratio: float = DEFAULT_UNMAPPED_WARNING_RATIO
    coverage_warning_ratio: float = DEFAULT_COVERAGE_WARNING_RATIO
    reconciliation_tolerance: float = DEFAULT_RECONCILIATION_TOLERANCE
    run_id: str = field(default_factory=lambda: def_make_run_id())


# =============================================================================
# 2. BASIC UTILITIES
# =============================================================================


def def_make_run_id() -> str:
    return datetime.now().strftime("RUN_%Y%m%d_%H%M%S")


def def_utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def def_setup_logging(level: str = DEFAULT_LOG_LEVEL) -> logging.Logger:
    logger = logging.getLogger(ENGINE_NAME)
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, str(level).upper(), logging.INFO))
    logger.propagate = False
    return logger


def def_json_default(value: Any) -> Any:
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if np.isnan(value):
            return None
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def def_sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        while True:
            chunk = file_handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def def_safe_sql_identifier(value: str) -> str:
    normalized = SAFE_SQL_IDENTIFIER_PATTERN.sub("_", str(value)).strip("_")
    if not normalized:
        raise ValueError(f"Invalid SQL identifier: {value!r}")
    if normalized[0].isdigit():
        normalized = f"t_{normalized}"
    return normalized


def def_normalize_label(value: Any) -> str:
    text = str(value).strip().lower()
    text = text.replace("％", "%")
    text = re.sub(r"[\s\-_/\\()（）\[\]【】:%]+", "", text)
    return text


def def_first_existing_path(candidates: Iterable[Path]) -> Optional[Path]:
    for candidate in candidates:
        candidate_path = Path(candidate)
        if candidate_path.exists() and candidate_path.is_file():
            return candidate_path
    return None


def def_month_delta(later: pd.Series, earlier: pd.Series) -> pd.Series:
    return (
        (later.dt.year - earlier.dt.year) * 12
        + (later.dt.month - earlier.dt.month)
    )


def def_streak_boolean(values: pd.Series) -> pd.Series:
    result: List[int] = []
    current = 0
    for value in values.fillna(False).astype(bool).tolist():
        if value:
            current += 1
        else:
            current = 0
        result.append(current)
    return pd.Series(result, index=values.index, dtype="int64")


def def_streak_same_value(values: pd.Series) -> pd.Series:
    result: List[int] = []
    previous: Any = object()
    current = 0
    for value in values.tolist():
        if pd.isna(value):
            current = 0
            previous = object()
        elif value == previous:
            current += 1
        else:
            current = 1
            previous = value
        result.append(current)
    return pd.Series(result, index=values.index, dtype="int64")


def def_weighted_average(
    values: pd.Series,
    weights: pd.Series,
    default: float = np.nan,
) -> float:
    valid = values.notna() & weights.notna() & np.isfinite(weights) & (weights > 0)
    if not valid.any():
        return float(default)
    value_array = values.loc[valid].astype(float).to_numpy()
    weight_array = weights.loc[valid].astype(float).to_numpy()
    denominator = weight_array.sum()
    if denominator <= 0:
        return float(default)
    return float(np.dot(value_array, weight_array) / denominator)


def def_safe_median(values: pd.Series, default: float = np.nan) -> float:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if numeric.empty:
        return float(default)
    return float(numeric.median())


def def_atomic_replace(source_temp: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(str(source_temp), str(destination))


def def_atomic_write_json(payload: Mapping[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=str(destination.parent),
        suffix=".tmp",
    ) as temp_file:
        json.dump(
            payload,
            temp_file,
            ensure_ascii=False,
            indent=2,
            default=def_json_default,
        )
        temp_path = Path(temp_file.name)
    def_atomic_replace(temp_path, destination)


def def_atomic_write_csv(
    dataframe: pd.DataFrame,
    destination: Path,
    encoding: str = DEFAULT_OUTPUT_ENCODING,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding=encoding,
        newline="",
        delete=False,
        dir=str(destination.parent),
        suffix=".tmp",
    ) as temp_file:
        dataframe.to_csv(temp_file, index=False)
        temp_path = Path(temp_file.name)
    def_atomic_replace(temp_path, destination)


def def_atomic_write_parquet(dataframe: pd.DataFrame, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.parent / f".{destination.name}.{os.getpid()}.tmp"
    try:
        dataframe.to_parquet(temp_path, index=False)
        def_atomic_replace(temp_path, destination)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def def_detect_capabilities() -> Dict[str, Any]:
    capabilities: Dict[str, Any] = {}
    for module_name in ("pyarrow", "fastparquet", "duckdb", "polars"):
        try:
            module = __import__(module_name)
            capabilities[module_name] = {
                "available": True,
                "version": getattr(module, "__version__", "unknown"),
            }
        except Exception as exc:
            capabilities[module_name] = {
                "available": False,
                "error": str(exc),
            }
    capabilities["parquet_available"] = bool(
        capabilities["pyarrow"]["available"]
        or capabilities["fastparquet"]["available"]
    )
    capabilities["duckdb_available"] = bool(capabilities["duckdb"]["available"])
    return capabilities


# =============================================================================
# 3. FILE READING AND COLUMN NORMALIZATION
# =============================================================================


def def_read_csv_with_encoding_fallback(path: Path) -> pd.DataFrame:
    errors: List[str] = []
    for encoding in ("utf-8-sig", "utf-8", "cp950", "big5"):
        try:
            return pd.read_csv(path, dtype=str, encoding=encoding)
        except Exception as exc:
            errors.append(f"{encoding}: {exc}")
    raise RuntimeError(
        f"Unable to read CSV {path}. Encoding attempts: {' | '.join(errors)}"
    )


def def_read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix in (".csv", ".txt"):
        return def_read_csv_with_encoding_fallback(path)
    if suffix in (".json", ".jsonl"):
        try:
            return pd.read_json(path)
        except ValueError:
            return pd.read_json(path, lines=True)
    raise ValueError(f"Unsupported input format: {path}")


def def_rename_by_aliases(
    dataframe: pd.DataFrame,
    aliases: Mapping[str, Sequence[str]],
) -> pd.DataFrame:
    result = dataframe.copy()
    normalized_to_original: Dict[str, List[str]] = {}
    for column in result.columns:
        normalized_to_original.setdefault(def_normalize_label(column), []).append(column)

    for canonical, candidates in aliases.items():
        candidate_labels = [canonical, *candidates]
        matched_columns: List[str] = []
        for candidate in candidate_labels:
            normalized = def_normalize_label(candidate)
            matched_columns.extend(normalized_to_original.get(normalized, []))
        matched_columns = list(dict.fromkeys(matched_columns))
        if not matched_columns:
            continue
        if canonical not in result.columns:
            result[canonical] = result[matched_columns[0]]
        for extra_column in matched_columns:
            if extra_column == canonical:
                continue
            result[canonical] = result[canonical].combine_first(result[extra_column])
    return result


def def_parse_numeric_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    text = series.astype("string").str.strip()
    text = text.str.replace(",", "", regex=False)
    text = text.str.replace("％", "", regex=False)
    text = text.str.replace("%", "", regex=False)
    text = text.str.replace("−", "-", regex=False)
    text = text.str.replace("—", "-", regex=False)
    text = text.str.replace("–", "-", regex=False)
    text = text.replace(
        {
            "": pd.NA,
            "-": pd.NA,
            "--": pd.NA,
            "---": pd.NA,
            "nan": pd.NA,
            "None": pd.NA,
            "N/A": pd.NA,
            "NA": pd.NA,
            "不適用": pd.NA,
            "無": pd.NA,
        }
    )
    negative_parentheses = text.str.match(r"^\(.*\)$", na=False)
    text = text.str.replace(r"[()]", "", regex=True)
    numeric = pd.to_numeric(text, errors="coerce")
    numeric.loc[negative_parentheses] = -numeric.loc[negative_parentheses].abs()
    return numeric


def def_parse_period_value(value: Any) -> pd.Timestamp:
    if value is None or pd.isna(value):
        return pd.NaT
    if isinstance(value, pd.Timestamp):
        return value.to_period("M").to_timestamp()
    if isinstance(value, datetime):
        return pd.Timestamp(value).to_period("M").to_timestamp()

    text = str(value).strip()
    if not text:
        return pd.NaT
    digits = re.sub(r"\D", "", text)

    year: Optional[int] = None
    month: Optional[int] = None
    if len(digits) == 5:
        roc_year = int(digits[:3])
        year = roc_year + 1911
        month = int(digits[3:5])
    elif len(digits) == 6:
        first_four = int(digits[:4])
        if first_four >= 1911:
            year = first_four
            month = int(digits[4:6])
        else:
            roc_year = int(digits[:3])
            year = roc_year + 1911
            month = int(digits[3:5])
    elif len(digits) == 8:
        year = int(digits[:4])
        month = int(digits[4:6])

    if year is not None and month is not None and 1 <= month <= 12:
        try:
            return pd.Timestamp(year=year, month=month, day=1)
        except ValueError:
            return pd.NaT

    try:
        parsed = pd.to_datetime(text, errors="coerce")
        if pd.isna(parsed):
            return pd.NaT
        return pd.Timestamp(parsed).to_period("M").to_timestamp()
    except Exception:
        return pd.NaT


def def_normalize_ticker(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip().upper()
    text = re.sub(r"\.(TW|TWO)$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", "", text)
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def def_normalize_market(value: Any, default_market: Optional[str] = None) -> str:
    text = "" if value is None or pd.isna(value) else str(value).strip().upper()
    mapping = {
        "上市": "TWSE",
        "上市公司": "TWSE",
        "L": "TWSE",
        "TWSE": "TWSE",
        "TSE": "TWSE",
        ".TW": "TWSE",
        "上櫃": "TPEX",
        "上櫃公司": "TPEX",
        "OTC": "TPEX",
        "O": "TPEX",
        "TPEX": "TPEX",
        ".TWO": "TPEX",
        "興櫃": "EMERGING",
        "P": "PUBLIC",
        "PUBLIC": "PUBLIC",
    }
    return mapping.get(text, default_market or text or "UNKNOWN")


def def_filter_period_range(
    dataframe: pd.DataFrame,
    start_period: Optional[str],
    end_period: Optional[str],
) -> pd.DataFrame:
    result = dataframe.copy()
    if start_period:
        start = def_parse_period_value(start_period)
        if pd.isna(start):
            raise ValueError(f"Invalid start_period: {start_period}")
        result = result.loc[result["period"] >= start]
    if end_period:
        end = def_parse_period_value(end_period)
        if pd.isna(end):
            raise ValueError(f"Invalid end_period: {end_period}")
        result = result.loc[result["period"] <= end]
    return result.reset_index(drop=True)


# =============================================================================
# 4. MOPS FETCHER AND INCREMENTAL CANONICAL MERGE
# =============================================================================


def def_decode_csv_bytes(content: bytes) -> pd.DataFrame:
    errors: List[str] = []
    for encoding in ("utf-8-sig", "utf-8", "cp950", "big5"):
        try:
            decoded = content.decode(encoding)
            return pd.read_csv(io.StringIO(decoded), dtype=str)
        except Exception as exc:
            errors.append(f"{encoding}: {exc}")
    raise RuntimeError(f"Unable to decode MOPS CSV: {' | '.join(errors)}")


def def_fetch_mops_endpoint(
    market: str,
    url: str,
    logger: logging.Logger,
) -> pd.DataFrame:
    last_error: Optional[Exception] = None
    headers = {"User-Agent": MOPS_USER_AGENT, "Accept": "text/csv,*/*;q=0.8"}
    for attempt in range(1, MOPS_HTTP_RETRY_COUNT + 1):
        try:
            logger.info("Fetch MOPS %s · attempt %s/%s", market, attempt, MOPS_HTTP_RETRY_COUNT)
            response = requests.get(
                url,
                headers=headers,
                timeout=MOPS_HTTP_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            if not response.content:
                raise RuntimeError(f"MOPS {market} returned empty content")
            dataframe = def_decode_csv_bytes(response.content)
            dataframe["market"] = market
            dataframe["source"] = f"MOPS_{market}"
            dataframe["fetched_at"] = def_utc_now_iso()
            return dataframe
        except Exception as exc:
            last_error = exc
            logger.warning("MOPS %s fetch failed: %s", market, exc)
            if attempt < MOPS_HTTP_RETRY_COUNT:
                time.sleep(MOPS_HTTP_BACKOFF_SECONDS * attempt)
    raise RuntimeError(f"MOPS {market} fetch failed after retries: {last_error}")


def def_fetch_latest_mops(logger: logging.Logger) -> Tuple[pd.DataFrame, List[str]]:
    frames: List[pd.DataFrame] = []
    warnings: List[str] = []
    for market, url in MOPS_ENDPOINTS.items():
        try:
            frames.append(def_fetch_mops_endpoint(market, url, logger))
        except Exception as exc:
            warnings.append(f"{market}: {exc}")
    if not frames:
        return pd.DataFrame(), warnings
    return pd.concat(frames, ignore_index=True, sort=False), warnings


def def_normalize_monthly_revenue(
    dataframe: pd.DataFrame,
    default_market: Optional[str] = None,
    source_priority: int = 0,
) -> pd.DataFrame:
    if dataframe.empty:
        return pd.DataFrame()

    result = def_rename_by_aliases(dataframe, COMPANY_COLUMN_ALIASES)
    required_columns = ("period_raw", "ticker", "revenue")
    missing = [column for column in required_columns if column not in result.columns]
    if missing:
        raise ValueError(f"Monthly revenue input missing required columns: {missing}")

    for column in (
        "name",
        "market",
        "industry_mops",
        "last_month_revenue_reported",
        "last_year_month_revenue_reported",
        "mom_reported_pct",
        "yoy_reported_pct",
        "cum_revenue",
        "last_year_cum_revenue",
        "cum_yoy_reported_pct",
        "note",
        "source",
        "fetched_at",
        "report_date",
    ):
        if column not in result.columns:
            result[column] = pd.NA

    result["ticker"] = result["ticker"].map(def_normalize_ticker)
    result["name"] = result["name"].astype("string").str.strip()
    result["market"] = result["market"].map(
        lambda value: def_normalize_market(value, default_market)
    )
    result["industry_mops"] = (
        result["industry_mops"].astype("string").str.strip().replace("", pd.NA)
    )
    result["period"] = result["period_raw"].map(def_parse_period_value)
    result["yyyymm"] = result["period"].dt.strftime("%Y%m")

    numeric_columns = (
        "revenue",
        "last_month_revenue_reported",
        "last_year_month_revenue_reported",
        "mom_reported_pct",
        "yoy_reported_pct",
        "cum_revenue",
        "last_year_cum_revenue",
        "cum_yoy_reported_pct",
    )
    for column in numeric_columns:
        result[column] = def_parse_numeric_series(result[column])

    result["source"] = (
        result["source"].astype("string").str.strip().replace("", pd.NA)
    ).fillna("VDF_EXISTING_CANONICAL")
    result["fetched_at"] = (
        result["fetched_at"].astype("string").str.strip().replace("", pd.NA)
    ).fillna(def_utc_now_iso())
    result["source_priority"] = int(source_priority)
    result["ticker_valid"] = result["ticker"].str.match(VALID_TW_TICKER_PATTERN)
    result["period_valid"] = result["period"].notna()
    result["revenue_valid"] = result["revenue"].notna()
    result["yf_ticker"] = np.select(
        [result["market"].eq("TWSE"), result["market"].eq("TPEX")],
        [result["ticker"] + ".TW", result["ticker"] + ".TWO"],
        default=result["ticker"],
    )

    selected_columns = [
        "period",
        "yyyymm",
        "ticker",
        "yf_ticker",
        "name",
        "market",
        "industry_mops",
        "revenue",
        "last_month_revenue_reported",
        "last_year_month_revenue_reported",
        "mom_reported_pct",
        "yoy_reported_pct",
        "cum_revenue",
        "last_year_cum_revenue",
        "cum_yoy_reported_pct",
        "note",
        "report_date",
        "source",
        "fetched_at",
        "source_priority",
        "ticker_valid",
        "period_valid",
        "revenue_valid",
    ]
    return result.loc[:, selected_columns].copy()


def def_merge_incremental_monthly_revenue(
    existing: pd.DataFrame,
    incoming: pd.DataFrame,
) -> pd.DataFrame:
    frames = [frame for frame in (existing, incoming) if not frame.empty]
    if not frames:
        return pd.DataFrame()
    merged = pd.concat(frames, ignore_index=True, sort=False)
    merged["source_priority"] = pd.to_numeric(
        merged.get("source_priority", 0), errors="coerce"
    ).fillna(0)
    merged["fetched_at_sort"] = pd.to_datetime(
        merged.get("fetched_at"), errors="coerce", utc=True
    )
    merged = merged.sort_values(
        ["period", "ticker", "market", "source_priority", "fetched_at_sort"],
        na_position="first",
    )
    merged = merged.drop_duplicates(
        subset=["period", "ticker", "market"],
        keep="last",
    )
    merged = merged.drop(columns=["fetched_at_sort"], errors="ignore")
    return merged.sort_values(["ticker", "period", "market"]).reset_index(drop=True)


def def_load_monthly_revenue_inputs(
    config: EngineConfig,
    logger: logging.Logger,
    injected_dataframe: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    source_manifest: Dict[str, Any] = {
        "existing_input": None,
        "fetch_latest_requested": config.fetch_latest,
        "fetch_warnings": [],
    }

    if injected_dataframe is not None:
        existing_normalized = def_normalize_monthly_revenue(
            injected_dataframe,
            source_priority=20,
        )
        source_manifest["existing_input"] = "INJECTED_DATAFRAME"
    else:
        input_path = config.input_path or def_first_existing_path(
            DEFAULT_MONTHLY_REVENUE_INPUT_CANDIDATES
        )
        if input_path is not None:
            logger.info("Load canonical monthly revenue: %s", input_path)
            existing_raw = def_read_table(input_path)
            existing_normalized = def_normalize_monthly_revenue(
                existing_raw,
                source_priority=20,
            )
            source_manifest["existing_input"] = str(input_path)
            source_manifest["existing_input_sha256"] = def_sha256_file(input_path)
        else:
            existing_normalized = pd.DataFrame()

    incoming_normalized = pd.DataFrame()
    if config.fetch_latest and injected_dataframe is None:
        latest_raw, fetch_warnings = def_fetch_latest_mops(logger)
        source_manifest["fetch_warnings"] = fetch_warnings
        if not latest_raw.empty:
            incoming_normalized = def_normalize_monthly_revenue(
                latest_raw,
                source_priority=100,
            )

    if config.incremental_update:
        canonical = def_merge_incremental_monthly_revenue(
            existing_normalized,
            incoming_normalized,
        )
    else:
        canonical = incoming_normalized if not incoming_normalized.empty else existing_normalized

    canonical = def_filter_period_range(
        canonical,
        config.start_period,
        config.end_period,
    )
    source_manifest["existing_rows"] = int(len(existing_normalized))
    source_manifest["incoming_rows"] = int(len(incoming_normalized))
    source_manifest["canonical_rows"] = int(len(canonical))
    return canonical, source_manifest


# =============================================================================
# 5. COMPANY MASTER AND MULTI-GROUP CLASSIFICATION SSOT
# =============================================================================


def def_prepare_company_master(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return pd.DataFrame(
            columns=[
                "ticker",
                "name_master",
                "market_master",
                "industry_master",
                "sector_master",
                "subindustry_master",
            ]
        )
    result = def_rename_by_aliases(dataframe, MASTER_COLUMN_ALIASES)
    if "ticker" not in result.columns:
        raise ValueError("Company master missing ticker column")
    result["ticker"] = result["ticker"].map(def_normalize_ticker)
    for column in (
        "name_master",
        "market_master",
        "industry_master",
        "sector_master",
        "subindustry_master",
    ):
        if column not in result.columns:
            result[column] = pd.NA
        result[column] = result[column].astype("string").str.strip().replace("", pd.NA)
    result["market_master"] = result["market_master"].map(
        lambda value: def_normalize_market(value, None)
    )
    result = result.loc[result["ticker"].ne("")].copy()
    result = result.sort_values("ticker").drop_duplicates("ticker", keep="last")
    return result[
        [
            "ticker",
            "name_master",
            "market_master",
            "industry_master",
            "sector_master",
            "subindustry_master",
        ]
    ].reset_index(drop=True)


def def_bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "是",
        "主要",
        "primary",
    }


def def_split_group_values(value: Any) -> List[str]:
    if value is None or pd.isna(value):
        return []
    text = str(value).strip()
    if not text:
        return []
    return [item.strip() for item in GROUP_SPLIT_PATTERN.split(text) if item.strip()]


def def_prepare_group_mapping(dataframe: pd.DataFrame) -> pd.DataFrame:
    output_columns = [
        "ticker",
        "group",
        "group_weight",
        "is_primary_group",
        "classification_version",
        "classification_source",
        "group_mapping_proxy",
    ]
    if dataframe.empty:
        return pd.DataFrame(columns=output_columns)

    result = def_rename_by_aliases(dataframe, GROUP_COLUMN_ALIASES)
    if "ticker" not in result.columns:
        raise ValueError("Group mapping missing ticker column")
    result["ticker"] = result["ticker"].map(def_normalize_ticker)

    dynamic_group_columns = [
        column
        for column in result.columns
        if re.fullmatch(r"(?i)(group|族群)[_\s-]*\d+", str(column).strip())
    ]
    rows: List[Dict[str, Any]] = []
    for _, row in result.iterrows():
        ticker = def_normalize_ticker(row.get("ticker"))
        if not ticker:
            continue

        group_values: List[str] = []
        group_values.extend(def_split_group_values(row.get("group")))
        group_values.extend(def_split_group_values(row.get("groups")))
        for column in dynamic_group_columns:
            group_values.extend(def_split_group_values(row.get(column)))
        group_values = list(dict.fromkeys(group_values))
        if not group_values:
            continue

        raw_weight = pd.to_numeric(row.get("group_weight"), errors="coerce")
        explicit_weight = float(raw_weight) if pd.notna(raw_weight) and raw_weight > 0 else np.nan
        primary_value = def_bool_value(row.get("is_primary_group"))
        version = row.get("classification_version", ENGINE_VERSION)
        source = row.get("classification_source", "GROUP_SSOT")

        for index, group_name in enumerate(group_values):
            rows.append(
                {
                    "ticker": ticker,
                    "group": str(group_name).strip(),
                    "group_weight": explicit_weight,
                    "is_primary_group": bool(primary_value or index == 0),
                    "classification_version": (
                        ENGINE_VERSION if pd.isna(version) else str(version)
                    ),
                    "classification_source": (
                        "GROUP_SSOT" if pd.isna(source) else str(source)
                    ),
                    "group_mapping_proxy": False,
                }
            )

    mapping = pd.DataFrame(rows, columns=output_columns)
    if mapping.empty:
        return mapping
    mapping = mapping.loc[mapping["group"].astype(str).str.strip().ne("")].copy()
    mapping = mapping.drop_duplicates(["ticker", "group"], keep="last")

    def def_normalize_ticker_weights(group: pd.DataFrame) -> pd.DataFrame:
        local = group.copy()
        weight_sum = pd.to_numeric(local["group_weight"], errors="coerce").sum(min_count=1)
        if pd.isna(weight_sum) or weight_sum <= 0:
            local["group_weight"] = 1.0 / len(local)
        else:
            local["group_weight"] = (
                pd.to_numeric(local["group_weight"], errors="coerce").fillna(0.0)
                / float(weight_sum)
            )
        if not local["is_primary_group"].any():
            local.loc[local.index[0], "is_primary_group"] = True
        return local

    normalized_groups = []
    for _, ticker_group in mapping.groupby("ticker", sort=False):
        normalized_groups.append(def_normalize_ticker_weights(ticker_group))
    mapping = pd.concat(normalized_groups, ignore_index=True)
    return mapping[output_columns].sort_values(
        ["ticker", "is_primary_group", "group"],
        ascending=[True, False, True],
    ).reset_index(drop=True)


def def_load_classification_inputs(
    config: EngineConfig,
    canonical: pd.DataFrame,
    injected_company_master: Optional[pd.DataFrame] = None,
    injected_group_mapping: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    manifest: Dict[str, Any] = {}

    if injected_company_master is not None:
        company_master = def_prepare_company_master(injected_company_master)
        manifest["company_master"] = "INJECTED_DATAFRAME"
    else:
        company_path = config.company_master_path or def_first_existing_path(
            DEFAULT_COMPANY_MASTER_CANDIDATES
        )
        if company_path:
            company_master = def_prepare_company_master(def_read_table(company_path))
            manifest["company_master"] = str(company_path)
            manifest["company_master_sha256"] = def_sha256_file(company_path)
        else:
            company_master = pd.DataFrame()
            manifest["company_master"] = None

    if company_master.empty:
        company_master = (
            canonical.sort_values(["ticker", "period"])
            .groupby("ticker", as_index=False)
            .agg(
                name_master=("name", "last"),
                market_master=("market", "last"),
                industry_master=("industry_mops", "last"),
            )
        )
        company_master["sector_master"] = pd.NA
        company_master["subindustry_master"] = pd.NA
        manifest["company_master_fallback"] = "MONTHLY_REVENUE_CANONICAL"

    if injected_group_mapping is not None:
        group_mapping = def_prepare_group_mapping(injected_group_mapping)
        manifest["group_mapping"] = "INJECTED_DATAFRAME"
    else:
        group_path = config.group_map_path or def_first_existing_path(
            DEFAULT_GROUP_MAP_CANDIDATES
        )
        if group_path:
            group_mapping = def_prepare_group_mapping(def_read_table(group_path))
            manifest["group_mapping"] = str(group_path)
            manifest["group_mapping_sha256"] = def_sha256_file(group_path)
        else:
            group_mapping = pd.DataFrame()
            manifest["group_mapping"] = None

    return company_master, group_mapping, manifest


def def_attach_company_master(
    canonical: pd.DataFrame,
    company_master: pd.DataFrame,
) -> pd.DataFrame:
    result = canonical.merge(company_master, on="ticker", how="left", validate="many_to_one")
    result["name"] = result["name_master"].combine_first(result["name"])
    result["market"] = result["market_master"].combine_first(result["market"])
    result["industry"] = result["industry_master"].combine_first(
        result["industry_mops"]
    )
    result["industry"] = (
        result["industry"].astype("string").str.strip().replace("", pd.NA)
    ).fillna("UNMAPPED_INDUSTRY")
    result["sector"] = (
        result["sector_master"].astype("string").str.strip().replace("", pd.NA)
    ).fillna(result["industry"])
    result["subindustry"] = (
        result["subindustry_master"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    ).fillna(result["industry"])
    result["company_master_mapped"] = result["name_master"].notna() | result[
        "industry_master"
    ].notna()
    result["yf_ticker"] = np.select(
        [result["market"].eq("TWSE"), result["market"].eq("TPEX")],
        [result["ticker"] + ".TW", result["ticker"] + ".TWO"],
        default=result["ticker"],
    )
    return result.drop(
        columns=[
            "name_master",
            "market_master",
            "industry_master",
            "sector_master",
            "subindustry_master",
        ],
        errors="ignore",
    )


def def_ensure_group_mapping(
    company: pd.DataFrame,
    group_mapping: pd.DataFrame,
    allow_industry_fallback: bool,
) -> pd.DataFrame:
    known_tickers = set(group_mapping["ticker"].tolist()) if not group_mapping.empty else set()
    latest_company = (
        company.sort_values(["ticker", "period"])
        .groupby("ticker", as_index=False)
        .agg(industry=("industry", "last"))
    )
    missing = latest_company.loc[~latest_company["ticker"].isin(known_tickers)].copy()
    if not missing.empty and allow_industry_fallback:
        fallback = pd.DataFrame(
            {
                "ticker": missing["ticker"],
                "group": missing["industry"].fillna("UNMAPPED_GROUP"),
                "group_weight": 1.0,
                "is_primary_group": True,
                "classification_version": ENGINE_VERSION,
                "classification_source": "INDUSTRY_FALLBACK",
                "group_mapping_proxy": True,
            }
        )
        if group_mapping.empty:
            group_mapping = fallback.copy()
        else:
            group_mapping = pd.concat([group_mapping, fallback], ignore_index=True)
    return group_mapping.drop_duplicates(["ticker", "group"], keep="last").reset_index(
        drop=True
    )


# =============================================================================
# 6. COMPANY-LEVEL MONTHLY REVENUE ANALYTICS
# =============================================================================


def def_build_company_metrics(
    company_input: pd.DataFrame,
    config: EngineConfig,
) -> pd.DataFrame:
    if company_input.empty:
        return company_input.copy()

    result = company_input.sort_values(["ticker", "period", "market"]).copy()
    result = result.drop_duplicates(["period", "ticker", "market"], keep="last")
    ticker_group = result.groupby("ticker", sort=False)

    result["period_lag_1"] = ticker_group["period"].shift(1)
    result["period_lag_12"] = ticker_group["period"].shift(12)
    result["revenue_lag_1_actual"] = ticker_group["revenue"].shift(1)
    result["revenue_lag_12_actual"] = ticker_group["revenue"].shift(12)
    lag_1_valid = def_month_delta(result["period"], result["period_lag_1"]).eq(1)
    lag_12_valid = def_month_delta(result["period"], result["period_lag_12"]).eq(12)
    result.loc[~lag_1_valid, "revenue_lag_1_actual"] = np.nan
    result.loc[~lag_12_valid, "revenue_lag_12_actual"] = np.nan

    result["last_month_revenue"] = result["revenue_lag_1_actual"].combine_first(
        result["last_month_revenue_reported"]
    )
    result["last_year_month_revenue"] = result[
        "revenue_lag_12_actual"
    ].combine_first(result["last_year_month_revenue_reported"])

    result["mom_calculated_pct"] = np.where(
        result["last_month_revenue"].notna()
        & result["last_month_revenue"].ne(0),
        (result["revenue"] / result["last_month_revenue"] - 1.0) * 100.0,
        np.nan,
    )
    result["yoy_calculated_pct"] = np.where(
        result["last_year_month_revenue"].notna()
        & result["last_year_month_revenue"].ne(0),
        (result["revenue"] / result["last_year_month_revenue"] - 1.0) * 100.0,
        np.nan,
    )
    result["mom_pct"] = result["mom_calculated_pct"].combine_first(
        result["mom_reported_pct"]
    )
    result["yoy_pct"] = result["yoy_calculated_pct"].combine_first(
        result["yoy_reported_pct"]
    )
    result["mom_source"] = np.where(
        result["mom_calculated_pct"].notna(), "CALCULATED", "MOPS_REPORTED"
    )
    result["yoy_source"] = np.where(
        result["yoy_calculated_pct"].notna(), "CALCULATED", "MOPS_REPORTED"
    )

    result["mom_reported_calculated_gap_pp"] = (
        result["mom_reported_pct"] - result["mom_calculated_pct"]
    ).abs()
    result["yoy_reported_calculated_gap_pp"] = (
        result["yoy_reported_pct"] - result["yoy_calculated_pct"]
    ).abs()

    for window in (3, 6, 12):
        result[f"revenue_ma_{window}"] = ticker_group["revenue"].transform(
            lambda values, size=window: values.rolling(
                size,
                min_periods=min(size, config.min_rolling_observations),
            ).mean()
        )
    result["yoy_ma_3"] = ticker_group["yoy_pct"].transform(
        lambda values: values.rolling(3, min_periods=2).mean()
    )
    result["yoy_ma_6"] = ticker_group["yoy_pct"].transform(
        lambda values: values.rolling(6, min_periods=3).mean()
    )
    result["yoy_lag_1"] = ticker_group["yoy_pct"].shift(1)
    result["yoy_lag_3"] = ticker_group["yoy_pct"].shift(3)
    result["yoy_acceleration_1m_pp"] = result["yoy_pct"] - result["yoy_lag_1"]
    result["yoy_acceleration_3m_pp"] = result["yoy_pct"] - result["yoy_lag_3"]

    result["positive_yoy_streak"] = ticker_group["yoy_pct"].transform(
        lambda values: def_streak_boolean(values > 0)
    )
    result["positive_mom_streak"] = ticker_group["mom_pct"].transform(
        lambda values: def_streak_boolean(values > 0)
    )
    result["accelerating_yoy_streak"] = ticker_group[
        "yoy_acceleration_1m_pp"
    ].transform(lambda values: def_streak_boolean(values > 0))

    result["revenue_previous_12m_high"] = ticker_group["revenue"].transform(
        lambda values: values.shift(1).rolling(12, min_periods=6).max()
    )
    result["revenue_previous_24m_high"] = ticker_group["revenue"].transform(
        lambda values: values.shift(1).rolling(24, min_periods=12).max()
    )
    result["new_high_12m"] = (
        result["revenue_previous_12m_high"].notna()
        & (result["revenue"] >= result["revenue_previous_12m_high"])
    )
    result["new_high_24m"] = (
        result["revenue_previous_24m_high"].notna()
        & (result["revenue"] >= result["revenue_previous_24m_high"])
    )

    rolling_mean = ticker_group["revenue"].transform(
        lambda values: values.rolling(12, min_periods=6).mean()
    )
    rolling_std = ticker_group["revenue"].transform(
        lambda values: values.rolling(12, min_periods=6).std(ddof=0)
    )
    result["revenue_zscore_12m"] = np.where(
        rolling_std.notna() & rolling_std.ne(0),
        (result["revenue"] - rolling_mean) / rolling_std,
        np.nan,
    )

    phase_conditions = [
        result["yoy_pct"].isna(),
        (result["yoy_pct"] > 0)
        & (result["yoy_acceleration_1m_pp"] > 0)
        & (result["mom_pct"] > 0),
        (result["yoy_pct"] > 0) & (result["yoy_acceleration_1m_pp"] >= 0),
        (result["yoy_pct"] <= 0)
        & (result["yoy_acceleration_1m_pp"] > 0)
        & (result["mom_pct"] > 0),
        (result["yoy_pct"] > 0) & (result["yoy_acceleration_1m_pp"] < 0),
        (result["yoy_pct"] < 0) & (result["yoy_acceleration_1m_pp"] <= 0),
    ]
    phase_values = [
        "INSUFFICIENT_HISTORY",
        "LEADING_ACCELERATION",
        "EXPANDING",
        "RECOVERING",
        "DECELERATING",
        "CONTRACTING",
    ]
    result["company_phase"] = np.select(
        phase_conditions,
        phase_values,
        default="MIXED",
    )
    result["company_phase_score"] = result["company_phase"].map(PHASE_SCORE_MAP)
    result["company_phase_age_months"] = result.groupby("ticker", sort=False)[
        "company_phase"
    ].transform(def_streak_same_value)

    quality_flags: List[str] = []
    for _, row in result.iterrows():
        flags: List[str] = []
        if not bool(row.get("ticker_valid", False)):
            flags.append("INVALID_TICKER")
        if pd.isna(row.get("period")):
            flags.append("INVALID_PERIOD")
        if pd.isna(row.get("revenue")):
            flags.append("MISSING_REVENUE")
        elif float(row.get("revenue")) < 0:
            flags.append("NEGATIVE_REVENUE")
        if (
            pd.notna(row.get("mom_reported_calculated_gap_pp"))
            and float(row.get("mom_reported_calculated_gap_pp"))
            > config.reported_calculated_tolerance_pp
        ):
            flags.append("MOM_REPORTED_CALCULATED_MISMATCH")
        if (
            pd.notna(row.get("yoy_reported_calculated_gap_pp"))
            and float(row.get("yoy_reported_calculated_gap_pp"))
            > config.reported_calculated_tolerance_pp
        ):
            flags.append("YOY_REPORTED_CALCULATED_MISMATCH")
        if row.get("industry") == "UNMAPPED_INDUSTRY":
            flags.append("UNMAPPED_INDUSTRY")
        quality_flags.append("|".join(flags) if flags else "OK")
    result["quality_flags"] = quality_flags
    result["calculation_contract"] = ENGINE_CONTRACT
    result["calculation_version"] = ENGINE_VERSION

    drop_columns = ["period_lag_1", "period_lag_12"]
    result = result.drop(columns=drop_columns, errors="ignore")
    return result.sort_values(["period", "ticker", "market"]).reset_index(drop=True)


# =============================================================================
# 7. INDUSTRY / GROUP AGGREGATION AND DYNAMIC PHASE CLASSIFICATION
# =============================================================================


def def_build_dimension_fact(
    company: pd.DataFrame,
    group_mapping: pd.DataFrame,
    dimension_type: str,
) -> pd.DataFrame:
    if dimension_type == "industry":
        fact = company.copy()
        fact["dimension"] = fact["industry"].fillna("UNMAPPED_INDUSTRY")
        fact["dimension_weight"] = 1.0
        fact["is_primary_group"] = True
        fact["group_mapping_proxy"] = False
        return fact

    if dimension_type != "group":
        raise ValueError(f"Unsupported dimension_type: {dimension_type}")
    fact = company.merge(group_mapping, on="ticker", how="left", validate="many_to_many")
    fact["group"] = fact["group"].fillna("UNMAPPED_GROUP")
    fact["group_weight"] = pd.to_numeric(
        fact["group_weight"], errors="coerce"
    ).fillna(1.0)
    fact["dimension"] = fact["group"]
    fact["dimension_weight"] = fact["group_weight"]
    fact["group_mapping_proxy"] = (
        fact["group_mapping_proxy"].astype("boolean").fillna(True).astype(bool)
    )
    return fact


def def_aggregate_dimension_rows(
    fact: pd.DataFrame,
    dimension_type: str,
) -> pd.DataFrame:
    if fact.empty:
        return pd.DataFrame()

    local = fact.copy()
    local["effective_revenue"] = local["revenue"] * local["dimension_weight"]
    local["effective_abs_revenue"] = local["effective_revenue"].abs()
    rows: List[Dict[str, Any]] = []

    for (period, dimension), group in local.groupby(
        ["period", "dimension"],
        sort=True,
        dropna=False,
    ):
        valid_revenue = group["revenue"].notna()
        valid_yoy = group["yoy_pct"].notna()
        valid_mom = group["mom_pct"].notna()
        weight = group["dimension_weight"].fillna(0.0).astype(float)
        revenue_weight = group["effective_abs_revenue"].fillna(0.0).astype(float)
        total_revenue = float(group["effective_revenue"].sum(min_count=1))

        positive_revenue = group.loc[group["effective_revenue"] > 0, "effective_revenue"]
        if total_revenue > 0 and not positive_revenue.empty:
            shares = positive_revenue / positive_revenue.sum()
            hhi = float(np.square(shares).sum())
            top5_concentration = float(shares.nlargest(5).sum())
        else:
            hhi = np.nan
            top5_concentration = np.nan

        rows.append(
            {
                "period": period,
                "yyyymm": pd.Timestamp(period).strftime("%Y%m") if pd.notna(period) else None,
                "dimension_type": dimension_type.upper(),
                "dimension": dimension,
                "total_revenue": total_revenue,
                "member_count": int(group["ticker"].nunique()),
                "effective_member_count": float(weight.sum()),
                "reported_member_count": int(group.loc[valid_revenue, "ticker"].nunique()),
                "coverage_ratio": float(
                    weight.loc[valid_revenue].sum() / weight.sum()
                    if weight.sum() > 0
                    else np.nan
                ),
                "positive_yoy_breadth": float(
                    weight.loc[valid_yoy & (group["yoy_pct"] > 0)].sum()
                    / weight.loc[valid_yoy].sum()
                    if weight.loc[valid_yoy].sum() > 0
                    else np.nan
                ),
                "positive_mom_breadth": float(
                    weight.loc[valid_mom & (group["mom_pct"] > 0)].sum()
                    / weight.loc[valid_mom].sum()
                    if weight.loc[valid_mom].sum() > 0
                    else np.nan
                ),
                "accelerating_breadth": float(
                    weight.loc[
                        group["yoy_acceleration_1m_pp"].notna()
                        & (group["yoy_acceleration_1m_pp"] > 0)
                    ].sum()
                    / weight.loc[group["yoy_acceleration_1m_pp"].notna()].sum()
                    if weight.loc[group["yoy_acceleration_1m_pp"].notna()].sum() > 0
                    else np.nan
                ),
                "new_high_12m_breadth": float(
                    weight.loc[group["new_high_12m"].fillna(False)].sum()
                    / weight.loc[valid_revenue].sum()
                    if weight.loc[valid_revenue].sum() > 0
                    else np.nan
                ),
                "weighted_mean_company_yoy_pct": def_weighted_average(
                    group["yoy_pct"], revenue_weight
                ),
                "median_company_yoy_pct": def_safe_median(group["yoy_pct"]),
                "weighted_mean_company_mom_pct": def_weighted_average(
                    group["mom_pct"], revenue_weight
                ),
                "median_company_mom_pct": def_safe_median(group["mom_pct"]),
                "company_phase_score_weighted": def_weighted_average(
                    group["company_phase_score"], revenue_weight
                ),
                "hhi_revenue_concentration": hhi,
                "top5_revenue_concentration": top5_concentration,
                "proxy_member_ratio": float(
                    weight.loc[group.get("group_mapping_proxy", False).fillna(False)].sum()
                    / weight.sum()
                    if weight.sum() > 0
                    else 0.0
                ),
            }
        )

    aggregate = pd.DataFrame(rows)
    aggregate = aggregate.sort_values(["dimension", "period"]).reset_index(drop=True)
    dimension_group = aggregate.groupby("dimension", sort=False)
    aggregate["period_lag_1"] = dimension_group["period"].shift(1)
    aggregate["period_lag_12"] = dimension_group["period"].shift(12)
    aggregate["revenue_lag_1"] = dimension_group["total_revenue"].shift(1)
    aggregate["revenue_lag_12"] = dimension_group["total_revenue"].shift(12)
    lag_1_valid = def_month_delta(aggregate["period"], aggregate["period_lag_1"]).eq(1)
    lag_12_valid = def_month_delta(aggregate["period"], aggregate["period_lag_12"]).eq(12)
    aggregate.loc[~lag_1_valid, "revenue_lag_1"] = np.nan
    aggregate.loc[~lag_12_valid, "revenue_lag_12"] = np.nan
    aggregate["mom_pct"] = np.where(
        aggregate["revenue_lag_1"].notna() & aggregate["revenue_lag_1"].ne(0),
        (aggregate["total_revenue"] / aggregate["revenue_lag_1"] - 1.0) * 100.0,
        np.nan,
    )
    aggregate["yoy_pct"] = np.where(
        aggregate["revenue_lag_12"].notna() & aggregate["revenue_lag_12"].ne(0),
        (aggregate["total_revenue"] / aggregate["revenue_lag_12"] - 1.0) * 100.0,
        np.nan,
    )
    aggregate["yoy_lag_1"] = dimension_group["yoy_pct"].shift(1)
    aggregate["yoy_lag_3"] = dimension_group["yoy_pct"].shift(3)
    aggregate["positive_yoy_breadth_lag_1"] = dimension_group[
        "positive_yoy_breadth"
    ].shift(1)
    aggregate["yoy_acceleration_1m_pp"] = aggregate["yoy_pct"] - aggregate[
        "yoy_lag_1"
    ]
    aggregate["yoy_acceleration_3m_pp"] = aggregate["yoy_pct"] - aggregate[
        "yoy_lag_3"
    ]
    aggregate["breadth_change_1m_pp"] = (
        aggregate["positive_yoy_breadth"]
        - aggregate["positive_yoy_breadth_lag_1"]
    ) * 100.0
    aggregate["market_total_revenue"] = aggregate.groupby("period")[
        "total_revenue"
    ].transform("sum")
    aggregate["market_contribution"] = np.where(
        aggregate["market_total_revenue"].ne(0),
        aggregate["total_revenue"] / aggregate["market_total_revenue"],
        np.nan,
    )
    aggregate = aggregate.drop(
        columns=["period_lag_1", "period_lag_12"],
        errors="ignore",
    )
    return aggregate.sort_values(["period", "dimension"]).reset_index(drop=True)


def def_rank_percentile_by_period(
    dataframe: pd.DataFrame,
    source_column: str,
    ascending: bool = True,
) -> pd.Series:
    return dataframe.groupby("period")[source_column].rank(
        pct=True,
        method="average",
        ascending=ascending,
    )


def def_assign_dynamic_phase(
    aggregate: pd.DataFrame,
    config: EngineConfig,
) -> pd.DataFrame:
    if aggregate.empty:
        return aggregate.copy()

    result = aggregate.copy()
    result["yoy_percentile"] = def_rank_percentile_by_period(result, "yoy_pct")
    result["mom_percentile"] = def_rank_percentile_by_period(result, "mom_pct")
    result["acceleration_percentile"] = def_rank_percentile_by_period(
        result, "yoy_acceleration_1m_pp"
    )
    result["breadth_percentile"] = def_rank_percentile_by_period(
        result, "positive_yoy_breadth"
    )
    result["new_high_percentile"] = def_rank_percentile_by_period(
        result, "new_high_12m_breadth"
    )

    percentile_columns = [
        "yoy_percentile",
        "mom_percentile",
        "acceleration_percentile",
        "breadth_percentile",
        "new_high_percentile",
    ]
    for column in percentile_columns:
        result[column] = result[column].fillna(0.5)

    result["rotation_score"] = (
        0.35 * result["yoy_percentile"]
        + 0.20 * result["mom_percentile"]
        + 0.25 * result["acceleration_percentile"]
        + 0.15 * result["breadth_percentile"]
        + 0.05 * result["new_high_percentile"]
    )

    high = config.phase_high_percentile
    low = config.phase_low_percentile
    minimum_breadth = config.phase_min_positive_breadth
    strong_breadth = config.phase_strong_breadth
    phase_conditions = [
        result["yoy_pct"].isna(),
        (result["yoy_percentile"] >= high)
        & (result["acceleration_percentile"] >= 0.60)
        & (result["positive_yoy_breadth"] >= strong_breadth),
        (result["yoy_pct"] > 0)
        & (result["positive_yoy_breadth"] >= minimum_breadth)
        & (result["yoy_acceleration_1m_pp"] >= 0),
        (result["yoy_pct"] <= 0)
        & (result["yoy_acceleration_1m_pp"] > 0)
        & (result["breadth_change_1m_pp"] > 0),
        (result["yoy_pct"] > 0)
        & (result["yoy_acceleration_1m_pp"] < 0),
        (result["yoy_percentile"] <= low)
        & (result["yoy_pct"] < 0)
        & (result["yoy_acceleration_1m_pp"] <= 0),
    ]
    phase_values = [
        "INSUFFICIENT_HISTORY",
        "LEADING_ACCELERATION",
        "EXPANDING",
        "RECOVERING",
        "DECELERATING",
        "CONTRACTING",
    ]
    result["phase"] = np.select(phase_conditions, phase_values, default="MIXED")
    result["phase_score"] = result["phase"].map(PHASE_SCORE_MAP)

    rotation_conditions = [
        (result["rotation_score"] >= config.rotation_leader_score)
        & (result["yoy_pct"] > 0),
        (result["rotation_score"] >= config.rotation_improving_score)
        & (result["yoy_acceleration_1m_pp"] > 0),
        result["rotation_score"] >= config.rotation_peer_score,
        result["rotation_score"] >= config.rotation_weakening_score,
    ]
    rotation_values = ["LEADER", "IMPROVING", "PEER", "WEAKENING"]
    result["rotation_state"] = np.select(
        rotation_conditions,
        rotation_values,
        default="LAGGER",
    )

    signal_consistency = (
        (result["yoy_pct"] > 0).astype(float)
        + (result["mom_pct"] > 0).astype(float)
        + (result["yoy_acceleration_1m_pp"] > 0).astype(float)
        + (result["positive_yoy_breadth"] >= minimum_breadth).astype(float)
    ) / 4.0
    result["phase_confidence"] = (
        result["coverage_ratio"].fillna(0.0).clip(0.0, 1.0)
        * (0.50 + 0.50 * signal_consistency)
    ).clip(0.0, 1.0)
    result["phase_age_months"] = result.groupby("dimension", sort=False)[
        "phase"
    ].transform(def_streak_same_value)
    result["rotation_rank"] = result.groupby("period")["rotation_score"].rank(
        ascending=False,
        method="min",
    )
    result["calculation_contract"] = ENGINE_CONTRACT
    result["calculation_version"] = ENGINE_VERSION
    return result.sort_values(["period", "rotation_rank", "dimension"]).reset_index(
        drop=True
    )


def def_build_dimension_analytics(
    company: pd.DataFrame,
    group_mapping: pd.DataFrame,
    dimension_type: str,
    config: EngineConfig,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    fact = def_build_dimension_fact(company, group_mapping, dimension_type)
    aggregate = def_aggregate_dimension_rows(fact, dimension_type)
    aggregate = def_assign_dynamic_phase(aggregate, config)
    return fact, aggregate


# =============================================================================
# 8. COMPANY × GROUP × PHASE AND INDUSTRY × GROUP BRIDGE
# =============================================================================


def def_build_company_group_phase(
    group_fact: pd.DataFrame,
    group_aggregate: pd.DataFrame,
    config: EngineConfig,
) -> pd.DataFrame:
    if group_fact.empty or group_aggregate.empty:
        return pd.DataFrame()

    group_columns = [
        "period",
        "dimension",
        "total_revenue",
        "yoy_pct",
        "mom_pct",
        "yoy_acceleration_1m_pp",
        "positive_yoy_breadth",
        "rotation_score",
        "rotation_rank",
        "phase",
        "phase_age_months",
        "phase_confidence",
        "rotation_state",
    ]
    group_state = group_aggregate[group_columns].rename(
        columns={
            "dimension": "group",
            "total_revenue": "group_total_revenue",
            "yoy_pct": "group_yoy_pct",
            "mom_pct": "group_mom_pct",
            "yoy_acceleration_1m_pp": "group_yoy_acceleration_1m_pp",
            "positive_yoy_breadth": "group_positive_yoy_breadth",
            "rotation_score": "group_rotation_score",
            "rotation_rank": "group_rotation_rank",
            "phase": "group_phase",
            "phase_age_months": "group_phase_age_months",
            "phase_confidence": "group_phase_confidence",
            "rotation_state": "group_rotation_state",
        }
    )
    result = group_fact.copy()
    result["group"] = result["dimension"]
    result["weighted_revenue"] = result["revenue"] * result["dimension_weight"]
    result = result.merge(
        group_state,
        on=["period", "group"],
        how="left",
        validate="many_to_one",
    )
    result["company_contribution_to_group"] = np.where(
        result["group_total_revenue"].notna()
        & result["group_total_revenue"].ne(0),
        result["weighted_revenue"] / result["group_total_revenue"],
        np.nan,
    )
    result["company_vs_group_yoy_gap_pp"] = (
        result["yoy_pct"] - result["group_yoy_pct"]
    )
    gap = config.company_group_relative_gap_pp
    result["company_relative_to_group"] = np.select(
        [
            result["company_vs_group_yoy_gap_pp"] >= gap,
            result["company_vs_group_yoy_gap_pp"] <= -gap,
        ],
        ["OUTPERFORMING", "UNDERPERFORMING"],
        default="IN_LINE",
    )
    result["company_revenue_rank_in_group"] = result.groupby(
        ["period", "group"]
    )["weighted_revenue"].rank(ascending=False, method="min")
    result["company_yoy_rank_in_group"] = result.groupby(["period", "group"])[
        "yoy_pct"
    ].rank(ascending=False, method="min")
    result["company_yoy_percentile_in_group"] = result.groupby(
        ["period", "group"]
    )["yoy_pct"].rank(pct=True, ascending=True, method="average")

    result["phase_alignment"] = np.select(
        [
            result["company_phase"].isin(["LEADING_ACCELERATION", "EXPANDING"])
            & result["group_phase"].isin(["LEADING_ACCELERATION", "EXPANDING"]),
            result["company_phase"].eq("RECOVERING")
            & result["group_phase"].isin(["RECOVERING", "EXPANDING"]),
            result["company_phase"].isin(["CONTRACTING", "DECELERATING"])
            & result["group_phase"].isin(["CONTRACTING", "DECELERATING"]),
        ],
        ["ALIGNED_EXPANSION", "ALIGNED_RECOVERY", "ALIGNED_WEAKNESS"],
        default="DIVERGENT_OR_MIXED",
    )
    result["calculation_contract"] = ENGINE_CONTRACT
    result["calculation_version"] = ENGINE_VERSION

    selected = [
        "period",
        "yyyymm",
        "ticker",
        "yf_ticker",
        "name",
        "market",
        "sector",
        "industry",
        "subindustry",
        "group",
        "dimension_weight",
        "is_primary_group",
        "group_mapping_proxy",
        "classification_version",
        "classification_source",
        "revenue",
        "weighted_revenue",
        "mom_pct",
        "yoy_pct",
        "yoy_acceleration_1m_pp",
        "company_phase",
        "company_phase_age_months",
        "group_total_revenue",
        "group_mom_pct",
        "group_yoy_pct",
        "group_yoy_acceleration_1m_pp",
        "group_positive_yoy_breadth",
        "group_rotation_score",
        "group_rotation_rank",
        "group_phase",
        "group_phase_age_months",
        "group_phase_confidence",
        "group_rotation_state",
        "company_contribution_to_group",
        "company_vs_group_yoy_gap_pp",
        "company_relative_to_group",
        "company_revenue_rank_in_group",
        "company_yoy_rank_in_group",
        "company_yoy_percentile_in_group",
        "phase_alignment",
        "calculation_contract",
        "calculation_version",
    ]
    return result.loc[:, [column for column in selected if column in result.columns]].sort_values(
        ["period", "group", "company_revenue_rank_in_group", "ticker"]
    ).reset_index(drop=True)


def def_build_industry_group_bridge(
    company_group_phase: pd.DataFrame,
) -> pd.DataFrame:
    if company_group_phase.empty:
        return pd.DataFrame()
    local = company_group_phase.copy()
    bridge = (
        local.groupby(["period", "industry", "group"], as_index=False)
        .agg(
            weighted_revenue=("weighted_revenue", "sum"),
            member_count=("ticker", "nunique"),
            weighted_mean_company_yoy_pct=(
                "yoy_pct",
                "mean",
            ),
            proxy_member_ratio=("group_mapping_proxy", "mean"),
        )
        .sort_values(["industry", "group", "period"])
    )
    bridge["industry_total_revenue"] = bridge.groupby(["period", "industry"])[
        "weighted_revenue"
    ].transform("sum")
    bridge["group_total_revenue"] = bridge.groupby(["period", "group"])[
        "weighted_revenue"
    ].transform("sum")
    bridge["share_of_industry"] = np.where(
        bridge["industry_total_revenue"].ne(0),
        bridge["weighted_revenue"] / bridge["industry_total_revenue"],
        np.nan,
    )
    bridge["share_of_group"] = np.where(
        bridge["group_total_revenue"].ne(0),
        bridge["weighted_revenue"] / bridge["group_total_revenue"],
        np.nan,
    )
    pair_group = bridge.groupby(["industry", "group"], sort=False)
    bridge["revenue_lag_12"] = pair_group["weighted_revenue"].shift(12)
    bridge["period_lag_12"] = pair_group["period"].shift(12)
    valid_lag = def_month_delta(bridge["period"], bridge["period_lag_12"]).eq(12)
    bridge.loc[~valid_lag, "revenue_lag_12"] = np.nan
    bridge["industry_group_yoy_pct"] = np.where(
        bridge["revenue_lag_12"].notna() & bridge["revenue_lag_12"].ne(0),
        (bridge["weighted_revenue"] / bridge["revenue_lag_12"] - 1.0) * 100.0,
        np.nan,
    )
    bridge["calculation_contract"] = ENGINE_CONTRACT
    bridge["calculation_version"] = ENGINE_VERSION
    return bridge.drop(columns=["period_lag_12"], errors="ignore").sort_values(
        ["period", "industry", "group"]
    ).reset_index(drop=True)


# =============================================================================
# 9. CROSS-INDUSTRY / CROSS-GROUP PAIRWISE MATRICES
# =============================================================================


def def_build_cross_dimension_matrix(aggregate: pd.DataFrame) -> pd.DataFrame:
    if aggregate.empty:
        return pd.DataFrame()
    columns = [
        "period",
        "dimension",
        "yoy_pct",
        "mom_pct",
        "yoy_acceleration_1m_pp",
        "positive_yoy_breadth",
        "rotation_score",
        "rotation_rank",
        "phase",
        "rotation_state",
        "market_contribution",
    ]
    left = aggregate[columns].rename(
        columns={column: f"{column}_a" for column in columns if column != "period"}
    )
    right = aggregate[columns].rename(
        columns={column: f"{column}_b" for column in columns if column != "period"}
    )
    matrix = left.merge(right, on="period", how="inner")
    matrix = matrix.loc[matrix["dimension_a"].astype(str) < matrix["dimension_b"].astype(str)].copy()
    matrix["yoy_gap_pp"] = matrix["yoy_pct_a"] - matrix["yoy_pct_b"]
    matrix["mom_gap_pp"] = matrix["mom_pct_a"] - matrix["mom_pct_b"]
    matrix["acceleration_gap_pp"] = (
        matrix["yoy_acceleration_1m_pp_a"]
        - matrix["yoy_acceleration_1m_pp_b"]
    )
    matrix["breadth_gap_pp"] = (
        matrix["positive_yoy_breadth_a"]
        - matrix["positive_yoy_breadth_b"]
    ) * 100.0
    matrix["rotation_score_gap"] = (
        matrix["rotation_score_a"] - matrix["rotation_score_b"]
    )
    matrix["dominant_dimension"] = np.select(
        [matrix["rotation_score_gap"] > 0, matrix["rotation_score_gap"] < 0],
        [matrix["dimension_a"], matrix["dimension_b"]],
        default="TIE",
    )
    matrix["dominance_strength"] = matrix["rotation_score_gap"].abs()
    matrix["calculation_contract"] = ENGINE_CONTRACT
    matrix["calculation_version"] = ENGINE_VERSION
    return matrix.sort_values(
        ["period", "dominance_strength", "dimension_a", "dimension_b"],
        ascending=[True, False, True, True],
    ).reset_index(drop=True)


def def_compute_lead_lag_matrix(
    aggregate: pd.DataFrame,
    config: EngineConfig,
) -> pd.DataFrame:
    if aggregate.empty:
        return pd.DataFrame()
    dimensions = sorted(aggregate["dimension"].dropna().astype(str).unique().tolist())
    if len(dimensions) > config.max_pairwise_dimensions:
        latest_period = aggregate["period"].max()
        dimensions = (
            aggregate.loc[aggregate["period"].eq(latest_period)]
            .sort_values("market_contribution", ascending=False)
            .head(config.max_pairwise_dimensions)["dimension"]
            .astype(str)
            .tolist()
        )

    pivot_yoy = aggregate.loc[aggregate["dimension"].isin(dimensions)].pivot(
        index="period",
        columns="dimension",
        values="yoy_pct",
    )
    pivot_score = aggregate.loc[aggregate["dimension"].isin(dimensions)].pivot(
        index="period",
        columns="dimension",
        values="rotation_score",
    )
    rows: List[Dict[str, Any]] = []
    for dimension_a, dimension_b in itertools.combinations(dimensions, 2):
        best: Optional[Dict[str, Any]] = None
        for lag in range(-config.lead_lag_max_months, config.lead_lag_max_months + 1):
            aligned = pd.concat(
                [
                    pivot_yoy[dimension_a].rename("a"),
                    pivot_yoy[dimension_b].shift(-lag).rename("b"),
                ],
                axis=1,
            ).dropna()
            if len(aligned) < config.lead_lag_min_observations:
                continue
            correlation = float(aligned["a"].corr(aligned["b"]))
            candidate = {
                "lag_months_a_leads_b": int(lag),
                "yoy_correlation": correlation,
                "abs_yoy_correlation": abs(correlation),
                "observations": int(len(aligned)),
            }
            if best is None or candidate["abs_yoy_correlation"] > best[
                "abs_yoy_correlation"
            ]:
                best = candidate

        contemporaneous = pd.concat(
            [
                pivot_yoy[dimension_a].rename("a"),
                pivot_yoy[dimension_b].rename("b"),
            ],
            axis=1,
        ).dropna()
        score_aligned = pd.concat(
            [
                pivot_score[dimension_a].rename("a"),
                pivot_score[dimension_b].rename("b"),
            ],
            axis=1,
        ).dropna()
        if best is None:
            best = {
                "lag_months_a_leads_b": np.nan,
                "yoy_correlation": np.nan,
                "abs_yoy_correlation": np.nan,
                "observations": int(len(contemporaneous)),
            }
        best_lag = best["lag_months_a_leads_b"]
        if pd.isna(best_lag):
            leader = "INSUFFICIENT_HISTORY"
        elif int(best_lag) > 0:
            leader = dimension_a
        elif int(best_lag) < 0:
            leader = dimension_b
        else:
            leader = "CONTEMPORANEOUS"
        rows.append(
            {
                "dimension_a": dimension_a,
                "dimension_b": dimension_b,
                **best,
                "contemporaneous_yoy_correlation": (
                    float(contemporaneous["a"].corr(contemporaneous["b"]))
                    if len(contemporaneous) >= 3
                    else np.nan
                ),
                "contemporaneous_rotation_score_correlation": (
                    float(score_aligned["a"].corr(score_aligned["b"]))
                    if len(score_aligned) >= 3
                    else np.nan
                ),
                "inferred_leader": leader,
                "lag_definition": "corr(A[t], B[t+L]); L>0 means A leads B",
                "calculation_contract": ENGINE_CONTRACT,
                "calculation_version": ENGINE_VERSION,
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["abs_yoy_correlation", "dimension_a", "dimension_b"],
        ascending=[False, True, True],
        na_position="last",
    ).reset_index(drop=True)


def def_build_phase_transition_matrix(aggregate: pd.DataFrame) -> pd.DataFrame:
    if aggregate.empty:
        return pd.DataFrame()
    local = aggregate.sort_values(["dimension", "period"]).copy()
    local["from_phase"] = local.groupby("dimension")["phase"].shift(1)
    local["to_phase"] = local["phase"]
    transitions = local.dropna(subset=["from_phase", "to_phase"])
    if transitions.empty:
        return pd.DataFrame()
    result = (
        transitions.groupby(["from_phase", "to_phase"], as_index=False)
        .agg(transition_count=("dimension", "size"))
        .sort_values(["from_phase", "transition_count"], ascending=[True, False])
    )
    result["from_phase_total"] = result.groupby("from_phase")[
        "transition_count"
    ].transform("sum")
    result["transition_probability"] = result["transition_count"] / result[
        "from_phase_total"
    ]
    result["calculation_contract"] = ENGINE_CONTRACT
    result["calculation_version"] = ENGINE_VERSION
    return result.reset_index(drop=True)


# =============================================================================
# 10. QUALITY GATES, RECONCILIATION, BACKUP, AND OUTPUT
# =============================================================================


def def_add_quality_check(
    checks: List[Dict[str, Any]],
    check_id: str,
    status: str,
    metric: Any,
    threshold: Any,
    message: str,
) -> None:
    checks.append(
        {
            "check_id": check_id,
            "status": status,
            "metric": metric,
            "threshold": threshold,
            "message": message,
        }
    )


def def_validate_pipeline(
    canonical: pd.DataFrame,
    company: pd.DataFrame,
    group_mapping: pd.DataFrame,
    industry_aggregate: pd.DataFrame,
    group_aggregate: pd.DataFrame,
    company_group_phase: pd.DataFrame,
    config: EngineConfig,
    capabilities: Dict[str, Any],
) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []

    duplicate_count = int(
        canonical.duplicated(["period", "ticker", "market"], keep=False).sum()
    )
    def_add_quality_check(
        checks,
        "Q01_CANONICAL_DUPLICATE_KEY",
        "PASS" if duplicate_count == 0 else "FAIL",
        duplicate_count,
        0,
        "Canonical key must be unique: period + ticker + market.",
    )

    invalid_period_count = int(canonical["period"].isna().sum())
    def_add_quality_check(
        checks,
        "Q02_INVALID_PERIOD",
        "PASS" if invalid_period_count == 0 else "FAIL",
        invalid_period_count,
        0,
        "Every canonical row requires a valid monthly period.",
    )

    missing_revenue_ratio = float(canonical["revenue"].isna().mean()) if len(canonical) else 1.0
    def_add_quality_check(
        checks,
        "Q03_MISSING_REVENUE_RATIO",
        "PASS" if missing_revenue_ratio == 0 else "WARN",
        missing_revenue_ratio,
        0,
        "Missing revenue rows are retained and flagged, never forward-filled.",
    )

    latest_period = company["period"].max() if not company.empty else pd.NaT
    latest_company = company.loc[company["period"].eq(latest_period)] if pd.notna(latest_period) else company
    unmapped_industry_ratio = float(
        latest_company["industry"].eq("UNMAPPED_INDUSTRY").mean()
    ) if len(latest_company) else 1.0
    def_add_quality_check(
        checks,
        "Q04_UNMAPPED_INDUSTRY_RATIO",
        "PASS"
        if unmapped_industry_ratio <= config.unmapped_warning_ratio
        else "WARN",
        unmapped_industry_ratio,
        config.unmapped_warning_ratio,
        "Industry mapping coverage at the latest period.",
    )

    mapped_tickers = set(group_mapping["ticker"].tolist()) if not group_mapping.empty else set()
    latest_tickers = set(latest_company["ticker"].tolist())
    unmapped_group_ratio = (
        len(latest_tickers - mapped_tickers) / len(latest_tickers)
        if latest_tickers
        else 1.0
    )
    def_add_quality_check(
        checks,
        "Q05_UNMAPPED_GROUP_RATIO",
        "PASS" if unmapped_group_ratio <= config.unmapped_warning_ratio else "WARN",
        unmapped_group_ratio,
        config.unmapped_warning_ratio,
        "Group mapping coverage after explicit or industry fallback mapping.",
    )

    weight_sum = group_mapping.groupby("ticker")["group_weight"].sum() if not group_mapping.empty else pd.Series(dtype=float)
    bad_weight_count = int((weight_sum.sub(1.0).abs() > config.reconciliation_tolerance).sum())
    def_add_quality_check(
        checks,
        "Q06_GROUP_WEIGHT_SUM",
        "PASS" if bad_weight_count == 0 else "FAIL",
        bad_weight_count,
        0,
        "Each ticker's multi-group weights must sum to one.",
    )

    reconciliation = pd.DataFrame()
    if not company.empty and not group_aggregate.empty:
        company_total = company.groupby("period", as_index=False)["revenue"].sum().rename(
            columns={"revenue": "company_total"}
        )
        group_total = group_aggregate.groupby("period", as_index=False)[
            "total_revenue"
        ].sum().rename(columns={"total_revenue": "group_total"})
        reconciliation = company_total.merge(group_total, on="period", how="outer")
        denominator = reconciliation["company_total"].abs().replace(0, np.nan)
        reconciliation["relative_gap"] = (
            reconciliation["company_total"] - reconciliation["group_total"]
        ).abs() / denominator
        max_gap = float(reconciliation["relative_gap"].max(skipna=True) or 0.0)
    else:
        max_gap = np.inf
    def_add_quality_check(
        checks,
        "Q07_GROUP_REVENUE_RECONCILIATION",
        "PASS" if max_gap <= config.reconciliation_tolerance else "FAIL",
        max_gap,
        config.reconciliation_tolerance,
        "Weighted multi-group revenue must reconcile to company total revenue.",
    )

    latest_group_coverage = float(
        group_aggregate.loc[group_aggregate["period"].eq(group_aggregate["period"].max()), "coverage_ratio"].median()
    ) if not group_aggregate.empty else 0.0
    def_add_quality_check(
        checks,
        "Q08_LATEST_GROUP_MEDIAN_COVERAGE",
        "PASS"
        if latest_group_coverage >= config.coverage_warning_ratio
        else "WARN",
        latest_group_coverage,
        config.coverage_warning_ratio,
        "Latest median group coverage ratio.",
    )

    company_group_duplicate_count = int(
        company_group_phase.duplicated(["period", "ticker", "group"], keep=False).sum()
    ) if not company_group_phase.empty else 0
    def_add_quality_check(
        checks,
        "Q09_COMPANY_GROUP_PHASE_DUPLICATE_KEY",
        "PASS" if company_group_duplicate_count == 0 else "FAIL",
        company_group_duplicate_count,
        0,
        "Company-group-phase key must be unique.",
    )

    parquet_status = capabilities.get("parquet_available", False)
    def_add_quality_check(
        checks,
        "Q10_PARQUET_CAPABILITY",
        "PASS" if parquet_status else ("FAIL" if config.require_parquet else "WARN"),
        parquet_status,
        config.require_parquet,
        "Parquet requires pyarrow or fastparquet.",
    )

    duckdb_status = capabilities.get("duckdb_available", False)
    def_add_quality_check(
        checks,
        "Q11_DUCKDB_CAPABILITY",
        "PASS" if duckdb_status else ("FAIL" if config.require_duckdb else "WARN"),
        duckdb_status,
        config.require_duckdb,
        "DuckDB output requires the duckdb package.",
    )

    statuses = [check["status"] for check in checks]
    overall_status = "FAIL" if "FAIL" in statuses else ("WARN" if "WARN" in statuses else "PASS")
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "contract": ENGINE_CONTRACT,
        "run_id": config.run_id,
        "generated_at": def_utc_now_iso(),
        "overall_status": overall_status,
        "latest_period": latest_period,
        "rows": {
            "canonical": int(len(canonical)),
            "company": int(len(company)),
            "industry": int(len(industry_aggregate)),
            "group": int(len(group_aggregate)),
            "company_group_phase": int(len(company_group_phase)),
        },
        "checks": checks,
        "reconciliation_preview": reconciliation.tail(24).to_dict(orient="records")
        if not reconciliation.empty
        else [],
    }


def def_collect_output_paths(output_dir: Path) -> List[Path]:
    paths: List[Path] = []
    for key, basename in OUTPUT_BASENAMES.items():
        if key in ("quality_report", "run_manifest", "duckdb", "sqlite_fallback"):
            paths.append(output_dir / basename)
        else:
            paths.append(output_dir / f"{basename}.csv")
            paths.append(output_dir / f"{basename}.parquet")
    return paths


def def_backup_existing_outputs(
    config: EngineConfig,
    logger: logging.Logger,
) -> Dict[str, Any]:
    backup_manifest: Dict[str, Any] = {"backup_created": False, "files": []}
    if not config.backup_before_write:
        return backup_manifest
    existing = [path for path in def_collect_output_paths(config.output_dir) if path.exists()]
    if not existing:
        return backup_manifest
    backup_run_dir = config.backup_dir / f"{ENGINE_NAME}_{ENGINE_VERSION}_{config.run_id}"
    backup_run_dir.mkdir(parents=True, exist_ok=True)
    for source in existing:
        destination = backup_run_dir / source.name
        shutil.copy2(source, destination)
        backup_manifest["files"].append(
            {
                "source": str(source),
                "backup": str(destination),
                "sha256": def_sha256_file(destination),
            }
        )
    backup_manifest["backup_created"] = True
    backup_manifest["backup_dir"] = str(backup_run_dir)
    logger.info("Backup existing outputs: %s files", len(existing))
    return backup_manifest


def def_write_dataframe_bundle(
    dataframe: pd.DataFrame,
    basename: str,
    config: EngineConfig,
    capabilities: Dict[str, Any],
) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "basename": basename,
        "rows": int(len(dataframe)),
        "columns": list(dataframe.columns),
        "outputs": [],
    }
    if config.write_csv:
        csv_path = config.output_dir / f"{basename}.csv"
        def_atomic_write_csv(dataframe, csv_path, config.output_encoding)
        record["outputs"].append(
            {
                "format": "csv",
                "path": str(csv_path),
                "sha256": def_sha256_file(csv_path),
            }
        )
    if config.write_parquet:
        parquet_path = config.output_dir / f"{basename}.parquet"
        if capabilities.get("parquet_available", False):
            def_atomic_write_parquet(dataframe, parquet_path)
            record["outputs"].append(
                {
                    "format": "parquet",
                    "path": str(parquet_path),
                    "sha256": def_sha256_file(parquet_path),
                }
            )
        else:
            record["outputs"].append(
                {
                    "format": "parquet",
                    "path": str(parquet_path),
                    "status": "SKIPPED_MISSING_ENGINE",
                }
            )
            if config.require_parquet:
                raise RuntimeError("Parquet output required but pyarrow/fastparquet is unavailable")
    return record


def def_write_duckdb(
    tables: Mapping[str, pd.DataFrame],
    config: EngineConfig,
    capabilities: Dict[str, Any],
) -> Dict[str, Any]:
    duckdb_path = config.output_dir / OUTPUT_BASENAMES["duckdb"]
    if not config.write_duckdb:
        return {"status": "SKIPPED_BY_CONFIG", "path": str(duckdb_path)}
    if not capabilities.get("duckdb_available", False):
        if config.require_duckdb:
            raise RuntimeError("DuckDB output required but duckdb package is unavailable")
        return {"status": "SKIPPED_MISSING_DUCKDB", "path": str(duckdb_path)}

    import duckdb  # type: ignore

    duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(duckdb_path))
    try:
        connection.execute("BEGIN TRANSACTION")
        for table_name, dataframe in tables.items():
            safe_name = def_safe_sql_identifier(table_name)
            registration_name = f"_df_{safe_name}"
            connection.register(registration_name, dataframe)
            connection.execute(
                f"CREATE OR REPLACE TABLE {safe_name} AS SELECT * FROM {registration_name}"
            )
            connection.unregister(registration_name)
        connection.execute(
            "CREATE OR REPLACE VIEW latest_group_phase AS "
            "SELECT * FROM monthly_revenue_group "
            "WHERE period = (SELECT MAX(period) FROM monthly_revenue_group)"
        )
        connection.execute(
            "CREATE OR REPLACE VIEW latest_company_group_phase AS "
            "SELECT * FROM monthly_revenue_company_group_phase "
            "WHERE period = (SELECT MAX(period) FROM monthly_revenue_company_group_phase)"
        )
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()
    return {
        "status": "WRITTEN",
        "path": str(duckdb_path),
        "sha256": def_sha256_file(duckdb_path),
    }


def def_write_sqlite_fallback(
    tables: Mapping[str, pd.DataFrame],
    config: EngineConfig,
) -> Dict[str, Any]:
    sqlite_path = config.output_dir / OUTPUT_BASENAMES["sqlite_fallback"]
    if not config.write_sqlite_fallback:
        return {"status": "SKIPPED_BY_CONFIG", "path": str(sqlite_path)}
    import sqlite3

    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(sqlite_path))
    try:
        for table_name, dataframe in tables.items():
            safe_name = def_safe_sql_identifier(table_name)
            local = dataframe.copy()
            for column in local.columns:
                if pd.api.types.is_datetime64_any_dtype(local[column]):
                    local[column] = local[column].dt.strftime("%Y-%m-%d")
            local.to_sql(safe_name, connection, if_exists="replace", index=False)
        connection.commit()
    finally:
        connection.close()
    return {
        "status": "WRITTEN",
        "path": str(sqlite_path),
        "sha256": def_sha256_file(sqlite_path),
    }


# =============================================================================
# 11. ORCHESTRATION
# =============================================================================


def def_run_engine(
    config: EngineConfig,
    injected_monthly_revenue: Optional[pd.DataFrame] = None,
    injected_company_master: Optional[pd.DataFrame] = None,
    injected_group_mapping: Optional[pd.DataFrame] = None,
    write_outputs: bool = True,
) -> Dict[str, Any]:
    logger = def_setup_logging(config.log_level)
    started_at = time.perf_counter()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.report_dir.mkdir(parents=True, exist_ok=True)
    config.backup_dir.mkdir(parents=True, exist_ok=True)
    capabilities = def_detect_capabilities()
    logger.info("%s %s · %s", ENGINE_NAME, ENGINE_VERSION, config.run_id)

    canonical, source_manifest = def_load_monthly_revenue_inputs(
        config,
        logger,
        injected_monthly_revenue,
    )
    if canonical.empty and config.fail_on_empty_result:
        raise RuntimeError("Monthly revenue canonical dataset is empty")

    invalid_period_count = int(canonical["period"].isna().sum())
    if invalid_period_count and config.fail_on_invalid_period:
        raise RuntimeError(f"Invalid period rows: {invalid_period_count}")
    canonical = canonical.loc[canonical["period"].notna()].copy()

    duplicate_count = int(
        canonical.duplicated(["period", "ticker", "market"], keep=False).sum()
    )
    if duplicate_count and config.fail_on_duplicate_keys:
        raise RuntimeError(f"Duplicate canonical keys remain: {duplicate_count}")

    company_master, group_mapping, classification_manifest = (
        def_load_classification_inputs(
            config,
            canonical,
            injected_company_master,
            injected_group_mapping,
        )
    )
    company_input = def_attach_company_master(canonical, company_master)
    company = def_build_company_metrics(company_input, config)
    group_mapping = def_ensure_group_mapping(
        company,
        group_mapping,
        config.allow_industry_as_group_fallback,
    )

    industry_fact, industry_aggregate = def_build_dimension_analytics(
        company,
        group_mapping,
        "industry",
        config,
    )
    group_fact, group_aggregate = def_build_dimension_analytics(
        company,
        group_mapping,
        "group",
        config,
    )
    company_group_phase = def_build_company_group_phase(
        group_fact,
        group_aggregate,
        config,
    )
    industry_group_bridge = def_build_industry_group_bridge(company_group_phase)
    cross_industry = def_build_cross_dimension_matrix(industry_aggregate)
    cross_group = def_build_cross_dimension_matrix(group_aggregate)
    lead_lag_industry = def_compute_lead_lag_matrix(industry_aggregate, config)
    lead_lag_group = def_compute_lead_lag_matrix(group_aggregate, config)
    phase_transition_industry = def_build_phase_transition_matrix(industry_aggregate)
    phase_transition_group = def_build_phase_transition_matrix(group_aggregate)

    quality_report = def_validate_pipeline(
        canonical,
        company,
        group_mapping,
        industry_aggregate,
        group_aggregate,
        company_group_phase,
        config,
        capabilities,
    )

    tables: Dict[str, pd.DataFrame] = {
        "monthly_revenue_company": company,
        "monthly_revenue_company_group_phase": company_group_phase,
        "monthly_revenue_industry": industry_aggregate,
        "monthly_revenue_group": group_aggregate,
        "monthly_revenue_industry_group_bridge": industry_group_bridge,
        "monthly_revenue_cross_industry": cross_industry,
        "monthly_revenue_cross_group": cross_group,
        "monthly_revenue_lead_lag_industry": lead_lag_industry,
        "monthly_revenue_lead_lag_group": lead_lag_group,
        "monthly_revenue_phase_transition_industry": phase_transition_industry,
        "monthly_revenue_phase_transition_group": phase_transition_group,
    }

    backup_manifest: Dict[str, Any] = {"backup_created": False, "files": []}
    output_records: List[Dict[str, Any]] = []
    duckdb_record: Dict[str, Any] = {"status": "NOT_WRITTEN"}
    sqlite_record: Dict[str, Any] = {"status": "NOT_WRITTEN"}

    if write_outputs:
        backup_manifest = def_backup_existing_outputs(config, logger)
        key_to_table = {
            "company": company,
            "company_group_phase": company_group_phase,
            "industry": industry_aggregate,
            "group": group_aggregate,
            "industry_group_bridge": industry_group_bridge,
            "cross_industry": cross_industry,
            "cross_group": cross_group,
            "lead_lag_industry": lead_lag_industry,
            "lead_lag_group": lead_lag_group,
            "phase_transition_industry": phase_transition_industry,
            "phase_transition_group": phase_transition_group,
        }
        for key, dataframe in key_to_table.items():
            output_records.append(
                def_write_dataframe_bundle(
                    dataframe,
                    OUTPUT_BASENAMES[key],
                    config,
                    capabilities,
                )
            )
        duckdb_record = def_write_duckdb(tables, config, capabilities)
        sqlite_record = def_write_sqlite_fallback(tables, config)
        quality_path = config.output_dir / OUTPUT_BASENAMES["quality_report"]
        def_atomic_write_json(quality_report, quality_path)

    elapsed_seconds = round(time.perf_counter() - started_at, 6)
    manifest = {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "build_date": ENGINE_BUILD_DATE,
        "contract": ENGINE_CONTRACT,
        "run_id": config.run_id,
        "started_at": def_utc_now_iso(),
        "elapsed_seconds": elapsed_seconds,
        "config": asdict(config),
        "capabilities": capabilities,
        "sources": source_manifest,
        "classification": classification_manifest,
        "backup": backup_manifest,
        "quality": quality_report,
        "outputs": output_records,
        "duckdb": duckdb_record,
        "sqlite_fallback": sqlite_record,
    }
    if write_outputs:
        manifest_path = config.output_dir / OUTPUT_BASENAMES["run_manifest"]
        def_atomic_write_json(manifest, manifest_path)
        manifest["manifest_path"] = str(manifest_path)
        manifest["manifest_sha256"] = def_sha256_file(manifest_path)

    logger.info(
        "Completed · status=%s · company=%s · industry=%s · group=%s · %.3fs",
        quality_report["overall_status"],
        len(company),
        len(industry_aggregate),
        len(group_aggregate),
        elapsed_seconds,
    )
    return {
        "manifest": manifest,
        "quality_report": quality_report,
        "tables": tables,
        "group_mapping": group_mapping,
        "canonical": canonical,
        "industry_fact": industry_fact,
        "group_fact": group_fact,
    }


# =============================================================================
# 12. SELF-TEST DATA GENERATOR
# =============================================================================


def def_generate_self_test_data(
    periods: int = 36,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(20260827)
    monthly_periods = pd.date_range("2023-01-01", periods=periods, freq="MS")
    companies = [
        ("1101", "Alpha Cement", "TWSE", "建材營造", "Traditional"),
        ("1102", "Beta Cement", "TWSE", "建材營造", "Traditional"),
        ("2301", "Alpha Electronics", "TWSE", "電子零組件", "AI Infrastructure"),
        ("2302", "Beta Electronics", "TWSE", "電子零組件", "AI Infrastructure"),
        ("2330", "Gamma Semiconductor", "TWSE", "半導體", "AI Semiconductor"),
        ("2454", "Delta IC", "TWSE", "半導體", "AI Semiconductor"),
        ("2603", "Alpha Shipping", "TWSE", "航運業", "Container Shipping"),
        ("2609", "Beta Shipping", "TWSE", "航運業", "Container Shipping"),
        ("5903", "Alpha Retail", "TPEX", "居家生活", "Domestic Consumption"),
        ("5904", "Beta Retail", "TPEX", "居家生活", "Domestic Consumption"),
        ("8069", "Alpha Network", "TPEX", "通信網路", "AI Infrastructure"),
        ("8086", "Beta Network", "TPEX", "通信網路", "AI Infrastructure"),
    ]
    rows: List[Dict[str, Any]] = []
    for company_index, (ticker, name, market, industry, theme) in enumerate(companies):
        base = 800.0 + company_index * 90.0
        for period_index, period in enumerate(monthly_periods):
            seasonal = 1.0 + 0.08 * np.sin(2 * np.pi * period.month / 12.0)
            if theme in ("AI Infrastructure", "AI Semiconductor"):
                trend = 1.0 + 0.012 * period_index + 0.0009 * period_index**2
            elif theme == "Container Shipping":
                trend = 1.0 + 0.020 * min(period_index, 12) - 0.012 * max(period_index - 12, 0)
            elif theme == "Domestic Consumption":
                trend = 0.92 + 0.006 * period_index + 0.0010 * max(period_index - 18, 0) ** 2
            else:
                trend = 1.0 - 0.004 * period_index
            noise = rng.normal(0.0, 0.015)
            revenue = max(20.0, base * seasonal * trend * (1.0 + noise))
            rows.append(
                {
                    "資料年月": period.strftime("%Y%m"),
                    "公司代號": ticker,
                    "公司名稱": name,
                    "市場別": market,
                    "產業別": industry,
                    "營業收入-當月營收": round(revenue, 3),
                    "營業收入-上月營收": np.nan,
                    "營業收入-去年當月營收": np.nan,
                    "營業收入-上月比較增減(%)": np.nan,
                    "營業收入-去年同月增減(%)": np.nan,
                    "累計營業收入-當月累計營收": np.nan,
                    "累計營業收入-去年累計營收": np.nan,
                    "累計營業收入-前期比較增減(%)": np.nan,
                    "備註": "SELF_TEST",
                    "source": "SELF_TEST_GENERATOR",
                    "fetched_at": "2026-08-27T00:00:00+00:00",
                }
            )
    monthly = pd.DataFrame(rows)
    duplicate = monthly.iloc[[-1]].copy()
    duplicate["營業收入-當月營收"] = duplicate["營業收入-當月營收"] * 0.99
    duplicate["source"] = "LOW_PRIORITY_DUPLICATE"
    monthly = pd.concat([duplicate, monthly], ignore_index=True)

    company_master = pd.DataFrame(
        [
            {
                "Ticker": ticker,
                "Name": name,
                "Market": market,
                "Industry": industry,
                "Sector": "Technology" if "電子" in industry or "半導體" in industry or "通信" in industry else "Non-Tech",
                "SubIndustry": industry,
            }
            for ticker, name, market, industry, _ in companies
        ]
    )

    group_rows: List[Dict[str, Any]] = []
    for ticker, _, _, industry, theme in companies:
        if ticker in {"2301", "2302", "8069", "8086"}:
            groups = ["AI Infrastructure", "Electronics Supply Chain"]
            weights = [0.70, 0.30]
        elif ticker in {"2330", "2454"}:
            groups = ["AI Semiconductor", "Electronics Supply Chain"]
            weights = [0.80, 0.20]
        else:
            groups = [theme]
            weights = [1.0]
        for index, (group_name, weight) in enumerate(zip(groups, weights)):
            group_rows.append(
                {
                    "Ticker": ticker,
                    "Group": group_name,
                    "GroupWeight": weight,
                    "IsPrimaryGroup": index == 0,
                    "ClassificationVersion": "SELF_TEST_V1",
                    "ClassificationSource": "SELF_TEST_SSOT",
                }
            )
    group_mapping = pd.DataFrame(group_rows)
    return monthly, company_master, group_mapping


def def_run_self_test(output_dir: Path) -> Dict[str, Any]:
    monthly, company_master, group_mapping = def_generate_self_test_data()
    config = EngineConfig(
        output_dir=output_dir,
        report_dir=output_dir,
        backup_dir=output_dir / "_backup",
        fetch_latest=False,
        incremental_update=True,
        require_parquet=False,
        require_duckdb=False,
        write_csv=True,
        write_parquet=True,
        write_duckdb=True,
        write_sqlite_fallback=True,
        backup_before_write=True,
        fail_on_duplicate_keys=True,
        fail_on_invalid_period=True,
        fail_on_empty_result=True,
        start_period=None,
        end_period=None,
        log_level="INFO",
        run_id=f"SELFTEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    )
    result = def_run_engine(
        config,
        injected_monthly_revenue=monthly,
        injected_company_master=company_master,
        injected_group_mapping=group_mapping,
        write_outputs=True,
    )

    company = result["tables"]["monthly_revenue_company"]
    industry = result["tables"]["monthly_revenue_industry"]
    group = result["tables"]["monthly_revenue_group"]
    company_group = result["tables"]["monthly_revenue_company_group_phase"]
    cross_group = result["tables"]["monthly_revenue_cross_group"]
    lead_lag_group = result["tables"]["monthly_revenue_lead_lag_group"]
    group_mapping_result = result["group_mapping"]

    assertions: List[Dict[str, Any]] = []

    def def_assert(test_id: str, condition: bool, message: str) -> None:
        assertions.append(
            {
                "test_id": test_id,
                "status": "PASS" if bool(condition) else "FAIL",
                "message": message,
            }
        )
        if not condition:
            raise AssertionError(f"{test_id}: {message}")

    def_assert(
        "T01_CANONICAL_UNIQUE",
        not company.duplicated(["period", "ticker", "market"]).any(),
        "Company canonical keys are unique after idempotent merge.",
    )
    def_assert(
        "T02_COMPANY_METRICS",
        {
            "mom_pct",
            "yoy_pct",
            "yoy_acceleration_1m_pp",
            "company_phase",
            "new_high_12m",
        }.issubset(company.columns),
        "Company metrics and phase columns exist.",
    )
    def_assert(
        "T03_INDUSTRY_ANALYTICS",
        not industry.empty and industry["dimension_type"].eq("INDUSTRY").all(),
        "Industry aggregation exists.",
    )
    def_assert(
        "T04_GROUP_ANALYTICS",
        not group.empty and group["dimension_type"].eq("GROUP").all(),
        "Group aggregation exists.",
    )
    def_assert(
        "T05_COMPANY_GROUP_PHASE",
        not company_group.empty
        and {
            "company_phase",
            "group_phase",
            "company_relative_to_group",
            "phase_alignment",
        }.issubset(company_group.columns),
        "Company-by-group-by-phase output exists.",
    )
    def_assert(
        "T06_GROUP_WEIGHT_RECONCILIATION",
        bool(
            np.allclose(
                group_mapping_result.groupby("ticker")["group_weight"].sum().to_numpy(),
                1.0,
                atol=1e-9,
            )
        ),
        "Multi-group weights sum to one for every ticker.",
    )
    def_assert(
        "T07_GROUP_TOTAL_RECONCILIATION",
        result["quality_report"]["checks"][6]["status"] == "PASS",
        "Weighted group total reconciles to company total.",
    )
    def_assert(
        "T08_CROSS_GROUP_MATRIX",
        not cross_group.empty and "dominant_dimension" in cross_group.columns,
        "Cross-group pairwise matrix exists.",
    )
    def_assert(
        "T09_LEAD_LAG",
        not lead_lag_group.empty and "lag_months_a_leads_b" in lead_lag_group.columns,
        "Lead-lag matrix exists with sufficient history.",
    )
    latest_group = group.loc[group["period"].eq(group["period"].max())]
    def_assert(
        "T10_DYNAMIC_PHASE",
        latest_group["phase"].nunique() >= 2,
        "Synthetic groups produce at least two distinct phases.",
    )
    def_assert(
        "T11_CSV_OUTPUT",
        (output_dir / f"{OUTPUT_BASENAMES['company']}.csv").exists(),
        "CSV output is written.",
    )
    def_assert(
        "T12_SQLITE_FALLBACK",
        (output_dir / OUTPUT_BASENAMES["sqlite_fallback"]).exists(),
        "SQLite fallback is written when enabled.",
    )

    test_report = {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "run_id": config.run_id,
        "generated_at": def_utc_now_iso(),
        "overall_status": (
            "PASS" if all(item["status"] == "PASS" for item in assertions) else "FAIL"
        ),
        "assertions": assertions,
        "quality_report": result["quality_report"],
        "latest_group_snapshot": latest_group[
            [
                "dimension",
                "yoy_pct",
                "yoy_acceleration_1m_pp",
                "positive_yoy_breadth",
                "rotation_score",
                "phase",
                "rotation_state",
            ]
        ].sort_values("rotation_score", ascending=False).to_dict(orient="records"),
    }
    test_report_path = output_dir / "VDF_TW_MonthlyRevenue_CrossGroupPhase_SelfTest_v030.json"
    def_atomic_write_json(test_report, test_report_path)
    return test_report


# =============================================================================
# 13. COMMAND-LINE ENTRY POINT
# =============================================================================


def def_build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "VDF 台股月營收公司別、產業別、族群別、跨群比較與動態 Phase 分析引擎"
        )
    )
    parser.add_argument("--input", type=Path, default=None, help="既有月營收 Parquet/CSV")
    parser.add_argument("--company-master", type=Path, default=None, help="公司主檔")
    parser.add_argument("--group-map", type=Path, default=None, help="多族群 SSOT")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--start-period", type=str, default=DEFAULT_START_PERIOD)
    parser.add_argument("--end-period", type=str, default=DEFAULT_END_PERIOD)
    parser.add_argument(
        "--fetch-latest",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_FETCH_LATEST,
    )
    parser.add_argument(
        "--incremental",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_INCREMENTAL_UPDATE,
    )
    parser.add_argument(
        "--require-parquet",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_REQUIRE_PARQUET,
    )
    parser.add_argument(
        "--require-duckdb",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_REQUIRE_DUCKDB,
    )
    parser.add_argument(
        "--write-parquet",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_WRITE_PARQUET,
    )
    parser.add_argument(
        "--write-duckdb",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_WRITE_DUCKDB,
    )
    parser.add_argument(
        "--write-sqlite-fallback",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_WRITE_SQLITE_FALLBACK,
    )
    parser.add_argument(
        "--backup-before-write",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_BACKUP_BEFORE_WRITE,
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--log-level", default=DEFAULT_LOG_LEVEL)
    return parser


def def_main(argv: Optional[Sequence[str]] = None) -> int:
    parser = def_build_argument_parser()
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            report = def_run_self_test(args.output_dir)
            print(json.dumps(report, ensure_ascii=False, indent=2, default=def_json_default))
            return 0 if report["overall_status"] == "PASS" else 2

        config = EngineConfig(
            output_dir=args.output_dir,
            report_dir=args.output_dir,
            input_path=args.input,
            company_master_path=args.company_master,
            group_map_path=args.group_map,
            start_period=args.start_period,
            end_period=args.end_period,
            fetch_latest=args.fetch_latest,
            incremental_update=args.incremental,
            require_parquet=args.require_parquet,
            require_duckdb=args.require_duckdb,
            write_parquet=args.write_parquet,
            write_duckdb=args.write_duckdb,
            write_sqlite_fallback=args.write_sqlite_fallback,
            backup_before_write=args.backup_before_write,
            log_level=args.log_level,
        )
        result = def_run_engine(config)
        print(
            json.dumps(
                {
                    "status": result["quality_report"]["overall_status"],
                    "manifest": result["manifest"].get("manifest_path"),
                    "rows": result["quality_report"]["rows"],
                },
                ensure_ascii=False,
                indent=2,
                default=def_json_default,
            )
        )
        return 0 if result["quality_report"]["overall_status"] != "FAIL" else 2
    except Exception as exc:
        failure = {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "status": "FAIL_CLOSED",
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        print(json.dumps(failure, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(def_main())

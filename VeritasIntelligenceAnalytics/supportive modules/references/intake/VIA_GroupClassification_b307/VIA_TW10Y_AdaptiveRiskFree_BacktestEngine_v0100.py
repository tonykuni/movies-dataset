from __future__ import annotations

"""
VIA 台灣 10 年期公債無風險利率、族群驗證與自適應回測引擎 v0.2.0

主要功能
1. 從證券櫃檯買賣中心（TPEx）官方月索引增量取得每日殖利率曲線 XLS。
2. 以 10 年期含息殖利率為主；缺值時才降級採同一官方檔的 10Y 零息利率。
3. 對齊股票交易日，只允許向後帶入已知利率，絕不從未來回填。
4. 以實際日期密度動態估計年化交易日數，固定 252 僅作安全備援。
5. 產生 60／120／240 日 Walk-forward 報酬、波動、Sharpe、Sortino 與回撤。
6. 原始檔 append-only；同名官方檔若內容改變，保留 revision，不靜默覆寫。
7. 以台股全市場（排除台積電）作市場因子，先殘差化再驗證族群。
8. 以 leave-one-out 族群報酬、同規模隨機群與區塊置換檢定，分成
   LEAD／PEER／LAG／UNRELATED；不使用綜合 Score。
9. 以全市場（排除台積電）市值做動態三群聚，標示 LARGE／MID／SMALL。

必要套件：numpy、pandas、xlrd
Parquet 輸出：pyarrow 或 fastparquet（二擇一）
"""

# ============================================================================
# 0. 所有可調參數集中於頂部
# ============================================================================

ENGINE_NAME = "VIA_TW10Y_AdaptiveRiskFree_BacktestEngine"
ENGINE_VERSION = "0.2.0"

TPEx_PAGE_URL = "https://www.tpex.org.tw/zh-tw/bond/info/statistics-gb/day/yield.html"
TPEx_MONTH_API_URL = "https://www.tpex.org.tw/www/zh-tw/bond/govDaily2"
TPEx_ORIGIN = "https://www.tpex.org.tw"
TPEx_FILE_CODE = "Curve"
TPEx_USER_AGENT = "VIA-TW10Y-RiskFree/0.2 (+official-public-data)"

DEFAULT_START_DATE = "2023-01-01"
DEFAULT_END_DATE = None
DEFAULT_OUTPUT_DIR = "VIA_TW10Y_Output"
DEFAULT_RISK_FREE_STEM = "tw_10y_risk_free"
DEFAULT_BACKTEST_STEM = "tw_10y_adaptive_backtest"
DEFAULT_GROUP_DETAIL_STEM = "tw_group_validation_roles"
DEFAULT_GROUP_SUMMARY_STEM = "tw_group_validation_groups"
DEFAULT_GROUP_BACKTEST_STEM = "tw_group_validation_backtest"

ROLLING_WINDOWS = (60, 120, 240)
VALIDATION_PERIOD_STARTS = {
    "2024": "2024-01-01",
    "2025": "2025-01-01",
    "2026": "2026-01-01",
}
TENOR_YEARS = 10.0
TENOR_LABEL_PATTERN = r"^\s*10\s*年"

DATE_COLUMN = "Date"
TICKER_COLUMN = "Ticker"
GROUP_COLUMN = "Group"
ADJUSTED_CLOSE_COLUMN = "Adj Close"
MARKET_CAP_COLUMN = "MarketCap"
EXCHANGE_COLUMN = "Exchange"
TSMC_TICKER_PATTERN = r"^2330(?:\.|$)"

# 固定值只界定檢定家族、可辨識範圍與數值運算；分類門檻來自滾動樣本／虛無分布。
VALIDATION_FDR_ALPHA = 0.05
DEFAULT_PERMUTATION_REPETITIONS = 199
MAX_CCF_LAG_DAYS = 5
FORWARD_VALIDATION_HORIZONS = (1, 3, 5)
MIN_GROUP_MEMBERS = 3
DEFAULT_EVALUATION_STEP = 1
SIZE_CLUSTER_MAX_ITERATIONS = 100
REQUIRE_TWSE_TPEX_COVERAGE = True

REQUEST_TIMEOUT_SECONDS = 30
REQUEST_RETRIES = 3
REQUEST_BACKOFF_SECONDS = 1.0
REQUEST_DELAY_SECONDS = 0.10

CSV_ENCODING = "utf-8-sig"
FALLBACK_TRADING_DAYS_PER_YEAR = 252.0
MIN_ANNUALIZATION_SAFETY = 200.0
MAX_ANNUALIZATION_SAFETY = 280.0
MIN_STALE_CALENDAR_DAYS = 3
MAX_STALE_CALENDAR_DAYS = 10
MIN_VALID_YIELD_PCT = -5.0
MAX_VALID_YIELD_PCT = 25.0

DEFAULT_RETURN_COLUMNS = ("strategy_return",)
FLOAT_EPSILON = 1e-12


# ============================================================================
# 1. 標準函式庫與第三方套件
# ============================================================================

import argparse
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd


# ============================================================================
# 2. 共用工具：日期、雜湊、稽核與安全寫檔
# ============================================================================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_date(value: Any) -> pd.Timestamp:
    parsed = pd.Timestamp(value)
    if parsed.tzinfo is not None:
        parsed = parsed.tz_convert("Asia/Taipei").tz_localize(None)
    return parsed.normalize()


def month_starts(start_date: Any, end_date: Any) -> list[pd.Timestamp]:
    start = normalize_date(start_date).replace(day=1)
    end = normalize_date(end_date).replace(day=1)
    return list(pd.date_range(start, end, freq="MS"))


def append_hash_chained_audit(audit_path: Path, event: dict[str, Any]) -> str:
    ensure_directory(audit_path.parent)
    previous_hash = "GENESIS"
    if audit_path.exists() and audit_path.stat().st_size:
        with audit_path.open("rb") as handle:
            lines = [line for line in handle.read().splitlines() if line.strip()]
        if lines:
            previous_hash = json.loads(lines[-1].decode("utf-8"))["event_hash"]

    material = dict(event)
    material["engine"] = ENGINE_NAME
    material["engine_version"] = ENGINE_VERSION
    material["event_time_utc"] = utc_now_iso()
    material["previous_event_hash"] = previous_hash
    event_hash = sha256_bytes(canonical_json_bytes(material))
    material["event_hash"] = event_hash

    with audit_path.open("ab") as handle:
        handle.write(canonical_json_bytes(material) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    return event_hash


def atomic_replace_bytes(path: Path, content: bytes) -> None:
    ensure_directory(path.parent)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary_path = Path(handle.name)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary_path, path)


def preserve_previous_version(path: Path, versions_dir: Path) -> Path | None:
    if not path.exists():
        return None
    digest = sha256_bytes(path.read_bytes())[:16]
    backup = ensure_directory(versions_dir) / f"{path.name}.{digest}.bak"
    if not backup.exists():
        shutil.copy2(path, backup)
    return backup


def write_append_only_raw(
    target_path: Path,
    content: bytes,
    audit_path: Path,
    source_url: str,
) -> tuple[Path, str, str]:
    digest = sha256_bytes(content)
    ensure_directory(target_path.parent)

    if not target_path.exists():
        atomic_replace_bytes(target_path, content)
        action = "RAW_CREATED"
        actual_path = target_path
    else:
        existing_digest = sha256_bytes(target_path.read_bytes())
        if existing_digest == digest:
            action = "RAW_IDENTICAL_SKIP"
            actual_path = target_path
        else:
            actual_path = target_path.with_name(
                f"{target_path.stem}.REV-{digest[:16]}{target_path.suffix}"
            )
            if not actual_path.exists():
                atomic_replace_bytes(actual_path, content)
            action = "RAW_SOURCE_REVISION"

    append_hash_chained_audit(
        audit_path,
        {
            "event_type": action,
            "source_url": source_url,
            "raw_path": str(actual_path),
            "raw_sha256": digest,
        },
    )
    return actual_path, digest, action


# ============================================================================
# 3. 官方 TPEx 擷取層
# ============================================================================

def http_request_bytes(
    url: str,
    form_data: dict[str, Any] | None = None,
    retries: int = REQUEST_RETRIES,
) -> bytes:
    if not url.startswith(TPEx_ORIGIN):
        raise ValueError(f"拒絕非 TPEx 網域：{url}")

    encoded = None
    if form_data is not None:
        encoded = urllib.parse.urlencode(form_data).encode("utf-8")

    headers = {
        "User-Agent": TPEx_USER_AGENT,
        "Accept": "application/json,text/html,application/vnd.ms-excel,*/*",
        "Referer": TPEx_PAGE_URL,
    }
    last_error: Exception | None = None

    for attempt in range(max(1, retries)):
        try:
            request = urllib.request.Request(
                url=url,
                data=encoded,
                headers=headers,
                method="POST" if encoded is not None else "GET",
            )
            with urllib.request.urlopen(
                request,
                timeout=REQUEST_TIMEOUT_SECONDS,
            ) as response:
                content = response.read()
            if not content:
                raise RuntimeError("TPEx 回傳空內容")
            return content
        except Exception as exc:  # noqa: BLE001 - 需要保留最後一個網路錯誤
            last_error = exc
            if attempt + 1 < max(1, retries):
                time.sleep(REQUEST_BACKOFF_SECONDS * (2**attempt))

    raise RuntimeError(f"TPEx 下載失敗：{url}；{last_error}") from last_error


def fetch_tpex_month_file_list(month: Any) -> list[dict[str, Any]]:
    month_ts = normalize_date(month).replace(day=1)
    content = http_request_bytes(
        TPEx_MONTH_API_URL,
        {
            "date": month_ts.strftime("%Y/%m/01"),
            "fileCode": TPEx_FILE_CODE,
            "response": "json",
        },
    )
    payload = json.loads(content.decode("utf-8"))
    if payload.get("stat") != "ok":
        raise RuntimeError(f"TPEx 月索引錯誤：{payload.get('stat', 'unknown')}")

    tables = payload.get("tables") or []
    rows = tables[0].get("data", []) if tables else []
    result: list[dict[str, Any]] = []

    for row in rows:
        if len(row) < 2:
            continue
        relative_path = str(row[1]).strip()
        match = re.search(r"Curve\.(\d{8})-C\.xls$", relative_path, re.IGNORECASE)
        if not match:
            continue
        source_date = pd.Timestamp(datetime.strptime(match.group(1), "%Y%m%d"))
        absolute_url = urllib.parse.urljoin(TPEx_ORIGIN, relative_path)
        if urllib.parse.urlparse(absolute_url).netloc != "www.tpex.org.tw":
            raise ValueError(f"TPEx 月索引包含非預期網域：{absolute_url}")
        result.append(
            {
                "date": source_date,
                "url": absolute_url,
                "filename": Path(relative_path).name,
            }
        )
    return result


def find_ten_year_row(frame: pd.DataFrame) -> pd.Series:
    if frame.empty:
        raise ValueError("含息殖利率工作表為空")

    tenor_column = None
    for column in frame.columns:
        sample = frame[column].astype(str)
        if sample.str.contains(r"年|Year", regex=True, na=False).any():
            tenor_column = column
            break
    if tenor_column is None and len(frame.columns) >= 2:
        tenor_column = frame.columns[1]
    if tenor_column is None:
        raise ValueError("找不到 Tenor 欄")

    mask = frame[tenor_column].astype(str).str.contains(
        TENOR_LABEL_PATTERN,
        regex=True,
        na=False,
    )
    matches = frame.loc[mask]
    if matches.empty:
        raise ValueError("找不到 10 年期公債列")
    return matches.iloc[0]


def find_yield_date_column(columns: Iterable[Any]) -> Any:
    for column in columns:
        if isinstance(column, (pd.Timestamp, datetime, date, np.datetime64)):
            return column
        try:
            parsed = pd.to_datetime(str(column), errors="raise")
            if 1990 <= parsed.year <= 2200:
                return column
        except Exception:  # noqa: BLE001 - 欄名型態不一
            continue
    raise ValueError("找不到殖利率日期欄")


def parse_numeric_tenor(value: Any) -> float | None:
    text = str(value).strip().lower()
    aliases = {"1m": 1 / 12, "3m": 0.25, "6m": 0.5}
    if text in aliases:
        return aliases[text]
    try:
        return float(text)
    except ValueError:
        return None


def parse_zcyc_ten_year(frame: pd.DataFrame) -> tuple[float | None, float | None]:
    if frame.empty:
        return None, None
    for _, row in frame.iterrows():
        tenor = parse_numeric_tenor(row.iloc[0] if len(row) else None)
        if tenor is None or not math.isclose(tenor, TENOR_YEARS, abs_tol=1e-9):
            continue
        bspline = pd.to_numeric(row.iloc[1], errors="coerce") if len(row) > 1 else np.nan
        svensson = pd.to_numeric(row.iloc[3], errors="coerce") if len(row) > 3 else np.nan
        bspline_pct = float(bspline) * 100.0 if pd.notna(bspline) else None
        svensson_pct = float(svensson) * 100.0 if pd.notna(svensson) else None
        return bspline_pct, svensson_pct
    return None, None


def validate_yield_value(value: float | None, field_name: str) -> float | None:
    if value is None or pd.isna(value):
        return None
    numeric = float(value)
    if not MIN_VALID_YIELD_PCT <= numeric <= MAX_VALID_YIELD_PCT:
        raise ValueError(f"{field_name} 超出安全範圍：{numeric}")
    return numeric


def parse_tpex_curve_xls(
    content: bytes,
    source_url: str,
    raw_sha256: str,
) -> dict[str, Any]:
    workbook = pd.ExcelFile(io.BytesIO(content), engine="xlrd")
    if not workbook.sheet_names:
        raise ValueError("TPEx XLS 沒有工作表")

    par_frame = pd.read_excel(
        io.BytesIO(content),
        sheet_name=workbook.sheet_names[0],
        header=0,
        engine="xlrd",
    )
    ten_year_row = find_ten_year_row(par_frame)
    yield_column = find_yield_date_column(par_frame.columns)
    source_date = normalize_date(yield_column)
    par_yield_pct = validate_yield_value(
        pd.to_numeric(ten_year_row[yield_column], errors="coerce"),
        "10Y 含息殖利率",
    )

    residual_year = None
    if len(ten_year_row) >= 4:
        residual_candidate = pd.to_numeric(ten_year_row.iloc[3], errors="coerce")
        if pd.notna(residual_candidate):
            residual_year = float(residual_candidate)

    zcyc_bspline_pct = None
    zcyc_svensson_pct = None
    for sheet_name in workbook.sheet_names:
        if "ZCYC Data" in sheet_name or "資料" in sheet_name:
            zcyc_frame = pd.read_excel(
                io.BytesIO(content),
                sheet_name=sheet_name,
                header=None,
                engine="xlrd",
            )
            zcyc_bspline_pct, zcyc_svensson_pct = parse_zcyc_ten_year(zcyc_frame)
            break

    zcyc_bspline_pct = validate_yield_value(zcyc_bspline_pct, "10Y B-Spline 零息利率")
    zcyc_svensson_pct = validate_yield_value(zcyc_svensson_pct, "10Y Svensson 零息利率")

    if par_yield_pct is not None:
        yield_used_pct = par_yield_pct
        yield_method = "TPEX_PAR_10Y"
        source_grade = "MEASURED"
    elif zcyc_bspline_pct is not None:
        yield_used_pct = zcyc_bspline_pct
        yield_method = "TPEX_ZCYC_BSPLINE_10Y_FALLBACK"
        source_grade = "OFFICIAL_MODEL_FALLBACK"
    elif zcyc_svensson_pct is not None:
        yield_used_pct = zcyc_svensson_pct
        yield_method = "TPEX_ZCYC_SVENSSON_10Y_FALLBACK"
        source_grade = "OFFICIAL_MODEL_FALLBACK"
    else:
        raise ValueError("TPEx XLS 不含可用的 10Y 殖利率")

    return {
        "Date": source_date,
        "tw10y_par_yield_pct": par_yield_pct,
        "tw10y_residual_year": residual_year,
        "tw10y_zcyc_bspline_pct": zcyc_bspline_pct,
        "tw10y_zcyc_svensson_pct": zcyc_svensson_pct,
        "yield_used_pct": yield_used_pct,
        "yield_method": yield_method,
        "source_grade": source_grade,
        "source_name": "Taipei Exchange (TPEx)",
        "source_page": TPEx_PAGE_URL,
        "source_url": source_url,
        "raw_sha256": raw_sha256,
        "retrieved_at_utc": utc_now_iso(),
    }


# ============================================================================
# 4. 自適應品質層：不竄改原值，只標記結構性異常
# ============================================================================

def rolling_tukey_upper_fence(series: pd.Series, window: int) -> pd.Series:
    minimum = max(5, int(math.sqrt(window)))
    q1 = series.rolling(window, min_periods=minimum).quantile(0.25)
    q3 = series.rolling(window, min_periods=minimum).quantile(0.75)
    return q3 + 1.5 * (q3 - q1)


def add_adaptive_yield_quality(
    frame: pd.DataFrame,
    windows: Sequence[int] = ROLLING_WINDOWS,
) -> pd.DataFrame:
    result = frame.copy().sort_values("Date").reset_index(drop=True)
    result["yield_change_bps"] = result["yield_used_pct"].diff() * 100.0
    absolute_change = result["yield_change_bps"].abs()

    regime_columns: list[str] = []
    for window in windows:
        fence_column = f"change_fence_bps_{window}d"
        regime_column = f"yield_regime_{window}d"
        result[fence_column] = rolling_tukey_upper_fence(absolute_change, int(window))
        result[regime_column] = np.where(
            result[fence_column].notna() & (absolute_change > result[fence_column]),
            "STRUCTURAL_MOVE",
            "TYPICAL",
        )
        regime_columns.append(regime_column)

    zcyc_reference = result["tw10y_zcyc_bspline_pct"].combine_first(
        result["tw10y_zcyc_svensson_pct"]
    )
    result["par_zcyc_gap_bps"] = (
        result["tw10y_par_yield_pct"] - zcyc_reference
    ).abs() * 100.0

    result["quality_state"] = "OK"
    fallback_mask = result["yield_method"].str.contains("FALLBACK", na=False)
    result.loc[fallback_mask, "quality_state"] = "OFFICIAL_MODEL_FALLBACK"

    structural_mask = pd.Series(False, index=result.index)
    for column in regime_columns:
        structural_mask |= result[column].eq("STRUCTURAL_MOVE")
    result.loc[structural_mask, "quality_state"] = "REVIEW_STRUCTURAL_MOVE"
    return result


def infer_dynamic_stale_limit(yield_dates: pd.Series) -> int:
    dates = pd.to_datetime(yield_dates, errors="coerce").dropna().drop_duplicates().sort_values()
    gaps = dates.diff().dt.days.dropna()
    if gaps.empty:
        return MIN_STALE_CALENDAR_DAYS

    q1 = gaps.quantile(0.25)
    q3 = gaps.quantile(0.75)
    upper_fence = q3 + 1.5 * (q3 - q1)
    normal_gaps = gaps[gaps <= upper_fence]
    inferred = int(math.ceil(normal_gaps.max())) if not normal_gaps.empty else MIN_STALE_CALENDAR_DAYS
    return int(np.clip(inferred, MIN_STALE_CALENDAR_DAYS, MAX_STALE_CALENDAR_DAYS))


def infer_trading_days_per_year(trading_dates: pd.Series) -> tuple[float, str]:
    dates = pd.to_datetime(trading_dates, errors="coerce").dropna().drop_duplicates().sort_values()
    if len(dates) >= 2:
        span_years = max((dates.iloc[-1] - dates.iloc[0]).days / 365.2425, FLOAT_EPSILON)
        observed = len(dates) / span_years
        if MIN_ANNUALIZATION_SAFETY <= observed <= MAX_ANNUALIZATION_SAFETY:
            return float(observed), "OBSERVED_DATE_DENSITY"
    return FALLBACK_TRADING_DAYS_PER_YEAR, "FIXED_FALLBACK"


def annual_yield_to_daily_return(
    annual_yield_pct: pd.Series,
    annualization: float,
) -> pd.Series:
    annual_decimal = pd.to_numeric(annual_yield_pct, errors="coerce") / 100.0
    invalid = annual_decimal <= -1.0
    if invalid.any():
        raise ValueError("年化殖利率不可小於或等於 -100%")
    return np.expm1(np.log1p(annual_decimal) / float(annualization))


# ============================================================================
# 5. 增量整併與 CSV／Parquet 雙輸出
# ============================================================================

def parquet_engine_available() -> str | None:
    if importlib.util.find_spec("pyarrow") is not None:
        return "pyarrow"
    if importlib.util.find_spec("fastparquet") is not None:
        return "fastparquet"
    return None


def read_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    try:
        return pd.read_parquet(path)
    except Exception:
        return pd.read_csv(path, encoding=CSV_ENCODING)


def load_existing_risk_free(output_dir: Path, stem: str) -> pd.DataFrame:
    parquet_path = output_dir / stem
    csv_path = output_dir / f"{stem}_csv"
    if parquet_path.exists():
        try:
            return pd.read_parquet(parquet_path)
        except Exception:
            pass
    if csv_path.exists():
        return pd.read_csv(csv_path, encoding=CSV_ENCODING)
    return pd.DataFrame()


def dataframe_csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False, date_format="%Y/%m/%d").encode(CSV_ENCODING)


def write_dual_outputs(
    frame: pd.DataFrame,
    output_dir: Path,
    stem: str,
    audit_path: Path,
) -> dict[str, Any]:
    ensure_directory(output_dir)
    versions_dir = ensure_directory(output_dir / "versions")
    csv_path = output_dir / f"{stem}_csv"
    parquet_path = output_dir / stem

    csv_content = dataframe_csv_bytes(frame)
    proposed_csv_hash = sha256_bytes(csv_content)
    current_csv_hash = sha256_bytes(csv_path.read_bytes()) if csv_path.exists() else None

    if current_csv_hash == proposed_csv_hash:
        csv_action = "CANONICAL_IDENTICAL_SKIP"
    else:
        preserve_previous_version(csv_path, versions_dir)
        atomic_replace_bytes(csv_path, csv_content)
        csv_action = "CANONICAL_APPLY"

    engine = parquet_engine_available()
    parquet_status = "SKIPPED_NO_ENGINE"
    if engine is not None:
        preserve_previous_version(parquet_path, versions_dir)
        temporary = output_dir / f".{stem}.{os.getpid()}.tmp"
        try:
            frame.to_parquet(temporary, index=False, engine=engine)
            os.replace(temporary, parquet_path)
            parquet_status = f"WRITTEN_{engine.upper()}"
        finally:
            if temporary.exists():
                temporary.unlink()

    append_hash_chained_audit(
        audit_path,
        {
            "event_type": "DUAL_OUTPUT",
            "rows": int(len(frame)),
            "csv_path": str(csv_path),
            "csv_sha256": proposed_csv_hash,
            "csv_action": csv_action,
            "parquet_path": str(parquet_path),
            "parquet_status": parquet_status,
        },
    )
    return {
        "csv_path": str(csv_path),
        "csv_action": csv_action,
        "parquet_path": str(parquet_path),
        "parquet_status": parquet_status,
        "rows": int(len(frame)),
    }


def merge_incremental_history(existing: pd.DataFrame, new_rows: pd.DataFrame) -> pd.DataFrame:
    frames = [frame for frame in (existing, new_rows) if not frame.empty]
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce").dt.normalize()
    combined = combined.dropna(subset=["Date", "yield_used_pct"])
    combined = combined.sort_values(["Date", "retrieved_at_utc"], na_position="first")
    combined = combined.drop_duplicates(subset=["Date"], keep="last")
    return combined.sort_values("Date").reset_index(drop=True)


def fetch_tw10y_history(
    start_date: Any = DEFAULT_START_DATE,
    end_date: Any = DEFAULT_END_DATE,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    stem: str = DEFAULT_RISK_FREE_STEM,
    refresh_existing: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    start = normalize_date(start_date)
    end = normalize_date(end_date or pd.Timestamp.today())
    if start > end:
        raise ValueError("start_date 不可晚於 end_date")

    out_dir = ensure_directory(Path(output_dir).resolve())
    raw_dir = ensure_directory(out_dir / "raw_tpex_xls")
    audit_path = out_dir / "append_only_audit.jsonl"
    existing = load_existing_risk_free(out_dir, stem)
    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for month in month_starts(start, end):
        try:
            entries = fetch_tpex_month_file_list(month)
        except Exception as exc:  # noqa: BLE001 - 月份失敗需續跑
            failures.append({"month": month.strftime("%Y-%m"), "error": str(exc)})
            append_hash_chained_audit(
                audit_path,
                {
                    "event_type": "MONTH_INDEX_FAILED",
                    "month": month.strftime("%Y-%m"),
                    "error": str(exc),
                },
            )
            continue

        for entry in entries:
            source_date = normalize_date(entry["date"])
            if source_date < start or source_date > end:
                continue
            raw_path = raw_dir / source_date.strftime("%Y") / source_date.strftime("%m") / entry["filename"]
            try:
                if raw_path.exists() and not refresh_existing:
                    content = raw_path.read_bytes()
                    digest = sha256_bytes(content)
                    actual_path = raw_path
                else:
                    content = http_request_bytes(entry["url"])
                    actual_path, digest, _ = write_append_only_raw(
                        raw_path,
                        content,
                        audit_path,
                        entry["url"],
                    )
                record = parse_tpex_curve_xls(content, entry["url"], digest)
                record["raw_path"] = str(actual_path)
                records.append(record)
            except Exception as exc:  # noqa: BLE001 - 單日失敗不可中斷全批次
                failures.append({"date": source_date.strftime("%Y-%m-%d"), "error": str(exc)})
                append_hash_chained_audit(
                    audit_path,
                    {
                        "event_type": "DAILY_PARSE_FAILED",
                        "date": source_date.strftime("%Y-%m-%d"),
                        "source_url": entry["url"],
                        "error": str(exc),
                    },
                )
            time.sleep(REQUEST_DELAY_SECONDS)

    new_rows = pd.DataFrame(records)
    history = merge_incremental_history(existing, new_rows)
    if history.empty:
        raise RuntimeError("沒有取得可用的 TPEx 10Y 殖利率，且本機亦無快取")

    history = add_adaptive_yield_quality(history)
    output_status = write_dual_outputs(history, out_dir, stem, audit_path)
    status = {
        **output_status,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "latest_date": history["Date"].max().strftime("%Y-%m-%d"),
        "failure_count": len(failures),
        "failures": failures,
        "audit_path": str(audit_path),
        "source_page": TPEx_PAGE_URL,
    }
    return history, status


# ============================================================================
# 6. 股票交易日對齊：只向後帶入，不使用未來資料
# ============================================================================

def align_risk_free_to_trading_dates(
    trading_frame: pd.DataFrame,
    risk_free_frame: pd.DataFrame,
    date_column: str = DATE_COLUMN,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    left = trading_frame.copy()
    right = risk_free_frame.copy()
    left[date_column] = pd.to_datetime(left[date_column], errors="coerce").dt.normalize()
    right["Date"] = pd.to_datetime(right["Date"], errors="coerce").dt.normalize()
    left = left.dropna(subset=[date_column]).sort_values(date_column)
    right = right.dropna(subset=["Date", "yield_used_pct"]).sort_values("Date")

    stale_limit = infer_dynamic_stale_limit(right["Date"])
    annualization, annualization_method = infer_trading_days_per_year(left[date_column])
    right = right.rename(columns={"Date": "rf_source_date"})

    aligned = pd.merge_asof(
        left,
        right,
        left_on=date_column,
        right_on="rf_source_date",
        direction="backward",
        allow_exact_matches=True,
    )
    aligned["rf_age_calendar_days"] = (
        aligned[date_column] - aligned["rf_source_date"]
    ).dt.days
    aligned["rf_alignment_state"] = np.where(
        aligned["rf_source_date"].isna(),
        "MISSING",
        np.where(
            aligned["rf_age_calendar_days"] == 0,
            "EXACT",
            np.where(
                aligned["rf_age_calendar_days"] <= stale_limit,
                "CARRY_FORWARD_OFFICIAL",
                "STALE_BLOCKED",
            ),
        ),
    )
    blocked = aligned["rf_alignment_state"].isin(["MISSING", "STALE_BLOCKED"])
    aligned.loc[blocked, "yield_used_pct"] = np.nan
    aligned["annualization_factor"] = annualization
    aligned["annualization_method"] = annualization_method
    aligned["rf_daily_return"] = annual_yield_to_daily_return(
        aligned["yield_used_pct"],
        annualization,
    )

    status = {
        "stale_limit_calendar_days": stale_limit,
        "annualization_factor": annualization,
        "annualization_method": annualization_method,
        "blocked_rows": int(blocked.sum()),
    }
    return aligned, status


# ============================================================================
# 7. Walk-forward 回測值修正與動態指標
# ============================================================================

def add_excess_return_columns(
    aligned_frame: pd.DataFrame,
    return_columns: Sequence[str],
) -> pd.DataFrame:
    """提供分類／CAPM 殘差引擎可直接使用的動態超額報酬欄位。"""
    result = aligned_frame.copy()
    rf = pd.to_numeric(result["rf_daily_return"], errors="coerce")
    for return_column in return_columns:
        if return_column not in result.columns:
            raise KeyError(f"找不到報酬欄位：{return_column}")
        raw_return = pd.to_numeric(result[return_column], errors="coerce")
        if (raw_return <= -1.0).any():
            raise ValueError(f"{return_column} 含小於或等於 -100% 的報酬")
        result[f"{return_column}_excess_rf"] = raw_return - rf
    return result

def rolling_compounded_return(series: pd.Series, window: int) -> pd.Series:
    minimum = max(2, int(math.sqrt(window)))
    log_return = np.log1p(pd.to_numeric(series, errors="coerce"))
    return np.expm1(log_return.rolling(window, min_periods=minimum).sum())


def rolling_annualized_return(
    series: pd.Series,
    window: int,
    annualization: float,
) -> pd.Series:
    compounded = rolling_compounded_return(series, window)
    return np.expm1(np.log1p(compounded) * (annualization / float(window)))


def rolling_max_drawdown(series: pd.Series, window: int) -> pd.Series:
    minimum = max(2, int(math.sqrt(window)))

    def calculate(values: np.ndarray) -> float:
        wealth = np.cumprod(1.0 + values)
        peak = np.maximum.accumulate(wealth)
        drawdown = wealth / np.maximum(peak, FLOAT_EPSILON) - 1.0
        return float(np.nanmin(drawdown))

    return pd.to_numeric(series, errors="coerce").rolling(
        window,
        min_periods=minimum,
    ).apply(calculate, raw=True)


def add_walk_forward_metrics(
    aligned_frame: pd.DataFrame,
    return_columns: Sequence[str] = DEFAULT_RETURN_COLUMNS,
    windows: Sequence[int] = ROLLING_WINDOWS,
    date_column: str = DATE_COLUMN,
) -> pd.DataFrame:
    result = add_excess_return_columns(aligned_frame, return_columns)
    result = result.sort_values(date_column).reset_index(drop=True)
    if result.empty:
        return result

    annualization = float(result["annualization_factor"].dropna().iloc[-1])
    rf = pd.to_numeric(result["rf_daily_return"], errors="coerce")

    for return_column in return_columns:
        strategy_return = pd.to_numeric(result[return_column], errors="coerce")
        excess_column = f"{return_column}_excess_rf"

        for window in windows:
            window = int(window)
            minimum = max(2, int(math.sqrt(window)))
            excess = result[excess_column]
            excess_mean = excess.rolling(window, min_periods=minimum).mean()
            excess_std = excess.rolling(window, min_periods=minimum).std(ddof=1)
            downside = excess.where(excess < 0.0, 0.0)
            downside_deviation = np.sqrt(
                downside.pow(2).rolling(window, min_periods=minimum).mean()
            )

            result[f"{return_column}_ann_return_{window}d"] = rolling_annualized_return(
                strategy_return,
                window,
                annualization,
            )
            result[f"rf_ann_return_{window}d"] = rolling_annualized_return(
                rf,
                window,
                annualization,
            )
            result[f"{return_column}_ann_vol_{window}d"] = (
                strategy_return.rolling(window, min_periods=minimum).std(ddof=1)
                * math.sqrt(annualization)
            )
            result[f"{return_column}_sharpe_{window}d"] = (
                excess_mean / excess_std.replace(0.0, np.nan) * math.sqrt(annualization)
            )
            result[f"{return_column}_sortino_{window}d"] = (
                excess_mean
                / downside_deviation.replace(0.0, np.nan)
                * math.sqrt(annualization)
            )
            result[f"{return_column}_max_drawdown_{window}d"] = rolling_max_drawdown(
                strategy_return,
                window,
            )
            result[f"{return_column}_observations_{window}d"] = (
                strategy_return.rolling(window, min_periods=1).count()
            )
    return result


def run_adaptive_backtest(
    returns_frame: pd.DataFrame,
    risk_free_frame: pd.DataFrame,
    return_columns: Sequence[str] = DEFAULT_RETURN_COLUMNS,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    stem: str = DEFAULT_BACKTEST_STEM,
    date_column: str = DATE_COLUMN,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    out_dir = ensure_directory(Path(output_dir).resolve())
    audit_path = out_dir / "append_only_audit.jsonl"
    aligned, alignment_status = align_risk_free_to_trading_dates(
        returns_frame,
        risk_free_frame,
        date_column=date_column,
    )
    result = add_walk_forward_metrics(
        aligned,
        return_columns=return_columns,
        date_column=date_column,
    )
    output_status = write_dual_outputs(result, out_dir, stem, audit_path)
    status = {**output_status, **alignment_status, "audit_path": str(audit_path)}
    return result, status


# ============================================================================
# 8. 台股去大盤影響、族群驗證、四角色與動態規模分類
# ============================================================================

def ticker_is_tsmc(value: Any) -> bool:
    return bool(re.search(TSMC_TICKER_PATTERN, str(value).strip(), re.IGNORECASE))


def deterministic_seed(*parts: Any) -> int:
    material = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.blake2s(material, digest_size=4).digest(), "big")


def rolling_required_observations(window: int) -> int:
    """接近完整窗口，但容許由窗口本身推導出的 sqrt(window) 缺口。"""
    window = int(window)
    return max(3, int(math.ceil(window - math.sqrt(window))))


def resolve_validation_period(
    available_dates: pd.Series,
    period: str = "2024",
    start_date: Any | None = None,
    end_date: Any | None = None,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    dates = pd.to_datetime(available_dates, errors="coerce").dropna().sort_values()
    if dates.empty:
        raise ValueError("沒有可用的股票交易日")
    if period not in {*VALIDATION_PERIOD_STARTS, "custom"}:
        raise ValueError("period 僅接受 2024、2025、2026 或 custom")
    if period == "custom":
        if start_date is None:
            raise ValueError("period=custom 時必須提供 start_date")
        start = normalize_date(start_date)
    else:
        start = normalize_date(start_date or VALIDATION_PERIOD_STARTS[period])
    end = normalize_date(end_date) if end_date is not None else dates.max().normalize()
    if start > end:
        raise ValueError("族群驗證起日不得晚於迄日")
    return start, end


def validate_group_panel_columns(
    panel: pd.DataFrame,
    date_column: str,
    ticker_column: str,
    group_column: str,
    price_column: str,
    market_cap_column: str,
) -> None:
    required = {date_column, ticker_column, group_column, price_column, market_cap_column}
    missing = sorted(required.difference(panel.columns))
    if missing:
        raise KeyError(f"族群驗證缺少必要欄位：{missing}")


def prepare_group_validation_panel(
    panel: pd.DataFrame,
    risk_free_frame: pd.DataFrame,
    windows: Sequence[int] = ROLLING_WINDOWS,
    date_column: str = DATE_COLUMN,
    ticker_column: str = TICKER_COLUMN,
    group_column: str = GROUP_COLUMN,
    price_column: str = ADJUSTED_CLOSE_COLUMN,
    market_cap_column: str = MARKET_CAP_COLUMN,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """建立唯一股票日資料，並用排除台積電的大盤超額報酬計算 T-1 Beta 殘差。"""
    validate_group_panel_columns(
        panel,
        date_column,
        ticker_column,
        group_column,
        price_column,
        market_cap_column,
    )
    source = panel.copy()
    source[date_column] = pd.to_datetime(source[date_column], errors="coerce").dt.normalize()
    source[ticker_column] = source[ticker_column].astype(str).str.strip()
    source[group_column] = source[group_column].fillna("").astype(str).str.strip()
    source[price_column] = pd.to_numeric(source[price_column], errors="coerce")
    source[market_cap_column] = pd.to_numeric(source[market_cap_column], errors="coerce")
    source = source.dropna(subset=[date_column, ticker_column, price_column])
    source = source[source[ticker_column] != ""]
    if source.empty:
        raise ValueError("族群面板清理後沒有可用資料")

    duplicates = source.groupby([date_column, ticker_column], sort=False)
    inconsistent_price = duplicates[price_column].nunique(dropna=True).gt(1)
    inconsistent_cap = duplicates[market_cap_column].nunique(dropna=True).gt(1)
    if inconsistent_price.any() or inconsistent_cap.any():
        raise ValueError("同一交易日／代碼在跨族群占位中出現不一致價格或市值")

    membership = source.loc[
        source[group_column] != "",
        [date_column, ticker_column, group_column],
    ].drop_duplicates()
    securities = (
        source[[date_column, ticker_column, price_column, market_cap_column]]
        .drop_duplicates([date_column, ticker_column], keep="last")
        .sort_values([ticker_column, date_column])
        .reset_index(drop=True)
    )
    securities["stock_return"] = securities.groupby(ticker_column, sort=False)[
        price_column
    ].pct_change(fill_method=None)
    securities["market_cap_lag1"] = securities.groupby(ticker_column, sort=False)[
        market_cap_column
    ].shift(1)
    securities["is_tsmc_anchor"] = securities[ticker_column].map(ticker_is_tsmc)

    market_rows: list[dict[str, Any]] = []
    for trading_date, day in securities.loc[~securities["is_tsmc_anchor"]].groupby(
        date_column,
        sort=True,
    ):
        returns = pd.to_numeric(day["stock_return"], errors="coerce")
        caps = pd.to_numeric(day["market_cap_lag1"], errors="coerce")
        weighted = returns.notna() & caps.notna() & caps.gt(0.0)
        if weighted.any() and caps.loc[weighted].sum() > 0.0:
            market_return = float(
                np.average(returns.loc[weighted], weights=caps.loc[weighted])
            )
            method = "LAGGED_MARKET_CAP_WEIGHTED_EX_TSMC"
            constituents = int(weighted.sum())
        else:
            valid = returns.dropna()
            market_return = float(valid.mean()) if not valid.empty else np.nan
            method = "EQUAL_WEIGHT_FALLBACK_EX_TSMC"
            constituents = int(valid.size)
        market_rows.append(
            {
                date_column: trading_date,
                "market_return_ex_tsmc": market_return,
                "market_factor_method": method,
                "market_constituents": constituents,
            }
        )
    market = pd.DataFrame(market_rows)
    calendar, alignment_status = align_risk_free_to_trading_dates(
        securities[[date_column]].drop_duplicates(),
        risk_free_frame,
        date_column=date_column,
    )
    market = market.merge(
        calendar[
            [
                date_column,
                "rf_source_date",
                "yield_used_pct",
                "rf_daily_return",
                "rf_alignment_state",
                "annualization_factor",
            ]
        ],
        on=date_column,
        how="left",
        validate="one_to_one",
    )
    market["market_excess_return_ex_tsmc"] = (
        market["market_return_ex_tsmc"] - market["rf_daily_return"]
    )
    securities = securities.merge(
        market,
        on=date_column,
        how="left",
        validate="many_to_one",
    )
    securities["stock_excess_return"] = (
        securities["stock_return"] - securities["rf_daily_return"]
    )

    for window_value in windows:
        window = int(window_value)
        minimum = rolling_required_observations(window)
        beta_column = f"beta_ex_tsmc_{window}d"
        residual_column = f"residual_return_{window}d"
        securities[beta_column] = np.nan
        for _, indices in securities.groupby(ticker_column, sort=False).groups.items():
            stock = securities.loc[indices, "stock_excess_return"].shift(1)
            market_excess = securities.loc[
                indices,
                "market_excess_return_ex_tsmc",
            ].shift(1)
            covariance = stock.rolling(window, min_periods=minimum).cov(market_excess)
            variance = market_excess.rolling(window, min_periods=minimum).var(ddof=1)
            securities.loc[indices, beta_column] = (
                covariance / variance.replace(0.0, np.nan)
            ).to_numpy()
        securities[residual_column] = (
            securities["stock_excess_return"]
            - securities[beta_column] * securities["market_excess_return_ex_tsmc"]
        )

    if EXCHANGE_COLUMN in source.columns:
        exchange_values = sorted(
            source[EXCHANGE_COLUMN].dropna().astype(str).str.upper().str.strip().unique()
        )
        normalized = set(exchange_values)
        has_twse = bool(normalized.intersection({"TWSE", "上市"}))
        has_tpex = bool(normalized.intersection({"TPEX", "TPEx", "上櫃"}))
        coverage_state = "TWSE_TPEX_PRESENT" if has_twse and has_tpex else "REVIEW_MARKET_COVERAGE"
    else:
        exchange_values = []
        coverage_state = "UNVERIFIED_NO_EXCHANGE_COLUMN"
    status = {
        **alignment_status,
        "security_rows": int(len(securities)),
        "membership_rows": int(len(membership)),
        "unique_tickers": int(securities[ticker_column].nunique()),
        "tsmc_excluded_from_market_factor": True,
        "market_universe_requirement": "FULL_TWSE_TPEX_INPUT_EX_TSMC",
        "market_coverage_state": coverage_state,
        "exchange_values": exchange_values,
        "windows": [int(window) for window in windows],
    }
    return securities, membership, status


def dynamic_size_snapshot(
    securities: pd.DataFrame,
    as_of_date: Any,
    window: int,
    date_column: str = DATE_COLUMN,
    ticker_column: str = TICKER_COLUMN,
    market_cap_column: str = MARKET_CAP_COLUMN,
) -> pd.DataFrame:
    """以滾動市值的 log 尺度做一維三群聚；台積電只標為巨錨，不參與切點。"""
    as_of = normalize_date(as_of_date)
    eligible_dates = (
        securities.loc[securities[date_column] <= as_of, date_column]
        .drop_duplicates()
        .sort_values()
        .tail(int(window))
    )
    sample = securities.loc[
        securities[date_column].isin(eligible_dates),
        [ticker_column, market_cap_column, "is_tsmc_anchor"],
    ].copy()
    sample[market_cap_column] = pd.to_numeric(sample[market_cap_column], errors="coerce")
    snapshot = (
        sample.loc[sample[market_cap_column].gt(0.0)]
        .groupby(ticker_column, as_index=False)
        .agg(
            rolling_market_cap=(market_cap_column, "median"),
            is_tsmc_anchor=("is_tsmc_anchor", "max"),
        )
    )
    if snapshot.empty:
        return pd.DataFrame(
            columns=[ticker_column, "size_bucket", "rolling_market_cap", "size_method"]
        )

    fit_mask = ~snapshot["is_tsmc_anchor"]
    fit_values = np.log(snapshot.loc[fit_mask, "rolling_market_cap"].to_numpy(float))
    snapshot["size_bucket"] = "NEEDS_FETCH"
    method = "DYNAMIC_LOG_MARKET_CAP_3MEANS_EX_TSMC"

    if fit_values.size >= 3 and np.unique(fit_values).size >= 3:
        centers = np.quantile(fit_values, [1 / 6, 1 / 2, 5 / 6]).astype(float)
        for _ in range(SIZE_CLUSTER_MAX_ITERATIONS):
            labels = np.abs(fit_values[:, None] - centers[None, :]).argmin(axis=1)
            revised = np.array(
                [fit_values[labels == cluster].mean() if np.any(labels == cluster) else centers[cluster]
                 for cluster in range(3)],
                dtype=float,
            )
            if np.allclose(revised, centers, rtol=0.0, atol=FLOAT_EPSILON):
                centers = revised
                break
            centers = revised
        ordered_clusters = np.argsort(centers)
        names = {int(ordered_clusters[0]): "SMALL", int(ordered_clusters[1]): "MID", int(ordered_clusters[2]): "LARGE"}
        snapshot.loc[fit_mask, "size_bucket"] = [names[int(label)] for label in labels]
    else:
        method = "EMPIRICAL_THIRDS_FALLBACK_EX_TSMC"
        ranks = snapshot.loc[fit_mask, "rolling_market_cap"].rank(method="first", pct=True)
        snapshot.loc[fit_mask, "size_bucket"] = np.select(
            [ranks <= 1 / 3, ranks <= 2 / 3],
            ["SMALL", "MID"],
            default="LARGE",
        )

    snapshot.loc[snapshot["is_tsmc_anchor"], "size_bucket"] = "MEGA_ANCHOR"
    snapshot["size_method"] = method
    snapshot["size_window_days"] = int(window)
    snapshot["as_of_date"] = as_of
    return snapshot


def principal_component_absorption(matrix: pd.DataFrame) -> float:
    values = matrix.to_numpy(dtype=float)
    if values.shape[0] < 2 or values.shape[1] < 2 or not np.isfinite(values).all():
        return np.nan
    centered = values - values.mean(axis=0, keepdims=True)
    covariance = np.cov(centered, rowvar=False, ddof=1)
    eigenvalues = np.linalg.eigvalsh(np.atleast_2d(covariance))
    eigenvalues = np.clip(eigenvalues, 0.0, None)
    total = float(eigenvalues.sum())
    return float(eigenvalues[-1] / total) if total > FLOAT_EPSILON else np.nan


def average_pairwise_correlation(matrix: pd.DataFrame) -> float:
    correlation = matrix.corr().to_numpy(dtype=float)
    if correlation.shape[0] < 2:
        return np.nan
    values = correlation[np.triu_indices_from(correlation, k=1)]
    values = values[np.isfinite(values)]
    return float(values.mean()) if values.size else np.nan


def benjamini_hochberg(values: pd.Series) -> pd.Series:
    result = pd.Series(np.nan, index=values.index, dtype=float)
    valid = pd.to_numeric(values, errors="coerce").dropna()
    if valid.empty:
        return result
    ordered = valid.sort_values()
    count = len(ordered)
    adjusted = ordered.to_numpy(float) * count / np.arange(1, count + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    result.loc[ordered.index] = np.clip(adjusted, 0.0, 1.0)
    return result


def matched_group_null_distribution(
    residual_matrix: pd.DataFrame,
    group_members: Sequence[str],
    size_by_ticker: dict[str, str],
    repetitions: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    group_members = [str(member) for member in group_members]
    pool = [str(column) for column in residual_matrix.columns if str(column) not in group_members]
    if len(pool) < len(group_members):
        pool = [str(column) for column in residual_matrix.columns]
    target_sizes = pd.Series([size_by_ticker.get(member, "UNKNOWN") for member in group_members]).value_counts()
    rng = np.random.default_rng(seed)
    absorption_values: list[float] = []
    cohesion_values: list[float] = []

    for _ in range(max(1, int(repetitions))):
        selected: list[str] = []
        for size_bucket, count in target_sizes.items():
            candidates = [
                ticker for ticker in pool
                if size_by_ticker.get(ticker, "UNKNOWN") == size_bucket and ticker not in selected
            ]
            take = min(int(count), len(candidates))
            if take:
                selected.extend(rng.choice(candidates, size=take, replace=False).tolist())
        shortage = len(group_members) - len(selected)
        if shortage > 0:
            remainder = [ticker for ticker in pool if ticker not in selected]
            if len(remainder) < shortage:
                continue
            selected.extend(rng.choice(remainder, size=shortage, replace=False).tolist())
        candidate = residual_matrix[selected].dropna(how="any")
        if candidate.shape[0] < 3:
            continue
        absorption = principal_component_absorption(candidate)
        cohesion = average_pairwise_correlation(candidate)
        if np.isfinite(absorption):
            absorption_values.append(absorption)
        if np.isfinite(cohesion):
            cohesion_values.append(cohesion)
    return np.asarray(absorption_values, dtype=float), np.asarray(cohesion_values, dtype=float)


def cross_correlation_spectrum(
    member: pd.Series,
    peer_group: pd.Series,
    max_lag: int = MAX_CCF_LAG_DAYS,
) -> pd.Series:
    values: dict[int, float] = {}
    for lag in range(-int(max_lag), int(max_lag) + 1):
        # 正 lag：member_t 對應 peer_group_(t+lag)，故正值代表 member 領先。
        values[lag] = member.corr(peer_group.shift(-lag))
    return pd.Series(values, dtype=float)


def permute_contiguous_blocks(values: np.ndarray, block_length: int, rng: np.random.Generator) -> np.ndarray:
    blocks = [values[index:index + block_length] for index in range(0, len(values), block_length)]
    order = rng.permutation(len(blocks))
    return np.concatenate([blocks[int(index)] for index in order])


def validate_member_lead_lag(
    member: pd.Series,
    peer_group: pd.Series,
    window: int,
    repetitions: int,
    seed: int,
) -> dict[str, Any]:
    aligned = pd.concat(
        [member.rename("member"), peer_group.rename("peer_group")],
        axis=1,
    ).dropna()
    minimum = rolling_required_observations(window)
    if len(aligned) < minimum:
        return {
            "dominant_lag_days": np.nan,
            "peak_ccf": np.nan,
            "ccf_null_median": np.nan,
            "member_p_value": np.nan,
            "ccf_observations": int(len(aligned)),
        }
    spectrum = cross_correlation_spectrum(aligned["member"], aligned["peer_group"])
    if spectrum.dropna().empty:
        return {
            "dominant_lag_days": np.nan,
            "peak_ccf": np.nan,
            "ccf_null_median": np.nan,
            "member_p_value": np.nan,
            "ccf_observations": int(len(aligned)),
        }
    dominant_lag = int(spectrum.idxmax())
    observed_peak = float(spectrum.loc[dominant_lag])
    block_length = max(2, int(math.ceil(len(aligned) ** (1 / 3))))
    rng = np.random.default_rng(seed)
    null_peaks: list[float] = []
    base = aligned["peer_group"].to_numpy(float)
    for _ in range(max(1, int(repetitions))):
        permuted = pd.Series(
            permute_contiguous_blocks(base, block_length, rng),
            index=aligned.index,
        )
        null_spectrum = cross_correlation_spectrum(aligned["member"], permuted)
        if not null_spectrum.dropna().empty:
            null_peaks.append(float(null_spectrum.max()))
    null_array = np.asarray(null_peaks, dtype=float)
    p_value = (
        (1.0 + float(np.sum(null_array >= observed_peak))) / (1.0 + len(null_array))
        if null_array.size else np.nan
    )
    return {
        "dominant_lag_days": dominant_lag,
        "peak_ccf": observed_peak,
        "ccf_null_median": float(np.nanmedian(null_array)) if null_array.size else np.nan,
        "member_p_value": p_value,
        "ccf_observations": int(len(aligned)),
        "permutation_block_days": block_length,
    }


def membership_snapshot(
    membership: pd.DataFrame,
    as_of_date: Any,
    date_column: str,
    ticker_column: str,
    group_column: str,
) -> pd.DataFrame:
    eligible = membership.loc[membership[date_column] <= normalize_date(as_of_date)].copy()
    if eligible.empty:
        return eligible
    snapshot_date = eligible[date_column].max()
    return eligible.loc[
        eligible[date_column] == snapshot_date,
        [ticker_column, group_column],
    ].drop_duplicates()


def validate_group_snapshot(
    securities: pd.DataFrame,
    membership: pd.DataFrame,
    as_of_date: Any,
    window: int,
    repetitions: int = DEFAULT_PERMUTATION_REPETITIONS,
    date_column: str = DATE_COLUMN,
    ticker_column: str = TICKER_COLUMN,
    group_column: str = GROUP_COLUMN,
    market_cap_column: str = MARKET_CAP_COLUMN,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    as_of = normalize_date(as_of_date)
    window = int(window)
    residual_column = f"residual_return_{window}d"
    if residual_column not in securities.columns:
        raise KeyError(f"找不到殘差欄位：{residual_column}")
    dates = (
        securities.loc[securities[date_column] <= as_of, date_column]
        .drop_duplicates()
        .sort_values()
        .tail(window)
    )
    history = securities.loc[
        securities[date_column].isin(dates),
        [date_column, ticker_column, residual_column],
    ]
    residual_matrix = history.pivot(index=date_column, columns=ticker_column, values=residual_column)
    current_membership = membership_snapshot(
        membership,
        as_of,
        date_column,
        ticker_column,
        group_column,
    )
    size_frame = dynamic_size_snapshot(
        securities,
        as_of,
        window,
        date_column,
        ticker_column,
        market_cap_column,
    )
    size_by_ticker = dict(zip(size_frame[ticker_column].astype(str), size_frame["size_bucket"]))
    size_method_by_ticker = dict(zip(size_frame[ticker_column].astype(str), size_frame["size_method"]))
    group_rows: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []
    minimum = rolling_required_observations(window)

    for group_name, group_membership in current_membership.groupby(group_column, sort=True):
        declared = sorted(group_membership[ticker_column].astype(str).unique())
        tested = [ticker for ticker in declared if ticker in residual_matrix.columns]
        base_group = {
            "as_of_date": as_of,
            "window_days": window,
            group_column: group_name,
            "declared_members": len(declared),
            "tested_members": len(tested),
            "required_observations": minimum,
            "permutation_repetitions": int(repetitions),
        }
        if len(tested) < MIN_GROUP_MEMBERS:
            group_rows.append(
                {
                    **base_group,
                    "common_observations": 0,
                    "pc1_absorption": np.nan,
                    "mean_pairwise_correlation": np.nan,
                    "matched_null_pc1_median": np.nan,
                    "matched_null_cohesion_median": np.nan,
                    "group_p_value": np.nan,
                    "group_state": "BLOCKED_INSUFFICIENT_MEMBERS",
                }
            )
            for ticker in declared:
                member_rows.append(
                    {
                        "as_of_date": as_of,
                        "window_days": window,
                        group_column: group_name,
                        ticker_column: ticker,
                        "dominant_lag_days": np.nan,
                        "peak_ccf": np.nan,
                        "ccf_null_median": np.nan,
                        "member_p_value": np.nan,
                        "ccf_observations": 0,
                        "size_bucket": size_by_ticker.get(ticker, "NEEDS_FETCH"),
                        "size_method": size_method_by_ticker.get(ticker, "NEEDS_FETCH"),
                        "signal_direction": "FLAT",
                        "validation_state": "BLOCKED",
                    }
                )
            continue

        group_matrix = residual_matrix[tested].dropna(how="any")
        observed_absorption = principal_component_absorption(group_matrix)
        observed_cohesion = average_pairwise_correlation(group_matrix)
        if len(group_matrix) >= minimum:
            null_absorption, null_cohesion = matched_group_null_distribution(
                residual_matrix.dropna(axis=1, how="all"),
                tested,
                size_by_ticker,
                repetitions,
                deterministic_seed("GROUP", as_of, window, group_name),
            )
            group_p_value = (
                (1.0 + float(np.sum(null_absorption >= observed_absorption)))
                / (1.0 + len(null_absorption))
                if np.isfinite(observed_absorption) and null_absorption.size else np.nan
            )
            null_pc1_median = float(np.nanmedian(null_absorption)) if null_absorption.size else np.nan
            null_cohesion_median = float(np.nanmedian(null_cohesion)) if null_cohesion.size else np.nan
            group_state = "TESTED"
        else:
            group_p_value = np.nan
            null_pc1_median = np.nan
            null_cohesion_median = np.nan
            group_state = "BLOCKED_INSUFFICIENT_HISTORY"
        group_rows.append(
            {
                **base_group,
                "common_observations": int(len(group_matrix)),
                "pc1_absorption": observed_absorption,
                "mean_pairwise_correlation": observed_cohesion,
                "matched_null_pc1_median": null_pc1_median,
                "matched_null_cohesion_median": null_cohesion_median,
                "group_p_value": group_p_value,
                "group_state": group_state,
            }
        )

        for ticker in declared:
            row = {
                "as_of_date": as_of,
                "window_days": window,
                group_column: group_name,
                ticker_column: ticker,
                "size_bucket": size_by_ticker.get(ticker, "NEEDS_FETCH"),
                "size_method": size_method_by_ticker.get(ticker, "NEEDS_FETCH"),
                "signal_direction": "FLAT",
                "validation_state": "BLOCKED",
            }
            if ticker not in group_matrix.columns or len(group_matrix) < minimum:
                member_rows.append(
                    {
                        **row,
                        "dominant_lag_days": np.nan,
                        "peak_ccf": np.nan,
                        "ccf_null_median": np.nan,
                        "member_p_value": np.nan,
                        "ccf_observations": int(len(group_matrix)),
                    }
                )
                continue
            peers = [column for column in group_matrix.columns if str(column) != ticker]
            leave_one_out = group_matrix[peers].median(axis=1)
            result = validate_member_lead_lag(
                group_matrix[ticker],
                leave_one_out,
                window,
                repetitions,
                deterministic_seed("MEMBER", as_of, window, group_name, ticker),
            )
            pulse_length = max(1, int(math.ceil(math.sqrt(window))))
            pulse = leave_one_out.tail(pulse_length).mean()
            direction = "UP" if pulse > 0.0 else "DOWN" if pulse < 0.0 else "FLAT"
            member_rows.append({**row, **result, "signal_direction": direction})

    groups = pd.DataFrame(group_rows)
    members = pd.DataFrame(member_rows)
    if groups.empty:
        return groups, members
    groups["group_q_value"] = benjamini_hochberg(groups["group_p_value"])
    groups["group_validated"] = (
        groups["group_q_value"].le(VALIDATION_FDR_ALPHA)
        & groups["pc1_absorption"].gt(groups["matched_null_pc1_median"])
        & groups["mean_pairwise_correlation"].gt(groups["matched_null_cohesion_median"])
    )
    groups["group_decision"] = np.where(
        groups["group_state"].str.startswith("BLOCKED"),
        groups["group_state"],
        np.where(groups["group_validated"], "GROUP_VALIDATED", "GROUP_UNVALIDATED"),
    )

    if not members.empty:
        members["member_q_value"] = members.groupby(
            ["as_of_date", "window_days", group_column],
            group_keys=False,
        )["member_p_value"].transform(benjamini_hochberg)
        members = members.merge(
            groups[["as_of_date", "window_days", group_column, "group_q_value", "group_validated", "group_decision"]],
            on=["as_of_date", "window_days", group_column],
            how="left",
            validate="many_to_one",
        )
        member_validated = (
            members["group_validated"].fillna(False)
            & members["member_q_value"].le(VALIDATION_FDR_ALPHA)
            & members["peak_ccf"].gt(members["ccf_null_median"])
        )
        members["role"] = "UNRELATED"
        members.loc[member_validated & members["dominant_lag_days"].gt(0), "role"] = "LEAD"
        members.loc[member_validated & members["dominant_lag_days"].eq(0), "role"] = "PEER"
        members.loc[member_validated & members["dominant_lag_days"].lt(0), "role"] = "LAG"
        members["validation_state"] = np.select(
            [
                members["group_decision"].astype(str).str.startswith("BLOCKED"),
                member_validated,
                members["group_validated"].fillna(False),
            ],
            ["BLOCKED", "CONFIRMED", "MEMBER_UNRELATED"],
            default="GROUP_UNVALIDATED",
        )
        members["classification_method"] = "RESIDUAL_LOO_CCF_BLOCK_PERMUTATION_FDR"
    return groups, members


def attach_forward_validation_outcomes(
    member_results: pd.DataFrame,
    securities: pd.DataFrame,
    horizons: Sequence[int] = FORWARD_VALIDATION_HORIZONS,
    date_column: str = DATE_COLUMN,
    ticker_column: str = TICKER_COLUMN,
) -> pd.DataFrame:
    """分類完成後才附加未來結果；這些欄位不參與角色判定。"""
    result = member_results.copy()
    if result.empty:
        return result
    for window in sorted(result["window_days"].dropna().astype(int).unique()):
        residual_column = f"residual_return_{window}d"
        source = securities[[date_column, ticker_column, residual_column]].sort_values(
            [ticker_column, date_column]
        )
        for horizon_value in horizons:
            horizon = int(horizon_value)
            lookup: dict[tuple[str, pd.Timestamp], float] = {}
            for ticker, stock in source.groupby(ticker_column, sort=False):
                stock = stock.reset_index(drop=True)
                values = pd.to_numeric(stock[residual_column], errors="coerce").to_numpy(float)
                dates = stock[date_column].to_numpy()
                for index in range(len(stock)):
                    future = values[index + 1:index + 1 + horizon]
                    value = (
                        float(np.expm1(np.log1p(future).sum()))
                        if len(future) == horizon and np.isfinite(future).all() and np.all(future > -1.0)
                        else np.nan
                    )
                    lookup[(str(ticker), pd.Timestamp(dates[index]))] = value
            mask = result["window_days"].eq(window)
            result.loc[mask, f"future_residual_return_{horizon}d"] = [
                lookup.get((str(ticker), pd.Timestamp(as_of)), np.nan)
                for ticker, as_of in zip(
                    result.loc[mask, ticker_column],
                    result.loc[mask, "as_of_date"],
                )
            ]
            direction = result.loc[mask, "signal_direction"].map({"UP": 1.0, "DOWN": -1.0})
            future_return = result.loc[mask, f"future_residual_return_{horizon}d"]
            hit = np.where(
                direction.notna() & future_return.notna(),
                (np.sign(future_return) == direction).astype(float),
                np.nan,
            )
            result.loc[mask, f"direction_hit_{horizon}d"] = hit
    return result


def summarize_group_validation_backtest(
    member_results: pd.DataFrame,
    horizons: Sequence[int] = FORWARD_VALIDATION_HORIZONS,
) -> pd.DataFrame:
    if member_results.empty:
        return pd.DataFrame()
    keys = ["window_days", "role", "size_bucket", "signal_direction"]
    rows: list[dict[str, Any]] = []
    for key_values, segment in member_results.groupby(keys, dropna=False, sort=True):
        row = dict(zip(keys, key_values))
        row["classifications"] = int(len(segment))
        row["confirmed_classifications"] = int(segment["validation_state"].eq("CONFIRMED").sum())
        for horizon_value in horizons:
            horizon = int(horizon_value)
            future_column = f"future_residual_return_{horizon}d"
            hit_column = f"direction_hit_{horizon}d"
            future_values = pd.to_numeric(segment[future_column], errors="coerce").dropna()
            hit_values = pd.to_numeric(segment[hit_column], errors="coerce").dropna()
            row[f"median_future_residual_{horizon}d"] = (
                float(future_values.median()) if not future_values.empty else np.nan
            )
            row[f"direction_hit_rate_{horizon}d"] = (
                float(hit_values.mean()) if not hit_values.empty else np.nan
            )
            row[f"outcome_observations_{horizon}d"] = int(len(future_values))
        rows.append(row)
    return pd.DataFrame(rows)


def run_group_validation_backtest(
    panel: pd.DataFrame,
    risk_free_frame: pd.DataFrame,
    period: str = "2024",
    start_date: Any | None = None,
    end_date: Any | None = None,
    windows: Sequence[int] = ROLLING_WINDOWS,
    repetitions: int = DEFAULT_PERMUTATION_REPETITIONS,
    evaluation_step: int = DEFAULT_EVALUATION_STEP,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    date_column: str = DATE_COLUMN,
    ticker_column: str = TICKER_COLUMN,
    group_column: str = GROUP_COLUMN,
    price_column: str = ADJUSTED_CLOSE_COLUMN,
    market_cap_column: str = MARKET_CAP_COLUMN,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    securities, membership, preparation_status = prepare_group_validation_panel(
        panel,
        risk_free_frame,
        windows,
        date_column,
        ticker_column,
        group_column,
        price_column,
        market_cap_column,
    )
    if (
        REQUIRE_TWSE_TPEX_COVERAGE
        and preparation_status["market_coverage_state"] != "TWSE_TPEX_PRESENT"
    ):
        raise ValueError(
            "族群結論已阻擋：全市場面板必須含 Exchange 欄，且同時涵蓋 TWSE／TPEX"
        )
    start, end = resolve_validation_period(
        securities[date_column],
        period,
        start_date,
        end_date,
    )
    dates = (
        securities.loc[securities[date_column].between(start, end), date_column]
        .drop_duplicates()
        .sort_values()
    )
    step = max(1, int(evaluation_step))
    evaluation_dates = dates.iloc[::step]
    if not dates.empty and (evaluation_dates.empty or evaluation_dates.iloc[-1] != dates.iloc[-1]):
        evaluation_dates = pd.concat([evaluation_dates, dates.iloc[[-1]]]).drop_duplicates()

    group_frames: list[pd.DataFrame] = []
    member_frames: list[pd.DataFrame] = []
    for as_of in evaluation_dates:
        for window_value in windows:
            groups, members = validate_group_snapshot(
                securities,
                membership,
                as_of,
                int(window_value),
                repetitions,
                date_column,
                ticker_column,
                group_column,
                market_cap_column,
            )
            if not groups.empty:
                group_frames.append(groups)
            if not members.empty:
                member_frames.append(members)
    groups_all = pd.concat(group_frames, ignore_index=True) if group_frames else pd.DataFrame()
    members_all = pd.concat(member_frames, ignore_index=True) if member_frames else pd.DataFrame()
    members_all = attach_forward_validation_outcomes(
        members_all,
        securities,
        date_column=date_column,
        ticker_column=ticker_column,
    )
    backtest = summarize_group_validation_backtest(members_all)

    out_dir = ensure_directory(Path(output_dir).resolve())
    audit_path = out_dir / "append_only_audit.jsonl"
    detail_status = write_dual_outputs(
        members_all,
        out_dir,
        DEFAULT_GROUP_DETAIL_STEM,
        audit_path,
    )
    group_status = write_dual_outputs(
        groups_all,
        out_dir,
        DEFAULT_GROUP_SUMMARY_STEM,
        audit_path,
    )
    backtest_status = write_dual_outputs(
        backtest,
        out_dir,
        DEFAULT_GROUP_BACKTEST_STEM,
        audit_path,
    )
    append_hash_chained_audit(
        audit_path,
        {
            "event_type": "GROUP_VALIDATION_BACKTEST",
            "period": period,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "windows": [int(window) for window in windows],
            "repetitions": int(repetitions),
            "evaluation_step": step,
            "evaluation_dates": int(len(evaluation_dates)),
            "classification_method": "RESIDUAL_LOO_CCF_BLOCK_PERMUTATION_FDR",
            "composite_score_used": False,
        },
    )
    status = {
        **preparation_status,
        "period": period,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "evaluation_step": step,
        "evaluation_dates": int(len(evaluation_dates)),
        "role_rows": int(len(members_all)),
        "group_rows": int(len(groups_all)),
        "backtest_rows": int(len(backtest)),
        "role_output": detail_status,
        "group_output": group_status,
        "backtest_output": backtest_status,
        "audit_path": str(audit_path),
        "composite_score_used": False,
    }
    return members_all, groups_all, backtest, status


# ============================================================================
# 9. 內建單元測試與官方格式整合測試
# ============================================================================

def build_synthetic_risk_free() -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=320)
    yields = 1.2 + np.sin(np.linspace(0, 8, len(dates))) * 0.15
    frame = pd.DataFrame(
        {
            "Date": dates,
            "tw10y_par_yield_pct": yields,
            "tw10y_residual_year": 9.8,
            "tw10y_zcyc_bspline_pct": yields - 0.02,
            "tw10y_zcyc_svensson_pct": yields - 0.03,
            "yield_used_pct": yields,
            "yield_method": "TPEX_PAR_10Y",
            "source_grade": "MEASURED",
            "source_name": "SYNTHETIC_TEST",
            "source_page": "TEST",
            "source_url": "TEST",
            "raw_sha256": "TEST",
            "retrieved_at_utc": utc_now_iso(),
        }
    )
    return add_adaptive_yield_quality(frame)


def run_self_tests() -> dict[str, Any]:
    tests: list[dict[str, str]] = []

    def record(name: str, function: Any) -> None:
        try:
            function()
            tests.append({"test": name, "status": "PASS"})
        except Exception as exc:  # noqa: BLE001 - 測試需彙總全部結果
            tests.append({"test": name, "status": "FAIL", "error": str(exc)})

    def test_daily_conversion() -> None:
        daily = annual_yield_to_daily_return(pd.Series([2.0]), 252.0).iloc[0]
        rebuilt = (1.0 + daily) ** 252.0 - 1.0
        assert abs(rebuilt - 0.02) < 1e-12

    def test_no_future_fill() -> None:
        risk_free = build_synthetic_risk_free().iloc[[2, 3, 4]].copy()
        trading = pd.DataFrame(
            {
                "Date": pd.bdate_range("2024-01-02", periods=8),
                "strategy_return": 0.001,
            }
        )
        aligned, _ = align_risk_free_to_trading_dates(trading, risk_free)
        before_first_source = aligned["Date"] < risk_free["Date"].min()
        assert aligned.loc[before_first_source, "rf_source_date"].isna().all()

    def test_walk_forward_columns() -> None:
        risk_free = build_synthetic_risk_free()
        trading = pd.DataFrame(
            {
                "Date": risk_free["Date"],
                "strategy_return": np.sin(np.arange(len(risk_free)) / 15.0) / 100.0,
            }
        )
        aligned, _ = align_risk_free_to_trading_dates(trading, risk_free)
        result = add_walk_forward_metrics(aligned)
        for window in ROLLING_WINDOWS:
            assert f"strategy_return_sharpe_{window}d" in result.columns
            assert f"strategy_return_max_drawdown_{window}d" in result.columns

    def test_dynamic_stale_limit() -> None:
        dates = pd.Series(pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-08"]))
        limit = infer_dynamic_stale_limit(dates)
        assert MIN_STALE_CALENDAR_DAYS <= limit <= MAX_STALE_CALENDAR_DAYS

    def test_append_only_hash_chain() -> None:
        with tempfile.TemporaryDirectory() as temporary:
            audit = Path(temporary) / "audit.jsonl"
            first = append_hash_chained_audit(audit, {"event_type": "TEST_A"})
            second = append_hash_chained_audit(audit, {"event_type": "TEST_B"})
            lines = [json.loads(line) for line in audit.read_text("utf-8").splitlines()]
            assert lines[0]["event_hash"] == first
            assert lines[1]["previous_event_hash"] == first
            assert lines[1]["event_hash"] == second

    def test_lead_lag_sign_convention() -> None:
        rng = np.random.default_rng(7)
        member = pd.Series(rng.normal(size=180))
        peer_group = member.shift(2)
        spectrum = cross_correlation_spectrum(member, peer_group)
        assert int(spectrum.idxmax()) == 2

    def test_market_factor_excludes_tsmc() -> None:
        dates = pd.bdate_range("2024-01-02", periods=80)
        rows: list[dict[str, Any]] = []
        returns = {
            "2330": np.full(len(dates), 0.20),
            "1101": np.full(len(dates), 0.01),
            "1102": np.full(len(dates), 0.01),
            "1103": np.full(len(dates), 0.01),
        }
        for ticker, stock_returns in returns.items():
            prices = 100.0 * np.cumprod(1.0 + stock_returns)
            for trading_date, price in zip(dates, prices):
                rows.append(
                    {
                        "Date": trading_date,
                        "Ticker": ticker,
                        "Group": "TEST_GROUP",
                        "Adj Close": price,
                        "MarketCap": 1e15 if ticker == "2330" else 1e10,
                    }
                )
        risk_free = build_synthetic_risk_free().iloc[: len(dates)]
        securities, _, _ = prepare_group_validation_panel(
            pd.DataFrame(rows),
            risk_free,
            windows=(60,),
        )
        observed = securities.loc[
            securities["Date"] == dates[-1],
            "market_return_ex_tsmc",
        ].iloc[0]
        assert abs(float(observed) - 0.01) < 1e-12

    def test_group_output_has_no_composite_score() -> None:
        dates = pd.bdate_range("2024-01-02", periods=100)
        rng = np.random.default_rng(19)
        common = rng.normal(0.0, 0.006, len(dates))
        rows: list[dict[str, Any]] = []
        for number, ticker in enumerate(["2330", "1101", "1102", "1103", "1104", "1105"]):
            returns = common + rng.normal(0.0, 0.001, len(dates))
            prices = 100.0 * np.cumprod(1.0 + returns)
            for trading_date, price in zip(dates, prices):
                rows.append(
                    {
                        "Date": trading_date,
                        "Ticker": ticker,
                        "Group": "TEST_GROUP",
                        "Adj Close": price,
                        "MarketCap": (number + 1) * 1e10,
                    }
                )
        risk_free = build_synthetic_risk_free().iloc[: len(dates)]
        securities, membership, _ = prepare_group_validation_panel(
            pd.DataFrame(rows),
            risk_free,
            windows=(60,),
        )
        groups, members = validate_group_snapshot(
            securities,
            membership,
            dates[-1],
            60,
            repetitions=9,
        )
        assert not groups.empty and not members.empty
        assert set(members["role"]).issubset({"LEAD", "PEER", "LAG", "UNRELATED"})
        assert not any("score" in column.lower() for column in [*groups.columns, *members.columns])

    record("annual_yield_to_daily_return", test_daily_conversion)
    record("no_future_fill", test_no_future_fill)
    record("walk_forward_60_120_240", test_walk_forward_columns)
    record("dynamic_stale_limit", test_dynamic_stale_limit)
    record("append_only_hash_chain", test_append_only_hash_chain)
    record("lead_lag_sign_convention", test_lead_lag_sign_convention)
    record("market_factor_excludes_tsmc", test_market_factor_excludes_tsmc)
    record("group_output_has_no_composite_score", test_group_output_has_no_composite_score)

    failed = [test for test in tests if test["status"] != "PASS"]
    return {
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "status": "PASS" if not failed else "FAIL",
        "passed": len(tests) - len(failed),
        "failed": len(failed),
        "tests": tests,
    }


def run_official_integration_test(test_date: Any, output_dir: str | Path) -> dict[str, Any]:
    target_date = normalize_date(test_date)
    entries = fetch_tpex_month_file_list(target_date)
    matching = [entry for entry in entries if normalize_date(entry["date"]) == target_date]
    if not matching:
        raise RuntimeError(f"TPEx 月索引找不到 {target_date:%Y-%m-%d}")
    entry = matching[0]
    content = http_request_bytes(entry["url"])
    out_dir = ensure_directory(Path(output_dir).resolve())
    raw_path = out_dir / "integration_raw" / entry["filename"]
    audit_path = out_dir / "append_only_audit.jsonl"
    actual_path, digest, action = write_append_only_raw(
        raw_path,
        content,
        audit_path,
        entry["url"],
    )
    record = parse_tpex_curve_xls(content, entry["url"], digest)
    return {
        "status": "PASS",
        "date": record["Date"].strftime("%Y-%m-%d"),
        "tw10y_par_yield_pct": record["tw10y_par_yield_pct"],
        "tw10y_zcyc_bspline_pct": record["tw10y_zcyc_bspline_pct"],
        "yield_method": record["yield_method"],
        "raw_action": action,
        "raw_path": str(actual_path),
        "source_url": entry["url"],
    }


# ============================================================================
# 10. CLI 入口
# ============================================================================

def parse_return_columns(value: str) -> tuple[str, ...]:
    columns = tuple(item.strip() for item in value.split(",") if item.strip())
    if not columns:
        raise argparse.ArgumentTypeError("至少需要一個報酬欄位")
    return columns


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="增量擷取 TPEx 台灣 10Y")
    fetch_parser.add_argument("--start", default=DEFAULT_START_DATE)
    fetch_parser.add_argument("--end", default=DEFAULT_END_DATE)
    fetch_parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    fetch_parser.add_argument("--refresh-existing", action="store_true")

    backtest_parser = subparsers.add_parser("backtest", help="執行自適應無風險利率回測")
    backtest_parser.add_argument("--returns", required=True, help="CSV 或 Parquet 路徑")
    backtest_parser.add_argument("--risk-free", required=True, help="風險利率 CSV 或 Parquet 路徑")
    backtest_parser.add_argument("--return-columns", type=parse_return_columns, default=DEFAULT_RETURN_COLUMNS)
    backtest_parser.add_argument("--date-column", default=DATE_COLUMN)
    backtest_parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)

    group_parser = subparsers.add_parser(
        "group-validate",
        help="去除台積電影響後執行 60／120／240 日族群與角色 Walk-forward 驗證",
    )
    group_parser.add_argument("--panel", required=True, help="含日價、市值、族群占位的 CSV 或 Parquet")
    group_parser.add_argument("--risk-free", required=True, help="風險利率 CSV 或 Parquet 路徑")
    group_parser.add_argument("--period", choices=["2024", "2025", "2026", "custom"], default="2024")
    group_parser.add_argument("--start", default=None, help="可覆寫預設起日；custom 時必填")
    group_parser.add_argument("--end", default=None, help="預設為資料最新交易日")
    group_parser.add_argument("--repetitions", type=int, default=DEFAULT_PERMUTATION_REPETITIONS)
    group_parser.add_argument("--evaluation-step", type=int, default=DEFAULT_EVALUATION_STEP)
    group_parser.add_argument("--date-column", default=DATE_COLUMN)
    group_parser.add_argument("--ticker-column", default=TICKER_COLUMN)
    group_parser.add_argument("--group-column", default=GROUP_COLUMN)
    group_parser.add_argument("--price-column", default=ADJUSTED_CLOSE_COLUMN)
    group_parser.add_argument("--market-cap-column", default=MARKET_CAP_COLUMN)
    group_parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)

    subparsers.add_parser("self-test", help="執行離線內建測試")

    integration_parser = subparsers.add_parser("integration-test", help="驗證官方 XLS 格式")
    integration_parser.add_argument("--date", required=True)
    integration_parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    try:
        if arguments.command == "fetch":
            _, status = fetch_tw10y_history(
                start_date=arguments.start,
                end_date=arguments.end,
                output_dir=arguments.output_dir,
                refresh_existing=arguments.refresh_existing,
            )
            print(json.dumps(status, ensure_ascii=False, indent=2, default=str))
            return 0 if status["failure_count"] == 0 else 2

        if arguments.command == "backtest":
            returns_frame = read_table(Path(arguments.returns))
            risk_free_frame = read_table(Path(arguments.risk_free))
            _, status = run_adaptive_backtest(
                returns_frame,
                risk_free_frame,
                return_columns=arguments.return_columns,
                output_dir=arguments.output_dir,
                date_column=arguments.date_column,
            )
            print(json.dumps(status, ensure_ascii=False, indent=2, default=str))
            return 0 if status["blocked_rows"] == 0 else 2

        if arguments.command == "group-validate":
            panel = read_table(Path(arguments.panel))
            risk_free_frame = read_table(Path(arguments.risk_free))
            _, _, _, status = run_group_validation_backtest(
                panel=panel,
                risk_free_frame=risk_free_frame,
                period=arguments.period,
                start_date=arguments.start,
                end_date=arguments.end,
                repetitions=arguments.repetitions,
                evaluation_step=arguments.evaluation_step,
                output_dir=arguments.output_dir,
                date_column=arguments.date_column,
                ticker_column=arguments.ticker_column,
                group_column=arguments.group_column,
                price_column=arguments.price_column,
                market_cap_column=arguments.market_cap_column,
            )
            print(json.dumps(status, ensure_ascii=False, indent=2, default=str))
            return 0

        if arguments.command == "self-test":
            report = run_self_tests()
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["status"] == "PASS" else 1

        if arguments.command == "integration-test":
            report = run_official_integration_test(arguments.date, arguments.output_dir)
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return 0
    except Exception as exc:  # noqa: BLE001 - CLI 必須輸出結構化失敗資訊
        error = {
            "engine": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "status": "FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        print(json.dumps(error, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

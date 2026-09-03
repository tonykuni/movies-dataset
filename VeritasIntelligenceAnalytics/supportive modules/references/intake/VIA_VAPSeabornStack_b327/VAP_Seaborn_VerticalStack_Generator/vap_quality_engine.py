"""Auditable data-quality checks and opt-in repairs for VAP charts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

import numpy as np
import pandas as pd


# =============================================================================
# 0. 品質引擎參數
# =============================================================================

QUALITY_SCHEMA = "VIA-VAP-DATA-QUALITY/2.2"
DEFAULT_OUTLIER_IQR_MULTIPLIER = 3.0
DEFAULT_SAMPLE_ISSUES = 8
SUPPORTED_OUTLIER_POLICIES = {"none", "report", "clip_iqr"}
SUPPORTED_DUPLICATE_POLICIES = {"last", "first", "fail"}
SUPPORTED_INVALID_DATE_POLICIES = {"fail", "drop"}
VOLUME_NAME_TOKENS = ("volume", "turnover", "shares", "成交量", "成交股數")


# =============================================================================
# 1. 基本工具
# =============================================================================


def utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def selected_columns(frame: pd.DataFrame, columns: Iterable[str] | None = None) -> list[str]:
    requested = [str(column) for column in columns or frame.columns]
    return [column for column in dict.fromkeys(requested) if column in frame.columns]


def numeric_columns(frame: pd.DataFrame, columns: Iterable[str] | None = None) -> list[str]:
    return [
        column
        for column in selected_columns(frame, columns)
        if pd.api.types.is_numeric_dtype(frame[column])
    ]


def is_volume_column(column_name: str) -> bool:
    normalized = str(column_name).strip().lower()
    return any(token in normalized for token in VOLUME_NAME_TOKENS)


def finite_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def outlier_bounds(series: pd.Series, multiplier: float = DEFAULT_OUTLIER_IQR_MULTIPLIER) -> tuple[float, float] | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return None
    q1 = float(values.quantile(0.25))
    q3 = float(values.quantile(0.75))
    iqr = q3 - q1
    if not np.isfinite(iqr) or iqr <= 0:
        return None
    return q1 - multiplier * iqr, q3 + multiplier * iqr


def outlier_profile(series: pd.Series, multiplier: float = DEFAULT_OUTLIER_IQR_MULTIPLIER) -> dict[str, Any]:
    bounds = outlier_bounds(series, multiplier)
    if bounds is None:
        return {"count": 0, "lower": None, "upper": None, "sample_indices": []}
    lower, upper = bounds
    numeric = pd.to_numeric(series, errors="coerce")
    mask = (numeric < lower) | (numeric > upper)
    return {
        "count": int(mask.sum()),
        "lower": finite_or_none(lower),
        "upper": finite_or_none(upper),
        "sample_indices": [str(index) for index in series.index[mask][:DEFAULT_SAMPLE_ISSUES].tolist()],
    }


# =============================================================================
# 2. 日期連續性與資料品質稽核
# =============================================================================


def date_gap_profile(series: pd.Series) -> dict[str, Any]:
    parsed = pd.to_datetime(series, errors="coerce").dropna().drop_duplicates().sort_values()
    if len(parsed) < 2:
        return {
            "basis": "insufficient",
            "missing_count": 0,
            "missing_samples": [],
            "largest_gap_days": None,
        }
    normalized = pd.DatetimeIndex(parsed).normalize()
    differences = normalized.to_series().diff().dt.total_seconds().div(86400).dropna()
    median_days = float(differences.median()) if not differences.empty else 0.0
    largest_gap = float(differences.max()) if not differences.empty else 0.0
    if median_days <= 1.5:
        has_weekend_observations = bool((normalized.dayofweek >= 5).any())
        basis = "calendar_day" if has_weekend_observations else "weekday_proxy"
        expected = (
            pd.date_range(normalized.min(), normalized.max(), freq="D")
            if has_weekend_observations
            else pd.bdate_range(normalized.min(), normalized.max())
        )
        missing = expected.difference(normalized)
        return {
            "basis": basis,
            "missing_count": int(len(missing)),
            "missing_samples": [value.strftime("%Y-%m-%d") for value in missing[:DEFAULT_SAMPLE_ISSUES]],
            "largest_gap_days": finite_or_none(largest_gap),
        }
    large_gap_count = int((differences > max(median_days * 1.75, median_days + 1)).sum())
    return {
        "basis": "observed_cadence",
        "missing_count": large_gap_count,
        "missing_samples": [],
        "largest_gap_days": finite_or_none(largest_gap),
        "median_gap_days": finite_or_none(median_days),
    }


def make_issue(
    code: str,
    severity: str,
    message: str,
    count: int = 0,
    columns: Iterable[str] | None = None,
    action: str = "report",
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "count": int(count),
        "columns": [str(column) for column in columns or []],
        "action": action,
    }


def audit_frame(
    frame: pd.DataFrame,
    date_column: str = "",
    columns: Iterable[str] | None = None,
    outlier_multiplier: float = DEFAULT_OUTLIER_IQR_MULTIPLIER,
    grain_columns: Iterable[str] | None = None,
) -> dict[str, Any]:
    checked_columns = selected_columns(frame, columns)
    null_counts = {column: int(frame[column].isna().sum()) for column in checked_columns}
    issues: list[dict[str, Any]] = []
    total_nulls = int(sum(null_counts.values()))
    if total_nulls:
        affected = [column for column, count in null_counts.items() if count]
        issues.append(make_issue("missing_values", "warning", "資料含空值。", total_nulls, affected))

    date_profile: dict[str, Any] = {
        "column": date_column,
        "invalid_count": 0,
        "duplicate_count": 0,
        "duplicate_basis": [date_column] if date_column else [],
        "gaps": {"basis": "not_checked", "missing_count": 0, "missing_samples": [], "largest_gap_days": None},
    }
    if date_column and date_column in frame.columns:
        raw_dates = frame[date_column]
        parsed_dates = pd.to_datetime(raw_dates, errors="coerce")
        invalid_count = int((raw_dates.notna() & parsed_dates.isna()).sum())
        duplicate_basis = [
            column
            for column in dict.fromkeys([str(value) for value in grain_columns or [date_column]])
            if column in frame.columns
        ]
        if date_column not in duplicate_basis:
            duplicate_basis.append(date_column)
        duplicate_frame = frame.loc[parsed_dates.notna(), duplicate_basis].copy()
        duplicate_frame[date_column] = parsed_dates.loc[parsed_dates.notna()]
        duplicate_count = int(duplicate_frame.duplicated(subset=duplicate_basis, keep=False).sum())
        gaps = date_gap_profile(parsed_dates)
        date_profile.update(
            {
                "invalid_count": invalid_count,
                "duplicate_count": duplicate_count,
                "duplicate_basis": duplicate_basis,
                "gaps": gaps,
            }
        )
        if invalid_count:
            issues.append(make_issue("invalid_dates", "error", "日期欄位含無法解析的值。", invalid_count, [date_column]))
        if duplicate_count:
            issues.append(
                make_issue(
                    "duplicate_grain",
                    "warning",
                    "資料含重複 grain。",
                    duplicate_count,
                    duplicate_basis,
                )
            )
        if int(gaps.get("missing_count", 0)):
            issues.append(
                make_issue(
                    "date_gaps",
                    "info",
                    f"時間軸可能有缺口（基準：{gaps.get('basis')}）。",
                    int(gaps.get("missing_count", 0)),
                    [date_column],
                )
            )

    outliers: dict[str, dict[str, Any]] = {}
    for column in numeric_columns(frame, checked_columns):
        profile = outlier_profile(frame[column], outlier_multiplier)
        outliers[column] = profile
        if int(profile["count"]):
            issues.append(
                make_issue(
                    "outliers",
                    "info",
                    "偵測到 IQR 極端值；預設僅警示，不修改原始資料。",
                    int(profile["count"]),
                    [column],
                )
            )

    severity_order = {"ok": 0, "info": 1, "warning": 2, "error": 3}
    status = "OK"
    highest = max((severity_order.get(str(issue["severity"]), 0) for issue in issues), default=0)
    if highest >= 3:
        status = "ERROR"
    elif highest >= 2:
        status = "WARN"
    elif highest >= 1:
        status = "INFO"
    return {
        "schema": QUALITY_SCHEMA,
        "status": status,
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "checked_columns": checked_columns,
        "null_counts": null_counts,
        "null_cells": total_nulls,
        "date": date_profile,
        "outliers": outliers,
        "issues": issues,
        "audited_at": utc_now_text(),
    }


# =============================================================================
# 3. 明確啟用才執行的修正
# =============================================================================


def apply_outlier_policy(
    frame: pd.DataFrame,
    columns: Iterable[str],
    policy: str = "report",
    multiplier: float = DEFAULT_OUTLIER_IQR_MULTIPLIER,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    if policy not in SUPPORTED_OUTLIER_POLICIES:
        raise ValueError(f"不支援 outlier_policy={policy!r}。")
    result = frame.copy()
    repairs: list[dict[str, Any]] = []
    if policy != "clip_iqr":
        return result, repairs
    for column in numeric_columns(result, columns):
        bounds = outlier_bounds(result[column], multiplier)
        if bounds is None:
            continue
        lower, upper = bounds
        numeric = pd.to_numeric(result[column], errors="coerce")
        mask = (numeric < lower) | (numeric > upper)
        affected = int(mask.sum())
        if not affected:
            continue
        result[column] = numeric.astype(float).clip(lower=lower, upper=upper)
        repairs.append(
            {
                "action": "clip_iqr",
                "column": column,
                "count": affected,
                "lower": finite_or_none(lower),
                "upper": finite_or_none(upper),
                "reason": "使用者明確啟用極端值截尾。",
            }
        )
    return result, repairs


def summarize_repairs(
    before: pd.DataFrame,
    after: pd.DataFrame,
    columns: Iterable[str],
    missing_policy: str,
    additional_repairs: Iterable[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    repairs = [dict(item) for item in additional_repairs or []]
    for column in selected_columns(before, columns):
        before_missing = int(before[column].isna().sum())
        after_missing = int(after[column].isna().sum()) if column in after.columns else 0
        fixed = max(0, before_missing - after_missing)
        if fixed:
            repairs.append(
                {
                    "action": f"missing_{missing_policy}",
                    "column": column,
                    "count": fixed,
                    "reason": "依圖表空值策略執行。",
                }
            )
    removed_rows = max(0, int(len(before) - len(after)))
    if removed_rows:
        repairs.append(
            {
                "action": "drop_rows",
                "column": "",
                "count": removed_rows,
                "reason": f"依 missing={missing_policy} 或日期策略移除資料列。",
            }
        )
    return repairs

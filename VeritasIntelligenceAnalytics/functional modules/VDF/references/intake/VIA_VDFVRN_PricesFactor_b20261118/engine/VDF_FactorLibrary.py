"""VDF factor-library candidate engine.

The engine consumes only ``prices_canonical`` rows.  Raw volume and raw
trading value remain auditable display fields; every factor that uses activity
must use the ex-daytrade fields.  The built-in provider is dependency-free and
the TA-Lib provider is capability-gated against the Central Indicator Registry.
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

import argparse
import hashlib
import importlib
import json
import math
import re
import statistics
import sys
import uuid
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


# =============================================================================
# 01. Parameters and authoritative paths
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SSOT_PATH = PROJECT_ROOT / "config" / "ssot" / "VDF_PricesFactorRegistry.candidate.json"
INDICATOR_REGISTRY_PATH = PROJECT_ROOT / "config" / "ssot" / "VIA_ParameterIndicatorRegistry.via"
DEFAULT_DATASET_ID = "factor_library"
DEFAULT_PARAMETER_SET_ID = "VDF_DEFAULT"
READY_PRICE_STATUSES = {"READY", "NO_TRADE_CARRIED_PRICE"}
FORMULA_BY_FACTOR_FAMILY = {
    "return_simple": "vdf.factor.return.simple",
    "return_log": "vdf.factor.return.log",
    "normalized_price": "vdf.factor.price.base100",
    "momentum": "vdf.factor.momentum",
    "sma_ratio": "vdf.factor.sma_ratio",
    "realized_volatility": "vdf.factor.realized_volatility",
    "drawdown": "vdf.factor.drawdown",
    "rolling_zscore": "vdf.factor.rolling_zscore",
}


# =============================================================================
# 02. SSOT, hashes, and scalar helpers
# =============================================================================


def def_fail(message: str) -> RuntimeError:
    return RuntimeError(f"VDF_FACTOR_LIBRARY_BLOCKED: {message}")


def def_load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise def_fail(f"registry missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def def_load_registry(path: Path = SSOT_PATH) -> dict[str, Any]:
    registry = def_load_json(path)
    required = ("schema", "schema_version", "defaults", "datasets", "formulas", "input_policy")
    missing = [key for key in required if key not in registry]
    if missing:
        raise def_fail(f"SSOT keys missing: {', '.join(missing)}")
    if registry["input_policy"]["factor_volume_mode"] != "EX_DAYTRADE_ONLY":
        raise def_fail("factor volume policy drifted from EX_DAYTRADE_ONLY")
    if registry["input_policy"]["factor_trading_value_mode"] != "EX_DAYTRADE_ONLY":
        raise def_fail("factor trading-value policy drifted from EX_DAYTRADE_ONLY")
    return registry


def def_load_indicator_registry(path: Path = INDICATOR_REGISTRY_PATH) -> dict[str, Any]:
    registry = def_load_json(path)
    if registry.get("schema") != "VIA.ParameterIndicatorRegistry":
        raise def_fail("unexpected Central Indicator Registry schema")
    return registry


def def_hash_inputs(payload: Mapping[str, Any]) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def def_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def def_iso_date(value: Any) -> str:
    text = str(value or "").replace("/", "-")[:10]
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise def_fail(f"invalid data_date={value!r}") from exc


def def_iso_datetime(value: Any, label: str) -> str:
    if isinstance(value, datetime):
        current = value
    else:
        try:
            current = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        except ValueError as exc:
            raise def_fail(f"invalid {label}={value!r}") from exc
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).isoformat()


def def_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def def_sample_std(values: Sequence[float]) -> float | None:
    return statistics.stdev(values) if len(values) >= 2 else None


def def_safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0.0:
        return None
    value = numerator / denominator
    return value if math.isfinite(value) else None


def def_window(values: Sequence[float | None], end: int, length: int) -> list[float] | None:
    start = end - length + 1
    if start < 0:
        return None
    selected = list(values[start : end + 1])
    if len(selected) != length or any(value is None for value in selected):
        return None
    return [float(value) for value in selected if value is not None]


# =============================================================================
# 03. Canonical input gate
# =============================================================================


def def_validate_price_rows(
    rows: Iterable[Mapping[str, Any]],
    calculation_time: str,
) -> list[dict[str, Any]]:
    required = {
        "market",
        "ticker",
        "data_date",
        "as_of_date",
        "fetch_time",
        "source_id",
        "source_tier",
        "adj_open",
        "adj_high",
        "adj_low",
        "adj_close",
        "volume_ex_daytrade",
        "trading_value_ex_daytrade",
        "validation_status",
        "run_id",
        "source_hash",
        "no_trade_confirmed",
    }
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for source in rows:
        missing = sorted(required - set(source))
        if missing:
            raise def_fail(f"prices_canonical columns missing: {', '.join(missing)}")
        row = dict(source)
        if row.get("dataset_id") != "prices_canonical":
            raise def_fail("factor input dataset_id must be prices_canonical")
        row["data_date"] = def_iso_date(row["data_date"])
        row["as_of_date"] = def_iso_datetime(row["as_of_date"], "as_of_date")
        row["fetch_time"] = def_iso_datetime(row["fetch_time"], "fetch_time")
        if row["as_of_date"] > row["fetch_time"]:
            raise def_fail("prices_canonical as_of_date exceeds fetch_time")
        if row["as_of_date"] > calculation_time:
            raise def_fail("publication-time gate failed: as_of_date exceeds calculation_time")
        if not str(row["source_id"]).strip() or not str(row["source_tier"]).strip():
            raise def_fail("prices_canonical source evidence is empty")
        if not str(row["run_id"]).strip():
            raise def_fail("prices_canonical run_id evidence is empty")
        if not re.fullmatch(r"[0-9a-f]{64}", str(row["source_hash"]).strip().lower()):
            raise def_fail("prices_canonical source_hash must be a SHA-256 hex digest")
        status = str(row["validation_status"])
        allowed_statuses = READY_PRICE_STATUSES | {"CALC_BLOCKED", "PARTIAL_BLOCKED"}
        if status not in allowed_statuses:
            raise def_fail(f"unexpected prices_canonical validation_status: {status}")
        market = str(row["market"])
        ticker = str(row["ticker"])
        if market != market.strip().upper() or not market:
            raise def_fail("prices_canonical market must be non-empty normalized uppercase")
        if ticker != ticker.strip() or not ticker:
            raise def_fail("prices_canonical ticker must be non-empty and trimmed")
        if not isinstance(row["no_trade_confirmed"], bool):
            raise def_fail("prices_canonical no_trade_confirmed must be boolean")
        no_trade = row["no_trade_confirmed"] is True
        adjusted: dict[str, float | None] = {}
        if status != "CALC_BLOCKED":
            price_fields = ("adj_open", "adj_high", "adj_low", "adj_close")
            adjusted = {field: def_number(row[field]) for field in price_fields}
            if any(value is None or value <= 0.0 for value in adjusted.values()):
                raise def_fail("priced prices_canonical adjusted OHLC must be finite and positive")
            if adjusted["adj_high"] < max(adjusted["adj_open"], adjusted["adj_close"]):
                raise def_fail("priced prices_canonical adj_high is below open/close")
            if adjusted["adj_low"] > min(adjusted["adj_open"], adjusted["adj_close"]):
                raise def_fail("priced prices_canonical adj_low is above open/close")
            if no_trade and len(set(adjusted.values())) != 1:
                raise def_fail("confirmed no-trade row must have one unchanged adjusted price")
        if status in READY_PRICE_STATUSES:
            volume = def_number(row["volume_ex_daytrade"])
            trading_value = def_number(row["trading_value_ex_daytrade"])
            if volume is None or volume < 0.0 or trading_value is None or trading_value < 0.0:
                raise def_fail("ready prices_canonical ex-daytrade activity must be finite and non-negative")
            if status == "NO_TRADE_CARRIED_PRICE":
                if not no_trade or volume != 0.0 or trading_value != 0.0:
                    raise def_fail("carried no-trade row must be confirmed with zero activity")
            elif no_trade:
                raise def_fail("READY row cannot claim confirmed no-trade")
        elif status == "PARTIAL_BLOCKED":
            for field in ("volume_ex_daytrade", "trading_value_ex_daytrade"):
                raw_value = row[field]
                if raw_value is None:
                    continue
                value = def_number(raw_value)
                if value is None or value < 0.0:
                    raise def_fail(f"partial prices_canonical {field} must be non-negative when present")
                if no_trade and value != 0.0:
                    raise def_fail(f"partial confirmed no-trade row has non-zero {field}")
        key = (market, ticker, row["data_date"])
        if key in seen:
            raise def_fail(f"duplicate prices_canonical primary key: {key}")
        seen.add(key)
        output.append(row)
    output.sort(key=lambda row: (str(row["market"]), str(row["ticker"]), row["data_date"]))
    previous_priced_close: dict[tuple[str, str], float] = {}
    for row in output:
        status = str(row["validation_status"])
        identity = (str(row["market"]), str(row["ticker"]))
        if status == "CALC_BLOCKED":
            continue
        current_close = float(row["adj_close"])
        if row["no_trade_confirmed"] is True:
            previous_close = previous_priced_close.get(identity)
            if previous_close is None:
                raise def_fail("confirmed no-trade row requires a previous priced close")
            if current_close != previous_close:
                raise def_fail("confirmed no-trade price differs from the previous priced close")
        previous_priced_close[identity] = current_close
    return output


# =============================================================================
# 04. Built-in price, momentum, risk, and liquidity factors
# =============================================================================


def def_factor_record(
    price_row: Mapping[str, Any],
    registry: Mapping[str, Any],
    factor_family: str,
    factor_id: str,
    formula_key: str,
    value: float | None,
    unit: str,
    parameter_set_id: str,
    calculation_time: str,
    factor_run_id: str,
    input_rows: Sequence[Mapping[str, Any]],
    input_fields: Sequence[str],
    missing_status: str = "WARMUP",
) -> dict[str, Any]:
    formula = registry["formulas"][formula_key]
    status = "PASS" if value is not None and math.isfinite(value) else missing_status
    return {
        "dataset_id": DEFAULT_DATASET_ID,
        "market": price_row["market"],
        "ticker": price_row["ticker"],
        "data_date": price_row["data_date"],
        "as_of_date": price_row["as_of_date"],
        "calculation_time": calculation_time,
        "factor_family": factor_family,
        "factor_id": factor_id,
        "factor_version": registry["schema_version"],
        "parameter_set_id": parameter_set_id,
        "formula_id": formula_key,
        "formula_version": formula["version"],
        "value": value if status == "PASS" else None,
        "unit": unit,
        "input_price_mode": "ADJUSTED_OHLC_ONLY",
        "input_volume_mode": "EX_DAYTRADE_ONLY",
        "validation_status": status,
        "quality_flag": "GREEN" if status == "PASS" else "YELLOW",
        "run_id": factor_run_id,
        "input_run_id": price_row["run_id"],
        "input_hash": def_hash_inputs(
            {
                "factor_id": factor_id,
                "formula_id": formula_key,
                "formula_version": formula["version"],
                "parameter_set_id": parameter_set_id,
                "inputs": [
                    {
                        "market": item["market"],
                        "ticker": item["ticker"],
                        "data_date": item["data_date"],
                        "source_hash": item["source_hash"],
                        **{field: item.get(field) for field in input_fields},
                    }
                    for item in input_rows
                ],
            }
        ),
        "year": int(str(price_row["data_date"])[:4]),
    }


def def_group_price_rows(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["market"]), str(row["ticker"]))].append(dict(row))
    for group in grouped.values():
        group.sort(key=lambda row: row["data_date"])
    return grouped


def def_compute_group_factors(
    rows: Sequence[Mapping[str, Any]],
    registry: Mapping[str, Any],
    factors_start_date: str,
    horizons: Sequence[int],
    calculation_time: str,
    factor_run_id: str,
) -> list[dict[str, Any]]:
    closes = [def_number(row["adj_close"]) if row["validation_status"] in READY_PRICE_STATUSES else None for row in rows]
    volumes = [def_number(row["volume_ex_daytrade"]) for row in rows]
    values = [def_number(row["trading_value_ex_daytrade"]) for row in rows]
    returns: list[float | None] = [None]
    log_returns: list[float | None] = [None]
    for index in range(1, len(rows)):
        ratio = def_safe_ratio(closes[index], closes[index - 1])
        returns.append(None if ratio is None else ratio - 1.0)
        log_returns.append(None if ratio is None or ratio <= 0.0 else math.log(ratio))

    base_observation = next(
        (
            (index, closes[index])
            for index, row in enumerate(rows)
            if row["data_date"] >= factors_start_date and closes[index] is not None
        ),
        (None, None),
    )
    base_index, base_close = base_observation
    output: list[dict[str, Any]] = []
    annualization = int(registry["defaults"]["annualization_sessions"])
    for index, row in enumerate(rows):
        if row["data_date"] < factors_start_date:
            continue
        if row["validation_status"] not in READY_PRICE_STATUSES:
            continue
        normalized = def_safe_ratio(closes[index], base_close)
        return_inputs = rows[max(0, index - 1) : index + 1]
        normalized_inputs = [rows[base_index], row] if base_index is not None else [row]
        output.extend(
            [
                def_factor_record(
                    row,
                    registry,
                    "price",
                    "return.simple.1d",
                    FORMULA_BY_FACTOR_FAMILY["return_simple"],
                    returns[index],
                    "ratio",
                    DEFAULT_PARAMETER_SET_ID,
                    calculation_time,
                    factor_run_id,
                    return_inputs,
                    ["adj_close"],
                ),
                def_factor_record(
                    row,
                    registry,
                    "price",
                    "return.log.1d",
                    FORMULA_BY_FACTOR_FAMILY["return_log"],
                    log_returns[index],
                    "log_ratio",
                    DEFAULT_PARAMETER_SET_ID,
                    calculation_time,
                    factor_run_id,
                    return_inputs,
                    ["adj_close"],
                ),
                def_factor_record(
                    row,
                    registry,
                    "price",
                    "price.normalized.base100",
                    FORMULA_BY_FACTOR_FAMILY["normalized_price"],
                    None if normalized is None else normalized * 100.0,
                    "index",
                    f"BASE_{factors_start_date}",
                    calculation_time,
                    factor_run_id,
                    normalized_inputs,
                    ["adj_close"],
                ),
            ]
        )
        for horizon in horizons:
            parameter_set_id = f"W{horizon:03d}"
            prior_index = index - horizon
            momentum_ratio = def_safe_ratio(closes[index], closes[prior_index]) if prior_index >= 0 else None
            close_window = def_window(closes, index, horizon)
            return_window = def_window(returns, index, horizon)
            volume_window = def_window(volumes, index, horizon)
            value_window = def_window(values, index, horizon)
            rolling_inputs = rows[max(0, index - horizon + 1) : index + 1]
            momentum_inputs = [rows[prior_index], row] if prior_index >= 0 else [row]
            sma_ratio = None
            realized_vol = None
            drawdown = None
            volume_zscore = None
            value_zscore = None
            if close_window:
                mean_close = statistics.fmean(close_window)
                ratio = def_safe_ratio(closes[index], mean_close)
                sma_ratio = None if ratio is None else ratio - 1.0
                peak = max(close_window)
                peak_ratio = def_safe_ratio(closes[index], peak)
                drawdown = None if peak_ratio is None else peak_ratio - 1.0
            if return_window:
                standard_deviation = def_sample_std(return_window)
                realized_vol = None if standard_deviation is None else standard_deviation * math.sqrt(annualization)
            if volume_window:
                standard_deviation = def_sample_std(volume_window)
                if standard_deviation not in (None, 0.0):
                    volume_zscore = (volume_window[-1] - statistics.fmean(volume_window)) / standard_deviation
            if value_window:
                standard_deviation = def_sample_std(value_window)
                if standard_deviation not in (None, 0.0):
                    value_zscore = (value_window[-1] - statistics.fmean(value_window)) / standard_deviation
            output.extend(
                [
                    def_factor_record(
                        row,
                        registry,
                        "momentum",
                        f"momentum.return.{horizon}d",
                        FORMULA_BY_FACTOR_FAMILY["momentum"],
                        None if momentum_ratio is None else momentum_ratio - 1.0,
                        "ratio",
                        parameter_set_id,
                        calculation_time,
                        factor_run_id,
                        momentum_inputs,
                        ["adj_close"],
                    ),
                    def_factor_record(
                        row,
                        registry,
                        "trend",
                        f"trend.sma_ratio.{horizon}d",
                        FORMULA_BY_FACTOR_FAMILY["sma_ratio"],
                        sma_ratio,
                        "ratio",
                        parameter_set_id,
                        calculation_time,
                        factor_run_id,
                        rolling_inputs,
                        ["adj_close"],
                    ),
                    def_factor_record(
                        row,
                        registry,
                        "risk",
                        f"risk.realized_vol.{horizon}d",
                        FORMULA_BY_FACTOR_FAMILY["realized_volatility"],
                        realized_vol,
                        "annualized_ratio",
                        parameter_set_id,
                        calculation_time,
                        factor_run_id,
                        rows[max(0, index - horizon) : index + 1],
                        ["adj_close"],
                    ),
                    def_factor_record(
                        row,
                        registry,
                        "risk",
                        f"risk.drawdown.{horizon}d",
                        FORMULA_BY_FACTOR_FAMILY["drawdown"],
                        drawdown,
                        "ratio",
                        parameter_set_id,
                        calculation_time,
                        factor_run_id,
                        rolling_inputs,
                        ["adj_close"],
                    ),
                    def_factor_record(
                        row,
                        registry,
                        "liquidity",
                        f"liquidity.volume_ex_daytrade_zscore.{horizon}d",
                        FORMULA_BY_FACTOR_FAMILY["rolling_zscore"],
                        volume_zscore,
                        "zscore",
                        parameter_set_id,
                        calculation_time,
                        factor_run_id,
                        rolling_inputs,
                        ["volume_ex_daytrade"],
                        "MISSING_EX_DAYTRADE_INPUT" if volumes[index] is None else "WARMUP",
                    ),
                    def_factor_record(
                        row,
                        registry,
                        "liquidity",
                        f"liquidity.value_ex_daytrade_zscore.{horizon}d",
                        FORMULA_BY_FACTOR_FAMILY["rolling_zscore"],
                        value_zscore,
                        "zscore",
                        parameter_set_id,
                        calculation_time,
                        factor_run_id,
                        rolling_inputs,
                        ["trading_value_ex_daytrade"],
                        "MISSING_EX_DAYTRADE_INPUT" if values[index] is None else "WARMUP",
                    ),
                ]
            )
    return output


def def_compute_factor_library(
    price_rows: Iterable[Mapping[str, Any]],
    registry: Mapping[str, Any] | None = None,
    factors_start_date: str | None = None,
    horizons: Sequence[int] | None = None,
    calculation_time: str | None = None,
    run_id: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    active_registry = dict(registry or def_load_registry())
    active_calculation_time = def_iso_datetime(calculation_time or def_now_iso(), "calculation_time")
    active_run_id = str(run_id or f"VDF-FACTOR-{uuid.uuid4().hex}")
    validated = def_validate_price_rows(price_rows, active_calculation_time)
    start = def_iso_date(factors_start_date or active_registry["defaults"]["factors_start_date"])
    active_horizons = tuple(int(value) for value in (horizons or active_registry["defaults"]["horizons"]))
    if not active_horizons or any(value <= 1 for value in active_horizons):
        raise def_fail("factor horizons must be integers greater than one")
    if len(set(active_horizons)) != len(active_horizons):
        raise def_fail("factor horizons must be unique")
    output: list[dict[str, Any]] = []
    for group in def_group_price_rows(validated).values():
        output.extend(
            def_compute_group_factors(
                group,
                active_registry,
                start,
                active_horizons,
                active_calculation_time,
                active_run_id,
            )
        )
    expected = active_registry["datasets"]["factor_library"]["columns"]
    missing = [column for column in expected if any(column not in row for row in output)]
    if missing:
        raise def_fail(f"factor output columns missing: {', '.join(missing)}")
    status_counts: dict[str, int] = {}
    for row in output:
        status = str(row["validation_status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    report = {
        "schema": active_registry["schema"],
        "schema_version": active_registry["schema_version"],
        "registration_state": active_registry["registration_state"],
        "run_id": active_run_id,
        "calculation_time": active_calculation_time,
        "prices_rows": len(validated),
        "factor_rows": len(output),
        "factors_start_date": start,
        "horizons": list(active_horizons),
        "status_counts": status_counts,
        "input_price_mode": "ADJUSTED_OHLC_ONLY",
        "input_volume_mode": "EX_DAYTRADE_ONLY",
        "network": "OFF",
    }
    return output, report


# =============================================================================
# 05. TA-Lib capability gate (no handwritten fallback)
# =============================================================================


def def_registered_indicators(indicator_registry: Mapping[str, Any]) -> list[str]:
    names: list[str] = []
    for category in indicator_registry.get("categories", []):
        names.extend(str(indicator["name"]).upper() for indicator in category.get("indicators", []))
    if len(names) != len(set(names)):
        raise def_fail("Central Indicator Registry contains duplicate indicator names")
    expected = int(indicator_registry.get("counts", {}).get("indicators", len(names)))
    if len(names) != expected:
        raise def_fail(f"Central Indicator Registry count drift: expected={expected} actual={len(names)}")
    return names


def def_talib_capability(
    indicator_registry: Mapping[str, Any],
    available_functions: Sequence[str],
) -> dict[str, Any]:
    registered = def_registered_indicators(indicator_registry)
    available = {str(name).upper() for name in available_functions}
    missing = sorted(set(registered) - available)
    extra = sorted(available - set(registered))
    return {
        "status": "PASS" if not missing else "BLOCKED",
        "registered": len(registered),
        "available": len(available & set(registered)),
        "missing": missing,
        "runtime_extra": extra,
        "fallback": "PROHIBITED",
        "volume_input": "volume_ex_daytrade",
    }


def def_probe_talib(indicator_registry: Mapping[str, Any] | None = None) -> dict[str, Any]:
    active_registry = dict(indicator_registry or def_load_indicator_registry())
    try:
        talib_module = importlib.import_module("talib")
    except Exception as exc:
        return {
            "status": "BLOCKED",
            "registered": len(def_registered_indicators(active_registry)),
            "available": 0,
            "missing": def_registered_indicators(active_registry),
            "runtime_extra": [],
            "fallback": "PROHIBITED",
            "volume_input": "volume_ex_daytrade",
            "error": f"{type(exc).__name__}: {exc}",
        }
    result = def_talib_capability(active_registry, list(talib_module.get_functions()))
    result["runtime_wrapper"] = str(getattr(talib_module, "__version__", "unknown"))
    core = getattr(talib_module, "__ta_version__", "unknown")
    result["runtime_c"] = core.decode("utf-8", errors="replace") if isinstance(core, bytes) else str(core)
    return result


# =============================================================================
# 06. CLI
# =============================================================================


def def_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VDF governed factor-library candidate")
    parser.add_argument("--input", type=Path, help="prices_canonical JSON array")
    parser.add_argument("--output", type=Path, help="factor-library JSON array")
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--start", default=None)
    parser.add_argument("--calculation-time", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--probe-talib", action="store_true")
    return parser


def def_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def def_main(argv: Sequence[str] | None = None) -> int:
    arguments = def_parser().parse_args(argv)
    try:
        if arguments.probe_talib:
            probe = def_probe_talib()
            print(json.dumps(probe, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if probe["status"] == "PASS" else 2
        if arguments.input is None or arguments.output is None:
            raise def_fail("--input and --output are required unless --probe-talib is used")
        price_rows = json.loads(arguments.input.read_text(encoding="utf-8"))
        factors, report = def_compute_factor_library(
            price_rows,
            factors_start_date=arguments.start,
            calculation_time=arguments.calculation_time,
            run_id=arguments.run_id,
        )
        def_write_json(arguments.output, factors)
        if arguments.report is not None:
            def_write_json(arguments.report, report)
        print(json.dumps({"status": "PASS", **report}, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(def_main())

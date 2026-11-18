"""VDF ``prices_canonical`` candidate engine.

This module is deliberately network-free.  Fetchers provide raw observations;
the engine resolves field aliases from the Central Governance candidate SSOT,
derives adjusted OHLC and ex-daytrade amount fields, and fails closed on
conflicting duplicates or unknown gaps.
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
import csv
import hashlib
import json
import math
import re
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


# =============================================================================
# 01. Parameters (all mutable defaults live here or in the SSOT)
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SSOT_PATH = PROJECT_ROOT / "config" / "ssot" / "VDF_PricesFactorRegistry.candidate.json"
DEFAULT_SOURCE_ID = "UNSPECIFIED"
DEFAULT_SOURCE_TIER = "UNVERIFIED"
DEFAULT_MARKET = "TW"
DEFAULT_ASSET_TYPE = "security"
DEFAULT_DATASET_ID = "prices_canonical"
CSV_ENCODING = "utf-8-sig"
FLOAT_TOLERANCE = 1e-9
PRICE_COLUMNS = ("raw_open", "raw_high", "raw_low", "raw_close", "adj_close_source")
METRIC_COLUMNS = (
    "volume_raw",
    "daytrade_volume",
    "volume_ex_daytrade",
    "trading_value_raw",
    "daytrade_trading_value",
    "trading_value_ex_daytrade",
)
CANONICAL_VALUE_COLUMNS = (
    "adj_factor",
    "adj_open",
    "adj_high",
    "adj_low",
    "adj_close",
    *METRIC_COLUMNS,
    "no_trade_confirmed",
    "price_fill_method",
    "validation_status",
)


# =============================================================================
# 02. Errors, serialization, and SSOT loading
# =============================================================================


def def_fail(message: str) -> RuntimeError:
    return RuntimeError(f"VDF_PRICES_CANONICAL_BLOCKED: {message}")


def def_load_registry(path: Path = SSOT_PATH) -> dict[str, Any]:
    if not path.is_file():
        raise def_fail(f"SSOT missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = ("schema", "schema_version", "datasets", "field_aliases", "formulas", "input_policy")
    missing = [key for key in required if key not in payload]
    if missing:
        raise def_fail(f"SSOT keys missing: {', '.join(missing)}")
    if payload["registration_state"] != "CANDIDATE_PENDING_CGC_PROMOTION":
        raise def_fail("candidate registry has an unexpected promotion state")
    return payload


def def_json_hash(payload: Mapping[str, Any]) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def def_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# =============================================================================
# 03. Field and scalar normalization
# =============================================================================


def def_normalize_field_name(value: Any) -> str:
    text = str(value).strip().lower().replace("％", "%")
    return re.sub(r"[^0-9a-z%\u4e00-\u9fff]+", "", text)


def def_alias_index(registry: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for canonical, aliases in registry["field_aliases"].items():
        for alias in aliases:
            normalized = def_normalize_field_name(alias)
            owner = result.get(normalized)
            if owner is not None and owner != canonical:
                raise def_fail(f"alias collision: {alias!r} => {owner!r}/{canonical!r}")
            result[normalized] = canonical
    return result


def def_resolve_row(row: Mapping[str, Any], registry: Mapping[str, Any]) -> dict[str, Any]:
    index = def_alias_index(registry)
    resolved: dict[str, Any] = {}
    unknown: list[str] = []
    for source_name, value in row.items():
        canonical = index.get(def_normalize_field_name(source_name))
        if canonical is None:
            unknown.append(str(source_name))
            continue
        if canonical in resolved and resolved[canonical] not in (None, "", value):
            raise def_fail(f"two source fields resolve to {canonical!r} with conflicting values")
        resolved[canonical] = value
    resolved["_unknown_fields"] = sorted(unknown)
    return resolved


def def_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def def_boolean(value: Any) -> bool:
    truthy = {"1", "true", "yes", "y", "confirmed", "是", "有", "確認"}
    return value is True or str(value).strip().lower() in truthy


def def_iso_date(value: Any, label: str) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value or "").strip().replace("/", "-")
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError as exc:
        raise def_fail(f"invalid {label}: {value!r}") from exc


def def_optional_iso_datetime(value: Any, fallback: str) -> str:
    if value is None or value == "":
        return fallback
    if isinstance(value, datetime):
        current = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        return current.astimezone(timezone.utc).isoformat()
    text = str(value).strip()
    try:
        current = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return f"{def_iso_date(text, 'as_of/fetch time')}T00:00:00+00:00"
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).isoformat()


def def_parse_iso_datetime(value: str, label: str) -> datetime:
    try:
        current = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise def_fail(f"invalid {label}: {value!r}") from exc
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc)


def def_sha256(value: Any, fallback_payload: Mapping[str, Any]) -> str:
    digest = str(value or "").strip().lower()
    if not digest:
        return def_json_hash(fallback_payload)
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise def_fail("source_hash must be a SHA-256 hex digest")
    return digest


def def_positive_or_none(value: Any) -> float | None:
    number = def_number(value)
    return number if number is not None and number > 0.0 else None


# =============================================================================
# 04. Canonical formulas
# =============================================================================


def def_adjusted_ohlc(
    resolved: Mapping[str, Any],
    previous_adj_close: float | None,
) -> tuple[dict[str, float | None], str, list[str]]:
    no_trade = def_boolean(resolved.get("no_trade_confirmed"))
    warnings: list[str] = []
    if no_trade:
        if previous_adj_close is None:
            return {
                "adj_factor": None,
                "adj_open": None,
                "adj_high": None,
                "adj_low": None,
                "adj_close": None,
            }, "CALC_BLOCKED", ["confirmed no-trade row has no previous adjusted close"]
        carried = float(previous_adj_close)
        return {
            "adj_factor": None,
            "adj_open": carried,
            "adj_high": carried,
            "adj_low": carried,
            "adj_close": carried,
        }, "NO_TRADE_CARRIED_PRICE", warnings

    values = {name: def_positive_or_none(resolved.get(name)) for name in PRICE_COLUMNS}
    missing = [name for name, value in values.items() if value is None]
    if missing:
        return {
            "adj_factor": None,
            "adj_open": None,
            "adj_high": None,
            "adj_low": None,
            "adj_close": None,
        }, "CALC_BLOCKED", [f"missing or non-positive price fields: {', '.join(missing)}"]

    if values["raw_high"] < max(values["raw_open"], values["raw_close"]):
        warnings.append("raw_high is below open/close")
    if values["raw_low"] > min(values["raw_open"], values["raw_close"]):
        warnings.append("raw_low is above open/close")
    if warnings:
        return {
            "adj_factor": None,
            "adj_open": None,
            "adj_high": None,
            "adj_low": None,
            "adj_close": None,
        }, "CALC_BLOCKED", warnings

    factor = values["adj_close_source"] / values["raw_close"]
    return {
        "adj_factor": factor,
        "adj_open": values["raw_open"] * factor,
        "adj_high": values["raw_high"] * factor,
        "adj_low": values["raw_low"] * factor,
        "adj_close": values["adj_close_source"],
    }, "READY", warnings


def def_subtract_metric(
    raw_value: Any,
    daytrade_value: Any,
    explicit_value: Any,
    no_trade_confirmed: bool,
    label: str,
) -> tuple[float | None, list[str]]:
    raw_number = def_number(raw_value)
    daytrade_number = def_number(daytrade_value)
    explicit_number = def_number(explicit_value)
    if no_trade_confirmed:
        nonzero = [number for number in (raw_number, daytrade_number, explicit_number) if number not in (None, 0.0)]
        if nonzero:
            return None, [f"confirmed no-trade row contains non-zero {label}"]
        return 0.0, []
    if raw_number is None or daytrade_number is None:
        return None, [f"{label} raw/daytrade missing; no raw fallback"]
    if raw_number < 0.0 or daytrade_number < 0.0 or daytrade_number > raw_number:
        return None, [f"invalid {label}: require 0 <= daytrade <= raw"]
    derived = raw_number - daytrade_number
    if explicit_number is not None and not math.isclose(explicit_number, derived, rel_tol=0.0, abs_tol=FLOAT_TOLERANCE):
        return None, [f"explicit {label} ex-daytrade conflicts with governed formula"]
    return derived, []


def def_canonical_row(
    source_row: Mapping[str, Any],
    registry: Mapping[str, Any],
    previous_adj_close: float | None,
    source_id: str,
    source_tier: str,
    run_id: str,
    fetch_time: str,
) -> tuple[dict[str, Any], list[str]]:
    resolved = def_resolve_row(source_row, registry)
    if registry["input_policy"]["unknown_alias"] == "FAIL_CLOSED" and resolved["_unknown_fields"]:
        raise def_fail(f"unregistered input fields: {', '.join(resolved['_unknown_fields'])}")
    ticker = str(resolved.get("ticker") or "").strip()
    if not ticker:
        raise def_fail("ticker is required")
    data_date = def_iso_date(resolved.get("data_date"), "data_date")
    market = str(resolved.get("market") or DEFAULT_MARKET).strip().upper()
    asset_type = str(resolved.get("asset_type") or DEFAULT_ASSET_TYPE).strip().lower()
    effective_fetch_time = def_optional_iso_datetime(resolved.get("fetch_time"), fetch_time)
    effective_as_of = def_optional_iso_datetime(resolved.get("as_of_date"), f"{data_date}T00:00:00+00:00")
    effective_source_id = str(resolved.get("source_id") or source_id).strip()
    effective_source_tier = str(resolved.get("source_tier") or source_tier).strip().upper()
    effective_run_id = str(resolved.get("run_id") or run_id).strip()
    if not effective_source_id or effective_source_id == DEFAULT_SOURCE_ID:
        raise def_fail("source_id evidence is required")
    if not effective_source_tier or effective_source_tier == DEFAULT_SOURCE_TIER:
        raise def_fail("source_tier evidence is required")
    if not effective_run_id:
        raise def_fail("run_id evidence is required")
    parsed_as_of = def_parse_iso_datetime(effective_as_of, "as_of_date")
    parsed_fetch = def_parse_iso_datetime(effective_fetch_time, "fetch_time")
    if parsed_as_of > parsed_fetch:
        raise def_fail("as_of_date must be earlier than or equal to fetch_time")
    if date.fromisoformat(data_date) > parsed_as_of.date():
        raise def_fail("data_date must be earlier than or equal to as_of_date")
    no_trade = def_boolean(resolved.get("no_trade_confirmed"))

    adjusted, price_status, warnings = def_adjusted_ohlc(resolved, previous_adj_close)
    volume_ex, volume_warnings = def_subtract_metric(
        resolved.get("volume_raw"),
        resolved.get("daytrade_volume"),
        resolved.get("volume_ex_daytrade"),
        no_trade,
        "volume",
    )
    value_ex, value_warnings = def_subtract_metric(
        resolved.get("trading_value_raw"),
        resolved.get("daytrade_trading_value"),
        resolved.get("trading_value_ex_daytrade"),
        no_trade,
        "trading value",
    )
    warnings.extend(volume_warnings)
    warnings.extend(value_warnings)

    validation_status = price_status
    if price_status != "CALC_BLOCKED" and (volume_ex is None or value_ex is None):
        validation_status = "PARTIAL_BLOCKED"
    quality_flag = "GREEN" if validation_status in {"READY", "NO_TRADE_CARRIED_PRICE"} else "RED"
    canonical = {
        "dataset_id": DEFAULT_DATASET_ID,
        "source_id": effective_source_id,
        "source_tier": effective_source_tier,
        "market": market,
        "asset_type": asset_type,
        "ticker": ticker,
        "data_date": data_date,
        "as_of_date": effective_as_of,
        "fetch_time": effective_fetch_time,
        "run_id": effective_run_id,
        "source_hash": def_sha256(resolved.get("source_hash"), dict(source_row)),
        "raw_open": def_number(resolved.get("raw_open")),
        "raw_high": def_number(resolved.get("raw_high")),
        "raw_low": def_number(resolved.get("raw_low")),
        "raw_close": def_number(resolved.get("raw_close")),
        "adj_close_source": def_number(resolved.get("adj_close_source")),
        **adjusted,
        "volume_raw": 0.0 if no_trade else def_number(resolved.get("volume_raw")),
        "daytrade_volume": 0.0 if no_trade else def_number(resolved.get("daytrade_volume")),
        "volume_ex_daytrade": volume_ex,
        "trading_value_raw": 0.0 if no_trade else def_number(resolved.get("trading_value_raw")),
        "daytrade_trading_value": 0.0 if no_trade else def_number(resolved.get("daytrade_trading_value")),
        "trading_value_ex_daytrade": value_ex,
        "no_trade_confirmed": no_trade,
        "price_fill_method": "PREVIOUS_ADJ_CLOSE_CONFIRMED_NO_TRADE" if no_trade else "NONE",
        "validation_status": validation_status,
        "quality_flag": quality_flag,
        "year": int(data_date[:4]),
    }
    return canonical, warnings


# =============================================================================
# 05. Batch normalization, dedupe, and validation report
# =============================================================================


def def_same_canonical_values(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return all(left.get(column) == right.get(column) for column in CANONICAL_VALUE_COLUMNS)


def def_canonicalize_prices(
    rows: Iterable[Mapping[str, Any]],
    registry: Mapping[str, Any] | None = None,
    source_id: str = DEFAULT_SOURCE_ID,
    source_tier: str = DEFAULT_SOURCE_TIER,
    run_id: str | None = None,
    fetch_time: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    active_registry = dict(registry or def_load_registry())
    active_run_id = run_id or f"VDF-{uuid.uuid4().hex}"
    active_fetch_time = fetch_time or def_now_iso()
    source_rows = list(rows)
    sortable: list[tuple[str, str, str, Mapping[str, Any]]] = []
    for source_row in source_rows:
        resolved = def_resolve_row(source_row, active_registry)
        sortable.append(
            (
                str(resolved.get("market") or DEFAULT_MARKET).strip().upper(),
                str(resolved.get("ticker") or "").strip(),
                def_iso_date(resolved.get("data_date"), "data_date"),
                source_row,
            )
        )
    sortable.sort(key=lambda item: item[:3])

    previous_by_ticker: dict[tuple[str, str], float] = {}
    canonical_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    warnings_by_key: dict[str, list[str]] = {}
    duplicates_removed = 0
    for market, ticker, data_date, source_row in sortable:
        previous = previous_by_ticker.get((market, ticker))
        canonical, warnings = def_canonical_row(
            source_row,
            active_registry,
            previous,
            source_id,
            source_tier,
            active_run_id,
            active_fetch_time,
        )
        key = (canonical["market"], canonical["ticker"], canonical["data_date"])
        current = canonical_by_key.get(key)
        if current is not None:
            if not def_same_canonical_values(current, canonical):
                raise def_fail(f"conflicting duplicate primary key: {key}")
            duplicates_removed += 1
            continue
        canonical_by_key[key] = canonical
        if canonical["adj_close"] is not None and canonical["validation_status"] != "CALC_BLOCKED":
            previous_by_ticker[(canonical["market"], canonical["ticker"])] = float(canonical["adj_close"])
        if warnings:
            warnings_by_key["|".join(key)] = warnings

    output = [canonical_by_key[key] for key in sorted(canonical_by_key)]
    expected_columns = active_registry["datasets"]["prices_canonical"]["columns"]
    missing_columns = [column for column in expected_columns if any(column not in row for row in output)]
    if missing_columns:
        raise def_fail(f"canonical output columns missing: {', '.join(missing_columns)}")
    status_counts: dict[str, int] = {}
    for row in output:
        status = str(row["validation_status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    report = {
        "schema": active_registry["schema"],
        "schema_version": active_registry["schema_version"],
        "registration_state": active_registry["registration_state"],
        "run_id": active_run_id,
        "rows_in": len(source_rows),
        "rows_out": len(output),
        "duplicates_removed": duplicates_removed,
        "status_counts": status_counts,
        "warnings": warnings_by_key,
        "network": "OFF",
        "input_policy": active_registry["input_policy"],
    }
    return output, report


# =============================================================================
# 06. Minimal network-free CLI for governed CSV/JSON input
# =============================================================================


def def_read_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise def_fail(f"input missing: {path}")
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise def_fail("JSON input must be a list of row objects")
        return [dict(row) for row in payload]
    if path.suffix.lower() in {".csv", ".txt"}:
        with path.open("r", encoding=CSV_ENCODING, newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    raise def_fail("CLI input supports governed JSON or UTF-8-SIG CSV only")


def def_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def def_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VDF prices_canonical candidate engine")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--source-tier", default=DEFAULT_SOURCE_TIER)
    parser.add_argument("--run-id", default=None)
    return parser


def def_main(argv: Sequence[str] | None = None) -> int:
    arguments = def_parser().parse_args(argv)
    try:
        canonical, report = def_canonicalize_prices(
            def_read_rows(arguments.input),
            source_id=arguments.source_id,
            source_tier=arguments.source_tier,
            run_id=arguments.run_id,
        )
        def_write_json(arguments.output, canonical)
        if arguments.report is not None:
            def_write_json(arguments.report, report)
        print(json.dumps({"status": "PASS", **report}, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(def_main())

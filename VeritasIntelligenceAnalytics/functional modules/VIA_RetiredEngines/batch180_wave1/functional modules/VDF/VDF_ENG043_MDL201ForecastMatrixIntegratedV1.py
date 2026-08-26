# -*- coding: utf-8 -*-
"""
VDF_MDL201_ForecastMatrix_Integrated_v1
VERITAS INTELLIGENCE ANALYTICS

單檔整合版：
1. 整合 supportive_module 內既有支援工具
2. 建立 Forecast / Compare / Matrix 主表
3. 產出 Parquet / CSV / JSON / HTML
4. 支援 DuckDB SSOT 寫入
5. 支援自動 fallback，不因單一支援模組缺失而中斷

注意：
- 所有參數集中於頂部
- 主要結構皆使用完整 def 定義
- 可直接複製後再依本機環境替換路徑
"""

from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
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

# =========================================================
# def PARAMETERS
# =========================================================

def def_parameters() -> dict:
    return {
        "APP_NAME": "VDF_MDL201_ForecastMatrix_Integrated_v1",
        "APP_VERSION": "1.0.0",
        "BASE_ROOT": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module",
        "SUPPORTIVE_ROOT": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module",
        "OUTPUT_ROOT": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\_forecast_matrix_output",
        "HTML_TITLE_LINE_1": "Veritas Forecast Matrix",
        "HTML_TITLE_LINE_2": "VERITAS INTELLIGENCE ANALYTICS",
        "HTML_TITLE_LINE_3": "YF × FS × TW Daily × 3M Chip Matrix",
        "DUCKDB_NAME": "forecast_matrix.duckdb",
        "PARQUET_NAME": "forecast_matrix_daily.parquet",
        "CSV_NAME": "forecast_matrix_daily.csv",
        "JSON_NAME": "forecast_matrix_daily.json",
        "HTML_NAME": "forecast_matrix_daily.html",
        "SUMMARY_JSON_NAME": "forecast_matrix_summary.json",
        "LOG_NAME": "run_log.json",
        "ENABLE_DUCKDB": True,
        "ENABLE_PARQUET": True,
        "ENABLE_CSV": True,
        "ENABLE_JSON": True,
        "ENABLE_HTML": True,
        "ENABLE_SAMPLE_DATA": True,
        "DATE_FORMAT_OUTPUT": "%Y/%m/%d",
        "DATE_FORMAT_CHART": "%Y-%m-%d",
        "TIME_FORMAT": "%Y-%m-%d %H:%M:%S",
        "STALENESS_DAYS_WARNING": 15,
        "STALENESS_DAYS_CRITICAL": 30,
        "DIFF_WARNING_PCT": 5.0,
        "DIFF_CRITICAL_PCT": 10.0,
        "MARKET_DEFAULT": "TWSE",
        "PREFERRED_FORECAST_SOURCE": "FS",
        "PREFERRED_ACTUAL_SOURCE": "MOPS/TWSE/TPEX",
        "FORMULA_UPSIDE_NAME": "Formula Upside %",
        "FORMULA_FORWARD_PE_NAME": "Formula PE Forward FS",
        "FORMULA_CUSTOM_NAME": "Formula Custom",
        "SUPPORTIVE_MODULES": {
            "VIA_SSOT_Unified": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_SSOT_Unified.py",
            "VeritasAegisNexus": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py",
            "VeritasCeleritas": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py",
            "VIA_EnvManager": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py",
            "VIA_Panorama_AST_RuntimeInjector": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_Panorama_AST_RuntimeInjector.py",
            "VIA_RegistryCore_v1": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_RegistryCore_v1.py",
            "VIA_Runtime_Bridge_All_in_One": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_Runtime_Bridge_All_in_One.py",
        },
        "DISPLAY_HEADERS": [
            "Date", "Ticker", "YFinance Ticker", "Name", "Market", "Adj Close", "Volume",
            "Category", "Metric Key", "Metric Name", "Unit",
            "N-2 FY Diluted EPS", "N-1 FY Diluted EPS", "N FY Diluted EPS",
            "N+1 FY Diluted EPS (FS)", "N+2 FY Diluted EPS (FS)",
            "N-2 FY Year", "N-1 FY Year", "N FY Year", "N+1 FY Year", "N+2 FY Year",
            "YF Value", "FS Value", "Master Value", "Master Source",
            "Abs Diff", "Diff %", "Diff Flag",
            "Target High Price", "Target Low Price", "Target Mean Price", "Target Median Price",
            "Analyst Count", "Recommendation",
            "Foreign Net 3M", "Investment Trust Net 3M", "Dealer Net 3M", "Main Force Net 3M",
            "Margin Change 3M", "Short Change 3M",
            "Formula Upside %", "Formula PE Forward FS", "Formula Custom",
            "Actual Source", "Forecast Source", "Report Date", "Update Time", "Stale Status",
            "Confidence Level", "Data Quality Flag"
        ],
        "SYSTEM_HEADERS": [
            "date", "ticker", "yf_ticker", "name", "market", "adj_close", "volume",
            "category", "metric_key", "metric_name_zh", "unit",
            "diluted_eps_fy_n2_actual", "diluted_eps_fy_n1_actual", "diluted_eps_fy_n_actual",
            "diluted_eps_fy_p1_forecast_fs", "diluted_eps_fy_p2_forecast_fs",
            "actual_fy_year_n2", "actual_fy_year_n1", "actual_fy_year_n", "forecast_fy_year_p1", "forecast_fy_year_p2",
            "yf_value", "fs_value", "master_value", "master_source",
            "abs_diff", "pct_diff", "diff_flag",
            "target_high_price", "target_low_price", "target_mean_price", "target_median_price",
            "analyst_opinion_count", "recommendation_key",
            "foreign_net_3m", "investment_trust_net_3m", "dealer_net_3m", "main_force_net_3m",
            "margin_change_3m", "short_change_3m",
            "formula_upside_pct", "formula_pe_forward_fs", "formula_custom_001",
            "actual_source", "forecast_source", "report_date", "update_time", "stale_status",
            "confidence_level", "data_quality_flag"
        ],
    }


CFG = def_parameters()

# =========================================================
# def IMPORTS
# =========================================================

def def_import_standard_libs():
    import os
    import sys
    import json
    import math
    import traceback
    import importlib.util
    from pathlib import Path
    from datetime import datetime, date
    return os, sys, json, math, traceback, importlib, Path, datetime, date


os, sys, json, math, traceback, importlib, Path, datetime, date = def_import_standard_libs()


def def_import_third_party_libs():
    libs = {}
    try:
        import pandas as pd
        libs["pd"] = pd
    except Exception:
        libs["pd"] = None
    try:
        import duckdb
        libs["duckdb"] = duckdb
    except Exception:
        libs["duckdb"] = None
    try:
        import pyarrow  # noqa: F401
        libs["pyarrow"] = True
    except Exception:
        libs["pyarrow"] = False
    return libs


LIBS = def_import_third_party_libs()
pd = LIBS["pd"]
duckdb = LIBS["duckdb"]

# =========================================================
# def PATH / LOG / STATE
# =========================================================

def def_state() -> dict:
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_root = Path(CFG["OUTPUT_ROOT"])
    run_dir = out_root / f"run_{run_ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return {
        "run_id": run_ts,
        "run_dir": run_dir,
        "duckdb_path": run_dir / CFG["DUCKDB_NAME"],
        "parquet_path": run_dir / CFG["PARQUET_NAME"],
        "csv_path": run_dir / CFG["CSV_NAME"],
        "json_path": run_dir / CFG["JSON_NAME"],
        "html_path": run_dir / CFG["HTML_NAME"],
        "summary_json_path": run_dir / CFG["SUMMARY_JSON_NAME"],
        "log_path": run_dir / CFG["LOG_NAME"],
        "events": [],
        "supportive_modules": {},
        "warnings": [],
        "errors": [],
    }


STATE = def_state()


def def_log(level: str, message: str, extra: dict | None = None) -> None:
    row = {
        "time": datetime.now().strftime(CFG["TIME_FORMAT"]),
        "level": level,
        "message": message,
        "extra": extra or {},
    }
    STATE["events"].append(row)
    print(f"[{row['time']}][{level}] {message}")


# =========================================================
# def SUPPORTIVE MODULE LOADER
# =========================================================

def def_load_module_from_path(module_name: str, module_path: str):
    try:
        file_path = Path(module_path)
        if not file_path.exists():
            raise FileNotFoundError(str(file_path))
        spec = importlib.util.spec_from_file_location(module_name, str(file_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create spec for {module_name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"



def def_try_load_supportive_modules() -> dict:
    result = {}
    for name, path in CFG["SUPPORTIVE_MODULES"].items():
        module, err = def_load_module_from_path(name, path)
        result[name] = {
            "path": path,
            "loaded": module is not None,
            "module": module,
            "error": err,
        }
        if module is not None:
            def_log("OK", f"Loaded supportive module: {name}", {"path": path})
        else:
            def_log("WARN", f"Supportive module fallback: {name}", {"path": path, "error": err})
            STATE["warnings"].append({"module": name, "error": err})
    STATE["supportive_modules"] = result
    return result


# =========================================================
# def OPTIONAL BRIDGE CALLS
# =========================================================

def def_try_call_first_available(module_names: list[str], candidate_funcs: list[str], *args, **kwargs):
    for module_name in module_names:
        info = STATE["supportive_modules"].get(module_name, {})
        module = info.get("module")
        if module is None:
            continue
        for func_name in candidate_funcs:
            func = getattr(module, func_name, None)
            if callable(func):
                try:
                    return {
                        "ok": True,
                        "module": module_name,
                        "func": func_name,
                        "value": func(*args, **kwargs),
                    }
                except Exception as exc:
                    STATE["warnings"].append({"module": module_name, "func": func_name, "error": str(exc)})
    return {"ok": False, "module": None, "func": None, "value": None}



def def_register_into_registry(payload: dict) -> dict:
    return def_try_call_first_available(
        ["VIA_RegistryCore_v1", "VIA_SSOT_Unified", "VIA_Runtime_Bridge_All_in_One"],
        ["register", "register_asset", "upsert", "upsert_record", "write_registry", "ssot_upsert"],
        payload,
    )



def def_notify_aegis(event_payload: dict) -> dict:
    return def_try_call_first_available(
        ["VeritasAegisNexus"],
        ["notify", "emit", "guard", "record_event"],
        event_payload,
    )



def def_accelerate_if_available(df):
    result = def_try_call_first_available(
        ["VeritasCeleritas"],
        ["accelerate_dataframe", "accelerate", "optimize_dataframe", "optimize"],
        df,
    )
    return result["value"] if result["ok"] and result["value"] is not None else df



def def_env_healthcheck() -> dict:
    result = def_try_call_first_available(
        ["VIA_EnvManager"],
        ["healthcheck", "run_healthcheck", "env_healthcheck", "inspect_environment"],
    )
    return result



def def_runtime_injector_probe(script_text: str) -> dict:
    return def_try_call_first_available(
        ["VIA_Panorama_AST_RuntimeInjector"],
        ["inject_runtime", "analyze_and_inject", "inspect_code", "panorama_scan"],
        script_text,
    )


# =========================================================
# def DATA BUILDERS
# =========================================================

def def_safe_float(value, default=None):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default



def def_today_strings() -> tuple[str, str]:
    now = datetime.now()
    return now.strftime(CFG["DATE_FORMAT_OUTPUT"]), now.strftime(CFG["TIME_FORMAT"])



def def_make_sample_rows() -> list[dict]:
    date_str, update_time = def_today_strings()
    rows = [
        {
            "date": date_str,
            "ticker": "2330",
            "yf_ticker": "2330.TW",
            "name": "台積電",
            "market": "TWSE",
            "adj_close": 950.0,
            "volume": 24500123,
            "category": "EPS",
            "metric_key": "diluted_eps_matrix",
            "metric_name_zh": "Diluted EPS 五期矩陣",
            "unit": "TWD/share",
            "diluted_eps_fy_n2_actual": 32.34,
            "diluted_eps_fy_n1_actual": 38.21,
            "diluted_eps_fy_n_actual": 45.12,
            "diluted_eps_fy_p1_forecast_fs": 51.88,
            "diluted_eps_fy_p2_forecast_fs": 58.77,
            "actual_fy_year_n2": 2023,
            "actual_fy_year_n1": 2024,
            "actual_fy_year_n": 2025,
            "forecast_fy_year_p1": 2026,
            "forecast_fy_year_p2": 2027,
            "yf_value": 45.10,
            "fs_value": 45.12,
            "master_value": 45.12,
            "master_source": "FS",
            "abs_diff": 0.02,
            "pct_diff": 0.04,
            "diff_flag": "OK",
            "target_high_price": 1280.0,
            "target_low_price": 980.0,
            "target_mean_price": 1160.0,
            "target_median_price": 1150.0,
            "analyst_opinion_count": 24,
            "recommendation_key": "buy",
            "foreign_net_3m": 152000,
            "investment_trust_net_3m": 18100,
            "dealer_net_3m": 5500,
            "main_force_net_3m": 176200,
            "margin_change_3m": -1200,
            "short_change_3m": 350,
            "formula_upside_pct": 22.1052631579,
            "formula_pe_forward_fs": 18.3114880493,
            "formula_custom_001": 1.2210526316,
            "actual_source": "MOPS/TWSE/TPEX",
            "forecast_source": "FS",
            "report_date": "2026-04-20",
            "update_time": update_time,
            "stale_status": "Fresh",
            "confidence_level": "HIGH",
            "data_quality_flag": "OK",
        },
        {
            "date": date_str,
            "ticker": "2454",
            "yf_ticker": "2454.TW",
            "name": "聯發科",
            "market": "TWSE",
            "adj_close": 1385.0,
            "volume": 6200123,
            "category": "EPS",
            "metric_key": "diluted_eps_matrix",
            "metric_name_zh": "Diluted EPS 五期矩陣",
            "unit": "TWD/share",
            "diluted_eps_fy_n2_actual": 55.12,
            "diluted_eps_fy_n1_actual": 62.87,
            "diluted_eps_fy_n_actual": 66.30,
            "diluted_eps_fy_p1_forecast_fs": 71.40,
            "diluted_eps_fy_p2_forecast_fs": 77.25,
            "actual_fy_year_n2": 2023,
            "actual_fy_year_n1": 2024,
            "actual_fy_year_n": 2025,
            "forecast_fy_year_p1": 2026,
            "forecast_fy_year_p2": 2027,
            "yf_value": 66.15,
            "fs_value": 66.30,
            "master_value": 66.30,
            "master_source": "FS",
            "abs_diff": 0.15,
            "pct_diff": 0.23,
            "diff_flag": "OK",
            "target_high_price": 1650.0,
            "target_low_price": 1420.0,
            "target_mean_price": 1545.0,
            "target_median_price": 1530.0,
            "analyst_opinion_count": 19,
            "recommendation_key": "buy",
            "foreign_net_3m": 89000,
            "investment_trust_net_3m": 9500,
            "dealer_net_3m": 2700,
            "main_force_net_3m": 101200,
            "margin_change_3m": -800,
            "short_change_3m": 125,
            "formula_upside_pct": 11.5523465704,
            "formula_pe_forward_fs": 19.3977591036,
            "formula_custom_001": 1.1155234657,
            "actual_source": "MOPS/TWSE/TPEX",
            "forecast_source": "FS",
            "report_date": "2026-04-18",
            "update_time": update_time,
            "stale_status": "Fresh",
            "confidence_level": "HIGH",
            "data_quality_flag": "OK",
        },
    ]
    return rows



def def_rows_to_dataframe(rows: list[dict]):
    if pd is None:
        raise RuntimeError("pandas is required for this integrated script")
    df = pd.DataFrame(rows)
    for header in CFG["SYSTEM_HEADERS"]:
        if header not in df.columns:
            df[header] = None
    df = df[CFG["SYSTEM_HEADERS"]].copy()
    return df



def def_apply_formulas(df):
    if pd is None:
        return df
    df = df.copy()
    df["formula_upside_pct"] = ((df["target_mean_price"] - df["adj_close"]) / df["adj_close"]) * 100.0
    df["formula_pe_forward_fs"] = df["adj_close"] / df["diluted_eps_fy_p1_forecast_fs"]
    df["formula_custom_001"] = (1.0 + (df["formula_upside_pct"] / 100.0))
    return df



def def_apply_diff_flags(df):
    if pd is None:
        return df
    df = df.copy()
    abs_diff = (df["yf_value"] - df["fs_value"]).abs()
    pct_diff = abs_diff / df["fs_value"].replace({0: math.nan}) * 100.0
    df["abs_diff"] = abs_diff.round(6)
    df["pct_diff"] = pct_diff.fillna(0).round(6)
    df["diff_flag"] = df["pct_diff"].apply(
        lambda x: "CRITICAL" if x >= CFG["DIFF_CRITICAL_PCT"] else ("WARN" if x >= CFG["DIFF_WARNING_PCT"] else "OK")
    )
    return df



def def_build_master_value(df):
    if pd is None:
        return df
    df = df.copy()
    preferred = CFG["PREFERRED_FORECAST_SOURCE"]
    df["master_value"] = df.apply(lambda r: r["fs_value"] if preferred == "FS" and pd.notna(r["fs_value"]) else r["yf_value"], axis=1)
    df["master_source"] = df.apply(lambda r: "FS" if preferred == "FS" and pd.notna(r["fs_value"]) else "YF", axis=1)
    return df



def def_build_stale_status(df):
    if pd is None:
        return df
    df = df.copy()
    today = pd.Timestamp.today().normalize()
    report_dt = pd.to_datetime(df["report_date"], errors="coerce")
    age_days = (today - report_dt.dt.normalize()).dt.days
    df["stale_status"] = age_days.apply(
        lambda x: "Stale" if pd.notna(x) and x > CFG["STALENESS_DAYS_CRITICAL"] else (
            "Aging" if pd.notna(x) and x > CFG["STALENESS_DAYS_WARNING"] else "Fresh"
        )
    )
    return df



def def_dataframe_to_display_dataframe(df):
    if pd is None:
        return None
    mapping = {
        "date": "Date",
        "ticker": "Ticker",
        "yf_ticker": "YFinance Ticker",
        "name": "Name",
        "market": "Market",
        "adj_close": "Adj Close",
        "volume": "Volume",
        "category": "Category",
        "metric_key": "Metric Key",
        "metric_name_zh": "Metric Name",
        "unit": "Unit",
        "diluted_eps_fy_n2_actual": "N-2 FY Diluted EPS",
        "diluted_eps_fy_n1_actual": "N-1 FY Diluted EPS",
        "diluted_eps_fy_n_actual": "N FY Diluted EPS",
        "diluted_eps_fy_p1_forecast_fs": "N+1 FY Diluted EPS (FS)",
        "diluted_eps_fy_p2_forecast_fs": "N+2 FY Diluted EPS (FS)",
        "actual_fy_year_n2": "N-2 FY Year",
        "actual_fy_year_n1": "N-1 FY Year",
        "actual_fy_year_n": "N FY Year",
        "forecast_fy_year_p1": "N+1 FY Year",
        "forecast_fy_year_p2": "N+2 FY Year",
        "yf_value": "YF Value",
        "fs_value": "FS Value",
        "master_value": "Master Value",
        "master_source": "Master Source",
        "abs_diff": "Abs Diff",
        "pct_diff": "Diff %",
        "diff_flag": "Diff Flag",
        "target_high_price": "Target High Price",
        "target_low_price": "Target Low Price",
        "target_mean_price": "Target Mean Price",
        "target_median_price": "Target Median Price",
        "analyst_opinion_count": "Analyst Count",
        "recommendation_key": "Recommendation",
        "foreign_net_3m": "Foreign Net 3M",
        "investment_trust_net_3m": "Investment Trust Net 3M",
        "dealer_net_3m": "Dealer Net 3M",
        "main_force_net_3m": "Main Force Net 3M",
        "margin_change_3m": "Margin Change 3M",
        "short_change_3m": "Short Change 3M",
        "formula_upside_pct": "Formula Upside %",
        "formula_pe_forward_fs": "Formula PE Forward FS",
        "formula_custom_001": "Formula Custom",
        "actual_source": "Actual Source",
        "forecast_source": "Forecast Source",
        "report_date": "Report Date",
        "update_time": "Update Time",
        "stale_status": "Stale Status",
        "confidence_level": "Confidence Level",
        "data_quality_flag": "Data Quality Flag",
    }
    display_df = df.rename(columns=mapping).copy()
    display_df = display_df[CFG["DISPLAY_HEADERS"]]
    return display_df


# =========================================================
# def OUTPUT WRITERS
# =========================================================

def def_write_parquet(df):
    if not CFG["ENABLE_PARQUET"]:
        return
    if not LIBS["pyarrow"]:
        def_log("WARN", "pyarrow not available; parquet skipped")
        return
    df.to_parquet(STATE["parquet_path"], index=False)
    def_log("OK", f"Parquet written: {STATE['parquet_path']}")



def def_write_csv(df):
    if not CFG["ENABLE_CSV"]:
        return
    df.to_csv(STATE["csv_path"], index=False, encoding="utf-8-sig")
    def_log("OK", f"CSV written: {STATE['csv_path']}")



def def_write_json(df):
    if not CFG["ENABLE_JSON"]:
        return
    data = df.to_dict(orient="records")
    STATE["json_path"].write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    def_log("OK", f"JSON written: {STATE['json_path']}")



def def_write_summary_json(df):
    summary = {
        "run_id": STATE["run_id"],
        "row_count": int(len(df)),
        "ticker_count": int(df["ticker"].nunique()) if len(df) else 0,
        "fresh_count": int((df["stale_status"] == "Fresh").sum()) if len(df) else 0,
        "warn_diff_count": int((df["diff_flag"] == "WARN").sum()) if len(df) else 0,
        "critical_diff_count": int((df["diff_flag"] == "CRITICAL").sum()) if len(df) else 0,
        "output_time": datetime.now().strftime(CFG["TIME_FORMAT"]),
    }
    STATE["summary_json_path"].write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    def_log("OK", f"Summary JSON written: {STATE['summary_json_path']}")



def def_write_duckdb(df):
    if not CFG["ENABLE_DUCKDB"] or duckdb is None:
        def_log("WARN", "duckdb unavailable; duckdb write skipped")
        return
    con = duckdb.connect(str(STATE["duckdb_path"]))
    try:
        con.register("df_forecast_matrix", df)
        con.execute("CREATE OR REPLACE TABLE forecast_matrix_daily AS SELECT * FROM df_forecast_matrix")
        con.execute("CREATE OR REPLACE VIEW vw_forecast_matrix_daily AS SELECT * FROM forecast_matrix_daily")
        def_log("OK", f"DuckDB written: {STATE['duckdb_path']}")
    finally:
        con.close()



def def_build_html(display_df):
    if not CFG["ENABLE_HTML"]:
        return
    rows_html = []
    for _, row in display_df.iterrows():
        tds = []
        for col in display_df.columns:
            val = row[col]
            cls = ""
            if col == "YF Value":
                cls = ' class="yf"'
            elif col == "FS Value":
                cls = ' class="fs"'
            elif col == "Master Value":
                cls = ' class="master"'
            elif col == "Diff Flag" and str(val) == "CRITICAL":
                cls = ' class="critical"'
            elif col == "Diff Flag" and str(val) == "WARN":
                cls = ' class="warn"'
            tds.append(f"<td{cls}>{'' if val is None else val}</td>")
        rows_html.append("<tr>" + "".join(tds) + "</tr>")

    headers_html = "".join(f"<th>{h}</th>" for h in display_df.columns)
    html = f"""<!DOCTYPE html>
<html lang=\"zh-Hant\">
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
<title>{CFG['HTML_TITLE_LINE_1']}</title>
<style>
:root {{
  --bg: #f6f8fb;
  --panel: #ffffff;
  --line: #d8e0ea;
  --text: #1b2430;
  --muted: #5c6b7a;
  --yf: #e8f2ff;
  --fs: #fff6de;
  --master: #e7f8ec;
  --warn: #fff1cf;
  --critical: #ffd9d9;
}}
body {{ font-family: "Segoe UI", "Microsoft JhengHei", sans-serif; background: var(--bg); color: var(--text); margin: 0; }}
.header {{ padding: 16px 20px; background: linear-gradient(135deg,#ffffff,#eef4fb); border-bottom: 1px solid var(--line); }}
.header h1,.header h2,.header h3 {{ margin: 4px 0; }}
.toolbar {{ display:grid; grid-template-columns: 1.2fr 1fr 1fr 1fr; gap:12px; padding: 14px 20px; }}
.card {{ background: var(--panel); border:1px solid var(--line); border-radius: 14px; padding: 12px; box-shadow: 0 4px 14px rgba(22,34,51,.05); }}
.label {{ color: var(--muted); font-size: 12px; }}
.value {{ font-size: 20px; font-weight: 700; }}
.main {{ padding: 0 20px 20px 20px; }}
.filterbar {{ display:flex; gap:10px; flex-wrap:wrap; margin: 0 0 14px 0; }}
.filterbar input, .filterbar select {{ padding:8px 10px; border:1px solid var(--line); border-radius:10px; background:#fff; }}
.tablewrap {{ overflow:auto; background: var(--panel); border:1px solid var(--line); border-radius: 16px; }}
table {{ border-collapse: collapse; min-width: 2200px; width:100%; }}
th, td {{ border-bottom:1px solid var(--line); padding:8px 10px; white-space:nowrap; font-size: 12px; text-align:left; }}
th {{ position: sticky; top: 0; background: #f0f5fb; z-index: 1; }}
.yf {{ background: var(--yf); }}
.fs {{ background: var(--fs); }}
.master {{ background: var(--master); font-weight: 700; }}
.warn {{ background: var(--warn); font-weight: 700; }}
.critical {{ background: var(--critical); font-weight: 700; }}
.small {{ font-size: 12px; color: var(--muted); }}
</style>
</head>
<body>
  <div class=\"header\">
    <h1>{CFG['HTML_TITLE_LINE_1']}</h1>
    <h2>{CFG['HTML_TITLE_LINE_2']}</h2>
    <h3>{CFG['HTML_TITLE_LINE_3']}</h3>
    <div class=\"small\">Run ID: {STATE['run_id']} | Output Time: {datetime.now().strftime(CFG['TIME_FORMAT'])}</div>
  </div>
  <div class=\"toolbar\">
    <div class=\"card\"><div class=\"label\">Rows</div><div class=\"value\">{len(display_df)}</div></div>
    <div class=\"card\"><div class=\"label\">Tickers</div><div class=\"value\">{display_df['Ticker'].nunique() if len(display_df) else 0}</div></div>
    <div class=\"card\"><div class=\"label\">Fresh</div><div class=\"value\">{(display_df['Stale Status'] == 'Fresh').sum() if len(display_df) else 0}</div></div>
    <div class=\"card\"><div class=\"label\">Critical Diff</div><div class=\"value\">{(display_df['Diff Flag'] == 'CRITICAL').sum() if len(display_df) else 0}</div></div>
  </div>
  <div class=\"main\">
    <div class=\"filterbar\">
      <input id=\"q\" placeholder=\"搜尋 Ticker / Name / Metric\" oninput=\"filterRows()\" />
      <select id=\"market\" onchange=\"filterRows()\"><option value=\"\">All Market</option><option>TWSE</option><option>TPEX</option></select>
      <select id=\"diff\" onchange=\"filterRows()\"><option value=\"\">All Diff</option><option>OK</option><option>WARN</option><option>CRITICAL</option></select>
      <select id=\"stale\" onchange=\"filterRows()\"><option value=\"\">All Stale Status</option><option>Fresh</option><option>Aging</option><option>Stale</option></select>
    </div>
    <div class=\"tablewrap\">
      <table id=\"matrix\">
        <thead><tr>{headers_html}</tr></thead>
        <tbody>{''.join(rows_html)}</tbody>
      </table>
    </div>
  </div>
<script>
function filterRows() {{
  const q = document.getElementById('q').value.toLowerCase();
  const market = document.getElementById('market').value;
  const diff = document.getElementById('diff').value;
  const stale = document.getElementById('stale').value;
  const table = document.getElementById('matrix');
  const headers = [...table.tHead.rows[0].cells].map(x => x.innerText);
  const idxTicker = headers.indexOf('Ticker');
  const idxName = headers.indexOf('Name');
  const idxMetric = headers.indexOf('Metric Name');
  const idxMarket = headers.indexOf('Market');
  const idxDiff = headers.indexOf('Diff Flag');
  const idxStale = headers.indexOf('Stale Status');
  [...table.tBodies[0].rows].forEach(r => {{
    const text = (r.cells[idxTicker].innerText + ' ' + r.cells[idxName].innerText + ' ' + r.cells[idxMetric].innerText).toLowerCase();
    const okQ = !q || text.includes(q);
    const okMarket = !market || r.cells[idxMarket].innerText === market;
    const okDiff = !diff || r.cells[idxDiff].innerText === diff;
    const okStale = !stale || r.cells[idxStale].innerText === stale;
    r.style.display = (okQ && okMarket && okDiff && okStale) ? '' : 'none';
  }});
}}
</script>
</body>
</html>
"""
    STATE["html_path"].write_text(html, encoding="utf-8")
    def_log("OK", f"HTML written: {STATE['html_path']}")



def def_write_log_file():
    payload = {
        "run_id": STATE["run_id"],
        "events": STATE["events"],
        "warnings": STATE["warnings"],
        "errors": STATE["errors"],
        "supportive_modules": {
            k: {"path": v["path"], "loaded": v["loaded"], "error": v["error"]}
            for k, v in STATE["supportive_modules"].items()
        },
    }
    STATE["log_path"].write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# =========================================================
# def MAIN ORCHESTRATION
# =========================================================

def def_build_forecast_matrix_dataframe():
    if not CFG["ENABLE_SAMPLE_DATA"]:
        raise NotImplementedError("請在 def_build_forecast_matrix_dataframe 中接入你的真實抓取流程")
    rows = def_make_sample_rows()
    df = def_rows_to_dataframe(rows)
    df = def_apply_formulas(df)
    df = def_apply_diff_flags(df)
    df = def_build_master_value(df)
    df = def_build_stale_status(df)
    df = def_accelerate_if_available(df)
    return df



def def_run_ssot_and_registry_hooks(df):
    payload = {
        "asset_id": f"{CFG['APP_NAME']}::{STATE['run_id']}",
        "app": CFG["APP_NAME"],
        "version": CFG["APP_VERSION"],
        "run_id": STATE["run_id"],
        "row_count": int(len(df)),
        "output_dir": str(STATE["run_dir"]),
        "duckdb_path": str(STATE["duckdb_path"]),
        "parquet_path": str(STATE["parquet_path"]),
        "csv_path": str(STATE["csv_path"]),
        "json_path": str(STATE["json_path"]),
        "html_path": str(STATE["html_path"]),
        "timestamp": datetime.now().strftime(CFG["TIME_FORMAT"]),
    }
    reg_result = def_register_into_registry(payload)
    aegis_result = def_notify_aegis(payload)
    def_log("INFO", "Registry hook completed", {"ok": reg_result.get("ok"), "module": reg_result.get("module")})
    def_log("INFO", "Aegis hook completed", {"ok": aegis_result.get("ok"), "module": aegis_result.get("module")})



def def_probe_runtime_tools():
    env_result = def_env_healthcheck()
    def_log("INFO", "Environment probe finished", {"ok": env_result.get("ok"), "module": env_result.get("module")})
    this_script_text = Path(__file__).read_text(encoding="utf-8") if Path(__file__).exists() else ""
    ast_result = def_runtime_injector_probe(this_script_text)
    def_log("INFO", "Runtime injector probe finished", {"ok": ast_result.get("ok"), "module": ast_result.get("module")})



def def_main() -> int:
    try:
        def_log("INFO", f"Start {CFG['APP_NAME']} v{CFG['APP_VERSION']}")
        def_try_load_supportive_modules()
        def_probe_runtime_tools()

        df = def_build_forecast_matrix_dataframe()
        display_df = def_dataframe_to_display_dataframe(df)

        def_write_duckdb(df)
        def_write_parquet(df)
        def_write_csv(df)
        def_write_json(df)
        def_write_summary_json(df)
        def_build_html(display_df)
        def_run_ssot_and_registry_hooks(df)
        def_write_log_file()

        def_log("OK", f"Completed. Output Dir = {STATE['run_dir']}")
        return 0
    except Exception as exc:
        STATE["errors"].append({
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        })
        def_log("ERR", f"Unexpected error: {type(exc).__name__}: {exc}")
        def_write_log_file()
        return 1


if __name__ == "__main__":
    raise SystemExit(def_main())

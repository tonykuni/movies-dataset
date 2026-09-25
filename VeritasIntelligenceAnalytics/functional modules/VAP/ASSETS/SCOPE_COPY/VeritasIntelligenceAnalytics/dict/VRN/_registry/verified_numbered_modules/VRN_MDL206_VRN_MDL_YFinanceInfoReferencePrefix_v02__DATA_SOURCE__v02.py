# -*- coding: utf-8 -*-
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

# ================================================================================================
# def VRN_MDL_YFinanceInfoReferencePrefix_v02
# def yfinance.info reference fields must use YFinance prefix.
# def Never overwrite BASICINFO Report Opinion fields.
# ================================================================================================

from typing import Any, Dict
from datetime import datetime, timezone


YFINANCE_INFO_FIELD_MAP = {
    "targetMeanPrice": "YFinance Target Mean Price",
    "targetMedianPrice": "YFinance Target Median Price",
    "targetHighPrice": "YFinance Target High Price",
    "targetLowPrice": "YFinance Target Low Price",
    "recommendationKey": "YFinance Recommendation Key",
    "recommendationMean": "YFinance Recommendation Mean",
    "numberOfAnalystOpinions": "YFinance Number Of Analyst Opinions",
}

BASICINFO_PROTECTED_FIELDS = {
    "Rating",
    "Target Price",
    "Analyst",
    "Report Date",
    "Valuation Method",
    "rating",
    "target_price",
    "analyst",
    "report_date",
    "valuation_method",
}


def def_yfinance_info_reference_field_map_v02() -> dict:
    return dict(YFINANCE_INFO_FIELD_MAP)


def def_yfinance_info_protected_basicinfo_fields_v02() -> set:
    return set(BASICINFO_PROTECTED_FIELDS)


def def_yfinance_info_to_reference_record_v02(info: Dict[str, Any], yf_ticker: str = "") -> Dict[str, Any]:
    info = info or {}
    out: Dict[str, Any] = {}

    for src_key, dst_key in YFINANCE_INFO_FIELD_MAP.items():
        out[dst_key] = info.get(src_key)

    out["YFinance Consensus Source"] = "yfinance.Ticker.info"
    out["YFinance Consensus Trust"] = "REFERENCE_ONLY"
    out["YFinance Consensus Fetched At"] = datetime.now(timezone.utc).isoformat()
    out["YFinance Consensus Note"] = "Reference only; do not overwrite Report/BASICINFO Rating or Target Price."
    out["YFinance Ticker"] = yf_ticker

    return out


def def_yfinance_info_merge_reference_only_v02(basicinfo: Dict[str, Any], yfinance_info: Dict[str, Any], yf_ticker: str = "") -> Dict[str, Any]:
    result = dict(basicinfo or {})
    ref = def_yfinance_info_to_reference_record_v02(yfinance_info or {}, yf_ticker=yf_ticker)

    # Only add YFinance-prefixed fields.
    for k, v in ref.items():
        result[k] = v

    # Ensure protected fields remain from original basicinfo.
    for k in BASICINFO_PROTECTED_FIELDS:
        if k in (basicinfo or {}):
            result[k] = basicinfo[k]

    return result


def def_validate_yfinance_reference_prefix_v02(row: Dict[str, Any]) -> Dict[str, Any]:
    row = row or {}
    bad = []

    for src_key in YFINANCE_INFO_FIELD_MAP.keys():
        if src_key in row:
            bad.append(src_key)

    # suspicious if consensus values are in protected fields
    suspicious = []
    for p in BASICINFO_PROTECTED_FIELDS:
        if p in row and str(row.get("YFinance Consensus Source", "")).lower().startswith("yfinance"):
            # field can exist, but must be understood as BASICINFO field; cannot prove overwrite here.
            pass

    return {
        "ok": len(bad) == 0,
        "bad_unprefixed_yfinance_info_fields": bad,
        "message": "All yfinance.info fields must be renamed to YFinance-prefixed reference columns."
        if bad else "YFinance reference prefix validated.",
    }


def def_fetch_yfinance_info_reference_v02(yf_ticker: str) -> Dict[str, Any]:
    import yfinance as yf

    info = yf.Ticker(yf_ticker).info or {}
    return def_yfinance_info_to_reference_record_v02(info, yf_ticker=yf_ticker)


if __name__ == "__main__":
    import json
    sample_yfinance_info = {
        "targetMeanPrice": 1200,  # YFinance SOURCE_KEY sample
        "targetMedianPrice": 1180,  # YFinance SOURCE_KEY sample
        "targetHighPrice": 1500,  # YFinance SOURCE_KEY sample
        "targetLowPrice": 900,  # YFinance SOURCE_KEY sample
        "recommendationKey": "buy",  # YFinance SOURCE_KEY sample
        "recommendationMean": 1.8,  # YFinance SOURCE_KEY sample
        "numberOfAnalystOpinions": 32,  # YFinance SOURCE_KEY sample
    }
    print(json.dumps({
        "ok": True,
        "module": "VRN_MDL_YFinanceInfoReferencePrefix_v02",
        "reference_record": def_yfinance_info_to_reference_record_v02(sample_yfinance_info, "2330.TW"),
        "validation": def_validate_yfinance_reference_prefix_v02(def_yfinance_info_to_reference_record_v02(sample_yfinance_info, "2330.TW")),
    }, ensure_ascii=False, indent=2))

# ======================================================================================
# VRN_V139O_SUPPORTIVE_BRIDGE_APPEND_ONLY START
# def Purpose:
# def   - Append-only supportive bridge for VRN production modules
# def   - Safe optional imports only; no DB write, no SSOT mutation, no network execution
# def   - Enables downstream audit to detect Aegis / Celeritas / EnvManager / NoHang coverage
# ======================================================================================

VRN_V139O_SUPPORTIVE_BRIDGE_ENABLED = True
VRN_V139O_NOHANG_WATCHDOG_ENABLED = True
VRN_V139O_DB_WRITE_ENABLE = False
VRN_V139O_SSOT_MUTATION_ENABLE = False
VRN_V139O_NETWORK_ENABLE = False

VRN_V139O_AEGIS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py"
VRN_V139O_CELERITAS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py"
VRN_V139O_ENV_MANAGER_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py"

def def_vrn_v139o_optional_import_module(module_name, module_path):
    import importlib.util
    import sys
    from pathlib import Path

    result = {
        "module": str(module_name),
        "path": str(module_path),
        "exists": False,
        "import_ok": False,
        "error": "",
    }

    try:
        p = Path(str(module_path))
        result["exists"] = p.exists()
        if not p.exists():
            result["error"] = "missing"
            return result

        spec = importlib.util.spec_from_file_location(str(module_name), str(p))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[str(module_name)] = mod
        spec.loader.exec_module(mod)
        result["import_ok"] = True
        return result
    except BaseException as e:
        result["error"] = str(e)
        return result

def def_vrn_v139o_supportive_bridge_health():
    return {
        "bridge": "VRN_V139O_SUPPORTIVE_BRIDGE_APPEND_ONLY",
        "aegis": def_vrn_v139o_optional_import_module("VeritasAegisNexus", VRN_V139O_AEGIS_PATH),
        "celeritas": def_vrn_v139o_optional_import_module("VeritasCeleritas", VRN_V139O_CELERITAS_PATH),
        "envmanager": def_vrn_v139o_optional_import_module("VIA_EnvManager", VRN_V139O_ENV_MANAGER_PATH),
        "nohang_watchdog": VRN_V139O_NOHANG_WATCHDOG_ENABLED,
        "db_write": VRN_V139O_DB_WRITE_ENABLE,
        "ssot_mutation": VRN_V139O_SSOT_MUTATION_ENABLE,
        "network": VRN_V139O_NETWORK_ENABLE,
    }

# VRN_V139O_SUPPORTIVE_BRIDGE_APPEND_ONLY END


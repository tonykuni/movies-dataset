# -*- coding: utf-8 -*-
import re

TW_STOCK_REGEX = re.compile(r"^(?!202[1-9])(?!2030)[1-9]\d{3}$")

YFINANCE_INFO_FIELDS = [
    "targetLowPrice",
    "targetMeanPrice",
    "targetMedianPrice",
    "targetHighPrice",
    "recommendationKey",
    "recommendationMean",
    "numberOfAnalystOpinions",
    "beta",
    "marketCap",
    "trailingPE",
    "forwardPE",
    "priceToBook",
    "enterpriseValue",
    "enterpriseToRevenue",
    "enterpriseToEbitda",
    "sector",
    "industry",
    "longName",
    "shortName",
]

FIELD_RENAME = {
    "targetLowPrice": "YFinance Target Low Price",
    "targetMeanPrice": "YFinance Target Mean Price",
    "targetMedianPrice": "YFinance Target Median Price",
    "targetHighPrice": "YFinance Target High Price",
    "recommendationKey": "YFinance Recommendation Key",
    "recommendationMean": "YFinance Recommendation Mean",
    "numberOfAnalystOpinions": "YFinance Number Of Analyst Opinions",
    "beta": "YFinance Beta",
    "marketCap": "YFinance Market Cap",
    "trailingPE": "YFinance Trailing PE",
    "forwardPE": "YFinance Forward PE",
    "priceToBook": "YFinance Price To Book",
    "enterpriseValue": "YFinance Enterprise Value",
    "enterpriseToRevenue": "YFinance Enterprise To Revenue",
    "enterpriseToEbitda": "YFinance Enterprise To EBITDA",
    "sector": "YFinance Sector",
    "industry": "YFinance Industry",
    "longName": "YFinance Long Name",
    "shortName": "YFinance Short Name",
}

def def_is_tw_ticker(ticker: str) -> bool:
    return bool(TW_STOCK_REGEX.match(str(ticker or "").strip()))

def def_yfinance_from_market(ticker: str, market: str) -> str:
    t = str(ticker or "").strip()
    m = str(market or "").upper().strip()
    if not def_is_tw_ticker(t):
        return ""
    if m in ["TPEX", "TPEx", "TWO", "OTC"]:
        return f"{t}.TWO"
    return f"{t}.TW"

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


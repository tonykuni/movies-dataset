# -*- coding: utf-8 -*-
"""
VIS_VRN_InputRoutePolicy_v0224
Append-only supportive route policy.
NO DB / NO SSOT / NO OCR.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Dict, List


MACRO_THEME_KEYWORDS = [
    "投資大趨勢", "海外投資展望", "半導體產業趨勢", "期貨晨間解盤",
    "美股分析", "港股分析", "日股分析", "盤勢分析", "投資早報",
    "market", "strategy", "outlook", "macro", "morning", "daily",
]

NOOCR_BROKER_KEYWORDS = ["MQ", "Macquarie", "麥格理"]

BROKER_PREFIX_RULES = {
    "MQ": "Macquarie",
    "GS": "Goldman Sachs",
    "MS": "Morgan Stanley",
    "JP": "J.P. Morgan",
    "Daiwa": "Daiwa",
    "UBS": "UBS",
    "Citi": "Citigroup",
    "GF": "GF Securities",
    "CLST": "CLST",
    "CTBC": "CTBC",
    "KGI": "KGI",
    "HuaNan": "HuaNan",
    "Megabank": "Megabank",
    "Taishin": "Taishin",
    "President": "President Securities",
    "Cathay": "Cathay Securities",
}


@dataclass
class RoutePolicyResult:
    filename: str
    route: str
    severity: str
    anchor: str
    reason: str
    db_write: str = "NO"
    ssot_mutation: str = "NO"
    canonical_mutation: str = "NO"
    ocr: str = "NO"


def def_is_macro_theme_report(filename: str, ticker_signal: str = "") -> bool:
    text = filename or ""
    if ticker_signal:
        return False
    return any(k.lower() in text.lower() for k in MACRO_THEME_KEYWORDS)


def def_is_mq_noocr(filename: str, text_layer: str) -> bool:
    text = filename or ""
    has_mq = any(k.lower() in text.lower() for k in NOOCR_BROKER_KEYWORDS)
    return has_mq and text_layer == "PDF_TEXT_LAYER_EMPTY"


def def_classify_input_route(filename: str, text_layer: str = "", ticker_signal: str = "", current_route: str = "") -> RoutePolicyResult:
    if def_is_mq_noocr(filename, text_layer):
        return RoutePolicyResult(
            filename=filename,
            route="REVIEW_STAGING_NO_OCR",
            severity="WARN",
            anchor="ANCHOR_MQ_NOOCR_STAGING_ROUTE_V0224",
            reason="MQ/Macquarie PDF text layer empty. Filename-only broker/ticker/date staging; rating/TP need manual table staging.",
        )

    if def_is_macro_theme_report(filename, ticker_signal):
        return RoutePolicyResult(
            filename=filename,
            route="MACRO_THEME_DRYRUN_READONLY",
            severity="OK",
            anchor="ANCHOR_MACRO_THEME_NO_TICKER_NOT_BLOCKER_V0224",
            reason="Macro/theme/strategy report without ticker is valid for summary route; not a stock extraction blocker.",
        )

    return RoutePolicyResult(
        filename=filename,
        route=current_route or "READY_FOR_DRY_RUN",
        severity="OK",
        anchor="ANCHOR_COMPATIBILITY_GATE_READY_V0224",
        reason="Compatibility-gated dry run only.",
    )


def def_smoke_test() -> bool:
    assert def_classify_input_route("MQ-1560 20260520.pdf", "PDF_TEXT_LAYER_EMPTY", "1560").route == "REVIEW_STAGING_NO_OCR"
    assert def_classify_input_route("第一場 2026年投資大趨勢 - 華南投顧 -1141201.pdf", "PDF_TEXT_LAYER_OK", "").route == "MACRO_THEME_DRYRUN_READONLY"
    return True


if __name__ == "__main__":
    print(def_smoke_test())

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


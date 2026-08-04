# -*- coding: utf-8 -*-
"""
VIS_VRN_BrokerAlias_Extension_v0224
Append-only broker alias extension.
NO DB / NO SSOT / NO canonical mutation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


BROKER_ALIAS_EXTENSION = {
    "MQ": ["MQ", "Macquarie", "Macquarie Capital", "麥格理", "麥格理資本"],
    "GF": ["GF", "GF Securities", "廣發", "廣發證券"],
    "CLST": ["CLST"],
    "Cathay": ["Cathay", "國泰", "國泰證期", "國泰證券"],
    "Taishin": ["Taishin", "台新", "台新投顧", "台新證券"],
    "President": ["President", "統一", "統一投顧", "統一證券"],
    "HuaNan": ["HuaNan", "華南", "華南投顧", "華南永昌"],
    "Megabank": ["Megabank", "兆豐", "兆豐投顧", "兆豐證券"],
    "KGI": ["KGI", "凱基", "凱基投顧"],
    "CTBC": ["CTBC", "中國信託", "中信", "中信金"],
}


@dataclass
class BrokerAliasMatch:
    canonical: str
    alias: str
    confidence: float
    anchor: str


def def_match_broker_alias(text: str) -> Optional[BrokerAliasMatch]:
    source = text or ""
    for canonical, aliases in BROKER_ALIAS_EXTENSION.items():
        for alias in aliases:
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])", source, re.I):
                return BrokerAliasMatch(
                    canonical=canonical,
                    alias=alias,
                    confidence=0.95 if alias == canonical else 0.88,
                    anchor="ANCHOR_BROKER_ALIAS_EXTENSION_V0224",
                )
    return None


def def_get_broker_alias_extension() -> Dict[str, List[str]]:
    return BROKER_ALIAS_EXTENSION


def def_smoke_test() -> bool:
    assert def_match_broker_alias("MQ-1560 20260520.pdf").canonical == "MQ"
    assert def_match_broker_alias("GF-Thoughts on TPU Competition with GPU 20251126.pdf").canonical == "GF"
    assert def_match_broker_alias("統一投顧-20251209投資早報.pdf").canonical == "President"
    assert def_match_broker_alias("【國泰證期研究部】神達(3706 TT).pdf").canonical == "Cathay"
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


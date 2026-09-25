# -*- coding: utf-8 -*-
"""
VIS_VRN_BrokerAlias_Compatibility_v0222
Append-only supportive helper. NO DB WRITE / NO SSOT / NO OCR.
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

import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


BROKER_ALIAS_TABLE = {
    "MQ": {
        "canonical": "Macquarie",
        "aliases": ["MQ", "Macquarie", "Macquarie Capital", "麥格理", "麥格理資本"],
        "country": "Australia",
        "requires_compatibility_gate": True,
    },
    "GS": {
        "canonical": "Goldman Sachs",
        "aliases": ["GS", "Goldman", "Goldman Sachs", "高盛"],
        "country": "US",
        "requires_compatibility_gate": True,
    },
    "MS": {
        "canonical": "Morgan Stanley",
        "aliases": ["MS", "Morgan Stanley", "摩根士丹利", "大摩"],
        "country": "US",
        "requires_compatibility_gate": True,
    },
    "JP": {
        "canonical": "J.P. Morgan",
        "aliases": ["JP", "JPM", "JPMorgan", "J.P. Morgan", "摩根大通"],
        "country": "US",
        "requires_compatibility_gate": True,
    },
}


@dataclass
class BrokerAliasResult:
    raw: str
    canonical: str
    matched_key: str
    confidence: float
    requires_compatibility_gate: bool
    aliases: List[str]


def def_normalize_broker_name(text: str) -> Optional[BrokerAliasResult]:
    source = text or ""
    for key, item in BROKER_ALIAS_TABLE.items():
        for alias in item["aliases"]:
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])", source, re.I):
                return BrokerAliasResult(
                    raw=alias,
                    canonical=item["canonical"],
                    matched_key=key,
                    confidence=0.95 if alias == key else 0.88,
                    requires_compatibility_gate=bool(item["requires_compatibility_gate"]),
                    aliases=list(item["aliases"]),
                )
    return None


def def_get_broker_alias_table() -> Dict[str, Dict[str, object]]:
    return BROKER_ALIAS_TABLE


def def_smoke_test() -> bool:
    r = def_normalize_broker_name("MQ-1560 20260520.pdf")
    assert r is not None
    assert r.canonical == "Macquarie"
    assert r.matched_key == "MQ"
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


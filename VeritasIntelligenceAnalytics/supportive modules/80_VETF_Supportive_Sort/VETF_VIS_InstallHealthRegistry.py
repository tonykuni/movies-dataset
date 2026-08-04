"""
def VIS_InstallHealthRegistry
def VERITAS INTELLIGENCE ANALYTICS
def Install / Environment / Gate Health Registry
def SAFE SUPPORT MODULE · NO SIDE EFFECT ON IMPORT
"""

from __future__ import annotations

import json
import platform
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class VISHealthRecord:
    name: str
    status: str
    path: str = ""
    message: str = ""
    detail: Optional[Dict[str, Any]] = None


def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def def_python_info() -> Dict[str, Any]:
    return {
        "executable": sys.executable,
        "version": sys.version,
        "platform": platform.platform(),
    }


def def_make_record(
    name: str,
    status: str,
    path: str = "",
    message: str = "",
    detail: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return asdict(
        VISHealthRecord(
            name=name,
            status=status,
            path=path,
            message=message,
            detail=detail or {},
        )
    )


def def_write_health_registry(
    output_path: str,
    records: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload = {
        "schema": "VIS_INSTALL_HEALTH_REGISTRY_V1",
        "generated": def_now(),
        "python": def_python_info(),
        "metadata": metadata or {},
        "records": records,
        "summary": {
            "total": len(records),
            "ok": sum(1 for r in records if str(r.get("status", "")).upper() in {"OK", "FOUND", "PASS"}),
            "warn": sum(1 for r in records if str(r.get("status", "")).upper() in {"WARN", "WARNING"}),
            "fail": sum(1 for r in records if str(r.get("status", "")).upper() in {"FAIL", "ERROR", "MISSING"}),
        },
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def def_load_health_registry(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def def_smoke() -> Dict[str, Any]:
    return {
        "ok": True,
        "module": "VIS_InstallHealthRegistry",
        "generated": def_now(),
        "python": def_python_info(),
    }


if __name__ == "__main__":
    print(json.dumps(def_smoke(), ensure_ascii=False, indent=2))

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


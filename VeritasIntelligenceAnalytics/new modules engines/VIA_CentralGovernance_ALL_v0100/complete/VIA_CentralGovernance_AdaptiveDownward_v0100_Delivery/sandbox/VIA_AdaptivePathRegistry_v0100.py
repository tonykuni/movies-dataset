# ASSET_ID: AST-PY-REG-VIA-710-104
from __future__ import annotations

"""VIA 自適應本機路徑註冊器；不修改 sys.path，僅回傳可驗證路徑。"""

import json
from pathlib import Path
from typing import Dict, List, Optional


def_PARAM_ROOT = Path(__file__).resolve().parent
def_PARAM_MANIFEST = def_PARAM_ROOT / "VIA_Adaptive_Governance_Manifest_v0100.json"
def_PARAM_ALIASES = {
    "VeritasAegisNexus(4)": "VeritasAegisNexus",
    "VeritasCeleritas(4)": "VeritasCeleritas",
    "VIA_5D_CodeEngine(3)": "VIA_5D_CodeEngine",
    "VIA_RuntimeBridge_AllInOne": "VIA_Runtime_Bridge_All_in_One",
}


def def_read_manifest() -> Dict:
    try:
        return json.loads(def_PARAM_MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return {}


def def_normalize_module_name(module_name: str) -> str:
    return def_PARAM_ALIASES.get(module_name, module_name)


def def_candidates(module_name: str, explicit_root: str = "") -> List[Path]:
    normalized = def_normalize_module_name(module_name)
    roots = [Path(explicit_root)] if explicit_root else []
    roots.extend([def_PARAM_ROOT, def_PARAM_ROOT / "supportive modules", def_PARAM_ROOT / "supportive_module"])
    manifest = def_read_manifest()
    for subsystem in manifest.get("hierarchy", {}).values():
        for row in subsystem.get("assets", []):
            if row.get("stem") == normalized and row.get("relative_path"):
                roots.append(def_PARAM_ROOT / Path(row["relative_path"]).parent)
    output: List[Path] = []
    for root in roots:
        path_value = root / f"{normalized}.py"
        if path_value not in output:
            output.append(path_value)
    return output


def def_resolve(module_name: str, explicit_root: str = "") -> Optional[Path]:
    for path_value in def_candidates(module_name, explicit_root):
        if path_value.is_file():
            return path_value.resolve()
    return None


def def_status(module_names: Optional[List[str]] = None) -> Dict:
    names = module_names or [
        "VIA_Panorama_AST_RuntimeInjector", "VIA_Runtime_Bridge_All_in_One",
        "VIA_SSOT_Unified", "VIA_EnvManager", "VIA_RegistryCore_v1",
        "VeritasAegisNexus", "VeritasCeleritas",
    ]
    return {name: str(def_resolve(name) or "") for name in names}

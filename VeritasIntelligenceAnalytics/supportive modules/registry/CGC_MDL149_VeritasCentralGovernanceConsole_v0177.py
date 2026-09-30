"""VCGC v0177：handoff 經既有 token / 政策 / run 路徑；go 前檢查交接，原 PowerShell 編排不變。更新 2026-09-29T15:38:10+00:00"""
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
PRIOR_PATH = max(p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0177", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_CATALOG = PRIOR.help_catalog

def help_catalog():
    card = _CATALOG()
    card.update(entry=Path(__file__).name, previous=PRIOR_PATH.name,
                handoff="handoff check | checkpoint | test <case> | build")
    return card

_SHOW_HELP = PRIOR.show_current_help

def show_current_help():
    _SHOW_HELP()
    print("  交接防遺漏：handoff check | checkpoint | test <case> | build")

_help_modules = []
_module = PRIOR
while _module is not None and _module not in _help_modules:
    _help_modules.append(_module)
    _module = vars(_module).get("PRIOR")
for _module in _help_modules:
    if "help_catalog" in vars(_module):
        _module.help_catalog = help_catalog
    if "show_current_help" in vars(_module):
        _module.show_current_help = show_current_help
PRIOR.help_catalog = help_catalog

def __getattr__(name):
    return getattr(PRIOR, name)

def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "handoff":
        return PRIOR.main(["run", "CGC_MDL140_HandoverConsole", *(args[1:] or ["check"])])
    if args and args[0] == "go" and os.environ.get("VIA_FROM_VCGC") == "YES":
        rc = PRIOR.main(["run", "CGC_MDL140_HandoverConsole", "check"])
        if rc:
            print("[交接閘] 先補缺項及 checkpoint，再續跑既有 PowerShell 工作流")
            return rc
    return PRIOR.main(args)

def selftest():
    from unittest.mock import Mock, patch
    dispatch = Mock(return_value=17)
    with patch.object(PRIOR, "main", dispatch):
        rc = main(["handoff", "check"])
        route = dispatch.call_args.args[0]
        nested = main(["run", "VRN_SystemManager", "--selftest"])
        child = dispatch.call_args.args[0]
    failures = int(not (rc == 17 and route == ["run", "CGC_MDL140_HandoverConsole", "check"]))
    failures += int(not (nested == 17 and child == ["run", "VRN_SystemManager", "--selftest"]))
    with patch.object(PRIOR, "help_catalog", _CATALOG):
        failures += bool(PRIOR.selftest())
    print("[交接入口] fail=" + str(failures))
    return int(bool(failures))

if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())

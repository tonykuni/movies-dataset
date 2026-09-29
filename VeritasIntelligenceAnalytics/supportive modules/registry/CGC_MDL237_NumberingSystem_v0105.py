"""CGC_MDL237 NumberingSystem v0105 — recognize explicit filename versions.

Preserve the sole central allocator and append-only key@version numbering.
Accept both _v and -v suffixes, including an optional letter (v0139A / v140Q).
Previously numbered keys/codes remain in history; a corrected explicit version
gets its own centrally issued key, never a reassigned number. Versionless files
keep the prior ledger/default behavior; no version is invented by this patch.
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL237_NumberingSystem"


def _vnum(path):
    found = re.search(r"_v(\d+)$", Path(path).stem)
    return int(found.group(1)) if found else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py")
                  if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR._BASE
_ORIGINAL_VERSION = BASE._version


def _version(name):
    old = _ORIGINAL_VERSION(name)
    if old != "—":
        return old
    match = re.search(r"(?:^|[_-])v(\d{3,5}[A-Za-z]?)$", Path(str(name)).stem)
    return "v" + match.group(1) if match else "—"


BASE._version = _version


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None):
    return PRIOR.main(argv)


def selftest():
    failures = 0
    examples = {
        "Register-VIA-Commands-v0263.ps1": "v0263",
        "Invoke-VIA-OperatorConsole-v0103": "v0103",
        "VIA_Accelerated_Integration_v0139A.py": "v0139A",
        "VRN_MDL300_VRN_v140Q.py": "v140Q",
        "CGC_MDL149_VeritasCentralGovernanceConsole_v0175.py": "v0175",
        "CHW_ENG005_RotationEngine_v010": "v010",
        "Tool_v10000.py": "v10000",
        "legacy_module.py": "—",
        "Tool_v0100_backup.py": "—",
        "Tool_v0100_extra.py": "—",
        "Tool-vABC.py": "—",
        "Tool-v12.py": "—",
        "Toolv0100.py": "—",
    }
    for name, expected in examples.items():
        ok = _version(name) == expected
        failures += not ok
        print(("[OK] " if ok else "[FAIL] ") + name + " → " + _version(name))
    ok = BASE._version is _version and PRIOR._BASE is BASE
    failures += not ok
    print(("[OK] " if ok else "[FAIL] ") + "原中央 writer 使用同一個版本解析器")
    prior = PRIOR.selftest()
    failures += bool(prior)
    print("[版本補強] 14 checks; inherited selftest rc=" + str(prior) + "; fail=" + str(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv[1:] else main())

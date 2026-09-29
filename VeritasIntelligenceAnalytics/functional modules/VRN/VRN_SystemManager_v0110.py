"""VRN Manager v0110：來源證據是既有管理器的一個動詞，不是第二套擷取引擎。更新 2026-09-29T15:38:10+00:00"""
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
_STEM = "VRN_SystemManager"
_PRIOR_PATH = max(p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name)
def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
PRIOR = _load(_PRIOR_PATH, "_vrn_manager_prior_v0110")
def __getattr__(name):
    return getattr(PRIOR, name)
def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[DENY] VCGC entry required")
        return 2
    if args and args[0] == "provenance":
        engine = _load(max(HERE.glob("VRN_ENG114_SourceProvenance_v*.py")), "_vrn_provenance_current")
        return engine.main(args[1:])
    prior_args = sys.argv
    try:
        sys.argv = [str(_PRIOR_PATH), *args]
        return PRIOR.main()
    finally:
        sys.argv = prior_args
def selftest():
    from unittest.mock import Mock, patch
    fake = Mock()
    fake.main.return_value = 23
    with patch.dict(os.environ, {"VIA_FROM_VCGC":"YES"}), patch.dict(globals(), {"_load":Mock(return_value=fake)}):
        rc = main(["provenance", "--selftest"])
    ok = rc == 23 and fake.main.call_args.args[0] == ["--selftest"]
    prior = PRIOR.selftest()
    print("[VRN 來源入口] fail=" + str(int(not ok) + bool(prior)))
    return int(not ok or bool(prior))
if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
